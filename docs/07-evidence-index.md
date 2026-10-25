# 7. Evidence index

Everything in this dossier traces to the files and offsets below. Reproduce by
extracting the same binaries and re-running the same tools.

## 7.1 Binaries

| File | Size | SHA-256 |
|---|---|---|
| `mpvis.dll` (Windows 11 26100 x64) | 221,184 | `29e82ec635a05f7b9d072c53d0d33f57b7fdf0b49ded274660f0f51dbc4b1299` |
| Win7 SP1 `mpvis.dll` | 293,376 | `5b1cf8de17dc039349e1af0bc0d728e3de3c0a96d9c50e81fc909b8ceb4927e0` |
| Win7 SP1 `wmp.dll` | 14,633,472 | `601a529eb775d0034c9f98755aa9e9191d546bcf4a7493d08294649120e96c52` |
| Win7 SP1 `wmploc.dll` | 12,625,920 | `4d66bc57ac6fb03b9fc9a554cb039faa8460cda9d25c078ae9421a9648809566` |

Win7 files extracted from
`install.wim` index 4 (Windows 7 ULTIMATE) of the archive.org item
`microsoft-windows-7-ultimate-with-service-pack-1-64-bit` with
`wimlib-imagex 1.14.5`.

Type library: `mpvis.dll` resource `TYPELIB #1`, LIBID
`{C58F1580-0DF3-401C-93B1-2D9DDA61CF04}`. It defines `IToleranceVis`
(`{9A85D909-C64A-4608-8DC4-76254D869553}`), 17 methods (7 `IDispatch` +
`foregroundColor`, `backgroundColor`, `miniMode`, `alpha`, `GetProperty`,
`SetProperty`).

## 7.2 Alchemy addresses (x64, image base `0x180000000`)

| RVA | What |
|---|---|
| `0x28000` | one-entry class table `{CLSID 0x22498, 0x6350, 0x4250, 0x4050, …}` |
| `0x4250` | factory for the 0x40-byte helper object |
| `0x4050` / `0x4064` | factory for the main 0xDF8-byte object |
| `0x33BC` | `DllGetClassObject` core |
| `0x20158` | `IWMPEffects2` vtable (20 slots) |
| `0x202D0`, `0x20230`, `0x201F8` | additional interface vtables installed at +0, +0x10, +0x18 |
| `0x20C90` | ATL interface map (`IToleranceVis`/`IDispatch` @0, `IWMPEffects`/`IWMPEffects2` @0xC0) |
| `0x8170` | `Render` |
| `0x8364` | fullscreen/spectrum renderer (mode 1) |
| `0x8A6C` | polar kaleidoscope renderer (mode 2) |
| `0x8E50` | `RenderWindowed` |
| `0x7540` | `Create` (Direct3DCreate9, window DC) |
| `0x76B0` | `Destroy` (ReleaseDC) |
| `0x7F40` | `MediaInfo` |
| `0x7E90` | `GetTitle` → string resource 100 |
| `0x7E00` | `GetPresetTitle` → string resource 117 |
| `0x7DF0` | `GetPresetCount` → 1 |
| `0x7DE0` | `GetCurrentPreset` → 0 |
| `0x7890` | `DisplayPropertyPage` → E_NOTIMPL |
| `0x7F20` | `GoFullscreen` |
| `0x92E0` | `SetCore` |
| `0x8080` | `OnWindowMessage` → 1 |
| `0x4470` | shared stub returning 0 (SetCurrentPreset / RenderFullScreen / NotifyNewMedia) |
| `0x9A94` | default render-cycle builder |
| `0x9EB0` | `BlurSwitch` builder (10 children) |
| `0x9E48` | adds a cycle transition entry |
| `0x9D38` | cycle object constructor (defaults 1000/5000 ms, rate 1.0, 4 slots) |
| `0x9B0/+0x9B8/+0x9C0` | three render surfaces (object fields) |
| `0xAD94` | base effect constructor (`Unnamed Effect`, id 6) |
| `0xC004` | `UnnamedRenderEffect` ctor (id 7) |
| `0xC058` | `Blur` ctor (id 8) |
| `0xC62C` | `BlurSwitch` ctor (id 9) |
| `0xD8B0` | `BlurSwitch` render |
| `0xF8EC` | `ShiftBackgroundBuild` ctor (id 12) |
| `0xFE50` | `ShiftBackgroundBuild` render |
| `0xF960` | `StrongSuperStar` ctor (id 13) |
| `0x10120` | `StrongSuperStar` render |
| `0xFA0C` | `SoftSmear` ctor (id 17) |
| `0x10380` | `SoftSmear` render |
| `0x111BC` | StretchBlt variant ctor (id 6, vtable `0x20980`) |
| `0x282E0` | profiler name/id table (24-byte entries, ids 1–18) |
| `0x28280` | 12 patchable function pointers used by D3DX PSGP dispatch |
| `0x221F8` | IID_IWMPEffects bytes |
| `0x22498` | CLSID_Alchemy bytes |
| `0x224A8` | LIBID_mpvis bytes |

## 7.3 Win7 `wmp.dll` addresses

Image base `0x7FF501F0000`, `.text` at RVA `0x1000` (raw `0x600`),
`.rdata` RVA `0x8D2000` (raw `0x8CF600`), `.data` RVA `0xC82000` (raw `0xC7F000`).

| RVA | What |
|---|---|
| `0x1A3270` / `0x1A3290` | globals initialised at runtime with the class table |
| `0xC83270` | pointer used by `DllRegisterServer` iteration |
| `0xC83290` | class-table base global (zero in file; set in DllMain) |
| `0xC831E0` | class-table entry for `{47DEA830-…}` (Effects wrapper; create `0xFF0A8`, register `0x521AF0`) |
| `0xC835A0` | entry for Bars (`{48501FF0-…}`; create `0x51D90C`, register `0x51D880`) |
| `0xC835C0` | entry for Battery (`{8D2A317B-…}`; create `0x7BA120`, data `0x27AF`) |
| `0x51D90C` | Bars create wrapper (aggregation check → `0x5218C4`) |
| `0x5218C4` | Bars object creator (size `0x2B6B8`) |
| `0x955390` | Bars `IWMPEffects2` vtable (slot 3 `Render = 0x2F46B4`) |
| `0x95F5C0`, `0x8FB8E0` | Bars secondary vtables |
| `0x2F46B4` | Bars `Render` |
| `0x7BA120` | Battery create wrapper (→ `0x7BD0F4`) |
| `0x7BD0F4` | Battery object creator (size `0xFF0`) |
| `0x7BD1E8` | Battery constructor |
| `0xEE6DC` | `DllGetClassObject` export |
| `0x21DE80` | `DllRegisterServer` export |
| `0x1010` | ATL `InternalQueryInterface` helper (IID compare) |

Type library `wmp.dll` resource `TYPELIB #1` (213,820 bytes, extracted as
`artifacts/wmp.tlb`) defines the visualization script surfaces:

| Interface | IID | Members |
|---|---|---|
| `IWMPEffectsCtrl` | `{A9EFAB80-0A60-4C3F-BBD1-4558DD2A9769}` | windowed, allowAll, currentEffect(Type/Title), next/previous, settings, next/previousEffect, next/previousPreset, currentPreset(Title), currentEffectPresetCount, fullScreen, effectCanGoFullScreen, effectHasPropertyPage, effectCount, effectTitle, effectType |
| `IBarsEffect` | `{33E9291A-F6A9-11D2-9435-00A0C92A2F2D}` | displayMode, showPeaks, peakHangTime, peak/level FallbackSpeed/Acceleration, backgroundColor, levelColor, peakColor, horizontalSpacing, levelWidth, levelScale, fadeRate, fadeMode, transparent |
| `IBattery` | `{F8578BFA-CD8F-4CE1-A684-5B7E85FCA7DC}` | presetCount, preset(i) |
| `IBatteryPreset` | `{40C6BDE7-9C90-49D4-AD20-BEF81A6C5F22}` | title |
| `IBatteryRandomPreset` | `{F85E2D65-207D-48DB-84B1-915E1735DB17}` | title |
| `IBatterySavedPreset` | `{876E7208-0172-4EBB-B08B-2E1D30DFE44C}` | title |
| `WMPEffects` (coclass) | `{47DEA830-D619-4154-B8D8-6B74845D6A2D}` | panel object |

Windows 7 `wmploc.dll` resources used for names: RT_STRING ids `5500`–`5539`
and `1563`–`1565` (the localized copies live in the corresponding `.mui`; on
Windows 11 the file is `System32\en-US\wmploc.dll.mui`).

## 7.4 Registry scripts

Extracted as UTF-16 text:

| File | Content |
|---|---|
| `mpvis.dll` `REGISTRY #101` | CLSID Alchemy, `Objects\Effects\Alchemy` |
| `wmp.dll` `REGISTRY #10110` | Bars registration |
| `wmp.dll` `REGISTRY #10147` | Ambience registration |
| `wmp.dll` `REGISTRY #10159` | Battery registration |
| `wmp.dll` `REGISTRY #10160` | 25 default Battery presets (incl. 1024-byte palettes) |
| `wmp.dll` `REGISTRY #10121` | Effects/WMPEffects panel object |

## 7.5 Tooling / commands

```text
# resources and class tables
python -c "import pefile; ..."            # see artifacts/*.py transcripts
# decompilation
analyzeHeadless.bat proj wmp -import artifacts/bin/mpvis_x64.dll \
    -scriptPath tools/ghidra_scripts -postScript DumpAll.java artifacts/decomp_x64
# Win7 extraction
wimlib-imagex.exe extract install.wim 4 "\Windows\System32\wmp.dll" --dest-dir=...
wimlib-imagex.exe extract install.wim 4 "\Program Files\Windows Media Player\mpvis.DLL" --dest-dir=...
# type library
python -c "import comtypes.typeinfo as ti; ti.LoadTypeLibEx('artifacts/mpvis.tlb')"
```

Regenerate the decompiled corpus with `tools/ghidra_scripts/DumpAll.java`; the
output used here is in `artifacts/decomp_x64/` (615 functions, 660 symbols
including imports).

## 7.6 Automated re-check

`tools/verify_docs.py` asserts the numeric claims above against the extracted
binaries: CLSID presence, class-table entries, all 17 mapped
`IWMPEffects2` slots, the profiler name table, the 25 presets, the 1024-byte
palette, and the GUID bytes in both `mpvis.dll` and Win7 `wmp.dll`.
Last run: **all checks pass**.

## 7.7 Confidence

| Claim | Confidence |
|---|---|
| Interface IIDs, method order, TimedLevel layout | High (typelib + vtable + code) |
| Alchemy effect inventory, cycle program, modes | High (code + strings) |
| Bars/Battery class ids, creators, object sizes, preset storage | High |
| Per-preset drawing algorithms for Bars | Medium (names + signatures; no decompiled body in this pass) |
| Exact meaning of each Battery `dbl1..dbl8` | Low–medium (data patterns only) |
| Ambience/Plenoptic not installed | High for Win7 SP1 Ultimate media; may differ in other SKUs |
