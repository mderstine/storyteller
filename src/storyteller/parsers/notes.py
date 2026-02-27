"""Parse markdown and text note files into Events."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from dateutil import parser as dateparser

from storyteller.models import Event, SourceType


_DATE_PATTERN = re.compile(r"(\d{4}[-_]\d{2}[-_]\d{2})")


def _extract_date_from_filename(path: Path) -> datetime | None:
    match = _DATE_PATTERN.search(path.stem)
    if match:
        date_str = match.group(1).replace("_", "-")
        try:
            return dateparser.parse(date_str)
        except (ValueError, OverflowError):
            return None
    return None


def _extract_date_from_content(content: str) -> datetime | None:
    for line in content.split("\n")[:10]:
        match = _DATE_PATTERN.search(line)
        if match:
            date_str = match.group(1).replace("_", "-")
            try:
                return dateparser.parse(date_str)
            except (ValueError, OverflowError):
                continue
    return None


def _extract_title(content: str, path: Path) -> str:
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line and not line.startswith("#"):
            break
    return path.stem.replace("_", " ").replace("-", " ").title()


def parse_notes(path: Path) -> list[Event]:
    """Parse .md and .txt files from a directory or single file."""
    events: list[Event] = []
    files: list[Path] = []

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob("**/*.md")) + sorted(path.glob("**/*.txt"))

    for file in files:
        content = file.read_text(errors="replace")
        timestamp = (
            _extract_date_from_filename(file)
            or _extract_date_from_content(content)
            or datetime.fromtimestamp(file.stat().st_mtime)
        )
        title = _extract_title(content, file)
        summary = content[:500].strip()

        events.append(
            Event(
                timestamp=timestamp,
                source_type=SourceType.NOTES,
                title=title,
                summary=summary,
                raw_content=content,
                metadata={"file": str(file)},
            )
        )

    return events
