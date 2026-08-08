"""The single DER code path, applied identically to all four systems (C5, D6).

Phase 16 owns this module. It consumes only the shared FileResult shape and cannot
see which system produced a record — that is what enforces identical methodology.
"""

from __future__ import annotations

from typing import Any


def score_file(result: Any) -> dict[str, float]:
    """DER for one FileResult: total plus miss / false alarm / confusion components.

    collar=COLLAR, skip_overlap=SKIP_OVERLAP, optimal (Hungarian) mapping, UEM-restricted.
    """
    raise NotImplementedError("Phase 16")


def score_all(results: list[Any]) -> Any:
    """Score every result; returns a tidy DataFrame keyed by system/runtime/dataset/file."""
    raise NotImplementedError("Phase 16")


def aggregate(scores: Any, by: tuple[str, ...] = ("system", "dataset")) -> Any:
    """Duration-weighted aggregate DER (sum of errors / sum of reference time), not a file mean."""
    raise NotImplementedError("Phase 16")
