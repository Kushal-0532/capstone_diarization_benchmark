# Phase 01 — Package scaffold + Colab bootstrap

## Status
✅ done

## Goal
An installable `benchmark` package that a fresh Colab runtime can clone and `pip install -e .`,
importing cleanly with pinned dependencies.

## Context
Everything else imports from here. The point of this phase is that no benchmark logic ever lives in
a notebook cell — the notebook is a narrative driver, and a parsing bug is debugged as a normal
Python module locally.

## Scope
### In scope
- `pyproject.toml` (src-less flat layout, `benchmark/` package, Python 3.11), pinned deps.
- Module stubs with real signatures and docstrings: `config.py`, `schema.py`, `store.py`, `env.py`,
  `instrument.py`, `data.py`, `pyannote_runner.py`, `gemma_prompt.py`, `gemma_chunk.py`,
  `gemma_runner.py`, `scoring.py`, `visualize.py`, `report.py`.
- `config.py` with the real registry: system ids, HF model ids, dataset ids, `COLLAR = 0.25`,
  `SKIP_OVERLAP = False`, `EXCERPT_SECONDS = 300`, `GEMMA_WINDOW_SECONDS = 30`, `SEED = 0`,
  results/Drive path roots.
- `notebooks/benchmark.ipynb` with only the bootstrap cell: clone/pull repo, `pip install -e .`,
  mount Drive, read `HF_TOKEN` from `google.colab.userdata`, print `env.describe()`.
- `.gitignore` excluding `results/`, audio, `.venv`, checkpoints. `README.md` one-paragraph.
- Local `uv` env: `uv venv && uv pip install -e .` works on Debian 13.

### Out of scope
- Any inference, dataset or scoring logic. Stubs raise `NotImplementedError`.
- Drive-mount fallback mechanics (only if cloning fails — decided here, implemented if needed).

## Technical Approach
- Flat package layout so `pip install -e .` from the repo root is the whole Colab story (D10).
- Pin exact versions in `pyproject.toml`, not ranges — reproducibility (C6). Note that Colab
  preinstalls a torch build; pin `torch` compatibly rather than forcing a reinstall that costs
  minutes and can break CUDA. Record whatever versions actually resolve.
- `config.py` holds every knob that must not drift between systems (collar, overlap, excerpt length,
  seed). Nothing else may define these — C5 depends on there being exactly one source.
- Notebook cells stay ≤10 lines each.

## Acceptance Criteria
- [x] `uv pip install -e .` succeeds locally on Debian 13; `python -c "import benchmark; print(benchmark.__version__)"` works.
- [x] Every module listed above exists and imports without error.
- [x] `benchmark.config` exposes COLLAR, SKIP_OVERLAP, EXCERPT_SECONDS, GEMMA_WINDOW_SECONDS, SEED,
      the 4 system ids and the 2 dataset ids.
- [x] Bootstrap cell in Colab: installs the package, mounts Drive, prints a runtime description,
      reads `HF_TOKEN` from Colab secrets without printing it.
- [x] `git grep -n "hf_"` finds no hardcoded token anywhere.

## Test Instructions
```bash
cd capstone_diarization_benchmark
uv venv && uv pip install -e .
uv run python -c "import benchmark, benchmark.config as c; print(c.SYSTEMS, c.COLLAR)"
```
Then in Colab: run the bootstrap cell top-to-bottom on a fresh runtime; it must complete without
manual intervention.

## Docs Needed
- [ ] None beyond what is fetched — packaging is stable ground.

## Notes
- Resolved + installed on Debian 13 / Python 3.11.14: `pyannote.audio==3.1.1`,
  `pyannote.metrics==3.2.1`, `transformers==5.14.1`, `torch==2.13.0`, `torchaudio==2.11.0`,
  `librosa==0.11.0`, `numpy==2.4.6`, `huggingface-hub==1.27.0`.
- **`huggingface-hub` is deliberately unpinned.** transformers 5.x requires `>=1.5,<2`; pyannote
  3.1.1 only floors it at `>=0.13`. Pinning 0.36 made the resolve unsatisfiable. Phase 02 must
  verify pyannote 3.1.1 actually *runs* against hub 1.x — the version range is satisfiable, the
  API compatibility is not yet proven (hub 1.x removed several 0.x helpers).
- `scipy` pinned 1.16.3, not 1.18.0: 1.18 requires Python >=3.12.
- `torch`/`torchaudio` left as lower bounds (`>=2.6`) on purpose — Colab ships a CUDA-matched
  build and reinstalling costs minutes and can break CUDA. `env.describe()` logs what actually ran.
- `env.py` is implemented, not stubbed — Phase 01's bootstrap cell needs a working `describe()`.
  Phase 02 extends it with the gated-access checks.
- Repo is public at `https://github.com/Kushal-0532/capstone_diarization_benchmark` (user decision,
  2026-08-08). Public was chosen over private so Colab clones unauthenticated — the D10 Drive-mount
  fallback is therefore not needed. `results/` and `data/` are gitignored; no token is committed.
- `notebooks/benchmark.ipynb` `REPO_URL` now points at that remote.
- **The notebook runs locally as well as in Colab**, every cell branching on `IN_COLAB` (user
  request, 2026-08-08: prototype locally instead of re-uploading on every change). Local path skips
  clone / `pip install` / Drive mount / `userdata`, resolves the repo root by walking up for
  `pyproject.toml`, and takes `HF_TOKEN` from the shell environment. `env.in_colab()` is the same
  check, available to the runners.
- **First Colab failure was `benchmark` not importable after `pip install -e`.** An editable install
  writes a `.pth` that only a fresh interpreter reads, so an install and an import in the same
  kernel session cannot both work without a restart. Fixed by inserting the repo root on `sys.path`
  after installing — the flat layout makes that sufficient. Do not "fix" this by adding a kernel
  restart; it would break resume-after-restart ergonomics for every later phase.
- Verified by executing the notebook headless: `uv run jupyter execute notebooks/benchmark.ipynb`.
  All five code cells pass locally.
- `[dev]` extra (jupyterlab, ipykernel, nbclient) is unpinned on purpose — dev tooling never
  touches a reported number, so C6 does not apply to it.
- Colab currently runs **Python 3.12**, inside `requires-python = ">=3.11,<3.13"`. Local env is
  3.11.14, so the two legs are not on the same interpreter — acceptable (no C-ABI-sensitive code
  here), but `env.describe()` records it per record.
