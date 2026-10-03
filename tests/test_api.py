import pytest
from fastapi.testclient import TestClient


def test_health_and_ready(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_services_crud_and_topology(client: TestClient):
    # Create service
    svc_data = {
        "name": "payment-service",
        "environment": "production",
        "description": "Payment microservice",
        "dependencies": ["postgres-db"]
    }
    resp = client.post("/api/services", json=svc_data)
    assert resp.status_code == 201
    svc_id = resp.json()["id"]

    # List services
    resp = client.get("/api/services")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Get service by id
    resp = client.get(f"/api/services/{svc_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "payment-service"


def test_deployments_api(client: TestClient):
    dep_data = {
        "service": "payment-service",
        "version": "v1.8.3",
        "commit_hash": "a1b2c3d4e5f6",
        "environment": "production",
        "status": "SUCCESS"
    }
    resp = client.post("/api/deployments", json=dep_data)
    assert resp.status_code == 201
    assert resp.json()["version"] == "v1.8.3"

    resp = client.get("/api/deployments?service=payment-service")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_event_ingestion_and_sentinel_trigger(client: TestClient):
    # Register deployment first
    client.post("/api/deployments", json={
        "service": "payment-service",
        "version": "v1.8.3",
        "commit_hash": "a1b2c3d4e5f6",
        "environment": "production",
        "status": "SUCCESS"
    })

    # Ingest error events to trigger Sentinel anomaly
    incident_id = None
    for i in range(7):
        resp = client.post("/api/events", json={
            "service": "payment-service",
            "environment": "production",
            "level": "ERROR",
            "event_type": "http_500",
            "message": f"Connection pool exhausted worker-{i}"
        })
        assert resp.status_code == 200
        data = resp.json()
        if data.get("incident_id"):
            incident_id = data.get("incident_id")

    assert incident_id is not None

    # Get incident
    resp = client.get(f"/api/incidents/{incident_id}")
    assert resp.status_code == 200
    assert resp.json()["severity"] in ["HIGH", "CRITICAL"]


def test_incident_investigation_and_remediation_lifecycle(client: TestClient):
    # 1. Create incident manually or via events
    inc_resp = client.post("/api/incidents", json={
        "title": "Payment Service 500 Outage",
        "service_id": "payment-service",
        "severity": "CRITICAL",
        "status": "DETECTED",
        "environment": "production"
    })
    assert inc_resp.status_code == 201
    incident_id = inc_resp.json()["id"]

    # 2. Run investigation
    inv_resp = client.post(f"/api/incidents/{incident_id}/investigate")
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()
    assert "rca" in inv_data
    assert inv_data["rca"]["primary_hypothesis"]["confidence"] in ["HIGH", "MEDIUM"]
    assert len(inv_data["rca"]["primary_hypothesis"]["evidence"]) > 0

    # 3. Check timeline
    timeline_resp = client.get(f"/api/incidents/{incident_id}/timeline")
    assert timeline_resp.status_code == 200
    assert len(timeline_resp.json()) > 0

    # 4. Check blast radius
    blast_resp = client.get(f"/api/incidents/{incident_id}/blast-radius")
    assert blast_resp.status_code == 200
    assert blast_resp.json()["total_affected_services"] >= 1

    # 5. Propose operational action
    act_resp = client.post(f"/api/incidents/{incident_id}/actions", json={
        "incident_id": incident_id,
        "type": "rollback_deployment",
        "risk_level": "MEDIUM",
        "proposed_by": "ResponsePlanner",
        "reason": "Rollback to stable v1.8.2",
        "expected_impact": "Restores DB pool",
        "metadata_json": {"service": "payment-service", "target_version": "v1.8.2"}
    })
    assert act_resp.status_code == 201
    action_id = act_resp.json()["id"]
    assert act_resp.json()["approval_status"] == "PENDING"

    # 6. Approve action
    app_resp = client.post(f"/api/actions/{action_id}/approve", json={
        "actor": "alice@company.com",
        "reason": "Verified RCA"
    })
    assert app_resp.status_code == 200
    assert app_resp.json()["approval_status"] == "APPROVED"

    # 7. Execute action
    exec_resp = client.post(f"/api/actions/{action_id}/execute", json={
        "actor": "alice@company.com"
    })
    assert exec_resp.status_code == 200
    assert exec_resp.json()["approval_status"] == "EXECUTED"

    # 8. Feed healthy events
    for _ in range(4):
        client.post("/api/events", json={
            "service": "payment-service",
            "level": "INFO",
            "event_type": "health_check",
            "message": "Health check 200 OK"
        })

    # 9. Resolve incident
    res_resp = client.post(f"/api/incidents/{incident_id}/resolve", json={
        "actor": "alice@company.com",
        "reason": "Recovery verified"
    })
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"

    # 10. Fetch postmortem
    pm_resp = client.get(f"/api/incidents/{incident_id}/postmortem")
    assert pm_resp.status_code == 200
    assert pm_resp.json()["incident_id"] == incident_id

    # 11. Check audit log
    audit_resp = client.get("/api/audit")
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) >= 3
