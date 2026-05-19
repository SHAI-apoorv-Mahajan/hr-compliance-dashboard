#!/usr/bin/env bash
# Stop hook. Runs the project's test suite.
# Exit 2 if any suite fails → returns control to Claude (invokes error-log via SubagentStart).
# Exit 0 if everything green, or if there are no tests to run yet.

set -uo pipefail

failed=0

# Backend tests — only run if backend/ exists and pytest is installed.
if [ -d "backend" ] && command -v pytest >/dev/null 2>&1; then
    pushd backend >/dev/null
    if ! pytest -q --no-header 2>&1; then
        failed=1
    fi
    popd >/dev/null
fi

# Frontend tests — only run if frontend/ exists and package.json declares a "test" script.
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    if grep -q '"test"' frontend/package.json; then
        pushd frontend >/dev/null
        if ! npm test --silent 2>&1; then
            failed=1
        fi
        popd >/dev/null
    fi
fi

if [ "$failed" -eq 1 ]; then
    echo "run-tests-on-stop: test suite failed" >&2
    exit 2
fi

exit 0
