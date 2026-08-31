# Appium MCP 설정 (tools/mcp/)

이 폴더는 공식 [appium/appium-mcp](https://github.com/appium/appium-mcp) 서버를
이 프로젝트와 연결하기 위한 설정 자산을 담고 있습니다.

> 전체 설정 절차는 **[docs/MCP_SETUP_GUIDE.md](../../docs/MCP_SETUP_GUIDE.md)** 를 참고하세요.

## 파일 구성

| 파일 | 설명 |
|------|------|
| `generate_capabilities.py` | 프로젝트 `.env` + `apps/` 폴더를 읽어 `capabilities.json` 자동 생성 |
| `capabilities.json` | (자동 생성) appium-mcp 가 읽는 디바이스/앱 설정 — gitignore 권장 |
| `samples/claude-desktop.example.json` | Cowork / Claude Desktop / Cursor 용 JSON 설정 샘플 |
| `samples/claude-code-add.sh` | Claude Code CLI 등록 스크립트 (macOS/Linux) |
| `samples/claude-code-add.ps1` | Claude Code CLI 등록 스크립트 (Windows PowerShell) |

## 빠른 시작

```bash
# 1. 사전 점검
python tools/mcp/generate_capabilities.py --verify

# 2. capabilities.json 생성
python tools/mcp/generate_capabilities.py

# 3-A. Claude Code 사용 시 (한 줄 등록)
bash tools/mcp/samples/claude-code-add.sh           # macOS/Linux
.\tools\mcp\samples\claude-code-add.ps1              # Windows PowerShell

# 3-B. Cowork / Claude Desktop 사용 시
# samples/claude-desktop.example.json 참고하여 설정 파일에 병합
```

> SauceLabs My Demo App은 단일 환경입니다. 머신을 옮기거나 앱 파일이 바뀌면 `capabilities.json`만 다시 생성하면 됩니다.
