"""Follow EBOOT code paths and collect literal u16 strings built with 'li r,X ; sh r,k(base)'.
Every branch is explored both ways; registers loaded by li/lui+ori are tracked, anything else
written to a register makes it unknown."""
import struct
VA0, OFF = 0x8804000, 0x54


class Code:
    def __init__(self, path='work/eboot_dec.bin'):
        self.x = open(path, 'rb').read()

    def w(self, va):
        return struct.unpack_from('<I', self.x, va - VA0 + OFF)[0]


def dest(w):
    """register written by a generic instruction (None if none)"""
    op = w >> 26
    if op == 0:
        f = w & 0x3f
        if f in (8, 0x0c, 0x0d, 0x18, 0x19, 0x1a, 0x1b):
            return None
        return (w >> 11) & 31
    if op in (8, 9, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x20, 0x21, 0x23, 0x24, 0x25):
        return (w >> 16) & 31
    if op == 3:
        return 31
    return None


def paths(code, start, stop, maxsteps=3000, regs0=None):
    """yield (start, stores) per path; stores = [(sh_va, base, off, value, li_va)]"""
    out = []
    seen = set()

    def run(va, regs, stores, steps):
        while True:
            if va in stop or steps > maxsteps:
                out.append(stores); return
            w = code.w(va)
            op, rs, rt, imm = w >> 26, (w >> 21) & 31, (w >> 16) & 31, w & 0xffff
            simm = imm - 0x10000 if imm & 0x8000 else imm
            steps += 1
            if op in (4, 5, 0x14, 0x15):          # beq bne beql bnel
                tgt = va + 4 + simm * 4
                dw = code.w(va + 4)
                r2 = exec1(dw, va + 4, dict(regs), stores2 := list(stores))
                if op == 4 and rs == 0 and rt == 0:
                    va, regs, stores = tgt, r2, stores2; continue
                key = (tgt, tuple(sorted(r2.items())), len(stores2))
                if key not in seen:
                    seen.add(key); run(tgt, r2, stores2, steps)
                if op in (0x14, 0x15):
                    va += 8; continue
                va, regs, stores = va + 8, r2, stores2; continue
            if op == 1:                            # bltz/bgez family: treat both ways
                tgt = va + 4 + simm * 4
                run(tgt, dict(regs), list(stores), steps)
                va += 8; continue
            if op == 2:                            # j
                tgt = (va & 0xf0000000) | ((w & 0x3ffffff) << 2)
                exec1(code.w(va + 4), va + 4, regs, stores)
                va = tgt; continue
            if op == 0 and (w & 0x3f) == 8:        # jr
                out.append(stores); return
            regs = exec1(w, va, regs, stores)
            va += 4

    def exec1(w, va, regs, stores):
        op, rs, rt, imm = w >> 26, (w >> 21) & 31, (w >> 16) & 31, w & 0xffff
        simm = imm - 0x10000 if imm & 0x8000 else imm
        if op == 0x0f:
            regs[rt] = (imm << 16, va); return regs
        if op == 0x0d and (rs == 0 or rs in regs):
            base = 0 if rs == 0 else regs[rs][0]
            regs[rt] = ((base | imm) & 0xffffffff, va); return regs
        if op == 0x09 and (rs == 0 or rs in regs):
            base = 0 if rs == 0 else regs[rs][0]
            regs[rt] = ((base + simm) & 0xffffffff, va); return regs
        if op == 0x29 and rt in regs:
            stores.append((va, rs, simm, regs[rt][0] & 0xffff, regs[rt][1]))
            return regs
        if op == 3:
            for r in list(regs):
                if r in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 24, 25, 31):
                    regs.pop(r)
            return regs
        d = dest(w)
        if d:
            regs.pop(d, None)
        return regs

    run(start, dict(regs0 or {}), [], 0)
    return out
