"""Cache breakpoint placed on a user message block."""
NAME = "cache_on_messages"
DESCRIPTION = "cache_control on a user content block triggers cache create/read"


def _u(u) -> dict:
    return {
        "input": u.input_tokens,
        "create": getattr(u, "cache_creation_input_tokens", 0),
        "read": getattr(u, "cache_read_input_tokens", 0),
    }


def run(client, model) -> dict:
    big_doc = "Reference material. " * 2000  # ~10K tokens
    user_blocks = [
        {"type": "text", "text": big_doc, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": "Reply with 'MSG_CACHE_OK'."},
    ]
    messages = [{"role": "user", "content": user_blocks}]
    r1 = client.messages.create(model=model, max_tokens=16, messages=messages)
    r2 = client.messages.create(model=model, max_tokens=16, messages=messages)
    u1, u2 = _u(r1.usage), _u(r2.usage)
    fresh = u1["create"] > 0 and u2["read"] > 0
    hot = u1["read"] > 0 and u2["read"] > 0
    return {
        "ok": fresh or hot,
        "info": {"first": u1, "second": u2,
                 "path": "fresh" if fresh else ("hot" if hot else "none")},
        "error": None if (fresh or hot) else "no cache create/read on message breakpoint",
    }
