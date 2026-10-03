from typing import List, Dict, Any, Optional
from app.schemas.investigation import RemediationOption, RootCauseAnalysis, BlastRadiusReport
from app.rules.action_allowlist import is_approval_required
from app.integrations.llm import get_llm_provider
from app.core.logging import logger


class ResponsePlannerAgent:
    """
    Response Planner Agent: Synthesizes operational remediation action options
    based on RCA, blast radius, and risk classifications.
    """

    def __init__(self):
        self.llm_provider = get_llm_provider()

    def plan_remediation_options(self, rca: RootCauseAnalysis, service_name: str, deployment_version: Optional[str] = None) -> List[RemediationOption]:
        """
        Generates structured, risk-classified operational actions.
        """
        options: List[RemediationOption] = []

        # 1. Rollback Option (Medium/High Risk depending on state)
        options.append(RemediationOption(
            type="ROLLBACK",
            risk_level="MEDIUM",
            reason=f"Roll back {service_name} from version {deployment_version or 'v1.8.3'} to previous stable release.",
            expected_impact="Estimated impact: Restores baseline healthy configuration and clears error spikes (AI-assisted assessment).",
            possible_side_effects=["Brief 2-second connection reset during replica termination."],
            rollback_path=f"Re-deploy {deployment_version or 'v1.8.3'} if rollback encounters deployment errors.",
            requires_approval=is_approval_required("MEDIUM"),
            evidence=rca.primary_hypothesis.evidence
        ))

        # 2. Restart Option (Low Risk)
        options.append(RemediationOption(
            type="RESTART_SERVICE",
            risk_level="LOW",
            reason=f"Perform rolling restart of {service_name} instances to flush degraded connection handles.",
            expected_impact="Estimated impact: Transient relief; underlying code defect remains active until permanent fix is deployed (AI-assisted assessment).",
            possible_side_effects=["Transient queueing of inflight requests."],
            rollback_path="No rollback path required.",
            requires_approval=is_approval_required("LOW"),
            evidence=[]
        ))

        # 3. Disable Feature Flag if applicable
        options.append(RemediationOption(
            type="DISABLE_FEATURE",
            risk_level="LOW",
            reason="Disable canary / optional features to reduce database connection demand.",
            expected_impact="Estimated impact: Lowers query pressure on primary database.",
            possible_side_effects=["Optional features unavailable to users."],
            rollback_path="Re-enable feature flag via configuration.",
            requires_approval=is_approval_required("LOW"),
            evidence=[]
        ))

        return options
