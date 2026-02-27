"""Tests for storyteller parsers."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from storyteller.models import SourceType
from storyteller.parsers.notes import parse_notes
from storyteller.parsers.calendar import parse_calendar
from storyteller.parsers.copilot_sessions import parse_copilot_sessions
from storyteller.parsers.github_repo import parse_github_repo


@pytest.fixture
def tmp_data(tmp_path: Path) -> Path:
    return tmp_path


class TestNotesParser:
    def test_parse_md_with_date_in_filename(self, tmp_data: Path) -> None:
        f = tmp_data / "2025-01-15-standup.md"
        f.write_text("# Standup Notes\n\n- Did thing A\n- Did thing B\n")

        events = parse_notes(f)
        assert len(events) == 1
        assert events[0].source_type == SourceType.NOTES
        assert events[0].title == "Standup Notes"
        assert events[0].timestamp.date() == datetime(2025, 1, 15).date()

    def test_parse_md_with_date_in_content(self, tmp_data: Path) -> None:
        f = tmp_data / "notes.md"
        f.write_text("# Meeting Notes\n2025-03-20\n\nDiscussed roadmap.\n")

        events = parse_notes(f)
        assert len(events) == 1
        assert events[0].timestamp.date() == datetime(2025, 3, 20).date()

    def test_parse_txt_file(self, tmp_data: Path) -> None:
        f = tmp_data / "todo.txt"
        f.write_text("Buy groceries\nClean house\n")

        events = parse_notes(f)
        assert len(events) == 1
        assert events[0].source_type == SourceType.NOTES

    def test_parse_directory(self, tmp_data: Path) -> None:
        (tmp_data / "a.md").write_text("# Note A\n")
        (tmp_data / "b.txt").write_text("Note B\n")
        (tmp_data / "c.py").write_text("# not a note\n")  # should be ignored

        events = parse_notes(tmp_data)
        assert len(events) == 2

    def test_empty_directory(self, tmp_data: Path) -> None:
        events = parse_notes(tmp_data)
        assert events == []

    def test_title_from_filename_when_no_heading(self, tmp_data: Path) -> None:
        f = tmp_data / "my-cool-notes.md"
        f.write_text("Just some text without a heading.\n")

        events = parse_notes(f)
        assert events[0].title == "My Cool Notes"


class TestCalendarParser:
    def test_parse_ics_file(self, tmp_data: Path) -> None:
        ics_content = """\
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20250115T100000
DTEND:20250115T110000
SUMMARY:Team Standup
DESCRIPTION:Daily standup meeting
LOCATION:Room 42
END:VEVENT
BEGIN:VEVENT
DTSTART:20250115T140000
DTEND:20250115T150000
SUMMARY:1:1 with Manager
END:VEVENT
END:VCALENDAR
"""
        f = tmp_data / "calendar.ics"
        f.write_text(ics_content)

        events = parse_calendar(f)
        assert len(events) == 2
        assert events[0].source_type == SourceType.CALENDAR
        assert events[0].title == "Team Standup"
        assert events[0].metadata.get("location") == "Room 42"
        assert events[1].title == "1:1 with Manager"

    def test_empty_calendar(self, tmp_data: Path) -> None:
        f = tmp_data / "empty.ics"
        f.write_text("BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR\n")

        events = parse_calendar(f)
        assert events == []


class TestCopilotSessionsParser:
    def test_parse_single_session(self, tmp_data: Path) -> None:
        session = {
            "timestamp": "2025-01-15T09:30:00",
            "title": "Refactoring auth module",
            "content": "Helped refactor the authentication module to use JWT.",
        }
        f = tmp_data / "session.json"
        f.write_text(json.dumps(session))

        events = parse_copilot_sessions(f)
        assert len(events) == 1
        assert events[0].source_type == SourceType.COPILOT
        assert events[0].title == "Refactoring auth module"

    def test_parse_session_list(self, tmp_data: Path) -> None:
        sessions = [
            {"timestamp": "2025-01-15T09:00:00", "title": "Session 1"},
            {"timestamp": "2025-01-15T14:00:00", "title": "Session 2"},
        ]
        f = tmp_data / "sessions.json"
        f.write_text(json.dumps(sessions))

        events = parse_copilot_sessions(f)
        assert len(events) == 2

    def test_skip_invalid_json(self, tmp_data: Path) -> None:
        f = tmp_data / "bad.json"
        f.write_text("not valid json{{{")

        events = parse_copilot_sessions(f)
        assert events == []

    def test_unix_timestamp(self, tmp_data: Path) -> None:
        session = {"timestamp": 1736935800, "title": "Unix time session"}
        f = tmp_data / "unix.json"
        f.write_text(json.dumps(session))

        events = parse_copilot_sessions(f)
        assert len(events) == 1


class TestGitHubRepoParser:
    def test_parse_current_repo(self) -> None:
        # Parse the storyteller repo itself
        repo_path = Path(__file__).resolve().parents[1]
        if not (repo_path / ".git").exists():
            pytest.skip("Not in a git repo")

        events = parse_github_repo(repo_path)
        # May have no commits yet if repo is freshly initialized
        assert isinstance(events, list)
        for e in events:
            assert e.source_type == SourceType.GITHUB
            assert e.metadata.get("commit")

    def test_non_repo_directory(self, tmp_data: Path) -> None:
        events = parse_github_repo(tmp_data)
        assert events == []

    def test_non_existent_path(self, tmp_data: Path) -> None:
        events = parse_github_repo(tmp_data / "nonexistent")
        assert events == []
