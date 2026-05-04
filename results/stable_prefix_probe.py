"""Companion probe: same as variability_probe.py BUT with NO salt.

Purpose: demonstrate that without cold-start isolation, run-to-run results
DO vary because cache state persists across invocations and across separate
process runs. This is the source of the historic "every verification gives
different results" observation.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from client import make_client
from config import MODEL_ID
from tests._base import usage_breakdown

TRIALS = 5
OUT = pathlib.Path(__file__).resolve().parent / "stable_prefix_probe.json"

STABLE_PREFIX = "Detailed instructions follow. " * 1500 + "Reply OK."


def trial(client, model: str, idx: int) -> dict:
    sys_blocks = [
        {
            "type": "text",
            "text": STABLE_PREFIX,
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }
    ]
    msg = [{"role": "user", "content": "reply OK"}]

    t0 = time.perf_counter()
    r1 = client.messages.create(model=model, max_tokens=8, system=sys_blocks, messages=msg)
    t1 = time.perf_counter()
    r2 = client.messages.create(model=model, max_tokens=8, system=sys_blocks, messages=msg)
    t2 = time.perf_counter()

    return {"trial": idx, "first_elapsed_s": round(t1-t0,2),
            "second_elapsed_s": round(t2-t1,2),
            "first": usage_breakdown(r1.usage),
            "second": usage_breakdown(r2.usage)}


def main() -> int:
    client = make_client()
    print(f"Stable-prefix probe: {TRIALS} trials against {MODEL_ID}")
    print("(no salt — same prefix as previous runs in this codebase)")
    results = []
    for i in range(1, TRIALS + 1):
        r = trial(client, MODEL_ID, i)
        results.append(r)
        u1, u2 = r["first"], r["second"]
        print(f"  trial {i}: first(create={u1['create_total']}, "
              f"create_1h={u1['create_1h']}, create_5m={u1['create_5m']}, "
              f"read={u1['read_total']})  "
              f"second(read={u2['read_total']})")

    OUT.write_text(json.dumps({"model": MODEL_ID, "trials": TRIALS,
                               "results": results}, indent=2))
    print(f"\nSaved → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
