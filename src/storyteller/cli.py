"""CLI entry point for storyteller."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import click

import storyteller.config as config
from storyteller.models import SourceType, Timeline
from storyteller.output import (
    build_narrative_context,
    render_activity_digest_md,
    render_narrative_context_md,
    render_timeline_md,
    write_output,
    write_timeline_json,
)
from storyteller.publisher import publish_gist, publish_to_repo
from storyteller.timeline import build_timeline, ingest


@click.group()
def cli() -> None:
    """Storyteller: craft narratives from scattered work data."""


@cli.command()
@click.argument("path", type=click.Path(path_type=Path), required=False, default=None)
@click.option(
    "--source-type",
    type=click.Choice(["auto", "copilot", "calendar", "msg", "github", "notes"]),
    default="auto",
    help="Source type to parse as (default: auto-detect).",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for structured JSON (default: $STORYTELLER_OUTPUT_DIR or output/).",
)
def ingest_cmd(path: Path | None, source_type: str, output_dir: Path | None) -> None:
    """Parse files into structured JSON.

    PATH defaults to $STORYTELLER_DATA_DIR when omitted.
    """
    if path is None:
        path = config.DATA_DIR
    if not path.exists():
        raise click.UsageError(
            f"Path '{path}' does not exist. "
            "Pass a path argument or set STORYTELLER_DATA_DIR in .env."
        )
    if output_dir is None:
        output_dir = config.OUTPUT_DIR

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
    type=click.Path(path_type=Path),
    default=None,
    help="Input JSON file from ingest step (default: $STORYTELLER_INGESTED_FILE).",
)
def timeline(
    from_date: datetime | None,
    to_date: datetime | None,
    sources: tuple[str, ...],
    input_file: Path | None,
) -> None:
    """Build and display timeline from ingested data."""
    if input_file is None:
        input_file = config.INGESTED_FILE
    if not input_file.exists():
        raise click.UsageError(
            f"Input file '{input_file}' not found. Run `storyteller ingest` first."
        )
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
    type=click.Path(path_type=Path),
    default=None,
    help="Input JSON file from ingest step (default: $STORYTELLER_INGESTED_FILE).",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for narrative context (default: $STORYTELLER_OUTPUT_DIR).",
)
def prepare(
    period: str,
    target_date: datetime | None,
    input_file: Path | None,
    output_dir: Path | None,
) -> None:
    """Prepare narrative context markdown for Copilot."""
    if input_file is None:
        input_file = config.INGESTED_FILE
    if not input_file.exists():
        raise click.UsageError(
            f"Input file '{input_file}' not found. Run `storyteller ingest` first."
        )
    if output_dir is None:
        output_dir = config.OUTPUT_DIR
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


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--mode",
    type=click.Choice(["gist", "repo"]),
    default=None,
    help="Publishing mode (default: $STORYTELLER_GITHUB_PUBLISH_MODE or 'gist').",
)
@click.option(
    "--description",
    default="",
    help="Short description for the Gist or commit message.",
)
@click.option(
    "--repo",
    default=None,
    help="Target repository 'owner/repo' (mode 'repo'; default: $STORYTELLER_GITHUB_REPO).",
)
@click.option(
    "--repo-path",
    default=None,
    help="Directory inside the repo (mode 'repo'; default: $STORYTELLER_GITHUB_REPO_PATH).",
)
@click.option(
    "--public",
    is_flag=True,
    default=None,
    help="Create a public Gist (mode 'gist'; default from $STORYTELLER_GITHUB_GIST_PUBLIC).",
)
def publish(
    file: Path,
    mode: str | None,
    description: str,
    repo: str | None,
    repo_path: str | None,
    public: bool | None,
) -> None:
    """Publish a narrative markdown summary to GitHub.

    FILE is the markdown file to publish (e.g. output/narrative-day-2025-01-15.md).

    Requires `gh` CLI to be installed and authenticated (`gh auth login`).
    """
    resolved_mode = mode or config.GITHUB_PUBLISH_MODE
    resolved_public = public if public is not None else config.GITHUB_GIST_PUBLIC

    try:
        if resolved_mode == "gist":
            url = publish_gist(file, description=description, public=resolved_public)
            click.echo(f"Published gist -> {url}")
        else:
            resolved_repo = repo or config.GITHUB_REPO
            resolved_repo_path = repo_path or config.GITHUB_REPO_PATH
            url = publish_to_repo(
                file,
                repo=resolved_repo,
                repo_path=resolved_repo_path,
                commit_message=description,
            )
            click.echo(f"Published to repo -> {url}")
    except ValueError as exc:
        raise click.ClickException(str(exc))
    except RuntimeError as exc:
        raise click.ClickException(str(exc))
    except FileNotFoundError:
        raise click.ClickException(
            "`git` not found. Ensure git is installed and on your PATH."
        )


@cli.command()
@click.option(
    "--period",
    type=click.Choice(["day", "week"]),
    default="day",
    help="Period to digest (default: day).",
)
@click.option(
    "--date",
    "target_date",
    type=click.DateTime(),
    default=None,
    help="Target date (default: today).",
)
@click.option(
    "--sources",
    multiple=True,
    type=click.Choice(["copilot", "github"]),
    default=["copilot", "github"],
    show_default=True,
    help="Sources to include in the digest.",
)
@click.option(
    "--input-file",
    type=click.Path(path_type=Path),
    default=None,
    help="Input JSON file from ingest step (default: $STORYTELLER_INGESTED_FILE).",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for the digest (default: $STORYTELLER_OUTPUT_DIR).",
)
def digest(
    period: str,
    target_date: datetime | None,
    sources: tuple[str, ...],
    input_file: Path | None,
    output_dir: Path | None,
) -> None:
    """Cache a Copilot + git activity digest to the output directory.

    Reads ingested data, filters to the specified sources and period, and
    writes a structured markdown digest to:

        output/digest-{period}-{date}.md

    Run daily to build a week's worth of digests, then use the
    generate-narrative skill at week's end to crystallise the narrative.
    """
    if input_file is None:
        input_file = config.INGESTED_FILE
    if not input_file.exists():
        raise click.UsageError(
            f"Input file '{input_file}' not found. Run `storyteller ingest` first."
        )
    if output_dir is None:
        output_dir = config.OUTPUT_DIR

    if target_date is None:
        target_date = datetime.now()

    if period == "day":
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        date_label = start.strftime("%Y-%m-%d")
        date_range = date_label
    else:  # week
        weekday = target_date.weekday()
        start = (target_date - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=7)
        date_label = start.strftime("%Y-%m-%d")
        date_range = f"{start.strftime('%Y-%m-%d')} to {(end - timedelta(days=1)).strftime('%Y-%m-%d')}"

    tl = Timeline.from_json(input_file.read_text())
    source_types = [SourceType(s) for s in sources]
    filtered = build_timeline(tl.events, start=start, end=end, sources=source_types)

    md_content = render_activity_digest_md(filtered, period=period, date_range=date_range)
    out_file = output_dir / f"digest-{period}-{date_label}.md"
    write_output(md_content, out_file)

    copilot_count = sum(1 for e in filtered.events if e.source_type.value == "copilot")
    github_count = sum(1 for e in filtered.events if e.source_type.value == "github")
    click.echo(f"Digest cached -> {out_file}")
    click.echo(f"  {copilot_count} Copilot session(s), {github_count} git commit(s)")


@cli.command()
@click.option(
    "--period",
    type=click.Choice(["day", "week"]),
    default="week",
    help="Period to run the full pipeline for (default: week).",
)
@click.option(
    "--date",
    "target_date",
    type=click.DateTime(),
    default=None,
    help="Target date (default: today).",
)
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Data pool to ingest from (default: $STORYTELLER_DATA_DIR).",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: $STORYTELLER_OUTPUT_DIR).",
)
def run(
    period: str,
    target_date: datetime | None,
    data_dir: Path | None,
    output_dir: Path | None,
) -> None:
    """Run the full automated pipeline: ingest → digest → prepare.

    After this command completes, open the generated narrative context file
    in Copilot Chat and use the generate-narrative skill to craft the final
    narrative.  Then publish with `storyteller publish`.
    """
    if data_dir is None:
        data_dir = config.DATA_DIR
    if not data_dir.exists():
        raise click.UsageError(
            f"Data directory '{data_dir}' does not exist. "
            "Set STORYTELLER_DATA_DIR in .env or pass --data-dir."
        )
    if output_dir is None:
        output_dir = config.OUTPUT_DIR

    if target_date is None:
        target_date = datetime.now()

    # ── Compute period bounds ────────────────────────────────────────────
    if period == "day":
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        date_label = start.strftime("%Y-%m-%d")
        date_range = date_label
    else:  # week
        weekday = target_date.weekday()
        start = (target_date - timedelta(days=weekday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=7)
        date_label = start.strftime("%Y-%m-%d")
        date_range = (
            f"{start.strftime('%Y-%m-%d')} to "
            f"{(end - timedelta(days=1)).strftime('%Y-%m-%d')}"
        )

    # ── Step 1: Ingest ───────────────────────────────────────────────────
    click.echo(f"[1/3] Ingesting data from {data_dir} ...")
    events = ingest(data_dir)
    if not events:
        raise click.ClickException(f"No events found in '{data_dir}'.")
    tl_all = Timeline(events=events)
    tl_all.sort()
    ingested_file = output_dir / "ingested.json"
    write_timeline_json(tl_all, ingested_file)
    click.echo(f"      {len(events)} events -> {ingested_file}")

    # ── Step 2: Digest (Copilot + git) ───────────────────────────────────
    click.echo(f"[2/3] Caching activity digest ({period}: {date_range}) ...")
    digest_sources = [SourceType.COPILOT, SourceType.GITHUB]
    tl_digest = build_timeline(tl_all.events, start=start, end=end, sources=digest_sources)
    digest_md = render_activity_digest_md(tl_digest, period=period, date_range=date_range)
    digest_file = output_dir / f"digest-{period}-{date_label}.md"
    write_output(digest_md, digest_file)
    copilot_n = sum(1 for e in tl_digest.events if e.source_type == SourceType.COPILOT)
    github_n = sum(1 for e in tl_digest.events if e.source_type == SourceType.GITHUB)
    click.echo(f"      {copilot_n} Copilot session(s), {github_n} git commit(s) -> {digest_file}")

    # ── Step 3: Prepare narrative context ────────────────────────────────
    click.echo(f"[3/3] Preparing narrative context ...")
    tl_period = build_timeline(tl_all.events, start=start, end=end)
    ctx = build_narrative_context(tl_period, period=period, date_range=date_range)
    narrative_md = render_narrative_context_md(ctx)
    narrative_file = output_dir / f"narrative-{period}-{date_label}.md"
    write_output(narrative_md, narrative_file)
    click.echo(
        f"      {len(tl_period.events)} events across "
        f"{len(ctx.source_summary)} sources -> {narrative_file}"
    )

    # ── Next steps ───────────────────────────────────────────────────────
    click.echo("")
    click.echo("Pipeline complete.  Next steps:")
    click.echo(f"  1. Open {narrative_file} in Copilot Chat")
    click.echo("  2. Use the generate-narrative skill to craft the narrative")
    click.echo(f"  3. storyteller publish <output-narrative-file>")
