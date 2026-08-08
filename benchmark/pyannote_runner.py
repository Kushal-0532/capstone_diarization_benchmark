"""System A — pyannote.audio 3.1 diarization runner.

Phase 09 owns this module. Call signature must be verified against the *installed*
3.1.x (OQ5): 3.1.x takes `use_auth_token=` and returns a plain `Annotation`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_pipeline(token: str, device: str | None = None) -> Any:
    """Load `pyannote/speaker-diarization-3.1` and move it to `device`."""
    raise NotImplementedError("Phase 09")


def run_file(pipeline: Any, audio_path: Path, dataset: str, file_id: str) -> Any:
    """Diarize one excerpt under `instrument.measure()`. Returns a FileResult."""
    raise NotImplementedError("Phase 09")


def to_turns(annotation: Any) -> list[Any]:
    """Convert a pyannote `Annotation` to the shared Turn list."""
    raise NotImplementedError("Phase 09")
