"""Structured Outputs (`output_config.format`) — model-divergent on Bedrock.

Opus 4.6 / Sonnet 4.6 (Invoke API) → accepted; returns schema-conformant JSON.
Opus 4.7 (Invoke API) → rejected with
`output_config.format: Extra inputs are not permitted` (docs direct
Opus 4.7 users to the Mantle endpoint, which is out of scope here —
see `results/docs_vs_reality.md`).
"""
import json

from anthropic import BadRequestError

from probes._base import text_of

NAME = "structured_outputs"
DESCRIPTION = (
    "output_config.format=json_schema accepted on supported models; "
    "rejected on Opus 4.7 via Invoke API (Mantle required)"
)

SCHEMA = {
    "type": "object",
    "properties": {"city": {"type": "string"}},
    "required": ["city"],
    "additionalProperties": False,
}


def run(client, model) -> dict:
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=64,
            messages=[
                {"role": "user", "content": "Reply with the city Seoul as JSON only."}
            ],
            extra_body={
                "output_config": {
                    "format": {"type": "json_schema", "schema": SCHEMA}
                }
            },
        )
    except BadRequestError as e:
        msg = (e.message or "")[:280]
        rejected = "output_config.format" in msg and "extra inputs" in msg.lower()
        return {
            "ok": rejected,
            "info": {
                "contract": "rejected_on_invoke_for_this_model",
                "message": msg,
                "note": (
                    "Mantle (`bedrock-mantle.{region}.api.aws`) is the "
                    "docs-recommended fallback for Opus 4.7 but is out of "
                    "scope for this suite — see results/docs_vs_reality.md."
                ),
            },
        }

    text = text_of(resp)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "info": {"contract": "supported_but_invalid_json", "raw": text[:200]},
            "error": "API accepted output_config.format but response was not valid JSON.",
        }
    schema_conformant = isinstance(parsed, dict) and parsed.get("city") == "Seoul"
    return {
        "ok": schema_conformant,
        "info": {
            "contract": "supported",
            "parsed": parsed,
            "stop_reason": resp.stop_reason,
        },
        "error": None if schema_conformant else (
            f"API accepted output_config.format but JSON did not satisfy schema: {parsed!r}"
        ),
    }
