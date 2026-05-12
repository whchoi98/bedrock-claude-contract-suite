"""Probe what structured-outputs request shapes Bedrock actually accepts.

Five variants per model, run in parallel:
  V1. response_format  (OpenAI-style, not in Anthropic schema)
  V2. output_config.format  (current Anthropic GA parameter)
  V3a. output_format (legacy) without beta header
  V3b. output_format (legacy) + structured-outputs-2025-11-13 beta header
  V4. tools[].strict = true (strict tool use, separate from JSON output)

Captures the raw 4xx body so the actual rejection reason is visible.
"""
from __future__ import annotations

import json
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from anthropic import APIStatusError, BadRequestError

from client import make_client
from config import ALL_MODELS, REGION
from providers import resolve_model
from tests._base import text_of
from tests.messages.test_structured_outputs import SCHEMA

PROMPT = [{"role": "user", "content": "Reply with the city Seoul as JSON."}]


def _try_call(client, model: str, **kwargs) -> tuple[bool, str, dict]:
    try:
        r = client.messages.create(model=model, max_tokens=64, messages=PROMPT, **kwargs)
        return True, "accepted: " + text_of(r)[:200].replace("\n", " "), {
            "stop_reason": r.stop_reason,
            "input_tokens": r.usage.input_tokens,
            "output_tokens": r.usage.output_tokens,
        }
    except BadRequestError as e:
        return False, f"400: {e.message[:280] if e.message else str(e)[:280]}", {}
    except APIStatusError as e:
        return False, f"{e.status_code}: {(e.message or str(e))[:280]}", {}


def _result(label: str, accepted: bool, detail: str, extra: dict) -> dict:
    return {"variant": label, "accepted": accepted, "detail": detail[:300], **extra}


VARIANTS: list[tuple[str, dict]] = [
    ("V1 response_format(json_object)",
     {"extra_body": {"response_format": {"type": "json_object"}}}),
    ("V2 output_config.format(json_schema)",
     {"extra_body": {"output_config": {"format": {"type": "json_schema", "schema": SCHEMA}}}}),
    ("V3a output_format (no beta header)",
     {"extra_body": {"output_format": {"type": "json_schema", "schema": SCHEMA}}}),
    ("V3b output_format + beta header",
     {"extra_body": {"output_format": {"type": "json_schema", "schema": SCHEMA}},
      "extra_headers": {"anthropic-beta": "structured-outputs-2025-11-13"}}),
    ("V4 strict tool use",
     {"tools": [{"name": "report_city", "description": "Report a city as JSON",
                  "strict": True, "input_schema": SCHEMA}],
      "tool_choice": {"type": "tool", "name": "report_city"}}),
]


def probe_model(client, model: str) -> list[dict]:
    with ThreadPoolExecutor(max_workers=len(VARIANTS)) as ex:
        futures = {label: ex.submit(_try_call, client, model, **kwargs)
                   for label, kwargs in VARIANTS}
        return [_result(label, *futures[label].result()) for label, _ in VARIANTS]


def main() -> int:
    client = make_client()
    payload: dict = {"region": REGION, "by_model": {}}
    for alias in ALL_MODELS:
        model_id = resolve_model("bedrock", alias)
        print(f"\n=== {alias} ===")
        results = probe_model(client, model_id)
        payload["by_model"][alias] = results
        for r in results:
            mark = "OK " if r["accepted"] else "RJ "
            print(f"  {mark} {r['variant']:<40s} {r['detail'][:130]}")

    out_path = pathlib.Path(__file__).resolve().parent.parent / "results" / "structured_outputs_probe.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str))
    print(f"\nSaved → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
