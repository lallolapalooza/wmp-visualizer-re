# 6. Reimplementation guide

This is the practical "build it from the dossier" plan. It targets behavioural
fidelity, not bit-exact output.

## 6.1 Host side (if you are replacing WMP's host)

1. Produce a 30–60 fps loop.
2. Each tick build a `TimedLevel`:
   * stereo, 1024 bins, 0..255;
   * `frequency[ch][i]` from an FFT (log or linear binning; the effects only
     need low-frequency energy in low indices);
   * `waveform[ch][i]` as the time-domain signal mapped to 0..255;
   * `state = 0` while playing; the visualizers special-case 1/2 as
     "paused/stopped" snapshots.
3. Call `Render(levels, hdc, rect)` for windowless drawing, or
   `RenderWindowed(levels, required)` when you have given the effect a window
   through `Create`.
4. Provide `MediaInfo(channels, sampleRate, title)` once per track.
5. Honour `GetCapabilities` bits when deciding whether to offer full screen or
   a property page.

## 6.2 Plugin side (if you are writing a compatible visualization)

Minimal COM server:

* `DllGetClassObject` → class factory → object implementing IUnknown,
  `IWMPEffects`, `IWMPEffects2`.
* Register `InprocServer32`, `ThreadingModel=Apartment`, and the
  `Objects\Effects\<Name>\Properties` key.
* `GetTitle`/`GetPresetTitle` may return strings from your own resources.
* `GetCapabilities` returns 0 for a windowed-only effect.
* `Render` must be fast: the host calls it every frame while the panel is
  visible.

Reference slot order (verified from both Alchemy and Bars binaries):

```
0 QueryInterface        6 GetTitle             12 GoFullscreen
1 AddRef                7 GetPresetTitle       13 RenderFullScreen
2 Release               8 GetPresetCount       14 SetCore
3 Render                9 SetCurrentPreset     15 Create
4 MediaInfo            10 GetCurrentPreset     16 Destroy
5 GetCapabilities      11 DisplayPropertyPage  17 NotifyNewMedia
                                               18 OnWindowMessage
                                               19 RenderWindowed
```

`IWMPEffects2` inherits the first 14 slots; the last six are its additions.

## 6.3 Alchemy-style engine

1. Three render targets (background / effect / composite), 32-bit BGRA.
2. Effect list where each effect implements:
   * `render(levels, src, dst)`,
   * `setParams(name, values)`,
   * optional state machine: `idle → fade-in → hold → fade-out`.
3. Ping-pong: effects read `src` and write `dst`, then swap.
4. Cycle scheduler with per-entry `{effect, flagA, flagB, timeA, timeB, mode}`
   (the shipped program is in `02-alchemy.md`).
5. Direct modes: 256-bin spectrum with 2/frame peak decay, or the 6-bin polar
   kaleidoscope with horizontal + vertical mirroring.
6. Composite with `StretchBlt` (or a D3D9 quad). Keep a `ForceDDraw`/software
   fallback.

## 6.4 Battery-style engine

1. Preset loader for the registry/`.bpx` schema (Section 4.2).
2. Palette: 256 BGRA entries; optional hue rotation when
   `PaletteLocked = 0`.
3. Layering: pre-shifts (bottom-up), current shift, post-shifts (top-down);
   each is `(class, double[8])`.
4. Implement shifts as small pixel operators over the target surface:
   * plane/pattern (dots, tiles, lines),
   * edge/waveform tracers (spectrum- or waveform-driven),
   * affine/motion (linear, stretch, swirl, ring-spin, zoom, starburst,
     twirl),
   * ink/scribble overlays.
5. Random mode: pick a random preset, optionally randomize palette/hue and
   parameter jitter.

## 6.5 Bars-style engine

One class, preset enum, shared FFT input:

* Bars: N-bin columns, peak-hold with gravity, mirrored reflection.
* Ocean Mist: low-pass filtered bins driving a sinusoidal swell field.
* Fire Storm: heat buffer + upward advection + palette ramp.
* Scope: raw waveform polyline.

## 6.6 Fidelity notes

* WMP's `frequency[]` is 8-bit and already scaled; do not assume linear FFT
  magnitudes. Apply AGC/compression similar to the host, or visualizations
  will look either flat or saturated.
* All surface code is BGRA with stride `width*4`; effects that look at
  neighbours use ±1 pixel and ±width.
* Timing is frame-based (30 or 60 fps), not wall-clock: durations in the
  cycle table are frame counts (e.g. 500 ≈ 8 s at 60 fps).
* The original engine mixes D3D9 and GDI/GDI+; a pure software compositor
  reproduces the look with far less code. Use D3D only if you need the
  stretch/filtering behaviour.
