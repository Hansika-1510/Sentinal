from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

#: Canonical Fix Advisor safety disclaimer.
#: The "AI never edits your source code" invariant is enforced by normalising every piece
#: of guidance against this one string, so it lives here as a constant rather than being
#: read back out of the Pydantic field definition (which would silently yield
#: PydanticUndefined if the field were ever redefined without a default).
FIX_ADVISOR_DISCLAIMER = (
    "AI Fix Advisor provides developer guidance only. Source code modifications must be "
    "implemented manually by developers and verified via CodeGuard."
)


class EvidenceItem(BaseModel):
    type: str = Field(..., description="Evidence type: deployment, log, commit, code_review, metric, health_check")
    reference: str = Field(..., description="ID or identifier of the evidence item")
    explanation: str = Field(..., description="Detailed explanation connecting evidence to hypothesis")
    is_observed: bool = Field(default=True, description="True for observed raw facts; False for inferences")


class Hypothesis(BaseModel):
    cause: str = Field(..., description="Description of the root cause hypothesis")
    confidence: str = Field(..., description="HIGH, MEDIUM, LOW")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Supporting evidence items")
    contradicting_evidence: List[EvidenceItem] = Field(default_factory=list, description="Evidence contradicting hypothesis")
    explanation: str = Field(..., description="Detailed hypothesis justification")


class FixAdvisorGuidance(BaseModel):
    repository: str = Field(..., description="Source repository name")
    file: str = Field(..., description="Source code file path, e.g. PaymentService.java or pool.py")
    line_start: Optional[int] = Field(default=None, description="Starting line number of problematic block")
    line_end: Optional[int] = Field(default=None, description="Ending line number of problematic block")
    problem: str = Field(..., description="Summary of the code defect")
    why: str = Field(..., description="Mechanistic explanation of why the defect causes runtime failure")
    recommended_change: str = Field(..., description="Conceptual and architectural recommended change")
    expected_behavior: str = Field(..., description="Expected runtime behavior after developer applies fix")
    evidence: List[EvidenceItem] = Field(default_factory=list)
    confidence: str = Field(default="HIGH", description="Confidence level in fix guidance")
    validation_steps: List[str] = Field(default_factory=list, description="Step-by-step developer validation instructions")
    disclaimer: str = Field(
        default=FIX_ADVISOR_DISCLAIMER,
        description="Safety disclaimer"
    )


class BlastRadiusNode(BaseModel):
    service_name: str
    impact_type: str = Field(..., description="DIRECT or DOWNSTREAM")
    affected_features: List[str] = Field(default_factory=list)
    affected_user_journeys: List[str] = Field(default_factory=list)
    database_dependencies: List[str] = Field(default_factory=list)
    external_api_dependencies: List[str] = Field(default_factory=list)
    uncertainty_note: Optional[str] = None


class BlastRadiusReport(BaseModel):
    failing_service: str
    direct_impact: List[BlastRadiusNode] = Field(default_factory=list)
    downstream_impact: List[BlastRadiusNode] = Field(default_factory=list)
    total_affected_services: int = 0
    critical_user_journeys_impacted: List[str] = Field(default_factory=list)


class RemediationOption(BaseModel):
    type: str = Field(..., description="Operational action type; must be in settings.ALLOWED_OPERATIONAL_ACTIONS, e.g. rollback_deployment, restart_service, disable_feature_flag")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH")
    reason: str = Field(..., description="Operational justification")
    expected_impact: str = Field(..., description="Estimated operational impact (AI-assisted assessment)")
    possible_side_effects: List[str] = Field(default_factory=list)
    rollback_path: str = Field(..., description="Rollback instructions if remediation action fails")
    requires_approval: bool = Field(default=True, description="True if approval is mandatory")
    evidence: List[EvidenceItem] = Field(default_factory=list)


class RootCauseAnalysis(BaseModel):
    summary: str = Field(..., description="High-level executive summary of the incident")
    primary_hypothesis: Hypothesis = Field(..., description="Primary evidence-backed hypothesis")
    alternative_hypotheses: List[Hypothesis] = Field(default_factory=list, description="Alternative hypotheses explored")
    affected_services: List[str] = Field(default_factory=list, description="List of directly or indirectly affected service names")
    blast_radius: Optional[BlastRadiusReport] = None
    fix_guidance: Optional[FixAdvisorGuidance] = None
    recommended_actions: List[RemediationOption] = Field(default_factory=list, description="Proposed operational actions")


class InvestigationResult(BaseModel):
    incident_id: str
    status: str
    rca: RootCauseAnalysis
    timeline_summary: List[Dict[str, Any]] = Field(default_factory=list)
    similar_historical_incidents: List[Dict[str, Any]] = Field(default_factory=list)
