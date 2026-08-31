"""iOS 상품 상세 — 수량/색상/별점평가 (Tier 1)."""
import allure
import pytest

from utils import flows_ios


@allure.epic("SauceLabs My Demo App")
@allure.feature("Product Detail")
@pytest.mark.ios
@pytest.mark.regression
class TestProductDetail:
    @allure.story("수량 변경")
    def test_change_quantity(self, ios_driver):
        detail = flows_ios.open_first_product(ios_driver)
        with allure.step("초기 수량은 1"):
            assert detail.get_quantity() == 1, "초기 수량이 1이 아님"
        with allure.step("수량 2회 증가 → 3"):
            detail.increase_quantity()
            detail.increase_quantity()
            qty = detail.get_quantity()
            print(f"[DEBUG] 증가 후 수량: {qty}")  # 디버그용 출력
            assert qty == 3, "증가 후 수량이 3이 아님"
        with allure.step("수량 1회 감소 → 2"):
            detail.decrease_quantity()
            qty = detail.get_quantity()
            print(f"[DEBUG] 감소 후 수량: {qty}")  # 디버그용 출력
            assert qty == 2, "감소 후 수량이 2가 아님"

    @allure.story("색상 선택")
    def test_select_color(self, ios_driver):
        detail = flows_ios.open_first_product(ios_driver)
        with allure.step("색상(Blue) 선택 → 선택상태 검증"):
            detail.select_color("Blue")
            # 담기 전에 색상 선택상태(Selected 아이콘)가 반영됐는지 검증
            assert detail.is_color_selected("Blue"), "Blue 색상 선택상태가 반영되지 않음"
        with allure.step("장바구니에 담기"):
            detail.add_to_cart()
        with allure.step("장바구니 탭으로 이동"):
            cart = flows_ios.go_to_cart(ios_driver)
        with allure.step("장바구니에 상품이 담겼는지 확인"):
            has_items = cart.has_items()
            print(f"[DEBUG] 장바구니 상품 존재 여부: {has_items}")  # 디버그용 출력
            assert has_items, "색상 선택 후 담은 상품이 장바구니에 없음"

    @allure.story("별점 평가")
    def test_rate_product(self, ios_driver):
        detail = flows_ios.open_first_product(ios_driver)
        with allure.step("별점 부여 → 리뷰 제출 Alert"):
            detail.rate_product()
            submitted = detail.is_review_submitted()
            print(f"[DEBUG] 리뷰 제출 Alert 표시: {submitted}")  # 디버그용 출력
            assert submitted, "별점 후 'Thank you for submitting' Alert가 표시되지 않음"
        with allure.step("Alert 닫기"):
            detail.close_review()
