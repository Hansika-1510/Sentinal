from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ServiceBase(BaseModel):
    name: str = Field(..., description="Service identifier name, e.g. payment-service")
    environment: str = Field(default="production", description="Environment")
    description: str = Field(default="", description="Description of the service")
    dependencies: List[str] = Field(default_factory=list, description="List of dependency service names or resources")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Metadata key-values")


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    description: Optional[str] = None
    dependencies: Optional[List[str]] = None
    metadata_json: Optional[Dict[str, Any]] = None


class ServiceRead(ServiceBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
