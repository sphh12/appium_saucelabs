"""iOS 상품 카탈로그 — 상품 목록 표시 (Tier 1)."""
import allure
import pytest

from pages.ios.catalog_page import CatalogPage


@allure.epic("SauceLabs My Demo App")
@allure.feature("Catalog")
@pytest.mark.ios
@pytest.mark.smoke
class TestCatalog:
    @allure.story("상품 목록 표시")
    def test_catalog_displays_products(self, ios_driver):
        catalog = CatalogPage(ios_driver)
        with allure.step("카탈로그 화면이 표시되는지 확인"):
            assert catalog.is_displayed(), "카탈로그 화면이 표시되지 않음"
        with allure.step("상품이 1개 이상 노출되는지 확인"):
            count = catalog.product_count()
            print(f"[DEBUG] 카탈로그 상품 수: {count}")  # 디버그용 출력
            assert count >= 1, "카탈로그에 상품이 없음"
