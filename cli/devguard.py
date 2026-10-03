import os
import sys
import subprocess
import click
import httpx
from typing import Optional

# Allow `python cli/devguard.py` to import the `app` package. When Python runs a
# script it puts the script's directory on sys.path, not the project root, so the
# offline-analyzer fallback below raised ModuleNotFoundError without this.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Windows consoles frequently default to a legacy code page (e.g. cp1252) which
# cannot encode the status glyphs printed at the end of a review. Without this the
# CLI dies with UnicodeEncodeError and exits 1, blocking even a clean commit.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


@click.group()
def cli():
    """DevGuard CLI: Developer safety guard and pre-commit reviewer."""
    pass


def get_staged_diff() -> str:
    """Extracts staged git diff using `git diff --cached`."""
    try:
        res = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout
    except Exception as e:
        return ""


@cli.command("review-staged")
@click.option("--backend-url", default="http://localhost:8000", help="Incident Response Agent Backend URL")
@click.option("--diff-file", type=click.Path(exists=True), help="Optional path to a diff file to review instead of git staged")
@click.option("--author", default="developer@company.com", help="Author identifier")
def review_staged(backend_url: str, diff_file: Optional[str], author: str):
    """
    Reviews staged code changes (`git diff --cached`) against CodeGuard/RobinReview rules.
    Exits with code 1 if BLOCK findings are detected (blocking git commit).
    Exits with code 0 if PASS or WARN.
    """
    if diff_file:
        with open(diff_file, "r", encoding="utf-8") as f:
            diff_text = f.read()
    else:
        diff_text = get_staged_diff()

    if not diff_text.strip():
        click.secho("[CodeGuard] No staged changes found to review.", fg="yellow")
        sys.exit(0)

    click.secho("[CodeGuard] Inspecting staged changes...", fg="cyan", bold=True)

    try:
        # Call backend API
        endpoint = f"{backend_url.rstrip('/')}/api/code-reviews/review-staged"
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(endpoint, json={"diff": diff_text, "author": author})
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        # Fallback to local offline analyzer if backend is unreachable
        click.secho(f"[CodeGuard Warning] Backend unreachable ({e}), running local security scan...", fg="yellow")
        from app.integrations.robin_review import RobinReviewIntegration
        import asyncio
        analyzer = RobinReviewIntegration()
        findings = asyncio.run(analyzer.analyze_diff(diff_text))
        has_block = any(f.decision == "BLOCK" for f in findings)
        decision = "BLOCK" if has_block else ("WARN" if any(f.decision == "WARN" for f in findings) else "PASS")
        data = {
            "decision": decision,
            "can_commit": not has_block,
            "summary": f"Local scan completed with decision [{decision}]",
            "findings": [
                {"finding": f.finding, "severity": f.severity, "file": f.file, "line": f.line, "decision": f.decision}
                for f in findings
            ]
        }

    # Print results
    decision = data.get("decision", "PASS")
    findings = data.get("findings", [])

    click.echo("\n" + "=" * 60)
    click.secho(f" CODEGUARD REVIEW RESULT: [{decision}]", bold=True, fg="red" if decision == "BLOCK" else ("yellow" if decision == "WARN" else "green"))
    click.echo("=" * 60)

    for f in findings:
        color = "red" if f.get("decision") == "BLOCK" else ("yellow" if f.get("decision") == "WARN" else "green")
        click.secho(f"• [{f.get('decision')}] [{f.get('severity')}] {f.get('file')}:{f.get('line') or 'all'}", fg=color, bold=True)
        click.echo(f"  {f.get('finding')}")

    click.echo("\n" + "-" * 60)
    if not data.get("can_commit", True):
        click.secho("⛔ COMMIT BLOCKED: Critical blocker findings must be resolved before committing.", fg="red", bold=True)
        sys.exit(1)
    elif decision == "WARN":
        click.secho("⚠️  COMMIT PERMITTED WITH WARNINGS: Please review non-blocking advisories.", fg="yellow", bold=True)
        sys.exit(0)
    else:
        click.secho("✅ COMMIT PASSED: All CodeGuard verification checks passed cleanly.", fg="green", bold=True)
        sys.exit(0)


if __name__ == "__main__":
    cli()
