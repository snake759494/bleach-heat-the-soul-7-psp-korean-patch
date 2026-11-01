"""python tools/grid.py TID x0 y0 x1 y1 [scale] -> work/tmp/g.png with 10px grid"""
import sys
from PIL import Image, ImageDraw
t, x0, y0, x1, y1 = map(int, sys.argv[1:6]); s = int(sys.argv[6]) if len(sys.argv) > 6 else 3
im = Image.open(f'work/tex/{t:04d}.png').convert('RGBA').crop((x0, y0, x1, y1))
bg = Image.new('RGBA', im.size, (90, 90, 110, 255)); bg.alpha_composite(im)
bg = bg.resize((im.width * s, im.height * s), Image.NEAREST).convert('RGB')
o = Image.new('RGB', (bg.width + 30, bg.height + 14), (0, 0, 0)); o.paste(bg, (30, 14)); d = ImageDraw.Draw(o)
for x in range((x0 + 9) // 10 * 10, x1, 10):
    X = 30 + (x - x0) * s; d.line([(X, 14), (X, o.height)], fill=(255, 0, 0) if x % 50 == 0 else (90, 0, 0))
    if x % 50 == 0: d.text((X + 1, 1), str(x), fill=(255, 255, 0))
for y in range((y0 + 9) // 10 * 10, y1, 10):
    Y = 14 + (y - y0) * s; d.line([(30, Y), (o.width, Y)], fill=(255, 0, 0) if y % 50 == 0 else (90, 0, 0))
    if y % 50 == 0: d.text((1, Y + 1), str(y), fill=(255, 255, 0))
o.save('work/tmp/g.png')
