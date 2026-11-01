# BLEACH 히트 더 소울 7 (PSP) 비공식 한글패치

PSP 일본판 **BLEACH ～ヒート・ザ・ソウル7～ (블리치 히트 더 소울 7, UCJS-10110)** 비공식 한국어 패치입니다. 이 저장소에는 제작 도구와 기술 문서만 있고, 패치 파일(xdelta)은 [Releases](../../releases)에서 받을 수 있습니다. 게임 원본·일본어 원문·번역 대본은 포함하지 않습니다.

## 적용 방법
1. 아래 해시와 일치하는 **원본 `.iso`** 를 준비합니다. (CSO·CHD 등으로 변환한 이미지에는 적용할 수 없습니다.)
   - PowerShell: `Get-FileHash -Algorithm MD5 -LiteralPath '.\Bleach - Heat the Soul 7 (Japan).iso'`
2. xdeltaUI 같은 도구로 원본 `.iso` 에 `Bleach_HeatTheSoul7_KO_v1.0.xdelta` 를 적용합니다. (Patch = xdelta, Source File = 원본 ISO, Output File = 새 파일명)
   - 명령줄: `xdelta3 -d -s "Bleach - Heat the Soul 7 (Japan).iso" Bleach_HeatTheSoul7_KO_v1.0.xdelta "Bleach - Heat the Soul 7 (Korean).iso"`
3. 만들어진 ISO를 PPSSPP 또는 커스텀 펌웨어(PSP·PS Vita Adrenaline 등)에서 실행합니다.

| 항목 | 값 |
| --- | --- |
| 원본 ISO 크기 | 560,496,640 바이트 |
| 원본 ISO MD5 | `b31eeedc05df9c7889ad6fe29726d3f6` |
| 원본 ISO SHA-256 | `895b827184aeb4403567d258a52d140bec2af302f723759e08f5889cf89bc26a` |
| xdelta SHA-256 | `d8a2e68e81ed5a2d1b0d072b6f8a447bc471cd246c7b7b4f72c7c6a8240c5328` |
| 결과 ISO 크기 | 574,310,400 바이트 |
| 결과 ISO SHA-256 | `58db6bd5a821fb21db8d37f3cfbbed0dcb37324e2d7921d5092a5332acdb7b20` |

## 주의
- 복호화한 실행 파일을 EBOOT로 넣었기 때문에 **PPSSPP·커스텀 펌웨어 전용**입니다. 정품 펌웨어에서는 부팅되지 않습니다.
- 원본이나 다른 버전 패치에서 만든 **상태저장(세이브 스테이트)** 은 불러오지 마세요. 일반 세이브는 그대로 쓸 수 있습니다.
- xdelta는 압축하지 않은 형식(`-0`)입니다(약 19MB).

## 한글화 내용
- 글리프 번호 방식 메시지 약 1,100종 — 메뉴 안내, 캐릭터 선택·소울 코드 설명, 갤러리·프로필, 시스템 메시지
- 스토리 대사 285줄, 튜토리얼 안내 172줄 직접 번역
- 소울 코드 칭호 305개·능력 설명 295개(16px 전투 글꼴)
- 배틀 HUD 캐릭터 이름 84명(시해·만해·귀인·허로우화 등 변신 이름 포함) — 실행 파일의 이름 생성 함수를 표 방식으로 교체
- 실행 파일 문자열 — 세이브 데이터 정보, 통신 오류, 랜덤·소울코드·소울파츠 등
- 그림 글자 약 145장 — 타이틀 로고(블리치 / 히트 더 소울)·저작권 문구, 메인 메뉴, 도움말 띠, 미션·튜토리얼·스토리 설명, 일시정지 메뉴, 캐릭터 선택(컬러·팀 이름판·설정 완료), 이름 입력 탭, 랭킹·온라인 공지 화면
- 글꼴: 시스템 글꼴(PGF) 한글 병합, 메시지·그림 글자 나눔스퀘어네오, 16px 전투 글꼴·아주 작은 글자 갈무리

## 그대로 둔 것
- 음성, 영어 표기(BLEACH 로고, PRESS START 등), 스태프 롤 그림, 개발용 문자열

## 검증 범위
PPSSPP에서 타이틀, 메인 메뉴, 스토리 대사, 캐릭터 선택·소울 코드 목록, 배틀 HUD·일시정지 메뉴 등을 확인했습니다. 텍스처와 메시지·실행 파일 문자열을 전수 검사했지만 결과 화면 등 일부 화면과 전체 플레이는 검증하지 않았습니다. 문제를 발견하면 Issues에 알려 주세요.

## 문서
- [CHANGELOG.md](CHANGELOG.md) — 변경 기록
- [docs/TECHNICAL.md](docs/TECHNICAL.md) — 파일 형식과 한글화 방법
- [docs/BUILD.md](docs/BUILD.md) — 직접 빌드하는 방법
- [docs/FONT_CREDITS.md](docs/FONT_CREDITS.md) — 글꼴
- [RIGHTS.md](RIGHTS.md) — 권리 및 외부 자료
