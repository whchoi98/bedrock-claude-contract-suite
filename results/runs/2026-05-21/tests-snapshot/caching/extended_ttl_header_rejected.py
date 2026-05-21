"""Bedrock-specific contract: the extended-cache-ttl beta flag is rejected.

The 1h cache feature itself works on Bedrock (see test_ttl_1h.py), but the
opt-in beta header `extended-cache-ttl-2025-04-11` is rejected as
"invalid beta flag". This test pins that contract so a future Bedrock release
that flips the header to accepted is detected.
"""
from anthropic import BadRequestError

NAME = "extended_ttl_beta_header_rejected_on_bedrock"
DESCRIPTION = "anthropic-beta: extended-cache-ttl-2025-04-11 is rejected on Bedrock"


def run(client, model) -> dict:
    try:
        client.messages.create(
            model=model,
            max_tokens=8,
            messages=[{"role": "user", "content": "hi"}],
            extra_headers={"anthropic-beta": "extended-cache-ttl-2025-04-11"},
        )
    except BadRequestError as e:
        msg = (e.message or "").lower()
        return {
            "ok": "invalid beta flag" in msg,
            "info": {"contract": "rejected", "message": e.message[:160]},
        }
    return {
        "ok": True,
        "info": {"contract": "accepted",
                 "note": "beta header now accepted — update README findings"},
    }
