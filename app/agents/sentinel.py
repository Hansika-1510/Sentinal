from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.event import Event
from app.models.incident import Incident
from app.models.service import Service
from app.schemas.event import EventCreate, EventIngestResponse, EventRead
from app.schemas.incident import IncidentCreate
from app.services.event_service import EventService
from app.services.deployment_service import DeploymentService
from app.services.incident_service import IncidentService
from app.rules.anomaly_rules import evaluate_all_rules, AnomalyDetectionResult
from app.rules.severity_rules import calculate_severity
from app.core.logging import logger


class SentinelAgent:
    """
    Sentinel Agent: Deterministic runtime event monitoring and anomaly detection engine.
    Detects error spikes, correlates with recent deployments, and automatically triggers incidents.
    """

    def __init__(self, db: Session):
        self.db = db
        self.event_service = EventService(db)
        self.deployment_service = DeploymentService(db)
        self.incident_service = IncidentService(db)

    def process_event(self, event_in: EventCreate) -> EventIngestResponse:
        """
        Ingests a runtime event and deterministically evaluates incident conditions.
        """
        # 1. Normalize and store event
        event = self.event_service.record_event(event_in)

        # 2. Check for active (unresolved) incident on this service
        active_incident = self._find_active_incident_for_service(event.service)
        if active_incident:
            # Associate event with active incident
            event.incident_id = active_incident.id
            self.db.commit()
            return EventIngestResponse(
                event=EventRead.model_validate(event),
                incident_created=False,
                incident_id=active_incident.id,
                reason=f"Linked to active incident {active_incident.id}"
            )

        # 3. Fetch recent events and deployments for this service
        recent_events = self.event_service.get_recent_events_for_service(event.service, window_seconds=600)
        recent_deployments = self.deployment_service.get_recent_deployments_for_service(event.service, limit=3)

        # 4. Deterministic rule evaluation
        anomaly_result: Optional[AnomalyDetectionResult] = evaluate_all_rules(recent_events, recent_deployments)

        if anomaly_result and anomaly_result.is_anomaly:
            # Calculate deterministic severity
            severity = calculate_severity(
                service_name=event.service,
                rule_name=anomaly_result.rule_name,
                matched_events=anomaly_result.matched_events
            )

            # Ensure service exists in Service catalog
            service_record = self.db.scalars(select(Service).where(Service.name == event.service)).first()
            if not service_record:
                service_record = Service(
                    name=event.service,
                    environment=event.environment,
                    description=f"Auto-discovered service for {event.service}",
                    dependencies=[]
                )
                self.db.add(service_record)
                self.db.commit()
                self.db.refresh(service_record)

            # 5. Automatically create Incident
            title = f"{event.service.upper()}: {anomaly_result.rule_name.replace('_', ' ').title()}"
            incident_create = IncidentCreate(
                title=title,
                service_id=service_record.id,
                environment=event.environment,
                severity=severity,
                status="DETECTED",
                summary=anomaly_result.reason,
                metadata_json={
                    "triggered_by_rule": anomaly_result.rule_name,
                    "confidence": anomaly_result.confidence,
                    "triggering_event_id": event.id,
                    "event_signature": event.signature
                }
            )
            incident = self.incident_service.create_incident(incident_create)

            # Associate matched events with newly created incident
            for ev in anomaly_result.matched_events:
                ev.incident_id = incident.id
            event.incident_id = incident.id
            self.db.commit()

            logger.info(
                f"Sentinel triggered new incident {incident.id} for {event.service} via rule {anomaly_result.rule_name}",
                extra={"incident_id": incident.id, "service": event.service}
            )

            return EventIngestResponse(
                event=EventRead.model_validate(event),
                incident_created=True,
                incident_id=incident.id,
                reason=anomaly_result.reason
            )

        return EventIngestResponse(
            event=EventRead.model_validate(event),
            incident_created=False,
            incident_id=None,
            reason="Event ingested. Anomaly thresholds not breached."
        )

    def _find_active_incident_for_service(self, service_name: str) -> Optional[Incident]:
        """Finds any active (non-resolved, non-rejected) incident for the given service."""
        active_statuses = ["DETECTED", "TRIAGED", "INVESTIGATING", "AWAITING_APPROVAL", "MITIGATING", "MONITORING"]
        
        service_record = self.db.scalars(select(Service).where(Service.name == service_name)).first()
        service_id = service_record.id if service_record else service_name

        stmt = (
            select(Incident)
            .where((Incident.service_id == service_id) | (Incident.service_id == service_name))
            .where(Incident.status.in_(active_statuses))
            .order_by(Incident.started_at.desc())
        )
        return self.db.scalars(stmt).first()
