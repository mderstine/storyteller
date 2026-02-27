"""Parse GitHub Copilot session cache/log files into Events."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from dateutil import parser as dateparser

from storyteller.models import Event, SourceType


def parse_copilot_sessions(path: Path) -> list[Event]:
    """Parse Copilot session JSON files from a directory or single file."""
    events: list[Event] = []
    files: list[Path] = []

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob("**/*.json"))

    for file in files:
        try:
            data = json.loads(file.read_text(errors="replace"))
        except (json.JSONDecodeError, OSError):
            continue

        if isinstance(data, list):
            sessions = data
        elif isinstance(data, dict):
            sessions = [data]
        else:
            continue

        for session in sessions:
            if not isinstance(session, dict):
                continue

            # Try to extract timestamp from various fields
            timestamp = None
            for ts_field in ("timestamp", "created", "date", "startTime", "time"):
                ts_val = session.get(ts_field)
                if ts_val:
                    try:
                        if isinstance(ts_val, (int, float)):
                            timestamp = datetime.fromtimestamp(ts_val)
                        else:
                            timestamp = dateparser.parse(str(ts_val))
                    except (ValueError, OverflowError, OSError):
                        continue
                    if timestamp:
                        break

            if timestamp is None:
                timestamp = datetime.fromtimestamp(file.stat().st_mtime)

            title = str(
                session.get("title")
                or session.get("name")
                or session.get("prompt", "")[:80]
                or f"Copilot Session ({file.stem})"
            )

            # Build summary from available content
            summary_parts: list[str] = []
            for content_field in ("content", "response", "output", "summary"):
                val = session.get(content_field)
                if val and isinstance(val, str):
                    summary_parts.append(val[:300])

            summary = "\n".join(summary_parts)[:500]

            events.append(
                Event(
                    timestamp=timestamp,
                    source_type=SourceType.COPILOT,
                    title=title,
                    summary=summary,
                    raw_content=json.dumps(session, default=str),
                    metadata={"file": str(file)},
                )
            )

    return events
