"""Server-Sent Events streaming via messages.stream()."""
NAME = "streaming"
DESCRIPTION = "messages.stream() yields incremental text deltas"


def run(client, model) -> dict:
    chunks: list[str] = []
    events_seen: set[str] = set()
    with client.messages.stream(
        model=model,
        max_tokens=64,
        messages=[{"role": "user", "content": "Count from 1 to 5, comma-separated."}],
    ) as stream:
        for event in stream:
            events_seen.add(type(event).__name__)
            if hasattr(event, "delta") and hasattr(event.delta, "text"):
                chunks.append(event.delta.text)
        final = stream.get_final_message()

    full = "".join(chunks)
    return {
        "ok": len(chunks) > 1 and final.stop_reason == "end_turn",
        "info": {
            "delta_count": len(chunks),
            "event_kinds": sorted(events_seen),
            "stop_reason": final.stop_reason,
            "preview": full[:80],
        },
    }
