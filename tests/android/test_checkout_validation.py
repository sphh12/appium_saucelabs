"""체크아웃 배송주소 필드 검증 (Tier 1)."""
import allure
import pytest

from utils.flows import login_as_valid_user
from pages.checkout_page import CheckoutPage


@allure.epic("SauceLabs My Demo App")
@allure.feature("Checkout")
@allure.story("주소 검증")
@pytest.mark.android
@pytest.mark.regression
class TestCheckoutValidation:
    @allure.title("필수 필드 미입력 → 검증 에러")
    def test_address_required_field_errors(self, android_driver):
        # 담기 → 카트 → 결제진행 → 로그인 게이트 → 정상 로그인 (공용 flow)
        login_as_valid_user(android_driver)
        checkout = CheckoutPage(android_driver)
        # 입력 없이 To Payment → 필드 에러 표시되어야 함
        checkout.to_payment()
        assert checkout.is_address_invalid(), "주소 검증 에러가 표시되지 않음"
        assert checkout.get_fullname_error() == "Please provide your full name."
