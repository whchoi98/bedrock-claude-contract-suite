"""Tool search built-in tool — rejected on Bedrock Invoke API for all 3 models.

Docs list `Tool search` as GA on Bedrock generally, but `bedrock-runtime`
rejects the `tool_search_tool_20250706` spec on Opus 4.7 / Opus 4.6 /
Sonnet 4.6. See `tests/_base.is_unsupported_tool_rejection` for the
patterns we accept as valid rejection signals.
"""
from anthropic import BadRequestError

from tests._base import is_unsupported_tool_rejection

NAME = "tool_search_tool_rejected_on_opus_4_7"
DESCRIPTION = (
    "tools=[{type:tool_search_tool_20250706}] rejected on Bedrock Invoke "
    "API for Opus 4.7 / Opus 4.6 / Sonnet 4.6"
)


def run(client, model) -> dict:
    try:
        client.messages.create(
            model=model,
            max_tokens=64,
            tools=[{"type": "tool_search_tool_20250706", "name": "tool_search"}],
            messages=[{"role": "user", "content": "hi"}],
        )
    except BadRequestError as e:
        msg = e.message or ""
        rejected = is_unsupported_tool_rejection(msg, "tool_search_tool_20250706")
        return {
            "ok": rejected,
            "info": {"contract": "rejected", "message": msg[:200]},
            "error": None if rejected else (
                "rejected with unexpected error message — review and update "
                "is_unsupported_tool_rejection() if Bedrock changed the format."
            ),
        }
    return {"ok": False, "info": {"contract": "accepted_unexpectedly"},
            "error": "tool_search accepted unexpectedly"}
