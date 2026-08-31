"""iOS More 탭 (메뉴) — 기능 네비게이션 / 로그인·로그아웃 / 앱 리셋.

각 메서드는 임의 탭에서 호출 가능 (먼저 More 탭을 연다).
"""
from appium.webdriver.common.appiumby import AppiumBy

from pages.ios.base_ios_page import IOSBasePage


class MorePage(IOSBasePage):
    WEBVIEW = (AppiumBy.ACCESSIBILITY_ID, "Webview-menu-item")
    QR_SCANNER = (AppiumBy.ACCESSIBILITY_ID, "QrCodeScanner-menu-item")
    GEO_LOCATION = (AppiumBy.ACCESSIBILITY_ID, "GeoLocation-menu-item")
    DRAWING = (AppiumBy.ACCESSIBILITY_ID, "Drawing-menu-item")
    ABOUT = (AppiumBy.ACCESSIBILITY_ID, "About-menu-item")
    CRASH = (AppiumBy.ACCESSIBILITY_ID, "CrashTheApp-menu-item")
    RESET = (AppiumBy.ACCESSIBILITY_ID, "ResetAppState-menu-item")
    BIOMETRICS = (AppiumBy.ACCESSIBILITY_ID, "Biometrics-menu-item")
    LOGIN_ENTRY = (AppiumBy.ACCESSIBILITY_ID, "Login Button")     # 로그아웃 상태
    LOGOUT_ITEM = (AppiumBy.ACCESSIBILITY_ID, "LogOut-menu-item")  # 로그인 상태
    # 리셋: 1차 확인 Alert → 2차 완료 Alert
    RESET_CONFIRM = (AppiumBy.ACCESSIBILITY_ID, "RESET APP")
    RESET_CANCEL = (AppiumBy.ACCESSIBILITY_ID, "CANCEL")
    RESET_DONE_OK = (AppiumBy.ACCESSIBILITY_ID, "OK")            # "App State has been reset." 확인

    def open(self):
        self.open_more_tab()

    def go_to_login(self):
        self.open()
        self.click(self.LOGIN_ENTRY)

    def go_to_about(self):
        self.open()
        self.click(self.ABOUT)

    def go_to_webview(self):
        self.open()
        self.click(self.WEBVIEW)

    def is_logged_in(self) -> bool:
        self.open()
        return self.is_visible(self.LOGOUT_ITEM)

    def is_logged_out(self) -> bool:
        self.open()
        return self.is_visible(self.LOGIN_ENTRY)

    def logout(self):
        """로그아웃 (확인 다이얼로그 없이 로그인 화면으로)."""
        self.open()
        self.click(self.LOGOUT_ITEM)

    def reset_app_state(self):
        """앱 리셋: More→Reset → 'Reset App State' Alert에서 RESET APP → '완료' Alert에서 OK."""
        self.open()
        self.click(self.RESET)
        self.click(self.RESET_CONFIRM)
        self.click(self.RESET_DONE_OK)   # 2차 Alert "App State has been reset." 닫기
