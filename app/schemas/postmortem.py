from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class PostmortemReport(BaseModel):
    incident_id: str
    title: str
    service: str
    severity: str
    duration_minutes: float
    summary: str
    impact: Dict[str, Any] = Field(default_factory=dict)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    root_cause: str
    contributing_factors: List[str] = Field(default_factory=list)
    detection_method: str
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    recovery_verification: Dict[str, Any] = Field(default_factory=dict)
    lessons_learned: List[str] = Field(default_factory=list)
    preventive_recommendations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IncidentMemoryRead(BaseModel):
    id: str
    incident_id: str
    summary: str
    symptoms: str
    rca: str
    resolution: str
    outcome: str
    similarity_score: Optional[float] = None
    created_at: datetime
