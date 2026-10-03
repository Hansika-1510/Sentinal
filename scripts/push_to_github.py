import os
import sys
from pathlib import Path
from dulwich.repo import Repo
from dulwich.porcelain import add, commit, push, remote_add, branch_create
from dulwich.client import get_transport_and_path


def push_to_remote(token: str = None, repo_url: str = "https://github.com/Hansika-1510/ai.git"):
    root = Path(".").resolve()
    repo = Repo(str(root))

    # Determine auth URL
    if token:
        # Inject token into https URL for basic auth
        # format: https://<token>@github.com/Hansika-1510/ai.git
        auth_url = repo_url.replace("https://", f"https://{token}@")
    else:
        auth_url = repo_url

    print(f"[*] Pushing code to {repo_url} (main branch)...")
    try:
        # Push to remote main branch
        push(repo, auth_url, refspecs=[b"refs/heads/master:refs/heads/main", b"refs/heads/main:refs/heads/main"])
        print("[+] Successfully pushed code to GitHub!")
        return True
    except Exception as e:
        print(f"[-] Push error: {e}")
        return False


if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GITHUB_TOKEN")
    push_to_remote(token=token)
