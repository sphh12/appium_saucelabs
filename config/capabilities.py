"""
Appium Desired Capabilities 설정
SauceLabs My Demo App (네이티브 Android) 기준 — Android / iOS 공통

환경변수 (.env 파일에서 설정):
  - APPIUM_HOST: Appium 서버 호스트 (기본: 127.0.0.1)
  - APPIUM_PORT: Appium 서버 포트 (기본: 4723)
  - ANDROID_UDID: 실물 디바이스 시리얼 (선택, adb devices로 확인)
  - ANDROID_DEVICE_NAME: 디바이스 이름 (선택, Allure 리포트 표시용)
  - ANDROID_PLATFORM_VERSION: Android OS 버전 (선택)
  - IOS_DEVICE_NAME: iOS 시뮬레이터 이름 (기본: iPhone 15)
  - IOS_PLATFORM_VERSION: iOS 버전 (기본: 17.0)
  - IOS_UDID: iOS 시뮬레이터 UUID (선택, 다중 시뮬 부팅 시 특정 시뮬 지정)

앱 파일 위치:
  - apps/android/*.apk   (여러 개면 이름순 마지막 파일 사용)
  - apps/ios/*.app|.ipa|.zip
"""
import os
from dotenv import load_dotenv

# 환경변수 로드 (.env 파일)
load_dotenv()

# 프로젝트 루트 경로 자동 계산
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 앱 식별 정보 (SauceLabs My Demo App) ──
APP_NAME = "saucelabs-mydemoapp"
ENV_TYPE = APP_NAME  # conftest.py 호환용 (Allure environment.properties에 기록)

# SauceLabs My Demo App (네이티브) 패키지/번들 정보
# 출처: https://github.com/saucelabs/my-demo-app-android (iOS: my-demo-app-ios)
ANDROID_PACKAGE = "com.saucelabs.mydemoapp.android"
ANDROID_ACTIVITY = "com.saucelabs.mydemoapp.android.view.activities.SplashActivity"
IOS_BUNDLE_ID = "com.saucelabs.mydemo.app.ios"

# ── 앱 파일 자동 탐색 ──
def _find_app_in_folder(platform: str) -> str:
    """플랫폼별 폴더에서 앱 파일을 자동 탐색

    Args:
        platform: "android" 또는 "ios"

    Returns:
        탐색된 앱 파일의 절대 경로 (없으면 빈 문자열)

    탐색 규칙:
        - android: apps/android/ 하위 .apk
        - ios:     apps/ios/ 하위 .app, .ipa, .zip
        - 여러 개면 이름순 마지막(최신) 파일 사용
    """
    if platform == "android":
        folder = os.path.join(PROJECT_ROOT, "apps", "android")
        extensions = (".apk",)
    elif platform == "ios":
        folder = os.path.join(PROJECT_ROOT, "apps", "ios")
        extensions = (".app", ".ipa", ".zip")
    else:
        return ""

    if os.path.isdir(folder):
        candidates = [f for f in os.listdir(folder) if f.endswith(extensions)]
        if candidates:
            return os.path.join(folder, sorted(candidates)[-1])
    return ""

ANDROID_APP_PATH = _find_app_in_folder("android")
IOS_APP_PATH = _find_app_in_folder("ios")

# ── Android 환경변수 ──
ANDROID_UDID = os.getenv("ANDROID_UDID")
ANDROID_DEVICE_NAME = os.getenv("ANDROID_DEVICE_NAME", "Android Emulator")
ANDROID_PLATFORM_VERSION = os.getenv("ANDROID_PLATFORM_VERSION")

# ── Android Capabilities ──
ANDROID_CAPS = {
    "platformName": "Android",
    "automationName": "UiAutomator2",
    "deviceName": ANDROID_DEVICE_NAME,
    "app": ANDROID_APP_PATH,
    "appPackage": ANDROID_PACKAGE,
    "appActivity": ANDROID_ACTIVITY,
    "noReset": False,
    "fullReset": False,
    "newCommandTimeout": 300,
    "autoGrantPermissions": True,
    "adbExecTimeout": 60000,                    # ADB 명령 타임아웃 60초
    "appWaitDuration": 60000,                   # 앱 시작 대기 60초
    "uiautomator2ServerLaunchTimeout": 60000,   # UiAutomator2 서버 시작 60초
}

# 실물 디바이스 연결 시 udid 추가
if ANDROID_UDID:
    ANDROID_CAPS["udid"] = ANDROID_UDID

if ANDROID_PLATFORM_VERSION:
    ANDROID_CAPS["platformVersion"] = ANDROID_PLATFORM_VERSION

# ── iOS Capabilities (Mac에서만 동작) ──
IOS_CAPS = {
    "platformName": "iOS",
    "automationName": "XCUITest",
    "deviceName": os.getenv("IOS_DEVICE_NAME", "iPhone 15"),
    "platformVersion": os.getenv("IOS_PLATFORM_VERSION", "17.0"),
    "app": IOS_APP_PATH,
    "bundleId": IOS_BUNDLE_ID,
    "noReset": False,
    "fullReset": False,
    "newCommandTimeout": 300,
    # WebDriverAgent 기동 대기. 첫 세션은 WDA를 빌드·설치하느라 오래 걸려
    # 기본값(60초)으로는 'connect ECONNREFUSED 127.0.0.1:8100'으로 첫 테스트만 실패한다
    # (CI 첫 런 실측: 9 passed / 1 error — 실패한 건 첫 테스트뿐이었다).
    # 새 머신·CI처럼 WDA 캐시가 없는 환경을 위해 넉넉히 두고 재시도도 준다.
    "wdaLaunchTimeout": int(os.getenv("IOS_WDA_LAUNCH_TIMEOUT", "240000")),
    "wdaStartupRetries": int(os.getenv("IOS_WDA_STARTUP_RETRIES", "2")),
    "wdaStartupRetryInterval": 20000,
}

# 특정 시뮬레이터를 udid로 지정 (예: 여러 시뮬 부팅 시). 미설정이면 deviceName+platformVersion으로 매칭
if os.getenv("IOS_UDID"):
    IOS_CAPS["udid"] = os.getenv("IOS_UDID")

# ── Appium 서버 ──
APPIUM_HOST = os.getenv("APPIUM_HOST", "127.0.0.1")
APPIUM_PORT = int(os.getenv("APPIUM_PORT", "4723"))

APPIUM_SERVER = {
    "host": APPIUM_HOST,
    "port": APPIUM_PORT,
}

def get_appium_server_url() -> str:
    """Appium 서버 URL 반환 (예: http://127.0.0.1:4723)"""
    return f"http://{APPIUM_SERVER['host']}:{APPIUM_SERVER['port']}"