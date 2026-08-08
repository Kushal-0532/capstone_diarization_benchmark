"""Dataset acquisition, deterministic excerpting, and reference construction.

Phases 04 (AMI), 05 (VoxConverse) and 06 (excerpting + UEM) own this module.
Excerpts are cut deterministically so every system is scored on the same span (D4).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def download_ami(dest: Path | None = None, n_files: int | None = None) -> list[str]:
    """Fetch AMI Mix-Headset audio + pyannote/AMI-diarization-setup RTTM/UEM. Returns file ids."""
    raise NotImplementedError("Phase 04")


def download_voxconverse(dest: Path | None = None, n_files: int | None = None) -> list[str]:
    """Fetch VoxConverse audio + RTTM. Returns file ids."""
    raise NotImplementedError("Phase 05")


def select_files(dataset: str, n: int) -> list[str]:
    """Stratified pick by reference speaker count (D5): low 2-3, high 4+."""
    raise NotImplementedError("Phase 04")


def excerpt(dataset: str, file_id: str) -> Path:
    """Cut the fixed EXCERPT_SECONDS window (offset from first annotated speech), 16 kHz mono."""
    raise NotImplementedError("Phase 06")


def reference(dataset: str, file_id: str) -> Any:
    """Reference `pyannote.core.Annotation`, trimmed to the excerpt span."""
    raise NotImplementedError("Phase 06")


def uem(dataset: str, file_id: str) -> Any:
    """Scoring `pyannote.core.Timeline` (UEM), trimmed to the excerpt span."""
    raise NotImplementedError("Phase 06")


def load_audio(path: Path) -> Any:
    """Load as float32 mono in [-1, 1] at config.SAMPLE_RATE (Gemma model card requirement)."""
    raise NotImplementedError("Phase 06")
