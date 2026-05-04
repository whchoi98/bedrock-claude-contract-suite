#!/usr/bin/env bash
# Verify .claude/hooks/ scripts exist, are executable, have valid bash syntax,
# and are registered in .claude/settings.json.

# Existence + executable
for h in check-doc-sync.sh secret-scan.sh session-context.sh notify.sh; do
    assert_file_exists "$h exists" ".claude/hooks/$h"
    assert_file_executable "$h is executable" ".claude/hooks/$h"
    assert_bash_syntax "$h has valid bash syntax" ".claude/hooks/$h"
done

# settings.json valid + each hook registered
assert_file_exists "settings.json exists" ".claude/settings.json"
assert_json_valid "settings.json is valid JSON" ".claude/settings.json"

SETTINGS=$(cat .claude/settings.json 2>/dev/null || echo "{}")
assert_contains "session-context.sh registered for SessionStart" "$SETTINGS" "session-context.sh"
assert_contains "secret-scan.sh registered for PreToolUse" "$SETTINGS" "secret-scan.sh"
assert_contains "check-doc-sync.sh registered for PostToolUse" "$SETTINGS" "check-doc-sync.sh"
assert_contains "notify.sh registered for Notification" "$SETTINGS" "notify.sh"

# Deny list contains the dangerous-command rules
assert_contains "deny list blocks rm -rf" "$SETTINGS" "rm -rf"
assert_contains "deny list blocks force push" "$SETTINGS" "git push --force"

# session-context.sh runs without error and emits expected lines
CTX_OUT=$(bash .claude/hooks/session-context.sh 2>&1 || true)
assert_contains "session-context emits Project line" "$CTX_OUT" "Project:"
assert_contains "session-context emits CLAUDE.md count" "$CTX_OUT" "CLAUDE.md files:"

# check-doc-sync.sh handles missing argument gracefully
DSYNC_OUT=$(bash .claude/hooks/check-doc-sync.sh 2>&1 || true)
assert_eq "check-doc-sync exits silently with no arg" "" "$DSYNC_OUT"

# check-doc-sync.sh warns when a tests/<cat>/test_*.py is missing the contract.
# The hook glob is `tests/*/test_*.py` (single level), so the fake file
# must live directly under a category-shaped directory.
FAKE_DIR="tests/_meta_probe"
mkdir -p "$FAKE_DIR"
FAKE_FILE="$FAKE_DIR/test_fake_probe.py"
echo "# missing NAME / DESCRIPTION / def run" > "$FAKE_FILE"
DSYNC_OUT=$(bash .claude/hooks/check-doc-sync.sh "$FAKE_FILE" 2>&1 || true)
assert_contains "check-doc-sync detects missing NAME" "$DSYNC_OUT" "NAME"
rm -rf "$FAKE_DIR"
