from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    COPILOT = "copilot"
    CALENDAR = "calendar"
    EMAIL = "email"
    GITHUB = "github"
    NOTES = "notes"


@dataclass
class Event:
    timestamp: datetime
    source_type: SourceType
    title: str
    summary: str = ""
    raw_content: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        d["source_type"] = self.source_type.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Event:
        return cls(
            timestamp=datetime.fromisoformat(d["timestamp"]),
            source_type=SourceType(d["source_type"]),
            title=d["title"],
            summary=d.get("summary", ""),
            raw_content=d.get("raw_content", ""),
            metadata=d.get("metadata", {}),
        )


@dataclass
class Timeline:
    events: list[Event] = field(default_factory=list)

    def add(self, event: Event) -> None:
        self.events.append(event)

    def extend(self, events: list[Event]) -> None:
        self.events.extend(events)

    def sort(self) -> None:
        self.events.sort(key=lambda e: e.timestamp)

    def filter_by_date(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> Timeline:
        filtered = self.events
        if start:
            filtered = [e for e in filtered if e.timestamp >= start]
        if end:
            filtered = [e for e in filtered if e.timestamp <= end]
        return Timeline(events=filtered)

    def filter_by_source(self, *sources: SourceType) -> Timeline:
        return Timeline(events=[e for e in self.events if e.source_type in sources])

    def group_by_day(self) -> dict[str, list[Event]]:
        groups: dict[str, list[Event]] = {}
        for event in self.events:
            key = event.timestamp.strftime("%Y-%m-%d")
            groups.setdefault(key, []).append(event)
        return groups

    def group_by_week(self) -> dict[str, list[Event]]:
        groups: dict[str, list[Event]] = {}
        for event in self.events:
            iso = event.timestamp.isocalendar()
            key = f"{iso.year}-W{iso.week:02d}"
            groups.setdefault(key, []).append(event)
        return groups

    def to_json(self) -> str:
        return json.dumps([e.to_dict() for e in self.events], indent=2)

    @classmethod
    def from_json(cls, data: str) -> Timeline:
        return cls(events=[Event.from_dict(d) for d in json.loads(data)])


@dataclass
class NarrativeContext:
    period: str
    date_range: str
    timeline: Timeline
    source_summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "period": self.period,
            "date_range": self.date_range,
            "source_summary": self.source_summary,
            "events": [e.to_dict() for e in self.timeline.events],
        }
