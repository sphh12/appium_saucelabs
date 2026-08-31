# Pytest 직접 실행 가이드

## 사전 준비

pytest로 직접 실행할 경우, 아래 3가지가 미리 준비되어 있어야 합니다.

```bash
# 1. venv 활성화
source venv/bin/activate

# 2. Appium 서버 실행
npx appium

# 3. 에뮬레이터/시뮬레이터 실행
emulator -avd Pixel_8            # Android
open -a Simulator                # iOS (macOS)
```

> 쉘 스크립트(`run-aos.sh`, `run-ios.sh`)는 위 사전 작업을 자동으로 처리합니다.

> **pytest 설정 출처는 `pytest.ini` 단일 파일입니다.**
> `testpaths`·`python_files`·`addopts`(`-v --tb=short`)·`markers`가 모두 여기에 정의되어
> 있습니다(별도 `setup.cfg`/`pyproject.toml` pytest 설정 없음). 마커 추가/변경은 `pytest.ini`에서만
> 합니다.

---

## 기본 실행

```bash
pytest tests/android/<파일>.py -v --platform=android
pytest tests/ios/<파일>.py -v --platform=ios
```

---

## 특정 테스트 실행

```bash
# 특정 클래스::메서드
pytest tests/android/<your_test>.py::<TestClass>::<test_method> -v --platform=android

# 키워드 필터 (-k)
pytest tests/android/<your_test>.py -v --platform=android -k "login"
pytest tests/android/<your_test>.py -v --platform=android -k "login or product"

# 여러 파일 동시 실행
pytest tests/android/<your_test>.py tests/android/<other_test>.py -v --platform=android

# 전체 Android 테스트
pytest tests/android/ -v --platform=android

# 전체 iOS 테스트
pytest tests/ios/ -v --platform=ios
```

---

## 주요 옵션

### 기본 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `-v` | 상세 출력 (테스트별 PASS/FAIL 표시) | `pytest -v` |
| `-s` | print() 출력 표시 (캡처 비활성화) | `pytest -s` |
| `-x` | 첫 번째 실패 시 즉시 중단 | `pytest -x` |
| `-k "키워드"` | 테스트 이름 필터링 | `pytest -k "Login"` |
| `--tb=short` | 트레이스백 간략 표시 (기본) | `pytest --tb=short` |
| `--tb=long` | 트레이스백 상세 표시 | `pytest --tb=long` |
| `--tb=no` | 트레이스백 숨기기 | `pytest --tb=no` |

### Appium 전용 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--platform` | 플랫폼 선택 (android/ios) | `--platform=android` |
| `--app` | APK/IPA 경로 직접 지정 (config 덮어쓰기) | `--app /path/to/app.apk` |
| `--record-video` | 화면 녹화 — **기본 ON**. 성공 영상은 폐기, 실패/스킵/broken만 Allure 첨부 | `--record-video` |
| `--no-record-video` | 화면 녹화 끄기 | `--no-record-video` |
| `--allure-attach` | 첨부 정책 (hybrid/all/fail-skip) | `--allure-attach all` |

> **`--record-video`는 기본값이 ON입니다.** 성공한 케이스의 영상은 회수·첨부하지 않고
> 폐기하며(전송·디코딩 비용 0), 실패/스킵/broken 케이스 영상만 Allure에
> 첨부합니다(`--allure-attach all`이면 성공도 첨부). 녹화를 끄려면 `--no-record-video`를 사용하세요.

### 첨부 정책 (`--allure-attach`)

| 모드 | PASS 시 | FAIL/SKIP/BROKEN 시 |
|------|---------|---------------------|
| `hybrid` (기본) | 없음 | 스크린샷 + XML + Capabilities + Logcat |
| `all` | 스크린샷 + XML | 스크린샷 + XML + Capabilities + Logcat |
| `fail-skip` | 없음 | 스크린샷 + XML + Capabilities + Logcat |

---

## 마커 (Marker)

테스트에 마커를 붙여 선택적으로 실행할 수 있습니다.

```bash
# 스모크 테스트만 실행
pytest tests/android/ -v --platform=android -m smoke

# 리그레션 테스트만 실행
pytest tests/android/ -v --platform=android -m regression

# Android 마커가 붙은 테스트만
pytest tests/ -v -m android
```

등록된 마커 (출처: `pytest.ini`):

| 마커 | 설명 |
|------|------|
| `@pytest.mark.android` | Android 전용 |
| `@pytest.mark.ios` | iOS 전용 |
| `@pytest.mark.smoke` | 스모크 테스트 |
| `@pytest.mark.e2e` | E2E 시나리오 테스트 (전체 플로우) |
| `@pytest.mark.regression` | 리그레션(회귀) 테스트 |

---

## Allure 리포트 (수동)

pytest 직접 실행 시 Allure 결과 파일(`allure-results/`)은 자동 생성되지만, HTML 리포트 생성과 로컬
대시보드 갱신은 별도로 해야 합니다.

```bash
# 1. HTML 리포트 생성
allure generate allure-results -o allure-report --clean

# 2. 브라우저에서 열기
allure open allure-report

# 3. 또는 서버 모드로 열기 (자동 브라우저 오픈)
allure serve allure-results

# 4. 로컬 대시보드·리포트 열람 (프로젝트 서버)
python tools/serve.py
```

---

## 실행 예시 모음

```bash
# 가장 기본적인 실행
pytest tests/android/<your_test>.py -v --platform=android

# 특정 테스트 + 상세 로그
pytest tests/android/<your_test>.py::<TestClass>::<test_method> -v -s --platform=android

# 비디오 녹화 포함 + 전체 첨부
pytest tests/android/<your_test>.py -v --platform=android --record-video --allure-attach all

# 첫 실패 시 중단 + 상세 트레이스백
pytest tests/android/ -v -x --tb=long --platform=android

# 앱 파일 직접 지정
pytest tests/android/<your_test>.py -v --platform=android --app /path/to/custom.apk

# iOS 테스트
pytest tests/ios/<your_test>.py -v --platform=ios
```

---

## pytest vs 쉘 스크립트 비교

| 항목 | pytest 직접 실행 | 쉘 스크립트 (run-aos.sh) |
|------|-----------------|------------------------|
| Appium 서버 | 수동 시작 필요 | 자동 시작 |
| 에뮬레이터 | 수동 시작 필요 | 자동 부팅 |
| venv 활성화 | 수동 필요 | 자동 처리 |
| 드라이버 확인 | 수동 확인 | 자동 확인/설치 |
| Allure 리포트 | 수동 생성 | 자동 생성 |
| 로컬 대시보드 갱신 | 수동 실행 | 자동 갱신 |
| 실행 속도 | 빠름 (사전 작업 없음) | 약간 느림 (체크 단계 포함) |
| 적합한 상황 | 개발/디버깅 중 빠른 반복 실행 | CI/CD, 전체 파이프라인 실행 |
