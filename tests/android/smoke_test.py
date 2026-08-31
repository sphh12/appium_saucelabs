"""SauceLabs My Demo App (네이티브 Android) 스모크 테스트.

앱 설치·실행 + 첫 화면(상품 카탈로그) 노출까지 검증.
POM(ProductsPage/BasePage) 기반 — locator는 페이지 객체에 위임(테스트 본문 raw 접근 제거).
실행: python tools/run_allure.py -- tests/android/smoke_test.py -v --platform=android
"""
import allure
import pytest

from pages.products_page import ProductsPage

APP_PACKAGE = "com.saucelabs.mydemoapp.android"


@allure.feature("Smoke")
@allure.story("App Launch")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.android
@pytest.mark.smoke
class TestSmoke:
    """앱 구동 + 첫 화면(상품 카탈로그) 스모크."""

    def test_app_launches(self, android_driver):
        """앱이 올바른 패키지로 포그라운드에 실행되는지 확인."""
        driver = android_driver
        with allure.step("현재 포그라운드 패키지 확인"):
            pkg = driver.current_package
            assert pkg == APP_PACKAGE, f"예상과 다른 패키지: {pkg}"

    def test_catalog_screen_loads(self, android_driver):
        """스플래시 후 상품 카탈로그 첫 화면이 정상 노출되는지 확인."""
        products = ProductsPage(android_driver)

        with allure.step("카탈로그 헤더('Products') 로드 확인"):
            assert products.is_displayed(), "상품 카탈로그 화면이 표시되지 않음"

        with allure.step("상품 목록에 상품이 1개 이상 표시되는지 확인"):
            assert products.product_count() > 0, "상품 목록이 비어있음"

        with allure.step("핵심 네비게이션(메뉴/장바구니) 노출 확인"):
            assert products.is_menu_visible(), "메뉴 버튼이 보이지 않음"
            assert products.is_cart_visible(), "장바구니 버튼이 보이지 않음"
