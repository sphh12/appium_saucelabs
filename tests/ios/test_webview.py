"""iOS WebView — 잘못된 URL 검증 (Tier 2).

⚠️ 현재 SKIP — iOS 소프트 키보드 환경 이슈(Xcode 26.5):
   URL 입력 시 타이핑이 필요한데, 소프트 키보드가 버튼을 가리고 입력을 오염시켜 자동화 불가.
   키보드 환경 이슈 해결 후 구현한다.

진입: MorePage(d).go_to_webview() (구현되어 있음).
"""
import allure
import pytest


@allure.epic("SauceLabs My Demo App")
@allure.feature("WebView")
@allure.story("URL 검증")
@pytest.mark.ios
@pytest.mark.skip(reason="iOS soft keyboard env blocker (Xcode 26.5): URL 입력 타이핑 필요")
class TestWebView:
    def test_invalid_url_shows_error(self, ios_driver):
        """키보드 환경 이슈 해결 후 구현 (잘못된 URL 입력 → 에러 메시지 검증)."""
        # 구현 스케치 (키보드 이슈 해결 후 활성화):
        # 1. MorePage(d).go_to_webview()  ← WebView 화면 진입 (메서드 존재함)
        # 2. URL 입력란에 잘못된 값 타이핑  ← 키보드 이슈 지점
        # 3. Go 탭 → "https url" 류 에러 메시지 검증
        pytest.skip("iOS soft keyboard env blocker (Xcode 26.5)")
