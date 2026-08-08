"""Runtime probe: what hardware and library versions produced a result (C6, G7).

Every FileResult carries the output of `describe()` so a number can always be traced
back to the runtime that made it.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from importlib import metadata

# Recorded per record so a version bump is visible in the results (G7).
TRACKED_PACKAGES = (
    "pyannote.audio",
    "pyannote.metrics",
    "transformers",
    "torch",
    "torchaudio",
    "librosa",
    "bitsandbytes",
)


def in_colab() -> bool:
    """True inside a Colab runtime. The notebook branches on this so it also runs locally."""
    return "google.colab" in sys.modules or "COLAB_RELEASE_TAG" in os.environ


def package_versions() -> dict[str, str | None]:
    """Installed version of each tracked package, or None if absent."""
    out: dict[str, str | None] = {}
    for name in TRACKED_PACKAGES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def git_sha() -> str | None:
    """Short SHA of the checked-out benchmark code, or None outside a git checkout."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True, cwd=_repo_dir(),
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _repo_dir() -> str:
    from pathlib import Path

    return str(Path(__file__).resolve().parent.parent)


def hardware() -> dict[str, object]:
    """CPU/GPU identity, VRAM and RAM. Torch is imported lazily — it is slow to import."""
    info: dict[str, object] = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "cpu_count": None,
        "ram_gb": None,
        "cuda_available": False,
        "gpu_name": None,
        "vram_gb": None,
        "bf16_supported": None,
    }
    try:
        import psutil

        info["cpu_count"] = psutil.cpu_count(logical=True)
        info["ram_gb"] = round(psutil.virtual_memory().total / 1024**3, 2)
    except ImportError:
        pass
    try:
        import torch

        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            info["cuda_available"] = True
            info["gpu_name"] = props.name
            info["vram_gb"] = round(props.total_memory / 1024**3, 2)
            info["bf16_supported"] = torch.cuda.is_bf16_supported()
    except ImportError:
        pass
    return info


def runtime_id() -> str:
    """`config.RUNTIME_GPU` if CUDA is usable, else `config.RUNTIME_CPU`."""
    from benchmark import config

    return config.RUNTIME_GPU if hardware()["cuda_available"] else config.RUNTIME_CPU


def describe() -> dict[str, object]:
    """Full provenance blob embedded in every result record."""
    return {
        "runtime": runtime_id(),
        "colab": in_colab(),
        "hardware": hardware(),
        "packages": package_versions(),
        "git_sha": git_sha(),
    }


def print_description() -> None:
    """Human-readable `describe()` for the notebook bootstrap cell."""
    import json

    print(json.dumps(describe(), indent=2, default=str))
