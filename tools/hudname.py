"""Battle HUD character names: EBOOT function 0x89c1a78 writes them with immediate
'li v1,cell ; sh v1,k(a0)' pairs (cells of the 16px font, see f16.py).
paths() follows every switch case / a2 branch and returns the stores of each string."""
import struct
VA0, OFF = 0x8804000, 0x54
FUNC, END = 0x89c1a78, 0x89c4320
TABLE, NCASE = 0x203bb0, 0x5c       # file offset of the jump table in eboot_dec.bin


def word(x, va):
    return struct.unpack_from('<I', x, va - VA0 + OFF)[0]


def step(x, va):
    """-> kind, info"""
    w = word(x, va)
    op, rs, rt, imm = w >> 26, (w >> 21) & 31, (w >> 16) & 31, w & 0xffff
    simm = imm - 0x10000 if imm & 0x8000 else imm
    if w == 0:
        return 'nop', None
    if op in (0x0d, 0x09) and rs == 0 and rt == 3:
        return 'li', imm if op == 0x0d else simm & 0xffff
    if op == 0x29 and rt == 3 and rs == 4:
        return 'sh', simm
    if op in (0x04, 0x05, 0x14, 0x15):
        return ('beq', 'bne', 'beql', 'bnel')[(op & 1) | ((op >> 3) & 2)], (rs, rt, va + 4 + simm * 4)
    return 'other', w


def paths(x):
    out = []
    targets = sorted(set(struct.unpack_from('<%dI' % NCASE, x, TABLE)))

    def run(va, v1, stores, depth, start):
        while True:
            if va >= END or va == END - 4 or depth > 400:
                out.append((start, stores)); return
            k, info = step(x, va)
            if k == 'li':
                v1 = (info, va)
            elif k == 'sh':
                stores = stores + [(va, info, v1)]
            elif k in ('beq', 'bne', 'beql', 'bnel'):
                rs, rt, tgt = info
                dk, dinfo = step(x, va + 4)
                v1d = (dinfo, va + 4) if dk == 'li' else v1
                if rs == 0 and rt == 0 and k == 'beq':      # unconditional b
                    if tgt >= END - 4:
                        out.append((start, stores)); return
                    va, v1 = tgt, v1d; depth += 1; continue
                run(tgt, v1d, stores, depth + 1, start)     # taken
                if k.endswith('l'):
                    va += 8; continue                        # likely: delay slot skipped
                va, v1 = va + 8, v1d; continue
            elif k == 'other':
                pass
            va += 4

    for t in targets:
        run(t, None, [], 0, t)
    return out
