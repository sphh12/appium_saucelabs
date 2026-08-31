# iOS UI Dump 기반 테스트 작성 가이드

## 개요

iOS 시뮬레이터를 대상으로 UI Dump → 분석 → 테스트 코드 작성까지의 전체 흐름을 정리한 가이드입니다.
본 프로젝트의 대상 앱은 SauceLabs My Demo App이며, 아래 예시는 iOS 자동화 기법을 익히기 위해
시뮬레이터 내장 앱(연락처)을 **학습 대상**으로 사용한 사례입니다 — 동일한 기법(UI Dump, Locator
전략, StaleElement 처리, 키보드 닫기 등)이 My Demo App에도 그대로 적용됩니다.

---

## 1. 전체 작업 흐름

```
[1] UI Dump 캡처  →  [2] XML 분석  →  [3] 테스트 코드 작성  →  [4] 실행 및 디버깅
```

| 단계 | 도구/명령어 | 산출물 |
|------|------------|--------|
| UI Dump 캡처 | `python tools/ui_dump_ios.py` | `ui_dumps/ios_{timestamp}/*.xml` |
| XML 분석 | VS Code에서 XML 열기 | 요소 정보 정리 (name, type, label) |
| 테스트 코드 작성 | - | `tests/ios/*_test.py` |
| 실행 | `pytest tests/ios/*_test.py -v -s` | 테스트 결과 |

---

## 2. Step 1: UI Dump 캡처

### 2.1 필요한 화면 캡처

테스트 시나리오에 포함되는 **모든 화면**을 캡처합니다.

```bash
# 가상환경 활성화
source venv/bin/activate

# 단일 캡처 (이름 지정)
python tools/ui_dump_ios.py contacts_list     # 연락처 목록 화면
python tools/ui_dump_ios.py contacts_add      # 연락처 추가 화면

# Watch 모드 (화면 변화 자동 캡처) - 여러 화면을 연속으로 캡처할 때
python tools/ui_dump_ios.py -w
```

### 2.2 저장 위치

```
ui_dumps/
├── ios_20260215_2348/                        # iOS 폴더 (ios_ 프리픽스)
│   ├── 20260215_2335_ios_contacts_list.xml
│   └── 20260215_2348_ios_contacts_add.xml
├── aos_260123_1254/                          # Android 폴더 (aos_ 프리픽스)
│   └── ...
```

---

## 3. Step 2: XML 분석

### 3.1 iOS XML 요소 구조

iOS는 Android와 속성명이 다릅니다.

| 용도 | iOS 속성 | Android 속성 |
|------|----------|-------------|
| 요소 식별 | `name` | `resource-id` |
| 접근성 ID | `name` / `label` | `content-desc` |
| 표시 텍스트 | `value` / `label` | `text` |
| 요소 타입 | `type` (XCUIElementType...) | `class` (android.widget...) |
| 클릭 가능 | `enabled` + `accessible` | `clickable` |

### 3.2 XML에서 추출할 정보

```xml
<!-- 예: 연락처 추가 화면의 TextField -->
<XCUIElementTypeTextField
    type="XCUIElementTypeTextField"
    name="성"              ← Locator로 사용
    label="성"
    value="성"             ← placeholder (입력 전)
    enabled="true"
    accessible="true"
/>

<!-- 예: 버튼 -->
<XCUIElementTypeButton
    type="XCUIElementTypeButton"
    name="완료"            ← Locator로 사용
    label="완료"
    enabled="true"
/>
```

### 3.3 분석 결과 정리 (권장 형식)

테스트 코드 작성 전, 분석 결과를 테스트 파일 docstring에 기록합니다.

```python
"""
UI 요소 정보 (ui_dumps/ios_20260215_2348 기반):
- 성: TextField name="성"
- 이름: TextField name="이름"
- 직장: TextField name="직장"
- 전화번호 추가: Cell → 클릭 후 TextField name="휴대전화" 생성
- 완료: Button name="완료"
- 추가: Button name="추가"
"""
```

---

## 4. Step 3: 테스트 코드 작성

### 4.1 기본 구조 — conftest `ios_driver` fixture 재사용

iOS 테스트는 드라이버를 직접 생성하지 말고 **conftest의 `ios_driver` fixture를 재사용**합니다. 이
fixture는 `config/capabilities.py`의 `IOS_CAPS`로 세션을 만들고, **`implicitly_wait(0)`** 으로
implicit wait를 0으로 고정합니다(명시적 대기 전용 — implicit와 혼용 시 타임아웃이 꼬임). 화면
녹화·Allure 첨부도 자동 처리됩니다.

```python
import pytest
import allure

from pages.ios.login_page import LoginPage


@allure.feature("Login")
class TestiOSLogin:

    def test_login_valid(self, ios_driver):
        """conftest의 ios_driver fixture 재사용 (implicit_wait=0, 명시적 대기 전용)."""
        login = LoginPage(ios_driver)   # POM은 BasePage 명시적 대기 헬퍼 사용
        login.login("bob@example.com", "10203040")
        assert login.is_logged_in()
```

> **`driver.implicitly_wait(...)`를 테스트/페이지 코드에서 호출하지 마세요.** 대기는 전부
> `BasePage`의 명시적 대기 헬퍼(`find`/`find_clickable`/`click`/`is_visible` 등)로 처리합니다. 별도
> caps가 꼭 필요한 학습용 예외 케이스라도 `implicitly_wait(0)`을 유지하세요.

#### (학습용) 내장 앱 등 별도 caps가 필요한 경우

iOS 자동화 기법 학습을 위해 시뮬레이터 내장 앱을 직접 띄울 때만 아래처럼 caps를 구성합니다. 이때도
implicit wait는 0으로 둡니다.

```python
import pytest
from appium import webdriver
from appium.options.ios import XCUITestOptions

from config.capabilities import get_appium_server_url


@pytest.fixture(scope="function")
def builtin_app_driver():
    caps = {
        "platformName": "iOS",
        "automationName": "XCUITest",
        "deviceName": "iPhone 17",
        "platformVersion": "26.3",
        "bundleId": "com.apple.MobileAddressBook",  # 학습용 내장 앱
        "noReset": True,
        "newCommandTimeout": 300,
    }
    options = XCUITestOptions().load_capabilities(caps)
    driver = webdriver.Remote(get_appium_server_url(), options=options)
    driver.implicitly_wait(0)   # 명시적 대기 전용 (implicit/explicit 혼용 금지)
    yield driver
    driver.quit()
```

### 4.2 iOS Locator 전략

iOS는 요소 식별·접근성 ID가 모두 **`name` 속성** 기반입니다. My Demo App(iOS)도 대부분 accessibility
id(`name`)로 식별됩니다.

```
1순위: ACCESSIBILITY_ID (name 속성)   → 대부분의 iOS 요소에서 사용 가능
2순위: XPath (type + name 조합)       → 동일 name이 여러 요소에 있을 때
```

```python
# 1순위: Accessibility ID (name)
element = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Tap to login")

# 2순위: XPath (타입 지정이 필요할 때)
field = driver.find_element(
    AppiumBy.XPATH,
    "//XCUIElementTypeTextField[@name='Username input field']"
)
```

> **My Demo App(iOS) 네비게이션은 하단 탭바**입니다. Android의 드로어/헤더와 달리 Catalog / Cart /
> More 탭으로 화면을 이동합니다. 이 탭 액션은 `pages/ios/base_ios_page.py`의 `IOSBasePage`에
> 정의되어 있고, 셀렉터는 모두 accessibility id(`name`)입니다.

```python
# pages/ios/base_ios_page.py (실제 코드 — 하단 탭바, accessibility id 기반)
CATALOG_TAB = (AppiumBy.ACCESSIBILITY_ID, "Catalog-tab-item")
CART_TAB    = (AppiumBy.ACCESSIBILITY_ID, "Cart-tab-item")
MORE_TAB    = (AppiumBy.ACCESSIBILITY_ID, "More-tab-item")
```

### 4.3 내장 앱 bundleId

| 앱 | bundleId |
|----|----------|
| 연락처 | `com.apple.MobileAddressBook` |
| 설정 | `com.apple.Preferences` |
| 캘린더 | `com.apple.mobilecal` |
| Safari | `com.apple.mobilesafari` |
| 메모 | `com.apple.mobilenotes` |

---

## 5. 시행착오 & 해결 방법

### 5.1 iOS 한국어 이름 표시 형식

**문제**: 성="홍", 이름="길동"을 입력했는데 목록에서 찾을 수 없음

```python
# ❌ 잘못된 방식 - "이름 성" 형식
full_name = f"{first_name} {last_name}"  # "길동 홍"

# ✅ 올바른 방식 - iOS는 "성이름" (공백 없음) 형식으로 표시
full_name = f"{last_name}{first_name}"   # "홍길동"
```

**원인**: iOS 연락처 앱은 한국어 이름을 `"성이름"` (공백 없음)으로 표시합니다. 영어 이름은
`"First Last"` 형식입니다.

### 5.2 앱 상태 불일치 (가장 빈번한 문제)

**문제**: 이전 테스트 실패로 앱이 편집 화면/상세 화면/그룹 화면에 남아있어서 다음 테스트에서 "추가"
버튼을 찾지 못함

```python
# ✅ 해결: terminate_app + activate_app으로 앱 재시작
def _ensure_contacts_list(self, driver):
    """앱 재시작으로 항상 깨끗한 상태에서 시작"""
    bundle_id = "com.apple.MobileAddressBook"
    driver.terminate_app(bundle_id)
    time.sleep(1)
    driver.activate_app(bundle_id)
    time.sleep(2)

    # 기대하는 화면인지 확인
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, "추가"))
    )
```

**핵심**: fixture에서 `yield` 전에 앱 상태를 초기화하면, 테스트 실패 후에도 다음 실행이
안정적입니다.

### 5.3 StaleElementReferenceException

**문제**: TextField를 찾아서 클릭했는데, `send_keys()` 시점에 요소 참조가 만료됨

```python
# ❌ 문제 코드 - 클릭 후 요소 갱신됨
field = driver.find_element(AppiumBy.XPATH, xpath)
field.click()
field.send_keys(text)  # StaleElementReferenceException!

# ✅ 해결 - 클릭 후 재탐색
field = driver.find_element(AppiumBy.XPATH, xpath)
field.click()
time.sleep(0.3)
field = driver.find_element(AppiumBy.XPATH, xpath)  # 재탐색
field.send_keys(text)
```

**원인**: iOS에서 TextField를 탭하면 키보드가 올라오면서 DOM이 갱신됩니다. 갱신 전에 찾은 요소
참조는 무효화됩니다.

### 5.4 동일 name의 Cell과 TextField 구분

**문제**: `"전화번호 추가"` Cell을 클릭하면 `"휴대전화"` TextField가 생성되는데, Accessibility ID로
찾으면 Cell이 먼저 잡힘

```python
# ❌ Cell과 TextField 모두 name="휴대전화"
field = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "휴대전화")  # Cell이 잡힐 수 있음

# ✅ XPath로 타입을 명시적으로 지정
field = driver.find_element(
    AppiumBy.XPATH,
    "//XCUIElementTypeTextField[@name='휴대전화']"
)
```

### 5.5 키보드가 버튼을 가림

**문제**: 전화번호 입력 후 키보드가 "완료" 버튼을 가려서 탭이 안 됨

```python
# ✅ NavigationBar 탭으로 키보드 닫기
def _dismiss_keyboard(self, driver):
    try:
        nav = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "새로운 연락처")
        nav.click()
    except Exception:
        pass
    time.sleep(0.5)
```

**참고**: `driver.hide_keyboard()`는 iOS에서 동작하지 않는 경우가 많습니다. NavigationBar나 빈
영역을 탭하는 방식이 안정적입니다.

### 5.6 전화번호 포맷팅 차이

**문제**: `"01012345678"` 입력 → iOS가 자동으로 `"010-1234-5678"`로 표시 → 문자열 비교 실패

```python
# ❌ 직접 비교 - 포맷이 다르면 실패
assert "01012345678" in page_source

# ✅ 숫자만 추출하여 비교
source_digits = "".join(c for c in page_source if c.isdigit())
assert "01012345678" in source_digits
```

### 5.7 동적으로 생성되는 요소

**문제**: "전화번호 추가" 셀을 클릭해야 "휴대전화" TextField가 생성됨 → 클릭 전에는 존재하지 않음

```python
# ✅ 셀 클릭 → 대기 → 생성된 요소 찾기
self._wait_and_tap(driver, "전화번호 추가")
time.sleep(0.5)

phone_field = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located(
        (AppiumBy.XPATH, "//XCUIElementTypeTextField[@name='휴대전화']")
    )
)
phone_field.send_keys("01012345678")
```

---

## 6. 헬퍼 메서드 모음

아래 헬퍼 메서드들은 iOS 테스트에서 반복적으로 사용됩니다.

```python
def _wait_and_tap(self, driver, accessibility_id, timeout=10):
    """요소 대기 후 탭"""
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, accessibility_id))
    )
    element.click()
    return element


def _input_text_field(self, driver, field_name, text):
    """TextField 입력 (StaleElement 방지)"""
    xpath = f"//XCUIElementTypeTextField[@name='{field_name}']"
    field = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((AppiumBy.XPATH, xpath))
    )
    field.click()
    time.sleep(0.3)
    field = driver.find_element(AppiumBy.XPATH, xpath)  # 재탐색
    field.send_keys(text)


def _is_element_present(self, driver, accessibility_id, timeout=5):
    """요소 존재 여부 확인"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, accessibility_id))
        )
        return True
    except Exception:
        return False
```

---

## 7. iOS vs Android 주요 차이 요약

| 항목 | iOS | Android |
|------|-----|---------|
| Locator 1순위 | `ACCESSIBILITY_ID` (name) | `ACCESSIBILITY_ID` (content-desc) |
| Locator 2순위 | `XPATH` (type + name) | `ID` (resource-id) |
| 요소 타입 접두사 | `XCUIElementType` | `android.widget.` |
| TextField 입력 | 클릭 → 재탐색 → send_keys | 바로 send_keys 가능 |
| 키보드 닫기 | NavigationBar 탭 | `driver.hide_keyboard()` |
| 앱 초기화 | `terminate_app` + `activate_app` | `driver.reset()` |
| 스크롤 | `mobile: scroll` | `UiScrollable` |
| 이름 표시 (한국어) | "홍길동" (성이름) | 앱마다 다름 |

---

## 8. 체크리스트

### 테스트 작성 전

- [ ] 대상 화면 UI Dump 캡처 완료
- [ ] XML에서 요소 정보(name, type) 추출
- [ ] 동일 name 요소 여부 확인 (Cell vs TextField 등)
- [ ] 동적 생성 요소 파악 (클릭 후 나타나는 요소)

### 테스트 작성 시

- [ ] fixture에 앱 상태 초기화 로직 포함
- [ ] TextField 입력은 **클릭 → 재탐색 → send_keys** 패턴
- [ ] XPath로 타입 명시 (동일 name 요소 구분)
- [ ] 키보드 닫기 로직 포함 (버튼 탭 전)
- [ ] 포맷팅되는 데이터는 숫자만 비교

### 테스트 작성 후

- [ ] 파일명 규칙 준수 (`*_test.py`)
- [ ] 연속 2회 실행해도 통과하는지 확인 (앱 상태 초기화 검증)
- [ ] 테스트 데이터 정리 로직 포함

---

## 관련 파일

| 파일 | 설명 |
|------|------|
| `tools/ui_dump_ios.py` | iOS UI Dump 도구 |
| `config/capabilities.py` | iOS/Android capabilities 설정 (`IOS_CAPS`) |
| `conftest.py` | `ios_driver` fixture (implicit_wait=0, 녹화/첨부 자동) |
| `pages/ios/base_ios_page.py` | iOS POM 베이스 (하단 탭바 액션, accessibility id 기반) |
| `pages/ios/*.py` | iOS 화면별 POM (login/catalog/cart/checkout 등) |
| `docs/UI_DUMP_GUIDE.md` | UI Dump 도구 사용 가이드 (Android 중심) |
| `docs/SETUP_GUIDE.md` | 환경 세팅 통합 가이드 (§4 iOS 추가 세팅) |
