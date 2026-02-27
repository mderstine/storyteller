"""Publish narrative markdown summaries to GitHub.

No third-party tools required — uses only the Python standard library and
plain ``git`` commands that ship with every developer machine.

Two publishing modes are supported, controlled by STORYTELLER_GITHUB_PUBLISH_MODE:

* ``gist`` — uploads the file via the GitHub Gist REST API (requires GITHUB_TOKEN).
* ``repo`` — clones the target repository with plain git, commits the file, and pushes.

Authentication
--------------
Set ``GITHUB_TOKEN`` (or ``STORYTELLER_GITHUB_TOKEN``) in your ``.env`` file.

For **gist** mode the token is sent as a Bearer header.

For **repo** mode the token is used in the HTTPS clone URL
(``https://x-access-token:<token>@github.com/…``).  If no token is set the
clone URL falls back to plain HTTPS or SSH, which works if the system already
has git credentials configured (e.g. an SSH key or a credential helper).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _token() -> str:
    return os.getenv("GITHUB_TOKEN") or os.getenv("STORYTELLER_GITHUB_TOKEN") or ""


def _api_request(method: str, url: str, payload: dict | None = None) -> dict:
    token = _token()
    if not token:
        raise ValueError(
            "GITHUB_TOKEN is required. Set it in your .env file or environment."
        )
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        raise RuntimeError(f"GitHub API error {exc.code}: {body}") from exc


# ---------------------------------------------------------------------------
# Gist publishing
# ---------------------------------------------------------------------------


def publish_gist(file: Path, description: str = "", *, public: bool = False) -> str:
    """Upload *file* as a GitHub Gist via the REST API and return the Gist URL.

    Args:
        file: Path to the markdown file to upload.
        description: Short description shown on the Gist page.
        public: Create a public Gist when ``True``; secret when ``False``.

    Returns:
        The HTML URL of the created Gist.

    Raises:
        ValueError: If ``GITHUB_TOKEN`` is not set.
        RuntimeError: If the GitHub API returns an error response.
    """
    result = _api_request(
        "POST",
        "https://api.github.com/gists",
        {
            "description": description,
            "public": public,
            "files": {file.name: {"content": file.read_text()}},
        },
    )
    return result["html_url"]


# ---------------------------------------------------------------------------
# Repository publishing
# ---------------------------------------------------------------------------


def publish_to_repo(
    file: Path,
    repo: str,
    repo_path: str = "summaries/",
    commit_message: str = "",
) -> str:
    """Commit *file* to a GitHub repository using plain git and return the file URL.

    Clones the repository to a temporary directory, copies the file, commits it,
    and pushes.  The temporary directory is deleted automatically when done.

    Authentication uses ``GITHUB_TOKEN`` via the HTTPS clone URL when set;
    otherwise relies on the system's existing git credentials or SSH config.

    Args:
        file: Path to the markdown file to publish.
        repo: Repository in ``owner/repo`` form.
        repo_path: Directory path inside the repo where the file is placed.
        commit_message: Commit message; defaults to "Add <filename>".

    Returns:
        The GitHub URL of the committed file.

    Raises:
        ValueError: If *repo* is empty.
        subprocess.CalledProcessError: If a git command fails.
        FileNotFoundError: If ``git`` is not installed.
    """
    if not repo:
        raise ValueError(
            "STORYTELLER_GITHUB_REPO must be set to 'owner/repo' for repo mode."
        )

    token = _token()
    if token:
        remote = f"https://x-access-token:{token}@github.com/{repo}.git"
    else:
        remote = f"https://github.com/{repo}.git"

    message = commit_message or f"Add {file.name}"
    target_subpath = repo_path.strip("/") + "/" + file.name

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        subprocess.run(
            ["git", "clone", "--depth=1", remote, tmpdir],
            check=True,
            capture_output=True,
        )

        target = tmp / target_subpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(file.read_bytes())

        subprocess.run(
            ["git", "-C", tmpdir, "add", target_subpath],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", tmpdir, "commit", "-m", message],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", tmpdir, "push"],
            check=True,
            capture_output=True,
        )

        branch = subprocess.run(
            ["git", "-C", tmpdir, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
        ).stdout.strip() or "main"

    return f"https://github.com/{repo}/blob/{branch}/{target_subpath}"
