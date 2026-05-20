"""Sampling parameters: deprecated on Opus 4.7, still legacy-supported on
Opus 4.6 / Sonnet 4.6.

Each of `temperature`, `top_p`, `top_k` is probed in parallel:
  * Opus 4.7 → all return 400 with a deprecation message
    (`info.contract = "rejected_deprecated"`).
  * Opus 4.6 / Sonnet 4.6 → all are accepted as legacy
    (`info.contract = "supported_legacy"`).

A bare call (no sampling params) must succeed in either case.
"""
from concurrent.futures import ThreadPoolExecutor

from anthropic import BadRequestError

from probes._base import text_of

NAME = "sampling_params_deprecated"
DESCRIPTION = (
    "temperature/top_p/top_k: rejected with deprecation on Opus 4.7; "
    "accepted on Opus 4.6 / Sonnet 4.6 (legacy)"
)

PARAMS = {"temperature": 0.0, "top_p": 0.9, "top_k": 40}

_CONTRACT_BY_STATES = {
    frozenset({"deprecated"}): "rejected_deprecated",
    frozenset({"accepted"}):   "supported_legacy",
}


def _classify(client, model, name, value) -> tuple[str, str]:
    """Return (status, detail). status ∈ {accepted, deprecated, unexpected}."""
    try:
        client.messages.create(
            model=model,
            max_tokens=8,
            messages=[{"role": "user", "content": "hi"}],
            **{name: value},
        )
        return "accepted", ""
    except BadRequestError as e:
        msg = e.message or ""
        if "deprecated" in msg.lower():
            return "deprecated", msg[:160]
        return "unexpected", msg[:160]


def run(client, model) -> dict:
    with ThreadPoolExecutor(max_workers=4) as ex:
        param_futures = {
            name: ex.submit(_classify, client, model, name, value)
            for name, value in PARAMS.items()
        }
        bare_future = ex.submit(
            client.messages.create,
            model=model, max_tokens=16,
            messages=[{"role": "user", "content": "Say 'sampled'."}],
        )
        signals = {name: f.result() for name, f in param_futures.items()}
        bare = bare_future.result()

    statuses = {name: status for name, (status, _) in signals.items()}
    contract = _CONTRACT_BY_STATES.get(frozenset(statuses.values()), "mixed_or_unexpected")
    bare_ok = bare.stop_reason in ("end_turn", "stop_sequence")
    ok = contract != "mixed_or_unexpected" and bare_ok

    return {
        "ok": ok,
        "info": {
            "contract": contract,
            "statuses": statuses,
            "details": {p: detail for p, (status, detail) in signals.items() if status != "accepted"},
            "bare_reply": text_of(bare)[:40],
        },
        "error": None if ok else (
            "mixed sampling-param statuses" if contract == "mixed_or_unexpected"
            else "bare call did not stop cleanly"
        ),
    }
