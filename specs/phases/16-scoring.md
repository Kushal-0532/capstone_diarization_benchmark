# Phase 16 — Unified DER scoring

## Status
🔲 todo

## Goal
One scoring function, blind to which system produced a record, computing DER with component
breakdown for every `FileResult` and emitting a tidy dataset for Phases 17-18.

## Context
This is what makes C5 ("identical scoring") structurally true rather than a promise kept by
discipline. If the scorer's function signature cannot express "which system" as an input it reads,
it cannot special-case one — that's the whole point. It consumes only the `FileResult`/`Turn` shape
Phase 06 defined and the excerpt references it built; it has no knowledge of pyannote vs Gemma.

## Scope
### In scope
- `scoring.py`: `score(result: FileResult, reference: Annotation, uem: Timeline) -> ScoreRecord`
  where `ScoreRecord` carries total DER plus miss / false-alarm / confusion components (needed for
  chart V2) and the file/system/dataset/runtime identifiers copied through from `result` — the
  function itself never branches on `result.system_id`.
- Uses `pyannote.metrics.diarization.DiarizationErrorRate(collar=0.25, skip_overlap=False)` (D6),
  called with `uem=` and `detailed=True`.
- Aggregation: `aggregate(records: list[ScoreRecord]) -> per-system-per-dataset totals`, computed as
  **component-weighted totals across files** (`sum(errors) / sum(reference_duration)`), not a mean of
  per-file DERs.
- A tidy per-file DataFrame/JSONL output (`results/scores.jsonl` or equivalent) with one row per
  `(system_id, dataset_id, runtime_id, file_id)`, columns for DER and each component, consumed
  directly by Phase 17 (charts) and Phase 18 (report tables).
- Sanity-check tests: scoring a reference against itself gives DER 0.0; scoring an empty hypothesis
  against a non-empty reference gives `miss=1.0` (proportion of reference time missed) and DER 1.0.

### Out of scope
- Choosing collar/overlap policy — already locked (D6). This phase implements it, does not relitigate it.
- Charting (Phase 17) and report prose (Phase 18) — this phase only emits the tidy scored data they consume.
- Greedy vs Hungarian mapping choice — `DiarizationErrorRate`'s default optimal (Hungarian) mapping is
  used as-is; do not substitute `GreedyDiarizationErrorRate`.

## Technical Approach
- Load `pyannote.metrics.diarization.DiarizationErrorRate` once with `collar=0.25, skip_overlap=False`
  and reuse the instance across all `score()` calls — it's stateless per call but avoids
  re-instantiation overhead across ~100+ file/system/runtime combinations.
- `result.turns` (list of `Turn`) converts to a pyannote `Annotation` via `schema.to_annotation()`
  from Phase 06 — do not hand-roll a second conversion here; there must be exactly one.
- `detailed=True` returns a dict with `diarization error rate`, `miss`, `false alarm`, `confusion`,
  `total` (reference duration) — map these into `ScoreRecord` fields explicitly named, not passed
  through as an opaque dict, so Phase 17/18 code is self-documenting.
- Aggregation bug to avoid: summing per-file DER and dividing by file count is wrong (unweighted mean
  over unequal reference durations). Sum `miss`/`false alarm`/`confusion`/`total` across files first,
  then divide, matching how `pyannote.metrics` itself aggregates internally.
- Note in the report-facing docstring: D6 means these numbers are not directly comparable to
  published DER using `skip_overlap=True` — this phase does not write that caveat into the report
  (Phase 18 does) but the function's docstring should carry it so it isn't lost.

## Acceptance Criteria
- [ ] `score()` takes no `system_id`-conditional branch anywhere in its implementation (grep-verified).
- [ ] Self-scoring test: `score(result_from_reference, reference, uem).der == 0.0` (within floating
      point tolerance).
- [ ] Empty-hypothesis test: scoring a `FileResult` with `turns=[]` against a non-empty reference
      yields `miss == 1.0` (proportion) and `der >= 1.0`.
- [ ] `aggregate()` produces component-weighted totals verified against a hand-computed example with
      two files of unequal reference duration (unweighted mean would give a different, wrong number —
      assert the two differ in the test).
- [ ] Every `FileResult` produced by Phases 09/12/13/14/15 that exists on disk gets a `ScoreRecord` in
      the tidy output — no silent drops.
- [ ] Tidy output loads cleanly as a dataframe with one row per `(system_id, dataset_id, runtime_id,
      file_id)` and no missing DER/component values for any row present.

## Test Instructions
```python
from benchmark import scoring, store, data

recs = list(store.read(store.run_key("pyannote", "ami", "gpu-t4")))
wav, ref, uem = data.excerpt(recs[0].file_id)
sr = scoring.score(recs[0], ref, uem)
print(sr.der, sr.miss, sr.false_alarm, sr.confusion)

# sanity: reference against itself
from benchmark.schema import FileResult, Turn
perfect = FileResult(system_id="oracle", dataset_id="ami", file_id=recs[0].file_id, runtime_id="gpu-t4",
                      turns=[Turn(s.start, s.end, label) for s, _, label in ref.itertracks(yield_label=True)],
                      wall_seconds=0, audio_seconds=300, rtf=0, peak_vram_mb=0, peak_ram_mb=0,
                      model_revision="n/a", lib_versions={}, raw_output_path=None, error=None)
print(scoring.score(perfect, ref, uem).der)  # ~0.0

df = scoring.aggregate([scoring.score(r, *data.excerpt(r.file_id)[1:]) for r in recs])
print(df)
```

## Docs Needed
- [x] pyannote.metrics DiarizationErrorRate detailed output — [../docs/pyannote-audio.md](../docs/pyannote-audio.md)

## Notes
