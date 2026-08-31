"""MCP 시나리오 녹화기 (Session Recorder).

사용자 프롬프트 기반 MCP 자동화 동작을 세션 단위로 기록하여
나중에 pytest 코드(`tools/mcp/codegen.py`)로 변환할 수 있게 합니다.

세션 폴더 구조:
    sessions/<timestamp>_<name>/
        ├── meta.json
        ├── prompts.md
        ├── actions.jsonl           (append-only 액션 로그)
        ├── screenshots/
        ├── page_sources/
        └── generated_test*.py       (codegen 출력)

대상 앱: SauceLabs My Demo App (단일 환경, `apps/android/`)

CLI 사용 예시:
    # 1. 시나리오 시작
    python tools/mcp/session_recorder.py start "login_flow"

    # 2. 액션 추가 (MCP 측에서 호출)
    python tools/mcp/session_recorder.py log \
        --action tap --strategy "accessibility id" \
        --selector "Login button" \
        --prompt "로그인 버튼 탭" --category scenario \
        --screenshot-after /path/to/img.png

    # 3. 활성 세션 조회
    python tools/mcp/session_recorder.py active

    # 4. 시나리오 종료 (codegen 자동 실행)
    python tools/mcp/session_recorder.py end --generate
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 프로젝트 루트 sys.path 등록
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config.capabilities import (  # noqa: E402  # pylint: disable=wrong-import-position
    ANDROID_CAPS,
    ANDROID_APP_PATH,
    ANDROID_PACKAGE,
    APPIUM_HOST,
    APPIUM_PORT,
)

SESSIONS_ROOT = PROJECT_ROOT / "sessions"
ACTIVE_FILE = PROJECT_ROOT / "sessions" / ".active_session"

VALID_CATEGORIES = ("observation", "exploration", "scenario")


# ─────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────


def _now_iso() -> str:
    """현재 시각 ISO 포맷 (초 단위)."""
    return datetime.now().replace(microsecond=0).isoformat()


def _now_compact() -> str:
    """타임스탬프 (YYYYMMDD_HHMMSS)."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_name(name: str) -> str:
    """파일/폴더명용 안전한 문자열로 변환."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip("_")


def _read_active() -> Path | None:
    """활성 세션 폴더 경로 반환."""
    if not ACTIVE_FILE.exists():
        return None
    path = Path(ACTIVE_FILE.read_text().strip())
    return path if path.exists() else None


def _write_active(session_dir: Path) -> None:
    ACTIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.write_text(str(session_dir))


def _clear_active() -> None:
    if ACTIVE_FILE.exists():
        ACTIVE_FILE.unlink()


def _resolve_caps() -> dict[str, Any]:
    """단일 환경 capabilities 생성 (SauceLabs My Demo App).

    config/capabilities.py 의 ANDROID_CAPS / ANDROID_APP_PATH / ANDROID_PACKAGE
    를 그대로 사용합니다 (환경 분기 없음).
    """
    if not ANDROID_APP_PATH:
        raise FileNotFoundError(
            "apps/android/ 폴더에 앱(.apk) 파일이 없습니다."
        )

    caps = {**ANDROID_CAPS, "app": ANDROID_APP_PATH}
    return {
        "platform": "android",
        "capabilities": caps,
        "resource_id_prefix": f"{ANDROID_PACKAGE}:id",
        "appium_server_url": f"http://{APPIUM_HOST}:{APPIUM_PORT}",
    }


# ─────────────────────────────────────────────
# 명령: start / log / active / end
# ─────────────────────────────────────────────


def cmd_start(args: argparse.Namespace) -> int:
    """시나리오 시작."""
    name = _safe_name(args.name)
    if not name:
        print("ERROR: 시나리오 이름이 비어있습니다.", file=sys.stderr)
        return 2

    if _read_active() is not None:
        print(
            "ERROR: 이미 활성 세션이 있습니다. 'end'로 종료 후 새로 시작하세요.",
            file=sys.stderr,
        )
        return 3

    session_dir = SESSIONS_ROOT / f"{_now_compact()}_{name}"
    (session_dir / "screenshots").mkdir(parents=True, exist_ok=True)
    (session_dir / "page_sources").mkdir(parents=True, exist_ok=True)

    env_caps = _resolve_caps()

    meta = {
        "session_name": name,
        "started_at": _now_iso(),
        "ended_at": None,
        "platform": "android",
        "device": {
            "udid": os.getenv("ANDROID_UDID") or "emulator-5554",
            "deviceName": ANDROID_CAPS.get("deviceName", "Android Emulator"),
            "automationName": ANDROID_CAPS.get("automationName", "UiAutomator2"),
        },
        "app": {
            "package": ANDROID_PACKAGE,
            "apk_path": env_caps["capabilities"]["app"],
            "resource_id_prefix": env_caps["resource_id_prefix"],
        },
        "capabilities": env_caps["capabilities"],
        "appium_server_url": env_caps["appium_server_url"],
        "intent": args.intent or "",
        "notes": args.notes or "",
    }

    meta_path = session_dir / "meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    prompts_path = session_dir / "prompts.md"
    prompts_path.write_text(
        "# 사용자 프롬프트 로그\n\n"
        f"> 세션: `{name}`\n"
        f"> 시작: {_now_iso()}\n\n"
        "## 프롬프트 시퀀스\n\n"
        "| Seq | 시각 | 프롬프트 (원문) | 분류 |\n"
        "|-----|------|----------------|------|\n"
    )

    (session_dir / "actions.jsonl").touch()
    _write_active(session_dir)

    # stdout으로 세션 폴더 경로 반환 (호출 측에서 캡처)
    print(json.dumps({"status": "started", "session_dir": str(session_dir)}, ensure_ascii=False))
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    """액션 1건 추가 (actions.jsonl 추가만 — 안전)."""
    session_dir = _read_active()
    if session_dir is None:
        print("ERROR: 활성 세션이 없습니다. 먼저 'start'로 시작하세요.", file=sys.stderr)
        return 4

    actions_path = session_dir / "actions.jsonl"
    seq = sum(1 for _ in actions_path.open()) + 1 if actions_path.exists() else 1

    entry: dict[str, Any] = {
        "seq": seq,
        "ts": _now_iso(),
        "prompt": args.prompt or "",
        "action": args.action,
        "status": args.status or "success",
        "category": args.category or "scenario",
    }

    if args.strategy:
        entry["strategy"] = args.strategy
    if args.selector:
        entry["selector"] = args.selector
    if args.element_uuid:
        entry["element_uuid"] = args.element_uuid
    if args.key:
        entry["key"] = args.key
    if args.duration_ms is not None:
        entry["duration_ms"] = args.duration_ms
    if args.screenshot_before:
        entry["screenshot_before"] = args.screenshot_before
    if args.screenshot_after:
        entry["screenshot_after"] = args.screenshot_after
    if args.page_source_before:
        entry["page_source_before"] = args.page_source_before
    if args.params_json:
        try:
            entry["params"] = json.loads(args.params_json)
        except json.JSONDecodeError as e:
            print(f"ERROR: --params-json 파싱 실패: {e}", file=sys.stderr)
            return 5
    if args.note:
        entry["note"] = args.note

    if entry["category"] not in VALID_CATEGORIES:
        print(
            f"ERROR: category는 {', '.join(VALID_CATEGORIES)} 중 하나여야 합니다.",
            file=sys.stderr,
        )
        return 6

    # include_in_test 자동 판정 (scenario만 포함)
    entry["include_in_test"] = entry["category"] == "scenario"

    with actions_path.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # prompts.md에도 한 줄 추가 (사용자 가독성)
    prompts_path = session_dir / "prompts.md"
    if args.prompt:
        with prompts_path.open("a") as f:
            f.write(
                f"| {seq} | {entry['ts'].split('T')[1]} | "
                f"`{args.prompt[:80]}` | {entry['category']} |\n"
            )

    print(json.dumps({"status": "logged", "seq": seq}, ensure_ascii=False))
    return 0


def cmd_active(_: argparse.Namespace) -> int:
    """현재 활성 세션 정보 출력."""
    session_dir = _read_active()
    if session_dir is None:
        print(json.dumps({"status": "no_active_session"}, ensure_ascii=False))
        return 0

    meta_path = session_dir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    actions_path = session_dir / "actions.jsonl"
    action_count = sum(1 for _ in actions_path.open()) if actions_path.exists() else 0

    print(
        json.dumps(
            {
                "status": "active",
                "session_dir": str(session_dir),
                "meta": meta,
                "action_count": action_count,
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_end(args: argparse.Namespace) -> int:
    """시나리오 종료 + (옵션) codegen 자동 실행."""
    session_dir = _read_active()
    if session_dir is None:
        print("ERROR: 활성 세션이 없습니다.", file=sys.stderr)
        return 4

    meta_path = session_dir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta["ended_at"] = _now_iso()
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    _clear_active()

    result: dict[str, Any] = {
        "status": "ended",
        "session_dir": str(session_dir),
    }

    if args.generate:
        from tools.mcp.codegen import generate_test_files  # 지연 import

        outputs = generate_test_files(session_dir, raw=args.raw)
        result["generated"] = [str(p) for p in outputs]

    print(json.dumps(result, ensure_ascii=False))
    return 0


# ─────────────────────────────────────────────
# 보조 명령들 (Trigger #1~#8 + #17 지원)
# ─────────────────────────────────────────────


def _load_actions(session_dir: Path) -> list[dict[str, Any]]:
    """actions.jsonl 전체 로드."""
    actions_path = session_dir / "actions.jsonl"
    if not actions_path.exists():
        return []
    return [
        json.loads(line)
        for line in actions_path.read_text().splitlines()
        if line.strip()
    ]


def _save_actions(session_dir: Path, actions: list[dict[str, Any]]) -> None:
    """actions.jsonl 전체 재작성 (수정 후)."""
    actions_path = session_dir / "actions.jsonl"
    actions_path.write_text(
        "\n".join(json.dumps(a, ensure_ascii=False) for a in actions) + "\n"
    )


def cmd_list(args: argparse.Namespace) -> int:
    """모든 세션 목록 + 상태 (Trigger #6)."""
    if not SESSIONS_ROOT.exists():
        print(json.dumps({"sessions": []}, ensure_ascii=False))
        return 0

    active = _read_active()
    sessions: list[dict[str, Any]] = []
    for d in sorted(SESSIONS_ROOT.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        meta_path = d / "meta.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        actions = _load_actions(d)
        sessions.append({
            "session_dir": str(d),
            "name": meta.get("session_name", d.name),
            "env": meta.get("env"),
            "started_at": meta.get("started_at"),
            "ended_at": meta.get("ended_at"),
            "active": active is not None and active.resolve() == d.resolve(),
            "paused": meta.get("paused", False),
            "aborted": d.name.endswith("_aborted"),
            "action_count": len(actions),
            "scenario_count": sum(1 for a in actions if a.get("category") == "scenario"),
            "has_generated_test": (d / "generated_test.py").exists(),
        })
    print(json.dumps({"sessions": sessions}, ensure_ascii=False, indent=2))
    return 0


def cmd_abort(args: argparse.Namespace) -> int:
    """활성 세션 폐기 (Trigger #5)."""
    session_dir = _read_active()
    if session_dir is None:
        print("ERROR: 활성 세션이 없습니다.", file=sys.stderr)
        return 4

    aborted_dir = session_dir.with_name(session_dir.name + "_aborted")
    session_dir.rename(aborted_dir)
    _clear_active()
    print(json.dumps(
        {"status": "aborted", "session_dir": str(aborted_dir)},
        ensure_ascii=False,
    ))
    return 0


def _toggle_pause(pause: bool) -> int:
    """일시정지/재개 공통 처리 (Trigger #4)."""
    session_dir = _read_active()
    if session_dir is None:
        print("ERROR: 활성 세션이 없습니다.", file=sys.stderr)
        return 4
    meta_path = session_dir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta["paused"] = pause
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(json.dumps(
        {"status": "paused" if pause else "resumed", "session_dir": str(session_dir)},
        ensure_ascii=False,
    ))
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    return _toggle_pause(True)


def cmd_resume(args: argparse.Namespace) -> int:
    return _toggle_pause(False)


def cmd_update_category(args: argparse.Namespace) -> int:
    """특정 액션의 카테고리 변경 (Trigger #1)."""
    session_dir = _read_active() if not args.session_dir else Path(args.session_dir)
    if session_dir is None or not session_dir.exists():
        print("ERROR: 세션 폴더를 찾을 수 없습니다.", file=sys.stderr)
        return 4
    if args.category not in VALID_CATEGORIES:
        print(
            f"ERROR: category는 {', '.join(VALID_CATEGORIES)} 중 하나여야 합니다.",
            file=sys.stderr,
        )
        return 6

    actions = _load_actions(session_dir)
    target = next((a for a in actions if a.get("seq") == args.seq), None)
    if target is None:
        print(f"ERROR: seq={args.seq} 액션을 찾을 수 없습니다.", file=sys.stderr)
        return 7

    target["category"] = args.category
    target["include_in_test"] = args.category == "scenario"
    _save_actions(session_dir, actions)
    print(json.dumps(
        {
            "status": "updated",
            "seq": args.seq,
            "new_category": args.category,
            "include_in_test": target["include_in_test"],
        },
        ensure_ascii=False,
    ))
    return 0


def cmd_add_verify(args: argparse.Namespace) -> int:
    """검증 액션 추가 (Trigger #3)."""
    session_dir = _read_active()
    if session_dir is None:
        print("ERROR: 활성 세션이 없습니다.", file=sys.stderr)
        return 4

    actions_path = session_dir / "actions.jsonl"
    seq = sum(1 for _ in actions_path.open()) + 1 if actions_path.exists() else 1

    entry = {
        "seq": seq,
        "ts": _now_iso(),
        "prompt": args.prompt or f"검증: {args.selector} = {args.expected}",
        "action": "verify",
        "verifications": [
            {
                "strategy": args.strategy or "id",
                "selector": args.selector,
                "expected_text": args.expected,
            }
        ],
        "status": "success",
        "category": "scenario",
        "include_in_test": True,
    }
    with actions_path.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(json.dumps({"status": "verify_added", "seq": seq}, ensure_ascii=False))
    return 0


def cmd_dump_source(args: argparse.Namespace) -> int:
    """페이지 소스 XML 저장 (Trigger #2).

    MCP 측에서 stdin이나 --content-file 로 XML을 전달하면
    page_sources/<seq>_<설명>.xml 로 저장.
    """
    session_dir = _read_active()
    if session_dir is None:
        print("ERROR: 활성 세션이 없습니다.", file=sys.stderr)
        return 4

    if args.content_file:
        content = Path(args.content_file).read_text()
    else:
        content = sys.stdin.read()
    if not content.strip():
        print("ERROR: XML 내용이 비어있습니다.", file=sys.stderr)
        return 8

    page_dir = session_dir / "page_sources"
    page_dir.mkdir(parents=True, exist_ok=True)
    actions_path = session_dir / "actions.jsonl"
    seq = sum(1 for _ in actions_path.open()) + 1 if actions_path.exists() else 1
    label = _safe_name(args.label or "source")
    out_path = page_dir / f"{seq:03d}_{label}.xml"
    out_path.write_text(content)

    # 액션 로그에도 기록 (observation으로)
    with actions_path.open("a") as f:
        f.write(
            json.dumps(
                {
                    "seq": seq,
                    "ts": _now_iso(),
                    "prompt": args.prompt or "화면 로그 저장",
                    "action": "get_page_source",
                    "result_path": f"page_sources/{out_path.name}",
                    "status": "success",
                    "category": "observation",
                    "include_in_test": False,
                },
                ensure_ascii=False,
            )
            + "\n"
        )

    print(json.dumps({"status": "saved", "path": str(out_path)}, ensure_ascii=False))
    return 0


_SECRET_HINT_RE = None  # 지연 컴파일


def cmd_mask_secrets(args: argparse.Namespace) -> int:
    """평문 비밀번호/PIN을 환경변수 키로 마스킹 (Trigger #17)."""
    import re as _re

    global _SECRET_HINT_RE
    if _SECRET_HINT_RE is None:
        _SECRET_HINT_RE = _re.compile(
            r"^(.{4,30})$"  # 4~30자 일반 입력값 (실제 마스킹은 사용자 매핑으로)
        )

    session_dir = _read_active() if not args.session_dir else Path(args.session_dir)
    if session_dir is None or not session_dir.exists():
        print("ERROR: 세션 폴더를 찾을 수 없습니다.", file=sys.stderr)
        return 4

    # value=key 매핑 (예: --map "secret123=TEST_PW")
    mapping: dict[str, str] = {}
    for m in args.map or []:
        if "=" not in m:
            continue
        v, k = m.split("=", 1)
        mapping[v] = k

    if not mapping:
        print(
            "ERROR: --map 인자를 1개 이상 지정하세요. 예: --map 'mypw=TEST_PW'",
            file=sys.stderr,
        )
        return 9

    actions = _load_actions(session_dir)
    masked_count = 0
    for a in actions:
        params = a.get("params") or {}
        if not isinstance(params, dict):
            continue
        val = params.get("value")
        if val in mapping:
            params["value_from"] = mapping[val]
            params.pop("value", None)
            a["params"] = params
            a.setdefault("note", "")
            a["note"] = (a["note"] + " [masked]").strip()
            masked_count += 1
    _save_actions(session_dir, actions)

    print(json.dumps(
        {"status": "masked", "count": masked_count},
        ensure_ascii=False,
    ))
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    """generated_test.py를 tests/android/<dest>/ 로 이동 (Trigger #8)."""
    session_dir = Path(args.session_dir).resolve() if args.session_dir else None
    if session_dir is None:
        # 최신 세션 자동 선택
        candidates = [
            d for d in SESSIONS_ROOT.iterdir()
            if d.is_dir() and not d.name.startswith(".")
            and (d / "generated_test.py").exists()
        ]
        if not candidates:
            print("ERROR: generated_test.py가 있는 세션이 없습니다.", file=sys.stderr)
            return 4
        session_dir = sorted(candidates)[-1]

    src = session_dir / "generated_test.py"
    if not src.exists():
        print(f"ERROR: {src} 미존재", file=sys.stderr)
        return 4

    dest_dir = PROJECT_ROOT / "tests" / "android" / (args.subdir or "")
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = args.filename or f"{session_dir.name}_test.py"
    dest = dest_dir / name

    if dest.exists() and not args.force:
        print(f"ERROR: 이미 존재: {dest} (--force로 덮어쓰기)", file=sys.stderr)
        return 10

    dest.write_text(src.read_text())
    print(json.dumps(
        {"status": "promoted", "src": str(src), "dest": str(dest)},
        ensure_ascii=False,
    ))
    return 0


# ─────────────────────────────────────────────
# argparse
# ─────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MCP 시나리오 녹화기")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start", help="시나리오 시작")
    p_start.add_argument("name", help="시나리오 이름 (영문/숫자/_/-)")
    p_start.add_argument("--intent", help="시나리오 의도 (한 줄 요약)")
    p_start.add_argument("--notes", help="추가 메모")
    p_start.set_defaults(func=cmd_start)

    p_log = sub.add_parser("log", help="액션 1건 기록")
    p_log.add_argument("--action", required=True,
                       help="tap, press_key, set_value, swipe, screenshot, get_page_source, wait, verify 등")
    p_log.add_argument("--prompt", help="사용자 프롬프트 원문")
    p_log.add_argument("--category", choices=VALID_CATEGORIES, default="scenario")
    p_log.add_argument("--strategy", help="Locator 전략 (id, accessibility id, -android uiautomator, xpath 등)")
    p_log.add_argument("--selector", help="Locator 셀렉터")
    p_log.add_argument("--element-uuid", help="MCP 반환 element UUID")
    p_log.add_argument("--key", help="press_key용 키 이름 (BACK, HOME 등)")
    p_log.add_argument("--duration-ms", type=int, help="실행 시간(ms)")
    p_log.add_argument("--status", default="success", help="success/failure")
    p_log.add_argument("--screenshot-before", help="실행 전 스크린샷 상대경로")
    p_log.add_argument("--screenshot-after", help="실행 후 스크린샷 상대경로")
    p_log.add_argument("--page-source-before", help="실행 전 페이지소스 상대경로")
    p_log.add_argument("--params-json", help="추가 파라미터 (JSON 문자열)")
    p_log.add_argument("--note", help="메모")
    p_log.set_defaults(func=cmd_log)

    p_active = sub.add_parser("active", help="활성 세션 조회")
    p_active.set_defaults(func=cmd_active)

    p_end = sub.add_parser("end", help="시나리오 종료")
    p_end.add_argument("--generate", action="store_true", help="종료와 동시에 코드 생성")
    p_end.add_argument("--raw", action="store_true", help="--generate 시 raw 버전도 같이 생성")
    p_end.set_defaults(func=cmd_end)

    p_list = sub.add_parser("list", help="모든 세션 목록 (Trigger #6)")
    p_list.set_defaults(func=cmd_list)

    p_abort = sub.add_parser("abort", help="활성 세션 폐기 (_aborted 접미사) (Trigger #5)")
    p_abort.set_defaults(func=cmd_abort)

    p_pause = sub.add_parser("pause", help="액션 로깅 일시정지 (Trigger #4)")
    p_pause.set_defaults(func=cmd_pause)

    p_resume = sub.add_parser("resume", help="액션 로깅 재개 (Trigger #4)")
    p_resume.set_defaults(func=cmd_resume)

    p_uc = sub.add_parser("update-category", help="액션 카테고리 변경 (Trigger #1)")
    p_uc.add_argument("--seq", type=int, required=True, help="변경할 액션의 seq")
    p_uc.add_argument(
        "--category", required=True, choices=VALID_CATEGORIES,
        help="새 카테고리"
    )
    p_uc.add_argument("--session-dir", help="활성 세션이 아닌 다른 세션 지정")
    p_uc.set_defaults(func=cmd_update_category)

    p_av = sub.add_parser("add-verify", help="검증 액션 추가 (Trigger #3)")
    p_av.add_argument("--selector", required=True, help="검증할 요소 셀렉터")
    p_av.add_argument("--expected", required=True, help="기대 텍스트")
    p_av.add_argument("--strategy", help="Locator 전략 (기본: id)")
    p_av.add_argument("--prompt", help="검증 설명")
    p_av.set_defaults(func=cmd_add_verify)

    p_ds = sub.add_parser("dump-source", help="페이지 소스 XML 저장 (Trigger #2 / 화면 로그 저장)")
    p_ds.add_argument("--label", help="파일명 라벨 (예: 'login_page')")
    p_ds.add_argument("--content-file", help="XML 내용이 있는 파일 경로 (없으면 stdin)")
    p_ds.add_argument("--prompt", help="프롬프트 설명")
    p_ds.set_defaults(func=cmd_dump_source)

    p_ms = sub.add_parser("mask-secrets", help="평문 값을 환경변수 키로 마스킹 (Trigger #17)")
    p_ms.add_argument("--map", action="append", help="value=ENV_KEY 매핑 (반복 가능)")
    p_ms.add_argument("--session-dir", help="활성 세션이 아닌 다른 세션 지정")
    p_ms.set_defaults(func=cmd_mask_secrets)

    p_pr = sub.add_parser("promote", help="generated_test.py를 tests/android/로 이동 (Trigger #8)")
    p_pr.add_argument("--session-dir", help="대상 세션 (생략 시 최신)")
    p_pr.add_argument("--subdir", help="tests/android/ 하위 폴더 이름")
    p_pr.add_argument("--filename", help="이동 후 파일명 (기본: <session>_test.py)")
    p_pr.add_argument("--force", action="store_true", help="대상 파일 존재 시 덮어쓰기")
    p_pr.set_defaults(func=cmd_promote)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
