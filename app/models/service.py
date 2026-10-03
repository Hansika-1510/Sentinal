import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    environment: Mapped[str] = mapped_column(String(64), default="production", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    dependencies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # list of downstream/upstream service names or IDs
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    incidents = relationship("Incident", back_populates="service", cascade="all, delete-orphan")
