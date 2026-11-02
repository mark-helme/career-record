# Notes formats the build scripts parse

All files live in `<workspace>/notes/`. Missing files or sections are skipped and don't cause errors. The parser handles a small markdown subset: headings, nested `-`/`1.` lists, `|` tables, `**bold**`, `*italic*` and `` `code` ``. Links are flattened to their text, so the output never contains internal URLs.

When building, these are stripped from text automatically:
- `(src: …)` evidence refs. Keep them in the notes, because they make claims auditable.
- `[ASK …]` gap markers.
- Slack timestamps.
- Anything matched by `career.json` → `redact`.

## cv-and-stories.md

```markdown
# CV bullets and STAR stories

## Executive summary
(not rendered; the summary comes from career.json "summary")

## CV bullets
1. **Bold lead-in.** One line of what they did and the measurable result. (src: …)
2. ...

## STAR stories

### 1. Story title (competency, competency)
- **Situation.** ...
- **Task.** ...
- **Action.**
  - ...
- **Result.** ...

---

### 2. Next story (…)
```

## project-cards.md

Each `##` heading is one card. Use `Title (Mon YYYY – Mon YYYY)` and the date in parentheses becomes the card's date label. Any `**Label:**` line starts a field. The field `**Impact / outcome:**` is highlighted, and `**Tech:**` and `**Evidence:**` are muted.

```markdown
## Service migration (Sep 2024 – Feb 2025)
One-line context.
**Problem:** ...
**My role:** ...
**What I built:**
- ...
**Impact / outcome:** ...
**Tech:** TypeScript, Fastify
**Evidence:** IM-123, repo#45 (src: …)
```

## people-skills-recognition.md

These sections are matched by keyword in the `##` heading:

| Keyword in heading | Long-page section |
|---|---|
| `Skills` | Skills & technology |
| `Leadership` | Leadership & collaboration |
| `Recognition` | Recognition & feedback (quotes with name, role, source and date) |
| `Growth` | Growth & learning: honest, interview-ready mistakes and lessons |

Other sections, such as `## 1. Headline numbers`, are not rendered. Keep them as your working evidence table.

## timeline.md

```markdown
## Career arc
- **Jan 2023 to mid-2023, Junior engineer.** ...

## 2023-Q1 (Jan–Mar): PRs 12 (11 merged)
**Role/context:** ...
- What happened, with ticket/PR refs (src: …)
```

The heading pattern `YYYY-Qn (months): count` is parsed into the quarter label, its month range and its count.

## confluence-authored.tsv

The file has 3 tab-separated columns and no header: `date<TAB>space<TAB>title`. Only list pages the person really authored or heavily co-authored, and confirm the list with them.

## Raw files read directly

- `raw/github/authored_prs.jsonl` and `raw/github/reviewed_prs.jsonl`: written by `scripts/github_dump.sh`.
- `raw/jira/assigned.jsonl` and `raw/jira/reported.jsonl`: one issue per line, with at least `key`, `issuetype`, `summary`, `status` and `created`.
