# Diarization Benchmark: pyannote.audio 3.1 vs Gemma 4 (E2B / E4B / 12B) — Specification

## Overview

Verascope (a video fact-checking pipeline) currently uses `pyannote.audio` 3.1 for speaker
diarization, ahead of Whisper + wav2vec2 forced alignment. Google's Gemma 4 family (2026) ships
native audio input on three variants — E2B, E4B and 12B Unified. This project measures, with
first-of-their-kind numbers, whether any Gemma 4 audio variant can perform speaker diarization
well enough to simplify or replace the pyannote stage in Verascope — and if so, at what compute
cost, on which hardware.

Deliverable: an importable Python package (`benchmark/`) plus a thin Colab notebook that drives it,
producing a generated Markdown report with DER, RTF and memory numbers, an extensive chart set, and
a written recommendation. The results are intended to be citable, so methodology rigour outranks
speed of delivery.

**Framing correction, load-bearing (see Prior Decisions D1):** the Gemma 4 model card does *not*
advertise diarization. Its stated audio capabilities are ASR and speech translation; its audio
benchmarks are CoVoST and FLEURS. This benchmark therefore measures an *emergent, unadvertised*
capability. "Gemma 4 cannot usefully diarize" is a legitimate and publishable outcome, and the
phase plan is ordered to discover that cheaply (Phase 03) rather than after building everything.

---

## Goals

- [ ] G1 — Measure DER (with miss / false-alarm / confusion breakdown) for 4 systems — pyannote 3.1,
      Gemma 4 E2B-it, E4B-it, 12B-it — on identical audio, with identical references, collar and
      overlap policy, scored by `pyannote.metrics`.
- [ ] G2 — Measure wall-clock time, RTF (`processing_time / audio_duration`) per file per system,
      on both a Colab CPU runtime and a Colab T4 GPU runtime.
- [ ] G3 — Measure peak VRAM (GPU leg) and peak RAM (CPU leg) per system per runtime.
- [ ] G4 — Produce the full chart set (§Visualizations) as standalone-legible PNGs, embedded in the
      report and rendered inline in the notebook.
- [ ] G5 — Produce a generated Markdown report: cross-system × cross-runtime × cross-dataset tables,
      embedded charts, and 2–3 concrete failure-case examples per system.
- [ ] G6 — Deliver a recommendation answering (a) keep pyannote / switch to Gemma / hybrid, and
      (b) does diarization quality plateau below 12B — is E2B or E4B "good enough"?
- [ ] G7 — Be independently re-runnable by the user after a pyannote or Gemma version bump, with
      pinned deps, logged model revision hashes, and logged runtime identity per result.

## Non-Goals (Explicit Out of Scope)

- Fine-tuning any model. Zero-shot / prompted only.
- Building a production diarization service. This is a decision artifact.
- Evaluating ASR or transcription quality. Diarization only — *who spoke when*, never *what was said*.
  (Gemma will emit text as a side effect; it is discarded, not scored.)
- DIHARD III (LDC licence friction).
- Gemma 4 26B A4B and 31B Dense — the model card confirms neither supports audio at all.
- Paid Colab tiers. Free CPU + free T4 only; infeasibility on free tier is a *result*, not a
  prompt to upgrade.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.11 | Colab-current; matches user's local uv envs |
| Local env | `uv` | User's standing local workflow (Debian 13 ThinkPad) |
| Package | `benchmark/` (src layout, `pyproject.toml`) | Logic lives in importable modules, not notebook cells |
| Baseline | `pyannote.audio` (3.1.x pin), `pyannote.metrics` | Verascope's current stack; the thing under test |
| Gemma | `transformers` (`AutoProcessor` + `AutoModelForMultimodalLM`) | Per Gemma 4 model card getting-started |
| GPU quant | `bitsandbytes` 4-bit (NF4) — *to be confirmed in Phase 14* | Only way 12B plausibly fits a 16 GB T4 |
| CPU path | `transformers` CPU, GGUF/llama.cpp only if it supports audio — *Phase 15* | See OQ4 |
| Audio IO | `librosa` / `soundfile`, `scipy.signal.resample` | Model card: mono, 16 kHz, float32 ∈ [-1, 1] |
| Charts | `matplotlib` + `seaborn`, static PNG | See D7 |
| Storage | JSONL + a run manifest on Google Drive | Survives Colab session death and CPU↔GPU restarts |
| Notebook | one `.ipynb`, thin narrative cells | Colab is notebook-native; runtime switches need restarts |

---

## Architecture

```
capstone_diarization_benchmark/
├── pyproject.toml            # pinned deps, installable via `pip install -e .`
├── notebooks/
│   └── benchmark.ipynb       # thin narrative: bootstrap → run → score → visualize → report
├── benchmark/
│   ├── config.py             # dataset/system registry, paths, collar, seeds, model ids+revisions
│   ├── schema.py             # Turn, FileResult, RunRecord dataclasses + JSONL (de)serialization
│   ├── store.py              # checkpoint/resume: manifest, atomic writes, Drive sync
│   ├── env.py                # runtime probe (CPU/GPU type, VRAM, RAM, lib versions, git sha)
│   ├── instrument.py         # timing + peak VRAM/RAM measurement context manager
│   ├── data.py               # AMI + VoxConverse acquisition, excerpting, RTTM/UEM → reference
│   ├── pyannote_runner.py    # System A
│   ├── gemma_prompt.py       # shared prompt + strict-output parser (identical across variants)
│   ├── gemma_chunk.py        # 30 s windowing + cross-chunk speaker stitching
│   ├── gemma_runner.py       # Systems B1/B2/B3, variant selected by config
│   ├── scoring.py            # unified pyannote.metrics DER for all systems
│   ├── visualize.py          # the full chart set
│   └── report.py             # Markdown assembly
├── specs/                    # this spec, phases, fetched docs
└── results/                  # JSONL outputs, charts, report (Drive-synced)
```

Data flow: every system, on every runtime, writes the **same** `FileResult` record shape
(`turns[]` + timing + memory + provenance) to JSONL. Scoring, charting and reporting consume only
that shape and are entirely system-agnostic. This is what enforces "identical methodology" — there
is only one DER code path and it cannot see which system produced a record.

---

## Key Constraints

- **C1 — Gemma audio input caps at 30 seconds.** (Model card, §"Audio and Video Length".) AMI and
  VoxConverse files are minutes to tens of minutes. Gemma therefore cannot ingest a file whole; it
  must be windowed and its per-window speaker labels stitched. This is the central methodological
  risk of the project — see D3, OQ1, Phase 11.
- **C2 — Free Colab only.** T4 (16 GB VRAM, compute capability 7.5, *no bf16*) and CPU runtime
  (~2 vCPU, ~13 GB RAM). Gemma 4 12B ships BF16 at ~24 GB — it cannot load unquantized on a T4, and
  cannot load on the CPU runtime at all without 4-bit.
- **C3 — Colab cannot switch CPU↔GPU without a runtime restart**, and free sessions are recycled
  when idle or long-running. Every run must checkpoint per-file and resume from the last
  checkpoint, for *unplanned* death as much as planned restarts.
- **C4 — Gated access.** `pyannote/speaker-diarization-3.1` and the Gemma variants require HF terms
  acceptance and a valid `HF_TOKEN`, supplied as a Colab secret, never hardcoded or committed.
- **C5 — Identical scoring.** One collar (0.25 s), one overlap policy, one reference set, one UEM
  per file, one mapping strategy — applied by one function to all four systems. Any drift
  invalidates the whole comparison.
- **C6 — Reproducibility over convenience.** Pinned versions, greedy decoding, logged model
  revision SHAs, logged runtime identity per record.

---

## Prior Decisions (locked)

- **D1 — Diarization is an unadvertised capability for Gemma 4.** The model card lists only ASR and
  speech translation under audio. We benchmark it anyway, and the report must state plainly that we
  are probing emergent behaviour, not a claimed feature. A near-total failure is a valid finding.
- **D2 — E2B/E4B are *not* encoder-free; only 12B Unified is.** Per the model card's Dense Models
  table, E2B and E4B carry ~300 M audio encoder parameters and ~150 M vision encoder parameters;
  12B Unified lists none, projecting waveforms straight into the decoder. So the three variants are
  **two architectures, not one scaling ladder**. The "is 12B worth it?" question must be reported as
  an architecture + size comparison, not a clean parameter-scaling curve.
- **D3 — DER is measured once, on the GPU leg; the CPU leg measures speed and memory only.**
  With greedy decoding and a fixed seed, model output is hardware-independent *given identical
  weights*, so a second full DER pass buys nothing but T4 hours. The CPU leg runs a small shared
  subset and Phase 15 verifies its outputs match the GPU leg's; where the CPU quantization path
  differs (e.g. GGUF Q4 vs bnb NF4), any output divergence is reported explicitly rather than
  averaged away. This is the single biggest compute saving in the plan.
- **D4 — Files are excerpted to a fixed 5-minute window.** Full AMI meetings (~30–60 min) at a 30 s
  Gemma window are 60–120 generate calls per file per variant, which does not fit free-tier T4
  hours. 5 min = 10 windows/file. Excerpts are cut deterministically (fixed offset from first
  annotated speech), and the UEM is trimmed to match so every system is scored on exactly the same
  span. Consequence, to be stated in the report: our pyannote numbers are **not** directly
  comparable to the published full-file model-card DER.
- **D5 — Sample size: 16 files per dataset** (AMI, VoxConverse) × 5 min = ~80 min audio per dataset,
  ~2.7 h total. Files are chosen stratified by reference speaker count (low: 2–3, high: 4+) so the
  DER-vs-speaker-count chart has populated buckets.
- **D6 — Scoring config: `collar=0.25`, `skip_overlap=False`, optimal (Hungarian) mapping via
  `pyannote.metrics.diarization.DiarizationErrorRate`, UEM-restricted.** Overlap **is** scored.
  Rationale: Verascope's real audio has crosstalk, and pyannote 3.1 handles overlap natively, so
  excluding it would flatter both systems and hide a real difference. The report states this
  explicitly and notes that many published numbers use `skip_overlap=True`.
- **D7 — Charts are static matplotlib/seaborn PNGs, not plotly.** The report is Markdown and the
  user wants to screenshot individual charts into a blog post; plotly's interactivity does not
  survive Markdown embedding and its HTML export is not screenshot-friendly. Interactivity earns
  nothing here.
- **D8 — Greedy decoding (`do_sample=False`) for all Gemma runs**, deviating from the model card's
  recommended `temperature=1.0, top_p=0.95, top_k=64`. Benchmark reproducibility outranks the
  vendor's chat-quality preset. Deviation is stated in the report. Thinking mode is **disabled**
  (no `<|think|>` token) — it burns tokens and adds nondeterminism for a formatting-bound task.
- **D9 — One prompt, one parser, byte-identical across E2B/E4B/12B.** Frozen after Phase 10. No
  per-variant prompt tuning, ever — otherwise measured differences reflect prompt engineering, not
  the models.
- **D10 — Package is installed in Colab by cloning the repo and running `pip install -e .`.** No
  copy-pasting code between local editing and the notebook; a Drive mount is the fallback only if
  the repo stays private and unauthenticated cloning fails.

---

## Open Questions

Each must be resolved before its named phase; none may be silently resolved by assumption.

- **OQ1 (Phase 03, then 11) — Can Gemma 4 diarize a 30 s clip at all?** And can *any* stitching
  strategy carry speaker identity across windows? Gemma exposes no speaker embeddings, so
  cross-window linking has no principled signal to use. **If within-window speaker separation fails,
  the project stops at Phase 03** (user decision, 2026-08-08) — we report the finding with the raw
  evidence and build nothing further. **Phase 03 exists to find this out in under an hour.**
- **OQ2 (Phase 03) — Will Gemma emit usable timestamps?** ASR-tuned models frequently emit turn
  order without wall-clock times. DER needs real times. If timestamps are absent or hallucinated,
  fallback is a fixed-grid formulation (label each ~1 s frame within the window) — decided in
  Phase 10, not assumed.
- **OQ3 (Phase 14) — Does 4-bit quantization work for `gemma4_unified` on a T4?** Unknowns:
  whether bitsandbytes NF4 supports this architecture in `AutoModelForMultimodalLM`, whether
  quantizing the audio projection layers destroys audio quality, and whether T4's lack of bf16
  forces an fp16 compute dtype that overflows. If 12B will not run on a free T4, that is reported
  as a blocker, not routed around with a paid GPU.
- **OQ4 (Phase 15) — Is there any working CPU path for the Gemma variants?** GGUF/llama.cpp is the
  realistic CPU option, but multimodal *audio* support for this architecture in llama.cpp is
  unverified. If audio is unsupported there, the CPU leg for Gemma uses `transformers` on CPU (slow
  but honest) or is reported as unavailable. 12B on a ~13 GB-RAM CPU runtime may be infeasible at
  any quantization — a reportable result.
- **OQ5 (Phase 02/09) — Exact `pyannote.audio` version pin.** Current upstream returns a
  `DiarizeOutput` dataclass (with a `legacy=True` flag for the old plain `Annotation`) and has
  renamed `use_auth_token` → `token`; 3.1.x returns `Annotation` directly. Pin 3.1.x for fidelity to
  Verascope's actual stack and confirm the exact call signature against the installed version.
- **OQ6 (Phase 04) — AMI Mix-Headset audio mirror availability and download size.** Confirm a
  working mirror and that 16 files fit Colab disk + Drive quota before committing.

---

## External Dependencies

| Dependency | Used for | Access |
|---|---|---|
| `pyannote/speaker-diarization-3.1` (HF) | System A | Gated — terms + `HF_TOKEN` |
| `google/gemma-4-E2B-it`, `-E4B-it`, `-12B-it` (HF) | Systems B1–B3 | Gated — terms + `HF_TOKEN` |
| AMI Corpus (Mix-Headset) + `pyannote/AMI-diarization-setup` RTTM/UEM | Dataset 1 | Open |
| VoxConverse audio + RTTM | Dataset 2 | Open |
| Google Colab (free CPU + T4) | Execution | Free tier |
| Google Drive | Checkpoints, results, report | User's account |

---

## Visualizations (deliverable, not decorative)

All produced by `visualize.py`, called from both the notebook and `report.py`; saved as PNG and
embedded in the Markdown report. Consistent axes, units, system colours and legends across every
chart, so any single chart is legible screenshotted out of context.

| # | Chart | Purpose |
|---|---|---|
| V1 | Grouped bar — DER per system, grouped by dataset | Headline accuracy |
| V2 | Stacked bar — DER split into miss / false alarm / confusion, per system | *Why* a system loses points |
| V3 | Line/scatter — DER vs reference speaker-count bucket, per system | Degradation with speaker count |
| V4 | Grouped bar — RTF per system, CPU vs GPU side by side | Answers the CPU-vs-GPU question directly |
| V5 | Scatter — audio duration (x) vs processing time (y), per file, coloured by system | Linear scaling or not |
| V6 | Grouped bar — peak VRAM (GPU) and peak RAM (CPU) per system | Resource cost beside accuracy |
| V7 | **Scatter — DER (x) vs RTF (y), per system per runtime; Pareto frontier marked** | **Priority chart for the recommendation** |
| V8 | Scatter — DER vs peak VRAM/RAM | Second resource axis, if it tells a different story |
| V9 | Gantt/timeline — reference turns vs predicted turns on a shared time axis | 2–3 failure cases per system |

---

## Definition of Done

A Colab notebook that, from a clean runtime and a valid `HF_TOKEN`, reproduces every number in
`results/report.md`; a report containing G1–G6; and a stated, numbers-backed recommendation for
Verascope's diarization stage — including an explicit verdict on whether the jump to Gemma 4 12B
is worth its compute over E2B/E4B for this task.
