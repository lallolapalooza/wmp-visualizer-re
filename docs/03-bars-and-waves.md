# 3. Bars and Waves

`Bars and Waves` is a collection implemented by a single COM class inside
`wmp.dll`. It exposes five presets; three are advertised in the UI.

## 3.1 Registration

```
HKLM\SOFTWARE\Microsoft\MediaPlayer\Objects\Effects\Bars\Properties
    classid     = {48501FF0-F6A9-11D2-9435-00A0C92A2F2D}
    name        = res://wmploc.dll/RT_STRING/#5500   ("Bars and Waves")
    description = res://wmploc.dll/RT_STRING/#5512
```

Preset titles come from the neighbouring strings:

| String id | Text |
|---|---|
| #5501 | Bars |
| #5502 | Ocean Mist |
| #5503 | Fire Storm |
| #5504 | Scope |

`#5512` reads: *"This collection includes the Bars, Ocean Mist and Fire Storm
visualizations."*

## 3.2 Implementation

| Property | Value |
|---|---|
| Class id | `{48501FF0-F6A9-11D2-9435-00A0C92A2F2D}` |
| Server | `%SystemRoot%\System32\wmp.dll` (Win7 SP1 build 7601, file 14,633,472 bytes) |
| Creator RVA | `0x5218C4` (wrapper `0x51D90C`, rejects aggregation) |
| Object size | `0x2B6B8` bytes (≈174 KB — it embeds its own effect/shift classes) |
| Vtables | `0x955390` (IWMPEffects2), `0x95F5C0`, `0x8FB8E0` (script/private interfaces) |
| IWMPEffects sub-object | +0x50 (vtable `0x8FB8E0`); private interfaces +0x00 (`0x955390`, IID `{33E9291A-…}`) and +0x08 (`0x95F5C0`, IID `{AEA0A1A1-…}`) |
| Render | slot 3 of `0x8FB8E0` = `0x51DBF8` — rejects null `TimedLevel*` and reads the rect edges |
| Preset validation | index compared against 4 (`preset ∈ [0,4]`) |

Interface map at `0xC251B0` (relative to the IWMPEffects sub-object at
+0x50): `{33E9291A-F6A9-11D2-9435-00A0C92A2F2D}` (private, +0),
`IDispatch` (+0), `IWMPEffects` (+0x50), `{AEA0A1A1-0423-11D3-BD3F-00C04F6EA5AE}`
(private, +0x08). Note there is **no** `IWMPEffects2` entry: Bars is a
windowless, `Render`-only visualizer.

## 3.3 The script surface (from the WMP type library)

`wmp.dll`'s type library (`TYPELIB #1`) defines `IBarsEffect`
(`{33E9291A-F6A9-11D2-9435-00A0C92A2F2D}`), a dual interface with the exact
knobs of the bar renderer:

| Property | Meaning (name-level) |
|---|---|
| `displayMode` | selects the drawing mode / preset family |
| `showPeaks` | draw peak caps |
| `peakHangTime` | how long a peak stays before falling |
| `peakFallbackSpeed`, `peakFallbackAcceleration` | gravity for peak caps |
| `levelFallbackSpeed`, `levelFallbackAcceleration` | decay for the bar levels |
| `backgroundColor`, `levelColor`, `peakColor` | colours (OLE colours) |
| `horizontalSpacing`, `levelWidth`, `levelScale` | bar geometry |
| `fadeRate`, `fadeMode` | trail/fade behaviour |
| `transparent` | draw over the background |

This is the complete parameter set needed to reproduce the "Bars" look. The
renderer is a peak-hold spectrum analyser; the other presets reuse the same
state machine with different `displayMode` drawing (waves / fire / scope).

## 3.4 What the presets are

* **Bars** — the classic analyser: symmetric frequency bars with a floor
  reflection. The host supplies 1024 bins; the effect aggregates them into a
  display-width number of bars.
* **Ocean Mist** — a smoothed, slowly moving waveform field; low-frequency
  energy drives the swell, high frequencies the shimmer.
* **Fire Storm** — a palette-driven flame: the spectrum is used as a heat
  source, with upward scrolling and a hot-colour ramp.
* **Scope** — a waveform oscilloscope (present but not advertised by the
  description string).

All four are **[inference]** from the names plus the shared renderer signature
(one `Render(TimedLevel*, HDC, RECT*)` entry with a preset switch). The binary
does not carry per-preset names in the code; the only strings are the
`wmploc` titles.

## 3.5 Renderer structure (verified details)

The `Render` body (`0x51DBF8`, 1048 bytes) is pure CPU work on memory
surfaces: it contains **no GDI/GDI+ import calls**, only calls to internal
helpers. It stores the destination width/height at object offsets `+0x550` /
`+0x554` from the RECT, then calls:

* `0x51E9E4` — rebuild the bin mapping for the current size/preset,
* `0x51E808` — bin aggregation helper,
* `0x51EACC` — peak/level update pass,
* `0x51E3D0`, `0x51E5A4` — two drawing passes,
* `0x51EDD4` — overlay/draw pass (uses 20.0 and 255.0 scale factors),
* `0x536810`, `0x536AF0` — surface fill/blit helpers.

Float constants found in these functions:

| Constant | Location | Meaning |
|---|---|---|
| `0.0078125` (1/128) | `0xC439C0` | frequency bin scale |
| `0.00390625` (1/256) | `0xC438E4` | secondary bin scale |
| `1024.0`, `0.0009765625` (1/1024) | `0x963FF4`, `0xC43B10` | full-buffer normalisation |
| `1.09`, `1.3` | `0xC43B70`, `0xC43B6C` | geometry/scale factors |
| `20.0`, `255.0` | `0xBD24B0`, `0x94A0E4` | fade fallback and colour range |

`SetCurrentPreset` (`0x51F3D4`) validates `preset <= 4`, stores it at
`+0x5D8`, and re-runs the bin-mapping setup.

## 3.6 Renderer structure

The render entry validates the level pointer, then dispatches on the current
preset (0..4). Each preset shares the same object state — the big 174 KB
allocation is mostly embedded per-preset tables and work buffers, not five
separate classes. If you re-implement it, model it as one class with a preset
enum and per-preset parameter blocks.

`SetCurrentPreset` (one of the small methods near `0x51F3D4`/`0x51FA6C`)
clamps/validates the index and resets the frame state; `GetPresetCount`
returns 5.

## 3.7 Minimal reimplementation

One class, five presets, one `Render` entry:

1. Down-mix `frequency[2][1024]` to N bars (N = width/2..width/8).
2. Apply a peak-hold envelope with hang time + fallback speed/acceleration
   (`IBarsEffect` names), then draw bars of `levelWidth` with
   `horizontalSpacing`, scaled by `levelScale`; optionally fade previous
   pixels at `fadeRate` in the `fadeMode` pattern.
3. For Ocean Mist / Fire Storm, keep the same peak machinery but render the
   level array as a smoothed wave field or a palette-driven heat field; use
   `waveform[]` directly for Scope.
3. Draw symmetrically about the vertical centre with a mirrored bottom half.
4. Keep the palette/colour ramp configurable; WMP skins can change it through
   the panel object.
