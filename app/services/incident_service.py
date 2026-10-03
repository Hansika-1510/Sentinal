from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.incident import Incident
from app.models.service import Service
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentResolveRequest
from app.services.audit_service import AuditService
from app.services.recovery_service import RecoveryService
from app.services.postmortem_service import PostmortemService
from app.core.exceptions import IncidentNotFoundException, RecoveryCriteriaNotMetException
from app.core.logging import logger


class IncidentService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
        self.recovery_service = RecoveryService(db)
        self.postmortem_service = PostmortemService(db)

    def create_incident(self, inc_in: IncidentCreate) -> Incident:
        """Creates a new incident and logs audit event."""
        # Find or create service reference
        service = self.db.get(Service, inc_in.service_id)
        if not service:
            service = self.db.scalars(select(Service).where(Service.name == inc_in.service_id)).first()

        service_id_to_use = service.id if service else inc_in.service_id

        incident = Incident(
            title=inc_in.title,
            severity=inc_in.severity.upper(),
            status=inc_in.status.upper(),
            service_id=service_id_to_use,
            environment=inc_in.environment,
            summary=inc_in.summary,
            root_cause=inc_in.root_cause,
            confidence=inc_in.confidence,
            metadata_json=inc_in.metadata_json,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)

        self.audit_service.record_audit_log(
            actor="SentinelAgent",
            action="CREATE_INCIDENT",
            target=f"Incident:{incident.id}",
            reason=f"Incident automatically created for {incident.title}",
            result="CREATED",
            metadata={"severity": incident.severity, "service_id": incident.service_id}
        )

        logger.info(
            f"INCIDENT CREATED: [{incident.id}] [{incident.severity}] {incident.title}",
            extra={"incident_id": incident.id, "service": incident.service_id}
        )
        return incident

    def get_incident(self, incident_id: str) -> Incident:
        incident = self.db.get(Incident, incident_id)
        if not incident:
            raise IncidentNotFoundException(incident_id)
        return incident

    def list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        service_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Incident]:
        stmt = select(Incident).order_by(desc(Incident.started_at)).limit(limit)
        if status:
            stmt = stmt.where(Incident.status == status.upper())
        if severity:
            stmt = stmt.where(Incident.severity == severity.upper())
        if service_id:
            stmt = stmt.where(Incident.service_id == service_id)
        return list(self.db.scalars(stmt).all())

    def update_incident(self, incident_id: str, inc_update: IncidentUpdate, actor: str = "system") -> Incident:
        incident = self.get_incident(incident_id)
        update_data = inc_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(incident, field, value)

        self.db.commit()
        self.db.refresh(incident)

        self.audit_service.record_audit_log(
            actor=actor,
            action="UPDATE_INCIDENT",
            target=f"Incident:{incident.id}",
            reason="Updated incident attributes",
            result="UPDATED",
            metadata={"updated_fields": list(update_data.keys())}
        )
        return incident

    async def resolve_incident(self, incident_id: str, resolve_in: IncidentResolveRequest) -> Incident:
        """
        Resolves an incident after verifying recovery criteria.
        Automatically generates postmortem upon resolution.
        """
        incident = self.get_incident(incident_id)

        # Enforce business rule: Incident resolution requires actual recovery verification unless forced
        if not resolve_in.force:
            recovery = self.recovery_service.verify_recovery(incident_id)
            if not recovery.is_recovered:
                logger.warning(f"Resolve attempted for {incident_id} but recovery criteria not met: {recovery.reason}")
                raise RecoveryCriteriaNotMetException(recovery.reason)

        incident.status = "RESOLVED"
        incident.resolved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(incident)

        self.audit_service.record_audit_log(
            actor=resolve_in.actor,
            action="RESOLVE_INCIDENT",
            target=f"Incident:{incident.id}",
            reason=resolve_in.reason or "Recovery verified",
            result="RESOLVED",
            metadata={"resolved_at": incident.resolved_at.isoformat()}
        )

        # Generate postmortem asynchronously / inline
        try:
            await self.postmortem_service.generate_and_store_postmortem(incident)
        except Exception as e:
            logger.error(f"Postmortem generation failed for incident {incident_id}: {str(e)}", exc_info=True)

        return incident
