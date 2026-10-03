import asyncio
from app.db.session import SessionLocal
from app.agents.investigator import InvestigatorAgent
from app.core.logging import logger


async def run_investigation_background(incident_id: str):
    """Background worker task for running LLM investigation, blast radius, and RCA generation."""
    db = SessionLocal()
    try:
        agent = InvestigatorAgent(db)
        await agent.investigate_incident(incident_id)
        logger.info(f"Background investigation completed for incident {incident_id}")
    except Exception as e:
        logger.error(f"Error in investigation worker for incident {incident_id}: {str(e)}", exc_info=True)
    finally:
        db.close()
