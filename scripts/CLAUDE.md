# scripts/ Module

## Role

Out-of-band utilities for ad-hoc API exploration. Distinct from `tests/`:
- `tests/` encode permanent contracts that run on every matrix execution.
- `scripts/` are one-off probes used to investigate behavior, capture
  evidence for a specific claim, or run a long-lived helper (proxy).

Probes write JSON output to `results/*_probe.json` so findings are
permanently captured even when the probe script is later modified.

## Key Files

- **`intercept_proxy.py`** — local HTTP proxy that captures Claude
  Code's outbound requests to Bedrock. Forwards to upstream so Claude
  Code receives real responses while we record the request shape
  (cache_control breakpoints, TTL values, body keys). Logs to
  `logs/intercept.jsonl`.
  - Env: `--upstream`, `--port`, `--label`, `--log-file`
  - Single `httpx.Client` reused across requests; line-buffered log fd
    held open for the proxy's lifetime.

- **`probe_structured_outputs.py`** — probes 5 variants of structured
  outputs (`response_format` OpenAI-style, `output_config.format` GA,
  legacy `output_format` with/without beta header, `tools[].strict=true`)
  across all 3 models in parallel. Output:
  `results/structured_outputs_probe.json`.

- **`probe_token_counting.py`** — probes 3 paths to token counting:
  Anthropic SDK `messages.count_tokens()`, raw HTTP to
  `/model/{id}/count-tokens` (AWS-native), raw HTTP to
  `/v1/messages/count_tokens` (Anthropic-shape). Output:
  `results/token_counting_probe.json`.

## Rules

- **Use `make_client()`** for SDK-based probes — picks up
  `AWS_BEARER_TOKEN_BEDROCK` consistently.
- **Use `config.ALL_MODELS` / `config.REGION`** — don't redeclare model
  lists.
- **Reuse `tests._base.text_of`** — don't reimplement text concatenation.
- **Narrow exception handling** — `except (httpx.HTTPError, ...)`, not
  bare `except Exception`.
- **Output to `results/<probe_name>_probe.json`** — preserve raw findings
  for evidence-citing in `results/docs_vs_reality.md`.
- **Parallelize independent calls** — probes that test N variants per
  model should use `concurrent.futures.ThreadPoolExecutor` for the
  variants. Models stay sequential for clean log output.
- **Document every probe** — add a one-paragraph description to this
  CLAUDE.md when adding a new probe.

## When to add a probe vs a test

| Situation | Add to |
|---|---|
| One specific behavior to encode as permanent contract | `tests/<cat>/test_*.py` |
| Multiple variants explored to find what works | `scripts/probe_*.py` |
| Long-lived utility used during a debugging session | `scripts/<utility>.py` |
| Statistical/repeated measurement | `results/*_probe.py` (close to data) |
