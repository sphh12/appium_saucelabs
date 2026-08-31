"""테스트 공용 네비게이션 헬퍼 (POM 조합).

여러 테스트에서 반복되는 '상품 담기 → 카트 → 로그인 게이트' 흐름을 재사용한다.
"""
from pages.products_page import ProductsPage
from pages.product_detail_page import ProductDetailPage
from pages.cart_page import CartPage
from pages.login_page import LoginPage


def add_first_product_to_cart(driver):
    """카탈로그 첫 상품을 카트에 담고 상세 페이지 객체를 반환."""
    products = ProductsPage(driver)
    assert products.is_displayed(), "카탈로그가 표시되지 않음"
    products.open_first_product()
    detail = ProductDetailPage(driver)
    assert detail.is_displayed(), "상품 상세가 표시되지 않음"
    detail.add_to_cart()
    return detail


def go_to_login(driver):
    """상품 담기 → 카트 → 결제 진행 → 로그인 화면 도달."""
    detail = add_first_product_to_cart(driver)
    detail.open_cart()
    cart = CartPage(driver)
    assert cart.is_displayed(), "장바구니가 표시되지 않음"
    cart.proceed_to_checkout()


def login_as_valid_user(driver):
    """로그인 게이트(체크아웃)까지 진행 후 정상 계정으로 로그인 완료.

    Android는 체크아웃 진행 시에만 로그인 화면이 노출되므로 담기→카트→결제진행이 선행된다.
    """
    go_to_login(driver)
    LoginPage(driver).login_with_valid_user()
