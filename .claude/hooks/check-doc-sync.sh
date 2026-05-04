#!/bin/bash
# Detect documentation sync needs after file changes.
# Triggered by PostToolUse (Write|Edit) events.
# Adapted for bedrock-claude-contract-suite: source roots are tests/, scripts/, results/.

FILE_PATH="${1:-}"
[ -z "$FILE_PATH" ] && exit 0

SOURCE_ROOTS="tests scripts results"

for ROOT in $SOURCE_ROOTS; do
    if [[ "$FILE_PATH" == ${ROOT}/* ]]; then
        DIR=$(dirname "$FILE_PATH")
        FOUND_CLAUDE=false
        CHECK_DIR="$DIR"
        while [ "$CHECK_DIR" != "$ROOT" ] && [ "$CHECK_DIR" != "." ]; do
            if [ -f "$CHECK_DIR/CLAUDE.md" ]; then
                FOUND_CLAUDE=true
                break
            fi
            CHECK_DIR=$(dirname "$CHECK_DIR")
        done
        if ! $FOUND_CLAUDE && [ "$DIR" != "$ROOT" ]; then
            echo "[doc-sync] $DIR/CLAUDE.md is missing. Create module documentation."
        fi
        break
    fi
done

# New tests/<category>/test_*.py — remind to follow the contract
if [[ "$FILE_PATH" == tests/*/test_*.py ]]; then
    if ! grep -qE '^NAME\s*=' "$FILE_PATH" 2>/dev/null; then
        echo "[doc-sync] $FILE_PATH does not expose NAME = '...'. Required by run_all.py."
    fi
    if ! grep -qE '^DESCRIPTION\s*=' "$FILE_PATH" 2>/dev/null; then
        echo "[doc-sync] $FILE_PATH does not expose DESCRIPTION = '...'."
    fi
    if ! grep -qE '^def run\(' "$FILE_PATH" 2>/dev/null; then
        echo "[doc-sync] $FILE_PATH does not expose def run(client, model). Required by harness."
    fi
fi

IS_SOURCE=false
for ROOT in $SOURCE_ROOTS; do
    [[ "$FILE_PATH" == ${ROOT}/* ]] && IS_SOURCE=true && break
done
if $IS_SOURCE || [[ "$FILE_PATH" == docs/architecture.md ]]; then
    ADR_COUNT=$(find docs/decisions -name 'ADR-*.md' -not -name '.template.md' 2>/dev/null | wc -l)
    if [ "$ADR_COUNT" -eq 0 ]; then
        echo "[doc-sync] No ADRs found. Record architectural decisions in docs/decisions/."
    fi
fi

# Cache-related test edits — remind about cold-start salt requirement
if [[ "$FILE_PATH" == tests/caching/* ]]; then
    if ! grep -qE 'secrets\.token_hex|salt\s*=' "$FILE_PATH" 2>/dev/null; then
        echo "[doc-sync] $FILE_PATH may be a cache test without cold-start salt — see CLAUDE.md Conventions §3."
    fi
fi
