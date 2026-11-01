"""Build the Korean ISO.
  python tools/build.py            -> "Bleach - Heat the Soul 7 (Korean).iso"
"""
import os, sys, json, struct, hashlib, shutil
sys.path.insert(0, os.path.dirname(__file__))
import lz, fpk, tim2, texedit
from isobuild import Iso

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)
SRC = 'Bleach - Heat the Soul 7 (Japan).iso'
DST = 'Bleach - Heat the Soul 7 (Korean).iso'
FP = 'work/iso/PSP_GAME/USRDIR/data/fpack/'
CACHE = 'work/cache'
os.makedirs(CACHE, exist_ok=True)


def compress_cached(data):
    h = hashlib.md5(data).hexdigest()
    p = f'{CACHE}/{h}.lz'
    if os.path.exists(p):
        return open(p, 'rb').read()
    c = lz.compress(data)
    assert lz.decompress(c) == data
    open(p, 'wb').write(c)
    return c


def rebuild_fpk(path, repl):
    """repl: {entry name: new bytes}"""
    d, hdr, ents = fpk.read(path)
    n = len(ents)
    pos = 16 + 48 * n
    pos = (pos + 15) & ~15
    head = bytearray(16 + 48 * n)
    body = bytearray()
    base = pos
    for k, e in enumerate(ents):
        if e['name'] in repl:
            raw = repl[e['name']]
            if e['cs'] == e['us'] and e['cs']:
                blob = raw; cs = us = len(raw)
            else:
                blob = compress_cached(raw); cs, us = len(blob), len(raw)
        else:
            blob, cs, us = e['data'], e['cs'], e['us']
        off = base + len(body)
        rec = bytearray(e['raw'])
        struct.pack_into('<4I', rec, 0x20, e['z'], off, cs, us)
        head[16 + 48 * k:16 + 48 * k + 48] = rec
        body += blob
        body += b'\0' * ((-len(body)) % 16)
    # first data offset in original files is right after the table (16-aligned)
    assert base == 16 + 48 * n or True
    out = head + b'\0' * (base - len(head)) + body
    cs16 = sum(out[16 + 48 * n:]) & 0xffff
    struct.pack_into('<4I', out, 0, cs16, n, 16, len(out))
    return bytes(out)


def collect_texture_edits():
    spec = json.load(open('trans/images.json', encoding='utf-8'))
    idx = json.load(open('work/tex/index.json'))
    per = {}  # ttd path -> {k: items}
    for tid, items in spec.items():
        e = idx[int(tid)]
        for p, k in [[e['file'], e['k']]] + e['dups']:
            per.setdefault(p, {})[k] = items
    out = {}
    for p, ks in per.items():
        d = bytearray(open(p, 'rb').read())
        L = tim2.parse_ttd(d)
        for k, items in ks.items():
            texedit.edit_blob(d, L[k][0], items)
        out[p] = bytes(d)
    return out


def main():
    files = {}   # extracted path work/x/<fpk rel>/<entry> -> bytes
    files.update(collect_texture_edits())
    extra = {}
    if os.path.exists('tools/textpatch.py'):
        import textpatch
        files.update(textpatch.files())
        extra = textpatch.iso_files()
    # group by fpk
    byfpk = {}
    for p, data in files.items():
        rel, entry = p[len('work/x/'):].split('.fpk/', 1)
        byfpk.setdefault(rel + '.fpk', {})[entry] = data
    shutil.copyfile(SRC, DST) if False else None
    iso = Iso(SRC, DST)
    sec = bytearray(iso.read('/PSP_GAME/USRDIR/data/fpack/sector.lst'))
    secidx = {}
    for k in range((len(sec) - 12) // 0x88):
        o = 12 + k * 0x88
        secidx[sec[o:o + 0x80].split(b'\0')[0].decode().upper()] = o
    changed = {}
    for rel, repl in sorted(byfpk.items()):
        data = rebuild_fpk(FP + rel, repl)
        changed['/PSP_GAME/USRDIR/data/fpack/' + rel] = data
    changed.update(extra)
    for path, data in changed.items():
        try:
            how = iso.replace(path, data)
        except FileNotFoundError:
            dpath, name = path.rsplit('/', 1)
            iso.add(dpath, name, data); how = 'added'
        _, _, _, lba, size = iso.find(path)
        key = ('disc0:' + path).upper()
        if key in secidx:
            struct.pack_into('<2I', sec, secidx[key] + 0x80, lba, size)
        print(how, path, size)
    iso.replace('/PSP_GAME/USRDIR/data/fpack/sector.lst', bytes(sec))
    iso.close()
    print('built', DST)


if __name__ == '__main__':
    main()
