# actions.jsonl 포맷 명세

각 줄이 하나의 JSON 액션. **append-only**라 도중 크래시에도 안전.

## 공통 필수 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `seq` | int | 순차 번호 (1부터) |
| `ts` | string | ISO 시각 (초 단위) |
| `prompt` | string | 사용자 프롬프트 원문 |
| `action` | string | 액션 종류 (아래 목록) |
| `status` | string | success / failure |
| `category` | string | observation / exploration / scenario |
| `include_in_test` | bool | codegen 포함 여부 (자동 판정: scenario만 true) |

## 액션 종류별 추가 필드

### `tap`
```json
{
  "action": "tap",
  "strategy": "id",
  "selector": "com.saucelabs.mydemoapp.android:id/loginButton",
  "element_uuid": "00000000-...",
  "screenshot_after": "screenshots/001_after.png"
}
```

### `press_key`
```json
{
  "action": "press_key",
  "key": "BACK",
  "keycode": 4
}
```
지원 키: `BACK` (4), `HOME` (3), `APP_SWITCH` (187)

### `set_value` (텍스트 입력)
```json
{
  "action": "set_value",
  "strategy": "id",
  "selector": "com.saucelabs.mydemoapp.android:id/loginUsername",
  "params": {"value": "user123"}
}
```

마스킹 후:
```json
{
  "action": "set_value",
  "strategy": "id",
  "selector": "com.saucelabs.mydemoapp.android:id/loginPassword",
  "params": {"value_from": "TEST_PW"},
  "note": "[masked]"
}
```

### `swipe` / `scroll`
```json
{
  "action": "swipe",
  "direction": "up",
  "params": {"duration": 800}
}
```

### `wait`
```json
{
  "action": "wait",
  "params": {"seconds": 3}
}
```

### `verify`
```json
{
  "action": "verify",
  "verifications": [
    {
      "strategy": "id",
      "selector": "com.saucelabs.mydemoapp.android:id/loginButton",
      "expected_text": "Login"
    }
  ]
}
```

### `screenshot` / `get_page_source` (observation)
```json
{
  "action": "get_page_source",
  "result_path": "page_sources/004_login_screen.xml",
  "category": "observation",
  "include_in_test": false
}
```

## Locator 전략 (strategy)

| strategy 값 | AppiumBy |
|-------------|----------|
| `accessibility id` | `AppiumBy.ACCESSIBILITY_ID` |
| `id` | `AppiumBy.ID` |
| `-android uiautomator` | `AppiumBy.ANDROID_UIAUTOMATOR` |
| `-ios predicate string` | `AppiumBy.IOS_PREDICATE` |
| `-ios class chain` | `AppiumBy.IOS_CLASS_CHAIN` |
| `xpath` | `AppiumBy.XPATH` |

우선순위: ACCESSIBILITY_ID > ID > 플랫폼 네이티브 > XPATH (최후)

## 카테고리 분류 가이드

| 사용자 프롬프트 예시 | 자동 분류 |
|---------------------|----------|
| "스크린샷 보여줘", "캡처해줘", "확인해줘" | `observation` |
| "다른 화면 가서 봐봐", "잠깐 다른 거 보여줘" | `exploration` |
| "탭", "입력", "스와이프", "선택", "검증" | `scenario` |

> 분류가 잘못된 경우 "분류 변경: seq <N> <카테고리>" 트리거로 즉시 수정 가능.

## 안전 정책

- **민감정보**: `set_value`의 평문 값은 `mask-secrets`로 즉시 환경변수 키 치환 권장
- **append-only**: actions.jsonl은 추가만 — 수정은 `update-category`, `mask-secrets`만 허용
- **JSON Lines**: 각 줄이 독립적인 JSON, 도중 크래시에도 이전 액션 보존
