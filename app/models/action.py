import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, JSON, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"ACT-{uuid.uuid4().hex[:8].upper()}")
    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # ROLLBACK, RESTART_SERVICE, DISABLE_FEATURE, CHANGE_CONFIGURATION, ESCALATE
    risk_level: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH
    proposed_by: Mapped[str] = mapped_column(String(128), default="ResponsePlannerAgent", nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    expected_impact: Mapped[str] = mapped_column(Text, nullable=False)
    rollback_path: Mapped[str] = mapped_column(Text, default="", nullable=False)
    approval_status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True, nullable=False)  # PENDING, APPROVED, REJECTED, EXECUTED, FAILED
    approved_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    incident = relationship("Incident", back_populates="actions")


Index("idx_action_incident_status", Action.incident_id, Action.approval_status)
