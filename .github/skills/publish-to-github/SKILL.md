# Publish to GitHub Skill

Upload a narrative markdown summary to GitHub — either as a **secret Gist** or as a **committed file** in a repository.

## Prerequisites

Install and authenticate the GitHub CLI:

```bash
# Install (pick your platform)
brew install gh          # macOS
sudo apt install gh      # Debian/Ubuntu

# Authenticate
gh auth login
```

## Configuration

Add these variables to your `.env` file (copy `.env.example` to get started):

```env
# "gist" (default) or "repo"
STORYTELLER_GITHUB_PUBLISH_MODE=gist

# Gist visibility — true = public, false = secret (default)
STORYTELLER_GITHUB_GIST_PUBLIC=false

# Required only for mode "repo"
STORYTELLER_GITHUB_REPO=your-username/your-repo
STORYTELLER_GITHUB_REPO_PATH=summaries/
```

## Usage

### Publish the most recent summary

```bash
# Publish using settings from .env (defaults to gist mode)
uv run storyteller publish output/narrative-day-2025-01-15.md

# Add a description
uv run storyteller publish output/narrative-day-2025-01-15.md \
  --description "Daily standup context 2025-01-15"
```

### Gist mode (explicit)

```bash
# Secret gist (default)
uv run storyteller publish output/narrative-week-2025-01-13.md \
  --mode gist

# Public gist
uv run storyteller publish output/narrative-week-2025-01-13.md \
  --mode gist --public
```

### Repo mode (explicit)

```bash
# Commit to the default repo/path from .env
uv run storyteller publish output/narrative-day-2025-01-15.md \
  --mode repo

# Override repo and path inline
uv run storyteller publish output/narrative-day-2025-01-15.md \
  --mode repo \
  --repo your-username/work-journal \
  --repo-path standups/
```

## End-to-end Workflow

```bash
# 1. Ingest your data pool (path from STORYTELLER_DATA_DIR if omitted)
uv run storyteller ingest

# 2. Prepare the narrative context
uv run storyteller prepare --period day

# 3. Ask Copilot to craft the narrative from the context file
#    (use the generate-narrative skill)

# 4. Publish the finished summary to GitHub
uv run storyteller publish output/narrative-day-$(date +%Y-%m-%d).md \
  --description "Standup $(date +%Y-%m-%d)"
```

## Output

| Mode | What you get |
|------|-------------|
| `gist` | URL like `https://gist.github.com/username/abc123` |
| `repo` | URL like `https://github.com/user/repo/blob/main/summaries/narrative-day-2025-01-15.md` |

## Troubleshooting

- **`gh` not found** — install the GitHub CLI and re-run.
- **401 / 403 error** — run `gh auth login` and choose the correct account.
- **Repo mode 422** — ensure `STORYTELLER_GITHUB_REPO` is correct and you have write access.
- **File already exists (repo mode)** — the skill handles this automatically by fetching the existing blob SHA before updating.
