import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_TIMESTAMP_DIR_RE = re.compile(r"^\d{8}_\d{6}$")


@dataclass(frozen=True)
class RunSummary:
    timestamp: str
    report_name: str
    stats: dict[str, int]
    time: dict[str, int]
    executor: dict[str, Any]
    environment: dict[str, Any]
    suites: list[dict[str, int | str]]
    behaviors: list[dict[str, int | str]]
    packages: list[dict[str, int | str]]


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_git_message(repo_root: Path, commit: str) -> str:
    if not commit:
        return ""
    try:
        proc = subprocess.run(
            ["git", "log", "-1", "--pretty=%s", commit],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return (proc.stdout or "").strip()
    except Exception:
        return ""


def _extract_branch_commit(build_name: str) -> tuple[str, str]:
    raw = (build_name or "").strip()
    if not raw:
        return "", ""
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if len(parts) < 3:
        return "", ""
    if "@" not in parts[2]:
        return "", ""
    branch, commit = [p.strip() for p in parts[2].split("@", 1)]
    return branch, commit


def _duration_ms_to_hms(duration_ms: int) -> str:
    seconds = max(0, duration_ms // 1000)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


def _extract_widget_items(data: dict[str, Any] | None) -> list[dict[str, int | str]]:
    if not data or not isinstance(data, dict):
        return []
    items = data.get("items")
    if not isinstance(items, list):
        return []
    output: list[dict[str, int | str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        stat = item.get("statistic") or {}
        if not name and not stat:
            continue
        output.append(
            {
                "name": name,
                "total": _safe_int(stat.get("total"), 0),
                "passed": _safe_int(stat.get("passed"), 0),
                "failed": _safe_int(stat.get("failed"), 0),
                "broken": _safe_int(stat.get("broken"), 0),
                "skipped": _safe_int(stat.get("skipped"), 0),
            }
        )
    output.sort(key=lambda x: int(x.get("total", 0)), reverse=True)
    return output


def _load_run_summary(report_dir: Path) -> RunSummary | None:
    summary = _read_json(report_dir / "widgets" / "summary.json")
    if not summary:
        return None

    report_name = str(summary.get("reportName") or report_dir.name)

    stats_raw = summary.get("statistic") or {}
    time_raw = summary.get("time") or {}

    stats = {
        "total": _safe_int(stats_raw.get("total"), 0),
        "passed": _safe_int(stats_raw.get("passed"), 0),
        "failed": _safe_int(stats_raw.get("failed"), 0),
        "broken": _safe_int(stats_raw.get("broken"), 0),
        "skipped": _safe_int(stats_raw.get("skipped"), 0),
        "unknown": _safe_int(stats_raw.get("unknown"), 0),
    }

    time = {
        "start": _safe_int(time_raw.get("start"), 0),
        "stop": _safe_int(time_raw.get("stop"), 0),
        "duration": _safe_int(time_raw.get("duration"), 0),
        "minDuration": _safe_int(time_raw.get("minDuration"), 0),
        "maxDuration": _safe_int(time_raw.get("maxDuration"), 0),
        "sumDuration": _safe_int(time_raw.get("sumDuration"), 0),
    }

    executors = _read_json(report_dir / "widgets" / "executors.json")
    environment = _read_json(report_dir / "widgets" / "environment.json")
    suites = _extract_widget_items(_read_json(report_dir / "widgets" / "suites.json"))
    behaviors = _extract_widget_items(_read_json(report_dir / "widgets" / "behaviors.json"))
    packages = _extract_widget_items(_read_json(report_dir / "widgets" / "packages.json"))

    executor_first = {}
    if isinstance(executors, list):
        executor_first = executors[0] if executors else {}

    env_map: dict[str, Any] = {}
    if isinstance(environment, list):
        for item in environment:
            try:
                name = str(item.get("name"))
                # Allure uses "values" (array) not "value"
                values = item.get("values")
                if isinstance(values, list) and values:
                    value = values[0]
                else:
                    value = item.get("value")
                if name:
                    env_map[name] = value
            except Exception:
                continue

    # Allure CLI가 environment.properties를 Latin-1로 읽어 한글이 깨지는 문제 보정
    # allure-results 원본 파일에서 UTF-8로 직접 읽어 덮어쓰기
    results_dir = report_dir.parent.parent / "allure-results" / report_dir.name
    env_props = results_dir / "environment.properties"
    if env_props.exists():
        try:
            for line in env_props.read_text(encoding="utf-8").splitlines():
                if "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip()
                    if key and val:
                        env_map[key] = val
        except Exception:
            pass

    return RunSummary(
        timestamp=report_dir.name,
        report_name=report_name,
        stats=stats,
        time=time,
        executor=executor_first,
        environment=env_map,
        suites=suites,
        behaviors=behaviors,
        packages=packages,
    )


def update_dashboard(reports_root: Path) -> Path:
    dashboard_dir = reports_root / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    repo_root = reports_root.resolve().parent

    runs: list[RunSummary] = []
    for child in reports_root.iterdir():
        if not child.is_dir():
            continue
        if not _TIMESTAMP_DIR_RE.match(child.name):
            continue
        run = _load_run_summary(child)
        if run:
            runs.append(run)

    # Latest first
    runs.sort(key=lambda r: r.timestamp, reverse=True)

    # Build runs.json
    payload: list[dict[str, Any]] = []
    for r in runs:
        env = dict(r.environment or {})
        build_name = r.executor.get("buildName", "")
        branch = str(env.get("gitBranch") or "").strip()
        commit = str(env.get("gitCommit") or "").strip()
        message = str(env.get("gitMessage") or "").strip()
        if not branch or not commit:
            parsed_branch, parsed_commit = _extract_branch_commit(build_name)
            branch = branch or parsed_branch
            commit = commit or parsed_commit
        if not message and commit:
            message = _safe_git_message(repo_root, commit)
        env.update({"gitBranch": branch or None, "gitCommit": commit or None, "gitMessage": message or None})
        payload.append(
            {
                "timestamp": r.timestamp,
                "href": f"/allure-reports/{r.timestamp}/index.html",
                "reportName": r.report_name,
                "stats": r.stats,
                "time": r.time,
                "durationText": _duration_ms_to_hms(r.time.get("duration", 0)),
                "executor": {
                    "name": r.executor.get("name", ""),
                    "type": r.executor.get("type", ""),
                    "buildName": r.executor.get("buildName", ""),
                    "buildUrl": r.executor.get("buildUrl", ""),
                },
                "environment": env,
                "suites": r.suites,
                "behaviors": r.behaviors,
                "packages": r.packages,
            }
        )

    (dashboard_dir / "runs.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Static dashboard HTML/CSS
    (dashboard_dir / "styles.css").write_text(
        """/* Dashboard styles (local) */
:root{
  color-scheme: dark;
  --bg:#0b1220;
  --panel:#0f1b33;
  --text:#e6edf7;
  --muted:#9bb0d0;
  --border:rgba(255,255,255,.08);
  --passed:#2fb344;
  --failed:#fa5252;
  --broken:#f08c00;
  --skipped:#868e96;
}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:linear-gradient(180deg,var(--bg),#070b14);color:var(--text)}
a{color:inherit}
.container{max-width:1200px;margin:0 auto;padding:24px}
.header{display:flex;flex-direction:column;gap:16px;margin-bottom:16px}
.header-top{display:flex;gap:16px;align-items:center;justify-content:space-between}
.h1{font-size:22px;font-weight:700;letter-spacing:.2px}
.sub{font-size:12px;color:var(--muted);white-space:nowrap}
.controls{display:flex;gap:10px;align-items:center;padding:12px 16px;background:rgba(255,255,255,.02);border-radius:12px;border:1px solid var(--border)}
input[type=search], input[type=date], select{padding:10px 12px;border-radius:10px;border:1px solid var(--border);background:rgba(255,255,255,.06);color:var(--text)}
select option, select optgroup{background-color:#0f1b33;color:var(--text)}
input[type=search]{width:340px;max-width:60vw}
input[type=date]{color-scheme:dark}
.card{background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:14px;overflow:hidden}
.table{width:100%;border-collapse:separate;border-spacing:0}
th,td{padding:10px 12px;border-bottom:1px solid var(--border);font-size:13px;vertical-align:middle;text-align:center}
th{color:var(--muted);font-weight:600;background:rgba(255,255,255,.02)}
tr:hover td{background:rgba(255,255,255,.03)}
.badge{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;border:1px solid var(--border);font-size:12px}
.dot{width:8px;height:8px;border-radius:999px}
.dot.passed{background:var(--passed)}
.dot.failed{background:var(--failed)}
.dot.broken{background:var(--broken)}
.dot.skipped{background:var(--skipped)}
.kv{display:flex;gap:10px;flex-wrap:wrap;color:var(--muted);font-size:12px;margin:10px 0 0}
.kv span{padding:6px 10px;border:1px solid var(--border);border-radius:10px;background:rgba(255,255,255,.03)}
.small{color:var(--muted);font-size:12px}
.ellipsis{max-width:260px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.result{font-weight:700;font-style:italic}
.footer{margin-top:12px;color:var(--muted);font-size:12px}
""",
        encoding="utf-8",
    )

    (dashboard_dir / "index.html").write_text(
        r"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Allure Reports Dashboard</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-top">
        <div class="h1">Allure Reports Dashboard</div>
      </div>
      <div class="controls">
        <input id="q" type="search" placeholder="검색: timestamp / buildName / 플랫폼 / git / commit message" />
        <select id="platform">
          <option value="all">Platform: 전체</option>
          <option value="android">Android</option>
          <option value="ios">iOS</option>
        </select>
        <select id="result">
          <option value="all">Result: 전체</option>
          <option value="pass">PASS</option>
          <option value="fail">FAIL</option>
          <option value="broken">BROKEN</option>
          <option value="skip">SKIP</option>
        </select>
        <input id="from" type="date" />
        <input id="to" type="date" />
        <button id="clearBtn" type="button" style="margin-left:auto;padding:10px 16px;border-radius:10px;border:1px solid var(--border);background:rgba(255,255,255,.06);color:var(--text);cursor:pointer">Clear</button>
      </div>
    </div>

    <div class="card">
      <table class="table" id="tbl">
        <thead>
          <tr>
            <th style="width:160px;text-align:left">Timestamp</th>
            <th style="width:260px;text-align:left">Device / Tests</th>
            <th style="width:280px;text-align:left">Branch / Commit</th>
            <th style="width:70px">Result</th>
            <th style="width:60px">Total</th>
            <th style="width:60px">Pass</th>
            <th style="width:60px">Fail</th>
            <th style="width:60px">Broken</th>
            <th style="width:60px">Skip</th>
            <th style="width:90px">Duration</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>

    <div class="footer" id="meta"></div>
  </div>

<script>
  const fmt = (v) => (v === undefined || v === null) ? '' : String(v);
  const basePath = getBasePath();

  function getBasePath() {
    const path = window.location.pathname;
    const marker = '/dashboard';
    const idx = path.indexOf(marker);
    if (idx >= 0) {
      return path.slice(0, idx + 1);
    }
    return '/';
  }

  function resolveHref(run) {
    const ts = (run && run.timestamp) ? String(run.timestamp) : '';
    if (ts) {
      return `${basePath}${ts}/index.html`;
    }
    const raw = (run && run.href) ? String(run.href) : '';
    if (!raw) return '#';
    if (raw.startsWith('/allure-reports/') && basePath === '/') {
      return raw.replace(/^\/allure-reports\//, '/');
    }
    return raw;
  }

  function truncate(str, maxLen = 40) {
    if (!str || str.length <= maxLen) return str || '';
    return str.slice(0, maxLen) + '...';
  }

  function formatTimestamp(ts) {
    // Parse "20260127_153847" -> { date: "2026-01-27", time: "15:38:47" }
    const match = String(ts || '').match(/^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$/);
    if (!match) return { date: ts || '', time: '' };
    const [, y, m, d, hh, mm, ss] = match;
    return { date: `${y}-${m}-${d}`, time: `${hh}:${mm}:${ss}` };
  }

  function formatBehaviors(items, limit = 4) {
    if (!Array.isArray(items) || items.length === 0) return '';
    const names = items.slice(0, limit).map(i => fmt(i.name)).filter(Boolean);
    const total = items.reduce((sum, i) => sum + (i.total || 0), 0);
    if (names.length === 0) return '';
    let text = names.join(', ');
    if (items.length > limit) {
      text += `, +${items.length - limit}`;
    }
    return `${text} (${total})`;
  }

  function namesFrom(items) {
    return Array.isArray(items) ? items.map(i => i && i.name ? i.name : '').join(' ') : '';
  }

  function row(run) {
    const stats = run.stats || {};
    const exe = run.executor || {};
    const env = run.environment || {};
    const href = resolveHref(run);

    // Priority: Failed > Passed > Broken > Skip
    let result, resultColor;
    if ((stats.failed || 0) > 0) {
      result = 'FAIL'; resultColor = 'var(--failed)';
    } else if ((stats.passed || 0) > 0) {
      result = 'PASS'; resultColor = 'var(--passed)';
    } else if ((stats.broken || 0) > 0) {
      result = 'BROKEN'; resultColor = 'var(--broken)';
    } else if ((stats.skipped || 0) > 0) {
      result = 'SKIP'; resultColor = 'var(--skipped)';
    } else {
      result = '-'; resultColor = 'var(--muted)';
    }

    // Tests column: Device + Behaviors
    const deviceName = env.deviceName || env.platform || 'Unknown';
    const behaviorsText = formatBehaviors(run.behaviors, 4);
    const platformVersion = fmt(env.platformVersion);
    const appName = fmt(env.app).split(/[\\/\\\\]/).pop();
    const appVersionMatch = appName.match(/(\d+\.\d+(?:\.\d+)*)(?:\.apk|\.ipa)?/i);
    const appVersion = appVersionMatch ? appVersionMatch[1] : '';
    const osLine = platformVersion ? `OS: ${platformVersion}` : '';
    const appLine = appVersion ? `App: v${appVersion}` : '';

    // Build/Env column: Git info
    const branch = fmt(env.gitBranch) || 'no-branch';
    const commit = fmt(env.gitCommit) || '';
    const rawMessage = fmt(env.gitMessage);
    const message = rawMessage ? truncate(rawMessage, 35) : '<span style="color:var(--muted);font-style:italic">(no message)</span>';

    const ts = formatTimestamp(run.timestamp);
    return `
      <tr>
        <td style="text-align:left"><a href="${href}"><div>${ts.date}</div><div class="small">${ts.time}</div></a></td>
        <td style="text-align:left">
          <div><strong>${deviceName}</strong></div>
          ${osLine ? `<div class="small">${osLine}</div>` : ''}
          ${appLine ? `<div class="small">${appLine}</div>` : ''}
          <div class="small">${behaviorsText || 'N/A'}</div>
        </td>
        <td style="text-align:left">
          <div class="badge"><span class="dot ${stats.failed ? 'failed' : stats.broken ? 'broken' : stats.skipped ? 'skipped' : 'passed'}"></span>
            <span>${branch}${commit ? ' @ ' + commit : ''}</span>
          </div>
          <div class="small ellipsis">${message}</div>
        </td>
        <td class="result" style="color:${resultColor}">${result}</td>
        <td>${fmt(stats.total)}</td>
        <td style="color:var(--passed)">${fmt(stats.passed)}</td>
        <td style="color:var(--failed)">${fmt(stats.failed)}</td>
        <td style="color:var(--broken)">${fmt(stats.broken)}</td>
        <td style="color:var(--skipped)">${fmt(stats.skipped)}</td>
        <td>${fmt(run.durationText)}</td>
      </tr>
    `;
  }

  function getResult(run) {
    const stats = run.stats || {};
    // Priority: Failed > Passed > Broken > Skip
    if ((stats.failed || 0) > 0) return 'fail';
    if ((stats.passed || 0) > 0) return 'pass';
    if ((stats.broken || 0) > 0) return 'broken';
    if ((stats.skipped || 0) > 0) return 'skip';
    return 'unknown';
  }

  function dateKeyFromTimestamp(ts) {
    const match = String(ts || '').match(/^(\d{8})/);
    return match ? match[1] : '';
  }

  function dateInputToKey(value) {
    return value ? value.replace(/-/g, '') : '';
  }

  async function main() {
    const res = await fetch('runs.json', { cache: 'no-store' });
    const runs = await res.json();

    const tbody = document.querySelector('#tbl tbody');
    const meta = document.getElementById('meta');
    const input = document.getElementById('q');
    const platformSelect = document.getElementById('platform');
    const resultSelect = document.getElementById('result');
    const fromInput = document.getElementById('from');
    const toInput = document.getElementById('to');

    const render = () => {
      const qq = (input.value || '').trim().toLowerCase();
      const platform = platformSelect.value;
      const result = resultSelect.value;
      const startKey = dateInputToKey(fromInput.value);
      const endKey = dateInputToKey(toInput.value);
      const filtered = runs.filter(r => {
        if (platform !== 'all') {
          const rp = ((r.environment && r.environment.platform) || '').toLowerCase();
          if (rp !== platform) return false;
        }
        if (result !== 'all' && getResult(r) !== result) return false;
        const dateKey = dateKeyFromTimestamp(r.timestamp);
        if (startKey && dateKey && dateKey < startKey) return false;
        if (endKey && dateKey && dateKey > endKey) return false;
        if (!qq) return true;
        const hay = [
          r.timestamp,
          (r.executor && r.executor.buildName) || '',
          (r.environment && r.environment.platform) || '',
          (r.environment && r.environment.gitBranch) || '',
          (r.environment && r.environment.gitCommit) || '',
          (r.environment && r.environment.gitMessage) || '',
          (r.environment && r.environment.deviceName) || '',
          (r.environment && r.environment.platformVersion) || '',
          (r.environment && r.environment.app) || '',
          namesFrom(r.suites),
          namesFrom(r.behaviors),
          namesFrom(r.packages)
        ].join(' ').toLowerCase();
        return hay.includes(qq);
      });
      tbody.innerHTML = filtered.map(row).join('');
      meta.textContent = `총 ${runs.length}건 중 ${filtered.length}건 표시 · 업데이트: ${new Date().toLocaleString()}`;
    };

    const clearBtn = document.getElementById('clearBtn');

    input.addEventListener('input', render);
    platformSelect.addEventListener('change', render);
    resultSelect.addEventListener('change', render);
    fromInput.addEventListener('change', render);
    toInput.addEventListener('change', render);
    clearBtn.addEventListener('click', () => {
      input.value = '';
      platformSelect.value = 'all';
      resultSelect.value = 'all';
      fromInput.value = '';
      toInput.value = '';
      render();
    });
    render();
  }

  main().catch(err => {
    const meta = document.getElementById('meta');
    meta.textContent = 'runs.json 로딩 실패: ' + err;
  });
</script>
</body>
</html>
""",
        encoding="utf-8",
    )

    return dashboard_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a simple dashboard for allure-reports history.")
    parser.add_argument("--reports-root", default="allure-reports", help="Allure reports root directory")
    args = parser.parse_args()

    reports_root = Path(args.reports_root)
    dashboard_dir = update_dashboard(reports_root)
    print(f"[update_dashboard] dashboard: {dashboard_dir}")
    print(f"[update_dashboard] open     : {dashboard_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
