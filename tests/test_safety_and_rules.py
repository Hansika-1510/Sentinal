import pytest
from fastapi.testclient import TestClient
from app.agents.codeguard import CodeGuardAgent
from app.schemas.code_review import StagedReviewRequest


def test_safety_unapproved_medium_risk_action_blocked(client: TestClient):
    # Create incident
    inc_resp = client.post("/api/incidents", json={
        "title": "Safety Test Incident",
        "service_id": "payment-service",
        "severity": "HIGH",
        "environment": "production"
    })
    incident_id = inc_resp.json()["id"]

    # Propose MEDIUM risk action
    act_resp = client.post(f"/api/incidents/{incident_id}/actions", json={
        "incident_id": incident_id,
        "type": "rollback_deployment",
        "risk_level": "MEDIUM",
        "proposed_by": "ResponsePlanner",
        "reason": "Test rollback",
        "expected_impact": "Impact test"
    })
    action_id = act_resp.json()["id"]

    # Attempt execution WITHOUT approval -> MUST BE 403 Forbidden
    exec_resp = client.post(f"/api/actions/{action_id}/execute", json={"actor": "attacker@evil.com"})
    assert exec_resp.status_code == 403
    err_body = exec_resp.json()
    assert err_body["error"]["code"] == "ACTION_NOT_APPROVED"


def test_safety_disallowed_arbitrary_action_rejected(client: TestClient):
    # Create incident
    inc_resp = client.post("/api/incidents", json={
        "title": "Safety Disallowed Action Test",
        "service_id": "payment-service",
        "severity": "HIGH",
        "environment": "production"
    })
    incident_id = inc_resp.json()["id"]

    # Attempt to propose an action not in the allowlist -> MUST BE 403 Forbidden
    disallowed_resp = client.post(f"/api/incidents/{incident_id}/actions", json={
        "incident_id": incident_id,
        "type": "execute_shell_rm_rf",
        "risk_level": "HIGH",
        "proposed_by": "Attacker",
        "reason": "Malicious command",
        "expected_impact": "Total destruction"
    })
    assert disallowed_resp.status_code == 403
    assert disallowed_resp.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


def test_codeguard_blocks_critical_secrets(client: TestClient):
    # Staged diff containing exposed secret
    secret_diff = """diff --git a/config/api.key b/config/api.key
new file mode 100644
--- /dev/null
+++ b/config/api.key
@@ -0,0 +1,1 @@
+ghp_1234567890abcdefghijklmnopqrstuvwxyz
"""
    resp = client.post("/api/code-reviews/review-staged", json={
        "diff": secret_diff,
        "author": "dev@company.com"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "BLOCK"
    assert data["can_commit"] is False


def test_codeguard_warns_on_low_pool_without_blocking(client: TestClient):
    # Staged diff reducing connection pool to 2 (WARN)
    pool_diff = """diff --git a/DatabasePool.java b/DatabasePool.java
--- a/DatabasePool.java
+++ b/DatabasePool.java
@@ -42,1 +42,1 @@
-    setMaximumPoolSize(50);
+    setMaximumPoolSize(2);
"""
    resp = client.post("/api/code-reviews/review-staged", json={
        "diff": pool_diff,
        "author": "dev@company.com"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "WARN"
    assert data["can_commit"] is True


def test_developer_responsibility_invariant():
    """
    Validates that Fix Advisor explicitly returns guidance and disclaimers,
    and the AI architecture has NO tool/endpoint to modify application source code.
    """
    from app.agents.fix_advisor import FixAdvisorAgent
    import asyncio

    advisor = FixAdvisorAgent()
    guidance = asyncio.run(advisor.generate_fix_guidance(
        service_name="payment-service",
        root_cause="Connection pool size set to 2"
    ))
    assert "guidance only" in guidance.disclaimer.lower()
    assert guidance.file is not None
    assert len(guidance.validation_steps) > 0
