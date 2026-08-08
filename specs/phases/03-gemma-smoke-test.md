# Phase 03 — Gemma diarization smoke test (risk kill)

## Status
🔲 todo

## Goal
Answer, in under an hour of T4 time and before building anything else: can Gemma 4 produce
speaker-attributed, timestamped turns for a single 30-second two-speaker clip at all?

## Context
**This is the highest-value phase in the plan.** Per D1, the model card never claims diarization —
its audio capabilities are ASR and speech translation, and its audio benchmarks are CoVoST and
FLEURS. If Gemma cannot separate speakers or cannot emit usable timestamps (OQ1, OQ2), then the
entire Gemma half of this benchmark changes shape. Finding that out now costs an hour; finding out
in Phase 14 costs the project.

The output of this phase is *evidence and a decision*, not production code.

## Scope
### In scope
- Load `google/gemma-4-E4B-it` (mid-size: representative, and fits a T4 unquantized-ish; avoids
  conflating a null result with a 12B quantization problem).
- Hand-pick 3 clips ≤30 s: (a) clean 2-speaker alternating, (b) 3-speaker with a short interjection,
  (c) 2-speaker with a genuine overlap. Any source with known ground truth; a hand-annotated AMI
  snippet is fine.
- Try 3–5 prompt formulations, including at minimum: strict JSON turns
  (`[{"speaker": "...", "start": s, "end": s}]`), and a fixed-grid variant (label each 1-second
  frame) as the OQ2 fallback.
- Record raw model output verbatim for every (clip × prompt) into `results/smoke/` — this is
  evidence for the report regardless of outcome.
- Written verdict against three specific questions:
  1. **Speaker separation** — does it distinguish speakers consistently *within* one window?
  2. **Timestamps** — are emitted times plausible and monotonic, or absent/hallucinated?
  3. **Format compliance** — does greedy decoding (D8) yield parseable output reliably?

### Out of scope
- Cross-window stitching (Phase 11), all other variants, any DER computation, any dataset pipeline.
- Prompt *optimization*. This phase establishes feasibility; Phase 10 designs the final prompt.

## Technical Approach
- Follow the model card getting-started exactly: `AutoProcessor` + `AutoModelForMultimodalLM`,
  `processor.apply_chat_template(messages, tokenize=True, return_dict=True, return_tensors="pt",
  add_generation_prompt=True)`, then `model.generate(...)`, then `processor.parse_response(...)`.
- **Audio content goes *after* the text** in the message content list — model card §"Modality order"
  is explicit about this and it is easy to get backwards.
- Thinking disabled (no `<|think|>` in the system prompt) per D8.
- `do_sample=False`, `max_new_tokens` generous (~1024) so truncation is never confused with
  incapability.
- Feed audio as a local path/array, mono 16 kHz float32 ∈ [-1, 1].

## Acceptance Criteria
- [ ] All 3 clips × all prompt variants produce raw output saved to `results/smoke/`.
- [ ] A written verdict on each of the three questions above, with quoted output as evidence.
- [ ] An explicit **GO / GO-WITH-FALLBACK / NO-GO** recommendation:
      - GO — timestamped speaker turns work; proceed as specced.
      - GO-WITH-FALLBACK — separation works, timestamps do not; Phase 10 adopts the fixed-grid
        formulation.
      - NO-GO — no reliable speaker separation within a single window. **Stop the project here.**
        Do not build Phases 10–15. Report the finding with the saved raw evidence, and stop; the
        user has decided this is a terminal outcome, not a pivot to a negative-result paper.
- [ ] OQ1 (within-window) and OQ2 both answered in Notes.

## Test Instructions
```python
from benchmark import gemma_prompt  # scratch functions are fine at this stage
# Run the smoke script, then read the saved outputs:
!ls results/smoke/ && cat results/smoke/clip_a__prompt_json.txt
```
Verify by eye: does the output name distinct speakers, with times inside [0, 30], in order?

## Docs Needed
- [x] Gemma 4 model card — audio snippet, modality order, thinking tokens, 30 s cap:
      [../docs/gemma-4-model-card.md](../docs/gemma-4-model-card.md)
- [ ] `transformers` — `AutoModelForMultimodalLM`, `AutoProcessor.apply_chat_template` audio content

## Notes
<!-- Verdict, quoted evidence, and the GO decision go here. -->
