from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogCreate
from app.core.security import redact_sensitive_data
from app.core.logging import logger


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record_audit_log(
        self,
        actor: str,
        action: str,
        target: str,
        reason: str = "",
        result: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Records an immutable audit log entry with sensitive data redacted."""
        clean_meta = redact_sensitive_data(metadata or {})
        
        entry = AuditLog(
            actor=actor,
            action=action,
            target=target,
            reason=reason,
            result=result,
            metadata_json=clean_meta,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        logger.info(
            f"AUDIT LOG: [{actor}] performed [{action}] on [{target}] - Result: {result}",
            extra={"actor": actor, "action": action, "target": target}
        )
        return entry

    def get_audit_logs(self, limit: int = 100, actor: Optional[str] = None, action: Optional[str] = None) -> List[AuditLog]:
        query = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
        if actor:
            query = query.filter(AuditLog.actor == actor)
        if action:
            query = query.filter(AuditLog.action == action)
        return list(self.db.scalars(query).all())
