"""Merge parsed events into a unified timeline."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from storyteller.models import Event, SourceType, Timeline
from storyteller.parsers import (
    parse_calendar,
    parse_copilot_sessions,
    parse_github_repo,
    parse_msg,
    parse_notes,
)

_PARSERS: dict[SourceType, Callable[[Path], list[Event]]] = {
    SourceType.NOTES: parse_notes,
    SourceType.CALENDAR: parse_calendar,
    SourceType.EMAIL: parse_msg,
    SourceType.COPILOT: parse_copilot_sessions,
    SourceType.GITHUB: parse_github_repo,
}

_EXT_TO_SOURCE: dict[str, SourceType] = {
    ".md": SourceType.NOTES,
    ".txt": SourceType.NOTES,
    ".ics": SourceType.CALENDAR,
    ".msg": SourceType.EMAIL,
    ".json": SourceType.COPILOT,
}


def detect_source_type(path: Path) -> SourceType | None:
    """Auto-detect source type from file extension or directory contents."""
    if path.is_file():
        return _EXT_TO_SOURCE.get(path.suffix.lower())
    if path.is_dir():
        if (path / ".git").exists():
            return SourceType.GITHUB
    return None


def ingest(path: Path, source_type: SourceType | None = None) -> list[Event]:
    """Ingest data from a path, auto-detecting source type if not specified."""
    if source_type is None:
        source_type = detect_source_type(path)

    if source_type is None:
        # Try all parsers for directories
        if path.is_dir():
            return ingest_directory(path)
        return []

    parser = _PARSERS[source_type]
    return parser(path)


def ingest_directory(path: Path) -> list[Event]:
    """Ingest all recognizable files from a directory."""
    events: list[Event] = []

    # Check if it's a git repo
    if (path / ".git").exists():
        events.extend(parse_github_repo(path))

    # Parse by extension
    for file in sorted(path.rglob("*")):
        if not file.is_file():
            continue
        source = _EXT_TO_SOURCE.get(file.suffix.lower())
        if source:
            parser = _PARSERS[source]
            events.extend(parser(file))

    return events


def build_timeline(
    events: list[Event],
    start: datetime | None = None,
    end: datetime | None = None,
    sources: list[SourceType] | None = None,
) -> Timeline:
    """Build a sorted, filtered timeline from events."""
    tl = Timeline(events=list(events))
    tl.sort()

    if start or end:
        tl = tl.filter_by_date(start=start, end=end)

    if sources:
        tl = tl.filter_by_source(*sources)

    return tl
