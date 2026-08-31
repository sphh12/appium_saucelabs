Param(
  [switch]$SkipEmulator,
  [switch]$SkipAllure,
  [string]$AndroidPlatformVersion = ""
)

$ErrorActionPreference = 'Stop'

Write-Host "========================================"
Write-Host "  Appium Project Bootstrap (Windows)"
Write-Host "========================================"

Set-Location (Split-Path -Parent $PSScriptRoot)

if ($AndroidPlatformVersion -ne "") {
  $env:ANDROID_PLATFORM_VERSION = $AndroidPlatformVersion
  Write-Host "[ENV] ANDROID_PLATFORM_VERSION=$AndroidPlatformVersion"
}

Write-Host "[1/6] Checking tools..."
foreach ($cmd in @('python','npm')) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    throw "Missing command in PATH: $cmd"
  }
}

Write-Host "[2/6] Python venv + requirements..."
if (-not (Test-Path .\venv)) {
  python -m venv venv
}
. .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "[3/6] Node dependencies (local appium + allure)..."
npm install --no-audit --no-fund

Write-Host "[4/6] Appium driver: UiAutomator2..."
# 드라이버 목록은 stderr 로 나오므로 2>&1 로 합쳐 확인한다. 이미 설치된 상태에서
# install 을 다시 호출하면 "already installed" 에러로 스크립트 종료코드가 1이 된다.
$drivers = (npx --yes appium driver list --installed 2>&1 | Out-String)
if ($drivers -match 'uiautomator2') {
  Write-Host "UiAutomator2 driver already installed (skip)"
} else {
  npx --yes appium driver install uiautomator2 | Out-Host
}

Write-Host "[5/6] Project files (.env + APK)..."
# .env: 없으면 템플릿 복사 (모든 값이 선택사항이라 기본값으로 즉시 동작)
if (-not (Test-Path .env)) {
  Copy-Item .env.example .env
  Write-Host ".env created from .env.example"
}
# apps/는 gitignore라 클론에 안 딸려옴 — 공개 테스트용 앱이므로 릴리스에서 자동 다운로드
# 버전 고정: capabilities.py 검증 완료 버전 (릴리스 2.2.0 / versionCode 25)
$apkDir = "apps\android"
New-Item -ItemType Directory -Force $apkDir | Out-Null
$existingApk = Get-ChildItem $apkDir -Filter *.apk -ErrorAction SilentlyContinue
if ($existingApk) {
  Write-Host "APK already present: $($existingApk[0].Name) (skip download)"
} else {
  $apkUrl = "https://github.com/saucelabs/my-demo-app-android/releases/download/2.2.0/mda-2.2.0-25.apk"
  $apkPath = Join-Path $apkDir "mda-2.2.0-25.apk"
  # .part로 받아서 검증 통과 후에만 .apk로 승격한다 — 중단(Ctrl+C)·손상 다운로드가
  # 남더라도 확장자가 .apk가 아니므로 다음 실행의 '이미 있음' 체크에 걸리지 않는다.
  $apkTmp = "$apkPath.part"
  try {
    Write-Host "Downloading: $apkUrl"
    $prevProgress = $ProgressPreference
    $ProgressPreference = 'SilentlyContinue'  # PS 5.1 진행바 렌더링이 대용량 다운로드를 크게 늦춤
    try {
      Invoke-WebRequest -Uri $apkUrl -OutFile $apkTmp
    } finally {
      $ProgressPreference = $prevProgress
    }
    # 내용 검증 — 프록시/캡티브 포털이 200으로 HTML을 돌려주면 그게 .apk로 저장된다.
    # APK는 ZIP이므로 매직 바이트 'PK'와 최소 크기로 확인한다.
    $magic = New-Object byte[] 2
    $fs = [System.IO.File]::OpenRead($apkTmp)
    try { $null = $fs.Read($magic, 0, 2) } finally { $fs.Close() }
    $sizeOk = (Get-Item $apkTmp).Length -gt 1MB
    $zipOk = ($magic[0] -eq 0x50 -and $magic[1] -eq 0x4B)
    if (-not ($sizeOk -and $zipOk)) {
      # 정리는 아래 catch에서 (부분 파일 삭제 경로와 동일하게 처리)
      throw "다운로드 파일이 APK가 아님 (크기/서명 불일치) — 프록시 차단 페이지일 수 있음"
    }
    Move-Item $apkTmp $apkPath -Force
    Write-Host "Saved: $apkPath"
  } catch {
    # 검증 실패·중단 시 임시 파일 제거 (.apk로는 승격되지 않았으므로 고착 위험 없음)
    Remove-Item $apkTmp -Force -ErrorAction SilentlyContinue
    # 다운로드 실패(오프라인/프록시)해도 나머지 셋업은 유효하므로 중단하지 않음
    Write-Host "APK download failed: $($_.Exception.Message)"
    Write-Host "Manual download: https://github.com/saucelabs/my-demo-app-android/releases -> $apkDir"
  }
}

if (-not $SkipEmulator) {
  Write-Host "[6/6] ADB/Emulator quick check..."
  if (Get-Command adb -ErrorAction SilentlyContinue) {
    adb start-server | Out-Host
    adb devices -l | Out-Host
  } else {
    Write-Host "adb not found in PATH (Android SDK not configured)"
  }
}

if (-not $SkipAllure) {
  Write-Host "Allure check (local):"
  npx --yes allure --version | Out-Host
}

Write-Host ""
Write-Host "Bootstrap complete."
Write-Host "Run tests: ./shell/run-app.sh"
