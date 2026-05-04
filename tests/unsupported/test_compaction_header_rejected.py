"""Compaction beta header — docs say bedrockBeta, reality rejects 'invalid beta flag'."""
from anthropic import BadRequestError

NAME = "compaction_beta_header_rejected_on_bedrock"
DESCRIPTION = "anthropic-beta: compaction-2025-09-17 rejected on Bedrock despite docs"


def run(client, model) -> dict:
    try:
        client.messages.create(
            model=model,
            max_tokens=8,
            messages=[{"role": "user", "content": "hi"}],
            extra_headers={"anthropic-beta": "compaction-2025-09-17"},
        )
    except BadRequestError as e:
        msg = (e.message or "").lower()
        return {
            "ok": "invalid beta flag" in msg,
            "info": {"contract": "rejected", "message": e.message[:160]},
        }
    return {"ok": False, "info": {"contract": "accepted_unexpectedly"},
            "error": "compaction header accepted — update README findings"}
