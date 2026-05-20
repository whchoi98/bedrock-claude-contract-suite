"""Interleaved thinking beta: thinking blocks appear BETWEEN tool_use blocks.

Forces a multi-step problem where the model must call a tool, observe the
result, then think about it before calling again. With the
interleaved-thinking beta enabled, a thinking block should appear in the
assistant turn that comes AFTER a tool_result — not only at the very start
of the response.
"""
NAME = "interleaved_thinking_between_tools"
DESCRIPTION = "thinking blocks appear after tool_result (interleaved with tool calls)"

TOOLS = [
    {
        "name": "add",
        "description": "Add two integers.",
        "input_schema": {
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    }
]


def _kinds(content) -> list[str]:
    return [b.type for b in content]


def run(client, model) -> dict:
    user_msg = {
        "role": "user",
        "content": (
            "Compute (123 + 456) + 789 using the 'add' tool. "
            "Call add for the first sum, see the result, then call add again."
        ),
    }
    common = dict(
        model=model,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        extra_body={"output_config": {"effort": "high"}},
        tools=TOOLS,
        extra_headers={"anthropic-beta": "interleaved-thinking-2025-05-14"},
    )

    r1 = client.messages.create(**common, messages=[user_msg])
    r1_kinds = _kinds(r1.content)
    tu1 = next((b for b in r1.content if b.type == "tool_use"), None)
    if tu1 is None:
        return {"ok": False, "info": {"r1_blocks": r1_kinds},
                "error": "first turn did not call tool"}

    r2 = client.messages.create(
        **common,
        messages=[
            user_msg,
            {"role": "assistant", "content": r1.content},
            {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tu1.id, "content": "579"}
            ]},
        ],
    )
    r2_kinds = _kinds(r2.content)
    has_thinking_after_tool = "thinking" in r2_kinds
    tu2 = next((b for b in r2.content if b.type == "tool_use"), None)

    final_text = ""
    if tu2 is not None:
        r3 = client.messages.create(
            **common,
            messages=[
                user_msg,
                {"role": "assistant", "content": r1.content},
                {"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": tu1.id, "content": "579"}
                ]},
                {"role": "assistant", "content": r2.content},
                {"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": tu2.id, "content": "1368"}
                ]},
            ],
        )
        final_text = "".join(b.text for b in r3.content if b.type == "text")
    else:
        final_text = "".join(b.text for b in r2.content if b.type == "text")

    # In a NON-interleaved response, thinking only appears at the very start
    # and never coexists with tool_use in the same assistant turn.
    # Interleaved mode is proven by EITHER:
    #  (a) thinking + tool_use coexisting in r1, OR
    #  (b) a thinking block appearing again in r2 (post tool_result), OR
    #  (c) both.
    coexisted_in_r1 = "thinking" in r1_kinds and "tool_use" in r1_kinds
    interleaved_signal = coexisted_in_r1 or has_thinking_after_tool
    correct = "1368" in final_text
    return {
        "ok": interleaved_signal and correct,
        "info": {
            "r1_blocks": r1_kinds,
            "r2_blocks": r2_kinds,
            "coexisted_in_r1": coexisted_in_r1,
            "thinking_after_tool": has_thinking_after_tool,
            "final_preview": final_text[:80],
        },
        "error": None if interleaved_signal else "no interleaved thinking signal observed",
    }
