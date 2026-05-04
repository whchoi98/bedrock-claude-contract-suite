"""Built-in memory tool (`memory_20250818`) — model-divergent on Bedrock.

Opus 4.7 / Opus 4.6 accept; the model emits a memory tool_use block.
Sonnet 4.6 rejects: the schema for that model does not list
`memory_20250818` among its accepted tool types.
"""
from anthropic import BadRequestError

from tests._base import is_unsupported_tool_rejection

NAME = "builtin_memory_tool"
DESCRIPTION = (
    "tools=[{type:memory_20250818}] — accepted on Opus 4.6/4.7, rejected "
    "on Sonnet 4.6 (not in expected-tags schema)"
)

TOOL = {"type": "memory_20250818", "name": "memory"}


def run(client, model) -> dict:
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=512,
            tools=[TOOL],
            messages=[
                {"role": "user", "content":
                    "Remember that my favorite color is blue. Use the memory tool."}
            ],
        )
    except BadRequestError as e:
        msg = e.message or ""
        if is_unsupported_tool_rejection(msg, "memory_20250818"):
            return {
                "ok": True,
                "info": {
                    "contract": "rejected",
                    "message": msg[:200],
                    "note": (
                        "This Bedrock model+endpoint does not list "
                        "memory_20250818 in its accepted tool-type schema."
                    ),
                },
            }
        return {
            "ok": False,
            "info": {"contract": "rejected_unexpected", "message": msg[:200]},
            "error": (
                "rejected with unexpected error message — review and update "
                "is_unsupported_tool_rejection() if Bedrock changed the format."
            ),
        }

    tu = [b for b in resp.content if b.type == "tool_use"]
    return {
        "ok": (
            bool(tu)
            and tu[0].name == "memory"
            and resp.stop_reason in ("tool_use", "end_turn", "max_tokens")
        ),
        "info": {
            "contract": "supported",
            "tool_called": tu[0].name if tu else None,
            "tool_input_keys": list(tu[0].input.keys()) if tu else [],
            "stop_reason": resp.stop_reason,
        },
    }
