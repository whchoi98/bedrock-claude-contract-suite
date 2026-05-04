"""Assistant prefill behavior.

Older Anthropic models continue from a trailing assistant turn. Opus 4.7
explicitly rejects this with: "This model does not support assistant message
prefill. The conversation must end with a user message."

This test passes if EITHER the continuation works (older models) OR the model
rejects it with the documented "must end with a user message" message
(Opus 4.7+). That keeps the same test green across models while loudly
flagging if the contract changes again.
"""
from anthropic import BadRequestError

from tests._base import text_of

NAME = "assistant_prefill"
DESCRIPTION = "prefill works (legacy) OR is cleanly rejected (Opus 4.7+ contract)"


def run(client, model) -> dict:
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=64,
            messages=[
                {"role": "user", "content": "List three primary colors."},
                {"role": "assistant", "content": "1. Red\n2."},
            ],
        )
    except BadRequestError as e:
        msg = (e.message or "").lower()
        rejected_clearly = "prefill" in msg or "end with a user message" in msg
        return {
            "ok": rejected_clearly,
            "info": {"contract": "rejected", "message": e.message[:200]},
        }
    txt = text_of(resp).lower()
    continued = ("blue" in txt or "yellow" in txt) and not txt.lstrip().startswith("1.")
    return {
        "ok": continued,
        "info": {"contract": "supported", "continuation_preview": txt[:80]},
    }
