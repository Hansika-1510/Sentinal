import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class IncidentMemory(Base):
    __tablename__ = "incident_memories"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id"), unique=True, nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    rca: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # Stored as vector or JSON float list
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    incident = relationship("Incident", back_populates="memory")
