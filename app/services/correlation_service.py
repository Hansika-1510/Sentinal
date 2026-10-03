from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.incident import Incident
from app.models.event import Event
from app.models.deployment import Deployment
from app.models.code_review import CodeReview
from app.models.action import Action
from app.schemas.incident import IncidentTimelineItem
from app.core.logging import logger


class CorrelationService:
    def __init__(self, db: Session):
        self.db = db

    def correlate_incident_context(self, incident: Incident) -> Dict[str, Any]:
        """
        Builds comprehensive chronological correlation connecting:
        Runtime Events -> Preceding Deployments -> Commits -> Code Reviews -> Historical Incidents.
        """
        service_name = incident.service.name if incident.service else incident.service_id

        # 1. Fetch recent deployments before or around incident start
        dep_stmt = (
            select(Deployment)
            .where(Deployment.service == service_name)
            .order_by(desc(Deployment.deployed_at))
            .limit(5)
        )
        recent_deployments = list(self.db.scalars(dep_stmt).all())
        latest_deployment = recent_deployments[0] if recent_deployments else None

        # 2. Fetch code reviews matching commit hash
        code_reviews: List[CodeReview] = []
        if latest_deployment:
            cr_stmt = select(CodeReview).where(CodeReview.commit_hash == latest_deployment.commit_hash)
            code_reviews = list(self.db.scalars(cr_stmt).all())

        # 3. Fetch runtime events linked to this incident or recent in service
        ev_stmt = (
            select(Event)
            .where((Event.incident_id == incident.id) | (Event.service == service_name))
            .order_by(desc(Event.timestamp))
            .limit(50)
        )
        events = list(self.db.scalars(ev_stmt).all())

        # 4. Fetch actions executed for this incident
        act_stmt = select(Action).where(Action.incident_id == incident.id).order_by(Action.created_at)
        actions = list(self.db.scalars(act_stmt).all())

        return {
            "incident": incident,
            "latest_deployment": latest_deployment,
            "recent_deployments": recent_deployments,
            "code_reviews": code_reviews,
            "events": events,
            "actions": actions
        }

    def build_chronological_timeline(self, incident_id: str) -> List[IncidentTimelineItem]:
        """
        Constructs a timeline of all events, explicitly labeling observed facts vs AI inferences.
        """
        incident = self.db.get(Incident, incident_id)
        if not incident:
            return []

        context = self.correlate_incident_context(incident)
        timeline: List[IncidentTimelineItem] = []

        # A. Deployments
        for dep in context["recent_deployments"]:
            timeline.append(IncidentTimelineItem(
                timestamp=dep.deployed_at,
                type="deployment",
                title=f"Deployment {dep.version} ({dep.status})",
                description=f"Deployed commit {dep.commit_hash[:7]} to {dep.environment}",
                is_observed=True,
                metadata={"version": dep.version, "commit_hash": dep.commit_hash, "status": dep.status}
            ))

        # B. Code reviews
        for cr in context["code_reviews"]:
            timeline.append(IncidentTimelineItem(
                timestamp=cr.created_at,
                type="code_review",
                title=f"Code Review [{cr.decision}] by {cr.tool}",
                description=f"{cr.finding} ({cr.file}:{cr.line or 'all'})",
                is_observed=True,
                metadata={"severity": cr.severity, "decision": cr.decision, "file": cr.file}
            ))

        # C. Incident detection
        timeline.append(IncidentTimelineItem(
            timestamp=incident.started_at,
            type="incident_detected",
            title=f"Incident {incident.id} Created ({incident.severity})",
            description=f"{incident.title} (Status: {incident.status})",
            is_observed=True,
            metadata={"severity": incident.severity, "status": incident.status}
        ))

        # D. Runtime Events (Top 10 sample)
        for ev in context["events"][:10]:
            timeline.append(IncidentTimelineItem(
                timestamp=ev.timestamp,
                type="runtime_event",
                title=f"[{ev.level}] {ev.event_type}",
                description=ev.message[:120],
                is_observed=True,
                metadata={"signature": ev.signature, "level": ev.level}
            ))

        # E. AI RCA & Hypotheses
        if incident.summary:
            timeline.append(IncidentTimelineItem(
                timestamp=incident.updated_at,
                type="investigation",
                title=f"AI RCA Generated (Confidence: {incident.confidence or 'MEDIUM'})",
                description=incident.summary[:150],
                is_observed=False,  # AI Inference
                metadata={"root_cause": incident.root_cause, "confidence": incident.confidence}
            ))

        # F. Operational Actions
        for act in context["actions"]:
            timeline.append(IncidentTimelineItem(
                timestamp=act.created_at,
                type="action_proposed",
                title=f"Action Proposed: {act.type} (Risk: {act.risk_level})",
                description=act.reason[:120],
                is_observed=False,  # AI Proposal
                metadata={"risk_level": act.risk_level, "approval_status": act.approval_status}
            ))
            if act.approved_at:
                timeline.append(IncidentTimelineItem(
                    timestamp=act.approved_at,
                    type="action_approved",
                    title=f"Action {act.id} APPROVED by {act.approved_by}",
                    description=f"Human authorization granted for {act.type}",
                    is_observed=True,
                    metadata={"approver": act.approved_by}
                ))
            if act.executed_at:
                timeline.append(IncidentTimelineItem(
                    timestamp=act.executed_at,
                    type="action_executed",
                    title=f"Action {act.id} EXECUTED",
                    description=act.result_json.get("message", "Executed"),
                    is_observed=True,
                    metadata={"result": act.result_json}
                ))

        # G. Resolution
        if incident.resolved_at:
            timeline.append(IncidentTimelineItem(
                timestamp=incident.resolved_at,
                type="resolved",
                title=f"Incident {incident.id} RESOLVED",
                description="Recovery verified by Sentinel monitoring. Incident closed.",
                is_observed=True,
                metadata={"status": "RESOLVED"}
            ))

        # Sort timeline chronologically
        timeline.sort(key=lambda item: item.timestamp)
        return timeline
