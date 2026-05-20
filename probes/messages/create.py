"""Smoke test: a single non-streaming user message round-trip."""
from probes._base import text_of

NAME = "basic"
DESCRIPTION = "messages.create round-trip with one user turn"


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=64,
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
    )
    txt = text_of(resp)
    return {
        "ok": resp.stop_reason in ("end_turn", "stop_sequence") and "OK" in txt,
        "info": {
            "stop_reason": resp.stop_reason,
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "text": txt[:80],
        },
    }
