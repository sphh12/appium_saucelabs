"""상품 카탈로그 화면 (Products) + 정렬."""
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException

from pages.base_page import BasePage

_PKG = "com.saucelabs.mydemoapp.android:id/"


class ProductsPage(BasePage):
    TITLE = (AppiumBy.ID, _PKG + "productTV")            # text="Products"
    PRODUCT_LIST = (AppiumBy.ID, _PKG + "productRV")
    PRODUCT_IMAGES = (AppiumBy.ID, _PKG + "productIV")   # 상품별 (clickable)
    PRODUCT_TITLES = (AppiumBy.ID, _PKG + "titleTV")
    PRODUCT_PRICES = (AppiumBy.ID, _PKG + "priceTV")
    SORT_BUTTON = (AppiumBy.ID, _PKG + "sortIV")
    # 정렬 시트 옵션 (accessibility id)
    SORT_NAME_ASC = (AppiumBy.ACCESSIBILITY_ID, "Ascending order by name")
    SORT_NAME_DESC = (AppiumBy.ACCESSIBILITY_ID, "Descending order by name")
    SORT_PRICE_ASC = (AppiumBy.ACCESSIBILITY_ID, "Ascending order by price")
    SORT_PRICE_DESC = (AppiumBy.ACCESSIBILITY_ID, "Descending order by price")

    def is_displayed(self) -> bool:
        return self.text_present(self.TITLE, "Products")

    def product_count(self) -> int:
        """상품 개수. 빈 목록이면 예외(broken) 대신 0 반환 — text_present()와 같은 bool 계약."""
        try:
            return len(self.find_all(self.PRODUCT_IMAGES))
        except TimeoutException:
            return 0

    def open_first_product(self):
        """첫 상품 상세로 진입 (clickable 대기 + stale 재시도)."""
        self.click(self.PRODUCT_IMAGES)

    # ── 정렬 ──
    def open_sort(self):
        self.click(self.SORT_BUTTON)

    def sort_by(self, option_locator):
        """정렬 시트를 열고 옵션을 선택한다."""
        self.open_sort()
        self.click(option_locator)

    def product_prices(self) -> list:
        """가격을 float 리스트로 반환 ('$ 7.99' → 7.99)."""
        prices = []
        for el in self.find_all(self.PRODUCT_PRICES):
            txt = el.text.replace("$", "").replace(",", "").strip()
            try:
                prices.append(float(txt))
            except ValueError:
                pass
        return prices

    def first_product_title(self) -> str:
        return self.find_all(self.PRODUCT_TITLES)[0].text
