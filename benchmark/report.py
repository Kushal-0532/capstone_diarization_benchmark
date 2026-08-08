"""Markdown report assembly (G5).

Phase 18 owns this module. The report must state the methodology deviations that make
the numbers what they are: 5-minute excerpts (D4), overlap scored (D6), greedy decoding
(D8), and that diarization is an unadvertised Gemma capability (D1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def results_tables(scores: Any) -> str:
    """Cross-system x cross-runtime x cross-dataset Markdown tables."""
    raise NotImplementedError("Phase 18")


def failure_cases(results: list[Any], n_per_system: int = 3) -> str:
    """2-3 worst-DER examples per system, with V9 timelines embedded."""
    raise NotImplementedError("Phase 18")


def methodology_section() -> str:
    """The stated deviations and constraints, generated from config so it cannot drift."""
    raise NotImplementedError("Phase 18")


def build(scores: Any, results: list[Any], out: Path | None = None) -> Path:
    """Assemble the full report to REPORT_PATH and return it."""
    raise NotImplementedError("Phase 18")
