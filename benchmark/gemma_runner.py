"""Systems B1/B2/B3 — Gemma 4 E2B / E4B / 12B, variant selected by config.

Phase 12 writes this once; Phases 13 and 14 only add configuration (and 4-bit
quantization for 12B, OQ3). There is deliberately no per-variant code path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_model(system: str, token: str, quantize_4bit: bool = False) -> tuple[Any, Any]:
    """Load (processor, model) for a Gemma system id. Returns AutoProcessor + model."""
    raise NotImplementedError("Phase 12")


def run_window(processor: Any, model: Any, audio: Any) -> str:
    """Generate raw text for one window. Greedy, thinking disabled (D8)."""
    raise NotImplementedError("Phase 12")


def run_file(
    processor: Any, model: Any, system: str, audio_path: Path, dataset: str, file_id: str
) -> Any:
    """Window -> generate -> parse -> stitch one excerpt under measurement. Returns FileResult."""
    raise NotImplementedError("Phase 12")
