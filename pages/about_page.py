"""About 화면 — 버전 / 웹사이트 / SNS."""
from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

_PKG = "com.saucelabs.mydemoapp.android:id/"


class AboutPage(BasePage):
    TITLE = (AppiumBy.ID, _PKG + "aboutTV")          # "About"
    VERSION = (AppiumBy.ID, _PKG + "versionTV")      # 예: "V.2.2.0-build 25"
    WEBSITE_LINK = (AppiumBy.ID, _PKG + "webTV")

    def is_displayed(self) -> bool:
        return self.text_present(self.TITLE, "About")

    def get_version(self) -> str:
        return self.get_text(self.VERSION)
