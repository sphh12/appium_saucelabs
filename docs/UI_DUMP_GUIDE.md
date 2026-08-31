# UI Dump 도구 가이드

## 개요

`ui_dump.py`는 Appium을 통해 연결된 에뮬레이터/디바이스의 현재 화면 UI 요소를 XML 파일로 저장하는
도구입니다. 저장된 XML 파일을 분석하여 테스트 스크립트 작성에 필요한 요소 정보(resource-id,
content-desc, text 등)를 추출할 수 있습니다.

## 설치 및 실행 환경

### 필수 조건

- Python 가상환경 활성화
- Appium 서버 실행 중
- 에뮬레이터 또는 실제 디바이스 연결

### 가상환경 활성화

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

## 사용 방법

### 1. 단일 캡처

현재 화면을 한 번 캡처합니다.

```bash
python tools/ui_dump.py
```

### 2. 이름 지정 캡처

파일명에 식별 가능한 이름을 추가합니다.

```bash
python tools/ui_dump.py login_screen
# 결과: ui_dumps/aos_20260123_143022/20260123_143022_login_screen.xml
```

### 3. 인터랙티브 모드

수동으로 화면을 탐색하며 원하는 시점에 캡처합니다.

```bash
python tools/ui_dump.py -i
```

**인터랙티브 모드 조작:**

- `Enter` : 현재 화면 캡처
- `q` + `Enter` : 종료

### 4. 자동 감지 모드 (Watch Mode) - 권장

화면 변화를 자동으로 감지하여 캡처합니다. 사용자 플로우를 따라가며 모든 화면을 자동으로 기록할 때
유용합니다.

```bash
# 기본 실행 (0.2초 간격으로 화면 체크)
python tools/ui_dump.py -w

# 체크 간격 지정 (1초)
python tools/ui_dump.py -w 1.0
```

**자동 감지 모드 특징:**

- 화면 변화 자동 감지 (MD5 해시 비교)
- 화면 이름 자동 추출 (screenTitle, activity명, 또는 첫 번째 텍스트)
- 파일명 형식: `001_ScreenName.xml`, `002_LoginScreen.xml` 등
- `Ctrl+C`로 종료

**화면 이름 추출 우선순위:**

1. `screenTitle` 또는 `toolbarTitle` 요소의 텍스트
2. 일반적인 title 패턴의 요소 텍스트
3. 현재 Activity 이름 (예: `MainActivity` → `Main`)
4. 첫 번째 의미있는 TextView 텍스트

**출력 예시:**

```
감시 시작! 앱에서 화면을 이동해보세요.
--------------------------------------------------

  [01] ProductList
       -> 001_ProductList.xml (요소: 45, 클릭: 12)
  [02] ProductDetail
       -> 002_ProductDetail.xml (요소: 38, 클릭: 8)
  [03] Cart
       -> 003_Cart.xml (요소: 52, 클릭: 15)

감시 종료.
==================================================
  총 3개 화면 자동 캡처 완료
  저장 위치: ui_dumps/aos_260123_1505
==================================================
```

## 저장 위치

캡처된 XML 파일은 `ui_dumps/` 폴더에 저장됩니다.

### 단일/이름 지정 캡처

플랫폼별 프리픽스 폴더(`aos_`, `ios_`) 안에 파일이 저장됩니다.

```
ui_dumps/
├── aos_20260122_132500/                         # Android 단일 캡처
│   └── 20260122_132500.xml
├── aos_20260122_143022/                         # Android 이름 지정 캡처
│   └── 20260122_143022_login_screen.xml
├── ios_20260215_2348/                           # iOS 이름 지정 캡처
│   └── 20260215_2348_contacts_add.xml
```

**폴더명 형식:** `{플랫폼}_{YYYYMMDD_HHMMSS}`

### 인터랙티브 모드 / 자동 감지 모드

세션 단위로 폴더가 생성됩니다. 폴더명은 플랫폼 프리픽스 + 종료 시점 타임스탬프입니다.

```
ui_dumps/
├── aos_20260122_132608/             # Android 인터랙티브 세션
│   ├── 20260122_132500_001.xml
│   ├── 20260122_132515_002.xml
│   └── 20260122_132540_003.xml
│
├── aos_260123_1505/                 # Android Watch 모드 세션
│   ├── 001_ProductList.xml
│   ├── 002_ProductDetail.xml
│   └── 003_Cart.xml
│
├── ios_20260215_1430/               # iOS 인터랙티브 세션
│   └── 20260215_143022_001.xml
│
└── ios_260216_1505/                 # iOS Watch 모드 세션
    ├── 001_ProductList.xml
    └── 002_ProductDetail.xml
```

**폴더명 형식:**

- Android 인터랙티브: `aos_YYYYMMDD_HHMMSS` (예: aos_20260123_150530)
- Android Watch: `aos_yymmdd_HHMM` (예: aos_260123_1505)
- iOS 인터랙티브: `ios_YYYYMMDD_HHMMSS` (예: ios_20260215_150530)
- iOS Watch: `ios_yymmdd_HHMM` (예: ios_260215_1505)

**Watch 모드 파일명 형식:** `순번_화면이름.xml`

---

## XML 파일 구조

### 주요 속성

| 속성           | 설명                               | Appium Locator                 |
| -------------- | ---------------------------------- | ------------------------------ |
| `resource-id`  | 요소의 고유 ID                     | `AppiumBy.ID`                  |
| `content-desc` | 접근성 설명 (Accessibility ID)     | `AppiumBy.ACCESSIBILITY_ID`    |
| `text`         | 표시되는 텍스트                    | `AppiumBy.ANDROID_UIAUTOMATOR` |
| `class`        | 요소 클래스명                      | `AppiumBy.CLASS_NAME`          |
| `clickable`    | 클릭 가능 여부                     | -                              |
| `bounds`       | 요소 위치 [left,top][right,bottom] | -                              |

### XML 예시

```xml
<android.widget.Button
    index="1"
    package="com.saucelabs.mydemoapp.android"
    class="android.widget.Button"
    text="Login"
    resource-id="com.saucelabs.mydemoapp.android:id/btn_submit"
    checkable="false"
    checked="false"
    clickable="true"
    enabled="true"
    focusable="true"
    bounds="[241,1043][838,1180]"
    displayed="true"
/>
```

---

## 캡처된 화면 분석 (예시)

> 아래는 분석 결과를 정리하는 **형식 예시**입니다. 실제 SauceLabs My Demo App의
> 화면별 요소 맵은 첫 UI Dump 수집 후 채워 넣습니다. 정확한 `content-desc`/`resource-id`는
> `python tools/ui_dump.py -w`로 실제 화면을 캡처해 확인하세요.

### 001_ProductList.xml - 상품 목록 화면 (메인)

| 요소      | content-desc / resource-id | 용도           |
| --------- | -------------------------- | -------------- |
| 상품 카드 | `store item`               | 상품 상세 진입 |
| 장바구니  | `cart badge`               | 장바구니 이동  |
| 메뉴 열기 | `open menu`                | 사이드 메뉴    |

### 002_Login.xml - 로그인 화면

| 요소          | content-desc / resource-id | 클릭 가능 |
| ------------- | -------------------------- | --------- |
| 아이디 입력   | `Username input field`     | O         |
| 비밀번호 입력 | `Password input field`     | O         |
| 로그인 버튼   | `Login button`             | O         |

---

## Locator 전략

### 우선순위

1. **Accessibility ID (`content-desc`)** - 권장
    - 크로스 플랫폼 호환성
    - 언어/지역 독립적
    - 유지보수 용이

2. **Resource ID (`resource-id`)** - Fallback
    - Android 전용
    - 패키지명에 의존적

### 코드 예시

```python
from appium.webdriver.common.appiumby import AppiumBy

# 1순위: Accessibility ID
try:
    element = driver.find_element(
        AppiumBy.ACCESSIBILITY_ID,
        "cart badge"
    )
except NoSuchElementException:
    # 2순위: Resource ID
    element = driver.find_element(
        AppiumBy.ID,
        "com.saucelabs.mydemoapp.android:id/cartBadge"
    )
```

### Fallback 헬퍼 함수

> ℹ️ 아래는 **개념 예시**입니다. 실제 프로젝트는 `pages/base_page.py`의
> `find`/`find_clickable`/`click`/`input_text` 헬퍼 + Locator 우선순위(accessibility id > id >
> -android uiautomator > xpath)를 사용하며, 별도 `find_element_with_fallback` 함수는 없습니다. 실제
> 패턴은 `docs/CODING_GUIDELINES.md` 참고.

```python
def find_element_with_fallback(driver, accessibility_id, resource_id, timeout=5):
    """Accessibility ID 우선, Resource ID fallback"""

    # 1순위: Accessibility ID
    if accessibility_id:
        try:
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(
                    (AppiumBy.ACCESSIBILITY_ID, accessibility_id)
                )
            )
        except TimeoutException:
            pass

    # 2순위: Resource ID
    if resource_id:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (AppiumBy.ID, resource_id)
            )
        )

    return None
```

---

## 테스트 스크립트에서 활용

### 테스트 클래스 구조 (예시)

```python
class TestLogin:
    PACKAGE_ID = "com.saucelabs.mydemoapp.android:id"

    # XML에서 추출한 요소 정보 (예시)
    LOGIN_SCREEN_CLICKABLE_ELEMENTS = [
        {
            "accessibility_id": "Username input field",
            "id": "loginUsername",
            "name": "아이디 입력란",
            "type": "EditText"
        },
        {
            "accessibility_id": "Login button",
            "id": "loginButton",
            "name": "로그인 버튼",
            "type": "Button"
        },
        # ...
    ]
```

---

## 민감정보 자동 마스킹

UI Dump 도구는 캡처 시 **개인정보를 자동으로 마스킹**하여 저장합니다. 이를 통해 덤프 파일을 Git
저장소에 안전하게 커밋할 수 있습니다.

### 마스킹 대상

| 데이터 유형 | 원본 예시 | 마스킹 결과 |
|------------|----------|------------|
| 전화번호 (하이픈) | `010-1234-5678` | `010-****-****` |
| 전화번호 (연속) | `01012345678` | `010********` |
| 이메일 | `user@gmail.com` | `u***@g***.com` |
| 생년월일 (하이픈) | `1990-05-15` | `****-**-**` |
| 생년월일 (연속) | `19900515` | `********` |

### 자동 마스킹 동작

모든 캡처 모드에서 자동으로 마스킹이 적용됩니다:

- **단일 캡처** (`python tools/ui_dump.py`)
- **이름 지정 캡처** (`python tools/ui_dump.py screen_name`)
- **인터랙티브 모드** (`python tools/ui_dump.py -i`)
- **자동 감지 모드** (`python tools/ui_dump.py -w`)

### 기존 덤프 파일 마스킹

이미 저장된 덤프 파일들을 일괄 마스킹할 수 있습니다:

```bash
python tools/ui_dump.py --mask-existing
```

**출력 예시:**

```
기존 ui_dumps 파일 마스킹 시작...
--------------------------------------------------
마스킹 완료: ui_dumps/aos_260123_1254/024_ProductDetail.xml
마스킹 완료: ui_dumps/aos_260123_1254/027_Checkout.xml
--------------------------------------------------
총 2개 파일 마스킹 완료
```

### 테스트 코드에 미치는 영향

마스킹은 테스트 코드 작성에 **영향을 주지 않습니다**:

- 테스트에서는 `resource-id`, `content-desc` 등 **속성 기반 locator**를 사용
- 개인정보가 포함된 `text` 속성은 테스트 assertion에 사용하지 않음
- 덤프 파일은 요소 구조 파악용 **참고 자료**로만 활용

---

## 팁 & 트러블슈팅

### 1. Appium 모듈 에러

```
ModuleNotFoundError: No module named 'appium'
```

**해결:** 가상환경 활성화 필요

```bash
venv\Scripts\activate
```

### 2. 요소를 찾을 수 없음

- `ui_dump.py`로 현재 화면 캡처하여 실제 요소 확인
- 앱 업데이트로 `resource-id`나 `content-desc`가 변경됐을 수 있음

### 3. content-desc가 없는 경우

대부분의 앱에서 `content-desc`가 제대로 설정되어 있지 않음

- 개발팀에 접근성 속성 추가 요청
- `resource-id` 또는 `text` 기반 locator 사용

### 4. 동적 요소 처리

화면 로딩 후 요소가 나타나는 경우 `WebDriverWait` 사용:

```python
element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((AppiumBy.ID, "element_id"))
)
```

---

## 관련 파일

| 파일                             | 설명                                      |
| -------------------------------- | ----------------------------------------- |
| `tools/ui_dump.py`               | Android UI 덤프 도구                      |
| `tools/ui_dump_ios.py`           | iOS UI 덤프 도구                          |
| `ui_dumps/*.xml`                 | 캡처된 XML 파일들                         |
| `pages/base_page.py`             | POM 공통 페이지 기능                      |
| `conftest.py`                    | pytest fixture (driver 설정)              |
| `docs/CODING_GUIDELINES.md`      | 테스트 스크립트 작성 가이드라인           |
