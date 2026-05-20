#!/usr/bin/env python3
"""Re-run specific (provider, alias) cells and splice into results/matrix.json.

Use this when a subset of cells was tainted (rate-limit, overload, network)
and you want to refresh only those without rerunning the entire matrix.

Why a focused rerun script (instead of just `run_all.py`):
  - Preserves the clean cells in matrix.json verbatim (no risk of regressing
    a passing baseline because the second run is also flaky).
  - Adds inter-probe pacing for rate-limited providers — important on Tier 1
    CPaws workspaces where the matrix's natural cadence exceeds 30k ITPM.
  - Re-renders matrix.md from the merged matrix.json so the snapshot reflects
    the latest state without manual surgery.

Usage:
  python3 scripts/rerun_cells.py --cell cpaws:sonnet-4-6 cpaws:haiku-4-5
  python3 scripts/rerun_cells.py --cell cpaws:sonnet-4-6 --pacing-delay 6
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Import runner machinery — these names are stable in run_all.py.
from run_all import (  # noqa: E402
    TokenAccumulator,
    _render_matrix_markdown,
    _run_one_model,
    discover,
    wrap_client_with_tracker,
)
from providers import make_client, resolve_model  # noqa: E402


def _parse_cells(raw: list[str]) -> list[tuple[str, str]]:
    """Parse 'provider:alias' tokens into pairs."""
    out: list[tuple[str, str]] = []
    for tok in raw:
        if ":" not in tok:
            raise SystemExit(f"--cell must be 'provider:alias', got {tok!r}")
        provider, alias = tok.split(":", 1)
        out.append((provider.strip(), alias.strip()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Re-run cells and splice into matrix.json")
    ap.add_argument("--cell", nargs="+", required=True,
                    help="Cells to refresh, formatted 'provider:alias'. "
                         "Example: --cell cpaws:sonnet-4-6 cpaws:haiku-4-5")
    ap.add_argument("--pacing-delay", type=float, default=0.0,
                    help="Seconds to sleep between probes (rate-limit pacing).")
    ap.add_argument("--matrix-json", type=str,
                    default=str(ROOT / "results" / "matrix.json"),
                    help="Path to matrix.json. Created/updated.")
    args = ap.parse_args()

    matrix_path = pathlib.Path(args.matrix_json)
    if matrix_path.exists():
        matrix = json.loads(matrix_path.read_text())
    else:
        matrix = {}

    cells = _parse_cells(args.cell)
    started_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    pacing = args.pacing_delay
    if pacing > 0:
        # Monkeypatch _run_one_model's per-test loop to sleep before each call.
        # _run_one_model uses execute(...) which calls mod.run inside; the
        # simplest pacing knob is to wrap the runner's loop. We do it here
        # by patching execute to sleep first.
        import tests._base as base
        original_execute = base.execute

        def paced_execute(name, description, fn):
            time.sleep(pacing)
            return original_execute(name, description, fn)

        base.execute = paced_execute  # the runner imports execute from tests._base
        import run_all as _ra
        _ra.execute = paced_execute   # the runner imports it at module level too

    fake_args = argparse.Namespace(only=None, only_tests=None)

    for provider, alias in cells:
        model_id = resolve_model(provider, alias)
        print(f"\n{'═' * 72}")
        print(f"RERUN: provider={provider} alias={alias} model_id={model_id} "
              f"pacing={pacing}s")
        print('═' * 72)

        client = make_client(provider)
        tokens = TokenAccumulator()
        wrap_client_with_tracker(client, tokens)

        payload = _run_one_model(client, model_id, fake_args, started_utc)
        if payload is None:
            print(f"WARN: empty payload for {provider}:{alias}, skipping")
            continue
        payload["provider"] = provider
        payload["alias"] = alias

        matrix.setdefault(provider, {})[alias] = payload
        passed = payload["totals"]["passed"]
        total = payload["totals"]["total"]
        print(f"\n  → spliced {provider}:{alias} = {passed}/{total} into matrix")

        # Save incrementally: a Ctrl-C between cells (or a long-running cell
        # that never completes) must not throw away the cells already done.
        matrix_path.write_text(json.dumps(matrix, default=str, indent=2))
        md_path = matrix_path.with_suffix(".md")
        md_path.write_text(_render_matrix_markdown(matrix))
        print(f"    persisted to {matrix_path.name} and {md_path.name}")

    md_path = matrix_path.with_suffix(".md")

    print(f"\nMatrix updated:")
    print(f"  {matrix_path}")
    print(f"  {md_path}")
    print()
    print("Per-cell totals:")
    for provider, by_alias in matrix.items():
        for alias, payload in by_alias.items():
            t = payload["totals"]
            print(f"  {provider:10s} {alias:12s} {t['passed']:>3}/{t['total']:>3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
