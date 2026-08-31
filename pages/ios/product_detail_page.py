"""iOS 상품 상세 (ProductDetails-screen) — 색상/수량/별점/담기."""
from appium.webdriver.common.appiumby import AppiumBy

from pages.ios.base_ios_page import IOSBasePage


class ProductDetailPage(IOSBasePage):
    SCREEN = (AppiumBy.ACCESSIBILITY_ID, "ProductDetails-screen")
    PRICE = (AppiumBy.ACCESSIBILITY_ID, "Price")
    ADD_TO_CART = (AppiumBy.ACCESSIBILITY_ID, "AddToCart")
    INCREASE_QTY = (AppiumBy.ACCESSIBILITY_ID, "AddPlus Icons")
    DECREASE_QTY = (AppiumBy.ACCESSIBILITY_ID, "SubtractMinus Icons")
    QUANTITY = (AppiumBy.ACCESSIBILITY_ID, "Amount")             # label = 수량
    STARS_UNSELECTED = (AppiumBy.ACCESSIBILITY_ID, "StarUnSelected Icons")
    # 별 탭 → '리뷰 제출' Alert (Android과 동일 동작)
    REVIEW_THANKYOU = (AppiumBy.IOS_PREDICATE, "label CONTAINS 'Thank you for submitting'")
    REVIEW_OK = (AppiumBy.ACCESSIBILITY_ID, "OK")

    def is_displayed(self) -> bool:
        return self.is_visible(self.ADD_TO_CART)

    def get_quantity(self) -> int:
        return int(self.get_text(self.QUANTITY))

    def increase_quantity(self):
        self.click(self.INCREASE_QTY)

    def decrease_quantity(self):
        self.click(self.DECREASE_QTY)

    def select_color(self, color: str):
        """color: Black | Blue | Gray | Green (해당 색의 UnSelected 버튼을 탭하면 선택됨)."""
        self.click((AppiumBy.ACCESSIBILITY_ID, f"{color}ColorUnSelected Icons"))

    def is_color_selected(self, color: str) -> bool:
        """해당 색이 선택됨 여부. iOS는 버튼 이름이 선택돼도 계속 '...ColorUnSelected'라,
        선택 상태는 그 버튼의 `selected` 속성(=true)으로 판정한다. color: Black|Blue|Gray|Green"""
        try:
            el = self.find((AppiumBy.ACCESSIBILITY_ID, f"{color}ColorUnSelected Icons"),
                           timeout=self.SHORT_TIMEOUT)
            return el.get_attribute("selected") == "true"
        except Exception:
            return False

    def rate_product(self, stars: int = 4):
        """N번째 별을 탭해 별점 부여 → '리뷰 제출' Alert.

        선택/미선택 별이 섞이고 식별자가 같으므로 전체 별(name CONTAINS 'Star')을 순서대로
        모아 N번째를 탭한다. (StarUnSelected[0] 의존 제거 — 일부 선택 상태/빈 리스트 IndexError 방지)
        """
        assert 1 <= stars <= 5, "별점은 1~5"
        all_stars = self.find_all(
            (AppiumBy.IOS_CLASS_CHAIN, '**/XCUIElementTypeButton[`name CONTAINS "Star"`]')
        )
        if len(all_stars) < stars:
            raise AssertionError(f"별 버튼 {stars}개 필요, {len(all_stars)}개 발견 (UI 변경 점검)")
        all_stars[stars - 1].click()

    def is_review_submitted(self) -> bool:
        return self.is_visible(self.REVIEW_THANKYOU)

    def close_review(self):
        self.click(self.REVIEW_OK)

    def add_to_cart(self):
        self.click(self.ADD_TO_CART)
