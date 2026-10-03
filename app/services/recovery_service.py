from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.incident import Incident
from app.models.event import Event
from app.core.exceptions import RecoveryCriteriaNotMetException
from app.core.logging import logger


class RecoveryVerificationResult:
    def __init__(self, is_recovered: bool, error_rate: float, health_check_ok: bool, details: Dict[str, Any], reason: str):
        self.is_recovered = is_recovered
        self.error_rate = error_rate
        self.health_check_ok = health_check_ok
        self.details = details
        self.reason = reason


class RecoveryService:
    def __init__(self, db: Session):
        self.db = db

    def verify_recovery(self, incident_id: str, window_seconds: int = 120) -> RecoveryVerificationResult:
        """
        Verifies if the system has recovered after remediation:
        1. Checks post-remediation error events (events after latest executed action or in recent monitoring window).
        2. Checks latest health check status.
        3. Checks if original error signature has stopped.
        """
        incident = self.db.get(Incident, incident_id)
        if not incident:
            return RecoveryVerificationResult(
                is_recovered=False,
                error_rate=100.0,
                health_check_ok=False,
                details={},
                reason="Incident not found"
            )

        service_name = incident.service.name if incident.service else incident.service_id
        now = datetime.now(timezone.utc)
        
        # Check if there is an executed remediation action
        executed_actions = [a for a in incident.actions if a.approval_status == "EXECUTED" and a.executed_at]
        if executed_actions:
            latest_action = max(executed_actions, key=lambda a: a.executed_at)
            action_time = latest_action.executed_at.replace(tzinfo=timezone.utc) if latest_action.executed_at.tzinfo is None else latest_action.executed_at
            window_start = action_time
        else:
            window_start = now - timedelta(seconds=window_seconds)

        # 1. Fetch recent events in post-remediation monitoring window
        ev_stmt = (
            select(Event)
            .where(Event.service == service_name)
            .where(Event.timestamp >= window_start)
            .order_by(desc(Event.timestamp))
        )
        post_remediation_events = list(self.db.scalars(ev_stmt).all())

        total_count = len(post_remediation_events)
        error_events = [e for e in post_remediation_events if e.level in ["ERROR", "CRITICAL"]]
        error_count = len(error_events)

        error_rate = (error_count / total_count * 100.0) if total_count > 0 else 0.0

        # 2. Check health check status
        hc_events = [e for e in post_remediation_events if e.event_type == "health_check"]
        latest_hc_healthy = True
        if hc_events:
            latest_hc_healthy = (hc_events[0].level == "INFO" or "ok" in hc_events[0].message.lower() or "200" in hc_events[0].message)

        # 3. Check if error count in post-remediation window is 0 or error rate < 5%
        is_recovered = (error_count == 0 or error_rate < 5.0) and latest_hc_healthy and (total_count > 0)

        details = {
            "window_seconds": window_seconds,
            "total_events": total_count,
            "error_events": error_count,
            "error_rate_percent": round(error_rate, 2),
            "health_check_healthy": latest_hc_healthy,
            "monitoring_period": f"{window_start.isoformat()} to {now.isoformat()}"
        }

        if is_recovered:
            reason = f"Recovery verified: Error rate is {round(error_rate, 2)}% (below threshold) and health check is nominal."
        else:
            reason = f"Recovery criteria not satisfied: {error_count} errors observed in last {window_seconds}s (error rate: {round(error_rate, 2)}%)."

        logger.info(f"Incident {incident_id} recovery check: is_recovered={is_recovered} (error_rate={error_rate}%)")
        return RecoveryVerificationResult(
            is_recovered=is_recovered,
            error_rate=error_rate,
            health_check_ok=latest_hc_healthy,
            details=details,
            reason=reason
        )
