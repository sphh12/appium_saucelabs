"""메뉴 드로어 — 로그아웃 / 앱 상태 리셋 (Tier 2)."""
import allure
import pytest

from utils.flows import login_as_valid_user, add_first_product_to_cart
from pages.menu_page import MenuPage


@allure.epic("SauceLabs My Demo App")
@allure.feature("Menu")
@pytest.mark.android
@pytest.mark.regression
class TestMenu:
    @allure.story("로그아웃")
    def test_logout(self, android_driver):
        # 로그인 상태 만들기 (담기 → 카트 → 체크아웃 → 정상 로그인, 공용 flow)
        login_as_valid_user(android_driver)
        menu = MenuPage(android_driver)
        menu.logout()
        assert menu.is_logged_out(), "로그아웃 후 'Log In'이 보이지 않음"

    @allure.story("앱 상태 리셋")
    def test_reset_app_state(self, android_driver):
        detail = add_first_product_to_cart(android_driver)
        assert detail.get_cart_badge_count() == 1
        MenuPage(android_driver).reset_app_state()
        assert detail.get_cart_badge_count() == 0, "리셋 후 카트가 비워지지 않음"
