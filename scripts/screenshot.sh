#!/usr/bin/env bash
# Screenshots a standalone page to check layout. Usage: screenshot.sh <page-standalone.html> <out.png> [width] [height]
set -euo pipefail
CHROME=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
SRC=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
"$CHROME" --headless --disable-gpu --hide-scrollbars --virtual-time-budget=8000 \
  --window-size="${3:-1280},${4:-2400}" --screenshot="$2" "file://$SRC" 2>/dev/null
echo "$2"
