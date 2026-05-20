"""Backcompat shim — actual probe lives in probes.messages.max_tokens_truncation."""
from probes.messages.max_tokens_truncation import NAME, DESCRIPTION, run  # noqa: F401
