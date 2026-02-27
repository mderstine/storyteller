"""Publish narrative markdown summaries to GitHub.

Requires the `gh` CLI to be installed and authenticated::

    gh auth login

Two publishing modes are supported, controlled by STORYTELLER_GITHUB_PUBLISH_MODE:

* ``gist``  — uploads the file as a GitHub Gist (default).
* ``repo``  — commits the file to a branch in an existing repository.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Gist publishing
# ---------------------------------------------------------------------------


def publish_gist(file: Path, description: str = "", *, public: bool = False) -> str:
    """Upload *file* as a GitHub Gist and return the Gist URL.

    Args:
        file: Path to the markdown file to upload.
        description: Short description shown on the Gist page.
        public: Create a public Gist when ``True``; secret when ``False``.

    Returns:
        The URL of the created Gist.

    Raises:
        subprocess.CalledProcessError: If the ``gh`` command fails.
        FileNotFoundError: If ``gh`` is not installed.
    """
    cmd = ["gh", "gist", "create", str(file)]
    if description:
        cmd += ["--desc", description]
    if public:
        cmd.append("--public")

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Repository publishing
# ---------------------------------------------------------------------------


def publish_to_repo(
    file: Path,
    repo: str,
    repo_path: str = "summaries/",
    commit_message: str = "",
) -> str:
    """Commit *file* to an existing GitHub repository and return the file URL.

    The file is pushed directly via the GitHub Contents API using ``gh api``.
    The repository must already exist and the authenticated user must have
    write access.

    Args:
        file: Path to the markdown file to publish.
        repo: Repository in ``owner/repo`` form.
        repo_path: Directory path inside the repo (trailing slash optional).
        commit_message: Commit message; defaults to "Add <filename>".

    Returns:
        The HTML URL of the committed file on GitHub.

    Raises:
        subprocess.CalledProcessError: If the ``gh`` command fails.
        FileNotFoundError: If ``gh`` is not installed.
        ValueError: If *repo* is empty.
    """
    if not repo:
        raise ValueError(
            "STORYTELLER_GITHUB_REPO must be set to 'owner/repo' for repo mode."
        )

    target_path = repo_path.rstrip("/") + "/" + file.name
    message = commit_message or f"Add {file.name}"

    # Encode file content as base64 inline via shell substitution is unreliable
    # across platforms; read and encode in Python instead.
    import base64

    content_b64 = base64.b64encode(file.read_bytes()).decode()

    # Check whether the file already exists so we can include the blob SHA
    # (required by the GitHub API for updates).
    sha_args: list[str] = []
    check = subprocess.run(
        [
            "gh", "api",
            f"repos/{repo}/contents/{target_path}",
            "--jq", ".sha",
        ],
        capture_output=True,
        text=True,
    )
    existing_sha = check.stdout.strip()
    if existing_sha:
        sha_args = ["-f", f"sha={existing_sha}"]

    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{repo}/contents/{target_path}",
            "--method", "PUT",
            "-f", f"message={message}",
            "-f", f"content={content_b64}",
            *sha_args,
            "--jq", ".content.html_url",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()
