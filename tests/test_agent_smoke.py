"""One end-to-end check per agent.

Each test drives a single agent through its real public entry point and asserts the
contract the product advertises for that agent, so a regression is attributed to the
agent that broke rather than to the pipeline as a whole.

Run with the mock LLM provider (forced by conftest), so these are offline and
deterministic. The agents that sit on the LLM path are additionally exercised against
the real provider by scripts/run_incident_demo.py.
"""
import asyncio

from app.agents.codeguard import CodeGuardAgent
from app.agents.fix_advisor import FixAdvisorAgent
from app.agents.investigator import InvestigatorAgent
from app.agents.response_planner import ResponsePlannerAgent
from app.agents.sentinel import SentinelAgent
from app.core.config import settings
from app.models.incident import Incident
from app.rules.action_allowlist import is_approval_required
from app.schemas.code_review import StagedReviewRequest
from app.schemas.event import EventCreate
from app.schemas.investigation import (
    FIX_ADVISOR_DISCLAIMER,
    EvidenceItem,
    Hypothesis,
    RootCauseAnalysis,
)

POOL_REGRESSION_DIFF = """diff --git a/src/main/java/com/company/payment/config/DatabasePool.java b/src/main/java/com/company/payment/config/DatabasePool.java
--- a/src/main/java/com/company/payment/config/DatabasePool.java
+++ b/src/main/java/com/company/payment/config/DatabasePool.java
@@ -42,6 +42,6 @@ public class DatabasePool {
-    config.setMaximumPoolSize(50);
-    config.setConnectionTimeout(30000);
+    config.setMaximumPoolSize(2);
+    config.setConnectionTimeout(1000);
"""

SECRET_DIFF = """diff --git a/src/settings.py b/src/settings.py
--- a/src/settings.py
+++ b/src/settings.py
@@ -1,2 +1,3 @@
+AWS_SECRET_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
"""


# ---------------------------------------------------------------------- Sentinel


def test_sentinel_agent_detects_a_spike_and_merges_later_events(db_session):
    """Sentinel is the only fully deterministic agent; it must work with no LLM at all."""
    agent = SentinelAgent(db_session)
    incident_id = None
    for i in range(7):
        resp = agent.process_event(EventCreate(
            service="smoke-sentinel",
            environment="production",
            level="ERROR",
            event_type="http_500",
            message=f"HTTP 500: DatabasePool timeout worker-{i}",
        ))
        if resp.incident_created:
            incident_id = resp.incident_id

    assert incident_id, "Sentinel should raise an incident on a 500 spike"
    incident = db_session.get(Incident, incident_id)
    assert incident.severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert resp.reason, "the trigger reason should be explained"

    # A later event must attach to the active incident rather than open a second one.
    follow_up = agent.process_event(EventCreate(
        service="smoke-sentinel",
        environment="production",
        level="ERROR",
        event_type="http_500",
        message="HTTP 500: DatabasePool timeout worker-late",
    ))
    assert follow_up.incident_created is False
    assert follow_up.incident_id == incident_id


# --------------------------------------------------------------------- CodeGuard


def test_codeguard_agent_blocks_a_hardcoded_secret(db_session):
    """A BLOCK finding must veto the commit; that is the pre-commit hook's whole purpose."""
    result = asyncio.run(CodeGuardAgent(db_session).review_staged_diff(StagedReviewRequest(
        diff=SECRET_DIFF, commit_hash="smoke-secret", author="smoke@test.local",
    )))

    assert result.decision == "BLOCK"
    assert result.can_commit is False
    assert any(f.metadata_json.get("rule_id") == "SEC-SECRETS-001" for f in result.findings)


def test_codeguard_agent_warns_on_the_pool_regression(db_session):
    """The regression this product demos must be caught deterministically, without the LLM."""
    result = asyncio.run(CodeGuardAgent(db_session).review_staged_diff(StagedReviewRequest(
        diff=POOL_REGRESSION_DIFF, commit_hash="smoke-pool", author="smoke@test.local",
    )))

    assert any(f.metadata_json.get("rule_id") == "PERF-DB-POOL-002" for f in result.findings)
    assert result.decision == "WARN", "a warning still allows the commit"
    assert result.can_commit is True
    assert result.can_commit is (result.decision != "BLOCK")


# ------------------------------------------------------------------ Investigator


def _raise_incident(client, service: str = "smoke-investigator") -> str:
    client.post("/api/deployments", json={
        "service": service, "version": "v1.0.0", "commit_hash": "beef1234567",
        "environment": "production", "status": "SUCCESS",
    })
    incident_id = None
    for i in range(7):
        res = client.post("/api/events", json={
            "service": service, "environment": "production", "level": "ERROR",
            "event_type": "http_500", "message": f"HTTP 500: DatabasePool timeout worker-{i}",
        })
        if res.json().get("incident_created"):
            incident_id = res.json()["incident_id"]
    assert incident_id
    return incident_id


def test_investigator_agent_produces_a_full_rca(client, db_session, monkeypatch):
    """Investigation must attach the deterministic blast radius and normalised guidance."""
    # Suppress the auto path so this exercises the agent directly, not the orchestrator.
    monkeypatch.setattr(settings, "AUTO_INVESTIGATE_ON_INCIDENT", False)
    incident_id = _raise_incident(client)

    result = asyncio.run(InvestigatorAgent(db_session).investigate_incident(incident_id))
    rca = result.rca

    assert rca.summary
    assert rca.primary_hypothesis.cause
    assert rca.primary_hypothesis.confidence in ("HIGH", "MEDIUM", "LOW")
    assert rca.blast_radius is not None, "blast radius is computed deterministically, not by the LLM"
    assert rca.affected_services
    assert rca.fix_guidance is not None, "the Fix Advisor fallback must guarantee guidance"
    assert rca.fix_guidance.disclaimer == FIX_ADVISOR_DISCLAIMER

    incident = db_session.get(Incident, incident_id)
    assert incident.root_cause, "the RCA must be persisted onto the incident"


# --------------------------------------------------------------- Response Planner


def test_response_planner_agent_emits_only_allowlisted_options():
    """The planner is pure and synchronous, so it needs no DB and no LLM."""
    rca = RootCauseAnalysis(
        summary="Connection pool exhaustion",
        primary_hypothesis=Hypothesis(
            cause="Maximum pool size reduced from 50 to 2",
            confidence="HIGH",
            explanation="Pool saturation under concurrent load.",
            evidence=[EvidenceItem(type="log", reference="evt-1", explanation="timeouts")],
        ),
    )

    options = ResponsePlannerAgent().plan_remediation_options(rca, "payment-service", "v1.0.0")

    assert options
    assert {o.type for o in options} <= set(settings.ALLOWED_OPERATIONAL_ACTIONS)
    assert all(o.reason and o.expected_impact and o.rollback_path for o in options)
    # The approval the planner advertises must match what execution actually enforces,
    # otherwise the UI promises a human gate that RemediationService does not apply.
    for option in options:
        assert option.requires_approval == is_approval_required(option.risk_level)


def test_low_risk_actions_execute_without_human_approval(client, db_session):
    """Pins the current approval policy, which is narrower than "approval is mandatory".

    `validate_action_approval` only gates MEDIUM/HIGH/CRITICAL (rules/action_allowlist.py:24).
    The autonomous planner auto-proposes restart_service and disable_feature_flag as LOW
    risk, so those reach EXECUTED straight from PENDING with no human sign-off. That is
    deliberate, but it is the one place the README's human-approval claim does not hold --
    pinned here so nobody changes the posture by accident.
    """
    service = client.post("/api/services", json={
        "name": "smoke-low-risk", "environment": "production",
    }).json()
    incident = client.post("/api/incidents", json={
        "title": "low risk gate check", "service_id": service["id"],
        "severity": "HIGH", "status": "DETECTED",
    }).json()

    action = client.post(f"/api/incidents/{incident['id']}/actions", json={
        "incident_id": incident["id"],
        "type": "restart_service",
        "risk_level": "LOW",
        "proposed_by": "ResponsePlannerAgent",
        "reason": "flush degraded handles",
        "expected_impact": "transient relief",
        "rollback_path": "none required",
    })
    assert action.status_code == 201, action.text
    action_id = action.json()["id"]
    assert action.json()["approval_status"] == "PENDING"

    executed = client.post(f"/api/actions/{action_id}/execute", json={"actor": "anyone@test.local"})

    assert executed.status_code == 200, (
        "LOW risk currently needs no approval; if this now 403s the policy was tightened"
    )
    assert executed.json()["approval_status"] == "EXECUTED"


# -------------------------------------------------------------------- Fix Advisor


def test_fix_advisor_agent_returns_actionable_guidance():
    """Guidance must be actionable *and* carry the no-code-modification invariant."""
    guidance = asyncio.run(FixAdvisorAgent().generate_fix_guidance(
        service_name="payment-service",
        root_cause="Connection pool max size reduced to 2",
        commit_hash="beef1234567",
    ))

    assert guidance.repository
    assert guidance.file
    assert guidance.problem
    assert guidance.why
    assert guidance.recommended_change
    assert guidance.expected_behavior
    assert guidance.validation_steps, "a developer needs steps to verify the fix"
    assert guidance.disclaimer == FIX_ADVISOR_DISCLAIMER
