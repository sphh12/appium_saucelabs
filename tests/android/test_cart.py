"""장바구니 — 수량 변경 / 항목 삭제·빈 카트 (Tier 1)."""
import allure
import pytest

from utils.flows import add_first_product_to_cart
from pages.cart_page import CartPage


def _money(s: str) -> float:
    """'$ 29.99' / '$29.99' 류 문자열에서 금액만 추출해 float로 파싱."""
    cleaned = "".join(ch for ch in s if ch.isdigit() or ch == ".")
    return round(float(cleaned), 2)


@allure.epic("SauceLabs My Demo App")
@allure.feature("Cart")
@pytest.mark.android
@pytest.mark.regression
class TestCart:
    @allure.story("수량 변경")
    def test_change_quantity_updates_count(self, android_driver):
        detail = add_first_product_to_cart(android_driver)
        detail.open_cart()
        cart = CartPage(android_driver)
        assert cart.is_displayed()
        assert cart.get_quantity() == 1
        t1 = _money(cart.get_total())   # 증가 전 합계
        cart.increase_quantity()
        assert cart.get_quantity() == 2
        assert "2" in cart.get_items_count_text(), f"항목 수 텍스트 불일치: {cart.get_items_count_text()}"
        t2 = _money(cart.get_total())   # 증가 후 합계
        # 수량 2배 → 합계도 2배
        assert t2 == round(t1 * 2, 2), f"수량 2배 시 합계 불일치: t1={t1}, t2={t2}"

    @allure.story("항목 삭제 → 빈 카트")
    def test_remove_item_shows_empty_cart(self, android_driver):
        detail = add_first_product_to_cart(android_driver)
        detail.open_cart()
        cart = CartPage(android_driver)
        assert cart.is_displayed()
        cart.remove_item()
        assert cart.is_empty(), "빈 카트 상태(No Items)가 아님"
        assert cart.is_visible(cart.GO_SHOPPING), "'Go Shopping' 버튼이 없음"
