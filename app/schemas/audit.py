from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AuditLogBase(BaseModel):
    actor: str = Field(..., description="Identity of the actor (human or agent)")
    action: str = Field(..., description="Action name, e.g. APPROVE_ACTION, EXECUTE_REMEDIATION")
    target: str = Field(..., description="Target entity ID or name")
    reason: str = Field(default="", description="Reason or context")
    result: str = Field(default="SUCCESS", description="Outcome result: SUCCESS, FAILURE, REJECTED")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Detailed parameters")


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogRead(AuditLogBase):
    id: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
