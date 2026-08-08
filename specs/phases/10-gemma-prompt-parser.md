# Phase 10 — Gemma prompt + output parser (frozen)

## Status
🔲 todo

## Goal
One prompt and one parser, byte-identical across E2B/E4B/12B, frozen at the end of this phase per D9.

## Context
Phase 03's smoke test verdict decides the output format this phase locks in. If GO, Gemma reliably
emits usable timestamps and the prompt asks for strict JSON turns. If GO-WITH-FALLBACK, timestamps
were absent or unreliable (OQ2) and the prompt instead asks for a fixed-grid per-frame labeling.
Either way, after this phase the prompt and parser never change per variant — a difference in DER
between E2B/E4B/12B must reflect the model, not prompt engineering drift (D9). No per-variant
tuning ever, including in Phases 12-14 if a variant looks bad.

## Scope
### In scope
- `gemma_prompt.py`:
  - `PROMPT: str` — the single frozen prompt template, parameterized only by window duration (for
    the fixed-grid case) or nothing (for the JSON case). No variant name in the template.
  - `parse(raw_text: str, window_seconds: float) -> tuple[list[Turn], ParseFailure | None]` — pure
    function, `str -> list[Turn]`, no model imports, no I/O beyond its arguments.
  - Malformed-output handling, each with its own counted failure mode: markdown code fences around
    JSON, trailing prose before/after the JSON block, truncated/incomplete JSON (cut off mid-object),
    overlapping turns, inverted turns (`end < start`), timestamps outside `[0, window_seconds]`,
    duplicate speaker labels reused inconsistently, completely empty output.
  - `ParseFailure` enum/dataclass recording which failure mode(s) fired, so `parse_failure_rate` can
    be aggregated per variant later (a headline result, not swept into logs).
- Unit tests against saved raw outputs from Phase 03's smoke test — the parser must be exercised
  offline, without loading any model.

### Out of scope
- Windowing and cross-window stitching (Phase 11) — this phase parses a single window's raw text only.
- Calling the model (Phases 12-14). Choosing which failure repair to attempt live at inference time —
  there is none; see Technical Approach.

## Technical Approach
- Never repair by re-prompting. If output is malformed, the parser does its best deterministic
  recovery (strip fences, truncate to last complete JSON object, clamp out-of-window timestamps) and
  otherwise returns an empty turn list plus a recorded `ParseFailure` — it does not call the model
  again. Re-prompting per-variant would silently reintroduce the tuning D9 forbids.
- Recovery order for JSON mode: strip ```json fences → strip leading/trailing prose outside the
  outermost `[...]`/`{...}` → attempt `json.loads` → on failure, try truncating to the last
  syntactically closed array element and re-parse → on failure, record `ParseFailure.UNPARSEABLE`
  and return `[]`.
  Duplicate/inconsistent speaker labels are not silently merged — pass them through as separate
  labels (Hungarian mapping in Phase 16 absorbs label identity anyway) but count the anomaly.
- Fixed-grid mode: parser expects one label per ~1 s frame; construct `Turn`s by merging consecutive
  frames with the same label. A grid response with the wrong frame count is a counted failure
  (`ParseFailure.GRID_LENGTH_MISMATCH`), not silently truncated/padded without recording it.
- Out-of-window and inverted timestamps are clamped/dropped and counted, never used to inflate DER
  silently — a dropped turn is a dropped turn, it just also gets tallied under
  `ParseFailure.INVALID_TIMESPAN`.
- The prompt text itself is decided by the Phase 03 verdict — read `specs/phases/03-gemma-smoke-test.md`
  and its output artifacts before writing `PROMPT`, do not guess.

## Acceptance Criteria
- [ ] `parse()` has zero imports from `transformers`, `torch`, or any model-loading module.
- [ ] Every one of the eight listed malformed-output cases has a dedicated unit test with a saved or
      hand-crafted raw-text fixture, and asserts both the resulting `list[Turn]` and the recorded
      `ParseFailure`.
- [ ] Running `parse()` against every raw output saved during Phase 03's smoke test completes without
      raising, and produces a non-crashing `parse_failure_rate` summary.
- [ ] `PROMPT` contains no variant name, model size, or E2B/E4B/12B-specific instruction.
- [ ] A second read of `gemma_prompt.py` after this phase is marked done requires no further edits in
      Phases 12-14 (grep for edits to this file after Phase 11 — should be empty).

## Test Instructions
```python
from benchmark import gemma_prompt

raw = '```json\n[{"start": 0.0, "end": 2.5, "speaker": "A"}, {"start": 2.0, "end": 4.0, "speaker": "B"}]\n```\nHope that helps!'
turns, failure = gemma_prompt.parse(raw, window_seconds=30.0)
print(turns, failure)

# malformed: truncated mid-object
raw_trunc = '[{"start": 0.0, "end": 2.5, "speaker": "A"}, {"start": 2.0,'
turns, failure = gemma_prompt.parse(raw_trunc, window_seconds=30.0)
print(turns, failure)  # non-empty from the first object, ParseFailure.TRUNCATED recorded

# empty
turns, failure = gemma_prompt.parse("", window_seconds=30.0)
print(turns, failure)  # [], ParseFailure.EMPTY_OUTPUT
```

## Docs Needed
- [ ] Phase 03 smoke-test verdict and saved raw outputs — read before writing `PROMPT`
- [ ] Python `json` module error handling for partial documents

## Notes
