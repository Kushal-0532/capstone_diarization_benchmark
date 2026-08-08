"""The chart set V1-V9 (G4, D7): static matplotlib/seaborn PNGs.

Phase 17 owns this module. Every chart must be legible screenshotted out of context:
consistent axes, units, system colours and legends across all nine.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# One colour per system, shared by every chart.
SYSTEM_COLORS: dict[str, str] = {}


def v1_der_by_system(scores: Any, out: Path | None = None) -> Path:
    """Grouped bar: DER per system, grouped by dataset."""
    raise NotImplementedError("Phase 17")


def v2_der_components(scores: Any, out: Path | None = None) -> Path:
    """Stacked bar: DER split into miss / false alarm / confusion."""
    raise NotImplementedError("Phase 17")


def v3_der_vs_speakers(scores: Any, out: Path | None = None) -> Path:
    """DER vs reference speaker-count bucket, per system."""
    raise NotImplementedError("Phase 17")


def v4_rtf_by_runtime(scores: Any, out: Path | None = None) -> Path:
    """Grouped bar: RTF per system, CPU vs GPU."""
    raise NotImplementedError("Phase 17")


def v5_duration_vs_time(scores: Any, out: Path | None = None) -> Path:
    """Scatter: audio duration vs processing time per file, coloured by system."""
    raise NotImplementedError("Phase 17")


def v6_peak_memory(scores: Any, out: Path | None = None) -> Path:
    """Grouped bar: peak VRAM (GPU) and peak RAM (CPU) per system."""
    raise NotImplementedError("Phase 17")


def v7_der_vs_rtf(scores: Any, out: Path | None = None) -> Path:
    """Scatter with Pareto frontier: DER vs RTF. Priority chart for the recommendation."""
    raise NotImplementedError("Phase 17")


def v8_der_vs_memory(scores: Any, out: Path | None = None) -> Path:
    """Scatter: DER vs peak VRAM/RAM."""
    raise NotImplementedError("Phase 17")


def v9_failure_timeline(result: Any, out: Path | None = None) -> Path:
    """Gantt: reference turns vs predicted turns on a shared time axis, for one file."""
    raise NotImplementedError("Phase 17")


def render_all(scores: Any, out_dir: Path | None = None) -> list[Path]:
    """Produce V1-V9 into CHARTS_DIR and return the written paths."""
    raise NotImplementedError("Phase 17")
