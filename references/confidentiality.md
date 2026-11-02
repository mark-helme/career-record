# Confidentiality rules

The output describes **the person's contributions**: what they did, why, the impact and the tech. Before publishing, check the content against the lists below.

## Never in the output

- **Customer identity.** Never use a customer's name, company ID, domain, or a detail that identifies them. Say "a high-value customer (HVC)" or "a large enterprise customer". Add every real name and ID to the blocklist.
- **Revenue.** No exact internal revenue, MRR, ARR or deal-value figures, even when they appear in a ticket. Describe them qualitatively, e.g. "churn risk", "high-value".
- **Personal data.** No compensation, salary bands, HR cases, health information, or personal details about anyone.
- **Secrets.** No credentials, tokens, environment variable values or internal hostnames.
- **Internal links.** No internal URLs used as content. The build flattens markdown links to their text; don't paste raw URLs into `career.json`.
- **Verbatim confidential documents.** Summarise them instead of copying.

## Allowed

- Ticket keys, repo names and PR numbers. These are useful evidence and mean nothing outside the company.
- Colleague names in attributed recognition quotes. Ask the person first if a quote came from a private DM.
- Product usage numbers from analytics, labelled with their scope ("external users", "team feature") and date range.

## Mechanics

- Keep `blocklist.txt` in the session scratchpad, not the workspace, because it contains the very names it blocks. Put one case-insensitive term per line.
- Run `scripts/check_blocklist.sh` on every output after every build and expect 0 hits.
- Use `career.json` → `redact` for regex-level scrubbing during the build, for example bare 7–9 digit IDs or "CID 123456".
- The person decides what to share. Artifacts start private; never share or publish them on the person's behalf.
