#!/usr/bin/env bash
# Install git hooks for this project.
#
# Hooks installed:
#   commit-msg — strips Co-Authored-By lines from commit messages so AI
#                assistants (Claude, Copilot, Gemini, etc.) do not appear
#                as contributors in git history.
#
# Idempotent. Safe to run any time. Skips silently if .git/ does not exist
# (project is not a git repo yet).

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -d .git ]; then
    echo "[install-hooks] .git/ not found — run 'git init' first, then re-run this script."
    exit 0
fi

mkdir -p .git/hooks

cat > .git/hooks/commit-msg <<'HOOK'
#!/bin/bash
# Strip Co-Authored-By lines from commit messages.
# Excludes Claude / Copilot / Gemini / any AI assistant from git contributors.
# Covers case variants: Co-Authored-By, Co-authored-by, co-authored-by, etc.

# Remove all Co-Authored-By trailer lines (case-insensitive).
sed -i '/^[Cc]o-[Aa]uthored-[Bb]y:.*/d' "$1"

# Trim trailing blank lines left after removal.
sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}' "$1"
HOOK

chmod +x .git/hooks/commit-msg

echo "[install-hooks] commit-msg hook installed at .git/hooks/commit-msg"
echo "[install-hooks]   strips Co-Authored-By lines from every commit message"

# Optional: scrub history if any past commits already contain Co-Authored-By.
# Run manually if needed:
#   git filter-branch --msg-filter \
#     "sed '/^[Cc]o-[Aa]uthored-[Bb]y:.*/d' | sed -e :a -e '/^\n*\$/{\$d;N;ba' -e '}'" \
#     -- --all
