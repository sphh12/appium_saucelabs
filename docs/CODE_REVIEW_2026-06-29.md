# 전체 코드 리뷰 결과 (2026-06-29)

> SauceLabs My Demo App Appium 자동화 프로젝트 전체 코드 리뷰 보고서
> 이 문서는 **개선 작업 추적용 기준 문서**입니다. 항목 처리 시 체크박스를 갱신하세요.
> 진행 관리: `CHANGELOG.md` `Todo` 섹션 참고.

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| 대상 커밋 | `dc6208f` (리뷰 시점 — 옛 저장소 해시, 2026-08-31 재생성으로 조회 불가) |
| 방식 | 10개 영역 다차원 병렬 리뷰 → 발견 항목별 적대적 검증(반증 시도) |
| 리뷰 영역 | Android POM / iOS POM / Android 테스트 / iOS 테스트 / conftest / config·utils / 도구류 / 프로젝트 설정 / 보안 / Android↔iOS 일관성 |
| 확정 | **65건** (허위양성 1건 기각) |

### 심각도 분포

| 심각도 | 건수 | 비고 |
|--------|------|------|
| 🔴 Critical | 1 | 보안 — **완료** |
| 🟠 High | 1 | 보안 — **완료** |
| 🟡 Medium | 12 | 권장 (보안 1건 완료, 10건 대기) |
| ⚪ Low | 41 | 개선 (보안 1건 완료) |
| ℹ️ Info | 10 | 정보성 |

---

## 2. 종합 평가

전반적으로 **골격이 잘 짜인 프로젝트**입니다. 리뷰어 공통으로 확인한 강점:

- ✅ `BasePage` 명시적 대기 설계 견고 (`implicit_wait=0` + `WebDriverWait`/`EC` + stale 재시도)
- ✅ Locator 우선순위(ACCESSIBILITY_ID > Resource ID > XPath) 준수, XPath 남용 없음
- ✅ POM 순수성 — 페이지엔 locator+동작, assert는 테스트
- ✅ 강한 단언 다수 (정렬 검증, E2E 합계, 카트 수량×2 합계 등)
- ✅ **치명적 false-pass 버그 없음 / 하드코딩된 시크릿·실제 개인정보 없음** (테스트 계정·카드는 공개 데모값)

→ 발견된 65건은 대부분 **견고성·일관성·포트폴리오 완성도** 차원입니다.

---

## 3. ✅ 완료 — 보안 하드닝 (A1~A3, 커밋 `a82a154`)

- [x] **A1 `.env`가 `.gitignore`에 미차단** — `.gitignore` · Public 레포에 토큰 커밋 위험 → `.env`/`.env.*` 추가, `!.env.example` 유지 (R-01/R-02)
- [x] **A2 `serve.py` 0.0.0.0 바인딩** — `tools/serve.py:88` · LAN에서 `/.env` 접근 가능 → `127.0.0.1` 바인딩 (R-13)
- [x] **A3 외부 대시보드 사용자명·앱경로 노출** — `conftest.py:251/414` · OS 사용자명 → `EXECUTOR_NAME`(기본 `local`), 앱 절대경로 → 파일명만 (R-34/R-51)
  - 참고: `gitMessage`(R-62)는 이미 공개 레포 히스토리에 있는 정보라 의도적으로 유지

---

## 4. 🟠 권장 — Medium (9/10 완료 · 2026-07-01, R-11 보류)

- [x] **R-03 bool 계약 위반** — `BasePage.text_present() -> bool` 헬퍼 추가(`TimeoutException`→`False`), `products/cart/about.is_displayed`·`cart.is_empty`·`checkout.is_order_complete`를 이 헬퍼로 통일. R-08(Android/iOS `is_empty` 불일치)도 함께 해소
- [x] **R-04 `smoke_test.py` POM 우회** — `ProductsPage` POM 기반으로 재작성(raw `WebDriverWait`/`find_elements` 제거, `test_app_launches` 패키지 검증은 유지)
- [x] **R-05 `driver` 픽스처 `--platform` 미지정 시 `ValueError`** — `_resolve_platform(config)` 단일 헬퍼로 `pytest_configure`·`platform` 픽스처 통일(경로 기반 자동 감지 + android 폴백)
- [x] **R-06 `driver.quit()` 누수 위험** — 픽스처를 `try/yield/finally: _teardown_driver`로, `_create_driver`도 생성 후 setup 실패 시 즉시 quit + quit 자체 예외 방어
- [x] **R-07 세 드라이버 픽스처 중복** — `_create_driver`/`_teardown_driver` 헬퍼로 단일화, 세 픽스처는 얇은 래퍼
- [x] **R-09 iOS `open_first_product` 헬퍼 우회** — Android/iOS 모두 `self.click(PRODUCT_IMAGES)`로 → `find_clickable`(첫 요소·clickable 대기) + stale 재시도 사용, raw `[0].click()` 제거
- [x] **R-10 iOS About 버전 동어반복 단언** — 로케이터와 독립적으로 실제 버전 번호(`\d+\.\d+`) 검증으로 변경
- [ ] **R-11 iOS 카트 수량변경 테스트 누락** — `tests/ios/test_cart.py` · **보류**: iOS `CartPage`에 수량/합계/항목수 accessibility id가 없어 추측 로케이터로 만들면 깨진 테스트가 됨. `python tools/ui_dump_ios.py -w`로 부팅된 시뮬에서 해당 id 확보 후 getter 보강 → `test_change_quantity` 추가 필요
- [x] **R-14 트렌드 history 항상 깨짐** — `_find_latest_timestamp_dir`가 타임스탬프 폴더(`^\d{8}_\d{6}$`)만 후보로 필터 → `LATEST`/`dashboard` 오선택 제거
- [x] **R-12 `run-app.sh` eval/오류무시** — `PYTEST_ARGS`/`RUN_ALLURE_OPTS` 배열화로 `eval` 제거(공백/특수문자 안전) + `set -o pipefail` 추가(`set -e`는 점검 로직 때문에 미적용)

---

## 5. 🟡 개선 — Low (41건, 테마별)

### 5-1. 죽은 코드 / 중복 정리

- [ ] **R-26 `utils/helpers.py` 모듈 전체 미사용** — `utils/helpers.py` · 어디서도 import 안 됨, conftest와 기능 중복 → 승격 또는 제거
- [ ] **R-24 `helpers.wait()` = 금지된 `time.sleep` 래퍼** — `utils/helpers.py:10` → 제거, 명시적 대기로 대체
- [ ] **R-25 `scroll_to_element` deprecated `driver.swipe`** — `utils/helpers.py:36` · 무대기 `find_element` + 구식 API → W3C Actions, 또는 제거(base_page와 중복)
- [ ] **R-29 `save_screenshot` CWD 의존 상대경로** — `utils/helpers.py:31` · `reports/` 하드코딩 → `PROJECT_ROOT` 절대경로화
- [ ] **R-56 `base_page.take_screenshot` 죽은 코드** — `pages/base_page.py:131` · conftest 첨부 정책과 이중화, 미사용 → 제거 또는 정렬
- [ ] **R-43 iOS `PRODUCT_NAMES` 미사용 상수** — `pages/ios/catalog_page.py:9` → 활용 메서드 추가 또는 제거
- [ ] **R-28 `test_data.ANDROID_VALID_USER` 미사용** — `config/test_data.py:15` → 제거 또는 실사용

### 5-2. Allure 어노테이션 (가이드라인 §4.1 "필수")

- [ ] **R-20 Android `@allure.severity`/`@allure.title` 누락** — `test_cart.py:21` 외 다수 → 메서드/클래스에 추가
- [ ] **R-45 iOS `@allure.severity` 누락** — `tests/ios/*.py` 대부분 → 추가

### 5-3. 단언 강화

- [ ] **R-22 체크아웃 검증이 5필드 중 1개만 확인** — `tests/android/test_checkout_validation.py:22` → 5개 에러 getter 추가 후 검증(또는 제목 축소)
- [ ] **R-23 `test_select_color` 약한 단언** — `tests/android/test_product_detail.py:33` · 색상선택 검증 못 함(배지만) → 검증신호 추가 또는 story 정직하게 기술
- [ ] **R-21 정렬 테스트 parametrize 기회** — `tests/android/test_catalog_sort.py:14` · asc/desc 중복 + 이름정렬 미검증 → `parametrize`로 4종 통합
- [ ] **R-46 iOS 빈 카트 `GoShopping` 미검증** — `tests/ios/test_cart.py:28` · Android보다 약함 → `assert cart.is_visible(GO_SHOPPING)` 추가
- [ ] **R-19 죽은 실패 메시지** — `tests/android/test_cart.py:42` · bool 계약(R-03)과 동일 뿌리 → R-03와 함께 처리

### 5-4. `test_data` 중앙화 / Android↔iOS 일관성

- [ ] **R-35 Android 로그인이 `test_data` 미사용** — `pages/login_page.py:14` · 계정값 코드/주석 하드코딩 → `test_data` 도입
- [ ] **R-36 iOS `login_as` 기본 이메일 하드코딩** — `pages/ios/login_page.py:25` · `test_data`와 중복 → `test_data.IOS_VALID_USER[0]`로 통일
- [ ] **R-37 Cart 페이지 API 플랫폼 비대칭** — `pages/ios/cart_page.py:7` · 한쪽에만 있는 메서드 다수 → 공통 메서드 계약 정의
- [ ] **R-39 `flows`/`flows_ios` 네이밍 불일치** — `utils/flows.py:31` → 명명 규칙 통일
- [ ] **R-44 iOS 수량 위젯 locator/메서드 중복** — `pages/ios/cart_page.py:13` · cart·product_detail 중복 → `IOSBasePage`로 공통화

### 5-5. Appium 견고성

- [ ] **R-38/R-41 iOS `checkout.fill_address` raw `send_keys`** — `pages/ios/checkout_page.py:43/58` · `input_text`(clear·stale 재시도) 우회 + 필드 매핑 불완전 → `NotImplementedError`로 명시(키보드 이슈 보류) 또는 `input_text` 사용
- [ ] **R-40 `item_count` bare `except Exception`** — `pages/cart_page.py:26` → `except TimeoutException`으로 축소
- [ ] **R-42 `is_color_selected` 광범위 except** — `pages/ios/product_detail_page.py:42` · 진짜 오류를 False로 은폐 → `except TimeoutException`
- [ ] **R-15 `QUANTITY=noTV` 다중항목 시 첫 항목만** — `pages/cart_page.py:11` · 멀티 상품 확장 시 잘못된 검증 → 인덱스/행 스코프 locator
- [ ] **R-16 `set_quantity`가 increase만** — `pages/product_detail_page.py:53` · 이름과 동작 불일치 → 멱등 구현 또는 `increase_quantity_by(n)` 개명
- [ ] **R-18 `rate_product` raw `assert`** — `pages/product_detail_page.py:59` · 입력 가드는 `ValueError`가 적절
- [ ] **R-17 `CART_BADGE` 패키지 풀 하드코딩** — `pages/base_page.py:29` · `_PKG` 상수 미사용 → 통일
- [ ] **R-27 앱 자동탐색 사전식 정렬** — `config/capabilities.py:65` · "최신=이름순 마지막" 가정이 버전 숫자에서 깨짐 → `mtime` 기준 또는 주석 정정

### 5-6. conftest 잔이슈

- [ ] **R-30 녹화 시작 실패 시 stop 미보장** — `conftest.py:687` → quit 직전 best-effort `stop_recording_screen`
- [ ] **R-31 `_dismiss_system_ui_dialog`가 implicit wait 토글 + `time.sleep`** — `conftest.py:277` · 프로젝트가 금지한 패턴 → 명시적 대기로 전환
- [ ] **R-32 `--record-video` 옵션 혼용** — `conftest.py:314` · `getoption` 표기 혼용 → 한 표기로 통일/`BooleanOptionalAction`
- [ ] **R-33 logcat 플랫폼 판정 휴리스틱 OR** — `conftest.py:564` → resolved platform 양성 판정으로 (R-05 연관)

### 5-7. 도구 견고성

- [ ] **R-52 codegen이 `time.sleep` 생성** — `tools/mcp/codegen.py:140` · 가이드라인 위반 코드 유입 → 명시적 대기 변환 또는 TODO 경고
- [ ] **R-53 `ui_dump` page_source 이중 조회** — `tools/ui_dump.py:380` · 저장본/통계본 불일치 → 원본 재사용
- [ ] **R-54 watch 루프 무한 공회전** — `tools/ui_dump.py:597`(ios:459) · 세션 끊겨도 무한 무시 → 연속 실패 카운트/종료성 예외 처리
- [~] **R-55 upload cleanup 용량 오계산** — `tools/upload_to_dashboard.py:439` · **해당 없음(2026-08-25)**: 공개 저장소 정책으로 외부 대시보드 업로드 기능(해당 파일) 자체를 제거

### 5-8. 프로젝트 설정

- [ ] **R-48 `package-lock.json` 미커밋** — `.gitignore:20` · node 의존성 비결정성(Appium 3.x 호환 민감) → lock 커밋
- [ ] **R-49 `run-app.sh` zshrc 이식성** — `shell/run-app.sh:22` · macOS 전제 → OS별 분기/주석
- [ ] **R-50 `package.json` allure 스크립트 Android만** — `package.json:12` → iOS용 스크립트 추가

---

## 6. ℹ️ 정보성 — Info (10건)

- [ ] **R-57 파일 명명 혼재** — `smoke_test.py`만 `*_test.py`, 나머지 `test_*.py` → 통일
- [ ] **R-58 `test_locked_out`의 `.lower()` 부분매칭 느슨** — `tests/android/test_login_negative.py:30` → 전문 일치/키워드 구체화
- [ ] **R-59 iOS `select_user` 인라인 로케이터** — `pages/ios/login_page.py:19` → 빌더 메서드 추출 또는 주석
- [ ] **R-60 iOS `get_quantity` `int()` 직접 변환** — `pages/ios/product_detail_page.py:23` · 형식 변동 시 `ValueError` → UI 덤프 확인 후 정규식 방어
- [ ] **R-61 Allure story 부여 위치 불일치** — `tests/ios/test_about.py:11` → 규칙 통일
- [ ] **R-64 `session_recorder` 죽은 정규식** — `tools/mcp/session_recorder.py:531` · `_SECRET_HINT_RE` 미사용 → 제거 또는 TODO
- [ ] **`.gitattributes`에 `*.sh eol=lf` 부재** — shell CRLF 위생(아래 §7 참고) → `*.sh text eol=lf` 추가 권장
- [x] **R-62 `gitMessage` 외부 업로드** — `conftest.py:400` · 공개 히스토리에 있는 정보라 유지(조치 불필요)
- [x] **R-63 외부 URL 하드코딩** — `tools/upload_to_dashboard.py` · 시크릿 아님(공개 엔드포인트)
- [x] **R-65 `capabilities.json` 타 프로젝트 잔존** — `tools/mcp/capabilities.json` · `.gitignore` 추적 제외 확인됨(보안 사고 아님), 재생성 시 정리

---

## 7. 기각된 항목 (허위양성 1건)

- **shell 스크립트 CRLF → `bad interpreter: ^M` 실행 불가** — `shell/run-app.sh` · **진단 과장으로 기각.** git 커밋 blob은 LF이고 로컬 Windows만 `core.autocrlf=true`로 CRLF가 보이는 것 → macOS clone에선 정상 동작. 단 `.gitattributes` 정규화 부재는 위생 이슈로 §6에 반영.

---

## 8. 부록 — 영역별 한줄 평

| 영역 | 평 |
|------|-----|
| Android POM | 잘 설계됨. bool 계약 일관성(R-03)·cart locator(R-15)만 보완 |
| iOS POM | 잘 설계됨. raw element 접근(R-09)·fill_address(R-38) flakiness 소지 |
| Android 테스트 | 강한 단언 정착. Allure 어노테이션·parametrize·죽은 메시지 보완 |
| iOS 테스트 | flakiness 낮음. About 동어반복 단언·커버리지 격차·severity 누락 |
| conftest | 정교함. 플랫폼 감지 분리(R-05)·quit 누수(R-06)·3중복(R-07)이 핵심 |
| config·utils | capabilities 견고. `helpers.py` 죽은 코드가 감점 |
| 도구류 | 견고한 편. serve 바인딩(완료)·trend history(R-14)가 핵심 |
| 프로젝트 설정 | pytest/pyproject 정합. `.env` 가드(완료)·lock 미커밋 |
| 보안 | 하드코딩 시크릿 없음. `.env` 가드(완료)가 최우선이었음 |
| Android↔iOS 일관성 | 대기 헬퍼 공유 양호. test_data·API 비대칭이 횡단 약점 |
