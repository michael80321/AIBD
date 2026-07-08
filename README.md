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

## Windows 每日 08:00 自動排程

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
