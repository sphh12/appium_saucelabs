# Git 푸시 규칙 (Git Push Rules)

이 문서는 코드를 Git 저장소에 푸시할 때 준수해야 할 규칙을 정리합니다.

---

## 1. 기본 푸시 정책

기본적으로 **GitHub origin 단일 푸시**를 진행합니다.

```bash
# 기본 푸시
git push origin <branch>

# 첫 푸시 (upstream 설정)
git push -u origin <branch>
```

> 향후 다른 원격 저장소(GitLab 등)를 추가할 경우 별도로 명시하여 푸시.

---

## 2. 저장소 유형별 보안 정책

### Private 저장소 (개인/팀 전용)

| 항목 | 필수 여부 | 설명 |
|------|-----------|------|
| 민감정보 제거 | **선택** | 접근 권한이 제한되므로 민감정보 포함 가능 |
| 환경변수 분리 | 권장 | 관리 편의성을 위해 권장하나 필수 아님 |
| .gitignore 설정 | 권장 | APK, 빌드 산출물 등 제외 권장 |

### Public 저장소 (공개 - 포트폴리오용 기본)

| 항목 | 필수 여부 | 설명 |
|------|-----------|------|
| 민감정보 제거 | **필수** | 누구나 접근 가능하므로 반드시 제거 |
| 환경변수 분리 | **필수** | 모든 민감정보는 환경변수로 처리 |
| .gitignore 설정 | **필수** | `.env`, APK, UI 덤프 등 반드시 제외 |
| .env.example 제공 | **필수** | 설정 방법 안내를 위한 템플릿 필수 |

> **중요**: Public 저장소에 민감정보가 한 번이라도 커밋되면, 히스토리에 영구 기록됩니다.
> 삭제 후에도 복구 가능하므로 **푸시 전 반드시 확인**하세요.

---

## 3. 민감정보 분류

### Public 저장소에서 반드시 제거해야 할 항목

| 항목 | 예시 | 처리 방법 |
|------|------|-----------|
| 테스트 계정 ID | `test_user@example.com` | 환경변수 (`TEST_USERNAME`) |
| 테스트 비밀번호/PIN | `password123` | 환경변수 (`TEST_PASSWORD`) |
| API 키/토큰 | `sk-xxxx`, `token_xxxx` 등 모든 자격증명 | 환경변수 사용 |
| 실제 `.env` 파일 | `.env`, `.env.local` | `.gitignore`에 추가 |

### 주의가 필요한 항목

| 항목 | 설명 | 권장 조치 |
|------|------|-----------|
| 디바이스 UDID | 실물 기기 시리얼 | 환경변수 `ANDROID_UDID` |
| UI 덤프 파일 | `ui_dumps/*.xml` | `.gitignore`에 추가 |
| 앱 파일 | 앱 빌드 산출물 | `.gitignore`에 추가 (`apps/`) |

---

## 4. Public 저장소용 .gitignore 필수 항목

```gitignore
# 환경변수 (민감정보)
.env
.env.local
.env.*.local
!.env.example

# 앱 파일 (SauceLabs 자산)
apps/
*.apk
*.ipa

# UI 덤프 (앱 구조 정보 포함)
ui_dumps/

# Appium 세션 파일
*.appiumsession
```

---

## 5. 환경변수 체크리스트 (Public 저장소 필수)

푸시 전 아래 항목들이 코드에 하드코딩되어 있지 않은지 확인:

- [ ] 테스트 계정/비밀번호 — 코드에 하드코딩 금지
- [ ] API 키/토큰 (외부 서비스 자격증명 전반)
- [ ] `ANDROID_UDID` - 실물 디바이스 시리얼
- [ ] `APPIUM_HOST` / `APPIUM_PORT` - Appium 서버 주소 (선택)
- [ ] 앱 파일이 `apps/` 폴더 외부에 노출되지 않는지 확인

---

## 6. Public 저장소 푸시 전 검증 명령어

```bash
# 민감정보 검색 (계정명, 비밀번호 등)
git diff --cached | grep -iE "password|secret|token|api_key|bearer"

# 실제 이메일 주소 노출 검색
git diff --cached | grep -iE "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# .env 파일이 스테이징되었는지 확인
git status | grep "\.env"

# 추적되면 안 되는 파일 확인
git ls-files | grep -E "\.env$|\.apk$|ui_dumps/"

# AI(claude) 흔적 검색 — 커밋 메시지/주석에서 제거 (16장 참고)
git diff --cached | grep -i "claude"
```

---

## 7. 코드 작성 규칙 (Public 저장소용)

### 올바른 환경변수 사용 패턴

```python
import os
from dotenv import load_dotenv

load_dotenv()

# 민감정보: 기본값 없이 환경변수 필수
API_TOKEN = os.getenv("EXTERNAL_API_TOKEN", "")

# 설정값: 기본값 허용 (단, 실제 값 대신 합리적 기본값)
APPIUM_HOST = os.getenv("APPIUM_HOST", "127.0.0.1")
APPIUM_PORT = int(os.getenv("APPIUM_PORT", "4723"))
```

### 잘못된 예시 (Public 저장소 금지)

```python
# BAD: 하드코딩된 민감정보
USERNAME = "real_test_user@example.com"
PASSWORD = "real_password123"
API_TOKEN = "sk_live_actual_token_xxx"
```

---

## 8. 커밋 메시지 규칙

### 기본 형식

```
<type>: <파일/기능1> - <변경내용> / <파일/기능2> - <변경내용>

<한글 상세 설명>
- 변경사항 1
- 변경사항 2
```

### Type 종류

| Type | 설명 |
|------|------|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `refactor` | 코드 리팩토링 |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 설정 변경 |
| `style` | 코드 포맷팅 |

### 예시

```
feat: conftest.py - 환경변수 지원 추가 / .env.example - 템플릿 생성 / .gitignore - 민감정보 제외

민감정보 환경변수 분리
- 테스트 계정 환경변수화
- .env.example 템플릿 파일 추가
- .gitignore 업데이트 (민감정보 보호)
```

```
fix: test_login.py - 타임아웃 증가 / conftest.py - 딜레이 추가

로그인 테스트 간헐적 실패 수정
- WebDriverWait 타임아웃 10초 → 15초 증가
- 보안 키보드 입력 후 딜레이 추가
```

```
docs: GIT_RULES.md - 푸시 규칙 문서 작성

Git 푸시 규칙 문서 작성
- Private/Public 저장소별 보안 정책 정리
- 민감정보 처리 가이드라인 작성
- 커밋 메시지 작성 규칙 추가
```

### 규칙

1. **제목**: `<파일/기능(영문)> - <변경내용(한글)>` 형식, 여러 파일은 `/`로 구분
2. **본문**: 한글 상세 설명, 변경 이유와 내용 포함
3. **빈 줄**: 제목과 본문 사이에 빈 줄 필수
4. **'claude' 흔적 금지**: 커밋 메시지(제목·본문)에 `claude` / `Co-Authored-By: Claude` / `Generated with Claude Code` 등 AI 도구 흔적을 넣지 않는다 (상세 및 주석 포함 규칙은 16장 참고)

---

## 9. 긴급 조치 (Public 저장소에 민감정보 노출 시)

만약 민감정보가 실수로 커밋된 경우:

```bash
# 1. 즉시 해당 파일 삭제 후 새 커밋
git rm --cached <파일명>
git commit -m "fix: 민감정보 포함 파일 제거"

# 2. 히스토리에서 완전 삭제 (주의: 협업 시 팀원 동기화 필요)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch <파일명>" \
  --prune-empty --tag-name-filter cat -- --all

# 3. 원격 강제 푸시
git push origin --force --all

# 4. 민감정보 즉시 변경 (비밀번호, API 키 등)
# - 노출된 계정 비밀번호 변경
# - 노출된 API 키 재발급
```

> **경고**: Public 저장소에 노출된 민감정보는 이미 복제되었을 수 있습니다.
> 히스토리 삭제와 함께 **반드시 해당 민감정보를 변경**하세요.

---

## 10. 원격 브랜치 상태 확인

원격 저장소의 브랜치 상태를 확인할 때는 **반드시 fetch 후 확인**해야 합니다.

### 주의사항

`git branch -a` 명령어는 로컬에 캐시된 원격 브랜치 정보만 표시합니다.
실제 원격 저장소의 최신 상태와 다를 수 있습니다.

### 올바른 확인 방법

```bash
# 1. 원격 저장소에서 최신 정보 가져오기
git fetch origin

# 2. 원격 브랜치 목록 확인
git branch -a

# 3. 로컬 vs 원격 비교
git log HEAD..origin/main --oneline   # pull 필요한 커밋
git log origin/main..HEAD --oneline   # push 필요한 커밋
```

### 잘못된 예시

```bash
# BAD: fetch 없이 바로 확인 (오래된 정보일 수 있음)
git branch -a
```

> **주의**: fetch 없이 `git branch -a`를 실행하면 원격에 새로 생성된 브랜치가
> 보이지 않거나, 이미 삭제된 브랜치가 여전히 표시될 수 있습니다.

---

## 11. Example 파일 동기화

원본 파일과 템플릿(example) 파일이 함께 존재하는 경우, **원본 파일의 구조 변경 시 example 파일에도 반영**해야 합니다.

### 대상 파일

| 원본 파일 | 템플릿 파일 | 설명 |
|-----------|-------------|------|
| `.env` | `.env.example` | 환경변수 설정 |

### 규칙

1. **구조 변경 시 동기화 필수**
   - 새 환경변수 추가 → example에도 추가 (플레이스홀더 값으로)
   - 환경변수 삭제 → example에서도 삭제
   - 변수명 변경 → example에서도 변경

2. **값은 동기화하지 않음**
   - 원본: 실제 민감정보 값
   - example: 플레이스홀더 값 (`your_username`, `sk_xxxxx` 등)

### 체크리스트

- [ ] `.env` 구조 변경 시 `.env.example`도 수정
- [ ] 새 환경변수는 example에 설명 주석과 함께 추가
- [ ] example 파일은 Git에 커밋 (원본은 .gitignore)

---

## 12. CHANGELOG.md 작업 추적

프로젝트의 변경 이력과 작업 현황을 `CHANGELOG.md` 단일 파일에서 관리합니다.
(2026-08-24 통합 — 구 `change_notes.md` + `Todo.md`. Todo 원본은 `archive/TODO-2026.md`에 보존)

### 파일 위치

```
프로젝트루트/CHANGELOG.md
```

### 구조 (Keep a Changelog 형식 참고)

| 섹션 | 역할 |
|------|------|
| `## [Unreleased]` | 미완료 할일 (최상단, 구 Todo.md 역할). 체크박스 `- [ ]`로 표기 |
| `## YYYY-MM-DD` | 날짜별 완료 이력 (최신이 위, 구 change_notes.md 역할) |

### 작성 규칙

1. **할일 추가**: `[Unreleased]`에 `- [ ]` 체크박스로 추가 (우선순위순)
2. **작업 완료 시**: `[Unreleased]`에서 항목을 제거하고, 해당 날짜 섹션에 작업 내용을 기록
   - 신규 기록은 `### Added` / `### Changed` / `### Fixed`로 분류 (통합 이전 이력은 원문 유지)
3. **새 날짜 작업**: `[Unreleased]` 바로 아래에 새 날짜 섹션 생성 (역순 유지)
4. **진행 중 표기**: `[Unreleased]` 항목에 `(진행 중: N/M단계)` 부기

---

## 13. ui_dumps 로그 파일 푸시 정책

`ui_dumps/` 폴더의 XML, 스크린샷 등 로그 파일은 **저장소 유형에 따라 처리 방식이 다릅니다.**

### Private 저장소

- `ui_dumps/` 로그 파일을 **Git에 포함하여 푸시 가능**
- 팀 내부에서 UI 분석, 디버깅 이력 공유에 유용하므로 포함 권장

### Public 저장소 (포트폴리오 기본)

- `ui_dumps/` 로그 파일을 **반드시 제외**
- 앱 구조 정보, 화면 요소 정보가 포함되어 있으므로 `.gitignore`에 추가 필수

```gitignore
# Public 저장소 전용 - ui_dumps 제외
ui_dumps/
```

> **요약**: Public 저장소(포트폴리오)에는 `ui_dumps/`를 제외하고, Private 저장소에서는 자유롭게 포함하여 푸시합니다.

---

## 14. 저장소 공개 상태 자동 판별 및 푸시 정책

### 판별 방법

푸시 전 `gh repo view` 명령어로 저장소 공개 상태를 자동 확인한다.

```bash
# 저장소 공개 여부 확인
gh repo view --json isPrivate --jq '.isPrivate'
# true → Private / false → Public
```

### Private 저장소 푸시 정책

Private 저장소일 경우 **민감정보를 그대로 포함하여 푸시**한다.

| 항목 | 처리 |
|------|------|
| 환경변수 (.env) | 그대로 커밋/푸시 허용 |
| APK 파일 | 그대로 커밋/푸시 허용 |
| 테스트 계정/PIN | 하드코딩 허용 |
| API 키/토큰 | 그대로 커밋/푸시 허용 |
| .gitignore 민감정보 제외 | 불필요 |

### Public 저장소 푸시 정책

Public 저장소일 경우 **민감정보를 반드시 제외**하고 푸시한다.

| 항목 | 처리 |
|------|------|
| 환경변수 (.env) | `.gitignore`에 추가하여 제외 |
| APK 파일 | `.gitignore`에 추가하여 제외 |
| 테스트 계정/PIN | 환경변수로 분리, 하드코딩 제거 |
| API 키/토큰 | 환경변수로 분리, `.gitignore`에 제외 |
| .env.example | 템플릿 파일 필수 제공 |

### 자동 처리 흐름

```
푸시 요청 ("푸시" 트리거)
  │
  ├─ gh repo view --json isPrivate
  │
  ├─ Private (true)
  │   └─ 민감정보 스캔 건너뜀
  │   └─ 그대로 커밋/푸시 진행
  │
  └─ Public (false)
      └─ 민감정보 스캔 실행 (섹션 6 검증 명령어)
      └─ .gitignore에 민감 파일 추가
      │   - .env, .env.local, .env.*.local
      │   - *.apk, *.ipa, apps/
      │   - ui_dumps/
      └─ 하드코딩된 민감정보 발견 시 경고 후 중단
      └─ 문제 없으면 커밋/푸시 진행
```

---

## 요약

| 저장소 유형 | 민감정보 처리 | 환경변수 분리 | .gitignore | ui_dumps |
|-------------|---------------|---------------|------------|----------|
| **Private** | 그대로 허용 | 선택 | 선택 | **포함 가능** |
| **Public** | **필수 제거** | **필수** | **필수** | **제외 필수** |

---

## 15. Claude 메모리 파일 동기화

Claude의 메모리 파일을 프로젝트 내 `.claude/memory/`에 복사하여 Git으로 관리할 수 있습니다.

### 파일 위치

| 원본 (로컬) | 프로젝트 내 복사본 |
|-------------|-------------------|
| `~/.claude/projects/<프로젝트경로>/memory/` | `.claude/memory/` |

### 관리 대상 파일 (예시)

| 파일 | 내용 |
|------|------|
| `MEMORY.md` | 메모리 인덱스 |
| `user_profile.md` | 사용자 프로필 |
| `triggers.md` | 키워드 트리거 + 자동 실행 규칙 |
| `git_rules.md` | Git 규칙 요약 |

### 동기화 규칙

1. **푸시 시 자동 동기화**: Git Push 트리거 실행 시, 원본 메모리 파일을 `.claude/memory/`에 복사 후 커밋에 포함
2. **새 환경에서 클론 시**: `.claude/memory/` 파일이 있으므로 컨텍스트 유지 가능
3. **Private 저장소에서만 추적**: 메모리 파일에 민감한 설정 정보가 포함될 수 있으므로 Public 저장소에서는 제외

---

## 16. 커밋·주석 'claude' 흔적 제거 (커밋/푸시 전 필수)

커밋 및 푸시 **직전**, **커밋 메시지와 변경 파일의 코드 주석**에 `claude`(대소문자 무관)가 포함되면 **모두 제거**한다. (포트폴리오 공개 저장소에 AI 도구 흔적이 노출되지 않도록)

### 제거 대상

| 위치 | 제거 대상 예시 |
|------|----------------|
| 커밋 메시지 (제목·본문) | `Co-Authored-By: Claude ...`, `🤖 Generated with Claude Code`, 그 외 `claude` 언급 일체 |
| 코드 주석 (`#`, `//`, `<!-- -->`, docstring 등) | `claude`를 언급하는 주석 → 삭제하거나 AI/도구 언급 없는 일반 설명으로 치환 |

### 검사 방법 (커밋 전 필수)

```bash
# 1) 스테이징된 변경(코드 주석 포함)에서 claude 검색
git diff --cached | grep -i "claude"

# 2) 작성한 커밋 메시지에서 claude 검색
echo "$COMMIT_MSG" | grep -i "claude"   # 또는 메시지 파일에 grep -i claude
```

→ 둘 중 하나라도 검출되면 **해당 내용을 제거한 뒤** 커밋/푸시한다. 검출 **0건**이어야 진행.

### 예외 — 기능 코드의 `claude`는 유지

`claude`가 **실제 기능**이면 제거 대상이 아니다 (제거 시 동작이 깨짐):
- Claude Code **CLI 명령** (`claude mcp add` / `claude mcp list` 등 — `tools/mcp/reconnect.sh`, `tools/mcp/samples/claude-code-add.sh`) 및 그 CLI 사용을 설명하는 주석
- **API 모델명·엔드포인트** (`claude-sonnet-4-6`, `api.anthropic.com` 등 — 기능 코드가 실제로 호출하는 식별자)

즉 이 규칙은 **AI 작성자 흔적(`Co-Authored-By`, "Generated with Claude Code" 등)과 부수적 언급 주석**만 대상으로 하며, 기능 식별자/명령은 유지한다.

> 이 규칙은 본 프로젝트 전용이며, 전역 설정(`~/.claude/CLAUDE.md`)이나 도구 기본값의 **AI 공동작성자 태그 자동 추가 동작보다 우선**한다. 즉, 이 저장소의 커밋에는 `Co-Authored-By: Claude` 류를 붙이지 않는다.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-14 | SauceLabs SMDA 프로젝트용으로 GIT_RULES.md 재작성 (이전 프로젝트 특화 내용 제거, 단일 origin 푸시 정책) |
| 2026-06-20 | 16장 추가 — 커밋/푸시 전 커밋 메시지·코드 주석의 'claude' 흔적 제거 (기능 코드=claude CLI·API 모델명은 예외, 전역 AI 공동작성자 태그보다 우선). 부수적 주석 정리(session_recorder·upload_to_dashboard) |
