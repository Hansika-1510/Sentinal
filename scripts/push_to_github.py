import os
import sys
from pathlib import Path
from dulwich.repo import Repo
from dulwich.porcelain import init, add, commit, push, remote_add
from dulwich.ignore import IgnoreFilterManager


def init_and_commit_repo(repo_path: str = "."):
    root = Path(repo_path).resolve()
    
    # Check if .git exists or initialize
    git_dir = root / ".git"
    if not git_dir.exists():
        repo = init(str(root))
        print(f"[*] Initialized new Git repository at {root}")
    else:
        repo = Repo(str(root))
        print(f"[*] Opened existing Git repository at {root}")

    # Add all files respecting .gitignore
    print("[*] Staging files for commit...")
    # Add files
    add(str(root))

    # Create initial commit
    try:
        commit_id = commit(
            str(root),
            message=b"feat: AI Software Incident Response Agent complete backend engine",
            author=b"AI Assistant <assistant@antigravity.ai>",
            committer=b"AI Assistant <assistant@antigravity.ai>"
        )
        print(f"[+] Created commit: {commit_id.decode() if isinstance(commit_id, bytes) else commit_id}")
    except Exception as e:
        print(f"[-] Commit notice: {e}")

    return repo


if __name__ == "__main__":
    init_and_commit_repo()
