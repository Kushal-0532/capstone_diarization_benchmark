# Phase 18 — report.py — Markdown report generation

## Status
🔲 todo

## Goal
Generate `results/report.md` entirely from data — methodology, results tables, all charts, parse
failure rates, and failure-case examples — never hand-edited.

## Context
The report is the citable deliverable (SPEC.md Overview). Every number in it must be traceable to a
`FileResult`/`ScoreRecord` on disk, not typed in by hand, so a rerun after a dependency bump
regenerates the same document structure with new numbers (G7). This phase must also degrade
gracefully: 12B may be blocked (Phase 14's ⛔ outcome) and the CPU leg may not have completed (Phase
15) — the report states that plainly rather than crashing or silently omitting the section.

## Scope
### In scope
- `report.py`: `generate(out_path="results/report.md") -> Path`, assembling:
  - **Methodology section**, stating: collar=0.25/skip_overlap=False policy and that this differs
    from many published skip_overlap=True numbers (D6); the 5-minute excerpting caveat and that our
    pyannote numbers are not directly comparable to published full-file model-card DER (D4); the
    greedy-decoding deviation from the model card's recommended sampling preset (D8); the D1 framing
    that diarization is an unadvertised Gemma capability, not a claimed one.
  - **Results tables**: DER + RTF + peak VRAM/RAM per system × dataset × runtime, CPU and GPU columns
    side by side in one table (not two separate tables the reader has to cross-reference).
  - **All V1-V9 charts embedded** as Markdown image links to the PNGs Phase 17 produced.
  - **Parse-failure rates per Gemma variant** (E2B/E4B/12B), pulled from the `raw_output_path` /
    `ParseFailure` data recorded in Phases 12-14.
  - **2-3 concrete failure cases per system**: reference turns vs predicted turns, the V9 timeline
    plot for that case, and the raw Gemma output quoted verbatim (for Gemma systems) or a brief note
    on what pyannote got wrong (for the pyannote system).
- Graceful degradation: any system/runtime combination with no data (12B blocked, CPU leg incomplete)
  renders a "not available" note stating the reason (cite the blocking phase/OQ), not a blank cell,
  not a crash.

### Out of scope
- Computing DER/RTF/memory (Phase 16) or drawing charts (Phase 17) — this phase only assembles their
  outputs into prose and Markdown tables.
- The recommendation write-up (Phase 19) — this phase's methodology/results sections are inputs to it,
  but the recommendation itself is appended separately.

## Technical Approach
- Read Phase 16's tidy scored data and Phase 17's chart paths as the only two data sources; do not
  recompute DER or redraw charts inline in `report.py`.
- Missing-data check happens per section: before rendering a system/runtime's table row or failure
  case, check whether records exist; if not, render `*(not available — see Phase 14, blocked by OQ3)*`
  or the CPU-leg equivalent, sourced from a small lookup of known blockers rather than a generic
  "no data" string, so the reader knows why.
- Failure-case selection: pick the highest per-file DER example(s) per system from Phase 16's tidy
  data, or a case with a notable `ParseFailure` for Gemma systems, and pass the `(file_id, system_id)`
  pairs into Phase 17's V9 function to render that case's timeline.
- Assemble as a plain Python string-building / Jinja-style template — whichever, but the function must
  be idempotent: running it twice with the same underlying data produces byte-identical output (aside
  from a timestamp header line, if included).
- Table formatting: use Markdown pipe tables generated from the tidy DataFrame (e.g.
  `df.to_markdown()`), not hand-formatted strings, so column alignment can't drift from the data.

## Acceptance Criteria
- [ ] `generate()` produces `results/report.md` containing all four named sections (methodology,
      results tables, embedded charts, failure cases) plus the parse-failure-rate section.
- [ ] Methodology section explicitly states the collar/overlap policy and skip_overlap comparability
      caveat, the excerpting caveat (D4), the greedy-decoding deviation (D8), and the D1 unadvertised-
      capability framing — grep-verifiable by keyword presence, not just "a methodology section exists".
- [ ] Running `generate()` against a dataset missing the 12B system (simulate Phase 14's ⛔ outcome)
      produces a report with an explicit "not available, see Phase 14" note in the relevant table
      cells and failure-case slot, and does not raise.
- [ ] Running `generate()` against a dataset missing the CPU leg entirely produces the GPU-only tables
      correctly and an explicit "CPU leg not available" note, without raising.
- [ ] All nine chart PNGs referenced in the report resolve to files that actually exist on disk at
      generation time.
- [ ] Each of the 2-3 failure cases per available system includes reference vs predicted turns, an
      embedded V9 image link, and (for Gemma systems) the raw quoted model output.

## Test Instructions
```python
from benchmark import report

path = report.generate("results/report.md")
text = path.read_text()
assert "skip_overlap" in text
assert "D4" in text or "5-minute" in text or "5 minute" in text
assert "unadvertised" in text
print(len(text), "chars written")

# missing-system degrade path
import shutil
shutil.move("results/gemma-12b.jsonl", "/tmp/gemma-12b.jsonl.bak")
path2 = report.generate("results/report_no12b.md")
assert "not available" in path2.read_text()
shutil.move("/tmp/gemma-12b.jsonl.bak", "results/gemma-12b.jsonl")
```

## Docs Needed
- [ ] pandas `DataFrame.to_markdown()` (tabulate dependency) for results tables

## Notes
