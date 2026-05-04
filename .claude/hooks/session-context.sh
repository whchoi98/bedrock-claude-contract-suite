#!/bin/bash
# Load project context at Claude Code session start.

echo "=== Project Context ==="
echo "Project: bedrock-claude-contract-suite (Python — Bedrock × Anthropic verification suite)"

# Token presence (without revealing the value)
if [ -n "${AWS_BEARER_TOKEN_BEDROCK:-}" ]; then
    echo "AWS_BEARER_TOKEN_BEDROCK: <set>"
else
    echo "AWS_BEARER_TOKEN_BEDROCK: ${TPUT_RED:-}NOT SET${TPUT_RESET:-} (run_all.py will fail)"
fi
echo "AWS_REGION:               ${AWS_REGION:-ap-northeast-2 (default)}"
echo "BEDROCK_MODEL_ID:         ${BEDROCK_MODEL_ID:-global.anthropic.claude-opus-4-7 (default)}"

# Latest matrix run, if any
if [ -f results/matrix.md ]; then
    LAST_LINE=$(grep -E '^\| `global' results/matrix.md 2>/dev/null | head -3)
    if [ -n "$LAST_LINE" ]; then
        echo ""
        echo "Latest matrix snapshot:"
        head -20 results/matrix.md | grep -E '^\| `(global|Model)' | head -5
    fi
fi

# Git state
LAST_COMMIT=$(git log -1 --format="%h %s (%cr)" 2>/dev/null)
[ -n "$LAST_COMMIT" ] && echo "Last commit: $LAST_COMMIT"
BRANCH=$(git branch --show-current 2>/dev/null)
[ -n "$BRANCH" ] && echo "Branch: $BRANCH"
CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
[ "$CHANGES" -gt 0 ] && echo "Uncommitted changes: $CHANGES file(s)"

CLAUDE_COUNT=$(find . -name "CLAUDE.md" -not -path "./.git/*" -not -path "./.claude/*" 2>/dev/null | wc -l | tr -d ' ')
echo "CLAUDE.md files: $CLAUDE_COUNT"

echo "======================"
