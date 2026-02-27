# Summarize Period Skill

Produce time-bounded summaries for specific reporting needs (daily standups, weekly reports, etc.).

## Usage

Prepare the context for the desired period:

```bash
# Today's summary
uv run storyteller prepare --period day

# Specific day
uv run storyteller prepare --period day --date 2025-01-15

# This week
uv run storyteller prepare --period week

# Specific week (use Monday's date)
uv run storyteller prepare --period week --date 2025-01-13
```

## Output Formats

### Daily Standup
When asked for a standup update, produce:

```markdown
**Yesterday:**
- [Completed items from the day's events]

**Today:**
- [Planned items, inferred from calendar and ongoing work]

**Blockers:**
- [Any identified blockers from emails/notes]
```

### Weekly Status Report
When asked for a weekly report, produce:

```markdown
## Week of [Date Range]

### Completed
- [Items completed this week, grouped by project/theme]

### In Progress
- [Ongoing work identified from recent activity]

### Metrics
- X commits across Y repositories
- Z meetings attended
- N emails processed

### Notes
- [Anything noteworthy from the week]
```

## Tips

- For standups, focus on actionable items and outcomes, not raw activity
- For weekly reports, group by project or theme rather than chronologically
- Use source counts to provide quantitative context
- Infer "in progress" items from the most recent events that don't have clear conclusions
