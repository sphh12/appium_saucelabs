"""
Allure 리포트 요약 HTML 생성
- 핵심 정보만 포함 (테스트 결과, 실패 상세, 환경 정보)
- 스크린샷은 Base64 인라인 (비디오 제외)
- 단일 HTML 파일로 출력
"""

import argparse
import base64
import json
import re
from datetime import datetime
from pathlib import Path


def _read_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _format_duration(ms: int) -> str:
    seconds = max(0, ms // 1000)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


def _format_timestamp(ts: str) -> str:
    match = re.match(r"^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$", ts)
    if match:
        y, mo, d, h, mi, s = match.groups()
        return f"{y}-{mo}-{d} {h}:{mi}:{s}"
    return ts


def _inline_image(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        data = path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        suffix = path.suffix.lower()
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif"}.get(
            suffix.lstrip("."), "image/png"
        )
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


def generate_summary_html(report_dir: Path, output_path: Path, include_screenshots: bool = True) -> None:
    summary = _read_json(report_dir / "widgets" / "summary.json")
    if not summary:
        raise FileNotFoundError(f"summary.json not found in {report_dir}")

    stats = summary.get("statistic", {})
    time_info = summary.get("time", {})
    report_name = summary.get("reportName", report_dir.name)

    # Environment info
    env_data = _read_json(report_dir / "widgets" / "environment.json") or []
    env_map = {}
    for item in env_data:
        name = item.get("name", "")
        values = item.get("values", [])
        if name and values:
            env_map[name] = values[0]

    # Test cases
    test_cases = []
    data_dir = report_dir / "data" / "test-cases"
    if data_dir.exists():
        for tc_file in data_dir.glob("*.json"):
            tc = _read_json(tc_file)
            if tc:
                test_cases.append(tc)

    # Sort by status (failed first)
    status_order = {"failed": 0, "broken": 1, "skipped": 2, "passed": 3, "unknown": 4}
    test_cases.sort(key=lambda x: status_order.get(x.get("status", "unknown"), 5))

    # Attachments mapping
    attachments_dir = report_dir / "data" / "attachments"

    # Build HTML
    html_parts = [
        """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Test Report Summary</title>
<style>
:root{--bg:#0b1220;--panel:#0f1b33;--text:#e6edf7;--muted:#9bb0d0;--border:rgba(255,255,255,.08);--passed:#2fb344;--failed:#fa5252;--broken:#f08c00;--skipped:#868e96}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.5;padding:24px}
.container{max-width:1000px;margin:0 auto}
h1{font-size:24px;margin-bottom:8px}
.meta{color:var(--muted);font-size:13px;margin-bottom:24px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}
.stats{display:flex;gap:16px;flex-wrap:wrap}
.stat{text-align:center;min-width:80px}
.stat-value{font-size:28px;font-weight:700}
.stat-label{font-size:12px;color:var(--muted)}
.passed{color:var(--passed)}.failed{color:var(--failed)}.broken{color:var(--broken)}.skipped{color:var(--skipped)}
.env{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;font-size:13px}
.env-item{padding:8px 12px;background:rgba(255,255,255,.03);border-radius:8px}
.env-key{color:var(--muted)}
h2{font-size:18px;margin:24px 0 12px;border-bottom:1px solid var(--border);padding-bottom:8px}
.test{border:1px solid var(--border);border-radius:8px;margin-bottom:8px;overflow:hidden}
.test-header{display:flex;align-items:center;gap:12px;padding:12px 16px;background:rgba(255,255,255,.02);cursor:pointer}
.test-header:hover{background:rgba(255,255,255,.04)}
.status-badge{padding:4px 10px;border-radius:999px;font-size:11px;font-weight:600;text-transform:uppercase}
.status-passed{background:rgba(47,179,68,.15);color:var(--passed)}
.status-failed{background:rgba(250,82,82,.15);color:var(--failed)}
.status-broken{background:rgba(240,140,0,.15);color:var(--broken)}
.status-skipped{background:rgba(134,142,150,.15);color:var(--skipped)}
.test-name{flex:1;font-weight:500}
.test-duration{color:var(--muted);font-size:12px}
.test-body{padding:16px;display:none;border-top:1px solid var(--border)}
.test.open .test-body{display:block}
.test-section{margin-bottom:16px}
.test-section:last-child{margin-bottom:0}
.section-title{font-size:13px;color:var(--muted);margin-bottom:8px}
.error-msg{background:rgba(250,82,82,.1);border:1px solid rgba(250,82,82,.3);border-radius:8px;padding:12px;font-family:monospace;font-size:12px;white-space:pre-wrap;word-break:break-all;color:#ff8080}
.screenshot{max-width:100%;max-height:300px;border-radius:8px;border:1px solid var(--border)}
.steps{font-size:13px}
.step{padding:6px 0;border-bottom:1px solid var(--border)}
.step:last-child{border-bottom:none}
.step-status{display:inline-block;width:60px}
</style>
</head>
<body>
<div class="container">
"""
    ]

    # Header
    html_parts.append(f'<h1>{report_name}</h1>')
    html_parts.append(f'<div class="meta">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Report: {_format_timestamp(report_dir.name)}</div>')

    # Stats card
    html_parts.append('<div class="card"><div class="stats">')
    html_parts.append(f'<div class="stat"><div class="stat-value">{stats.get("total", 0)}</div><div class="stat-label">Total</div></div>')
    html_parts.append(f'<div class="stat passed"><div class="stat-value">{stats.get("passed", 0)}</div><div class="stat-label">Passed</div></div>')
    html_parts.append(f'<div class="stat failed"><div class="stat-value">{stats.get("failed", 0)}</div><div class="stat-label">Failed</div></div>')
    html_parts.append(f'<div class="stat broken"><div class="stat-value">{stats.get("broken", 0)}</div><div class="stat-label">Broken</div></div>')
    html_parts.append(f'<div class="stat skipped"><div class="stat-value">{stats.get("skipped", 0)}</div><div class="stat-label">Skipped</div></div>')
    html_parts.append(f'<div class="stat"><div class="stat-value">{_format_duration(time_info.get("duration", 0))}</div><div class="stat-label">Duration</div></div>')
    html_parts.append('</div></div>')

    # Environment card
    if env_map:
        html_parts.append('<div class="card"><div class="env">')
        for k, v in env_map.items():
            html_parts.append(f'<div class="env-item"><span class="env-key">{k}:</span> {v}</div>')
        html_parts.append('</div></div>')

    # Test cases
    html_parts.append('<h2>Test Cases</h2>')
    for tc in test_cases:
        status = tc.get("status", "unknown")
        name = tc.get("name", "Unknown")
        full_name = tc.get("fullName", name)
        duration = tc.get("time", {}).get("duration", 0)
        status_trace = tc.get("statusTrace", "") or tc.get("statusMessage", "")

        html_parts.append(f'<div class="test" data-status="{status}">')
        html_parts.append(f'<div class="test-header" onclick="this.parentElement.classList.toggle(\'open\')">')
        html_parts.append(f'<span class="status-badge status-{status}">{status}</span>')
        html_parts.append(f'<span class="test-name">{name}</span>')
        html_parts.append(f'<span class="test-duration">{_format_duration(duration)}</span>')
        html_parts.append('</div>')
        html_parts.append('<div class="test-body">')

        # Full name
        html_parts.append(f'<div class="test-section"><div class="section-title">Full Name</div><div>{full_name}</div></div>')

        # Error message
        if status in ("failed", "broken") and status_trace:
            html_parts.append(f'<div class="test-section"><div class="section-title">Error</div><div class="error-msg">{status_trace[:2000]}</div></div>')

        # Screenshots - search in all stages
        if include_screenshots:
            all_attachments = []
            def collect_attachments(obj):
                if isinstance(obj, dict):
                    if "attachments" in obj and isinstance(obj["attachments"], list):
                        all_attachments.extend(obj["attachments"])
                    for v in obj.values():
                        collect_attachments(v)
                elif isinstance(obj, list):
                    for item in obj:
                        collect_attachments(item)
            collect_attachments(tc)
            screenshots = [a for a in all_attachments if a.get("type", "").startswith("image/")]
            if screenshots:
                html_parts.append('<div class="test-section"><div class="section-title">Screenshots</div>')
                for att in screenshots[:3]:  # Max 3 screenshots
                    source = att.get("source", "")
                    if source:
                        img_path = attachments_dir / source
                        data_uri = _inline_image(img_path)
                        if data_uri:
                            html_parts.append(f'<img class="screenshot" src="{data_uri}" alt="{att.get("name", "screenshot")}">')
                html_parts.append('</div>')

        html_parts.append('</div></div>')

    # Footer
    html_parts.append("""
</div>
<script>
// Auto-open failed tests
document.querySelectorAll('.test[data-status="failed"], .test[data-status="broken"]').forEach(el => el.classList.add('open'));
</script>
</body>
</html>
""")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(html_parts), encoding="utf-8")
    print(f"Summary HTML generated: {output_path}")
    print(f"File size: {output_path.stat().st_size:,} bytes")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate summary HTML from Allure report")
    parser.add_argument("report_dir", help="Allure report directory (e.g., allure-reports/20260127_153847)")
    parser.add_argument("--output", "-o", default=None, help="Output HTML file path")
    parser.add_argument("--no-screenshots", action="store_true", help="Exclude screenshots (smaller file)")
    args = parser.parse_args()

    report_dir = Path(args.report_dir)
    if not report_dir.exists():
        print(f"Error: Report directory not found: {report_dir}")
        return 1

    output = Path(args.output) if args.output else report_dir.parent / "export" / f"summary_{report_dir.name}.html"

    generate_summary_html(report_dir, output, include_screenshots=not args.no_screenshots)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
