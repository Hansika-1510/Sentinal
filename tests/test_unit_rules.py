import pytest
from datetime import datetime, timezone, timedelta
from app.models.event import Event
from app.models.deployment import Deployment
from app.rules.anomaly_rules import (
    check_http_500_spike,
    check_post_deployment_anomaly,
    check_health_check_failure,
    check_repeated_stack_trace,
    evaluate_all_rules
)
from app.rules.severity_rules import calculate_severity
from app.rules.action_allowlist import (
    validate_operational_action_allowed,
    validate_action_approval,
    is_approval_required
)
from app.core.exceptions import ActionNotAllowedException, ActionNotApprovedException


def test_severity_calculation():
    # Payment critical service with post deployment anomaly
    sev_crit = calculate_severity("payment-service", "POST_DEPLOYMENT_ANOMALY", [Event(level="ERROR")] * 5)
    assert sev_crit == "CRITICAL"

    # Health check consecutive failure is CRITICAL
    sev_hc = calculate_severity("order-service", "HEALTH_CHECK_CONSECUTIVE_FAILURE", [Event(level="ERROR")] * 2)
    assert sev_hc == "CRITICAL"

    # Standard medium severity for generic repeated errors on non-critical service
    sev_med = calculate_severity("reporting-service", "REPEATED_STACK_TRACE", [Event(level="WARN")] * 3)
    assert sev_med == "MEDIUM"


def test_http_500_spike_detection():
    now = datetime.now(timezone.utc)
    events = [
        Event(
            service="order-service",
            level="ERROR",
            event_type="http_500",
            message=f"Order error {i}",
            signature=f"sig-{i}",
            timestamp=now - timedelta(seconds=i * 2)
        )
        for i in range(6)
    ]
    res = check_http_500_spike(events, window_seconds=60, threshold=5)
    assert res is not None
    assert res.is_anomaly is True
    assert res.rule_name == "HTTP_500_SPIKE"


def test_post_deployment_anomaly_detection():
    now = datetime.now(timezone.utc)
    dep_time = now - timedelta(seconds=60)
    deployment = Deployment(
        service="payment-service",
        version="v1.8.3",
        commit_hash="a1b2c3d",
        environment="production",
        deployed_at=dep_time
    )

    errors_after_dep = [
        Event(
            service="payment-service",
            level="ERROR",
            event_type="error_log",
            message=f"Pool timeout {i}",
            signature="pool-sig",
            timestamp=dep_time + timedelta(seconds=i * 5)
        )
        for i in range(4)
    ]

    res = check_post_deployment_anomaly(errors_after_dep, [deployment], window_seconds=600)
    assert res is not None
    assert res.is_anomaly is True
    assert res.rule_name == "POST_DEPLOYMENT_ANOMALY"


def test_health_check_failure_detection():
    now = datetime.now(timezone.utc)
    hc_events = [
        Event(
            service="auth-service",
            level="CRITICAL",
            event_type="health_check",
            message="Health check failed: connection refused",
            signature="hc-sig",
            timestamp=now - timedelta(seconds=i * 10)
        )
        for i in range(3)
    ]
    res = check_health_check_failure(hc_events, consecutive_threshold=2)
    assert res is not None
    assert res.is_anomaly is True
    assert res.rule_name == "HEALTH_CHECK_CONSECUTIVE_FAILURE"


def test_action_allowlist_and_approval():
    # Valid allowed action
    assert validate_operational_action_allowed("rollback_deployment") is True
    assert validate_operational_action_allowed("restart_service") is True

    # Disallowed action must raise exception
    with pytest.raises(ActionNotAllowedException):
        validate_operational_action_allowed("rm_rf_production_database")

    # Approval required for MEDIUM and HIGH risk
    assert is_approval_required("MEDIUM") is True
    assert is_approval_required("HIGH") is True
    assert is_approval_required("LOW") is False

    # Executing MEDIUM action when PENDING raises exception
    with pytest.raises(ActionNotApprovedException):
        validate_action_approval("rollback_deployment", "MEDIUM", "PENDING", "ACT-01")

    # Executing MEDIUM action when APPROVED succeeds
    assert validate_action_approval("rollback_deployment", "MEDIUM", "APPROVED", "ACT-01") is True
