"""Probe run-to-run variability of Bedrock 1h cache behavior.

Runs 5 cold-start trials of cache_ttl_1h-style probe and records:
  - whether the 1h bucket populated on the fresh write
  - whether the 5m bucket populated instead (silent demotion signal)
  - whether the second call read back the prefix
  - elapsed time per call

Output: JSON written to results/variability_probe.json so we can compare
trial-to-trial behavior.
"""
from __future__ import annotations

import json
import pathlib
import secrets
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from client import make_client
from config import MODEL_ID
from tests._base import usage_breakdown

TRIALS = 5
OUT = pathlib.Path(__file__).resolve().parent / "variability_probe.json"
_PREFIX = "Detailed instructions follow. " * 1500


def trial(client, model: str, idx: int) -> dict:
    salt = secrets.token_hex(8)
    sys_blocks = [
        {
            "type": "text",
            "text": f"Run salt {salt}. " + _PREFIX + "Reply OK.",
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }
    ]
    msg = [{"role": "user", "content": "reply OK"}]

    t0 = time.perf_counter()
    r1 = client.messages.create(model=model, max_tokens=8, system=sys_blocks, messages=msg)
    t1 = time.perf_counter()
    r2 = client.messages.create(model=model, max_tokens=8, system=sys_blocks, messages=msg)
    t2 = time.perf_counter()

    u1, u2 = usage_breakdown(r1.usage), usage_breakdown(r2.usage)
    return {
        "trial": idx,
        "salt": salt,
        "first_elapsed_s": round(t1 - t0, 2),
        "second_elapsed_s": round(t2 - t1, 2),
        "first": u1,
        "second": u2,
        "verdict": {
            "cold_start": u1["create_total"] > 0 and u1["read_total"] == 0,
            "1h_bucket_populated": u1["create_1h"] > 0,
            "5m_bucket_populated": u1["create_5m"] > 0,
            "demoted_to_5m": u1["create_5m"] > 0 and u1["create_1h"] == 0,
            "second_call_reads": u2["read_total"] > 0,
            "second_call_reads_via_1h": u2["read_total"] >= u1["create_1h"] > 0,
        },
    }


def main() -> int:
    client = make_client()
    print(f"Probing {TRIALS} trials against {MODEL_ID} ...")
    results = []
    for i in range(1, TRIALS + 1):
        print(f"  trial {i}/{TRIALS} ...", end="", flush=True)
        r = trial(client, MODEL_ID, i)
        results.append(r)
        v = r["verdict"]
        flags = []
        flags.append("cold" if v["cold_start"] else "HOT")
        flags.append("1h+" if v["1h_bucket_populated"] else "1h0")
        flags.append("5m+" if v["5m_bucket_populated"] else "5m0")
        flags.append("read" if v["second_call_reads"] else "noread")
        print(f"  [{'/'.join(flags)}] first={r['first']} second_read={r['second']['read_total']}")

    OUT.write_text(json.dumps({
        "model": MODEL_ID,
        "trials": TRIALS,
        "results": results,
    }, indent=2))
    print(f"\nSaved → {OUT}")

    # Summary table
    print("\nSummary:")
    print("trial | cold | 1h_create | 5m_create | 2nd_read | demoted")
    print("-" * 60)
    for r in results:
        v = r["verdict"]
        print(f"  {r['trial']}   |  {'Y' if v['cold_start'] else 'N'}   | "
              f"{r['first']['create_1h']:>8} | {r['first']['create_5m']:>8} | "
              f"{r['second']['read_total']:>8} |   {'Y' if v['demoted_to_5m'] else 'N'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
