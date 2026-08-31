# Appium MCP 재연결 자동화 (Windows PowerShell)
#
# 사전 점검(Node.js / claude / adb / Appium 서버 / 디바이스 / capabilities.json)
# → 필요 시 capabilities.json 자동 생성 → MCP 재등록 → 결과 검증
#
# 사용법:
#   .\tools\mcp\reconnect.ps1               # 점검 + 미연결 시 재등록
#   .\tools\mcp\reconnect.ps1 -Verify       # 점검만 (등록 변경 없음)
#   .\tools\mcp\reconnect.ps1 -Force        # 이미 연결돼 있어도 강제 재등록

[CmdletBinding()]
param(
    [switch]$Verify,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# 프로젝트 루트 자동 감지 (tools/mcp -> 2단계 위)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir\..\..").Path

$CapabilitiesConfig = Join-Path $ProjectRoot "tools\mcp\capabilities.json"
$ScreenshotsDir = Join-Path $ProjectRoot "ui_dumps\mcp"

# ANDROID_HOME 자동 감지
if (-not $env:ANDROID_HOME) {
    $env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA "Android\Sdk"
}

# 색상 헬퍼
function Write-Step($msg) { Write-Host "[STEP] $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR]  $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "=== Appium MCP 재연결 자동화 ===" -ForegroundColor Magenta
Write-Host "Project Root        : $ProjectRoot"
Write-Host "ANDROID_HOME        : $env:ANDROID_HOME"
Write-Host "CAPABILITIES_CONFIG : $CapabilitiesConfig"
Write-Host "SCREENSHOTS_DIR     : $ScreenshotsDir"
Write-Host ""

$AllOk = $true

# 1. Node.js v22+
Write-Step "1. Node.js v22+ 확인"
try {
    $nodeVer = (node -v) -replace '^v', ''
    $major = [int](($nodeVer -split '\.')[0])
    if ($major -ge 22) {
        Write-OK "Node.js v$nodeVer"
    } else {
        Write-Err "Node.js v$nodeVer (v22 이상 필요)"
        $AllOk = $false
    }
} catch {
    Write-Err "Node.js 미설치 또는 PATH 미등록"
    $AllOk = $false
}

# 2. Claude Code CLI
Write-Step "2. Claude Code CLI 확인"
try {
    $claudeVer = (claude --version 2>&1 | Select-Object -First 1)
    Write-OK "claude CLI: $claudeVer"
} catch {
    Write-Err "claude CLI 없음 — Claude Code 설치 필요"
    $AllOk = $false
}

# 3. adb
Write-Step "3. adb 확인"
try {
    $null = adb version 2>&1
    Write-OK "adb 사용 가능"
} catch {
    Write-Err "adb 없음 — Android SDK platform-tools PATH 추가 필요"
    $AllOk = $false
}

# 4. appium-mcp 명령 존재 확인 (글로벌 설치 여부)
Write-Step "4. appium-mcp 글로벌 설치 확인"
$appiumMcpPath = (Get-Command appium-mcp -ErrorAction SilentlyContinue).Source
if ($appiumMcpPath) {
    Write-OK "appium-mcp: $appiumMcpPath"
} else {
    Write-Warn "appium-mcp 글로벌 설치 안됨 — 'npm install -g appium-mcp' 권장"
}

if (-not $AllOk) {
    Write-Err "필수 도구 누락 — 종료"
    exit 1
}

# 5. Appium 서버
Write-Step "5. Appium 서버 (127.0.0.1:4723) 응답"
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:4723/status" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
    if ($resp.StatusCode -eq 200) {
        Write-OK "Appium 서버 동작 중"
    } else {
        Write-Warn "Appium 서버 응답 코드: $($resp.StatusCode)"
    }
} catch {
    Write-Warn "Appium 서버 응답 없음 — 별도 터미널에서 'appium' 실행 필요"
}

# 6. adb devices
Write-Step "6. 연결된 디바이스 확인"
$devLines = (adb devices | Select-String -Pattern "\sdevice$")
if ($devLines.Count -ge 1) {
    Write-OK "$($devLines.Count)대 디바이스 연결됨"
    $devLines | ForEach-Object { Write-Host "       $_" }
} else {
    Write-Warn "연결된 디바이스 없음 — 에뮬레이터/실기기 부팅 필요"
}

# 7. capabilities.json
Write-Step "7. capabilities.json 점검"
if (-not (Test-Path $CapabilitiesConfig)) {
    Write-Warn "없음 — 자동 생성 시도 (python tools/mcp/generate_capabilities.py)"
    Push-Location $ProjectRoot
    try {
        python tools/mcp/generate_capabilities.py
    } finally {
        Pop-Location
    }
    if (Test-Path $CapabilitiesConfig) {
        Write-OK "capabilities.json 생성됨"
    } else {
        Write-Err "capabilities.json 생성 실패"
        exit 1
    }
} else {
    Write-OK "capabilities.json 존재"
}

# Verify 모드 — 등록 변경 없이 종료
if ($Verify) {
    Write-Host ""
    Write-OK "검증 완료 (Verify 모드 — 등록 변경 없음)"
    Write-Host ""
    Write-Host "현재 MCP 상태:"
    $listOut = claude mcp list 2>&1
    $line = $listOut | Select-String "appium-mcp"
    if ($line) {
        Write-Host "  $line"
    } else {
        Write-Host "  (appium-mcp 등록 없음)"
    }
    exit 0
}

# 8. 현재 MCP 등록 상태 확인
Write-Step "8. 현재 MCP 등록 상태"
$mcpList = claude mcp list 2>&1
$appiumLine = ($mcpList | Select-String "appium-mcp" | Select-Object -First 1).ToString()
if ($appiumLine) {
    Write-Host "       $appiumLine"
} else {
    Write-Host "       (등록 없음)"
}

$isConnected = $appiumLine -match "Connected"

if ($isConnected -and -not $Force) {
    Write-OK "appium-mcp 이미 Connected — 재등록 생략 (강제 시 -Force)"
    exit 0
}

# 9. 기존 등록 제거 (있으면)
if ($appiumLine) {
    Write-Step "9. 기존 등록 제거"
    try {
        claude mcp remove appium-mcp 2>&1 | Out-Null
        Write-OK "기존 등록 제거됨"
    } catch {
        Write-Warn "제거 실패 — 계속 진행"
    }
}

# 10. 재등록
Write-Step "10. appium-mcp 재등록 (NO_UI=true)"
claude mcp add appium-mcp `
    --env NO_UI=true `
    --env ANDROID_HOME="$env:ANDROID_HOME" `
    --env CAPABILITIES_CONFIG="$CapabilitiesConfig" `
    --env SCREENSHOTS_DIR="$ScreenshotsDir" `
    -- appium-mcp

# 11. 검증
Write-Step "11. 등록 결과 검증"
Start-Sleep -Seconds 1
$result = (claude mcp list 2>&1 | Select-String "appium-mcp" | Select-Object -First 1).ToString()
Write-Host "       $result"

if ($result -match "Connected") {
    Write-OK "재연결 성공"
    Write-Host ""
    Write-Host "다음 단계: claude 명령으로 새 세션을 시작하세요." -ForegroundColor Cyan
} else {
    Write-Warn "Connected 미확인 — Claude Code 재시작 후 'claude mcp list'로 재확인"
    Write-Host "로그 확인: claude mcp logs appium-mcp"
    exit 2
}

Write-Host ""
Write-OK "완료"
