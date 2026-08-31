"""
유틸리티 헬퍼 함수
"""
import json
import time
import os
from datetime import datetime


def wait(seconds: float):
    """지정된 시간 동안 대기"""
    time.sleep(seconds)


def get_timestamp() -> str:
    """현재 타임스탬프 반환"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_report_dir():
    """리포트 디렉토리 생성"""
    report_dir = "reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    return report_dir


def save_screenshot_with_timestamp(driver, prefix: str = "screenshot"):
    """타임스탬프가 포함된 스크린샷 저장"""
    create_report_dir()
    filename = f"reports/{prefix}_{get_timestamp()}.png"
    driver.save_screenshot(filename)
    return filename


def scroll_to_element(driver, locator, max_scrolls: int = 5):
    """요소가 나타날 때까지 스크롤"""
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.common.exceptions import NoSuchElementException

    for _ in range(max_scrolls):
        try:
            element = driver.find_element(*locator)
            if element.is_displayed():
                return element
        except NoSuchElementException:
            pass

        # 아래로 스와이프
        size = driver.get_window_size()
        start_x = size['width'] // 2
        start_y = int(size['height'] * 0.8)
        end_y = int(size['height'] * 0.2)
        driver.swipe(start_x, start_y, start_x, end_y, 800)

    raise NoSuchElementException(f"요소를 찾을 수 없습니다: {locator}")


def is_android(driver) -> bool:
    """드라이버 플랫폼이 Android인지 — capabilities['platformName']를 단일 진실원으로 판정.

    (테스트 경로 문자열/--platform 폴백 대신 실제 세션 capability 사용)
    """
    return str(driver.capabilities.get("platformName", "")).lower() == "android"


def get_device_info(driver) -> dict:
    """디바이스 정보 반환"""
    return {
        "platform": driver.capabilities.get("platformName"),
        "platform_version": driver.capabilities.get("platformVersion"),
        "device_name": driver.capabilities.get("deviceName"),
        "automation_name": driver.capabilities.get("automationName"),
    }


def save_error_logcat(driver, folder: str, name: str, tail_lines: int = 300) -> str | None:
    """에러/예외 발생 시 logcat을 파일로 저장합니다.

    Args:
        driver: Appium 드라이버
        folder: 저장할 폴더 경로
        name: 파일명 접두사 (예: "error_login_failed")
        tail_lines: 최근 N줄만 저장 (기본 300줄, 파일 크기 제한)

    Returns:
        저장된 파일 경로 (실패 시 None)
    """
    try:
        logs = driver.get_log("logcat")
        if not logs:
            return None

        # 최근 로그만 추출
        tail = logs[-tail_lines:] if len(logs) > tail_lines else logs
        log_text = "\n".join(json.dumps(entry, ensure_ascii=False) for entry in tail)

        os.makedirs(folder, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        filepath = os.path.join(folder, f"{name}_{timestamp}.logcat.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(log_text)

        size_kb = len(log_text.encode("utf-8")) // 1024
        print(f"  [logcat] {os.path.basename(filepath)} 저장 ({size_kb}KB, {len(tail)}줄)")
        return filepath
    except Exception as e:
        print(f"  [logcat] 저장 실패: {e}")
        return None


def save_error_snapshot(driver, folder: str, name: str) -> dict:
    """에러 발생 시 진단 파일 일괄 저장 (스크린샷 + XML + logcat).

    Args:
        driver: Appium 드라이버
        folder: 저장할 폴더 경로
        name: 파일명 접두사 (예: "error_login_failed")

    Returns:
        저장된 파일 경로 딕셔너리 {"screenshot": ..., "xml": ..., "logcat": ...}
    """
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    result = {}

    # 스크린샷
    try:
        screenshot_path = os.path.join(folder, f"{name}_{timestamp}.png")
        driver.save_screenshot(screenshot_path)
        print(f"  [snapshot] 스크린샷: {os.path.basename(screenshot_path)}")
        result["screenshot"] = screenshot_path
    except Exception:
        pass

    # XML (page_source + Activity 주석)
    try:
        xml = driver.page_source
        activity = driver.current_activity or "unknown"
        package = driver.current_package or "unknown"
        comment = f"<!-- Activity: {activity} | Package: {package} -->\n"
        if xml.startswith("<?xml"):
            decl_end = xml.index("?>") + 2
            xml = xml[:decl_end] + "\n" + comment + xml[decl_end:].lstrip("\n")
        else:
            xml = comment + xml
        xml_path = os.path.join(folder, f"{name}_{timestamp}.xml")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"  [snapshot] XML: {os.path.basename(xml_path)}")
        result["xml"] = xml_path
    except Exception:
        pass

    # Logcat
    logcat_path = save_error_logcat(driver, folder, name, tail_lines=300)
    if logcat_path:
        result["logcat"] = logcat_path

    return result
