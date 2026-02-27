"""CLI entry point for storyteller."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import click

from storyteller.models import SourceType, Timeline
from storyteller.output import (
    build_narrative_context,
    render_narrative_context_md,
    render_timeline_md,
    write_output,
    write_timeline_json,
)
from storyteller.timeline import build_timeline, ingest


@click.group()
def cli() -> None:
    """Storyteller: craft narratives from scattered work data."""


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--source-type",
    type=click.Choice(["auto", "copilot", "calendar", "msg", "github", "notes"]),
    default="auto",
    help="Source type to parse as (default: auto-detect).",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("output"),
    help="Output directory for structured JSON.",
)
def ingest_cmd(path: Path, source_type: str, output_dir: Path) -> None:
    """Parse files into structured JSON."""
    st = None if source_type == "auto" else SourceType(source_type)
    events = ingest(path, source_type=st)

    if not events:
        click.echo("No events found.")
        return

    tl = Timeline(events=events)
    tl.sort()

    out_file = output_dir / "ingested.json"
    write_timeline_json(tl, out_file)
    click.echo(f"Ingested {len(events)} events -> {out_file}")


@cli.command()
@click.option("--from", "from_date", type=click.DateTime(), default=None)
@click.option("--to", "to_date", type=click.DateTime(), default=None)
@click.option(
    "--sources",
    multiple=True,
    type=click.Choice(["copilot", "calendar", "email", "github", "notes"]),
)
@click.option(
    "--input-file",
    type=click.Path(exists=True, path_type=Path),
    default=Path("output/ingested.json"),
    help="Input JSON file from ingest step.",
)
def timeline(
    from_date: datetime | None,
    to_date: datetime | None,
    sources: tuple[str, ...],
    input_file: Path,
) -> None:
    """Build and display timeline from ingested data."""
    tl = Timeline.from_json(input_file.read_text())

    source_types = [SourceType(s) for s in sources] if sources else None
    tl = build_timeline(tl.events, start=from_date, end=to_date, sources=source_types)

    click.echo(render_timeline_md(tl))


@cli.command()
@click.option(
    "--period",
    type=click.Choice(["day", "week"]),
    default="day",
    help="Period to summarize.",
)
@click.option(
    "--date",
    "target_date",
    type=click.DateTime(),
    default=None,
    help="Target date (default: today).",
)
@click.option(
    "--input-file",
    type=click.Path(exists=True, path_type=Path),
    default=Path("output/ingested.json"),
    help="Input JSON file from ingest step.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("output"),
    help="Output directory for narrative context.",
)
def prepare(
    period: str,
    target_date: datetime | None,
    input_file: Path,
    output_dir: Path,
) -> None:
    """Prepare narrative context markdown for Copilot."""
    tl = Timeline.from_json(input_file.read_text())

    if target_date is None:
        target_date = datetime.now()

    if period == "day":
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        date_range = start.strftime("%Y-%m-%d")
    else:  # week
        weekday = target_date.weekday()
        start = (target_date - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=7)
        date_range = f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"

    filtered = build_timeline(tl.events, start=start, end=end)
    ctx = build_narrative_context(filtered, period=period, date_range=date_range)

    md_content = render_narrative_context_md(ctx)
    out_file = output_dir / f"narrative-{period}-{date_range.split(' ')[0]}.md"
    write_output(md_content, out_file)
    click.echo(f"Prepared narrative context -> {out_file}")
    click.echo(
        f"  {len(filtered.events)} events across {len(ctx.source_summary)} sources"
    )
