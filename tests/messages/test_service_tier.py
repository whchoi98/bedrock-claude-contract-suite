"""service_tier parameter (Anthropic-direct concept; Bedrock may ignore or reject)."""
from anthropic import BadRequestError

from tests._base import text_of

NAME = "service_tier"
DESCRIPTION = "service_tier='auto' is accepted, ignored, or cleanly rejected on Bedrock"


def run(client, model) -> dict:
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=16,
            messages=[{"role": "user", "content": "Say 'tier-ok'."}],
            extra_body={"service_tier": "auto"},
        )
        return {
            "ok": resp.stop_reason in ("end_turn", "stop_sequence"),
            "info": {"reply": text_of(resp)[:40], "stop_reason": resp.stop_reason},
        }
    except BadRequestError as e:
        # Cleanly rejected with a clear message is also acceptable; we just want
        # a documented contract, not a server-side surprise.
        msg = e.message or str(e)
        return {
            "ok": True,
            "info": {"rejected_with": msg[:160]},
        }
