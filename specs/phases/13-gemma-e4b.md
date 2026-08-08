# Phase 13 — System B2: Gemma E4B runner (GPU)

## Status
🔲 todo

## Goal
E4B-it runs over all 32 excerpts on the T4 using Phase 12's runner unchanged, via a new config entry.

## Context
Pure execution phase. If this phase requires writing or editing any code in `gemma_runner.py`,
`gemma_prompt.py`, or `gemma_chunk.py`, Phase 12's parameterization failed and must be fixed there
— not patched here with a variant-specific branch. The entire point of D9/C5 is that E2B vs E4B vs
12B differences are measured, not manufactured by different code paths.

## Scope
### In scope
- `config.py`: add a `gemma-e4b` entry to the system registry with E4B's model id/revision, dtype,
  and load kwargs. Same shape as the E2B entry from Phase 12.
- Running `gemma_runner.run("ami", "gpu-t4", config.SYSTEMS["gemma-e4b"])` and the VoxConverse
  equivalent, over all 32 excerpts.
- Diff/inspection check confirming zero code changes outside `config.py` since Phase 12.

### Out of scope
- Any change to `gemma_runner.py`, `gemma_prompt.py`, or `gemma_chunk.py`. If one seems needed, stop
  and fix it as a Phase 12 defect, then re-run E2B too so both variants used the identical code.
- 12B / quantization (Phase 14). CPU leg (Phase 15). Scoring (Phase 16).

## Technical Approach
- Copy the E2B config entry, change only model id/revision and dtype if E4B's model card specifies a
  different one.
- Note in the config comment: E4B also carries the ~300M audio encoder (D2), same architecture family
  as E2B — the meaningful architectural split is E2B/E4B vs 12B, not E2B vs E4B.
- Run both datasets (`ami`, `voxconverse`) at `gpu-t4`, same as Phase 12 did for E2B.

## Acceptance Criteria
- [ ] `git diff` (or equivalent file comparison) between the state after Phase 12 and the state after
      this phase touches only `config.py` — verified and noted here, not assumed.
- [ ] All 32 excerpts produce `FileResult` records with non-empty `turns` or explicit `error`.
- [ ] Every record has `wall_seconds`, `rtf`, `peak_vram_mb`, `model_revision`, `runtime_id`,
      `raw_output_path` set, `raw_output_path` resolving to 10 saved raw outputs per excerpt.
- [ ] `parse_failure_rate` computed for the full E4B run and compared side-by-side with E2B's number
      from Phase 12 (recorded in Notes).
- [ ] Killing mid-run and re-running resumes without duplicating records.

## Test Instructions
```python
from benchmark import gemma_runner, store, config

gemma_runner.run("ami", "gpu-t4", config.SYSTEMS["gemma-e4b"])
gemma_runner.run("voxconverse", "gpu-t4", config.SYSTEMS["gemma-e4b"])
recs = list(store.read(store.run_key("gemma-e4b", "ami", "gpu-t4")))
print(len(recs), recs[0].rtf, recs[0].peak_vram_mb, len(recs[0].turns))
```
Expected: 16 records per dataset, RTF and turn-count patterns broadly similar in shape to E2B's
(same architecture family), any accuracy difference attributable to model, not code.

## Docs Needed
- [ ] Gemma 4 model card — E4B-it model id/revision, confirm no getting-started deviation from E2B

## Notes
E2B vs E4B `parse_failure_rate` comparison (fill in once run): TBD.
