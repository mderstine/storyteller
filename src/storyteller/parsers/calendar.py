"""Parse ICS calendar files into Events."""

from __future__ import annotations

from datetime import datetime, date
from pathlib import Path

from icalendar import Calendar

from storyteller.models import Event, SourceType


def _to_datetime(dt_value: datetime | date) -> datetime:
    if isinstance(dt_value, datetime):
        return dt_value.replace(tzinfo=None)
    return datetime(dt_value.year, dt_value.month, dt_value.day)


def parse_calendar(path: Path) -> list[Event]:
    """Parse .ics files from a directory or single file."""
    events: list[Event] = []
    files: list[Path] = []

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob("**/*.ics"))

    for file in files:
        cal = Calendar.from_ical(file.read_bytes())
        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            dtstart = component.get("dtstart")
            if dtstart is None:
                continue
            timestamp = _to_datetime(dtstart.dt)

            summary_val = component.get("summary", "")
            title = str(summary_val) if summary_val else "Untitled Event"

            description = str(component.get("description", ""))
            location = str(component.get("location", ""))

            metadata: dict[str, str] = {"file": str(file)}
            if location:
                metadata["location"] = location

            dtend = component.get("dtend")
            if dtend:
                metadata["end"] = _to_datetime(dtend.dt).isoformat()

            events.append(
                Event(
                    timestamp=timestamp,
                    source_type=SourceType.CALENDAR,
                    title=title,
                    summary=description[:500] if description else "",
                    raw_content=description,
                    metadata=metadata,
                )
            )

    return events
