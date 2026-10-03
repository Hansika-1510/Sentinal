import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"DEP-{uuid.uuid4().hex[:8].upper()}")
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    commit_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    environment: Mapped[str] = mapped_column(String(64), default="production", nullable=False)
    service: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="SUCCESS", nullable=False)  # SUCCESS, FAILED, ROLLED_BACK
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


Index("idx_deployment_service_time", Deployment.service, Deployment.deployed_at)
