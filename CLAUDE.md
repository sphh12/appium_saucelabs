# Appium Mobile Test — 프로젝트 가이드

> 공통 규칙 (응답 스타일, 코드 스타일, 에러 해결 등)은 글로벌 `~/.claude/CLAUDE.md`에 정의됨.
> 이 파일은 **프로젝트 전용** 설정만 포함.

---

## 프로젝트 사전 지식

### 프로젝트 개요

**대상 앱**: SauceLabs My Demo App (네이티브 Android, 이커머스 데모)
**목적**: Appium 포트폴리오 프로젝트 — 풀 E2E 자동화 구축 (로그인 → 결제까지)
**기술 스택**: Python + pytest + Appium + Allure
**대상 OS 우선순위**: Android → iOS

### 프로젝트 구조

```
appium-SMDA/
├── config/
│   └── capabilities.py          # ANDROID_CAPS, IOS_CAPS, get_appium_server_url()
├── utils/
│   └── helpers.py               # 유틸리티 (scroll_to_element, save_screenshot 등)
├── pages/
│   ├── base_page.py             # Android POM 베이스 (명시적 대기 헬퍼 + 공통 헤더)
│   ├── login_page.py / products_page.py / product_detail_page.py
│   ├── cart_page.py / checkout_page.py / menu_page.py / about_page.py / webview_page.py
│   └── ios/                     # iOS POM (base_ios_page.py + 화면별 페이지, 하단 탭바 기반)
├── tools/
│   ├── ui_dump.py               # Android UI 덤프 도구 (단일/인터랙티브/Watch 모드)
│   ├── ui_dump_ios.py           # iOS UI 덤프 도구 (동일 옵션 지원)
│   ├── run_allure.py            # Allure 리포트 생성/관리
│   ├── export_summary.py        # Allure 경량 HTML 요약 Export
│   ├── update_dashboard.py      # 로컬 실행 이력 대시보드 생성/갱신
│   ├── serve.py                 # 로컬 HTTP 서버 (대시보드·리포트 열람용)
│   └── mcp/                     # Appium MCP 도구 세트 (session_recorder, codegen 등)
├── tests/
│   ├── android/                 # Android 테스트 (구현됨: login/catalog/cart/checkout/menu/about/webview/smoke 등)
│   └── ios/                     # iOS 테스트 (구현됨: login/catalog/cart/checkout/menu/about/webview/product_detail)
├── conftest.py                  # pytest fixture (driver, android_driver, ios_driver)
├── apps/                        # 앱 설치 파일 보관 (Android/iOS 통합)
│   ├── android/                 # Android APK
│   └── ios/                     # iOS .app / .ipa / .zip
├── ui_dumps/                    # UI 덤프 XML 저장소 (도구 실행 시 자동 생성)
├── allure-results/              # Allure 테스트 결과 (타임스탬프 폴더, 자동 생성)
├── allure-reports/              # Allure HTML 리포트 (LATEST/, dashboard/, 자동 생성)
├── shell/                       # 실행 스크립트 (run-app.sh, run-aos.sh, run-ios.sh 등)
├── .env                         # 환경변수 (Git 미추적)
└── .env.example                 # 환경변수 템플릿
```

### 대상 앱 정보

| 항목 | 값 |
|------|---|
| 앱 이름 | SauceLabs My Demo App (네이티브 Android) |
| GitHub | https://github.com/saucelabs/my-demo-app-android (iOS: my-demo-app-ios) |
| Android 패키지 | `com.saucelabs.mydemoapp.android` |
| Android Activity | `com.saucelabs.mydemoapp.android.view.activities.SplashActivity` |
| iOS Bundle ID | `com.saucelabs.mydemo.app.ios` |
| APK 위치 | `apps/android/*.apk` |
| iOS 앱 위치 | `apps/ios/*.app|.ipa|.zip` |
| 테스트 계정 | 앱 로그인 화면에 예시 표시 (`bob@example.com` / `10203040` 등) |

### 이미 구현된 주요 도구

#### 1. UI Dump 도구 (`tools/ui_dump.py`, `tools/ui_dump_ios.py`)
- **사용법**: `python tools/ui_dump.py [옵션]`
- **모드**:
  - 단일 캡처: `python tools/ui_dump.py [이름]`
  - 인터랙티브: `python tools/ui_dump.py -i` (Enter로 캡처, q로 종료)
  - **Watch 모드 (권장)**: `python tools/ui_dump.py -w` (화면 변화 자동 감지, 0.2초 간격)
  - 기존 파일 마스킹: `python tools/ui_dump.py --mask-existing`
- **저장 위치**: `ui_dumps/` (플랫폼별 `aos_`/`ios_` 프리픽스)
- **민감정보 자동 마스킹**: 전화번호, 이메일, 생년월일 자동 마스킹 적용
- **가이드 문서**: `docs/UI_DUMP_GUIDE.md`

#### 2. pytest Fixture (`conftest.py`)
- `driver` - 플랫폼 자동 감지 드라이버 (`--platform android|ios`)
- `android_driver` - Android 전용 드라이버
- `ios_driver` - iOS 전용 드라이버
- `--record-video` - 테스트 화면 녹화 (실패 시 Allure 첨부)
- `--allure-attach=hybrid|all` - Allure 첨부 정책 (hybrid: 실패만, all: 전체)
- 실패 시 자동 첨부: 스크린샷, page_source.xml, capabilities.json, logcat.txt(Android)

#### 3. Allure 리포트 (`tools/run_allure.py`)
- 테스트 결과 자동 수집 → HTML 리포트 생성 → 로컬 대시보드 갱신
- 필수 패키지 자동 감지/설치 (`_ensure_dependencies`)
- `allure-results/YYYYMMDD_HHMMSS/` - 타임스탬프별 결과 보관
- `allure-reports/LATEST/` - 최신 리포트 고정 경로
- `allure-reports/dashboard/` - 로컬 실행 이력 대시보드
- `--open`: 리포트 생성 후 브라우저에서 열기
- 결과는 **로컬 전용** — 외부 업로드 없음 (공개 저장소 정책)
- **가이드 문서**: `docs/ALLURE_REPORT_GUIDE.md`

#### 4. 리포트 열람 (`tools/serve.py`)
- 프로젝트 루트를 서빙하는 로컬 HTTP 서버 (127.0.0.1 바인딩)
- 대시보드·개별 리포트 모두 이 서버로 열람 (리포트는 XHR로 데이터를 읽어 `file://`로는 안 열림)
- **사용법**: `python tools/serve.py` (대시보드) / `--latest` (최신 리포트) / `--port 9000`

#### 5. MCP 시나리오 도구 (`tools/mcp/`)
- Appium MCP를 통한 시나리오 녹화 + 자동 코드 생성
- `session_recorder.py`: 시나리오 시작/종료/로그 기록
- `codegen.py`: 액션 로그 → pytest 코드 변환
- **가이드 문서**: `docs/MCP_RECORD_GUIDE.md`, `docs/MCP_SETUP_GUIDE.md`

### 기존 가이드 문서 목록 (`docs/`)

| 문서 | 내용 |
|------|------|
| `UI_DUMP_GUIDE.md` | UI Dump 도구 전체 사용법, XML 분석법, Locator 전략 |
| `CODING_GUIDELINES.md` | 테스트 스크립트 작성 규칙 (파일명, Locator 우선순위, Allure 어노테이션) |
| `ALLURE_REPORT_GUIDE.md` | Allure 리포트 탭별 설명, 30초 분석 루틴, 진단 파일 활용법 |
| `SETUP_GUIDE.md` | **환경 세팅 통합 가이드** — 클론·Windows(bootstrap)·macOS·iOS 세팅 + 트러블슈팅 (구 README_CLONE/MAC_SETUP/IOS_SETUP 통합) |
| `IOS_TEST_GUIDE.md` | iOS UI Dump 기반 테스트 작성 가이드 |
| `PYTEST_GUIDE.md` | pytest 사용법 가이드 |
| `CI_CD_STRATEGY.md` | CI/CD 파이프라인 전략 (플랫폼 선택·무료 한도 비교) |
| `CI_GUIDE.md` | **GitHub Actions 사용법** — 트리거 4종·야간 회귀·아티팩트 확인·트러블슈팅 |
| `MCP_RECORD_GUIDE.md` | MCP 시나리오 녹화 가이드 |
| `MCP_SETUP_GUIDE.md` | Appium MCP 셋업 가이드 |
| `MCP_개념_가이드.md` | MCP 개념 설명 (한국어) |
| `MCP_단계별_실행계획.md` | MCP 단계별 실행 계획 (한국어) |

### 환경변수 (.env)

모든 변수는 선택사항입니다. `.env.example` 참고.

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `APPIUM_HOST` / `APPIUM_PORT` | Appium 서버 주소 | `127.0.0.1` / `4723` |
| `ANDROID_UDID` | 실물 디바이스 시리얼 | 미설정 (에뮬레이터 자동 사용) |
| `ANDROID_DEVICE_NAME` | 디바이스 이름 (Allure 표시용) | `Android Emulator` |
| `ANDROID_PLATFORM_VERSION` | Android OS 버전 | 자동 감지 |
| `IOS_DEVICE_NAME` | iOS 시뮬레이터 이름 | `iPhone 15` |
| `IOS_PLATFORM_VERSION` | iOS 버전 | `17.0` |
| `IOS_UDID` | iOS 시뮬레이터 UUID (다중 시뮬 부팅 시 특정 시뮬 지정) | 미설정 (deviceName+version 매칭) |
| `EXECUTOR_NAME` | Allure 리포트 실행자 표시명 (OS 사용자명 미기록) | `local` |

### 코드 작성 전 반드시 확인

1. **기존 도구가 있는지 확인** - 새로 만들기 전에 `tools/`, `utils/` 폴더의 기존 코드를 먼저 확인
2. **최신 UI Dump 참조** - `ui_dumps/` 폴더에서 최신 XML 파일 분석 후 코드 작성
3. **Locator 우선순위** - ACCESSIBILITY_ID > Resource ID > XPath
4. **가이드 문서 참조** - `docs/` 폴더의 해당 가이드를 먼저 읽고 기존 패턴을 따름

---

## 워크플로우

### 트리거 요약

| 구분 | 키워드 | 동작 |
|------|--------|------|
| Session Start | "하이" / "안녕" / "컴백" / "high" | `CHANGELOG.md`(최근 이력 + `Todo`) 참고하여 진행상황 브리핑 + 원격/로컬 코드 비교하여 최신 여부 알림 |
| Session End | "바이" / "갈게" / "퇴근" | `CHANGELOG.md` 업데이트(날짜 섹션 + `Todo` 정리) → **Git Push 규칙** 따라 커밋/푸시 |
| Git Push | "푸시" / "깃 푸시" / "깃에 올려줘" | `GIT_RULES.md` 참고 → 민감정보 스캔 → `CHANGELOG.md` 업데이트(미기록 변경 + `Todo` 정리) → 커밋/푸시 |
| Briefing | "브리핑" / "다음 할일" / "현재 상황" / "뭐하고 있었지" | 현재 프로젝트 상황 브리핑 |
| Git Status | "git 확인" / "상태 확인" / "깃 확인해줘" | `git fetch --all` → 로컬 vs 원격 비교표 출력 |
| 자동화 코드 | "자동화 코드를 만들어줘" | UI Dump 분석 → 테스트 코드 구현 → 실행/디버깅 → 리포트 |
| MCP 시나리오 시작 | "시나리오 시작: <이름>" / "테스트코드 작성하자" / "appium 코드 작성하자" / "애피움 코드 작성하자" | `tools/mcp/session_recorder.py start <이름>` → 활성 세션 폴더 생성. 별칭 트리거 사용 시 이름을 사용자에게 1회 질문 |
| MCP 시나리오 종료 | "시나리오 종료" / "코드 생성" | `tools/mcp/session_recorder.py end --generate --raw` → 액션 로그를 pytest 코드로 변환 |
| MCP 시나리오 상태 | "시나리오 상태" / "활성 세션" | `tools/mcp/session_recorder.py active` → 진행 중 세션 정보 출력 |
| MCP 분류 변경 | "시나리오 분류 변경: seq <N> <카테고리>" | `session_recorder.py update-category --seq <N> --category <obs\|exp\|scenario>` |
| MCP 화면 로그 저장 | "시나리오 페이지소스 저장" / "화면 로그 저장" | `session_recorder.py dump-source --label <설명>` (MCP get_page_source XML을 stdin으로 전달) |
| MCP 검증 추가 | "시나리오 검증 추가: <셀렉터> = <기대값>" | `session_recorder.py add-verify --selector <셀렉터> --expected <기대값>` |
| MCP 일시정지/재개 | "시나리오 일시정지" / "시나리오 재개" | `session_recorder.py pause` / `resume` (자동 로깅 토글) |
| MCP 폐기 | "시나리오 폐기" | `session_recorder.py abort` (`_aborted` 접미사로 보존 후 종료) |
| MCP 목록 | "시나리오 목록" | `session_recorder.py list` (모든 세션 + 상태/액션 수 요약) |
| MCP 테스트 실행 | "테스트 실행: <세션명\|최신>" | `pytest sessions/<id>/generated_test.py -v` |
| MCP 정식 등록 | "테스트 정식 등록: <세션명> [<subdir>]" | `session_recorder.py promote --subdir <subdir>` (tests/android/로 이동) |
| UI 덤프 | "UI 덤프" / "덤프해줘" | `python tools/ui_dump.py -w` 실행 (Watch 모드) |
| 리포트 열기 | "리포트 열어줘" / "결과 보여줘" | `python tools/run_allure.py --open` 실행 |
| 디바이스 확인 | "디바이스 확인" | `adb devices` + iOS 시뮬레이터 부팅 상태 확인 |
| MCP 재연결 | "MCP 재연결" | `bash tools/mcp/reconnect.sh` 실행 |
| 패턴 등록 | "패턴 등록: <설명>" | `tools/mcp/codegen.py`의 `PATTERNS` 리스트에 새 detect/emit 함수 추가 안내 |
| 회귀 검증 | "이번 시나리오로 회귀 검증" | 종료된 세션의 generated_test.py 실행 + Allure 리포트 자동 생성 (`run_allure.py`) |
| 비밀번호 마스킹 | "비밀번호 마스킹: <평문>=<ENV_KEY>" | `session_recorder.py mask-secrets --map <평문>=<ENV_KEY>` (set_value 액션의 평문 → 환경변수 키) |

### 자동 실행 규칙

| 조건 | 동작 |
|------|------|
| 큰 단위 작업 완료 | `CHANGELOG.md` 자동 업데이트 (날짜 섹션 + `Todo`) |
| 중간 진행 상태 | `CHANGELOG.md` `Todo`에 진행 중 표기 + 날짜 섹션에 단계 기록 |
| **MCP 시나리오 활성 상태** | 모든 MCP 액션을 `session_recorder.py log`로 자동 기록 (스크린샷, 셀렉터, 카테고리 포함) |

> **큰 단위 작업**: 새로운 기능 구현, 프로젝트 생성/배포, 시스템 구조 변경, 도구 추가 등 여러 파일에 걸친 의미 있는 작업 단위
> **중간 진행 기록 형식**: `- **[작업명]**: N/M단계 완료, 다음: [다음 단계 설명]`

---

### MCP 시나리오 워크플로우

**참고 문서**: `docs/MCP_RECORD_GUIDE.md`
**스킬**: `.claude/skills/mcp-scenario/SKILL.md` (슬래시 명령 `/mcp-scenario`로도 호출 가능)

**트리거 동작:**

#### 시나리오 시작
- **트리거**:
  - 명시형: "시나리오 시작: <이름>"
  - 별칭: "테스트코드 작성하자" / "appium 코드 작성하자" / "애피움 코드 작성하자"
- **동작**:
  1. **별칭 트리거 사용 시** — 사용자에게 시나리오 이름을 1회 질문 후 진행
  2. `tools/mcp/session_recorder.py start <이름> [--intent "..."]` 실행
  3. 활성 세션 폴더(`sessions/<timestamp>_<이름>/`) 생성, `meta.json`에 디바이스/capabilities 저장
  4. **앱 파일 자동 감지**:
     - Android → `apps/android/*.apk` 자동 탐색
     - iOS → `apps/ios/*.app|.ipa|.zip` 자동 탐색
  5. **기존 MCP 세션이 있다면 먼저 정리** 후 새 capabilities로 재생성

#### 시나리오 진행 중 (자동)
- 사용자 프롬프트로 발생하는 모든 MCP 액션마다 `session_recorder.py log` 자동 호출
- **카테고리 자동 분류** (사용자 의도 추론):
  - `observation`: 사용자가 "보여줘"/"확인해줘"/스크린샷 요청 → 테스트 미포함
  - `exploration`: 시나리오 본 동작과 무관한 임시 탐색 (예: "다른 화면 보여줘") → 테스트 미포함
  - `scenario`: 본 동작 ("탭", "입력", "스와이프" 등 시나리오 의도와 일치) → 테스트 포함
- 액션 직후 스크린샷은 `screenshots/<seq>_<설명>.png`로 저장
- 사용자가 분류 의도와 다른 경우 명시적으로 "이건 시나리오 외 동작이야" 등으로 지시 가능

#### 시나리오 종료 / 코드 생성
- **트리거**: "시나리오 종료" / "코드 생성"
- **동작**:
  1. `tools/mcp/session_recorder.py end --generate --raw`
  2. `tools/mcp/codegen.py` 실행하여 `generated_test.py` (압축) + `generated_test_raw.py` (1:1) 작성
  3. 생성된 코드를 `pytest sessions/<id>/generated_test.py -v`로 자동 실행 제안
  4. 통과 시 `tests/android/`로 이동 권장 안내

#### 시나리오 보조 트리거 (영역 1)

| 트리거 | 동작 / CLI |
|--------|-----------|
| "시나리오 분류 변경: seq <N> <카테고리>" | `session_recorder.py update-category --seq <N> --category <observation\|exploration\|scenario>` |
| "시나리오 페이지소스 저장" / "화면 로그 저장" | MCP `appium_get_page_source` 호출 → 결과를 `session_recorder.py dump-source --label <설명>`로 stdin 전달 |
| "시나리오 검증 추가: <셀렉터> = <기대값>" | `session_recorder.py add-verify --selector <셀렉터> --expected <기대값>` (전략 미지정 시 id) |
| "시나리오 일시정지" | `session_recorder.py pause` → meta.json `paused=true`, 자동 로깅 중단 |
| "시나리오 재개" | `session_recorder.py resume` → meta.json `paused=false`, 자동 로깅 재개 |
| "시나리오 폐기" | `session_recorder.py abort` → 폴더명 끝에 `_aborted` 추가 후 활성 세션 마커 제거 |
| "시나리오 목록" | `session_recorder.py list` → JSON 형태로 세션별 상태(active/paused/aborted/scenario_count/has_generated_test) 출력 |
| "테스트 실행: <세션명\|최신>" | 세션 폴더 결정 후 `python -m pytest <세션>/generated_test.py -v --tb=short` 실행 |
| "테스트 정식 등록: <세션명> [<subdir>]" | `session_recorder.py promote --session-dir <세션> --subdir <subdir> [--filename <이름>]` |

#### 일반 워크플로우 트리거 (영역 2)

| 트리거 | 동작 |
|--------|------|
| "UI 덤프" / "덤프해줘" | `python tools/ui_dump.py -w` (Watch 모드 — 화면 변화 자동 감지) |
| "리포트 열어줘" / "결과 보여줘" | `python tools/run_allure.py --open` (Allure 리포트 생성 + 브라우저로 열기) |
| "디바이스 확인" | `adb devices` (Android) + `xcrun simctl list devices booted` (iOS, macOS만) |
| "MCP 재연결" | `bash tools/mcp/reconnect.sh` (점검 → 필요 시 재등록) |

#### AI/생성 고급 트리거 (영역 3)

| 트리거 | 동작 |
|--------|------|
| "패턴 등록: <설명>" | `tools/mcp/codegen.py`의 `PATTERNS` 리스트에 새 패턴을 추가하는 가이드 제시. 사용자에게 detect/emit 함수 시그니처와 기존 예시를 보여주고 시나리오 의도에 맞춰 신규 함수 작성 |
| "이번 시나리오로 회귀 검증" | 직전 종료된 세션 또는 명시한 세션의 `generated_test.py`를 pytest로 실행하고, 통과 시 `python tools/run_allure.py --open`으로 Allure 리포트까지 자동 생성 |
| "비밀번호 마스킹: <평문>=<ENV_KEY>" | `session_recorder.py mask-secrets --map <평문>=<ENV_KEY>` 실행. set_value 액션의 평문을 환경변수 키로 치환하여 codegen 시 `os.getenv(KEY)` 호출 코드 생성 |

---

### Session Start (세션 시작)

**트리거**: "하이" / "안녕" / "컴백" / "high"

**질문 없이 중단 없이** 아래를 모두 실행하고 결과만 보고:

1. `git fetch --all` → 원격과 비교하여 로컬 최신 여부 확인
   - 최신이면: "로컬 코드 최신 상태입니다" 한 줄 표시
   - 최신 아니면: 자동 pull + 변경 내용 요약
2. `CHANGELOG.md` 최근 날짜 섹션 확인 → 최근 완료 작업 요약 (1~3줄)
3. `CHANGELOG.md` `Todo` 확인 → 진행 중/남은 할일 목록 + 다음 추천 작업 제안

### Session End (세션 종료)

**트리거**: "바이" / "갈게" / "퇴근"

**질문 없이 중단 없이** 아래를 모두 실행하고 결과만 보고:

1. 당일 작업 내용을 `CHANGELOG.md` 날짜 섹션에 정리 (날짜별, 최신이 위, `### Added/Changed/Fixed` 분류)
2. 미완료/다음 작업을 `CHANGELOG.md` `Todo`에 정리 (완료 항목은 날짜 섹션으로 이동)
3. 변경사항이 있으면 → **Git Push 규칙** 따라 커밋/푸시

### Git Push

**트리거**: "푸시" / "깃 푸시" / "깃에 올려줘" / "깃에 업로드 해줘"

**참고 문서**: 반드시 `GIT_RULES.md` 파일을 **읽고** 규칙 준수

**동작:**
1. **`GIT_RULES.md` 읽기**: 매 세션 첫 push 시 반드시 파일을 읽어 최신 규칙 확인
2. **md 파일 업데이트**: `CHANGELOG.md` (날짜 섹션에 미기록 변경사항 + `Todo` 완료 이동·할일 추가) + 기타 관련 md
3. **민감정보 스캔** (`GIT_RULES.md` 섹션 2~6): `git diff`에서 API 키/토큰/비밀번호/이메일/전화번호 노출 확인 → 발견 시 커밋 중단
4. **커밋 메시지** (`GIT_RULES.md` 섹션 8): `<type>: <파일/기능> - <변경내용>` + 본문 한글 설명
5. **push 대상** (`GIT_RULES.md` 섹션 1): GitHub origin 단일 푸시
   ```bash
   git push origin <branch>
   ```
6. **후처리**: `.env` 변경 시 `.env.example` 동기화

### Briefing (브리핑)

**트리거**: "브리핑" / "다음 할일" / "현재 상황" / "뭐하고 있었지"

**동작:**
1. `CHANGELOG.md` 최근 날짜 섹션 → 최근 완료 작업 확인
2. `CHANGELOG.md` `Todo` → 진행 중/다음 단계 확인
3. 간결 요약: 최근 완료 (1~3줄) + 남은 할일 (우선순위순) + 다음 추천 작업

### Git Status (상태 확인)

**트리거**: "git 확인해줘" / "상태 확인" / "깃 확인해줘"

**동작:**
1. `git fetch --all` → `git status` → `git diff --stat` → `git diff --cached --stat`
2. `git log HEAD..origin/<branch> --oneline` (pull 필요한 커밋)
3. `git log origin/<branch>..HEAD --oneline` (push 필요한 커밋)
4. 결과를 **로컬 vs 원격** 비교표로 정리

### 자동화 코드 작성

**트리거**: "자동화 코드를 만들어줘" (OS 미언급 시 현재 작업 흐름으로 판단, 불확실하면 질문)

**동작:**
1. OS별 설정 확인 (capabilities, 드라이버, 시뮬레이터/에뮬레이터)
2. UI Dump로 대상 화면 요소 분석 → 테스트 코드 구현
3. 코드 실행 + 디버깅
4. Allure Report 결과 확인 (성공: 결과 보여줌 / 실패: 사유 정리)
5. 실패 사유 → 관련 가이드 문서 업데이트
6. **반복 실패로 진행 불가 시**: 사용자에게 알리고 중지
