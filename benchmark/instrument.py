"""Timing and peak-memory measurement (G2, G3).

Phase 08 owns this module. One context manager used identically by every runner, so
the timing boundary is the same for pyannote and Gemma.
"""

from __future__ import annotations

from typing import Any


class Measurement:
    """Result of a measured block: wall seconds, peak VRAM MB, peak RAM MB."""

    def __init__(self, **fields: Any) -> None:
        raise NotImplementedError("Phase 08")


class measure:
    """Context manager: `with measure() as m: ...` then read `m.result`.

    Resets torch CUDA peak stats on entry and samples RSS on a background thread so the
    CPU leg's peak is not just the value at exit.
    """

    def __enter__(self) -> "measure":
        raise NotImplementedError("Phase 08")

    def __exit__(self, *exc: object) -> None:
        raise NotImplementedError("Phase 08")


def rtf(processing_seconds: float, audio_seconds: float) -> float:
    """Real-time factor: processing_time / audio_duration."""
    raise NotImplementedError("Phase 08")
