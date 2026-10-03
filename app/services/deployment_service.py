from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.deployment import Deployment
from app.schemas.deployment import DeploymentCreate
from app.core.logging import logger


class DeploymentService:
    def __init__(self, db: Session):
        self.db = db

    def record_deployment(self, dep_in: DeploymentCreate) -> Deployment:
        deployed_at = dep_in.deployed_at or datetime.now(timezone.utc)
        if deployed_at.tzinfo is None:
            deployed_at = deployed_at.replace(tzinfo=timezone.utc)

        deployment = Deployment(
            service=dep_in.service,
            version=dep_in.version,
            commit_hash=dep_in.commit_hash,
            environment=dep_in.environment,
            status=dep_in.status,
            metadata_json=dep_in.metadata_json,
            deployed_at=deployed_at
        )
        self.db.add(deployment)
        self.db.commit()
        self.db.refresh(deployment)

        logger.info(
            f"Deployment registered: [{deployment.service}] version={deployment.version} commit={deployment.commit_hash[:7]}",
            extra={"service": deployment.service, "action": "DEPLOYMENT"}
        )
        return deployment

    def get_recent_deployments_for_service(self, service: str, limit: int = 5) -> List[Deployment]:
        stmt = (
            select(Deployment)
            .where(Deployment.service == service)
            .order_by(desc(Deployment.deployed_at))
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_deployment_by_version(self, service: str, version: str) -> Optional[Deployment]:
        stmt = (
            select(Deployment)
            .where(Deployment.service == service)
            .where(Deployment.version == version)
        )
        return self.db.scalars(stmt).first()
