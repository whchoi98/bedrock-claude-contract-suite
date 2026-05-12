"""Server tools (web_search, web_fetch, code_execution) are Anthropic-direct only.

On Bedrock, declaring a server-side tool type should produce a clear rejection.
This pins the boundary so a future Bedrock release that hosts server tools is
detected immediately. On Claude Platform on AWS the same declarations are
accepted, which makes them a primary cross-provider divergence point.
"""
from anthropic import BadRequestError

NAME = "server_tools_rejected"
DESCRIPTION = "server tool types (web_search, web_fetch, code_execution) rejected on Bedrock"


def _try(client, model, tool_def) -> tuple[bool, str]:
    try:
        client.messages.create(
            model=model,
            max_tokens=64,
            tools=[tool_def],
            messages=[{"role": "user", "content": "Use the tool if needed."}],
        )
        return False, "accepted_unexpectedly"
    except BadRequestError as e:
        return True, (e.message or "")[:160]
    except Exception as e:  # noqa: BLE001
        return True, f"{type(e).__name__}: {e}"[:160]


def run(client, model) -> dict:
    tools = {
        "web_search":     {"type": "web_search_20250305",     "name": "web_search"},
        "web_fetch":      {"type": "web_fetch_20250910",      "name": "web_fetch"},
        "code_execution": {"type": "code_execution_20250825", "name": "code_execution"},
    }
    results = {name: _try(client, model, td) for name, td in tools.items()}
    rejected = {n: r[0] for n, r in results.items()}
    return {
        "ok": all(rejected.values()),
        "info": {n: {"rejected": r[0], "detail": r[1]} for n, r in results.items()},
    }
