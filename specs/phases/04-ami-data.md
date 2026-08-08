# Phase 04 — AMI subset acquisition

## Status
🔲 todo

## Goal
16 AMI Mix-Headset files on disk with matching RTTM references and UEM files, stratified by speaker
count, downloadable reproducibly from a Colab runtime.

## Context
AMI is one of the two datasets on the pyannote 3.1 model card, so it anchors our baseline against a
published context (with the D4 excerpting caveat). Meeting audio with 4+ speakers is where
diarization gets hard, which makes it the more discriminating of the two datasets.

## Scope
### In scope
- `data.py`: `download_ami(dest)` fetching Mix-Headset WAVs for a fixed, hardcoded file list.
- Reference RTTM + UEM from the `pyannote/AMI-diarization-setup` layout (its "only_words" RTTMs and
  official UEMs — the same references the pyannote model card scores against).
- File selection: 16 files stratified into low (2–3 speakers) and high (4+) buckets by reference
  speaker count, 8 each where AMI's distribution allows. The chosen ids are **hardcoded** in
  `config.py`, not sampled at runtime — reruns must pick the same files (C6).
- Resumable download: skip files already present with the right size; survive session death (C3).
- A manifest row per file: id, path, sha256, duration, reference speaker count.

### Out of scope
- Excerpting and reference parsing (Phase 06 — this phase only acquires raw assets).
- VoxConverse (Phase 05).

## Technical Approach
- Resolve **OQ6** first: confirm a working AMI Mix-Headset mirror and measure total download size
  for 16 files *before* committing to the list. AMI headset-mix WAVs are large; if 16 full files
  blow Colab disk or Drive quota, download only the needed 5-minute byte range if the mirror
  supports HTTP range requests, else download-excerpt-delete one file at a time.
- Get the speaker count for stratification from the RTTMs (cheap, text) before downloading any
  audio — pick the file list first, then fetch only those.
- Store under a Drive-backed path so a runtime restart does not re-download gigabytes (C3).

## Acceptance Criteria
- [ ] 16 AMI ids hardcoded in `config.py`, with the low/high speaker-count split recorded.
- [ ] `download_ami()` fetches audio + RTTM + UEM for all 16 and is idempotent — a second run
      downloads nothing and completes in seconds.
- [ ] Interrupting mid-download and re-running resumes rather than restarting.
- [ ] Manifest lists all 16 with duration and reference speaker count; counts match the intended
      stratification.
- [ ] Total on-disk footprint recorded and within Colab/Drive limits.

## Test Instructions
```python
from benchmark import data
m = data.download_ami()
print(len(m), sum(r["duration"] for r in m)/60, "min")
print(sorted(r["n_speakers"] for r in m))
# interrupt mid-run, re-run: must resume, not restart
```

## Docs Needed
- [ ] `pyannote/AMI-diarization-setup` — RTTM/UEM layout and which RTTM flavour the model card uses

## Notes
<!-- OQ6 answer: mirror URL, total size, range-request support -->
