from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.api.deps import get_db
from app.models.deployment import Deployment
from app.schemas.deployment import DeploymentCreate, DeploymentRead
from app.services.deployment_service import DeploymentService

router = APIRouter(prefix="/deployments", tags=["Deployments"])


@router.post("", response_model=DeploymentRead, status_code=status.HTTP_201_CREATED)
def record_deployment(dep_in: DeploymentCreate, db: Session = Depends(get_db)):
    """Register a new deployment event."""
    service = DeploymentService(db)
    return service.record_deployment(dep_in)


@router.get("", response_model=List[DeploymentRead])
def list_deployments(
    service: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List deployment records."""
    stmt = select(Deployment).order_by(desc(Deployment.deployed_at)).limit(limit)
    if service:
        stmt = stmt.where(Deployment.service == service)
    return list(db.scalars(stmt).all())
