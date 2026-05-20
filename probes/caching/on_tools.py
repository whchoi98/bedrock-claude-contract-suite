"""Cache breakpoint placed on the tools list (not on system)."""
NAME = "cache_on_tools"
DESCRIPTION = "cache_control attached to last tool definition triggers cache use"


def _tools() -> list[dict]:
    # Inflate descriptions so the tools block alone exceeds the cache threshold.
    big_desc = "Detailed tool documentation. " * 1500
    return [
        {
            "name": "noop_a",
            "description": big_desc + " Tool A.",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "noop_b",
            "description": big_desc + " Tool B.",
            "input_schema": {"type": "object", "properties": {}},
            "cache_control": {"type": "ephemeral"},
        },
    ]


def _u(u) -> dict:
    return {
        "input": u.input_tokens,
        "create": getattr(u, "cache_creation_input_tokens", 0),
        "read": getattr(u, "cache_read_input_tokens", 0),
    }


def run(client, model) -> dict:
    tools = _tools()
    msg = [{"role": "user", "content": "Just say hi (no tool needed)."}]
    r1 = client.messages.create(model=model, max_tokens=16, tools=tools,
                                tool_choice={"type": "none"}, messages=msg)
    r2 = client.messages.create(model=model, max_tokens=16, tools=tools,
                                tool_choice={"type": "none"}, messages=msg)
    u1, u2 = _u(r1.usage), _u(r2.usage)
    fresh = u1["create"] > 0 and u2["read"] > 0
    hot = u1["read"] > 0 and u2["read"] > 0
    return {
        "ok": fresh or hot,
        "info": {"first": u1, "second": u2,
                 "path": "fresh" if fresh else ("hot" if hot else "none")},
        "error": None if (fresh or hot) else "no cache create/read on tools breakpoint",
    }
