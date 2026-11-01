"""Glyph-index text records in seq files (font/1000.ttd cells).
record: name[32] | 06 11 06 20 | u16 1 | u16 A(=B+0x38) | u16 B(text bytes) | u16 lines-1 | u16 0x38 ... (24 bytes) | u16 text[B/2] | 16 zero"""
import os, struct, json
MAGIC = b'\x06\x11\x06\x20'
NL = 0x4100


def glyphs():
    g = json.load(open('work/glyphs.json', encoding='utf-8'))
    return {r['idx']: r['ch'] for r in g}


def records(d):
    i = d.find(MAGIC)
    while i >= 0:
        A, B, ln = struct.unpack_from('<HHH', d, i + 6)
        if A == B + 0x38 and B % 2 == 0:
            yield i, B, ln, list(struct.unpack_from('<%dH' % (B // 2), d, i + 24))
        i = d.find(MAGIC, i + 1)


VAR = 0x4801   # value insert, followed by its slot number -> '{n}'


def decode(w, ch):
    out, k = '', 0
    while k < len(w):
        v = w[k]
        if v == VAR and k + 1 < len(w):
            out += '{%d}' % w[k + 1]; k += 2; continue
        out += '\n' if v == NL else ch.get(v, '〓') if v else '　'
        k += 1
    return out


def seqfiles():
    for dp, _, fs in os.walk('work/x'):
        for f in fs:
            if f.endswith('.seq'):
                yield os.path.join(dp, f).replace(os.sep, '/')


if __name__ == '__main__':
    ch = glyphs()
    out = {}
    for p in seqfiles():
        d = open(p, 'rb').read()
        for i, B, ln, w in records(d):
            t = decode(w, ch)
            out.setdefault(t, []).append([p, i, B])
    json.dump(out, open('work/msg_jp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(out), sum(len(k) for k in out))
