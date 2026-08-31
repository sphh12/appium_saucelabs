"""iOS POM 베이스 페이지.

명시적 대기 헬퍼(find/click/wait_*)는 `BasePage`를 그대로 재사용한다.
iOS는 하단 **탭바**(Catalog/Cart/More)로 네비게이션하므로 그 액션을 여기에 둔다.
(Android의 드로어 기반 헤더 액션과 다름)
"""
from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage


class IOSBasePage(BasePage):
    # 하단 탭바 (모든 화면 공통)
    CATALOG_TAB = (AppiumBy.ACCESSIBILITY_ID, "Catalog-tab-item")
    CART_TAB = (AppiumBy.ACCESSIBILITY_ID, "Cart-tab-item")
    MORE_TAB = (AppiumBy.ACCESSIBILITY_ID, "More-tab-item")

    def open_catalog_tab(self):
        self.click(self.CATALOG_TAB)

    def open_cart_tab(self):
        self.click(self.CART_TAB)

    def open_more_tab(self):
        self.click(self.MORE_TAB)
