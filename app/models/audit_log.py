import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"AUD-{uuid.uuid4().hex[:8].upper()}")
    actor: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    target: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    result: Mapped[str] = mapped_column(String(64), default="SUCCESS", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


Index("idx_audit_actor_action_time", AuditLog.actor, AuditLog.action, AuditLog.timestamp)
