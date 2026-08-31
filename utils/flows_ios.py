"""iOS 테스트 공용 네비게이션 헬퍼 (POM 조합) — Android `utils/flows.py`의 iOS 대응.

iOS는 하단 탭바(Catalog/Cart/More) 기반이라 Android와 진입 경로가 다르다.
여러 iOS 테스트에서 반복되던 '담기 / 로그인 / 체크아웃 진입' 시퀀스를 캡슐화한다.
"""
from pages.ios.catalog_page import CatalogPage
from pages.ios.product_detail_page import ProductDetailPage
from pages.ios.cart_page import CartPage
from pages.ios.login_page import LoginPage
from pages.ios.more_page import MorePage
from config import test_data


def open_first_product(driver) -> ProductDetailPage:
    """카탈로그 → 첫 상품 → 상세 진입 후 ProductDetailPage 반환."""
    catalog = CatalogPage(driver)
    assert catalog.is_displayed(), "카탈로그가 표시되지 않음"
    catalog.open_first_product()
    detail = ProductDetailPage(driver)
    assert detail.is_displayed(), "상품 상세가 표시되지 않음"
    return detail


def add_first_product_to_cart(driver) -> ProductDetailPage:
    """첫 상품을 카트에 담고 상세 페이지 객체 반환."""
    detail = open_first_product(driver)
    detail.add_to_cart()
    return detail


def login(driver, email: str = test_data.IOS_VALID_USER[0]):
    """More → Login → 저장계정 버튼 로그인 (타이핑 불필요)."""
    MorePage(driver).go_to_login()
    LoginPage(driver).login_as(email)


def go_to_cart(driver) -> CartPage:
    """카트 탭으로 이동 후 CartPage 반환."""
    cart = CartPage(driver)
    cart.open_cart_tab()
    return cart


def go_to_checkout(driver):
    """로그인 → 담기 → 카트 → 결제 진행 (체크아웃 배송주소 화면 도달)."""
    login(driver)
    add_first_product_to_cart(driver)
    go_to_cart(driver).proceed_to_checkout()
