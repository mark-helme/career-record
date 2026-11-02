#!/usr/bin/env bash
# Dumps authored and reviewed PRs to <workspace>/raw/github/*.jsonl, one month per search to stay under GitHub's 1000-result cap.
# Usage: github_dump.sh <org> <login> <from YYYY-MM-DD> <to YYYY-MM-DD> <workspace>
set -euo pipefail
ORG=$1 LOGIN=$2 FROM=$3 TO=$4 WS=$5
HERE=$(cd "$(dirname "$0")" && pwd)
OUT="$WS/raw/github"; mkdir -p "$OUT"
: > "$OUT/authored_prs.jsonl"; : > "$OUT/reviewed_prs.jsonl"
python3 - "$FROM" "$TO" <<'PY' | while read -r A B; do
import sys, datetime as d
a, end = d.date.fromisoformat(sys.argv[1]), d.date.fromisoformat(sys.argv[2])
while a <= end:
    nxt = (a.replace(day=1) + d.timedelta(days=32)).replace(day=1)
    print(a, min(end, nxt - d.timedelta(days=1)))
    a = nxt
PY
  gh api graphql --paginate -F q="org:$ORG author:$LOGIN is:pr created:$A..$B" -F query=@"$HERE/authored.graphql" \
    --jq '.data.search.nodes[] | @json' >> "$OUT/authored_prs.jsonl"
  gh api graphql --paginate -F q="org:$ORG reviewed-by:$LOGIN -author:$LOGIN is:pr created:$A..$B" -F query=@"$HERE/reviewed.graphql" \
    --jq '.data.search.nodes[] | @json' >> "$OUT/reviewed_prs.jsonl"
  echo "$A..$B done"
done
echo "authored: $(wc -l < "$OUT/authored_prs.jsonl")  reviewed: $(wc -l < "$OUT/reviewed_prs.jsonl")"
echo "Cross-check: gh search prs --owner $ORG --author $LOGIN --limit 1000 --json number --jq length (search caps at 1000; also compare the GitHub UI count)"
