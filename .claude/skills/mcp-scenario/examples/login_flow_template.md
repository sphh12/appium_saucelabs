# 템플릿: 로그인 시나리오 (PATTERNS 등록 예시)

> 상태: 템플릿 (검증 미완료) — PATTERNS 등록의 첫 사례로 활용 권장
> 대상: SauceLabs My Demo App

## 목표

아이디/비밀번호 입력 후 로그인 버튼 탭 → 메인(로그인 후) 화면 확인.
복잡한 시퀀스를 `login()` 헬퍼 한 줄로 압축할 수 있도록 PATTERNS 등록.

## 대화 흐름

### 1. 시나리오 시작

```
사용자: 시나리오 시작: login_flow
Claude: [session_recorder.py start login_flow]
```

### 2. 비밀번호 입력 시 마스킹

```
사용자: 사용자 ID 입력란에 TEST_USER 환경변수 값 입력해줘
Claude: [appium_set_value 입력]
        → actions.jsonl seq=1: action=set_value, params={"value": "<실제ID>"}

사용자: 비밀번호 마스킹: <실제ID>=TEST_USER
Claude: [session_recorder.py mask-secrets --map "<실제ID>=TEST_USER"]
        → seq=1 액션이 params={"value_from": "TEST_USER"} 로 변환됨
```

(비밀번호도 동일하게 처리)

### 3. 로그인 버튼 탭

```
사용자: Login 버튼 탭
Claude: [appium_gesture tap on loginButton]
```

### 4. 시나리오 종료

```
사용자: 시나리오 종료
Claude: [session_recorder.py end --generate]
```

## codegen 결과 (PATTERNS 등록 전)

```python
def test_login_flow(android_driver):
    driver = android_driver

    with allure.step("사용자 ID 입력"):
        elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (AppiumBy.ID, f"{RESOURCE_ID_PREFIX}/loginUsername")
        ))
        elem.send_keys(os.getenv("TEST_USER", ""))

    with allure.step("비밀번호 입력"):
        elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (AppiumBy.ID, f"{RESOURCE_ID_PREFIX}/loginPassword")
        ))
        elem.send_keys(os.getenv("TEST_PW", ""))

    with allure.step("Login 버튼 탭"):
        elem = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (AppiumBy.ID, f"{RESOURCE_ID_PREFIX}/loginButton")
        ))
        elem.click()
```

## codegen 결과 (PATTERNS 등록 후 — 목표 압축 형태)

```python
def test_login_flow(android_driver):
    driver = android_driver

    with allure.step("로그인"):
        from utils.helpers import login
        login(
            driver,
            username=os.getenv("TEST_USER", ""),
            password=os.getenv("TEST_PW", ""),
            resource_id_prefix=RESOURCE_ID_PREFIX,
        )
```

## PATTERNS 등록 절차

`tools/mcp/codegen.py` 수정:

```python
def _detect_login_flow(actions, prefix):
    """ID 입력 + 비밀번호 입력 + 로그인 버튼 탭 시퀀스 검출."""
    if not prefix:
        return None
    user_id_sel = f"{prefix}/loginUsername"
    pw_sel = f"{prefix}/loginPassword"
    login_btn_sel = f"{prefix}/loginButton"

    for i, a in enumerate(actions):
        if (a.get("action") == "set_value"
                and a.get("selector") == user_id_sel):
            user_env = (a.get("params") or {}).get("value_from")

            for j in range(i + 1, len(actions)):
                b = actions[j]
                if (b.get("action") == "set_value"
                        and b.get("selector") == pw_sel):
                    pw_env = (b.get("params") or {}).get("value_from")

                    for k in range(j + 1, len(actions)):
                        c = actions[k]
                        if (c.get("action") == "tap"
                                and c.get("selector") == login_btn_sel):
                            return (i, k, {
                                "username_env": user_env or "TEST_USER",
                                "password_env": pw_env or "TEST_PW",
                            })
                    break
            break
    return None


def _emit_login_flow(ctx):
    return [
        f"    with allure.step('로그인'):",
        f"        from utils.helpers import login",
        f"        login(",
        f"            driver,",
        f"            username=os.getenv({_q(ctx['username_env'])}, ''),",
        f"            password=os.getenv({_q(ctx['password_env'])}, ''),",
        f"            resource_id_prefix=RESOURCE_ID_PREFIX,",
        f"        )",
    ]


# PATTERNS 리스트에 추가
PATTERNS.append({
    "name": "login_flow",
    "detect": _detect_login_flow,
    "emit": _emit_login_flow,
})
```

> 셀렉터(`loginUsername`, `loginPassword`, `loginButton`)는 실제 앱의 resource-id/accessibility id로 확인 후 수정. UI 덤프(`tools/ui_dump.py`)로 확인.

## 검증 절차

1. 위 PATTERNS 추가 후 시나리오 codegen 재생성: `python tools/mcp/codegen.py sessions/<login_flow>/`
2. `pytest sessions/<id>/generated_test.py -v`로 통과 확인
3. **회귀 검증**: 다른 세션도 codegen 재생성 → 영향 없는지 확인
