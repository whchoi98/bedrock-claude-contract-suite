"""Backcompat shim — actual probe lives in probes.unsupported.compaction_header_rejected."""
from probes.unsupported.compaction_header_rejected import NAME, DESCRIPTION, run  # noqa: F401
