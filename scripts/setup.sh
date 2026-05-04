#!/usr/bin/env bash
# Project setup for a new contributor to bedrock-claude-contract-suite.
#
# Idempotent. Safe to re-run.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== bedrock-claude-contract-suite setup ==="

# 1. Prerequisites
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 required"; exit 1; }
PYV=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python: $PYV"

# 2. Python dependencies (this project has no formal package manifest;
#    we install the runtime deps directly).
echo "Checking required Python packages..."
MISSING=()
for pkg in anthropic httpx boto3; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        MISSING+=("$pkg")
    fi
done
if [ ${#MISSING[@]} -gt 0 ]; then
    echo "Installing: ${MISSING[*]}"
    python3 -m pip install --user "${MISSING[@]}"
else
    echo "All Python packages present."
fi

# 3. Environment file
if [ -f .env.example ] && [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "IMPORTANT: edit .env and set AWS_BEARER_TOKEN_BEDROCK"
fi

# 4. Claude hooks executable
if [ -d .claude/hooks ]; then
    chmod +x .claude/hooks/*.sh 2>/dev/null || true
    echo "Claude hooks made executable."
fi

# 5. Git commit-msg hook (skips silently if not a git repo)
if [ -f scripts/install-hooks.sh ]; then
    bash scripts/install-hooks.sh
fi

# 6. Smoke check (optional — only if token already set)
if [ -n "${AWS_BEARER_TOKEN_BEDROCK:-}" ]; then
    echo
    echo "Smoke test: running a single 'basic' messages test..."
    python3 run_all.py --only-tests basic --no-save 2>&1 | tail -10 || {
        echo "Smoke test failed — check token/region/model access."
    }
else
    echo
    echo "AWS_BEARER_TOKEN_BEDROCK not set — skipping smoke test."
    echo "After setting it (or sourcing .env), run:"
    echo "    python3 run_all.py --only-tests basic"
fi

echo
echo "=== Setup complete ==="
echo "Next steps:"
echo "  1. Edit .env (set AWS_BEARER_TOKEN_BEDROCK)"
echo "  2. Read CLAUDE.md for conventions"
echo "  3. Read docs/onboarding.md for the development workflow"
echo "  4. Run ./verify.sh for the interactive launcher"
