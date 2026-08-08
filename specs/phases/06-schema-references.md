# Phase 06 — Turn schema + excerpting + UEM references

## Status
🔲 todo

## Goal
One canonical `Turn`/`FileResult` record shape, plus deterministic 5-minute excerpting that
produces perfectly aligned audio, reference `Annotation` and UEM for every file in both datasets.

## Context
This phase is what makes C5 ("identical scoring") structurally true rather than a promise. If every
system emits the same record shape and every reference is built by one function, DER cannot drift
between systems — scoring code never learns which system produced a record.

## Scope
### In scope
- `schema.py`:
  - `Turn(start: float, end: float, speaker: str)` — seconds, file-relative.
  - `FileResult(system_id, dataset_id, file_id, runtime_id, turns: list[Turn], wall_seconds,
    audio_seconds, rtf, peak_vram_mb, peak_ram_mb, model_revision, lib_versions, raw_output_path,
    error)`.
  - JSONL read/write, one `FileResult` per line; `to_annotation(FileResult) -> pyannote.core.Annotation`.
- `data.py` excerpting: `excerpt(file_id) -> (wav_path, reference: Annotation, uem: Timeline)`.
  - Deterministic window: `EXCERPT_SECONDS` (300) starting at the first annotated speech onset,
    floored to a whole second. No randomness (C6).
  - Audio cut to mono 16 kHz float32 ∈ [-1, 1] once, here, so **every** system consumes byte-identical
    audio. Resample with a Fourier method (`scipy.signal.resample`) per the model card.
  - Reference RTTM cropped to the window and time-shifted to start at 0.
  - UEM cropped identically; AMI's official UEM intersected with the window, VoxConverse's
    synthesized UEM set to the window.
- Round-trip test: `Annotation -> FileResult -> JSONL -> FileResult -> Annotation` is lossless.

### Out of scope
- Running any system. Computing DER (Phase 16) — this phase only builds the inputs it will consume.

## Technical Approach
- `Turn` is deliberately minimal: no confidence, no embedding, no text. Gemma emits text; it is
  discarded here, at the boundary, so it can never leak into scoring (non-goal: ASR quality).
- Speaker labels are opaque strings. Cross-system label agreement is *not* required — Hungarian
  mapping in Phase 16 handles it (D6). Do not try to normalize labels here.
- Cropping: `Annotation.crop(Segment(t0, t1), mode="intersection")` then shift by `-t0`. Verify
  shifting is applied to the UEM too, or every system silently mis-scores identically-but-wrongly.
- Cache excerpts to Drive keyed by `(file_id, EXCERPT_SECONDS)` — recomputing them each session is
  wasted minutes (C3).

## Acceptance Criteria
- [ ] `excerpt()` returns audio whose duration is 300 s ± one frame for all 32 files.
- [ ] Reference and UEM both start at 0 and end at ≤300 for all 32 files.
- [ ] Excerpt audio is verified mono, 16 kHz, float32, `max(abs(x)) <= 1.0`.
- [ ] Round-trip `Annotation → FileResult → JSONL → Annotation` is exactly equal.
- [ ] Re-running `excerpt()` on the same file yields a byte-identical WAV (determinism).
- [ ] Every excerpt contains ≥2 reference speakers (a single-speaker excerpt makes DER meaningless —
      if one occurs, shift that file's window and record the exception).

## Test Instructions
```python
from benchmark import data, schema
wav, ref, uem = data.excerpt("AMI/ES2004a")
print(ref.labels(), ref.get_timeline().extent(), uem.extent())
import soundfile as sf; x, sr = sf.read(wav); print(sr, x.ndim, x.shape[0]/sr, abs(x).max())
# determinism
import hashlib; h = lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest()
assert h(wav) == h(data.excerpt("AMI/ES2004a")[0])
```

## Docs Needed
- [x] pyannote.core Annotation/Timeline crop semantics —
      [../docs/pyannote-audio.md](../docs/pyannote-audio.md)

## Notes
