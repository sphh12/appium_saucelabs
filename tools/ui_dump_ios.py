"""
iOS UI 요소 덤프 스크립트
현재 화면의 UI 요소를 XML 파일로 저장합니다.

사용법:
    python tools/ui_dump_ios.py [이름]

예시:
    python tools/ui_dump_ios.py login_screen
    python tools/ui_dump_ios.py home
    python tools/ui_dump_ios.py -i               # 인터랙티브 모드
    python tools/ui_dump_ios.py -w               # 자동 감지 모드

참고:
    - 저장 시 민감 정보(전화번호, 이메일, 생년월일)가 자동으로 마스킹됩니다.
    - iOS 시뮬레이터 또는 실기기가 연결되어 있어야 합니다.
"""

import os
import sys
import shutil
import hashlib
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from appium import webdriver
from appium.options.ios import XCUITestOptions

# 프로젝트 루트 경로
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.capabilities import IOS_CAPS, get_appium_server_url


# =============================================================================
# 민감 정보 마스킹 기능 (Android 버전과 동일)
# =============================================================================

def _mask_sensitive_data(xml_content: str) -> str:
    """
    XML 내용에서 민감한 개인정보를 마스킹합니다.

    마스킹 대상:
    - 전화번호 (한국 형식)
    - 이메일 주소
    - 생년월일 (YYYY-MM-DD, YYYYMMDD 형식)
    """
    masked = xml_content

    # 1. 전화번호 마스킹
    phone_patterns = [
        (r'(\d{2,3})-(\d{3,4})-(\d{4})', r'\1-****-****'),
        (r'(\d{2,3})\s(\d{3,4})\s(\d{4})', r'\1-****-****'),
        (r'(?<!\d)(01[0-9])(\d{3,4})(\d{4})(?!\d)', r'\1********'),
        (r'(?<!\d)(0[2-6][0-9]?)(\d{3,4})(\d{4})(?!\d)', r'\1*******'),
    ]
    for pattern, replacement in phone_patterns:
        masked = re.sub(pattern, replacement, masked)

    # 2. 이메일 마스킹
    def mask_email(match):
        email = match.group(0)
        local, domain = email.split('@')
        domain_parts = domain.split('.')
        masked_local = local[0] + '***' if len(local) > 1 else '***'
        masked_domain = domain_parts[0][0] + '***' if len(domain_parts[0]) > 1 else '***'
        return f"{masked_local}@{masked_domain}.{'.'.join(domain_parts[1:])}"

    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    masked = re.sub(email_pattern, mask_email, masked)

    # 3. 생년월일 마스킹 (YYYY-MM-DD)
    date_pattern = r'(?<!\d)(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])(?!\d)'
    masked = re.sub(date_pattern, '****-**-**', masked)

    # 4. 생년월일 마스킹 (YYYYMMDD)
    date_pattern2 = r'(?<!\d)(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)'
    masked = re.sub(date_pattern2, '********', masked)

    return masked


def _save_xml_with_masking(filepath: str, content: str) -> None:
    """XML 파일을 마스킹하여 저장합니다."""
    masked_content = _mask_sensitive_data(content)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(masked_content)


# =============================================================================
# 유틸리티 함수
# =============================================================================

def _ensure_unique_dir(path: str) -> str:
    """중복되지 않는 디렉토리 경로를 반환합니다."""
    if not os.path.exists(path):
        return path
    idx = 1
    while True:
        candidate = f"{path}_{idx}"
        if not os.path.exists(candidate):
            return candidate
        idx += 1


def _finalize_session_dir(session_tmp_dir: str, output_root: str, timestamp_format: str = "%Y%m%d_%H%M%S") -> str | None:
    """세션 임시 폴더를 ios_ 프리픽스 + 종료시간 기반 폴더명으로 변경합니다."""
    if not session_tmp_dir or not os.path.isdir(session_tmp_dir):
        return None

    end_timestamp = datetime.now().strftime(timestamp_format)
    final_dir = _ensure_unique_dir(os.path.join(output_root, f"ios_{end_timestamp}"))

    try:
        os.rename(session_tmp_dir, final_dir)
    except Exception:
        try:
            shutil.move(session_tmp_dir, final_dir)
        except Exception:
            return session_tmp_dir

    return final_dir


def _sanitize_filename(name: str) -> str:
    """파일명에 사용할 수 없는 문자를 제거합니다."""
    name = name.replace(" ", "_")
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name[:30] if len(name) > 30 else name


# =============================================================================
# iOS 전용: 요소 분석 함수
# =============================================================================

# 클릭/입력 가능한 iOS 요소 타입
IOS_INTERACTIVE_TYPES = {
    "XCUIElementTypeButton",
    "XCUIElementTypeTextField",
    "XCUIElementTypeSecureTextField",
    "XCUIElementTypeSearchField",
    "XCUIElementTypeSwitch",
    "XCUIElementTypeSlider",
    "XCUIElementTypeStepper",
    "XCUIElementTypeIcon",
    "XCUIElementTypeLink",
    "XCUIElementTypeCell",
    "XCUIElementTypeSegmentedControl",
    "XCUIElementTypePicker",
    "XCUIElementTypeDatePicker",
    "XCUIElementTypeTab",
    "XCUIElementTypeToggle",
}


def _get_ios_element_stats(page_source: str) -> dict:
    """
    iOS XML에서 요소 통계를 추출합니다.

    Returns:
        {"total": 전체 요소 수, "interactive": 상호작용 가능 요소 수}
    """
    try:
        root = ET.fromstring(page_source)
        total = len(list(root.iter()))
        interactive = 0
        for elem in root.iter():
            elem_type = elem.get("type", "") or elem.tag
            if elem_type in IOS_INTERACTIVE_TYPES:
                interactive += 1
        return {"total": total, "interactive": interactive}
    except Exception:
        return {"total": 0, "interactive": 0}


def _extract_screen_name(driver, page_source: str) -> str:
    """
    iOS 화면 이름을 추출합니다.

    우선순위:
    1. NavigationBar의 name/label 속성
    2. 첫 번째 StaticText의 label (제목으로 추정)
    3. "unknown"
    """
    try:
        root = ET.fromstring(page_source)

        # 1. NavigationBar에서 타이틀 찾기
        for elem in root.iter():
            elem_type = elem.get("type", "") or elem.tag
            if "NavigationBar" in elem_type:
                name = elem.get("name", "").strip()
                if name:
                    return _sanitize_filename(name)

        # 2. NavigationBar 내부 StaticText에서 찾기
        for elem in root.iter():
            elem_type = elem.get("type", "") or elem.tag
            if "NavigationBar" in elem_type:
                for child in elem.iter():
                    child_type = child.get("type", "") or child.tag
                    if "StaticText" in child_type:
                        label = child.get("label", "").strip() or child.get("name", "").strip()
                        if label and len(label) < 50:
                            return _sanitize_filename(label)

        # 3. 첫 번째 의미있는 StaticText
        for elem in root.iter():
            elem_type = elem.get("type", "") or elem.tag
            if "StaticText" in elem_type:
                label = elem.get("label", "").strip() or elem.get("name", "").strip()
                if label and 2 < len(label) < 30 and not label.startswith("http"):
                    return _sanitize_filename(label)

    except Exception:
        pass

    return "unknown"


def _get_screen_hash(page_source: str) -> str:
    """화면 내용의 해시를 생성합니다 (변화 감지용)."""
    try:
        root = ET.fromstring(page_source)
        structure = []
        for elem in root.iter():
            # iOS: name, label 기반으로 구조 해시
            name = elem.get("name", "")
            label = elem.get("label", "")
            if name or label:
                structure.append(f"{name}:{label[:20]}")

        content = "|".join(structure[:50])
        return hashlib.md5(content.encode()).hexdigest()[:16]
    except Exception:
        return hashlib.md5(page_source.encode()).hexdigest()[:16]


# =============================================================================
# iOS 드라이버 연결
# =============================================================================

def _connect_ios_driver():
    """iOS 시뮬레이터/디바이스에 Appium으로 연결합니다."""
    caps = IOS_CAPS.copy()
    caps["noReset"] = True
    caps.pop("app", None)  # 앱 재설치 방지

    options = XCUITestOptions()
    for key, value in caps.items():
        if value:  # 빈 값 제외
            options.set_capability(key, value)

    print(f"[INFO] Appium 서버 연결 중... ({get_appium_server_url()})")

    try:
        driver = webdriver.Remote(
            command_executor=get_appium_server_url(),
            options=options
        )
        print("[INFO] iOS 연결 성공!")
        return driver
    except Exception as e:
        print(f"[ERROR] 연결 실패: {e}")
        print()
        print("확인사항:")
        print("  1. Appium 서버가 실행 중인지 확인 (appium --relaxed-security)")
        print("  2. iOS 시뮬레이터가 부팅되어 있는지 확인 (xcrun simctl list devices)")
        print("  3. XCUITest 드라이버가 설치되어 있는지 확인 (appium driver list --installed)")
        return None


# =============================================================================
# 모드별 실행 함수
# =============================================================================

def dump_ui(name: str = None):
    """현재 화면의 UI 요소를 XML 파일로 저장합니다."""
    output_dir = os.path.join(PROJECT_ROOT, "ui_dumps")
    os.makedirs(output_dir, exist_ok=True)

    # ios_ 프리픽스 + 타임스탬프 폴더 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(output_dir, f"ios_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)

    filename = f"{timestamp}_{name}.xml" if name else f"{timestamp}.xml"
    filepath = os.path.join(session_dir, filename)

    print("=" * 50)
    print("  iOS UI 요소 덤프 스크립트")
    print("=" * 50)
    print()

    driver = _connect_ios_driver()
    if not driver:
        return None

    try:
        print(f"[1/2] 화면 요소 추출 중...")
        page_source = driver.page_source

        print(f"[2/2] XML 파일 저장 중 (마스킹 적용)... ({filepath})")
        _save_xml_with_masking(filepath, page_source)

        print()
        print("=" * 50)
        print(f"  저장 완료: {filepath}")
        print("=" * 50)
        print()

        # iOS 요소 통계
        stats = _get_ios_element_stats(page_source)
        print(f"요소 통계:")
        print(f"  - 전체 요소: {stats['total']}개")
        print(f"  - 상호작용 가능 (버튼/입력 등): {stats['interactive']}개")
        print()

        return filepath

    except Exception as e:
        print(f"오류 발생: {e}")
        return None
    finally:
        driver.quit()


def interactive_mode():
    """인터랙티브 모드: Enter 키로 캡처, q로 종료"""
    print("=" * 50)
    print("  iOS UI 요소 덤프 - 인터랙티브 모드")
    print("=" * 50)
    print()
    print("  [Enter]  현재 화면 캡처")
    print("  [q]      종료")
    print()

    output_dir = os.path.join(PROJECT_ROOT, "ui_dumps")
    os.makedirs(output_dir, exist_ok=True)

    driver = _connect_ios_driver()
    if not driver:
        return

    # 세션 임시 폴더
    session_start = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_tmp_dir = _ensure_unique_dir(os.path.join(output_dir, f"_ios_running_{session_start}"))
    os.makedirs(session_tmp_dir, exist_ok=True)

    capture_count = 0
    print("-" * 50)
    print("준비 완료! 원하는 화면에서 Enter를 누르세요.")
    print("-" * 50)

    try:
        while True:
            user_input = input("\n[Enter=캡처, q=종료]: ").strip().lower()

            if user_input == 'q':
                print("\n종료합니다.")
                break

            capture_count += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{capture_count:03d}.xml"
            filepath = os.path.join(session_tmp_dir, filename)

            try:
                page_source = driver.page_source
                _save_xml_with_masking(filepath, page_source)

                stats = _get_ios_element_stats(page_source)
                print(f"  [{capture_count}] 저장: {filename}")
                print(f"      요소: {stats['total']}개 / 상호작용: {stats['interactive']}개")

            except Exception as e:
                print(f"  캡처 실패: {e}")

    except KeyboardInterrupt:
        print("\n\n강제 종료됨.")
    finally:
        if driver is not None:
            driver.quit()

        final_dir = _finalize_session_dir(session_tmp_dir, output_dir)
        print()
        print("=" * 50)
        print(f"  총 {capture_count}개 화면 캡처 완료")
        if final_dir:
            print(f"  저장 위치: {final_dir}")
        else:
            print(f"  저장 위치: {session_tmp_dir}")
        print("=" * 50)


def watch_mode(interval: float = 0.2):
    """자동 감지 모드: 화면 변화를 자동으로 감지하여 캡처합니다."""
    print("=" * 50)
    print("  iOS UI 요소 덤프 - 자동 감지 모드 (Watch)")
    print("=" * 50)
    print()
    print("  화면이 변경되면 자동으로 캡처됩니다.")
    print("  [Ctrl+C] 종료")
    print()

    output_dir = os.path.join(PROJECT_ROOT, "ui_dumps")
    os.makedirs(output_dir, exist_ok=True)

    driver = _connect_ios_driver()
    if not driver:
        return

    # 세션 폴더 생성
    session_start = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_tmp_dir = _ensure_unique_dir(os.path.join(output_dir, f"_ios_watch_{session_start}"))
    os.makedirs(session_tmp_dir, exist_ok=True)

    capture_count = 0
    last_screen_hash = None
    captured_screens = set()

    print("-" * 50)
    print("감시 시작! 앱에서 화면을 이동해보세요.")
    print("-" * 50)
    print()

    try:
        while True:
            try:
                page_source = driver.page_source
                current_hash = _get_screen_hash(page_source)

                # 화면 변화 감지
                if current_hash != last_screen_hash:
                    screen_name = _extract_screen_name(driver, page_source)
                    capture_key = f"{screen_name}_{current_hash[:8]}"

                    if capture_key not in captured_screens:
                        capture_count += 1

                        # 파일명: 순번_화면이름.xml
                        filename = f"{capture_count:03d}_{screen_name}.xml"
                        filepath = os.path.join(session_tmp_dir, filename)

                        _save_xml_with_masking(filepath, page_source)

                        stats = _get_ios_element_stats(page_source)
                        print(f"  [{capture_count:02d}] {screen_name}")
                        print(f"       -> {filename} (요소: {stats['total']}, 상호작용: {stats['interactive']})")

                        captured_screens.add(capture_key)

                    last_screen_hash = current_hash

            except Exception:
                pass

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n감시 종료.")
    finally:
        if driver is not None:
            driver.quit()

        # Watch 모드는 yymmdd_HHMM 형식 사용
        final_dir = _finalize_session_dir(session_tmp_dir, output_dir, "%y%m%d_%H%M")
        print()
        print("=" * 50)
        print(f"  총 {capture_count}개 화면 자동 캡처 완료")
        if final_dir:
            print(f"  저장 위치: {final_dir}")
        else:
            print(f"  저장 위치: {session_tmp_dir}")
        print("=" * 50)

        if capture_count > 0:
            print()
            print("캡처된 화면:")
            for screen in sorted(captured_screens):
                name = screen.rsplit('_', 1)[0]
                print(f"  - {name}")


def list_dumps():
    """저장된 UI 덤프 파일 목록을 표시합니다."""
    output_dir = os.path.join(PROJECT_ROOT, "ui_dumps")

    if not os.path.exists(output_dir):
        print("저장된 덤프 파일이 없습니다.")
        return

    entries = sorted(os.listdir(output_dir))
    xml_files = [e for e in entries if e.endswith(".xml") and os.path.isfile(os.path.join(output_dir, e))]
    session_dirs = [e for e in entries if os.path.isdir(os.path.join(output_dir, e))]

    if not xml_files and not session_dirs:
        print("저장된 덤프 파일이 없습니다.")
        return

    print("저장된 UI 덤프 파일/세션:")
    print("-" * 50)

    for f in xml_files:
        filepath = os.path.join(output_dir, f)
        size = os.path.getsize(filepath)
        print(f"  [file] {f} ({size:,} bytes)")

    for d in session_dirs:
        dirpath = os.path.join(output_dir, d)
        xml_count = len([x for x in os.listdir(dirpath) if x.endswith(".xml")])
        print(f"  [dir ] {d}/ ({xml_count} xml)")

    print("-" * 50)
    print(f"총 파일 {len(xml_files)}개, 세션 폴더 {len(session_dirs)}개")


def mask_existing_dumps():
    """기존에 저장된 ui_dumps 파일들을 마스킹 처리합니다."""
    output_dir = os.path.join(PROJECT_ROOT, "ui_dumps")

    if not os.path.exists(output_dir):
        print("ui_dumps 폴더가 없습니다.")
        return

    print("=" * 50)
    print("  기존 UI 덤프 파일 마스킹")
    print("=" * 50)
    print()

    masked_count = 0
    for root_dir, dirs, files in os.walk(output_dir):
        for filename in files:
            if filename.endswith(".xml"):
                filepath = os.path.join(root_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        original = f.read()

                    masked = _mask_sensitive_data(original)

                    if original != masked:
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(masked)
                        rel_path = os.path.relpath(filepath, output_dir)
                        print(f"  [마스킹] {rel_path}")
                        masked_count += 1

                except Exception as e:
                    print(f"  [오류] {filepath}: {e}")

    print()
    print(f"총 {masked_count}개 파일 마스킹 완료")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--mask-existing":
            mask_existing_dumps()
        elif sys.argv[1] == "--list":
            list_dumps()
        elif sys.argv[1] in ("-i", "--interactive"):
            interactive_mode()
        elif sys.argv[1] in ("-w", "--watch"):
            interval = 0.2
            if len(sys.argv) > 2:
                try:
                    interval = float(sys.argv[2])
                except ValueError:
                    pass
            watch_mode(interval)
        elif sys.argv[1] == "--help":
            print("사용법:")
            print("  python tools/ui_dump_ios.py [옵션] [이름]")
            print()
            print("옵션:")
            print("  -i, --interactive  인터랙티브 모드 (Enter로 캡처, q로 종료)")
            print("  -w, --watch [초]   자동 감지 모드 (화면 변화 자동 캡처, 기본 0.2초)")
            print("  --list             저장된 덤프 파일 목록 표시")
            print("  --mask-existing    기존 덤프 파일들을 마스킹 처리")
            print("  --help             도움말 표시")
            print()
            print("예시:")
            print("  python tools/ui_dump_ios.py                  # 현재 화면 1회 캡처")
            print("  python tools/ui_dump_ios.py login_screen     # 이름 지정하여 캡처")
            print("  python tools/ui_dump_ios.py -i               # 인터랙티브 모드")
            print("  python tools/ui_dump_ios.py -w               # 자동 감지 모드 (0.2초 간격)")
            print("  python tools/ui_dump_ios.py -w 1.0           # 자동 감지 모드 (1초 간격)")
            print()
            print("참고:")
            print("  - iOS 시뮬레이터 또는 실기기가 연결되어 있어야 합니다")
            print("  - Appium 서버가 실행 중이어야 합니다 (appium --relaxed-security)")
            print("  - 저장 시 민감 정보가 자동으로 마스킹됩니다")
        else:
            dump_ui(sys.argv[1])
    else:
        dump_ui()
