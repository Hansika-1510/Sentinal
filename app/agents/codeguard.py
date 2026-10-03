import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.code_review import CodeReview
from app.schemas.code_review import StagedReviewRequest, StagedReviewResponse, CodeReviewRead
from app.integrations.robin_review import RobinReviewIntegration, RobinReviewFinding
from app.services.audit_service import AuditService
from app.core.logging import logger


class CodeGuardAgent:
    """
    CodeGuard Agent: Inspects staged git diffs (`git diff --cached`) using RobinReview
    and deterministic security rules. Enforces PASS/WARN/BLOCK commit gating.
    """

    def __init__(self, db: Session):
        self.db = db
        self.robin_review = RobinReviewIntegration()
        self.audit_service = AuditService(db)

    async def review_staged_diff(self, request: StagedReviewRequest) -> StagedReviewResponse:
        """
        Reviews staged diff.
        BLOCK findings -> can_commit = False (triggers non-zero exit in pre-commit hook).
        WARN/PASS findings -> can_commit = True.
        """
        commit_hash = request.commit_hash or hashlib.sha256(request.diff.encode("utf-8")).hexdigest()[:12]
        
        findings_raw: List[RobinReviewFinding] = await self.robin_review.analyze_diff(
            diff_text=request.diff,
            commit_hash=commit_hash
        )

        overall_decision = "PASS"
        can_commit = True
        saved_reviews: List[CodeReviewRead] = []

        # Determine overall decision: BLOCK > WARN > PASS
        if any(f.decision == "BLOCK" for f in findings_raw):
            overall_decision = "BLOCK"
            can_commit = False
        elif any(f.decision == "WARN" for f in findings_raw):
            overall_decision = "WARN"
            can_commit = True

        for f in findings_raw:
            cr = CodeReview(
                commit_hash=commit_hash,
                tool="CodeGuard/RobinReview",
                finding=f.finding,
                severity=f.severity,
                file=f.file,
                line=f.line,
                decision=f.decision,
                metadata_json={"rule_id": f.rule_id, "author": request.author}
            )
            self.db.add(cr)
            self.db.commit()
            self.db.refresh(cr)
            saved_reviews.append(CodeReviewRead.model_validate(cr))

        summary = f"CodeGuard review finished with decision [{overall_decision}]. {len(saved_reviews)} findings recorded."

        self.audit_service.record_audit_log(
            actor=request.author or "developer",
            action="CODEGUARD_STAGED_REVIEW",
            target=f"Commit:{commit_hash}",
            reason="Pre-commit staged diff review",
            result=overall_decision,
            metadata={"can_commit": can_commit, "finding_count": len(saved_reviews)}
        )

        logger.info(f"CodeGuard review for {commit_hash}: {overall_decision} (can_commit={can_commit})")

        return StagedReviewResponse(
            decision=overall_decision,
            findings=saved_reviews,
            summary=summary,
            can_commit=can_commit
        )
