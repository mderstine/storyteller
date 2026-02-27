# Ingest Data Skill

Parse raw data sources into structured JSON using the storyteller CLI.

## Usage

Run the ingestion pipeline on raw data files:

```bash
# Auto-detect and ingest all files in data/
uv run storyteller ingest data/

# Ingest specific source type
uv run storyteller ingest <path> --source-type <type>
```

### Source Types

| Type | File Extensions | Description |
|------|----------------|-------------|
| `notes` | `.md`, `.txt` | Markdown/text notes |
| `calendar` | `.ics` | ICS calendar exports |
| `msg` | `.msg` | Outlook email files |
| `copilot` | `.json` | Copilot session logs |
| `github` | (directory) | Git repository |
| `auto` | (any) | Auto-detect from extension |

### Output

Produces `output/ingested.json` containing a JSON array of events, each with:
- `timestamp` — ISO 8601 datetime
- `source_type` — one of: copilot, calendar, email, github, notes
- `title` — short description
- `summary` — longer description (up to 500 chars)
- `metadata` — source-specific metadata (file path, author, etc.)

### Verification

After ingestion, verify the output:
```bash
# Check event count
python -c "import json; d=json.load(open('output/ingested.json')); print(f'{len(d)} events')"

# View timeline
uv run storyteller timeline
```
