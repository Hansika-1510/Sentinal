from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from app.models.event import Event
from app.models.deployment import Deployment
from app.core.config import settings


class AnomalyDetectionResult:
    def __init__(self, is_anomaly: bool, rule_name: str, reason: str, confidence: str, matched_events: List[Event], suggested_severity: str = "MEDIUM"):
        self.is_anomaly = is_anomaly
        self.rule_name = rule_name
        self.reason = reason
        self.confidence = confidence
        self.matched_events = matched_events
        self.suggested_severity = suggested_severity


def check_http_500_spike(events: List[Event], window_seconds: int = None, threshold: int = None) -> Optional[AnomalyDetectionResult]:
    """Rule 1: Detect X HTTP 500 errors within Y seconds."""
    window = window_seconds or settings.HTTP_500_WINDOW_SECONDS
    thresh = threshold or settings.HTTP_500_ERROR_THRESHOLD
    
    if not events:
        return None

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=window)

    recent_500s = [
        e for e in events
        if (e.level in ["ERROR", "CRITICAL"] or e.event_type in ["http_500", "error_log"])
        and (e.timestamp.replace(tzinfo=timezone.utc) if e.timestamp.tzinfo is None else e.timestamp) >= cutoff
    ]

    if len(recent_500s) >= thresh:
        return AnomalyDetectionResult(
            is_anomaly=True,
            rule_name="HTTP_500_SPIKE",
            reason=f"Detected {len(recent_500s)} error/HTTP 500 events in {window}s window (threshold: {thresh})",
            confidence="HIGH",
            matched_events=recent_500s,
            suggested_severity="HIGH" if len(recent_500s) < 10 else "CRITICAL"
        )
    return None


def check_post_deployment_anomaly(events: List[Event], deployments: List[Deployment], window_seconds: int = None) -> Optional[AnomalyDetectionResult]:
    """Rule 2: Detect abnormal error spike immediately following a recent deployment."""
    window = window_seconds or settings.DEPLOYMENT_ANOMALY_WINDOW_SECONDS
    if not deployments or not events:
        return None

    now = datetime.now(timezone.utc)
    # Check most recent deployment
    latest_deployment = deployments[0]
    dep_time = latest_deployment.deployed_at.replace(tzinfo=timezone.utc) if latest_deployment.deployed_at.tzinfo is None else latest_deployment.deployed_at
    
    if (now - dep_time).total_seconds() <= window:
        # Check error events occurring after deployment
        post_dep_errors = [
            e for e in events
            if (e.level in ["ERROR", "CRITICAL"])
            and ((e.timestamp.replace(tzinfo=timezone.utc) if e.timestamp.tzinfo is None else e.timestamp) >= dep_time)
        ]
        if len(post_dep_errors) >= 3:
            return AnomalyDetectionResult(
                is_anomaly=True,
                rule_name="POST_DEPLOYMENT_ANOMALY",
                reason=f"Deployment {latest_deployment.version} (commit {latest_deployment.commit_hash[:7]}) followed by {len(post_dep_errors)} error events within {int((now - dep_time).total_seconds())}s",
                confidence="HIGH",
                matched_events=post_dep_errors,
                suggested_severity="CRITICAL"
            )
    return None


def check_health_check_failure(events: List[Event], consecutive_threshold: int = None) -> Optional[AnomalyDetectionResult]:
    """Rule 3: Consecutive health check failure detection."""
    thresh = consecutive_threshold or settings.HEALTH_CHECK_FAILURE_CONSECUTIVE
    hc_events = [e for e in events if e.event_type == "health_check"]
    
    if len(hc_events) >= thresh:
        consecutive_failures = [e for e in hc_events[:thresh] if e.level in ["ERROR", "CRITICAL"]]
        if len(consecutive_failures) >= thresh:
            return AnomalyDetectionResult(
                is_anomaly=True,
                rule_name="HEALTH_CHECK_CONSECUTIVE_FAILURE",
                reason=f"{len(consecutive_failures)} consecutive health check failures detected",
                confidence="HIGH",
                matched_events=consecutive_failures,
                suggested_severity="CRITICAL"
            )
    return None


def check_repeated_stack_trace(events: List[Event], threshold: int = 4) -> Optional[AnomalyDetectionResult]:
    """Rule 4: Repeated identical stack trace or error signature."""
    signatures: Dict[str, List[Event]] = {}
    for e in events:
        if e.level in ["ERROR", "CRITICAL"]:
            signatures.setdefault(e.signature, []).append(e)
            if len(signatures[e.signature]) >= threshold:
                return AnomalyDetectionResult(
                    is_anomaly=True,
                    rule_name="REPEATED_STACK_TRACE",
                    reason=f"Signature '{e.signature}' occurred {len(signatures[e.signature])} times in recent window",
                    confidence="HIGH",
                    matched_events=signatures[e.signature],
                    suggested_severity="HIGH"
                )
    return None


def evaluate_all_rules(events: List[Event], deployments: List[Deployment]) -> Optional[AnomalyDetectionResult]:
    """Evaluates all deterministic anomaly rules in priority order."""
    # 1. Post deployment anomaly is highest priority
    res = check_post_deployment_anomaly(events, deployments)
    if res:
        return res

    # 2. Consecutive health check failures
    res = check_health_check_failure(events)
    if res:
        return res

    # 3. HTTP 500 spike
    res = check_http_500_spike(events)
    if res:
        return res

    # 4. Repeated stack trace
    res = check_repeated_stack_trace(events)
    if res:
        return res

    return None
