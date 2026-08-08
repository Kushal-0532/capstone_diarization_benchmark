# Phase 09 — System A: pyannote runner (GPU)

## Status
🔲 todo

## Goal
`pyannote/speaker-diarization-3.1` runs over all 32 excerpts on the T4, writing instrumented
`FileResult` records through the checkpoint store.

## Context
This is the baseline — Verascope's current production stage — and the first real end-to-end use of
Phases 06–08. Getting it working validates the whole record/checkpoint/instrument spine before the
much harder Gemma runners depend on it.

## Scope
### In scope
- `pyannote_runner.py`: `run(dataset_id, runtime_id)` looping `store.iter_pending(...)`, calling the
  pipeline inside `instrument.measure()`, converting output to `list[Turn]`, appending a record.
- Pipeline loaded once outside the per-file loop and reused (model load is not part of RTF, Phase 08),
  with load time recorded once into the run manifest.
- `pipeline.to(torch.device("cuda"))` on the GPU leg; device comes from config, not hardcoded.
- Output conversion: whichever return type OQ5 established — `Annotation.itertracks(yield_label=True)`
  for 3.1.x — into `Turn(start, end, speaker)`.
- The pinned model revision SHA (Phase 02) passed explicitly, so a silent upstream update cannot
  change results between reruns (C6).

### Out of scope
- CPU leg (Phase 15). Scoring (Phase 16). Any tuning of pyannote hyper-parameters — stock pipeline,
  as Verascope runs it.

## Technical Approach
- Use the OQ5 answer for the exact kwarg (`token=` vs `use_auth_token=`) and return type. Upstream
  has changed both since 3.1; do not code from memory or from the newest docs.
- Do **not** pass `num_speakers` or `min/max_speakers`. Gemma will not be given the speaker count
  either, so giving it to pyannote would be an unfair advantage. Record this choice — it costs
  pyannote some DER versus its published numbers, and the report must say so.
- Feed the Phase 06 excerpt WAV path, so pyannote and Gemma consume byte-identical audio.
- Seed torch/numpy/random from `config.SEED` before the loop.

## Acceptance Criteria
- [ ] All 32 excerpts produce records in `results/` with non-empty `turns`.
- [ ] Every record has `wall_seconds`, `rtf`, `peak_vram_mb`, `model_revision`, `runtime_id` set.
- [ ] Killing mid-run and re-running resumes and does not duplicate records.
- [ ] Spot-check DER on 2–3 AMI files lands in a plausible range (roughly 10–25% given no speaker
      count hint, overlap scored, and 5-minute excerpts). Wildly off (e.g. >50%) means a reference
      alignment bug in Phase 06 — stop and fix rather than proceeding.
- [ ] No speaker-count hints passed to the pipeline (verify by reading the call site).

## Test Instructions
```python
from benchmark import pyannote_runner, store
pyannote_runner.run("ami", "gpu-t4")
recs = list(store.read(store.run_key("pyannote", "ami", "gpu-t4")))
print(len(recs), recs[0].rtf, recs[0].peak_vram_mb, len(recs[0].turns))
```
Expected: 16 records, RTF well under 0.1 on a T4, plausible turn counts (tens per 5 min).

## Docs Needed
- [x] pyannote.audio Pipeline API — [../docs/pyannote-audio.md](../docs/pyannote-audio.md)
- [ ] Confirm against the *installed* 3.1.x version (OQ5), not upstream main

## Notes
