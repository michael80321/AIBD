# BD 攻堅名單 — 每日 Lead 生成專案

雲端/CDN/主機服務商的每日 BD Lead 生成系統。純網路搜尋,產出 Markdown 日報。
目標行業:AI、iGaming(博彩)、成人、賽事/體育(含電競、串流)。

規則與評分標準見 [CLAUDE.md](CLAUDE.md),行業訊號與打法見 [config/icp.md](config/icp.md)。

## 使用方式

```
claude
> /bd-daily
```

產出:`reports/YYYY-MM-DD.md` 日報 + append 到 `leads/leads.csv`。

## 儀表板(每日一頁)

- 每次執行 `/bd-daily` 後,`scripts/build_dashboard.py` 會從 `leads/leads.csv` + `reports/*.md` 重新生成儀表板:
  - `docs/index.html` — 完整獨立頁面,雙擊即可本機開啟(也可架 GitHub Pages)
  - 雲端版發佈在 Claude Artifact,網址固定(見 `docs/ARTIFACT_URL.txt`),每天自動更新
- 內容:今日必打 A 級卡片 → A/B/C 統計 → 可篩選 Lead 資料庫(行業/評分/狀態/搜尋)→ 日報全文(近 14 天可切換)→ 跟進到期提醒

## Telegram 日報推送

1. 在 Telegram 找 **@BotFather** → `/newbot` 建立機器人,取得 **Bot Token**。
2. 跟你的新機器人說一句話,然後開 `https://api.telegram.org/bot<TOKEN>/getUpdates` 取得你的 **chat id**。
3. 憑證設定(擇一,勿 commit 到 repo):
   - Claude Code 環境設定中加環境變數 `TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`(建議,重啟不丟)
   - 或建 `config/telegram.env`(已在 .gitignore):
     ```
     TELEGRAM_BOT_TOKEN=123456:ABC...
     TELEGRAM_CHAT_ID=987654321
     ```
4. 每日流程會自動執行 `scripts/send-telegram.sh`:發送「今日必打 Top 3 + 統計」摘要,並附上完整日報 .md 檔;未設定憑證時自動跳過。

## 每日自動執行(雲端 Routine)

本專案已在 Claude Code 雲端 session 設定每日 Routine(台北時間 08:00),自動:
執行 `/bd-daily` 搜尋產出日報 → 重建儀表板並更新 Artifact 頁面 → 發送 Telegram 日報 → 手機推播一行摘要 → commit & push。
管理方式:在該 session 對 Claude 說「列出/暫停/刪除 routine」即可。

## Windows 每日 08:00 自動排程(備用方案)

以**系統管理員**開啟 PowerShell,執行(把路徑換成你的實際專案路徑):

```powershell
schtasks /Create /TN "BD-Daily-Leads" /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"C:\path\to\AIBD\scripts\run-daily.ps1\"" /SC DAILY /ST 08:00 /F
```

常用管理指令:

```powershell
schtasks /Run /TN "BD-Daily-Leads"      # 立刻手動執行一次(測試用)
schtasks /Query /TN "BD-Daily-Leads" /V # 查看排程狀態
schtasks /Delete /TN "BD-Daily-Leads" /F # 刪除排程
```

前置條件:

1. 已安裝 Claude Code CLI 且 `claude` 在 PATH 中(可在 PowerShell 執行 `claude --version` 驗證)。
2. `scripts/run-daily.ps1` 中透過 `claude -p "/bd-daily"` 以非互動模式執行,只開放 `WebSearch,WebFetch,Read,Write,Edit,Glob,Grep` 工具。
3. 執行紀錄寫在 `logs/run-daily.log`。

## 檔案結構

```
CLAUDE.md                    # 公司背景、Lead 類型、硬性規則、評分標準
.claude/commands/bd-daily.md # /bd-daily 流程定義
config/icp.md                # 各行業買方訊號 + 跟進打法
config/search-queries.md     # 搜尋模板 + 行業媒體清單
config/exclusions.csv        # 排除名單(現有客戶等,去重用)
reports/_template.md         # 日報模板
reports/YYYY-MM-DD.md        # 每日日報產出
leads/leads.csv              # 累積 Lead 資料庫(去重依據)
scripts/run-daily.ps1        # Windows 排程執行腳本
```

## 維護

- 成交/放棄的 Lead:更新 `leads/leads.csv` 的 `status`(new → contacted → won/lost/dropped)。
- 新增現有客戶或不想再看到的公司:加進 `config/exclusions.csv`。
- 調整搜尋方向:改 `config/search-queries.md`;調整評分口徑:改 `config/icp.md`。
