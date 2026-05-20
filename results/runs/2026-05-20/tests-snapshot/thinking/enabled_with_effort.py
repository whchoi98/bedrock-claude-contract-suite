"""thinking.type=enabled is the legacy explicit-budget mode.

Opus 4.7 rejects it and points users to adaptive + output_config.effort.
This test passes if the model either accepts enabled (legacy) or returns the
documented redirect message (Opus 4.7+).
"""
from anthropic import BadRequestError

NAME = "thinking_enabled_with_effort"
DESCRIPTION = "thinking.type=enabled supported (legacy) or cleanly redirected (Opus 4.7+)"


def run(client, model) -> dict:
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            thinking={"type": "enabled", "budget_tokens": 2048},
            messages=[
                {
                    "role": "user",
                    "content": "List the prime factors of 84. Reply with factors comma separated.",
                }
            ],
        )
    except BadRequestError as e:
        msg = (e.message or "").lower()
        redirected = "adaptive" in msg
        return {
            "ok": redirected,
            "info": {"contract": "rejected_use_adaptive", "message": e.message[:220]},
        }
    blocks = [b.type for b in resp.content]
    answer = "".join(b.text for b in resp.content if b.type == "text")
    has_thinking = "thinking" in blocks
    return {
        "ok": has_thinking and all(p in answer for p in ("2", "3", "7")),
        "info": {"contract": "supported", "blocks": blocks, "answer": answer[:80]},
    }
