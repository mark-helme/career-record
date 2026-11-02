#!/usr/bin/env bash
# Wraps an artifact page in a document skeleton and prints it to PDF with headless Chrome.
# Usage: export_pdf.sh <page.html>   -> <page>-standalone.html and <page>.pdf next to it
set -euo pipefail
SRC=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
BASE=${SRC%.html}
CHROME=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
{ printf '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>\n'
  cat "$SRC"; printf '\n</body></html>\n'; } > "$BASE-standalone.html"
"$CHROME" --headless --disable-gpu --no-pdf-header-footer --virtual-time-budget=8000 \
  --print-to-pdf="$BASE.pdf" "file://$BASE-standalone.html" 2>/dev/null
echo "$BASE.pdf: $(python3 -c "import re,sys;print(len(re.findall(rb'/Type\\s*/Page[^s]',open(sys.argv[1],'rb').read())))" "$BASE.pdf") pages"
