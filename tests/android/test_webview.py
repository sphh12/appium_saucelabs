"""WebView — 잘못된 URL 검증 (Tier 2)."""
import allure
import pytest

from pages.menu_page import MenuPage
from pages.webview_page import WebViewPage


@allure.epic("SauceLabs My Demo App")
@allure.feature("WebView")
@pytest.mark.android
@pytest.mark.regression
class TestWebView:
    @allure.title("HTTPS 아닌 URL → 에러 메시지")
    def test_invalid_url_shows_error(self, android_driver):
        MenuPage(android_driver).navigate_to("WebView")
        web = WebViewPage(android_driver)
        assert web.is_displayed(), "WebView 화면이 아님"
        web.enter_url("notaurl")
        web.tap_go()
        assert "https url" in web.get_url_error().lower(), \
            f"URL 검증 메시지 아님: {web.get_url_error()}"
