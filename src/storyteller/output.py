"""Format structured timeline data as Markdown for Copilot consumption."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from storyteller.models import Event, NarrativeContext, Timeline


def _format_event_md(event: Event) -> str:
    """Format a single event as a Markdown list item."""
    time_str = event.timestamp.strftime("%H:%M")
    source_tag = f"[{event.source_type.value}]"
    lines = [f"- **{time_str}** {source_tag} {event.title}"]
    if event.summary:
        # Indent summary and truncate
        summary = event.summary.replace("\n", " ").strip()
        if len(summary) > 200:
            summary = summary[:200] + "..."
        lines.append(f"  > {summary}")
    return "\n".join(lines)


def render_timeline_md(timeline: Timeline) -> str:
    """Render a timeline as a Markdown document."""
    timeline.sort()
    groups = timeline.group_by_day()

    sections: list[str] = []
    for day, events in sorted(groups.items()):
        sections.append(f"## {day}\n")
        for event in events:
            sections.append(_format_event_md(event))
        sections.append("")

    return "\n".join(sections)


def render_narrative_context_md(context: NarrativeContext) -> str:
    """Render a narrative context document for Copilot to consume."""
    lines: list[str] = [
        f"# Narrative Context: {context.period}",
        f"**Date range:** {context.date_range}",
        "",
        "## Source Summary",
    ]

    for source, count in sorted(context.source_summary.items()):
        lines.append(f"- {source}: {count} events")

    lines.append("")
    lines.append("## Events")
    lines.append("")
    lines.append(render_timeline_md(context.timeline))

    return "\n".join(lines)


def build_narrative_context(
    timeline: Timeline, period: str, date_range: str
) -> NarrativeContext:
    """Build a NarrativeContext from a timeline."""
    source_counts = Counter(e.source_type.value for e in timeline.events)
    return NarrativeContext(
        period=period,
        date_range=date_range,
        timeline=timeline,
        source_summary=dict(source_counts),
    )


def render_activity_digest_md(timeline: Timeline, period: str, date_range: str) -> str:
    """Render a focused Copilot + git activity digest for the given period.

    Structures events by source type and day so the storyteller agent can
    quickly scan what was worked on and identify themes.
    """
    timeline.sort()

    copilot_events = [e for e in timeline.events if e.source_type.value == "copilot"]
    github_events = [e for e in timeline.events if e.source_type.value == "github"]

    lines: list[str] = [
        f"# Activity Digest: {period} — {date_range}",
        "",
        "## At a Glance",
        f"- **Copilot sessions:** {len(copilot_events)}",
    ]

    repos = {e.metadata.get("repo", "unknown") for e in github_events}
    lines.append(
        f"- **Git commits:** {len(github_events)}"
        + (f" across {len(repos)} repositories" if repos else "")
    )
    lines.append("")

    # ------------------------------------------------------------------
    # Copilot sessions grouped by day
    # ------------------------------------------------------------------
    lines.append("## Copilot Sessions")
    lines.append("")

    if not copilot_events:
        lines.append("_No Copilot sessions recorded for this period._")
        lines.append("")
    else:
        copilot_tl = Timeline(events=copilot_events)
        for day, events in sorted(copilot_tl.group_by_day().items()):
            lines.append(f"### {day}")
            for event in events:
                time_str = event.timestamp.strftime("%H:%M")
                lines.append(f"- **{time_str}** {event.title}")
                if event.summary:
                    summary = event.summary.replace("\n", " ").strip()
                    if len(summary) > 300:
                        summary = summary[:300] + "..."
                    lines.append(f"  > {summary}")
            lines.append("")

    # ------------------------------------------------------------------
    # Git commits grouped by repository
    # ------------------------------------------------------------------
    lines.append("## Git Commits")
    lines.append("")

    if not github_events:
        lines.append("_No git commits recorded for this period._")
        lines.append("")
    else:
        by_repo: dict[str, list] = {}
        for event in github_events:
            repo = event.metadata.get("repo", "unknown")
            by_repo.setdefault(repo, []).append(event)

        for repo, events in sorted(by_repo.items()):
            lines.append(f"### {repo}")
            for event in sorted(events, key=lambda e: e.timestamp):
                commit = event.metadata.get("commit", "")
                sha = commit[:7] if commit else "·"
                lines.append(f"- `{sha}` {event.title}")
                if event.summary:
                    body = event.summary.replace("\n", " ").strip()
                    if len(body) > 200:
                        body = body[:200] + "..."
                    lines.append(f"  > {body}")
            lines.append("")

    # ------------------------------------------------------------------
    # Topics: word-frequency extraction across all titles + summaries
    # ------------------------------------------------------------------
    _STOP_WORDS = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "can", "not",
        "it", "its", "this", "that", "these", "those", "as", "if", "so",
        "my", "your", "their", "our", "we", "i", "you", "they", "he",
        "she", "add", "adds", "added", "fix", "fixes", "fixed", "update",
        "updates", "updated", "change", "changes", "changed", "remove",
        "removes", "removed", "refactor", "refactors", "refactored",
        "implement", "implements", "implemented", "use", "uses", "used",
    }

    word_counter: Counter[str] = Counter()
    for event in timeline.events:
        for text in (event.title, event.summary):
            for word in text.lower().split():
                word = word.strip(".,;:!?\"'()`[]#*-/\\")
                if len(word) >= 4 and word not in _STOP_WORDS:
                    word_counter[word] += 1

    top_topics = [w for w, _ in word_counter.most_common(15)]

    lines.append("## Topics")
    lines.append("")
    if top_topics:
        lines.append(", ".join(top_topics))
    else:
        lines.append("_No topics extracted._")
    lines.append("")

    return "\n".join(lines)


def write_output(content: str, output_path: Path) -> Path:
    """Write content to a file in the output directory."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    return output_path


def write_timeline_json(timeline: Timeline, output_path: Path) -> Path:
    """Write timeline as JSON for programmatic consumption."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(timeline.to_json())
    return output_path
