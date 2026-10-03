import asyncio
from typing import Optional
from app.db.session import SessionLocal
from app.agents.sentinel import SentinelAgent
from app.schemas.event import EventCreate
from app.core.logging import logger


async def process_event_background(event_data: dict):
    """Background task for async event processing and anomaly evaluation."""
    db = SessionLocal()
    try:
        agent = SentinelAgent(db)
        event_in = EventCreate.model_validate(event_data)
        res = agent.process_event(event_in)
        logger.info(f"Background Sentinel processed event. Incident created: {res.incident_created}")
    except Exception as e:
        logger.error(f"Error in Sentinel background worker: {str(e)}", exc_info=True)
    finally:
        db.close()
