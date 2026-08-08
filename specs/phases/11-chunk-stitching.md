# Phase 11 — Windowing + cross-window speaker stitching

## Status
🔲 todo

## Goal
Split each 5-minute excerpt into Gemma-sized windows, run one stitching strategy chosen by
measurement, and emit file-relative `Turn`s that are directly scoreable.

## Context
**This is the hardest phase in the project — flag it as such and budget accordingly.** C1 caps
Gemma audio at 30 s; excerpts are 300 s, so 10 windows per file. Window-local speaker labels are
not comparable across windows — window 2's "Speaker A" may be window 1's "Speaker B" — and Gemma
exposes no speaker embeddings (OQ1), so there is no principled linking signal. Whatever this phase
picks must be applied identically to all three Gemma variants (D9, C5); a stitching strategy that
only works for one variant invalidates the cross-variant comparison before it starts.

## Scope
### In scope
- `gemma_chunk.py`:
  - `window(excerpt_seconds=300, window_seconds=30, hop_seconds=...) -> list[(t0, t1)]` — window
    boundaries in file-relative seconds.
  - `stitch(window_results: list[list[Turn]], boundaries: list[(t0, t1)]) -> list[Turn]` — the chosen
    strategy, converting window-relative timestamps to file-relative and reconciling labels.
  - Turn merging across a boundary: if the same (stitched) speaker has turns ending at one window's
    edge and starting at the next window's edge within a small gap tolerance, merge into one turn
    rather than leaving an artificial split.
- Candidate strategies, implemented and compared on a small dev subset (2-3 files):
  - (a) **Naive concatenation, no linking** — labels stay window-local (`w0_A`, `w1_A`, ...
    never merged). This is the honest null / floor-of-badness baseline and must be reported even if
    not chosen.
  - (b) **Overlapping windows** (e.g. 30 s window / 5 s hop) — use the shared audio region between
    adjacent windows to align labels by comparing turns predicted in the overlap.
  - (c) **Context-in-prompt** — feed the previous window's turns as text context in the next window's
    prompt, encouraging the model to reuse the same label strings. Note: this changes what is fed to
    the model between windows, so it must still route through the one frozen prompt template from
    Phase 10 (a context block appended to the same `PROMPT`, not a second prompt).
- Comparison harness: run all implemented strategies over the dev subset, score each with Phase 16's
  scorer (or a temporary standalone DER call if Phase 16 isn't done yet), and record DER per strategy.
- Picking one strategy and wiring it into `stitch()` as the only path used by Phases 12-14.

### Out of scope
- Building new prompt variants beyond what (c) requires — the prompt template itself is frozen
  (Phase 10, D9).
- Full-dataset runs (Phases 12-14 do that, using whichever strategy this phase picks).
- Any per-variant stitching logic. One stitcher, all three variants.

## Technical Approach
- Window-relative to file-relative conversion is `t_file = t_window + boundary[i][0]`, applied before
  any merge/stitch logic runs — do this first so downstream code only ever sees file-relative time.
- For strategy (b), overlap alignment needs a similarity heuristic since there's no embedding: compare
  turn count and rough time alignment of labels active in the shared region, and remap the later
  window's labels to the earlier window's via a greedy or Hungarian match on overlap-region time
  coverage. This is a weak signal — expect it to only partially work, and say so in Notes.
- For strategy (c), keep the context block short (prior window's turns as compact text, not full
  audio) — it must not push the prompt near a length that risks truncation on top of C1's audio cap.
- Boundary merge tolerance: pick a small gap (e.g. ≤0.5 s) below which two same-speaker turns
  straddling a boundary are merged into one; do not merge across a silence gap that's part of the
  reference.
- Keep the dev subset separate from the 16+16 file benchmark set so the strategy choice isn't fit to
  the exact files that will be scored later.

## Acceptance Criteria
- [ ] `window()` covers `[0, 300)` with no gaps for the chosen `window_seconds`/`hop_seconds`.
- [ ] All three candidate strategies run end-to-end on the 2-3 dev-subset files and produce a DER
      number each (via Phase 16's scorer or an inline equivalent).
- [ ] The chosen strategy is wired as the only path in `stitch()`; the other two remain in the module
      (or a clearly marked experiments location) but are not called by Phases 12-14.
- [ ] `stitch()` output for a dev file has turns spanning `[0, 300)` file-relative, monotonically
      sane (no turn starting before a prior turn from the same speaker ends by more than the merge
      tolerance allows without being merged).
- [ ] The comparison numbers (DER per strategy, on which files) are recorded in Notes below before
      this phase is marked done.
- [ ] `stitch()` is identical code regardless of which Gemma variant produced `window_results` — no
      variant branching inside this module (D9/C5).

## Test Instructions
```python
from benchmark import gemma_chunk

boundaries = gemma_chunk.window(excerpt_seconds=300, window_seconds=30, hop_seconds=30)
print(len(boundaries), boundaries[0], boundaries[-1])

# fake per-window turns from a smoke run, then stitch
from benchmark.schema import Turn
window_results = [[Turn(0.0, 5.0, "A"), Turn(5.0, 12.0, "B")], [Turn(1.0, 9.0, "A"), Turn(9.0, 20.0, "B")]]
turns = gemma_chunk.stitch(window_results, boundaries[:2])
print(turns)  # file-relative, second window's times shifted by +30
```

## Docs Needed
- [ ] Phase 10's `parse()` output shape — `stitch()` consumes `list[Turn]` per window directly
- [ ] pyannote.metrics DER call signature, if used for the strategy comparison ahead of Phase 16

## Notes
Strategy comparison results (fill in once run):
- (a) naive concatenation — DER on dev subset: TBD
- (b) overlapping windows — DER on dev subset: TBD
- (c) context-in-prompt — DER on dev subset: TBD
- Chosen strategy: TBD, with justification.
