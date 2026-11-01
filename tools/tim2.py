"""TIM2 decode (PSP, 4/8bpp CLUT, 32bpp), optional swizzle detection by header flag"""
import struct
import numpy as np
from PIL import Image

def parse_ttd(d):
    """ttd: u32 count, then entries; returns list of (name, tim2_offset, tim2_size)"""
    out=[]; i=0
    while True:
        i=d.find(b'TIM2',i)
        if i<0: break
        tot=struct.unpack_from('<I',d,i+16)[0]
        out.append((i,16+tot)); i+=16+tot
    return out

def decode(d, i):
    tot,pal,img,hs,cc,pf,mip,cf,ff,w,h=struct.unpack_from('<IIIHHBBBBHH',d,i+16)
    base=i+16+hs
    px=d[base:base+img]; pl=d[base+img:base+img+pal]
    if ff==5: idx=np.frombuffer(px,np.uint8)[:w*h]
    elif ff==4:
        b=np.frombuffer(px,np.uint8); idx=np.empty(b.size*2,np.uint8); idx[0::2]=b&15; idx[1::2]=b>>4; idx=idx[:w*h]
    elif ff==3:
        return Image.frombytes('RGBA',(w,h),px[:w*h*4]),dict(w=w,h=h,ff=ff)
    else: raise ValueError(ff)
    n=cc
    P=np.frombuffer(pl[:n*4],np.uint8).reshape(-1,4).copy()
    if ff==5 and n==256 and (cf&0x80)==0:
        # CSM1 swizzle of 8bpp palettes
        P2=P.copy()
        for k in range(256):
            j=(k&0xe7)|((k&0x08)<<1)|((k&0x10)>>1); P2[k]=P[j]
        P=P2
    P[:,3]=np.minimum(255,P[:,3].astype(int)*2)
    rgba=P[idx].reshape(h,w,4)
    return Image.fromarray(rgba,'RGBA'),dict(w=w,h=h,ff=ff,cf=cf)


def palette(d, i):
    """RGBA palette in index order (after CSM1 unswizzle), alpha scaled 0..255"""
    tot,pal,img,hs,cc,pf,mip,cf,ff,w,h=struct.unpack_from('<IIIHHBBBBHH',d,i+16)
    base=i+16+hs
    P=np.frombuffer(d[base+img:base+img+cc*4],np.uint8).reshape(-1,4).copy()
    if ff==5 and cc==256 and (cf&0x80)==0:
        P2=P.copy()
        for k in range(256):
            j=(k&0xe7)|((k&0x08)<<1)|((k&0x10)>>1); P2[k]=P[j]
        P=P2
    P=P.astype(np.int32); P[:,3]=np.minimum(255,P[:,3]*2)
    return P


def indices(d, i):
    tot,pal,img,hs,cc,pf,mip,cf,ff,w,h=struct.unpack_from('<IIIHHBBBBHH',d,i+16)
    base=i+16+hs
    if ff==5: return np.frombuffer(d[base:base+w*h],np.uint8).reshape(h,w).copy()
    b=np.frombuffer(d[base:base+w*h//2],np.uint8); a=np.empty(b.size*2,np.uint8); a[0::2]=b&15; a[1::2]=b>>4
    return a.reshape(h,w)


def put_indices(d, i, idx):
    """write index image back in place; d is bytearray"""
    tot,pal,img,hs,cc,pf,mip,cf,ff,w,h=struct.unpack_from('<IIIHHBBBBHH',d,i+16)
    base=i+16+hs
    if ff==5: d[base:base+w*h]=idx.astype(np.uint8).tobytes()
    else:
        a=idx.astype(np.uint8).ravel(); d[base:base+w*h//2]=(a[0::2]|(a[1::2]<<4)).tobytes()
