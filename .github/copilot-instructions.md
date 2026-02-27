# Storyteller - Copilot Instructions

This is a Python toolkit for crafting coherent narratives from scattered work data.

## Project Structure

- `src/storyteller/` — Python package with parsers, timeline builder, and output formatter
- `data/` — Raw input data (gitignored)
- `output/` — Generated output files (gitignored)

## Data Sources

The toolkit can parse:
- **Copilot session logs** (JSON) — AI coding session records
- **Calendar events** (ICS) — Outlook/calendar exports
- **Outlook emails** (MSG) — Email message files
- **GitHub repo activity** — Git commit history
- **Notes** (Markdown/TXT) — Freeform notes with dates

## CLI Commands

```bash
# Ingest raw data into structured JSON
storyteller ingest <path> [--source-type auto|copilot|calendar|msg|github|notes]

# View timeline from ingested data
storyteller timeline [--from DATE] [--to DATE] [--sources ...]

# Prepare narrative context for Copilot agents
storyteller prepare [--period day|week] [--date DATE]
```

## Workflow

1. Place raw data files in `data/`
2. Run `storyteller ingest data/` to parse everything into `output/ingested.json`
3. Run `storyteller prepare --period week` to generate narrative context markdown
4. Use the `@storyteller` agent to craft narratives from the prepared context

## Conventions

- All timestamps are naive (no timezone info) for simplicity
- Output is always Markdown
- The `output/` directory is the canonical location for generated files
