from typing import List
from app.models.event import Event


def calculate_severity(
    service_name: str,
    rule_name: str,
    matched_events: List[Event],
    error_rate: float = 0.0
) -> str:
    """
    Deterministically computes the severity level for an incident based on:
    - Service criticality (e.g. payment-service, auth-service vs reporting-service)
    - Triggered anomaly rule
    - Event levels and counts
    - Error rate
    """
    critical_services = {"payment-service", "auth-service", "api-gateway"}
    is_critical_service = service_name.lower() in critical_services
    
    has_critical_events = any(e.level == "CRITICAL" for e in matched_events)
    
    if rule_name == "POST_DEPLOYMENT_ANOMALY":
        if is_critical_service or len(matched_events) >= 5 or has_critical_events:
            return "CRITICAL"
        return "HIGH"

    if rule_name == "HEALTH_CHECK_CONSECUTIVE_FAILURE":
        return "CRITICAL"

    if rule_name == "HTTP_500_SPIKE":
        if is_critical_service or len(matched_events) >= 15 or error_rate >= 50.0:
            return "CRITICAL"
        if len(matched_events) >= 5 or error_rate >= 20.0:
            return "HIGH"
        return "MEDIUM"

    if rule_name == "REPEATED_STACK_TRACE":
        if is_critical_service:
            return "HIGH"
        return "MEDIUM"

    if has_critical_events:
        return "HIGH"

    return "MEDIUM"
