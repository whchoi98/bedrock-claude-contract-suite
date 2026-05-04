#!/bin/bash
# Dual-channel secret scanner.
#   (a) PreToolUse Bash command lines  — stdin JSON, blocks at runtime.
#   (b) git staged files               — `git diff --cached` on commit prep.
# Both channels share the PATTERNS list below. See
# docs/decisions/ADR-002-runtime-secret-scanning.md for the full
# architectural rationale (why dual-channel, alternatives considered,
# verification evidence).

SECRETS_FOUND=0

PATTERNS=(
    'AKIA[0-9A-Z]{16}'                          # AWS Access Key ID
    '(?<=aws_secret_access_key\s{0,5}[=:]\s{0,5})[A-Za-z0-9/+=]{40}' # AWS Secret Key
    'ABSK[A-Za-z0-9+/]{60,}={0,2}'              # AWS Bedrock API Key (base64)
    'sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}' # OpenAI API Key
    'sk-ant-[A-Za-z0-9-]{90,}'                   # Anthropic API Key
    'ghp_[A-Za-z0-9]{36}'                        # GitHub Personal Access Token
    'gho_[A-Za-z0-9]{36}'                        # GitHub OAuth Token
    'github_pat_[A-Za-z0-9_]{82}'                # GitHub Fine-grained PAT
    'xoxb-[0-9]+-[A-Za-z0-9]+'                   # Slack Bot Token
    'xoxp-[0-9]+-[A-Za-z0-9]+'                   # Slack User Token
    'sk_live_[A-Za-z0-9]{24,}'                   # Stripe Secret Key
    'rk_live_[A-Za-z0-9]{24,}'                   # Stripe Restricted Key
    'AIza[A-Za-z0-9_-]{35}'                      # Google API Key
    'ya29\.[A-Za-z0-9_-]{50,}'                   # Google OAuth Token
    'DefaultEndpointsProtocol=https;Account'     # Azure Connection String
    'password\s*[:=]\s*["\x27][^"\x27]{8,}'      # Password assignments
    'secret\s*[:=]\s*["\x27][^"\x27]{8,}'        # Secret assignments
    'api[_-]?key\s*[:=]\s*["\x27][^"\x27]{8,}'   # API key assignments
)

scan_string() {
    # Scan a single string against PATTERNS. Sets SECRETS_FOUND=1 on hit.
    # Args: $1 source label (for error message), $2 string to scan.
    local label="$1" content="$2"
    [ -z "$content" ] && return 0
    local hit=0
    for regex in "${PATTERNS[@]}"; do
        if printf '%s' "$content" | grep -qP "$regex" 2>/dev/null; then
            echo "[secret-scan] Inline secret in $label (pattern: ${regex:0:30}...)" >&2
            hit=1
        fi
    done
    if [ "$hit" -eq 1 ]; then
        SECRETS_FOUND=1
    fi
}

# ── (a) PreToolUse channel ───────────────────────────────────────────────
# Claude Code pipes a JSON payload to stdin on PreToolUse. Skip if no stdin.
if [ ! -t 0 ]; then
    HOOK_INPUT=$(timeout 1 cat 2>/dev/null || true)
    if [ -n "$HOOK_INPUT" ]; then
        # Extract tool_input.command via python3 (more robust than jq for
        # nested JSON; python3 is a project prerequisite).
        CMD=$(printf '%s' "$HOOK_INPUT" | python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    cmd = data.get('tool_input', {}).get('command', '') or ''
    print(cmd, end='')
except Exception:
    pass
" 2>/dev/null)
        if [ -n "$CMD" ]; then
            scan_string "Bash command line" "$CMD"
            if [ "$SECRETS_FOUND" -eq 1 ]; then
                echo "" >&2
                echo "[secret-scan] BLOCKED: command contains an inline secret." >&2
                echo "[secret-scan] Use \$AWS_BEARER_TOKEN_BEDROCK (env-var indirection)" >&2
                echo "[secret-scan]   instead of pasting the literal value into the command." >&2
                exit 1
            fi
        fi
    fi
fi

# ── (b) Staged-files channel ─────────────────────────────────────────────
SKIP_PATTERNS=('.env.example' 'secret-scan.sh' '*.md' 'package-lock.json' 'yarn.lock' 'tests/_meta/fixtures/*')
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null)
if [ -n "$STAGED_FILES" ]; then
    for file in $STAGED_FILES; do
        skip=false
        for pattern in "${SKIP_PATTERNS[@]}"; do
            [[ "$file" == $pattern ]] && skip=true && break
        done
        $skip && continue
        [ ! -f "$file" ] && continue

        for regex in "${PATTERNS[@]}"; do
            if grep -qP "$regex" "$file" 2>/dev/null; then
                echo "[secret-scan] Potential secret found in $file (pattern: ${regex:0:30}...)" >&2
                SECRETS_FOUND=1
            fi
        done
    done
fi

if [ "$SECRETS_FOUND" -eq 1 ]; then
    echo "" >&2
    echo "[secret-scan] BLOCKED: secrets detected. Review and remove before proceeding." >&2
    echo "[secret-scan] Use .env files for secrets and .env.example for templates." >&2
    exit 1
fi
exit 0
