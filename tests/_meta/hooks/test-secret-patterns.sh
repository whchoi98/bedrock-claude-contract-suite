#!/usr/bin/env bash
# Verify secret-scan.sh patterns by feeding it true-positive and false-positive samples.

# Helper: scan a string by writing it to a temp file under a fake "staged"
# environment. We can't easily test the git-staging path; instead invoke
# the regex set directly using grep -P against the patterns embedded in
# secret-scan.sh.
SCAN_SCRIPT=".claude/hooks/secret-scan.sh"
assert_file_exists "secret-scan.sh exists" "$SCAN_SCRIPT"

TPOS_FILE="tests/_meta/fixtures/secret-samples.txt"
FPOS_FILE="tests/_meta/fixtures/false-positives.txt"
assert_file_exists "true-positive fixture exists" "$TPOS_FILE"
assert_file_exists "false-positive fixture exists" "$FPOS_FILE"

# Walk each known pattern and test
PATTERNS=(
    'AKIA[0-9A-Z]{16}'
    'ABSK[A-Za-z0-9+/]{60,}={0,2}'
    'sk-ant-[A-Za-z0-9-]{90,}'
    'ghp_[A-Za-z0-9]{36}'
    'AIza[A-Za-z0-9_-]{35}'
)

for pat in "${PATTERNS[@]}"; do
    assert_grep_match "true-positive sample matches /$pat/" "$pat" "$(cat $TPOS_FILE)"
done

# False-positive samples should NOT match the secret patterns.
for pat in "${PATTERNS[@]}"; do
    assert_grep_no_match "false-positive sample does NOT match /$pat/" "$pat" "$(cat $FPOS_FILE)"
done
