"""iOS 장바구니 (Cart-screen) — 수량/삭제/빈상태/결제진행."""
from appium.webdriver.common.appiumby import AppiumBy

from pages.ios.base_ios_page import IOSBasePage


class CartPage(IOSBasePage):
    SCREEN = (AppiumBy.ACCESSIBILITY_ID, "Cart-screen")
    EMPTY_TITLE = (AppiumBy.ACCESSIBILITY_ID, "No Items")
    GO_SHOPPING = (AppiumBy.ACCESSIBILITY_ID, "GoShopping")
    REMOVE_ITEM = (AppiumBy.ACCESSIBILITY_ID, "Remove Item")
    PROCEED = (AppiumBy.ACCESSIBILITY_ID, "ProceedToCheckout")
    INCREASE_QTY = (AppiumBy.ACCESSIBILITY_ID, "AddPlus Icons")
    DECREASE_QTY = (AppiumBy.ACCESSIBILITY_ID, "SubtractMinus Icons")

    def is_displayed(self) -> bool:
        return self.is_visible(self.SCREEN)

    def has_items(self) -> bool:
        return self.is_visible(self.PROCEED, timeout=5)

    def is_empty(self) -> bool:
        return self.is_visible(self.EMPTY_TITLE, timeout=5)

    def remove_item(self):
        self.click(self.REMOVE_ITEM)

    def increase_quantity(self):
        self.click(self.INCREASE_QTY)

    def proceed_to_checkout(self):
        self.click(self.PROCEED)
