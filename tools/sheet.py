import sys,json;sys.path.insert(0,'tools')
from glyph_ocr import cells
from PIL import Image,ImageDraw,ImageFont
import numpy as np
cs=cells(); r=json.load(open('work/glyphs.json',encoding='utf-8'))
a,b=int(sys.argv[1]),int(sys.argv[2]); out=sys.argv[3]
f=ImageFont.truetype('C:/Windows/Fonts/YuGothB.ttc',24)
n=b-a; cols=20; rows=(n+cols-1)//cols
im=Image.new('RGB',(cols*40,rows*70),'white'); d=ImageDraw.Draw(im)
for k in range(n):
    i=a+k; x=(k%cols)*40; y=(k//cols)*70
    g=Image.fromarray((np.clip(cs[i],0,15)*17).astype(np.uint8)).resize((30,30),Image.NEAREST)
    im.paste(g,(x+5,y+2))
    d.text((x+8,y+34),r[i]['ch'],font=f,fill='red')
im.save(out)
