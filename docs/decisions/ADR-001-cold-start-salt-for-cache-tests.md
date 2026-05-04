# ADR-001: Cold-start salt for cache-related tests

## Status

Accepted

## Date

2026-05-03

## Context

Cache-related tests (`tests/caching/test_ttl_*.py`,
`results/variability_probe.py`, `results/stable_prefix_probe.py`) were
producing run-to-run variable results. Investigation showed that with a
stable cached prefix, the first invocation performs a fresh write, but
subsequent invocations within the cache TTL window observe only reads
— `cache_creation_input_tokens == 0` even though the underlying
caching contract is functioning correctly.

This caused two concrete false-positive episodes during development:

1. `cache_ttl_1h` was originally asserted as ⛔ "1h not supported on
   Bedrock" because reads showed `ephemeral_1h_input_tokens=0`. The
   test was actually observing a read of a 5m cache from a prior run,
   not testing the 1h logic at all.
2. The mixed 5m+1h test passed even when the 1h bucket was empty,
   because its OR-fallback assertion accepted any cache read as proof.

Stable-prefix probe data (`results/stable_prefix_probe.json`):
trial 1 fresh-write into 1h bucket; trials 2–5 read-only with 1h bucket
reporting 0.

## Decision

Every cache-related test in this suite MUST embed a unique per-run
salt (`secrets.token_hex(8)`) into the cached prefix to force a cold
start. The first call must be a verifiable fresh write
(`cache_creation_input_tokens > 0` AND `cache_read_input_tokens == 0`)
before any other assertion is evaluated.

Concretely:

```python
import secrets
salt = secrets.token_hex(8)
sys_blocks = [{
    "type": "text",
    "text": f"Run salt {salt}. " + _PREFIX,
    "cache_control": {"type": "ephemeral", "ttl": "1h"},
}]
```

The prefix's bulk content (`_PREFIX`) is module-level to avoid
recomputing the 1500× multiplied string per call. Only the salt portion
varies between runs.

Asserting strictness — no OR-fallback. The test must check the specific
signal it intends to measure (e.g. `create_1h > 0 AND create_5m == 0`),
not "any cache activity is fine."

## Consequences

### Positive
- Cache test results become deterministic across runs (5/5 cold-start
  trials in `variability_probe.json` produce the same contract verdict).
- Contract drift surfaces immediately as a test failure rather than
  hiding behind cache state.
- The 1h-supported finding (now `results/prompt_caching_verified.md`
  §1.2) is reproducible; without salt, that finding could not be made.

### Negative / Trade-offs
- Each test invocation forces a fresh cache write on Bedrock — small
  per-run cost increase (~$0.30 across 3 models per matrix run, see
  `verify.sh` cost notice). Acceptable for the determinism gained.
- Tests cannot validate hot-cache behavior (read-only path). If a
  future test needs to verify the read path, it should call twice
  (with the same salt) and assert read on the second call.

### Neutral
- The salt makes per-run input tokens slightly higher due to the
  added prefix bytes. Counted in TokenAccumulator output.

## Alternatives Considered

- **Stable prefix + accept either fresh-write or hot-read**: rejected
  because OR-fallback assertions silently hide contract drift. The
  test would pass even if the underlying logic broke, as long as some
  cache state remained.
- **TTL-based reset (wait 1h between runs)**: impractical for CI/dev
  loop.
- **External cache-invalidation API**: Bedrock does not expose one for
  prompt caches.

## Verification

- `results/variability_probe.json` — 5 cold-start trials, each
  populates `ephemeral_1h_input_tokens` with 39K–43K.
- `results/stable_prefix_probe.json` — 5 stable-prefix trials, only
  trial 1 shows fresh write; trials 2–5 are reads.
- The contrast between these two probes is the empirical proof of
  this decision's necessity.

## References

- `tests/caching/test_ttl_1h.py`
- `tests/caching/test_ttl_mixed.py`
- `results/prompt_caching_verified.md` §P-1 (Cold-start salt)
- Root `CLAUDE.md` Conventions §3
