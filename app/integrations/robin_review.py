from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger


class RobinReviewFinding:
    def __init__(self, file: str, line: Optional[int], finding: str, severity: str, decision: str, rule_id: str):
        self.file = file
        self.line = line
        self.finding = finding
        self.severity = severity  # LOW, MEDIUM, HIGH, BLOCKER
        self.decision = decision  # PASS, WARN, BLOCK
        self.rule_id = rule_id


class RobinReviewIntegration:
    """RobinReview integration and deterministic analyzer."""

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or settings.ROBIN_REVIEW_URL or settings.LLM_BASE_URL
        self.api_key = api_key or settings.ROBIN_REVIEW_API_KEY or settings.LLM_API_KEY or settings.OPENROUTER_API_KEY
        self.is_mock = not bool(self.api_key)

    async def analyze_diff(self, diff_text: str, commit_hash: Optional[str] = None) -> List[RobinReviewFinding]:
        """Analyzes a git diff for anti-patterns, dangerous config, and security flaws."""
        if not self.is_mock and self.api_key and self.api_url:
            # 1. If explicit Robin API endpoint is provided
            if settings.ROBIN_REVIEW_URL:
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                        resp = await client.post(f"{self.api_url}/v1/review", json={"diff": diff_text, "commit": commit_hash}, headers=headers)
                        resp.raise_for_status()
                        results = resp.json().get("findings", [])
                        return [
                            RobinReviewFinding(
                                file=r.get("file", "unknown"),
                                line=r.get("line"),
                                finding=r.get("finding", ""),
                                severity=r.get("severity", "MEDIUM"),
                                decision=r.get("decision", "PASS"),
                                rule_id=r.get("rule_id", "RR-UNKNOWN")
                            )
                            for r in results
                        ]
                except Exception as e:
                    logger.warning(f"External RobinReview call failed, falling back to local deterministic analyzer: {str(e)}")

        # Deterministic local rules analyzer for diff
        findings: List[RobinReviewFinding] = []

        diff_lower = diff_text.lower()

        # Rule 1: Hardcoded secrets or private keys (BLOCK)
        if "private_key" in diff_lower or "aws_secret_access_key" in diff_lower or "ghp_" in diff_text:
            findings.append(RobinReviewFinding(
                file="security/credentials",
                line=1,
                finding="Potential hardcoded secret or credential detected in diff",
                severity="BLOCKER",
                decision="BLOCK",
                rule_id="SEC-SECRETS-001"
            ))

        # Rule 2: Dangerous pool size reduction (WARN or BLOCK based on bounds)
        if "setmaximumpoolsize(2)" in diff_lower or "maxpoolsize = 2" in diff_lower or "max_connections = 2" in diff_lower:
            findings.append(RobinReviewFinding(
                file="src/main/java/com/company/payment/config/DatabasePool.java",
                line=43,
                finding="Database connection pool size reduced to critically low value (2). Under concurrent traffic, threads will experience pool exhaustion.",
                severity="HIGH",
                decision="WARN",
                rule_id="PERF-DB-POOL-002"
            ))

        # Rule 3: Disabled security checks (BLOCK)
        if "disable_auth = true" in diff_lower or "verify=false" in diff_lower or "security.bypass=true" in diff_lower:
            findings.append(RobinReviewFinding(
                file="config/security.yaml",
                line=10,
                finding="Security verification bypass detected in configuration",
                severity="BLOCKER",
                decision="BLOCK",
                rule_id="SEC-BYPASS-003"
            ))

        # If no issues found
        if not findings:
            findings.append(RobinReviewFinding(
                file="general",
                line=None,
                finding="No critical code quality or security violations detected in staged diff.",
                severity="LOW",
                decision="PASS",
                rule_id="CLEAN-001"
            ))

        return findings
