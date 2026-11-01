"""Battle HUD names: EBOOT function 0x89c1a78 builds them with li/sh per character id (jump table, 92 cases).
case: li v1,6 ; beql a2,v1,ALT ; li v1,X ; beql a2,zero,BASE ; li v1,X ; b EXIT"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from mipsstr import Code, paths
FUNC, TABLE, N, EXIT, EMPTY = 0x89c1a78, 0x8a07b5c, 92, 0x89c4320, 0x89c4318


def cases(code=None):
    code = code or Code()
    out = {}
    for c in range(N):
        t = code.w(TABLE + 4 * c)
        if t == EMPTY:
            continue
        res, k, v1 = {}, 0, None
        while True:
            w = code.w(t + 4 * k)
            if w >> 16 == 0x2403:
                v1 = w & 0xffff
            elif w >> 16 in (0x50c3, 0x50c0):
                a2 = v1 if w >> 16 == 0x50c3 else 0
                tgt = t + 4 * k + 4 + 4 * ((w & 0xffff) - (0x10000 if w & 0x8000 else 0))
                res[a2] = (tgt, code.w(t + 4 * k + 4) & 0xffff)
                k += 1
            elif w >> 16 == 0x1000:
                break
            k += 1
        for a2, (tgt, v1) in list(res.items()):
            best = []
            for st in paths(code, tgt, {EXIT}, regs0={3: (v1, t)}):
                s = {}
                for va, base, off, val, _ in st:
                    if base == 4:
                        s[off] = val
                w = [s[o] for o in sorted(s)]
                if 0xfffe in w:
                    w = w[:w.index(0xfffe)]
                    if len(w) > len(best):
                        best = w
            res[a2] = best
        out[c] = res
    return out


if __name__ == '__main__':
    import f16
    for c, r in cases().items():
        print(c, [(k, f16.decode(v)) for k, v in r.items()])
