"""Parse Outlook .msg email files into Events."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from storyteller.models import Event, SourceType


def parse_msg(path: Path) -> list[Event]:
    """Parse .msg files from a directory or single file."""
    import extract_msg

    events: list[Event] = []
    files: list[Path] = []

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob("**/*.msg"))

    for file in files:
        msg = extract_msg.Message(str(file))
        try:
            timestamp = msg.date
            if timestamp is None:
                timestamp = datetime.fromtimestamp(file.stat().st_mtime)
            elif isinstance(timestamp, str):
                from dateutil import parser as dateparser

                timestamp = dateparser.parse(timestamp)

            # Strip timezone info for consistency
            if hasattr(timestamp, "tzinfo") and timestamp.tzinfo is not None:
                timestamp = timestamp.replace(tzinfo=None)

            title = msg.subject or "Untitled Email"
            body = msg.body or ""
            sender = msg.sender or ""

            metadata: dict[str, str] = {"file": str(file)}
            if sender:
                metadata["sender"] = sender
            recipients = msg.to
            if recipients:
                metadata["to"] = recipients

            events.append(
                Event(
                    timestamp=timestamp,
                    source_type=SourceType.EMAIL,
                    title=title,
                    summary=body[:500].strip(),
                    raw_content=body,
                    metadata=metadata,
                )
            )
        finally:
            msg.close()

    return events
