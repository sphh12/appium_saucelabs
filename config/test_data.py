"""테스트 데이터·계정 중앙 관리 (config.test_data).

SauceLabs My Demo App의 **공개 데모** 계정·결제 데이터를 한 곳에 모은다.
테스트/페이지가 값을 하드코딩하지 않고 여기서 가져오도록 한다.

⚠️ 계정 이메일은 플랫폼별로 앱 실제값이 다름 (오타 아님 — 앱 자체가 다름):
   - Android 앱: bod@example.com (앱 자체 오타) · alice@example.com(잠긴 계정)
   - iOS 앱:     bob@example.com (정상) · alice/john/visual (잠긴 계정 없음)
모든 계정 공통 비밀번호: 10203040 (앱 로그인 화면에 그대로 노출되는 공개 데모 값).
"""

DEFAULT_PASSWORD = "10203040"

# (이메일, 비밀번호) 튜플
ANDROID_VALID_USER = ("bod@example.com", DEFAULT_PASSWORD)   # Android 정상 계정 (앱 오타 'bod')
ANDROID_LOCKED_USER = ("alice@example.com", DEFAULT_PASSWORD)  # Android 잠긴 계정
IOS_VALID_USER = ("bob@example.com", DEFAULT_PASSWORD)       # iOS 정상 계정

LOCKED_OUT_MESSAGE = "locked out"  # 잠긴 계정 에러 메시지 부분 문자열

# 체크아웃 배송 주소 (필수 필드)
SHIPPING = {
    "full_name": "John Doe",
    "address1": "123 Main St",
    "city": "Seoul",
    "zip_code": "12345",
    "country": "South Korea",
}

# 결제 카드 (테스트용 더미 — 실제 결제 없음)
PAYMENT = {
    "card_name": "John Doe",
    "card_number": "4111111111111111",
    "expiration": "0826",
    "cvv": "123",
}
