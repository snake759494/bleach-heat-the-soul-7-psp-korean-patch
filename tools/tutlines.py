"""line boxes for tutorial pages: row projection right of the picture column"""
import numpy as np
from PIL import Image


def lines(t):
    a = np.asarray(Image.open(f'work/tex/{t:04d}.png').convert('RGBA'))[..., 3] > 60
    pic = a[:, :148].mean() > 0.3
    if pic:
        a = a.copy(); a[:, :152] = 0
    pr = a.sum(1); runs = []; s = None
    for y, v in enumerate(list(pr) + [0]):
        if v > 0 and s is None: s = y
        if v == 0 and s is not None: runs.append((s, y - s)); s = None
    out = []
    for y, h in runs:
        if h < 7: continue
        cols = np.nonzero(a[y:y + h].any(0))[0]
        out.append([int(cols[0]), y, int(cols[-1] - cols[0] + 1), h])
    return out, pic
