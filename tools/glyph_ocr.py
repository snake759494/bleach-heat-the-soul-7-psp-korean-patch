"""Identify every cell of the b_font bitmap pages.  The glyph set is a subset of
Shift-JIS in ascending code order, so the cells are aligned to the candidate list
with a monotonic DP that maximises template similarity."""
import sys, os, struct, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TTD = 'work/x/2d/font/0000.fpk/font/1000.ttd'


def pages():
    d = open(TTD, 'rb').read()
    out = []
    i = 0
    while True:
        i = d.find(b'TIM2', i + 1)
        if i < 0:
            break
        hs = struct.unpack_from('<H', d, i + 16 + 12)[0]
        img = struct.unpack_from('<I', d, i + 16 + 8)[0]
        out.append(np.frombuffer(d[i + 16 + hs:i + 16 + hs + img], np.uint8).reshape(256, 256))
    return out


def cells():
    res = []
    for p in pages():
        for r in range(17):
            for c in range(17):
                a = np.zeros((16, 16), np.float32)
                a[:15, :15] = p[r * 15:r * 15 + 15, c * 15:c * 15 + 15]
                res.append(a)
    while res and res[-1].max() == 0:
        res.pop()
    return res


def candidates():
    out = []
    for hi in list(range(0x81, 0xa0)) + list(range(0xe0, 0xeb)):
        for lo in list(range(0x40, 0x7f)) + list(range(0x80, 0xfd)):
            try:
                ch = bytes([hi, lo]).decode('cp932')
            except UnicodeDecodeError:
                continue
            if len(ch) == 1 and not (0xe000 <= ord(ch) < 0xf900):
                out.append((hi << 8 | lo, ch))
    return out


def norm(a):
    a = a - a.mean()
    n = np.sqrt((a * a).sum())
    return a / n if n else a


def feat(a, S=24):
    a = np.asarray(a, np.float32)
    ys, xs = np.nonzero(a > 40)
    if len(xs) == 0:
        return np.zeros(S * S, np.float32)
    sub = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = sub.shape
    k = (S - 2) / max(h, w)
    im = Image.fromarray(sub.astype(np.uint8)).resize((max(1, round(w * k)), max(1, round(h * k))), Image.BILINEAR)
    cv = Image.new('L', (S, S), 0)
    cv.paste(im, ((S - im.width) // 2, (S - im.height) // 2))
    cv = cv.filter(ImageFilter.GaussianBlur(1.2))
    return norm(np.asarray(cv, np.float32)).ravel()


def render(ch, font):
    im = Image.new('L', (48, 48), 0)
    ImageDraw.Draw(im).text((4, 4), ch, font=font, fill=255)
    return np.asarray(im, np.float32)


def _unused(ch, font):
    im = Image.new('L', (16, 16), 0)
    dr = ImageDraw.Draw(im)
    bb = dr.textbbox((0, 0), ch, font=font)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    dr.text(((16 - w) / 2 - bb[0], (16 - h) / 2 - bb[1]), ch, font=font, fill=255)
    return np.asarray(im, np.float32)


def center(a):
    ys, xs = np.nonzero(a > 0)
    if len(xs) == 0:
        return a
    out = np.zeros_like(a)
    sub = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = sub.shape
    oy, ox = (16 - h) // 2, (16 - w) // 2
    out[oy:oy + h, ox:ox + w] = sub
    return out


def main():
    cs = cells()
    print('cells', len(cs))
    fonts = [ImageFont.truetype('C:/Windows/Fonts/YuGothB.ttc', 36), ImageFont.truetype('C:/Windows/Fonts/BIZ-UDGothicB.ttc', 36)]
    cand = candidates()
    print('candidates', len(cand))
    F = np.stack([feat(np.where(c >= 8, c * 16, 0)) for c in cs])
    S = None
    for font in fonts:
        G = np.stack([feat(render(ch, font)) for _, ch in cand])
        T = F @ G.T
        S = T if S is None else np.maximum(S, T)
    n, m = S.shape
    # cell 0 is blank (space 0x8140) -> force
    NEG = -1e9
    dp = np.full((n, m), NEG, np.float32)
    bk = np.zeros((n, m), np.int32)
    dp[0] = S[0]
    for i in range(1, n):
        best = np.maximum.accumulate(dp[i - 1])
        arg = np.zeros(m, np.int32)
        cur = 0
        prevrow = dp[i - 1]
        # running argmax
        idx = np.arange(m)
        mask = prevrow == best
        arg = np.maximum.accumulate(np.where(mask, idx, 0))
        dp[i, 1:] = best[:-1] + S[i, 1:]
        bk[i, 1:] = arg[:-1]
    j = int(dp[n - 1].argmax())
    path = [0] * n
    for i in range(n - 1, -1, -1):
        path[i] = j
        j = bk[i, j]
    res = []
    for i, j in enumerate(path):
        res.append(dict(idx=i, sjis=cand[j][0], ch=cand[j][1], score=float(S[i, j])))
    json.dump(res, open('work/glyphs.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    low = sorted(res, key=lambda r: r['score'])[:30]
    print('lowest', [(r['idx'], r['ch'], round(r['score'], 2)) for r in low])
    print(''.join(r['ch'] for r in res))


if __name__ == '__main__':
    main()
