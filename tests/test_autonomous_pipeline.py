"""Autonomous closed-loop pipeline: detection -> investigation -> remediation proposal.

These tests exercise the behaviour the product advertises: for a HIGH/CRITICAL incident,
posting an error event alone is enough to produce an RCA and pending remediation
proposals. No test here calls POST /incidents/{id}/investigate.

Execution is deliberately NOT covered as automatic — human approval still gates it.
"""
import asyncio
import json
import logging

import pytest
from fastapi.testclient import TestClient

from app.agents.fix_advisor import FixAdvisorAgent
from app.agents.investigator import InvestigatorAgent
from app.agents.response_planner import ResponsePlannerAgent
from app.core.config import settings
from app.models.incident import Incident
from app.schemas.investigation import (
    FIX_ADVISOR_DISCLAIMER,
    EvidenceItem,
    FixAdvisorGuidance,
    Hypothesis,
    RootCauseAnalysis,
)
from app.services.autonomous_response_service import run_autonomous_response
from app.services.remediation_service import RemediationService


def _register_deployment(client: TestClient, service: str, version: str, commit: str):
    res = client.post("/api/deployments", json={
        "service": service,
        "version": version,
        "commit_hash": commit,
        "environment": "production",
        "status": "SUCCESS",
    })
    assert res.status_code == 201


def _trigger_critical_incident(client: TestClient, service: str = "payment-service") -> str:
    """Post enough post-deployment errors to create a HIGH/CRITICAL incident.

    Returns the incident id, taken from the ingest response that created it.
    """
    _register_deployment(client, service, "v1.8.3", "a1b2c3d4e5f6")
    incident_id = None
    for i in range(7):
        res = client.post("/api/events", json={
            "service": service,
            "environment": "production",
            "level": "ERROR",
            "event_type": "http_500",
            "message": f"HTTP 500: DatabasePool timeout worker-{i}",
        })
        assert res.status_code == 200
        if res.json().get("incident_created"):
            incident_id = res.json()["incident_id"]
    assert incident_id, "Sentinel should have created an incident"
    return incident_id


# ---------------------------------------------------------------- auto-investigation


def test_high_severity_incident_auto_investigates_and_proposes(client: TestClient):
    """The headline behaviour: detection alone produces an RCA and pending proposals."""
    incident_id = _trigger_critical_incident(client)

    detail = client.get(f"/api/incidents/{incident_id}").json()
    assert detail["severity"] in ("HIGH", "CRITICAL")
    assert detail["root_cause"], "Investigator should have run without a manual trigger"
    assert detail["confidence"] in ("HIGH", "MEDIUM")

    actions = client.get(f"/api/actions?incident_id={incident_id}").json()
    assert actions, "Response Planner should have auto-proposed remediation actions"
    for action in actions:
        assert action["proposed_by"] == "ResponsePlannerAgent"
        assert action["approval_status"] == "PENDING", "nothing may auto-execute"
        assert action["type"] in settings.ALLOWED_OPERATIONAL_ACTIONS, (
            f"planner emitted non-allowlisted action type {action['type']!r}"
        )

    # The incident waits for a human; it must not have self-remediated.
    assert detail["status"] == "AWAITING_APPROVAL"


def test_medium_severity_incident_does_not_auto_investigate(client: TestClient):
    """The severity gate holds: a MEDIUM incident is left alone for a human."""
    # reporting-service is not in the critical-services set, so a repeated-stack-trace
    # incident yields MEDIUM. Four identical ERROR signatures trip REPEATED_STACK_TRACE
    # (threshold 4) while staying under HTTP_500_SPIKE (threshold 5).
    incident_id = None
    for _ in range(4):
        res = client.post("/api/events", json={
            "service": "reporting-service",
            "environment": "production",
            "level": "ERROR",
            "event_type": "error_log",
            "message": "NullPointerException at ReportBuilder.render",
            "signature": "NullPointerException:ReportBuilder.render",
        })
        assert res.status_code == 200
        if res.json().get("incident_created"):
            incident_id = res.json()["incident_id"]

    assert incident_id, "Sentinel should still detect the incident"
    detail = client.get(f"/api/incidents/{incident_id}").json()
    assert detail["severity"] == "MEDIUM"
    assert detail["root_cause"] is None, "MEDIUM must not auto-investigate"
    assert client.get(f"/api/actions?incident_id={incident_id}").json() == []


def test_webhook_ingest_also_auto_investigates(client: TestClient):
    """The APM/webhook ingest path gets the same autonomy as /api/events."""
    _register_deployment(client, "payment-service", "v1.8.3", "a1b2c3d4e5f6")
    incident_id = None
    for i in range(7):
        res = client.post("/api/webhooks/runtime-events", json={
            "service": "payment-service",
            "environment": "production",
            "level": "ERROR",
            "event_type": "http_500",
            "message": f"HTTP 500: DatabasePool timeout worker-{i}",
        })
        assert res.status_code == 200
        if res.json().get("incident_created"):
            incident_id = res.json()["incident_id"]

    assert incident_id
    assert client.get(f"/api/incidents/{incident_id}").json()["root_cause"]


def test_manual_investigate_after_auto_does_not_duplicate_actions(client: TestClient):
    """Re-investigating is safe: the manual endpoint never re-proposes actions."""
    incident_id = _trigger_critical_incident(client)
    before = client.get(f"/api/actions?incident_id={incident_id}").json()
    assert before

    res = client.post(f"/api/incidents/{incident_id}/investigate")
    assert res.status_code == 200

    after = client.get(f"/api/actions?incident_id={incident_id}").json()
    assert len(after) == len(before), "manual re-investigation must not double-propose"


def test_autonomous_run_gives_up_at_the_overall_timeout(client, db_session, monkeypatch):
    """A slow provider must not hold the ingest request open indefinitely.

    On timeout the incident has to read as awaiting triage, not as in-progress: the
    Investigator commits INVESTIGATING before it calls the model.
    """
    # Build a DETECTED incident without the auto path so we can drive it by hand.
    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", False)
    incident_id = _trigger_critical_incident(client)
    assert client.get(f"/api/incidents/{incident_id}").json()["status"] == "DETECTED"

    async def slow_investigation(self, iid):
        self.db.get(Incident, iid).status = "INVESTIGATING"  # mirrors investigator.py:44
        self.db.commit()
        await asyncio.sleep(30)

    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", True)
    monkeypatch.setattr(settings, "AUTO_RESPONSE_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(InvestigatorAgent, "investigate_incident", slow_investigation)

    result = asyncio.run(run_autonomous_response(incident_id, db_session))

    assert result is None, "a timed-out run must report failure rather than a partial RCA"
    detail = client.get(f"/api/incidents/{incident_id}").json()
    assert detail["status"] == "DETECTED", "a timed-out investigation must not look in progress"
    assert detail["root_cause"] is None
    assert client.get(f"/api/actions?incident_id={incident_id}").json() == []


def test_disclaimer_constant_is_the_single_source_of_truth():
    """Guards the fix for the Pydantic-internals lookup Robin flagged.

    The investigator normalises every piece of guidance against this constant, so it must
    stay identical to the schema default -- otherwise the safety invariant silently drifts.
    """
    assert "guidance only" in FIX_ADVISOR_DISCLAIMER.lower()
    assert FixAdvisorGuidance.model_fields["disclaimer"].default == FIX_ADVISOR_DISCLAIMER


def test_auto_investigation_can_be_disabled(client: TestClient, monkeypatch):
    """The whole chain is switchable off via config."""
    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", False)

    incident_id = _trigger_critical_incident(client)

    detail = client.get(f"/api/incidents/{incident_id}").json()
    assert detail["root_cause"] is None
    assert detail["status"] == "DETECTED"
    assert client.get(f"/api/actions?incident_id={incident_id}").json() == []


def test_autonomous_run_skips_an_incident_that_already_has_a_root_cause(
    client: TestClient, db_session, monkeypatch
):
    """Idempotency on the RCA, not just on the proposals.

    A retry (or a duplicate webhook delivery) must not pay for a second LLM call, nor
    overwrite a diagnosis somebody may already be acting on.
    """
    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", False)
    incident_id = _trigger_critical_incident(client)

    incident = db_session.get(Incident, incident_id)
    incident.root_cause = "already diagnosed by an earlier run"
    db_session.commit()

    called = []

    async def forbidden(self, iid):
        called.append(iid)
        raise AssertionError("the Investigator must not run when a root cause already exists")

    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", True)
    monkeypatch.setattr(InvestigatorAgent, "investigate_incident", forbidden)

    assert asyncio.run(run_autonomous_response(incident_id, db_session)) is None
    assert called == []
    assert db_session.get(Incident, incident_id).root_cause == "already diagnosed by an earlier run"


def test_a_failed_run_leaves_an_audit_row(client: TestClient, db_session, monkeypatch):
    """A swallowed failure must still be visible to an operator somewhere.

    The orchestrator never raises, so without this audit row a provider outage would
    leave no trace at all beyond a log line.
    """
    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", False)
    incident_id = _trigger_critical_incident(client)

    async def boom(self, iid):
        raise RuntimeError("provider exploded")

    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", True)
    monkeypatch.setattr(InvestigatorAgent, "investigate_incident", boom)

    assert asyncio.run(run_autonomous_response(incident_id, db_session)) is None

    rows = [
        row for row in client.get("/api/audit").json()
        if row["action"] == "AUTONOMOUS_RESPONSE" and row["result"] == "FAILED"
    ]
    assert rows, "a failed autonomous run must leave an audit trail"
    assert rows[0]["actor"] == "AutonomousPipeline"
    assert rows[0]["target"] == f"Incident:{incident_id}"
    assert "provider exploded" in json.dumps(rows[0]["metadata_json"])


def test_a_cancelled_run_still_resets_the_incident(client: TestClient, db_session, monkeypatch):
    """A client disconnect mid-run must not strand the incident looking in-progress.

    CancelledError derives from BaseException, so it bypasses the broad `except Exception`
    that performs the reset -- which is exactly why it needs a handler of its own.
    """
    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", False)
    incident_id = _trigger_critical_incident(client)

    async def slow_investigation(self, iid):
        self.db.get(Incident, iid).status = "INVESTIGATING"  # mirrors investigator.py:44
        self.db.commit()
        await asyncio.sleep(30)

    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", True)
    monkeypatch.setattr(InvestigatorAgent, "investigate_incident", slow_investigation)

    async def start_then_cancel():
        task = asyncio.ensure_future(run_autonomous_response(incident_id, db_session))
        await asyncio.sleep(0.05)  # let it get past the gates into the investigation
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(start_then_cancel())

    assert client.get(f"/api/incidents/{incident_id}").json()["status"] == "DETECTED"


def test_the_logged_proposal_count_excludes_rejected_options(client: TestClient, db_session, monkeypatch):
    """The summary line must count proposals that were actually created.

    It logged len(options), so a run where every proposal was rejected still reported
    three successes -- the log said the opposite of what happened.
    """
    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", False)
    incident_id = _trigger_critical_incident(client)

    original = RemediationService.create_action_proposal

    def reject_rollback(self, action_in):
        if action_in.type == "rollback_deployment":
            raise RuntimeError("proposal rejected by the allowlist")
        return original(self, action_in)

    messages: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record):
            messages.append(record.getMessage())

    capture = _Capture()
    app_logger = logging.getLogger("incident_agent")
    app_logger.addHandler(capture)  # propagate is False, so the root handler would miss these

    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", True)
    monkeypatch.setattr(RemediationService, "create_action_proposal", reject_rollback)
    try:
        asyncio.run(run_autonomous_response(incident_id, db_session))
    finally:
        app_logger.removeHandler(capture)

    summary = [m for m in messages if "remediation option(s)" in m]
    assert summary, "the planner should report what it created"
    assert "2/3" in summary[0], f"expected 2 of 3 creations, got: {summary[0]}"

    created = client.get(f"/api/actions?incident_id={incident_id}").json()
    assert len(created) == 2


# ------------------------------------------------------------------- planner contract


def test_planner_emits_only_allowlisted_action_types(client: TestClient):
    """The planner's output must survive the allowlist that gates action creation.

    This is the regression guard for the bug where the planner emitted ROLLBACK /
    DISABLE_FEATURE while the allowlist required rollback_deployment /
    disable_feature_flag, so two of its three options were rejected.
    """
    rca = RootCauseAnalysis(
        summary="Connection pool exhaustion",
        primary_hypothesis=Hypothesis(
            cause="Maximum pool size reduced from 50 to 2",
            confidence="HIGH",
            explanation="Pool saturation under concurrent load.",
            evidence=[EvidenceItem(type="log", reference="evt-1", explanation="timeouts")],
        ),
    )

    options = ResponsePlannerAgent().plan_remediation_options(rca, "payment-service", "v1.8.3")
    assert options
    for option in options:
        assert option.type in settings.ALLOWED_OPERATIONAL_ACTIONS, (
            f"planner emitted {option.type!r}, which the allowlist would reject"
        )

    # And prove it end to end: every option must be accepted by the proposal service.
    svc = client.post("/api/services", json={"name": "planner-check", "environment": "production"}).json()
    incident = client.post("/api/incidents", json={
        "title": "planner contract check",
        "service_id": svc["id"],
        "severity": "HIGH",
        "status": "DETECTED",
    })
    incident_id = incident.json()["id"]

    for option in options:
        res = client.post(f"/api/incidents/{incident_id}/actions", json={
            "incident_id": incident_id,
            "type": option.type,
            "risk_level": option.risk_level,
            "proposed_by": "ResponsePlannerAgent",
            "reason": option.reason,
            "expected_impact": option.expected_impact,
            "rollback_path": option.rollback_path,
        })
        assert res.status_code == 201, f"{option.type} rejected: {res.text}"


# ------------------------------------------------------------------ fix advisor revival


def test_fix_advisor_fallback_keeps_safety_disclaimer():
    """The revived Fix Advisor path must always carry the guidance-only disclaimer."""
    guidance = asyncio.run(
        FixAdvisorAgent().generate_fix_guidance(
            service_name="payment-service",
            root_cause="Connection pool size set to 2",
        )
    )
    assert "guidance only" in guidance.disclaimer.lower()
