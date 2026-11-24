#!/usr/bin/env python3
"""Are any of the lifter's "not detected" stubs real code?   .venv/bin/python tools/stubcheck.py  (capstone)

engine/gen/recomp_stubs_unresolved.c gives every direct call or jump target the disassembler did not
detect as a function an empty body (`g_esp += 4`, a bare ret; `g_esp += 4+N` where the bytes end in
`ret N`). For bytes the lifter decoded out of alignment that is harmless: nothing reaches them. For a real
instruction start -- typically a function's shared exit (`pop esi; pop ebp; pop edi; ret`) that another
path jumps to -- it is a silent bug: the pops never happen and the caller gets its registers and stack back
wrong (Harry Potter CoS: a tail jump to such an exit froze the game at the next door). Each stub is classed:
  BOUNDARY  an instruction start inside a detected function: real code, seed it (engine/config/seed_functions.json)
  code      outside every function but in a code section: real code, seed it
  mid-insn  inside an instruction of a detected function: a misdecode, harmless
  pad       int3 alignment padding (reached only from a misdecoded jump table): harmless
  data      outside the code sections: harmless
Exits 1 when any stub is real code. Seeding one can split a function and turn its internal jumps into new
stubs: regenerate (engine/tools/regen.sh) and run this again until it passes.
From hpcos-xbox-port's tools/stubcheck.py; the XBE reader is inlined and the code ranges come from the
section headers."""
import bisect, glob, json, os, re, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
XBE = os.environ.get("NFSU1_XBE", os.path.join(R, "game/extracted/default.xbe"))
GEN = os.environ.get("NFSU1_GEN_DIR", os.path.join(R, "engine/gen"))
FUNCS = os.path.join(R, "engine/xboxrecomp/tools/disasm/output/functions.json")
CODE_SECTIONS = {".text", "D3D", "XGRPH", "DSOUND", "XPP"}   # the title's code and the linked XDK libraries


def load(path):
    d = open(path, "rb").read()
    base, = struct.unpack_from("<I", d, 0x104)
    n, sa = struct.unpack_from("<II", d, 0x11C)
    secs = []
    for i in range(n):
        o = sa - base + i * 56
        _fl, va, vs, ra, rs, na = struct.unpack_from("<IIIIII", d, o)
        secs.append((d[na - base:na - base + 12].split(b"\0")[0].decode(), va, vs, d[ra:ra + rs]))
    return secs


def read(secs, va, n):
    for _nm, v, _vs, b in secs:
        if v <= va < v + len(b):
            return b[va - v:va - v + n]
    return b""


secs = load(XBE)
code = [(v, v + vs) for nm, v, vs, _ in secs if nm in CODE_SECTIONS]
rng = sorted((int(f["start"], 16), int(f["end"], 16)) for f in json.load(open(FUNCS)))
starts = [r[0] for r in rng]
md = Cs(CS_ARCH_X86, CS_MODE_32)
refs = {}
for path in glob.glob(os.path.join(GEN, "recomp_0*.c")):
    cur = None
    for line in open(path, errors="ignore"):
        m = re.match(r"^void (sub_[0-9A-F]{8})(_gen)?\(void\)", line)
        if m:
            cur = m.group(1)
        for t in re.findall(r"\b(sub_[0-9A-F]{8})\(\)", line):
            refs.setdefault(t, set()).add(cur or "?")
stubs = re.findall(r"0x([0-9A-F]+): (?:not detected|ret \d+) \*/",
                   open(os.path.join(GEN, "recomp_stubs_unresolved.c")).read())
real = 0
for a in (int(x, 16) for x in stubs):
    i = bisect.bisect_right(starts, a) - 1
    if i >= 0 and rng[i][0] <= a < rng[i][1]:
        s = rng[i][0]
        kind = "BOUNDARY" if a in {x.address for x in md.disasm(read(secs, s, a - s + 16), s)} else "mid-insn"
    else:
        kind = "code" if any(lo <= a < hi for lo, hi in code) else "data"
    if kind in ("BOUNDARY", "code") and read(secs, a, 1) == b"\xcc":
        kind = "pad"
    real += kind in ("BOUNDARY", "code")
    ins = [f"{x.mnemonic} {x.op_str}" for x, _ in zip(md.disasm(read(secs, a, 16), a), range(2))]
    print(f"{a:#010x} {kind:8} from {','.join(sorted(refs.get('sub_%08X' % a, [])))} | {' ; '.join(ins)}")
print(f"stubcheck: {len(stubs)} stubs, {real} real code" + (" -- seed them" if real else ""))
sys.exit(1 if real else 0)
