"""상품 상세 화면 (Product Details) — 색상/수량/별점평가/담기."""
from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PKG = "com.saucelabs.mydemoapp.android:id/"


class ProductDetailPage(BasePage):
    TITLE = (AppiumBy.ID, _PKG + "productTV")
    PRICE = (AppiumBy.ID, _PKG + "priceTV")
    ADD_TO_CART = (AppiumBy.ACCESSIBILITY_ID, "Tap to add product to cart")
    INCREASE_QTY = (AppiumBy.ACCESSIBILITY_ID, "Increase item quantity")
    DECREASE_QTY = (AppiumBy.ACCESSIBILITY_ID, "Decrease item quantity")
    QUANTITY = (AppiumBy.ID, _PKG + "noTV")
    COLOR_OPTIONS = (AppiumBy.ID, _PKG + "colorIV")   # 상품별 색상 (이름은 상품마다 다름)
    # 별점 탭 → 즉시 리뷰 제출 다이얼로그
    REVIEW_CLOSE = (AppiumBy.ACCESSIBILITY_ID, "Closes review dialog")   # "Continue"
    REVIEW_THANKYOU = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Thank you for submitting")',
    )

    def is_displayed(self) -> bool:
        return self.is_visible(self.ADD_TO_CART)

    def get_title(self) -> str:
        return self.get_text(self.TITLE)

    def get_price(self) -> str:
        return self.get_text(self.PRICE)

    def select_color(self, color: str):
        """color: Black | Blue | Gray | Green (상품에 해당 색상이 있을 때)."""
        self.click((AppiumBy.ACCESSIBILITY_ID, f"{color} color"))

    def color_count(self) -> int:
        return len(self.find_all(self.COLOR_OPTIONS))

    def select_color_by_index(self, index: int):
        """색상명에 의존하지 않고 N번째 색상 선택."""
        self.find_all(self.COLOR_OPTIONS)[index].click()

    def get_quantity(self) -> int:
        return int(self.get_text(self.QUANTITY))

    def increase_quantity(self):
        self.click(self.INCREASE_QTY)

    def decrease_quantity(self):
        self.click(self.DECREASE_QTY)

    def set_quantity(self, qty: int):
        for _ in range(max(0, qty - 1)):
            self.increase_quantity()

    def rate_product(self, stars: int):
        """1~5 별점 탭 (탭 즉시 리뷰가 제출됨)."""
        assert 1 <= stars <= 5
        self.click((AppiumBy.ID, _PKG + f"start{stars}IV"))

    def is_review_submitted(self) -> bool:
        return self.is_visible(self.REVIEW_THANKYOU)

    def close_review(self):
        self.click(self.REVIEW_CLOSE)

    def add_to_cart(self):
        self.click(self.ADD_TO_CART)
