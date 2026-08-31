# Claude Code CLI 에 appium-mcp 등록 (Windows PowerShell)
#
# 사전 조건:
#   - Claude Code 설치되어 있어야 함
#   - Node.js v22 이상
#   - 프로젝트 루트에서 `python tools/mcp/generate_capabilities.py` 실행 완료
#
# 사용법:
#   PowerShell> .\tools\mcp\samples\claude-code-add.ps1

$ErrorActionPreference = "Stop"

# 프로젝트 루트 자동 감지
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\..\..\.."

$CapabilitiesConfig = Join-Path $ProjectRoot "tools\mcp\capabilities.json"
$ScreenshotsDir = Join-Path $ProjectRoot "ui_dumps\mcp"

# ANDROID_HOME 자동 감지
if (-not $env:ANDROID_HOME) {
    $env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA "Android\Sdk"
}

Write-Host "Project Root        : $ProjectRoot"
Write-Host "ANDROID_HOME        : $env:ANDROID_HOME"
Write-Host "CAPABILITIES_CONFIG : $CapabilitiesConfig"
Write-Host "SCREENSHOTS_DIR     : $ScreenshotsDir"
Write-Host ""

# capabilities.json 존재 확인
if (-not (Test-Path $CapabilitiesConfig)) {
    Write-Host "[!] capabilities.json 없음. 먼저 실행하세요:" -ForegroundColor Red
    Write-Host "    python tools/mcp/generate_capabilities.py"
    exit 1
}

# Claude Code 명령 등록
# NO_UI=true: base64 응답 대신 파일 경로만 반환 → 토큰 60~90% 절감 (LLM 컨텍스트 보호)
claude mcp add appium-mcp `
    --env NO_UI=true `
    --env ANDROID_HOME="$env:ANDROID_HOME" `
    --env CAPABILITIES_CONFIG="$CapabilitiesConfig" `
    --env SCREENSHOTS_DIR="$ScreenshotsDir" `
    -- appium-mcp

Write-Host ""
Write-Host "[OK] Claude Code 에 appium-mcp 등록 완료" -ForegroundColor Green
Write-Host "확인: claude mcp list"
