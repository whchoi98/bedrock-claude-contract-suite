#!/usr/bin/env python3
"""Build a dated snapshot of a matrix run.

Creates results/runs/<YYYY-MM-DD>/ with:
  - matrix.json, matrix.md       (verbatim copy of latest)
  - bedrock.md, cpaws.md         (per-provider single-provider views)
  - tests-snapshot/              (probes/ at this point in time)
  - MANIFEST.md                  (git SHA, command, env, per-cell counts)

Usage:
  python3 scripts/snapshot_matrix.py             # uses today (UTC)
  python3 scripts/snapshot_matrix.py 2026-05-20
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import shutil
import subprocess
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
PROBES = ROOT / "probes"


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), *args],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return ""


def _redact_env() -> dict[str, str]:
    """Snapshot relevant env vars with secrets reduced to prefix+length."""
    import os
    keys = (
        "AWS_BEARER_TOKEN_BEDROCK",
        "AWS_REGION",
        "BEDROCK_MODEL_ID",
        "ANTHROPIC_AWS_API_KEY",
        "ANTHROPIC_AWS_WORKSPACE_ID",
        "CPAWS_REGION",
    )
    out: dict[str, str] = {}
    for k in keys:
        v = os.environ.get(k)
        if v is None:
            out[k] = "<unset>"
        elif any(s in k for s in ("TOKEN", "KEY", "WORKSPACE_ID")):
            # WORKSPACE_ID is not a secret per se but identifies the org;
            # redact for the same reason we redact tokens — public sharing
            # of snapshots should not leak account-shaped identifiers.
            out[k] = f"{v[:6]}…<redacted, len={len(v)}>"
        else:
            out[k] = v
    return out


def _failure_caveats(matrix: dict) -> list[str]:
    """Build human-readable notes about why specific failures occurred.

    Distinguishes three kinds of ❌ in the matrix:
      - **Contract divergence captured** — the probe's assertion is shaped
        around one provider's contract (typically Bedrock). The other
        provider satisfies the *opposite* contract correctly. ❌ here
        means "the alternative provider's behavior was observed", not
        "the probe is broken". See `unsupported/*` for canonical examples.
      - **Tier 1 rate-limit** — CPaws workspaces start at Tier 1
        (30k ITPM). Probes with large prompts (PDF, 1M context) exceed
        this in a single call and 429 even after SDK retries.
      - **Real failure** — neither of the above. Worth investigating.
    """
    notes: list[str] = []
    rate_limited: list[str] = []
    divergent: list[str] = []
    other: list[str] = []
    for provider, by_alias in matrix.items():
        for alias, payload in by_alias.items():
            for cat, c in payload["categories"].items():
                for t in c["tests"]:
                    if t["ok"]:
                        continue
                    err = (t.get("error") or "") + json.dumps(t.get("info", {}))
                    label = f"{provider}/{alias}: {cat}/{t['name']}"
                    if "rate_limit_error" in err or "RateLimitError" in err:
                        rate_limited.append(label)
                    elif (
                        "accepted_unexpectedly" in err
                        or "succeeded_unexpectedly" in err
                        or t["name"].endswith("_rejected_on_bedrock")
                        or t["name"] == "bedrock_unsupported"
                        or t["name"] == "server_tools_rejected"
                    ):
                        divergent.append(label)
                    else:
                        other.append(label)
    if rate_limited:
        notes.append(
            "### Tier 1 rate-limit blocked (not a contract issue)\n\n"
            "These probes' input size alone exceeds the workspace's 30k "
            "ITPM; SDK retries do not help.\n\n" +
            "\n".join(f"- `{r}`" for r in rate_limited)
        )
    if divergent:
        notes.append(
            "### Contract divergence captured (probe expects Bedrock shape)\n\n"
            "These probes' pass-condition is shaped around Bedrock's "
            "rejection. The opposing provider (CPaws) accepts the surface "
            "— ❌ here documents *where the providers diverge*, not where "
            "the probe is broken. Compare with the corresponding row in "
            "`cpaws_findings.md §A`.\n\n" +
            "\n".join(f"- `{r}`" for r in divergent)
        )
    if other:
        notes.append(
            "### Other failures (investigate)\n\n"
            "Failures not classified above. These are either real "
            "contract changes, transient errors, or probe assertions "
            "that need refinement.\n\n" +
            "\n".join(f"- `{r}`" for r in other)
        )
    return notes


def _classify_kind(t: dict) -> str:
    """Mirror run_all.py:_classify_kind so the snapshot has stable counts."""
    if not t["ok"]:
        return "fail"
    info = t.get("info") or {}
    name = t.get("name", "")
    contract = info.get("contract")
    if isinstance(contract, str) and "reject" in contract.lower():
        return "rejected"
    if "deprecation_signals" in info:
        return "rejected"
    if info.get("config_rejected_on_bedrock") is True and info.get("header_accepted") is True:
        return "mixed"
    if info.get("backend") == "bedrock_unsupported":
        return "rejected"
    if "rejected" in name or "deprecated" in name or "absent" in name:
        return "rejected"
    if name == "bedrock_unsupported":
        return "rejected"
    return "behavioral"


def _kind_icon(kind: str) -> str:
    return {"behavioral": "🟢", "rejected": "⛔", "mixed": "🟡", "fail": "❌"}.get(kind, "·")


def _render_provider_view(matrix: dict, provider: str) -> str:
    """Single-provider markdown: model columns × test rows."""
    if provider not in matrix or not matrix[provider]:
        return f"# {provider} (no runs)\n"
    aliases = list(matrix[provider].keys())

    # Build {test_name: {alias: kind}} keyed by category for nice grouping.
    by_cat: dict[str, dict[str, dict[str, str]]] = {}
    for alias, payload in matrix[provider].items():
        for cat, c in payload["categories"].items():
            for t in c["tests"]:
                by_cat.setdefault(cat, {}).setdefault(t["name"], {})[alias] = _classify_kind(t)

    lines: list[str] = [
        f"# `{provider}` — single-provider matrix",
        "",
        f"- **Date**: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')}",
        f"- **Models**: {aliases}",
        "",
        "## Totals",
        "",
        "| Model | 🟢 Supported | ⛔ Rejected | 🟡 Mixed | ❌ Fail | Total |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for alias in aliases:
        payload = matrix[provider][alias]
        c = Counter()
        for cat in payload["categories"].values():
            for t in cat["tests"]:
                c[_classify_kind(t)] += 1
        total = payload["totals"]["total"]
        lines.append(
            f"| `{alias}` | {c['behavioral']} | {c['rejected']} | "
            f"{c['mixed']} | {c['fail']} | {total} |"
        )
    lines.append("")
    lines.append("## Test × Model matrix")
    lines.append("")
    header = "| Test | " + " | ".join(f"`{a}`" for a in aliases) + " |"
    sep = "| --- | " + " | ".join(":---:" for _ in aliases) + " |"
    for cat in sorted(by_cat):
        lines.append(f"### `{cat}`")
        lines.append("")
        lines.append(header)
        lines.append(sep)
        for tname in sorted(by_cat[cat]):
            kinds = by_cat[cat][tname]
            row = [f"`{tname}`"]
            for a in aliases:
                row.append(_kind_icon(kinds.get(a, "fail")))
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    return "\n".join(lines)


def _render_manifest(date: str, matrix: dict, command: str) -> str:
    git_sha = _git("rev-parse", "--short", "HEAD") or "(no git)"
    git_status = _git("status", "--porcelain")
    dirty = "dirty (uncommitted changes)" if git_status else "clean"
    env = _redact_env()

    # Collect concrete model IDs per provider × alias.
    model_ids: dict[str, dict[str, str]] = {}
    for provider, by_alias in matrix.items():
        for alias, payload in by_alias.items():
            model_ids.setdefault(provider, {})[alias] = payload.get("model", "<unknown>")

    # Per-cell pass counts.
    cells: list[tuple[str, str, int, int]] = []
    for provider, by_alias in matrix.items():
        for alias, payload in by_alias.items():
            cells.append((provider, alias,
                          payload["totals"]["passed"], payload["totals"]["total"]))

    lines = [
        f"# Matrix run snapshot — {date}",
        "",
        "## Git",
        "",
        f"- SHA: `{git_sha}`",
        f"- State: {dirty}",
        "",
        "## Command",
        "",
        "```bash",
        command,
        "```",
        "",
        "## Environment (secrets redacted)",
        "",
    ]
    for k, v in env.items():
        lines.append(f"- `{k}` = `{v}`")
    lines.append("")
    lines.append("## Concrete model IDs used")
    lines.append("")
    lines.append("| Provider | Alias | Model ID |")
    lines.append("| --- | --- | --- |")
    for provider in sorted(model_ids):
        for alias in sorted(model_ids[provider]):
            lines.append(f"| `{provider}` | `{alias}` | `{model_ids[provider][alias]}` |")
    lines.append("")
    lines.append("## Per-cell totals")
    lines.append("")
    lines.append("| Provider | Alias | Passed | Total |")
    lines.append("| --- | --- | ---: | ---: |")
    for provider, alias, passed, total in cells:
        lines.append(f"| `{provider}` | `{alias}` | {passed} | {total} |")
    lines.append("")
    n_providers = len(matrix)
    n_models = len({a for by in matrix.values() for a in by})
    lines.append("## Files in this snapshot")
    lines.append("")
    lines.append(f"- `matrix.{{json,md}}` — full {n_providers}-provider × {n_models}-model matrix (verbatim run output)")
    lines.append("- `bedrock.md` / `cpaws.md` — per-provider sub-matrices for at-a-glance comparison")
    lines.append("- `tests-snapshot/` — `probes/` package at run time (the canonical, reusable form of every probe). Importable as a Python module.")
    lines.append("- `MANIFEST.md` — this file")
    lines.append("")
    caveats = _failure_caveats(matrix)
    if caveats:
        lines.append("## Notes on failures (read before interpreting ❌)")
        lines.append("")
        for section in caveats:
            lines.append(section)
            lines.append("")
    return "\n".join(lines)


def main() -> int:
    date = sys.argv[1] if len(sys.argv) > 1 else dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        print(f"ERROR: date must be YYYY-MM-DD; got {date!r}", file=sys.stderr)
        return 2

    matrix_json = RESULTS / "matrix.json"
    matrix_md = RESULTS / "matrix.md"
    if not matrix_json.exists():
        print(f"ERROR: {matrix_json} missing — run the matrix first.", file=sys.stderr)
        return 2

    snap = RESULTS / "runs" / date
    snap.mkdir(parents=True, exist_ok=True)

    shutil.copy(matrix_json, snap / "matrix.json")
    shutil.copy(matrix_md, snap / "matrix.md")

    matrix = json.loads(matrix_json.read_text())
    for provider in matrix:
        (snap / f"{provider}.md").write_text(_render_provider_view(matrix, provider))

    tests_snap = snap / "tests-snapshot"
    if tests_snap.exists():
        shutil.rmtree(tests_snap)
    shutil.copytree(PROBES, tests_snap, ignore=shutil.ignore_patterns("__pycache__"))

    command = "python3 run_all.py --providers bedrock cpaws --all-models"
    (snap / "MANIFEST.md").write_text(_render_manifest(date, matrix, command))

    print(f"Snapshot written: {snap}")
    for f in sorted(snap.iterdir()):
        print(f"  {f.relative_to(RESULTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
