#!/usr/bin/env bash
# Verify the project structure is intact.

# Required top-level files
assert_file_exists "root CLAUDE.md present" "CLAUDE.md"
assert_file_exists "README.md present" "README.md"
assert_file_exists "config.py present" "config.py"
assert_file_exists "client.py present" "client.py"
assert_file_exists "run_all.py present" "run_all.py"
assert_file_exists "verify.sh present" "verify.sh"
assert_file_executable "verify.sh executable" "verify.sh"

# Required directories
for d in tests scripts results docs fixtures \
         .claude/hooks .claude/skills .claude/commands .claude/agents \
         docs/decisions docs/runbooks; do
    assert_dir_exists "$d/ exists" "$d"
done

# Module CLAUDE.md
for d in tests scripts results fixtures; do
    assert_file_exists "$d/CLAUDE.md exists" "$d/CLAUDE.md"
done

# Test category directory has _base.py and __init__.py
assert_file_exists "tests/_base.py present" "tests/_base.py"
assert_file_exists "tests/__init__.py present" "tests/__init__.py"

# Each test category has at least one test_*.py
for cat in caching messages tools thinking vision documents citations \
           streaming token_counting context multilingual client unsupported; do
    if [ -d "tests/$cat" ]; then
        COUNT=$(find "tests/$cat" -name 'test_*.py' -not -path '*/__pycache__/*' | wc -l | tr -d ' ')
        if [ "$COUNT" -gt 0 ]; then
            pass "tests/$cat has $COUNT test file(s)"
        else
            fail "tests/$cat has no test_*.py" "expected at least one"
        fi
    fi
done

# tests/_base.py exposes the shared helpers
BASE_TXT=$(cat tests/_base.py)
assert_contains "_base.py defines text_of" "$BASE_TXT" "def text_of"
assert_contains "_base.py defines usage_breakdown" "$BASE_TXT" "def usage_breakdown"
assert_contains "_base.py defines is_unsupported_tool_rejection" "$BASE_TXT" "def is_unsupported_tool_rejection"
assert_contains "_base.py defines Result" "$BASE_TXT" "class Result"
assert_contains "_base.py defines execute" "$BASE_TXT" "def execute"

# verify.sh contains the cost notice
VSH=$(head -50 verify.sh)
assert_contains "verify.sh has token cost notice" "$VSH" "Token / cost notice"
assert_contains "verify.sh notice mentions matrix run cost" "$VSH" "matrix run"

# run_all.py emits TokenAccumulator summary
RUNALL=$(cat run_all.py)
assert_contains "run_all.py defines TokenAccumulator" "$RUNALL" "class TokenAccumulator"
assert_contains "run_all.py prints token summary" "$RUNALL" "_print_token_summary"

# Architecture doc bilingual sections
ARCH=$(cat docs/architecture.md 2>/dev/null || echo "")
assert_contains "architecture.md has Korean section" "$ARCH" "한국어"
assert_contains "architecture.md has English section" "$ARCH" "# English"

# At least one ADR exists
ADR_COUNT=$(find docs/decisions -name 'ADR-*.md' -not -name '.template.md' 2>/dev/null | wc -l | tr -d ' ')
[ "$ADR_COUNT" -gt 0 ] && pass "at least one ADR present" || fail "ADR count" "no ADR-*.md in docs/decisions/"

# At least one runbook exists
RBOOK_COUNT=$(find docs/runbooks -name '*.md' -not -name '.template.md' 2>/dev/null | wc -l | tr -d ' ')
[ "$RBOOK_COUNT" -gt 0 ] && pass "at least one runbook present" || fail "runbook count" "no runbooks in docs/runbooks/"
