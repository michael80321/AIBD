---
description: 每日 BD Lead 搜尋與日報產出(AI / iGaming / 成人 / 賽事)
allowed-tools: WebSearch, WebFetch, Read, Write, Edit, Glob, Grep
---

# /bd-daily — 每日 BD 攻堅名單生成

嚴格依照以下流程執行。全程遵守 CLAUDE.md 的硬性規則:**每個 Lead 必附來源連結、不可捏造、寧缺勿濫**。

## 步驟 1:讀取設定與歷史

1. 讀 `CLAUDE.md`(公司背景、評分標準)。
2. 讀 `config/icp.md`(各行業買方訊號與打法)。
3. 讀 `config/search-queries.md`(搜尋模板與媒體清單)。
4. 讀 `leads/leads.csv` 全部歷史 Lead(去重依據)。
5. 讀 `config/exclusions.csv`(排除名單)。
6. 讀最近 1–2 份 `reports/*.md`,避免重複報導同一事件;並找出 7 天前後的舊 A 級 Lead,準備跟進提醒。

## 步驟 2:網路搜尋(核心)

- 對 **AI、iGaming、成人、賽事/體育** 四個行業,**每行業至少執行 8 組搜尋**(從 `config/search-queries.md` 的模板挑選/變化,並將日期佔位符替換為實際近期日期;可混用英/中/西語)。
- **另加至少 4 組「定向挖掘」搜尋**(不依賴新聞事件):展會參展商名單(SiGMA、SBC、G2E Asia、ICE)、行業名錄(白牌平台商、聚合商、成人平台目錄)、融資資料庫頁(Crunchbase、Dealroom、funding tracker)——見 `config/search-queries.md` 定向挖掘章節。
- **聚合商/平台商軌道(每日必掃 ≥1 組,最高槓桿)**:掃到任何**新的**遊戲聚合商、白牌平台商、OTT/串流方案商、AI 模型 API 市集——只要不在庫,一律入庫(綁一家帶整批下游)。新發現者同步更新 `config/targets-aggregators.md` 總表;A/B 級附開場訊息。
- **時間窗**:
  - **A 級訊號**:限近 7 天(「被 DDoS/宕機」限近 3 天)——不放寬。
  - **B 級訊號**:可放寬至近 14 天;名錄/展會/結構型標的不受時間窗限制,但須符合 ICP 且附名錄來源連結。
- 對有潛力的結果,用 WebFetch 讀原文確認細節(公司名、地區、事件時間),不可只憑搜尋摘要下結論。
- 優先掃 `config/search-queries.md` 列出的行業媒體。

## 步驟 3:評分與去重

對每個候選 Lead:

1. **去重**:公司名(含常見別名)已在 `leads/leads.csv` 或 `config/exclusions.csv` → 跳過;除非有重大新訊號(如新融資、被 DDoS),則可更新並在日報註明「舊 Lead 新訊號」。
2. **標注方案組合與城市**:依 CLAUDE.md 方案映射表為每筆 Lead 標 `solutions`(可談方案,分號分隔、按優先順序);`city` 標總部/決策人所在城市(不確定則留空或註「待查」)。記住 AI 線已放寬:有 LLM token 消耗即為有效標的(模型折扣線)。
3. **對照 ICP**(`config/icp.md` + CLAUDE.md 公司背景)判斷類型(客戶/合作夥伴/ISV)與評分:
   - **A**:明確買方訊號 + 符合 ICP(7 天內跟進)
   - **B**:符合 ICP 但訊號間接(2 週內跟進)
   - **C**:觀察,只入庫不進日報重點
3. 來源連結必須是實際搜到、可打開的 URL。**無來源 = 丟棄。**

## 步驟 4:產出

1. 依 `reports/_template.md` 寫 `reports/YYYY-MM-DD.md`(用今天日期):
   - **今日 5 件事**(行動清單置頂):先讀 `deals/deals.csv`——`next_date` 到期或階段停滯 >5 天的案子優先列入;其餘為 2–3 件跟進到期 + 新開發。**新開發至少含 1 件聚合商/平台商**(從 `config/targets-aggregators.md` 未接觸者輪替,或當日新發現者);每件一行寫明「找誰(公司/角色)、談什麼方案(依 solutions)、用什麼管道」;同城多家可打包時註明城市。簽約/上線案並提醒 cross-sell 下一方案。
   - A 級明細(每筆必含:公司、類型、行業、地區/城市、**可談方案組合**、預估月消費、訊號摘要、為何是現在、**具名決策人**(從融資新聞/官網/LinkedIn 查證真名與職稱;查不到則註明「待查」並給搜尋建議)、**三版可直接複製的開場訊息**(Email 含主旨行、LinkedIn ≤300 字、Telegram 口語短句;對象為華語公司用中文、否則英文)、**窗口挖掘指引**(見下)、來源連結)
   - **窗口挖掘指引**(每筆 A 級必附,教使用者去哪拿到聯絡方式):
     1. **官網 domain**:給出公司官網網址(從來源或搜尋確認);提示查 about/team/contact 頁
     2. **Email 格式猜測**:依 domain 給 3 種常見格式(`first@`、`first.last@`、`flast@`),提示用 Hunter.io / Apollo.io 驗證
     3. **該搜的精確職稱**(依 `config/roles.md` 該類別):列出「該搜職稱(含採購線)」與「一律避開(HR/Recruiter/Support/客服)」。
        - **若 country=中國/香港/台灣**:改用大陸版指引——「①企查查/天眼查查法人+高管姓名 → ②脈脈篩上述職稱 → ③IT桔子查投資方(阿里/螞蟻投資者標✅可引薦)→ ④微信成交;大陸別猜 email」。
        - **否則(國際)**:給 LinkedIn/Apollo 職稱字串 + email 格式猜測。
     4. **最佳渠道**:依 CLAUDE.md/playbook 對應(大陸 AI/短劇→阿里系引薦+脈脈+微信;國際 AI→LinkedIn+Apollo;iGaming/聚合商→官網 sales@+Telegram;成人→官網+Telegram 低調)
     5. **阿里系引薦路徑**:若該公司由阿里/螞蟻/阿里雲投資或領投,明確標「✅ 可走阿里投後/生態引薦」;否則標「—」
   - B 級表格(含方案欄)
   - 觀察中(C 級)
   - 統計 + 舊 A 級跟進提醒(7 天前的 A 級且 status 仍為 new)
2. 將所有新 Lead(含 C 級)**append** 到 `leads/leads.csv`,欄位:
   `date_added,company,vertical,type,region,city,country,signal,score,status,solutions,est_value,source_url,notes`
   - status 初始值 `new`;**country 填國家**(中國/香港/台灣/新加坡/馬來西亞/菲律賓/日本/韓國/美國/歐洲…,不確定填「待查」);city 填城市(不確定留空或註「待查」);solutions 依 CLAUDE.md 映射表(分號分隔);est_value 為預估月消費區間;含逗號的欄位用雙引號包住。儀表板支援「國家→城市」階層篩選。

## 步驟 4.5:每週日附加任務

1. **轉化復盤週報**:寫 `reports/weekly-YYYY-Wnn.md`——本週各狀態變化統計(從 leads.csv 的 notes 狀態軌跡彙整)、回覆率最高的訊號類型/行業、白費力氣的方向、下週搜尋配比調整建議、下週事件行事曆。
2. **C 級復活掃描**:從庫內 C 級挑 15–20 家(輪替,優先核心地區)以公司名做定向搜尋;有新訊號(融資/擴張/被攻擊/上市)者升級 B/A 並在日報「舊 Lead 新訊號」區列出。
3. **重生脈脈配方**:執行 `python3 scripts/gen_maimai.py` 重新生成 `reports/maimai-lookup.md`(全部中文客戶的脈脈搜尋職稱清單)。

## 步驟 5:更新儀表板與推送

1. 執行 `python3 scripts/build_dashboard.py` 重新生成 `docs/index.html` 與 `docs/artifact.html`。
2. **若有 Artifact 工具**(在 Claude Code 雲端/網頁 session 中):用 Artifact 工具發佈 `docs/artifact.html`,favicon 用 `📡`;若 `docs/ARTIFACT_URL.txt` 存在,傳入其中的 URL 更新同一頁面,不要另開新網址;首次發佈後把 URL 寫入 `docs/ARTIFACT_URL.txt` 並 commit。
3. 執行 `bash scripts/send-telegram.sh` 發送 Telegram 日報(未設定憑證時會自動跳過,不算錯誤)。
   - 若 `config/telegram.env` 不存在且環境變數未設(容器重建後會發生):檢查對話上下文中使用者先前提供的 Bot Token 與 Chat ID,若有則重建 `config/telegram.env`(該檔已在 .gitignore,**絕不 commit**)再執行。
   - 若 curl 回 403(代理政策封鎖 api.telegram.org):跳過並在最終回報中提醒使用者到環境設定放行該網域,不要重試繞過。
4. **若有 PushNotification 工具**:發送一行摘要推播,格式如:`BD日報 7/8:A級2筆 B級4筆|Top1: AIsa(阿里領投種子輪)`。
5. 將日報、leads.csv、docs/ 的變更 commit 並 push。

## 步驟 6:輸出統計

回報:各行業搜尋組數、候選數、去重丟棄數、最終 A/B/C 筆數、與目標(A 3–5、B 5–8)的差距。若未達標,說明原因(如當日訊號少),**不得湊數**。
