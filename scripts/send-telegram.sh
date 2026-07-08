#!/usr/bin/env bash
# 將當日 BD 日報摘要 + 全文檔案發送到 Telegram。
# 憑證來源(擇一):
#   1. 環境變數 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID(建議設在 Claude Code 環境設定)
#   2. config/telegram.env(KEY=VALUE 格式,已加入 .gitignore,不會被 commit)
# 用法: scripts/send-telegram.sh [報告路徑]  # 預設為 reports/<今天>.md
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -f "$ROOT/config/telegram.env" ] && . "$ROOT/config/telegram.env"

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "SKIP: 未設定 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID(環境變數或 config/telegram.env)" >&2
  exit 0
fi

TODAY="$(TZ=Asia/Taipei date +%F)"
REPORT="${1:-$ROOT/reports/$TODAY.md}"
if [ ! -f "$REPORT" ]; then
  echo "ERROR: 找不到日報 $REPORT" >&2
  exit 1
fi

API="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}"

# 雲端環境的網路政策可能封鎖 api.telegram.org;屆時由 GitHub Actions
# (.github/workflows/telegram-report.yml)在 push 後代發,此處優雅跳過。
if ! curl -sS --max-time 15 -o /dev/null "$API/getMe" 2>/dev/null; then
  echo "SKIP: 無法連線 api.telegram.org(網路政策封鎖),改由 GitHub Actions 於 push 後發送" >&2
  exit 0
fi

# 摘要:取「今日必打 Top 3」段落 + 統計行,純文字避免 Markdown 解析錯誤
SUMMARY="$(awk '/^## 🎯/,/^---/' "$REPORT" | grep -v '^---' | sed 's/[*#|]//g' | head -c 3500)"
STATS="$(grep -m1 '最終' "$REPORT" | sed 's/[*#-]//g' || true)"

curl -sS -X POST "$API/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=📡 BD 攻堅日報 ${TODAY}
${SUMMARY}
${STATS}" > /dev/null

# 附上完整日報檔
curl -sS -X POST "$API/sendDocument" \
  -F "chat_id=${TELEGRAM_CHAT_ID}" \
  -F "document=@${REPORT};filename=BD日報-${TODAY}.md" \
  -F "caption=完整日報(Markdown)" > /dev/null

echo "OK: 已發送 Telegram 日報(摘要 + 檔案)"
