# Phase 19 — Recommendation write-up

## Status
🔲 todo

## Goal
A numbers-backed recommendation appended to `results/report.md`, answering G6's two questions
directly, with honest limitations and no smoothed-over architecture confound.

## Context
This is the final human-judgment deliverable — the one section of the project that is written, not
generated, because it requires weighing tradeoffs Phase 18's tables only lay out. It must not present
E2B → E4B → 12B as a clean size ladder: per D2, E2B/E4B carry ~300M audio encoders while 12B Unified
is encoder-free, so any quality difference between 12B and the other two conflates architecture with
scale. It must also be honest about what the 30s-window stitching penalty (Phase 11) does to Gemma's
numbers for reasons that have nothing to do with its diarization ability.

## Scope
### In scope
- Answer to G6(a): for Verascope's diarization stage — keep pyannote, switch to a Gemma variant, or a
  hybrid (e.g. Gemma E2B as a fast first pass + pyannote for final accuracy) — backed by specific DER/
  RTF/memory numbers from Phase 18's tables, not qualitative impressions.
- Answer to G6(b): does diarization quality plateau below 12B — is E2B or E4B "good enough" to make
  12B's extra compute (and quantization complexity, per Phase 14) not worth it for this task — again
  backed by numbers, and explicitly framed as an architecture comparison (encoder vs encoder-free),
  not a parameter-count curve.
- A **limitations section**, stated plainly, covering: 5-minute excerpts (D4) and their non-
  comparability to published full-file DER; 16 files per dataset (D5) as a small sample; single seed
  (C6) — no variance estimate across seeds; the 30s-window stitching strategy (Phase 11) as a
  methodological confound that handicaps Gemma for reasons architectural to the 30s audio cap (C1)
  rather than about its diarization ability per se; the D1 framing that this benchmarks an
  unadvertised capability, so a negative result says less about Gemma's ceiling than about what it
  was tuned for.
- A **"what would change this answer" section**: concrete conditions under which the recommendation
  should be revisited — e.g. a future Gemma release lifting the 30s audio cap (removing the stitching
  confound entirely), a larger sample size, or quantization improvements changing 12B's Phase 14
  outcome.

### Out of scope
- Any new measurement, chart, or scoring run — this phase only interprets Phase 16-18's existing
  numbers. If a needed number doesn't exist, that's a gap to state, not a reason to go back and
  measure it here.
- Regenerating `report.md`'s methodology/results/charts sections — this phase appends to that file,
  it does not rebuild it (Phase 18 owns generation; this phase's text is appended, ideally by a
  clearly marked function in `report.py` so a rerun doesn't clobber the hand-written recommendation).

## Technical Approach
- Pull the specific DER/RTF/VRAM numbers this write-up cites directly from `results/scores.jsonl` /
  `results/report.md`'s tables at the time of writing — quote actual figures, not placeholders, once
  Phases 09-18 have real data.
- Structure the hybrid option (G6a) concretely: what would trigger falling back to pyannote (e.g. a
  file where Gemma's parse-failure rate spikes, or a speaker count above what Gemma handled well in
  V3), not just "hybrid" as an abstract idea.
- For G6b, explicitly separate two comparisons that are easy to conflate: (i) E2B vs E4B — same
  architecture, different scale, a legitimate scaling comparison; (ii) E4B vs 12B — different
  architecture (encoder vs encoder-free) as well as different scale, not a clean comparison. State
  which one actually supports a "plateau" claim.
- If Phase 14 hit its ⛔ blocker (12B never ran), this section must say so plainly and answer G6b as
  "cannot be answered for 12B on free-tier hardware — here is what we know about E2B vs E4B only,"
  not paper over the gap.
- Write this as prose with inline numbers, not a template with `{{blanks}}` — it is the one generated-
  report section that is deliberately authored, per the phase's own Goal.

## Acceptance Criteria
- [ ] G6(a) answer states a specific recommendation (keep / switch / hybrid) and cites at least one
      DER number, one RTF number, and one memory number from Phase 18's tables in support.
- [ ] G6(b) answer explicitly distinguishes the E2B-vs-E4B (same architecture) comparison from the
      E4B-vs-12B (cross-architecture) comparison, and does not describe E2B→E4B→12B as a single
      scaling curve anywhere in the text.
- [ ] Limitations section names all five items listed in Scope (excerpting, sample size, single seed,
      stitching confound, unadvertised-capability framing) — grep-verifiable by keyword.
- [ ] "What would change this answer" section lists at least the 30s-audio-cap-lifted scenario by name.
- [ ] If Phase 14 recorded a ⛔ blocker, this section states that explicitly and does not claim a
      12B-inclusive answer to G6(b).
- [ ] The write-up is appended to `results/report.md` without altering or duplicating Phase 18's
      generated sections (verified by diffing the file before/after appending).

## Test Instructions
```python
from benchmark import report

# Phase 18's generate() must already have run and produced results/report.md
before = open("results/report.md").read()
report.append_recommendation("results/report.md")  # or equivalent entry point
after = open("results/report.md").read()

assert after.startswith(before)  # pure append, generated sections untouched
assert "hybrid" in after.lower() or "keep pyannote" in after.lower() or "switch" in after.lower()
assert "encoder" in after.lower()  # G6b architecture framing present
assert "single seed" in after.lower()
assert "30" in after and "second" in after.lower()  # stitching/audio-cap confound named
```

## Docs Needed
- [ ] None beyond this project's own Phase 16-18 outputs — this phase is interpretation, not new API surface.

## Notes
