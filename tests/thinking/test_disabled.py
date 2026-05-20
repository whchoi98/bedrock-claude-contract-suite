"""Backcompat shim — actual probe lives in probes.thinking.disabled."""
from probes.thinking.disabled import NAME, DESCRIPTION, run  # noqa: F401
