from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.api.deps import get_db
from app.models.code_review import CodeReview
from app.schemas.code_review import CodeReviewCreate, CodeReviewRead, StagedReviewRequest, StagedReviewResponse
from app.agents.codeguard import CodeGuardAgent

router = APIRouter(prefix="/code-reviews", tags=["CodeGuard Code Reviews"])


@router.post("", response_model=CodeReviewRead, status_code=status.HTTP_201_CREATED)
def record_code_review(cr_in: CodeReviewCreate, db: Session = Depends(get_db)):
    """Record a code review finding for a commit."""
    cr = CodeReview(
        commit_hash=cr_in.commit_hash,
        tool=cr_in.tool,
        finding=cr_in.finding,
        severity=cr_in.severity.upper(),
        file=cr_in.file,
        line=cr_in.line,
        decision=cr_in.decision.upper(),
        metadata_json=cr_in.metadata_json
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)
    return cr


@router.post("/review-staged", response_model=StagedReviewResponse, status_code=status.HTTP_200_OK)
async def review_staged_diff(review_req: StagedReviewRequest, db: Session = Depends(get_db)):
    """
    Review staged git diff payload (`devguard review-staged`).
    Blocks commits with BLOCKER / BLOCK severity findings.
    """
    agent = CodeGuardAgent(db)
    return await agent.review_staged_diff(review_req)


@router.get("", response_model=List[CodeReviewRead])
def list_code_reviews(
    commit_hash: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List code review findings."""
    stmt = select(CodeReview).order_by(desc(CodeReview.created_at)).limit(limit)
    if commit_hash:
        stmt = stmt.where(CodeReview.commit_hash == commit_hash)
    if decision:
        stmt = stmt.where(CodeReview.decision == decision.upper())
    return list(db.scalars(stmt).all())
