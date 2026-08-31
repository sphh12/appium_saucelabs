"""iOS About 화면 (About-screen)."""
from appium.webdriver.common.appiumby import AppiumBy

from pages.ios.base_ios_page import IOSBasePage


class AboutPage(IOSBasePage):
    SCREEN = (AppiumBy.ACCESSIBILITY_ID, "About-screen")
    WEBSITE_LINK = (AppiumBy.ACCESSIBILITY_ID, "Go to saucelabs.com")
    VERSION = (AppiumBy.IOS_PREDICATE, "label BEGINSWITH 'Demo App'")

    def is_displayed(self) -> bool:
        return self.is_visible(self.SCREEN)

    def has_website_link(self) -> bool:
        return self.is_visible(self.WEBSITE_LINK)

    def get_version_text(self) -> str:
        return self.get_text(self.VERSION)
