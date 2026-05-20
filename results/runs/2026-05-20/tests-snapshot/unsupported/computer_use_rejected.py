"""Computer use tool — rejected on Bedrock Invoke API for all 3 measured models.

Docs list `Computer use` as `bedrockBeta`, but `bedrock-runtime` rejects
the `computer_20250124` spec on Opus 4.7 / Opus 4.6 / Sonnet 4.6 — either
with the older "not supported" wording or the current SDK schema-validation
"Input tag ... does not match any of the expected tags". Either form is a
valid rejection signal. See `tests/_base.is_unsupported_tool_rejection`.
"""
from anthropic import BadRequestError

from probes._base import is_unsupported_tool_rejection

NAME = "computer_use_tool_rejected_on_opus_4_7"
DESCRIPTION = (
    "tools=[{type:computer_20250124}] rejected on Bedrock Invoke API for "
    "Opus 4.7 / Opus 4.6 / Sonnet 4.6"
)


def run(client, model) -> dict:
    tool = {
        "type": "computer_20250124",
        "name": "computer",
        "display_width_px": 1024,
        "display_height_px": 768,
    }
    try:
        client.messages.create(
            model=model,
            max_tokens=64,
            tools=[tool],
            messages=[{"role": "user", "content": "Take a screenshot."}],
        )
    except BadRequestError as e:
        msg = e.message or ""
        rejected = is_unsupported_tool_rejection(msg, "computer_20250124")
        return {
            "ok": rejected,
            "info": {"contract": "rejected", "message": msg[:200]},
            "error": None if rejected else (
                "rejected with unexpected error message — review and update "
                "is_unsupported_tool_rejection() if Bedrock changed the format."
            ),
        }
    return {"ok": False, "info": {"contract": "accepted_unexpectedly"},
            "error": "computer use accepted unexpectedly"}
