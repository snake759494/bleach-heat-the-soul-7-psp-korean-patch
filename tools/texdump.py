"""Dump every unique 2D texture (excluding chr/eft/stg) to work/tex/NNNN.png + work/tex/index.json"""
import os,sys,json,hashlib;sys.path.insert(0,os.path.dirname(__file__))
from tim2 import parse_ttd,decode
from PIL import Image
root='work/x'; out='work/tex'; os.makedirs(out,exist_ok=True)
idx=[];seen={}
for dp,_,fs in sorted(os.walk(root)):
    for f in sorted(fs):
        if not f.endswith('.ttd'): continue
        p=os.path.join(dp,f).replace(os.sep,'/')
        inner=p.split('.fpk/')[1]
        if inner.startswith(('chr/','eft/','stg/')): continue
        d=open(p,'rb').read()
        for k,(i,n) in enumerate(parse_ttd(d)):
            blob=d[i:i+n]; h=hashlib.md5(blob).hexdigest()
            if h in seen: seen[h]['dups'].append([p,k]); continue
            im,info=decode(d,i)
            e=dict(id=len(idx),file=p,k=k,w=info['w'],h=info['h'],md5=h,dups=[])
            seen[h]=e; idx.append(e)
            im.save(f'{out}/{e["id"]:04d}.png')
json.dump(idx,open(f'{out}/index.json','w'),indent=0)
print(len(idx))
