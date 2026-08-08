# Phase 14 — System B3: Gemma 12B runner (GPU) + quantization

## Status
🔲 todo

## Goal
Resolve OQ3: establish whether Gemma 4 12B Unified can run on a free T4 at all, and if so under what
quantization, then run it over all 32 excerpts.

## Context
12B ships BF16 at ~24GB. The free T4 has 16GB VRAM and compute capability 7.5, which has **no bf16
support**. 12B is also the encoder-free variant (D2) — waveforms project straight into the decoder via
lightweight linear layers, unlike E2B/E4B's ~300M-parameter audio encoders. Those projection layers
are the entire audio pathway for 12B, which makes them exactly the layers naive 4-bit quantization is
most likely to damage. This phase is a genuine feasibility investigation, not a guaranteed execution
step — constraint is free tier only, so if 12B cannot run, that is reported, not routed around with a
paid GPU.

## Scope
### In scope
- Investigation: does `bitsandbytes` 4-bit NF4 support the `gemma4_unified` architecture under
  `AutoModelForMultimodalLM`? Try loading with `BitsAndBytesConfig(load_in_4bit=True, ...)`.
- Investigation: does naive 4-bit quantization of the audio projection layers degrade audio
  understanding? Compare against a config using `llm_int8_skip_modules` (or equivalent) to keep the
  audio projection layers in fp16 while the rest of the decoder is 4-bit.
- Investigation: does fp16 compute dtype (`bnb_4bit_compute_dtype=torch.float16`, since bf16 is
  unavailable on T4) overflow or produce garbage output?
- Quality sanity check: re-run the Phase 03 smoke-test clips under the chosen quantization config and
  compare output qualitatively against E4B's output on the same clips (12B is not directly comparable
  to E2B/E4B by size — see D2 — this is a sanity check, not a scientific control).
- A documented decision on final quant config (or a documented BLOCKER if none works).
- If viable: run `gemma_runner.run(..., config.SYSTEMS["gemma-12b"])` over all 32 excerpts, same
  runner as Phases 12/13, config-only difference plus the quant config.

### Out of scope
- Any code change to `gemma_runner.py`/`gemma_prompt.py`/`gemma_chunk.py` beyond what's needed to
  accept a `quantization_config` field already anticipated in Phase 12's `variant_config` schema.
  If that field isn't there, fix Phase 12, don't patch around it here.
- Switching to a paid Colab GPU tier to make 12B fit. Not permitted under any circumstance.
- CPU leg for 12B (Phase 15 territory, and likely infeasible there too per OQ4).

## Technical Approach
- Load order to try: (1) full 4-bit NF4, no skip modules — cheapest, most likely to break audio;
  (2) 4-bit NF4 with audio projection layers in `llm_int8_skip_modules` / fp16 — the load-bearing
  candidate; (3) if VRAM allows, 8-bit as a fallback between full precision and 4-bit.
- Identify the exact module names for the audio projection layers by inspecting the loaded model's
  `named_modules()` before assuming a name from the model card — architectures vary in naming.
- Watch for NaN/inf in `model.generate()` output under fp16 compute dtype — a classic overflow
  symptom on non-bf16 hardware. If it appears, that itself is evidence for the BLOCKER path.
- Quality comparison against E4B is qualitative (read the parsed turns, read the raw text) — do not
  invent a fabricated quantitative score for something this phase isn't scoped to formally DER-score
  yet (that's Phase 16, using this phase's config once chosen).

## Acceptance Criteria
- [ ] A documented decision recorded in Notes: which quant config was chosen (or that none worked),
      with the VRAM figures observed for each attempted config.
- [ ] If a working config is found: quality sanity check comparing quantized-12B output on the Phase
      03 smoke clips against E4B output on the same clips, written up in Notes (not just "looks fine").
- [ ] If a working config is found: all 32 excerpts produce `FileResult` records with
      `model_revision`, `raw_output_path`, and a `quantization_config` value logged per record.
- [ ] If **no** config lets 12B load and generate coherently on a free T4: this phase is marked ⛔
      (not 🔲 or ✅) in its Status section, the blocker is stated plainly in Notes with what was tried,
      and the user is told directly — never silently replaced with a paid GPU or silently dropped
      from the comparison.
- [ ] Whatever the outcome, Phases 16-19 must be able to read this phase's Notes and know exactly
      whether System B3 has data or is reported as unavailable.

## Test Instructions
```python
from benchmark import gemma_runner, store, config
import torch

# feasibility probe first
from transformers import AutoModelForMultimodalLM, BitsAndBytesConfig
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                          llm_int8_skip_modules=["<audio_projection_module_name>"])
model = AutoModelForMultimodalLM.from_pretrained("google/gemma-4-12B-it", quantization_config=bnb, device_map="cuda")
print(torch.cuda.max_memory_allocated() / 1e9, "GB")

# if feasible, full run
gemma_runner.run("ami", "gpu-t4", config.SYSTEMS["gemma-12b"])
recs = list(store.read(store.run_key("gemma-12b", "ami", "gpu-t4")))
print(len(recs), recs[0].peak_vram_mb)
```
Expected: either a peak VRAM figure under 16GB with coherent output, or a documented failure
(OOM, NaN output, or unsupported architecture error) that becomes this phase's BLOCKER writeup.

## Docs Needed
- [ ] bitsandbytes `BitsAndBytesConfig` — 4-bit NF4, `llm_int8_skip_modules`, compute dtype options
- [ ] Gemma 4 model card — 12B Unified architecture, audio projection layer names
- [ ] transformers `AutoModelForMultimodalLM` quantization support notes

## Notes
Quant decision (fill in once investigated): TBD.
VRAM observed per config attempted: TBD.
Quality sanity check vs E4B on smoke clips: TBD.
If BLOCKED: state exactly what was tried and why each failed.
