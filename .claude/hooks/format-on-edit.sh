#!/usr/bin/env bash
# PostToolUse hook on Edit|Write.
# Formats the file in place based on extension. Exit 0 always — formatting
# failures are reported but never block the edit.

set -uo pipefail

input="$(cat)"

target="$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
' 2>/dev/null || true)"

if [ -z "$target" ] || [ ! -f "$target" ]; then
    exit 0
fi

case "$target" in
    *.py)
        if command -v black >/dev/null 2>&1; then
            black --quiet "$target" 2>/dev/null || true
        fi
        ;;
    *.js|*.jsx|*.ts|*.tsx|*.json|*.css|*.md)
        if command -v npx >/dev/null 2>&1; then
            npx --no-install prettier --write --loglevel silent "$target" 2>/dev/null || true
        fi
        ;;
esac

exit 0
