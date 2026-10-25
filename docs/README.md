# Windows Media Player visualizations — reverse-engineering dossier

Target: the music visualizations shipped with Windows Media Player 12
(Windows 7 SP1 and later, including the legacy WMP still present in Windows 11).

Goal: enough behavioural and structural knowledge for another agent to build a
faithful re-implementation — **not** a pixel-exact clone. The emphasis is on
architecture, data formats, effect inventory, and algorithm families.

## Where the code lives

| Component | Binary | Notes |
|---|---|---|
| Alchemy visualizer | `%ProgramFiles%\Windows Media Player\mpvis.dll` | x64 + x86 copies. Registry class `AlchemyVis Class`. |
| Bars and Waves collection | `%SystemRoot%\System32\wmp.dll` | Class id `{48501FF0-F6A9-11D2-9435-00A0C92A2F2D}` |
| Battery collection | `%SystemRoot%\System32\wmp.dll` | Class id `{8D2A317B-D98B-4EFA-89D6-E49F0ACF98A1}` |
| Effects wrapper (skins) | `%SystemRoot%\System32\wmp.dll` | Class id `{47DEA830-D619-4154-B8D8-6B74845D6A2D}` |
| Names / descriptions | `%SystemRoot%\System32\wmploc.dll` + `en-US\wmploc.dll.mui` | `res://wmploc.dll/RT_STRING/#…` |
| Battery default presets | `wmp.dll` resource `REGISTRY #10160` | Also written to `HKCU\Software\Microsoft\MediaPlayer\Battery\Presets` |

All three visualizations are ordinary COM in-proc servers that implement the
public `IWMPEffects2` contract. WMP enumerates them from
`HKLM\SOFTWARE\Microsoft\MediaPlayer\Objects\Effects`.

Alchemy is a separate DLL; Bars and Battery are classes inside the 14.6 MB
`wmp.dll`. The Alchemy class id also appears in `wmp.dll`, but the registered
server is `mpvis.dll`.

## Verification status

Everything in `01`–`05` is derived from the binaries and their resources
(strings, type libraries, registry scripts, class tables, vtables, decompiled
functions). Where a conclusion is behavioural inference rather than a directly
observed constant, it is marked **[inference]**.

Read in this order:

1. [01-host-contract.md](01-host-contract.md) — the plugin ABI WMP gives you.
2. [02-alchemy.md](02-alchemy.md) — Alchemy's render engine and effect cycle.
3. [03-bars-and-waves.md](03-bars-and-waves.md) — Bars / Ocean Mist / Fire Storm.
4. [04-battery.md](04-battery.md) — the preset-driven Battery engine.
5. [05-catalog.md](05-catalog.md) — every collection/preset name WMP knows,
   including ones whose DLL is not present on a stock Windows 7 SP1 install.
6. [06-reimplementation-guide.md](06-reimplementation-guide.md) — how to build
   an equivalent system from scratch.
7. [07-evidence-index.md](07-evidence-index.md) — files, hashes, RVAs, commands.
8. [08-runtime-verification.md](08-runtime-verification.md) — live COM test,
   captured frame, and behavioural caveats.

## Tooling used

* Ghidra 12.2 PUBLIC, headless (`analyzeHeadless`), Temurin JDK 21.
* `pefile`, `capstone`, `comtypes` for PE resources, TLB parsing, disassembly.
* Registry and `.rgs` (ATL register-script) resources extracted from the PE.
* Windows 7 SP1 Ultimate x64 `install.wim` (archive.org item
  `microsoft-windows-7-ultimate-with-service-pack-1-64-bit`), files extracted
  with `wimlib-imagex 1.14.5`.

## Legal / scope note

The binaries are Microsoft proprietary code. This dossier documents behaviour,
formats and interfaces for interoperability; it contains no copied source or
large verbatim code excerpts. Do not redistribute the extracted binaries or
the ISO. Names such as `Battery`, `Alchemy` and preset titles are quoted only
as identifiers.
