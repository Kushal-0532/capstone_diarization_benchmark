# Phase 12 — System B1: Gemma E2B runner (GPU)

## Status
🔲 todo

## Goal
`gemma_runner.py` built once, parameterized by config, running E2B-it over all 32 excerpts on the T4.

## Context
This is the first live Gemma run and the phase that builds the runner Phases 13-14 reuse unchanged.
Getting the config parameterization right here is what makes 13/14 execution-only — if the runner
needs new code paths for E4B or 12B, the cross-variant comparison stops being apples-to-apples (D9,
C5). Everything upstream (Phase 10's prompt/parser, Phase 11's windowing/stitching) is variant-
agnostic already; this phase just wires a model into it.

## Scope
### In scope
- `gemma_runner.py`: `run(dataset_id, runtime_id, variant_config)` looping `store.iter_pending(...)`,
  windowing each excerpt via `gemma_chunk.window()`, running one `instrument.measure()`-wrapped
  inference call per window, parsing raw text via `gemma_prompt.parse()`, stitching via
  `gemma_chunk.stitch()`, appending one `FileResult` per file.
- Model load: `AutoProcessor` + `AutoModelForMultimodalLM` per the Gemma 4 model card, loaded once
  outside the loop, `.to("cuda")`, `torch_dtype` per config.
- Inference call: greedy decoding (`do_sample=False`, D8), thinking disabled, audio content placed
  **after** text in the message content list (model card modality-order requirement — flag this in
  code comments, it is easy to get backwards and silently degrades output without erroring).
- Raw model text saved to `raw_output_path` for **every window**, not just failures — needed for
  Phase 18's failure-case analysis and for `parse_failure_rate` stats.
- `variant_config` entry for E2B: model id/revision, dtype, any variant-specific load kwargs, kept in
  `config.py`'s system registry (per the architecture tree), not hardcoded in `gemma_runner.py`.
- Note in code/docs: E2B has a ~300M audio encoder (D2) — it is not encoder-free, unlike 12B.

### Out of scope
- E4B, 12B execution (Phases 13, 14) — same code, different config only.
- Quantization (Phase 14 territory, though the runner's dtype/quant hook must exist so 14 doesn't
  need new code paths — see Technical Approach).
- CPU leg (Phase 15). Scoring (Phase 16).

## Technical Approach
- Design `variant_config` up front to carry everything Phase 14 will need (a `quantization_config`
  field, even if `None` for E2B/E4B) so adding 12B is a config entry, not a code change.
- Per-window inference: build the message content list with text first, audio second — verify this
  against the model card's actual example, don't assume the natural order.
- Seed torch/numpy/random from `config.SEED` before the loop (C6).
- Model load time recorded once into the run manifest, not counted in per-file RTF (consistent with
  Phase 09's pyannote runner).
- `instrument.measure()` wraps only the `model.generate(...)` call per window, not parsing/stitching,
  so RTF reflects model compute.

## Acceptance Criteria
- [ ] All 32 excerpts produce `FileResult` records with non-empty `turns` (or an explicit `error`
      field if a file genuinely fails).
- [ ] Every record has `wall_seconds`, `rtf`, `peak_vram_mb`, `model_revision`, `runtime_id`,
      `raw_output_path` set; `raw_output_path` resolves to a file with 10 saved raw outputs (one per
      window) per excerpt.
- [ ] Audio-after-text message ordering verified by reading the actual call site, not assumed.
- [ ] Killing mid-run and re-running resumes via `store.iter_pending` and does not duplicate records.
- [ ] `parse_failure_rate` computed and printed for the full E2B run (expected to be nonzero — this is
      a result, not a bug).
- [ ] Config diff check: `variant_config` for E2B contains no field that only E2B could populate
      (i.e. the schema already anticipates E4B/12B).

## Test Instructions
```python
from benchmark import gemma_runner, store, config

gemma_runner.run("ami", "gpu-t4", config.SYSTEMS["gemma-e2b"])
recs = list(store.read(store.run_key("gemma-e2b", "ami", "gpu-t4")))
print(len(recs), recs[0].rtf, recs[0].peak_vram_mb, len(recs[0].turns))

from benchmark import gemma_prompt
failures = [gemma_prompt.parse(open(p).read(), 30.0)[1] for r in recs for p in [r.raw_output_path]]
print(sum(f is not None for f in failures) / len(failures))
```
Expected: 16 records for `ami`, RTF likely well above pyannote's (10 generate calls per file), plausible
turn counts, nonzero-but-not-total `parse_failure_rate`.

## Docs Needed
- [ ] Gemma 4 model card getting-started — AutoProcessor/AutoModelForMultimodalLM usage, modality
      order for message content
- [ ] transformers generation config for greedy decoding + disabling thinking mode

## Notes
