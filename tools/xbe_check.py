#!/usr/bin/env python3
"""Check that a default.xbe is the NFSU1 NTSC-U build this port is made for.

Every section's raw size and the SHA-1 digest stored in its header must match the reference (the values are
the same in reUndr-ps5's game_revision.h). Region and media patches (extract-xiso applies one by default)
change the certificate and a few .text bytes but leave the stored digests alone, so they still pass; the
script says whether .text is pristine (its data matches its stored digest) or patched.
Exit 0 = supported, 5 = another build or region, 2 = not an XBE.     tools/xbe_check.py <default.xbe>"""
import hashlib, struct, sys

TITLE_ID = 0x45410047
REF = [  # (name, raw size, stored digest)
    (".text", 1819996, "1acc7ee644625186136901b99a5d7abdcfd4970b"),
    ("D3D", 66504, "02176124699ec4020d83c37eca9998551f9deaae"),
    ("XGRPH", 5744, "266e9a64439fbddc2316b3b061a6329ad03c844c"),
    ("DSOUND", 36820, "82711055c8a00cf8a6f68c81459ded673f49d956"),
    ("XPP", 32388, "100206059d4aeb32802cf51ea43d98f1135f08a1"),
    (".rdata", 147408, "a6ce6de49dddca68bd052b9bafe92355c25897b3"),
    (".data", 299804, "1ae953d1fbb2f4de89fc13fc02c5dae9d99171e6"),
    ("DOLBY", 29036, "c8c9142dccbd31bdca9a2d94e0acc47c2048d615"),
    ("$$XTIMAGE", 10240, "0fd7ef8a9459bfbb3668139e43261894aed581d3"),
    (".XTLID", 1216, "166f5f95ae0397dbb43cab97d7320c9998526d46"),
]

def main(path):
    b = open(path, "rb").read()
    if b[:4] != b"XBEH":
        print(f"xbe_check: {path} is not an XBE"); return 2
    base, = struct.unpack_from("<I", b, 0x104)
    cert, = struct.unpack_from("<I", b, 0x118)
    count, at = struct.unpack_from("<II", b, 0x11C)
    tid, = struct.unpack_from("<I", b, cert - base + 8)
    if tid != TITLE_ID or count != len(REF):
        print(f"xbe_check: title {tid:#x}, {count} sections: not NFS Underground (USA)"); return 5
    text_pristine = True
    for i, (name, size, digest) in enumerate(REF):
        o = at - base + i * 56
        raw, rsz = struct.unpack_from("<II", b, o + 12)
        stored = b[o + 36:o + 56]
        if rsz != size or stored.hex() != digest:
            print(f"xbe_check: section {name} differs: another build or region (only NTSC-U is supported)"); return 5
        if name == ".text":
            text_pristine = hashlib.sha1(struct.pack("<I", rsz) + b[raw:raw + rsz]).digest() == stored
    print(f"xbe_check: OK, NFS Underground NTSC-U ({'pristine' if text_pristine else 'media/region-patched'} .text)")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
