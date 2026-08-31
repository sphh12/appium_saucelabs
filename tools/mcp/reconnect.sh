#!/bin/bash
# Appium MCP 재연결 자동화 (macOS / Linux / WSL)
#
# 사전 점검(Node.js / claude / adb / Appium 서버 / 디바이스 / capabilities.json)
# → 필요 시 capabilities.json 자동 생성 → MCP 재등록 → 결과 검증
#
# 사용법:
#   bash tools/mcp/reconnect.sh             # 점검 + 미연결 시 재등록
#   bash tools/mcp/reconnect.sh --verify    # 점검만 (등록 변경 없음)
#   bash tools/mcp/reconnect.sh --force     # 이미 연결돼 있어도 강제 재등록

set -uo pipefail

VERIFY=0
FORCE=0
for arg in "$@"; do
    case "$arg" in
        --verify) VERIFY=1 ;;
        --force)  FORCE=1 ;;
        -h|--help)
            grep '^#' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
    esac
done

# 색상
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

step() { echo -e "${CYAN}[STEP]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}   $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC}  $1"; }

# 프로젝트 루트 자동 감지 (tools/mcp -> 2단계 위)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CAPABILITIES_CONFIG="$PROJECT_ROOT/tools/mcp/capabilities.json"
SCREENSHOTS_DIR="$PROJECT_ROOT/ui_dumps/mcp"

# ANDROID_HOME 자동 감지
if [[ -z "${ANDROID_HOME:-}" ]]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        ANDROID_HOME="$HOME/Library/Android/sdk"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        ANDROID_HOME="${LOCALAPPDATA:-$HOME/AppData/Local}/Android/Sdk"
    else
        ANDROID_HOME="$HOME/Android/Sdk"
    fi
    export ANDROID_HOME
fi

echo
echo -e "${MAGENTA}=== Appium MCP 재연결 자동화 ===${NC}"
echo "Project Root        : $PROJECT_ROOT"
echo "ANDROID_HOME        : $ANDROID_HOME"
echo "CAPABILITIES_CONFIG : $CAPABILITIES_CONFIG"
echo "SCREENSHOTS_DIR     : $SCREENSHOTS_DIR"
echo

ALL_OK=1

# 1. Node.js v22+
step "1. Node.js v22+ 확인"
if command -v node >/dev/null 2>&1; then
    NODE_VER=$(node -v | sed 's/^v//')
    NODE_MAJOR=${NODE_VER%%.*}
    if (( NODE_MAJOR >= 22 )); then
        ok "Node.js v$NODE_VER"
    else
        err "Node.js v$NODE_VER (v22 이상 필요)"
        ALL_OK=0
    fi
else
    err "Node.js 미설치"
    ALL_OK=0
fi

# 2. claude
step "2. Claude Code CLI 확인"
if command -v claude >/dev/null 2>&1; then
    ok "claude CLI: $(claude --version 2>&1 | head -1)"
else
    err "claude CLI 없음"
    ALL_OK=0
fi

# 3. adb
step "3. adb 확인"
if command -v adb >/dev/null 2>&1; then
    ok "adb 사용 가능"
else
    err "adb 없음 — Android SDK platform-tools PATH 추가 필요"
    ALL_OK=0
fi

# 4. appium-mcp 글로벌 설치 확인
step "4. appium-mcp 글로벌 설치 확인"
if command -v appium-mcp >/dev/null 2>&1; then
    ok "appium-mcp: $(command -v appium-mcp)"
else
    warn "appium-mcp 글로벌 설치 안됨 — 'npm install -g appium-mcp' 권장"
fi

if (( ALL_OK == 0 )); then
    err "필수 도구 누락 — 종료"
    exit 1
fi

# 5. Appium 서버
step "5. Appium 서버 (127.0.0.1:4723) 응답"
if curl -fsS --max-time 3 http://127.0.0.1:4723/status >/dev/null 2>&1; then
    ok "Appium 서버 동작 중"
else
    warn "Appium 서버 응답 없음 — 별도 터미널에서 'appium' 실행 필요"
fi

# 6. 디바이스
step "6. 연결된 디바이스 확인"
DEV_LINES=$(adb devices 2>/dev/null | awk 'NR>1 && /\sdevice$/{print}')
if [[ -n "$DEV_LINES" ]]; then
    DEV_COUNT=$(echo "$DEV_LINES" | wc -l | tr -d ' ')
    ok "${DEV_COUNT}대 디바이스 연결됨"
    echo "$DEV_LINES" | sed 's/^/       /'
else
    warn "연결된 디바이스 없음 — 에뮬레이터/실기기 부팅 필요"
fi

# 7. capabilities.json
step "7. capabilities.json 점검"
if [[ ! -f "$CAPABILITIES_CONFIG" ]]; then
    warn "없음 — 자동 생성 시도 (python tools/mcp/generate_capabilities.py)"
    pushd "$PROJECT_ROOT" >/dev/null
    python tools/mcp/generate_capabilities.py || true
    popd >/dev/null
    if [[ -f "$CAPABILITIES_CONFIG" ]]; then
        ok "capabilities.json 생성됨"
    else
        err "capabilities.json 생성 실패"
        exit 1
    fi
else
    ok "capabilities.json 존재"
fi

# Verify 모드
if (( VERIFY == 1 )); then
    echo
    ok "검증 완료 (--verify 모드 — 등록 변경 없음)"
    echo
    echo "현재 MCP 상태:"
    LINE=$(claude mcp list 2>&1 | grep -i "appium-mcp" || true)
    if [[ -n "$LINE" ]]; then
        echo "  $LINE"
    else
        echo "  (appium-mcp 등록 없음)"
    fi
    exit 0
fi

# 8. 현재 MCP 등록 상태
step "8. 현재 MCP 등록 상태"
APPIUM_LINE=$(claude mcp list 2>&1 | grep -i "appium-mcp" | head -1 || true)
if [[ -n "$APPIUM_LINE" ]]; then
    echo "       $APPIUM_LINE"
else
    echo "       (등록 없음)"
fi

if echo "$APPIUM_LINE" | grep -q "Connected" && (( FORCE == 0 )); then
    ok "appium-mcp 이미 Connected — 재등록 생략 (강제 시 --force)"
    exit 0
fi

# 9. 기존 등록 제거
if [[ -n "$APPIUM_LINE" ]]; then
    step "9. 기존 등록 제거"
    if claude mcp remove appium-mcp >/dev/null 2>&1; then
        ok "기존 등록 제거됨"
    else
        warn "제거 실패 — 계속 진행"
    fi
fi

# 10. 재등록
step "10. appium-mcp 재등록 (NO_UI=true)"
claude mcp add appium-mcp \
    --env NO_UI=true \
    --env ANDROID_HOME="$ANDROID_HOME" \
    --env CAPABILITIES_CONFIG="$CAPABILITIES_CONFIG" \
    --env SCREENSHOTS_DIR="$SCREENSHOTS_DIR" \
    -- appium-mcp

# 11. 검증
step "11. 등록 결과 검증"
sleep 1
RESULT=$(claude mcp list 2>&1 | grep -i "appium-mcp" | head -1 || true)
echo "       $RESULT"

if echo "$RESULT" | grep -q "Connected"; then
    ok "재연결 성공"
    echo
    echo -e "${CYAN}다음 단계: claude 명령으로 새 세션을 시작하세요.${NC}"
else
    warn "Connected 미확인 — Claude Code 재시작 후 'claude mcp list'로 재확인"
    echo "로그 확인: claude mcp logs appium-mcp"
    exit 2
fi

echo
ok "완료"
