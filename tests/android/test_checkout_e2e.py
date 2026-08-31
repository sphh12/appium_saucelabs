"""
E2E: 핵심 구매 해피패스 (로그인 → 카탈로그 → 상품 → 카트 → 체크아웃 → 주문완료).

POM(Page Object Model) + 명시적 대기 기반.
- 각 화면 동작은 pages/*.py 페이지 클래스에 캡슐화.
- 대기는 BasePage의 explicit wait 헬퍼로 처리(time.sleep 미사용).
"""
import allure
import pytest

from utils import flows
from pages.cart_page import CartPage
from pages.login_page import LoginPage
from pages.checkout_page import CheckoutPage
from config.test_data import SHIPPING, PAYMENT

# 배송비 (주문 합계 = 상품가 + 배송비)
SHIPPING_FEE = 5.99


def _money(s: str) -> float:
    """'$ 29.99' / '$29.99' 류 문자열에서 금액만 추출해 float로 파싱."""
    cleaned = "".join(ch for ch in s if ch.isdigit() or ch == ".")
    return round(float(cleaned), 2)


@allure.epic("SauceLabs My Demo App")
@allure.feature("Checkout")
@allure.story("구매 해피패스 E2E")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.android
@pytest.mark.e2e
class TestCheckoutE2E:
    def test_complete_purchase(self, android_driver):
        """상품을 골라 카트에 담고, 로그인 후 결제까지 완료한다."""
        driver = android_driver
        cart = CartPage(driver)
        login = LoginPage(driver)
        checkout = CheckoutPage(driver)

        with allure.step("1~3. 첫 상품 담기 (공용 flow) + 가격/배지 확인"):
            detail = flows.add_first_product_to_cart(driver)
            price = _money(detail.get_price())   # 주문 합계 검증용 상품가 캡처
            print(f"[debug] product = {detail.get_title()} / {detail.get_price()}")
            assert detail.get_cart_badge_count() == 1, "카트 배지 수량이 1이 아님"

        with allure.step("4. 장바구니 열기 + 담긴 상품 확인"):
            detail.open_cart()
            assert cart.is_displayed(), "장바구니(My Cart) 화면이 아님"
            assert cart.item_count() >= 1, "장바구니가 비어 있음"

        with allure.step("5. 결제 진행 → 로그인 게이트"):
            cart.proceed_to_checkout()
            assert login.is_displayed(), "로그인 화면이 표시되지 않음"
            login.login_with_valid_user()

        with allure.step("6. 배송 주소 입력 → 결제수단으로"):
            checkout.enter_shipping_address(**SHIPPING)
            checkout.to_payment()

        with allure.step("7. 결제수단 입력 → 주문검토로"):
            checkout.enter_payment(**PAYMENT)
            checkout.review_order()

        with allure.step("8. 주문 검토 → 합계 검증 → 주문하기"):
            total_text = checkout.get_total()
            allure.attach(total_text, "주문 합계", allure.attachment_type.TEXT)
            print(f"[debug] order total = {total_text}")
            total = _money(total_text)
            # 주문 합계 == 상품가 + 배송비($5.99)
            assert total == round(price + SHIPPING_FEE, 2), \
                f"주문 합계 불일치: total={total}, price={price}, fee={SHIPPING_FEE}"
            checkout.place_order()

        with allure.step("9. 주문완료(Checkout Complete) 확인"):
            assert checkout.is_order_complete(), "주문완료 화면이 표시되지 않음"
