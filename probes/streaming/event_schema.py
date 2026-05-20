"""Streaming event schema: required event types appear at least once."""
NAME = "event_schema"
DESCRIPTION = "stream emits message_start, content_block_start/stop, message_stop"


def run(client, model) -> dict:
    types_seen: list[str] = []
    with client.messages.stream(
        model=model,
        max_tokens=32,
        messages=[{"role": "user", "content": "Hello."}],
    ) as stream:
        for event in stream:
            t = getattr(event, "type", None)
            if t:
                types_seen.append(t)
        stream.get_final_message()

    required = {"message_start", "content_block_start", "content_block_stop", "message_stop"}
    missing = required - set(types_seen)
    return {
        "ok": not missing,
        "info": {"types": sorted(set(types_seen)), "missing": sorted(missing)},
        "error": f"missing event types: {sorted(missing)}" if missing else None,
    }
