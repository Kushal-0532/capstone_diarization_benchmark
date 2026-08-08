# Diarization benchmark: pyannote.audio 3.1 vs Gemma 4 (E2B / E4B / 12B)

Measures DER, RTF and peak memory for four speaker-diarization systems on identical AMI and
VoxConverse excerpts, on free Colab CPU and T4 runtimes, to decide whether any Gemma 4 audio
variant can simplify or replace the `pyannote.audio` stage in Verascope. Diarization is an
*unadvertised* Gemma 4 capability — "it cannot usefully diarize" is a valid outcome. Logic lives
in the importable `benchmark/` package; `notebooks/benchmark.ipynb` is a thin driver.

Spec, phase plan and fetched docs: [`specs/`](specs/). Local setup: `uv venv && uv pip install -e .`
