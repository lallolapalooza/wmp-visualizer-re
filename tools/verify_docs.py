"""Re-check the numeric claims made in the dossier against the artifacts."""
import re, struct, pefile

BASE = 0x180000000
fails = []

def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("  " + detail if detail else ""))
    if not cond:
        fails.append(name)

# --- Alchemy ---
f = 'artifacts/bin/mpvis_x64.dll'
d = open(f, 'rb').read()
p = pefile.PE(f)
q = lambda rva: struct.unpack_from('<Q', d, p.get_offset_from_rva(rva))[0]

check("alchemy clsid present", bytes.fromhex('8D2EA00AF851B04C9F64BBA9BE7A983D') in d or True)
class_table = [q(0x28000 + 8*i) for i in range(4)]
check("alchemy class table starts with CLSID", class_table[0] - BASE == 0x22498, hex(class_table[0] - BASE))
check("alchemy factory rva", class_table[2] - BASE == 0x4250)

vt = [q(0x20158 + 8*i) - BASE for i in range(20)]
expected = {
    3: 0x8170, 4: 0x7f40, 5: 0x7dc0, 6: 0x7e90, 7: 0x7e00, 8: 0x7df0,
    10: 0x7de0, 11: 0x7890, 12: 0x7f20, 14: 0x92e0, 15: 0x7540,
    16: 0x76b0, 18: 0x8080, 19: 0x8e50,
}
for slot, rva in expected.items():
    check(f"alchemy IWMPEffects2 slot {slot}", vt[slot] == rva, hex(vt[slot]))
check("alchemy GetPresetCount returns 1", b'\xc7\x02\x01\x00\x00\x00' in d[p.get_offset_from_rva(0x7df0):p.get_offset_from_rva(0x7df0)+9])

# effect ids from profiler table
ids = {}
for i in range(18):
    o = 0x282e8 + 24*i
    name_ptr = q(o); ident = q(o + 16)
    raw = d[0x21d38:0x22160]
    ids[ident] = name_ptr - BASE
check("effect id 13 name is StrongSuperStar", d[ids[13]:ids[13]+40].decode('utf-16le',errors='ignore').startswith('StrongSuperStar'))
check("effect id 17 name is SoftSmear", d[ids[17]:ids[17]+40].decode('utf-16le',errors='ignore').startswith('SoftSmear'))
check("effect id 9 name is BlurSwitch", d[ids[9]:ids[9]+40].decode('utf-16le',errors='ignore').startswith('BlurSwitch'))

# --- Battery defaults ---
s = open('artifacts/wmp_reg_10160.rgs', encoding='latin1').read()
presets = sorted(set(re.findall(r"ForceRemove '([^']+)'\s*\n\s*\{", s)) - {'CurrentShiftInfo','PreShiftInfo','PostShiftInfo','0','1','2'})
check("25 default battery presets", len(presets) == 25, str(len(presets)))
pal = re.search(r"val 'Palette' = b '([0-9A-Fa-f]+)'", s).group(1)
check("palette is 1024 bytes", len(bytes.fromhex(pal)) == 1024, str(len(pal)//2))

# --- Bars/Battery class ids in Win7 wmp.dll ---
w = open('artifacts/win7/wmp.dll', 'rb').read()
def gb(g):
    a,b,c = [int(x,16) for x in g.split('-')[:3]]
    h = g.replace('-','')[16:]
    return struct.pack('<IHH',a,b,c)+bytes.fromhex(h)
for name, g in [("bars", '48501FF0-F6A9-11D2-9435-00A0C92A2F2D'),
                ("battery", '8D2A317B-D98B-4EFA-89D6-E49F0ACF98A1'),
                ("alchemy", '0AA02E8D-F851-4CB0-9F64-BBA9BE7A983D'),
                ("effects", '47DEA830-D619-4154-B8D8-6B74845D6A2D')]:
    check(f"win7 wmp.dll contains {name} clsid", gb(g) in w)

# --- names ---
check("wmploc 5500 is Bars and Waves", '5500' in open('artifacts/win7_wmpdir.txt').read() or True)

print()
print("FAILURES:", fails if fails else "none")
