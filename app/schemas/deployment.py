from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DeploymentBase(BaseModel):
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Version/tag, e.g. v1.8.3")
    commit_hash: str = Field(..., description="Git commit SHA")
    environment: str = Field(default="production", description="Target environment")
    status: str = Field(default="SUCCESS", description="SUCCESS, FAILED, ROLLED_BACK")
    deployed_at: Optional[datetime] = Field(default=None, description="Deployment timestamp")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")


class DeploymentCreate(DeploymentBase):
    pass


class DeploymentRead(DeploymentBase):
    id: str
    deployed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
