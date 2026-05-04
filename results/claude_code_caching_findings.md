# Claude Code on Bedrock — empirical caching contract

Captured 2026-05-03 by intercepting Claude Code v2.1.126's outbound HTTP via
a local proxy (`scripts/intercept_proxy.py`) and forwarding to
`https://bedrock-runtime.ap-northeast-2.amazonaws.com`.

The proxy parses every request body, extracts every `cache_control` block,
records its TTL value, and relays the request unchanged to the real
Bedrock endpoint so Claude Code receives an authentic response.

## Method

For each scenario:
- run `claude -p "<short prompt>" --model <id>` non-interactively
- with `HOME=/tmp/claude-experiment-X` to avoid contaminating the user's
  Claude Code state
- `ANTHROPIC_BEDROCK_BASE_URL=http://127.0.0.1:9001` (Invoke API) or
  `ANTHROPIC_BEDROCK_MANTLE_BASE_URL=http://127.0.0.1:9001` (Mantle)

Each scenario was a single `claude -p` invocation that produced one
response and exited. The proxy logs are in
`logs/intercept.jsonl`.

## Results

### Experiment A — Bedrock Invoke, default

```
CLAUDE_CODE_USE_BEDROCK=1
```

Outbound request to `/model/global.anthropic.claude-opus-4-7/invoke-with-response-stream`:

| location | cache_control |
| --- | --- |
| `$.system[1]` | `{"type": "ephemeral"}` |
| `$.system[2]` | `{"type": "ephemeral"}` |
| `$.messages[0].content[3]` | `{"type": "ephemeral"}` |

→ no `ttl` field → Bedrock interprets as 5 minutes (default).
→ HTTP 200, response was returned correctly.

### Experiment B — Bedrock Invoke + 1h

```
CLAUDE_CODE_USE_BEDROCK=1
ENABLE_PROMPT_CACHING_1H=1
```

| location | cache_control |
| --- | --- |
| `$.system[1]` | `{"type": "ephemeral", "ttl": "1h"}` |
| `$.system[2]` | `{"type": "ephemeral", "ttl": "1h"}` |
| `$.messages[0].content[3]` | `{"type": "ephemeral", "ttl": "1h"}` |

→ Claude Code sets `ttl: "1h"` on every breakpoint.
→ HTTP 200, response was returned correctly.

### Experiment C — Bedrock Invoke + disable

```
CLAUDE_CODE_USE_BEDROCK=1
DISABLE_PROMPT_CACHING=1
```

| location | cache_control |
| --- | --- |
| (none) | (no breakpoints anywhere in the request body) |

→ `cache_breakpoint_count == 0` for both Haiku and Opus calls.
→ Request body still ~71KB (system prompt + tools), but caching directive
  is fully stripped.
→ HTTP 200, response was returned correctly.

### Experiment D — Mantle, default

```
CLAUDE_CODE_USE_MANTLE=1
```

Outbound path: `/v1/messages?beta=true` (Anthropic Messages shape, NOT Bedrock
Invoke shape).

Request body top-level keys: `context_management`, `max_tokens`, `messages`,
`metadata`, `model`, `stream`, `system`, `thinking`, `tools` —
`model` is in the body (Anthropic API style), unlike Invoke where it is in
the URL path.

| location | cache_control |
| --- | --- |
| `$.system[1]` | `{"type": "ephemeral"}` |
| `$.system[2]` | `{"type": "ephemeral"}` |
| `$.messages[0].content[2]` | `{"type": "ephemeral"}` |

→ same default as Invoke (no ttl, defaults to 5m).

### Experiment D2 — Mantle + 1h

```
CLAUDE_CODE_USE_MANTLE=1
ENABLE_PROMPT_CACHING_1H=1
```

| location | cache_control |
| --- | --- |
| `$.system[1]` | `{"type": "ephemeral", "ttl": "1h"}` |
| `$.system[2]` | `{"type": "ephemeral", "ttl": "1h"}` |
| `$.messages[0].content[2]` | `{"type": "ephemeral", "ttl": "1h"}` |

→ same 1h injection as Invoke.

## Summary matrix

| scenario                                   | path                           | breakpoints | ttl           |
| ------------------------------------------ | ------------------------------ | ----------- | ------------- |
| Bedrock Invoke, default                    | `/model/{id}/invoke-with-…`    | 3           | none → **5m** |
| Bedrock Invoke + `ENABLE_PROMPT_CACHING_1H`| `/model/{id}/invoke-with-…`    | 3           | **`"1h"`**    |
| Bedrock Invoke + `DISABLE_PROMPT_CACHING`  | `/model/{id}/invoke-with-…`    | **0**       | n/a           |
| Mantle, default                            | `/v1/messages?beta=true`       | 3           | none → **5m** |
| Mantle + `ENABLE_PROMPT_CACHING_1H`        | `/v1/messages?beta=true`       | 3           | **`"1h"`**    |

## Conclusions

1. **Claude Code's `ENABLE_PROMPT_CACHING_1H=1` does what the docs claim.**
   The flag injects `ttl: "1h"` into every cache_control breakpoint Claude
   Code emits (verified at the byte level in 2 different request formats:
   Bedrock Invoke and Mantle). Without the flag, the same breakpoints are
   emitted with no `ttl` field, leaving Bedrock to use the 5-minute default.

2. **`DISABLE_PROMPT_CACHING=1` strips cache_control entirely.** Claude Code
   does not just remove the `ttl` — it removes the whole `cache_control`
   block, so even the 5-minute path is disabled.

3. **Mantle vs Invoke caching contract is identical at the cache_control
   level.** Both use the same shape of cache_control object on the same
   logical breakpoint locations (system blocks 1 and 2, plus the last
   user-message content block). The difference between them is the request
   envelope:
   - Invoke: model in URL path, body keyed by `anthropic_version`
   - Mantle: model in body, body keyed like Anthropic Messages API,
     including `context_management`, `thinking`, etc.
   This means Mantle does not require any caching-specific changes when
   migrating from Invoke — if your account is on the Mantle allowlist for
   the model, behavior is the same.

4. **The breakpoint count is 3, not 1, even on a single-shot non-interactive
   `claude -p`.** Claude Code marks two system blocks (the agent system
   prompt itself, plus tool/environment context) and the last user-message
   content block. This is the standard "split the prompt at stable
   boundaries" pattern; it lets the cache survive the addition of new turns
   without invalidating earlier prefixes.

## Caveats

- The 1h cache observation is a property of *what Claude Code SENDS*, not
  what Bedrock does with it. The companion finding in
  `bedrock-claude-contract-suite/results/matrix.md` already establishes that
  Bedrock honors `ttl="1h"` (it populates `ephemeral_1h_input_tokens`).
  Together: Claude Code on Bedrock with `ENABLE_PROMPT_CACHING_1H=1`
  → 1h cache writes actually land in the 1h bucket.
- Streaming response parsing through the proxy was lossy (Claude Code
  sometimes reported "empty response") because the simple proxy buffers
  the full response before relaying. That affected response delivery but
  not the request capture, which is what these conclusions rest on.
- Tested only Opus 4.7 and Haiku 4.5 in `ap-northeast-2`. Other regions
  may differ if cache feature availability differs by region (the docs
  warn "prompt caching may not be available in all regions").
