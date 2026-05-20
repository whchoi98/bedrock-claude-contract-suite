"""Built-in text_editor tool (version 20250728 — older versions rejected)."""
NAME = "builtin_text_editor_tool"
DESCRIPTION = "tools=[{type:text_editor_20250728}] accepted; model emits the tool"

TOOL = {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"}


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=512,
        tools=[TOOL],
        messages=[
            {"role": "user", "content":
                "Open the file /tmp/notes.txt and read its first 5 lines."}
        ],
    )
    tu = [b for b in resp.content if b.type == "tool_use"]
    return {
        "ok": bool(tu) and resp.stop_reason in ("tool_use", "end_turn"),
        "info": {
            "tool_called": tu[0].name if tu else None,
            "stop_reason": resp.stop_reason,
        },
    }
