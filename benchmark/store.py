"""Checkpoint/resume store: survives Colab session death and CPU<->GPU restarts (C3).

Phase 07 owns this module. Per-file granularity: an interrupted run resumes from the
last completed file, not from zero.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    """Read the run manifest (which (system, runtime, dataset, file) keys are done)."""
    raise NotImplementedError("Phase 07")


def save_manifest(manifest: dict[str, Any], path: Path | None = None) -> None:
    """Write the manifest atomically (temp file + os.replace)."""
    raise NotImplementedError("Phase 07")


def is_done(system: str, runtime: str, dataset: str, file_id: str) -> bool:
    """True if this cell already has a checkpointed result."""
    raise NotImplementedError("Phase 07")


def record_result(result: Any) -> None:
    """Persist one FileResult and mark it done in the manifest."""
    raise NotImplementedError("Phase 07")


def sync_to_drive(local: Path | None = None, remote: Path | None = None) -> None:
    """Copy results to the mounted Drive directory."""
    raise NotImplementedError("Phase 07")
