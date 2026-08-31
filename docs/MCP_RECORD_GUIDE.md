# MCP 시나리오 녹화 → pytest 자동 생성 워크플로우

> **마지막 업데이트**: 2026-05-05
> **관련 도구**: `tools/mcp/session_recorder.py`, `tools/mcp/codegen.py`
> **검증 시나리오**: `sessions/20260505_1200_login_flow/`

---

## 1. 무엇을 해주는 워크플로우인가?

자연어 프롬프트로 MCP 자동화를 수행하면서 **모든 동작을 세션 단위로 녹화**하고,
끝나면 **pytest 회귀 테스트 코드를 자동 생성**합니다.

```
[사용자 프롬프트]                        [자동 산출물]
"로그인 버튼 탭"          ────►          actions.jsonl  (액션 로그)
"비밀번호 입력해줘"                       screenshots/   (단계별 캡처)
"홈 화면 캡처"                            page_sources/  (XML 덤프)
                                           generated_test.py  (pytest 코드)
                                           generated_test_raw.py
```

---

## 2. 핵심 도구 2개

| 도구 | 역할 |
|------|------|
| `tools/mcp/session_recorder.py` | 시나리오 시작/종료, 액션 로그 기록 |
| `tools/mcp/codegen.py` | 액션 로그 → pytest 코드 변환 |

---

## 3. 라이프사이클

```
┌─────────────────────────────────────────────────────────┐
│ 1. 시나리오 시작                                          │
│    "시나리오 시작: login_flow"                       │
│    → sessions/20260505_120000_login_flow/ 생성            │
│    → meta.json에 디바이스/앱 capabilities 저장              │
├─────────────────────────────────────────────────────────┤
│ 2. 진행 (사용자 프롬프트 → MCP 동작 → 자동 로깅)            │
│    "사용자 ID 입력란에 아이디 입력해줘"                     │
│    "비밀번호 입력란에 비밀번호 입력해줘"                      │
│    "Login 버튼 탭"                                        │
│    → 매 액션마다 actions.jsonl 추가, 스크린샷 저장        │
├─────────────────────────────────────────────────────────┤
│ 3. 시나리오 종료 + 코드 생성                              │
│    "시나리오 종료" 또는 "코드 생성"                       │
│    → generated_test.py + generated_test_raw.py 자동 작성  │
├─────────────────────────────────────────────────────────┤
│ 4. 검증                                                  │
│    pytest sessions/<id>/generated_test.py -v             │
│    → PASS 시 tests/android/ 로 이동 권장                  │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 세션 시작

`session_recorder.py start` 호출 시 현재 `apps/android/`(또는 `apps/ios/`)의 앱과
`config/capabilities.py` 설정으로 세션이 생성됩니다. SauceLabs My Demo App은 단일 빌드라
별도의 환경(stage/live) 분기가 없습니다.

```bash
# CLI 직접 호출
python tools/mcp/session_recorder.py start "login_flow"
```

자연어 트리거: "**시나리오 시작: login_flow**"

---

## 5. 액션 카테고리 (포함/제외 정책)

생성된 회귀 테스트의 노이즈를 줄이기 위해 모든 액션은 **3가지 카테고리**로 분류됩니다.

| 카테고리 | 의미 | 테스트 포함 |
|---------|------|------------|
| `observation` | 화면 확인용 (스크린샷, 페이지 소스 조회) | ❌ |
| `exploration` | 시나리오 의도와 무관한 탐색 액션 | ❌ |
| `scenario` | 본 시나리오의 핵심 동작 (탭/입력/스와이프 등) | ✅ |

**판정 기준** (Claude가 사용자 프롬프트로부터 자동 추론):

- "보여줘", "캡처해줘", "확인해줘" → `observation`
- "다른 화면 가서 봐봐", 의도와 다른 임시 동작 → `exploration`
- "탭", "입력", "스와이프", "선택" → `scenario`

> 분류가 잘못된 경우 사용자가 명시적으로 "이건 시나리오 외 동작이야" 라고 지시하면
> 해당 액션의 `category`/`include_in_test`가 즉시 수정됩니다.

---

## 6. 세션 폴더 구조

```
sessions/20260505_120000_login_flow/
├── meta.json                     # 환경/디바이스/capabilities/시나리오 의도
├── prompts.md                    # 사용자 프롬프트 원문 + 분류 (가독성용)
├── actions.jsonl                 # 액션 로그 (append-only, JSON Lines)
├── screenshots/
│   ├── 001_before_tap.png
│   ├── 001_after_tap.png
│   └── ...
├── page_sources/                 # 핵심 단계 XML 덤프 (필요 시)
├── generated_test.py             # ▶ 압축 모드 (utils 패턴 인식)
└── generated_test_raw.py         # ▶ raw 모드 (1:1 매핑) [--raw 옵션]
```

---

## 7. 액션 로그 포맷 (`actions.jsonl`)

각 줄이 하나의 JSON 액션 entry. **append-only**라 도중 크래시에도 안전합니다.

### 필수 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `seq` | int | 순차 번호 |
| `ts` | string | ISO 시각 (초) |
| `prompt` | string | 사용자 프롬프트 원문 |
| `action` | string | tap / press_key / set_value / swipe / wait / verify 등 |
| `status` | string | success / failure |
| `category` | string | observation / exploration / scenario |
| `include_in_test` | bool | 테스트 코드에 포함할지 여부 |

### 액션별 추가 필드

| 액션 | 추가 필드 |
|------|-----------|
| `tap` | `strategy`, `selector`, `element_uuid`, `screenshot_after` |
| `press_key` | `key` (BACK/HOME/APP_SWITCH), `keycode` |
| `set_value` | `strategy`, `selector`, `params.value` (마스킹 권장) |
| `swipe` / `scroll` | `direction`, `params.duration` 등 |
| `wait` | `params.seconds` |
| `verify` | `verifications`: `[{strategy, selector, expected_text}]` |

### 예시

```jsonl
{"seq":1,"ts":"2026-05-05T12:03:00","prompt":"메뉴 열기 탭","action":"tap","strategy":"accessibility id","selector":"open menu","status":"success","category":"scenario","include_in_test":true}
{"seq":2,"ts":"2026-05-05T12:03:15","prompt":"Login 메뉴 선택","action":"tap","strategy":"accessibility id","selector":"menu item log in","status":"success","category":"scenario","include_in_test":true}
{"seq":3,"ts":"2026-05-05T12:03:30","prompt":"화면 전환 대기","action":"wait","params":{"seconds":2},"status":"success","category":"scenario","include_in_test":true}
{"seq":4,"ts":"2026-05-05T12:03:33","prompt":"결과 검증","action":"verify","verifications":[{"strategy":"accessibility id","selector":"Login button","expected_text":"Login"}],"status":"success","category":"scenario","include_in_test":true}
```

---

## 8. 코드 생성 (압축 모드 vs raw 모드)

### 압축 모드 (기본)

`tools/mcp/codegen.py <session_dir>` 실행 시 기본 출력.
`utils/` 모듈의 검증된 패턴을 자동 인식하여 코드를 단축합니다.

| 인식 패턴 | 출력 |
|-----------|------|
| (계획) 로그인 시퀀스 | `login(driver, username, password)` 1줄로 압축 |
| (계획) 상품 검색 시퀀스 | `search_product(driver, keyword)` |
| (계획) 장바구니 담기 시퀀스 | `add_to_cart(driver, product)` |

### raw 모드 (`--raw`)

`generated_test_raw.py` 추가 생성. 액션을 1:1로 매핑한 명시적 코드.
디버깅·재현 검증·수동 수정 시 유리합니다.

```bash
python tools/mcp/codegen.py sessions/20260505_120000_login_flow/ --raw
```

---

## 9. 실행 가이드

### 9.1 사전 준비

```bash
# 1. Appium 서버 가동 (4723 포트)
appium  # 또는 npx appium

# 2. 에뮬레이터/실기기 준비
adb devices  # emulator-5554 확인
```

### 9.2 시나리오 진행

Claude와의 대화에서:

```
사용자: 시나리오 시작: login_flow
Claude: [session_recorder start 실행]
        새 세션 시작: sessions/20260505_120000_login_flow/

사용자: 메뉴 열고 Login 화면으로 이동해줘
Claude: [MCP tap 호출 → 자동 로깅]

사용자: 아이디/비밀번호 입력하고 로그인 버튼 탭해줘
Claude: [MCP set_value + tap 호출 → 자동 로깅]

사용자: 시나리오 종료
Claude: [session_recorder end --generate --raw]
        생성됨: generated_test.py, generated_test_raw.py
```

### 9.3 회귀 테스트 검증

```bash
source venv/bin/activate
python -m pytest sessions/<id>/generated_test.py -v --tb=short
```

통과 시 `tests/android/<적절한_위치>/`로 이동하여 정식 회귀 테스트로 등록 권장.

---

## 10. 트러블슈팅

### "활성 세션이 없습니다"

`session_recorder.py log` 호출 전에 `start`로 시작해야 합니다.
또는 직전 `end` 후 새 액션을 시도한 경우 발생.

### "이미 활성 세션이 있습니다"

`sessions/.active_session` 파일이 남아있는 경우. `end` 호출이 안 됐을 수 있음.

```bash
# 현재 활성 세션 확인
python tools/mcp/session_recorder.py active

# 강제 종료가 필요하면
rm sessions/.active_session
```

### `apps/` 폴더에 앱 파일 없음

`session_recorder.py start` 시 `apps/android/`(또는 `apps/ios/`)에 앱 파일이 있어야 합니다.

```bash
ls apps/android/  # Android 앱(.apk)
ls apps/ios/      # iOS 앱(.app/.ipa/.zip)
```

### codegen 출력이 비어있음 (`scenario 카테고리 액션이 없습니다`)

모든 액션이 `observation` / `exploration`으로 분류된 경우. 사용자가 명시적으로
"이번 동작은 시나리오에 포함해줘" 라고 지시하거나, `actions.jsonl`을 직접 편집하여
`include_in_test: true`로 변경하세요.

### 생성된 테스트가 `noReset=False` 때문에 매번 APK 재설치

`config/capabilities.py`의 `ANDROID_CAPS`가 `noReset=False`로 되어 있습니다.
같은 빌드를 반복 검증할 땐 임시로 `noReset=True`로 변경하면 30% 이상 빨라집니다.
단, 시나리오의 시작 상태에 의존성이 있다면 주의.

---

## 11. 한계와 개선 후보

| 한계 | 해결 후보 |
|------|----------|
| 패턴 인식기 미구현 | 로그인, 상품 검색, 장바구니 패턴 추가 |
| 비밀번호 입력값 평문 저장 위험 | `set_value` 시 `value_from: <ENV_KEY>` 형태로 환경변수 키만 저장 |
| 모든 액션의 페이지 소스 미저장 | 핵심 단계 + 실패 시점만 저장 (현재 미구현) |
| iOS 미지원 | `ios_driver` 픽스처 + `IOS_CAPS` 매핑 추가 |
| 생성 코드의 자동 검증(테스트 실행) 별도 단계 | `--auto-run` 옵션 추가 |

---

## 12. 보조 트리거 (영역 1: 시나리오 운영)

진행 중·완료 시나리오를 세밀하게 다루기 위한 트리거.

| 트리거 | 효과 | CLI 등가 |
|--------|------|---------|
| "시나리오 분류 변경: seq 4 exploration" | 이미 기록된 액션의 카테고리(observation/exploration/scenario) 변경 → codegen 포함 여부 즉시 반영 | `session_recorder.py update-category --seq 4 --category exploration` |
| "화면 로그 저장" / "시나리오 페이지소스 저장" | 현재 화면 XML을 `page_sources/<seq>_<라벨>.xml`로 저장 | `session_recorder.py dump-source --label <라벨> < page.xml` |
| "시나리오 검증 추가: btn_lgn = Login" | 검증 액션을 actions.jsonl에 추가 (codegen 시 assert 라인 생성) | `session_recorder.py add-verify --selector <셀렉터> --expected <기대값>` |
| "시나리오 일시정지" / "시나리오 재개" | 메타에 `paused` 플래그 토글. Claude는 paused 상태일 때 액션을 로깅하지 않음 | `pause` / `resume` |
| "시나리오 폐기" | 활성 세션 폴더를 `<id>_aborted`로 이름 변경 + 활성 마커 제거 | `abort` |
| "시나리오 목록" | 모든 세션 + 진행 상태/액션 수/생성된 테스트 유무 요약 | `list` |
| "테스트 실행: 최신" | 가장 최근 세션의 `generated_test.py`를 pytest로 즉시 실행 | `python -m pytest <세션>/generated_test.py -v` |
| "테스트 정식 등록: <세션> regression" | `tests/android/regression/<세션>_test.py`로 이동 | `promote --subdir regression` |

---

## 13. 일반 워크플로우 트리거 (영역 2)

MCP 시나리오와 상관없이 자주 쓰이는 외부 도구 호출.

| 트리거 | 효과 |
|--------|------|
| "UI 덤프" / "덤프해줘" | `python tools/ui_dump.py -w` (Watch 모드) |
| "리포트 열어줘" | `python tools/run_allure.py --open` |
| "디바이스 확인" | `adb devices` + (macOS) `xcrun simctl list devices booted` |
| "MCP 재연결" | `bash tools/mcp/reconnect.sh` |

---

## 14. AI/생성 고급 트리거 (영역 3)

| 트리거 | 효과 |
|--------|------|
| "패턴 등록: <설명>" | `codegen.py`의 `PATTERNS` 리스트에 새 패턴 추가 가이드 제공. 형식: `_detect_<name>(actions, prefix)` + `_emit_<name>(ctx)` 함수 정의 후 PATTERNS에 등록 |
| "이번 시나리오로 회귀 검증" | 직전 세션의 `generated_test.py` pytest 실행 → 통과 시 `run_allure.py --open` 자동 |
| "비밀번호 마스킹: <평문>=<ENV_KEY>" | `mask-secrets --map <평문>=<ENV_KEY>` → set_value 액션의 `value` 필드를 `value_from`으로 변환. codegen 시 `elem.send_keys(os.getenv("ENV_KEY", ""))`로 출력 |

### 패턴 등록 절차 상세 (#15)

`tools/mcp/codegen.py` 수정 단계:

```python
# 1. 검출 함수: 액션 시퀀스에서 패턴이 시작-종료되는 인덱스와 컨텍스트 반환
def _detect_login_flow(actions, prefix):
    # 예: ID 입력 + 비밀번호 입력 + 로그인 버튼 탭 시퀀스 감지
    ...
    return (start_idx, end_idx, {"username_env": "TEST_USER", "password_env": "TEST_PW"}) or None

# 2. 출력 함수: 헬퍼 호출 코드 라인 반환
def _emit_login_flow(ctx):
    return [
        f"    with allure.step('로그인'):",
        f"        from utils.auth import login",
        f"        login(driver, os.getenv({_q(ctx['username_env'])}), os.getenv({_q(ctx['password_env'])}))",
    ]

# 3. PATTERNS에 등록
PATTERNS.append({
    "name": "login_flow",
    "detect": _detect_login_flow,
    "emit": _emit_login_flow,
})
```

> 패턴은 `PATTERNS` 순서대로 검출되며, 한 인덱스가 한 패턴에 매칭되면 다른 패턴은 스킵됩니다.

---

## 15. 관련 문서

- `CLAUDE.md` — 시나리오 트리거 전체 정의
- `docs/MCP_SETUP_GUIDE.md` — MCP 환경 세팅
- `docs/MCP_개념_가이드.md` — MCP 개념과 아키텍처
- `docs/CODING_GUIDELINES.md` — Locator 우선순위, Allure 어노테이션 규칙
- `utils/helpers.py` — 공통 유틸리티 (codegen 패턴이 활용)
