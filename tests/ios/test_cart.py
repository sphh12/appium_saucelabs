"""iOS 장바구니 — 항목 삭제 → 빈 카트 (POM + 명시적 대기)."""
import allure
import pytest

from utils import flows_ios


@allure.epic("SauceLabs My Demo App")
@allure.feature("Cart")
@pytest.mark.ios
@pytest.mark.regression
class TestCart:
    @allure.story("항목 삭제 → 빈 카트")
    def test_remove_item_empties_cart(self, ios_driver):
        # 1) 상품 담기: 카탈로그 첫 상품 → 상세 → AddToCart (공용 flow)
        with allure.step("첫 상품을 카트에 담기"):
            flows_ios.add_first_product_to_cart(ios_driver)

        # 2) 하단 탭바로 카트 이동
        with allure.step("카트 탭 열기"):
            cart = flows_ios.go_to_cart(ios_driver)
            assert cart.is_displayed(), "카트 화면이 표시되지 않음"

        # 3) 항목 존재 확인 → 삭제 → 빈 카트 확인
        with allure.step("항목 삭제 후 빈 카트 확인"):
            assert cart.has_items(), "카트에 담긴 항목이 없음"
            cart.remove_item()
            assert cart.is_empty(), "항목 삭제 후 빈 카트(No Items) 상태가 아님"
