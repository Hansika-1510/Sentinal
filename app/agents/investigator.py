import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.incident import Incident
from app.schemas.investigation import (
    RootCauseAnalysis,
    InvestigationResult,
    Hypothesis,
    EvidenceItem
)
from app.services.correlation_service import CorrelationService
from app.services.blast_radius_service import BlastRadiusService
from app.services.incident_memory_service import IncidentMemoryService
from app.services.audit_service import AuditService
from app.integrations.llm import get_llm_provider
from app.core.logging import logger


class InvestigatorAgent:
    """
    Investigator Agent: Gathers evidence, runs causal correlation, queries historical incidents,
    computes blast radius, and synthesizes structured, evidence-backed Root Cause Analysis (RCA).
    """

    def __init__(self, db: Session):
        self.db = db
        self.correlation_service = CorrelationService(db)
        self.blast_radius_service = BlastRadiusService(db)
        self.memory_service = IncidentMemoryService(db)
        self.audit_service = AuditService(db)
        self.llm_provider = get_llm_provider()

    async def investigate_incident(self, incident_id: str) -> InvestigationResult:
        """Runs the end-to-end investigation pipeline on an incident."""
        incident = self.db.get(Incident, incident_id)
        if not incident:
            from app.core.exceptions import IncidentNotFoundException
            raise IncidentNotFoundException(incident_id)

        # Transition status to INVESTIGATING
        if incident.status in ["DETECTED", "TRIAGED"]:
            incident.status = "INVESTIGATING"
            self.db.commit()

        service_name = incident.service.name if incident.service else incident.service_id

        # 1. Correlate runtime events, deployments, commits, and code reviews
        context = self.correlation_service.correlate_incident_context(incident)
        latest_dep = context["latest_deployment"]
        code_reviews = context["code_reviews"]
        recent_events = context["events"]

        # 2. Query historical incident memory for similar incidents
        query_text = f"{incident.title} {service_name} {incident.summary or ''}"
        similar_memories = await self.memory_service.find_similar_incidents(query_text, top_k=2)
        similar_data = [
            {
                "incident_id": m.incident_id,
                "summary": m.summary,
                "symptoms": m.symptoms,
                "rca": m.rca,
                "resolution": m.resolution,
                "similarity": m.similarity_score
            }
            for m in similar_memories
        ]

        # 3. Calculate blast radius
        blast_report = self.blast_radius_service.calculate_blast_radius(service_name)

        # 4. Synthesize LLM prompt for structured Root Cause Analysis
        prompt = f"""
        Investigate software incident {incident.id}:
        Service: {service_name}
        Severity: {incident.severity}
        Title: {incident.title}
        Detection Summary: {incident.summary}
        
        Recent Deployment: {latest_dep.version if latest_dep else 'None'} (Commit: {latest_dep.commit_hash if latest_dep else 'N/A'})
        CodeGuard Findings: {[cr.finding for cr in code_reviews]}
        Recent Error Events Count: {len(recent_events)}
        Sample Logs: {[e.message for e in recent_events[:5]]}
        Similar Historical Incidents: {similar_data}
        Blast Radius Affected Services: {blast_report.total_affected_services}

        Provide a rigorous, evidence-backed Root Cause Analysis (RCA) with:
        - Primary hypothesis (cause, confidence: HIGH/MEDIUM/LOW, supporting evidence, explanation)
        - Alternative hypotheses
        - Affected services
        - Fix advisor guidance for developers (never directly modify code)
        - Recommended operational remediation actions with risk levels
        """

        rca: RootCauseAnalysis = await self.llm_provider.generate_structured(
            prompt=prompt,
            schema_class=RootCauseAnalysis,
            system_prompt="You are an expert Principal SRE and Root Cause Investigator. Base all hypotheses on concrete observed evidence. Never claim certainty without proof."
        )

        # Attach computed blast radius to ensure topology accuracy
        rca.blast_radius = blast_report
        if not rca.affected_services:
            rca.affected_services = [service_name]

        # 5. Persist RCA summary & root cause on Incident model
        incident.summary = rca.summary
        incident.root_cause = rca.primary_hypothesis.cause
        incident.confidence = rca.primary_hypothesis.confidence
        self.db.commit()

        # 6. Build timeline
        timeline_items = self.correlation_service.build_chronological_timeline(incident.id)
        timeline_summary = [
            {
                "timestamp": item.timestamp.isoformat(),
                "type": item.type,
                "title": item.title,
                "description": item.description,
                "is_observed": item.is_observed
            }
            for item in timeline_items
        ]

        self.audit_service.record_audit_log(
            actor="InvestigatorAgent",
            action="INVESTIGATE_INCIDENT",
            target=f"Incident:{incident.id}",
            reason="Investigation completed and RCA synthesized.",
            result="SUCCESS",
            metadata={
                "confidence": rca.primary_hypothesis.confidence,
                "primary_cause": rca.primary_hypothesis.cause[:100]
            }
        )

        logger.info(f"Investigation completed for {incident.id}: Cause='{rca.primary_hypothesis.cause[:60]}'")

        return InvestigationResult(
            incident_id=incident.id,
            status=incident.status,
            rca=rca,
            timeline_summary=timeline_summary,
            similar_historical_incidents=similar_data
        )
