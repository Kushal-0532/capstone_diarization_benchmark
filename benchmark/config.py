"""Single source of truth for every knob that must not drift between systems.

C5 depends on there being exactly one definition of the scoring and excerpting
constants. Nothing else in the package may define COLLAR, SKIP_OVERLAP,
EXCERPT_SECONDS, GEMMA_WINDOW_SECONDS or SEED.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Scoring (D6) ------------------------------------------------------------
COLLAR = 0.25
SKIP_OVERLAP = False  # overlap IS scored; see D6

# --- Excerpting / windowing (D4, C1) -----------------------------------------
EXCERPT_SECONDS = 300  # 5 min per file
GEMMA_WINDOW_SECONDS = 30  # Gemma 4 hard audio cap
FILES_PER_DATASET = 16  # D5

# --- Audio (Gemma model card) ------------------------------------------------
SAMPLE_RATE = 16_000
AUDIO_CHANNELS = 1

# --- Determinism (C6, D8) ----------------------------------------------------
SEED = 0
DO_SAMPLE = False  # greedy decoding for all Gemma runs
THINKING = False  # thinking mode disabled

# --- Systems -----------------------------------------------------------------
SYSTEM_PYANNOTE = "pyannote-3.1"
SYSTEM_GEMMA_E2B = "gemma4-e2b"
SYSTEM_GEMMA_E4B = "gemma4-e4b"
SYSTEM_GEMMA_12B = "gemma4-12b"

SYSTEMS: tuple[str, ...] = (
    SYSTEM_PYANNOTE,
    SYSTEM_GEMMA_E2B,
    SYSTEM_GEMMA_E4B,
    SYSTEM_GEMMA_12B,
)

# HF model ids. Revision SHAs are resolved and logged at run time (C6), not pinned here.
MODEL_IDS: dict[str, str] = {
    SYSTEM_PYANNOTE: "pyannote/speaker-diarization-3.1",
    SYSTEM_GEMMA_E2B: "google/gemma-4-E2B-it",
    SYSTEM_GEMMA_E4B: "google/gemma-4-E4B-it",
    SYSTEM_GEMMA_12B: "google/gemma-4-12B-it",
}

GEMMA_SYSTEMS: tuple[str, ...] = (SYSTEM_GEMMA_E2B, SYSTEM_GEMMA_E4B, SYSTEM_GEMMA_12B)

# --- Datasets ----------------------------------------------------------------
DATASET_AMI = "ami"
DATASET_VOXCONVERSE = "voxconverse"
DATASETS: tuple[str, ...] = (DATASET_AMI, DATASET_VOXCONVERSE)

# Speaker-count strata for file selection and the DER-vs-speakers chart (D5, V3).
SPEAKER_BUCKETS: dict[str, tuple[int, int]] = {"low": (2, 3), "high": (4, 99)}

# --- Runtimes ----------------------------------------------------------------
RUNTIME_CPU = "cpu"
RUNTIME_GPU = "gpu"
RUNTIMES: tuple[str, ...] = (RUNTIME_CPU, RUNTIME_GPU)

# --- Paths -------------------------------------------------------------------
# BENCHMARK_ROOT lets Colab point results at Drive without editing code.
ROOT = Path(os.environ.get("BENCHMARK_ROOT", Path(__file__).resolve().parent.parent))
RESULTS_DIR = ROOT / "results"
DATA_DIR = ROOT / "data"
CHARTS_DIR = RESULTS_DIR / "charts"
REPORT_PATH = RESULTS_DIR / "report.md"
MANIFEST_PATH = RESULTS_DIR / "manifest.json"

DRIVE_MOUNT = Path("/content/drive")
DRIVE_RESULTS_DIR = DRIVE_MOUNT / "MyDrive" / "capstone_diarization_benchmark"
