"""Built-in client-side bash tool: model emits tool_use of type bash."""
NAME = "builtin_bash_tool"
DESCRIPTION = "tools=[{type:bash_20250124}] is accepted; model uses it for shell-style requests"


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=512,
        tools=[{"type": "bash_20250124", "name": "bash"}],
        messages=[{"role": "user", "content": "List files in /tmp using bash."}],
    )
    tu = [b for b in resp.content if b.type == "tool_use"]
    used_bash = bool(tu) and tu[0].name == "bash"
    return {
        "ok": used_bash and resp.stop_reason == "tool_use",
        "info": {
            "tool_called": tu[0].name if tu else None,
            "tool_input": dict(tu[0].input) if tu else None,
            "stop_reason": resp.stop_reason,
        },
    }
