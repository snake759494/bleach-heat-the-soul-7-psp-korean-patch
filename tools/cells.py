"""python tools/cells.py TID < [[x0,x1,y0,y1,text,{opts}],...]  -> tight-box spec merged into images.json"""
import sys, io, json, numpy as np
from PIL import Image
t = sys.argv[1]
base = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
cells = json.load(io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8'))
a = np.asarray(Image.open(f'work/tex/{int(t):04d}.png').convert('RGBA'))[..., 3] > 40
items = []
for c in cells:
    x0, x1, y0, y1, text = c[:5]
    sub = a[y0:y1, x0:x1]; cs = np.nonzero(sub.any(0))[0]; rs = np.nonzero(sub.any(1))[0]
    if not len(cs):
        print('empty', c); continue
    box = [x0 + int(cs[0]), y0 + int(rs[0]), int(cs[-1] - cs[0] + 1), int(rs[-1] - rs[0] + 1)]
    it = dict(base); it.update(box=box, text=text)
    if len(c) > 5: it.update(c[5])
    items.append(it)
s = json.load(open('trans/images.json', encoding='utf-8'))
s[t] = items
json.dump(s, open('trans/images.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
