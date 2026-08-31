"""상품 상세 — 수량/색상/별점평가 (Tier 1)."""
import allure
import pytest

from pages.products_page import ProductsPage
from pages.product_detail_page import ProductDetailPage


@allure.epic("SauceLabs My Demo App")
@allure.feature("Product Detail")
@pytest.mark.android
@pytest.mark.regression
class TestProductDetail:
    def _open_detail(self, driver) -> ProductDetailPage:
        products = ProductsPage(driver)
        assert products.is_displayed()
        products.open_first_product()
        detail = ProductDetailPage(driver)
        assert detail.is_displayed(), "상품 상세가 표시되지 않음"
        return detail

    @allure.story("수량 변경")
    def test_change_quantity(self, android_driver):
        detail = self._open_detail(android_driver)
        assert detail.get_quantity() == 1
        detail.increase_quantity()
        detail.increase_quantity()
        assert detail.get_quantity() == 3
        detail.decrease_quantity()
        assert detail.get_quantity() == 2

    @allure.story("색상 선택")
    def test_select_color(self, android_driver):
        # 참고: Android는 색상 선택상태가 UI에 깔끔히 노출되지 않아 선택상태를 직접 검증할 수 없다.
        #       (iOS는 is_color_selected로 검증 가능 — 플랫폼 차이)
        #       따라서 여기서는 '색상 선택 → 담기 → 배지 수량' 흐름으로만 검증한다.
        detail = self._open_detail(android_driver)
        assert detail.color_count() >= 1, "색상 옵션이 없음"
        if detail.color_count() > 1:
            detail.select_color_by_index(1)   # 다른 색상 선택
        detail.add_to_cart()
        assert detail.get_cart_badge_count() == 1

    @allure.story("별점 평가 제출")
    def test_rate_product(self, android_driver):
        detail = self._open_detail(android_driver)
        detail.rate_product(4)
        assert detail.is_review_submitted(), "리뷰 제출 다이얼로그가 표시되지 않음"
        detail.close_review()
