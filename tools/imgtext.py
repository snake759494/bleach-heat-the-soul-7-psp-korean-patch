"""Replace Japanese text in a CLUT texture with Korean.

spec item: {"box":[x,y,w,h], "text":"..", "font":"sans|serif|pixel", "bold":0..4,
            "align":"l|c|r", "vert":false, "erase":"clear|fill|none", "size":px(optional),
            "fill":[r,g,b](optional), "fill2":[r,g,b](optional, bottom gradient),
            "outline":[r,g,b](optional), "ow":px(optional), "pad":px}
Text style is sampled from the original box when not given.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FONTS = {
    'sans': ['NanumSquareNeo-bRg.ttf', 'NanumSquareNeo-cBd.ttf', 'NanumSquareNeo-dEb.ttf', 'NanumSquareNeo-eHv.ttf', 'NanumSquareNeo-eHv.ttf'],
    'serif': ['SeoulHangangM.ttf', 'SeoulHangangB.ttf', 'SeoulHangangEB.ttf', 'SeoulHangangEB.ttf', 'SeoulHangangEB.ttf'],
}
PIXEL = {7: 'work/fonts/Galmuri7.ttf', 9: 'work/fonts/Galmuri9.ttf', 11: 'work/fonts/Galmuri11.ttf', 14: 'work/fonts/Galmuri14.ttf'}
_fc = {}


def font(kind, bold, px):
    if kind == 'pixel':
        k = min(PIXEL, key=lambda s: (abs(s - px), -s))
        path = PIXEL[k]
        if k == 11 and bold >= 2:
            path = 'work/fonts/Galmuri11-Bold.ttf'
        sz = {7: 8, 9: 10, 11: 12, 14: 15}[k]
    else:
        path = FONTS[kind][max(0, min(4, bold))]; sz = px
    key = (path, sz)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(os.path.join(ROOT, path), sz)
    return _fc[key]


def luma(c):
    return 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]


def sample_style(rgba):
    a = rgba[..., 3]
    m = a > 160
    if m.sum() < 4:
        m = a > 40
    px = rgba[m][:, :3].astype(float)
    if len(px) == 0:
        return dict(fill=(255, 255, 255), fill2=None, outline=None)
    L = luma(px)
    hi = px[L >= np.percentile(L, 70)]
    px2 = rgba[a > 40][:, :3].astype(float)
    L2 = luma(px2)
    lo = px2[L2 <= np.percentile(L2, 15)]
    fill = hi.mean(0)
    out = lo.mean(0) if len(lo) and luma(fill[None])[0] - luma(lo.mean(0)[None])[0] > 60 else None
    # vertical gradient of the bright part
    ys, xs = np.nonzero(m)
    Lm = luma(rgba[ys, xs, :3].astype(float))
    sel = Lm >= np.percentile(Lm, 60)
    yy = ys[sel]
    fill2 = None
    if len(yy) > 10:
        mid = np.median(yy)
        top = rgba[ys[sel][yy <= mid], xs[sel][yy <= mid], :3].mean(0)
        bot = rgba[ys[sel][yy > mid], xs[sel][yy > mid], :3].mean(0)
        if np.abs(top - bot).sum() > 60:
            fill, fill2 = top, bot
    # dark text on light/transparent background (no bright fill): use dark as fill
    if luma(fill[None])[0] < 90:
        out = None
    return dict(fill=tuple(int(v) for v in fill), fill2=None if fill2 is None else tuple(int(v) for v in fill2),
                outline=None if out is None else tuple(int(v) for v in out))


def erase(rgba, x, y, w, h, mode):
    H, W = rgba.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if mode == 'clear':
        rgba[y0:y1, x0:x1] = 0
    elif mode == 'fill':
        # per-row linear blend between left and right border pixels, then per-column top/bottom, averaged
        L = rgba[y0:y1, max(0, x0 - 1)].astype(float)
        R = rgba[y0:y1, min(W - 1, x1)].astype(float)
        T = rgba[max(0, y0 - 1), x0:x1].astype(float)
        B = rgba[min(H - 1, y1), x0:x1].astype(float)
        t = np.linspace(0, 1, x1 - x0)[None, :, None]
        hor = L[:, None] * (1 - t) + R[:, None] * t
        s = np.linspace(0, 1, y1 - y0)[:, None, None]
        ver = T[None] * (1 - s) + B[None] * s
        rgba[y0:y1, x0:x1] = ((hor + ver) / 2).astype(np.uint8)
    elif mode.startswith('inpaint'):
        # inpaint:THR[:DIL]  text = pixels brighter than THR (or darker if THR<0)
        import cv2
        from scipy import ndimage
        parts = mode.split(':')
        thr = float(parts[1]) if len(parts) > 1 else 170
        dil = int(parts[2]) if len(parts) > 2 else 2
        sub = rgba[y0:y1, x0:x1]
        L = luma(sub[..., :3].astype(float))
        m = (L > thr) if thr >= 0 else (L < -thr)
        m = ndimage.binary_dilation(m, iterations=dil)
        pad = 6
        Y0, Y1, X0, X1 = max(0, y0 - pad), min(H, y1 + pad), max(0, x0 - pad), min(W, x1 + pad)
        big = rgba[Y0:Y1, X0:X1]
        M = np.zeros(big.shape[:2], np.uint8)
        M[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = m * 255
        rgb = cv2.inpaint(np.ascontiguousarray(big[..., :3]), M, 4, cv2.INPAINT_TELEA)
        al = cv2.inpaint(np.ascontiguousarray(big[..., 3]), M, 4, cv2.INPAINT_TELEA)
        big[..., :3] = rgb; big[..., 3] = al
    elif mode.startswith('color:'):
        c = [int(v) for v in mode[6:].split(',')]
        rgba[y0:y1, x0:x1] = c


def render(text, w, h, st, kind, bold, size, align, vert, ow, spacing=0):
    S = 4
    lines = text.split('\n')
    if size is None:
        size = h / len(lines) * (0.92 if kind != 'pixel' else 1.0) if not vert else w * 0.92
    size = max(6, size)
    while True:
        if kind == 'pixel':
            f = font('pixel', bold, int(round(size)))
            fs = f.size
            big = False
        else:
            f = font(kind, bold, int(round(size * S)))
            fs = f.size
            big = True
        sc = S if big else 1
        # measure
        if not vert:
            widths = [f.getlength(l) + spacing * sc * max(0, len(l) - 1) for l in lines]
            tw = max(widths) / sc
            lh = h / len(lines)
            fitw = w - 2 * ow
            if tw <= fitw or size <= 6:
                break
            if kind == 'pixel':
                # pixel fonts: shrink by squeezing horizontally later
                break
            size *= max(0.8, fitw / tw * 0.99)
        else:
            th = len(text.replace('\n', '')) * size
            if th <= h or size <= 6:
                break
            size *= h / th * 0.99
    W, H = w * sc, h * sc
    if not big and not vert and tw > w - 2 * ow:
        W = int(tw) + 2 * ow + 2
    mask = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(mask)
    asc, desc = f.getmetrics()
    if not vert:
        lh = H / len(lines)
        for k, l in enumerate(lines):
            lw = f.getlength(l) + spacing * sc * max(0, len(l) - 1)
            x = {'l': ow * sc, 'c': (W - lw) / 2, 'r': W - lw - ow * sc}[align]
            bb = f.getbbox('한가A')
            gh = bb[3] - bb[1]
            y = k * lh + (lh - gh) / 2 - bb[1]
            if spacing:
                for ch in l:
                    d.text((x, y), ch, font=f, fill=255); x += f.getlength(ch) + spacing * sc
            else:
                d.text((x, y), l, font=f, fill=255)
    else:
        chars = list(text.replace('\n', ''))
        step = min(H / max(1, len(chars)), f.size * 1.05)
        y0 = {'l': 0, 'c': (H - step * len(chars)) / 2, 'r': H - step * len(chars)}[align]
        for k, ch in enumerate(chars):
            bb = f.getbbox(ch)
            cw, chh = bb[2] - bb[0], bb[3] - bb[1]
            if ch in 'ー―－-~～':
                # rotate long marks for vertical text
                tmp = Image.new('L', (int(f.size * 1.2), int(f.size * 1.2)), 0)
                ImageDraw.Draw(tmp).text((tmp.width / 2 - cw / 2 - bb[0], tmp.height / 2 - chh / 2 - bb[1]), ch, font=f, fill=255)
                tmp = tmp.rotate(-90)
                mask.paste(tmp, (int(W / 2 - tmp.width / 2), int(y0 + k * step + step / 2 - tmp.height / 2)), tmp)
                continue
            d.text((W / 2 - cw / 2 - bb[0], y0 + k * step + (step - chh) / 2 - bb[1]), ch, font=f, fill=255)
    if big:
        mask = mask.resize((w, h), Image.LANCZOS)
    else:
        # pixel font measured at 1x; squeeze if too wide
        bbx = mask.getbbox()
        if bbx and not vert and (bbx[2] - bbx[0] > w - 2 * ow or mask.width != w):
            crop = mask.crop((bbx[0], 0, bbx[2], h))
            nw = w - 2 * ow
            crop = crop.resize((nw, h), Image.LANCZOS)
            m2 = Image.new('L', (w, h), 0)
            m2.paste(crop, ({'l': ow, 'c': (w - nw) // 2, 'r': w - nw - ow}[align], 0))
            mask = m2
    m = np.asarray(mask, np.float32) / 255
    out = np.zeros((h, w, 4), np.float32)
    # outline
    if st.get('outline') is not None and ow > 0:
        om = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * ow + 1))
        om = np.asarray(om, np.float32) / 255
        out[..., :3] = np.array(st['outline'], np.float32)
        out[..., 3] = om
    fill = np.array(st['fill'], np.float32)
    if st.get('fill2') is not None:
        t = np.linspace(0, 1, h)[:, None, None]
        col = fill * (1 - t) + np.array(st['fill2'], np.float32) * t
    else:
        col = np.broadcast_to(fill, (h, w, 3))
    a = m[..., None]
    out[..., :3] = col * a + out[..., :3] * (1 - a) * (out[..., 3:4] > 0) + col * 0 * (1 - a) * (out[..., 3:4] == 0)
    out[..., 3] = np.maximum(out[..., 3], m)
    return out


def composite(rgba, x, y, layer):
    h, w = layer.shape[:2]
    H, W = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    L = layer[y0 - y:y1 - y, x0 - x:x1 - x]
    B = rgba[y0:y1, x0:x1].astype(np.float32)
    la = L[..., 3:4]
    ba = B[..., 3:4] / 255
    oa = la + ba * (1 - la)
    oc = (L[..., :3] * la + B[..., :3] * ba * (1 - la)) / np.maximum(oa, 1e-6)
    rgba[y0:y1, x0:x1, :3] = np.clip(oc, 0, 255).astype(np.uint8)
    rgba[y0:y1, x0:x1, 3] = np.clip(oa[..., 0] * 255, 0, 255).astype(np.uint8)


def quantize(rgba, pal, region=None):
    """map RGBA image to nearest palette index (alpha weighted)."""
    P = pal.astype(np.float32)
    src = rgba.reshape(-1, 4).astype(np.float32)
    out = np.empty(len(src), np.uint8)
    wgt = np.array([1, 1, 1, 1.5], np.float32)
    # premultiplied-ish distance: colour difference matters less when transparent
    for s in range(0, len(src), 4096):
        c = src[s:s + 4096]
        a = c[:, 3:4] / 255
        pa = P[None, :, 3] / 255
        dc = ((c[:, None, :3] - P[None, :, :3]) ** 2).sum(-1) * np.minimum(a, pa[..., None][..., 0] if False else pa)
        da = (c[:, None, 3] - P[None, :, 3]) ** 2 * 2.0
        out[s:s + 4096] = np.argmin(dc + da, 1)
    return out.reshape(rgba.shape[:2])


def apply(rgba, items):
    for it in items:
        x, y, w, h = it['box']
        sub = rgba[y:y + h, x:x + w].copy()
        st = sample_style(sub)
        for k in ('fill', 'fill2', 'outline'):
            if k in it:
                st[k] = tuple(it[k]) if it[k] is not None else None
        erase(rgba, x, y, w, h, it.get('erase', 'clear'))
        if not it.get('text'):
            continue
        kind = it.get('font', 'sans')
        ow = it.get('ow', 1 if st.get('outline') is not None else 0)
        pad = it.get('pad', 0)
        rw = w - 2 * pad
        if it.get('squeeze') and kind != 'pixel' and not it.get('vert'):
            # fixed glyph size; compress horizontally instead of shrinking
            sz = it.get('size') or h * 0.92
            f = font(kind, it.get('bold', 1), int(round(sz * 4)))
            need = max(f.getlength(l) for l in it['text'].split(chr(10))) / 4 + 2 * ow + 1
            if need > rw:
                lay = render(it['text'], int(need + 1), h, st, kind, it.get('bold', 1), sz, 'c', False, ow, it.get('spacing', 0))
                pm = np.concatenate([lay[..., :3] * lay[..., 3:4], lay[..., 3:4] * 255], -1)
                pm = np.asarray(Image.fromarray(np.clip(pm, 0, 255).astype(np.uint8), 'RGBA').resize((rw, h), Image.LANCZOS), np.float32)
                a = pm[..., 3:4] / 255
                composite(rgba, x + pad, y, np.concatenate([pm[..., :3] / np.maximum(a, 1e-3), a], -1))
                continue
        layer = render(it['text'], rw, h, st, kind, it.get('bold', 1), it.get('size'), it.get('align', 'l'),
                       it.get('vert', False), ow, it.get('spacing', 0))
        composite(rgba, x + pad, y, layer)
    return rgba
