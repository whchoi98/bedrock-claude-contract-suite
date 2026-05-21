"""Two cache breakpoints in one request (system + user message)."""
NAME = "cache_multi_breakpoint"
DESCRIPTION = "system breakpoint AND user message breakpoint both register"


def _u(u) -> dict:
    return {
        "input": u.input_tokens,
        "create": getattr(u, "cache_creation_input_tokens", 0),
        "read": getattr(u, "cache_read_input_tokens", 0),
    }


def run(client, model) -> dict:
    sys_blocks = [
        {
            "type": "text",
            "text": "Detailed instructions. " * 1500,
            "cache_control": {"type": "ephemeral"},
        }
    ]
    msg = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Reference data. " * 1500,
                    "cache_control": {"type": "ephemeral"},
                },
                {"type": "text", "text": "Reply 'multi-cache-ok'."},
            ],
        }
    ]
    r1 = client.messages.create(model=model, max_tokens=16, system=sys_blocks, messages=msg)
    r2 = client.messages.create(model=model, max_tokens=16, system=sys_blocks, messages=msg)
    u1, u2 = _u(r1.usage), _u(r2.usage)
    fresh = u1["create"] > 0 and u2["read"] > 0
    hot = u1["read"] > 0 and u2["read"] > 0
    return {
        "ok": fresh or hot,
        "info": {"first": u1, "second": u2,
                 "path": "fresh" if fresh else ("hot" if hot else "none")},
        "error": None if (fresh or hot) else "no cache read on multi-breakpoint",
    }
