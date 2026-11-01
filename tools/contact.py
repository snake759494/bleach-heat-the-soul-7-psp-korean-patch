import sys,json
from PIL import Image,ImageDraw
ids=[int(x) for x in sys.argv[2].split(',')] if ',' in sys.argv[2] else list(range(int(sys.argv[2].split('-')[0]),int(sys.argv[2].split('-')[1])+1))
out=sys.argv[1]; T=int(sys.argv[3]) if len(sys.argv)>3 else 400
cols=4; rows=(len(ids)+cols-1)//cols
sh=Image.new('RGB',(cols*T,rows*(T+14)),(40,40,40)); d=ImageDraw.Draw(sh)
for n,i in enumerate(ids):
    im=Image.open(f'work/tex/{i:04d}.png').convert('RGBA')
    k=min(T/im.width,T/im.height,1.0)
    im=im.resize((max(1,int(im.width*k)),max(1,int(im.height*k))),Image.LANCZOS)
    bg=Image.new('RGBA',im.size,(90,90,110,255)); bg.alpha_composite(im)
    x=(n%cols)*T; y=(n//cols)*(T+14)
    sh.paste(bg.convert('RGB'),(x,y+14)); d.text((x+2,y),str(i),fill=(255,255,0))
sh.save(out)
