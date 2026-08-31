# Appium MCP 설정 가이드 (Windows + macOS)

> **마지막 업데이트**: 2026-04-29 **대상**: 클로드(Cowork / Claude Code 등)가 에뮬레이터/실기기
> 화면을 직접 보고 조작하면서 코드 작성을 돕도록 하는 환경 구성 **MCP 서버**: 공식
> [appium/appium-mcp](https://github.com/appium/appium-mcp) (Apache-2.0, Node.js v22+)

---

## 0. 이 가이드의 목적

기존 `ui_dump.py`는 사용자가 수동으로 실행해서 결과 파일을 클로드에게 전달해야 했습니다. MCP를
도입하면 클로드가 직접 다음 작업을 수행할 수 있습니다.

- 현재 화면 스크린샷 + page_source 가져오기
- 특정 요소 탭/스와이프/입력
- 앱 실행/종료/딥링크
- 자연어로 요소 찾기 (AI Vision 모드 — 선택)

이를 통해 **코드 작성 → 실행 → 결과 확인 → 수정** 사이클이 사용자 개입 없이 빠르게 반복됩니다.

---

## 1. 사전 조건

| 항목 | Windows | macOS | 확인 명령 |
|------|---------|-------|-----------|
| Node.js | v22 이상 | v22 이상 | `node -v` |
| Java JDK | 8 이상 | 8 이상 | `java -version` |
| Android SDK | 설치됨 | 설치됨 | `adb version` |
| Xcode CLT (iOS용) | 미지원 | 설치됨 | `xcode-select -p` |
| Claude Code CLI | 설치됨 | 설치됨 | `claude --version` |
| Appium 서버 | localhost:4723 | localhost:4723 | `curl http://127.0.0.1:4723/status` |
| 에뮬레이터 / 실기기 | 1대 이상 부팅됨 | 1대 이상 부팅됨 | `adb devices` |
| iOS 시뮬레이터 (선택) | 미지원 | 부팅됨 | `xcrun simctl list devices booted` |

> 위 항목들은 이미 `shell/run-app.sh` 사전점검 단계에서 검증하던 것과 동일합니다.

### 1.0. macOS 첫 진입 체크리스트 (Apple Silicon 기준)

이미 `shell/run-app.sh` 가 동작 중이라면 대부분 충족되어 있습니다. 신규 셋업 시:

```bash
# 1. Homebrew (없다면)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. nvm + Node.js v22
brew install nvm
nvm install 22 && nvm use 22 && nvm alias default 22

# 3. Xcode CLT (iOS 자동화용)
xcode-select --install
sudo xcodebuild -license accept

# 4. Claude Code CLI (없다면)
# 공식 가이드 참조: https://docs.claude.com/claude-code

# 5. 환경변수 .zshrc 적용 (이미 적용된 경우 건너뜀)
source ~/.zshrc
```

> **중요**: `.zshrc` 를 수정한 직후에는 **반드시 `source ~/.zshrc` 또는 새 터미널을 열어야**
> ANDROID_HOME 등이 적용됩니다.
>
> 기존 가이드: `docs/SETUP_GUIDE.md` (환경 세팅 통합 — §3 macOS Appium 전체 셋업, §4 iOS 시뮬레이터 +
> XCUITest 드라이버).

### 1.1. Node.js 버전이 22 미만인 경우

```bash
# macOS (nvm 사용)
nvm install 22 && nvm use 22

# Windows (nvm-windows)
nvm install 22.11.0
nvm use 22.11.0
```

### 1.2. ANDROID_HOME 환경변수

| OS | 기본 경로 |
|----|-----------|
| Windows | `%LOCALAPPDATA%\Android\Sdk` |
| macOS | `~/Library/Android/sdk` |

설정되어 있지 않다면:

```powershell
# Windows (PowerShell)
[Environment]::SetEnvironmentVariable("ANDROID_HOME", "$env:LOCALAPPDATA\Android\Sdk", "User")
```

```bash
# macOS (~/.zshrc 에 추가)
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
```

---

## 2. capabilities.json 생성 (양쪽 OS 공통)

### 2.1. 사전 점검

```bash
python tools/mcp/generate_capabilities.py --verify
```

출력 예시:
```
[1] OS              : Windows (AMD64)
[2] App             : SauceLabs My Demo App (com.saucelabs.mydemoapp.android)
[3] Node.js         : v22.11.0 OK
[4] npx             : OK
[5] ANDROID_HOME    : C:\Users\<user>\AppData\Local\Android\Sdk
[6] APK             : C:\Users\<user>\appium_saucelabs\apps\android\mda-2.2.0-25.apk
[7] Appium 서버     : Running (127.0.0.1:4723)
[OK] 모든 사전 조건 충족 — generate 모드로 다시 실행하세요.
```

### 2.2. capabilities.json 생성

```bash
python tools/mcp/generate_capabilities.py
```

생성 위치: `tools/mcp/capabilities.json`

> 이 파일은 GIT 추적에서 제외하는 것이 좋습니다 — `.gitignore`에 `tools/mcp/capabilities.json`
> 추가를 권장합니다.

---

## 3. MCP 클라이언트 등록

사용 중인 클라이언트에 따라 둘 중 하나를 선택하세요.

### 3-A. Claude Code (CLI)

가장 간단합니다. 한 줄로 등록 가능.

**선조치 (양쪽 OS 권장)** — `npx -y` 첫 실행 시 EPERM/timeout 회피용:
```bash
npm install -g appium-mcp
where.exe appium-mcp        # Windows: 경로 확인
which appium-mcp            # macOS: 경로 확인
```

> macOS에서 `EACCES: permission denied` 가 나오면 nvm 환경에서 실행 중이 아닐 가능성. `nvm use 22`
> 후 재시도.

**macOS / Linux**:
```bash
chmod +x tools/mcp/samples/claude-code-add.sh    # 최초 1회
bash tools/mcp/samples/claude-code-add.sh
```

**Windows (PowerShell)**:
```powershell
.\tools\mcp\samples\claude-code-add.ps1
```

확인:
```bash
claude mcp list
# appium-mcp: appium-mcp - ✓ Connected  ← 이렇게 보이면 성공
```

### 3-B. Cowork / Claude Desktop / Cursor (JSON 설정)

설정 파일 위치:

| 클라이언트 | Windows | macOS |
|------------|---------|-------|
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Cowork | 앱 설정 → Connectors / MCP | 앱 설정 → Connectors / MCP |
| Cursor | Settings → MCP → Add new MCP Server | 동일 |

설정에 추가할 블록 (`samples/claude-desktop.example.json` 참고):

```json
{
  "mcpServers": {
    "appium-mcp": {
      "command": "npx",
      "args": ["-y", "appium-mcp@latest"],
      "env": {
        "ANDROID_HOME": "<본인 OS의 Android SDK 경로>",
        "CAPABILITIES_CONFIG": "<프로젝트 절대경로>/tools/mcp/capabilities.json",
        "SCREENSHOTS_DIR": "<프로젝트 절대경로>/ui_dumps/mcp"
      }
    }
  }
}
```

**Windows 경로 작성법**: `C:/Users/.../...` (슬래시) 또는 `C:\\Users\\...\\...` (이스케이프된
백슬래시)

설정 후 클라이언트를 재시작하면 도구 목록에 `appium_*` 항목들이 노출됩니다.

---

## 4. 검증 (5분)

클라이언트에서 클로드에게 다음 명령을 차례로 시도해보세요.

### 4.1. 디바이스 검색 (필수 첫 단계)

> "Select my android device"

- 클로드가 `select_device` 도구 호출 → 연결된 디바이스 목록 출력
- 1대만 있으면 자동 선택됨

### 4.2. 세션 생성

> "Create an appium session for android"

- `create_session` 도구가 `capabilities.json` 의 `android` 블록을 읽어 세션 생성
- 앱이 실행되면 성공

### 4.3. 스크린샷

> "Take a screenshot of the current screen"

- `appium_screenshot` 도구 호출 → PNG 파일 저장
- 클로드가 이미지를 직접 확인하고 "현재 화면은 로그인 화면입니다" 같은 분석 가능

### 4.4. Page Source

> "Show me the page source"

- `appium_get_page_source` → XML 트리 반환
- 기존 `ui_dump.py` 결과와 동일한 정보를 클로드가 즉시 받음

### 4.5. 간단한 액션

> "Tap on the Login button"

- `appium_click` 또는 `appium_find_element` + `appium_click`
- 동작이 디바이스에 반영되면 성공

### 4.6. 세션 정리

> "Delete the current session"

- `delete_session` 호출 → 디바이스 해제
- 이후 pytest 등 다른 도구로 다시 세션 생성 가능

---

## 4-iOS. iOS 시뮬레이터 검증 (macOS 전용)

iOS 자동화는 macOS 에서만 가능합니다. Android 검증과 동일한 흐름이지만 몇 가지 다른 점이 있습니다.

### 사전 준비

```bash
# 부팅된 시뮬레이터 확인
xcrun simctl list devices booted

# 없다면 부팅 (예: iPhone 17, iOS 26.4)
xcrun simctl boot "iPhone 17"
open -a Simulator
```

> 시뮬레이터 디바이스 이름과 OS 버전이 `tools/mcp/capabilities.json` 의 `ios.appium:deviceName` /
> `appium:platformVersion` 과 일치해야 합니다. 다르면 `IOS_DEVICE_NAME`, `IOS_PLATFORM_VERSION`
> 환경변수로 .env 에 설정 후 `python tools/mcp/generate_capabilities.py` 재실행.

### 4-iOS.1. 디바이스 선택

> "Select my iOS device"

`select_device` 가 부팅된 시뮬레이터를 자동 선택합니다.

### 4-iOS.2. WebDriverAgent 준비 (첫 실행만)

> "Prepare the iOS simulator"

- `prepare_ios_simulator` 도구가 시뮬레이터 부팅 + WDA 다운로드 + 설치 + 실행을 한 번에 처리
- **첫 실행 시 1~3분 소요** (WDA 빌드/설치) — 이후 실행은 캐시 사용
- 진행 메시지가 멈춘 듯 보여도 종료하지 말 것

### 4-iOS.3. 세션 생성

> "Create an iOS session"

`capabilities.json` 의 `ios` 블록 사용. `appium:app` 또는 `appium:bundleId` 둘 중 하나가 필요합니다
(`.env` 의 `IOS_BUNDLE_ID` 설정 권장).

### 4-iOS.4. 검증 명령

이후 4.3 ~ 4.6 과 동일하게 진행 가능. iOS 에서는 locator 가 다름:
- Android: `id` (resource-id) → iOS: `accessibility id` (name 속성)
- 자연어 요청은 양쪽 동일하게 동작 ("Find the login button and tap it")

### 4-iOS.5. iOS 특화 도구 (참고)

| 도구 | 용도 |
|------|------|
| `appium_mobile_shake` | 흔들기 제스처 (시뮬레이터 전용) |
| `appium_geolocation` | GPS 좌표 변경 |
| `appium_orientation` | 화면 회전 |

---

## 5. 트러블슈팅

| 증상 | 원인 / 해결 |
|------|-------------|
| `npx: command not found` | Node.js v22 이상 재설치, PATH 확인 |
| `Cannot connect to Appium server` | `npx appium` 으로 서버 시작, `127.0.0.1:4723/status` 응답 확인 |
| `No devices found` | `adb devices` / 에뮬레이터 부팅 / USB 디버깅 활성화 |
| `App is not installed` 에러 | `capabilities.json` 의 `appium:app` 경로 확인 — APK 실제 존재 여부 |
| 도구 목록에 `appium_*` 없음 | 클라이언트 재시작 / MCP 서버 로그 확인 (Claude Code: `claude mcp logs`) |
| `npx -y` 첫 실행 timeout / EPERM | `npm install -g appium-mcp` 로 글로벌 설치, 명령을 `appium-mcp` 로 변경 |
| 스크린샷 / page_source 토큰 한도 초과 | 환경변수 `NO_UI=true` 추가 (필수) — base64 인라인 반환 비활성화 |
| UiAutomator2 인스트루멘테이션 크래시 | `capabilities.json` 의 안정화 옵션 (`disableWindowAnimation`, `waitForIdleTimeout`) 적용, `generate_capabilities.py` 재실행 |
| 두 세션 충돌 (pytest + MCP) | 동시에 실행 금지 — 한 쪽 세션 종료 후 다른 쪽 시작 |
| Windows 경로 오류 | JSON에서 백슬래시는 `\\` 또는 슬래시(`/`) 로 작성 |
| (macOS) `EACCES: permission denied` 글로벌 install 실패 | 시스템 Node.js 사용 중 — `nvm use 22` 로 nvm 환경 진입 후 재시도. 절대 `sudo npm install -g` 쓰지 말 것 |
| (macOS) `xcrun: error: invalid active developer path` | `xcode-select --install` 후 `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` |
| (macOS) `claude: command not found` | Claude Code 미설치 또는 nvm 셸 분리 — 새 터미널 열거나 `source ~/.zshrc` |
| (macOS) WebDriverAgent 빌드 timeout | `prepare_ios_simulator` 첫 실행 시 1~3분 정상 — 종료 말고 대기. 반복되면 `~/.appium/node_modules/.../WebDriverAgent` 삭제 후 재시도 |
| (macOS) `.zshrc` 변경이 적용 안 됨 | 터미널 재시작 또는 `source ~/.zshrc`. Claude Code 세션도 새로 시작해야 새 환경변수 인식 |
| (macOS) `claude mcp add` 시 `permission denied` 셸 스크립트 | `chmod +x tools/mcp/samples/claude-code-add.sh` |

### 5.1. NO_UI 모드 (필수 권장)

공식 appium-mcp 의 `appium_screenshot`, `appium_get_page_source` 등은 기본적으로 base64 인라인
응답을 사용합니다. 1080×2400 해상도 스크린샷 한 장이 LLM 컨텍스트 토큰 수만 단위를 차지하여 한도를
초과합니다.

`NO_UI=true` 환경변수를 설정하면:

- 스크린샷은 `SCREENSHOTS_DIR` 에 PNG 파일로만 저장 (base64 인라인 X)
- page_source 는 텍스트로만 반환 (HTML 인스펙터 X)
- 토큰 사용량 60~90% 감소
- 응답 속도 50~80% 향상

이 가이드의 등록 스크립트(`samples/claude-code-add.{ps1,sh}`)는 NO_UI=true 가 기본 적용되어
있습니다.

### 5.2. UiAutomator2 안정화 옵션

`generate_capabilities.py` 가 자동으로 다음 안정화 옵션을 포함합니다.

| 옵션 | 효과 |
|------|------|
| `disableIdLocatorAutocompletion` | resource-id 접두사 자동 추가 비활성화 — 명시적 locator 우선 |
| `waitForIdleTimeout: 100` | UI idle 대기를 10초→100ms 단축 (기본값에서 발생하던 timeout 완화) |
| `disableWindowAnimation` | 시스템 애니메이션 OFF — 화면 전환 안정성 ↑ |
| `nativeWebScreenshot: true` | 스크린샷을 native 방식으로 — 일부 화면 검정 출력 방지 |
| `uiautomator2ServerInstallTimeout: 60000` | UIA2 server 설치 대기 60초 |

이러한 옵션 적용 후에도 인스트루멘테이션 크래시가 반복되면 `delete_session` → `create_session` 으로
세션 재생성하면 복구됩니다. 좌표 기반 동작은 ADB `input tap` 우회로 진행 가능 (Claude 가 자동 판단).

---

## 6. 머신 전환 체크리스트 (Windows ↔ macOS)

같은 프로젝트를 다른 머신에서 이어서 작업할 때:

1. `git pull` (변경 사항 동기화)
2. **머신 환경에 맞춰 capabilities.json 재생성**:
   ```bash
   python tools/mcp/generate_capabilities.py --verify   # 사전 점검
   python tools/mcp/generate_capabilities.py            # 생성
   ```
3. **머신 환경에 맞춰 MCP 재등록** (이전 머신 등록은 그대로 둬도 무방):
   ```bash
   # macOS
   chmod +x tools/mcp/samples/claude-code-add.sh
   bash tools/mcp/samples/claude-code-add.sh
   ```
   ```powershell
   # Windows
   .\tools\mcp\samples\claude-code-add.ps1
   ```
4. `claude mcp list` 로 `✓ Connected` 확인
5. 4장 검증 절차 (Android는 4.1~4.6 / iOS는 4-iOS.1~4-iOS.4) 시도

---

## 7. 향후 확장 (Phase 2 — 선택)

공식 MCP에 없는 프로젝트 전용 기능을 직접 MCP 도구로 추가할 수 있습니다.

- 로그인 헬퍼 (`utils/helpers.py` 에 추가)
- 마스킹 처리된 UI 덤프 (`tools/ui_dump.py`)
- 장바구니/결제 플로우 헬퍼

이는 Python MCP SDK (`pip install mcp`) 로 별도 서버를 만들어 공식 서버와 같이 등록하면 됩니다.
자세한 설계는 Phase 2에서 진행 예정입니다.

---

## 8. 참고 링크

- [appium/appium-mcp (공식)](https://github.com/appium/appium-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- 본 프로젝트 관련 가이드:
  - `docs/UI_DUMP_GUIDE.md` — 기존 UI Dump 도구
  - `docs/CODING_GUIDELINES.md` — 테스트 작성 규칙
  - `docs/PYTEST_GUIDE.md` — pytest 직접 실행
