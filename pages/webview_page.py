"""WebView 화면 — URL 입력 / HTTPS 검증."""
from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PKG = "com.saucelabs.mydemoapp.android:id/"


class WebViewPage(BasePage):
    TITLE = (AppiumBy.ID, _PKG + "webViewTV")        # "Webview"
    URL_INPUT = (AppiumBy.ID, _PKG + "urlET")
    GO_BUTTON = (AppiumBy.ID, _PKG + "goBtn")        # "Go To Site"
    URL_ERROR = (AppiumBy.ID, _PKG + "urlErrorTV")

    def is_displayed(self) -> bool:
        return self.is_visible(self.URL_INPUT)

    def enter_url(self, url: str):
        self.input_text(self.URL_INPUT, url)
        self.hide_keyboard()

    def tap_go(self):
        self.click(self.GO_BUTTON)

    def get_url_error(self) -> str:
        return self.get_text(self.URL_ERROR)

    def has_url_error(self) -> bool:
        return self.is_visible(self.URL_ERROR)
