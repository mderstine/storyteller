"""Tests for storyteller timeline and output modules."""

from datetime import datetime
from pathlib import Path

from storyteller.models import Event, SourceType, Timeline
from storyteller.output import (
    build_narrative_context,
    render_timeline_md,
    render_narrative_context_md,
)
from storyteller.timeline import build_timeline, detect_source_type


def _make_event(
    ts: str = "2025-01-15T10:00:00",
    source: SourceType = SourceType.NOTES,
    title: str = "Test Event",
) -> Event:
    return Event(
        timestamp=datetime.fromisoformat(ts),
        source_type=source,
        title=title,
    )


class TestTimeline:
    def test_sort(self) -> None:
        tl = Timeline(
            events=[
                _make_event("2025-01-15T14:00:00"),
                _make_event("2025-01-15T09:00:00"),
                _make_event("2025-01-15T11:00:00"),
            ]
        )
        tl.sort()
        assert tl.events[0].timestamp.hour == 9
        assert tl.events[1].timestamp.hour == 11
        assert tl.events[2].timestamp.hour == 14

    def test_filter_by_date(self) -> None:
        tl = Timeline(
            events=[
                _make_event("2025-01-14T10:00:00"),
                _make_event("2025-01-15T10:00:00"),
                _make_event("2025-01-16T10:00:00"),
            ]
        )
        filtered = tl.filter_by_date(
            start=datetime(2025, 1, 15),
            end=datetime(2025, 1, 15, 23, 59),
        )
        assert len(filtered.events) == 1
        assert filtered.events[0].timestamp.day == 15

    def test_filter_by_source(self) -> None:
        tl = Timeline(
            events=[
                _make_event(source=SourceType.NOTES),
                _make_event(source=SourceType.CALENDAR),
                _make_event(source=SourceType.GITHUB),
            ]
        )
        filtered = tl.filter_by_source(SourceType.NOTES, SourceType.GITHUB)
        assert len(filtered.events) == 2

    def test_group_by_day(self) -> None:
        tl = Timeline(
            events=[
                _make_event("2025-01-15T09:00:00"),
                _make_event("2025-01-15T14:00:00"),
                _make_event("2025-01-16T10:00:00"),
            ]
        )
        groups = tl.group_by_day()
        assert len(groups) == 2
        assert len(groups["2025-01-15"]) == 2
        assert len(groups["2025-01-16"]) == 1

    def test_json_roundtrip(self) -> None:
        events = [
            _make_event("2025-01-15T10:00:00", SourceType.NOTES, "Note"),
            _make_event("2025-01-15T14:00:00", SourceType.CALENDAR, "Meeting"),
        ]
        tl = Timeline(events=events)
        json_str = tl.to_json()
        restored = Timeline.from_json(json_str)

        assert len(restored.events) == 2
        assert restored.events[0].title == "Note"
        assert restored.events[1].source_type == SourceType.CALENDAR


class TestBuildTimeline:
    def test_build_with_filters(self) -> None:
        events = [
            _make_event("2025-01-14T10:00:00", SourceType.NOTES),
            _make_event("2025-01-15T10:00:00", SourceType.CALENDAR),
            _make_event("2025-01-16T10:00:00", SourceType.GITHUB),
        ]
        tl = build_timeline(
            events,
            start=datetime(2025, 1, 15),
            sources=[SourceType.CALENDAR],
        )
        assert len(tl.events) == 1
        assert tl.events[0].source_type == SourceType.CALENDAR


class TestDetectSourceType:
    def test_detect_md(self, tmp_path: Path) -> None:
        f = tmp_path / "notes.md"
        f.touch()
        assert detect_source_type(f) == SourceType.NOTES

    def test_detect_ics(self, tmp_path: Path) -> None:
        f = tmp_path / "cal.ics"
        f.touch()
        assert detect_source_type(f) == SourceType.CALENDAR

    def test_detect_msg(self, tmp_path: Path) -> None:
        f = tmp_path / "email.msg"
        f.touch()
        assert detect_source_type(f) == SourceType.EMAIL

    def test_detect_git_repo(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        assert detect_source_type(tmp_path) == SourceType.GITHUB

    def test_unknown_returns_none(self, tmp_path: Path) -> None:
        f = tmp_path / "data.csv"
        f.touch()
        assert detect_source_type(f) is None


class TestOutput:
    def test_render_timeline_md(self) -> None:
        tl = Timeline(
            events=[
                _make_event("2025-01-15T10:00:00", SourceType.NOTES, "Morning Note"),
                _make_event(
                    "2025-01-15T14:00:00", SourceType.CALENDAR, "Afternoon Meeting"
                ),
            ]
        )
        md = render_timeline_md(tl)
        assert "## 2025-01-15" in md
        assert "Morning Note" in md
        assert "Afternoon Meeting" in md
        assert "[notes]" in md
        assert "[calendar]" in md

    def test_narrative_context(self) -> None:
        tl = Timeline(
            events=[
                _make_event("2025-01-15T10:00:00", SourceType.NOTES, "Note"),
                _make_event("2025-01-15T14:00:00", SourceType.CALENDAR, "Meeting"),
            ]
        )
        ctx = build_narrative_context(tl, period="day", date_range="2025-01-15")
        assert ctx.source_summary["notes"] == 1
        assert ctx.source_summary["calendar"] == 1

        md = render_narrative_context_md(ctx)
        assert "Narrative Context: day" in md
        assert "2025-01-15" in md
