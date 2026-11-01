"""Bleach Heat the Soul 7 FPK compression (EBOOT 0x89375c8).

Bit reader: one control byte at a time, MSB first, refilled lazily between tokens.
  1            literal byte
  0 0 a b o    short copy: len = 2 + (a<<1|b), src = dst - (0x100 - o)
  0 1 hi lo    long copy:  v = hi<<8|lo, src = dst - (0x2000 - (v>>3)),
               len = (v&7)+2, or if v&7==0: next byte c, c==0 -> end, len = c+1
"""


def decompress(src, usize=None):
    out = bytearray()
    i = 0
    flag = 0
    nbits = 0

    def bit():
        nonlocal flag, nbits, i
        if nbits == 0:
            flag = src[i]; i += 1; nbits = 8
        nbits -= 1
        return (flag >> nbits) & 1

    while True:
        if bit():
            out.append(src[i]); i += 1
            continue
        if bit():
            v = src[i] << 8 | src[i + 1]; i += 2
            dist = 0x2000 - (v >> 3)
            n = v & 7
            if n:
                ln = n + 2
            else:
                c = src[i]; i += 1
                if c == 0:
                    break
                ln = c + 1
        else:
            ln = 2 + (bit() << 1)
            ln += bit()
            dist = 0x100 - src[i]; i += 1
        p = len(out) - dist
        for k in range(ln):
            out.append(out[p + k])
    return bytes(out)


class _Bits:
    def __init__(self):
        self.out = bytearray()
        self.fpos = -1
        self.n = 0

    def bit(self, b):
        if self.n == 0:
            self.fpos = len(self.out); self.out.append(0); self.n = 8
        self.n -= 1
        if b:
            self.out[self.fpos] |= 1 << self.n

    def byte(self, b):
        self.out.append(b)


def compress(data):
    """Greedy LZ with hash chains; output is decoded exactly by decompress()."""
    n = len(data)
    w = _Bits()
    head = {}
    prev = [-1] * n
    i = 0

    def insert(p):
        if p + 2 < n:
            k = data[p:p + 3]
            prev[p] = head.get(k, -1)
            head[k] = p

    while i < n:
        best_len, best_dist = 0, 0
        if i + 2 < n:
            cand = head.get(data[i:i + 3], -1)
            tries = 0
            maxl = min(256, n - i)
            while cand >= 0 and i - cand <= 0x1fff and tries < 64:
                l = 3
                while l < maxl and data[cand + l] == data[i + l]:
                    l += 1
                if l > best_len:
                    best_len, best_dist = l, i - cand
                    if l == maxl:
                        break
                cand = prev[cand]; tries += 1
        # 2-byte short match
        if best_len < 3 and i + 1 < n:
            for d in range(1, min(0x100, i) + 1):
                if data[i - d] == data[i] and data[i - d + 1] == data[i + 1]:
                    best_len, best_dist = 2, d
                    break
        if best_len >= 2 and best_len <= 5 and best_dist <= 0x100:
            w.bit(0); w.bit(0)
            l = best_len - 2
            w.bit(l >> 1); w.bit(l & 1)
            w.byte(0x100 - best_dist)
        elif best_len >= 3:
            w.bit(0); w.bit(1)
            v = (0x2000 - best_dist) << 3
            if best_len <= 9:
                v |= best_len - 2
                w.byte(v >> 8); w.byte(v & 0xff)
            else:
                w.byte(v >> 8); w.byte(v & 0xff); w.byte(best_len - 1)
        else:
            best_len = 1
            w.bit(1); w.byte(data[i])
        for k in range(best_len):
            insert(i + k)
        i += best_len
    w.bit(0); w.bit(1); w.byte(0); w.byte(0); w.byte(0)
    return bytes(w.out)


if __name__ == '__main__':
    import sys, struct
    d = open(sys.argv[1], 'rb').read()
    n = struct.unpack_from('<I', d, 4)[0]
    for k in range(n):
        e = d[16 + k * 48:64 + k * 48]
        o, cs, us = struct.unpack_from('<3I', e, 0x24)
        name = e[:32].split(b'\0')[0].decode()
        if cs and cs != us:
            u = decompress(d[o:o + cs])
            c = compress(u)
            print(name, hex(us), hex(len(u)), 'ok' if len(u) == us and decompress(c) == u else 'BAD', hex(cs), hex(len(c)))
