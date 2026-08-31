"""iOS 체크아웃 배송주소 (ShippingAddress-screen) + 검증.

⚠️ 입력란은 name 없는 TextField라 인덱스로 접근.
⚠️ 주소/결제 '입력'은 iOS 소프트 키보드 환경 이슈로 자동화 보류(타이핑 필요).
   단, '검증'(빈 상태 To Payment → Alert)은 타이핑이 없어 자동화 가능.
필드 순서: 0 FullName / 1 Address1 / 2 Address2 / 3 City / 4 Zip / 5 State / 6 Country
"""
from appium.webdriver.common.appiumby import AppiumBy

from pages.ios.base_ios_page import IOSBasePage


class CheckoutPage(IOSBasePage):
    SCREEN = (AppiumBy.ACCESSIBILITY_ID, "ShippingAddress-screen")
    TO_PAYMENT = (AppiumBy.ACCESSIBILITY_ID, "To Payment")
    TEXT_FIELDS = (AppiumBy.CLASS_NAME, "XCUIElementTypeTextField")
    # 주소 입력란은 name 없는 TextField → UI 순서 기반 인덱스(명명 상수). 순서 변경 시 여기만 조정.
    FIELD_FULL_NAME, FIELD_ADDRESS1, FIELD_ADDRESS2 = 0, 1, 2
    FIELD_CITY, FIELD_ZIP, FIELD_STATE, FIELD_COUNTRY = 3, 4, 5, 6
    EXPECTED_FIELD_COUNT = 7
    # 검증 Alert
    VALIDATION_ALERT = (AppiumBy.ACCESSIBILITY_ID, "Validation Error!")
    ALERT_OK = (AppiumBy.ACCESSIBILITY_ID, "OK")

    def is_displayed(self) -> bool:
        return self.is_visible(self.SCREEN)

    def tap_to_payment(self):
        self.click(self.TO_PAYMENT)

    def has_validation_error(self) -> bool:
        return self.is_visible(self.VALIDATION_ALERT)

    def get_validation_message(self) -> str:
        # Alert 내부 메시지 StaticText
        loc = (AppiumBy.IOS_PREDICATE, "type == 'XCUIElementTypeStaticText' AND label CONTAINS 'provide'")
        return self.get_text(loc)

    def dismiss_validation(self):
        self.click(self.ALERT_OK)

    # ── 타이핑 필요(키보드 이슈로 보류) — 구조만 보존 ──
    def fill_address(self, full_name, address1, city, zip_code, country):
        fields = self.find_all(self.TEXT_FIELDS)
        # silent mismatch 차단: 기대 개수 미만이면 인덱스 매핑이 어긋난 것 → 명시적 실패
        if len(fields) < self.EXPECTED_FIELD_COUNT:
            raise AssertionError(
                f"체크아웃 입력란 {self.EXPECTED_FIELD_COUNT}개 기대, {len(fields)}개 발견 "
                "— iOS 폼 변경 가능성(인덱스 매핑 점검 필요)"
            )
        by_index = {
            self.FIELD_FULL_NAME: full_name,
            self.FIELD_ADDRESS1: address1,
            self.FIELD_CITY: city,
            self.FIELD_ZIP: zip_code,
            self.FIELD_COUNTRY: country,
        }
        for idx, value in by_index.items():
            fields[idx].click()
            fields[idx].send_keys(value)
