"""trans/story_lines.json + detected line boxes -> trans/images.json entries for story textures"""
import json, sys
sys.path.insert(0, 'tools')
import numpy as np
from PIL import Image
from boxes import detect
tr = json.load(open('trans/story_lines.json', encoding='utf-8'))
s = json.load(open('trans/images.json', encoding='utf-8'))
for t in range(556, 592):
    a = np.asarray(Image.open(f'work/tex/{t:04d}.png').convert('RGBA'))
    W = a.shape[1]
    items = []
    for k, (x, y, w, h) in enumerate(detect(a, 12)):
        txt = tr.get(f'{t}:{k}')
        if not txt:
            continue
        if t >= 559:   # dialogue: full-width centered rows
            box = [0, y - 1, W, h + 2]
        else:
            box = [x - 1, y - 1, w + 2, h + 2]
        items.append({"box": box, "text": txt, "font": "pixel", "bold": 2, "size": 11, "align": "c",
                      "fill": [255, 255, 255], "outline": [20, 20, 30], "ow": 1,
                      "erase": "clear"})
        # erase the original glyphs exactly
        items.insert(0, {"box": [x - 1, y - 1, w + 2, h + 2], "erase": "clear", "text": None})
    if items:
        s[str(t)] = items
json.dump(s, open('trans/images.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(s))
