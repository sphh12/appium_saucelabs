# Changelog

> SauceLabs My Demo App Appium 자동화 프로젝트의 변경 이력 + 할일 추적 (구 `change_notes.md` + `Todo.md` 통합)
> 형식: [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 참고 — 최신이 위, 날짜별 섹션
> 신규 항목은 `### Added` / `### Changed` / `### Fixed`로 분류 (2026-08-24 이전 이력은 원문 그대로 보존)
> 구 `Todo.md` 원본 보존: [archive/TODO-2026.md](archive/TODO-2026.md)

> **저장소 재생성 안내(2026-08-31)**: 초기 커밋에 이전 프로젝트의 내부 식별자가 남아 있어
> 저장소를 새로 만들고 이력을 초기화했다. 따라서 아래 이력 중 **2026-08-31 이전 항목이 인용하는
> 커밋 해시와 PR 링크는 옛 저장소의 것이라 더 이상 조회되지 않는다**(내용 기록은 그대로 유효).
> 전체 커밋 이력은 로컬 번들로 보관 중이다.

## [Unreleased]

### 다음 작업 (우선순위순)

- [ ] **R-11 (iOS 카트 수량 테스트) 보류 해제** — 시뮬 부팅 후 `python tools/ui_dump_ios.py -w`로 수량/합계 accessibility id 확보 → iOS `CartPage` getter 보강 → `test_change_quantity` 추가
- [ ] 코드 리뷰 잔여 — 🟡 개선(Low) 41건(`docs/CODE_REVIEW_2026-06-29.md` §5) + ℹ️ 정보성(Info) 10건(§6)

### CI 후속 (남은 결정)

- [ ] (검토) **`run-name` 지정** — 수동·스케줄 런은 제목이 워크플로 이름으로만 표시된다(GitHub 규칙). `run-name: "iOS 회귀 · ${{ github.event_name == 'schedule' && '야간' || '수동' }} · ${{ github.actor }}"` 식으로 넣으면 목록에서 야간/수동을 구분할 수 있다
- [ ] (검토) 문서 커밋에 `paths-ignore: ['**.md']` — 지금은 문서만 고쳐도 8~9분짜리 에뮬레이터 런이 돈다
- [ ] (검토) 남은 긴 줄 정리 — `docs/CODE_REVIEW_2026-06-29.md`(24건)·`MCP_개념_가이드`·`MCP_단계별_실행계획`(9건). 체크리스트 기록물이라 보류 중
- [ ] (검토) cron을 **KST 03:05로 정렬** — playwright_sauceLabs가 실측 지연(평소 +19분, GitHub 장애 시 +203분)을 근거로 03:05 사용. 현재 03:20도 3시간 지연 시 06:30 이전 종료라 문제는 없음
- [ ] (검토) **`package-lock.json` 커밋 정책** — 현재 `.gitignore` 대상이라 CI에서 npm 캐시·`npm ci`를 못 쓴다. 커밋하면 설치 30~60초 단축 + Appium 버전이 CI에서 예고 없이 올라가는 것 방지
- [ ] (검토) **액션 메이저 버전 상향** — Node 20 deprecation 경고(checkout/setup-node/setup-python/upload-artifact가 Node 24로 강제 실행 중). green 확보를 우선해 미뤘음

### 자동화 확장 (구 Step 10)

- [ ] **Tier 3** (권한·디바이스 의존): QR(카메라)/Geo(위치)/FingerPrint(지문)/Drawing(제스처)/Virtual USB/Crash 2종
- [ ] 보강: 결제수단 필드 검증(F6.2), 다중 상품 구매, 정렬 name asc/desc, 다른 상품 구매 경로
- [ ] **iOS 키보드 블로커 해결** (Xcode 26.5 한글 소프트 키보드) → 해결 시 체크아웃 완주 E2E + WebView URL 추가 (현재 2건 skip)
- [ ] iOS 추가: 결제수단/리뷰/완료 화면(키보드 해결 후), QR·Geo·Drawing·Biometrics(권한·디바이스 의존)

### 보류 / 차후 결정

- README 영문판 작성 (한국어판 완료)
- 서브 프로젝트: WebdriverIO Native Demo App (메인 완료 후)

---

## 2026-08-31

### Changed
- **워크플로 이름 체계 정리** — `My Demo App - Android/iOS` → **`[Android] Appium - My Demo App`** / **`[iOS] Appium - My Demo App`**
  (플랫폼을 대괄호로 앞세워 목록에서 먼저 눈에 띄게 하고, 도구명 `Appium` 을 붙여 다른 저장소의 Playwright·Cypress 워크플로와 구분). `docs/CI_GUIDE.md` 표도 갱신
- **실행 이력(런) 제목 지정 — `run-name` 추가** (두 워크플로 공통)
  - 스케줄·수동 런은 커밋 맥락이 없어 GitHub 이 워크플로 이름으로 폴백한다. 그래서 목록의 모든 야간 런이 `My Demo App - iOS` 로만 보여 구분이 되지 않았다
  - `schedule` → **`[Daily] Regression Test`** / `workflow_dispatch` → `[Manual] Regression Test`
  - `push`·`pull_request` 는 빈 문자열로 둬 GitHub 기본값(커밋 메시지·PR 제목)을 유지 — 커밋 제목이 사라지지 않게
  - 워크플로 이름은 부제(`... #12: Scheduled`)에 남아 플랫폼 구분은 그대로 된다
  - `docs/CI_GUIDE.md` 에 트리거별 제목 표 추가

## 2026-08-28

### Changed
- **`fix/code-review-medium` → main 병합 완료** (PR [#1](https://github.com/sphh12/appium_saucelabs/pull/1), 머지 커밋 `79bcf26`)
  - CHANGELOG 가 개별 커밋 해시를 인용하므로 squash 대신 **머지 커밋**으로 이력을 보존
  - 병합으로 `schedule`·`workflow_dispatch` 가 활성화됐다 — 기본 브랜치의 워크플로 파일만 스케줄되기 때문
  - 병합 조건이던 **iOS 미검증 2파일은 iOS CI 로 해소**(집 macOS 대기 불필요)
- **산문 줄바꿈 정리** — README + docs 가이드 11개의 긴 줄(최대 260자)을 표시 폭 100칸 기준으로 **문단 단위 재정렬**(줄 단위로 접으면 이미 접힌 문단에 짧은 자투리가 생겨 오히려 나빠진다). 표·코드블록·제목은 미변경, CHANGELOG·CODE_REVIEW 는 기록물이라 제외
  - 검증 2겹: 본문 문자 동일성(공백·인용접두 제거 후) + **GitHub `/markdown` API 렌더 HTML 동일성** 11/11
  - 검증이 잡은 결함 3건: ① 토큰 재조립이 `` `code`(주석) `` 처럼 붙은 곳에 공백 삽입 → 자르기 방식으로 변경 ② 접힌 줄이 `+` 로 시작해 마크다운이 불릿으로 해석 → 줄머리 블록 마커 금지 ③ `>` 만 있는 인용 구분줄을 경계로 못 봐 두 문단 병합 → 경계 처리 추가
  - 부수 확인: 정적 검사가 지적한 "제목·표·목록 앞 빈 줄 누락" 33건은 **GitHub 렌더러 실측 결과 전부 오탐**(표·목록·코드블록은 문단을 중단할 수 있다)

### Added
- **iOS 회귀 워크플로 신설** — `.github/workflows/ios-regression.yml` + `.github/scripts/run-ios-ci-tests.sh`
  - `macos-latest` 러너의 시뮬레이터에서 `tests/ios` 실행. 트리거는 **수동 + 스케줄(KST 03:50)** 만 — push/PR 을 뺀 것은 일상 푸시마다 macOS 러너를 쓰지 않고 iOS 불안정성이 PR 게이트를 막지 않게 하기 위함
  - **Android 와 파일 분리** — 같은 워크플로에 job 으로 붙이면 iOS 문제(WDA 빌드 등)로 Android 회귀까지 붉어진다
  - 시뮬레이터를 **동적 선택**(`xcrun simctl list devices available --json` → 최신 iOS 런타임의 iPhone → `IOS_UDID` 로 지정). 러너 Xcode 버전에 따라 런타임이 달라 고정값은 첫 런부터 깨진다
  - 앱은 릴리스 2.2.2 의 `SauceLabs-Demo-App.Simulator.zip` 다운로드 + ZIP 매직 검증 (`capabilities.py` 가 `.zip` 을 그대로 인식해 압축 해제 불필요)
  - 이 워크플로가 **미검증 iOS 2파일**(`pages/ios/catalog_page.py`, `tests/ios/test_about.py`)의 검증을 대신할 수 있다 — macOS 장비를 기다릴 필요가 없어졌다

### Changed
- 워크플로 이름을 플랫폼 체계로 정리: `Android Regression - SMDA` → **`My Demo App - Android`**, 신규 **`My Demo App - iOS`** (앱 실제 라벨이 `My Demo App` 임을 APK `application-label` 로 확인)
- `docs/CI_GUIDE.md`: 워크플로 2개 비교표 · iOS 워크플로 절(동적 시뮬 선택·WDA·skip 2건·실기기 한계) · iOS 트러블슈팅 2종 추가

### Fixed
- **iOS About 버전 단언이 실제 화면과 맞지 않던 문제 — CI 가 미검증 코드의 실제 버그를 잡아냄**
  - 2026-07-01 코드 리뷰 R-10 이 동어반복 제거를 위해 `re.search(r"\d+\.\d+", v)` 로 바꿨는데, **온디바이스 검증 없이 들어간 추측**이었다
  - CI 실측: iOS About 텍스트는 `"Demo App V.01 by "` — `숫자.숫자` 패턴이 없어 항상 실패한다
  - Android 쪽 단언(`version.startswith("V.")`)과 같은 규약으로 `r"V\.\s*\d+"` 로 정정. 로케이터(`label BEGINSWITH 'Demo App'`)와 독립적이므로 동어반복도 아니다
  - 이로써 **미검증 iOS 2파일이 모두 검증됐다** — `pages/ios/catalog_page.py` 는 `test_catalog` 통과로, `tests/ios/test_about.py` 는 이 수정으로. 집 macOS 를 기다리던 병합 조건이 CI 로 해소됨
- **iOS CI 첫 세션 WDA 기동 실패 수정** — 첫 런([33135296802](https://github.com/sphh12/appium_saucelabs/actions/runs/33135296802))이 `9 passed, 2 skipped, 1 error`
  - 유일한 error 는 **첫 테스트**의 `Unable to start WebDriverAgent session ... ECONNREFUSED 127.0.0.1:8100`. 첫 세션이 WDA 를 빌드·설치하는 동안 기본 타임아웃(60초)을 넘긴 것으로, 이후 테스트는 WDA 가 이미 떠 있어 전부 통과했다 — 테스트 코드가 아니라 워밍업 문제
  - `capabilities.py` IOS_CAPS 에 `wdaLaunchTimeout`(기본 240초, `IOS_WDA_LAUNCH_TIMEOUT` 로 조절) · `wdaStartupRetries` · `wdaStartupRetryInterval` 추가. CI 는 360초 주입
  - 새 macOS 머신에서 처음 돌릴 때도 같은 증상이 나므로 **로컬에도 적용되는 개선**이다
  - 성과: 시뮬레이터 동적 선택(iPhone 17 Pro / iOS 26.5 자동 선택)·앱 설치·9개 케이스 통과로 **iOS 파이프라인 자체는 동작 확인**
- **CI 무더기 실패(16 failed / 1 passed) 수정 — ANR 시스템 대화상자 차단**
  - PR #1 병합 후 main 첫 푸시 런([33129044712](https://github.com/sphh12/appium_saucelabs/actions/runs/33129044712))이 실패. 같은 코드가 PR 에서 3연속 green 이라 원인을 아티팩트로 추적
  - 실패 시점 `page_source.xml` 이 앱이 아니라 **시스템 대화상자**였다: `package="android"` · `android:id/aerr_close` · `"Pixel Launcher isn't responding" / Close app / Wait`
  - 소프트웨어 렌더링(SwiftShader) 환경에서 Pixel Launcher 가 ANR 을 내면 그 대화상자가 앱 위를 덮고, 이후 전 케이스가 앱 대신 대화상자를 만나 무너진다(에뮬레이터 부팅 41.6초·첫 테스트 통과로 '러너가 느려서'가 아님을 확인)
  - 조치 ①(근본): `run-ci-tests.sh` 에서 `adb shell settings put global hide_error_dialogs 1` 로 ANR/크래시 대화상자를 OS 레벨에서 차단
  - 조치 ②(방어): `conftest._dismiss_system_ui_dialog` 를 resource-id 기반(`android:id/aerr_close` → `aerr_wait` → 텍스트 폴백)으로 강화하고 **Close app 우선**으로 변경 — Launcher ANR 은 Wait 로는 해소되지 않아 대화상자가 계속 남는다
  - 기존 구현의 한계도 함께 정리: 텍스트 `Wait` 단일 매칭이라 로케일·버튼 구성이 다르면 놓쳤다

## 2026-08-27

### Added
- **GitHub Actions 야간 회귀 CI 구축** — `.github/workflows/android-regression.yml` + `.github/scripts/run-ci-tests.sh`
  - 트리거 4종: `push`(main/master) · `pull_request` · `workflow_dispatch` · `schedule`
  - 스케줄 `'20 18 * * *'` = **UTC 18:20 = KST 03:20** (정시는 GitHub 부하로 밀려 비정시로 둠)
  - 실패 시 `--reruns 2` 재시도(플레이키 완화) → `requirements.txt`에 `pytest-rerunfailures==16.6` 추가(pytest 9.0.2 호환 확인)
  - Allure 리포트(`allure-report/` + `allure-results/` + `appium.log`)를 성공·실패 무관 업로드, 보관 30일
  - 스크린샷·비디오·logcat은 **실패 시에만 첨부** — conftest 기본값(`--allure-attach=hybrid`, `--record-video` ON이지만 성공 영상은 폐기)이 이미 그렇게 동작하므로 그대로 유지
  - Appium 특성 반영(참조한 Playwright 워크플로와 다른 부분): KVM 활성화 + `reactivecircus/android-emulator-runner`(API 34 / x86_64 / google_apis) 에뮬레이터 부팅, `apps/`가 gitignore라 APK를 릴리스에서 `curl`로 받고 ZIP 매직 검증, Appium 서버 기동 후 `/status` 응답 대기(최대 60초)
  - **여러 줄 셸은 YAML에 넣지 않고 `.github/scripts/run-ci-tests.sh`로 분리** — 콜론·인용 규칙으로 워크플로가 통째로 무효화되는 사고를 피하고 `bash -n`으로 로컬 검증이 가능하다
  - 시크릿 불필요: `.env` 전 항목이 선택값이고 테스트 계정은 앱에 표시되는 공개 데모값 (저장소가 Public이라 Actions 실행 시간도 무료)
  - iOS 미포함: macOS 러너·WDA 빌드 필요 + `apps/ios`가 구 RN 빌드(1.3.0)로 대상 앱 불일치 + 키보드 이슈 2건 skip → `CI_CD_STRATEGY.md` 시나리오 A/B 순서에 맞춰 후속
- **CI 첫 green 확보 — 17 passed (5분 31초, 재시도 0건)** · 런 [33053458405](https://github.com/sphh12/appium_saucelabs/actions/runs/33053458405) · job 8분 23초 · 아티팩트 1.2MB
  - 실패 지점을 3번에 걸쳐 내려가며 수정했다(각 원인은 아래 Fixed 항목):
    1차 `setup-node`(25초) → 2차 드라이버 스텝(42초) → 3차 테스트 실행(11분 23초) → **4차 성공**
  - 3차 런에서 인프라 전 구간(Appium 4초 준비 · APK 다운로드·검증 · KVM · 에뮬레이터 부팅 · Allure 생성 · 아티팩트 업로드)이 먼저 통과해, 이후 실패는 테스트 환경 문제로 좁혀 진단할 수 있었다
  - 검증 방법: `gh run view --log-failed` + 아티팩트를 내려받아 실패 시점 `page_source.xml`의 `bounds` 확인
- **`docs/CI_GUIDE.md` 신설** — 트리거 표·동작 흐름·리포트 확인·로컬 vs CI 차이·스케줄 주의사항(기본 브랜치 한정, 60일 비활성화)·트러블슈팅 6종. `CI_CD_STRATEGY.md`(전략)와 역할 분리하고 상호 링크, README·CLAUDE.md 문서 표에 등재

### Fixed
- **어제 Vercel 제거 때 놓친 잔존 문구 정리** — 어제 스캔이 `vercel|upload|BLOB` 패턴이라 **한글 "업로드"** 표현을 놓쳤다
  - `README.md`: run_allure 설명·셸 스크립트 설명의 "웹 대시보드 업로드" → "로컬 이력 대시보드 갱신", mermaid 노드 라벨, Tech Stack의 `Next.js (대시보드)` 행 삭제
  - `docs/PYTEST_GUIDE.md`: Allure 수동 절차 설명 + pytest/셸 비교표의 "대시보드 업로드" 행

## 2026-08-25

### Fixed
- **코드 리뷰 확인 5건 중 4건 반영** (1건은 부작용이 커서 기각)
  - **logcat 첨부 누락 위험** — `pytest_runtest_makereport`가 아직 `"ios" not in str(item.fspath)` 부분문자열 판정을 쓰고 있어, 저장소가 `C:\work\ios-tools\...` 같은 경로에 있으면 **모든 Android 실패에서 logcat이 조용히 빠졌다**. `_is_ios_path()` 헬퍼를 신설해 `_resolve_platform`과 판정 기준을 통일(중복 로직도 제거). 케이스별 판정은 유지 — 혼합 실행에서 세션 단위 판정보다 정확
  - **`text_present` 진단 정보 소실** — 예외를 삼키면 리포트에 `AssertionError`만 남아 '무엇을 못 찾았는지'가 사라졌다 → 타임아웃 시 locator·기대 텍스트를 로그로 남김(첨부된 page_source와 대조 가능)
  - **`run-app.sh` 주석 과장 + 글롭 확장** — "공백/특수문자 대응" 주장은 `$TARGET`이 비인용이라 사실이 아니었다 → 주석을 실제 보장 범위로 정정(`--files` 다중 경로를 위한 의도적 단어 분할, 공백 미지원)하고 `set -f`로 글롭 확장만 차단
  - **`bootstrap.ps1` 부분 다운로드 고착** — Ctrl+C 중단은 outer catch를 타지 않아 잘린 `.apk`가 남고 다음 실행의 '이미 있음' 체크가 이를 수용했다 → `.part`로 받아 검증 통과 후에만 `.apk`로 승격(`Move-Item`)
  - **기각**: `text_present` 기본 타임아웃 15초 → `SHORT_TIMEOUT`(5초) 제안. `is_displayed()`류는 화면 전환 직후 **양성 단언**으로 쓰여, 콜드 부팅 에뮬(오늘 스모크 2:11)에서 5초는 flaky 위험이 있다. 15초 비용은 실패 경로에서만 발생하므로 안정성을 택함
  - 검증: `_is_ios_path` 14케이스 통과(Windows 백슬래시·`ios-tools` 상위 경로 포함) · `set -f` 글롭 차단 실측 · `.part`가 `-Filter *.apk`에 안 걸리고 승격 후 잡히는 것 확인 · **의도적 실패 테스트로 logcat 첨부 5종 + 진단 로그 확인** · **전체 회귀 17/17 (6:14)**

### Removed
- **외부(Vercel) 대시보드 업로드 기능 전면 제거** — 이 저장소는 공개용이라 테스트 결과를 외부로 올리지 않는다. 결과는 **로컬 전용**(`allure-reports/`)으로 유지
  - `tools/upload_to_dashboard.py` 삭제(Blob 첨부 업로드·용량 정리·AI 실패 분석 포함)
  - `tools/run_allure.py`: `--upload`/`--no-upload`/`--dashboard-url` 옵션 + 업로드 호출 블록 제거 (로컬 대시보드 갱신은 유지)
  - `.env.example`: `BLOB_READ_WRITE_TOKEN`·`DASHBOARD_API_URL` 삭제 → `EXECUTOR_NAME`(리포트 표시명)만 남김
  - `shell/run-app.sh`: 실행 요약의 Dashboard 항목을 외부 URL → 로컬 경로로 교체
  - 문서 정리: `CLAUDE.md`(구조 트리·도구 설명 #3·#4·환경변수 표) · `README.md`(주요 특징·구조·mermaid·대시보드 섹션·환경변수·참고 링크) · `docs/ALLURE_REPORT_GUIDE.md` §6(웹 대시보드 → 로컬 이력 대시보드) · `docs/SETUP_GUIDE.md`(.env 선택 항목·SSL 트러블슈팅 행) · `docs/PYTEST_GUIDE.md` · `GIT_RULES.md`(시크릿 예시를 중립 토큰으로) · `docs/MCP_단계별_실행계획.md`
  - `docs/CODE_REVIEW_2026-06-29.md` R-55(업로드 정리 로직 버그)는 **해당 없음**으로 표시 — 대상 파일 자체가 없어짐
  - 부수 효과: 회사망에서 매 실행마다 나던 `SSL: CERTIFICATE_VERIFY_FAILED` 업로드 실패가 사라짐(관련 `[Unreleased]` 할일도 삭제)
  - 검증: 잔존 활성 참조 0건(남은 5건은 과거 이력·완료된 리뷰 항목·MCP 서버 예시) · `run_allure.py --help`에 업로드 옵션 없음 · py_compile·`bash -n` OK · **온디바이스 스모크 2 passed + 리포트 생성 + 로컬 대시보드 3건 정상 갱신**(업로드 시도·SSL 오류 없음)

---

## 2026-08-24

### Changed
- **환경 세팅 가이드 통합** — `README_CLONE.md` + `MAC_SETUP_GUIDE.md` + `IOS_SETUP_GUIDE.md` → 단일 **`docs/SETUP_GUIDE.md`**
  - 구조: 시나리오별 읽기 순서 → 공통 클론 → Windows(bootstrap) → macOS → iOS 추가 → .env·앱 배치 → 검증·첫 실행 → 트러블슈팅 통합(공통/mac/iOS) → OS·플랫폼 차이표
  - `MAC_SETUP_GUIDE.md`를 `git mv`로 이어받아 작성(재구성 폭이 커서 git은 rename이 아닌 삭제+추가로 기록 — 3개 문서 원문은 커밋 이력에서 조회 가능), 참조 6곳 갱신(CLAUDE.md·README 문서표·IOS_TEST_GUIDE·MCP_SETUP_GUIDE)
  - 낡은 정보 정정: README_CLONE의 옛 GitLab 클론 URL → GitHub `appium_saucelabs`, "iOS 가이드 작성 예정" 등
- **변경 이력 통합** — `change_notes.md` + `Todo.md` → 단일 `CHANGELOG.md`(Keep a Changelog 형식, 본 파일)로 개편 (커밋 `bf59295`)
  - `change_notes.md` → `CHANGELOG.md` git rename(무손실), Todo 미완료 항목은 `[Unreleased]`로 큐레이션, 원본은 `archive/TODO-2026.md` 동결 보존
  - 참조 갱신 16곳: `CLAUDE.md` 워크플로우 / `GIT_RULES.md` §12 / `docs/CODE_REVIEW_2026-06-29.md` / mcp-scenario 스킬
  - 선행 작업: origin/main(7/13 레포명 변경 커밋)을 `fix/code-review-medium`에 병합해 이력 유실 방지 (커밋 `8dc6cd5`)

### Added
- **conftest 사전점검(preflight) + fail-fast 안전장치** — 1차 회귀 사고(잔존 Appium·adb 불일치로 17건 × 20초 연쇄 에러) 재발 방지
  - `_preflight_check(platform)`: 첫 드라이버 생성 전 **플랫폼별 1회** — Appium `/status` 응답 + (로컬 서버·Android일 때) `adb devices` 확인, 이상 시 `pytest.exit`로 원인·처방과 함께 즉시 중단
  - 오탐 방지 설계: 확실한 이상(서버 무응답·디바이스 0대·adb 비-0 종료·프록시 가로채기)만 중단 사유로 삼고, 불확실한 경우(로컬 adb 없음·원격 `APPIUM_HOST`)는 경고만 남기고 진행 — 점검이 정상 환경을 막지 않게
  - fail-fast: 세션 생성이 `Could not find a connected ...`로 실패하면 환경 문제로 판정, 나머지 테스트를 돌리지 않고 SETUP_GUIDE §7.1 처방과 함께 전체 중단
  - 검증(온디바이스 시나리오 6종): Appium 다운 → 2.7초 중단 / 디바이스 없음 → 0.7초 중단 / 프록시 오설정 → 0.9초 중단 / 프록시+`no_proxy` 정상 → 2 passed / 평시 → 2 passed / **전체 회귀 17/17 (5:19)** — 기존엔 앞 세 상황이 모두 5~18초씩 × 전 케이스 연쇄 실패
- **`bootstrap.ps1` [5/6] 단계 신설: `.env` 자동 생성 + APK 자동 다운로드** — 공개 테스트용 앱이라 릴리스(2.2.0 고정, capabilities 검증 버전)에서 자동 수령, `apps/`가 gitignore라 클론에 안 오는 공백 해소
  - README 서두에 "대상 앱: SauceLabs My Demo App" 소개 섹션 신설 (배포·테스트 계정·APK 입수·iOS 링크)
  - 코드 리뷰 3건 반영: ① 다운로드 실패 시 부분 파일 삭제(다음 실행 오인 방지) ② README "1~4단계" 과장 → `.env` 복사 추가 후 "2~5단계"로 정정 ③ PS 5.1 진행바 지연 방지(`$ProgressPreference` 스코프 처리)
  - 검증: 스킵 경로(APK 존재 시) · 다운로드 경로(SHA256 원본 일치) · 실패 경로(404 시뮬, 부분 파일 잔존 없음) · `.env` 생성 확인
- **회사 Windows 환경 시운전** — 클론 후 첫 실행 환경 구축 + 스모크 검증 (repo 변경 없음, 로컬 환경 기록)
  - `shell/bootstrap.ps1` 실행: venv 패키지(Appium-Python-Client 5.2.4·pytest 9.0.2 등 35개) + npm 1065개(로컬 Appium 3.1.2) + uiautomator2 6.9.3 드라이버 + Allure 2.43.0
  - 네이티브 APK `mda-2.2.0-25.apk` 배치(gh release 2.2.0). 구 RN APK·`mda-androidTest` APK는 `apps/archive/`로 이동 — capabilities의 "이름순 마지막 파일" 자동 선택이 androidTest APK를 잘못 집는 함정 방지
  - 검증: capabilities가 네이티브 APK/패키지 정확히 해석 → Pixel_6 에뮬 + Appium 서버(127.0.0.1:4723) 기동 → `smoke_test.py` **2 passed** (28s)
  - 트러블슈팅: Appium 서버를 `| head`로 파이프해 백그라운드 기동하면 로그 초과 시 SIGPIPE로 서버가 죽음 → 파이프 없이 기동해야 함
- **Android 온디바이스 회귀 통과 — 17/17 passed (4:49)** · Medium 9건(R-03~R-14) 검증 완료
  - Pixel_6 에뮬 + Appium 3.1.2 + `mda-2.2.0-25.apk`. 스모크~체크아웃 E2E~WebView 전 케이스 통과 (`allure-reports/20260824_112335`)
  - 남은 병합 조건: iOS 온디바이스 회귀(집 macOS) — R-09·R-10이 iOS POM도 수정함
  - 1차 시도는 17건 전부 세션 생성 에러 — 원인: task kill로 죽다 만 구 Appium 프로세스가 adb 디바이스를 못 봄 → Appium·adb 재기동으로 해결

### Fixed
- **코드 리뷰(2차) 확인 5건 반영** — 새 안전장치·도구가 만들 수 있는 오탐·오진 정리
  - preflight 프록시 판정에 **포트 포함 host:port**를 넘김: `NO_PROXY=127.0.0.1:4723`처럼 포트가 붙은 항목은 호스트만 넘기면 포트 불일치로 스킵돼 정상 환경을 막았다 (A/B 실측: 호스트만 `False` → host:port `True`)
  - `_resolve_platform`을 **`tests/ios` 경로에 고정**: 임의 세그먼트 매칭은 인자 없는 `pytest`(rootdir가 인자로 들어옴)에서 저장소가 `~/work/ios/...` 아래 있으면 Android 전체를 XCUITest로 몰아버린다
  - `bootstrap.ps1` APK **내용 검증**(ZIP 매직 `PK` + 최소 크기): 프록시·캡티브 포털이 200으로 HTML을 주면 그게 `.apk`로 저장되고 다음 실행의 '이미 있음' 체크가 고착시킨다 (A/B 실측: HTML 위장 파일 거부 / 실제 APK 통과)
  - `run_allure._resolve_allure_cmd()`가 못 찾을 때 `"allure"`를 반환해 `FileNotFoundError` 트레이스백으로 죽고 **pytest 종료코드까지 잃던 것** → `None` 반환 + 설치 안내 후 종료코드 보존
  - `serve.py` 종료 시 `server_close()` 누락(리스닝 소켓 반납) 보완
  - 검증: 로직 15종 전부 통과(프록시 5케이스·A/B·플랫폼 7케이스·allure 2분기) · PowerShell 파서 OK · `bash -n` OK · 대시보드 재기동 후 4엔드포인트 200 · **온디바이스 스모크 2 passed**
  - 참고: 1차 실행에서 프록시 3케이스가 실패로 나왔는데 원인은 **검증 스크립트 버그**였다 — Windows `os.environ`은 대소문자를 구분하지 않아 `pop("no_proxy")`가 방금 설정한 `NO_PROXY`를 지웠다. 코드가 아니라 테스트를 고쳐야 하는 사례
- **`tools/serve.py` 로컬 대시보드 서버 2건 수정** — 대시보드를 실제로 띄워보다 발견
  - **단일 스레드 → 요청당 스레드**(`TCPServer` → `ThreadingHTTPServer`): 브라우저가 미리 열어두는 유휴 연결(preconnect) 하나가 요청 루프를 붙잡아 서버 전체가 멈췄다. Allure 리포트는 에셋 요청이 수십 개라 특히 잘 재현 — 실측: 수정 전 요청 3연속 타임아웃(5s·15s) + `ConnectionAbortedError` 트레이스백 다발 → 수정 후 유휴 소켓 3개를 열어둔 채 동시 요청 8건 **전부 200 (각 0.13초)**, 예외 0건. 죽은 연결이 스레드를 점유하지 않도록 핸들러 `timeout=30`도 추가
  - **비대화형 stdin에서 즉시 자멸하던 문제**: 종료 대기용 `input()`이 파이프·CI·에이전트 실행에서 곧바로 EOF가 되어 서버가 스스로 내려갔다(서버를 띄우려면 `tail -f /dev/null |` 같은 우회가 필요했음) → EOF를 'Enter를 받을 수 없는 환경' 신호로 해석해 Ctrl+C까지 계속 서빙. `isatty()`는 Git Bash에서 True로 나와 신뢰할 수 없어 EOF 기반으로 판정
- **코드 리뷰(안전장치 diff) 확인 7건 반영** — preflight가 오히려 오진·오탐을 만드는 경로를 정리
  - `_PREFLIGHT_DONE`을 단일 bool → **플랫폼 집합**으로: 혼합 실행(iOS 먼저)에서 Android adb 점검이 통째로 스킵돼 사고 방지 장치가 무력화되던 문제
  - adb `returncode` 미검사 → 버전 불일치·데몬 오류를 "디바이스 없음"으로 오진하던 것을 stderr 원문과 함께 정확히 보고
  - adb 미설치 시 전체 중단 → **경고 후 진행**(Appium 서버는 자기 PATH의 adb를 씀), 원격 `APPIUM_HOST`면 로컬 adb 점검 자체를 스킵
  - **프록시 진단** — 리뷰는 "selenium은 프록시를 안 타니 우회만 하면 된다"고 했으나 **실측으로 반박**: selenium(urllib3)도 `HTTP_PROXY`를 따라 localhost 요청이 프록시로 샌다(17.8초 연쇄 실패 재현). 단순 우회는 preflight를 거짓 OK로 만들어 목적을 훼손하므로, 프록시 우회 프로브로 서버 생존을 확인한 뒤 **`no_proxy` 누락을 별도 진단**(0.9초 중단 + `NO_PROXY` 처방)하도록 설계
  - `_resolve_platform` 부분문자열 `"ios"` → **경로 세그먼트 매칭**: `sessions/…-ios-flow/`·`C:/work/ios-projects/…` 같은 경로에서 Android 실행이 조용히 XCUITest로 새는 잠재 버그 제거
  - `run-app.sh` 드라이버 점검: `... | grep -q`가 파이프를 조기 종료시켜 상위 명령이 SIGPIPE(141) → `pipefail`로 설치된 드라이버가 "Not Installed"로 오판. 목록을 변수로 캡처 후 검사로 교체 (실측: 구 방식 141 → 신 방식 0)
  - `archive/TODO-2026.md`의 죽은 포인터(개편으로 사라진 `GIT_RULES.md` "Todo.md 작업 추적" 섹션) — 원문 보존을 위해 본문 대신 헤더에 대체 섹션 명시
  - 검증: 로직 단위 6종(플랫폼별 점검·adb 미설치·adb 오류·디바이스 0대·원격 스킵·세그먼트 매칭) 전부 통과 · `bash -n` OK · 온디바이스 프록시 3케이스 · 전체 회귀 **17/17 passed (5:19, `allure-reports/20260824_140544`)**
- **코드 리뷰(회귀 후 diff 리뷰) 확인 2건 반영** — 둘 다 R-04 스모크 재작성분에서 발견, 브랜치 자체 원칙(bool 계약·POM 캡슐화) 위반
  - `product_count()` 빈 목록 시 `TimeoutException`(broken) → `0` 반환(fail)으로 — Android `ProductsPage` + iOS `CatalogPage` 동일 적용 (iOS는 예정된 iOS 회귀에서 온디바이스 검증)
  - 스모크가 private locator(`_MENU_ICON`/`_CART_ICON`)에 직접 접근 → `BasePage.is_menu_visible()`/`is_cart_visible()` 헬퍼 신설 후 위임
  - 검증: py_compile 4개 통과 + 스모크 온디바이스 재실행 **2 passed** (16s)
- **`tools/run_allure.py` Windows에서 Allure 실행 불가 수정** — bare `"allure"` subprocess 호출은 Windows CreateProcess가 `.cmd`(scoop shim·npm 로컬 설치본)를 못 찾아 `FileNotFoundError`로 크래시(macOS에선 정상이라 잠재해 있던 버그)
  - `_resolve_allure_cmd()` 추가: `shutil.which` → 로컬 `node_modules/.bin`(Windows는 `allure.cmd`) 순 탐색, `generate`·`open` 두 호출부 교체
  - 검증: 실제 회귀 실행에서 리포트 생성 성공 (scoop shim `allure.CMD` 해석 확인)
- (미해결·환경) Vercel 대시보드 업로드가 회사망에서 `SSL: CERTIFICATE_VERIFY_FAILED`(사내 프록시 CA 인증서의 key usage 확장 누락 + Python 3.14 강화 검증 추정) — 메타데이터 업로드만 실패, 로컬 리포트·대시보드는 정상

---

## 2026-07-13

### 저장소 이름 변경: `sauceLabs_appium` → `appium_saucelabs`

- `gh repo rename appium_saucelabs`로 GitHub 저장소명 변경 (로컬 origin URL 자동 갱신, fetch 정상 확인)
- 현재 상태 문서의 옛 이름 참조 일괄 정정: `README.md`(클론 URL·구조 트리), `docs/IOS_SETUP_GUIDE.md`, `docs/MAC_SETUP_GUIDE.md`, `docs/MCP_SETUP_GUIDE.md`
- `change_notes.md`·`Todo.md`의 과거 이력 속 옛 이름은 당시 기록이라 유지
- 옛 URL(`sphh12/sauceLabs_appium`)은 GitHub 리다이렉트로 계속 동작

---

## 2026-07-01

### 코드 리뷰 개선 — 🟠 권장(Medium) 9/10 구현 (R-11 보류) · 브랜치 `fix/code-review-medium`

`docs/CODE_REVIEW_2026-06-29.md` §4의 Medium 10건 중 9건 구현.

**bool 계약 (R-03·R-08)**
- `BasePage.text_present() -> bool` 헬퍼 추가(`TimeoutException`→`False`) → `products/cart/about.is_displayed`·`cart.is_empty`·`checkout.is_order_complete` 통일. 음성 케이스가 broken이 아닌 fail로 분류.

**conftest 드라이버 (R-05·R-06·R-07)**
- `_resolve_platform(config)` 단일 헬퍼로 pytest_configure·platform 픽스처 통일(경로 기반 자동 감지 + android 폴백) → `--platform` 미지정 시 ValueError 제거
- `_create_driver`/`_teardown_driver` 헬퍼로 세 픽스처 단일화, `try/finally`로 quit 보장 + 생성 실패 시 즉시 정리

**기타**
- R-04: `smoke_test.py`를 ProductsPage POM 기반으로 재작성
- R-09: Android/iOS `open_first_product`을 `self.click(PRODUCT_IMAGES)`로 (clickable 대기 + stale 재시도)
- R-10: iOS About 버전 단언을 `\d+\.\d+` 패턴으로(동어반복 제거)
- R-14: `run_allure` 트렌드 history — 타임스탬프 폴더만 필터(LATEST/dashboard 오선택 제거)
- R-12: `run-app.sh` eval 제거(배열화) + `set -o pipefail`

**검증**: py_compile 전체 통과 · `run-app.sh` `bash -n` OK · `pytest --collect-only` 29 tests. 온디바이스 회귀는 미실행(다음 단계).
**보류**: R-11(iOS 카트 수량 테스트) — iOS 수량/합계 accessibility id 확보(`ui_dump_ios.py`) 선행 필요.

---

## 2026-06-30

### README 검토·보강 + 실행 구조 다이어그램 추가

전체 코드와 대조해 README 미비점을 수정하고 실행 흐름 다이어그램을 추가.

- **구조 트리 보강**: `config/test_data.py`, `utils/flows.py`·`flows_ios.py` 누락분 반영
- **문서 표**: `docs/APP_STRUCTURE.md`(테스트 범위 인벤토리) 링크 추가
- **실행 구조 섹션 신설**: Mermaid 2종 — ① 실행 파이프라인(진입점 → `run_allure.py` → pytest → conftest/driver → POM → Appium → 리포트 → 대시보드) ② 코드 레이어(테스트 → flows → POM → BasePage → Driver → 앱)
- **주요 특징 / 테스트 커버리지 섹션 신설**: 강점 요약 + 기능영역별 Android/iOS 커버리지 표(iOS 결제 E2E·WebView 2건 키보드 이슈 skip 명시)
- 검증: requirements/package 버전 README 일치, mermaid 2블록·코드펜스 짝, 참조 파일 실재 확인

---

## 2026-06-29

### 전체 코드 리뷰 + Public 레포 보안 하드닝 3건 (A1~A3)

원격 최신(`dc6208f`)으로 fast-forward pull 후, 전 코드(테스트/POM/conftest/도구/설정 10개 영역) 다차원 병렬 리뷰 + 발견 항목별 적대적 검증 수행 → 65개 개선항목 도출. 치명적 false-pass 버그·하드코딩 시크릿 없음 확인(테스트 계정/카드는 공개 데모값). 이번 커밋에서는 우선순위 최상인 보안 3건만 반영, **전체 65건은 `docs/CODE_REVIEW_2026-06-29.md`에 체크리스트로 정리**(개선 작업 추적은 `Todo.md` "코드 리뷰 개선 작업" 섹션).

**A1 — `.gitignore`: bare `.env` 미차단 문제 수정**
- 기존엔 `.env.local`/`.env.*.local`만 무시하고 `.env` 자체는 추적 가능 상태였음 (옛 private 레포 시절 주석 잔재)
- `.env` + `.env.*` 추가, `!.env.example` 예외 유지 → 토큰을 담은 `.env` 실수 커밋 차단
- 검증: `git check-ignore`로 `.env` 무시 / `.env.example` 추적 유지 확인. 현재 `.env`는 추적/히스토리 모두 없음(사고 전)

**A2 — `tools/serve.py`: 로컬 전용 바인딩**
- `TCPServer(("", port))` → `("127.0.0.1", port)`로 변경. `0.0.0.0`(전 인터페이스) + 프로젝트 루트 서빙 조합이라 같은 LAN에서 `/.env` 다운로드 가능했던 것을 차단

**A3 — `conftest.py`: 외부 대시보드 업로드 정보 익명화**
- executor.json `name`: `getpass.getuser()`(OS 사용자명) → `EXECUTOR_NAME` 환경변수(미설정 시 `"local"`)
- environment.properties `app`: 절대경로(`C:\Users\<user>\...`) → 파일명만(`os`/`Path` 기존 import 활용)
- gitMessage는 이미 공개 레포 히스토리에 있는 정보라 유지

**검증**
- conftest.py / serve.py `py_compile` 통과
- 커밋 diff 민감정보 스캔 clean (토큰/키/이메일/전화번호 0건)
- 부수 확인: 레포명이 `appium-saucelabs` → `sauceLabs_appium`으로 변경됨(origin은 리다이렉트로 동작), 공개 상태 PUBLIC 확정

---

## 2026-06-21

### 코드 리뷰 개선 14건 구현 (P1 3 · P2 6 · P3 5) + 온디바이스 회귀 검증

다차원 코드 리뷰(서브에이전트 다수: 발견 → 적대적 검증 → 종합)로 도출한 14개 개선항목을 우선순위별로 구현하고, 양 플랫폼 실기기로 회귀 검증.

**P1 — 신뢰성·즉시 위험 (3)**
- `BasePage._retry_on_stale()` 추가 → `click`/`input_text`/`get_text`를 감싸 `StaleElementReferenceException` 시 재탐색·재시도 (RecyclerView 재렌더·카트 수량변경 간헐 실패 차단)
- `tools/update_dashboard.py` 인라인 JS 문자열 raw화 → `\/`·`\d` 등 `SyntaxWarning`(향후 SyntaxError로 대시보드 생성 중단 위험) 제거 + 미사용 함수/import 정리
- pytest 설정 단일화: `pyproject.toml`의 `[tool.pytest.ini_options]` 삭제 → `pytest.ini` 단일 출처 ("ignoring pytest config" 경고 해소)

**P2 — 권장 (6, #9는 일부 보류)**
- 합계 assert 강화: 체크아웃 `합계 == round(상품가합 + 5.99, 2)`, 카트 수량2배 `t2 == round(t1*2, 2)` 검증으로 가격 회귀 차단
- iOS `is_color_selected()` 추가 — ⚠️온디바이스 검증 중 `{color}ColorSelected` 이름 추측이 틀림을 발견(실제는 이름이 항상 `...ColorUnSelected`, **`selected=true` 속성**으로 선택 표현) → 속성 기반으로 정정
- iOS 인덱스 의존 제거: 체크아웃 `FIELD_*` 의미 상수 + `EXPECTED_FIELD_COUNT` 가드, `rate_product(stars)` class-chain + `len` 가드 파라미터화
- 리포트 후처리 단일화: `run-app.sh` STEP4 제거 → `run_allure.py` 위임(macOS BSD `sed` 버그 원천 제거)
- `config/test_data.py` 신설: 계정·`SHIPPING`·`PAYMENT` 중앙관리 (Android `bod@`/iOS `bob@`는 앱 실제값이라 분리 유지)
- (보류) driver fixture 3중복 제거: `is_android()` 헬퍼만 추가, `_build_driver` 공통화는 리스크 대비 효익 낮아 별도 작업으로

**P3 — 선택 (5)**
- 타임아웃 상수화(`SHORT_TIMEOUT`) + `is_invisible()` 헬퍼 + `hide_keyboard` 예외 안전화
- 마커 전략: `--strict-markers` + `smoke`/`regression`/`e2e` 부착 + `PYTEST_GUIDE` 실행 레시피
- `utils/flows_ios.py` 신설(iOS 네비 중복 제거) + `flows.login_as_valid_user`
- 문서 드리프트 정정(CODING_GUIDELINES/IOS_TEST_GUIDE/CLAUDE.md/README/UI_DUMP_GUIDE)
- `.env.example` 동기화(`IOS_UDID`·`ANDROID_HOME`)

**온디바이스 회귀 결과**: Android 17 passed (2:56) / iOS 10 passed·2 skip (2:40, `test_select_color` 정정 후 통과). checkout_e2e·webview iOS 2건은 키보드 환경이슈로 의도된 skip 유지.

---

## 2026-06-20

### iOS 자동화 (탭바 POM + 10 테스트 통과, 키보드 환경이슈 2건 skip)

Android와 동일 방식(탐색→POM→테스트→온디바이스 검증)으로 iOS 구축. 서브에이전트로 테스트 병렬 작성.

**환경 셋업**
- iOS 26.5 플랫폼 설치(`xcodebuild -downloadPlatform iOS`, 8.5GB) — Xcode 26.5에 iOS SDK 미설치였음(WDA 빌드 실패 → 설치 후 해결)
- 시뮬 iPhone 17 (iOS 26.5). 실행 env: `IOS_UDID`/`IOS_DEVICE_NAME="iPhone 17 26.5"`/`IOS_PLATFORM_VERSION=26.5` (`capabilities.py`가 `IOS_UDID` 지원 추가)

**구조 차이 (Android 대비, 탐색으로 확정)**
- 네비: **하단 탭바**(`Catalog/Cart/More-tab-item`) — 드로어 아님. 드로어 기능은 More 탭(`*-menu-item`).
- locator: 서술형 accessibility id `name` (`AddToCart`/`ProceedToCheckout`/`Product Image`/`To Payment` 등)
- 로그인: 저장계정 **버튼** 탭(타이핑 불필요). 계정 bob/alice/john/visual — **잠긴 계정 없음**(alice도 정상)
- **정렬 기능 없음**. 검증=네이티브 Alert `Validation Error!`. 리셋=2단 Alert(`RESET APP`→`App State has been reset.` OK). 별점=리뷰 Alert(Android과 동일).

**POM** (`pages/ios/`): `base_ios_page`(탭바) + catalog/product_detail/cart/login/more/about/checkout (8개). 명시적 대기는 `BasePage` 재사용.
**테스트** (`tests/ios/`): **10 통과** — 카탈로그·상세(수량/색상/별점)·카트(삭제·빈)·로그인·로그아웃·리셋·체크아웃검증·About. **2 skip**.

**키보드 환경 블로커** (Xcode 26.5 + 한글 macOS)
- 시뮬 한글 소프트 키보드가 억제·해제 안 됨(캡·제스처·오프라인 plist·Simulator.app 등 13종 시도 실패) → 버튼 가림 + 입력 오염(`ㅍ`)
- 타이핑 필요 2건(**체크아웃 완주 E2E**, **WebView URL**)만 `@pytest.mark.skip("iOS soft keyboard env blocker")`. 나머지(버튼 기반)는 전부 자동화·검증 완료.

### 기능 인벤토리 + POM 자동화 (해피패스 E2E + Tier 1·2, 17 케이스 통과)

`APPIUM_MCP_WORKPLAN` 기반: 전체 기능 파악 → 기능리스트 → 자동화 스크립트(일부) 구축.

**기능 인벤토리 (`docs/APP_STRUCTURE.md`)**
- 처음엔 화면 수준 20개로 빈약 → 사용자 지적 후 **APK 리소스 전수 추출**(aapt: 문자열 186 / id 681 / 액티비티 4)로 확정
- 19개 기능영역 / 60+ 테스트 동작 + 화면별 locator(content-desc·id) + 상태범례(✅검증/🟡확정/⬜권한의존)

**POM 구조 (명시적 대기 100%, `time.sleep` 0)**
- `base_page.py` 보강: explicit-wait 헬퍼(find/click/wait_until_invisible/wait_for_text) + 공통 헤더(메뉴/카트/배지)
- `conftest.py` implicit_wait 10→0 (explicit 혼용 방지)
- 페이지 8개: login/products/product_detail/cart/checkout/menu/webview/about + `utils/flows.py`(네비 헬퍼)

**테스트 17 케이스 전부 통과 (Allure)**
- 스모크 2 + 해피패스 E2E 1 (로그인→결제완료)
- Tier 1 (10): 정렬 asc/desc · 상품상세 수량/색상/별점 · 카트 수량/삭제·빈상태 · 로그인 빈값/잠긴계정 · 주소 필드검증
- Tier 2 (4): WebView URL검증 · About 버전 · 로그아웃(확인 다이얼로그) · 앱 리셋(카트 초기화)

**실전 디버깅 (문서 반영)**
- 체크아웃 3버튼이 모두 `id/paymentBtn` → 화면별 content-desc로 구분. 캡처 요약이 desc를 30자 절단해 `Review Order` 값을 추측 오류 → 저장 page source XML 원문으로 교정
- 입력란 `showing-hint="true"` = placeholder(빈값) → 필수 미입력 시 검증 에러
- 별점 탭 = 즉시 리뷰 제출("Thank you…") / 로그아웃 = AlertDialog(`android:id/button1`)

**방법론**: 온디바이스 탐색·검증은 에뮬레이터 1대라 직렬 → Tier1·2 화면 상태를 1회 캡처(그라운드트루스)로 front-load 후 POM·테스트 작성 → 직렬 검증

---

### 이전 프로젝트 → SMDA 잔존 흔적 전면 정리 (문서·스킬·도구·스크립트)

이전 마이그레이션(2026-05)에서 코드(capabilities.py/.env/conftest fixture)는 SMDA로 정리됐으나, 문서·예시·일부 도구에 이전 프로젝트의 다중환경·삭제된 코드 참조가 남아 단일환경 SMDA 기준으로 일괄 정리.

**결정 (사용자 합의)**
- 다중환경(APP_ENV 분기) → 완전 제거, 단일 환경 통일
- 예시 테스트명 → `<your_test>.py` 플레이스홀더 (실행형은 `tests/android` 디렉터리)
- README.md → 현재 상태로 전면 재작성

**문서 (13개)**
- `README.md` 전면 재작성 (SMDA 단일환경, 실제 파일 구조, 올바른 클론 URL `sauceLabs_appium`)
- docs 11개: PYTEST/ALLURE/CODING_GUIDELINES/MCP_개념/UI_DUMP/MCP_RECORD/MAC_SETUP/MCP_SETUP/MCP_단계별/IOS_SETUP/IOS_TEST
  - 다중환경 섹션·환경별 계정·이전 프로젝트 패키지·삭제 파일 참조·깨진 PDF 링크 제거
  - MAC_SETUP: GitLab 듀얼리모트 → 단일 origin, 없는 `run-stg.sh` → `run-aos.sh`
  - IOS_TEST: Contacts 앱 예시를 'iOS 학습 예시(My Demo App에 적용)'로 재구성

**스킬 (`.claude/skills/mcp-scenario` 6개)**
- SKILL/triggers/action_format/pattern_registration 단일환경화, 이전 프로젝트 셀렉터 → SMDA(`com.saucelabs.mydemoapp.rn`)
- `change_language.md` → `add_to_cart.md`로 교체 (SMDA 대표 시나리오)
- `login_flow_template.md` SMDA 셀렉터/계정(`TEST_USER`/`TEST_PW`)으로 재작성

**코드/스크립트 (단일환경 리팩터링)**
- `tools/mcp/session_recorder.py` — **깨진 import 수정**: capabilities.py에서 제거된 `_find_apk_in_folder`/`get_env_config`를 import해 실행 즉시 ImportError 상태였음 → 단일환경으로 재작성
- `tools/mcp/generate_capabilities.py` — 다중환경 엔진 제거, `apps/android` + SMDA 패키지로 단일화
- `tools/mcp/codegen.py` — 생성 코드의 `get_env_config`(삭제됨)·`skip_initial_screens` 마커·`utils.language` 패턴 제거
- `shell/run-app.sh` — 환경 선택 플래그·`apk/` 경로 제거(`apps/android`), 기본 타깃 `tests/android`
- `run-aos.sh`/`run-ios.sh` 헤더, `package.json`/`run_allure.py` 예시, `pytest.ini` 죽은 마커(`skip_initial_screens`), `conftest.py` 주석, `tools/mcp/README.md`, `.gitattributes`/`GIT_RULES.md`의 `apk/`→`apps/`

**검증**
- `python -m py_compile` (변경 .py 6개) ✅ / `bash -n` (셸 3개) ✅
- 잔여 이전 프로젝트·다중환경 grep 0건 (의도적 보존: 메타파일/`GIT_RULES.md` changelog 기록, IOS_TEST의 iOS Contacts 학습 예시)

### 대상 앱 네이티브 Android 전환 + APK 배치

사용자가 RN 앱이 아닌 **네이티브 Android 앱**(`saucelabs/my-demo-app-android`)을 지정 → 받은 앱에 맞춰 프로젝트 전체를 네이티브로 전환.

- `apps/android/mda-2.2.0-25.apk` 다운로드 배치 (릴리스 2.2.0 / versionCode 25, `.gitignore`로 커밋 제외)
- 패키지 `com.saucelabs.mydemoapp.rn` → **`com.saucelabs.mydemoapp.android`** 전면 교체
  - 액티비티 → `com.saucelabs.mydemoapp.android.view.activities.SplashActivity`
  - iOS 번들 → `com.saucelabs.mydemo.app.ios` (실제 `.app` Info.plist로 검증 — 초기 가정값 `mydemoapp.ios`는 오류였음)
  - iOS 시뮬레이터 빌드 `apps/ios/SauceLabs-Demo-App.Simulator.zip`(릴리스 2.2.2, `my-demo-app-ios`) 배치 + README에 iOS 다운로드/참고 링크 추가
  - "React Native"/"(RN)" 설명 → "네이티브 Android"
- 대상 파일: `config/capabilities.py`, `tools/mcp/generate_capabilities.py`, `CLAUDE.md`, `README.md`, docs(UI_DUMP/ALLURE/MCP_SETUP/MAC_SETUP), 스킬(SKILL/action_format/add_to_cart)
- 검증: capabilities.py 패키지/액티비티 = APK `aapt badging` 실측 **일치** ✅ / `mydemoapp.rn`·`my-demo-app-rn`·"React Native" grep **0건** ✅

### 환경 세팅 (venv + npm + 검증)

- venv 생성 + `pip install -r requirements.txt` (Appium-Python-Client 5.2.4, selenium 4.39.0, pytest 9.0.2 등 — Python 3.14 휠 정상)
- `npm install` → Appium **3.5.2** + 드라이버(uiautomator2@6.9.3, xcuitest@10.43.1) 설치
- 검증: `capabilities` import OK(앱경로/패키지/액티비티/번들 실측 일치), `session_recorder.py active` 정상(복구 확인), `pytest --collect-only` conftest 정상 로드(테스트 0개 — 미작성)
- 참고: `pyproject.toml`/`pytest.ini` 설정 중복 경고(무해, pytest.ini 우선), npm 취약점 18건(Appium 의존성 트리)

### 첫 스모크 테스트 작성 + 통과 (Step 9 착수)

에뮬레이터(Pixel_8) + Appium 3.5.2로 앱을 실제 구동해 전 체인 검증.

- UI Dump로 첫 화면 locator 확보 (스플래시 `splashIV` → 카탈로그)
- `tests/android/smoke_test.py` 작성 (2 케이스):
  - `test_app_launches` — `current_package == com.saucelabs.mydemoapp.android`
  - `test_catalog_screen_loads` — 'Products' 헤더 + 상품 목록 + 메뉴/장바구니 노출
- 결과: **2 passed** (pytest 직접 + `run_allure.py` 양쪽), Allure 리포트 생성 OK (`allure-reports/20260620_*`)
- 확인된 첫 화면 핵심 locator (`com.saucelabs.mydemoapp.android:id/`): `productTV`(Products 헤더), `titleTV`(상품명), `priceTV`(가격), `menuIV`/"View menu", `cartRL`/"View cart", `sortIV`, `productRV`(상품 목록)
- 참고: `tools/update_dashboard.py`의 JS-in-string `\/` SyntaxWarning(무해, 기존)

---

## 2026-05-15

### 누적 변경사항 push (옵션 A 결정 후)

**결정: CLAUDE.md / .claude/ 그대로 공개 유지 (옵션 A)**
- `.claude/skills/mcp-scenario/`는 이미 트래킹 중 → 별도 작업 없이 그대로 공개
- 포트폴리오 차원에서 Claude 작업 워크플로우까지 노출하는 방향 채택

**push 대상 (어제 누적분)**
- `apk/` → `apps/` 폴더명 변경 (Android/iOS 통합)
- `.gitignore` 정리 (`*.apk+` 제거, `apps/`, `*.ipa` 추가)
- `config/capabilities.py` 경로 수정 (3곳)
- `CLAUDE.md` 경로 수정 (3곳)
- `change_notes.md`, `Todo.md` 메타파일 갱신

---

## 2026-05-14

### Step 6~7: GitHub 레포 생성 + SauceLabs 앱 파일 배치 + 폴더명 정리

**Step 6: Git 초기화 + GitHub 원격 연결**
- `git init` + `git branch -M main`
- GitHub에 `appium-saucelabs` 레포 생성 (Public)
- `git remote add origin` + 첫 커밋 + 첫 push 완료

**Step 7: SauceLabs 앱 파일 배치 + 폴더명 변경**
- 폴더명 `apk/` → `apps/`로 변경 (Android/iOS 통합 의미)
- SauceLabs My Demo App 파일 배치
  - `apps/android/Android-MyDemoAppRN.1.3.0.build-244.apk`
  - `apps/ios/iOS-Real-Device-MyRNDemoApp.1.3.0-162.ipa`
  - `apps/ios/iOS-Simulator-MyRNDemoApp.1.3.0-162.zip`
- 코드/문서 경로 수정
  - `config/capabilities.py`: `apk` → `apps` (3곳)
  - `CLAUDE.md`: `apk/` → `apps/` (3곳)
- `.gitignore` 정리
  - 잘못된 패턴 `*.apk+` 제거
  - Public 정책으로 `apps/`, `*.apk`, `*.ipa` 추가
  - SauceLabs 앱 자산은 미러링 제외

### 미해결 (내일 결정 + 진행 예정)
- CLAUDE.md / .claude/ 공개 여부 결정 (옵션 A 추천: 그대로 공개)
- 결정 후 누적 변경사항 push

### 이전 프로젝트 의존성 제거 + 프로젝트 메타파일 정리 (Step 4~5)

**Step 4: 코드 정리 (이전 프로젝트 의존성 제거)**
- `conftest.py` 정리
  - 깨진 import 제거: `from utils.initial_screens import handle_initial_screens`
  - `driver` / `android_driver` fixture에서 `handle_initial_screens()` 호출 제거
  - `skip_initial_screens` 마커 처리 제거
  - `android_driver_logged_in` fixture 전체 삭제 (utils.auth 의존)
- `config/capabilities.py` SauceLabs용 전면 단순화
  - 이전 프로젝트의 환경 분기 모두 제거
  - `_ENV_CONFIG` 딕셔너리, `get_env_config()` 함수 제거
  - APK 폴더 구조 단순화 (`apk/{env}/` → `apk/android/`, `apk/ios/`)
  - SauceLabs 패키지 정보 명시 (`com.saucelabs.mydemoapp.rn`)
  - iOS 앱 확장자 다중 지원 추가 (`.app`, `.ipa`, `.zip`)
  - 함수 시그니처에 타입 힌트 추가
- `.env.example` SauceLabs용 재작성
  - 이전 프로젝트 환경변수 13개 제거
  - 5개 섹션 구조로 정리 (Appium / Android / iOS / Allure / 헤더)
  - 모든 변수 옵션 처리 (주석 처리, 기본값 명시)
- `.vscode/settings.json` Python 인터프리터 경로 정리
  - `python.defaultInterpreterPath` 하드코딩 제거 (VSCode 자동 감지로 변경)

**Step 3: 보안/Git 정리 (남은 항목 완료)**
- `.git/` 폴더 삭제 (이전 프로젝트 원격 완전 제거)

**Step 5: 프로젝트 메타파일 작성**
- `change_notes.md` 신규 작성 (본 파일)
- `Todo.md` 신규 작성
- `GIT_RULES.md` 정리 (이전 프로젝트 특화 내용 제거, SMDA용으로 수정)
- `CLAUDE.md` 정리 (이전 프로젝트 특화 내용 제거, 활용 가능한 내용 보존)

---

## 2026-05-13

### 회사 → 집 이전 준비 (Step 1~3)

**Step 1: 캐시/결과물 삭제 (10개 항목)**
- 삭제: `node_modules/`, `allure-report/`, `allure-reports/`, `allure-results/`, `ui_dumps/`, `debug_output/`, `reports/`, `sessions/`, `pdf/`, `pixel5.appiumsession`

**Step 2: 이전 프로젝트 코드/테스트/문서/APK 삭제 (34개 항목)**
- APK: `apk/` 통째 삭제
- tests: 이전 프로젝트 테스트 파일, iOS 테스트 (`ios_contacts_test.py`, `test_ios_first.py`) 등
- utils: `auth.py`, `initial_screens.py`, `language.py` (이전 프로젝트 로그인/언어 모듈)
- pages: `sample_page.py`
- tools: `test_login_live.py`, `debug_keyboard.py`, `explore_app.py`, `fix_git_messages.py`, `teams_notify.py`, `trigger_listener.py`
- docs: `APP_STRUCTURE_stg.md`, `feature_list_live.md`, `PORTFOLIO_GUIDE.md`, `PUBLIC_PUSH_GUIDE.md`
- 루트: 기존 `change_notes.md`, `Todo.md`, `readme_status.md`, `generate_*_pdf.py`
- IDE: `.claude/settings.json`, `.claude/memory/`, `.claude/agents/`, `.vscode/tasks.json`

**Step 3: 보안 정리 (일부)**
- `.env` 파일 삭제 (회사 계정/토큰 제거)

**기타**
- 인수인계 문서 작성 (`Desktop/Claude/appium-SMDA_인수인계/appium-SMDA_인수인계.md`)
- 다음 작업 환경: 회사 Windows 11 (가상화 복구 후) 또는 집 macOS Apple Silicon
