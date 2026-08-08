"""30 s windowing and cross-window speaker stitching (C1, OQ1).

Phase 11 owns this module. Gemma exposes no speaker embeddings, so cross-window
linking has no principled signal — whatever heuristic is chosen here must be stated
plainly in the report as a methodological limitation.
"""

from __future__ import annotations

from typing import Any, Iterator


def windows(audio: Any, window_seconds: float | None = None) -> Iterator[tuple[float, float, Any]]:
    """Yield (start, end, samples) windows of at most GEMMA_WINDOW_SECONDS."""
    raise NotImplementedError("Phase 11")


def stitch(per_window_turns: list[list[Any]]) -> list[Any]:
    """Map per-window local speaker labels onto global ones across the whole excerpt."""
    raise NotImplementedError("Phase 11")


def merge_adjacent(turns: list[Any], gap_tolerance: float = 0.0) -> list[Any]:
    """Merge consecutive same-speaker turns separated by <= gap_tolerance seconds."""
    raise NotImplementedError("Phase 11")
