# Phase 07 — Checkpoint & resume store

## Status
🔲 todo

## Goal
Any run can die at any moment — planned runtime switch or Colab recycling — and resume from the last
completed file with no duplicated work and no corrupted records.

## Context
C3 is not a nice-to-have: the CPU leg (Phase 15) may run for hours on free Colab, which recycles
sessions. Without this, a 90%-complete run is worth nothing. Building it *before* the runners means
no runner has to grow its own ad-hoc resume logic.

## Scope
### In scope
- `store.py`:
  - `run_key(system_id, dataset_id, runtime_id)` → the JSONL path under `results/`.
  - `completed_file_ids(run_key)` → set, by reading existing JSONL.
  - `append(run_key, FileResult)` — **atomic**: write to a temp file in the same directory, fsync,
    then `os.replace` / append-with-flush, so a kill mid-write can never leave a half-line.
  - `iter_pending(run_key, all_file_ids)` — the resume primitive every runner loops over.
  - `sync_to_drive()` / results path rooted on the mounted Drive.
- A run manifest per run key: env description (Phase 02), config snapshot (collar, excerpt length,
  seed, model revision), started/updated timestamps.
- Config-drift guard: if an existing run's manifest disagrees with current `config.py` on any
  scoring-relevant value, **refuse to append** and tell the user to start a new run key. This is the
  mechanism that enforces C5 across sessions.

### Out of scope
- Running anything. Charting/reporting.

## Technical Approach
- JSONL over a database: append-only, human-readable, greppable, and trivially resumable — a partial
  file is still valid data. `ponytail: JSONL not sqlite; revisit only if record count outgrows a
  linear scan, which at 32 files × 4 systems × 2 runtimes it never will.`
- Write directly to the Drive-mounted path, flushing per record. Drive's FUSE layer is slow but the
  write volume is tiny, and buffering is exactly what loses data when a session is killed.
- Errors are records too: a failed file writes a `FileResult` with `error` set and `turns=[]`, so
  resume does not retry it forever and the report can count failures honestly.

## Acceptance Criteria
- [ ] `append()` then simulated kill (`SIGKILL` mid-loop) leaves a JSONL where every line parses.
- [ ] `completed_file_ids()` after that kill returns exactly the files fully written.
- [ ] Re-running the loop processes only the pending files.
- [ ] Changing `COLLAR` in config and re-running against an existing run key raises a clear
      config-drift error instead of appending.
- [ ] Records survive a Colab runtime restart (write on GPU runtime, read on CPU runtime).
- [ ] A file that raises during processing produces an `error` record and is not retried on resume.

## Test Instructions
```python
from benchmark import store, schema
k = store.run_key("pyannote", "ami", "gpu-t4")
for fid in store.iter_pending(k, all_ids):
    store.append(k, schema.FileResult(file_id=fid, ...))
# kill the kernel mid-loop, restart, re-run the same cell:
print(len(store.completed_file_ids(k)))   # monotonically increases, never resets
```

## Docs Needed
- [ ] None — stdlib file semantics.

## Notes
