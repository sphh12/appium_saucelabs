"""장바구니 화면 (My Cart) — 수량변경/삭제/빈상태/결제."""
from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PKG = "com.saucelabs.mydemoapp.android:id/"


class CartPage(BasePage):
    TITLE = (AppiumBy.ID, _PKG + "productTV")            # text="My Cart"
    ITEM_TITLES = (AppiumBy.ID, _PKG + "titleTV")
    QUANTITY = (AppiumBy.ID, _PKG + "noTV")
    INCREASE_QTY = (AppiumBy.ACCESSIBILITY_ID, "Increase item quantity")
    DECREASE_QTY = (AppiumBy.ACCESSIBILITY_ID, "Decrease item quantity")
    ITEMS_COUNT = (AppiumBy.ID, _PKG + "itemsTV")        # "N Items"
    TOTAL_PRICE = (AppiumBy.ID, _PKG + "totalPriceTV")
    REMOVE_ITEM = (AppiumBy.ACCESSIBILITY_ID, "Removes product from cart")
    PROCEED_TO_CHECKOUT = (AppiumBy.ACCESSIBILITY_ID, "Confirms products for checkout")
    # 빈 카트 상태
    EMPTY_TITLE = (AppiumBy.ID, _PKG + "noItemTitleTV")  # "No Items"
    GO_SHOPPING = (AppiumBy.ID, _PKG + "shoppingBt")     # "Go Shopping"

    def is_displayed(self) -> bool:
        return self.text_present(self.TITLE, "My Cart")

    def item_count(self) -> int:
        try:
            return len(self.find_all(self.ITEM_TITLES, timeout=5))
        except Exception:
            return 0

    def has_product(self, name: str) -> bool:
        return self.is_visible(
            (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{name}")')
        )

    def get_quantity(self) -> int:
        return int(self.get_text(self.QUANTITY))

    def increase_quantity(self):
        self.click(self.INCREASE_QTY)

    def decrease_quantity(self):
        self.click(self.DECREASE_QTY)

    def get_items_count_text(self) -> str:
        return self.get_text(self.ITEMS_COUNT)

    def get_total(self) -> str:
        return self.get_text(self.TOTAL_PRICE)

    def remove_item(self):
        self.click(self.REMOVE_ITEM)

    def is_empty(self) -> bool:
        return self.text_present(self.EMPTY_TITLE, "No Items")

    def proceed_to_checkout(self):
        self.click(self.PROCEED_TO_CHECKOUT)
