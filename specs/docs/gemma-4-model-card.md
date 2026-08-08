# Gemma 4 — model card excerpts (fetched 2026-08-08)

Source: https://huggingface.co/google/gemma-4-12B-it
Tech report: arXiv 2607.02770 · License: Apache 2.0

Only the parts load-bearing for this benchmark are kept here. Re-fetch before relying on anything
else — this card is newer than the assistant's training data.

## Audio support and the 30-second cap  ← constraint C1

> All models support image inputs and can process videos as frames whereas the **E2B, E4B, and 12B
> models also support audio inputs. Audio supports a maximum length of 30 seconds.**

This is the single most consequential constraint in the project. 5-minute excerpts require 10
windows per file and cross-window speaker stitching (Phase 11).

## Diarization is NOT a claimed capability  ← decision D1

Stated audio capabilities:

> **Audio** (E2B, E4B, and 12B only) – Automatic speech recognition (ASR) and speech-to-translated-text
> translation across multiple languages.

Audio benchmarks reported: **CoVoST** (translation) and **FLEURS** (ASR, lower is better). No
diarization benchmark, no mention of speakers. We are probing an emergent capability.

| Audio benchmark | 12B Unified | E4B | E2B |
|---|---|---|---|
| CoVoST | 38.5* | 35.54 | 33.47 |
| FLEURS (lower better) | 0.069* | 0.08 | 0.09 |

\* excluding Chinese.

## Architecture: E2B/E4B have encoders, 12B does not  ← decision D2

| Property | E2B | E4B | 12B Unified | 31B Dense |
|---|---|---|---|---|
| Total params | 2.3B effective (5.1B w/ embeddings) | 4.5B effective (8B w/ embeddings) | 11.95B | 30.7B |
| Layers | 35 | 42 | 48 | 60 |
| Context | 128K | 128K | 256K | 256K |
| Modalities | Text, Image, Audio | Text, Image, Audio | Text, Image, Audio | Text, Image |
| Vision encoder | ~150M | ~150M | — | ~550M |
| **Audio encoder** | **~300M** | **~300M** | **—** | No audio |

> The "Unified" in Gemma 4 12B Unified refers to its **encoder-free architecture. Other Gemma 4
> models use dedicated encoders** to process multimodal data before passing it to the LLM. Gemma 4
> 12B eliminates these encoders entirely, projecting raw image patches and audio waveforms directly
> into the LLM's embedding space through lightweight linear layers.

Two consequences: (1) the E2B→E4B→12B comparison is two architectures, not a scaling curve;
(2) for 12B those "lightweight linear layers" are the entire audio path — 4-bit quantizing them is
a specific risk (OQ3, Phase 14).

26B A4B (MoE) and 31B Dense support **Text, Image only** — correctly excluded from this benchmark.

## Getting started (audio)

```python
from transformers import AutoProcessor, AutoModelForMultimodalLM

MODEL_ID = "google/gemma-4-12B-it"
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = AutoModelForMultimodalLM.from_pretrained(MODEL_ID, dtype="auto", device_map="auto")

messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "..."},
        {"type": "audio", "audio": "<url or path>"},   # audio AFTER text
    ],
}]

inputs = processor.apply_chat_template(
    messages, tokenize=True, return_dict=True, return_tensors="pt",
    add_generation_prompt=True,
).to(model.device)
input_len = inputs["input_ids"].shape[-1]

outputs = model.generate(**inputs, max_new_tokens=512)
response = processor.decode(outputs[0][input_len:], skip_special_tokens=False)
processor.parse_response(response, prefix=inputs["input_ids"])
```

Requires `pip install -U transformers torch torchvision librosa accelerate`.

## Modality order  ← easy to get backwards

> Image content **before** the text in your prompt. **Audio content after the text** in your prompt.

## Thinking mode

> Thinking is enabled by including the `<|think|>` token at the start of the system prompt. To
> disable thinking, remove the token.

Output structure when enabled: `<|channel>thought\n[reasoning]<channel|>`. For all models except
E2B/E4B, disabled thinking still emits an empty thought block. We disable it (D8).

## Recommended sampling — which we deliberately deviate from (D8)

> `temperature=1.0`, `top_p=0.95`, `top_k=64`

We use greedy decoding (`do_sample=False`) for benchmark reproducibility, and say so in the report.

## Audio preprocessing

Mono, 16 kHz, float32 in [-1, 1]. `AutoProcessor` handles this; manual resampling should use a
Fourier method (`scipy.signal.resample`, or librosa with `res_type='scipy'`).

## Other facts

- Native `system` role support (unlike Gemma 3).
- Weights ship BF16; 12B is ~12B params ⇒ ~24 GB at BF16, vs a free T4's 16 GB (OQ3).
- Prompt templates the card gives for audio are ASR- and translation-shaped only — there is no
  vendor-provided diarization prompt to copy. Phase 10 designs ours.
