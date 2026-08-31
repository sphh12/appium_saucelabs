"""iOS 로그인 — 저장 계정 버튼 탭 방식 (타이핑 불필요).

iOS 계정: bob@example.com(정상) / alice / john / visual@example.com.
(Android와 달리 잠긴 계정 없음 — alice도 정상 로그인됨)
"""
from appium.webdriver.common.appiumby import AppiumBy

from pages.ios.base_ios_page import IOSBasePage


class LoginPage(IOSBasePage):
    VALID_USER = (AppiumBy.ACCESSIBILITY_ID, "bob@example.com")
    # 'Login' 은 StaticText/Button 둘 다라 Button만 특정
    LOGIN_BTN = (AppiumBy.IOS_CLASS_CHAIN, '**/XCUIElementTypeButton[`name == "Login"`]')

    def is_displayed(self) -> bool:
        return self.is_visible(self.VALID_USER)

    def select_user(self, email: str):
        self.click((AppiumBy.ACCESSIBILITY_ID, email))

    def tap_login(self):
        self.click(self.LOGIN_BTN)

    def login_as(self, email: str = "bob@example.com"):
        """저장 계정 버튼 탭(자동완성) 후 로그인."""
        self.select_user(email)
        self.tap_login()
