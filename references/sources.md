# Capture recipes per source

Every source is **read-only**. Never send messages, add reactions, or create or update tickets, pages, charts or dashboards. Save raw results under `<workspace>/raw/<source>/` before you summarise anything, because access may be removed at any time.

When several agents capture in parallel, give each agent one source, the exact output paths, and the read-only rule in its prompt.

## GitHub (`gh`, should already be authenticated)

1. Run `scripts/github_dump.sh <org> <login> <start> <end> <workspace>`. It searches one month at a time, so no window hits the 1000-result search cap.
2. Cross-check the totals:
   - `gh search prs --owner <org> --author <login> --json number --limit 1000 | jq length`, or
   - the count in the GitHub UI.
3. Extract Jira keys from PR titles, branch names (`headRefName`) and bodies with a regex such as `[A-Z][A-Z0-9]+-\d+`. Save them to `raw/github/jira_keys_from_prs.txt`.
4. To find AI-assisted PRs, match bodies for "Claude Code" or "Generated with".

Caveat: line counts are inflated by lockfiles and dependency upgrades. Cite PR and ticket counts instead.

## Jira (jira plugin: `searchJiraTasks`, `getJiraTask`, `getIssueWithPrs`)

- **Rate limit:** about 30 requests per minute per user, and parallel agents share it.
- **Queries (JQL):**
  - `assignee was currentUser()` → `raw/jira/assigned.jsonl`
  - `reporter = currentUser()` → `raw/jira/reported.jsonl`
  - epics they owned → `raw/jira/epics.jsonl`
  - Missions or initiatives they were part of, by epic or parent, even when someone else is the assignee.
- **Fields to save:** `key`, `issuetype`, `summary`, `description` (truncated is fine), `status`, `resolution`, `created`, `resolutiondate`, `labels`, `parent`/epic, `team`.
- **Key issues:** fetch their full detail with comments into `raw/jira/detail/<KEY>.md`. Comments often hold the real story, such as reverts, customer impact or who did what.
- **Dev-panel links:** use `getIssueWithPrs` on epics to find linked PRs that have no key in their text.

## Confluence (confluence plugin: `searchConfluenceContent`, `getConfluencePage`)

- **Queries (CQL):**
  - `creator = currentUser()`
  - `contributor = currentUser()`
  - title searches for the projects or missions found in Jira, such as "<mission> checklist", "PoC", "retro" or "tech talk"
- **Where to save:**
  - metadata → `raw/confluence/pages.jsonl`
  - full text of design docs, PoCs, postmortems, onboarding and process docs → `raw/confluence/pages/<id>-<slug>.md`
- **Before listing as authored:** confirm with the person which pages they actually authored. Creator is not always the author, and contributors include people who fixed a typo.
- **Recurring notes:** count pages they wrote regularly, such as weekly sync notes, separately.

## Slack (slack plugin: `searchSlack`, `getSlackChannelMessages`, `getSlackMessage`)

**History limit:** Slack only keeps about **2 years** of history from today. Searches for anything older come back empty or incomplete; that means the history is gone, not that nothing happened. Write the cutoff date in `notes/slack-summary.md`. Work from before it has to be reconstructed from GitHub and Jira and confirmed with the person (see Phase 5b in `SKILL.md`).

**What can be captured:** the Slack tools only reach **public channels**. They cannot read private channels or DMs (direct or group). Don't report a private channel as "empty" or "no results"; say it can't be reached.

**Channel list:** start from the channels the person named in the Phase 0 interview. Look up each one with `listSlackChannels` and confirm it is public and reachable. Read their recent history with `getSlackChannelMessages`, and run the targeted searches below inside them. Save one file per channel, `raw/slack/<channel>.md`, with date, author, text and permalink.

**Private channels and DMs (manual):** if the person wants these included, ask them to copy the messages into the workspace themselves:

1. Open the channel or DM in Slack.
2. Select and copy the relevant messages or threads.
3. Paste them into `raw/slack/<channel-or-person>.txt` (or `.md`), keeping dates and author names where possible.
4. Tell Claude which files they added.

Treat the pasted files like any other raw source:
- Long conversations can be split into chunks, e.g. `raw/slack/dm_chunks/`, and summarised piece by piece.
- Summarise work facts only, and keep anything personal out of the notes.
- Ask before quoting a private message in the output.

Search with targets in mind; don't try to capture everything. Useful queries:

- **Recognition:**
  - `@<user> thanks`, `kudos`, `shoutout`, `great job`, `well done`, `amazing`
  - the company `#shoutouts` / kudos channel searched for their name
- **Their announcements:** `from:@<user>` combined with `released`, `rolled out`, `demo`, `RFC` or `postmortem`.
- **On-call:** count their messages per quarter in the team's alert channels (P1/P2/P3); that gives a measure of on-call weeks. Save notable incidents.
- **Mission and squad channels:** capture the main threads from each project channel.
- **Promotion:** check people-news or announcement channels.

Some public channels are still not searchable through the API. If search finds nothing in a channel the person knows was active, ask them to paste the key threads into `raw/slack/<channel>.md` in the same way.

Direct messages with managers or close collaborators often give the most context, especially for leadership, staffing and escalation stories, but they're sensitive. Summarise only work facts and never quote personal content.

## Culture Amp (manual; the Claude in Chrome extension is not approved)

**History limit:** Culture Amp only has review cycles from **2024 onward**. There are no earlier reviews, feedback or shoutouts to collect, so don't ask the person to look for them. For pre-2024 work, there are no review ratings or reviewer quotes. Recognition from that time can only come from Slack (if it's still within the 2-year window), from Jira or Confluence comments, or from the person's memory. Record the gap in `notes/cultureamp-summary.md` and ask the person whether they kept any older feedback elsewhere, e.g. emails or saved messages.

1. Ask the person to open every review cycle and save it with Print → Save as PDF into `raw/cultureamp/`. That covers:
   - self reviews and manager reviews;
   - peer feedback / "View feedback" pages;
   - quarterly reflections;
   - Shoutouts;
   - project/mission 360 reports.
2. Extract the text with:
   ```bash
   mkdir -p raw/cultureamp/text
   for f in raw/cultureamp/*.pdf; do swift <skill>/scripts/pdf2txt.swift "$f" "raw/cultureamp/text/$(basename "${f%.pdf}").txt"; done
   ```
3. From the text, pull out:
   - the trajectory of ratings;
   - recurring strengths;
   - quotes, attributed by name and role;
   - promotion evidence.
   
   Leave out compensation and personal content.

## Product analytics (optional; Amplitude plugin)

- Run read-only ad-hoc queries only. Never create or save charts or dashboards.
- Filter to **external users**, and state the date range.
- Record each query and its result in `raw/amplitude/queries-<date>.md`.
- When a number covers a whole-team feature, label it that way, e.g. "~105k users (team feature)". Don't present it as the person's own result.
- Don't claim "100% adoption" just because a feature flag was rolled out to everyone.
