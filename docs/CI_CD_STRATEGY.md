# CI/CD 전략 — 모바일 자동화 테스트

> 작성일: 2026-03-06 목적: GitHub Actions + Bitrise를 활용한 AOS/iOS 자동화 테스트 CI/CD 전략 정리
> **구현 상태(2026-08-27)**: 시나리오 A 의 Android 부분이 구현됐다 —
> `.github/workflows/android-regression.yml`. 사용법은 [CI_GUIDE.md](CI_GUIDE.md) 참고. iOS 는
> 미구현.

---

## 1. 전략 요약

```
1단계: GitHub Actions로 AOS/iOS 모두 시작
2단계: iOS 불안정 또는 무료 한도 부족 시 → Bitrise로 iOS 전환
```

---

## 2. 플랫폼별 실행 환경

### GitHub Actions

| 항목 | Android | iOS |
|------|---------|-----|
| **러너** | `ubuntu-latest` | `macos-latest` |
| **테스트 환경** | Android 에뮬레이터 (KVM 가속) | iOS 시뮬레이터 (Xcode 내장) |
| **Appium 드라이버** | UiAutomator2 | XCUITest |
| **안정성** | 높음 | 보통 (불안정 보고 있음) |
| **비용** | $0.008/분 | $0.08/분 (10배) |

### Bitrise (iOS 백업)

| 항목 | 내용 |
|------|------|
| **특징** | 모바일 CI/CD 전용 플랫폼 |
| **macOS 환경** | 기본 제공 (별도 설정 불필요) |
| **Appium 지원** | 네이티브 지원 |
| **iOS 안정성** | GitHub Actions 대비 높음 |

---

## 3. 무료 플랜 비교

| 플랫폼 | 무료 한도 | 과금 기준 | macOS (iOS) | 비고 |
|--------|----------|----------|:-----------:|------|
| **GitHub Actions** | Linux 2,000분 + macOS 200분/월 | 시간 기반 | O | 이미 GitHub 사용 중 |
| **Bitrise** | 200회/월, 빌드당 30분 | 횟수 기반 | O | 모바일 전용 |
| **CircleCI** | 80,000분/월 (크레딧) | 크레딧 기반 | O | 무료 한도 넉넉 |
| **Codemagic** | 500분/월 | 시간 기반 | O | Flutter 중심 |
| **GitLab CI** | 400분/월 | 시간 기반 | Self-hosted만 | iOS 제한적 |

### Bitrise 무료 플랜 상세

| 항목 | 한도 |
|------|------|
| 월 빌드 횟수 | 200회 |
| 빌드당 최대 시간 | 30분 |
| 동시 빌드 | 5개 |
| 빌드 타임아웃 | 90분 |

> **참고**: Bitrise는 횟수 기반이므로 여러 테스트 파일을 하나의 workflow에서 실행하면 1회만 차감됨.
> Appium 테스트 1건 ≈ 1~2분 기준, 한 빌드에 15~20개 테스트 실행 가능.

---

## 4. Linux에서 모바일 테스트 가능 여부

| 항목 | Linux | 비고 |
|------|:-----:|------|
| **Android 테스트** | O | Android SDK + 에뮬레이터 (KVM 가속, macOS/Windows보다 빠름) |
| **iOS 테스트** | X | Xcode가 macOS 전용이라 불가 |

GitHub Actions의 `ubuntu-latest` 러너는 Linux 기반이므로 Android 테스트만 가능.
iOS 테스트는 반드시 `macos-latest` 러너 또는 Bitrise 같은 macOS 환경 필요.

---

## 5. 실행 시나리오

### 시나리오 A: GitHub Actions 단독 (시작 단계)

```yaml
# .github/workflows/test.yml
jobs:
  android-test:
    runs-on: ubuntu-latest
    steps:
      - name: Start Android Emulator
      - name: Install Appium + UiAutomator2
      - name: Run AOS Tests
      - name: Upload Allure Report

  ios-test:
    runs-on: macos-latest
    steps:
      - name: Boot iOS Simulator
      - name: Install Appium + XCUITest
      - name: Run iOS Tests
      - name: Upload Allure Report
```

### 시나리오 B: GitHub Actions (AOS) + Bitrise (iOS)

iOS가 GitHub Actions에서 불안정하거나 macOS 분(200분) 소진 시:

- **Android** → GitHub Actions (`ubuntu-latest`) 유지
- **iOS** → Bitrise로 이전 (macOS 기본 제공, 200회/월)

---

## 6. 의사결정 기준

```
GitHub Actions iOS 테스트 실행
  ├── 안정적 + 한도 충분 → GitHub Actions 유지
  └── 불안정 또는 한도 부족
       └── Bitrise 무료 플랜으로 iOS 이전
            ├── 200회/월 충분 → Bitrise 유지
            └── 부족 → Self-hosted 러너 (집/회사 Mac) 또는 유료 검토
```

---

## 7. 참고 자료

- [Bitrise Plans & Pricing](https://bitrise.io/pricing)
- [Comparing the top 10 mobile CI/CD providers](https://www.runway.team/blog/comparing-the-top-10-mobile-ci-cd-providers)
- [Mobile CI/CD Tools: GitLab, TeamCity, CodeMagic, Github, Bitrise](https://www.repeato.app/mobile-ci-cd-tools/)
- [Can iOS Simulator from macOS GitHub Action runner be used for Appium?](https://discuss.appium.io/t/can-ios-simulator-from-macos-github-action-runner-be-used-for-appium/37734)
- [Running Appium tests with GitHub Actions](https://www.linkedin.com/pulse/running-appium-tests-github-actions-moataz-nabil)
- [How to Integrate Appium Testing with Jenkins, GitHub Actions & Azure DevOps](https://metadesignsolutions.com/how-to-integrate-appium-testing-with-jenkins-github-actions-azure-devops/)
