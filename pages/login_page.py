"""로그인 화면 (Login) — 정상/네거티브."""
from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PKG = "com.saucelabs.mydemoapp.android:id/"


class LoginPage(BasePage):
    USERNAME = (AppiumBy.ID, _PKG + "nameET")
    PASSWORD = (AppiumBy.ID, _PKG + "passwordET")
    LOGIN_BTN = (AppiumBy.ACCESSIBILITY_ID, "Tap to login with given credentials")
    # 화면에 노출된 저장 계정 (탭하면 자동완성)
    SAVED_USER_VALID = (AppiumBy.ID, _PKG + "username1TV")    # bod@example.com (정상)
    SAVED_USER_LOCKED = (AppiumBy.ID, _PKG + "username2TV")   # alice (locked out)
    SAVED_USER_VISUAL = (AppiumBy.ID, _PKG + "username3TV")   # visual
    # 에러 메시지
    USERNAME_ERROR = (AppiumBy.ID, _PKG + "nameErrorTV")
    PASSWORD_ERROR = (AppiumBy.ID, _PKG + "passwordErrorTV")

    def is_displayed(self) -> bool:
        return self.is_visible(self.LOGIN_BTN)

    def login(self, username: str, password: str):
        self.input_text(self.USERNAME, username)
        self.input_text(self.PASSWORD, password)
        self.hide_keyboard()
        self.click(self.LOGIN_BTN)

    def login_with_valid_user(self):
        """첫 저장 계정(bod@example.com / 10203040) 자동완성 후 로그인."""
        self.click(self.SAVED_USER_VALID)
        self.click(self.LOGIN_BTN)

    def tap_login(self):
        """입력 없이 로그인 버튼만 탭 (검증용)."""
        self.click(self.LOGIN_BTN)

    def get_username_error(self) -> str:
        return self.get_text(self.USERNAME_ERROR)

    def get_password_error(self) -> str:
        return self.get_text(self.PASSWORD_ERROR)
