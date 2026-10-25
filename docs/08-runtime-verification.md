# 8. Runtime verification (Alchemy)

Static analysis is not proof of behaviour. This section records an actual
activation of the installed `mpvis.dll` (Windows 11 26100 build) through COM,
driven with synthetic `TimedLevel` data, and the pixels that came out.

Harness: `tools/smoke_alchemy.py` (ctypes, no WMP UI).

## 8.1 Sequence

```text
CoInitializeEx(STA)
CoCreateInstance({0AA02E8D-…}, IID_IWMPEffects2)      -> S_OK
GetTitle()                                            -> "Alchemy"
GetPresetCount()                                       -> 1
GetCapabilities()                                      -> 0
Create(hwnd 640x480)                                   -> S_OK
RenderWindowed(levels, required=1) x120                -> S_OK each time
desktop BitBlt of the window region                    -> captured
Destroy()                                              -> S_OK
Release()                                              -> refcount 0
```

`TimedLevel` was built as documented: 0x1010 bytes, `state` at +0x1000,
synthetic stereo FFT/waveform in the two 1024-byte arrays; `state` was set to
2 for five frames to exercise the paused branch.

## 8.2 Observed results

| Item | Result |
|---|---|
| Activation | `S_OK`; the returned interface is routed through `wmpps.dll`'s proxy in this environment (observed via `GetModuleHandleEx` on the vtable address) |
| Title / preset count / capabilities | `"Alchemy"`, `1`, `0` — exactly as the static analysis predicted |
| Render throughput | 120 frames in ~1.4 s (≈86 fps at 624×441) |
| Captured frame | 94.2 % non-black client pixels, >4096 distinct colours, mean RGB ≈ (42, 17, 50) |
| Evidence | `artifacts/alchemy_frame.png` (client area, 624×441) |
| Shutdown | `Destroy` `S_OK`, final refcount 0 |

The frame is the radial/kaleidoscopic Alchemy look (purple-dominant), which
matches the mode-2 polar renderer described in `02-alchemy.md`.

## 8.3 Findings that matter for a re-implementation

1. **`Render` is not a generic "draw into any HDC" call.** Calling slot 3
   directly with an offscreen DIB DC caused an access violation on a null
   pointer inside the D3D path. WMP's windowed host uses
   `RenderWindowed`, which fetches the window DC itself and calls `Render`
   internally. A re-implementation should either own the window (and its
   swap chain) or use a plain software path; do not feed it an arbitrary DC.
2. **D3D9 content is invisible to GDI window capture.** `PrintWindow` returned
   the window background only (one colour). Capturing the desktop region
   produced the real frame. Any automated visual test must use desktop
   capture, D3D readback, or `PW_RENDERFULLCONTENT` on a composited window.
3. **Activation may be proxied.** In this environment `CoCreateInstance`
   returned a proxy whose vtable lives in `wmpps.dll` (the WMP proxy/stub),
   even though the class is `InprocServer32` in `mpvis.dll`. Consequence:
   reading object fields through the returned pointer is meaningless; the
   proxy marshals calls. Behavioural calls still reach the real object.
4. **The object survives a 0.2 s+ render loop with state transitions** and
   shuts down cleanly, so the documented `Create`/`RenderWindowed`/`Destroy`
   lifecycle is correct.

## 8.4 Reproduce

```powershell
python tools/smoke_alchemy.py
```

Requires the Alchemy registration (`HKLM\…\CLSID\{0AA02E8D-…}` →
`mpvis.dll`) and an interactive desktop session (D3D9 + screen capture).
Output includes the HRESULT trace, throughput, pixel statistics, and writes
`artifacts/alchemy_frame.png`.
