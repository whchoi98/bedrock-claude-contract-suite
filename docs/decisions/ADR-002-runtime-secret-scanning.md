# ADR-002: Runtime secret scanning at PreToolUse

## Status

Accepted

## Date

2026-05-03

## Context

The harness-eval pass `eval-2026-05-03-001` surfaced a CRITICAL finding:
13 inline AWS Bedrock API key (ABSK base64) values were stored verbatim in
`.claude/settings.local.json` lines 5, 9, 12, 13, 28, 29, 30, 39, 40, 52,
53, 54, 55. Each value was a real bearer token persisted on disk for
multi-day periods, reloaded into context every session.

The project's own `secret-scan.sh` hook was supposed to prevent exactly
this. Investigation showed why it didn't:

- The hook scanned `git diff --cached --name-only` — only files staged
  for commit.
- `.claude/settings.local.json` is gitignored. It is never staged.
  Therefore the hook never inspected it.
- The hook was registered for the PreToolUse Bash event, but the event
  payload (the proposed Bash command line) was discarded; the hook only
  used the event as a trigger to scan staged files.
- Every interactive testing session that ran a command of the form
  `AWS_BEARER_TOKEN_BEDROCK="ABSK..." python3 ...` resulted in Claude
  Code adding that command to the session's allow patterns, where the
  inline token was preserved indefinitely.

Two issues need to be addressed:
1. **Retrospective**: 13 tokens already on disk must be redacted.
2. **Prospective**: the hook must be extended to cover the channel where
   the leakage happens (the Bash command line), not only the channel
   where the leakage would *eventually* be committed (staged files).

This ADR documents the prospective fix. The retrospective fix (redaction
to `$AWS_BEARER_TOKEN_BEDROCK` env-var indirection) is a one-time data
migration with no architectural decision to record.

## Decision

Extend `.claude/hooks/secret-scan.sh` to a **dual-channel** design:

**Channel (a) — PreToolUse Bash command-line scan (NEW)**

When the hook runs as a PreToolUse[Bash] handler, Claude Code pipes a
JSON payload to stdin containing `tool_input.command` — the proposed
Bash command about to be executed. The hook now:

1. Detects whether stdin has data (`[ ! -t 0 ]`).
2. Reads with a 1-second `timeout cat` to avoid hanging if invoked
   manually.
3. Extracts `tool_input.command` via inline `python3 -c "import json,sys;
   ..."` (python3 is already a project prerequisite).
4. Runs the same `PATTERNS` regex list against the command text via
   `grep -qP`.
5. Exits 1 immediately on a match with a message that redirects the
   user to `$AWS_BEARER_TOKEN_BEDROCK` env-var indirection.

**Channel (b) — Staged-files scan (PRESERVED)**

The original `git diff --cached --name-only` scan is unchanged. It
still catches secrets that survived channel (a) (e.g., values committed
into ordinary files, not Bash command lines).

**Single source of truth**

Both channels iterate the same `PATTERNS` array (18 entries: AWS
AKIA, ABSK Bedrock, sk-ant Anthropic, GitHub PAT/OAuth/fine-grained,
Slack bot/user, Stripe, Google AIza/ya29, Azure connection string,
password / secret / api_key generic assignments). A new pattern is
added in one place; both channels pick it up automatically.

## Consequences

### Positive

- Inline secrets in Bash commands are blocked **before execution**,
  preventing accumulation in `settings.local.json` allow patterns.
- The hook now defends both layers (runtime channel + commit channel)
  with a unified pattern set — a single regex update extends both.
- Architecture is cleanly modular: a third channel (e.g., `Write`/`Edit`
  `tool_input.content`) could be added by another `scan_string` call
  without modifying any other component.
- Empirically validated: 5 manual probes confirm clean-pass / inline-ABSK
  block / Authorization-Bearer-ABSK block / env-var-indirection pass /
  malformed-JSON graceful behavior. Meta-test suite remains 87/87.
- harness-eval re-evaluation `eval-2026-05-04-001` shows
  Safety 6 → 8 (+2) and Feedback Loop Maturity 9 → 10 (+1) directly
  attributable to this change.

### Negative / Trade-offs

- Hook stdin reading adds a 1-second timeout in the path where the
  hook is invoked without a payload (e.g., manual test runs). Worst
  case: 1 second of additional latency per direct test invocation.
  Negligible in normal Claude Code flow where stdin always has data.
- `python3` becomes a hard runtime dependency for the hook. It was
  already a project prerequisite; this tightens the binding.
- The 5 channel-(a) manual probes are not yet encoded as automated
  assertions in the meta-test suite. A regression to the python3
  extraction path or the timeout logic would not be caught by
  `tests/_meta/run-all.sh`. (Tracked: completeness-evaluator finding,
  WARN tier, eval-2026-05-04-001.)

### Neutral

- `secret-scan.sh` grew from ~60 lines to ~118 lines.
- The hook header now documents both channels and the skip-list
  rationale explicitly, which is more verbose but more discoverable.

## Alternatives Considered

1. **Do nothing — accept that `settings.local.json` may contain inline
   secrets.** Rejected: that file is loaded into context every session
   and was the actual exposure surface. The harness-eval pass labeled
   this CRITICAL.

2. **Redact-only — clear the 13 existing tokens but leave the hook
   alone.** Rejected: would not prevent recurrence. Each future session
   that ran the same kind of inline-token command would re-add the
   pattern, and within days the file would re-accumulate live tokens.

3. **Block all `AWS_BEARER_TOKEN_BEDROCK=` patterns at PreToolUse
   regardless of value.** Rejected: too aggressive. Would prevent
   legitimate env-var indirection forms like
   `AWS_BEARER_TOKEN_BEDROCK=$AWS_BEARER_TOKEN_BEDROCK python3 ...`,
   which is the recommended safe pattern.

4. **Move the secret into the OS keyring (gnome-keyring, macOS Keychain,
   AWS SSM Parameter Store, etc.).** Rejected for now as a heavyweight
   change. Env-var indirection achieves the same exposure-reduction goal
   at near-zero cost. Reconsider if this project ever needs cross-host
   credential sharing.

5. **Periodic file-level scan of `.claude/settings.local.json`.**
   Considered as a complement, not a replacement. The dual-channel
   approach addresses the leakage at the source; a periodic scan would
   only catch leakage that escaped through some other path. Out of
   scope for this ADR; revisit if a third leakage vector is identified.

6. **Use `jq` instead of `python3` for JSON extraction in channel (a).**
   Rejected: `jq` is not a project dependency on the deployment host
   (Amazon Linux 2023). `python3` is already required.

## Verification

- **5 manual probes** (documented in `eval-2026-05-04-001` review):
  - Clean command (`python3 run_all.py --only caching`) → exit 0 (pass)
  - Inline ABSK token (`AWS_BEARER_TOKEN_BEDROCK="ABSK..." python3 ...`)
    → exit 1 with redirect-to-env-var message
  - Authorization Bearer ABSK (curl pattern) → exit 1
  - Env-var indirection (`$AWS_BEARER_TOKEN_BEDROCK`) → exit 0 (pass)
  - Malformed JSON on stdin → exit 0 (graceful, no crash)
- **Meta-test suite**: `tests/_meta/run-all.sh` 87/87 passing — no
  regression.
- **Retrospective state**: `grep -c 'ABSK' .claude/settings.local.json`
  returns 0; previously 13.
- **Harness-eval re-evaluation**: Safety 6 → 8 (+2),
  Feedback Loop Maturity 9 → 10 (+1) in `eval-2026-05-04-001`.

Future verification debt (tracked, not blocking this ADR):
- Encode the 5 manual probes as automated assertions in
  `tests/_meta/hooks/test-hooks.sh`.
- Expand `tests/_meta/hooks/test-secret-patterns.sh` to cover all 18
  PATTERNS (currently 5/18 = 28% coverage).

## References

- **Code**: `.claude/hooks/secret-scan.sh:62-89` (channel a),
  `.claude/hooks/secret-scan.sh:91-110` (channel b),
  `.claude/hooks/secret-scan.sh:24-43` (PATTERNS).
- **Tests**: `tests/_meta/hooks/test-secret-patterns.sh`,
  `tests/_meta/hooks/test-hooks.sh`.
- **Configuration**: `.claude/settings.json` registers the hook for
  PreToolUse[Bash]; `.claude/settings.local.json` was redacted.
- **Related ADRs**: [ADR-001](ADR-001-cold-start-salt-for-cache-tests.md)
  — same "real bug → fix + ADR + hook + meta-test" pattern applied to
  the caching domain. ADR-002 mirrors that structure.
- **Harness-eval reports**:
  - `eval-2026-05-03-001` — initial finding (Safety 6/10).
  - `eval-2026-05-04-001` — verification of remediation
    (Safety 8/10, Feedback Loop Maturity 10/10).
- **External**: Amazon Bedrock API key documentation
  (https://docs.aws.amazon.com/bedrock/) for the `ABSK` token format.

## Operational notes

When this token is rotated (P0 follow-up after eval-2026-05-04-001),
the new value should always be supplied via environment variable
indirection:

```bash
# Recommended pattern
export AWS_BEARER_TOKEN_BEDROCK="<rotated-key>"
AWS_BEARER_TOKEN_BEDROCK=$AWS_BEARER_TOKEN_BEDROCK python3 run_all.py
```

If a user accidentally types the literal value into a Bash command, the
PreToolUse hook (channel a) will block execution and print:

```
[secret-scan] Inline secret in Bash command line (pattern: ABSK[A-Za-z0-9+/]{60,}={0,2}...)

[secret-scan] BLOCKED: command contains an inline secret.
[secret-scan] Use $AWS_BEARER_TOKEN_BEDROCK (env-var indirection)
[secret-scan]   instead of pasting the literal value into the command.
```

This is the prospective guardrail. Future ADBSK leakage in `settings.local.json`
is now structurally impossible without disabling the hook.
