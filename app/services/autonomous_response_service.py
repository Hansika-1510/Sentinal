"""Autonomous closed-loop response orchestrator.

Sentinel already detects incidents on its own. This service is what makes the stages
*after* detection run without a human calling `POST /incidents/{id}/investigate`:
investigation, then remediation proposal.

Execution is deliberately NOT automated. A MEDIUM/HIGH risk action still requires an
explicit human approval before `execute_action` will run it.
"""
import asyncio
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.investigator import InvestigatorAgent
from app.agents.response_planner import ResponsePlannerAgent
from app.core.config import settings
from app.core.logging import logger
from app.models.action import Action
from app.models.incident import Incident
from app.schemas.action import ActionCreate
from app.schemas.investigation import InvestigationResult, RootCauseAnalysis
from app.services.audit_service import AuditService
from app.services.deployment_service import DeploymentService
from app.services.remediation_service import RemediationService

#: Actor recorded on audit rows and on planner-authored action proposals.
AUTONOMOUS_ACTOR = "AutonomousPipeline"
#: Identity stamped on actions this orchestrator proposes. Also the idempotency key:
#: we never auto-propose twice for the same incident.
_PLANNER_ACTOR = "ResponsePlannerAgent"


def should_auto_investigate(severity: Optional[str]) -> bool:
    """Whether this incident severity is configured to auto-investigate.

    Severity is computed deterministically by Sentinel before any LLM call, so gating
    here is what keeps automatic investigation from spending money on every blip.
    Reads settings at call time so tests can monkeypatch it.
    """
    allowed = {s.strip().upper() for s in settings.AUTO_INVESTIGATE_SEVERITIES}
    return (severity or "").strip().upper() in allowed


async def run_autonomous_response(incident_id: str, db: Session) -> Optional[InvestigationResult]:
    """Investigate a freshly created incident and propose remediation, unattended.

    Called inline from the ingest routes with the request's own DB session, so any
    caller (including tests) observes the effect immediately on the same session.

    Never raises: an LLM or planner failure must not turn a successful event ingest
    into a 5xx. The incident is reset to DETECTED for a human to investigate manually.
    The whole run is bounded by AUTO_RESPONSE_TIMEOUT_SECONDS.
    """
    try:
        if not settings.AUTO_INVESTIGATE_ON_INCIDENT:
            return None

        incident = db.get(Incident, incident_id)
        if incident is None:
            return None

        if not should_auto_investigate(incident.severity):
            logger.info(
                f"Autonomous pipeline skipped incident {incident_id}: "
                f"severity {incident.severity} is not in {settings.AUTO_INVESTIGATE_SEVERITIES}"
            )
            return None

        # Idempotency: if a root cause is already recorded, someone (or a retry) already
        # investigated this incident.
        if incident.root_cause:
            return None

        result = await asyncio.wait_for(
            InvestigatorAgent(db).investigate_incident(incident_id),
            timeout=settings.AUTO_RESPONSE_TIMEOUT_SECONDS,
        )

        if settings.AUTO_PROPOSE_REMEDIATION:
            _propose_remediation_from_rca(db, incident, result.rca)

        return result

    except Exception as exc:  # noqa: BLE001 - deliberate: ingest must survive this
        logger.error(
            f"Autonomous response failed for incident {incident_id}: {exc}", exc_info=True
        )
        _reset_to_detected(db, incident_id)
        _record_failure(db, incident_id, exc)
        return None


def _propose_remediation_from_rca(db: Session, incident: Incident, rca: RootCauseAnalysis) -> None:
    """Turn the RCA into pending Action rows via the Response Planner.

    Synchronous throughout: the planner is pure, and RemediationService is sync. Only
    the investigation call above is awaited.
    """
    # Idempotency guard: never double-propose for the same incident.
    already_proposed = db.scalars(
        select(Action).where(
            Action.incident_id == incident.id,
            Action.proposed_by == _PLANNER_ACTOR,
        )
    ).first()
    if already_proposed:
        return

    service_name = incident.service.name if incident.service else incident.service_id
    deployments = DeploymentService(db).get_recent_deployments_for_service(service_name, limit=1)
    deployment_version = deployments[0].version if deployments else None

    options = ResponsePlannerAgent().plan_remediation_options(rca, service_name, deployment_version)
    remediation_service = RemediationService(db)

    for option in options:
        try:
            remediation_service.create_action_proposal(ActionCreate(
                incident_id=incident.id,
                type=option.type,
                risk_level=option.risk_level,
                proposed_by=_PLANNER_ACTOR,
                reason=option.reason,
                expected_impact=option.expected_impact,
                rollback_path=option.rollback_path,
                metadata_json={
                    "service": service_name,
                    "target_version": deployment_version,
                    "auto_proposed": True,
                    # RemediationOption carries these but Action has no column for them;
                    # park them in result_json rather than dropping them.
                    "possible_side_effects": option.possible_side_effects,
                    "evidence": [e.model_dump() for e in option.evidence],
                },
            ))
        except Exception as exc:  # noqa: BLE001 - one bad option must not abort the rest
            logger.warning(
                f"Autonomous planner option '{option.type}' for incident {incident.id} "
                f"could not be proposed: {exc}"
            )

    logger.info(
        f"Autonomous planner proposed {len(options)} remediation option(s) for incident {incident.id}"
    )


def _reset_to_detected(db: Session, incident_id: str) -> None:
    """Return a failed investigation to a state that reads as 'awaiting triage'.

    The Investigator commits INVESTIGATING before it calls the model (investigator.py:44),
    so a timeout or provider failure would otherwise strand the incident looking like
    somebody is still working on it. Best-effort: never raises.
    """
    try:
        incident = db.get(Incident, incident_id)
        if incident is not None and not incident.root_cause and incident.status == "INVESTIGATING":
            incident.status = "DETECTED"
            db.commit()
            logger.info(f"Incident {incident_id} reset to DETECTED after a failed autonomous run")
    except Exception as exc:  # noqa: BLE001 - cleanup must not mask the original failure
        logger.warning(f"Could not reset incident {incident_id} to DETECTED: {exc}")


def _record_failure(db: Session, incident_id: str, exc: Exception) -> None:
    """Best-effort audit trail for a failed autonomous run. Never raises."""
    try:
        AuditService(db).record_audit_log(
            actor=AUTONOMOUS_ACTOR,
            action="AUTONOMOUS_RESPONSE",
            target=f"Incident:{incident_id}",
            reason="Autonomous investigation/proposal failed; incident left for manual triage.",
            result="FAILED",
            metadata={"error": str(exc)},
        )
    except Exception as audit_exc:  # noqa: BLE001
        logger.error(f"Could not record autonomous failure audit for {incident_id}: {audit_exc}")
