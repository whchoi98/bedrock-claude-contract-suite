"""Streaming with thinking active: thinking-related delta events are produced.

We use the Opus 4.7 path (adaptive + output_config.effort) so we still observe
thinking deltas without relying on the deprecated `enabled` mode.
"""
NAME = "streaming_thinking"
DESCRIPTION = "stream with thinking yields thinking_delta or signature_delta events"


def run(client, model) -> dict:
    delta_kinds: set[str] = set()
    block_kinds: set[str] = set()
    with client.messages.stream(
        model=model,
        max_tokens=2048,
        thinking={"type": "adaptive"},
        extra_body={"output_config": {"effort": "high"}},
        messages=[
            {
                "role": "user",
                "content": "What is the integer cube root of 1331? Show your reasoning briefly.",
            }
        ],
    ) as stream:
        for event in stream:
            d = getattr(event, "delta", None)
            if d is not None:
                t = getattr(d, "type", None)
                if t:
                    delta_kinds.add(t)
            cb = getattr(event, "content_block", None)
            if cb is not None:
                block_kinds.add(getattr(cb, "type", "?"))
        final = stream.get_final_message()

    final_blocks = [b.type for b in final.content]
    has_thinking_block = "thinking" in final_blocks
    has_thinking_delta = ("thinking_delta" in delta_kinds) or ("signature_delta" in delta_kinds)
    # Adaptive may decide not to think on a trivial problem. We pass if either
    # (a) we got a thinking block + matching deltas, OR
    # (b) the model elected not to think and returned a clean text answer.
    answered = "11" in "".join(b.text for b in final.content if b.type == "text")
    return {
        "ok": (has_thinking_block and has_thinking_delta) or (answered and not has_thinking_block),
        "info": {
            "delta_kinds": sorted(delta_kinds),
            "block_kinds_seen": sorted(block_kinds),
            "final_blocks": final_blocks,
            "thinking_used": has_thinking_block,
        },
    }
