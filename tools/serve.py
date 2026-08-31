"""Allure 리포트 서버 실행 스크립트

프로젝트 루트에서 HTTP 서버를 띄워 대시보드와 리포트를 브라우저에서 볼 수 있게 합니다.

사용법:
    python tools/serve.py              # 대시보드 열기 (기본)
    python tools/serve.py --latest     # 최신 리포트 열기
    python tools/serve.py --port 9000  # 포트 변경
"""

import argparse
import http.server
import socketserver
import webbrowser
from pathlib import Path
import threading
import time
import signal
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Allure 리포트 서버를 실행합니다."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="서버 포트 (기본: 8000)",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="대시보드 대신 최신 리포트 열기",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="브라우저 자동 열기 비활성화",
    )
    parser.add_argument(
        "--reports-root",
        default="allure-reports",
        help="리포트 루트 폴더 (기본: allure-reports)",
    )

    args = parser.parse_args()

    # 프로젝트 루트로 이동 (tools/ 폴더 기준)
    project_root = Path(__file__).resolve().parent.parent
    reports_root = project_root / args.reports_root

    if not reports_root.exists():
        print(f"[ERROR] 리포트 폴더가 없습니다: {reports_root}")
        print("먼저 테스트를 실행하세요: python tools/run_allure.py -- tests/...")
        return 1

    # 열 URL 결정
    if args.latest:
        url_path = f"{args.reports_root}/LATEST/index.html"
    else:
        url_path = f"{args.reports_root}/dashboard/index.html"

    url = f"http://localhost:{args.port}/{url_path}"

    # 브라우저 열기 (서버 시작 직후)
    if not args.no_open:
        def open_browser():
            time.sleep(0.5)  # 서버가 뜰 때까지 잠깐 대기
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()

    # HTTP 서버 시작 (프로젝트 루트에서)
    import os
    os.chdir(project_root)

    class Handler(http.server.SimpleHTTPRequestHandler):
        # 죽은/유휴 연결이 워커 스레드를 영구 점유하지 않도록 연결 타임아웃
        timeout = 30

    print(f"[serve] 프로젝트 루트: {project_root}")
    print(f"[serve] 서버 시작: http://localhost:{args.port}")
    print(f"[serve] 열기: {url}")
    print()

    try:
        socketserver.TCPServer.allow_reuse_address = True
        # 로컬호스트(127.0.0.1)에만 바인딩 — 같은 LAN의 다른 사용자가 프로젝트 루트(.env 포함)에
        # 접근하는 것을 차단. 외부에서 열 이유가 없는 로컬 리포트 열람용 서버이기 때문.
        #
        # 요청당 스레드(ThreadingHTTPServer) — 단일 스레드 TCPServer로 두면 브라우저가
        # 미리 열어두는 유휴 연결(preconnect) 하나가 요청 루프를 붙잡아 서버 전체가 멈춘다
        # (Allure 리포트는 에셋 요청이 수십 개라 특히 잘 재현됨).
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler)

        # 서버를 별도 스레드에서 실행
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        # 종료 대기 — Enter(대화형) 또는 Ctrl+C.
        # 파이프·CI·에이전트 실행에서는 input()이 즉시 EOF가 되는데, 예전엔 그걸 종료로
        # 해석해 서버가 곧바로 자멸했다. EOF는 'Enter를 받을 수 없는 환경'이라는 신호이므로
        # 그때는 Ctrl+C까지 계속 서빙한다. (isatty()는 Git Bash에서 True로 나와 신뢰 불가)
        try:
            input("[serve] Enter 또는 Ctrl+C로 종료\n")
        except EOFError:
            print("[serve] 비대화형 stdin — 종료하려면 Ctrl+C")
            try:
                server_thread.join()
            except KeyboardInterrupt:
                pass
        except KeyboardInterrupt:
            pass

        print("[serve] 서버 종료 중...")
        httpd.shutdown()
        httpd.server_close()   # 리스닝 소켓 반납 (없으면 프로세스 종료 때까지 포트 점유)

    except OSError as e:
        if "Address already in use" in str(e) or "10048" in str(e):
            print(f"[ERROR] 포트 {args.port}이 이미 사용 중입니다.")
            print(f"다른 포트를 사용하세요: python tools/serve.py --port 9000")
            return 1
        raise

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
