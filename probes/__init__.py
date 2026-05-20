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
