"""iOS More 탭(메뉴) — 로그아웃 / 앱 상태 리셋 (POM + 명시적 대기)."""
import allure
import pytest

from utils import flows_ios
from pages.ios.more_page import MorePage


@allure.epic("SauceLabs My Demo App")
@allure.feature("Menu")
@pytest.mark.ios
@pytest.mark.regression
class TestMenu:
    @allure.story("로그아웃")
    def test_logout(self, ios_driver):
        more = MorePage(ios_driver)

        # 1) 먼저 로그인 상태로 만들기 (공용 flow)
        with allure.step("bob 계정으로 로그인"):
            flows_ios.login(ios_driver)
            assert more.is_logged_in(), "로그인 상태가 아님 (LogOut 메뉴 없음)"

        # 2) 로그아웃 → 로그아웃 상태 확인 (로그인 화면 / Login Button 노출)
        with allure.step("로그아웃 후 로그아웃 상태 검증"):
            more.logout()
            assert more.is_logged_out(), "로그아웃 후 Login Button이 보이지 않음"

    @allure.story("앱 상태 리셋")
    def test_reset_app_state(self, ios_driver):
        # 1) 상품 담기 (리셋 전 카트에 항목 존재, 공용 flow)
        with allure.step("첫 상품을 카트에 담기"):
            flows_ios.add_first_product_to_cart(ios_driver)

        # 2) More → Reset App State → 확인 Alert(RESET APP)
        with allure.step("More 탭에서 앱 상태 리셋"):
            MorePage(ios_driver).reset_app_state()

        # 3) 카트 이동 → 리셋으로 비워졌는지 확인
        with allure.step("리셋 후 카트가 비었는지 검증"):
            cart = flows_ios.go_to_cart(ios_driver)
            assert cart.is_empty(), "리셋 후 카트가 비워지지 않음"
