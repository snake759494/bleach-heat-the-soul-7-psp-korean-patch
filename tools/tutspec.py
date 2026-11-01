"""tutorial pages -> images.json entries"""
import json, sys
sys.path.insert(0, 'tools')
import numpy as np
from PIL import Image
from tutlines import lines

tr = json.load(open('trans/tutorial_lines.json', encoding='utf-8'))
por = json.load(open('trans/tutorial_portrait.json', encoding='utf-8'))
s = json.load(open('trans/images.json', encoding='utf-8'))


def runs(a, y, h, x0, thr):
    pr = (a[y:y + h, x0:] > thr).sum(1); out = []; st = None
    for i, v in enumerate(list(pr) + [0]):
        if v > 0 and st is None: st = i
        if v == 0 and st is not None:
            if i - st >= 5: out.append((y + st, i - st))
            st = None
    return out


RGB = None


def item(x, y, h, text):
    sub = RGB[y:y + h, x:510]
    m = sub[..., 3] > 200
    px = sub[m][:, :3].astype(int) if m.any() else np.zeros((1, 3), int)
    br = px[px.sum(1) > 450]
    big = len(br) > 0 and (br[:, 0].mean() - br[:, 2].mean()) > 35
    text = text.replace('・', '·')
    return {"box": [x, y, 510 - x, h], "text": text, "bold": 3 if big else 2, "size": 16 if big else 13,
            "align": "l", "squeeze": True, "erase": "clear", "fill": [255, 236, 150] if big else [255, 255, 255], "outline": [20, 20, 30], "ow": 1}


for t in range(660, 693):
    RGB = np.asarray(Image.open(f'work/tex/{t:04d}.png').convert('RGBA'))
    A = RGB[..., 3]
    bx, pic = lines(t)
    items = []
    for k, (x, y, w, h) in enumerate(bx):
        key = f'{t}:{k}'
        if str(t) in por and k == 0 and key not in tr:
            # portrait panel: text right of the face
            colc = (A[y:y + h, :] > 60).sum(0)
            px = x + 60
            while px < 500 and colc[px] > h * 0.15: px += 1
            rs = []
            for yy, hh in runs(A, y, h, px, 60):
                if hh < 10: continue
                rs += [(yy, hh // 2), (yy + hh // 2, hh - hh // 2)] if hh >= 26 else [(yy, hh)]
            L = por[str(t)]
            if len(rs) != len(L):
                print('portrait mismatch', t, rs, len(L))
            cols = np.nonzero((A[rs[0][0]:rs[0][0] + rs[0][1], px:] > 60).any(0))[0]
            xx = px + int(cols[0])
            for (yy, hh), txt in zip(rs, L):
                txt = txt.replace('・', '·')
                items.append({"box": [xx - 1, yy - 1, 510 - xx, hh + 2], "erase": "clear", "text": None})
                items.append(dict(item(xx, yy - 1, hh + 2, txt), font="pixel", size=11, bold=2, fill=[255, 255, 255], outline=[20, 20, 30], ow=1))
            continue
        if key not in tr:
            continue
        L = tr[key].split('\n')
        items.append({"box": [x - 1, y, 512 - x, h], "erase": "clear", "text": None})
        if len(L) == 1:
            rs = [(y, h)]
        else:
            rs = runs(A, y, h, x, 200)
            if len(rs) != len(L):
                rs2 = runs(A, y, h, x, 250)
                rs = rs2 if len(rs2) == len(L) else None
            if rs is None:
                print('split fail', key, len(L)); step = h / len(L)
                rs = [(int(y + i * step), int(step)) for i in range(len(L))]
            else:
                rs = [(yy - 1, hh + 2) for yy, hh in rs]
        for (yy, hh), txt in zip(rs, L):
            cols = np.nonzero((A[yy:yy + hh, x:] > 60).any(0))[0]
            items.append(item(x + (int(cols[0]) if len(cols) else 0), yy, hh, txt))
    if items:
        s[str(t)] = items
json.dump(s, open('trans/images.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
