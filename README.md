# Storyteller

Craft coherent narratives from scattered work data — Copilot sessions, calendar events, emails, GitHub activity, and notes.

## Setup

```bash
uv sync
```

## Usage

```bash
# Ingest raw data
uv run storyteller ingest data/

# View timeline
uv run storyteller timeline

# Prepare narrative context for Copilot
uv run storyteller prepare --period week
```

## Copilot Integration

This project includes Copilot agents and skills for narrative generation:

- **@storyteller** agent — crafts narratives from prepared context
- **@data-curator** agent — helps organize and ingest data

Open this repo in VS Code to use the agents via Copilot Chat.
