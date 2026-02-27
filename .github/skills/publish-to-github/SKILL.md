# Publish to GitHub Skill

Upload a narrative markdown summary to GitHub — either as a **secret Gist** or as a **committed file** in a repository.

No extra tools required beyond plain `git` (already on every developer machine) and a GitHub personal access token.

## Prerequisites

**Create a GitHub personal access token** at <https://github.com/settings/tokens>:

| Mode | Token type | Required scope |
|------|-----------|----------------|
| `gist` | Classic or fine-grained | Gists — read & write |
| `repo` | Classic or fine-grained | Repository Contents — read & write |

Add the token to your `.env` file (copied from `.env.example`):

```env
GITHUB_TOKEN=ghp_...
```

For **repo mode without a token**: if your machine already has git configured with SSH keys or a credential helper, the push will use those credentials automatically and no token is needed.

## Configuration

```env
# .env

GITHUB_TOKEN=ghp_...                              # required for gist; optional for repo

STORYTELLER_GITHUB_PUBLISH_MODE=gist             # "gist" (default) or "repo"
STORYTELLER_GITHUB_GIST_PUBLIC=false             # true = public gist, false = secret

STORYTELLER_GITHUB_REPO=your-username/your-repo  # repo mode only
STORYTELLER_GITHUB_REPO_PATH=summaries/          # directory inside the repo
```

## Usage

### Publish the most recent summary

```bash
# Uses settings from .env (defaults to secret gist)
uv run storyteller publish output/narrative-day-2025-01-15.md

# With a description
uv run storyteller publish output/narrative-day-2025-01-15.md \
  --description "Daily standup context 2025-01-15"
```

### Gist mode

```bash
# Secret gist (default)
uv run storyteller publish output/narrative-week-2025-01-13.md --mode gist

# Public gist
uv run storyteller publish output/narrative-week-2025-01-13.md --mode gist --public
```

### Repo mode

```bash
# Uses STORYTELLER_GITHUB_REPO and STORYTELLER_GITHUB_REPO_PATH from .env
uv run storyteller publish output/narrative-day-2025-01-15.md --mode repo

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

# 3. Ask Copilot to craft the narrative (generate-narrative skill)

# 4. Publish the finished summary
uv run storyteller publish output/narrative-day-$(date +%Y-%m-%d).md \
  --description "Standup $(date +%Y-%m-%d)"
```

## Output

| Mode | What you get |
|------|-------------|
| `gist` | URL like `https://gist.github.com/username/abc123` |
| `repo` | URL like `https://github.com/user/repo/blob/main/summaries/narrative-day-2025-01-15.md` |

## Troubleshooting

- **"GITHUB_TOKEN is required"** — add `GITHUB_TOKEN=ghp_...` to your `.env`.
- **GitHub API error 401** — token is invalid or expired; generate a new one.
- **GitHub API error 403** — token lacks the required scope (see Prerequisites table above).
- **Repo mode push fails** — ensure the token has Contents write access, or configure SSH keys on the machine.
- **"`git` not found"** — install git and make sure it is on your `PATH`.
