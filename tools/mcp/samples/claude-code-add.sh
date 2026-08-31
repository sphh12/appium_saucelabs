#!/bin/bash
# Claude Code CLI 에 appium-mcp 등록 (한 줄 명령)
#
# 사전 조건:
#   - Claude Code 설치되어 있어야 함 (https://docs.claude.com)
#   - Node.js v22 이상
#   - 프로젝트 루트에서 `python tools/mcp/generate_capabilities.py` 실행 완료
#
# 사용법:
#   bash tools/mcp/samples/claude-code-add.sh           # 자동 감지
#   PROJECT_ROOT=/custom/path bash tools/mcp/samples/claude-code-add.sh

set -e

# 프로젝트 루트 자동 감지
if [[ -z "$PROJECT_ROOT" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
fi

CAPABILITIES_CONFIG="$PROJECT_ROOT/tools/mcp/capabilities.json"
SCREENSHOTS_DIR="$PROJECT_ROOT/ui_dumps/mcp"

# ANDROID_HOME 자동 감지 (없으면 OS별 기본값)
if [[ -z "$ANDROID_HOME" ]]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        ANDROID_HOME="$HOME/Library/Android/sdk"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        ANDROID_HOME="$LOCALAPPDATA/Android/Sdk"
    else
        ANDROID_HOME="$HOME/Android/Sdk"
    fi
fi

echo "Project Root        : $PROJECT_ROOT"
echo "ANDROID_HOME        : $ANDROID_HOME"
echo "CAPABILITIES_CONFIG : $CAPABILITIES_CONFIG"
echo "SCREENSHOTS_DIR     : $SCREENSHOTS_DIR"
echo

# capabilities.json 존재 확인
if [[ ! -f "$CAPABILITIES_CONFIG" ]]; then
    echo "[!] capabilities.json 없음. 먼저 실행하세요:"
    echo "    python tools/mcp/generate_capabilities.py"
    exit 1
fi

# Claude Code 명령 등록
# NO_UI=true: base64 응답 대신 파일 경로만 반환 → 토큰 60~90% 절감 (LLM 컨텍스트 보호)
claude mcp add appium-mcp \
    --env NO_UI=true \
    --env ANDROID_HOME="$ANDROID_HOME" \
    --env CAPABILITIES_CONFIG="$CAPABILITIES_CONFIG" \
    --env SCREENSHOTS_DIR="$SCREENSHOTS_DIR" \
    -- appium-mcp

echo
echo "[OK] Claude Code 에 appium-mcp 등록 완료"
echo "확인: claude mcp list"
