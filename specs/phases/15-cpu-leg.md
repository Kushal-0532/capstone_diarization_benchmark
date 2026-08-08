# Phase 15 — CPU leg: all four systems, timing subset

## Status
🔲 todo

## Goal
Measure wall-clock time and peak RAM for all four systems on a Colab CPU runtime, on a reduced
subset, and resolve OQ4 (whether any CPU path exists for Gemma).

## Context
Per D3, this leg measures speed and memory only — not DER. Greedy decoding (D8) makes model output
hardware-independent given identical weights, so a second full DER pass on CPU buys nothing but
burnt free-tier hours; DER already comes from the GPU leg (Phases 09, 12-14). Colab's free CPU
runtime is roughly 2 vCPU / 13GB RAM, which may make 12B infeasible at any quantization — that is a
result to report, not a failure to hide. Reaching a CPU runtime requires a restart (C3); Phase 07's
checkpoint store is what makes that survivable mid-benchmark.

## Scope
### In scope
- A reduced subset: 3-4 files (not all 32), since only timing/memory is needed here.
- pyannote on CPU: same `pyannote_runner.py` from Phase 09, `runtime_id="cpu"`, `pipeline.to("cpu")`.
- Gemma E2B/E4B on CPU: same `gemma_runner.py` from Phase 12, `runtime_id="cpu"`, CPU device map.
- Gemma 12B on CPU: attempt via whichever quant path is feasible on CPU (see Technical Approach) —
  document as infeasible if 13GB RAM cannot hold it at any quantization tried.
- OQ4 investigation: is GGUF/llama.cpp a viable audio-capable path for this architecture, or does the
  CPU leg fall back to `transformers` on CPU (slow but honest)?
- Divergence check: for the shared subset, compare CPU-leg raw outputs/turns against the GPU-leg
  outputs for the same files, and report any divergence explicitly — do not average it into a single
  number that hides it.
- Runtime restart procedure using Phase 07's checkpoint/resume so the CPU leg can be run as a
  separate Colab session without losing GPU-leg results.

### Out of scope
- Scoring DER on CPU-leg output (D3 — GPU leg is authoritative for DER).
- Running the full 32-file set on CPU — timing subset only.
- Any new prompt/parser/stitching code — reuse Phases 10/11 unchanged.

## Technical Approach
- Investigate GGUF/llama.cpp audio support for `gemma4_unified`/the E2B/E4B encoder architecture
  first; if no verified audio-capable build exists, fall back to `transformers` CPU inference using
  the exact same `gemma_runner.py` with `device_map="cpu"`, `torch_dtype=torch.float32` (no bf16/fp16
  benefit on CPU).
- For 12B on CPU: try 4-bit NF4 via bitsandbytes CPU support if available, otherwise document that
  bitsandbytes requires CUDA and 12B has no CPU path at all — that's a legitimate OQ4 answer.
- Record `lib_versions` and `runtime_id="cpu"` on every record so Phase 18 can render CPU vs GPU
  side-by-side without ambiguity (C6).
- Divergence comparison: for the shared subset, diff parsed `Turn` lists (not raw text, which will
  differ trivially in whitespace) between the CPU run and the GPU run for the same file/system;
  report turn-count and rough time-alignment differences, keyed by whether the CPU quant path (e.g.
  GGUF Q4) differs from the GPU quant path (bnb NF4, Phase 14) — expect more divergence for 12B than
  for E2B/E4B if their CPU/GPU quant paths differ.

## Acceptance Criteria
- [ ] pyannote and Gemma E2B/E4B each produce CPU-leg `FileResult` records for the 3-4 file subset,
      with `wall_seconds`, `rtf`, `peak_ram_mb`, `runtime_id="cpu"` set.
- [ ] 12B CPU attempt is either: records produced with peak RAM figures, or a documented infeasibility
      finding in Notes (which quant paths were tried and why each failed/was unavailable) — not silent
      omission.
- [ ] OQ4 answered explicitly in Notes: GGUF/llama.cpp audio support verified working / verified
      unsupported / untested-because-X, with the fallback path actually used stated.
- [ ] Divergence report: for every file/system pair present in both CPU and GPU legs, a written
      comparison of parsed turns exists (even if "no meaningful divergence") — not silently skipped.
- [ ] A restart from GPU runtime to CPU runtime was actually exercised, and `store.iter_pending`
      correctly picked up only the CPU-leg subset without re-running or duplicating GPU-leg work.

## Test Instructions
```python
from benchmark import pyannote_runner, gemma_runner, store, config

pyannote_runner.run("ami", "cpu")
gemma_runner.run("ami", "cpu", config.SYSTEMS["gemma-e2b"])
gemma_runner.run("ami", "cpu", config.SYSTEMS["gemma-e4b"])
# 12b attempt guarded by whatever quant path Notes records as feasible, else skipped with a logged reason

recs = list(store.read(store.run_key("pyannote", "ami", "cpu")))
print(len(recs), recs[0].rtf, recs[0].peak_ram_mb)

# divergence check against the GPU leg for the same files
gpu_recs = list(store.read(store.run_key("pyannote", "ami", "gpu-t4")))
cpu_ids = {r.file_id for r in recs}
for g in gpu_recs:
    if g.file_id in cpu_ids:
        c = next(r for r in recs if r.file_id == g.file_id)
        print(g.file_id, len(g.turns), len(c.turns))
```
Expected: 3-4 records per system, CPU RTF well above GPU RTF, turn counts for pyannote (deterministic,
no quantization) matching almost exactly between CPU and GPU; Gemma variants matching closely unless
a differing CPU/GPU quant path is in play.

## Docs Needed
- [ ] llama.cpp multimodal/audio support status for the relevant architecture (verify, don't assume)
- [ ] bitsandbytes CPU support status, if attempting 12B CPU quantization

## Notes
OQ4 answer (fill in once investigated): TBD.
12B CPU feasibility: TBD.
Divergence summary (CPU vs GPU, per system): TBD.
