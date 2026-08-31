"""카탈로그 정렬 (Tier 1)."""
import allure
import pytest

from pages.products_page import ProductsPage


@allure.epic("SauceLabs My Demo App")
@allure.feature("Catalog")
@allure.story("정렬")
@pytest.mark.android
@pytest.mark.smoke
class TestCatalogSort:
    def test_sort_by_price_ascending(self, android_driver):
        products = ProductsPage(android_driver)
        assert products.is_displayed()
        products.sort_by(products.SORT_PRICE_ASC)
        prices = products.product_prices()
        allure.attach(str(prices), "가격(오름차순)", allure.attachment_type.TEXT)
        assert prices, "가격을 읽지 못함"
        assert prices == sorted(prices), f"가격 오름차순 정렬 아님: {prices}"

    def test_sort_by_price_descending(self, android_driver):
        products = ProductsPage(android_driver)
        assert products.is_displayed()
        products.sort_by(products.SORT_PRICE_DESC)
        prices = products.product_prices()
        allure.attach(str(prices), "가격(내림차순)", allure.attachment_type.TEXT)
        assert prices, "가격을 읽지 못함"
        assert prices == sorted(prices, reverse=True), f"가격 내림차순 정렬 아님: {prices}"
