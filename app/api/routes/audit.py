from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.audit import AuditLogRead
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("", response_model=List[AuditLogRead])
def list_audit_logs(
    actor: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve immutable audit trail of all AI recommendations, approvals, and operational executions."""
    service = AuditService(db)
    return service.get_audit_logs(limit=limit, actor=actor, action=action)
