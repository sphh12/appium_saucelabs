"""
Page Object Model - Base Page
모든 페이지 클래스의 기본 클래스.

설계 원칙:
- **명시적 대기(explicit wait)만 사용** — 모든 요소 접근은 WebDriverWait + expected_conditions
  기반. 테스트/페이지 코드에 `time.sleep` 금지(조건 기반 대기로 대체).
- implicit wait는 conftest에서 0으로 설정(explicit와 혼용 시 타임아웃이 꼬임).
- SauceLabs My Demo App 단일 앱 기준이라, 모든 화면 공통인 헤더(메뉴/카트) 액션을 여기 둠.
"""
import os

from appium.webdriver.webdriver import WebDriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


class BasePage:
    """기본 페이지 클래스 (명시적 대기 헬퍼 + 공통 헤더)."""

    DEFAULT_TIMEOUT = 15
    SHORT_TIMEOUT = 5    # 음성 단언·빠른 가시성 체크용 (요소 부재/미표시 확인)

    # 공통 헤더 (대부분 화면 상단)
    _MENU_ICON = (AppiumBy.ACCESSIBILITY_ID, "View menu")
    _CART_ICON = (AppiumBy.ACCESSIBILITY_ID, "View cart")
    _CART_BADGE = (AppiumBy.ID, "com.saucelabs.mydemoapp.android:id/cartTV")

    def __init__(self, driver: WebDriver, timeout: int = DEFAULT_TIMEOUT):
        self.driver = driver
        self.timeout = timeout

    # ── 명시적 대기 헬퍼 ──────────────────────────────────────────
    def _wait(self, timeout: int = None) -> WebDriverWait:
        return WebDriverWait(self.driver, timeout or self.timeout)

    def find(self, locator: tuple, timeout: int = None):
        """요소가 DOM에 존재할 때까지 대기 후 반환."""
        return self._wait(timeout).until(EC.presence_of_element_located(locator))

    def find_visible(self, locator: tuple, timeout: int = None):
        """요소가 화면에 보일 때까지 대기 후 반환."""
        return self._wait(timeout).until(EC.visibility_of_element_located(locator))

    def find_clickable(self, locator: tuple, timeout: int = None):
        """요소가 클릭 가능할 때까지 대기 후 반환."""
        return self._wait(timeout).until(EC.element_to_be_clickable(locator))

    def find_all(self, locator: tuple, timeout: int = None) -> list:
        """요소가 1개 이상 존재할 때까지 대기 후 전체 반환."""
        return self._wait(timeout).until(EC.presence_of_all_elements_located(locator))

    def _retry_on_stale(self, action, retries: int = 2):
        """StaleElementReferenceException 발생 시 locator로 재탐색·재시도.

        implicit_wait=0 이라 Selenium 자동 재탐색이 없어, 화면 재렌더(RecyclerView·
        카트 수량변경·iOS Alert dismiss 등)로 잡아둔 핸들이 무효화되면 한 번에 깨진다.
        action은 매 시도마다 find_*를 새로 호출하도록 작성(루프 내 새 핸들 확보).
        첫 시도 성공 시 기존 동작과 완전히 동일(투명).
        """
        last_exc = None
        for _ in range(retries + 1):
            try:
                return action()
            except StaleElementReferenceException as exc:
                last_exc = exc
        raise last_exc

    def click(self, locator: tuple, timeout: int = None):
        """클릭 가능 대기 후 클릭 (stale 시 재탐색 재시도)."""
        self._retry_on_stale(lambda: self.find_clickable(locator, timeout).click())

    def input_text(self, locator: tuple, text: str, timeout: int = None):
        """입력란 클릭 가능 대기 후 텍스트 입력(기존 값 제거, stale 시 재시도)."""
        def _do():
            element = self.find_clickable(locator, timeout)
            element.clear()
            element.send_keys(text)
        self._retry_on_stale(_do)

    def get_text(self, locator: tuple, timeout: int = None) -> str:
        """요소 텍스트 반환(존재 대기 포함, stale 시 재시도)."""
        return self._retry_on_stale(lambda: self.find(locator, timeout).text)

    def is_visible(self, locator: tuple, timeout: int = SHORT_TIMEOUT) -> bool:
        """요소가 (timeout 내) 화면에 보이는지 여부."""
        try:
            self.find_visible(locator, timeout)
            return True
        except TimeoutException:
            return False

    def is_invisible(self, locator: tuple, timeout: int = SHORT_TIMEOUT) -> bool:
        """요소가 (timeout 내) 사라지거나 없는지 — 음성 단언용(풀 타임아웃 회피)."""
        try:
            return bool(self._wait(timeout).until(EC.invisibility_of_element_located(locator)))
        except TimeoutException:
            return False

    def wait_until_invisible(self, locator: tuple, timeout: int = None) -> bool:
        """요소가 사라질 때까지 대기(예: 스플래시/로딩). 사라지면 True."""
        return self._wait(timeout).until(EC.invisibility_of_element_located(locator))

    def wait_for_text(self, locator: tuple, text: str, timeout: int = None) -> bool:
        """요소에 특정 텍스트가 나타날 때까지 대기(미충족 시 TimeoutException)."""
        return self._wait(timeout).until(EC.text_to_be_present_in_element(locator, text))

    def text_present(self, locator: tuple, text: str, timeout: int = None) -> bool:
        """요소에 특정 텍스트가 나타나는지 여부(bool). 타임아웃 시 예외 대신 False.

        화면/상태 확인용 is_* 메서드가 음성 케이스에서 예외(broken)가 아니라
        깔끔한 False(→ AssertionError=fail)를 반환하도록 하는 bool 계약 헬퍼.
        is_visible()과 동일한 계약(항상 bool 반환).
        """
        try:
            return bool(self.wait_for_text(locator, text, timeout))
        except TimeoutException:
            # 예외를 삼키면 리포트에 남는 건 AssertionError뿐이라 '무엇을 못 찾았는지'가
            # 사라진다. 사유를 로그로 남겨 첨부된 page_source와 대조할 단서를 남긴다.
            print(f"[text_present] 타임아웃 — {locator}에서 '{text}' 미확인")
            return False

    # ── 제스처 ────────────────────────────────────────────────────
    def swipe_up(self):
        size = self.driver.get_window_size()
        x = size["width"] // 2
        self.driver.swipe(x, int(size["height"] * 0.8), x, int(size["height"] * 0.2), 800)

    def swipe_down(self):
        size = self.driver.get_window_size()
        x = size["width"] // 2
        self.driver.swipe(x, int(size["height"] * 0.2), x, int(size["height"] * 0.8), 800)

    def go_back(self):
        self.driver.back()

    def hide_keyboard(self):
        """키보드 숨김. 실패는 삼키지 않고 디버그 출력 — 미해제 시 다음 클릭이 가려질 수 있어 가시화."""
        try:
            self.driver.hide_keyboard()
        except Exception as exc:
            print(f"[hide_keyboard] 무시: {exc}")

    def take_screenshot(self, filename: str):
        os.makedirs("reports", exist_ok=True)
        self.driver.save_screenshot(f"reports/{filename}.png")

    # ── 공통 헤더 액션 ────────────────────────────────────────────
    def open_menu(self):
        """헤더의 메뉴(드로어) 열기."""
        self.click(self._MENU_ICON)

    def open_cart(self):
        """헤더의 장바구니 열기."""
        self.click(self._CART_ICON)

    def is_menu_visible(self) -> bool:
        """헤더 메뉴 아이콘 노출 여부 — 테스트가 private locator에 직접 접근하지 않도록 제공."""
        return self.is_visible(self._MENU_ICON)

    def is_cart_visible(self) -> bool:
        """헤더 장바구니 아이콘 노출 여부."""
        return self.is_visible(self._CART_ICON)

    def get_cart_badge_count(self) -> int:
        """장바구니 배지 수량. 배지가 없으면 0."""
        try:
            return int(self.find(self._CART_BADGE, timeout=self.SHORT_TIMEOUT).text)
        except (TimeoutException, ValueError):
            return 0
