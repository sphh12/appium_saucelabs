# SauceLabs My Demo App — 기능 인벤토리 & 화면 구조

> 대상: **SauceLabs My Demo App (네이티브 Android)** · `com.saucelabs.mydemoapp.android` · APK
> `mda-2.2.0-25` 진입: `SplashActivity` → `MainActivity`(대부분 화면은 프래그먼트). 별도 액티비티:
> `VirtualUsbActivity`, `DebugCrashActivity` Locator 우선순위: **accessibility id > id(resource-id) >
> -android uiautomator > xpath** **출처**: APK 리소스 전수 추출(문자열 186 / id 681 / 액티비티 4) +
> appium-mcp 온디바이스 탐색(2026-06-20). 리소스 ID·content-desc는 APK에서 확정한 값.

**상태 범례**: ✅ E2E로 실행·검증됨 · 🟡 APK 리소스로 확정(자동화 미작성) · ⬜ 권한/디바이스 의존 —
구현 시 온디바이스 확인 필요

---

## 1. 기능 인벤토리 (테스트 케이스 단위)

### F1. 상품 카탈로그 (Products)
- 1.1 ✅ 상품 목록 표시 (`productRV`, 카드별 `productIV`/`titleTV`/`priceTV`)
- 1.2 🟡 **정렬** — 4종: Name ↑/↓, Price ↑/↓ (`sortIV` → 시트 `menuRV`:
  `nameAscCL`/`nameDesCL`/`priceAscCL`/`priceDesCL`, 선택 틱 `tickNameAscIV` 등)
- 1.3 ✅ 상품 탭 → 상세 진입
- 1.4 ✅ 장바구니 배지 수량 (`cartTV`)
- 1.5 🟡 드로어 메뉴 열기 (`menuIV`)

### F2. 상품 상세 (Product Details)
- 2.1 🟡 상품 정보: 이름/가격/이미지/**Product Highlights**(`productHeightLightsTV`)/설명
- 2.2 🟡 **색상 선택** — Black/Blue/Gray/Green (`colorRV`/`colorIV`, 선택표시 `aroundIV`)
- 2.3 🟡 **수량 증감** (`plusIV`/`minusIV`/`noTV`)
- 2.4 🟡 **별점 평가 제출** — 1~5 star 탭(`start1IV`~`start5IV`, desc "Tap to rate an item N star")
  → "Thank you for submitting your review!"
- 2.5 ✅ **장바구니 담기** (`cartBt`, desc "Tap to add product to cart")

### F3. 장바구니 (My Cart)
- 3.1 ✅ 담긴 상품/수량/합계 (`titleTV`/`priceTV`/`itemsTV`/`totalPriceTV`)
- 3.2 🟡 수량 변경 (`plusIV`/`minusIV`)
- 3.3 🟡 **항목 삭제** (`removeBt`, desc "Removes product from cart")
- 3.4 🟡 **빈 카트 상태** ("Oh no! Your cart is empty…", `noItemCL`/`noItemTitleTV`)
- 3.5 ✅ 결제 진행 (`cartBt`, desc "Confirms products for checkout") → 로그인 게이트

### F4. 로그인 (Login)
- 4.1 ✅ 정상 로그인 — `bod@example.com` / `10203040`
- 4.2 🟡 **잠긴 계정** — `alice@example.com` → "Sorry this user has been locked out."
- 4.3 🟡 Visual 유저 — `visual@example.com`
- 4.4 🟡 **빈 값 검증** — "Username is required" / "Password is required"
- 4.5 ✅ 계정 자동완성 (`username1/2/3TV` 탭, desc "Tap to use this username for login")
- 4.6 ⬜ **생체인증 로그인** (desc "Tap to login using biometric verification") — 지문 등록 필요
- 4.7 🟡 **로그아웃** (드로어 `Log Out`) → "You are Successfully logged out."

### F5. 체크아웃 — 배송주소 (Checkout / Address)
- 5.1 ✅ 필수 입력: Full Name / Address1 / City / Zip / Country (+ 선택: Address2 / State)
- 5.2 🟡 **필드별 검증 에러** — 각 필드 `*ErrorTV`/`*ErrorIV` ("Value looks invalid." 등)
- 5.3 ✅ To Payment (`paymentBtn`, desc "Saves user info for checkout")

### F6. 체크아웃 — 결제수단 (Checkout / Payment)
- 6.1 ✅ 카드 입력: 소유자/번호/유효기간/CVV
- 6.2 🟡 필드별 검증 에러 (`cardNumberErrorTV` 등)
- 6.3 🟡 **CVV 툴팁** (`questionIV` → "CVV is the last three digits…")
- 6.4 🟡 **청구지=배송지 체크박스** 토글 (`billingAddressCB`)
- 6.5 ✅ Review Order (`paymentBtn`, desc "Saves payment info and launches screen to review checkout
  data")

### F7. 체크아웃 — 주문검토 (Checkout / Review)
- 7.1 ✅ 주문 요약: 상품 / 배송지(`fullNameTV`…) / 결제수단(`billFullnameTV`…)
- 7.2 🟡 **금액 검증** — 배송비 **$5.99** (`DHL Standard Delivery`) + 상품가 → 합계 `totalAmountTV`
- 7.3 ✅ Place Order (`paymentBtn`, desc "Completes the process of checkout")

### F8. 주문완료 (Checkout Complete)
- 8.1 ✅ 완료 메시지 (`completeTV` "Checkout Complete", `thankYouTV`, `swagTV`, `orderTV`)
- 8.2 🟡 Continue Shopping (`shoopingBt`/`shoppingBt`, desc "Tap to open catalog") → 카탈로그

### F9. WebView
- 9.1 🟡 URL 입력 + 이동 (`urlET`, `goBtn`)
- 9.2 🟡 **HTTPS 검증** — "Please provide a correct https url." (`urlErrorTV`)
- 9.3 ⬜ 웹 콘텐츠 표시 (`webView`)

### F10. QR Code Scanner
- 10.1 ⬜ 카메라 권한 처리
- 10.2 ⬜ 스캔 동작 (`qrCodeTV`, `previewView`)

### F11. Geo Location
- 11.1 ⬜ 위치 권한 처리
- 11.2 🟡 위/경도 표시 (`latitudeTV`/`longitudeTV`)
- 11.3 🟡 **관찰 시작/중지** (`startBtn`/`stopBtn`, desc "Start/Stop observation of user location")

### F12. Drawing
- 12.1 ⬜ 패드에 그리기 (`signature_pad`)
- 12.2 🟡 지우기 (`clearBtn`, desc "Removes anything drawn on pad")
- 12.3 🟡 저장 (`saveBtn`, desc "Save anything drawn on pad")

### F13. About
- 13.1 🟡 버전 표시 (`versionTV`)
- 13.2 ⬜ 웹사이트 링크 ("Go to the Sauce Labs website.")
- 13.3 🟡 SNS 링크 (`FacebookIV`/`LinkedInIV`/`twitterIV`)

### F14. Reset App State
- 14.1 🟡 앱 상태 초기화 (드로어 `Reset App State`, `app_reset_state`)

### F15. FingerPrint (Biometrics)
- 15.1 🟡 생체인증 토글 (`bioMetricSw`, "Allow login with FingerPrint")
- 15.2 ⬜ 등록/지원 여부 메시지 (지문 미등록 시)

### F16. Virtual USB
- 16.1 ⬜ Virtual USB 화면 (`VirtualUsbActivity`, `virtual_usb_message`)

### F17. Crash app (debug)
- 17.1 🟡 **Native crash** (`DebugCrashActivity`, `cause_native_crash_button`)
- 17.2 🟡 **Uncaught exception** (`cause_uncaught_exception_button`)

### F18. 메뉴 드로어 (Menu)
- 18.1 🟡 전체 항목 네비게이션 (`menuRV`, `itemTV`): Catalog / WebView / QR Code Scanner / Geo
  Location / Drawing / About / Reset App State / FingerPrint / Log In·Out

### F19. 스플래시 (Splash)
- 19.1 ✅ 앱 실행 → 카탈로그 자동 전환 (`splashIV`)

> **요약**: 19개 기능영역, **60+ 테스트 가능 동작**. 현재 ✅(검증)=해피패스 11개, 나머지는 🟡(리소스
> 확정)/⬜(권한·디바이스 의존).

---

## 2. 테스트 계정 (로그인 화면 노출)

| 사용자 | 비밀번호 | 용도 |
|--------|----------|------|
| `bod@example.com` | `10203040` | 정상 (해피패스) |
| `alice@example.com` | `10203040` | **잠긴 계정** — "Sorry this user has been locked out." |
| `visual@example.com` | `10203040` | Visual 테스트 |

---

## 3. 화면별 상세 Locator (핵심 플로우 — ✅ 검증)

### 공통 헤더
| 요소 | resource-id | accessibility id |
|------|-------------|------------------|
| 메뉴 | `menuIV` | `View menu` |
| 카트 | `cartRL` | `View cart` |
| 카트 배지 | `cartTV` | — |
| 정렬 | `sortIV` | `Shows current sorting order and displays available sorting options` |

### F1 카탈로그
`productRV`(목록, desc `Displays all products of catalog`) · `productIV`(상품 이미지, **clickable**)
· `titleTV` · `priceTV` · `start1IV`~`start5IV`

### F1.2 정렬 시트
`menuRV` · 항목: `nameAscCL`/`nameDesCL`/`priceAscCL`/`priceDesCL` · 선택 틱:
`tickNameAscIV`/`tickNameDesIV`/`tickPriceAscIV`/`tickPriceDscIV` · 라벨: "Name -
Ascending/Descending", "Price - Ascending/Descending"

### F2 상품 상세
`productTV` · `priceTV` · `productHeightLightsTV` · `descTV` · 색상 `colorRV`/`colorIV`(desc
`Black color` 등)/`aroundIV` · 수량 `minusIV`/`noTV`/`plusIV` · 담기 `cartBt`(desc
`Tap to add product to cart`) · 별점 `start1IV`~`start5IV`(desc `Tap to rate an item N star`)

### F3 장바구니
제목 `productTV`("My Cart") · `titleTV`/`priceTV` · 수량 `minusIV`/`noTV`/`plusIV` · 삭제
`removeBt`(desc `Removes product from cart`) · 합계 `itemsTV`/`totalPriceTV` · 빈 상태
`noItemCL`/`noItemTitleTV` · 결제 `cartBt`(desc `Confirms products for checkout`)

### F4 로그인
`nameET` · `passwordET` · `loginBtn`(desc `Tap to login with given credentials`) · 자동완성
`username1/2/3TV`(desc `Tap to use this username for login`) · 검증
`usernameErrorIV`/`passwordErrorIV` · 생체 `bioMetricIB`/`bioMetricSw`

### F5 체크아웃-주소
> ⚠️ 입력란은 placeholder(`showing-hint="true"`)로 비어 있음 → 필수 미입력 시 검증 에러로 진행 불가.

`fullNameET`/`address1ET`/`address2ET`/`cityET`/`stateET`/`zipET`/`countryET` (각
`*ErrorTV`/`*ErrorIV`) · To Payment `paymentBtn`(desc `Saves user info for checkout`)

### F6 체크아웃-결제
`nameET`(카드소유자)/`cardNumberET`/`expirationDateET`/`securityCodeET` · CVV툴팁 `questionIV` ·
청구지 `billingAddressCB` · `visaIV`/`mastercardIV` · Review `paymentBtn`(desc
`Saves payment info and launches screen to review checkout data`)

### F7 체크아웃-검토
`placeOrderRV` · 배송지 `fullNameTV`/`addressTV`/`cityTV`/`countryTV` · 청구지
`billFullnameTV`/`billaddressTV`/`billingCityAndStateTV`/`billingZipAndCountryTV` · `dhlTV`(배송비)
· `totalAmountTV` · Place Order `paymentBtn`(desc `Completes the process of checkout`)

### F8 주문완료
`completeTV`("Checkout Complete") · `thankYouTV` · `swagTV` · `orderTV` · `shoopingBt`(desc
`Tap to open catalog`)

### F9~F17 추가 화면 (APK 확정 ID — 구현 시 온디바이스 확인)
| 화면 | 핵심 ID |
|------|---------|
| WebView | `urlET`, `urlErrorTV`, `goBtn`, `webView` |
| QR Scanner | `qrCodeTV`, `previewView` |
| Geo Location | `latitudeTV`, `longitudeTV`, `startBtn`, `stopBtn` |
| Drawing | `signature_pad`, `padBackgroundIV`, `clearBtn`, `saveBtn` |
| About | `aboutTV`, `versionTV`, `FacebookIV`, `LinkedInIV`, `twitterIV` |
| FingerPrint | `bioMetricSw`, `bioMetricIB`, `bioMetricInfoTV` |
| Virtual USB | (`VirtualUsbActivity`) `virtual_usb_message` |
| Crash | (`DebugCrashActivity`) `cause_native_crash_button`, `cause_uncaught_exception_button` |

---

## 4. Locator 전략 & 주의사항

1. **체크아웃 3버튼 동일 id**: `To Payment`·`Review Order`·`Place Order`가 모두 `id/paymentBtn`.
   화면당 1개씩만 존재하나, 본 프로젝트는 의도가 드러나도록 화면별 **accessibility id** 사용(§3).
2. **placeholder vs 실제값**: 체크아웃·로그인 입력란은 hint만 있고 비어 있음(`showing-hint="true"`)
   → 필수 입력 안 하면 진행 불가.
3. **content-desc 우선**: 위 desc 값은 APK 문자열 리소스에서 확정한 것이라 가장 안정적. 반복
   목록(상품/색상/별점)은 text·instance 인덱스로 특정.
4. **권한 의존 기능**(⬜): QR(카메라)·Geo(위치)는 런타임 권한 처리 필요. 생체인증은 에뮬레이터 지문
   등록 필요.
5. **별도 액티비티**: Virtual USB·Crash는 `MainActivity`가 아닌 전용 액티비티 → `current_activity`로
   검증 가능.
6. **앱 리셋**: `noReset=false`라 세션마다 초기화(로그아웃 상태로 시작).

---

## 5. 자동화 커버리지 (현재)

> 17 케이스 전부 통과 (POM + 명시적 대기). 실행: `pytest tests/android/`

| 테스트 파일 | 커버 기능 | 케이스 |
|------------|-----------|:---:|
| `smoke_test.py` | 앱 실행 · 카탈로그 로드 | 2 |
| `test_checkout_e2e.py` | 구매 해피패스 (F1→F9) | 1 |
| `test_catalog_sort.py` | 정렬 가격 asc/desc (F1.2) | 2 |
| `test_product_detail.py` | 수량/색상/별점평가 (F2.2~2.4) | 3 |
| `test_cart.py` | 수량변경·삭제/빈카트 (F3.2~3.4) | 2 |
| `test_login_negative.py` | 빈값·잠긴계정 (F4.2, 4.4) | 2 |
| `test_checkout_validation.py` | 주소 필드검증 (F5.2) | 1 |
| `test_webview.py` | URL 검증 (F9.2) | 1 |
| `test_about.py` | 버전 표시 (F13.1) | 1 |
| `test_menu.py` | 로그아웃·앱리셋 (F4.7, F14) | 2 |

**미커버(다음)**: Tier 3 권한·디바이스 의존(F10 QR · F11 Geo · F12 Drawing · F15 FingerPrint · F16
VirtualUSB · F17 Crash), 결제 필드검증(F6.2), 다중상품·정렬 name(F1.2).

> §5는 **Android**(`tests/android/`). iOS는 §6 참조.

---

## 6. iOS 자동화 (구조 차이 + 커버리지)

> iOS는 **UIKit/하단 탭바** 구조라 Android와 다름. POM은 `pages/ios/`, 테스트는 `tests/ios/`. 실행:
> `IOS_UDID=<udid> IOS_DEVICE_NAME="iPhone 17 26.5" IOS_PLATFORM_VERSION=26.5 pytest tests/ios/`

### Android 대비 차이
| 항목 | Android | iOS |
|------|---------|-----|
| 네비게이션 | 햄버거 드로어 | **하단 탭바** (`Catalog/Cart/More-tab-item`) |
| Locator | resource-id + content-desc | 서술형 **accessibility id `name`** (`AddToCart`, `ProceedToCheckout`, `*-menu-item`) |
| 로그인 | 입력 or 저장계정 탭 | **저장계정 버튼 탭만**(타이핑 X). bob/alice/john/visual — **잠긴 계정 없음** |
| 정렬 | 있음 | **없음** |
| 주소 검증 | 인라인 필드 에러 | **네이티브 Alert** `Validation Error!` |
| 앱 리셋 | 단일 | **2단 Alert** (`RESET APP` → `App State has been reset.` OK) |

### 주요 화면 locator (accessibility id)
- 탭바: `Catalog-tab-item` / `Cart-tab-item` / `More-tab-item`
- 카탈로그: `Product Image`(→상세) / `Product Name` / `Product Price`
- 상세(`ProductDetails-screen`): `AddToCart` / `AddPlus Icons` / `SubtractMinus Icons` / `Amount` /
  `{Black|Blue|Gray|Green}ColorUnSelected Icons` / `StarUnSelected Icons`(→리뷰 Alert)
- 카트(`Cart-screen`): `ProceedToCheckout` / `Remove Item` / `No Items` / `GoShopping`
- 로그인: 계정 버튼 `bob@example.com` 등 + Button `Login`
- More:
  `Webview/QrCodeScanner/GeoLocation/Drawing/About/ResetAppState/Biometrics/CrashTheApp-menu-item` /
  `Login Button` / `LogOut-menu-item`
- 체크아웃(`ShippingAddress-screen`): `To Payment` / 입력란=name 없는 TextField(인덱스) / 검증 Alert
  `Validation Error!`+`OK`
- About(`About-screen`): `Go to saucelabs.com`

### 커버리지 (10 통과 + 2 skip)
| 테스트 | 케이스 |
|--------|:---:|
| `test_catalog` | 1 |
| `test_product_detail` (수량/색상/별점) | 3 |
| `test_cart` (삭제→빈) | 1 |
| `test_login` (정상) | 1 |
| `test_menu` (로그아웃/리셋) | 2 |
| `test_checkout_validation` (Alert) | 1 |
| `test_about` | 1 |
| `test_checkout_e2e` / `test_webview` | **skip** ×2 |

**⛔ skip 사유**: iOS 소프트 키보드(한글) 환경 블로커 — 타이핑 화면(체크아웃 완주·WebView URL)은
키보드가 버튼을 가리고 입력을 오염시킴. Xcode 26.5 + 한글 macOS 이슈. 키보드 해결 시 활성화
가능(`pages/ios/checkout_page.py`에 입력 구조는 보존).
