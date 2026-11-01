"""16px battle font (2d/cmn/0000.ttd, 12px cells) + its big copy on character select (22px cells):
Hangul goes into the kanji cells (261..), then
  - soul code titles / abilities  cmn/attach_name.atn, attach_mat_name.atn  (trans/atn_ko.json)
  - battle HUD names: EBOOT 0x89c1a78 rewritten to copy from a table   (trans/hud_ko.json)
  - a few EBOOT literals built with li/sh."""
import os, sys, json, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import tim2, f16

FIRST, LAST = 261, 882
END, PAD = 0xfffe, 0xffff
SMALL = ('work/fonts/Galmuri11-Bold.ttf', 12, 12, 21)     # ttf, px, pitch, columns
BIG = ('NanumSquareNeo-cBd.ttf', 19, 22, 23)
FONTS = [(246, 0, SMALL), (247, 1, SMALL), (239, 0, BIG), (240, 1, BIG), (241, 2, BIG), (242, 3, BIG)]

# EBOOT literals: li addresses (in order of characters), optional length immediate (addiu v0,v0,n)
LITERALS = [
    ([0x89c0f58, 0x89c0f64, 0x89c0f70, 0x89c0f7c], None, '랜덤선택'),
    ([(0x89c1348, 0x89c1350), 0x89c1360, 0x89c1368, 0x89c1370, 0x89c1378, 0x89c1380], 0x89c138c, '소울코드'),
    ([(0x89c1348, 0x89c1350), 0x89c1394, 0x89c139c, 0x89c13a4, 0x89c13ac, 0x89c13b4], 0x89c13c0, '소울파츠'),
]
HUD_FUNC, HUD_TBL_N, HUD_EMPTY, HUD_END = 0x89c1a94, 92, 0x89c4318, 0x89c4318
VA0, OFF = 0x8804000, 0x54


def load():
    atn = json.load(open('trans/atn_ko.json', encoding='utf-8'))
    hud = {int(k): v for k, v in json.load(open('trans/hud_ko.json', encoding='utf-8')).items()}
    return atn, hud


def norm(t):
    out = ''
    for c in t:
        o = ord(c)
        if c == ' ':
            c = '　'
        elif 0x21 <= o <= 0x7e:
            c = chr(o + 0xfee0)
        out += c
    return out


def cellmap(texts):
    inv = {c: i for i, c in f16.CH.items() if i < FIRST}
    hangul = sorted({c for t in texts for c in norm(t) if 0xac00 <= ord(c) <= 0xd7a3})
    assert len(hangul) <= LAST - FIRST, f'f16patch: {len(hangul)} hangul > {LAST - FIRST} cells'
    slots = list(zip(range(FIRST, LAST), hangul))
    inv.update({c: i for i, c in slots})
    return inv, slots


def enc(t, inv):
    out = []
    for c in norm(t):
        if c == '　':
            out.append(f16.SPACE)
        else:
            if c not in inv:
                raise KeyError(f'f16patch: no cell for {c!r} in {t!r}')
            out.append(inv[c])
    return out


def render(c, ttf, px, pitch, pal, bg):
    """glyph cell: white body (opaque grays), soft black shadow below/right (black alphas)"""
    face = ImageFont.truetype(ttf, px * 4 if ttf.endswith('cBd.ttf') else px)
    if ttf.endswith('cBd.ttf'):
        S = 4
        im = Image.new('L', (pitch * S, pitch * S), 0)
        dr = ImageDraw.Draw(im)
        bb = dr.textbbox((0, 0), c, font=face)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        dr.text(((pitch - 2) * S / 2 - w / 2 - bb[0], (pitch - 2) * S / 2 - h / 2 - bb[1]), c, font=face, fill=255)
        m = np.asarray(im.resize((pitch, pitch), Image.LANCZOS), np.float32) / 255
    else:
        im = Image.new('L', (pitch, pitch), 0)
        dr = ImageDraw.Draw(im)
        bb = dr.textbbox((0, 0), c, font=face)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        dr.text(((pitch - 1 - w) // 2 - bb[0], (pitch - 1 - h) // 2 - bb[1]), c, font=face, fill=255)
        m = (np.asarray(im, np.float32) / 255 > 0.5).astype(np.float32)
    sh = np.zeros_like(m)
    sh[1:, 1:] = m[:-1, :-1]
    sh = np.maximum(sh, np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)), np.float32) / 255 * 0.6)
    gray = [(i, p[0]) for i, p in enumerate(pal) if p[3] == 255 and p[0] == p[1] == p[2]]
    blk = [(i, p[3]) for i, p in enumerate(pal) if p[0] == 0 and p[3] < 255]
    out = np.full((pitch, pitch), bg, np.uint8)
    for y in range(pitch):
        for x in range(pitch):
            t = m[y, x]
            if t > 0.15:
                v = 120 + 135 * min(1, t)
                out[y, x] = min(gray, key=lambda g: abs(g[1] - v))[0]
            elif sh[y, x] > 0.1:
                a = 255 * min(1, sh[y, x])
                out[y, x] = min(blk, key=lambda g: abs(g[1] - a))[0]
    return out


def fonts(slots):
    idx = json.load(open('work/tex/index.json'))
    out = {}
    for tid, page, (ttf, px, pitch, cols) in FONTS:
        e = idx[tid]
        per = (256 if pitch == 12 else 256) // pitch * cols
        for p, k in [[e['file'], e['k']]] + e['dups']:
            d = out.get(p) or bytearray(open(p, 'rb').read())
            L = tim2.parse_ttd(d)
            o = L[k][0]
            im = tim2.indices(d, o).copy()
            pal = [tuple(int(v) for v in q) for q in tim2.palette(d, o)]
            vals, cnt = np.unique(im, return_counts=True)
            bg = int(vals[cnt.argmax()])
            for cell in range(FIRST, LAST):
                pg, r = divmod(cell, per)
                if pg != page:
                    continue
                y, x = divmod(r, cols)
                if (y + 1) * pitch > im.shape[0]:
                    continue
                im[y * pitch:(y + 1) * pitch, x * pitch:(x + 1) * pitch] = bg
            for cell, c in slots:
                pg, r = divmod(cell, per)
                if pg != page:
                    continue
                y, x = divmod(r, cols)
                if (y + 1) * pitch > im.shape[0]:
                    continue
                im[y * pitch:(y + 1) * pitch, x * pitch:(x + 1) * pitch] = render(c, ttf, px, pitch, pal, bg)
            tim2.put_indices(d, o, im)
            out[p] = d
    return {p: bytes(d) for p, d in out.items()}


def atn_file(path, tr, inv, miss):
    d = bytearray(open(path, 'rb').read())
    for b in range(0, len(d), 168):
        t = ''
        for s in range(7):
            for x in struct.unpack_from('<12H', d, b + 24 * s):
                if x >= END:
                    break
                t += f16.decode([x])
        if not t:
            continue
        ko = tr.get(t)
        if ko is None:
            miss.add(t)
            continue
        w = enc(ko, inv)
        parts = [w[i:i + 10] for i in range(0, len(w), 10)] or [[]]
        assert len(parts) <= 7, ko
        for s in range(7):
            ws = (parts[s] + [END]) if s < len(parts) else [END]
            ws += [PAD] * (12 - len(ws))
            struct.pack_into('<12H', d, b + 24 * s, *ws)
    return bytes(d)


def eboot(d):
    """d: decrypted EBOOT bytearray (patched in place)"""
    _, hud = load()
    inv, _ = cellmap(texts())

    def put(va, w):
        struct.pack_into('<I', d, va - VA0 + OFF, w)

    def get(va):
        return struct.unpack_from('<I', d, va - VA0 + OFF)[0]

    # literals
    for lis, lenva, ko in LITERALS:
        w = enc(ko, inv)
        for k, va in enumerate(lis):
            v = w[k] if k < len(w) else f16.SPACE
            for a in (va if isinstance(va, tuple) else (va,)):
                assert get(a) >> 16 & 0xffe0 == 0x2400, hex(a)
                put(a, get(a) & 0xffff0000 | v)
        if lenva:
            assert get(lenva) >> 16 == 0x2442
            put(lenva, 0x24420000 | len(w))
    # HUD names: table of string pointers [a2=0 x92][a2=6 x92], strings after
    assert get(HUD_FUNC) == 0x00051880
    code_end = HUD_FUNC + 4 * 24
    tbl = code_end
    strs = tbl + 8 * HUD_TBL_N
    blob = bytearray()
    ptr = [0] * (2 * HUD_TBL_N)
    cache = {}
    for cid, (v0, v6) in sorted(hud.items()):
        for j, t in ((0, v0), (1, v6)):
            w = enc(t, inv)[:11] + [END]
            key = tuple(w)
            if key not in cache:
                cache[key] = strs + len(blob)
                blob += struct.pack('<%dH' % len(w), *w)
                blob += b'\0' * (len(blob) % 4)
            ptr[j * HUD_TBL_N + cid] = cache[key]
    assert strs + len(blob) <= HUD_END, hex(strs + len(blob))
    hi = (tbl + 0x8000) >> 16
    lo = tbl & 0xffff
    rel = lambda at, to: ((to - at - 4) >> 2) & 0xffff
    A = HUD_FUNC
    code = [
        0x00051880,                 # sll   v1,a1,2
        0x3c080000 | hi,            # lui   t0,hi
        0x25080000 | lo,            # addiu t0,t0,lo
        0x01034021,                 # addu  t0,t0,v1
        None,                       # beq   a2,zero,L0
        0x00000000,
        0x24090006,                 # li    t1,6
        None,                       # bne   a2,t1,EXIT
        0x00000000,
        0x25080000 | 4 * HUD_TBL_N,  # addiu t0,t0,368
        0x8d080000,                 # L0: lw t0,0(t0)
        None,                       # beq   t0,zero,EMPTY
        0x00000000,
        0x95090000,                 # LOOP: lhu t1,0(t0)
        0xa4890000,                 # sh    t1,0(a0)
        0x25080002,                 # addiu t0,t0,2
        0x340afffe,                 # ori   t2,zero,0xfffe
        None,                       # bne   t1,t2,LOOP
        0x24840002,                 # addiu a0,a0,2
        0x03e00008,                 # jr    ra
        0x00000000,
        0, 0, 0,
    ]
    code[4] = 0x10c00000 | rel(A + 16, A + 40)
    code[7] = 0x14c90000 | rel(A + 28, HUD_EMPTY + 8)
    code[11] = 0x11000000 | rel(A + 44, HUD_EMPTY)
    code[17] = 0x152a0000 | rel(A + 68, A + 52)
    assert len(code) == 24
    for k, w in enumerate(code):
        put(A + 4 * k, w)
    for k, p in enumerate(ptr):
        put(tbl + 4 * k, p)
    o = strs - VA0 + OFF
    d[o:o + len(blob)] = blob


def texts():
    atn, hud = load()
    t = list(atn.values()) + [s for v in hud.values() for s in v] + [x[2] for x in LITERALS]
    return t


def files():
    atn, _ = load()
    inv, slots = cellmap(texts())
    out = fonts(slots)
    miss = set()
    for p in f16.FILES:
        out[p] = atn_file(p, atn, inv, miss)
    print(f'f16patch: {len(slots)} hangul cells, {len(miss)} untranslated atn')
    if miss:
        os.makedirs('work/tmp', exist_ok=True)
        json.dump(sorted(miss), open('work/tmp/atn_missing.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    return out
