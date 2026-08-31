# 코딩 가이드라인

## 개요

이 문서는 테스트 스크립트 작성 시 따라야 할 규칙과 가이드라인을 정리합니다.

---

## 1. UI Dump 기반 테스트 스크립트 작성

### 1.1 XML 덤프 파일 참조

| 상황 | 규칙 |
|------|------|
| 별도 언급 없음 | **최신 dump 폴더/파일** 참조 |
| 특정 폴더/파일 지정 | 지정된 파일 참조 |

**최신 폴더 확인 방법:**
```
ui_dumps/
├── aos_20260122_132608/    # Android 이전 세션
├── aos_260123_1254/        # Android 최신
├── ios_20260215_0009/      # iOS 이전 세션
└── ios_20260215_2348/      # ← iOS 최신 (이 폴더 사용)
```

### 1.2 XML 파일 분석 시 확인 항목

테스트 스크립트 생성 전 반드시 확인:

1. **화면 타이틀** - `screenTitle`, `toolbar_title`, `txvTitle` 등
2. **클릭 가능 요소** - `clickable="true"` 속성
3. **주요 UI 요소** - `resource-id`, `content-desc`, `text`
4. **입력 필드** - EditText 클래스의 요소들

---

## 2. Locator 전략

### 2.1 우선순위

```
1순위: accessibility id   (Android content-desc / iOS name)
2순위: id                 (Android resource-id)
3순위: -android uiautomator (UiSelector — Android 전용, 텍스트/스크롤 탐색 등)
4순위: xpath              (위 셀렉터로 식별 불가할 때 최후 수단)
```

> 위쪽 셀렉터일수록 빠르고 깨지지 않습니다. xpath는 동일 셀렉터로 구분이 불가능할 때만 사용하세요.

### 2.2 구현 패턴 — POM Locator는 `(By, value)` 튜플 상수

별도의 `find_*_with_fallback` 헬퍼는 **존재하지 않습니다.** Locator는 페이지 클래스에
`(AppiumBy.XXX, value)` 튜플 상수로 선언하고, `BasePage`가 제공하는 명시적 대기 헬퍼(`find` /
`find_clickable` / `click` / `input_text` 등)에 그대로 넘깁니다.

Android resource-id는 패키지 접두사(`_PKG`)를 붙여 작성합니다.

```python
# pages/login_page.py (실제 코드)
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage

_PKG = "com.saucelabs.mydemoapp.android:id/"


class LoginPage(BasePage):
    # 1순위 accessibility id
    LOGIN_BTN = (AppiumBy.ACCESSIBILITY_ID, "Tap to login with given credentials")
    # 2순위 id (resource-id, _PKG 접두사 결합)
    USERNAME = (AppiumBy.ID, _PKG + "nameET")
    PASSWORD = (AppiumBy.ID, _PKG + "passwordET")
    USERNAME_ERROR = (AppiumBy.ID, _PKG + "nameErrorTV")

    def login(self, username: str, password: str):
        self.input_text(self.USERNAME, username)   # 클릭 가능 대기 + clear + send_keys
        self.input_text(self.PASSWORD, password)
        self.hide_keyboard()
        self.click(self.LOGIN_BTN)                  # 클릭 가능 대기 + stale 재시도 포함
```

### 2.3 `BasePage` 헬퍼 요약

| 헬퍼 | 동작 | 비고 |
|------|------|------|
| `find(locator)` | DOM 존재 대기 후 반환 | `presence_of_element_located` |
| `find_visible(locator)` | 화면 표시 대기 후 반환 | `visibility_of_element_located` |
| `find_clickable(locator)` | 클릭 가능 대기 후 반환 | `element_to_be_clickable` |
| `find_all(locator)` | 1개 이상 전체 반환 | `presence_of_all_elements_located` |
| `click(locator)` | 클릭 가능 대기 후 클릭 | Stale 시 자동 재탐색·재시도 |
| `input_text(locator, text)` | clear 후 텍스트 입력 | Stale 시 재시도 |
| `get_text(locator)` | 요소 텍스트 반환 | Stale 시 재시도 |
| `is_visible(locator, timeout=5)` | 표시 여부 bool | TimeoutException → False |

> 모든 헬퍼는 **명시적 대기(WebDriverWait)** 기반입니다. implicit wait는 conftest에서 0으로 고정되어
> 있으므로 `time.sleep`이나 implicit wait에 의존하지 마세요.

### 2.4 `-android uiautomator` / `xpath` 사용 예시

```python
# 3순위: -android uiautomator (텍스트로 찾거나 스크롤하여 노출시킬 때)
ITEM_BY_TEXT = (
    AppiumBy.ANDROID_UIAUTOMATOR,
    'new UiSelector().textContains("Sauce Labs Backpack")',
)

# 4순위: xpath (위 셀렉터로 구분 불가할 때 최후 수단)
PRICE_IN_ROW = (AppiumBy.XPATH, "//android.widget.TextView[@content-desc='Price']")
```

---

## 3. 테스트 파일 명명 규칙

### 3.1 파일명

```
tests/android/
├── login_test.py       # 로그인 테스트
├── products_test.py    # 상품 목록 테스트
├── cart_test.py        # 장바구니 테스트
└── <기능>_test.py      # 기능별 테스트
```

### 3.2 클래스/메서드명

```python
class TestLogin:
    """테스트 클래스 - Test로 시작"""

    def test_01_login_with_valid_user(self, android_driver):
        """테스트 메서드 - test_로 시작, 순번_기능명"""
        pass
```

---

## 4. Allure 리포트 어노테이션

### 4.1 필수 어노테이션

```python
@allure.feature("기능 영역")      # Login, Catalog, Cart, Checkout 등
@allure.story("세부 기능")        # 정상 로그인, 상품 정렬, 카트 수량 변경 등
@allure.severity(allure.severity_level.CRITICAL)  # BLOCKER, CRITICAL, NORMAL, MINOR
@allure.title("테스트 제목")
@allure.description("테스트 설명")
def test_example(self, android_driver):
    pass
```

### 4.2 Step 사용

```python
with allure.step("단계 설명"):
    # 테스트 코드
    assert condition, "실패 메시지"
```

---

## 5. UI Dump 도구 사용

### 5.1 모드 선택

| 모드 | 명령어 | 용도 |
|------|--------|------|
| 단일 캡처 | `python tools/ui_dump.py` | 현재 화면 1회 캡처 |
| 이름 지정 | `python tools/ui_dump.py login` | 이름 붙여 캡처 |
| 인터랙티브 | `python tools/ui_dump.py -i` | 수동 캡처 |
| **Watch (권장)** | `python tools/ui_dump.py -w` | 자동 감지 캡처 |

> iOS: `python tools/ui_dump_ios.py` (동일 옵션 지원)

### 5.2 Watch 모드 출력

```
ui_dumps/aos_260123_1505/
├── 001_ProductList.xml
├── 002_ProductDetail.xml
└── 003_Cart.xml
```

---

## 6. 테스트 실행

### 6.1 단일 파일 실행

```bash
./shell/run-app.sh --<your_test>
```

### 6.2 직접 실행

```bash
pytest tests/android/<your_test>.py -v
```

---

## 7. 체크리스트

### 테스트 스크립트 작성 전

- [ ] 최신 UI dump 폴더 확인
- [ ] 대상 화면의 XML 파일 분석
- [ ] 주요 요소의 resource-id, content-desc 추출

### 테스트 스크립트 작성 시

- [ ] Locator 우선순위 준수 (accessibility id > id > -android uiautomator > xpath)
- [ ] Locator는 페이지 클래스에 `(AppiumBy.XXX, value)` 튜플 상수로 선언 (id는 `_PKG` 접두사)
- [ ] `BasePage` 헬퍼(`find`/`find_clickable`/`click`/`input_text`) 사용, `time.sleep` 금지
- [ ] Allure 어노테이션 추가
- [ ] Step 단위로 구분

### 테스트 스크립트 작성 후

- [ ] 파일명 규칙 준수 확인 (`*_test.py`)
- [ ] 실행 테스트