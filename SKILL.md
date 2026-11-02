---
name: career-record
description: Use when someone wants a record of their achievements at the company (leaving, layoff, promotion case, performance review, CV refresh, "what have I done in the last N years"). Captures evidence from GitHub, Jira, Confluence, Slack, Culture Amp and optionally Amplitude, then builds two private HTML artifacts plus PDFs: a long record (summary, CV bullets, STAR stories, timeline, project cards, recognition, full appendix) and a short screening brief with a timeline chart. Strictly read-only against company tools.
---

# Career record

Builds a career record from a person's real work evidence:

- **Long record:** an executive summary, impact tiles, a PRs-per-quarter chart, CV bullets, STAR stories, a quarterly timeline, project cards, skills, leadership, recognition, growth moments, and an appendix listing every PR, Jira issue and Confluence page.
- **Short brief** for screening interviews: a pitch, key facts, a hoverable career timeline, the biggest wins, quotes and the tech stack.

Both are published as **private** artifacts and exported to PDF.

Run this as a multi-session collaboration with the person; it is not a one-shot task. Expect several rounds of their review.

## Hard rules

1. **Read-only everywhere.** Never send Slack messages, add reactions, create or update Jira tickets or Confluence pages, or save Amplitude charts. Put this rule in every subagent prompt.
2. **Capture first, analyse later.** Access can disappear at any time, for example on a layoff. Dump raw data to disk before summarising, and don't wait on analysis to capture the next source.
3. **No invented metrics.** Every number needs a source. Where a number is missing, write `[ASK <NAME>: …]` in the notes and ask the person; never guess.
4. **Confidentiality.** Follow `references/confidentiality.md` in full. In short:
   - no customer names or IDs;
   - no internal revenue or ARR figures;
   - no compensation, HR or personal content;
   - no credentials;
   - no internal URLs as content.
   
   Raw dumps stay local.
5. **Credit accurately.** For team features, say "team feature". If a teammate implemented something, say so. The person decides how strongly each item is framed.
6. Before editing notes after a review round, copy them to `notes/backups/<file>.pre-<round>.md`.

## Workspace

Default: `~/career-record/`. Ask the person if they want a different location.

```
career.json          # identity + front-matter content for both pages (see examples/career.json)
raw/{github,jira,confluence,slack,cultureamp,amplitude}/   # untouched exports
notes/               # per-source summaries + the synthesis files the build reads
notes/session-handoff.md   # running state; read first after every compaction
output/              # achievements.html, overview.html, *-standalone.html, *.pdf
```

Keep `notes/session-handoff.md` up to date as you go. Record:

- phase status;
- confirmed facts;
- the person's decisions and framing preferences;
- artifact URLs;
- the rebuild steps.

Save a short project memory that points to it, so a later session can resume.

## Phases

### 0. Interview (AskUserQuestion)

Ask for:

- start and end dates;
- teams or tribes, with dates;
- levels and promotion dates;
- managers (for context only);
- the purpose of the record (job hunt, promotion, archive) and the audience;
- the GitHub org and login;
- highlights they remember, as a seed list to cross-check;
- any customers or topics that must never be named. These go into the blocklist.
- the important Slack channels:
  - team and tribe channels;
  - mission, project or squad channels;
  - on-call or alert channels;
  - incident channels;
  - recognition channels such as #shoutouts;
  - process or launchpad channels.
- whether any private channels or DMs matter, such as threads with managers, close collaborators or a private squad channel.

Tell them plainly that the Slack tools can only capture public channels. If they want private channels or DMs included, they must copy those messages into `raw/slack/` themselves, as `.txt` or `.md` files, one per channel or person. The steps are in the Slack section of `references/sources.md`.

Write the answers to `notes/phase0-background.md`, including the channel list and which private sources the person will paste. Create `<scratchpad>/blocklist.txt`, one term per line: customer names, company IDs and anything else they flagged. Keep it outside the workspace.

### 1–5. Capture

Follow `references/sources.md` for each source:

1. GitHub
2. Jira
3. Confluence
4. Slack
5. Culture Amp (manual PDFs)
6. Amplitude, optionally

Run independent sources in parallel with subagents. If access might be revoked soon, capture Slack and Culture Amp first. They are the hardest to recreate.

After capture, write one summary per source: `notes/<source>-summary.md`.

### 5b. Cross-reference

Build `notes/crossref.md`, plus `crossref.json` if useful:

1. Map each PR to its Jira keys.
2. Roll each Jira issue up to its epic or mission.
3. Attach Confluence docs and Slack threads to those clusters.

**Work older than 2 years.** Slack history only goes back about 2 years from today. Slack holds most of the "glue" that explains why work happened and how pieces relate, so for anything older, rebuild the story from GitHub and Jira, plus Confluence where it exists:

- **Look for clusters.** Many tickets on the same board about the same or a similar topic, created or resolved close together, are probably one mission or project. Examples are a run of IM, QOL or IL tickets on one feature area. Further signals:
  - a shared epic or parent;
  - a shared label or sprint name;
  - PRs to the same repos in the same weeks;
  - a Confluence checklist or design doc from that period.
- **Record each cluster in the notes** as a likely mission, flagged as reconstructed. List:
  - the tickets and PRs;
  - the date range;
  - your guess at the goal;
  - the evidence for it.

  For example: `**Likely mission (reconstructed, pre-Slack):** visibility rules, Sep 2023, IM-762/763/764 + 3 PRs. [ASK <NAME>: mission name, goal, your role?]`
- **Confirm context with the person** unless you are certain, e.g. the epic name and description spell it out. Ask about:
  - the mission's name and purpose;
  - who else was on it;
  - their role in it;
  - the outcome;
  - anything that went wrong.

  Batch these questions per period rather than asking one at a time.
- **Never invent the glue.** Without Slack or the person's confirmation, describe what the tickets and PRs show, not the motivation or the impact.
- **No reviews before 2024.** Culture Amp only goes back to 2024. For anything earlier there are no ratings or reviewer quotes. Don't leave a gap that looks like the person had no recognition in that period: note that the source doesn't exist, and ask the person for any feedback they remember or kept.

Every authored PR must land in exactly one cluster or in "misc/maintenance". Mark PRs that you grouped by repo, time or title as *inferred*. Epics with no PRs are non-code work, such as design, coordination or leadership, so keep them. Show the clusters to the person and apply their corrections.

### 6. Synthesis

Write the notes files in the formats from `references/notes-format.md`:

- `notes/timeline.md`: the career arc plus one section per quarter.
- `notes/project-cards.md`: one card per cluster, covering problem, role, what they built, impact/outcome, tech and evidence.
- `notes/people-skills-recognition.md`: headline numbers, skills matrix, leadership, recognition quotes and growth moments.
- `notes/cv-and-stories.md`: 8–12 CV bullets and 5–8 STAR stories.

Every claim carries a `(src: …)` reference. Then have the person review the cards and metrics. This round usually reorders priorities and catches mis-credits.

### 7. Output

1. Run the Artifact quickstart with `intent: "other"`, which covers the page-design guidance.
2. Fill in `career.json` from `examples/career.json`:
   - name, dates and subtitle;
   - summary paragraphs;
   - impact tiles. Count tiles such as PRs, repos, reviews, Jira issues and Confluence pages are generated automatically; only add extras.
   - chart bands such as promotions;
   - redact patterns;
   - the `overview` block: lanes, milestones (`row` 0/1 and `anchor` start/middle/end prevent label collisions), wins, quotes, facts and stack.
   
   Bar kinds are `role`, `promoted`, `lead`, `work`, `oncall` and `alt`.
3. Build:
   ```bash
   python3 <skill>/scripts/build.py <workspace>
   python3 <skill>/scripts/build_overview.py <workspace>
   <skill>/scripts/check_blocklist.sh <scratchpad>/blocklist.txt <workspace>/output/achievements.html <workspace>/output/overview.html   # must be 0
   ```
4. Check the layout:
   - `scripts/export_pdf.sh` writes `*-standalone.html`.
   - `scripts/screenshot.sh` renders it; look at the PNG for label collisions or overflow.
   - Look at the timeline milestones in particular.
5. Publish each page as a **private** artifact with the Artifact tool, then pass the same `file_path` to republish later. Give the person both links.
6. Export the PDFs with `scripts/export_pdf.sh <workspace>/output/achievements.html` and `scripts/export_pdf.sh <workspace>/output/overview.html`. The long PDF is mostly appendix and is often 50–100 pages.
7. Ask the person to spot-check about 10 claims against the evidence.

### Tweak loop

The person will ask to reorder emphasis, add or swap quotes, or add missing early work.

1. Edit the notes or `career.json`.
2. Rebuild.
3. Run the blocklist check.
4. Republish to the same URLs.
5. Re-export the PDFs.
6. Log each decision in the handoff file.

The early years are often under-documented: Slack history only reaches back about 2 years, and Culture Amp only covers 2024 onward. Search Jira, Confluence and GitHub for that period specifically.

## Lessons from earlier runs

- **Tooltips:** SVG `<title>` hover doesn't work inside artifacts. The overview uses a JS tooltip driven by `data-tip="Label|detail"`, and the build already handles it.
- **Long STAR stories:** keep the bullets short and nested rather than long paragraphs.
- **People's preferences:**
  - feature whole squads or missions rather than single tickets;
  - frame trust signals relative to level, e.g. "while still a junior";
  - include hiring interviews, talks and process leadership, not just code.
- **Mistakes and reverts** are valuable "Growth" material when told honestly. Don't hide them, but let the person decide whether one becomes a STAR story.
