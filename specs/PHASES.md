# Phase Tracker

> Strict sequencing: never start phase N+1 until N is marked ✅ Done.
> To mark done: user verifies acceptance criteria, then updates status here.

## Legend
- 🔲 todo
- 🔄 in-progress
- ✅ done
- ⛔ blocked (reason in phase file)

---

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | Package scaffold + Colab bootstrap | 🔲 todo | [phases/01-scaffold.md](phases/01-scaffold.md) |
| 2 | Gated access + environment verification | 🔲 todo | [phases/02-access-env.md](phases/02-access-env.md) |
| 3 | **Gemma diarization smoke test (risk kill)** | 🔲 todo | [phases/03-gemma-smoke-test.md](phases/03-gemma-smoke-test.md) |
| 4 | AMI subset acquisition | 🔲 todo | [phases/04-ami-data.md](phases/04-ami-data.md) |
| 5 | VoxConverse subset acquisition | 🔲 todo | [phases/05-voxconverse-data.md](phases/05-voxconverse-data.md) |
| 6 | Turn schema + excerpting + UEM references | 🔲 todo | [phases/06-schema-references.md](phases/06-schema-references.md) |
| 7 | Checkpoint & resume store | 🔲 todo | [phases/07-checkpoint-store.md](phases/07-checkpoint-store.md) |
| 8 | Instrumentation harness (time, VRAM, RAM) | 🔲 todo | [phases/08-instrumentation.md](phases/08-instrumentation.md) |
| 9 | System A — pyannote runner (GPU) | 🔲 todo | [phases/09-pyannote-runner.md](phases/09-pyannote-runner.md) |
| 10 | Gemma prompt + output parser (frozen) | 🔲 todo | [phases/10-gemma-prompt-parser.md](phases/10-gemma-prompt-parser.md) |
| 11 | Windowing + cross-window speaker stitching | 🔲 todo | [phases/11-chunk-stitching.md](phases/11-chunk-stitching.md) |
| 12 | System B1 — Gemma E2B runner (GPU) | 🔲 todo | [phases/12-gemma-e2b.md](phases/12-gemma-e2b.md) |
| 13 | System B2 — Gemma E4B runner (GPU) | 🔲 todo | [phases/13-gemma-e4b.md](phases/13-gemma-e4b.md) |
| 14 | System B3 — Gemma 12B runner (GPU) + quantization | 🔲 todo | [phases/14-gemma-12b.md](phases/14-gemma-12b.md) |
| 15 | CPU leg — all four systems, timing subset | 🔲 todo | [phases/15-cpu-leg.md](phases/15-cpu-leg.md) |
| 16 | Unified DER scoring | 🔲 todo | [phases/16-scoring.md](phases/16-scoring.md) |
| 17 | `visualize.py` — full chart set | 🔲 todo | [phases/17-visualize.md](phases/17-visualize.md) |
| 18 | `report.py` — Markdown report generation | 🔲 todo | [phases/18-report.md](phases/18-report.md) |
| 19 | Recommendation write-up | 🔲 todo | [phases/19-recommendation.md](phases/19-recommendation.md) |

---

## Critical path notes

- **Phase 03 is a deliberate cheap risk kill.** It answers OQ1/OQ2 (can Gemma diarize a 30 s clip at
  all? does it emit usable timestamps?) before any dataset, runner or scoring code is built. If it
  fails hard — no reliable speaker separation within a single 30 s window — **the project stops
  there.** User decision (2026-08-08): report the finding with the saved raw evidence and build
  nothing further. Do not skip ahead past this phase.
- **Phases 04 and 05 can run while 03 is pending** if downloads are slow — they have no dependency
  on Gemma's behaviour.
- **Phases 12/13/14 are near-identical** by design: the runner is written once in Phase 12 and
  parameterized by config; 13 and 14 are execution + variant-specific fitting, not new code paths.
- **Phase 15 (CPU leg) is the most likely to hit a hard infeasibility** (OQ4). Per D3 it only needs
  speed/memory numbers on a small subset, so a partial result there does not endanger the DER
  results from phases 09–14.

---

## Completion Log
<!-- Append here when each phase is verified done -->
<!-- Format: - Phase N — [date] — [brief note] -->
