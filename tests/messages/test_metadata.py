"""Backcompat shim — actual probe lives in probes.messages.metadata."""
from probes.messages.metadata import NAME, DESCRIPTION, run  # noqa: F401
