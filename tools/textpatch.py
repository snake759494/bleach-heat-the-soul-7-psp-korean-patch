"""Non-image text: seq strings, EBOOT strings, PARAM.SFO, system font (Hangul PGF) and jis2ucs remap.
Used by build.py: files() -> {extracted fpk entry path: bytes}, iso_files() -> {iso path: bytes}"""
import os, sys, struct, json
sys.path.insert(0, os.path.dirname(__file__))

EBOOT = 'work/eboot_dec.bin'
VA0 = 0x8804000
OFF = 0x54
J2U = 'work/x/cmn/1000.fpk/cmn/jis2ucs.bin'
STORY_SEQ = 'work/x/cmn/1000.fpk/2d/story/0000.seq'
FONT_ISO = '/PSP_GAME/USRDIR/K.PGF'
FONT_PATH = b'disc0:/PSP_GAME/USRDIR/K.PGF\0'
FONT_OUT = 'work/cache/K.PGF'

TITLE = 'BLEACH ~히트 더 소울 7~'

# SJIS strings (drawn with the system font through jis2ucs)
SEQ = {
    'シークレットミッションが出現しました': '시크릿　미션이　출현했습니다',
    '特定のミッションを高いランクでクリアすると': '특정　미션을　높은　랭크로　클리어하면',
    'シークレットミッションが出現します': '시크릿　미션이　출현합니다',
}
EB_SJIS = {
    '新規作成データ': '새 데이터',
    'ブリーチ７': '블리치７',
    '通信が切断されました。\nWLAN/WIRELESSスイッチがオフになりました。\n×ボタンでメインメニューへ戻ります。':
        '통신이 끊어졌습니다.\nWLAN/WIRELESS 스위치가 꺼졌습니다.\n×버튼으로 메인 메뉴로 돌아갑니다.',
    '通信が切断されました。\n×ボタンでメインメニューへ戻ります。':
        '통신이 끊어졌습니다.\n×버튼으로 메인 메뉴로 돌아갑니다.',
    '対戦相手とのゲーム内容に差異が発生しました。\n通信エラーが発生したため、通信を切断します。\n×ボタンでメインメニューへ戻ります。':
        '대전 상대와 게임 내용에 차이가 발생했습니다.\n통신 오류가 발생하여 통신을 끊습니다.\n×버튼으로 메인 메뉴로 돌아갑니다.',
}
EB_U16 = {
    'ゲームデータをロードできませんでした。\n\rゲームデータの使用設定をオフにしました。':
        '게임 데이터를 로드하지 못했습니다.\n\r게임 데이터 사용 설정을 껐습니다.',
    'ゲームデータの破損のため、ロードに失敗しました。\n\rタイトル画面の「DATA INSTALL」から\n\r再度ゲームデータを\n\rインストールしなおしてください。\n\r\n\rゲームデータの使用設定をオフにしました。':
        '게임 데이터가 손상되어 로드에 실패했습니다.\n\r타이틀 화면의 「DATA INSTALL」에서\n\r게임 데이터를 다시\n\r설치해 주세요.\n\r\n\r게임 데이터 사용 설정을 껐습니다.',
    'BLEACH ～ヒート・ザ・ソウル７～のゲームデータ\n\rをインストールするには記録メディアに\n\rあと':
        'BLEACH ~히트 더 소울 7~의 게임 데이터를\n\r설치하려면 기록 미디어에\n\r앞으로 ',
    '以上の空き容量が必要です。\n\rデータ削除を行いますか？':
        ' 이상 여유 공간 필요\n\r데이터를 삭제할까요?',
    '既にBLEACH ～ヒート・ザ・ソウル７～の\n\rゲームデータが存在します。\n\r上書きしますか？':
        '이미 BLEACH ~히트 더 소울 7~의\n\r게임 데이터가 있습니다.\n\r덮어쓸까요?',
    'BLEACH ～ヒート・ザ・ソウル７～のゲームデータ\n\rをインストールするには記録メディアに\n\r140MB以上の空き容量が必要です。\n\rバッテリー残量にも注意してください。':
        'BLEACH ~히트 더 소울 7~의 게임 데이터를\n\r설치하려면 기록 미디어에\n\r140MB 이상의 여유 공간이 필요합니다.\n\r배터리 잔량에도 주의해 주세요.',
    'BLEACH ～ヒート・ザ・ソウル７～のゲームデータ\n\rの作成を中断しました。':
        'BLEACH ~히트 더 소울 7~의 게임 데이터\n\r생성을 중단했습니다.',
    'データインストールの機能を有効にするためには、\n\rメインメニューの「設定」にある\n\r「ゲームデータの使用」の項目を「オン」\n\rにする必要があります。\n\r\n\rゲームデータの使用設定を「オン」\n\rに設定しました。':
        '데이터 설치 기능을 사용하려면\n\r메인 메뉴의 「설정」에 있는\n\r「게임 데이터 사용」 항목을 「켬」으로\n\r해야 합니다.\n\r\n\r게임 데이터 사용 설정을\n\r「켬」으로 설정했습니다.',
    '総容量が256MB以上ある\n\r記録メディアを使用してください。':
        '총용량 256MB 이상인\n\r기록 미디어를 사용해 주세요.',
}
DESC = ('4명의 소울이 격렬하게 부딪친다!! 초거대 캐릭터가 격렬하게 날뛴다!! '
        '새로운 배틀 요소인 4인 대전과 초거대 캐릭터 탑재로 새로운 진화를 이룬 '
        '『BLEACH』 대전 격투 액션 제7탄 여기에 등장! 소울이 교차할 때 새로운 역사가 태어난다')
EB_U8 = {
    'BLEACH ～ヒート・ザ・ソウル７～': TITLE,
    'セーブデータ': '세이브 데이터',
    'ゲームデータ': '게임 데이터',
    '４人のソウルが激しくぶつかり合う！！超巨大キャラクターが激しく暴れまわる！！新バトル要素の４人対戦と超巨大キャラクターの搭載で新たな進化を遂げた『BLEACH』対戦格闘アクション第７弾 ここに登場！ソウルが交わるとき 新たな歴史が生まれる': DESC,
}


# ---------- JIS slots for Hangul ----------
def sjis_of_jis(j):
    j1, j2 = j >> 8, j & 0xff
    s1 = (j1 + 1) // 2 + (0x70 if j1 <= 0x5e else 0xb0)
    if j1 & 1:
        s2 = j2 + (0x1f if j2 <= 0x5f else 0x20)
    else:
        s2 = j2 + 0x7e
    return bytes([s1, s2])


def hangul_map():
    """assign each Hangul syllable used in SJIS text to a free JIS slot (rows 0x29-0x2f, empty in JIS X 0208)"""
    chars = sorted({c for t in list(SEQ.values()) + list(EB_SJIS.values()) for c in t if 0xac00 <= ord(c) <= 0xd7a3})
    j2u = bytearray(open(J2U, 'rb').read())
    slots = [(r << 8) | c for r in range(0x29, 0x30) for c in range(0x21, 0x7f)]
    slots = [s for s in slots if struct.unpack_from('<H', j2u, s * 2)[0] == 0]
    assert len(chars) <= len(slots)
    m = {}
    for ch, s in zip(chars, slots):
        struct.pack_into('<H', j2u, s * 2, ord(ch))
        m[ch] = sjis_of_jis(s)
    return m, bytes(j2u)


def enc_sjis(t, m):
    out = b''
    for ch in t:
        out += m[ch] if ch in m else ch.encode('cp932')
    return out


def put(d, old, new, cap_extra=True):
    """replace every occurrence of NUL-terminated old with new (padded with NULs)"""
    n = 0
    i = 0
    while True:
        i = d.find(old + b'\0', i)
        if i < 0:
            break
        if i > 0 and d[i - 1] != 0 and not cap_extra:
            i += 1; continue
        cap = len(old)
        while (i + cap + 1) % 4 and d[i + cap + 1] == 0:   # alignment padding after the NUL
            cap += 1
        assert len(new) <= cap, (new.decode('utf-8', 'replace'), cap)
        d[i:i + cap] = new + b'\0' * (cap - len(new))
        n += 1
        i += len(old)
    return n


def put16(d, old, new):
    o = old.encode('utf-16le'); nw = new.encode('utf-16le')
    i = d.find(o + b'\0\0')
    assert i >= 0 and i % 2 == 0, old[:10]
    assert len(nw) <= len(o), (new, len(nw), len(o))
    d[i:i + len(o)] = nw + b'\0' * (len(o) - len(nw))


def ins(d, va, w):
    struct.pack_into('<I', d, va - VA0 + OFF, w)


def word(d, va):
    return struct.unpack_from('<I', d, va - VA0 + OFF)[0]


def patch_font(d):
    """sceFontGetFontList stub -> sceFontOpenUserFile; open(lib,0) -> OpenUserFile(lib, K.PGF)"""
    # NID table: find GetFontList NID 0xBC75D85B and swap it to OpenUserFile 0x57FCB733
    nid = struct.pack('<I', 0xBC75D85B)
    i = d.find(nid)
    assert i > 0 and d.find(nid, i + 1) < 0
    struct.pack_into('<I', d, i, 0x57FCB733)
    # path string over "font_error:B" + "font_error:C" (48 bytes)
    po = 0x8a10d30 - VA0 + OFF
    assert d[po:po + 13] == b'font_error:B,' and d[po + 24:po + 37] == b'font_error:C,'
    d[po:po + len(FONT_PATH)] = FONT_PATH
    hi = (0x8a10d30 + 0x8000) >> 16; lo = 0x8a10d30 & 0xffff
    assert word(d, 0x890b7f4) == 0x0c000000 | (0x89f8664 >> 2)
    assert word(d, 0x890b834) == 0x0c000000 | (0x89f865c >> 2)
    ins(d, 0x890b7f0, 0x00003025)        # move a2, zero
    ins(d, 0x890b7f4, 0x00001025)        # move v0, zero   (no GetFontList)
    ins(d, 0x890b824, 0x3c0408aa)        # lui  a0, 0x8aa
    ins(d, 0x890b828, 0x8c843074)        # lw   a0, 0x3074(a0)
    ins(d, 0x890b82c, 0x3c050000 | hi)   # lui  a1, hi
    ins(d, 0x890b830, 0x24a50000 | lo)   # addiu a1, a1, lo
    ins(d, 0x890b834, 0x0c000000 | (0x89f8664 >> 2))  # jal OpenUserFile


def eboot(m):
    d = bytearray(open(EBOOT, 'rb').read())
    for jp, kr in EB_SJIS.items():
        n = put(d, jp.encode('cp932'), enc_sjis(kr, m))
        assert n, jp
    for jp, kr in EB_U16.items():
        put16(d, jp, kr)
    for jp, kr in EB_U8.items():
        n = put(d, jp.encode('utf-8'), kr.encode('utf-8'))
        assert n, jp
    patch_font(d)
    import f16patch
    f16patch.eboot(d)
    return bytes(d)


def sfo(data):
    d = bytearray(data)
    kt, dt, n = struct.unpack_from('<III', d, 8)
    for k in range(n):
        ko, fmt, ln, mx, do = struct.unpack_from('<HHIII', d, 20 + 16 * k)
        key = d[kt + ko:d.index(b'\0', kt + ko)].decode()
        if key == 'TITLE':
            v = TITLE.encode('utf-8') + b'\0'
            assert len(v) <= mx
            d[dt + do:dt + do + mx] = v + b'\0' * (mx - len(v))
            struct.pack_into('<I', d, 20 + 16 * k + 4, len(v))
    return bytes(d)


def font():
    if not os.path.exists(FONT_OUT):
        import build_font
        txt = ''.join(list(SEQ.values()) + list(EB_SJIS.values()) + list(EB_U16.values()) + list(EB_U8.values()))
        build_font.build_all([ord(c) for c in txt if 0xac00 <= ord(c) <= 0xd7a3], FONT_OUT)
    return open(FONT_OUT, 'rb').read()


def files():
    m, j2u = hangul_map()
    out = {J2U: j2u}
    d = bytearray(open(STORY_SEQ, 'rb').read())
    for jp, kr in SEQ.items():
        assert put(d, jp.encode('cp932'), enc_sjis(kr, m)), jp
    out[STORY_SEQ] = bytes(d)
    import msgpatch
    out.update(msgpatch.files(out))
    import f16patch
    out.update(f16patch.files())
    return out


def iso_files():
    m, _ = hangul_map()
    e = eboot(m)
    from isobuild import Iso
    sf = open('work/iso/PSP_GAME/PARAM.SFO', 'rb').read()
    return {'/PSP_GAME/SYSDIR/EBOOT.BIN': e, '/PSP_GAME/SYSDIR/BOOT.BIN': e,
            '/PSP_GAME/PARAM.SFO': sfo(sf), FONT_ISO: font()}
