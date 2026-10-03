from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.api.deps import get_db
from app.models.action import Action
from app.schemas.action import (
    ActionRead,
    ActionApproveRequest,
    ActionRejectRequest,
    ActionExecuteRequest
)
from app.services.remediation_service import RemediationService
from app.core.exceptions import ActionNotFoundException

router = APIRouter(prefix="/actions", tags=["Operational Actions & Remediation"])


@router.get("/{action_id}", response_model=ActionRead)
def get_action(action_id: str, db: Session = Depends(get_db)):
    """Get operational action by ID."""
    action = db.get(Action, action_id)
    if not action:
        raise ActionNotFoundException(action_id)
    return action


@router.post("/{action_id}/approve", response_model=ActionRead)
def approve_action(action_id: str, req: ActionApproveRequest, db: Session = Depends(get_db)):
    """Human operator approves a proposed remediation action."""
    service = RemediationService(db)
    return service.approve_action(action_id, req)


@router.post("/{action_id}/reject", response_model=ActionRead)
def reject_action(action_id: str, req: ActionRejectRequest, db: Session = Depends(get_db)):
    """Human operator rejects a proposed remediation action."""
    service = RemediationService(db)
    return service.reject_action(action_id, req)


@router.post("/{action_id}/execute", response_model=ActionRead)
async def execute_action(action_id: str, req: ActionExecuteRequest, db: Session = Depends(get_db)):
    """
    Execute an operational remediation action.
    Server-side rule: MEDIUM & HIGH risk actions strictly require prior approval (status == APPROVED).
    Only allowlisted actions are executed.
    """
    service = RemediationService(db)
    return await service.execute_action(action_id, req)


@router.get("", response_model=List[ActionRead])
def list_actions(
    incident_id: Optional[str] = None,
    approval_status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List operational actions."""
    stmt = select(Action).order_by(desc(Action.created_at)).limit(limit)
    if incident_id:
        stmt = stmt.where(Action.incident_id == incident_id)
    if approval_status:
        stmt = stmt.where(Action.approval_status == approval_status.upper())
    return list(db.scalars(stmt).all())
