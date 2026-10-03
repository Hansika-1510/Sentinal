import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, JSON, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(128), default="runtime", nullable=False)
    service: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    environment: Mapped[str] = mapped_column(String(64), default="production", nullable=False)
    level: Mapped[str] = mapped_column(String(32), default="INFO", index=True, nullable=False)  # INFO, WARN, ERROR, CRITICAL
    message: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), default="error_log", index=True, nullable=False)  # error_log, http_500, stack_trace, alert, deployment_event, health_check, runtime_metric
    signature: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    incident_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("incidents.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    incident = relationship("Incident", back_populates="events")


Index("idx_event_service_type_time", Event.service, Event.event_type, Event.timestamp)
