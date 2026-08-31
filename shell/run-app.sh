#!/bin/bash

# Appium Mobile Test Runner
# Usage: ./shell/run-app.sh [options]
#
# Options:
#   --platform    : android or ios (default: android)
#   --app         : path to APK or IPA file (default: auto-detect from apps/)
#   --test        : specific test to run (e.g., test_login)
#   --files       : space-separated test paths to run in order (quote the value)
#   --all         : run all tests
#   --report      : open allure report after test
#   --generate    : generate allure html report (without server)
#   --skip-check  : skip prerequisite checks
#   --no-auto     : don't auto-start missing prerequisites

# Windows cp949 인코딩 문제 방지 (Python UTF-8 강제)
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# 파이프라인 중간 명령 실패가 조용히 묻히지 않도록 (set -e는 점검 로직의 의도적 비-0 처리 때문에 미적용)
set -o pipefail

# ~/.zshrc 환경변수 로드 (bash에서 실행 시 ANDROID_HOME, nvm 등 PATH 누락 방지)
if [[ -f "$HOME/.zshrc" ]]; then
    source "$HOME/.zshrc" 2>/dev/null
fi

PLATFORM="android"
TEST_NAME=""
TEST_FILES=""
APP_PATH=""
OPEN_REPORT=false
RUN_ALL=false
GENERATE_REPORT=false
SKIP_CHECK=false
AUTO_START=true

APPIUM_CMD="npx appium"
ALLURE_CMD="allure"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --test)
            TEST_NAME="$2"
            shift 2
            ;;
        --files)
            TEST_FILES="$2"
            shift 2
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        --report)
            OPEN_REPORT=true
            shift
            ;;
        --generate)
            GENERATE_REPORT=true
            shift
            ;;
        --skip-check)
            SKIP_CHECK=true
            shift
            ;;
        --no-auto)
            AUTO_START=false
            shift
            ;;
        --app)
            APP_PATH="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./shell/run-app.sh [options]"
            echo ""
            echo "Options:"
            echo "  --platform <android|ios>  Set test platform (default: android)"
            echo "  --app <path>              Path to APK or IPA file (default: auto-detect from apps/)"
            echo "  --test <test_name>        Run specific test (e.g., test_login)"
            echo "  --files \"<paths...>\"     Run specific test files in given order"
            echo "  --<file>                  Shorthand for tests/<platform>/<file>.py (e.g., --login_test)"
            echo "  --all                     Run all tests"
            echo "  --report                  Open allure report after test (requires server)"
            echo "  --generate                Generate HTML report to allure-report folder"
            echo "  --skip-check              Skip prerequisite checks"
            echo "  --no-auto                 Don't auto-start missing prerequisites"
            echo "  --help                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./shell/run-app.sh --login_test                   # specific test file"
            echo "  ./shell/run-app.sh --login_test --test test_login # + specific test method"
            echo "  ./shell/run-app.sh --app apps/android/app.apk     # explicit app path"
            echo "  ./shell/run-app.sh --all --report                 # All tests + report"
            echo ""
            echo "iOS Examples:"
            echo "  ./shell/run-ios.sh --login_test                   # iOS test"
            echo "  ./shell/run-ios.sh --all                          # All iOS tests"
            exit 0
            ;;
        *)
            # Shorthand: treat unknown --<name> as tests/<platform>/<name>.py if it exists.
            if [[ "$1" == --* ]]; then
                SHORT_NAME="${1#--}"
                if [[ -n "$SHORT_NAME" ]]; then
                    CANDIDATE="$SHORT_NAME"
                    if [[ "$CANDIDATE" != *.py ]]; then
                        CANDIDATE="$CANDIDATE.py"
                    fi
                    CANDIDATE_PATH="tests/$PLATFORM/$CANDIDATE"
                    if [[ -f "$CANDIDATE_PATH" ]]; then
                        if [[ -z "$TEST_FILES" ]]; then
                            TEST_FILES="$CANDIDATE_PATH"
                        else
                            TEST_FILES="$TEST_FILES $CANDIDATE_PATH"
                        fi
                        shift
                        continue
                    fi
                fi
            fi

            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# ========================================
# APK 자동 설정 (Android 전용, --app 미지정 시)
# ========================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ "$PLATFORM" == "android" && -z "$APP_PATH" ]]; then
    # apps/android/ 폴더 내 .apk 자동 탐색 (이름순 마지막 = 최신)
    APK_DIR="$PROJECT_ROOT/apps/android"
    if [[ -d "$APK_DIR" ]]; then
        APK_FILE=$(ls "$APK_DIR"/*.apk 2>/dev/null | sort | tail -1)
        if [[ -n "$APK_FILE" ]]; then
            APP_PATH="$APK_FILE"
        else
            echo -e "${RED}[ERROR] No .apk file found in $APK_DIR${NC}"
            exit 1
        fi
    else
        echo -e "${RED}[ERROR] App folder not found: $APK_DIR${NC}"
        echo -e "${YELLOW}[FIX] Create folder and place .apk: mkdir -p $APK_DIR${NC}"
        exit 1
    fi
fi

echo "========================================"
echo "  Appium Mobile Test Runner"
echo "========================================"
echo ""

# ========================================
# STEP 1: Prerequisite Checks & Auto-Start
# ========================================
if [[ "$SKIP_CHECK" == false ]]; then
    echo "[STEP 1] Checking prerequisites..."
    echo ""

    APPIUM_RUNNING=false
    DEVICE_CONNECTED=false
    VENV_EXISTS=false

    # Check 1: Appium Server
    echo -n "  - Appium Server (port 4723): "
    if curl -s http://127.0.0.1:4723/status > /dev/null 2>&1; then
        echo -e "${GREEN}Running${NC}"
        APPIUM_RUNNING=true
    else
        echo -e "${RED}Not Running${NC}"
        if [[ "$AUTO_START" == true ]]; then
            echo -e "    ${BLUE}[AUTO] Starting Appium server...${NC}"
            $APPIUM_CMD > /dev/null 2>&1 &
            APPIUM_PID=$!
            echo -e "    ${BLUE}[AUTO] Waiting for Appium to start...${NC}"

            # Wait for Appium to start (max 30 seconds)
            for i in {1..30}; do
                sleep 1
                if curl -s http://127.0.0.1:4723/status > /dev/null 2>&1; then
                    echo -e "    ${GREEN}[OK] Appium server started (PID: $APPIUM_PID)${NC}"
                    APPIUM_RUNNING=true
                    break
                fi
                echo -n "."
            done
            echo ""

            if [[ "$APPIUM_RUNNING" == false ]]; then
                echo -e "    ${RED}[FAIL] Could not start Appium server${NC}"
            fi
        else
            echo -e "    ${YELLOW}[FIX] Run: npx appium${NC}"
        fi
    fi

    # Check 2: Device / Emulator / Simulator (플랫폼별 분기)
    if [[ "$PLATFORM" == "ios" ]]; then
        # ---- iOS Simulator 점검 ----
        echo -n "  - iOS Simulator:            "
        if command -v xcrun &> /dev/null; then
            BOOTED_SIM=$(xcrun simctl list devices booted 2>/dev/null | grep -c "Booted")
            if [[ $BOOTED_SIM -gt 0 ]]; then
                SIM_NAME=$(xcrun simctl list devices booted 2>/dev/null | grep "Booted" | head -1 | sed 's/^[[:space:]]*//' | sed 's/ (.*$//')
                echo -e "${GREEN}Running ($SIM_NAME)${NC}"
                DEVICE_CONNECTED=true
            else
                echo -e "${RED}Not Running${NC}"
                if [[ "$AUTO_START" == true ]]; then
                    echo -e "    ${BLUE}[AUTO] Starting iOS Simulator...${NC}"

                    # 사용 가능한 iPhone 시뮬레이터 찾기
                    SIM_UDID=$(xcrun simctl list devices available 2>/dev/null | grep "iPhone" | head -1 | grep -oE '[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}')
                    SIM_NAME=$(xcrun simctl list devices available 2>/dev/null | grep "iPhone" | head -1 | sed 's/^[[:space:]]*//' | sed 's/ (.*$//')

                    if [[ -n "$SIM_UDID" ]]; then
                        echo -e "    ${BLUE}[AUTO] Found simulator: $SIM_NAME${NC}"
                        xcrun simctl boot "$SIM_UDID" 2>/dev/null
                        open -a Simulator 2>/dev/null
                        echo -e "    ${BLUE}[AUTO] Waiting for simulator to boot...${NC}"

                        # 시뮬레이터 부팅 대기 (최대 60초)
                        for i in {1..30}; do
                            sleep 2
                            BOOTED=$(xcrun simctl list devices booted 2>/dev/null | grep -c "Booted")
                            if [[ $BOOTED -gt 0 ]]; then
                                echo -e "    ${GREEN}[OK] Simulator started ($SIM_NAME)${NC}"
                                DEVICE_CONNECTED=true
                                break
                            fi
                            if (( i % 5 == 0 )); then
                                echo -e "    ${BLUE}[AUTO] Still waiting... ($((i*2))s)${NC}"
                            fi
                        done

                        if [[ "$DEVICE_CONNECTED" == false ]]; then
                            echo -e "    ${RED}[FAIL] Simulator boot timeout${NC}"
                        fi
                    else
                        echo -e "    ${RED}[FAIL] No iPhone simulator found. Create one in Xcode.${NC}"
                    fi
                else
                    echo -e "    ${YELLOW}[FIX] Open Simulator app or run: xcrun simctl boot <device_udid>${NC}"
                fi
            fi
        else
            echo -e "${RED}xcrun not found${NC}"
            echo -e "    ${YELLOW}[FIX] Install Xcode Command Line Tools: xcode-select --install${NC}"
        fi
    else
        # ---- Android Emulator / Device 점검 ----
        # ANDROID_HOME 미설정 시 기본 경로 탐색 (macOS)
        if ! command -v adb &> /dev/null; then
            for SDK_PATH in "$HOME/Library/Android/sdk" "/usr/local/share/android-sdk"; do
                if [[ -f "$SDK_PATH/platform-tools/adb" ]]; then
                    export ANDROID_HOME="$SDK_PATH"
                    export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
                    break
                fi
            done
        fi

        echo -n "  - Android Device/Emulator:  "
        if command -v adb &> /dev/null; then
            # Suppress adb daemon messages
            adb start-server > /dev/null 2>&1
            sleep 1

            DEVICE_COUNT=$(adb devices 2>/dev/null | grep -w "device" | wc -l)
            if [[ $DEVICE_COUNT -gt 0 ]]; then
                DEVICE_NAME=$(adb devices 2>/dev/null | grep -w "device" | head -1 | cut -f1)
                echo -e "${GREEN}Connected ($DEVICE_NAME)${NC}"
                DEVICE_CONNECTED=true
            else
                echo -e "${RED}Not Connected${NC}"
                if [[ "$AUTO_START" == true ]]; then
                    echo -e "    ${BLUE}[AUTO] Starting Android emulator...${NC}"

                    # Preferred emulator: Pixel_6, otherwise use first available
                    EMULATOR_NAME=$(emulator -list-avds 2>/dev/null | grep -i "Pixel_6" | head -1)
                    if [[ -z "$EMULATOR_NAME" ]]; then
                        EMULATOR_NAME=$(emulator -list-avds 2>/dev/null | head -1)
                    fi

                    if [[ -n "$EMULATOR_NAME" ]]; then
                        echo -e "    ${BLUE}[AUTO] Found emulator: $EMULATOR_NAME${NC}"
                        emulator -avd "$EMULATOR_NAME" -no-snapshot-load > /dev/null 2>&1 &
                        EMULATOR_PID=$!
                        echo -e "    ${BLUE}[AUTO] Waiting for emulator to boot (this may take a while)...${NC}"

                        # Wait for emulator to boot (max 120 seconds)
                        for i in {1..120}; do
                            sleep 2
                            BOOT_COMPLETED=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
                            if [[ "$BOOT_COMPLETED" == "1" ]]; then
                                DEVICE_NAME=$(adb devices 2>/dev/null | grep -w "device" | head -1 | cut -f1)
                                echo -e "    ${GREEN}[OK] Emulator started ($DEVICE_NAME)${NC}"
                                DEVICE_CONNECTED=true

                                # Some environments report boot completed before ADB is fully in 'device' state.
                                # Wait a bit longer to avoid Appium timing out while searching for a connected device.
                                echo -e "    ${BLUE}[AUTO] Waiting for ADB to be ready...${NC}"
                                ADB_READY=false
                                for j in {1..30}; do
                                    STATE=$(adb get-state 2>/dev/null | tr -d '\r')
                                    if [[ "$STATE" == "device" ]]; then
                                        ADB_READY=true
                                        break
                                    fi
                                    sleep 2
                                done

                                if [[ "$ADB_READY" == true ]]; then
                                    echo -e "    ${GREEN}[OK] ADB is ready${NC}"
                                else
                                    echo -e "    ${RED}[FAIL] ADB not ready (still offline).${NC}"
                                    DEVICE_CONNECTED=false
                                fi
                                break
                            fi
                            # Show progress every 10 seconds
                            if (( i % 5 == 0 )); then
                                echo -e "    ${BLUE}[AUTO] Still waiting... (${i}s)${NC}"
                            fi
                        done

                        if [[ "$DEVICE_CONNECTED" == false ]]; then
                            echo -e "    ${RED}[FAIL] Emulator boot timeout${NC}"
                        fi
                    else
                        echo -e "    ${RED}[FAIL] No emulator found. Create one in Android Studio.${NC}"
                    fi
                else
                    echo -e "    ${YELLOW}[FIX] Start emulator from Android Studio or connect device${NC}"
                fi
            fi
        else
            echo -e "${RED}ADB not found${NC}"
            echo -e "    ${YELLOW}[FIX] Check ANDROID_HOME environment variable${NC}"
        fi
    fi

    # Check 3: Virtual Environment
    echo -n "  - Python venv:              "
    if [[ -d "venv" ]]; then
        echo -e "${GREEN}Found${NC}"
        VENV_EXISTS=true
    else
        echo -e "${RED}Not Found${NC}"
        if [[ "$AUTO_START" == true ]]; then
            echo -e "    ${BLUE}[AUTO] Creating virtual environment...${NC}"
            python -m venv venv
            if [[ -d "venv" ]]; then
                echo -e "    ${GREEN}[OK] Virtual environment created${NC}"
                VENV_EXISTS=true

                # Activate and install requirements
                echo -e "    ${BLUE}[AUTO] Installing requirements...${NC}"
                if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                    source venv/Scripts/activate
                else
                    source venv/bin/activate
                fi
                pip install -r requirements.txt > /dev/null 2>&1
                echo -e "    ${GREEN}[OK] Requirements installed${NC}"
            else
                echo -e "    ${RED}[FAIL] Could not create virtual environment${NC}"
            fi
        else
            echo -e "    ${YELLOW}[FIX] Run: python -m venv venv${NC}"
        fi
    fi

    echo ""

    # Check 4: Appium Driver (플랫폼별 분기)
    # 목록을 먼저 변수로 받는다 — `... | grep -q`는 grep이 첫 매치에서 파이프를 닫아
    # 상위 명령이 SIGPIPE(141)로 죽고, pipefail 때문에 파이프라인 전체가 비-0이 되어
    # 설치된 드라이버가 'Not Installed'로 오판될 수 있다.
    INSTALLED_DRIVERS="$($APPIUM_CMD driver list --installed 2>&1 || true)"
    if [[ "$PLATFORM" == "ios" ]]; then
        echo -n "  - Appium driver (XCUITest):    "
        if grep -qi "xcuitest" <<< "$INSTALLED_DRIVERS"; then
            echo -e "${GREEN}Installed${NC}"
        else
            echo -e "${RED}Not Installed${NC}"
            if [[ "$AUTO_START" == true ]]; then
                echo -e "    ${BLUE}[AUTO] Installing XCUITest driver...${NC}"
                if $APPIUM_CMD driver install xcuitest; then
                    echo -e "    ${GREEN}[OK] XCUITest driver installed${NC}"
                else
                    echo -e "    ${RED}[FAIL] Could not install XCUITest driver${NC}"
                fi
            else
                echo -e "    ${YELLOW}[FIX] Run: appium driver install xcuitest${NC}"
            fi
        fi
    else
        echo -n "  - Appium driver (UiAutomator2): "
        if grep -qi "uiautomator2" <<< "$INSTALLED_DRIVERS"; then
            echo -e "${GREEN}Installed${NC}"
        else
            echo -e "${RED}Not Installed${NC}"
            if [[ "$AUTO_START" == true ]]; then
                echo -e "    ${BLUE}[AUTO] Installing UiAutomator2 driver...${NC}"
                if $APPIUM_CMD driver install uiautomator2; then
                    echo -e "    ${GREEN}[OK] UiAutomator2 driver installed${NC}"
                else
                    echo -e "    ${RED}[FAIL] Could not install UiAutomator2 driver${NC}"
                fi
            else
                echo -e "    ${YELLOW}[FIX] Run: appium driver install uiautomator2${NC}"
            fi
        fi
    fi

    # Check 5: Allure CLI (report)
    echo -n "  - Allure CLI:               "
    if command -v allure &> /dev/null; then
        echo -e "${GREEN}Found (global)${NC}"
    else
        # Prefer local install via npm (npx)
        if npx --yes allure --version > /dev/null 2>&1; then
            ALLURE_CMD="npx --yes allure"
            echo -e "${GREEN}Found (npx/local)${NC}"
        else
            echo -e "${RED}Not Found${NC}"
            if [[ "$AUTO_START" == true ]]; then
                echo -e "    ${BLUE}[AUTO] Installing allure-commandline locally...${NC}"
                if npm install --no-audit --no-fund; then
                    ALLURE_CMD="npx --yes allure"
                    echo -e "    ${GREEN}[OK] allure-commandline installed (use npx allure)${NC}"
                else
                    echo -e "    ${RED}[FAIL] npm install failed (cannot install allure-commandline)${NC}"
                fi
            else
                echo -e "    ${YELLOW}[FIX] Run: npm install (then use npx allure) or install allure globally${NC}"
            fi
        fi
    fi

    # Final check
    if [[ "$APPIUM_RUNNING" == false || "$DEVICE_CONNECTED" == false || "$VENV_EXISTS" == false ]]; then
        echo -e "${RED}[ERROR] Prerequisites not met.${NC}"
        echo ""
        if [[ "$AUTO_START" == true ]]; then
            echo "Auto-start failed for some components. Please check manually."
        else
            echo "To auto-start missing prerequisites, remove --no-auto option"
        fi
        echo "To skip checks, use: ./shell/run-app.sh --skip-check [options]"
        exit 1
    fi

    echo -e "${GREEN}[OK] All prerequisites met!${NC}"
    echo ""
fi

# ========================================
# STEP 2: Activate Virtual Environment
# ========================================
echo "[STEP 2] Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
echo -e "${GREEN}[OK] Virtual environment activated${NC}"
echo ""

# ========================================
# STEP 3: Run Tests + Generate Report (via run_allure.py)
# ========================================
# 테스트 실행과 Allure 후처리(타임스탬프 폴더 생성·history 이어붙임·custom.css 주입·
# LATEST 고정·dashboard 업데이트·web 업로드)를 모두 tools/run_allure.py 한 곳에 위임한다.
# (셸에서 sed/cp/cat으로 중복 구현하던 후처리를 제거 — macOS BSD sed 비호환 문제도 해소)
echo "[STEP 3] Running tests + generating Allure report..."
echo ""

# pytest 대상 결정
DEFAULT_TARGET="tests/android"
if [[ "$PLATFORM" == "ios" ]]; then
    DEFAULT_TARGET="tests/ios"
fi

TARGET="$DEFAULT_TARGET"
if [[ "$RUN_ALL" == true ]]; then
    TARGET="tests/$PLATFORM"
fi
if [[ -n "$TEST_FILES" ]]; then
    TARGET="$TEST_FILES"
fi

# run_allure.py 에 전달할 pytest 인자 구성 (배열 — eval 제거로 임의 명령 실행 위험 없음)
# TARGET 은 --files 로 여러 경로가 한 인자에 올 수 있어 의도적으로 단어 분할한다.
# 그 대가로 경로에 공백은 지원하지 않는다(테스트 파일명 규칙상 공백 없음).
# set -f 로 글롭 확장만 차단 — 경로에 [ ] * 가 있어도 파일명으로 그대로 전달된다.
set -f
PYTEST_ARGS=($TARGET -v --platform="$PLATFORM" --record-video --allure-attach=hybrid)
set +f

if [[ -n "$APP_PATH" ]]; then
    # Convert MINGW path to Windows path if needed
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        APP_PATH=$(cygpath -w "$APP_PATH" 2>/dev/null || echo "$APP_PATH")
    fi
    PYTEST_ARGS+=(--app="$APP_PATH")
fi

if [[ "$RUN_ALL" == false && -n "$TEST_NAME" ]]; then
    PYTEST_ARGS+=(-k "$TEST_NAME")
fi

# run_allure.py 옵션: --report 지정 시 리포트 생성 후 브라우저로 열기(--open)
RUN_ALLURE_OPTS=()
if [[ "$OPEN_REPORT" == true ]]; then
    RUN_ALLURE_OPTS+=(--open)
fi

echo "  Platform: $PLATFORM"
if [[ -n "$APP_PATH" ]]; then
    echo "  App:      $APP_PATH"
fi
if [[ -n "$TEST_FILES" ]]; then
    echo "  Files:    $TEST_FILES"
else
    echo "  Target:   $TARGET"
fi
echo "  Filter:   ${TEST_NAME:-none}"
echo ""
echo "----------------------------------------"

# 테스트 실행 + 리포트 후처리 (단일 경로)
# run_allure.py 는 pytest 의 종료 코드를 그대로 반환한다. (eval 제거 → 배열로 안전 실행)
python tools/run_allure.py "${RUN_ALLURE_OPTS[@]}" -- "${PYTEST_ARGS[@]}"
TEST_EXIT_CODE=$?

echo "----------------------------------------"
echo ""

# ========================================
# Summary
# ========================================
echo "========================================"
if [[ $TEST_EXIT_CODE -eq 0 ]]; then
    echo -e "  ${GREEN}Tests completed successfully!${NC}"
else
    echo -e "  ${RED}Tests failed (exit code: $TEST_EXIT_CODE)${NC}"
fi
echo "========================================"
echo ""
echo "Results:    allure-results/<timestamp>"
echo "Report:     allure-reports/<timestamp>"
echo "Latest:     allure-reports/LATEST/index.html"
echo "Dashboard:  allure-reports/dashboard/index.html  (python tools/serve.py)"
echo ""
echo "To view the local report:"
echo "  python tools/run_allure.py --open  (또는: allure open allure-reports/LATEST/..)"
echo ""

exit $TEST_EXIT_CODE
