"""로그인 네거티브 — 빈 값 / 잠긴 계정 (Tier 1)."""
import allure
import pytest

from utils.flows import go_to_login
from pages.login_page import LoginPage
from config.test_data import ANDROID_LOCKED_USER, LOCKED_OUT_MESSAGE


@allure.epic("SauceLabs My Demo App")
@allure.feature("Login")
@allure.story("네거티브")
@pytest.mark.android
@pytest.mark.regression
class TestLoginNegative:
    @allure.title("빈 자격증명 로그인 → 필수 입력 에러")
    def test_empty_credentials(self, android_driver):
        go_to_login(android_driver)
        login = LoginPage(android_driver)
        assert login.is_displayed()
        login.tap_login()
        assert login.get_username_error() == "Username is required"

    @allure.title("잠긴 계정(alice) 로그인 → 차단 메시지")
    def test_locked_out_user(self, android_driver):
        go_to_login(android_driver)
        login = LoginPage(android_driver)
        assert login.is_displayed()
        login.login(*ANDROID_LOCKED_USER)
        assert LOCKED_OUT_MESSAGE in login.get_password_error().lower(), \
            f"잠금 메시지 아님: {login.get_password_error()}"
