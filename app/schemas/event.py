from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class EventBase(BaseModel):
    service: str = Field(..., description="Target service name")
    environment: str = Field(default="production", description="Environment")
    source: str = Field(default="runtime", description="Source of the event (e.g. log_stream, k8s, sentry)")
    level: str = Field(default="ERROR", description="Log level: INFO, WARN, ERROR, CRITICAL")
    message: str = Field(..., description="Log message or alert payload")
    event_type: str = Field(default="error_log", description="Type: error_log, http_500, stack_trace, alert, deployment_event, health_check, runtime_metric")
    signature: Optional[str] = Field(default=None, description="Event signature/fingerprint for deduplication")
    timestamp: Optional[datetime] = Field(default=None, description="Event occurrence timestamp")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")
    incident_id: Optional[str] = Field(default=None, description="Associated incident ID if known")


class EventCreate(EventBase):
    pass


class EventRead(EventBase):
    id: str
    signature: str
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventIngestResponse(BaseModel):
    event: EventRead
    incident_created: bool = False
    incident_id: Optional[str] = None
    reason: Optional[str] = None
