from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ActionBase(BaseModel):
    incident_id: str = Field(..., description="Target incident ID")
    type: str = Field(..., description="Operational action type; must be in settings.ALLOWED_OPERATIONAL_ACTIONS, e.g. rollback_deployment, restart_service, disable_feature_flag")
    risk_level: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH")
    proposed_by: str = Field(default="ResponsePlannerAgent", description="Proposer identity")
    reason: str = Field(..., description="Reason for proposing this action")
    expected_impact: str = Field(..., description="Estimated/expected impact")
    rollback_path: str = Field(default="", description="Rollback path if action fails")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Metadata parameters, e.g. service, target_version")


class ActionCreate(ActionBase):
    pass


class ActionApproveRequest(BaseModel):
    actor: str = Field(..., description="Identity of the approver, e.g. alice@company.com")
    reason: Optional[str] = Field(default="Approved after review", description="Approval justification")


class ActionRejectRequest(BaseModel):
    actor: str = Field(..., description="Identity of the rejector")
    reason: str = Field(..., description="Reason for rejection")


class ActionExecuteRequest(BaseModel):
    actor: str = Field(..., description="Actor executing the action")


class ActionRead(BaseModel):
    id: str
    incident_id: str
    type: str
    risk_level: str
    proposed_by: str
    reason: str
    expected_impact: str
    rollback_path: str
    approval_status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    result_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
