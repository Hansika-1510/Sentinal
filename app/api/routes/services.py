from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.api.deps import get_db
from app.models.service import Service
from app.schemas.service import ServiceRead, ServiceCreate, ServiceUpdate
from app.core.exceptions import ServiceNotFoundException

router = APIRouter(prefix="/services", tags=["Services Topology"])


@router.get("", response_model=List[ServiceRead])
def list_services(db: Session = Depends(get_db)):
    """List all registered services and their dependencies."""
    return list(db.scalars(select(Service)).all())


@router.post("", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
def create_service(service_in: ServiceCreate, db: Session = Depends(get_db)):
    """Register a new service in the dependency graph."""
    service = Service(
        name=service_in.name,
        environment=service_in.environment,
        description=service_in.description,
        dependencies=service_in.dependencies,
        metadata_json=service_in.metadata_json
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.get("/{service_id_or_name}", response_model=ServiceRead)
def get_service(service_id_or_name: str, db: Session = Depends(get_db)):
    """Retrieve service details by ID or Name."""
    service = db.get(Service, service_id_or_name)
    if not service:
        service = db.scalars(select(Service).where(Service.name == service_id_or_name)).first()
    if not service:
        raise ServiceNotFoundException(service_id_or_name)
    return service
