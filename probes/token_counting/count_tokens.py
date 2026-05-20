"""Token counting on Bedrock — dual reality.

The Anthropic build-with-claude/overview availability table marks
"Token counting" as supported on Bedrock, but the Anthropic SDK's
`messages.count_tokens()` returns "Token counting is not supported in
Bedrock yet" on every Bedrock model. The discrepancy is real but not
because docs are wrong — they refer to two different APIs:

  * Anthropic SDK call (`messages.count_tokens` → Anthropic-shape
    `/v1/messages/count_tokens` path)
    → not available on Bedrock. The SDK explicitly rejects.

  * AWS Bedrock-native CountTokens API (`/model/{id}/count-tokens`,
    requires `bedrock:CountTokens` IAM permission)
    → exists. Confirmed by hitting the path directly with our bearer
    token: returns 403 IAM auth failure, NOT 404, proving the route is
    recognized by the Bedrock service. Granting the IAM action would
    enable it.

This test pins the SDK-layer rejection contract on Bedrock so a future
Anthropic SDK release that wires `count_tokens` through the AWS-native
endpoint will flip this test from ⛔ to 🟢. The companion
`scripts/probe_token_counting.py` records the AWS-native path's
existence (separate from this contract).
"""
from anthropic import AnthropicError

NAME = "count_tokens"
DESCRIPTION = (
    "messages.count_tokens via Anthropic SDK rejected on Bedrock with "
    "'not supported in Bedrock yet'; AWS-native /model/{id}/count-tokens "
    "exists separately, see scripts/probe_token_counting.py"
)


def run(client, model) -> dict:
    try:
        out = client.messages.count_tokens(
            model=model,
            messages=[{"role": "user", "content": "How many tokens?"}],
        )
        return {
            "ok": out.input_tokens > 0,
            "info": {
                "contract": "supported",
                "input_tokens": out.input_tokens,
                "note": (
                    "Anthropic SDK count_tokens succeeded — Bedrock now "
                    "exposes the Anthropic-shape path. Update README findings."
                ),
            },
        }
    except AnthropicError as e:
        msg = str(e)
        bedrock_unsupported = "not supported in Bedrock" in msg
        return {
            "ok": bedrock_unsupported,
            "info": {
                "contract": "rejected",
                "backend": "bedrock_unsupported",
                "sdk_message": msg[:200],
                "aws_native_alternative": {
                    "path": "/model/{model_id}/count-tokens",
                    "iam_action_required": "bedrock:CountTokens",
                    "evidence": "results/token_counting_probe.json (V2 returns 403 IAM auth, not 404)",
                },
            },
            "error": None if bedrock_unsupported else msg,
        }
