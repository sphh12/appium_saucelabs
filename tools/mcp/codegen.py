"""MCP 액션 로그 → pytest 코드 변환기.

`sessions/<id>/actions.jsonl` + `meta.json` 을 입력받아
- generated_test.py     (압축 모드, utils 패턴 인식 적용)
- generated_test_raw.py (raw 모드, 1:1 매핑) [--raw 옵션 시]
를 출력합니다.

CLI 사용 예시:
    python tools/mcp/codegen.py sessions/20260505_1200_login_flow/
    python tools/mcp/codegen.py <session_dir> --raw
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


# ─────────────────────────────────────────────
# 데이터 로딩
# ─────────────────────────────────────────────


def _load_session(session_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """meta.json + actions.jsonl 로드."""
    meta_path = session_dir / "meta.json"
    actions_path = session_dir / "actions.jsonl"
    if not meta_path.exists():
        raise FileNotFoundError(f"meta.json 미발견: {meta_path}")
    if not actions_path.exists():
        raise FileNotFoundError(f"actions.jsonl 미발견: {actions_path}")

    meta = json.loads(meta_path.read_text())
    actions: list[dict[str, Any]] = []
    for line in actions_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        actions.append(json.loads(line))
    return meta, actions


def _scenario_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """category=scenario + status=success + include_in_test=True만 필터."""
    return [
        a
        for a in actions
        if a.get("include_in_test", a.get("category") == "scenario")
        and a.get("status", "success") == "success"
    ]


# ─────────────────────────────────────────────
# Locator 변환
# ─────────────────────────────────────────────

_STRATEGY_TO_BY = {
    "accessibility id": "AppiumBy.ACCESSIBILITY_ID",
    "id": "AppiumBy.ID",
    "-android uiautomator": "AppiumBy.ANDROID_UIAUTOMATOR",
    "-ios predicate string": "AppiumBy.IOS_PREDICATE",
    "-ios class chain": "AppiumBy.IOS_CLASS_CHAIN",
    "xpath": "AppiumBy.XPATH",
    "name": "AppiumBy.NAME",
    "class name": "AppiumBy.CLASS_NAME",
}


def _selector_to_code(strategy: str, selector: str, prefix: str | None) -> tuple[str, str]:
    """(by_const, selector_python_literal) 반환.

    resource_id_prefix가 selector 앞부분과 정확히 일치하면 변수로 치환.
    """
    by = _STRATEGY_TO_BY.get(strategy, "AppiumBy.XPATH")
    sel = selector

    if strategy == "id" and prefix and selector.startswith(f"{prefix}/"):
        suffix = selector[len(prefix) + 1 :]
        sel_code = f'f"{{RESOURCE_ID_PREFIX}}/{suffix}"'
    else:
        # 안전한 escape
        escaped = selector.replace("\\", "\\\\").replace('"', '\\"')
        sel_code = f'"{escaped}"'

    return by, sel_code


# ─────────────────────────────────────────────
# 액션 → pytest 코드 라인 변환
# ─────────────────────────────────────────────


def _emit_action_raw(action: dict[str, Any], prefix: str | None) -> list[str]:
    """raw 모드: 액션 1건을 1:1 매핑."""
    kind = action.get("action")
    lines: list[str] = []
    step_name = action.get("prompt") or kind

    if kind == "tap":
        by, sel = _selector_to_code(action["strategy"], action["selector"], prefix)
        lines.append(f"    with allure.step({_q(step_name)}):")
        lines.append(
            f"        elem = WebDriverWait(driver, 10).until("
            f"EC.element_to_be_clickable(({by}, {sel})))"
        )
        lines.append("        elem.click()")

    elif kind == "press_key":
        key = action.get("key", "BACK")
        keymap = {"BACK": 4, "HOME": 3, "APP_SWITCH": 187}
        keycode = keymap.get(key, 4)
        lines.append(f"    with allure.step({_q(step_name)}):")
        lines.append(f"        driver.press_keycode({keycode})  # {key}")

    elif kind == "set_value":
        by, sel = _selector_to_code(action["strategy"], action["selector"], prefix)
        params = action.get("params", {}) or {}
        value_from = params.get("value_from")
        value = params.get("value", "")
        lines.append(f"    with allure.step({_q(step_name)}):")
        lines.append(
            f"        elem = WebDriverWait(driver, 10).until("
            f"EC.presence_of_element_located(({by}, {sel})))"
        )
        if value_from:
            # 환경변수 키만 저장된 경우 (mask-secrets 적용된 액션)
            lines.append(
                f"        elem.send_keys(os.getenv({_q(value_from)}, ''))"
            )
        else:
            lines.append(f"        elem.send_keys({_q(value)})")

    elif kind == "wait":
        sec = action.get("params", {}).get("seconds", 1)
        lines.append(f"    with allure.step({_q(step_name)}):")
        lines.append(f"        time.sleep({sec})")

    elif kind == "verify":
        verifications = action.get("verifications", [])
        if verifications:
            lines.append(f"    with allure.step({_q(step_name)}):")
            for v in verifications:
                by, sel = _selector_to_code(v["strategy"], v["selector"], prefix)
                expected = v.get("expected_text")
                if expected is not None:
                    lines.append(
                        f"        elem = driver.find_element({by}, {sel})"
                    )
                    lines.append(
                        f"        assert elem.text == {_q(expected)}, "
                        f"f\"기대값과 다름: {{elem.text!r}}\""
                    )

    elif kind in ("screenshot", "get_page_source"):
        # observation류는 raw에서도 보통 제외되지만 명시 호출 시 그대로 남김
        lines.append(f"    # [{kind}] {step_name}")

    else:
        lines.append(f"    # TODO unhandled action: {kind} — {step_name}")

    return lines


# ─────────────────────────────────────────────
# 압축 모드 패턴 인식기 (Trigger #15: 패턴 등록 인터페이스)
# ─────────────────────────────────────────────
#
# 새 패턴을 등록하려면:
#   1) `_detect_<name>(actions, prefix) -> (start_idx, end_idx, ctx) | None` 정의
#   2) `_emit_<name>(ctx) -> list[str]` 정의 (들여쓰기 4칸 포함된 라인)
#   3) PATTERNS 리스트에 {"name", "detect", "emit"} 추가
#
# 패턴은 위에서 아래로 순차 적용되며, 한 번 매칭된 인덱스 범위는 후속 패턴에서 제외됨.


# 패턴 레지스트리: 새 패턴 추가는 여기에 한 줄 추가
# (현재 등록된 압축 패턴 없음 — 모든 scenario 액션이 raw 매핑으로 출력됨)
PATTERNS: list[dict[str, Any]] = [
    # 향후 추가 후보 (SauceLabs My Demo App):
    # {"name": "login_flow", "detect": _detect_login, "emit": _emit_login},
    # {"name": "add_to_cart", "detect": _detect_cart, "emit": _emit_cart},
]


# ─────────────────────────────────────────────
# 코드 생성
# ─────────────────────────────────────────────


def _q(s: str) -> str:
    """Python 문자열 리터럴로 안전 escape."""
    return json.dumps(s, ensure_ascii=False)


def _function_name(meta: dict[str, Any]) -> str:
    raw = meta.get("session_name") or "scenario"
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", raw).strip("_") or "scenario"
    return f"test_{safe}"


def _header(meta: dict[str, Any], variant: str) -> list[str]:
    intent = meta.get("intent") or meta.get("session_name", "")
    started = meta.get("started_at", "")
    return [
        '"""',
        f"[Auto-generated] {intent}",
        "",
        f"원본 세션: {meta.get('session_name', '')}",
        f"생성 시각: {started}",
        f"버전: {variant}",
        '"""',
    ]


def _imports(needs_time: bool) -> list[str]:
    lines = ["import os"]
    if needs_time:
        lines.append("import time")
    lines += [
        "",
        "import allure",
        "import pytest",
        "from appium.webdriver.common.appiumby import AppiumBy",
        "from selenium.webdriver.support import expected_conditions as EC",
        "from selenium.webdriver.support.ui import WebDriverWait",
        "",
        "from config.capabilities import ANDROID_PACKAGE",
    ]
    return lines


def _generate_raw(meta: dict[str, Any], scenario: list[dict[str, Any]]) -> str:
    prefix = meta.get("app", {}).get("resource_id_prefix")
    needs_time = any(a.get("action") == "wait" for a in scenario)

    lines: list[str] = []
    lines += _header(meta, "RAW (1:1 매핑)")
    lines += _imports(needs_time)
    lines += [
        "",
        'RESOURCE_ID_PREFIX = f"{ANDROID_PACKAGE}:id"',
        "",
        "",
        '@allure.feature("Auto-generated Scenario")',
        f'@allure.story({_q(meta.get("session_name", ""))})',
        '@allure.severity(allure.severity_level.NORMAL)',
        '@pytest.mark.android',
        f'def {_function_name(meta)}_raw(android_driver):',
        f'    """{meta.get("intent", meta.get("session_name", ""))}"""',
        "    driver = android_driver",
        "",
    ]

    for action in scenario:
        lines += _emit_action_raw(action, prefix)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _generate_compressed(meta: dict[str, Any], scenario: list[dict[str, Any]]) -> str:
    prefix = meta.get("app", {}).get("resource_id_prefix")

    # 패턴 인식 (PATTERNS 레지스트리 순회)
    skipped: set[int] = set()
    helper_calls: list[tuple[int, list[str]]] = []  # (insert_at_idx, lines)

    for pat in PATTERNS:
        match = pat["detect"](scenario, prefix)
        if match is None:
            continue
        start, end, ctx = match
        # 이미 다른 패턴이 점유한 인덱스면 스킵
        if any(k in skipped for k in range(start, end + 1)):
            continue
        for k in range(start, end + 1):
            skipped.add(k)
        helper_calls.append((start, pat["emit"](ctx)))

    needs_time = any(
        a.get("action") == "wait"
        for i, a in enumerate(scenario)
        if i not in skipped
    )

    lines: list[str] = []
    lines += _header(meta, "압축 (utils 패턴 인식)")
    lines += _imports(needs_time)
    lines += [
        "",
        'RESOURCE_ID_PREFIX = f"{ANDROID_PACKAGE}:id"',
        "",
        "",
        '@allure.feature("Auto-generated Scenario")',
        f'@allure.story({_q(meta.get("session_name", ""))})',
        '@allure.severity(allure.severity_level.NORMAL)',
        '@pytest.mark.android',
        f'def {_function_name(meta)}(android_driver):',
        f'    """{meta.get("intent", meta.get("session_name", ""))}"""',
        "    driver = android_driver",
        "",
    ]

    for i, action in enumerate(scenario):
        # helper 삽입 시점
        for at_idx, helper_lines in helper_calls:
            if i == at_idx:
                lines += helper_lines
                lines.append("")
        if i in skipped:
            continue
        lines += _emit_action_raw(action, prefix)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ─────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────


def generate_test_files(session_dir: Path, raw: bool = False) -> list[Path]:
    """세션 폴더에 generated_test.py / generated_test_raw.py 작성.

    Returns:
        생성된 파일 경로 리스트
    """
    meta, actions = _load_session(session_dir)
    scenario = _scenario_actions(actions)
    if not scenario:
        raise ValueError(
            "scenario 카테고리 액션이 없습니다 (include_in_test=true). codegen 실행 불가."
        )

    outputs: list[Path] = []

    compressed_path = session_dir / "generated_test.py"
    compressed_path.write_text(_generate_compressed(meta, scenario))
    outputs.append(compressed_path)

    if raw:
        raw_path = session_dir / "generated_test_raw.py"
        raw_path.write_text(_generate_raw(meta, scenario))
        outputs.append(raw_path)

    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MCP 액션 로그 → pytest 코드 변환기")
    parser.add_argument("session_dir", help="sessions/<id>/ 경로")
    parser.add_argument("--raw", action="store_true", help="raw 1:1 매핑 코드도 함께 생성")
    args = parser.parse_args(argv)

    session_dir = Path(args.session_dir).resolve()
    outputs = generate_test_files(session_dir, raw=args.raw)
    for p in outputs:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
