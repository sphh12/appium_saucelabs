"""pytest conftest - 테스트 픽스처 및 설정"""
import base64
from datetime import datetime
import getpass
import json
import os
import platform as _platform
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException

from config.capabilities import ANDROID_CAPS, IOS_CAPS, get_appium_server_url, ENV_TYPE

try:
    import allure  # type: ignore
except Exception:  # pragma: no cover
    allure = None


def _get_any_driver(item):
    return (
        item.funcargs.get("driver")
        or item.funcargs.get("android_driver")
        or item.funcargs.get("ios_driver")
    )


def _safe_allure_attach(name: str, data: bytes, attachment_type):
    if allure is None:
        return
    try:
        allure.attach(data, name=name, attachment_type=attachment_type)
    except Exception:
        return


def _safe_run_git(args: list[str], cwd: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
        )
        return (proc.stdout or "").strip()
    except Exception:
        return ""


def _safe_get_ios_simulator_info() -> tuple[str, str]:
    """xcrun simctl을 통해 부팅된 iOS 시뮬레이터 정보 조회

    Returns:
        (디바이스명, iOS 버전) 튜플. 실패 시 ("", "")
        예: ("iPhone 17", "26.2")
    """
    try:
        proc = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "booted"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # 출력 형식: "-- iOS 26.2 --" 다음 줄에 "    iPhone 17 (UUID) (Booted)"
        ios_version = ""
        device_name = ""
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.startswith("-- iOS"):
                # "-- iOS 26.2 --" → "26.2"
                ios_version = line.replace("--", "").replace("iOS", "").strip()
            elif "(Booted)" in line:
                # "iPhone 17 (UUID) (Booted)" → "iPhone 17"
                device_name = line.split("(")[0].strip()
                break
        if device_name:
            return (f"{device_name} (Simulator)", ios_version)
    except Exception:
        pass
    return ("", "")


def _extract_test_script(config) -> str:
    """pytest 실행 인자에서 테스트 스크립트 파일명을 추출합니다."""
    import os
    for arg in (config.args or []):
        arg_str = str(arg)
        # :: 이전 부분 (파일 경로만)
        file_part = arg_str.split("::")[0]
        if file_part.endswith(".py"):
            return os.path.basename(file_part)
    return ""


def _safe_get_apk_info(apk_path: str) -> tuple[str, str]:
    """aapt로 APK에서 앱 이름과 버전을 추출합니다.

    Returns:
        (앱 이름, 앱 버전) 튜플. 실패 시 빈 문자열.
    """
    if not apk_path or not os.path.isfile(apk_path):
        return "", ""

    # aapt 경로 탐색 (build-tools 내 최신 버전)
    android_home = os.environ.get("ANDROID_HOME", "")
    aapt_path = ""
    if android_home:
        build_tools = os.path.join(android_home, "build-tools")
        if os.path.isdir(build_tools):
            versions = sorted(os.listdir(build_tools))
            for v in reversed(versions):
                candidate = os.path.join(build_tools, v, "aapt")
                if os.path.isfile(candidate):
                    aapt_path = candidate
                    break
    if not aapt_path:
        return "", ""

    try:
        proc = subprocess.run(
            [aapt_path, "dump", "badging", apk_path],
            capture_output=True, text=True, timeout=10,
        )
        output = proc.stdout or ""
        app_name = ""
        app_version = ""
        for line in output.splitlines():
            if line.startswith("application-label:"):
                # application-label:'My Demo App'
                app_name = line.split(":", 1)[1].strip().strip("'")
            if line.startswith("package:") and "versionName=" in line:
                # versionName='7.15.0'
                import re
                m = re.search(r"versionName='([^']+)'", line)
                if m:
                    app_version = m.group(1)
        return app_name, app_version
    except Exception:
        return "", ""


def _safe_get_ios_app_info(app_path: str) -> tuple[str, str]:
    """iOS .app 번들의 Info.plist에서 앱 이름과 버전을 추출합니다.

    Returns:
        (앱 이름, 앱 버전) 튜플. 실패 시 빈 문자열.
    """
    import plistlib

    if not app_path:
        return "", ""

    # .app 번들 경로에서 Info.plist 찾기
    app_dir = Path(app_path)
    if not app_dir.is_dir():
        return "", ""

    plist_path = app_dir / "Info.plist"
    if not plist_path.is_file():
        return "", ""

    try:
        with open(plist_path, "rb") as f:
            plist = plistlib.load(f)
        # 앱 이름: CFBundleDisplayName > CFBundleName
        app_name = plist.get("CFBundleDisplayName", "") or plist.get("CFBundleName", "")
        # 앱 버전: CFBundleShortVersionString
        app_version = plist.get("CFBundleShortVersionString", "")
        print(f"[DEBUG] iOS Info.plist → appName={app_name}, appVersion={app_version}")
        return app_name, app_version
    except Exception as e:
        print(f"[DEBUG] iOS Info.plist 파싱 실패: {e}")
        return "", ""


def _safe_get_android_platform_version() -> str:
    """adb를 통해 Android OS 버전 조회 (예: 14, 13)"""
    try:
        proc = subprocess.run(
            ["adb", "shell", "getprop", "ro.build.version.release"],
            check=True,
            capture_output=True,
            text=True,
        )
        return (proc.stdout or "").strip()
    except Exception:
        return ""


def _safe_get_android_device_model(max_retries: int = 3, retry_delay: float = 1.0) -> str:
    """adb를 통해 디바이스 모델명 조회

    조회 우선순위:
    1. ro.boot.qemu.avd_name - 에뮬레이터 AVD 이름 (예: Pixel_6_API_34)
    2. ro.product.model - 실물 디바이스 모델명 (예: Pixel 6, Galaxy S21)

    반환 형식: "Pixel_6 (Emulator)" 또는 "Pixel 6 (Device)"

    Args:
        max_retries: adb 연결 실패 시 재시도 횟수
        retry_delay: 재시도 간 대기 시간(초)
    """
    for attempt in range(max_retries):
        # 1) 에뮬레이터: AVD 이름 조회
        try:
            proc = subprocess.run(
                ["adb", "shell", "getprop", "ro.boot.qemu.avd_name"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            avd_name = (proc.stdout or "").strip()
            if avd_name:
                return f"{avd_name} (Emulator)"
        except Exception:
            pass

        # 2) 실물 디바이스: 모델명 조회
        try:
            proc = subprocess.run(
                ["adb", "shell", "getprop", "ro.product.model"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            model = (proc.stdout or "").strip()
            if model:
                return f"{model} (Device)"
        except Exception:
            pass

        # 재시도 전 대기
        if attempt < max_retries - 1:
            time.sleep(retry_delay)

    return ""


def _write_executor_json(results_path: Path, build_name: str) -> None:
    executor = {
        # OS 사용자명은 기록하지 않는다(리포트 공유 시 노출 방지) — EXECUTOR_NAME으로 덮어쓰기, 미설정 시 "local"
        "name": os.getenv("EXECUTOR_NAME") or "local",
        "type": "local",
        "buildName": build_name,
        "buildUrl": "",
        "reportName": "appium-mobile-test",
        "reportUrl": "",
    }
    (results_path / "executor.json").write_text(
        json.dumps(executor, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# ANR 대화상자 버튼 (android:id/aerr_* — 'aerr' = application error).
# 텍스트 매칭은 로케일마다 달라져 resource-id 를 우선한다.
_ANR_BUTTONS = (
    # 'Close app' 우선 — Launcher 가 멈춘 경우 Wait 로는 해소되지 않고 대화상자가 계속 남는다.
    (AppiumBy.ID, "android:id/aerr_close"),
    (AppiumBy.ID, "android:id/aerr_wait"),
    (AppiumBy.XPATH, "//android.widget.Button[@text='Close app' or @text='Wait' or @text='앱 닫기' or @text='기다리기' or @text='대기']"),
)


def _dismiss_system_ui_dialog(driver, max_attempts=3, wait_after_dismiss=2):
    """ANR('...isn't responding') 시스템 대화상자가 떠 있으면 닫는다.

    이 대화상자는 앱 위를 덮기 때문에 방치하면 이후 모든 요소 탐색이 실패한다.
    CI 에서는 `settings put global hide_error_dialogs 1` 로 애초에 뜨지 않게 하고,
    이 함수는 그 뒤에 남는 방어선이다(로컬·이미 떠 있는 경우 대비).

    Args:
        driver: Appium 드라이버
        max_attempts: 최대 시도 횟수
        wait_after_dismiss: 팝업 닫은 후 대기 시간(초)
    """
    for attempt in range(max_attempts):
        dismissed = False
        try:
            driver.implicitly_wait(2)  # 팝업 확인용 짧은 대기
            for by, value in _ANR_BUTTONS:
                try:
                    driver.find_element(by=by, value=value).click()
                    print(f"[INFO] ANR 대화상자 닫음 (attempt {attempt + 1}, {value})")
                    dismissed = True
                    break
                except Exception:
                    continue
        finally:
            driver.implicitly_wait(0)  # explicit-wait 우선 (implicit와 혼용 시 타임아웃 꼬임 방지)

        if not dismissed:
            break  # 팝업 없음 = 정상
        time.sleep(wait_after_dismiss)  # 시스템 안정화 대기 후 재확인


def pytest_addoption(parser):
    """커맨드라인 옵션 추가"""
    parser.addoption(
        "--platform",
        action="store",
        default="",
        help="테스트 플랫폼: android 또는 ios (미지정 시 테스트 경로에서 자동 감지)"
    )
    parser.addoption(
        "--app",
        action="store",
        default="",
        help="앱 파일 경로 (.apk 또는 .ipa/.app)"
    )

    parser.addoption(
        "--record-video",
        action="store_true",
        default=True,
        help="테스트 화면녹화(mp4) — 기본 ON. 성공은 첨부하지 않고 폐기, 실패/스킵/broken만 Allure 첨부",
    )
    parser.addoption(
        "--no-record-video",
        dest="record_video",
        action="store_false",
        help="화면 녹화 끄기 (기본은 ON)",
    )

    parser.addoption(
        "--allure-attach",
        action="store",
        default="hybrid",
        choices=["hybrid", "all", "fail-skip"],
        help=(
            "Allure 첨부 정책: hybrid(기본, FAIL/SKIP/BROKEN만 첨부), "
            "all(성공 포함 전체 첨부). fail-skip은 이전 값 호환용"
        ),
    )


def _is_ios_path(path_like) -> bool:
    """경로가 `tests/ios` 아래를 가리키는지 — iOS 판정의 단일 기준.

    단순 부분문자열('ios' 포함) 매칭은 저장소가 `~/work/ios/...` 아래 있거나
    폴더명이 `login-ios-flow`인 경우까지 iOS로 오판한다(Android 실행이 조용히
    XCUITest로 새거나 logcat 첨부가 누락됨). 경로 세그먼트에 고정한다.
    """
    norm = str(path_like).lower().replace("\\", "/")
    return bool(re.search(r"(^|/)tests/ios(/|$|::)", norm))


def _resolve_platform(config) -> str:
    """--platform 값을 반환하되, 미지정 시 테스트 경로에서 자동 감지(최종 폴백 android).

    pytest_configure(메타데이터)와 platform 픽스처(실제 드라이버 생성)가 동일한
    결과를 쓰도록 단일화 — '자동 감지가 메타에만 반영되고 픽스처는 ValueError' 이슈 방지.
    """
    name = (config.getoption("platform") or "").lower()
    if name:
        return name
    return "ios" if any(_is_ios_path(arg) for arg in (config.args or [])) else "android"


def pytest_configure(config):
    """설정 수집만 수행. 파일 쓰기는 pytest_sessionstart에서 실행.
    (--clean-alluredir이 폴더를 삭제한 뒤에 파일을 써야 하므로)
    """
    try:
        results_dir = config.getoption("allure_report_dir")
    except Exception:
        results_dir = None
    results_dir = results_dir or "allure-results"

    platform_name = _resolve_platform(config)
    app_path = config.getoption("app") or ""
    record_video = bool(config.getoption("record_video"))
    allure_attach = str(config.getoption("allure_attach") or "hybrid")
    if allure_attach == "fail-skip":
        allure_attach = "hybrid"

    caps = ANDROID_CAPS if platform_name == "android" else IOS_CAPS
    effective_app = app_path or str(caps.get("app", ""))

    # 앱 이름/버전 추출 (플랫폼별 분기)
    if platform_name == "ios":
        app_name, app_version = _safe_get_ios_app_info(effective_app)
    else:
        app_name, app_version = _safe_get_apk_info(effective_app)

    platform_version = str(caps.get("platformVersion", "") or "").strip()
    if not platform_version and platform_name == "android":
        platform_version = _safe_get_android_platform_version()
    # OS 버전에 플랫폼명 접두사 추가 (예: "14" → "Android 14")
    if platform_version:
        if platform_name == "android" and not platform_version.lower().startswith("android"):
            platform_version = f"Android {platform_version}"
        elif platform_name == "ios" and not platform_version.lower().startswith("ios"):
            platform_version = f"iOS {platform_version}"

    # deviceName: 환경변수 > adb/simctl 동적 조회 > 기본값
    device_name = str(caps.get("deviceName", "") or "").strip()
    if platform_name == "android" and (not device_name or device_name == "Android Emulator"):
        adb_model = _safe_get_android_device_model()
        if adb_model:
            device_name = adb_model
    elif platform_name == "ios":
        sim_name, sim_version = _safe_get_ios_simulator_info()
        if sim_name:
            device_name = sim_name
        if sim_version and not platform_version:
            platform_version = f"iOS {sim_version}"
    if not device_name:
        device_name = caps.get("deviceName", "Unknown")

    repo_root = Path(getattr(config, "rootpath", Path.cwd()))
    git_branch = _safe_run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    git_commit = _safe_run_git(["rev-parse", "--short", "HEAD"], cwd=repo_root)
    git_message = _safe_run_git(["log", "-1", "--pretty=%s"], cwd=repo_root)
    build_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}|{platform_name}" + (
        f"|{git_branch}@{git_commit}" if (git_branch or git_commit) else ""
    )

    # config에 메타정보 저장 (pytest_sessionstart에서 파일로 기록)
    config._allure_meta = {
        "results_dir": results_dir,
        "build_name": build_name,
        "env_lines": [
            f"platform={platform_name}",
            f"deviceName={device_name}",
            f"platformVersion={platform_version}",
            f"automationName={caps.get('automationName', '')}",
            f"app={Path(str(effective_app)).name}",
            f"appName={app_name}",
            f"appVersion={app_version}",
            f"appEnv={ENV_TYPE}",
            f"testScript={_extract_test_script(config)}",
            f"appiumServer={get_appium_server_url()}",
            f"recordVideo={record_video}",
            f"allureAttach={allure_attach}",
            f"os={_platform.platform()}",
            f"python={sys.version.split()[0]}",
            f"gitBranch={git_branch}",
            f"gitCommit={git_commit}",
            f"gitMessage={git_message}",
        ],
        "categories": [
            {
                "name": "Appium 서버 연결 실패",
                "matchedStatuses": ["broken", "failed"],
                "traceRegex": ".*(ConnectionRefusedError|WinError 10061|MaxRetryError|Failed to establish a new connection).*",
            },
            {
                "name": "UI 동기화/대기 타임아웃",
                "matchedStatuses": ["broken", "failed"],
                "traceRegex": ".*(TimeoutException|Timed out|WebDriverWait).*",
            },
            {
                "name": "요소 탐색 실패",
                "matchedStatuses": ["broken", "failed"],
                "traceRegex": ".*(NoSuchElementException|Unable to locate element).*",
            },
            {
                "name": "Stale element",
                "matchedStatuses": ["broken", "failed"],
                "traceRegex": ".*(StaleElementReferenceException|StaleObjectException).*",
            },
        ],
    }


def pytest_sessionstart(session):
    """allure-pytest의 --clean-alluredir 처리가 완료된 후 메타파일을 생성합니다."""
    meta = getattr(session.config, "_allure_meta", None)
    if not meta:
        return

    results_path = Path(meta["results_dir"])
    results_path.mkdir(parents=True, exist_ok=True)

    # environment.properties
    (results_path / "environment.properties").write_text(
        "\n".join(meta["env_lines"]) + "\n",
        encoding="utf-8",
    )

    # executor.json
    _write_executor_json(results_path, meta["build_name"])

    # categories.json
    (results_path / "categories.json").write_text(
        json.dumps(meta["categories"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    # 실패/스킵은 setup 단계에서도 발생할 수 있어 캡처 범위를 넓힘
    if report.when not in ("setup", "call", "teardown"):
        return

    driver = _get_any_driver(item)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    attach_mode = str(item.config.getoption("allure_attach") or "hybrid")
    if attach_mode == "fail-skip":
        attach_mode = "hybrid"
    attach_all = attach_mode == "all"

    # 전체 단계(setup/call/teardown) 중 한 번이라도 실패/스킵이면 기록
    if report.failed:
        item._allure_any_failed = True
    if report.skipped:
        item._allure_any_skipped = True

    # 스크린샷: hybrid는 FAIL/SKIP/BROKEN(대부분 setup/teardown 실패=report.failed)에만,
    # all 모드에선 PASS도(call 단계에서) 첨부.
    # outcome이 "passed"가 아닌 모든 경우 (failed, skipped, broken 포함)
    is_problematic = report.outcome != "passed"
    want_screenshot = is_problematic or (attach_all and report.when == "call")

    # 부가 진단(page source/caps/logcat):
    # - hybrid: FAIL/SKIP/BROKEN (outcome != "passed")
    # - all 모드: PASS도 포함 (call 단계에서)
    want_diagnostics = is_problematic or (attach_all and report.when == "call")

    if want_screenshot and not getattr(item, "_allure_screen_attached", False):
        if driver:
            try:
                png = driver.get_screenshot_as_png()
                status = (
                    "failed"
                    if report.failed
                    else "skipped"
                    if report.skipped
                    else "passed"
                    if report.passed
                    else report.outcome
                )
                phase = report.when
                _safe_allure_attach(
                    name=f"screenshot_{status}_{phase}_{item.name}_{timestamp}.png",
                    data=png,
                    attachment_type=getattr(allure.attachment_type, "PNG", None),
                )
                item._allure_screen_attached = True
            except Exception:
                pass

    if want_diagnostics and driver and not getattr(item, "_allure_diag_attached", False):
        item._allure_diag_attached = True

        try:
            source = getattr(driver, "page_source", "")
            if source:
                _safe_allure_attach(
                    name=f"page_source_{item.name}_{timestamp}.xml",
                    data=source.encode("utf-8", errors="replace"),
                    attachment_type=getattr(allure.attachment_type, "XML", None)
                    or getattr(allure.attachment_type, "TEXT", None),
                )
        except Exception:
            pass

        try:
            caps = getattr(driver, "capabilities", None)
            if caps:
                _safe_allure_attach(
                    name=f"capabilities_{item.name}_{timestamp}.json",
                    data=json.dumps(caps, ensure_ascii=False, indent=2).encode("utf-8"),
                    attachment_type=getattr(allure.attachment_type, "JSON", None)
                    or getattr(allure.attachment_type, "TEXT", None),
                )
        except Exception:
            pass

        try:
            platform_name = (item.config.getoption("platform") or "").lower()
            # logcat은 Android에서만 수집. 테스트 파일 경로로 판정하므로 혼합 실행에서도
            # 케이스별로 맞고, 판정 기준은 _is_ios_path로 통일(경로 부분문자열 오판 방지).
            if platform_name != "ios" and not _is_ios_path(item.fspath):
                logs = driver.get_log("logcat")
                if logs:
                    # 너무 커질 수 있어 최근 일부만 첨부
                    tail = logs[-300:] if len(logs) > 300 else logs
                    log_text = "\n".join(json.dumps(entry, ensure_ascii=False) for entry in tail)
                    _safe_allure_attach(
                        name=f"logcat_{item.name}_{timestamp}.txt",
                        data=log_text.encode("utf-8", errors="replace"),
                        attachment_type=getattr(allure.attachment_type, "TEXT", None),
                    )
        except Exception:
            pass

    # 비디오: fixture teardown에서 stop_recording_screen() 결과를 저장해두고,
    # 여기서 상태에 따라 Allure에 첨부한다 (driver가 이미 quit 되어도 첨부 가능).
    record_video = bool(item.config.getoption("record_video"))
    video_bytes = getattr(item, "_recorded_video_bytes", None)
    if record_video and video_bytes and not getattr(item, "_allure_video_attached", False):
        if report.when == "teardown":
            any_failed = bool(getattr(item, "_allure_any_failed", False))
            any_skipped = bool(getattr(item, "_allure_any_skipped", False))
            if attach_all or any_failed or any_skipped:
                try:
                    stop_ts = getattr(item, "_video_stop_timestamp", timestamp)
                    status = "failed" if any_failed else "skipped" if any_skipped else "passed"
                    _safe_allure_attach(
                        name=f"video_{status}_teardown_{item.name}_{stop_ts}.mp4",
                        data=video_bytes,
                        attachment_type=getattr(allure.attachment_type, "MP4", None),
                    )
                    item._allure_video_attached = True
                except Exception:
                    pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    try:
        results_dir = config.getoption("allure_report_dir")
    except Exception:
        results_dir = None
    results_dir = results_dir or "allure-results"
    terminalreporter.write_sep("=", "Allure report")
    terminalreporter.write_line(f"Generate: allure generate {results_dir} -o allure-report --clean")
    terminalreporter.write_line(f"Serve   : allure serve {results_dir}")
    terminalreporter.write_line("Open    : allure open allure-report")


def _finalize_video(request, driver):
    """녹화 종료 + 조건부 회수 (성공 케이스 최적화).

    성공 테스트는 stop_recording_screen() 호출 자체를 건너뛴다 → 영상 전송·base64 디코딩 0.
    디바이스 측 녹화는 이어지는 driver.quit()(세션 종료) 시 정리된다.
    실패/스킵/broken (또는 --allure-attach=all)일 때만 영상을 회수·디코딩해 둔다.

    동작 근거: pytest 실행 순서가 'call 단계 makereport → fixture teardown' 이라,
    이 시점엔 본문 성공/실패가 이미 확정(_allure_any_failed/_allure_any_skipped 설정 완료)돼 있다.
    """
    node = request.node
    if not request.config.getoption("--record-video"):
        return
    if not getattr(node, "_video_recording_started", False):
        return
    if getattr(node, "_video_recording_stopped", False):
        return
    node._video_recording_stopped = True

    attach_all = str(request.config.getoption("allure_attach") or "hybrid") == "all"
    keep = (
        attach_all
        or getattr(node, "_allure_any_failed", False)
        or getattr(node, "_allure_any_skipped", False)
    )
    # 디버깅용: 영상 보존/스킵 결정 출력 (-s 또는 실패 시 캡처 출력에 표시)
    print(f"[video] {node.name}: {'keep(fail/skip)' if keep else 'skip(passed)'}")
    if not keep:
        return  # 성공 → 회수/디코딩 스킵 (driver.quit()이 디바이스 녹화 정리)

    try:
        video_b64 = driver.stop_recording_screen()
        node._video_stop_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if video_b64:
            node._recorded_video_bytes = base64.b64decode(video_b64)
    except Exception:
        pass


_PREFLIGHT_DONE: set[str] = set()   # 플랫폼별 1회 — 단일 bool이면 혼합 실행 시 뒤 플랫폼 점검이 통째로 스킵됨
_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "0.0.0.0"}


def _preflight_check(platform_name: str) -> None:
    """첫 드라이버 생성 전 (플랫폼별) 1회: Appium 서버·디바이스 상태 점검, 실패 시 전체 중단.

    2026-08-24 사고 재발 방지 — 잔존(반쯤 죽은) Appium·adb 상태 불일치로 세션 생성이
    테스트당 20초씩 연쇄 에러(17건, 총 5:50). 사전에 걸러 명확한 처방과 함께 즉시 끝낸다.
    점검이 오히려 정상 환경을 막지 않도록, 확실한 이상(서버 무응답·프록시 가로채기·
    adb 비-0 종료·디바이스 0대)만 중단 사유로 삼고, 판단이 불확실한 경우(로컬 adb가
    PATH에 없음·원격 Appium 서버)는 경고만 남기고 진행한다.
    """
    if platform_name in _PREFLIGHT_DONE:
        return

    # 1) Appium 서버 /status 응답 확인 — 프록시를 우회한 프로브로 '서버 자체의 생존'을 먼저 판정
    #    (프록시 설정이 섞이면 서버가 정상인데도 무응답으로 오판하게 된다)
    status_url = get_appium_server_url().rstrip("/") + "/status"
    parsed = urllib.parse.urlparse(get_appium_server_url())
    host = parsed.hostname or ""
    # 프록시 우회 판정에는 포트까지 포함한 host:port를 넘긴다 — 포트 없이 호스트만 주면
    # `NO_PROXY=127.0.0.1:4723`처럼 포트가 붙은 항목이 매칭되지 않아(포트 불일치로 스킵)
    # 정상 설정을 오탐하고 전체 실행을 막는다.
    host_port = f"{host}:{parsed.port}" if parsed.port else host
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(status_url, timeout=5):
            pass
    except Exception as exc:
        pytest.exit(
            f"[preflight] Appium 서버 응답 없음 ({status_url}): {exc}\n"
            "  → 서버 기동: npx appium (기존 프로세스가 있다면 종료 후 재기동)",
            returncode=1,
        )

    # 서버는 살아있다 → 프록시 설정이 실제 세션 연결까지 가로채는지 점검.
    # selenium(urllib3)은 HTTP_PROXY를 따르므로, no_proxy에 서버 호스트가 없으면
    # localhost 요청이 프록시로 새어 세션 생성이 전부 실패한다(실측 확인).
    # 판단 기준을 '환경변수'로 한정 — getproxies()는 Windows 레지스트리·macOS 시스템
    # 프록시까지 읽지만 urllib3는 그것들을 무시하므로, 넓게 보면 정상 환경을 오탐한다.
    env_proxies = urllib.request.getproxies_environment()
    if env_proxies.get("http") and host and not urllib.request.proxy_bypass_environment(host_port):
        pytest.exit(
            f"[preflight] Appium 서버는 응답하는데 HTTP 프록시({env_proxies['http']})가 "
            f"{host} 요청까지 가로채는 설정 — selenium 연결이 프록시로 새서 전부 실패한다.\n"
            f"  → NO_PROXY(no_proxy)에 {host},localhost 추가 후 재실행",
            returncode=1,
        )

    # 2) Android: adb에 'device' 상태 디바이스가 최소 1개 있는지 확인
    #    (원격 Appium 서버면 디바이스는 그 서버 쪽 adb가 관리하므로 로컬 점검은 무의미)
    if platform_name == "android" and host in _LOCAL_HOSTS:
        try:
            result = subprocess.run(
                ["adb", "devices"], capture_output=True, text=True, timeout=10
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            # Appium 서버는 자기 PATH의 adb를 쓰므로, 여기서 adb가 안 보인다고 실패는 아니다.
            # (IDE 실행 등) → 경고만 남기고 진행, 실제 문제면 아래 fail-fast가 잡는다.
            print(f"[preflight] adb 확인 건너뜀 (adb 실행 불가: {exc}) — 디바이스 점검 없이 진행")
            _PREFLIGHT_DONE.add(platform_name)
            return
        if result.returncode != 0:
            # 버전 불일치·데몬 연결 실패 등 — '디바이스 없음'으로 오진하지 않도록 원문 노출
            pytest.exit(
                f"[preflight] adb 오류 (exit {result.returncode}): "
                f"{(result.stderr or result.stdout or '').strip()}\n"
                "  → adb kill-server && adb start-server (버전 불일치면 SDK platform-tools 정리)",
                returncode=1,
            )
        devices = [
            line for line in result.stdout.strip().splitlines()[1:]
            if line.strip().endswith("device")
        ]
        if not devices:
            pytest.exit(
                "[preflight] adb에 연결된 디바이스 없음 — 에뮬레이터 부팅(emulator -avd <이름>) "
                "또는 실기기 연결 후 재실행\n"
                "  (offline 상태면: adb kill-server && adb start-server)",
                returncode=1,
            )

    print(f"[preflight] OK ({platform_name}) — Appium {status_url} 응답, 디바이스 확인 완료")
    _PREFLIGHT_DONE.add(platform_name)


def _create_driver(request, platform_name: str):
    """플랫폼별 Appium 드라이버 생성 + 초기화(implicit wait 0 · System UI · 녹화 시작).

    driver/android_driver/ios_driver 세 픽스처의 공통 라이프사이클을 단일화한다.
    생성 이후 초기화 단계에서 예외가 나면 만들어둔 세션을 즉시 정리하고 재전파(누수 방지).
    """
    app_path = request.config.getoption("--app")
    if platform_name == "android":
        caps = ANDROID_CAPS.copy()
        if app_path:
            caps["app"] = app_path
        options = UiAutomator2Options().load_capabilities(caps)
    elif platform_name == "ios":
        caps = IOS_CAPS.copy()
        if app_path:
            caps["app"] = app_path
        options = XCUITestOptions().load_capabilities(caps)
    else:
        raise ValueError(f"지원하지 않는 플랫폼: {platform_name}")

    _preflight_check(platform_name)

    try:
        driver = webdriver.Remote(command_executor=get_appium_server_url(), options=options)
    except WebDriverException as exc:
        # 디바이스 탐색 실패는 이 테스트만의 문제가 아니라 환경 문제 — 나머지 테스트도
        # 전부 같은 이유로 20초씩 실패하므로 연쇄를 끊고 처방과 함께 즉시 중단(fail-fast)
        if "Could not find a connected" in str(exc):
            pytest.exit(
                "[fail-fast] Appium이 디바이스를 찾지 못해 세션 생성 실패 — "
                "잔존 Appium·adb 상태 불일치 의심.\n"
                "  → Appium 프로세스 종료 + adb kill-server && adb start-server 후 "
                "Appium 재기동 (docs/SETUP_GUIDE.md §7.1)\n"
                f"  원인: {str(exc).splitlines()[0]}",
                returncode=1,
            )
        raise
    try:
        driver.implicitly_wait(0)  # explicit-wait 우선 (implicit와 혼용 시 타임아웃 꼬임 방지)
        # Android는 부팅 직후 System UI 팝업이 뜰 수 있어 처리
        if platform_name == "android":
            _dismiss_system_ui_dialog(driver)
        if request.config.getoption("--record-video"):
            try:
                driver.start_recording_screen()
                request.node._video_recording_started = True
            except Exception:
                request.node._video_recording_started = False
    except Exception:
        try:
            driver.quit()
        except Exception:
            pass
        raise
    return driver


def _teardown_driver(request, driver):
    """녹화 회수(조건부) + 세션 종료. quit 실패가 다음 테스트를 오염시키지 않도록 방어."""
    try:
        _finalize_video(request, driver)
    finally:
        try:
            driver.quit()
        except Exception as exc:
            print(f"[teardown] driver.quit() 무시: {exc}")


@pytest.fixture(scope="session")
def platform(request):
    """현재 테스트 플랫폼 반환 (--platform 미지정 시 경로 기반 자동 감지, 최종 폴백 android)."""
    return _resolve_platform(request.config)


@pytest.fixture(scope="function")
def driver(request, platform):
    """Appium 드라이버 (플랫폼 자동 감지). 생성/정리는 _create_driver/_teardown_driver로 단일화."""
    drv = _create_driver(request, platform)
    try:
        yield drv
    finally:
        _teardown_driver(request, drv)


@pytest.fixture(scope="function")
def android_driver(request):
    """Android 전용 드라이버."""
    drv = _create_driver(request, "android")
    try:
        yield drv
    finally:
        _teardown_driver(request, drv)


@pytest.fixture(scope="function")
def ios_driver(request):
    """iOS 전용 드라이버."""
    drv = _create_driver(request, "ios")
    try:
        yield drv
    finally:
        _teardown_driver(request, drv)
