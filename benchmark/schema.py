"""Record shapes shared by every system, and their JSONL (de)serialization.

Phase 06 owns this module. The invariant it enforces: every system on every runtime
writes the *same* FileResult shape, so scoring/charting/reporting cannot tell which
system produced a record.
"""

from __future__ import annotations

from typing import Any, Iterable, Iterator
from pathlib import Path


class Turn:
    """A single speaker turn: (start, end, speaker) in seconds, relative to the excerpt."""

    def __init__(self, start: float, end: float, speaker: str) -> None:
        raise NotImplementedError("Phase 06")


class FileResult:
    """One (system, runtime, dataset, file) result: turns + timing + memory + provenance."""

    def __init__(self, **fields: Any) -> None:
        raise NotImplementedError("Phase 06")


class RunRecord:
    """One invocation of the harness: config snapshot, env.describe(), file results."""

    def __init__(self, **fields: Any) -> None:
        raise NotImplementedError("Phase 06")


def write_jsonl(path: Path, records: Iterable[Any]) -> None:
    """Append records to a JSONL file atomically (see store.py for the atomicity contract)."""
    raise NotImplementedError("Phase 06")


def read_jsonl(path: Path) -> Iterator[Any]:
    """Stream records back out of a JSONL file."""
    raise NotImplementedError("Phase 06")
