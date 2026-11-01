# 빌드 방법

번역 대본·원문은 저장소에 없으므로, 아래는 자신이 가진 원본과 번역 파일로 다시 빌드하는 절차입니다.

## 준비물
- 원본 ISO `Bleach - Heat the Soul 7 (Japan).iso` (MD5 `b31eeedc05df9c7889ad6fe29726d3f6`)
- Python 3.12+ : `pip install pillow numpy scipy opencv-python websocket-client`
- 글꼴: `NanumSquareNeo-*.ttf`, `SeoulHangang*.ttf` (작업 폴더), `Galmuri*.ttf` (`work/fonts/`)

## 폴더 구성
```
<작업 폴더>/
  Bleach - Heat the Soul 7 (Japan).iso
  *.ttf
  tools/        (이 저장소의 tools)
  trans/        msg_ko*.json, atn_ko.json, hud_ko.json, story_lines.json, tutorial_lines.json, images.json  (번역 — 저장소 미포함)
  work/iso/     ISO를 풀어 둔 폴더
  work/x/       fpk를 풀어 둔 폴더 (<fpk 경로>/<항목 이름>)
  work/tex/     텍스처 PNG와 index.json
  work/eboot_dec.bin  복호화한 EBOOT
```

## 순서
1. ISO 풀기: `python tools/extract_iso.py` → `work/iso/`, fpk 해제(`tools/fpk.py`, `tools/lz.py`) → `work/x/`
2. EBOOT 복호화 → `work/eboot_dec.bin`
3. 원문 추출
   - 텍스처: `python tools/texdump.py` → `work/tex/*.png`, `index.json`
   - 글리프 메시지: `python tools/msgrec.py` → `work/msg_jp.json`
   - 소울 코드 표·HUD 이름: `tools/f16.py`, `python tools/hudtbl.py`
4. 번역 작성
   - `trans/msg_ko*.json` = `{원문: 번역}` — `python tools/msgcheck.py`로 길이·글자 검사
   - `trans/atn_ko.json` = 칭호·능력 `{원문: 번역}`, `trans/hud_ko.json` = `{캐릭터 번호: [변신 이름, 기본 이름]}`
   - `trans/images.json` = 텍스처별 글자 상자 사양 (`python tools/texedit.py <id> 미리보기.png`로 확인)
5. 빌드: `python tools/build.py` → `Bleach - Heat the Soul 7 (Korean).iso`
6. 차분: `xdelta3 -e -0 -s 원본.iso 한글.iso 패치.xdelta`

PPSSPP 원격 디버거로 자동 확인할 때는 `python tools/emu.py start <ISO>` / `shot` / `press` / `seq` 를 씁니다.
