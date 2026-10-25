# 1. The WMP visualization host contract

## 1.1 What a visualization is

A visualization is a COM in-proc server (`ThreadingModel=Apartment`) that
implements `IWMPEffects`, optionally `IWMPEffects2`. WMP loads it through
`DllGetClassObject`, creates the object once, then drives it from the UI
thread:

* `Create(hwnd)` / `Destroy()` for windowed presentation,
* `Render(...)` every frame,
* `RenderWindowed(...)` for the windowed panel variant,
* `RenderFullScreen(...)` when the user goes full screen,
* `MediaInfo`, `GetCapabilities`, `GetTitle`, preset methods, and
  `DisplayPropertyPage`.

Registration is data-driven. Each visualization adds a key under

```
HKLM\SOFTWARE\Microsoft\MediaPlayer\Objects\Effects\<Name>\Properties
    classid     = {CLSID}
    name        = res://<module>/RT_STRING/#<id>
    description = res://<module>/RT_STRING/#<id>
```

WMP builds its visualization list from these keys. Alchemy's install script
(`mpvis.dll` resource `REGISTRY #101`) registers `Alchemy`; `wmp.dll`
resources `#10110`, `#10147`, `#10159` register `Bars`, `Ambience`, `Battery`.

The skin engine uses a second object, `Objects\Effects` /
`Objects\WMPEffects`, class id `{47DEA830-D619-4154-B8D8-6B74845D6A2D}`
(implemented in `wmp.dll`). That object is the visualizer *panel*: it owns the
child effect, exposes `currentEffectType`, `currentPreset`, `next()`, and
forwards the render calls.

## 1.2 Interfaces and IIDs

From the type library embedded in `mpvis.dll` (resource `TYPELIB #1`,
LIBID `{C58F1580-0DF3-401C-93B1-2D9DDA61CF04}`) and from the community
`effects.h` translation:

| Interface | IID | Methods |
|---|---|---|
| `IWMPEffects` | `{D3984C13-C3CB-48E2-8BE5-5168340B4F35}` | Render, MediaInfo, GetCapabilities, GetTitle, GetPresetTitle, GetPresetCount, SetCurrentPreset, GetCurrentPreset, DisplayPropertyPage, GoFullscreen, RenderFullScreen |
| `IWMPEffects2` | `{695386EC-AA3C-4618-A5E1-DD9A8B987632}` | SetCore, Create, Destroy, NotifyNewMedia, OnWindowMessage, RenderWindowed |
| `IToleranceVis` (Alchemy private, dual) | `{9A85D909-C64A-4608-8DC4-76254D869553}` | foregroundColor, backgroundColor, miniMode, alpha, GetProperty, SetProperty |

`mpvis.dll`'s ATL interface map (`0x180020C90`) resolves, relative to the
object's primary sub-object:

* `IToleranceVis` and `IDispatch` → offset `0x00`
* `IWMPEffects` and `IWMPEffects2` → offset `0xC0`

The `IWMPEffects2` vtable in `mpvis.dll` is at RVA `0x20158`; the 20 slots map
to verified implementations (see `07-evidence-index.md`).

## 1.3 The audio buffer (`TimedLevel`)

WMP hands the visualization a stereo, 8-bit snapshot of the audio engine every
frame:

```c
struct TimedLevel {           // layout verified from code offsets
    uint8_t frequency[2][1024];  // +0x0000 .. +0x07FF  (per channel)
    uint8_t waveform [2][1024];  // +0x0800 .. +0x0FFF
    int32_t state;               // +0x1000  (0 = running, 1/2 = other states)
    int64_t timeStamp;           // +0x1008  [inference: older SDK layout]
};
```

Evidence: `mpvis.dll!Render` reads `*(int *)(levels + 0x1000)` to test state,
and the spectrum renderer reads `levels + i` and `levels + 0x400 + i`
simultaneously (two channels). `Bars`' render method rejects a null pointer
with `E_INVALIDARG` and then reads the same structure.

Values are unsigned bytes. A host implementation may produce them with any
FFT/AGC it likes; the visualizations only assume 0..255 magnitudes, low
frequencies first, 1024 bins per channel.

## 1.4 Method semantics observed

`MediaInfo(channels, sampleRate, title)` — stored; Alchemy keeps all three
(channels at +0x888, sample rate at +0x88C, title string at +0x890).

`GetCapabilities(dword*)` — Alchemy returns `0` (no fullscreen, no property
page, no variable frequency step). Bits defined by the SDK:
`1 = CANGOFULLSCREEN`, `2 = HASPROPERTYPAGE`, `4 = VARIABLEFREQSTEP`.

`GetTitle` / `GetPresetTitle` — load a `RT_STRING` resource:
Alchemy title `#100` ("Alchemy"), preset title `#117`.

`GetPresetCount` — Alchemy returns **1**; `SetCurrentPreset` is a no-op
returning `S_OK`; `GetCurrentPreset` returns 0.
Bars returns a small preset count and validates `preset <= 4`.
Battery's presets are much richer (see 04).

`DisplayPropertyPage` — Alchemy returns `E_NOTIMPL`.

`GoFullscreen(bool)` — Alchemy stores the flag at +0xCE1.
`RenderFullScreen` — Alchemy returns `S_OK` without drawing (stub).

`Create(hwnd)` — Alchemy stores the HWND, gets a window DC, and creates a
Direct3D 9 device (`Direct3DCreate9(0x20)`, i.e. `D3D_SDK_VERSION` 32).
`Destroy` releases the DC.

`Render(levels, hdc, rect)` — the main entry. Alchemy branches on an internal
mode at +0x80 (see 02).

`RenderWindowed(levels, required)` — separate path used by the panel host;
windowed rendering is also available through `Render` when mode is 0.

## 1.5 Registration details that matter for a replacement

* Alchemy's class is `{0AA02E8D-F851-4CB0-9F64-BBA9BE7A983D}`, name
  "AlchemyVis Class", `InprocServer32 = mpvis.dll`, `ThreadingModel=Apartment`,
  `TypeLib = {C58F1580-…}`, `Version = 1.0`.
* The install script deletes the legacy value
  `HKLM\SOFTWARE\Microsoft\MediaPlayer\Tolerance` (a Microsoft test harness
  key; see 02.6).
* A replacement can be registered exactly the same way; no signing or
  special interfaces are required.
