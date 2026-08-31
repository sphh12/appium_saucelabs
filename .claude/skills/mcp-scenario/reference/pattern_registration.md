# 패턴 등록 절차 (#15)

`tools/mcp/codegen.py`의 `PATTERNS` 레지스트리에 새 패턴을 추가하면, 해당 시퀀스가 헬퍼 호출 한 줄로 자동 압축됩니다.

## 형식

```python
PATTERNS: list[dict[str, Any]] = [
    {
        "name": "<고유 이름>",
        "detect": <검출 함수>,
        "emit": <코드 출력 함수>,
    },
    ...
]
```

## 검출 함수 시그니처

```python
def _detect_<name>(
    actions: list[dict[str, Any]],
    prefix: str | None,
) -> tuple[int, int, dict] | None:
    """
    Args:
        actions: 시나리오 카테고리 액션만 필터된 리스트
        prefix: meta.app.resource_id_prefix

    Returns:
        매칭 시 (start_idx, end_idx, ctx)
            - start_idx, end_idx: 패턴이 점유하는 액션 인덱스 범위
            - ctx: emit 함수에 전달할 컨텍스트 dict
        매칭 안 되면 None
    """
    ...
```

## 출력 함수 시그니처

```python
def _emit_<name>(ctx: dict) -> list[str]:
    """
    Returns:
        pytest 코드 라인 리스트 (들여쓰기 4칸 포함, 각 줄 끝 개행 없음)
    """
    return [
        "    with allure.step('...'):",
        "        ...",
    ]
```

## 동작 규칙

- PATTERNS는 **선언 순서대로** 검출됨
- **한 인덱스가 한 번만 매칭** — 먼저 매칭된 패턴이 우선, 후속 패턴에서는 해당 범위 제외
- 매칭 시 `start_idx ~ end_idx` 범위의 원본 액션은 출력에서 스킵되고, `_emit_<name>` 결과로 대체됨

## 예시: 로그인 플로우 (등록 후보)

현재 기본 등록된 압축 패턴은 없습니다 (모든 scenario 액션이 raw 매핑으로 출력). 첫 패턴 등록 사례로 로그인 플로우를 권장합니다 — `examples/login_flow_template.md` 의 `_detect_login_flow` / `_emit_login_flow` 참조.

## 등록 후 검증 절차

1. **단위 검증**: 새 패턴이 적용된 시나리오 codegen 재생성 → pytest 통과 확인
   ```bash
   python tools/mcp/codegen.py sessions/<new_scenario>/
   pytest sessions/<new_scenario>/generated_test.py -v
   ```

2. **회귀 검증**: 기존 시나리오에 영향 없는지 확인
   ```bash
   python tools/mcp/codegen.py sessions/20260505_1200_login_flow/
   pytest sessions/20260505_1200_login_flow/generated_test.py -v
   ```

3. **CHANGELOG.md 갱신**: 새 패턴 추가 사실 기록

## 패턴 등록 후보 (TODO)

- [ ] `login_flow` — 아이디/비밀번호 입력 + 로그인 버튼 → `login()`
- [ ] `add_to_cart` — 상품 선택 + 장바구니 담기 시퀀스
- [ ] `checkout` — 배송정보 입력 + 결제 시퀀스
- [ ] `logout` — 메뉴 → 로그아웃 버튼 시퀀스
