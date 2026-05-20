"""Backcompat shim — actual probe lives in probes.caching.on_system."""
from probes.caching.on_system import NAME, DESCRIPTION, run  # noqa: F401
