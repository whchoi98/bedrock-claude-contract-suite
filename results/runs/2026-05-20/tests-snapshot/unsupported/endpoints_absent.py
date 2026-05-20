"""Anthropic-direct features that Bedrock does not host: confirm they fail cleanly.

Test passes if the Bedrock client either lacks the surface or returns a clearly
unsupported error. This documents the boundary so a future Bedrock release can
flip these to expected-PASS by updating this test.
"""
NAME = "bedrock_unsupported"
DESCRIPTION = "Files / Batches / Models endpoints absent or refused on Bedrock"


def _absent_or_errors(client, dotted_path: str) -> tuple[bool, str]:
    obj = client
    for part in dotted_path.split("."):
        obj = getattr(obj, part, None)
        if obj is None:
            return True, "attribute_absent"
    # The attribute exists; try to call list() to see if Bedrock rejects it.
    try:
        obj.list() if hasattr(obj, "list") else obj.retrieve("nonexistent")
    except Exception as e:  # noqa: BLE001
        return True, type(e).__name__
    return False, "succeeded_unexpectedly"


def run(client, model) -> dict:
    results = {}
    for path in ("files", "batches", "messages.batches", "models"):
        absent, detail = _absent_or_errors(client, path)
        results[path] = {"absent_or_error": absent, "detail": detail}
    all_unsupported = all(r["absent_or_error"] for r in results.values())
    return {
        "ok": all_unsupported,
        "info": results,
    }
