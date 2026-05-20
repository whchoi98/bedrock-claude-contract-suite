"""Backcompat shim — actual probe lives in probes.caching.savings_measured."""
from probes.caching.savings_measured import NAME, DESCRIPTION, run  # noqa: F401
