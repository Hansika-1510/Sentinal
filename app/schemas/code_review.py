from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CodeReviewBase(BaseModel):
    commit_hash: str = Field(..., description="Git commit hash")
    tool: str = Field(default="CodeGuard", description="Review engine: CodeGuard, RobinReview")
    finding: str = Field(..., description="Description of the finding")
    severity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, BLOCKER")
    file: str = Field(..., description="Source code file path")
    line: Optional[int] = Field(default=None, description="Line number")
    decision: str = Field(default="PASS", description="PASS, WARN, BLOCK")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Metadata key-values")


class CodeReviewCreate(CodeReviewBase):
    pass


class CodeReviewRead(CodeReviewBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StagedReviewRequest(BaseModel):
    diff: str = Field(..., description="Git diff payload to review")
    commit_hash: Optional[str] = Field(default=None, description="Commit hash if pre-assigned")
    author: Optional[str] = Field(default="developer", description="Author name or email")


class StagedReviewResponse(BaseModel):
    decision: str = Field(..., description="PASS, WARN, BLOCK")
    findings: list[CodeReviewRead] = Field(default_factory=list)
    summary: str = Field(..., description="Overall review summary")
    can_commit: bool = Field(..., description="True if no BLOCK findings exist")
