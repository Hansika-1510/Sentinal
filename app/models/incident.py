import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, DateTime, JSON, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"INC-{uuid.uuid4().hex[:8].upper()}")
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="MEDIUM", index=True, nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    status: Mapped[str] = mapped_column(String(32), default="DETECTED", index=True, nullable=False)    # DETECTED, TRIAGED, INVESTIGATING, AWAITING_APPROVAL, MITIGATING, MONITORING, RESOLVED, REJECTED, ESCALATED
    service_id: Mapped[str] = mapped_column(String(64), ForeignKey("services.id"), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(64), default="production", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # HIGH, MEDIUM, LOW
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    service = relationship("Service", back_populates="incidents")
    actions = relationship("Action", back_populates="incident", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="incident")
    memory = relationship("IncidentMemory", back_populates="incident", uselist=False, cascade="all, delete-orphan")


Index("idx_incident_status_severity", Incident.status, Incident.severity)
