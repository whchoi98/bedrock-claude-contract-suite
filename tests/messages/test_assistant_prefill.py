"""Backcompat shim — actual probe lives in probes.messages.assistant_prefill."""
from probes.messages.assistant_prefill import NAME, DESCRIPTION, run  # noqa: F401
