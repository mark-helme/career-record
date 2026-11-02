# career-record

A [Claude Code](https://claude.com/claude-code) skill that turns your work history into a career record. It collects evidence from the tools you used, then builds two HTML pages and matching PDFs:

- **Full record:** executive summary, impact highlights, CV bullets, STAR interview stories, a quarterly timeline, project cards, skills, recognition, growth moments, and an appendix of your pull requests, tickets and docs.
- **Short brief:** a one-page overview for screening interviews, with an interactive career timeline, biggest wins, quotes and your tech stack.

It's useful when you're leaving a job, preparing a promotion case or performance review, refreshing your CV, or just keeping an archive of what you've done.

## How it works

1. **Interview.** Claude asks about your dates, roles, promotions, the important channels, and anything that must never be named.
2. **Capture.** Raw data is saved to disk before any analysis, because access can disappear at any time. Sources:
   - GitHub (`gh` CLI)
   - Jira
   - Confluence
   - Slack
   - your performance review tool (exported manually as PDFs)
   - product analytics (optional)
3. **Cross-reference.** PRs are linked to tickets, tickets to epics and projects, then docs and threads are attached. Older work with no chat history is reconstructed and confirmed with you.
4. **Synthesis.** Claude writes the timeline, project cards, CV bullets and STAR stories. Every claim carries a source, and gaps are flagged as questions for you rather than guessed.
5. **Output.** The HTML pages are built from your notes and published privately, then exported to PDF.

All access to company tools is **read-only**: no messages are sent, and no tickets or pages are changed. The output leaves out customer names, revenue figures, personal data and credentials, and a blocklist check runs on every build.

## Requirements

- Claude Code.
- Python 3.
- macOS and Google Chrome for the PDF export and screenshots. The scripts use headless Chrome, and PDF text extraction uses Swift's PDFKit.
- The GitHub CLI (`gh`), authenticated.
- Optional: Jira, Confluence, Slack and analytics connectors (MCP servers) set up in Claude Code. Without them, you can paste exports into `raw/` manually.

## Install

```bash
git clone https://github.com/mark-helme/career-record ~/.claude/skills/career-record
```

Then, in Claude Code, run `/career-record` or ask for "a record of my achievements".

## Layout

```
SKILL.md                    the full process the agent follows
references/
  sources.md                capture recipes per source
  notes-format.md           markdown formats the build scripts parse
  confidentiality.md        what must never appear in the output
scripts/
  github_dump.sh            authored + reviewed PRs to JSONL
  build.py                  full record HTML
  build_overview.py         short brief HTML
  export_pdf.sh             HTML to PDF via headless Chrome
  screenshot.sh             layout check
  check_blocklist.sh        fails on any blocklisted term
  pdf2txt.swift             text from exported review PDFs
templates/                  page templates (light and dark mode, print CSS)
examples/career.json        example config for a fictional person
```

## Building pages by hand

The pages are built from a workspace folder that holds `career.json`, `notes/` and `raw/`:

```bash
python3 scripts/build.py ~/career-record
python3 scripts/build_overview.py ~/career-record
scripts/check_blocklist.sh blocklist.txt ~/career-record/output/*.html
scripts/export_pdf.sh ~/career-record/output/overview.html
```

See `examples/career.json` for the config shape and `references/notes-format.md` for the notes.

## License

MIT
