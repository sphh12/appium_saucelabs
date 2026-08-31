"""체크아웃 플로우 (배송주소 → 결제수단 → 주문검토 → 주문완료) + 주소 검증.

⚠️ 'To Payment' / 'Review Order' / 'Place Order' 버튼은 **모두 같은 resource-id `paymentBtn`** 라,
   반드시 accessibility id(content-desc)로 구분한다.
"""
from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PKG = "com.saucelabs.mydemoapp.android:id/"


class CheckoutPage(BasePage):
    # ── 배송주소 ──
    FULL_NAME = (AppiumBy.ID, _PKG + "fullNameET")
    ADDRESS1 = (AppiumBy.ID, _PKG + "address1ET")
    CITY = (AppiumBy.ID, _PKG + "cityET")
    ZIP = (AppiumBy.ID, _PKG + "zipET")
    COUNTRY = (AppiumBy.ID, _PKG + "countryET")
    TO_PAYMENT = (AppiumBy.ACCESSIBILITY_ID, "Saves user info for checkout")
    # 주소 필드별 검증 에러
    FULLNAME_ERROR = (AppiumBy.ID, _PKG + "fullNameErrorTV")
    ADDRESS1_ERROR = (AppiumBy.ID, _PKG + "address1ErrorTV")
    CITY_ERROR = (AppiumBy.ID, _PKG + "cityErrorTV")
    ZIP_ERROR = (AppiumBy.ID, _PKG + "zipErrorTV")
    COUNTRY_ERROR = (AppiumBy.ID, _PKG + "countryErrorTV")

    # ── 결제수단 ──
    CARD_NAME = (AppiumBy.ID, _PKG + "nameET")
    CARD_NUMBER = (AppiumBy.ID, _PKG + "cardNumberET")
    EXPIRATION = (AppiumBy.ID, _PKG + "expirationDateET")
    CVV = (AppiumBy.ID, _PKG + "securityCodeET")
    REVIEW_ORDER = (AppiumBy.ACCESSIBILITY_ID, "Saves payment info and launches screen to review checkout data")

    # ── 주문검토 ──
    TOTAL_AMOUNT = (AppiumBy.ID, _PKG + "totalAmountTV")
    PLACE_ORDER = (AppiumBy.ACCESSIBILITY_ID, "Completes the process of checkout")

    # ── 주문완료 ──
    COMPLETE_MSG = (AppiumBy.ID, _PKG + "completeTV")          # "Checkout Complete"
    CONTINUE_SHOPPING = (AppiumBy.ACCESSIBILITY_ID, "Tap to open catalog")

    # ── 배송주소 ──
    def enter_shipping_address(self, full_name, address1, city, zip_code, country):
        self.input_text(self.FULL_NAME, full_name)
        self.input_text(self.ADDRESS1, address1)
        self.input_text(self.CITY, city)
        self.input_text(self.ZIP, zip_code)
        self.input_text(self.COUNTRY, country)
        self.hide_keyboard()

    def to_payment(self):
        self.click(self.TO_PAYMENT)

    def get_fullname_error(self) -> str:
        return self.get_text(self.FULLNAME_ERROR)

    def is_address_invalid(self) -> bool:
        """필수 미입력 시 이름 에러가 뜨는지로 판정."""
        return self.is_visible(self.FULLNAME_ERROR)

    # ── 결제수단 ──
    def enter_payment(self, card_name, card_number, expiration, cvv):
        self.input_text(self.CARD_NAME, card_name)
        self.input_text(self.CARD_NUMBER, card_number)
        self.input_text(self.EXPIRATION, expiration)
        self.input_text(self.CVV, cvv)
        self.hide_keyboard()

    def review_order(self):
        self.click(self.REVIEW_ORDER)

    # ── 주문검토 ──
    def get_total(self) -> str:
        return self.get_text(self.TOTAL_AMOUNT)

    def place_order(self):
        self.click(self.PLACE_ORDER)

    # ── 주문완료 ──
    def is_order_complete(self) -> bool:
        return self.text_present(self.COMPLETE_MSG, "Checkout Complete")
