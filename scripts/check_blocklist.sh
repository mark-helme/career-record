#!/usr/bin/env bash
# Fails if any blocklisted term (one per line, case-insensitive) appears in the given files.
# Usage: check_blocklist.sh <blocklist.txt> <file>...
set -uo pipefail
LIST=$1; shift
HITS=$(grep -oiFf "$LIST" "$@" | sort | uniq -c)
if [ -n "$HITS" ]; then echo "BLOCKLIST HITS:"; echo "$HITS"; exit 1; fi
echo "0 blocklist hits in $*"
