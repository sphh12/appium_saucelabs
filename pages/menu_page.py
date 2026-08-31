"""메뉴 드로어 (Menu) — 네비게이션 / 로그아웃 / 앱 리셋.

각 메서드는 '드로어가 닫힌 상태'에서 호출하는 것을 전제로 한다.
"""
from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PKG = "com.saucelabs.mydemoapp.android:id/"


class MenuPage(BasePage):
    MENU_LIST = (AppiumBy.ID, _PKG + "menuRV")
    LOG_OUT_ITEM = (AppiumBy.ACCESSIBILITY_ID, "Logout Menu Item")
    LOG_IN_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Log In")')
    # 로그아웃 확인 다이얼로그 (표준 AlertDialog)
    DIALOG_CONFIRM = (AppiumBy.ID, "android:id/button1")   # "LOGOUT"
    DIALOG_CANCEL = (AppiumBy.ID, "android:id/button2")    # "CANCEL"

    @staticmethod
    def _item(text):
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{text}")')

    def navigate_to(self, item_text: str):
        """드로어를 열고 메뉴 항목을 탭한다."""
        self.open_menu()
        self.click(self._item(item_text))

    def is_logged_in(self) -> bool:
        """드로어에 'Log Out'이 보이면 로그인 상태."""
        self.open_menu()
        return self.is_visible(self.LOG_OUT_ITEM)

    def is_logged_out(self) -> bool:
        self.open_menu()
        return self.is_visible(self.LOG_IN_TEXT)

    def logout(self):
        """드로어 → Log Out → 확인 다이얼로그 LOGOUT."""
        self.open_menu()
        self.click(self.LOG_OUT_ITEM)
        self.click(self.DIALOG_CONFIRM)

    def reset_app_state(self):
        self.navigate_to("Reset App State")
