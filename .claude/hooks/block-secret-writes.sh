#!/usr/bin/env bash
# PreToolUse hook on Write|Edit.
# Reads the tool call from stdin (JSON) and blocks writes to secret files.
# Exit 2 = blocked (returned to Claude). Exit 0 = allow.

set -euo pipefail

input="$(cat)"

# Extract the target path from the tool input. We accept both Write (file_path)
# and Edit (file_path) shapes; both use file_path.
target="$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
' 2>/dev/null || true)"

if [ -z "$target" ]; then
    exit 0
fi

# Normalize to forward slashes for matching on Windows / Git Bash.
norm="${target//\\//}"

case "$norm" in
    */.env|*/.env.*|*.env|*.env.*)
        echo "block-secret-writes: refusing to write to .env file: $target" >&2
        exit 2
        ;;
    */secrets/*|*/credentials.json|*/credentials.*.json)
        echo "block-secret-writes: refusing to write to credential file: $target" >&2
        exit 2
        ;;
esac

exit 0
