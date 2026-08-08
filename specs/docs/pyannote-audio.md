# pyannote.audio / pyannote.metrics — API notes (fetched 2026-08-08, Context7)

Source: /pyannote/pyannote-audio (github.com/pyannote/pyannote-audio)

**Warning — version drift.** The snippets below come from current upstream, which has moved past
3.1. We pin **3.1.x** (Verascope's actual stack). Two things changed upstream and must be verified
against the *installed* version in Phase 02 (OQ5):

1. `use_auth_token=` → `token=`
2. Return type: 3.1.x returns a plain `Annotation`; upstream returns a `DiarizeOutput` dataclass
   (with `legacy=True` to restore the old behaviour).

## `Pipeline.from_pretrained` (current upstream signature)

```python
@classmethod
def from_pretrained(
    cls,
    checkpoint: str | Path | dict,
    revision: str | None = None,      # pin this — reproducibility
    hparams_file: str | Path | None = None,
    subfolder: str | None = None,
    token: str | bool | None = None,  # was use_auth_token in 3.1
    cache_dir: Path | str | None = None,
) -> Optional["Pipeline"]:
```

## Usage

```python
import torch
from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1", token=HF_TOKEN)
pipeline.to(torch.device("cuda"))          # or "cpu"
output = pipeline("audio.wav")
```

3.1.x — output is an `Annotation`:

```python
from pyannote.core import Annotation
assert isinstance(dia, Annotation)
for turn, _, speaker in dia.itertracks(yield_label=True):
    ...  # turn.start, turn.end, speaker
```

Upstream `DiarizeOutput` (for reference only; not what we pin):

```python
@dataclass
class DiarizeOutput:
    speaker_diarization: Annotation
    exclusive_speaker_diarization: Annotation   # no overlapping turns
    speaker_embeddings: np.ndarray | None = None   # (num_speakers, dim)
```

`ProgressHook` exists for progress reporting: `with ProgressHook() as hook: pipeline(f, hook=hook)`.

## Scoring — the canonical evaluation loop

```python
from pyannote.metrics.diarization import DiarizationErrorRate

metric = DiarizationErrorRate()
for file in dataset.test():
    hypothesis = pipeline(file)
    metric(file["annotation"], hypothesis, uem=file["annotated"])
print(f"DER = {100 * abs(metric):.1f}%")
```

For this project (D6): `DiarizationErrorRate(collar=0.25, skip_overlap=False)`, called with
`uem=` and `detailed=True` to get the miss / false alarm / confusion / total components that
chart V2 needs. `DiarizationErrorRate` uses **optimal (Hungarian) mapping** by default —
`GreedyDiarizationErrorRate` is the greedy-mapping variant and is *not* what we want.

Aggregate as `sum(errors) / sum(reference durations)` (which `abs(metric)` does), **not** as a mean
of per-file DERs.

## Not fetched
`pyannote.metrics` has no separate Context7 entry. The `DiarizationErrorRate` constructor kwargs
(`collar`, `skip_overlap`) and the `detailed=True` return keys are stable across releases, but
Phase 16 should assert the exact detail-dict key names against the installed version rather than
trusting the strings.
