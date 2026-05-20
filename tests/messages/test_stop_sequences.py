"""Backcompat shim — actual probe lives in probes.messages.stop_sequences."""
from probes.messages.stop_sequences import NAME, DESCRIPTION, run  # noqa: F401
