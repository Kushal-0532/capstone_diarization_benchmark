# Phase 08 — Instrumentation harness (time, VRAM, RAM)

## Status
🔲 todo

## Goal
One system-agnostic context manager that measures wall-clock time, peak VRAM and peak RAM
identically for pyannote and for every Gemma variant.

## Context
G2 and G3. If each runner measured its own timings, the CPU-vs-GPU and cross-system comparisons
would be comparing measurement methodologies as much as systems. One measurement path, used by all
four runners, is the only way the RTF chart (V4) and Pareto chart (V7) mean anything.

## Scope
### In scope
- `instrument.py`: `measure()` context manager yielding a result object with
  `wall_seconds`, `peak_vram_mb`, `peak_ram_mb`.
- GPU: `torch.cuda.reset_peak_memory_stats()` before, `torch.cuda.max_memory_allocated()` +
  `max_memory_reserved()` after, with `torch.cuda.synchronize()` *before* stopping the clock —
  without the sync, async kernel launches make GPU timings fiction.
- CPU RAM: sampling thread on `psutil.Process().memory_info().rss` (~10 Hz) tracking the max, since
  peak RSS is not otherwise observable mid-call.
- A documented boundary for what is measured: **inference only**, excluding model load and audio
  decode; model load time is measured separately and reported as its own number.
- `rtf = wall_seconds / audio_seconds`, computed in exactly one place.

### Out of scope
- Any per-system logic. `instrument.py` must not import any runner.

## Technical Approach
- Excluding model-load from RTF is the decision that makes the metric mean "cost per hour of audio
  in a warm service", which is the Verascope-relevant question. Load time is reported separately
  because for a 12B 4-bit model it is minutes and a real deployment consideration.
- Peak VRAM reported as `max_memory_reserved` (what the GPU actually cannot give back to anything
  else), with `max_memory_allocated` also recorded — the report should say which it plots.
- The RSS sampler must be `daemon=True` and joined in `__exit__`, or a killed session leaks threads.
- On a CPU runtime, VRAM fields are `None`, not `0` — a missing measurement and a zero measurement
  must never be conflated in the charts.

## Acceptance Criteria
- [ ] `measure()` works unchanged on both CPU and GPU runtimes.
- [ ] On GPU, wrapping a known allocation (e.g. a 1 GB tensor) reports peak VRAM within ~10%.
- [ ] On CPU, wrapping a known allocation reports peak RAM within ~10%.
- [ ] Timing a `time.sleep(2)` reports ~2.0 s.
- [ ] GPU timing includes a synchronize — verified by timing an async-heavy op and confirming the
      number does not collapse to near-zero.
- [ ] VRAM fields are `None` (not 0) on CPU runtimes.
- [ ] `instrument.py` imports no runner module.

## Test Instructions
```python
from benchmark.instrument import measure
import torch, time
with measure() as m:
    x = torch.zeros(int(2.5e8), device="cuda")   # ~1 GB fp32
    time.sleep(2)
print(m.wall_seconds, m.peak_vram_mb, m.peak_ram_mb)
# expect ~2.0s, ~1000MB
```

## Docs Needed
- [ ] `torch.cuda` memory stats API — exact semantics of allocated vs reserved

## Notes
