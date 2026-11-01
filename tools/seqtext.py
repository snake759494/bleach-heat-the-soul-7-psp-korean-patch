"""seq scripts reference string constants with the 8-byte op  28 3f 00 00 <u32 abs offset>.
Extract every referenced string that contains Japanese."""
import os, sys, struct, json, re

OP = b'\x28\x3f\x00\x00'
JP = re.compile('[぀-ヿ一-鿿！-～　-〿]')


def cstr(d, o):
    e = d.find(b'\0', o)
    return d[o:e]


def refs(d):
    out = []
    i = 0
    while True:
        i = d.find(OP, i)
        if i < 0:
            break
        if i % 4 == 0 and i + 8 <= len(d):
            v = struct.unpack_from('<I', d, i + 4)[0]
            if 0 < v < len(d):
                out.append((i + 4, v))
        i += 4
    return out


def strings(d):
    res = {}
    for at, v in refs(d):
        raw = cstr(d, v)
        try:
            s = raw.decode('cp932')
        except UnicodeDecodeError:
            continue
        if JP.search(s):
            res.setdefault(v, dict(off=v, raw=raw, text=s, refs=[]))['refs'].append(at)
    return res


if __name__ == '__main__':
    root = sys.argv[1]
    allt = {}
    tot = 0
    for dp, _, fs in os.walk(root):
        for f in fs:
            if not f.endswith('.seq'):
                continue
            p = os.path.join(dp, f)
            d = open(p, 'rb').read()
            st = strings(d)
            if st:
                rel = os.path.relpath(p, root).replace('\\', '/')
                allt[rel] = [dict(off=v['off'], text=v['text'], nref=len(v['refs'])) for v in st.values()]
                tot += len(st)
    json.dump(allt, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    uniq = {x['text'] for v in allt.values() for x in v}
    print('files', len(allt), 'strings', tot, 'unique', len(uniq), 'chars', sum(len(u) for u in uniq))
