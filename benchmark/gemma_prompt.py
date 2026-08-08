"""The one prompt and the one output parser, byte-identical across E2B/E4B/12B (D9).

Phase 10 owns this module and *freezes* it. No per-variant tuning, ever — otherwise
measured differences reflect prompt engineering rather than the models.
"""

from __future__ import annotations

from typing import Any

# Frozen in Phase 10. Changing this after Phase 12 invalidates every Gemma DER number.
PROMPT: str = ""


def build_messages(audio: Any) -> list[dict[str, Any]]:
    """Chat-template message list for one <=30 s window (config.GEMMA_WINDOW_SECONDS)."""
    raise NotImplementedError("Phase 10")


def parse(text: str, window_start: float, window_end: float) -> list[Any]:
    """Parse model output into Turns with absolute times.

    Tolerant of formatting noise, strict about times: anything unparseable or outside
    the window is dropped and counted, never guessed. Fallback formulation (fixed ~1 s
    grid labelling) is decided here per OQ2, not assumed.
    """
    raise NotImplementedError("Phase 10")


def parse_failures() -> dict[str, int]:
    """Counts of dropped/unparseable outputs, reported alongside DER."""
    raise NotImplementedError("Phase 10")
