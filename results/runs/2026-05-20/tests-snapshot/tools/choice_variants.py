"""tool_choice variants: any, none, auto (default)."""
NAME = "tool_choice_variants"
DESCRIPTION = "tool_choice supports any/none/auto with documented effects"

TOOLS = [
    {
        "name": "lookup",
        "description": "Look up a value.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"],
        },
    }
]


def _has_tool_use(resp) -> bool:
    return any(b.type == "tool_use" for b in resp.content)


def run(client, model) -> dict:
    msg = [{"role": "user", "content": "Look up 'alpha'."}]
    msg_no_tool = [{"role": "user", "content": "Just say hi."}]

    r_any = client.messages.create(
        model=model, max_tokens=128, tools=TOOLS,
        tool_choice={"type": "any"}, messages=msg,
    )
    r_none = client.messages.create(
        model=model, max_tokens=128, tools=TOOLS,
        tool_choice={"type": "none"}, messages=msg,
    )
    r_auto = client.messages.create(
        model=model, max_tokens=128, tools=TOOLS,
        tool_choice={"type": "auto"}, messages=msg_no_tool,
    )
    any_ok = _has_tool_use(r_any)
    none_ok = not _has_tool_use(r_none)
    auto_ok = not _has_tool_use(r_auto)
    return {
        "ok": any_ok and none_ok and auto_ok,
        "info": {
            "any_called_tool": any_ok,
            "none_avoided_tool": none_ok,
            "auto_avoided_when_not_needed": auto_ok,
        },
    }
