# Phase 05 — VoxConverse subset acquisition

## Status
🔲 todo

## Goal
16 VoxConverse test files on disk with matching RTTM references, stratified by speaker count, via
the same resumable path as Phase 04.

## Context
VoxConverse is real-world YouTube audio — noisier, more acoustically varied, and the second dataset
on the pyannote 3.1 model card. Pairing it with AMI's clean meeting audio separates "this system is
bad at diarization" from "this system is bad at messy audio", which matters directly for Verascope,
whose inputs are internet video.

## Scope
### In scope
- `data.py`: `download_voxconverse(dest)` — audio + RTTM for a hardcoded 16-file list from the
  VoxConverse **test** split.
- Same stratification (low 2–3 / high 4+ speakers), same hardcoded-ids rule, same resumability and
  manifest shape as Phase 04.
- UEM: VoxConverse ships no official UEM. Synthesize one per file spanning the full excerpt window
  and record that this is a synthesized UEM — it must be applied identically to all four systems
  (C5), and the report must state it.

### Out of scope
- Excerpting/reference parsing (Phase 06). AMI (Phase 04).

## Technical Approach
- Reuse the Phase 04 download/resume/manifest helpers; only the source URLs and the RTTM parsing
  entry point differ. If the two functions diverge by more than their URLs, factor the shared part
  out rather than duplicating.
- Speaker counts again come from RTTM before audio download.
- Prefer the official VoxConverse RTTM repo release matching the test split; pin the release tag.

## Acceptance Criteria
- [ ] 16 VoxConverse test ids hardcoded in `config.py` with the speaker-count split recorded.
- [ ] `download_voxconverse()` is idempotent and resumable, same as Phase 04.
- [ ] Manifest shape is **identical** to AMI's — downstream code must not branch on dataset.
- [ ] Synthesized-UEM decision recorded in Notes with its justification.
- [ ] Combined AMI + VoxConverse audio ≈ 2.5–3 h at 5-minute excerpts (D5 sanity check).

## Test Instructions
```python
from benchmark import data
m = data.download_voxconverse()
assert set(m[0]) == set(data.download_ami()[0])   # identical manifest schema
print(len(m), sorted(r["n_speakers"] for r in m))
```

## Docs Needed
- [ ] VoxConverse RTTM release — split layout and pinned tag

## Notes
