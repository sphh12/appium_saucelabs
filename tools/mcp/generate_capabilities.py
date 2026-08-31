"""
Appium MCP capabilities.json 자동 생성 스크립트

이 스크립트는 기존 프로젝트 설정(.env, config/capabilities.py, apps/ 폴더)을
읽어서 공식 appium-mcp 서버가 사용할 capabilities.json 파일을 생성합니다.

대상 앱: SauceLabs My Demo App (단일 환경)
Windows / macOS 양쪽에서 동작합니다.

사용법:
  # capabilities.json 생성
  python tools/mcp/generate_capabilities.py

  # 사전 점검 (생성 안 함, 환경/앱/Node만 확인)
  python tools/mcp/generate_capabilities.py --verify

생성 파일:
  tools/mcp/capabilities.json   ← appium-mcp가 읽는 파일 (gitignore 권장)
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# .env 자동 로드 (python-dotenv 우선, 없으면 수동 파싱)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# SauceLabs My Demo App (네이티브 Android) 패키지 / resource-id 접두사
# 출처: https://github.com/saucelabs/my-demo-app-android
ANDROID_PACKAGE = "com.saucelabs.mydemoapp.android"
RESOURCE_ID_PREFIX = f"{ANDROID_PACKAGE}:id"

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv(ENV_FILE)
except ImportError:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# ---------- 유틸리티 ----------
def _detect_android_home() -> str | None:
    """OS별 기본 ANDROID_HOME 경로 자동 감지"""
    env_value = os.getenv("ANDROID_HOME") or os.getenv("ANDROID_SDK_ROOT")
    if env_value and Path(env_value).exists():
        return env_value

    candidates: list[Path] = []
    system = platform.system()

    if system == "Windows":
        local_app = os.getenv("LOCALAPPDATA")
        if local_app:
            candidates.append(Path(local_app) / "Android" / "Sdk")
        candidates.append(Path.home() / "AppData" / "Local" / "Android" / "Sdk")
    elif system == "Darwin":  # macOS
        candidates.append(Path.home() / "Library" / "Android" / "sdk")
        candidates.append(Path("/usr/local/share/android-sdk"))
    else:  # Linux
        candidates.append(Path.home() / "Android" / "Sdk")

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def _find_apk() -> str | None:
    """apps/android/ 폴더에서 가장 최신 .apk 파일 탐색"""
    apk_dir = PROJECT_ROOT / "apps" / "android"
    if not apk_dir.is_dir():
        return None

    apks = sorted(p for p in apk_dir.iterdir() if p.suffix == ".apk")
    if not apks:
        return None

    # 이름순 마지막(최신) 반환
    return str(apks[-1].resolve())


def _check_node() -> tuple[bool, str]:
    """Node.js 설치 + v22 이상 확인"""
    try:
        result = subprocess.run(
            ["node", "-v"], capture_output=True, text=True, timeout=10
        )
        version = result.stdout.strip().lstrip("v")
        major = int(version.split(".")[0])
        ok = major >= 22
        return ok, version
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        return False, "not found"


def _check_appium_running(host: str, port: int) -> bool:
    """Appium 서버가 떠 있는지 간단 확인 (옵션)"""
    try:
        import urllib.request

        with urllib.request.urlopen(
            f"http://{host}:{port}/status", timeout=2
        ) as response:
            return response.status == 200
    except Exception:
        return False


# ---------- 메인 로직 ----------
def build_capabilities() -> dict:
    """capabilities 블록 생성 (SauceLabs My Demo App, 단일 환경)"""
    apk_path = _find_apk()
    udid = os.getenv("ANDROID_UDID")
    device_name = os.getenv("ANDROID_DEVICE_NAME", "Android Emulator")
    platform_version = os.getenv("ANDROID_PLATFORM_VERSION")

    android_caps: dict = {
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": device_name,
        "appium:appPackage": ANDROID_PACKAGE,
        "appium:appActivity": "com.saucelabs.mydemoapp.android.view.activities.SplashActivity",
        "appium:noReset": False,
        "appium:fullReset": False,
        "appium:newCommandTimeout": 300,
        "appium:autoGrantPermissions": True,
        "appium:adbExecTimeout": 60000,
        "appium:appWaitDuration": 60000,
        "appium:uiautomator2ServerLaunchTimeout": 60000,
        # ── UiAutomator2 안정화 옵션 (MCP 인터랙티브 사용 시 크래시 완화) ──
        "appium:disableIdLocatorAutocompletion": True,
        "appium:waitForIdleTimeout": 100,
        "appium:disableWindowAnimation": True,
        "appium:ensureWebviewsHavePages": False,
        "appium:uiautomator2ServerInstallTimeout": 60000,
        "appium:uiautomator2ServerReadTimeout": 60000,
        "appium:skipServerInstallation": False,
        "appium:nativeWebScreenshot": True,
    }
    if apk_path:
        android_caps["appium:app"] = apk_path
    if udid:
        android_caps["appium:udid"] = udid
    if platform_version:
        android_caps["appium:platformVersion"] = platform_version

    ios_caps = {
        "platformName": "iOS",
        "appium:automationName": "XCUITest",
        "appium:deviceName": os.getenv("IOS_DEVICE_NAME", "iPhone 17"),
        "appium:platformVersion": os.getenv("IOS_PLATFORM_VERSION", "26.4"),
        "appium:bundleId": os.getenv("IOS_BUNDLE_ID", "com.saucelabs.mydemo.app.ios"),
        "appium:noReset": False,
        "appium:fullReset": False,
        "appium:newCommandTimeout": 300,
    }

    return {
        "android": android_caps,
        "ios": ios_caps,
        # 메타정보 (참고용, MCP가 읽지 않아도 무방)
        "_meta": {
            "app": "SauceLabs My Demo App",
            "resource_id_prefix": RESOURCE_ID_PREFIX,
            "appium_host": os.getenv("APPIUM_HOST", "127.0.0.1"),
            "appium_port": int(os.getenv("APPIUM_PORT", "4723")),
            "generated_by": "tools/mcp/generate_capabilities.py",
        },
    }


def verify() -> int:
    """사전 점검 모드"""
    print("=" * 60)
    print("Appium MCP 사전 점검")
    print("=" * 60)

    issues: list[str] = []
    print(f"\n[1] OS              : {platform.system()} ({platform.machine()})")
    print(f"[2] App             : SauceLabs My Demo App ({ANDROID_PACKAGE})")

    node_ok, node_version = _check_node()
    print(f"[3] Node.js         : v{node_version} {'OK' if node_ok else 'FAIL (v22 이상 필요)'}")
    if not node_ok:
        issues.append("Node.js v22 이상 설치 필요")

    npx_ok = shutil.which("npx") is not None
    print(f"[4] npx             : {'OK' if npx_ok else 'FAIL'}")
    if not npx_ok:
        issues.append("npx 명령 사용 불가 (Node.js 설치 확인)")

    android_home = _detect_android_home()
    print(f"[5] ANDROID_HOME    : {android_home or 'NOT FOUND'}")
    if not android_home:
        issues.append("ANDROID_HOME 환경변수 미설정 (Android SDK 위치)")

    apk_path = _find_apk()
    print(f"[6] APK             : {apk_path or 'NOT FOUND'}")
    if not apk_path:
        issues.append("apps/android/ 폴더에 .apk 파일 없음")

    host = os.getenv("APPIUM_HOST", "127.0.0.1")
    port = int(os.getenv("APPIUM_PORT", "4723"))
    appium_ok = _check_appium_running(host, port)
    print(f"[7] Appium 서버     : {'Running' if appium_ok else 'Not running'} ({host}:{port})")
    if not appium_ok:
        issues.append(f"Appium 서버 미실행 ({host}:{port}) — 'npx appium' 으로 시작")

    print()
    if issues:
        print(f"[!] 점검 결과 — 해결 필요 항목 {len(issues)}개:")
        for idx, item in enumerate(issues, start=1):
            print(f"    {idx}. {item}")
        return 1

    print("[OK] 모든 사전 조건 충족 — generate 모드로 다시 실행하세요.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Appium MCP capabilities.json 자동 생성"
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "tools" / "mcp" / "capabilities.json"),
        help="출력 파일 경로",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="사전 점검만 수행 (파일 생성 안 함)",
    )
    args = parser.parse_args()

    if args.verify:
        return verify()

    # 환경 점검 (verify 와 동일한 항목, 단 실패해도 일단 생성은 진행)
    print(f"[generate_capabilities] App = SauceLabs My Demo App ({ANDROID_PACKAGE})")

    apk_path = _find_apk()
    if not apk_path:
        print("[!] 경고: apps/android/ 에 .apk 파일이 없음 — appium:app 누락 상태로 생성")

    android_home = _detect_android_home()
    if not android_home:
        print("[!] 경고: ANDROID_HOME 미감지 — MCP 설정에서 직접 지정 필요")

    caps = build_capabilities()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(caps, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] 생성됨: {output_path}")
    print(f"[INFO] APK: {apk_path or '(미설정)'}")
    print(f"[INFO] ANDROID_HOME: {android_home or '(미감지)'}")
    print()
    print("다음 단계: docs/MCP_SETUP_GUIDE.md 의 [3. MCP 클라이언트 등록] 참조")

    return 0


if __name__ == "__main__":
    sys.exit(main())
