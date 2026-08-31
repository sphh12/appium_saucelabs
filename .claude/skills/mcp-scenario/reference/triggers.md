# 트리거 전체 레퍼런스 (18개)

## 라이프사이클 (3개)

| # | 자연어 트리거 | CLI |
|---|--------------|-----|
| L1 | "시나리오 시작: <이름>" / "테스트코드 작성하자" / "appium 코드 작성하자" / "애피움 코드 작성하자" | `session_recorder.py start <이름>` (별칭은 이름 1회 질문) |
| L2 | "시나리오 종료" / "코드 생성" | `session_recorder.py end --generate --raw` |
| L3 | "시나리오 상태" / "활성 세션" | `session_recorder.py active` |

## 영역 1: 시나리오 보조 (8개)

| # | 자연어 트리거 | CLI |
|---|--------------|-----|
| 1 | "시나리오 분류 변경: seq <N> <카테고리>" | `update-category --seq <N> --category <obs\|exp\|scenario>` |
| 2 | "화면 로그 저장" / "시나리오 페이지소스 저장" | `dump-source --label <라벨>` (XML stdin) |
| 3 | "시나리오 검증 추가: <셀렉터> = <기대값>" | `add-verify --selector <셀렉터> --expected <기대값>` |
| 4 | "시나리오 일시정지" / "시나리오 재개" | `pause` / `resume` |
| 5 | "시나리오 폐기" | `abort` |
| 6 | "시나리오 목록" | `list` |
| 7 | "테스트 실행: <세션\|최신>" | `pytest sessions/<id>/generated_test.py -v` |
| 8 | "테스트 정식 등록: <세션> [<subdir>]" | `promote --session-dir <세션> --subdir <subdir>` |

## 영역 2: 일반 워크플로우 (4개)

| # | 자연어 트리거 | 동작 |
|---|--------------|------|
| 10 | "UI 덤프" / "덤프해줘" | `python tools/ui_dump.py -w` |
| 12 | "리포트 열어줘" / "결과 보여줘" | `python tools/run_allure.py --open` |
| 13 | "디바이스 확인" | `adb devices` + (macOS) `xcrun simctl list devices booted` |
| 14 | "MCP 재연결" | `bash tools/mcp/reconnect.sh` |

## 영역 3: AI/생성 (3개)

| # | 자연어 트리거 | 동작 |
|---|--------------|------|
| 15 | "패턴 등록: <설명>" | `codegen.py`의 PATTERNS에 detect/emit 함수 추가 (reference/pattern_registration.md 참조) |
| 16 | "이번 시나리오로 회귀 검증" | pytest + run_allure.py 자동 연계 |
| 17 | "비밀번호 마스킹: <평문>=<ENV_KEY>" | `mask-secrets --map <평문>=<ENV_KEY>` |

## 자동 동작 규칙 (트리거 외)

| 조건 | 동작 |
|------|------|
| 시나리오 활성 + paused=false | 모든 MCP 액션을 자동으로 `session_recorder.py log`로 기록 |
| 시나리오 활성 + paused=true | 액션 로깅 중단 (디버깅용) |
| 사용자 프롬프트의 의도 추론 | category 자동 분류 (observation/exploration/scenario) |
