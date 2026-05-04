#!/usr/bin/env bash
# Meta-test runner — validates harness engineering quality.
#
# Distinct from the project's main test suite: `python3 run_all.py`
# verifies the Bedrock × Anthropic API contract; this runner verifies
# that our hooks, settings, structure, and CLAUDE.md hygiene are intact.
#
# Usage:
#   bash tests/_meta/run-all.sh             # run all meta-tests
#   bash tests/_meta/run-all.sh hooks       # run only hook tests
#   bash tests/_meta/run-all.sh structure   # run only structure tests

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0
FAILURES=()

export TEST_RUNNER_ACTIVE=1

pass() {
    TOTAL=$((TOTAL + 1)); PASSED=$((PASSED + 1))
    echo -e "  ${GREEN}✓${NC} $1"
}
fail() {
    TOTAL=$((TOTAL + 1)); FAILED=$((FAILED + 1))
    FAILURES+=("$1: $2")
    echo -e "  ${RED}✗${NC} $1"
    echo -e "    ${RED}→ $2${NC}"
}
skip() {
    TOTAL=$((TOTAL + 1)); SKIPPED=$((SKIPPED + 1))
    echo -e "  ${YELLOW}○${NC} $1 (skipped: $2)"
}

assert_eq() {
    local desc="$1" expected="$2" actual="$3"
    [ "$expected" = "$actual" ] && pass "$desc" || fail "$desc" "expected '$expected', got '$actual'"
}
assert_contains() {
    local desc="$1" haystack="$2" needle="$3"
    echo "$haystack" | grep -q "$needle" && pass "$desc" || fail "$desc" "output does not contain '$needle'"
}
assert_file_exists() {
    local desc="$1" filepath="$2"
    [ -f "$filepath" ] && pass "$desc" || fail "$desc" "file not found: $filepath"
}
assert_dir_exists() {
    local desc="$1" dirpath="$2"
    [ -d "$dirpath" ] && pass "$desc" || fail "$desc" "directory not found: $dirpath"
}
assert_file_executable() {
    local desc="$1" filepath="$2"
    [ -x "$filepath" ] && pass "$desc" || fail "$desc" "file not executable: $filepath"
}
assert_json_valid() {
    local desc="$1" filepath="$2"
    python3 -m json.tool "$filepath" > /dev/null 2>&1 && pass "$desc" || fail "$desc" "invalid JSON: $filepath"
}
assert_bash_syntax() {
    local desc="$1" filepath="$2"
    bash -n "$filepath" 2>/dev/null && pass "$desc" || fail "$desc" "bash syntax error in: $filepath"
}
assert_grep_match() {
    local desc="$1" pattern="$2" input="$3"
    echo "$input" | grep -qP "$pattern" 2>/dev/null && pass "$desc" || fail "$desc" "pattern '$pattern' did not match"
}
assert_grep_no_match() {
    local desc="$1" pattern="$2" input="$3"
    echo "$input" | grep -qP "$pattern" 2>/dev/null && fail "$desc" "pattern '$pattern' matched (expected no match)" || pass "$desc"
}

export -f pass fail skip assert_eq assert_contains assert_file_exists assert_dir_exists
export -f assert_file_executable assert_json_valid assert_bash_syntax
export -f assert_grep_match assert_grep_no_match

FILTER="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${CYAN}=== Harness Meta-Test Suite ===${NC}"
echo

TEST_FILES=$(find "$SCRIPT_DIR" -name "test-*.sh" | sort)

for test_file in $TEST_FILES; do
    test_name=$(basename "$test_file" .sh)
    if [ -n "$FILTER" ] && ! echo "$test_name" | grep -q "$FILTER"; then
        continue
    fi
    echo -e "${CYAN}▸ $test_name${NC}"
    # shellcheck disable=SC1090
    source "$test_file"
    echo
done

echo -e "${CYAN}=== Results ===${NC}"
echo -e "  Total:   $TOTAL"
echo -e "  ${GREEN}Passed:  $PASSED${NC}"
[ "$FAILED" -gt 0 ]  && echo -e "  ${RED}Failed:  $FAILED${NC}"  || echo -e "  Failed:  $FAILED"
[ "$SKIPPED" -gt 0 ] && echo -e "  ${YELLOW}Skipped: $SKIPPED${NC}" || echo -e "  Skipped: $SKIPPED"
echo

if [ "$FAILED" -gt 0 ]; then
    echo -e "${RED}Failures:${NC}"
    for f in "${FAILURES[@]}"; do echo "  - $f"; done
    exit 1
fi
exit 0
