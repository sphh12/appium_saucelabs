"""About — 버전 표시 (Tier 2)."""
import allure
import pytest

from pages.menu_page import MenuPage
from pages.about_page import AboutPage


@allure.epic("SauceLabs My Demo App")
@allure.feature("About")
@pytest.mark.android
@pytest.mark.regression
class TestAbout:
    @allure.title("About 화면 버전 표시")
    def test_about_shows_version(self, android_driver):
        MenuPage(android_driver).navigate_to("About")
        about = AboutPage(android_driver)
        assert about.is_displayed(), "About 화면이 아님"
        version = about.get_version()
        allure.attach(version, "버전", allure.attachment_type.TEXT)
        assert version.strip().startswith("V."), f"버전 형식 예상과 다름: {version}"
