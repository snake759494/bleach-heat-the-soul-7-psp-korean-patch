"""Detect text line boxes in a texture and save an annotated, enlarged view.
usage: boxes.py TID [scale] [gap]  -> work/tmp/bx_TID.png, prints boxes"""
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
def split(a,b):
    x,y,w,h=b
    if h<24: return [b]
    pr=a[y:y+h,x:x+w].sum(1).astype(float)
    mx=pr.max(); cuts=[]
    for r in range(6,h-6):
        if pr[r]<=0.12*mx and pr[r]==pr[max(0,r-4):r+5].min(): 
            if not cuts or r-cuts[-1]>6: cuts.append(r)
    if not cuts: return [b]
    res=[];s0=0
    for c in cuts+[h]:
        seg=a[y+s0:y+c,x:x+w]; cols=np.nonzero(seg.any(0))[0]; rows=np.nonzero(seg.any(1))[0]
        if len(cols) and len(rows): res.append([x+int(cols[0]),y+s0+int(rows[0]),int(cols[-1]-cols[0]+1),int(rows[-1]-rows[0]+1)])
        s0=c
    return res
def detect(rgba,gap=5,minh=5):
    a=rgba[...,3]>40
    d=ndimage.binary_dilation(a,structure=np.ones((1,gap*2+1)))
    d=ndimage.binary_dilation(d,structure=np.ones((3,1)))
    lab,n=ndimage.label(d)
    out=[]
    for sl in ndimage.find_objects(lab):
        y,x=sl[0].start,sl[1].start; h=sl[0].stop-y; w=sl[1].stop-x
        if h>=minh and w>=4: out+=split(a,[int(x),int(y),int(w),int(h)])
    out.sort(key=lambda b:(b[1]//8,b[0]))
    return out
if __name__=='__main__':
    tid=int(sys.argv[1]); sc=int(sys.argv[2]) if len(sys.argv)>2 else 2; gap=int(sys.argv[3]) if len(sys.argv)>3 else 5
    im=Image.open(f'work/tex/{tid:04d}.png').convert('RGBA'); a=np.asarray(im)
    bx=detect(a,gap)
    bg=Image.new('RGBA',im.size,(60,60,80,255)); bg.alpha_composite(im)
    bg=bg.resize((im.width*sc,im.height*sc),Image.NEAREST); d=ImageDraw.Draw(bg)
    for k,(x,y,w,h) in enumerate(bx):
        d.rectangle([x*sc,y*sc,(x+w)*sc-1,(y+h)*sc-1],outline=(255,0,0)); d.text((x*sc+1,y*sc),str(k),fill=(0,255,0))
    bg.save(f'work/tmp/bx_{tid}.png')
    print(json.dumps(bx))
