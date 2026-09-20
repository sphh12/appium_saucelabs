import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 필수 패키지 목록 (import명, pip 패키지명)
_REQUIRED_PACKAGES = [
    ("pytest", "pytest"),
    ("allure", "allure-pytest"),
    ("appium", "Appium-Python-Client"),
    ("selenium", "selenium"),
    ("dotenv", "python-dotenv"),
]


def _ensure_dependencies() -> None:
    """필수 패키지가 설치되어 있는지 확인하고, 없으면 자동 설치합니다."""
    missing: list[str] = []
    for import_name, pip_name in _REQUIRED_PACKAGES:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)

    if not missing:
        return

    print(f"[run_allure] 누락 패키지 감지: {', '.join(missing)}")

    # requirements.txt가 있으면 전체 설치, 없으면 누락분만 설치
    req_file = Path(__file__).resolve().parent.parent / "requirements.txt"
    if req_file.exists():
        print(f"[run_allure] requirements.txt로 전체 패키지 설치 중...")
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"]
    else:
        print(f"[run_allure] 누락 패키지 설치 중: {', '.join(missing)}")
        cmd = [sys.executable, "-m", "pip", "install", *missing, "-q"]

    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("[run_allure] 패키지 설치 완료")
    else:
        print("[run_allure] 패키지 설치 실패 — 수동으로 설치하세요: pip install -r requirements.txt")
        sys.exit(1)


def _resolve_allure_cmd() -> str | None:
    """allure 실행 파일 경로 탐색: PATH → 로컬 node_modules/.bin 순. 없으면 None.

    Windows에서 bare "allure"는 npm 로컬 설치본(allure.cmd)을 CreateProcess가
    못 찾아 FileNotFoundError가 나므로 (.cmd는 PATHEXT 해석 없이 실행 불가)
    실제 실행 파일 경로로 해석해서 반환한다.
    """
    found = shutil.which("allure")
    if found:
        return found
    local_bin = Path(__file__).resolve().parent.parent / "node_modules" / ".bin"
    candidate = local_bin / ("allure.cmd" if os.name == "nt" else "allure")
    if candidate.exists():
        return str(candidate)
    return None


# 타임스탬프 폴더명 패턴 (YYYYMMDD_HHMMSS) — LATEST/dashboard 등 비-타임스탬프 폴더 배제용
_TIMESTAMP_DIR_RE = re.compile(r"^\d{8}_\d{6}$")


def _find_latest_timestamp_dir(root: Path) -> Path | None:
    if not root.exists():
        return None
    # 타임스탬프 폴더만 후보로 — 이름순 정렬 마지막이 'dashboard'/'LATEST'로 잡혀
    # 트렌드(history) 이어붙임이 조용히 깨지던 문제 방지
    dirs = [p for p in root.iterdir() if p.is_dir() and _TIMESTAMP_DIR_RE.match(p.name)]
    if not dirs:
        return None
    # Timestamp folder names sort lexicographically in chronological order (YYYYMMDD_HHMMSS)
    return sorted(dirs, key=lambda p: p.name)[-1]


def _copy_history(previous_report_dir: Path, results_dir: Path) -> bool:
    """이전 리포트의 history/ 를 새 results 로 복사. 실제로 복사했으면 True.

    복사 여부를 돌려주는 이유: 이전 리포트에 history/ 가 없으면(첫 실행, 직전
    generate 실패, --no-history 로 돌린 경우) 조용히 아무것도 안 하는데,
    호출부가 그걸 모르면 "이어붙였다" 고 잘못 보고하게 된다.
    """
    src = previous_report_dir / "history"
    dst = results_dir / "history"
    if not src.exists() or not src.is_dir():
        return False
    # rmtree(ignore_errors=True) 뒤 copytree 는 삭제가 실패했을 때(파일 잠금 등)
    # 엉뚱한 FileExistsError 로 튄다. dirs_exist_ok 로 덮어써서 그 함정을 피한다.
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return True


def _write_latest_entry(reports_root: Path, timestamp: str) -> None:
        """Create/update a stable 'LATEST' folder that redirects to the latest report.

        This avoids relying on Explorer/VS Code sort order and does not require symlinks.
        """

        latest_dir = reports_root / "LATEST"
        latest_dir.mkdir(parents=True, exist_ok=True)

        # Use forward slashes for browser compatibility.
        target = f"../{timestamp}/index.html"
        html = f"""<!doctype html>
<html lang=\"en\">
    <head>
        <meta charset=\"utf-8\" />
        <meta http-equiv=\"refresh\" content=\"0; url={target}\" />
        <title>Allure Report - LATEST</title>
    </head>
    <body>
        <p>Redirecting to latest report: <a href=\"{target}\">{timestamp}</a></p>
    </body>
</html>
"""
        (latest_dir / "index.html").write_text(html, encoding="utf-8")
        (latest_dir / "LATEST_TIMESTAMP.txt").write_text(f"{timestamp}\n", encoding="utf-8")


def _inject_custom_css(report_dir: Path) -> None:
        """Inject custom CSS into a generated Allure report.

        Purpose: keep text readable while reducing oversized screenshot/video previews.
        """

        index_file = report_dir / "index.html"
        if not index_file.exists():
                return

        css_name = "custom.css"
        css_file = report_dir / css_name

        css = """/* Custom Allure overrides (project-local)
     Goal: reduce attachment media preview size without shrinking text.
*/

/* Limit media preview height in the test details view */
.attachment__media-container:not(.attachment__media-container_fullscreen) .attachment__media,
.attachment__media-container:not(.attachment__media-container_fullscreen) .attachment__embed {
    max-height: min(42vh, 460px);
    width: auto;
    height: auto;
}

/* Videos sometimes use the same class; ensure it fits nicely */
.attachment__media-container:not(.attachment__media-container_fullscreen) video.attachment__media {
    max-height: min(42vh, 460px);
    width: 100%;
}

/* Keep the container from taking too much vertical space */
.attachment__media-container:not(.attachment__media-container_fullscreen) {
    padding: 8px 16px;
}

/* If an iframe attachment exists, constrain it too */
.attachment__iframe-container:not(.attachment__iframe-container_fullscreen) {
    max-height: min(60vh, 520px);
    overflow: auto;
}

/* Make attachment filename/header a bit tighter */
.attachment__filename {
    padding: 10px 16px;
}
"""

        css_file.write_text(css, encoding="utf-8")

        html = index_file.read_text(encoding="utf-8", errors="replace")
        link_tag = f'<link rel="stylesheet" type="text/css" href="{css_name}">' 
        if css_name in html:
                return

        # Insert after the main styles.css link (best-effort)
        marker = '<link rel="stylesheet" type="text/css" href="styles.css">'
        if marker in html:
                html = html.replace(marker, marker + "\n    " + link_tag, 1)
        else:
                # Fallback: before </head>
                html = html.replace("</head>", f"    {link_tag}\n</head>")

        index_file.write_text(html, encoding="utf-8")


def main() -> int:
    _ensure_dependencies()

    parser = argparse.ArgumentParser(
        description=(
            "pytest 실행 결과를 날짜/시간별 Allure 결과/리포트로 저장합니다. "
            "예) allure-results/20260119_153012, allure-reports/20260119_153012"
        )
    )
    parser.add_argument(
        "--results-root",
        default="allure-results",
        help="Allure results 루트 폴더(하위에 timestamp 폴더 생성)",
    )
    parser.add_argument(
        "--reports-root",
        default="allure-reports",
        help="Allure report 루트 폴더(하위에 timestamp 폴더 생성)",
    )
    parser.add_argument(
        "--keep-history",
        action="store_true",
        default=True,
        help="이전 실행의 트렌드(history)를 다음 리포트에 이어붙임 (기본: 켜짐)",
    )
    parser.add_argument(
        "--no-history",
        dest="keep_history",
        action="store_false",
        help="트렌드(history) 이어붙임 끄기",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        default=False,
        help="리포트 생성 후 allure open 실행",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="pytest 인자들 (예: -- tests/android/<your_test>.py -v --platform=android)",
    )

    args = parser.parse_args()

    pytest_args = list(args.pytest_args)
    if pytest_args and pytest_args[0] == "--":
        pytest_args = pytest_args[1:]
    if not pytest_args:
        print(
            "pytest 인자가 없습니다. 예: python tools/run_allure.py -- tests/android/<your_test>.py -v --platform=android"
        )
        return 2

    # Default is handled in conftest.py: --allure-attach=hybrid
    # Users can override with --allure-attach=all if they want to attach everything.

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(args.results_root) / timestamp
    report_dir = Path(args.reports_root) / timestamp

    results_dir.mkdir(parents=True, exist_ok=False)
    report_dir.parent.mkdir(parents=True, exist_ok=True)

    # 이어붙일 '직전 리포트' 는 pytest 실행 **전** 에 확정한다.
    # 실행 중에 다른 런이 끝나면 더 큰 타임스탬프가 생겨, 나중에 조회할 경우
    # 자기보다 늦게 시작한 런에 이어붙는 역전이 생긴다.
    previous_report_dir = None
    if args.keep_history:
        candidate = _find_latest_timestamp_dir(Path(args.reports_root))
        if candidate is not None and candidate.name != timestamp:
            previous_report_dir = candidate

    env = os.environ.copy()

    pytest_cmd = [sys.executable, "-m", "pytest", *pytest_args, "--alluredir", str(results_dir)]
    print("[run_allure] pytest:", " ".join(pytest_cmd))
    pytest_proc = subprocess.run(pytest_cmd, env=env)

    # 복사 자체는 pytest **뒤** 에 해야 한다.
    # --clean-alluredir 은 results 폴더를 통째로 rmtree 한다(allure_commons/logger.py 의
    # AllureFileLogger.__init__). pytest 앞에서 복사하면 방금 넣은 history/ 가 그대로 지워져
    # 리포트를 아무리 쌓아도 트렌드가 항상 1건이 된다.
    # conftest 의 pytest_sessionstart 가 environment.properties 를 clean 뒤로 미룬 것과 같은 이유다.
    #
    # try 로 감싸는 이유: 이 시점엔 테스트가 이미 다 끝났다. 트렌드 하나 때문에
    # 여기서 죽으면 리포트·업로드까지 통째로 날아간다. 트렌드는 포기해도 리포트는 만든다.
    if previous_report_dir is not None:
        try:
            if _copy_history(previous_report_dir, results_dir):
                print(f"[run_allure] 트렌드 이어붙임: {previous_report_dir}/history -> {results_dir}/history")
            else:
                print(f"[run_allure] 직전 리포트에 history 가 없어 트렌드를 이번 실행부터 다시 시작한다: {previous_report_dir}")
        except OSError as exc:
            print(f"[run_allure] 트렌드 이어붙임 실패 — 무시하고 리포트 생성을 계속한다: {exc}")

    allure_cmd = _resolve_allure_cmd()
    if allure_cmd is None:
        # 리포트 생성만 건너뛰고 pytest 종료코드는 살린다 — 여기서 죽으면 테스트 결과가 사라진다
        print("[run_allure] allure CLI를 찾을 수 없어 리포트 생성을 건너뜁니다.")
        print("  → 설치: scoop install allure / choco install allure / npm install (로컬 npx allure)")
        print(f"[run_allure] results: {results_dir}")
        return int(pytest_proc.returncode)

    allure_generate_cmd = [
        allure_cmd,
        "generate",
        str(results_dir),
        "-o",
        str(report_dir),
        "--clean",
    ]
    print("[run_allure] allure generate:", " ".join(allure_generate_cmd))
    subprocess.run(allure_generate_cmd, env=env, check=True)

    _inject_custom_css(report_dir)

    latest_file = Path(args.reports_root) / "LATEST.txt"
    latest_file.write_text(f"{timestamp}\n", encoding="utf-8")

    _write_latest_entry(Path(args.reports_root), timestamp)

    # Generate/update a simple dashboard that lists all saved runs.
    # (Static HTML + runs.json; browser cannot list directories by itself.)
    try:
        dashboard_script = Path(__file__).resolve().parent / "update_dashboard.py"
        dashboard_cmd = [sys.executable, str(dashboard_script), "--reports-root", str(args.reports_root)]
        print("[run_allure] dashboard:", " ".join(dashboard_cmd))
        subprocess.run(dashboard_cmd, env=env, check=False)
    except Exception as e:
        print(f"[run_allure] dashboard update skipped: {e}")

    print(f"[run_allure] results: {results_dir}")
    print(f"[run_allure] report  : {report_dir}")
    print(f"[run_allure] latest  : {Path(args.reports_root) / 'LATEST' / 'index.html'}")
    print(f"[run_allure] dash    : {Path(args.reports_root) / 'dashboard' / 'index.html'}")

    if args.open:
        allure_open_cmd = [allure_cmd, "open", str(report_dir)]
        print("[run_allure] allure open:", " ".join(allure_open_cmd))
        subprocess.run(allure_open_cmd, env=env, check=False)

    return int(pytest_proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
