"""Runtime configuration loaded from environment / .env file."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Data paths
# ---------------------------------------------------------------------------

#: Directory storyteller scans when no explicit path is passed to `ingest`.
DATA_DIR: Path = Path(os.getenv("STORYTELLER_DATA_DIR", "data"))

#: Default directory for all generated output files.
OUTPUT_DIR: Path = Path(os.getenv("STORYTELLER_OUTPUT_DIR", "output"))

#: Path to the structured JSON produced by the ingest step.
INGESTED_FILE: Path = Path(
    os.getenv("STORYTELLER_INGESTED_FILE", str(OUTPUT_DIR / "ingested.json"))
)

# ---------------------------------------------------------------------------
# GitHub publishing
# ---------------------------------------------------------------------------

#: Publishing mode: "gist" (default) or "repo".
GITHUB_PUBLISH_MODE: str = os.getenv("STORYTELLER_GITHUB_PUBLISH_MODE", "gist")

#: Target repository in "owner/repo" form — required when mode is "repo".
GITHUB_REPO: str = os.getenv("STORYTELLER_GITHUB_REPO", "")

#: Path prefix inside the repo where summaries are written (mode "repo").
GITHUB_REPO_PATH: str = os.getenv("STORYTELLER_GITHUB_REPO_PATH", "summaries/")

#: Create public gists when True; secret gists when False (mode "gist").
GITHUB_GIST_PUBLIC: bool = (
    os.getenv("STORYTELLER_GITHUB_GIST_PUBLIC", "false").lower() == "true"
)
