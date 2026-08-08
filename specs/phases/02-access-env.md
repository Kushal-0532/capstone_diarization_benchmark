# Phase 02 — Gated access + environment verification

## Status
🔲 todo

## Goal
Prove, before any benchmark logic exists, that this account can download all four gated models and
that the runtime is what we think it is.

## Context
C4: all four models are gated. Discovering a licence blocker in Phase 14 would waste days. This
phase is a cheap, early gate. It also builds `env.py`, whose provenance output is stamped onto every
result record for G7.

## Scope
### In scope
- `env.describe()` → dict: runtime kind (CPU/GPU), GPU name + total VRAM + compute capability,
  CPU count, total RAM, disk free, python/torch/transformers/pyannote versions, CUDA version,
  repo git SHA, timestamp.
- `env.verify_access(model_ids)` → per-model dict of `{accessible, revision_sha, error}`, using
  `huggingface_hub.HfApi.model_info(...)` — metadata only, no weight download.
- Resolve and record the **exact revision SHA** of each of the four models into `config.py` as
  pins (C6/G7).
- Resolve **OQ5**: install the intended `pyannote.audio` 3.1.x pin, inspect the actual
  `Pipeline.from_pretrained` signature (`token=` vs `use_auth_token=`) and the return type
  (`Annotation` vs `DiarizeOutput`), and record the answer in this file's Notes.

### Out of scope
- Downloading weights or running inference (Phase 03 does the first real download).
- Dataset access (Phases 04/05).

## Technical Approach
- `HfApi().model_info(model_id, token=...)` raises `GatedRepoError` when terms are unaccepted —
  catch it and report a clear, actionable message naming the URL to accept terms at, rather than a
  raw traceback.
- Print a 4-row access table. Anything not ✅ blocks the phase; the fix is a human accepting terms
  on huggingface.co, not a code change.
- For OQ5: `inspect.signature(Pipeline.from_pretrained)` on the installed version, and read the
  installed `speaker_diarization.py` for the return type. Record verbatim, do not infer from docs —
  upstream has since changed both.

## Acceptance Criteria
- [ ] `env.describe()` returns correct values on a Colab T4 runtime (GPU name "Tesla T4", ~15–16 GB).
- [ ] `env.verify_access()` reports ✅ for all four model ids with a resolved revision SHA each.
- [ ] Those four SHAs are pinned in `config.py`.
- [ ] Gated-without-terms produces a readable message naming the model URL, not a traceback.
- [ ] OQ5 resolved and written into Notes below: exact pyannote version, exact kwarg name, exact
      return type.

## Test Instructions
```python
from benchmark import env
print(env.describe())
for mid, r in env.verify_access().items():
    print(mid, r["accessible"], r["revision_sha"][:8] if r["accessible"] else r["error"])
```
Expected: four rows, all `True`, each with an 8-char SHA prefix. Run on both a CPU and a GPU
runtime; `describe()` must differ correctly between them.

## Docs Needed
- [x] Gemma 4 model card — see [../docs/gemma-4-model-card.md](../docs/gemma-4-model-card.md)
- [x] pyannote.audio — see [../docs/pyannote-audio.md](../docs/pyannote-audio.md)
- [ ] `huggingface_hub` — `HfApi.model_info`, gated-repo error types

## Notes
<!-- OQ5 answer goes here, verbatim from the installed package -->
