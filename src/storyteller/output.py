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
