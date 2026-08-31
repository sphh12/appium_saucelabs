#!/usr/bin/env bash
# CI 전용 실행 스크립트 — 에뮬레이터 부팅 후 android-emulator-runner 의 script: 에서 호출된다.
#
# 여러 줄 셸을 YAML 안에 직접 넣으면 콜론·인용 규칙 때문에 워크플로 전체가 조용히 무효화되기 쉬워
# 별도 파일로 분리했다(로컬에서 bash -n 으로 검증 가능하다는 이점도 있다).
set -euo pipefail

APPIUM_LOG="appium.log"
APPIUM_URL="http://127.0.0.1:4723/status"

echo "::group::디바이스 확인"
adb devices -l
adb shell getprop ro.build.version.release || true

# ANR/크래시 시스템 대화상자를 OS 레벨에서 끈다.
# 소프트웨어 렌더링(SwiftShader) 환경에서는 Pixel Launcher 가 ANR 을 내는 일이 있는데,
# 그 대화상자가 앱 위를 덮으면 이후 전 테스트가 앱 대신 대화상자를 만나 무더기로 깨진다
# (실측: main 첫 런에서 16 failed / 1 passed).
adb shell settings put global hide_error_dialogs 1 || true
# 혹시 이미 떠 있는 대화상자가 있으면 정리
adb shell input keyevent KEYCODE_BACK || true
echo "::endgroup::"

echo "::group::Appium 서버 기동"
npx appium --address 127.0.0.1 --port 4723 --log-level info > "$APPIUM_LOG" 2>&1 &
APPIUM_PID=$!

# /status 응답까지 대기(최대 60초). conftest 의 preflight 보다 먼저 확인해 실패 원인을 분명히 한다.
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

echo "::group::Android 회귀 실행"
# --reruns 2 : 플레이키 완화(재시도마다 드라이버 세션을 새로 만든다)
# 스크린샷/비디오/logcat 은 conftest 기본값(--allure-attach=hybrid)에 따라 실패 시에만 첨부된다
set +e
python -m pytest tests/android -v --platform=android --reruns 2 --alluredir allure-results
PYTEST_EXIT=$?
set -e
echo "::endgroup::"

kill "$APPIUM_PID" 2>/dev/null || true
echo "pytest exit=$PYTEST_EXIT"
exit "$PYTEST_EXIT"
