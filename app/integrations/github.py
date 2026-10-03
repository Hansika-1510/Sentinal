import hmac
import hashlib
from typing import Dict, Any, Optional, List
import httpx
from app.core.config import settings
from app.core.logging import logger


class GitHubIntegration:
    """Integration for interacting with GitHub API and Webhooks."""

    def __init__(self, token: Optional[str] = None, webhook_secret: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.webhook_secret = webhook_secret or settings.GITHUB_WEBHOOK_SECRET
        self.is_mock = not bool(self.token)

    def verify_webhook_signature(self, payload_body: bytes, signature_header: Optional[str]) -> bool:
        """Verifies GitHub SHA-256 HMAC signature."""
        if not self.webhook_secret:
            # In demo mode without secret, allow webhook
            return True
        if not signature_header or not signature_header.startswith("sha256="):
            return False

        expected_sig = "sha256=" + hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature_header)

    async def get_commit_details(self, repo: str, commit_sha: str) -> Dict[str, Any]:
        """Fetches commit details, modified files, and author."""
        if self.is_mock or not self.token:
            # Deterministic mock commit details for demo
            return {
                "sha": commit_sha,
                "author": "developer@company.com",
                "message": "fix(db): optimize connection pool configuration",
                "files_changed": [
                    {
                        "filename": "src/main/java/com/company/payment/config/DatabasePool.java",
                        "status": "modified",
                        "additions": 4,
                        "deletions": 2,
                        "patch": "@@ -42,6 +42,6 @@ public class DatabasePool {\n-    config.setMaximumPoolSize(50);\n-    config.setConnectionTimeout(30000);\n+    config.setMaximumPoolSize(2);\n+    config.setConnectionTimeout(1000);"
                    }
                ]
            }

        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json"
            }
            resp = await client.get(f"https://api.github.com/repos/{repo}/commits/{commit_sha}", headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return {
                "sha": data.get("sha"),
                "author": data.get("commit", {}).get("author", {}).get("email", "unknown"),
                "message": data.get("commit", {}).get("message", ""),
                "files_changed": [
                    {
                        "filename": f.get("filename"),
                        "status": f.get("status"),
                        "additions": f.get("additions"),
                        "deletions": f.get("deletions"),
                        "patch": f.get("patch", "")
                    }
                    for f in data.get("files", [])
                ]
            }
