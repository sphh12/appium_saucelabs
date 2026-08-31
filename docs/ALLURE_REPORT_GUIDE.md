# Allure Report 사용 가이드 (로컬/CI 공통)

이 문서는 Allure Report 웹 UI(예: `http://127.0.0.1:60703/#`)에서 **각 탭이 의미하는 바**와
**실무에서 빠르게 원인 분석하는 사용 루틴**을 정리합니다.

---

## 1) Allure 리포트가 만들어지는 흐름(How it works 요약)

Allure는 크게 아래 3단계로 동작합니다.

1. **테스트 실행 중 데이터 수집**
   - 프레임워크 어댑터(allure-pytest 등)가 테스트 생명주기(Setup/Call/Teardown)에 걸쳐
     step, 실행 시간, 상태, 첨부(스크린샷/비디오/로그) 등을 결과 폴더에 기록합니다.
   - 기본 결과 폴더는 보통 `allure-results`입니다.

2. **메타데이터 보강(Optional)**
   - `environment.properties`, `executor.json`, `categories.json`, `history/` 같은 추가 파일로
     “환경 정보/실행자/분류 규칙/트렌드”를 리포트에 반영할 수 있습니다.

3. **리포트 생성/열람**
   - `allure generate`로 정적 HTML 리포트를 생성(아카이빙/공유에 적합)
   - `allure open` 또는 `allure serve`로 로컬에서 빠르게 열람

공식 문서 참고: https://allurereport.org/docs/how-it-works/

---

## 1.1) 이 프로젝트에서의 저장 구조(중요)

이 레포는 실행 이력을 남기기 위해 결과/리포트를 타임스탬프 폴더로 보관합니다.

- 결과(raw): `allure-results/YYYYMMDD_HHMMSS/`
- 리포트(html): `allure-reports/YYYYMMDD_HHMMSS/`
- 최신 고정 엔트리: `allure-reports/LATEST/index.html`
- 전체 이력 대시보드: `allure-reports/dashboard/index.html`

`tools/run_allure.py` 또는 `shell/run-app.sh`로 실행하면 위 구조가 자동으로 갱신됩니다.

## 1.2) 리포트 열기 — HTTP 서버가 필요한 이유

생성된 `index.html`은 데이터를 품고 있지 않은 껍데기 페이지입니다. 실제 결과는
`widgets/*.json`·`data/*.json`을 런타임에 XHR로 읽어오므로, **파일을 더블클릭해서(`file://`) 열면
스피너만 돌고 내용이 나오지 않습니다.** 대시보드도 같은 이유(+`runs.json` fetch, 프로젝트 루트 기준
절대경로 링크)로 서버가 필요합니다.

| 방법 | 명령 | 비고 |
|------|------|------|
| **프로젝트 서버(권장)** | `python tools/serve.py` | 대시보드 + 모든 리포트를 한 번에. 프로젝트 루트를 서빙하므로 대시보드 링크가 정상 동작 |
| 최신 리포트 바로 | `python tools/serve.py --latest` | |
| Allure CLI | `npx allure open allure-reports/<타임스탬프>` | 리포트 **폴더 하나**를 루트로 서빙 → 대시보드 링크(`/allure-reports/...`)는 404. `LATEST`는 리다이렉트 스텁이라 이 방식으로 열면 안 됨 |
| **서버 없이 단일 파일** | `allure generate <결과폴더> -o <출력폴더> --clean --single-file` | 모든 데이터를 HTML 하나에 base64로 내장(약 2.7MB) → `file://` 더블클릭으로 열림. 공유·첨부용으로 유용 |

> Allure CLI는 **리포트 생성**에는 필수지만, **열람**에는 필수가 아닙니다(위 표의 1·2행은 CLI
> 불필요).

---

## 2) 상태(Status) 빠른 이해

Allure UI에서 가장 자주 보는 상태 의미는 아래와 같습니다.

- **PASSED**: 테스트가 기대대로 성공
- **FAILED**: 검증(assert) 실패 등 “테스트 로직상 실패”
- **BROKEN**: 주로 예외/환경 문제로 테스트가 정상 수행되지 못함(Setup/Teardown 실패, 세션 끊김,
  타임아웃 등)
- **SKIPPED**: 조건에 의해 실행이 건너뜀(pytest skip/marker 등)

실무 팁:

- 실패가 많을 때는 `FAILED`/`BROKEN` 비율이 높아졌는지부터 확인하고,
  `BROKEN`이 많다면 환경/인프라(Appium/디바이스/네트워크) 이슈 가능성을 먼저 봅니다.

---

## 3) 좌측 탭별 기능 요약

### 3.1 Overview (전체 요약)

**목적**: “이번 실행이 전체적으로 건강한가?”를 30초~1분 안에 판단.

주로 확인하는 내용

- Passed/Failed/Broken/Skipped 카운트와 비율
- 트렌드(History가 연결되어 있을 때): 최근 실행 대비 실패 증가/감소
- Environment/Executor 정보: 어떤 OS/디바이스/브랜치/커밋에서 돌렸는지

추천 사용 흐름

- Overview에서 **이상 징후**를 보고 → `Categories` 또는 `Suites`로 내려가 원인 분석.

---

### 3.2 Suites (테스트 구조 탐색)

**목적**: 테스트를 파일/클래스/스위트 구조로 탐색하면서 **개별 테스트를 깊게 분석**.

주로 하는 일

- 실패/깨짐/스킵 케이스 선택
- Steps(Execution)에서 어느 단계에서 멈췄는지 확인
- Attachments(스크린샷/비디오/log/page source 등)로 재현 없이 원인 단서 확보
- History / Retries로 flaky 여부(재시도에서만 통과하는지) 확인

실무에서 가장 자주 클릭하는 화면입니다.

---

### 3.3 Categories (실패 유형별 분류)

**목적**: 실패를 “유형별”로 묶어서 원인 파악 시간을 단축.

동작 방식

- 스택트레이스/메시지에 정규식 룰을 적용해 카테고리로 자동 분류합니다.
  (예: UI 동기화 타임아웃, 요소 탐색 실패, 서버 연결 실패 등)

추천 사용 흐름

- 실패가 많을 때 **가장 큰 카테고리부터** 해결하면 효율이 좋습니다.

---

### 3.4 Graphs (차트/분포)

**목적**: 결과를 차트로 요약하여 품질 패턴을 빠르게 확인.

자주 보는 포인트(구성은 리포트 버전에 따라 일부 다를 수 있음)

- Status 분포: 실패/스킵 비율 변화
- Duration 분포: 느린 테스트가 늘었는지
- Severity 분포: 중요도 라벨 기반(팀이 라벨을 잘 쓰고 있을 때 유용)

추천 사용 흐름

- “느려진 구간”이나 “특정 중요도에서 실패가 몰림” 같은 운영 관점 분석에 좋습니다.

---

### 3.5 Timeline (시간축)

**목적**: 테스트가 시간축에서 어떻게 실행됐는지 시각화.

유용한 상황

- 병렬 실행 시 특정 시간대에 실패가 몰리는지
- 특정 구간에서 대기/응답 지연이 집중되는지

---

### 3.6 Behaviors (기능 라벨 기반)

**목적**: `feature`/`story`(또는 epic 등) 라벨 기준으로 기능 단위 품질을 확인.

추천 사용 흐름

- “기능별 품질 현황”을 보고할 때 Suites보다 직관적인 경우가 많습니다.

---

### 3.7 Packages (코드 단위 그룹)

**목적**: 테스트를 패키지/모듈/클래스 단위로 묶어 코드 소유권 관점에서 확인.

추천 사용 흐름

- “어느 모듈이 가장 많이 깨지나?” 같은 담당 범위 중심 분석에 적합.

---

## 4) 개별 테스트 상세 화면: 꼭 알아야 할 것

### 4.1 Execution / Steps

- 테스트가 어떤 순서로 수행됐는지, 어느 Step에서 실패/스킵됐는지 확인합니다.
- 모바일 테스트는 UI 동기화 문제로 “실패 지점”이 중요하므로 Step 단위 기록이 특히 유용합니다.

### 4.2 Attachments

주로 첨부되는 자료 예시

- 스크린샷(PNG)
- 비디오(mp4)
- page source(XML/TEXT)
- logcat(TEXT)
- capabilities(JSON)

이 프로젝트에서 첨부가 붙는 대표 케이스

- **기본(hybrid)**: FAIL/SKIP/BROKEN에만 첨부(성공은 첨부하지 않음)
- **다 붙이기(all)**: 성공(PASS)까지 포함해 최대한 첨부

옵션

- `--allure-attach=hybrid` (기본)
- `--allure-attach=all`

실무 팁

- 실패 직후 화면(스크린샷/비디오) + page source + 로그 조합이면 재현 없이도 원인 추정이 가능한
  경우가 많습니다.

### 4.3 History / Retries

- History: 이전 실행들에서 같은 테스트가 어땠는지
- Retries: 재시도 내역이 있으면 “처음 실패 → 재시도 성공” 같은 flaky 패턴을 확인 가능

---

## 5) 실무용 ‘30초 분석 루틴’ 추천

1. **Overview**: Failed/Broken이 급증했는지 확인
2. **Categories**: 가장 큰 실패 카테고리부터 확인(환경/동기화/요소 탐색)
3. **Suites → 실패 테스트 선택**
4. **Steps**에서 실패 위치 확인
5. **Attachments**에서 스크린샷/비디오/log/page source를 순서대로 확인
6. flaky 의심이면 **Retries/History**로 “재시도 성공 패턴” 확인

---

## 6) 로컬 이력 대시보드

실행 이력은 **로컬 대시보드**에 누적됩니다. 이 저장소는 공개용이라 **테스트 결과를 외부로 업로드하지
않습니다.**

- **위치**: `allure-reports/dashboard/index.html` (실행마다 `update_dashboard.py`가 자동 갱신)
- **기능**: 실행 이력 목록(날짜·통계·소요시간), 각 리포트로 이동
- **첨부파일**: 스크린샷·비디오·logcat·page_source는 각 리포트 안에 그대로 보관

### 실행 방식

```bash
# Shell 스크립트 (권장)
./shell/run-aos.sh --<your_test>             # Android
./shell/run-ios.sh --<your_test>             # iOS

# run_allure.py 직접 실행
python tools/run_allure.py -- tests/android/<your_test>.py -v --platform=android
```

> - 파일명에서 `.py`는 생략 가능 (`--<your_test>` = `tests/<platform>/<your_test>.py`)

### 열람

```bash
python tools/serve.py            # 대시보드
python tools/serve.py --latest   # 최신 리포트
```

서버가 필요한 이유와 서버 없이 보는 방법은 §1.2 참고.

---

## 6.1) 로컬 리포트 접근

로컬에서도 리포트를 확인할 수 있습니다.

- `allure-reports/LATEST.txt`: 최신 실행 timestamp 기록
- `allure-reports/LATEST/index.html`: 최신 리포트로 리다이렉트

특정 실행 리포트는 `allure-reports/<timestamp>/index.html`을 열면 됩니다.

### 로컬 대시보드

전체 실행 이력을 로컬에서 보려면 간단 서버가 필요합니다.

```bash
# 레포 루트에서 실행
python -m http.server 8000
```

브라우저 접속: `http://127.0.0.1:8000/allure-reports/dashboard/`

> 서버를 `allure-reports/dashboard` 폴더에서 띄우면 상위 리포트 폴더에 접근할 수 없어 404가
> 발생합니다. 반드시 레포 루트에서 띄우세요.

---

## 7) 자주 겪는 질문(FAQ)

### Q1. 스크린샷/비디오가 너무 커서 텍스트까지 줄여야 해요.

- 권장: 브라우저 줌을 낮추지 말고, 첨부 미디어 미리보기 크기만 제한하는 CSS 후처리를 적용합니다.

참고(이 레포 적용 내용)

- 생성된 리포트의 `index.html`에 `custom.css`가 주입되어 첨부 미리보기만 줄어듭니다.

### Q2. SKIPPED인데도 스크린샷/비디오가 없어요.

- 테스트가 드라이버/녹화 시작 전에 skip되면(예: collection/fixture 진입 전) 캡처할 대상이 없어
  첨부가 불가능합니다.

### Q4. BROKEN인데 비디오가 안 붙어요.

- BROKEN은 주로 setup/teardown 실패로 발생하며, 드라이버가 정상 생성되기 전에 실패하면 녹화/첨부
  자체가 불가능합니다.
- 드라이버가 생성되고 `--record-video`가 켜진 상태에서 실패했다면, teardown 시점에 저장된 녹화
  파일이 Allure에 첨부됩니다.

### Q3. “다 붙이기” / “하이브리드”가 뭐예요?

- `--allure-attach=hybrid`(기본): FAIL/SKIP/BROKEN만 첨부(성공은 첨부하지 않음)
- `--allure-attach=all`: 성공(PASS)까지 포함해 최대한 첨부

---

## 부록) 어노테이션/라벨(권장)

팀에서 아래 라벨을 꾸준히 쓰면 Behaviors/Graphs가 훨씬 유용해집니다.

- `@allure.feature("..." )`
- `@allure.story("..." )`
- `@allure.severity(...)`
- `@allure.title("..." )`
- `@allure.description("..." )`
- `with allure.step("..." ):`

---

## 8) 진단용 첨부 파일 상세 가이드

테스트 실패 시 자동으로 첨부되는 진단 파일들입니다. 재현 없이 원인을 파악하는 데 핵심적인 역할을
합니다.

### 8.1 page_source_*.xml (UI 구조 스냅샷)

**설명**: 테스트 실패 시점의 화면 UI 구조를 XML 형태로 캡처한 파일입니다.

**확인 가능한 정보**:

- 현재 화면에 표시된 모든 UI 요소 목록
- 각 요소의 속성 (`resource-id`, `content-desc`, `text`, `class`, `bounds` 등)
- 요소의 상태 (`clickable`, `enabled`, `displayed`, `focused` 등)
- 화면 계층 구조 (부모-자식 관계)

**활용 방법**:

| 상황 | 확인 포인트 |
|------|-------------|
| 요소를 찾지 못함 | XML에서 해당 요소가 존재하는지 검색 |
| 잘못된 화면 | 예상 화면의 고유 요소가 있는지 확인 |
| 로케이터 실패 | `resource-id`, `content-desc` 값 변경 여부 확인 |
| 동적 요소 | `text` 속성이 예상과 다른지 확인 |

**예시**:
```xml
<android.widget.Button
    resource-id="com.app:id/btn_login"
    text="로그인"
    clickable="true"
    enabled="false"  <!-- 버튼이 비활성화 상태! -->
    bounds="[100,500][300,600]"
/>
```

---

### 8.2 capabilities_*.json (Appium 설정 정보)

**설명**: 테스트 실행 시 사용된 Appium Desired Capabilities 설정 파일입니다.

**확인 가능한 정보**:

- **디바이스 정보**: `deviceName`, `udid`, `platformVersion`
- **앱 정보**: `appPackage`, `appActivity`, `app` 경로
- **자동화 설정**: `automationName`, `autoGrantPermissions`, `noReset`
- **타임아웃 설정**: `newCommandTimeout`, `adbExecTimeout`
- **기타 옵션**: `unicodeKeyboard`, `resetKeyboard`, `fullReset` 등

**활용 방법**:

| 상황 | 확인 포인트 |
|------|-------------|
| 특정 디바이스에서만 실패 | `platformVersion`, `deviceName` 차이 확인 |
| 앱 상태 문제 | `noReset`, `fullReset` 설정 확인 |
| 타임아웃 실패 | `newCommandTimeout` 값 확인 |
| 권한 문제 | `autoGrantPermissions` 설정 확인 |

**예시**:
```json
{
  "platformName": "Android",
  "platformVersion": "14",
  "deviceName": "emulator-5554",
  "appPackage": "com.saucelabs.mydemoapp.android",
  "automationName": "UiAutomator2",
  "noReset": true,
  "newCommandTimeout": 300
}
```

---

### 8.3 logcat_*.txt (Android 시스템 로그)

**설명**: 테스트 실행 중 수집된 Android 시스템 로그입니다. 앱 내부 동작과 시스템 수준의 이벤트를
확인할 수 있습니다.

**확인 가능한 정보**:

- **앱 크래시**: `FATAL EXCEPTION`, `java.lang.NullPointerException` 등
- **ANR(응답 없음)**: `ANR in com.app`, `Input dispatching timed out`
- **네트워크 오류**: `UnknownHostException`, `SocketTimeoutException`
- **메모리 문제**: `OutOfMemoryError`, GC 로그
- **앱 로그**: 개발팀이 남긴 `Log.d()`, `Log.e()` 메시지
- **시스템 이벤트**: Activity 전환, 서비스 시작/종료

**주요 검색 키워드**:

```
FATAL           # 앱 크래시
ANR             # 응답 없음
Exception       # 예외 발생
Error           # 에러 로그
com.saucelabs   # 특정 앱 패키지 로그
ActivityManager # 액티비티 전환 이벤트
```

**활용 방법**:

| 상황 | 확인 포인트 |
|------|-------------|
| 앱이 갑자기 종료 | `FATAL EXCEPTION` 검색 |
| 화면 전환 안됨 | `ActivityManager` 로그에서 Activity 전환 확인 |
| 네트워크 실패 | `Exception` 검색 후 네트워크 관련 에러 확인 |
| 버튼 클릭 안됨 | ANR 또는 UI 블로킹 로그 확인 |

---

### 8.4 진단 파일 활용 워크플로우

테스트 실패 시 권장하는 분석 순서:

```
1. 스크린샷 확인
   └─ 실패 시점의 실제 화면 상태 파악

2. page_source.xml 분석
   └─ 예상 요소가 있는지, 속성이 맞는지 확인

3. logcat.txt 검색
   └─ 앱 크래시, ANR, 네트워크 에러 등 확인

4. capabilities.json 검토
   └─ 환경 설정 문제인지 확인 (타임아웃, 디바이스 등)
```

**실패 유형별 우선 확인 파일**:

| 실패 유형 | 1순위 | 2순위 | 3순위 |
|-----------|-------|-------|-------|
| 요소 못 찾음 | page_source.xml | 스크린샷 | logcat.txt |
| 앱 크래시 | logcat.txt | 스크린샷 | capabilities.json |
| 타임아웃 | logcat.txt | capabilities.json | page_source.xml |
| 잘못된 화면 | 스크린샷 | page_source.xml | logcat.txt |

---

### 8.5 진단 파일 저장 위치

첨부 파일은 Allure 결과 폴더에 저장됩니다:

```
allure-results/YYYYMMDD_HHMMSS/
├── *-attachment.xml      # page_source
├── *-attachment.json     # capabilities
├── *-attachment.txt      # logcat
├── *-attachment.png      # screenshot
└── *-attachment.mp4      # video (녹화 옵션 사용 시)
```

Allure UI에서는 각 테스트의 **Attachments** 섹션에서 확인할 수 있습니다.

---

## 9) 리포트 HTML Export (공유/보관용)

Allure 리포트를 단일 HTML 파일로 추출하여 공유하거나 보관할 수 있습니다.

### 9.1 Export 방법 비교

| 방법 | 파일 크기 | 특징 | 용도 |
|------|-----------|------|------|
| **allure-combine** | ~9 MB | 전체 리포트 (모든 기능 포함) | 완전한 아카이브 |
| **export_summary.py** | 8~270 KB | 요약 리포트 (핵심 정보만) | 빠른 공유, 이메일 첨부 |

---

### 9.2 allure-combine (전체 리포트)

모든 에셋(JS, CSS, 이미지)을 인라인으로 포함한 단일 HTML 파일을 생성합니다.

**설치:**
```bash
pip install allure-combine
```

**사용법:**
```bash
# 기본 사용
allure-combine allure-reports/20260127_153847

# 출력 경로 지정
allure-combine allure-reports/20260127_153847 --dest ./export/complete.html
```

**Python API:**
```python
from allure_combine import combine_allure

combine_allure(
    "allure-reports/20260127_153847",
    dest_folder="allure-reports/export",
    auto_create_folders=True
)
```

**출력:** `complete.html` (~9 MB)

---

### 9.3 export_summary.py (경량 요약)

핵심 정보만 추출한 경량 HTML을 생성합니다. 스크린샷은 Base64로 인라인 포함됩니다.

**사용법:**
```bash
# 스크린샷 포함 (기본)
python tools/export_summary.py allure-reports/20260127_153847

# 스크린샷 제외 (더 작은 파일)
python tools/export_summary.py allure-reports/20260127_153847 --no-screenshots

# 출력 경로 지정
python tools/export_summary.py allure-reports/20260127_153847 -o ./my_report.html
```

**포함 정보:**
- 테스트 결과 요약 (Total, Passed, Failed, Broken, Skipped)
- 실행 시간 (Duration)
- 환경 정보 (Device, OS, App 등)
- 테스트 케이스 목록 (상태별 정렬)
- 실패/깨짐 테스트의 에러 메시지
- 스크린샷 (옵션, 테스트당 최대 3장)

**출력 크기:**
- 스크린샷 포함: ~270 KB
- 스크린샷 제외: ~8 KB

---

### 9.4 Export 파일 저장 위치

```
allure-reports/
├── export/
│   ├── complete.html                          # allure-combine 출력
│   ├── summary_with_screenshots_*.html        # 스크린샷 포함 요약
│   └── summary_no_screenshots_*.html          # 스크린샷 제외 요약
└── 20260127_153847/                           # 원본 리포트
```

---

### 9.5 용도별 권장 방법

| 용도 | 권장 방법 | 이유 |
|------|----------|------|
| 장기 보관/아카이브 | allure-combine | 모든 정보 보존 |
| 이메일 공유 | export_summary (no-screenshots) | 8 KB로 첨부 제한 없음 |
| Slack/Teams 공유 | export_summary (with-screenshots) | 270 KB로 적당한 크기 |
| 상세 디버깅 | 원본 리포트 서버 | 전체 기능 사용 가능 |
