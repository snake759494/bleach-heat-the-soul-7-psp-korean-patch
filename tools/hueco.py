"""Hueco conquest mission name textures (305-310)"""
import json
import numpy as np
from PIL import Image

N = {'ひよ里': '히요리', '狛村': '코마무라', 'ヤミー': '얌미', '乱菊': '란기쿠', 'チルッチ': '칠루치', 'アーロニーロ': '아로니로 카이엔ver.',
     'マユリ': '마유리', 'ザエルアポロ': '자엘아폴로', '砕蜂夜一': '쇠봉&요루이치', 'ルキア白哉': '루키아&뱌쿠야', '弓親': '유미치카',
     '藍染雛森': '아이젠&히나모리', 'ゾマリ': '조마리', 'ルピ': '루피', '恋次': '렌지', '剣八': '켄파치', 'グリムジョー': '그림조',
     '白哉': '뱌쿠야', 'イヅル': '이즈루', 'ノイトラ': '노이토라', '東仙': '토센', '竜弦': '류켄', 'ダークルキア': '다크 루키아',
     'ウルキオラ': '울키오라', 'ルキアアーロニーロ': '루키아&아로니로 카이엔ver.', 'ネリエルノイトラ': '넬리엘&노이토라', '乱菊ギン': '란기쿠&긴',
     'ハリベル': '할리벨', '浮竹京楽': '우키타케&쿄라쿠', '元柳斎': '겐류사이', 'バラガン': '바라간', '草冠': '쿠사카', 'スターク': '스타크',
     '村正': '무라마사', 'ギン': '긴', '藍染': '아이젠'}
M = {'T': '토너먼트', 'BR': '배틀 로열', 'L': '리그전'}
C = {'憤怒': '분노', '強欲': '탐욕', '狂気': '광기', '陶酔': '도취', '破壊': '파괴', '絶望': '절망', '虚無': '허무', '犠牲': '희생', '老い': '노쇠', '孤独': '고독', '大逆': '대역'}
SEQ = [('憤怒', 'ひよ里'), ('憤怒', 'T'), ('憤怒', 'BR'), ('憤怒', '狛村'), ('憤怒', 'ヤミー'), ('強欲', '乱菊'), ('強欲', 'BR'), ('強欲', 'チルッチ'), ('強欲', 'L'),
       ('強欲', 'アーロニーロ'), ('狂気', 'L'), ('狂気', 'T'), ('狂気', 'BR'), ('狂気', 'マユリ'), ('狂気', 'ザエルアポロ'), ('陶酔', '砕蜂夜一'), ('陶酔', 'ルキア白哉'),
       ('陶酔', '弓親'), ('陶酔', '藍染雛森'), ('陶酔', 'ゾマリ'), ('破壊', 'ルピ'), ('破壊', '恋次'), ('破壊', 'BR'), ('破壊', '剣八'), ('破壊', 'グリムジョー'),
       ('絶望', '白哉'), ('絶望', 'BR'), ('絶望', 'T'), ('絶望', 'イヅル'), ('絶望', 'ノイトラ'), ('虚無', '東仙'), ('虚無', '竜弦'), ('虚無', 'ダークルキア'), ('虚無', 'L'),
       ('虚無', 'ウルキオラ'), ('犠牲', 'ルキアアーロニーロ'), ('犠牲', 'ネリエルノイトラ'), ('犠牲', '乱菊ギン'), ('犠牲', 'BR'), ('犠牲', 'ハリベル'), ('老い', 'BR'),
       ('老い', '浮竹京楽'), ('老い', 'L'), ('老い', '元柳斎'), ('老い', 'バラガン'), ('孤独', '剣八'), ('孤独', '草冠'), ('孤独', 'ノイトラ'), ('孤独', 'T'), ('孤独', 'スターク')]
TAIL = [('大逆', x) for x in ('村正', '草冠', '東仙', 'ギン', '藍染')]


def text(c, w):
    if w in M:
        return f'{C[c]}의 {M[w]}'
    return f'VS  {C[c]}의 {N[w]}'


def rows(a, x0, x1):
    pr = (a[:, x0:x1, 3] > 230).sum(1); out = []; st = None
    for y, v in enumerate(list(pr) + [0]):
        if v > 0 and st is None: st = y
        if v == 0 and st is not None:
            if y - st >= 8: out.append((st, y - st))
            st = None
    return out


def color(a, x, y, w, h):
    p = a[y:y + h, x:x + w].reshape(-1, 4).astype(int)
    p = p[(p[:, 3] > 230)]
    s = p[:, :3].max(1) - p[:, :3].min(1)
    p = p[s > 60]
    return [int(v) for v in np.median(p[:, :3], 0)] if len(p) else [200, 200, 200]


def build():
    s = json.load(open('trans/images.json', encoding='utf-8'))
    plan = {305: [((0, 255), SEQ[:25]), ((255, 512), SEQ[25:])],
            306: [((0, 255), SEQ[:18]), ((255, 512), SEQ[18:35])],
            307: [((0, 256), SEQ[35:])], 309: [((0, 256), TAIL)], 310: [((0, 256), TAIL)]}
    for t, cols in plan.items():
        a = np.asarray(Image.open(f'work/tex/{t:04d}.png').convert('RGBA'))
        items = []
        for (x0, x1), seq in cols:
            R = rows(a, x0, x1)
            if t == 306 and x0 == 255: R = [r for r in R if r[0] < 470]
            assert len(R) >= len(seq), (t, x0, len(R), len(seq))
            for (y, h), (c, w) in zip(R, seq):
                cs = np.nonzero((a[y:y + h, x0:x1, 3] > 60).any(0))[0]
                bx = [x0 + int(cs[0]), y - 1, int(cs[-1] - cs[0] + 1), h + 2]
                col = color(a, *bx)
                items.append({"box": bx, "erase": "clear", "text": None})
                items.append({"box": [bx[0], bx[1], x1 - bx[0] - 1, bx[3]], "text": text(c, w), "font": "serif", "bold": 4, "align": "l",
                              "squeeze": True, "size": round(h * 0.9), "fill": col, "outline": [255, 255, 255], "ow": 1, "erase": "none"})
        s[str(t)] = items
    json.dump(s, open('trans/images.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


build()
