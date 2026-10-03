import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, JSON, Text, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class CodeReview(Base):
    __tablename__ = "code_reviews"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    commit_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    tool: Mapped[str] = mapped_column(String(64), default="CodeGuard", nullable=False)  # CodeGuard, RobinReview
    finding: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, BLOCKER
    file: Mapped[str] = mapped_column(String(256), nullable=False)
    line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    decision: Mapped[str] = mapped_column(String(32), default="PASS", nullable=False)  # PASS, WARN, BLOCK
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


Index("idx_codereview_commit_decision", CodeReview.commit_hash, CodeReview.decision)
