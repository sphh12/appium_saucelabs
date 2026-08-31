# CI 가이드 (GitHub Actions)

워크플로는 플랫폼별로 **2개**다. iOS 는 WDA 빌드 등 실패 지점이 많아 파일을 나눠, iOS 문제가
Android 회귀를 붉게 만들지 않도록 격리했다.

| 워크플로 | 파일 | 러너 | 트리거 | 스케줄 |
|---|---|---|---|---|
| **[Android] Appium - My Demo App** | `android-regression.yml` | `ubuntu-latest` + 에뮬레이터 | push · PR · 수동 · 스케줄 | KST 03:20 |
| **[iOS] Appium - My Demo App** | `ios-regression.yml` | `macos-latest` + 시뮬레이터 | 수동 · 스케줄 | KST 03:50 |

iOS 에 push/PR 트리거를 넣지 않은 것은 의도적이다 — 일상적인 코드 푸시마다 macOS 러너를 쓰지 않고,
iOS 불안정성이 PR 게이트를 막지 않게 한다. 필요해지면 추가하면 된다.

> 전략(플랫폼 선택·무료 한도·Bitrise 비교)은 [CI_CD_STRATEGY.md](CI_CD_STRATEGY.md) 참고.
> 이 문서는 **현재 구현된 워크플로의 사용법**만 다룬다.

## 실행 이력 제목 (run-name)

GitHub 은 `push`/`pull_request` 런의 제목을 커밋 메시지·PR 제목으로 정하지만,
`schedule`/`workflow_dispatch` 는 커밋 맥락이 없어 **워크플로 이름으로 폴백**한다.
그러면 목록에서 모든 야간 런이 같은 제목으로 보여 구분이 안 된다. 그래서 `run-name` 을 지정했다.

| 트리거 | 런 제목 |
|---|---|
| `schedule` | `[Daily] Regression Test` |
| `workflow_dispatch` | `[Manual] Regression Test` |
| `push` / `pull_request` | GitHub 기본값(커밋 메시지·PR 제목) — `run-name` 이 빈 문자열이면 기본값을 쓴다 |

워크플로 이름(`[Android] Appium - My Demo App` / `[iOS] ...`)은 목록의 **부제**(`... #12: Scheduled`)에 그대로 남아
어느 플랫폼의 런인지 구분된다.

## 실행 트리거 4가지 (Android)

| 트리거 | 방식 | 코드 변경 | 용도 |
|---|---|---|---|
| `push` | 자동 | 필요 | main/master 푸시 시 회귀 검증 |
| `pull_request` | 자동 | 필요 | PR 머지 전 게이트 |
| `workflow_dispatch` | 수동 | 불필요 | Actions 탭 "Run workflow" — 올라간 코드 재실행 |
| `schedule` | 자동 | 불필요 | 야간 회귀 (매일 **KST 03:20**) |

```bash
gh workflow run android-regression.yml   # 최신 main 코드로 새로 실행
gh run list --workflow android-regression.yml --limit 5
gh run view <런ID>                       # 요약 (--log 로 전체 로그)
gh run rerun <런ID> --failed             # 실패 job 만 재실행 (플레이키 확인)
```

## 동작 흐름

1. Python 3.12 + Node 22 설치 → `pip install -r requirements.txt` → `npm install`
2. UiAutomator2 드라이버 설치 (이미 있으면 건너뜀)
3. **대상 앱 APK 다운로드** — `apps/` 는 gitignore 라 저장소에 없으므로 릴리스(2.2.0 고정)에서 받고
   ZIP 매직으로 검증
4. **KVM 활성화** — 에뮬레이터 하드웨어 가속(없으면 부팅이 사실상 불가)
5. `reactivecircus/android-emulator-runner` 로 API 34 / x86_64 / google_apis / **profile `pixel_6`**
   에뮬레이터 부팅
6. `.github/scripts/run-ci-tests.sh` 실행 — ANR 대화상자 차단(`hide_error_dialogs`) → Appium 기동 →
   `/status` 응답 대기(최대 60초) → `pytest tests/android --reruns 2 --alluredir allure-results`
7. 성공/실패 무관하게 `allure-report/` + `allure-results/` + `appium.log` 를 아티팩트로 업로드(30일)

소요 시간은 **15~25분**(에뮬레이터 부팅 3~5분 + 17 케이스). 저장소가 Public 이라 실행 시간은 무료다.

> **npm 캐시를 쓰지 않는 이유**: `package-lock.json` 이 이 저장소의 `.gitignore` 대상이라 러너에
> 존재하지 않는다. `actions/setup-node` 의 `cache: npm` 과 `npm ci` 는 lock 파일을 **필수**로
> 요구하므로 (없으면 `Dependencies lock file is not found` 로 job 이 즉시 실패한다) 캐시 없이
> `npm install` 을 쓴다. lock 파일을 커밋하기로 정책을 바꾸면 캐시와 `npm ci`(재현 가능한 설치)를
> 함께 얻을 수 있다 — 설치가 30~60초 빨라지고 Appium 버전이 CI 에서 예고 없이 올라가는 일도 막힌다.

## 시크릿 / 환경변수

**등록할 시크릿이 없다.** `.env` 의 모든 항목이 선택값이고, 테스트 계정(`bob@example.com` /
`10203040`)은 앱 로그인 화면에 표시되는 공개 데모값이다. 워크플로에서는
`EXECUTOR_NAME=github-actions` 만 지정한다.

민감값이 필요해지면 저장소 Settings → Secrets and variables → Actions 에 등록 후 주입한다:

```yaml
      - name: "테스트 실행"
        run: python -m pytest
        env:
          SOME_TOKEN: "${{ secrets.SOME_TOKEN }}"
```

## 리포트 확인

GitHub → Actions → 해당 실행 → Artifacts → `allure-report` 다운로드 후:

- `allure-report/index.html` — **로컬 서버로 열어야 한다.** 데이터를 XHR 로 읽어 `file://` 로는 빈
  화면이다. 압축을 풀고 `python tools/serve.py --port 8000` 방식으로 열거나
  `npx allure open allure-report` 를 쓴다.
- 실패 케이스에는 스크린샷 · 비디오(mp4) · `logcat.txt` · `page_source.xml` · `capabilities.json` 이
  첨부된다 (성공 케이스는 첨부하지 않는다 — `--allure-attach=hybrid` 기본값).
- `appium.log` — 세션 생성 실패 등 드라이버 레벨 문제를 볼 때.

## 로컬 실행과 다른 점

| 항목 | 로컬 | CI |
|---|---|---|
| 실행 진입점 | `python tools/run_allure.py -- ...` (리포트 생성 + 로컬 대시보드 갱신) | `pytest --alluredir` 후 워크플로에서 `npx allure generate` |
| 에뮬레이터 | 미리 띄워둔 AVD | 워크플로가 매번 새로 부팅(상태 없음) |
| 앱 | `apps/android/*.apk` 수동 배치 또는 `bootstrap.ps1` | 워크플로가 `curl` 로 다운로드 |
| 재시도 | 기본 없음 | `--reruns 2` (플레이키 완화) |

## 스케줄 관련 주의사항

- `cron` 은 **UTC 기준**이다. KST = UTC + 9 (한국은 서머타임 없음). `'20 18 * * *'` = KST 03:20.
- 정시(`:00`)는 GitHub 부하가 몰려 수 분~수십 분 지연될 수 있어 분 단위를 비정시로 둔다.
- **기본 브랜치(main)의 워크플로 파일만** 스케줄·수동 실행된다. 작업 브랜치에서 cron 을 바꿔도
  병합 전에는 적용되지 않고, Actions 탭에 "Run workflow" 버튼도 나타나지 않는다.
- 저장소가 **60일간 활동이 없으면** 스케줄이 자동 비활성화된다(알림 메일). Actions 탭에서
  재활성화하면 된다.

## iOS 워크플로

```bash
gh workflow run ios-regression.yml     # 수동 실행
gh run list --workflow ios-regression.yml --limit 5
```

동작 흐름은 Android 와 같고, iOS 특유의 단계가 셋 있다.

1. **앱**: 릴리스 2.2.2 의 `SauceLabs-Demo-App.Simulator.zip` 을 받는다.
   `capabilities.py` 가 `.zip` 을 그대로 인식하므로 압축 해제가 필요 없다.
2. **시뮬레이터 동적 선택**: `xcrun simctl list devices available --json` 에서 가장 높은 iOS
   런타임의 iPhone 을 골라 **udid 로 지정**한다(`IOS_UDID`). 러너의 Xcode 버전에 따라 설치된
   런타임이 달라지므로 `IOS_DEVICE_NAME="iPhone 15"` 같은 고정값을 쓰면 첫 런부터 세션 생성이
   실패한다.
3. **WDA(WebDriverAgent) 빌드**: 첫 세션에서 2~5분 추가로 걸린다. 시뮬레이터는 **코드 서명이 필요
   없어** 실기기보다 훨씬 수월하다(실기기로 확장하려면 인증서·provisioning profile 이 필요하다).

전체 소요는 15~25분으로 Android(6~9분)보다 길다. 저장소가 Public 이라 macOS 러너도 무료다
(Private 이면 Linux 대비 10배로 과금되므로 정책을 다시 검토해야 한다).

### skip 중인 2건

`test_checkout_e2e` · `test_webview` 는 로컬 macOS 의 한글 소프트 키보드 문제로 skip 상태다. 러너는
영문 환경이라 **CI 에서는 통과할 가능성**이 있다 — green 확보 후 skip 을 풀어 확인해 볼 만하다.

### 실기기 확장

실기기(iPhone)는 GitHub 호스팅 러너로는 불가능하다. 필요해지면 self-hosted 러너나
`CI_CD_STRATEGY.md` 의 시나리오 B(Bitrise) 를 검토한다.

## 트러블슈팅

| 증상 | 원인 / 대응 |
|---|---|
| `Dependencies lock file is not found` | `setup-node` 의 `cache: npm` 이 `package-lock.json` 을 찾지 못한 것. 이 저장소는 lock 을 커밋하지 않으므로 캐시 옵션을 쓰지 않는다 |
| job 이 아예 생성되지 않음 | 워크플로 YAML 이 깨진 것. 값에 콜론·하이픈이 있으면 반드시 인용해야 한다. 커밋 전 `npx --yes js-yaml <파일>` 로 파싱 확인 |
| 대부분의 케이스가 요소 미발견으로 무더기 실패 | ANR 시스템 대화상자(`Pixel Launcher isn't responding`)가 앱 위를 덮은 것. 아티팩트의 `page_source.xml` 에 `package="android"` · `android:id/aerr_close` 가 보이면 확정. 워크플로가 `hide_error_dialogs 1` 로 차단하며, conftest 가 남은 대화상자를 닫는다 |
| 상세 화면 진입 실패로 다수 케이스가 `상품 상세가 표시되지 않음` | 에뮬레이터 화면이 너무 작은 것. `profile` 을 생략하면 기본 디바이스가 **320x640** 으로 생성돼 카탈로그에 상품이 1개만 보이고 탭이 상세로 이어지지 않는다(실측). `profile: pixel_6` 을 유지할 것 |
| 에뮬레이터 부팅 타임아웃 | KVM 활성화 스텝이 빠졌거나 러너가 가속을 지원하지 않는 경우. `api-level`/`arch` 조합(34 / x86_64 / google_apis)을 유지할 것 |
| `다운로드 파일이 APK(ZIP)가 아니다` | 릴리스 URL 변경 또는 네트워크 차단. `APK_URL` 을 최신 릴리스로 갱신 |
| `Appium 기동 실패(60초 초과)` | 아티팩트의 `appium.log` 확인. 드라이버 미설치면 `npx appium driver install uiautomator2` 스텝 실패 여부를 본다 |
| `Could not find a connected Android device` | 에뮬레이터가 준비되기 전에 테스트가 시작된 경우. conftest 의 preflight 가 즉시 중단시키므로 로그 앞부분에서 원인이 보인다 |
| (iOS) `Could not find a device with name/version` | 시뮬레이터를 고정값으로 지정한 경우. 스크립트가 `xcrun simctl` 로 동적 선택하도록 되어 있으니, 러너에 iPhone 시뮬이 하나도 없으면 로그의 '사용 가능한 iPhone 시뮬레이터가 없다' 메시지를 확인한다 |
| (iOS) 첫 테스트만 `ECONNREFUSED 127.0.0.1:8100` | WDA 기동이 기본 타임아웃(60초)을 넘긴 것. 첫 세션은 WebDriverAgent를 빌드·설치하느라 오래 걸린다. `IOS_WDA_LAUNCH_TIMEOUT`(기본 240초, CI 360초)으로 조절한다 |
| (iOS) WDA 빌드 실패 | Xcode 버전과 xcuitest 드라이버 호환 문제. 아티팩트의 `appium.log` 에서 `xcodebuild` 출력을 확인하고, 필요하면 드라이버 버전을 올린다 |
| 특정 케이스만 간헐 실패 | `--reruns 2` 로 재시도 후에도 실패한 것. `gh run rerun <ID> --failed` 로 재현성을 확인하고 대기 조건을 보강한다 |
