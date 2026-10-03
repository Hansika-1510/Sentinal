from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.action import ActionRead
from app.schemas.event import EventRead


class IncidentBase(BaseModel):
    title: str = Field(..., description="Incident title")
    service_id: str = Field(..., description="Target service ID or name")
    environment: str = Field(default="production", description="Environment")
    severity: str = Field(default="MEDIUM", description="CRITICAL, HIGH, MEDIUM, LOW")
    status: str = Field(default="DETECTED", description="Lifecycle status")
    summary: Optional[str] = Field(default=None, description="Executive summary")
    root_cause: Optional[str] = Field(default=None, description="Root cause summary")
    confidence: Optional[str] = Field(default=None, description="HIGH, MEDIUM, LOW")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Metadata key-values")


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None
    root_cause: Optional[str] = None
    confidence: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None


class IncidentRead(IncidentBase):
    id: str
    started_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentDetailRead(IncidentRead):
    actions: List[ActionRead] = Field(default_factory=list)
    recent_events: List[EventRead] = Field(default_factory=list)


class IncidentResolveRequest(BaseModel):
    actor: str = Field(default="system", description="Actor resolving incident")
    reason: Optional[str] = Field(default="Verified recovery", description="Resolution justification")
    force: bool = Field(default=False, description="Force resolve without strict recovery verification check")


class IncidentTimelineItem(BaseModel):
    timestamp: datetime
    type: str  # event, deployment, commit, code_review, investigation, action_proposed, action_approved, action_executed, recovery_verified, resolved
    title: str
    description: str
    is_observed: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
