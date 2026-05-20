#!/usr/bin/env python3
"""One-shot migration: tests/ → probes/ reusable library.

Effect:
  - Moves tests/_base.py    → probes/_base.py (tests/_base.py becomes shim)
  - Moves tests/<cat>/test_<name>.py → probes/<cat>/<name>.py
    (drops the test_ prefix; fixes `tests._base` import → `probes._base`)
  - Replaces each tests/<cat>/test_<name>.py with a 3-line shim that
    imports NAME/DESCRIPTION/run from the probes counterpart.
  - Writes probes/<cat>/__init__.py (auto-re-exports submodules).
  - Writes probes/__init__.py with a PROBES catalog plus list_probes() and
    get_probe() helpers.

Result: external projects can `from probes.caching.cache_ttl_1h import run`
or iterate `probes.PROBES`. The existing run_all.py discovers tests/
unchanged and gets the same behaviour via shims.

Idempotent: re-running after partial completion is safe because each step
is a no-op when its target already exists in the migrated shape.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
PROBES = ROOT / "probes"


def _is_category_dir(p: pathlib.Path) -> bool:
    return (
        p.is_dir()
        and not p.name.startswith("_")
        and p.name != "__pycache__"
    )


def _move_base() -> None:
    """tests/_base.py → probes/_base.py; install shim in tests/_base.py."""
    src = TESTS / "_base.py"
    dst = PROBES / "_base.py"
    if not dst.exists():
        if not src.exists():
            raise RuntimeError("tests/_base.py missing and probes/_base.py absent")
        shutil.copy(src, dst)
    shim = textwrap.dedent('''\
        """Backwards-compat shim — implementations live in probes._base.

        Tests still import from `tests._base` via the runner's auto-discovery
        path. New code should import directly from `probes._base`.
        """
        from probes._base import (  # noqa: F401
            Result,
            execute,
            is_unsupported_tool_rejection,
            text_of,
            usage_breakdown,
        )
    ''')
    src.write_text(shim)


def _migrate_probes() -> list[tuple[str, str]]:
    """Migrate every tests/<cat>/test_*.py to probes/<cat>/<name>.py.

    Returns list of (category, name_without_test_prefix) entries.
    """
    entries: list[tuple[str, str]] = []
    for cat_dir in sorted(filter(_is_category_dir, TESTS.iterdir())):
        cat = cat_dir.name
        pcat = PROBES / cat
        pcat.mkdir(parents=True, exist_ok=True)

        for tpath in sorted(cat_dir.glob("test_*.py")):
            new_stem = tpath.stem.removeprefix("test_")
            # Make a valid Python identifier:
            #  - reserved word (`async`) → suffix `_client` (in client/) or `_`
            #  - starts with a digit (e.g. `1m_window`) → prefix the category
            import keyword
            if keyword.iskeyword(new_stem) or new_stem in {"async", "await", "match", "case"}:
                new_stem = f"{new_stem}_client" if cat == "client" else f"{new_stem}_"
            if new_stem[:1].isdigit():
                new_stem = f"{cat}_{new_stem}"
            new_path = pcat / f"{new_stem}.py"

            shim_marker = (
                f"from probes.{cat}.{new_stem} import NAME, DESCRIPTION, run"
            )
            if tpath.read_text().strip().endswith(shim_marker) and new_path.exists():
                entries.append((cat, new_stem))
                continue

            src = tpath.read_text()
            src = re.sub(r"\btests\._base\b", "probes._base", src)
            src = re.sub(
                r"\bfrom tests\.(\w+)\.test_(\w+)\b",
                r"from probes.\1.\2",
                src,
            )
            src = re.sub(
                r"\bimport tests\.(\w+)\.test_(\w+)\b",
                r"import probes.\1.\2",
                src,
            )
            new_path.write_text(src)

            shim = textwrap.dedent(f'''\
                """Backcompat shim — actual probe lives in probes.{cat}.{new_stem}."""
                from probes.{cat}.{new_stem} import NAME, DESCRIPTION, run  # noqa: F401
            ''')
            tpath.write_text(shim)
            entries.append((cat, new_stem))
    return entries


def _write_category_inits(entries: list[tuple[str, str]]) -> None:
    by_cat: dict[str, list[str]] = {}
    for cat, name in entries:
        by_cat.setdefault(cat, []).append(name)
    for cat, names in by_cat.items():
        lines = [
            f'"""Reusable probes in the {cat}/ category."""',
            "",
        ]
        for n in sorted(names):
            lines.append(f"from . import {n}  # noqa: F401")
        lines.append("")
        lines.append("__all__ = " + repr(sorted(names)))
        lines.append("")
        (PROBES / cat / "__init__.py").write_text("\n".join(lines))


def _write_root_init() -> None:
    src = textwrap.dedent('''\
        """Bedrock × CPaws contract probes — reusable Python library.

        Each probe takes ``(client, model)`` and returns a dict shaped
        ``{"ok": bool, "info": dict, "error": str | None}``. Importing this
        package eagerly walks the category subpackages and registers every
        probe into the ``PROBES`` catalog.

        Examples
        --------
        Single probe::

            from probes.caching import cache_ttl_1h
            result = cache_ttl_1h.run(client, "claude-opus-4-7")

        Iterate the catalog::

            from probes import PROBES, list_probes
            for key in list_probes(category="tools"):
                print(key, "—", PROBES[key]["description"])

        Lookup by key::

            from probes import get_probe
            entry = get_probe("caching.cache_ttl_1h")
            entry["run"](client, "claude-opus-4-7")
        """
        from __future__ import annotations

        import importlib
        import pathlib
        from typing import Any, Callable

        _ROOT = pathlib.Path(__file__).resolve().parent

        PROBES: dict[str, dict[str, Any]] = {}


        def _walk_and_register() -> None:
            for cat_dir in sorted(_ROOT.iterdir()):
                if not cat_dir.is_dir() or cat_dir.name.startswith("_") or cat_dir.name == "__pycache__":
                    continue
                cat = cat_dir.name
                for path in sorted(cat_dir.glob("*.py")):
                    if path.name == "__init__.py":
                        continue
                    mod_name = f"probes.{cat}.{path.stem}"
                    mod = importlib.import_module(mod_name)
                    key = f"{cat}.{mod.NAME}"
                    PROBES[key] = {
                        "category": cat,
                        "name": mod.NAME,
                        "description": mod.DESCRIPTION,
                        "run": mod.run,
                        "module": mod_name,
                    }


        _walk_and_register()


        def list_probes(category: str | None = None) -> list[str]:
            """Return probe keys sorted; optionally filter by category."""
            if category is None:
                return sorted(PROBES)
            return sorted(k for k, v in PROBES.items() if v["category"] == category)


        def get_probe(key: str) -> dict[str, Any]:
            """Lookup a probe entry by ``"<category>.<name>"`` key."""
            try:
                return PROBES[key]
            except KeyError as exc:
                raise KeyError(
                    f"unknown probe {key!r}; known keys: {list_probes()[:5]}…"
                ) from exc


        def run_probe(key: str, client, model) -> dict[str, Any]:
            """Convenience: look up ``key`` and invoke its ``run(client, model)``."""
            return get_probe(key)["run"](client, model)


        __all__ = ["PROBES", "list_probes", "get_probe", "run_probe"]
    ''')
    (PROBES / "__init__.py").write_text(src)


def main() -> int:
    PROBES.mkdir(exist_ok=True)
    _move_base()
    entries = _migrate_probes()
    _write_category_inits(entries)
    _write_root_init()
    by_cat: dict[str, int] = {}
    for cat, _ in entries:
        by_cat[cat] = by_cat.get(cat, 0) + 1
    print(f"Migrated {len(entries)} probes into {len(by_cat)} categories.")
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat:18s} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
