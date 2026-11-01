# 기술 문서

## 디스크 구성
- `PSP_GAME/SYSDIR/EBOOT.BIN`: 암호화된 실행 파일. 복호화하면 고정 주소 ELF(가상 주소 0x08804000, 파일 오프셋 0x54). 패치는 복호화한 실행 파일을 EBOOT.BIN·BOOT.BIN으로 넣습니다.
- `PSP_GAME/USRDIR/data/fpack/**.fpk`: 데이터 묶음. 헤더 16바이트(데이터 영역 16비트 합 체크섬, 항목 수, 0x10, 파일 크기) + 항목 48바이트(이름 32, 0, 오프셋, 압축 크기, 원래 크기).
- 압축: 비트·바이트 혼합 LZ(EBOOT 0x089375C8의 해제 루틴). `tools/lz.py`가 해제·재압축을 왕복 검증합니다.
- `fpack/sector.lst`: 파일별 (경로, LBA, 크기). 파일을 옮기거나 늘리면 갱신합니다(`tools/build.py`).

## 텍스트 종류
1. **텍스처**(.ttd 안의 TIM2, 4/8bpp CLUT): 메뉴·도움말 띠·설명문 대부분. 상자 사양(`trans/images.json`)에 따라 원문을 지우고(clear/fill/inpaint) 한글을 그린 뒤 원래 팔레트로 다시 양자화합니다(`tools/imgtext.py`, `tools/texedit.py`).
2. **글리프 번호 메시지**(seq 안 `06 11 06 20` 레코드): u16 = 15px 글꼴 `font/1000.ttd`의 칸 번호(17×17×5쪽). 한자 칸(261~)을 한글로 바꾸고 문장을 다시 인코딩합니다. **seq 파일이 커지면 게임이 멈추므로** 번역은 원래 레코드 길이 안에 맞춥니다(`tools/msgpatch.py`).
3. **16px 전투 글꼴** `2d/cmn/0000.ttd`(12px 칸 21×21×2쪽, 공백 0xFF20, 끝 0xFFFE): 소울 코드 표 `cmn/attach_name.atn`·`attach_mat_name.atn`(24바이트 칸 7개 = 168바이트 블록, 칸당 10자)과 배틀 HUD 이름이 씁니다. 캐릭터 선택 화면의 큰 글꼴(`2d/chrsel/1000.ttd`, 22px 칸 23열)도 같은 번호 순서라 함께 한글을 그립니다(`tools/f16patch.py`).
4. **배틀 HUD 이름**: EBOOT 0x089C1A78 함수가 캐릭터 번호별 92갈래 점프표로 `li`/`sh` 명령을 이어 이름을 씁니다. 함수 본문을 「번호 → 문자열 포인터」 표를 복사하는 짧은 루프로 바꾸고, 남는 공간에 표와 한글 문자열을 넣었습니다(a2=0 변신 이름, a2=6 기본 이름). 원래 이름 목록은 `tools/hudtbl.py`로 뽑습니다.
5. **EBOOT 문자열**: 세이브 정보(UTF-8), 통신 오류(SJIS, 시스템 글꼴), `li` 즉시값으로 만드는 짧은 문구(랜덤·소울코드·소울파츠).

## 시스템 글꼴
- 게임은 sceFont로 jpn0을 엽니다. import NID를 `sceFontOpenUserFile`로 바꾸고 디스크의 `USRDIR/K.PGF`(jpn0 + 한글 병합)를 열게 했습니다.
- SJIS 문자열의 한글은 `cmn/jis2ucs.bin`에서 쓰지 않는 SJIS 코드를 한글 UCS로 다시 매핑해 표시합니다.

## 확인 방법
PPSSPP 원격 디버거(`tools/ppsspp_rpc.py`, `tools/emu.py`)로 버튼 입력·화면 캡처·메모리 쓰기 중단점을 걸어, 화면 글자가 어느 코드·데이터에서 오는지 추적했습니다.
