"""Backcompat shim — actual probe lives in probes.token_counting.count_tokens."""
from probes.token_counting.count_tokens import NAME, DESCRIPTION, run  # noqa: F401
