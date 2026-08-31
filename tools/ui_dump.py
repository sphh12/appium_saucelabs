"""
UI 요소 덤프 스크립트
현재 화면의 UI 요소를 XML 파일로 저장합니다.

사용법:
    python tools/ui_dump.py [이름]

예시:
    python tools/ui_dump.py login_screen
    python tools/ui_dump.py home

참고:
    - 저장 시 민감 정보(전화번호, 이메일, 생년월일)가 자동으로 마스킹됩니다.
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
from appium.options.android import UiAutomator2Options

# 프로젝트 루트 경로
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.capabilities import ANDROID_CAPS, get_appium_server_url


# =============================================================================
# 민감 정보 마스킹 기능
# =============================================================================

def _mask_sensitive_data(xml_content: str) -> str:
    """
    XML 내용에서 민감한 개인정보를 마스킹합니다.

    마스킹 대상:
    - 전화번호 (한국 형식)
    - 이메일 주소
    - 생년월일 (YYYY-MM-DD, YYYYMMDD 형식)

    Args:
        xml_content: 원본 XML 문자열

    Returns:
        마스킹된 XML 문자열
    """
    import re

    masked = xml_content

    # 1. 전화번호 마스킹 (다양한 한국 전화번호 형식)
    # 010-1234-5678, 01012345678, 010 1234 5678, 019-555-9999 등
    phone_patterns = [
        # 하이픈 포함: 010-1234-5678, 02-123-4567
        (r'(\d{2,3})-(\d{3,4})-(\d{4})', r'\1-****-****'),
        # 공백 포함: 010 1234 5678
        (r'(\d{2,3})\s(\d{3,4})\s(\d{4})', r'\1-****-****'),
        # 연속 숫자 (10-11자리 휴대폰): 01012345678
        (r'(?<!\d)(01[0-9])(\d{3,4})(\d{4})(?!\d)', r'\1********'),
        # 연속 숫자 (지역번호 포함): 0212345678
        (r'(?<!\d)(0[2-6][0-9]?)(\d{3,4})(\d{4})(?!\d)', r'\1*******'),
    ]

    for pattern, replacement in phone_patterns:
        masked = re.sub(pattern, replacement, masked)

    # 2. 이메일 마스킹
    # user@domain.com -> u***@d***.com
    def mask_email(match):
        email = match.group(0)
        local, domain = email.split('@')
        domain_parts = domain.split('.')

        # 로컬 파트 마스킹 (첫 글자만 표시)
        if len(local) > 1:
            masked_local = local[0] + '***'
        else:
            masked_local = '***'

        # 도메인 마스킹 (첫 글자만 표시)
        if len(domain_parts[0]) > 1:
            masked_domain = domain_parts[0][0] + '***'
        else:
            masked_domain = '***'

        # TLD는 유지
        return f"{masked_local}@{masked_domain}.{'.'.join(domain_parts[1:])}"

    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    masked = re.sub(email_pattern, mask_email, masked)

    # 3. 생년월일 마스킹 (YYYY-MM-DD 형식)
    # 1990-01-15 -> ****-**-**
    date_pattern = r'(?<!\d)(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])(?!\d)'
    masked = re.sub(date_pattern, '****-**-**', masked)

    # 4. 생년월일 마스킹 (YYYYMMDD 형식, 8자리 연속)
    # 19900115 -> ********
    date_pattern2 = r'(?<!\d)(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)'
    masked = re.sub(date_pattern2, '********', masked)

    return masked


def _get_activity_comment(driver) -> str:
    """현재 Activity와 Package 정보를 XML 주석 문자열로 반환합니다."""
    try:
        activity = driver.current_activity or "unknown"
        package = driver.current_package or "unknown"
        return f"<!-- Activity: {activity} | Package: {package} -->\n"
    except Exception:
        return ""


def _prepend_activity_comment(xml_content: str, driver) -> str:
    """XML 내용 상단에 Activity 주석을 삽입합니다.

    XML 선언(<?xml ...?>) 바로 다음 줄에 삽입되며,
    선언이 없으면 맨 앞에 추가합니다.
    """
    comment = _get_activity_comment(driver)
    if not comment:
        return xml_content

    # XML 선언 뒤에 삽입
    if xml_content.startswith("<?xml"):
        decl_end = xml_content.index("?>") + 2
        return xml_content[:decl_end] + "\n" + comment + xml_content[decl_end:].lstrip("\n")
    else:
        return comment + xml_content


def _save_xml_with_masking(filepath: str, content: str) -> None:
    """XML 파일을 마스킹하여 저장합니다."""
    masked_content = _mask_sensitive_data(content)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(masked_content)


def _ensure_unique_dir(path: str) -> str:
    """Return a directory path that does not exist by appending _N suffix."""
    if not os.path.exists(path):
        return path
    idx = 1
    while True:
        candidate = f"{path}_{idx}"
        if not os.path.exists(candidate):
            return candidate
        idx += 1


def _finalize_session_dir(session_tmp_dir: str, output_root: str, timestamp_format: str = "%Y%m%d_%H%M%S") -> str | None:
    """Rename/move the session temp directory into output_root/<end_timestamp>.

    Args:
        session_tmp_dir: 임시 세션 폴더 경로
        output_root: 출력 루트 폴더
        timestamp_format: 폴더명 타임스탬프 형식 (기본: %Y%m%d_%H%M%S)
    """
    if not session_tmp_dir or not os.path.isdir(session_tmp_dir):
        return None

    end_timestamp = datetime.now().strftime(timestamp_format)
    final_dir = _ensure_unique_dir(os.path.join(output_root, f"aos_{end_timestamp}"))

    try:
        os.rename(session_tmp_dir, final_dir)
    except Exception:
        try:
            shutil.move(session_tmp_dir, final_dir)
        except Exception:
            return session_tmp_dir

    return final_dir


def dump_ui(name: str = None):
    """
    현재 화면의 UI 요소를 XML 파일로 저장합니다.

    Args:
        name: 저장할 파일의 이름 (선택사항)
    """
    # 출력 폴더 생성
    output_dir = os.path.join(PROJECT_ROOT, "ui_dumps")
    os.makedirs(output_dir, exist_ok=True)

    # aos_ 프리픽스 + 타임스탬프 폴더 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(output_dir, f"aos_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)

    # 파일명 생성
    if name:
        filename = f"{timestamp}_{name}.xml"
    else:
        filename = f"{timestamp}.xml"

    filepath = os.path.join(session_dir, filename)

    print("=" * 50)
    print("  UI 요소 덤프 스크립트")
    print("=" * 50)
    print()

    # 기존 세션에 연결 시도 (noReset 모드)
    caps = ANDROID_CAPS.copy()
    caps["noReset"] = True
    caps.pop("app", None)  # 앱 재설치 방지

    options = UiAutomator2Options()
    for key, value in caps.items():
        options.set_capability(key, value)

    print(f"[1/3] Appium 서버 연결 중... ({get_appium_server_url()})")

    try:
        driver = webdriver.Remote(
            command_executor=get_appium_server_url(),
            options=options
        )
        print("      연결 성공!")
    except Exception as e:
        print(f"      연결 실패: {e}")
        print()
        print("확인사항:")
        print("  1. Appium 서버가 실행 중인지 확인 (npx appium)")
        print("  2. 에뮬레이터/디바이스가 연결되어 있는지 확인 (adb devices)")
        return None

    try:
        print(f"[2/3] 화면 요소 추출 중...")
        page_source = driver.page_source
        # Activity 정보를 XML 주석으로 삽입
        page_source = _prepend_activity_comment(page_source, driver)

        print(f"[3/3] XML 파일 저장 중 (마스킹 적용)... ({filepath})")
        _save_xml_with_masking(filepath, page_source)

        print()
        print("=" * 50)
        print(f"  저장 완료: {filepath}")
        print("=" * 50)
        print()

        # 간단한 요소 통계
        root = ET.fromstring(page_source)
        element_count = len(list(root.iter()))
        clickable_count = len([e for e in root.iter() if e.get("clickable") == "true"])

        print(f"요소 통계:")
        print(f"  - 전체 요소: {element_count}개")
        print(f"  - 클릭 가능: {clickable_count}개")
        print()

        return filepath

    except Exception as e:
        print(f"오류 발생: {e}")
        return None
    finally:
        driver.quit()


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


def interactive_mode():
    """
    인터랙티브 모드: Enter 키로 캡처, q로 종료
    """
    print("=" * 50)
    print("  UI 요소 덤프 - 인터랙티브 모드")
    print("=" * 50)
    print()
    print("  [Enter]  현재 화면 캡처")
    print("  [q]      종료")
    print()

    # 출력 폴더 생성
    output_dir = os.path.join(PROJECT_ROOT, "ui_dumps")
    os.makedirs(output_dir, exist_ok=True)

    # Appium 연결
    caps = ANDROID_CAPS.copy()
    caps["noReset"] = True
    caps.pop("app", None)

    options = UiAutomator2Options()
    for key, value in caps.items():
        options.set_capability(key, value)

    print(f"Appium 서버 연결 중... ({get_appium_server_url()})")
    driver = None
    try:
        driver = webdriver.Remote(
            command_executor=get_appium_server_url(),
            options=options
        )
        print("연결 성공!")
        print()
    except Exception as e:
        print(f"연결 실패: {e}")
        print()
        print("확인사항:")
        print("  1. Appium 서버가 실행 중인지 확인 (npx appium)")
        print("  2. 에뮬레이터/디바이스가 연결되어 있는지 확인 (adb devices)")
        return

    # 세션 임시 폴더(종료 시점에 폴더명을 종료시간으로 확정)
    session_start = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_tmp_dir = os.path.join(output_dir, f"_aos_running_{session_start}")
    session_tmp_dir = _ensure_unique_dir(session_tmp_dir)
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

            # 캡처 실행
            capture_count += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{capture_count:03d}.xml"
            filepath = os.path.join(session_tmp_dir, filename)

            try:
                page_source = driver.page_source
                # Activity 정보를 XML 주석으로 삽입
                page_source = _prepend_activity_comment(page_source, driver)

                # 마스킹 적용하여 저장
                _save_xml_with_masking(filepath, page_source)

                # 요소 통계 (Activity 주석 제거 후 파싱)
                raw_xml = driver.page_source
                root = ET.fromstring(raw_xml)
                element_count = len(list(root.iter()))
                clickable_count = len([e for e in root.iter() if e.get("clickable") == "true"])

                print(f"  [{capture_count}] 저장: {filename}")
                print(f"      요소: {element_count}개 / 클릭 가능: {clickable_count}개")

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
        print(f"  폴더명은 종료시간(YYYYMMDD_HHMMSS) 기준입니다")
        print("=" * 50)


def _extract_screen_name(driver, page_source: str) -> str:
    """
    화면 이름을 추출합니다.

    우선순위:
    1. screenTitle 요소의 텍스트
    2. toolbarTitle 요소의 텍스트
    3. 현재 activity 이름
    4. 첫 번째 의미있는 텍스트
    """
    try:
        root = ET.fromstring(page_source)

        # 1. screenTitle 찾기
        for elem in root.iter():
            resource_id = elem.get("resource-id", "")
            if "screenTitle" in resource_id or "toolbar_title" in resource_id or "toolbarTitle" in resource_id:
                text = elem.get("text", "").strip()
                if text:
                    return _sanitize_filename(text)

        # 2. 일반적인 타이틀 패턴 찾기
        for elem in root.iter():
            resource_id = elem.get("resource-id", "")
            if "title" in resource_id.lower():
                text = elem.get("text", "").strip()
                if text and len(text) < 50:  # 너무 긴 텍스트 제외
                    return _sanitize_filename(text)

        # 3. Activity 이름 가져오기
        try:
            current_activity = driver.current_activity
            if current_activity:
                # .MainActivity -> MainActivity
                activity_name = current_activity.split(".")[-1]
                # Activity 접미사 제거
                activity_name = activity_name.replace("Activity", "")
                if activity_name:
                    return _sanitize_filename(activity_name)
        except Exception:
            pass

        # 4. 첫 번째 의미있는 텍스트 (TextView에서)
        for elem in root.iter():
            if "TextView" in elem.get("class", ""):
                text = elem.get("text", "").strip()
                if text and 3 < len(text) < 30 and not text.startswith("http"):
                    return _sanitize_filename(text[:20])

    except Exception:
        pass

    return "unknown"


def _sanitize_filename(name: str) -> str:
    """파일명에 사용할 수 없는 문자를 제거합니다."""
    # 공백을 언더스코어로
    name = name.replace(" ", "_")
    # 특수문자 제거
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # 연속 언더스코어 정리
    name = re.sub(r'_+', '_', name)
    # 앞뒤 언더스코어 제거
    name = name.strip('_')
    # 길이 제한
    return name[:30] if len(name) > 30 else name


def _get_screen_hash(page_source: str) -> str:
    """화면 내용의 해시를 생성합니다 (변화 감지용)."""
    # 전체 XML 대신 주요 구조만 해시
    try:
        root = ET.fromstring(page_source)
        # resource-id와 text만 추출하여 해시
        structure = []
        for elem in root.iter():
            resource_id = elem.get("resource-id", "")
            text = elem.get("text", "")
            if resource_id or text:
                structure.append(f"{resource_id}:{text[:20]}")

        content = "|".join(structure[:50])  # 상위 50개만
        return hashlib.md5(content.encode()).hexdigest()[:16]
    except Exception:
        return hashlib.md5(page_source.encode()).hexdigest()[:16]


def watch_mode(interval: float = 0.2):
    """
    자동 감지 모드: 화면 변화를 자동으로 감지하여 캡처합니다.

    Args:
        interval: 화면 체크 간격 (초), 기본 0.2초
    """
    print("=" * 50)
    print("  UI 요소 덤프 - 자동 감지 모드 (Watch)")
    print("=" * 50)
    print()
    print("  화면이 변경되면 자동으로 캡처됩니다.")
    print("  [Ctrl+C] 종료")
    print()

    # 출력 폴더 생성
    output_dir = os.path.join(PROJECT_ROOT, "ui_dumps")
    os.makedirs(output_dir, exist_ok=True)

    # Appium 연결
    caps = ANDROID_CAPS.copy()
    caps["noReset"] = True
    caps.pop("app", None)

    options = UiAutomator2Options()
    for key, value in caps.items():
        options.set_capability(key, value)

    print(f"Appium 서버 연결 중... ({get_appium_server_url()})")
    driver = None
    try:
        driver = webdriver.Remote(
            command_executor=get_appium_server_url(),
            options=options
        )
        print("연결 성공!")
        print()
    except Exception as e:
        print(f"연결 실패: {e}")
        print()
        print("확인사항:")
        print("  1. Appium 서버가 실행 중인지 확인 (npx appium)")
        print("  2. 에뮬레이터/디바이스가 연결되어 있는지 확인 (adb devices)")
        return

    # 세션 폴더 생성
    session_start = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_tmp_dir = os.path.join(output_dir, f"_aos_watch_{session_start}")
    session_tmp_dir = _ensure_unique_dir(session_tmp_dir)
    os.makedirs(session_tmp_dir, exist_ok=True)

    capture_count = 0
    last_screen_hash = None
    last_screen_name = None
    captured_screens = set()  # 이미 캡처한 화면 이름 추적

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

                    # 같은 이름의 화면은 한 번만 캡처 (옵션)
                    # 매번 캡처하려면 이 조건 제거
                    capture_key = f"{screen_name}_{current_hash[:8]}"

                    if capture_key not in captured_screens:
                        capture_count += 1
                        timestamp = datetime.now().strftime("%H%M%S")

                        # 파일명: 순번_화면이름.xml
                        filename = f"{capture_count:03d}_{screen_name}.xml"
                        filepath = os.path.join(session_tmp_dir, filename)

                        # Activity 정보를 XML 주석으로 삽입 + 마스킹 적용하여 저장
                        save_content = _prepend_activity_comment(page_source, driver)
                        _save_xml_with_masking(filepath, save_content)

                        # 요소 통계
                        root = ET.fromstring(page_source)
                        element_count = len(list(root.iter()))
                        clickable_count = len([e for e in root.iter() if e.get("clickable") == "true"])

                        print(f"  [{capture_count:02d}] {screen_name}")
                        print(f"       -> {filename} (요소: {element_count}, 클릭: {clickable_count})")

                        captured_screens.add(capture_key)
                        last_screen_name = screen_name

                    last_screen_hash = current_hash

            except Exception as e:
                # 일시적 오류는 무시 (화면 전환 중 등)
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

        # 캡처된 화면 목록 출력
        if capture_count > 0:
            print()
            print("캡처된 화면:")
            for screen in sorted(captured_screens):
                name = screen.rsplit('_', 1)[0]  # 해시 제거
                print(f"  - {name}")


def mask_existing_dumps():
    """
    기존에 저장된 ui_dumps 파일들을 마스킹 처리합니다.
    """
    output_dir = os.path.join(PROJECT_ROOT, "ui_dumps")

    if not os.path.exists(output_dir):
        print("ui_dumps 폴더가 없습니다.")
        return

    print("=" * 50)
    print("  기존 UI 덤프 파일 마스킹")
    print("=" * 50)
    print()

    masked_count = 0

    # 모든 XML 파일 찾기
    for root_dir, dirs, files in os.walk(output_dir):
        for filename in files:
            if filename.endswith(".xml"):
                filepath = os.path.join(root_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        original = f.read()

                    masked = _mask_sensitive_data(original)

                    # 변경된 경우에만 저장
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
        elif sys.argv[1] == "-i" or sys.argv[1] == "--interactive":
            interactive_mode()
        elif sys.argv[1] == "-w" or sys.argv[1] == "--watch":
            # 옵션으로 간격 지정 가능: -w 0.2
            interval = 0.2
            if len(sys.argv) > 2:
                try:
                    interval = float(sys.argv[2])
                except ValueError:
                    pass
            watch_mode(interval)
        elif sys.argv[1] == "--help":
            print("사용법:")
            print("  python tools/ui_dump.py [옵션] [이름]")
            print()
            print("옵션:")
            print("  -i, --interactive  인터랙티브 모드 (Enter로 캡처, q로 종료)")
            print("  -w, --watch [초]   자동 감지 모드 (화면 변화 자동 캡처, 기본 0.2초)")
            print("  --list             저장된 덤프 파일 목록 표시")
            print("  --mask-existing    기존 덤프 파일들을 마스킹 처리")
            print("  --help             도움말 표시")
            print()
            print("예시:")
            print("  python tools/ui_dump.py                  # 현재 화면 1회 캡처")
            print("  python tools/ui_dump.py login_screen     # 이름 지정하여 캡처")
            print("  python tools/ui_dump.py -i               # 인터랙티브 모드")
            print("  python tools/ui_dump.py -w               # 자동 감지 모드 (0.2초 간격)")
            print("  python tools/ui_dump.py -w 1.0           # 자동 감지 모드 (1초 간격)")
            print()
            print("참고:")
            print("  - 저장 시 민감 정보가 자동으로 마스킹됩니다:")
            print("    전화번호: 010-1234-5678 -> 010-****-****")
            print("    이메일: user@mail.com -> u***@m***.com")
            print("    생년월일: 1990-01-15 -> ****-**-**")
        else:
            dump_ui(sys.argv[1])
    else:
        dump_ui()