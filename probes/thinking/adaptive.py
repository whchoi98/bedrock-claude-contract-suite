"""Extended thinking: adaptive mode + output_config.effort (Opus 4.7 signature).

The response is correct under thinking — we don't require a thinking block to
appear because adaptive mode lets the model decide. We DO verify that the API
accepts the new signature and that the answer is correct.
"""
NAME = "extended_thinking"
DESCRIPTION = "thinking.type=adaptive + output_config.effort accepted; correct answer"


def run(client, model) -> dict:
    resp = client.messages.create(
        model=model,
        max_tokens=2048,
        thinking={"type": "adaptive"},
        extra_body={"output_config": {"effort": "medium"}},
        messages=[
            {
                "role": "user",
                "content": "Compute 137 * 219. Reply with just the integer.",
            }
        ],
    )
    block_kinds = [b.type for b in resp.content]
    answer = "".join(b.text for b in resp.content if b.type == "text")
    return {
        "ok": "30003" in answer,
        "info": {
            "blocks": block_kinds,
            "thinking_block_present": "thinking" in block_kinds,
            "answer_preview": answer[:60],
            "stop_reason": resp.stop_reason,
        },
    }
