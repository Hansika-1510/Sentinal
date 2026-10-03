import asyncio
from app.db.session import SessionLocal
from app.services.remediation_service import RemediationService
from app.schemas.action import ActionExecuteRequest
from app.core.logging import logger


async def execute_remediation_background(action_id: str, actor: str):
    """Background worker task for executing approved remediation actions."""
    db = SessionLocal()
    try:
        service = RemediationService(db)
        await service.execute_action(action_id, ActionExecuteRequest(actor=actor))
        logger.info(f"Background remediation completed for action {action_id}")
    except Exception as e:
        logger.error(f"Error in remediation worker for action {action_id}: {str(e)}", exc_info=True)
    finally:
        db.close()
