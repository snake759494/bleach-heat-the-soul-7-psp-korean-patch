"""Apply image text specs to textures.  trans/images.json: {"<tex id>": [items...]}"""
import os,sys,json;sys.path.insert(0,os.path.dirname(__file__))
import numpy as np
from PIL import Image
import tim2, imgtext

def edit_blob(d, i, items):
    """d bytearray of ttd, i TIM2 offset"""
    pal=tim2.palette(d,i); idx=tim2.indices(d,i)
    rgba=pal[idx].astype(np.uint8)
    new=imgtext.apply(rgba.copy(),items)
    H,W=idx.shape
    m=np.zeros((H,W),bool)
    for it in items:
        x,y,w,h=it['box']; m[max(0,y):y+h,max(0,x):x+w]=True
    ys,xs=np.nonzero(m)
    if len(ys):
        y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
        q=imgtext.quantize(new[y0:y1,x0:x1],pal)
        sub=idx[y0:y1,x0:x1]; mm=m[y0:y1,x0:x1]; sub[mm]=q[mm]
    if pal.shape[0]<=16: idx=np.minimum(idx,15)
    tim2.put_indices(d,i,idx)
    return pal[idx].astype(np.uint8)

def preview(tid, items, out):
    idx=json.load(open('work/tex/index.json'))
    e=idx[tid]; d=bytearray(open(e['file'],'rb').read())
    i=tim2.parse_ttd(d)[e['k']][0]
    rgba=edit_blob(d,i,items)
    im=Image.fromarray(rgba,'RGBA'); bg=Image.new('RGBA',im.size,(70,70,90,255)); bg.alpha_composite(im)
    bg.save(out)

if __name__=='__main__':
    spec=json.load(open('trans/images.json',encoding='utf-8'))
    tid=sys.argv[1]
    preview(int(tid),spec[tid],sys.argv[2])
