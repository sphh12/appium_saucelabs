"""iOS 상품 카탈로그 (탭: Catalog)."""
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException

from pages.ios.base_ios_page import IOSBasePage


class CatalogPage(IOSBasePage):
    PRODUCT_IMAGES = (AppiumBy.ACCESSIBILITY_ID, "Product Image")   # clickable → 상세
    PRODUCT_NAMES = (AppiumBy.ACCESSIBILITY_ID, "Product Name")

    def is_displayed(self) -> bool:
        return self.is_visible(self.PRODUCT_IMAGES)

    def product_count(self) -> int:
        """상품 개수. 빈 목록이면 예외(broken) 대신 0 반환 — Android ProductsPage와 동일 계약."""
        try:
            return len(self.find_all(self.PRODUCT_IMAGES))
        except TimeoutException:
            return 0

    def open_first_product(self):
        """첫 상품 상세로 진입 (clickable 대기 + stale 재시도, raw element 접근 회피)."""
        self.click(self.PRODUCT_IMAGES)
