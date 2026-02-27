# Generate Narrative Skill

Craft a coherent narrative from structured timeline data.

## Prerequisites

Data must be ingested first (see `ingest-data` skill). Then prepare the narrative context:

```bash
uv run storyteller prepare --period day --date 2025-01-15
# or
uv run storyteller prepare --period week --date 2025-01-13
```

## Process

1. Read the prepared narrative context file from `output/` (e.g., `output/narrative-day-2025-01-15.md`)
2. Analyze the events across all sources
3. Identify themes, connections, and patterns
4. Write a coherent narrative in Markdown

## Narrative Structure

### Daily Narrative
```markdown
# Day Summary: [Date]

## Key Themes
- Theme 1: ...
- Theme 2: ...

## What Happened
[Flowing narrative connecting events]

## Highlights
- Notable accomplishment or event
- Important decision or communication
```

### Weekly Narrative
```markdown
# Week Summary: [Date Range]

## Overview
[High-level summary paragraph]

## By Theme
### Theme 1
[Events and activities related to this theme]

### Theme 2
[Events and activities related to this theme]

## Key Accomplishments
- ...

## Looking Ahead
- ...
```

## Tips

- Cross-reference events: a meeting (calendar) + code changes (github) + follow-up email (msg) often tell one story
- Note transitions between activities
- Highlight collaboration patterns from emails and meetings
- Connect Copilot sessions to the code changes they produced
