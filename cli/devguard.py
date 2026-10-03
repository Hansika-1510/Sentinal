import os
import sys
import subprocess
import click
import httpx
from typing import Optional
from urllib.parse import urlparse

# Allow `python cli/devguard.py` to import the `app` package. When Python runs a
# script it puts the script's directory on sys.path, not the project root, so the
# offline-analyzer fallback below raised ModuleNotFoundError without this.
# realpath (not abspath) so a symlinked entry point still resolves to the real
# project root, and insert(0) (not append) so our own `app` package wins over any
# same-named package in site-packages.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Windows consoles frequently default to a legacy code page (e.g. cp1252) which
# cannot encode the status glyphs printed at the end of a review. Without this the
# CLI dies with UnicodeEncodeError and exits 1, blocking even a clean commit.
_utf8_ok = True
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):
        _utf8_ok = False

if not _utf8_ok:
    # Warn once on the original stderr. If reconfiguration failed the status glyphs
    # printed later may still raise UnicodeEncodeError; without this the user sees
    # that crash with no hint that the encoding workaround was tried and failed.
    # The message is deliberately ASCII-only so it cannot itself hit the code page
    # problem, and __stderr__ may be None (e.g. pythonw.exe), hence the guard.
    try:
        sys.__stderr__.write(
            "[CodeGuard] warning: could not switch stdout/stderr to UTF-8; "
            "status symbols may not print on this console.\n"
        )
    except Exception:
        pass


@click.group()
def cli():
    """DevGuard CLI: Developer safety guard and pre-commit reviewer."""
    pass


#: Written into the generated hook so we can tell our own hook from a developer's.
HOOK_MARKER = "installed by `devguard install-hook`"
HOOK_FILENAME = "pre-commit"

#: The pre-commit hook body. POSIX sh because Git for Windows runs hooks through its
#: bundled bash. LF endings matter: a CRLF shebang makes the hook unrunnable.
HOOK_SCRIPT = """#!/bin/sh
# CodeGuard pre-commit hook -- {marker}
# Blocks the commit on a BLOCK finding; lets WARN/PASS through.
# Bypass for a single commit with: git commit --no-verify
# Remove with: python cli/devguard.py install-hook --uninstall

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT" || exit 0

# Prefer the project virtualenv so the hook does not depend on the developer's PATH.
PYTHON="python"
if [ -x ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
fi

AUTHOR="$(git config user.email 2>/dev/null)"
[ -n "$AUTHOR" ] || AUTHOR="developer@company.com"

exec "$PYTHON" "cli/devguard.py" review-staged --backend-url "__BACKEND_URL__" --author "$AUTHOR"
"""


def _git_hooks_dir() -> Optional[str]:
    """Locate the hooks directory, honouring core.hooksPath and linked worktrees."""
    for args in (
        ["git", "rev-parse", "--path-format=absolute", "--git-path", "hooks"],
        ["git", "rev-parse", "--git-path", "hooks"],
    ):
        try:
            res = subprocess.run(args, capture_output=True, text=True, check=True)
            path = res.stdout.strip()
            if path:
                return os.path.abspath(path)
        except Exception:
            continue
    return None


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


#: Characters that would break out of the double-quoted `--backend-url "..."` slot in the
#: generated hook, or start a new shell construct inside it. A backend URL never legitimately
#: needs any of them, so rejecting the set outright is simpler and safer than escaping.
_UNSAFE_URL_CHARS = set("\"'`$&|;<>()\\ \t\r\n")


def _validate_backend_url(url: str) -> Optional[str]:
    """Return an error message if the URL cannot be embedded safely in the hook, else None.

    The URL is interpolated into a shell script, so an unvalidated value containing a quote
    or a semicolon could alter the generated hook rather than merely break it.
    """
    if set(url) & _UNSAFE_URL_CHARS:
        return "must not contain quotes, whitespace, or shell metacharacters"
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "must be an absolute http:// or https:// URL"
    return None


@cli.command("install-hook")
@click.option("--backend-url", default="http://localhost:8000", help="Backend URL the hook calls for the review")
@click.option("--force", is_flag=True, help="Overwrite a pre-commit hook that devguard did not install")
@click.option("--uninstall", is_flag=True, help="Remove the devguard pre-commit hook")
def install_hook(backend_url: str, force: bool, uninstall: bool):
    """
    Install a git pre-commit hook so CodeGuard reviews every commit automatically.

    Without this, `review-staged` only runs when a developer remembers to type it, which
    makes the review advisory rather than enforced. With it, `git commit` runs the review
    unconditionally and a BLOCK finding aborts the commit.
    """
    hooks_dir = _git_hooks_dir()
    if not hooks_dir:
        click.secho("[CodeGuard] Not inside a git repository -- nothing to install.", fg="red", bold=True)
        sys.exit(1)

    hook_path = os.path.join(hooks_dir, HOOK_FILENAME)
    installed = os.path.exists(hook_path) and HOOK_MARKER in _read_text(hook_path)

    if uninstall:
        if not os.path.exists(hook_path):
            click.secho("[CodeGuard] No pre-commit hook to remove.", fg="yellow")
            return
        if not installed:
            click.secho(
                "[CodeGuard] That pre-commit hook was not installed by devguard; refusing to delete it.",
                fg="red", bold=True,
            )
            raise SystemExit(1)
        os.remove(hook_path)
        click.secho(f"[CodeGuard] Removed {hook_path}", fg="green", bold=True)
        return

    if os.path.exists(hook_path) and not installed and not force:
        click.secho(
            f"[CodeGuard] {hook_path} already exists and was not installed by devguard.",
            fg="red", bold=True,
        )
        click.secho("            Re-run with --force to overwrite it (the existing hook will be lost).", fg="red")
        raise SystemExit(1)

    url_error = _validate_backend_url(backend_url)
    if url_error:
        click.secho(f"[CodeGuard] Invalid --backend-url {backend_url!r}: {url_error}.", fg="red", bold=True)
        raise SystemExit(1)

    os.makedirs(hooks_dir, exist_ok=True)
    script = HOOK_SCRIPT.replace("__BACKEND_URL__", backend_url).replace("{marker}", HOOK_MARKER)
    with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(script)
    # git silently skips a hook it cannot execute.
    os.chmod(hook_path, 0o755)

    click.secho(f"[CodeGuard] Installed pre-commit hook at {hook_path}", fg="green", bold=True)
    click.secho("            Every `git commit` now runs CodeGuard on the staged diff.", fg="green")
    click.secho("            Bypass once with: git commit --no-verify", fg="yellow")


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
