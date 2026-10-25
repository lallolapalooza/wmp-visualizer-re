# 5. Full catalog and installed-vs-registered state

WMP's visualization list is built from `wmploc.dll` strings plus the
`Objects\Effects` registry keys. The table below is the complete set of
collections and preset names found in the Win7 SP1 `wmploc.dll.mui` /
`wmploc.dll` resources.

## 5.1 Collections

| String | Name | Presets | Implementation |
|---|---|---|---|
| #5500 | Bars and Waves | Bars (#5501), Ocean Mist (#5502), Fire Storm (#5503), Scope (#5504) | `wmp.dll`, `{48501FF0-…}` |
| #1563 | Battery | 25 stored presets (see 04) | `wmp.dll`, `{8D2A317B-…}` |
| — | Alchemy | single | `mpvis.dll`, `{0AA02E8D-…}` |
| #5528 | Ambience | Random, Swirl, Warp, Anon, Falloff, Water, Bubble, Dizzy, Windmill, Niagara, Blender, X Marks the Spot, Down the Drain, Thingus | **not installed** in Win7 SP1 Ultimate (see 5.3) |
| #5530 | Plenoptic | Random, Smokey Circles, Smokey Lines, Vox, Flame, Fountain | **not installed** |
| #5513 | (legacy) | Spike, Amoeba | not installed; strings only |
| #5514 | (legacy) | Particle, Rotating Particle | not installed; strings only |

Preset names #5515–#5527 (Ambience), #5532–#5539 (Plenoptic) are present in
the MUI, so a Windows installation that has those DLLs will display exactly
those names.

## 5.2 Registry entries written by `wmp.dll`

`wmp.dll`'s register scripts (`REGISTRY #10110`, `#10147`, `#10159`, `#10121`)
create:

```
Objects\Effects\Bars      {48501FF0-F6A9-11D2-9435-00A0C92A2F2D}
Objects\Effects\Battery   {8D2A317B-D98B-4EFA-89D6-E49F0ACF98A1}
Objects\Effects\Ambience  {9CA6AD35-A548-4C7B-8E0A-EF29748FAA16}
Objects\Effects           {47DEA830-D619-4154-B8D8-6B74845D6A2D}
Objects\WMPEffects        {47DEA830-D619-4154-B8D8-6B74845D6A2D}
```

`mpvis.dll` writes `Objects\Effects\Alchemy {0AA02E8D-…}`.

`wmp.dll` also references legacy keys `Objects\Effects\{Dotplane, Plenoptic,
Spikes}` in its code (string constants), left over from WMP 9/10; no matching
implementation ships in Win7 SP1 Ultimate.

## 5.3 Installed vs. registered

Evidence that Ambience/Plenoptic are dead registrations on a stock Win7 SP1
Ultimate:

* `{9CA6AD35-A548-4C7B-8E0A-EF29748FAA16}` (Ambience) occurs **only** in the
  `wmp.dll` register script, not in any WMP binary (checked `mpvis.dll`,
  `wmp.dll`, `wmpdxm.dll`, `wmpeffects.dll`, `wmploc.dll`).
* The Win7 `Program Files\Windows Media Player\Visualizations` folder is
  empty.
* `wmp.dll` contains Bars/Battery/Alchemy class ids, but not Ambience's.
* `DirectShow`-era names (`Spikes`, `Dotplane`, `Plenoptic`) exist only as
  strings for upgrade paths.

Therefore a faithful re-implementation of "the Win7 SP1 visualizer set" needs
Alchemy, Bars and Waves, and Battery. The Ambience/Plenoptic names are useful
only if you want to reproduce WMP 9/10 behaviour.

## 5.4 The skin-facing panel

`Objects\WMPEffects` is the object a skin embeds as a control. Its
registration (resource `#10121`) declares:

```
width=250 height=200, stretch,
currentEffectType = wmpprop:mediacenter.effectType
currentPreset     = wmpprop:mediacenter.effectPreset
onclick           = next();
```

Its interface is `IWMPEffectsCtrl` (`{A9EFAB80-0A60-4C3F-BBD1-4558DD2A9769}`,
duplicated from the coclass `WMPEffects` `{47DEA830-…}`). It offers
`currentEffect`, `currentEffectType`, `currentEffectTitle`,
`currentEffectPresetCount`, `currentPreset`, `currentPresetTitle`,
`nextEffect`, `previousEffect`, `nextPreset`, `previousPreset`,
`showEffects`, `showResizeBars`, `effectPresetName`, `viewPresetName`,
`displayPreset`, `metadataPreset`, `settingsPreset`, `userWMPDisplayPreset`,
`hueShift`, `backHueShift`, `buttonHueShift`, `exclusiveHueShift`,
`backgroundImageHueShift`, `disableGlassBlurBackground`, and a
`PresetNameList`/`SelectPreset` pair (also mirrored as an MPRIS-like UPnP
`A_ARG_TYPE_PresetName`/`PresetNameList`).

A replacement only needs to expose the same properties if it wants to work
inside existing `.wmz` skins.
