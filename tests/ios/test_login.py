"""iOS 로그인 — 정상 계정 로그인 (POM + 명시적 대기).

참고: iOS는 Android와 달리 잠긴(locked) 계정이 없어 bob/alice/john 모두 정상
로그인된다. 따라서 별도의 네거티브(로그인 실패) 테스트는 작성하지 않는다.
"""
import allure
import pytest

from pages.ios.more_page import MorePage
from pages.ios.login_page import LoginPage
from config.test_data import IOS_VALID_USER


@allure.epic("SauceLabs My Demo App")
@allure.feature("Login")
@pytest.mark.ios
@pytest.mark.smoke
class TestLogin:
    @allure.story("정상 로그인")
    def test_valid_login(self, ios_driver):
        more = MorePage(ios_driver)

        # 1) More 탭 → 로그인 화면 진입
        with allure.step("More 탭에서 로그인 화면 열기"):
            more.go_to_login()

        # 2) 저장 계정(bob@example.com) 버튼 탭 후 로그인
        with allure.step("bob@example.com 계정으로 로그인"):
            LoginPage(ios_driver).login_as(IOS_VALID_USER[0])

        # 3) 로그인 성공 확인 (More 탭에 LogOut 메뉴 노출)
        with allure.step("로그인 상태 검증 (More에 LogOut 표시)"):
            assert more.is_logged_in(), "로그인 후 More 탭에 LogOut 메뉴가 보이지 않음"
