# 환경 세팅 가이드 (Setup Guide)

> **클론부터 첫 테스트 실행까지, OS별 환경 구성을 한 문서로 안내합니다.** 2026-08-24 통합 — 구
> `README_CLONE.md`(Windows 클론·부트스트랩) + `MAC_SETUP_GUIDE.md`(macOS Android) +
> `IOS_SETUP_GUIDE.md`(iOS) 작성 이력: 2026-02-14 macOS(Apple Silicon) 초안 → 2026-03-04 실세팅 보완
> → 2026-08-24 Windows 시운전 반영·3문서 통합

## 사용 시나리오별 읽는 순서

| 하려는 것 | 읽는 순서 |
|-----------|----------|
| **Windows에서 Android 테스트** | §1 클론 → §2 Windows → §5 검증·첫 실행 |
| **macOS에서 Android 테스트** | §1 클론 → §3 macOS → §5 검증·첫 실행 |
| **macOS에서 iOS 테스트** | §1 클론 → §3 macOS → §4 iOS 추가 → §5 검증·첫 실행 |

---

## 0. 전체 구조 + 요구사항

```
Python 테스트 코드 (pytest)
    ↓ HTTP 요청
Appium Server (localhost:4723)
    ↓
UiAutomator2 드라이버(Android) / XCUITest 드라이버(iOS)
    ↓
Android 에뮬레이터·실기기 / iOS 시뮬레이터·실기기
```

- **Appium**: 테스트 명령을 전달하는 서버
- **드라이버**: Appium 명령을 각 OS가 이해하는 언어로 변환하는 통역사
- **Android Studio / Xcode**: 앱이 실행되는 가상 디바이스 환경 제공

| 요구사항 | 버전 | 비고 |
|----------|------|------|
| Python | 3.10+ | venv 사용 |
| Node.js | 20+ | Appium 3.x가 20+ 요구 (18은 `ERR_REQUIRE_ESM` 발생) |
| Java JDK | 17 | Android SDK 도구용 |
| Android Studio | 최신 | 에뮬레이터 생성 (Android 테스트 시) |
| Xcode | 최신 | **macOS 전용**, iOS 테스트 시 (~15GB) |

---

## 1. 공통: 클론

GitHub CLI(권장) 또는 HTTPS로 클론합니다.

```bash
# GitHub CLI (권장)
gh auth login          # GitHub.com → HTTPS → Login with a web browser
gh auth setup-git      # ⚠️ 필수 — 이거 없이는 일반 git pull/push가 인증 안 됨
gh repo clone sphh12/appium_saucelabs
cd appium_saucelabs

# HTTPS 직접 클론
git clone https://github.com/sphh12/appium_saucelabs.git
```

> **중요**: `gh auth login`만으로는 일반 `git pull/push`가 인증되지 않습니다.
> 반드시 `gh auth setup-git`으로 git credential helper를 연동하세요.

클론 후 Git 사용자 정보 설정 (이 프로젝트는 단일 `origin`(GitHub)만 사용 — 규칙은
`../GIT_RULES.md`):

```bash
git config user.name "이름"
git config user.email "이메일@example.com"
```

---

## 2. Windows 세팅

### 2.1 원샷 부트스트랩 (권장)

새 PC에서는 아래 1회 실행으로 **venv 생성/의존성 설치/UiAutomator2 드라이버/`.env` 생성/APK 자동
다운로드/ADB·Allure 확인**까지 진행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File shell/bootstrap.ps1
```

| 단계 | 내용 |
|------|------|
| [1/6] | 도구 확인 (python, npm) |
| [2/6] | venv 생성 + `pip install -r requirements.txt` |
| [3/6] | `npm install` (로컬 Appium + Allure) |
| [4/6] | UiAutomator2 드라이버 설치 |
| [5/6] | `.env` 생성(템플릿 복사) + SauceLabs My Demo App APK 자동 다운로드 (`apps/android/`) |
| [6/6] | ADB/에뮬레이터 확인 |

옵션:
```powershell
# Android OS 버전 고정
powershell -ExecutionPolicy Bypass -File shell/bootstrap.ps1 -AndroidPlatformVersion 12
# 에뮬레이터 확인 생략 / Allure 확인 생략
powershell -ExecutionPolicy Bypass -File shell/bootstrap.ps1 -SkipEmulator -SkipAllure
```

> APK 다운로드가 오프라인/프록시로 실패해도 나머지 셋업은 계속 진행됩니다.
> 수동 다운로드: https://github.com/saucelabs/my-demo-app-android/releases → `apps/android/`

### 2.2 수동 점검 체크리스트

부트스트랩이 실패했거나, 회사 PC 권한/프록시 등으로 자동 설치가 막히는 경우 순서대로 점검합니다.

**① Python 가상환경 + 패키지**
```powershell
./venv/Scripts/activate
pip install -r requirements.txt
```

**② Node.js / Appium**
```powershell
appium --version                      # 또는 npx appium --version
appium driver list --installed        # uiautomator2가 보여야 함
appium driver install uiautomator2   # 없으면 설치
```

**③ Android SDK / ADB / 에뮬레이터**
```powershell
adb devices -l    # device 상태가 최소 1개
# offline이면: adb kill-server → adb start-server
```

**④ Appium 서버(로컬) 실행 확인**
```powershell
try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:4723/status -TimeoutSec 3).StatusCode } catch { "NOT_RUNNING" }
```

**⑤ Allure CLI**
```powershell
allure --version
# 설치: scoop install allure  /  choco install allure
# 전역 설치가 막힌 경우: npm install 후 npx allure --version
```

### 2.3 (선택) Android OS 버전 고정

에뮬레이터/디바이스 OS 버전과 테스트 설정을 맞춰야 하는 경우에만 사용합니다.

```powershell
setx ANDROID_PLATFORM_VERSION "12"          # 영구
$env:ANDROID_PLATFORM_VERSION="12"          # 현재 세션
```

---

## 3. macOS 세팅 (Android)

> 2026-03-04 실제 세팅 경험 기반. macOS에는 부트스트랩 스크립트가 없어 아래 순서로 수동 진행합니다.

### 3.1 세팅 순서 요약

| 순서 | 항목 | 명령어 |
|------|------|--------|
| 1 | GitHub CLI 설치 & 인증 & 클론 | §1 참고 |
| 2 | Homebrew 설치 | 수동 설치 (sudo 필요) |
| 3 | Node.js 20 설치 | `brew install node@20` |
| 4 | Python 3.10 설치 | `brew install python@3.10` |
| 5 | Java JDK 17 설치 | `brew install openjdk@17` |
| 6 | Allure 설치 | `brew install allure` |
| 7 | 환경변수 설정 | `~/.zshrc` 편집 (§3.4) |
| 8 | npm + venv + pip 설치 | §3.5 |
| 9 | Android Studio 설치 | 수동 설치 (GUI) |
| 10 | 에뮬레이터 생성 + 성능 튜닝 | §3.7 (**튜닝 필수**) |
| 11 | .env + 앱 파일 배치 | §5 참고 |
| 12 | 셸 스크립트 권한 | `chmod +x shell/*.sh` |

### 3.2 Homebrew 설치

비대화형 환경(Claude Code 등)에서는 sudo 권한 문제로 자동 설치 불가. **터미널에서 직접 실행**해야
합니다.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### 3.3 핵심 도구 설치 (순차 설치 권장 — 병렬 시 brew lock 충돌)

```bash
brew install node@20       # Appium 3.x는 Node 20+ 필수 (18은 ERR_REQUIRE_ESM)
brew install python@3.10   # macOS 기본 3.9.6은 요구사항(3.10+) 미충족
brew install openjdk@17
brew install allure
```

### 3.4 환경변수 설정 (~/.zshrc)

```bash
# Homebrew
eval "$(/opt/homebrew/bin/brew shellenv)"

# Node.js 20
export PATH="/opt/homebrew/opt/node@20/bin:$PATH"

# Python 3.10
export PATH="/opt/homebrew/opt/python@3.10/libexec/bin:$PATH"

# Java JDK 17
export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"

# Android SDK
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
```

설정 후 반드시 적용: `source ~/.zshrc`

### 3.5 프로젝트 의존성 설치

```bash
cd ~/appium_saucelabs
npm install
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> **참고**: `package.json`에 Appium 드라이버(uiautomator2, xcuitest)가 의존성으로 포함되어 있어
> `npm install`만 실행하면 드라이버도 함께 설치됩니다. 인식이 안 되면
> `appium driver list --installed`로 확인 후 `appium driver install uiautomator2`를 별도 실행하세요.

### 3.6 Android Studio 설치 + 에뮬레이터 생성

- 다운로드: https://developer.android.com/studio → **Standard** 설치, License 모두 **Accept**
- Android Studio → **Virtual Device Manager** → **Create Virtual Device**
  - 디바이스: Pixel 8 (또는 원하는 기종) / System Image: API 34

### 3.7 에뮬레이터 성능 튜닝 (필수)

> **이 단계를 건너뛰면 테스트가 불안정해질 수 있습니다.**
> 실측: 기본 설정으로 3번째 테스트에서 **UiAutomator2 프록시 타임아웃(240초 초과)** 발생 →
> 아래 튜닝 후 동일 테스트 3건 모두 통과 (총 3분 56초).

```bash
# 에뮬레이터 이름에 맞게 경로 변경 (예: Pixel_8)
vi ~/.android/avd/Pixel_8.avd/config.ini
```

| 항목 | 기본값 | 권장값 | 설명 |
|------|--------|--------|------|
| `hw.ramSize` | 4096 | **8192** | 기본 4GB는 앱 설치+UiAutomator2 서버+테스트 동시 진행 시 부족 |
| `vm.heapSize` | 228 | **512** | 힙이 작으면 렌더링 시 GC 빈발로 응답 지연 |
| `hw.gpu.mode` | auto | **host** | Mac GPU 직접 사용으로 렌더링 성능 향상 |

> **변경 후 에뮬레이터를 반드시 재시작**해야 적용됩니다 (Cold Boot 권장).

### 3.8 셸 스크립트 실행 권한

macOS에서는 clone 시 실행 권한이 보존되지 않아 부여가 필요합니다:
```bash
chmod +x ./shell/*.sh
```

---

## 4. iOS 추가 세팅 (macOS 전용)

> 전제조건: §3의 macOS Android 세팅 완료 (Homebrew/Node/Appium/Python 재설치 불필요)

### 4.1 세팅 순서 요약

| 순서 | 항목 | 소요 시간 | 비고 |
|------|------|----------|------|
| 1 | Xcode 설치 | 30분~1시간 | App Store (~15GB) |
| 2 | iOS 시뮬레이터(플랫폼) 다운로드 | 10~20분 | (~8GB) |
| 3 | 라이선스 동의 + 경로 설정 | 1분 | 터미널 |
| 4 | XCUITest 드라이버 설치 | 1분 | |
| 5 | Appium 서버 재시작 | 1분 | 드라이버 인식 필수 |
| 6 | 환경 검증 | 1분 | `appium-doctor --ios` |

### 4.2 Xcode 설치 + iOS 플랫폼 다운로드

App Store에서 "Xcode" 설치. 컴포넌트 선택 화면에서 **iOS** 체크 필수 (watchOS/tvOS/visionOS는
불필요).

설치 시 iOS를 선택하지 못했다면 나중에 추가:
```bash
# 방법 1) Xcode → Settings(⌘,) → Platforms → "+" → iOS
# 방법 2) 터미널
xcodebuild -downloadPlatform iOS
```

### 4.3 라이선스 동의 + 경로 설정

```bash
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -license accept
xcodebuild -version   # 확인
```

### 4.4 XCUITest 드라이버 설치 + Appium 서버 재시작

```bash
appium driver install xcuitest
appium driver list --installed   # xcuitest@10.x.x 확인
```

> 드라이버 설치 전에 Appium 서버가 실행 중이었다면 **반드시 재시작**해야 새 드라이버를 인식합니다.

```bash
lsof -ti:4723 | xargs kill -9
appium --relaxed-security
# 로그에 "XCUITestDriver has been successfully loaded" 확인
```

### 4.5 환경 검증 (appium-doctor)

```bash
npm install -g @appium/doctor
appium-doctor --ios
```

**필수 항목** (모두 ✔): Xcode / Xcode CLT / Node.js / DevToolsSecurity

**선택 항목** (✖ 이어도 기본 테스트 지장 없음):

| 항목 | 용도 | 필요 시점 |
|------|------|----------|
| ffmpeg | 화면 녹화 | 테스트 영상 녹화 |
| ios-deploy | 실물 iPhone 앱 설치 | 실기기 테스트 |
| idb / applesimutils | 고급 디바이스 제어·권한 자동화 | 위치/알림 권한 테스트 |

### 4.6 시뮬레이터 관리 명령어

```bash
xcrun simctl list devices available   # 목록
xcrun simctl boot "iPhone 17"         # 부팅
open -a Simulator                     # UI 열기
xcrun simctl shutdown "iPhone 17"     # 종료 (all 로 전체 종료)
```

### 4.7 Safari 테스트 시 추가 설정

```bash
# 시뮬레이터 부팅 상태에서 Web Inspector 활성화
xcrun simctl spawn "iPhone 17" defaults write com.apple.mobilesafari WebKitDeveloperExtras -bool true
xcrun simctl spawn "iPhone 17" defaults write com.apple.mobilesafari WebInspectorEnabled -bool true
```

```python
# Safari 테스트용 capabilities 권장 옵션
caps = {
    "browserName": "Safari",
    "webviewConnectTimeout": 30000,                # 기본 5초 → 30초
    "safariInitialUrl": "https://www.google.com",
}
```

---

## 5. 공통 마무리: .env + 앱 파일 배치

### 5.1 .env

```bash
cp .env.example .env    # Windows는 bootstrap.ps1이 자동 생성
```

> SauceLabs My Demo App은 별도 테스트 계정/APK 환경변수가 필요 없습니다.
> `.env`의 **모든 항목은 선택사항**이며, 미설정 시 기본값이 사용됩니다.

선택 항목:
- `EXECUTOR_NAME` — Allure 리포트에 표시할 실행자 이름 (미설정 시 `local`. OS 사용자명은 기록하지
  않음)

> 테스트 결과는 **로컬에만 저장**됩니다(공개 저장소 정책 — 외부 대시보드 업로드 기능 없음).

### 5.2 앱 파일

| 플랫폼 | 위치 | 입수 |
|--------|------|------|
| Android | `apps/android/*.apk` | **Windows: bootstrap.ps1 자동 다운로드** (검증된 2.2.0 고정) / 수동: [releases](https://github.com/saucelabs/my-demo-app-android/releases) |
| iOS | `apps/ios/*.app·.ipa·.zip` | [my-demo-app-ios releases](https://github.com/saucelabs/my-demo-app-ios/releases) (시뮬레이터는 zip) |

파일명은 자동 인식됩니다(`config/capabilities.py`가 폴더 스캔, 여러 개면 이름순 마지막 사용).
⚠️ `mda-androidTest-*.apk`(계측 테스트용)는 함께 두지 마세요 — 이름순 마지막으로 잘못 선택됩니다.

---

## 6. 설치 검증 + 첫 실행

> **자동 사전점검(preflight)**: 테스트 실행 시 `conftest.py`가 첫 드라이버 생성 전에
> Appium `/status` 응답과 adb 디바이스 연결을 자동 점검합니다. 환경이 안 갖춰져 있으면
> 테스트를 돌리지 않고 몇 초 안에 원인·해결책과 함께 중단되므로, 아래 2)~3)을 빠뜨려도
> 긴 연쇄 실패 없이 바로 알 수 있습니다.

```bash
# 1) 수집 검증 (드라이버/디바이스 없이 통과해야 함)
python -m pytest --collect-only -q

# 2) 디바이스 준비 — Android 에뮬 부팅 후:
adb devices           # device 1개 이상

# 3) Appium 서버 (별도 터미널)
npx appium

# 4) 스모크 테스트
python -m pytest tests/android/smoke_test.py -v --platform=android

# 5) 전체 실행 + Allure 리포트 (권장 러너)
python tools/run_allure.py -- tests/android -v --platform=android
# macOS 셸 스크립트: ./shell/run-aos.sh
```

---

## 7. 트러블슈팅

### 7.1 공통 / Windows

| 증상 | 원인 / 해결 |
|------|------------|
| `Could not find a driver for automationName 'UiAutomator2'` | `appium driver install uiautomator2` |
| `allure: command not found` | `scoop install allure` 또는 `choco install allure`, 로컬은 `npx allure` |
| `adb devices`에 `offline` | `adb kill-server` → `adb start-server` |
| `Could not find a connected Android device` (에뮬은 떠 있음) | adb 서버와 Appium이 서로 다른 상태를 봄 — Appium 프로세스 종료 + `adb kill-server/start-server` 후 Appium 재기동. conftest의 preflight/fail-fast가 이 상황을 감지해 연쇄 실패 전에 즉시 중단시킴 |
| `No .apk file found in apps/android/` | 앱 파일 미배치 — §5.2 참고 |
| `[preflight] ... HTTP 프록시가 127.0.0.1 요청까지 가로채는 설정` | 회사망 프록시 환경변수(`HTTP_PROXY`)가 localhost 요청까지 프록시로 보냄 — selenium도 이 설정을 따르므로 세션 생성이 전부 실패한다. `NO_PROXY`(소문자 `no_proxy`)에 `127.0.0.1,localhost` 추가 후 재실행 |
| `[preflight] adb 오류 (exit N)` + 버전 불일치 메시지 | adb 클라이언트/서버 버전 충돌(여러 SDK 설치) — `adb kill-server` 후 사용할 platform-tools 하나로 PATH 정리 |

### 7.2 macOS

| 증상 | 원인 / 해결 |
|------|------------|
| Homebrew `Need sudo access` | 비대화형 환경에서 sudo 불가 → 터미널에서 직접 설치 |
| brew `process has already locked ...` | 병렬 설치 lock 충돌 → 순차 설치 |
| `ERR_REQUIRE_ESM` | Appium 3.x는 Node 20+ → `brew install node@20` + `.zshrc` PATH 변경 |
| `Permission denied` (셸 스크립트) | `chmod +x ./shell/*.sh` |
| `command not found: ^M` / 경로 끝 `\r` | `.zshrc`가 CRLF로 저장됨 → `sed -i '' 's/\r$//' ~/.zshrc` |
| `ADB not found` / `SDK root does not exist` | 환경변수 미로드 → `source ~/.zshrc` 또는 터미널 재시작 |
| UiAutomator2 "Not Installed" 오탐 | 체크 스크립트 감지 로직 한계 — 실제로는 설치됨. `run-aos.sh`로 실행 |
| `UiAutomator2 proxy timeout exceeded (240s)` | 에뮬 기본 성능 부족 → §3.7 튜닝 (RAM 8192/Heap 512/GPU host) + Cold Boot |
| `gh auth login` 후 git pull/push 인증 실패 | `gh auth setup-git` 미실행 → 실행하여 credential helper 연동 |

### 7.3 iOS

| 증상 | 원인 / 해결 |
|------|------------|
| `Could not find a driver for automationName 'XCUITest'` | 드라이버 설치 전 서버가 떠 있었음 → 서버 재시작 (§4.4) |
| Safari `remote debugger did not return ... after 5068ms` | Web Inspector 비활성 + 타임아웃 5초 → §4.7 활성화 + `webviewConnectTimeout: 30000` |
| `appium: command not found` / `node: command not found` | Homebrew PATH 미적용 → `eval "$(/opt/homebrew/bin/brew shellenv)"` 또는 터미널 재시작 |

---

## 8. 참고 차이표

### macOS vs Windows

| 항목 | Windows | macOS |
|------|---------|-------|
| 터미널 | Git Bash 권장 | 기본 Terminal (zsh) |
| 패키지 매니저 | choco / scoop | Homebrew |
| 환경변수 설정 | 시스템 환경변수 | `~/.zshrc` |
| Python venv 활성화 | `.\venv\Scripts\activate` | `source venv/bin/activate` |
| 셸 스크립트 권한 | 불필요 | `chmod +x` 필요 |
| SDK 기본 경로 | `%LOCALAPPDATA%\Android\Sdk` | `~/Library/Android/sdk` |
| JAVA_HOME 경로 | `C:\Program Files\Eclipse Adoptium\jdk-17` | `/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home` |
| 원샷 세팅 | `shell/bootstrap.ps1` | 없음 (§3 수동) |

### Android vs iOS (Appium 기준)

| 항목 | Android | iOS |
|------|---------|-----|
| 자동화 엔진 | UiAutomator2 | XCUITest |
| 필수 IDE | Android Studio | Xcode |
| 앱 파일 형식 | `.apk` | `.app`(시뮬) / `.ipa`(실기기) |
| 요소 탐색 도구 | uiautomatorviewer / Appium Inspector | Appium Inspector |
| 드라이버 픽스처 | `android_driver` | `ios_driver` |
| 실행 OS 제한 | Windows / macOS / Linux | **macOS 전용** |
| 디바이스 ID 확인 | `adb devices` | `xcrun simctl list devices` |

---

## 9. 관련 문서

- [Allure 리포트 가이드](ALLURE_REPORT_GUIDE.md)
- [코딩 가이드라인](CODING_GUIDELINES.md)
- [UI Dump 가이드](UI_DUMP_GUIDE.md)
- [iOS 테스트 작성 가이드](IOS_TEST_GUIDE.md)
- [MCP 셋업 가이드](MCP_SETUP_GUIDE.md) — MCP 시나리오 녹화 도구는 별도 셋업 (환경 세팅과 독립)
