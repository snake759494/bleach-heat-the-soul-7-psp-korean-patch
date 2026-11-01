"""merge spec JSON (stdin, utf-8) into trans/images.json"""
import sys, json, io
p = 'trans/images.json'
s = json.load(open(p, encoding='utf-8'))
s.update(json.load(io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')))
json.dump(s, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(s))
