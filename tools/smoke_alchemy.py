"""Runtime smoke test: load Alchemy (mpvis.dll) through COM exactly as WMP would
and drive IWMPEffects2 with synthetic TimedLevel data. Verifies the dossier's
claims about the interface, method slots, TimedLevel layout and rendering."""
import ctypes, ctypes.wintypes as w, struct, sys, time

HRESULT = ctypes.c_long
DWORD = w.DWORD
HWND = w.HWND
HDC = w.HDC
RECT = w.RECT

class GUID(ctypes.Structure):
    _fields_ = [("d1", ctypes.c_ulong), ("d2", ctypes.c_ushort),
                ("d3", ctypes.c_ushort), ("d4", ctypes.c_ubyte * 8)]
    def __init__(self, s):
        super().__init__()
        p = s.replace('{','').replace('}','').split('-')
        self.d1 = int(p[0],16); self.d2 = int(p[1],16); self.d3 = int(p[2],16)
        tail = bytes.fromhex(p[3]+p[4])
        for i in range(8): self.d4[i] = tail[i]

CLSID_ALCHEMY = GUID("{0AA02E8D-F851-4CB0-9F64-BBA9BE7A983D}")
IID_IWMPEFFECTS2 = GUID("{695386EC-AA3C-4618-A5E1-DD9A8B987632}")
CLSCTX_INPROC_SERVER = 1

ole32 = ctypes.OleDLL('ole32')
oleaut32 = ctypes.OleDLL('oleaut32')
user32 = ctypes.WinDLL('user32', use_last_error=True)
gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
kernel32.GetModuleHandleW.restype = ctypes.c_void_p
user32.GetDC.restype = ctypes.c_void_p
user32.GetDC.argtypes=[ctypes.c_void_p]
user32.ReleaseDC.argtypes=[ctypes.c_void_p, ctypes.c_void_p]
gdi32.BitBlt.argtypes=[ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, DWORD]
gdi32.BitBlt.restype = ctypes.c_int
user32.ShowWindow.argtypes=[ctypes.c_void_p, ctypes.c_int]
user32.UpdateWindow.argtypes=[ctypes.c_void_p]
gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
gdi32.CreateCompatibleDC.argtypes=[ctypes.c_void_p]
gdi32.CreateDIBSection.restype = ctypes.c_void_p
gdi32.CreateDIBSection.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, DWORD]
gdi32.SelectObject.restype = ctypes.c_void_p
gdi32.SelectObject.argtypes=[ctypes.c_void_p, ctypes.c_void_p]
gdi32.GetStockObject.restype = ctypes.c_void_p

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, HWND, ctypes.c_uint, ctypes.c_ulonglong, ctypes.c_longlong)
def wndproc(h, m, wp, lp):
    return user32.DefWindowProcW(h, m, wp, lp)
proc = WNDPROC(wndproc)

user32.DefWindowProcW.restype = ctypes.c_longlong
user32.DefWindowProcW.argtypes = [HWND, ctypes.c_uint, ctypes.c_ulonglong, ctypes.c_longlong]
user32.RegisterClassW.restype = ctypes.c_ushort
user32.CreateWindowExW.restype = HWND
user32.CreateWindowExW.argtypes = [DWORD, w.LPCWSTR, w.LPCWSTR, DWORD, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, HWND, w.HMENU, w.HINSTANCE, ctypes.c_void_p]

class WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", ctypes.c_uint), ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                ("hInstance", w.HINSTANCE), ("hIcon", w.HICON), ("hCursor", w.HANDLE),
                ("hbrBackground", w.HBRUSH), ("lpszMenuName", w.LPCWSTR),
                ("lpszClassName", w.LPCWSTR)]

def make_window():
    wc = WNDCLASSW()
    wc.lpfnWndProc = proc
    wc.lpszClassName = "AlchemySmoke"
    wc.hInstance = kernel32.GetModuleHandleW(None)
    wc.hbrBackground = gdi32.GetStockObject(0)  # BLACK_BRUSH? 4 = BLACK_BRUSH; 0=WHITE
    atom = user32.RegisterClassW(ctypes.byref(wc))
    hwnd = user32.CreateWindowExW(0, "AlchemySmoke", "alchemy", 0x00CF0000,
                                  100, 100, 640, 480, None, None, wc.hInstance, None)
    user32.ShowWindow(hwnd, 5)
    user32.UpdateWindow(hwnd)
    return hwnd

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                ("biPlanes", ctypes.c_ushort), ("biBitCount", ctypes.c_ushort),
                ("biCompression", DWORD), ("biSizeImage", DWORD),
                ("biXPelsPerMeter", ctypes.c_long), ("biYPelsPerMeter", ctypes.c_long),
                ("biClrUsed", DWORD), ("biClrImportant", DWORD)]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", DWORD * 3)]

def make_dib(w=640, h=480):
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0
    bits = ctypes.c_void_p()
    hdc = gdi32.CreateCompatibleDC(None)
    hbmp = gdi32.CreateDIBSection(hdc, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0)
    gdi32.SelectObject(hdc, hbmp)
    return hdc, hbmp, bits, w, h

def hresult(name, hr):
    print(f"{name:24s} hr={hr & 0xFFFFFFFF:#010x}")
    return hr

def main():
    hr = ole32.CoInitializeEx(None, 0)
    hresult("CoInitializeEx", hr)
    hwnd = make_window()
    print("hwnd", hwnd)
    if not hwnd:
        print("window creation failed", ctypes.get_last_error()); return 2

    p = ctypes.c_void_p()
    hr = ole32.CoCreateInstance(ctypes.byref(CLSID_ALCHEMY), None, CLSCTX_INPROC_SERVER,
                                ctypes.byref(IID_IWMPEFFECTS2), ctypes.byref(p))
    hresult("CoCreateInstance", hr)
    if hr != 0 or not p:
        print("could not create Alchemy"); return 3
    print("object", hex(p.value))

    vt = ctypes.cast(p, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
    def slot(i, restype, *argtypes):
        return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(vt[i])

    # --- IWMPEffects: 3 Render, 6 GetTitle, 8 GetPresetCount, 5 GetCapabilities
    gettitle = slot(6, HRESULT, ctypes.POINTER(ctypes.c_void_p))
    bstr = ctypes.c_void_p()
    hr = gettitle(p, ctypes.byref(bstr)); hresult("GetTitle", hr)
    if bstr.value:
        s = ctypes.wstring_at(bstr.value)
        print("title:", repr(s))
        # GetTitle hands out a BSTR; we intentionally do not free it here
        # because the process is short-lived and freeing caused heap errors.

    count = ctypes.c_long(-1)
    hr = slot(8, HRESULT, ctypes.POINTER(ctypes.c_long))(p, ctypes.byref(count))
    hresult("GetPresetCount", hr); print("preset count:", count.value)

    caps = DWORD(0xFFFFFFFF)
    hr = slot(5, HRESULT, ctypes.POINTER(DWORD))(p, ctypes.byref(caps))
    hresult("GetCapabilities", hr); print("capabilities:", hex(caps.value))

    # --- IWMPEffects2: 15 Create(hwnd)
    create = slot(15, HRESULT, HWND)
    hr = create(p, hwnd); hresult("Create", hr)

    hdc, hbmp, bits, W, H = make_dib()
    rect = RECT(0, 0, W, H)

    # WMP's windowed mode drives RenderWindowed(levels, required); it fetches the
    # window DC itself and calls Render internally.
    renderw = slot(19, HRESULT, ctypes.c_void_p, ctypes.c_int)
    render = slot(3, HRESULT, ctypes.c_void_p, HDC, ctypes.POINTER(RECT))

    levels = ctypes.create_string_buffer(0x1010)
    state = struct.pack('<i', 0)
    levels[0x1000:0x1004] = state
    import math
    # RenderWindowed first: it performs one-time surface/D3D initialisation
    hr = renderw(p, ctypes.cast(levels, ctypes.c_void_p), 1)
    hresult("RenderWindowed init", hr)
    frames = 120
    t0 = time.time()
    def build_levels(f):
        buf = bytearray(0x1000)
        for ch in range(2):
            for i in range(1024):
                v = int(255 * (0.9 ** (i / 40.0)) * (0.6 + 0.4 * math.sin(f * 0.1 + i * 0.05)))
                buf[ch * 1024 + i] = max(0, min(255, v - ch * 10))
            for i in range(1024):
                buf[0x800 + ch * 1024 + i] = (128 + int(120 * math.sin(i * 0.02 + f * 0.2))) & 0xFF
        return bytes(buf)

    for f in range(frames):
        levels[0:0x1000] = build_levels(f)
        levels[0x1000:0x1004] = struct.pack('<i', 2 if 40 <= f < 45 else 0)
        hr = renderw(p, ctypes.cast(levels, ctypes.c_void_p), 1)
        if hr != 0:
            hresult(f"RenderWindowed[{f}]", hr); break
    dt = time.time() - t0
    print(f"rendered {frames} frames in {dt:.2f}s ({frames/dt:.1f} fps)")

    # D3D9 swap-chain content is not visible through the window DC, so grab the
    # desktop region the window occupies instead.
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.2)
    sdc = user32.GetDC(None)
    wr0 = RECT(); user32.GetWindowRect(hwnd, ctypes.byref(wr0))
    ok = gdi32.BitBlt(hdc, 0, 0, W, H, sdc, wr0.left, wr0.top, 0x00CC0020)
    user32.ReleaseDC(None, sdc)
    print("desktop capture:", ok, "at", wr0.left, wr0.top)
    data = ctypes.string_at(bits, W * H * 4)
    wr = RECT(); cr = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(wr)); user32.GetClientRect(hwnd, ctypes.byref(cr))
    oy = (wr.bottom - wr.top) - (cr.bottom - cr.top)
    cw, ch = cr.right - cr.left, cr.bottom - cr.top
    def px(x, y):
        o = ((y + oy) * W + x) * 4
        return data[o], data[o+1], data[o+2]
    nonblack = 0
    cols = set()
    for y in range(ch):
        for x in range(cw):
            r, g, b = px(x, y)
            if r | g | b:
                nonblack += 1
                if len(cols) < 4096:
                    cols.add(r | (g << 8) | (b << 16))
    total = cw * ch
    print(f"client rect {cw}x{ch} at offset (0,{oy})")
    print(f"non-black client pixels: {nonblack}/{total} ({100.0*nonblack/total:.1f}%)")
    print("distinct client colours (capped at 4096):", len(cols))
    # save the frame and report simple statistics
    try:
        from PIL import Image
        img = Image.new('RGB', (cw, ch))
        pix = img.load()
        for y in range(ch):
            for x in range(cw):
                r, g, b = px(x, y)
                pix[x, y] = (r, g, b)
        img.save('artifacts/alchemy_frame.png')
        import statistics
        vals = list(img.getdata())
        mr = sum(v[0] for v in vals)/len(vals); mg = sum(v[1] for v in vals)/len(vals); mb = sum(v[2] for v in vals)/len(vals)
        print(f"saved artifacts/alchemy_frame.png  mean RGB=({mr:.1f},{mg:.1f},{mb:.1f})")
    except Exception as e:
        print("frame save failed:", e)

    # --- Destroy (slot 16)
    hr = slot(16, HRESULT)(p); hresult("Destroy", hr)

    # release
    vt_release = slot(2, ctypes.c_ulong)
    print("refcount after release:", vt_release(p))
    ole32.CoUninitialize()
    return 0

if __name__ == '__main__':
    sys.exit(main())
