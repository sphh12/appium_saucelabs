"""iOS 체크아웃 배송주소 필드 검증 (Tier 1).

빈 상태로 To Payment → "Validation Error!" Alert 검증.
(타이핑이 없어 소프트 키보드 이슈 없이 자동화 가능)
"""
import allure
import pytest

from utils import flows_ios
from pages.ios.checkout_page import CheckoutPage


@allure.epic("SauceLabs My Demo App")
@allure.feature("Checkout")
@allure.story("주소 검증")
@pytest.mark.ios
@pytest.mark.regression
class TestCheckoutValidation:
    @allure.title("필수 필드 미입력 → 검증 에러 Alert")
    def test_address_validation_error(self, ios_driver):
        d = ios_driver

        with allure.step("1~3. 로그인 → 첫 상품 담기 → 카트 → 결제 진행 (공용 flow)"):
            flows_ios.go_to_checkout(d)

        with allure.step("4. 체크아웃(배송주소) 화면 진입 확인"):
            checkout = CheckoutPage(d)
            assert checkout.is_displayed(), "체크아웃(배송주소) 화면이 표시되지 않음"

        with allure.step("5. 빈 상태로 To Payment → 검증 에러 Alert"):
            checkout.tap_to_payment()
            assert checkout.has_validation_error(), "Validation Error! Alert가 표시되지 않음"
            msg = checkout.get_validation_message()
            print(f"[DEBUG] 검증 메시지: {msg}")  # 디버그용 출력
            assert "provide" in msg.lower(), f"검증 메시지에 'provide' 없음: {msg}"
