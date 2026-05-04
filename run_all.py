"""Discover tests/<category>/test_*.py and run by category.

Usage:
    AWS_BEARER_TOKEN_BEDROCK="..." python run_all.py
    AWS_BEARER_TOKEN_BEDROCK="..." python run_all.py --only messages tools
    AWS_BEARER_TOKEN_BEDROCK="..." python run_all.py --json
    AWS_BEARER_TOKEN_BEDROCK="..." python run_all.py --no-save  # skip writing results/

Results are written to results/ by default:
    results/latest.json      machine-readable summary
    results/latest.md        human-readable Markdown report
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib
import json
import pathlib
import sys
import time
from collections import defaultdict

from client import make_client
from config import ALL_MODELS, MODEL_ID, REGION
from tests._base import Result, execute, usage_breakdown

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
TESTS_ROOT = PROJECT_ROOT / "tests"
RESULTS_DIR = PROJECT_ROOT / "results"


class TokenAccumulator:
    """Record per-call usage from every messages.create response."""

    def __init__(self) -> None:
        self.calls = 0
        self.input = 0
        self.output = 0
        self.cache_create_total = 0
        self.cache_create_5m = 0
        self.cache_create_1h = 0
        self.cache_read = 0

    def record(self, response) -> None:
        u = getattr(response, "usage", None)
        if u is None:
            return
        b = usage_breakdown(u)
        self.calls += 1
        self.input += b["input"] or 0
        self.output += getattr(u, "output_tokens", 0) or 0
        self.cache_create_total += b["create_total"] or 0
        self.cache_create_5m += b["create_5m"] or 0
        self.cache_create_1h += b["create_1h"] or 0
        self.cache_read += b["read_total"] or 0

    def summary(self) -> dict:
        return {
            "calls": self.calls,
            "input_tokens": self.input,
            "output_tokens": self.output,
            "cache_creation_input_tokens": self.cache_create_total,
            "ephemeral_5m_input_tokens": self.cache_create_5m,
            "ephemeral_1h_input_tokens": self.cache_create_1h,
            "cache_read_input_tokens": self.cache_read,
            "total_billable_input": (
                self.input + self.cache_create_total + self.cache_read
            ),
        }


def wrap_client_with_tracker(client, accumulator: TokenAccumulator):
    """Monkey-patch client.messages.create to record usage on every response."""
    original_create = client.messages.create

    def tracked_create(*args, **kwargs):
        resp = original_create(*args, **kwargs)
        accumulator.record(resp)
        return resp

    client.messages.create = tracked_create
    return client


def discover() -> dict[str, list]:
    """Return {category_name: [module, ...]} for every tests/<cat>/test_*.py."""
    by_cat: dict[str, list] = defaultdict(list)
    for cat_dir in sorted(p for p in TESTS_ROOT.iterdir() if p.is_dir() and not p.name.startswith("_") and p.name != "__pycache__"):
        for path in sorted(cat_dir.glob("test_*.py")):
            mod_name = f"tests.{cat_dir.name}.{path.stem}"
            try:
                by_cat[cat_dir.name].append(importlib.import_module(mod_name))
            except Exception as e:  # noqa: BLE001
                print(f"WARN: could not import {mod_name}: {e}", file=sys.stderr)
    return by_cat


def _classify(t: dict) -> tuple[str, str]:
    """Return (kind, status_label) for a test result.

    kind ∈ {"behavioral", "rejected", "mixed", "fail"}
        behavioral — the feature works on Bedrock and we verified the response.
        rejected   — the feature is explicitly NOT supported on Bedrock; the
                     test passes because the API correctly refuses it.
        mixed      — partial support (e.g. header accepted, config rejected).
        fail       — actual failure.
    """
    if not t["ok"]:
        return "fail", "❌ FAIL"
    info = t.get("info") or {}
    name = t.get("name", "")

    contract = info.get("contract")
    if isinstance(contract, str) and "reject" in contract.lower():
        return "rejected", "⛔ REJECTED (contract)"
    if "deprecation_signals" in info:
        return "rejected", "⛔ REJECTED (contract)"
    if info.get("config_rejected_on_bedrock") is True and info.get("header_accepted") is True:
        return "mixed", "🟡 MIXED (partial)"
    if info.get("backend") == "bedrock_unsupported":
        return "rejected", "⛔ REJECTED (contract)"
    if "rejected" in name or "deprecated" in name or "absent" in name:
        return "rejected", "⛔ REJECTED (contract)"
    if name == "bedrock_unsupported":
        return "rejected", "⛔ REJECTED (contract)"
    return "behavioral", "🟢 SUPPORTED (behavior verified)"


def _render_markdown(payload: dict) -> str:
    """Render the results payload as a Markdown report."""
    lines: list[str] = []
    totals = payload["totals"]
    lines.append("# Bedrock × Anthropic Messages API verification")
    lines.append("")
    lines.append(f"- **Started (UTC)**: {payload['started_utc']}")
    lines.append(f"- **Region**: `{payload['region']}`")
    lines.append(f"- **Model**: `{payload['model']}`")
    lines.append(f"- **Result**: **{totals['passed']} / {totals['total']} passed**")
    lines.append("")

    # Classify every test so we can show kind-aware totals.
    flat_tests: list[tuple[str, dict, str]] = []
    for cat, c in payload["categories"].items():
        for t in c["tests"]:
            kind, _ = _classify(t)
            flat_tests.append((cat, t, kind))

    counts = {"behavioral": 0, "rejected": 0, "mixed": 0, "fail": 0}
    for _, _, k in flat_tests:
        counts[k] += 1

    lines.append("## Result legend")
    lines.append("")
    lines.append("| Icon | Meaning | Count |")
    lines.append("| --- | --- | ---: |")
    lines.append(f"| 🟢 | **Supported** — feature works on Bedrock; behavior verified | {counts['behavioral']} |")
    lines.append(f"| ⛔ | **Rejected (contract)** — feature is NOT supported on Bedrock; rejection verified | {counts['rejected']} |")
    lines.append(f"| 🟡 | **Mixed** — partial support (e.g. header accepted, config rejected) | {counts['mixed']} |")
    lines.append(f"| ❌ | **FAIL** — actual failure | {counts['fail']} |")
    lines.append("")
    lines.append(f"**Genuine feature support on this model+region**: "
                 f"{counts['behavioral']} of {totals['total']} surfaces. "
                 f"{counts['rejected']} surfaces are confirmed unsupported. "
                 f"{counts['mixed']} are partially supported.")
    lines.append("")

    lines.append("## Summary by category")
    lines.append("")
    lines.append("| Category | Total | 🟢 Supported | ⛔ Rejected | 🟡 Mixed | ❌ Fail |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for cat, c in payload["categories"].items():
        cat_counts = {"behavioral": 0, "rejected": 0, "mixed": 0, "fail": 0}
        for t in c["tests"]:
            cat_counts[_classify(t)[0]] += 1
        lines.append(
            f"| `{cat}` | {c['total']} | {cat_counts['behavioral']} | "
            f"{cat_counts['rejected']} | {cat_counts['mixed']} | {cat_counts['fail']} |"
        )
    lines.append("")

    lines.append("## Details")
    for cat, c in payload["categories"].items():
        lines.append("")
        lines.append(f"### `{cat}` — {c['passed']} / {c['total']}")
        lines.append("")
        lines.append("| Test | Status | Time | Description | Notes |")
        lines.append("| --- | --- | ---: | --- | --- |")
        for t in c["tests"]:
            _, label = _classify(t)
            elapsed = f"{t['elapsed_s']:.2f}s"
            note = ""
            if not t["ok"] and t.get("error"):
                note = (t["error"].splitlines()[0] if t["error"] else "")[:120]
            elif t.get("info"):
                note = json.dumps(t["info"], default=str)[:120]
            note = note.replace("|", "\\|").replace("\n", " ")
            desc = (t.get("description") or "").replace("|", "\\|")
            lines.append(f"| `{t['name']}` | {label} | {elapsed} | {desc} | {note} |")
    lines.append("")
    return "\n".join(lines)


def _write_results(by_cat_summary, all_results, started_utc: str, model_id: str = MODEL_ID) -> dict:
    payload = {
        "started_utc": started_utc,
        "region": REGION,
        "model": model_id,
        "totals": {
            "passed": sum(1 for _, r in all_results if r.ok),
            "total": len(all_results),
        },
        "categories": {
            c: {
                "passed": sum(1 for r in rs if r.ok),
                "total": len(rs),
                "tests": [
                    {
                        "name": r.name,
                        "description": r.description,
                        "ok": r.ok,
                        "elapsed_s": round(r.elapsed_s, 3),
                        "info": r.info,
                        "error": r.error,
                    }
                    for r in rs
                ],
            }
            for c, rs in by_cat_summary.items()
        },
    }
    return payload


def _list_inventory_json() -> None:
    """Emit the test inventory (categories, names, descriptions) and exit."""
    by_cat = discover()
    inventory = {
        "model": MODEL_ID,
        "region": REGION,
        "totals": sum(len(ms) for ms in by_cat.values()),
        "categories": [
            {
                "name": cat,
                "count": len(modules),
                "tests": [{"name": m.NAME, "description": m.DESCRIPTION} for m in modules],
            }
            for cat, modules in by_cat.items()
        ],
    }
    print(json.dumps(inventory, indent=2))


def _run_one_model(client, model_id: str, args, started_utc: str):
    """Run the filtered plan against a specific model_id; return payload dict."""
    by_cat = discover()
    only_tests = set(args.only_tests) if args.only_tests else None

    plan: list[tuple[str, list]] = []
    for category, modules in by_cat.items():
        if args.only and category not in args.only:
            continue
        selected = [m for m in modules if not only_tests or m.NAME in only_tests]
        if selected:
            plan.append((category, selected))
    total = sum(len(ms) for _, ms in plan)
    if total == 0:
        print("\nNo tests match the filter.")
        return None

    is_tty = sys.stdout.isatty()
    use_color = is_tty
    GREEN = "\033[32m" if use_color else ""
    RED = "\033[31m" if use_color else ""
    YELLOW = "\033[33m" if use_color else ""
    DIM = "\033[2m" if use_color else ""
    BOLD = "\033[1m" if use_color else ""
    RESET = "\033[0m" if use_color else ""

    def _bar(cur: int, total: int, width: int = 24) -> str:
        if total <= 0:
            return ""
        filled = max(0, min(width, int(round(cur * width / total))))
        return "█" * filled + "░" * (width - filled)

    print(f"\nPlanned: {total} test(s) across {len(plan)} categor"
          f"{'y' if len(plan)==1 else 'ies'}")

    all_results: list[tuple[str, Result]] = []
    counter = 0
    overall_start = time.perf_counter()

    for category, modules in plan:
        print(f"\n{BOLD}# {category}{RESET}  ({len(modules)} test"
              f"{'s' if len(modules)!=1 else ''})")
        for mod in modules:
            counter += 1
            pct = int(counter * 100 / total)
            elapsed = time.perf_counter() - overall_start
            bar = _bar(counter - 1, total)
            start_line = (
                f"  [{counter:3d}/{total}] {bar} {pct:3d}%  "
                f"{YELLOW}▶{RESET} {mod.NAME:<38s} {DIM}running…{RESET} "
                f"{DIM}elapsed {elapsed:5.1f}s{RESET}"
            )
            if is_tty:
                sys.stdout.write("\r\033[K" + start_line); sys.stdout.flush()
            else:
                print(start_line)

            r = execute(mod.NAME, mod.DESCRIPTION,
                        lambda m=mod, mid=model_id: m.run(client, mid))
            all_results.append((category, r))

            bar = _bar(counter, total)
            elapsed = time.perf_counter() - overall_start
            icon = f"{GREEN}✓{RESET}" if r.ok else f"{RED}✗{RESET}"
            status = f"{GREEN}PASS{RESET}" if r.ok else f"{RED}FAIL{RESET}"
            done_line = (
                f"  [{counter:3d}/{total}] {bar} {pct:3d}%  "
                f"{icon} {mod.NAME:<38s} {status} {r.elapsed_s:5.2f}s "
                f"{DIM}(total {elapsed:5.1f}s){RESET}"
            )
            if is_tty:
                sys.stdout.write("\r\033[K" + done_line + "\n"); sys.stdout.flush()
            else:
                print(done_line)

            if not r.ok:
                err_line = (r.error or "").splitlines()[0] if r.error else ""
                if err_line:
                    print(f"        {RED}↳{RESET} {err_line[:120]}")
                if r.info:
                    info_str = json.dumps(r.info, default=str)
                    print(f"        {DIM}info: {info_str[:180]}{RESET}")

    print()
    by_cat_summary: dict[str, list[Result]] = defaultdict(list)
    for c, r in all_results:
        by_cat_summary[c].append(r)
    print("Category summary:")
    for c, rs in by_cat_summary.items():
        passed = sum(1 for r in rs if r.ok)
        print(f"  {c:18s} {passed}/{len(rs)}")
    total_pass = sum(1 for _, r in all_results if r.ok)
    print(f"\nOverall: {total_pass}/{len(all_results)} passed")

    return _write_results(by_cat_summary, all_results, started_utc, model_id=model_id)


def _classify_kind(t: dict) -> str:
    return _classify(t)[0]


def _icon_for(kind: str) -> str:
    return {"behavioral": "🟢", "rejected": "⛔", "mixed": "🟡", "fail": "❌"}.get(kind, "·")


def _render_matrix_markdown(matrix: dict[str, dict]) -> str:
    """Render a multi-model matrix payload {model_id: payload}."""
    lines: list[str] = []
    lines.append("# Bedrock × Anthropic API — multi-model matrix")
    lines.append("")
    if matrix:
        first = next(iter(matrix.values()))
        lines.append(f"- **Region**: `{first['region']}`")
        lines.append(f"- **Started (UTC)**: {first['started_utc']}")
    lines.append(f"- **Models**: {len(matrix)}")
    lines.append("")

    # Per-model totals
    lines.append("## Per-model totals")
    lines.append("")
    lines.append("| Model | 🟢 Supported | ⛔ Rejected | 🟡 Mixed | ❌ Fail | Total |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for model_id, payload in matrix.items():
        counts = {"behavioral": 0, "rejected": 0, "mixed": 0, "fail": 0}
        for c in payload["categories"].values():
            for t in c["tests"]:
                counts[_classify_kind(t)] += 1
        total = payload["totals"]["total"]
        lines.append(f"| `{model_id}` | {counts['behavioral']} | "
                     f"{counts['rejected']} | {counts['mixed']} | "
                     f"{counts['fail']} | {total} |")
    lines.append("")

    # Build a flat lookup: {test_name: {model_id: kind}}
    # Use the union of test names across all models.
    test_kinds: dict[str, dict[str, str]] = {}
    test_categories: dict[str, str] = {}
    for model_id, payload in matrix.items():
        for cat, c in payload["categories"].items():
            for t in c["tests"]:
                test_kinds.setdefault(t["name"], {})[model_id] = _classify_kind(t)
                test_categories[t["name"]] = cat

    # Test × Model matrix grouped by category
    lines.append("## Test × Model matrix")
    lines.append("")
    by_cat: dict[str, list[str]] = defaultdict(list)
    for tname, cat in test_categories.items():
        by_cat[cat].append(tname)

    model_order = list(matrix.keys())
    for cat in sorted(by_cat.keys()):
        lines.append(f"### `{cat}`")
        lines.append("")
        header = "| Test | " + " | ".join(f"`{m}`" for m in model_order) + " |"
        sep = "| --- | " + " | ".join(":---:" for _ in model_order) + " |"
        lines.append(header)
        lines.append(sep)
        for tname in sorted(by_cat[cat]):
            row = [f"`{tname}`"]
            for m in model_order:
                kind = test_kinds[tname].get(m, "fail")
                row.append(_icon_for(kind))
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    # Inter-model differences
    lines.append("## Inter-model differences")
    lines.append("")
    diffs = []
    for tname, kinds in test_kinds.items():
        present_kinds = set(kinds.values())
        if len(present_kinds) > 1:
            diffs.append((tname, kinds))
    if not diffs:
        lines.append("All tests agree across models.")
    else:
        lines.append(f"{len(diffs)} test(s) where models disagree:")
        lines.append("")
        lines.append("| Test | " + " | ".join(f"`{m}`" for m in model_order) + " |")
        lines.append("| --- | " + " | ".join(":---:" for _ in model_order) + " |")
        for tname, kinds in sorted(diffs):
            row = [f"`{tname}`"]
            for m in model_order:
                k = kinds.get(m, "fail")
                row.append(f"{_icon_for(k)} {k}")
            lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="Run only these category names.")
    ap.add_argument("--only-tests", nargs="*", default=None,
                    help="Run only tests whose NAME matches.")
    ap.add_argument("--list-json", action="store_true",
                    help="Print the test inventory as JSON and exit.")
    ap.add_argument("--json", action="store_true",
                    help="Also emit JSON results to stdout.")
    ap.add_argument("--no-save", action="store_true",
                    help="Do not write results/ files.")
    ap.add_argument("--all-models", action="store_true",
                    help="Run tests for every model in config.ALL_MODELS and emit a matrix.")
    args = ap.parse_args()

    if args.list_json:
        _list_inventory_json()
        return 0

    started_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    client = make_client()
    tokens = TokenAccumulator()
    wrap_client_with_tracker(client, tokens)
    print(f"Started: {started_utc}")
    print(f"Region:  {REGION}")

    if args.all_models:
        print(f"Models:  {len(ALL_MODELS)} (matrix mode)")
        for m in ALL_MODELS:
            print(f"  - {m}")
        matrix: dict[str, dict] = {}
        per_model_tokens: dict[str, TokenAccumulator] = {}
        for i, model_id in enumerate(ALL_MODELS, 1):
            print(f"\n{'═' * 72}")
            print(f"MODEL {i}/{len(ALL_MODELS)}: {model_id}")
            print('═' * 72)
            model_tokens = TokenAccumulator()
            client_for_model = make_client()
            wrap_client_with_tracker(client_for_model, model_tokens)
            wrap_client_with_tracker(client_for_model, tokens)
            payload = _run_one_model(client_for_model, model_id, args, started_utc)
            if payload is not None:
                matrix[model_id] = payload
                per_model_tokens[model_id] = model_tokens

        # Aggregate totals
        all_pass = sum(p["totals"]["passed"] for p in matrix.values())
        all_total = sum(p["totals"]["total"] for p in matrix.values())
        print(f"\n{'═' * 72}")
        print(f"MATRIX TOTAL: {all_pass}/{all_total} across {len(matrix)} models")
        for model_id, t in per_model_tokens.items():
            print()
            print(f"-- per-model tokens: {model_id} --")
            _print_token_summary(t)
        print()
        print("== matrix-wide tokens ==")
        _print_token_summary(tokens)

        if not args.no_save:
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            matrix_json = RESULTS_DIR / "matrix.json"
            matrix_md = RESULTS_DIR / "matrix.md"
            matrix_json.write_text(json.dumps(matrix, default=str, indent=2))
            matrix_md.write_text(_render_matrix_markdown(matrix))
            print(f"\nMatrix saved:\n  {matrix_json}\n  {matrix_md}")
        return 0 if all_pass == all_total else 1

    # Single-model run
    print(f"Model:   {MODEL_ID}")
    payload = _run_one_model(client, MODEL_ID, args, started_utc)
    if payload is None:
        return 0

    if args.json:
        print(json.dumps(payload, default=str, indent=2))

    if not args.no_save:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        latest_json = RESULTS_DIR / "latest.json"
        latest_md = RESULTS_DIR / "latest.md"
        latest_json.write_text(json.dumps(payload, default=str, indent=2))
        latest_md.write_text(_render_markdown(payload))
        print(f"\nResults saved:\n  {latest_json}\n  {latest_md}")

    _print_token_summary(tokens)
    return 0 if payload["totals"]["passed"] == payload["totals"]["total"] else 1


def _print_token_summary(tokens: TokenAccumulator) -> None:
    s = tokens.summary()
    print()
    print("Token usage summary (across all messages.create calls):")
    print(f"  Calls:                 {s['calls']}")
    print(f"  Input tokens:          {s['input_tokens']:>10,}")
    print(f"  Output tokens:         {s['output_tokens']:>10,}")
    print(f"  Cache create (5m):     {s['ephemeral_5m_input_tokens']:>10,}")
    print(f"  Cache create (1h):     {s['ephemeral_1h_input_tokens']:>10,}")
    print(f"  Cache create (total):  {s['cache_creation_input_tokens']:>10,}")
    print(f"  Cache read:            {s['cache_read_input_tokens']:>10,}")
    print(f"  Total billable input:  {s['total_billable_input']:>10,}")


if __name__ == "__main__":
    sys.exit(main())
