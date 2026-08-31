#!/usr/bin/env bash
# iOS CI 전용 실행 스크립트 — macOS 러너에서 시뮬레이터를 고르고 부팅한 뒤 테스트를 돌린다.
#
# 시뮬레이터 이름/버전을 하드코딩하지 않는 이유: 러너의 Xcode 버전에 따라 설치된 런타임이
# 달라져(로컬은 iOS 26.5) 고정값을 쓰면 첫 런부터 세션 생성이 실패한다. 실제 사용 가능한
# 시뮬을 조회해 udid 로 지정한다(capabilities.py 가 IOS_UDID 를 지원한다).
set -euo pipefail

APPIUM_LOG="appium.log"
APPIUM_URL="http://127.0.0.1:4723/status"

echo "::group::시뮬레이터 선택"
# 가장 높은 iOS 런타임의 iPhone 계열 시뮬을 고른다
SIM_JSON="$(python3 - <<'PY'
import json, subprocess

out = subprocess.run(
    ["xcrun", "simctl", "list", "devices", "available", "--json"],
    capture_output=True, text=True, check=True,
).stdout
data = json.loads(out)

best = None  # (version_tuple, name, udid, version_str)
for runtime, devices in data.get("devices", {}).items():
    if "iOS" not in runtime:
        continue
    ver_str = runtime.split("iOS-")[-1].replace("-", ".")
    try:
        ver_tuple = tuple(int(x) for x in ver_str.split("."))
    except ValueError:
        continue
    for d in devices:
        if not d.get("isAvailable"):
            continue
        name = d.get("name", "")
        if not name.startswith("iPhone"):
            continue
        cand = (ver_tuple, name, d["udid"], ver_str)
        if best is None or cand[0] > best[0]:
            best = cand

if best is None:
    raise SystemExit("사용 가능한 iPhone 시뮬레이터가 없다")
print(f"{best[2]}\t{best[1]}\t{best[3]}")
PY
)"
IOS_UDID="$(echo "$SIM_JSON" | cut -f1)"
IOS_DEVICE_NAME="$(echo "$SIM_JSON" | cut -f2)"
IOS_PLATFORM_VERSION="$(echo "$SIM_JSON" | cut -f3)"
export IOS_UDID IOS_DEVICE_NAME IOS_PLATFORM_VERSION
echo "선택: $IOS_DEVICE_NAME (iOS $IOS_PLATFORM_VERSION) / udid=$IOS_UDID"
echo "::endgroup::"

echo "::group::시뮬레이터 부팅"
xcrun simctl boot "$IOS_UDID" || true   # 이미 부팅된 경우 비-0 이므로 무시
xcrun simctl bootstatus "$IOS_UDID" -b
xcrun simctl list devices booted
echo "::endgroup::"

echo "::group::Appium 서버 기동"
npx appium --address 127.0.0.1 --port 4723 --log-level info > "$APPIUM_LOG" 2>&1 &
APPIUM_PID=$!

READY=0
for i in $(seq 1 60); do
  if curl -sf "$APPIUM_URL" > /dev/null 2>&1; then
    echo "Appium 준비 완료 (${i}초)"
    READY=1
    break
  fi
  if ! kill -0 "$APPIUM_PID" 2>/dev/null; then
    echo "Appium 프로세스가 조기 종료됨 — 로그:"
    cat "$APPIUM_LOG"
    exit 1
  fi
  sleep 1
done
if [ "$READY" -ne 1 ]; then
  echo "Appium 기동 실패(60초 초과) — 로그:"
  cat "$APPIUM_LOG"
  exit 1
fi
echo "::endgroup::"

echo "::group::iOS 회귀 실행"
# 첫 세션에서 WebDriverAgent 를 빌드하므로 2~5분 더 걸린다(시뮬레이터는 코드 서명 불필요).
set +e
python -m pytest tests/ios -v --platform=ios --reruns 2 --alluredir allure-results
PYTEST_EXIT=$?
set -e
echo "::endgroup::"

kill "$APPIUM_PID" 2>/dev/null || true
echo "pytest exit=$PYTEST_EXIT"
exit "$PYTEST_EXIT"
