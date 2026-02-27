"""Parse GitHub repo activity from git log into Events."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from storyteller.models import Event, SourceType


def parse_github_repo(path: Path) -> list[Event]:
    """Parse git log from a local repository."""
    events: list[Event] = []

    if not path.is_dir():
        return events

    git_dir = path / ".git"
    if not git_dir.exists():
        return events

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(path),
                "log",
                "--format=%H%n%aI%n%an%n%s%n%b%n---END---",
                "--no-merges",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return events

    if result.returncode != 0:
        return events

    raw = result.stdout.strip()
    if not raw:
        return events

    entries = raw.split("---END---")
    for entry in entries:
        lines = entry.strip().split("\n")
        if len(lines) < 4:
            continue

        commit_hash = lines[0].strip()
        try:
            timestamp = datetime.fromisoformat(lines[1].strip())
            if timestamp.tzinfo is not None:
                timestamp = timestamp.replace(tzinfo=None)
        except ValueError:
            continue
        author = lines[2].strip()
        subject = lines[3].strip()
        body = "\n".join(lines[4:]).strip()

        events.append(
            Event(
                timestamp=timestamp,
                source_type=SourceType.GITHUB,
                title=subject,
                summary=body[:500] if body else subject,
                raw_content=body,
                metadata={
                    "commit": commit_hash,
                    "author": author,
                    "repo": str(path),
                },
            )
        )

    return events
