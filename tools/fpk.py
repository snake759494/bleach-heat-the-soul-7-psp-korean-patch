"""FPK container: header (u32 checksum?, u32 count, u32 0x10, u32 total), then count x 48-byte
entries (name[32], u32 0, u32 offset, u32 csize, u32 usize); data 16-byte aligned.
csize == usize means stored raw; csize == 0 means empty."""
import struct, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import lz


def read(path):
    d = open(path, 'rb').read()
    hdr = struct.unpack_from('<4I', d)
    ents = []
    for k in range(hdr[1]):
        e = d[16 + k * 48:64 + k * 48]
        z, o, cs, us = struct.unpack_from('<4I', e, 0x20)
        ents.append(dict(name=e[:32].split(b'\0')[0].decode(), raw=e, z=z, off=o, cs=cs, us=us, data=d[o:o + cs]))
    return d, hdr, ents


def unpack(ent):
    if ent['cs'] == 0:
        return b''
    if ent['cs'] == ent['us']:
        return ent['data']
    return lz.decompress(ent['data'])


if __name__ == '__main__':
    import glob
    root = sys.argv[1]; dst = sys.argv[2]
    for f in sorted(glob.glob(os.path.join(root, '**', '*.fpk'), recursive=True)):
        rel = os.path.relpath(f, root)
        _, hdr, ents = read(f)
        for e in ents:
            out = os.path.join(dst, rel, e['name'])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'wb').write(unpack(e))
