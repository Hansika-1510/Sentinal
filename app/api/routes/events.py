import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.api.deps import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventRead, EventIngestResponse
from app.agents.sentinel import SentinelAgent
from app.services.autonomous_response_service import run_autonomous_response

router = APIRouter(prefix="/events", tags=["Runtime Events"])


@router.post("", response_model=EventIngestResponse, status_code=status.HTTP_200_OK)
async def ingest_event(event_in: EventCreate, db: Session = Depends(get_db)):
    """
    Ingest a runtime event.
    Automatically normalizes, deduplicates, and evaluates anomaly rules via Sentinel Agent.
    Creates an incident automatically if configured thresholds are breached, and — for
    HIGH/CRITICAL severities — runs investigation and remediation proposal unattended.
    """
    # Sentinel is synchronous and does real DB work, so it must not run on the event
    # loop: this route used to be `def` and FastAPI kept it in a threadpool. Awaiting
    # the thread hop restores that without giving up the async orchestration below.
    response = await asyncio.to_thread(SentinelAgent(db).process_event, event_in)
    if response.incident_created and response.incident_id:
        await run_autonomous_response(response.incident_id, db)
    return response


@router.get("", response_model=List[EventRead])
def list_events(
    service: Optional[str] = None,
    level: Optional[str] = None,
    incident_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Query recent runtime events."""
    stmt = select(Event).order_by(desc(Event.timestamp)).limit(limit)
    if service:
        stmt = stmt.where(Event.service == service)
    if level:
        stmt = stmt.where(Event.level == level.upper())
    if incident_id:
        stmt = stmt.where(Event.incident_id == incident_id)
    return list(db.scalars(stmt).all())
