---
name: mcp-scenario
description: Appium MCP로 모바일 UI 동작을 자연어 프롬프트로 녹화하고, 액션 로그를 pytest 회귀 테스트 코드로 자동 생성하는 워크플로우. 시나리오 시작/종료/검증/패턴 등록을 한 번에 다룸.
when_to_use: 사용자가 모바일 UI 자동화 시나리오를 작성·검증하려 할 때. 또는 "시나리오 시작/종료/목록", "테스트 실행: <세션>", "테스트 정식 등록" 등 MCP 시나리오 트리거를 사용할 때.
disable-model-invocation: true
allowed-tools: Bash(python *), Bash(pytest *), Bash(adb *), Bash(rm *), Bash(mv *), Bash(cat *), Bash(ls *), Bash(mkdir *)
argument-hint: "<start|end|status|list|run|promote|...> [args]"
---

# MCP 시나리오 → pytest 자동 생성 워크플로우

Appium MCP로 모바일 UI 동작을 녹화하고, 종료 시점에 pytest 회귀 테스트 코드를 자동 생성하는 도구 모음.

## 핵심 도구

- `tools/mcp/session_recorder.py` — 시나리오 녹화기 (서브커맨드 13개)
- `tools/mcp/codegen.py` — 액션 로그 → pytest 코드 변환기 (PATTERNS 레지스트리)

## 라이프사이클

```
1. 시나리오 시작        → 세션 폴더 생성, capabilities 기록
2. 액션 자동 로깅       → 사용자 프롬프트 → MCP 동작 → actions.jsonl 추가
3. (선택) 보조 작업     → 분류 변경, 검증 추가, 페이지소스 저장, 일시정지/재개
4. 시나리오 종료        → generated_test.py + generated_test_raw.py 자동 생성
5. 회귀 검증            → pytest 실행 + Allure 리포트
6. 정식 등록            → tests/android/<subdir>/ 로 이동
```

## 대상 앱

SauceLabs My Demo App (단일 환경, 패키지 `com.saucelabs.mydemoapp.android`). 앱 파일은 `apps/android/`(`.apk`) / `apps/ios/`에 위치하며 `config/capabilities.py`가 자동 인식합니다. 별도의 환경 분기는 없습니다.

## 액션 카테고리 정책

| 카테고리 | 의미 | 테스트 포함 |
|---------|------|------------|
| `observation` | 화면 확인 (screenshot, get_page_source) | ❌ |
| `exploration` | 시나리오 외 임시 탐색 | ❌ |
| `scenario` | 본 동작 (탭/입력/스와이프/검증) | ✅ |

## 트리거 (자연어) ↔ CLI 매핑

| 자연어 트리거 | CLI |
|--------------|-----|
| "시나리오 시작: <이름>" / "테스트코드 작성하자" / "appium 코드 작성하자" / "애피움 코드 작성하자" | `python tools/mcp/session_recorder.py start <이름>` (별칭은 이름 1회 질문) |
| "시나리오 종료" / "코드 생성" | `python tools/mcp/session_recorder.py end --generate --raw` |
| "시나리오 상태" / "활성 세션" | `python tools/mcp/session_recorder.py active` |
| "시나리오 목록" | `python tools/mcp/session_recorder.py list` |
| "시나리오 폐기" | `python tools/mcp/session_recorder.py abort` |
| "시나리오 일시정지" / "재개" | `python tools/mcp/session_recorder.py pause` / `resume` |
| "시나리오 분류 변경: seq <N> <카테고리>" | `update-category --seq <N> --category <obs\|exp\|scenario>` |
| "시나리오 검증 추가: <셀렉터> = <기대값>" | `add-verify --selector <셀렉터> --expected <기대값>` |
| "화면 로그 저장" / "시나리오 페이지소스 저장" | `dump-source --label <라벨>` (XML stdin) |
| "비밀번호 마스킹: <평문>=<ENV_KEY>" | `mask-secrets --map <평문>=<ENV_KEY>` |
| "테스트 실행: <세션\|최신>" | `pytest sessions/<id>/generated_test.py -v` |
| "테스트 정식 등록: <세션> [<subdir>]" | `promote --session-dir <세션> --subdir <subdir>` |
| "이번 시나리오로 회귀 검증" | pytest + `python tools/run_allure.py --open` |
| "패턴 등록: <설명>" | `codegen.py`의 PATTERNS에 detect/emit 추가 (레퍼런스 참조) |

## Claude 측 자동 동작

이 스킬이 활성화된 상태에서 사용자 프롬프트를 처리할 때:

1. **시나리오 활성 상태이면** — 모든 MCP 액션을 자동으로 `session_recorder.py log`로 기록
2. **카테고리 자동 분류**:
   - "보여줘", "캡처해줘", "확인해줘", "스크린샷" → `observation`
   - "다른 화면 가서", "잠깐 다른 거 봐봐" → `exploration`
   - "탭", "입력", "스와이프", "선택", "검증" → `scenario`
3. **시나리오 종료 시** — codegen 실행 후 `pytest sessions/<id>/generated_test.py` 자동 실행 제안
4. **민감정보 입력** — 평문 입력 후 즉시 `mask-secrets`로 환경변수 키 치환 권장

## 사전 준비

```bash
# 1. Appium 서버 실행 (4723 포트)
appium  # 또는 npx appium

# 2. 디바이스 준비
adb devices  # Android 에뮬레이터 또는 실기기

# 3. 앱 파일 폴더 확인
ls apps/android/   # 또는 apps/ios/
```

## 슬래시 명령으로 직접 호출 (선택)

```bash
/mcp-scenario start login_flow
/mcp-scenario list
/mcp-scenario run latest
```

> 인자는 `session_recorder.py`의 서브커맨드와 동일 (start/end/active/list/abort/pause/resume/update-category/add-verify/dump-source/mask-secrets/promote)

## 부속 파일

- [examples/add_to_cart.md](examples/add_to_cart.md) — 장바구니 담기 시나리오 워크스루 (예시)
- [examples/login_flow_template.md](examples/login_flow_template.md) — 로그인 시나리오 템플릿 (PATTERNS 활용 예시)
- [reference/triggers.md](reference/triggers.md) — 17개 트리거 전체 레퍼런스
- [reference/action_format.md](reference/action_format.md) — actions.jsonl 포맷 명세
- [reference/pattern_registration.md](reference/pattern_registration.md) — 패턴 등록 절차 (#15)

## 관련 문서

- `docs/MCP_RECORD_GUIDE.md` — 풀 가이드 (15 섹션)
- `docs/MCP_SETUP_GUIDE.md` — Appium MCP 환경 세팅
- `CLAUDE.md` — 프로젝트 트리거 정의
