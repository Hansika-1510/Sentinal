from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.api.deps import get_db
from app.models.incident import Incident
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentRead,
    IncidentDetailRead,
    IncidentResolveRequest,
    IncidentTimelineItem
)
from app.schemas.action import ActionCreate, ActionRead
from app.schemas.investigation import InvestigationResult, BlastRadiusReport
from app.schemas.postmortem import PostmortemReport, IncidentMemoryRead
from app.services.incident_service import IncidentService
from app.services.correlation_service import CorrelationService
from app.services.blast_radius_service import BlastRadiusService
from app.services.incident_memory_service import IncidentMemoryService
from app.services.remediation_service import RemediationService
from app.services.postmortem_service import PostmortemService
from app.agents.investigator import InvestigatorAgent
from app.core.exceptions import IncidentNotFoundException

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
def create_incident(inc_in: IncidentCreate, db: Session = Depends(get_db)):
    """Manually or programmatically create an incident."""
    service = IncidentService(db)
    return service.create_incident(inc_in)


@router.get("", response_model=List[IncidentRead])
def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    service_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all incidents with optional filtering."""
    service = IncidentService(db)
    return service.list_incidents(status=status, severity=severity, service_id=service_id, limit=limit)


@router.get("/{incident_id}", response_model=IncidentDetailRead)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Retrieve full incident details including actions and events."""
    service = IncidentService(db)
    inc = service.get_incident(incident_id)
    return inc


@router.post("/{incident_id}/investigate", response_model=InvestigationResult)
async def investigate_incident(incident_id: str, db: Session = Depends(get_db)):
    """
    Triggers the Investigator Agent on the incident.
    Synthesizes evidence, correlates commits/deployments/logs, calculates blast radius,
    and returns structured, evidence-backed Root Cause Analysis (RCA).
    """
    agent = InvestigatorAgent(db)
    return await agent.investigate_incident(incident_id)


@router.post("/{incident_id}/actions", response_model=ActionRead, status_code=status.HTTP_201_CREATED)
def propose_action(incident_id: str, action_in: ActionCreate, db: Session = Depends(get_db)):
    """Propose an operational remediation action for an incident."""
    action_in.incident_id = incident_id
    remediation_service = RemediationService(db)
    return remediation_service.create_action_proposal(action_in)


@router.get("/{incident_id}/timeline", response_model=List[IncidentTimelineItem])
def get_incident_timeline(incident_id: str, db: Session = Depends(get_db)):
    """
    Retrieve chronological incident timeline.
    Distinguishes observed facts from AI inferences.
    """
    correlation_service = CorrelationService(db)
    return correlation_service.build_chronological_timeline(incident_id)


@router.get("/{incident_id}/blast-radius", response_model=BlastRadiusReport)
def get_incident_blast_radius(incident_id: str, db: Session = Depends(get_db)):
    """Compute topology blast radius for an incident's service."""
    incident_service = IncidentService(db)
    inc = incident_service.get_incident(incident_id)
    service_name = inc.service.name if inc.service else inc.service_id
    blast_service = BlastRadiusService(db)
    return blast_service.calculate_blast_radius(service_name)


@router.get("/{incident_id}/similar", response_model=List[IncidentMemoryRead])
async def get_similar_incidents(incident_id: str, limit: int = Query(3, ge=1, le=10), db: Session = Depends(get_db)):
    """Retrieve semantically similar historical incidents from IncidentMemory."""
    incident_service = IncidentService(db)
    inc = incident_service.get_incident(incident_id)
    memory_service = IncidentMemoryService(db)
    query = f"{inc.title} {inc.summary or ''} {inc.root_cause or ''}"
    return await memory_service.find_similar_incidents(query, top_k=limit)


@router.post("/{incident_id}/resolve", response_model=IncidentRead)
async def resolve_incident(incident_id: str, req: IncidentResolveRequest, db: Session = Depends(get_db)):
    """
    Resolve an incident.
    Requires recovery verification (Sentinel monitoring confirms nominal error rates and health).
    Automatically generates postmortem on resolution.
    """
    service = IncidentService(db)
    return await service.resolve_incident(incident_id, req)


@router.get("/{incident_id}/postmortem", response_model=PostmortemReport)
async def get_postmortem(incident_id: str, db: Session = Depends(get_db)):
    """Generate or retrieve structured postmortem for an incident."""
    incident_service = IncidentService(db)
    inc = incident_service.get_incident(incident_id)
    postmortem_service = PostmortemService(db)
    return await postmortem_service.generate_and_store_postmortem(inc)
