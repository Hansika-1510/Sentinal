from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.action import Action
from app.models.incident import Incident
from app.schemas.action import ActionCreate, ActionApproveRequest, ActionRejectRequest, ActionExecuteRequest
from app.rules.action_allowlist import (
    validate_action_approval,
    validate_operational_action_allowed,
    is_approval_required
)
from app.core.exceptions import ActionNotFoundException, IncidentNotFoundException
from app.services.audit_service import AuditService
from app.integrations.runtime import runtime_adapter
from app.core.logging import logger


class RemediationService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def create_action_proposal(self, action_in: ActionCreate) -> Action:
        """Proposes an operational remediation action."""
        incident = self.db.get(Incident, action_in.incident_id)
        if not incident:
            raise IncidentNotFoundException(action_in.incident_id)

        # Validate action is in operational allowlist
        validate_operational_action_allowed(action_in.type.lower())

        action = Action(
            incident_id=action_in.incident_id,
            type=action_in.type,
            risk_level=action_in.risk_level.upper(),
            proposed_by=action_in.proposed_by,
            reason=action_in.reason,
            expected_impact=action_in.expected_impact,
            rollback_path=action_in.rollback_path,
            approval_status="PENDING",
            result_json=action_in.metadata_json or {}
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)

        # Update incident status to AWAITING_APPROVAL if medium/high risk
        if is_approval_required(action.risk_level) and incident.status != "RESOLVED":
            incident.status = "AWAITING_APPROVAL"
            self.db.commit()

        self.audit_service.record_audit_log(
            actor=action.proposed_by,
            action="PROPOSE_REMEDIATION_ACTION",
            target=f"Action:{action.id}",
            reason=action.reason,
            result="PROPOSED",
            metadata={"incident_id": action.incident_id, "type": action.type, "risk_level": action.risk_level}
        )
        return action

    def approve_action(self, action_id: str, approve_in: ActionApproveRequest) -> Action:
        """Human operator approves a proposed remediation action."""
        action = self.db.get(Action, action_id)
        if not action:
            raise ActionNotFoundException(action_id)

        action.approval_status = "APPROVED"
        action.approved_by = approve_in.actor
        action.approved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)

        self.audit_service.record_audit_log(
            actor=approve_in.actor,
            action="APPROVE_REMEDIATION_ACTION",
            target=f"Action:{action.id}",
            reason=approve_in.reason or "Approved by operator",
            result="APPROVED",
            metadata={"incident_id": action.incident_id, "type": action.type, "risk_level": action.risk_level}
        )
        return action

    def reject_action(self, action_id: str, reject_in: ActionRejectRequest) -> Action:
        """Human operator rejects a proposed remediation action."""
        action = self.db.get(Action, action_id)
        if not action:
            raise ActionNotFoundException(action_id)

        action.approval_status = "REJECTED"
        action.approved_by = reject_in.actor
        action.approved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)

        self.audit_service.record_audit_log(
            actor=reject_in.actor,
            action="REJECT_REMEDIATION_ACTION",
            target=f"Action:{action.id}",
            reason=reject_in.reason,
            result="REJECTED",
            metadata={"incident_id": action.incident_id, "type": action.type}
        )
        return action

    async def execute_action(self, action_id: str, exec_in: ActionExecuteRequest) -> Action:
        """
        Executes an approved, allowlisted operational action.
        Strictly enforces server-side approval check for MEDIUM/HIGH risk actions.
        """
        action = self.db.get(Action, action_id)
        if not action:
            raise ActionNotFoundException(action_id)

        incident = self.db.get(Incident, action.incident_id)

        # 1. Enforce business rule: MEDIUM/HIGH risk requires approval_status == APPROVED
        validate_action_approval(
            action_type=action.type,
            risk_level=action.risk_level,
            approval_status=action.approval_status,
            action_id=action.id
        )

        # 2. Enforce business rule: Operational action must be allowlisted
        validate_operational_action_allowed(action.type.lower())

        # Update status to MITIGATING on incident
        if incident:
            incident.status = "MITIGATING"
            self.db.commit()

        # 3. Safe operational runtime execution
        exec_params = action.result_json or {}
        if incident and incident.service:
            exec_params["service"] = incident.service.name
        elif incident:
            exec_params["service"] = incident.service_id

        try:
            exec_result = await runtime_adapter.execute_action(
                action_name=action.type.lower(),
                parameters=exec_params
            )
            action.approval_status = "EXECUTED"
            action.executed_at = datetime.now(timezone.utc)
            action.result_json = exec_result
            self.db.commit()

            # Shift incident to MONITORING after remediation
            if incident:
                incident.status = "MONITORING"
                self.db.commit()

            self.audit_service.record_audit_log(
                actor=exec_in.actor,
                action="EXECUTE_REMEDIATION_ACTION",
                target=f"Action:{action.id}",
                reason=action.reason,
                result="SUCCESS",
                metadata={"execution_result": exec_result, "incident_id": action.incident_id}
            )
            return action
        except Exception as e:
            action.approval_status = "FAILED"
            action.result_json = {"error": str(e)}
            self.db.commit()

            self.audit_service.record_audit_log(
                actor=exec_in.actor,
                action="EXECUTE_REMEDIATION_ACTION",
                target=f"Action:{action.id}",
                reason=action.reason,
                result="FAILED",
                metadata={"error": str(e), "incident_id": action.incident_id}
            )
            raise e
