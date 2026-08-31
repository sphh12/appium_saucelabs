# 예시: 상품 장바구니 담기 시나리오

> 대상: SauceLabs My Demo App
> 상태: 예시 워크스루 (실제 셀렉터는 UI 덤프로 확인 필요)

## 목표

상품 목록에서 상품을 선택 → 장바구니에 담기 → 장바구니 배지 수량이 증가했는지 검증.

## 대화 흐름

### 1. 시나리오 시작

```
사용자: 시나리오 시작: add_to_cart
Claude: [session_recorder.py start add_to_cart]
        → sessions/<timestamp>_add_to_cart/ 생성
        → meta.json: app=com.saucelabs.mydemoapp.android, prefix=com.saucelabs.mydemoapp.android:id
```

### 2. 액션 녹화

```
사용자: 상품 목록 스크린샷 보여줘
Claude: [appium_screenshot] → category=observation 자동 분류 (테스트 미포함)

사용자: 첫 번째 상품 탭해줘
Claude: [appium_find_element accessibility id="store item"]
        [appium_gesture tap]
        → category=scenario 자동 분류, actions.jsonl seq=1 추가

사용자: 장바구니 담기 버튼 탭해줘
Claude: [appium_find_element accessibility id="Add To Cart button"]
        [appium_gesture tap]
        → seq=2 추가

사용자: 검증 추가: cart badge = 1
Claude: [session_recorder.py add-verify --selector "cart badge" --expected 1]
        → seq=3 추가 (verify 액션)
```

### 3. 시나리오 종료

```
사용자: 시나리오 종료
Claude: [session_recorder.py end --generate --raw]
        → generated_test.py + generated_test_raw.py 자동 생성
        → "테스트 실행: 최신"으로 검증 권장
```

### 4. 회귀 검증

```
사용자: 테스트 실행: 최신
Claude: [pytest sessions/<id>/generated_test.py -v]
```

### 5. 정식 등록

```
사용자: 테스트 정식 등록: add_to_cart cart
Claude: [session_recorder.py promote --session-dir <id> --subdir cart]
        → tests/android/cart/add_to_cart_test.py 로 이동
```

## 생성된 코드 (raw 매핑)

```python
"""
[Auto-generated] 상품을 장바구니에 담고 배지 수량 검증
생성 시각: 20260505_120000
버전: RAW (1:1 매핑)
"""
import os

import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.capabilities import ANDROID_PACKAGE

RESOURCE_ID_PREFIX = f"{ANDROID_PACKAGE}:id"


@allure.feature("Auto-generated Scenario")
@allure.story("add_to_cart")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.android
def test_add_to_cart(android_driver):
    """상품을 장바구니에 담고 배지 수량 검증"""
    driver = android_driver

    with allure.step("첫 번째 상품 탭"):
        elem = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (AppiumBy.ACCESSIBILITY_ID, "store item")
        ))
        elem.click()

    with allure.step("장바구니 담기 버튼 탭"):
        elem = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (AppiumBy.ACCESSIBILITY_ID, "Add To Cart button")
        ))
        elem.click()

    with allure.step("결과 검증"):
        elem = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "cart badge")
        assert elem.text == "1", f"기대값과 다름: {elem.text!r}"
```

## 핵심 학습 포인트

1. **카테고리 분류는 사용자 의도 기준** — "보여줘"는 observation, "탭"은 scenario
2. **검증 단계는 명시 추가가 안전** — 자동 추론은 누락 가능
3. **현재 등록된 압축 패턴 없음** — 모든 scenario 액션이 raw 매핑으로 출력됨. 로그인 등 반복 시퀀스는 `login_flow_template.md`를 참고해 PATTERNS에 등록 가능
4. **셀렉터는 예시** — `store item`, `Add To Cart button`, `cart badge` 등 실제 값은 `python tools/ui_dump.py -w`로 확인
