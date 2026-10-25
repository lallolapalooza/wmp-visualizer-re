# Windows Media Player visualizations — reverse-engineering dossier

Behavioural and structural documentation of WMP 12's music visualizations,
produced by static analysis (Ghidra 12.2 headless) and a live COM test:

* **Alchemy** — `mpvis.dll`, `{0AA02E8D-F851-4CB0-9F64-BBA9BE7A983D}`
* **Bars and Waves** — `wmp.dll`, `{48501FF0-F6A9-11D2-9435-00A0C92A2F2D}`
* **Battery** — `wmp.dll`, `{8D2A317B-D98B-4EFA-89D6-E49F0ACF98A1}`

The goal is enough knowledge for another agent or developer to re-implement the
visualizations, not a pixel-exact clone.

## Contents

| Path | What |
|---|---|
| [`docs/01-host-contract.md`](docs/01-host-contract.md) | `IWMPEffects`/`IWMPEffects2`, `TimedLevel`, registration, presets |
| [`docs/02-alchemy.md`](docs/02-alchemy.md) | Alchemy engine: 3-surface pipeline, effect cycle, render modes, parameter vocabulary |
| [`docs/03-bars-and-waves.md`](docs/03-bars-and-waves.md) | `IBarsEffect` surface, presets, renderer constants |
| [`docs/04-battery.md`](docs/04-battery.md) | Battery preset schema, 23 shift classes, palettes, 25 shipped presets |
| [`docs/05-catalog.md`](docs/05-catalog.md) | Every collection/preset name WMP knows, installed vs. registered |
| [`docs/06-reimplementation-guide.md`](docs/06-reimplementation-guide.md) | Build plan for a compatible host/plugin |
| [`docs/07-evidence-index.md`](docs/07-evidence-index.md) | Hashes, RVAs, resource ids, confidence levels |
| [`docs/08-runtime-verification.md`](docs/08-runtime-verification.md) | Live COM test, captured frame, behavioural caveats |
| `docs/assets/alchemy_frame.png` | Frame captured from the live visualizer (research evidence) |
| `tools/verify_docs.py` | Re-checks every numeric claim against extracted binaries |
| `tools/smoke_alchemy.py` | Drives `IWMPEffects2` through COM with synthetic audio |
| `tools/ghidra_scripts/` | Headless scripts used to dump functions and call-graph slices |
| `archive/omp-archive-…zip` | Full session archive produced with [omp-archive](https://github.com/alosslessdev/omp-archive-main) |

## Key results

* Alchemy is not a single effect: it is a small compositor with three render
  targets, a timed cycle of procedural effects (blur, multi-tap filter, star
  burst, scrolling background, scaled blit, random smear), plus two direct
  GDI+ modes — a 256-bin spectrum analyser and a 6-bin polar kaleidoscope.
* Bars and Waves is a peak-hold spectrum renderer with five presets; its entire
  parameter set is exposed through `IBarsEffect`.
* Battery is data-driven: 25 registry presets, each an ordered stack of
  pre/current/post "shifts" with eight doubles each and a 256-entry BGRA
  palette.
* Ambience and Plenoptic are registered by `wmp.dll` but no implementing binary
  ships in Windows 7 SP1 Ultimate.

Runtime check: `CoCreateInstance` → `GetTitle` = "Alchemy", preset count 1,
capabilities 0, 120 frames at ~86 fps, captured frame 94 % non-black,
`Destroy`/`Release` clean.

## Reproducing the evidence

The Microsoft binaries are **not** part of this repository. To re-run the
analysis you need your own licensed copies:

* `%ProgramFiles%\Windows Media Player\mpvis.dll` (Alchemy)
* Windows 7 SP1 `wmp.dll` and `wmploc.dll` (Bars/Battery; extracted from
  `install.wim`)

Then:

```powershell
python tools/verify_docs.py     # expects artifacts/ laid out as in docs/07
python tools/smoke_alchemy.py   # needs an interactive desktop session
```

## Session archive

`archive/omp-archive-wmp-visualizer-re.zip` is the complete research record:
main transcript, tool logs (untruncated), job state, and a standalone
`viewer.html`. It is **verbatim and unredacted**, including local paths and
command output. It may contain short excerpts of decompiled proprietary code
used as evidence; it contains no Microsoft binaries.

## Legal

This is independent interoperability research. No Microsoft source code or
binaries are redistributed. Names such as *Alchemy*, *Bars and Waves* and
*Battery* are used only as identifiers. See [DISCLAIMER.md](DISCLAIMER.md).

Original text and scripts: MIT — see [LICENSE](LICENSE).
