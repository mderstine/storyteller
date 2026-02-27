# Digest Skill

Cache a structured Copilot + git activity digest for a day or week.  The digest
is designed to accumulate throughout the week as raw material that the storyteller
crystallises into a coherent narrative when you're ready.

## How it fits into the workflow

```
Throughout the week
  └─ Copilot session logs → data/
  └─ git commits in local repos

End of each day
  └─ storyteller ingest           # refresh ingested.json
  └─ storyteller digest           # cache today's activity digest

End of the week
  └─ storyteller digest --period week   # optional: single weekly digest
  └─ storyteller prepare --period week  # full narrative context
  └─ [ask Copilot to generate the narrative — generate-narrative skill]
  └─ storyteller publish output/narrative-week-*.md
```

## Usage

```bash
# Cache today's Copilot + git activity
uv run storyteller digest

# Cache a specific day
uv run storyteller digest --date 2025-01-15

# Cache this week so far
uv run storyteller digest --period week

# Copilot sessions only
uv run storyteller digest --sources copilot

# Git commits only
uv run storyteller digest --sources github
```

## Output

Writes `output/digest-{period}-{date}.md`.  Example for a daily digest:

```markdown
# Activity Digest: day — 2025-01-15

## At a Glance
- **Copilot sessions:** 4
- **Git commits:** 7 across 2 repositories

## Copilot Sessions

### 2025-01-15
- **09:15** Scaffold authentication module
  > Built JWT-based auth with refresh token support...
- **11:30** Debug token expiry edge case
  > Investigated race condition in token refresh...

## Git Commits

### ~/projects/my-app
- `a1b2c3d` Add JWT middleware
- `e4f5a6b` Fix token refresh race condition
  > Ensure refresh lock is released on timeout
- `c7d8e9f` Add auth integration tests

## Topics
auth, token, refresh, middleware, tests, jwt, expiry, session, login, user
```

## How the storyteller uses digests

When you run `storyteller prepare --period week` at week's end, the event data
from all sources is assembled into a narrative context file.  You can then open
that file in Copilot Chat and ask the storyteller agent to:

- Identify the major themes from the **Topics** section
- Reconstruct the arc of the week from **Copilot Sessions** + **Git Commits**
- Produce a weekly narrative, standup bullet points, or a status report

The digest's **Topics** section gives the agent a ready-made theme scaffold so
it doesn't have to infer everything from raw timestamps.

## Tips

- Run `storyteller ingest` before `digest` to pick up new session files
- Set `STORYTELLER_DATA_DIR` in `.env` so `ingest` needs no path argument
- Commit or back up the `output/digest-*.md` files — they are your weekly log
- For Copilot session files, drop `.json` exports into your `STORYTELLER_DATA_DIR`
