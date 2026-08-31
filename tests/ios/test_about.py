"""iOS About — 화면/웹사이트 링크/버전 표시 (Tier 2)."""
import re

import allure
import pytest

from pages.ios.more_page import MorePage
from pages.ios.about_page import AboutPage


@allure.epic("SauceLabs My Demo App")
@allure.feature("About")
@allure.story("About 화면 표시")
@pytest.mark.ios
@pytest.mark.regression
class TestAbout:
    @allure.title("About 화면 — 링크/버전 표시")
    def test_about_screen(self, ios_driver):
        d = ios_driver

        with allure.step("1. More → About 진입"):
            MorePage(d).go_to_about()

        with allure.step("2. About 화면 표시 확인"):
            about = AboutPage(d)
            assert about.is_displayed(), "About 화면이 표시되지 않음"

        with allure.step("3. 웹사이트 링크 노출 확인"):
            assert about.has_website_link(), "saucelabs.com 링크가 표시되지 않음"

        with allure.step("4. 버전 텍스트 확인"):
            v = about.get_version_text()
            print(f"[DEBUG] 버전: {v}")  # 디버그용 출력
            allure.attach(v, "버전", allure.attachment_type.TEXT)
            # 로케이터('label BEGINSWITH Demo App')와 독립적으로 버전 표기를 검증한다.
            # (기존 '"Demo App" in v'는 로케이터 조건과 동어반복이라 사실상 항상 통과했음)
            # 실제 화면 텍스트는 'Demo App V.01 by ...' 라서 'x.y' 숫자 패턴이 없다(CI 실측).
            # Android 쪽 단언(startswith("V."))과 같은 규약으로 'V.' + 숫자를 본다.
            assert re.search(r"V\.\s*\d+", v), f"버전 표기(V.nn)가 없음: {v}"
