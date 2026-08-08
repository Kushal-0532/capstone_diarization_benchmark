# Phase 17 — visualize.py — full chart set

## Status
🔲 todo

## Goal
Implement V1-V9 exactly as specified in SPEC.md §Visualizations, as standalone-legible static PNGs.

## Context
These charts are a deliverable, not decoration — they carry the recommendation in Phase 19 and get
screenshotted individually into a blog post. D7 locked static matplotlib/seaborn over plotly because
Markdown embedding and screenshots don't survive interactivity. Every chart must be readable with
zero surrounding context: a viewer who only sees one PNG, no caption, must still be able to tell
which system is which and what the axes mean.

## Scope
### In scope
All nine charts, each its own function in `visualize.py`, taking Phase 16's tidy scored data (plus
timing/memory fields already present on `FileResult`) and returning a saved PNG path:

| # | Chart | Purpose |
|---|---|---|
| V1 | Grouped bar — DER per system, grouped by dataset | Headline accuracy |
| V2 | Stacked bar — DER split into miss / false alarm / confusion, per system | *Why* a system loses points |
| V3 | Line/scatter — DER vs reference speaker-count bucket, per system | Degradation with speaker count |
| V4 | Grouped bar — RTF per system, CPU vs GPU side by side | Answers the CPU-vs-GPU question directly |
| V5 | Scatter — audio duration (x) vs processing time (y), per file, coloured by system | Linear scaling or not |
| V6 | Grouped bar — peak VRAM (GPU) and peak RAM (CPU) per system | Resource cost beside accuracy |
| V7 | Scatter — DER (x) vs RTF (y), per system per runtime; Pareto frontier marked | Priority chart for the recommendation |
| V8 | Scatter — DER vs peak VRAM/RAM | Second resource axis, if it tells a different story |
| V9 | Gantt/timeline — reference turns vs predicted turns on a shared time axis | 2-3 failure cases per system |

- One shared `SYSTEM_COLORS: dict[str, str]` mapping used by every chart that plots per-system data —
  defined once, imported everywhere, never redefined per chart.
- Consistent axis units and limits across systems/runtimes within each chart (e.g. V1's DER axis uses
  the same 0-to-max scale regardless of which system happens to be plotted).
- Every chart has a title, axis labels, and a legend (where more than one series is present).
- Callable both from the notebook (returns a `matplotlib.figure.Figure` or displays inline) and from
  `report.py` (returns a saved PNG path) — one function, both call sites, not two implementations.

### Out of scope
- Scoring (Phase 16, consumed as input). Report prose/assembly (Phase 18, which embeds these PNGs).
- Interactive/plotly variants — explicitly rejected by D7.

## Technical Approach
- `SYSTEM_COLORS` covers `pyannote`, `gemma-e2b`, `gemma-e4b`, `gemma-12b` and is defined at module
  level so every chart function imports the same dict; if a system is missing from a given run (e.g.
  12B blocked per Phase 14), that chart simply omits its bar/point rather than erroring or reassigning
  colors.
- V7's Pareto frontier: sort by DER ascending, walk the sorted list keeping only points whose RTF is
  lower than every prior kept point's RTF, plot that subset as a connected line overlaid on the
  scatter, and label it explicitly in the legend as "Pareto frontier" — this is the chart the
  recommendation leans on most, get it right.
- V9 needs 2-3 concrete failure cases per system, selected by Phase 18 (highest per-file DER, or a
  qualitatively interesting parse failure) and passed in as `(file_id, system_id)` pairs — V9's
  function itself is generic, it draws whatever reference/predicted turn pair it's given rather than
  picking cases itself.
- Each function signature: `def vN_name(df: pd.DataFrame, out_path: Path, **kwargs) -> Path`, saving a
  PNG at `out_path` and returning it, so `report.py` can call all nine in a loop with predictable paths.
- Use `seaborn` for grouped/stacked bars and consistent styling; keep custom matplotlib for V7's
  frontier overlay and V9's Gantt-style timeline, since neither maps cleanly onto a seaborn chart type.

## Acceptance Criteria
- [ ] All nine chart functions exist, each returns a saved PNG path that exists on disk.
- [ ] `SYSTEM_COLORS` is defined once and every chart function that plots per-system series imports it
      rather than defining local colors (grep-verified).
- [ ] Every chart has a non-empty title, non-empty axis labels on both axes, and a legend if more than
      one series is plotted (spot-checked visually for at least V1, V4, V7, V9).
- [ ] V7 visibly marks the Pareto frontier as a distinct line/marker style with its own legend entry,
      separate from the raw scatter points.
- [ ] Rendering the full chart set with one Gemma variant missing (simulate a 12B-blocked run per
      Phase 14) does not crash any of the nine functions — missing systems are simply absent from
      that chart, not an exception.
- [ ] Chart axis ranges for a shared metric (e.g. DER in V1 and V7) are consistent with each other
      within a single report render — not independently auto-scaled per chart.

## Test Instructions
```python
from benchmark import visualize, scoring, store
import pandas as pd
from pathlib import Path

df = pd.read_json("results/scores.jsonl", lines=True)  # Phase 16 output
out_dir = Path("results/charts")
paths = [
    visualize.v1_der_by_system(df, out_dir / "v1.png"),
    visualize.v2_der_components(df, out_dir / "v2.png"),
    visualize.v7_der_vs_rtf_pareto(df, out_dir / "v7.png"),
    visualize.v9_timeline(df, out_dir / "v9.png", cases=[("AMI/ES2004a", "pyannote")]),
]
for p in paths:
    assert p.exists()
print(paths)
```

## Docs Needed
- [ ] matplotlib/seaborn grouped and stacked bar chart APIs
- [ ] matplotlib Gantt/broken_barh usage for V9's timeline chart

## Notes
