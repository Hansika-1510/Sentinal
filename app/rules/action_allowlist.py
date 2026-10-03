from typing import Tuple
from app.core.config import settings
from app.core.exceptions import ActionNotAllowedException, ActionNotApprovedException


ALLOWED_OPERATIONAL_ACTIONS = set(settings.ALLOWED_OPERATIONAL_ACTIONS)


def validate_operational_action_allowed(action_name: str) -> bool:
    """Validates that the given operational action is strictly present in the allowlist."""
    normalized = action_name.lower().strip()
    if normalized not in ALLOWED_OPERATIONAL_ACTIONS:
        raise ActionNotAllowedException(action_name)
    return True


def validate_action_approval(action_type: str, risk_level: str, approval_status: str, action_id: str) -> bool:
    """
    Enforces business rules:
    - MEDIUM and HIGH risk operational actions strictly require human approval (status == 'APPROVED').
    - If status != 'APPROVED', raises ActionNotApprovedException.
    """
    normalized_risk = risk_level.upper()
    if normalized_risk in ["MEDIUM", "HIGH", "CRITICAL"]:
        if approval_status.upper() != "APPROVED":
            raise ActionNotApprovedException(
                action_id=action_id,
                current_status=approval_status,
                risk_level=risk_level
            )
    return True


def is_approval_required(risk_level: str) -> bool:
    """Returns True if the given risk level requires explicit human approval."""
    return risk_level.upper() in ["MEDIUM", "HIGH", "CRITICAL"]
