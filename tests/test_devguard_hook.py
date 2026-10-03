"""The devguard pre-commit installer.

The hook is what turns CodeGuard from advice into a gate, so these tests pin the things
that silently break it: a CRLF shebang, a missing exec bit, and clobbering a developer's
own pre-commit hook.
"""
import subprocess

import pytest
from click.testing import CliRunner

from cli import devguard


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A throwaway git repo the CLI treats as its working tree."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _hook_path(repo):
    return repo / ".git" / "hooks" / "pre-commit"


def test_install_writes_a_runnable_hook(repo):
    result = CliRunner().invoke(devguard.cli, ["install-hook"])

    assert result.exit_code == 0, result.output
    hook = _hook_path(repo)
    assert hook.exists()

    raw = hook.read_bytes()
    assert raw.startswith(b"#!/bin/sh"), "the hook must be a shell script"
    assert b"\r\n" not in raw, "a CRLF shebang makes the hook unrunnable under Git Bash"
    assert devguard.HOOK_MARKER.encode() in raw
    assert b"review-staged" in raw


def test_install_bakes_in_the_backend_url(repo):
    CliRunner().invoke(devguard.cli, ["install-hook", "--backend-url", "http://127.0.0.1:8123"])

    assert "http://127.0.0.1:8123" in _hook_path(repo).read_text(encoding="utf-8")


def test_reinstall_is_idempotent(repo):
    CliRunner().invoke(devguard.cli, ["install-hook"])
    result = CliRunner().invoke(devguard.cli, ["install-hook"])

    assert result.exit_code == 0, "our own hook must be replaceable without --force"


def test_install_refuses_to_clobber_a_developer_hook(repo):
    hook = _hook_path(repo)
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho mine\n", encoding="utf-8")

    result = CliRunner().invoke(devguard.cli, ["install-hook"])

    assert result.exit_code == 1
    assert hook.read_text(encoding="utf-8") == "#!/bin/sh\necho mine\n"


def test_force_overwrites_a_developer_hook(repo):
    hook = _hook_path(repo)
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho mine\n", encoding="utf-8")

    result = CliRunner().invoke(devguard.cli, ["install-hook", "--force"])

    assert result.exit_code == 0
    assert devguard.HOOK_MARKER in hook.read_text(encoding="utf-8")


def test_uninstall_removes_our_hook(repo):
    CliRunner().invoke(devguard.cli, ["install-hook"])
    assert _hook_path(repo).exists()

    result = CliRunner().invoke(devguard.cli, ["install-hook", "--uninstall"])

    assert result.exit_code == 0
    assert not _hook_path(repo).exists()


def test_uninstall_leaves_a_developer_hook_alone(repo):
    hook = _hook_path(repo)
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho mine\n", encoding="utf-8")

    result = CliRunner().invoke(devguard.cli, ["install-hook", "--uninstall"])

    assert result.exit_code == 1
    assert hook.exists(), "someone else's hook must survive an uninstall"


def test_install_outside_a_git_repo_fails_cleanly(tmp_path, monkeypatch):
    # Stop git walking up into an enclosing repository on the developer's machine.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(devguard.cli, ["install-hook"])

    assert result.exit_code == 1
    assert "Not inside a git repository" in result.output
