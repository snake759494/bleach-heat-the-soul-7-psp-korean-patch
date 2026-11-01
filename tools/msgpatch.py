"""Translate the glyph-index text records (see msgrec.py) and rebuild the bitmap font font/1000.ttd.
Hangul syllables take over the kanji cells (261..) and the unused cells after them.
Seq files must not grow (the game hangs), so a translation has to fit in the original record."""
import os, sys, re, struct, json, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import tim2

from msgrec import records, decode, glyphs, seqfiles, NL, VAR

FONT_TTD = 'work/x/2d/font/0000.fpk/font/1000.ttd'
FIRST = 261           # first kanji cell
CELLS = 5 * 17 * 17
REF = b'\x39\x17\x00\x02'
TTF = 'NanumSquareNeo-cBd.ttf'


def translations():
    tr = {}
    for p in sorted(glob.glob('trans/msg_ko*.json')):
        tr.update(json.load(open(p, encoding='utf-8')))
    return tr


def norm(t):
    """half-width -> full-width (the font only has full-width cells)"""
    out = ''
    for c in t:
        o = ord(c)
        if c == ' ':
            c = '　'
        elif 0x21 <= o <= 0x7e:
            c = chr(o + 0xfee0)
        out += c
    return out.replace('～', '～').replace('?', '？').replace('·', '・')


def cellmap(tr):
    ch = glyphs()
    inv = {}
    for i, c in sorted(ch.items()):
        if i < FIRST:
            inv.setdefault(c, i)
    used = {c for t in tr.values() for c in norm(t)}
    hangul = sorted(c for c in used if 0xac00 <= ord(c) <= 0xd7a3)
    cells = list(range(FIRST, CELLS))
    if len(hangul) > len(cells):
        # last resort: kana cells no translation uses (player-typed names may still need them)
        spare = [i for i, c in sorted(ch.items()) if i < FIRST and 0x3041 <= ord(c) <= 0x30fa and c not in used]
        cells += spare[::-1]
        print(f'msgpatch: {len(hangul) - (CELLS - FIRST)} hangul cells taken from kana')
    assert len(hangul) <= len(cells), len(hangul)
    slots = list(zip(cells, hangul))
    for i, c in slots:
        inv[c] = i
    return inv, slots


def encode(t, inv):
    w = []
    for part in re.split(r'(\{\d+\})', t):
        if part[:1] == '{':
            w += [VAR, int(part[1:-1])]
        else:
            w += encode_plain(part, inv)
    return w


def encode_plain(t, inv):
    w = []
    for c in norm(t):
        if c == '\n':
            w.append(NL)
        elif c == '　':
            w.append(0)
        else:
            if c not in inv:
                raise KeyError(f'no cell for {c!r} in {t!r}')
            w.append(inv[c])
    return w


def glyph(c, face):
    S = 4
    im = Image.new('L', (15 * S, 15 * S), 0)
    dr = ImageDraw.Draw(im)
    bb = dr.textbbox((0, 0), c, font=face)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    dr.text(((15 * S - w) / 2 - bb[0], (15 * S - h) / 2 - bb[1]), c, font=face, fill=255)
    m = np.asarray(im.resize((15, 15), Image.LANCZOS), np.float32) / 255
    o = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)), np.float32) / 255
    # palette: 0..5 black alpha 0,44,102,152,188,224 ; 6..15 gray 8..255 opaque
    alphas = np.array([0, 44, 102, 152, 188, 224]) / 255
    out = np.zeros((15, 15), np.uint8)
    for y in range(15):
        for x in range(15):
            t = m[y, x]
            if t > 0.12:
                out[y, x] = 6 + int(round(min(1, t) * 9))
            else:
                a = o[y, x] * 0.9
                out[y, x] = int(np.abs(alphas - a).argmin())
    return out


def font(slots):
    d = bytearray(open(FONT_TTD, 'rb').read())
    L = tim2.parse_ttd(d)
    face = ImageFont.truetype(TTF, 13 * 4)
    pages = [tim2.indices(d, L[k][0]).copy() for k in range(5)]
    for k in range(FIRST, CELLS):
        p, r = divmod(k, 289)
        y, x = divmod(r, 17)
        pages[p][y * 15:y * 15 + 15, x * 15:x * 15 + 15] = 0
    for i, c in slots:
        p, r = divmod(i, 289)
        y, x = divmod(r, 17)
        pages[p][y * 15:y * 15 + 15, x * 15:x * 15 + 15] = glyph(c, face)
    for k in range(5):
        tim2.put_indices(d, L[k][0], pages[k])
    return bytes(d)


def patch_file(d, tr, inv, ch, miss):
    d = bytearray(d)
    tail = bytearray()
    base = len(d)
    for i, B, ln, w in list(records(bytes(d))):
        jp = decode(w, ch)
        ko = tr.get(jp)
        if ko is None:
            if any(0x3040 <= ord(c) <= 0x9fff for c in jp):
                miss.add(jp)
            continue
        nw = encode(ko, inv)
        if w[0] == 0x4d01 and nw[:1] == [0]:   # leading control code shown as 〓
            nw[0] = 0x4d01
        lines = ko.count('\n')
        if 2 * len(nw) <= B:
            struct.pack_into('<%dH' % len(nw), d, i + 24, *nw)
            d[i + 24 + 2 * len(nw):i + 24 + B] = b'\0' * (B - 2 * len(nw))
            struct.pack_into('<HHH', d, i + 6, 2 * len(nw) + 0x38, 2 * len(nw), lines)
            continue
        miss.add('[long %d>%d] ' % (len(nw), B // 2) + jp)
    return bytes(d + tail)


def files(base=None):
    """base: {path: bytes} already modified by other patches"""
    base = base or {}
    tr = translations()
    inv, hangul = cellmap(tr)
    ch = glyphs()
    out = {FONT_TTD: font(hangul)}
    miss = set()
    for p in seqfiles():
        d = base.get(p) or open(p, 'rb').read()
        if b'\x06\x11\x06\x20' not in d:
            continue
        nd = patch_file(d, tr, inv, ch, miss)
        if nd != d:
            out[p] = nd
    print(f'msgpatch: {len(hangul)} hangul cells, {len(miss)} untranslated records')
    if miss:
        os.makedirs('work/tmp', exist_ok=True)
        json.dump(sorted(miss), open('work/tmp/msg_missing.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    return out
