import pytest
from fastapi.testclient import TestClient


def test_full_end_to_end_incident_lifecycle(client: TestClient):
    """
    Final End-to-End Acceptance Test:
    Validates the entire closed-loop incident lifecycle through the REST API.
    """
    # 0. Setup Services
    client.post("/api/services", json={
        "name": "payment-service",
        "environment": "production",
        "description": "Payment microservice",
        "dependencies": ["postgres-db", "stripe-api"]
    })
    client.post("/api/services", json={
        "name": "order-service",
        "environment": "production",
        "description": "Order microservice",
        "dependencies": ["payment-service"]
    })

    # 1. Developer modifies code & CodeGuard checks diff
    staged_diff = """diff --git a/DatabasePool.java b/DatabasePool.java
--- a/DatabasePool.java
+++ b/DatabasePool.java
@@ -42,1 +42,1 @@
-    setMaximumPoolSize(50);
+    setMaximumPoolSize(2);
"""
    review_res = client.post("/api/code-reviews/review-staged", json={
        "diff": staged_diff,
        "author": "developer@company.com"
    })
    assert review_res.status_code == 200
    assert review_res.json()["can_commit"] is True

    # 2. Deployment registered (v1.8.3)
    dep_res = client.post("/api/deployments", json={
        "service": "payment-service",
        "version": "v1.8.3",
        "commit_hash": "a1b2c3d4e5f6",
        "environment": "production",
        "status": "SUCCESS"
    })
    assert dep_res.status_code == 201

    # 3. Sentinel receives runtime error events and auto-creates incident
    incident_id = None
    for i in range(7):
        ev_res = client.post("/api/events", json={
            "service": "payment-service",
            "environment": "production",
            "level": "ERROR",
            "event_type": "http_500",
            "message": f"HTTP 500: DatabasePool timeout worker-{i}"
        })
        assert ev_res.status_code == 200
        if ev_res.json().get("incident_id"):
            incident_id = ev_res.json()["incident_id"]

    assert incident_id is not None, "Sentinel should have triggered incident on error spike"

    # 4. Investigator Agent runs investigation & generates RCA
    inv_res = client.post(f"/api/incidents/{incident_id}/investigate")
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    rca = inv_data["rca"]

    # Verify RCA contains evidence-backed primary hypothesis
    assert rca["primary_hypothesis"]["confidence"] in ["HIGH", "MEDIUM"]
    assert len(rca["primary_hypothesis"]["evidence"]) > 0

    # Verify Blast Radius
    assert rca["blast_radius"]["total_affected_services"] >= 1
    assert "payment-service" in [n["service_name"] for n in rca["blast_radius"]["direct_impact"]]

    # Verify Fix Advisor guidance
    assert rca["fix_guidance"] is not None
    assert "guidance only" in rca["fix_guidance"]["disclaimer"].lower()

    # 5. Propose Remediation Action
    act_res = client.post(f"/api/incidents/{incident_id}/actions", json={
        "incident_id": incident_id,
        "type": "rollback_deployment",
        "risk_level": "MEDIUM",
        "proposed_by": "ResponsePlannerAgent",
        "reason": "Rollback v1.8.3 to restore connection pool capacity",
        "expected_impact": "Restores DB pool to 50 connections",
        "metadata_json": {"service": "payment-service", "target_version": "v1.8.2"}
    })
    assert act_res.status_code == 201
    action_id = act_res.json()["id"]

    # 6. Safety Verification: Unapproved execution blocked
    unapproved_exec = client.post(f"/api/actions/{action_id}/execute", json={"actor": "operator@company.com"})
    assert unapproved_exec.status_code == 403

    # 7. Human Approves Action
    app_res = client.post(f"/api/actions/{action_id}/approve", json={
        "actor": "alice@company.com",
        "reason": "RCA confirmed DB pool regression in v1.8.3"
    })
    assert app_res.status_code == 200
    assert app_res.json()["approval_status"] == "APPROVED"

    # 8. Operational Action Executes
    exec_res = client.post(f"/api/actions/{action_id}/execute", json={"actor": "alice@company.com"})
    assert exec_res.status_code == 200
    assert exec_res.json()["approval_status"] == "EXECUTED"

    # 9. Sentinel Recovery Monitoring (healthy events recorded)
    for _ in range(5):
        client.post("/api/events", json={
            "service": "payment-service",
            "level": "INFO",
            "event_type": "health_check",
            "message": "Health check 200 OK"
        })

    # 10. Resolve Incident with recovery verification
    resolve_res = client.post(f"/api/incidents/{incident_id}/resolve", json={
        "actor": "alice@company.com",
        "reason": "Sentinel verified healthy error rate"
    })
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"

    # 11. Postmortem Generated & Stored
    pm_res = client.get(f"/api/incidents/{incident_id}/postmortem")
    assert pm_res.status_code == 200
    pm_data = pm_res.json()
    assert pm_data["incident_id"] == incident_id
    assert len(pm_data["lessons_learned"]) > 0

    # 12. Similar Historical Incidents Retrieval
    sim_res = client.get(f"/api/incidents/{incident_id}/similar")
    assert sim_res.status_code == 200
    assert isinstance(sim_res.json(), list)

    # 13. Audit Log Verification
    audit_res = client.get("/api/audit")
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 4
