"""Check a translation file against the glyph-record limits.
  python tools/msgcheck.py trans/msg_ko_xxx.json [work/tmp/todo_xxx.json]
Limits per entry: encoded length <= original record capacity, same {n} tokens,
no more lines than the original, each line no wider than the widest original line,
only hangul / kana / full-width ASCII / the symbols in the font."""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))
import msgpatch as m

tr = json.load(open(sys.argv[1], encoding='utf-8'))
todo = json.load(open(sys.argv[2], encoding='utf-8')) if len(sys.argv) > 2 else None
caps = {}
ch = m.glyphs()
for p in m.seqfiles():
    for i, B, ln, w in m.records(open(p, 'rb').read()):
        jp = m.decode(w, ch)
        caps[jp] = min(caps.get(jp, 9999), B // 2)
inv = {c: i for i, c in sorted(ch.items(), reverse=True) if i < m.FIRST}
bad = 0


def width(line):
    return len(re.sub(r'\{\d+\}', '00', line))


for jp, ko in tr.items():
    err = []
    if jp not in caps:
        err.append('unknown key')
    else:
        n = len(m.encode_plain(re.sub(r'\{\d+\}', '', ko), {c: 1 for c in m.norm(ko)})) + 2 * len(re.findall(r'\{\d+\}', ko))
        if n > caps[jp]:
            err.append(f'too long {n}>{caps[jp]}')
        if sorted(re.findall(r'\{\d+\}', ko)) != sorted(re.findall(r'\{\d+\}', jp)):
            err.append('tokens differ')
        if ko.count('\n') > jp.count('\n'):
            err.append('more lines')
        wj = max(width(l) for l in jp.split('\n'))
        wk = max(width(l) for l in ko.split('\n'))
        if wk > wj:
            err.append(f'line too wide {wk}>{wj}')
        for c in m.norm(re.sub(r'\{\d+\}', '', ko)):
            if c not in '\n　' and c not in inv and not 0xac00 <= ord(c) <= 0xd7a3:
                err.append(f'bad char {c!r}')
    if err:
        bad += 1
        print(json.dumps(jp, ensure_ascii=False), '=>', ', '.join(err))
if todo:
    keys = {a for a, b in todo}
    miss = keys - set(tr)
    print(f'missing {len(miss)} of {len(keys)}')
print(f'{len(tr)} entries, {bad} with problems')
