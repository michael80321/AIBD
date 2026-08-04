#!/usr/bin/env python3
"""從 leads/leads.csv 與 reports/*.md 生成 BD 儀表板。

輸出:
  docs/index.html    — 完整獨立頁面(可本機開啟或架 GitHub Pages)
  docs/artifact.html — 內容片段(給 Claude Artifact 發佈用,不含 doctype/html/head/body)
"""
import csv
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MAX_EMBEDDED_REPORTS = 14

SCORE_ORDER = {"A": 0, "B": 1, "C": 2}
VERTICALS = ["AI", "iGaming", "成人", "賽事"]


def load_leads():
    path = ROOT / "leads" / "leads.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("company") or "").strip()]
    rows.sort(key=lambda r: (r.get("date_added", ""), SCORE_ORDER.get(r.get("score", "C"), 3)))
    rows.reverse()
    return rows


def load_reports():
    rep_dir = ROOT / "reports"
    out = []
    if rep_dir.exists():
        for p in sorted(rep_dir.glob("*.md"), reverse=True):
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.stem):
                out.append({"date": p.stem, "md": p.read_text(encoding="utf-8")})
    return out[:MAX_EMBEDDED_REPORTS]


def build(leads, reports):
    taipei = timezone(timedelta(hours=8))
    now = datetime.now(taipei)
    latest_date = reports[0]["date"] if reports else (leads[0]["date_added"] if leads else now.strftime("%Y-%m-%d"))

    today_rows = [r for r in leads if r["date_added"] == latest_date]
    count = lambda rows, s: sum(1 for r in rows if r.get("score") == s)

    due_cutoff = (datetime.strptime(latest_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
    due = [r for r in leads if r.get("score") == "A" and r.get("status") == "new" and r.get("date_added", "9999") <= due_cutoff]

    playbook_path = ROOT / "config" / "playbook.md"
    playbook = playbook_path.read_text(encoding="utf-8") if playbook_path.exists() else ""

    def load_csv(path):
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as f:
            return [r for r in csv.DictReader(f) if any(v.strip() for v in r.values())]

    deals = load_csv(ROOT / "deals" / "deals.csv")
    incomes = load_csv(ROOT / "finance" / "income.csv")

    data = {
        "generated": now.strftime("%Y-%m-%d %H:%M"),
        "latestDate": latest_date,
        "playbook": playbook,
        "deals": deals,
        "incomes": incomes,
        "thisMonth": now.strftime("%Y-%m"),
        "today": {"A": count(today_rows, "A"), "B": count(today_rows, "B"), "C": count(today_rows, "C")},
        "totals": {"all": len(leads), "A": count(leads, "A"), "B": count(leads, "B"), "C": count(leads, "C")},
        "dueFollowups": due,
        "leads": leads,
        "reports": reports,
        "verticals": VERTICALS,
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    body = """<title>BD 攻堅日報儀表板</title>
<style>
:root{
  --bg:#F4F7F7; --surface:#FFFFFF; --ink:#17272B; --muted:#5B6E73; --line:#DCE4E5;
  --accent:#0F7B84; --accent-soft:#0F7B8418; --on-accent:#FFFFFF;
  --a:#B23A2E; --a-soft:#B23A2E16; --b:#96700F; --b-soft:#96700F16; --c:#5B6E73; --c-soft:#5B6E7314;
  --v-ai:#3E7BC0; --v-ig:#8A5BB5; --v-ad:#C05B7E; --v-sp:#4E9A6A;
}
@media (prefers-color-scheme: dark){:root{
  --bg:#0D1517; --surface:#152124; --ink:#E4EDEE; --muted:#8AA0A4; --line:#233539;
  --accent:#43B7C0; --accent-soft:#43B7C01F; --on-accent:#0D1517;
  --a:#E0685C; --a-soft:#E0685C1F; --b:#D5A63A; --b-soft:#D5A63A1C; --c:#8AA0A4; --c-soft:#8AA0A41A;
  --v-ai:#6FA5DC; --v-ig:#AF87D4; --v-ad:#DB8AA5; --v-sp:#7BBD92;
}}
:root[data-theme="dark"]{
  --bg:#0D1517; --surface:#152124; --ink:#E4EDEE; --muted:#8AA0A4; --line:#233539;
  --accent:#43B7C0; --accent-soft:#43B7C01F; --on-accent:#0D1517;
  --a:#E0685C; --a-soft:#E0685C1F; --b:#D5A63A; --b-soft:#D5A63A1C; --c:#8AA0A4; --c-soft:#8AA0A41A;
  --v-ai:#6FA5DC; --v-ig:#AF87D4; --v-ad:#DB8AA5; --v-sp:#7BBD92;
}
:root[data-theme="light"]{
  --bg:#F4F7F7; --surface:#FFFFFF; --ink:#17272B; --muted:#5B6E73; --line:#DCE4E5;
  --accent:#0F7B84; --accent-soft:#0F7B8418; --on-accent:#FFFFFF;
  --a:#B23A2E; --a-soft:#B23A2E16; --b:#96700F; --b-soft:#96700F16; --c:#5B6E73; --c-soft:#5B6E7314;
  --v-ai:#3E7BC0; --v-ig:#8A5BB5; --v-ad:#C05B7E; --v-sp:#4E9A6A;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.65 "PingFang TC","Noto Sans TC","Microsoft JhengHei",-apple-system,"Segoe UI",sans-serif;}
.wrap{max-width:1100px;margin:0 auto;padding:28px 20px 64px;}
a{color:var(--accent);text-decoration:none} a:hover{text-decoration:underline}
a:focus-visible,button:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}
.mono{font-family:ui-monospace,"SF Mono",Consolas,monospace;font-variant-numeric:tabular-nums}

header.top{display:flex;flex-wrap:wrap;align-items:baseline;gap:12px 18px;border-bottom:2px solid var(--ink);padding-bottom:14px;margin-bottom:18px}
.top h1{font-size:26px;margin:0;letter-spacing:.02em;text-wrap:balance}
.top .date{font-size:15px;color:var(--muted)}
.counts{display:flex;gap:8px;margin-left:auto;flex-wrap:wrap}
.count{display:inline-flex;align-items:baseline;gap:6px;padding:4px 12px;border:1px solid var(--line);border-radius:999px;background:var(--surface);font-size:13px;color:var(--muted)}
.count strong{font-size:17px;color:var(--ink);font-family:ui-monospace,Consolas,monospace;font-variant-numeric:tabular-nums}
.count.sA strong{color:var(--a)} .count.sB strong{color:var(--b)}

.topnav{position:sticky;top:0;z-index:20;display:flex;gap:4px;flex-wrap:wrap;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line)}
.topnav a{padding:5px 14px;border-radius:999px;font-size:13.5px;color:var(--muted);border:1px solid transparent}
.topnav a:hover{color:var(--accent);border-color:var(--line);text-decoration:none}
.eyebrow{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:34px 0 10px;display:flex;align-items:center;gap:10px;scroll-margin-top:56px}
.eyebrow::after{content:"";flex:1;border-top:1px solid var(--line)}

.top3{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.card{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--a);border-radius:6px;padding:16px 18px}
.card h3{margin:0 0 4px;font-size:18px}
.card .meta{font-size:13px;color:var(--muted);margin-bottom:8px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.card p{margin:6px 0;font-size:14px}
.card .why{color:var(--muted)}
.pill{display:inline-block;padding:1px 9px;border-radius:999px;font-size:12px;font-weight:600;letter-spacing:.05em}
.pill.A{background:var(--a-soft);color:var(--a)} .pill.B{background:var(--b-soft);color:var(--b)} .pill.C{background:var(--c-soft);color:var(--c)}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;vertical-align:1px}
.due{background:var(--surface);border:1px solid var(--b);border-radius:6px;padding:12px 16px;font-size:14px}
.dealhint{font-size:13px;color:var(--muted);margin:0 0 10px}
.dealhint code{background:var(--accent-soft);color:var(--accent);border-radius:4px;padding:1px 6px;font-size:12.5px}
.due ul{margin:6px 0 0;padding-left:20px}

.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;align-items:center}
.chip{border:1px solid var(--line);background:var(--surface);color:var(--muted);border-radius:999px;padding:4px 13px;font-size:13px;cursor:pointer;font-family:inherit}
.chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
.filters input{margin-left:auto;padding:6px 12px;border:1px solid var(--line);border-radius:6px;background:var(--surface);color:var(--ink);font:inherit;font-size:14px;min-width:180px}
.fgrp{display:flex;flex-wrap:wrap;gap:6px;align-items:center;width:100%}
.flabel{font-size:11px;letter-spacing:.1em;color:var(--muted);min-width:56px;text-transform:uppercase}
.fnote{font-size:12.5px;color:var(--muted)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:6px;background:var(--surface)}
table.leads{border-collapse:collapse;width:100%;min-width:1180px;font-size:14px}
.soltag{display:inline-block;background:var(--accent-soft);color:var(--accent);border-radius:4px;padding:0 6px;font-size:11.5px;margin:1px 2px 1px 0;white-space:nowrap}
.leads td.sols{min-width:150px}
.leads th{position:sticky;top:0;background:var(--surface);text-align:left;font-size:12px;letter-spacing:.08em;color:var(--muted);border-bottom:2px solid var(--line);padding:10px 12px;white-space:nowrap}
.leads td{border-bottom:1px solid var(--line);padding:9px 12px;vertical-align:top}
.leads tr:last-child td{border-bottom:none}
.leads td.sig{min-width:280px} .leads td.nowrap{white-space:nowrap}
.empty{padding:24px;text-align:center;color:var(--muted)}

.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:0}
.tabs .chip[aria-pressed="true"]{background:var(--surface);color:var(--ink);border-color:var(--ink);font-weight:600}
.report{background:var(--surface);border:1px solid var(--line);border-radius:0 6px 6px 6px;padding:8px 26px 22px;margin-top:8px}
.report h1{font-size:22px;border-bottom:2px solid var(--ink);padding-bottom:8px}
.report h2{font-size:18px;margin-top:26px}
.report h3{font-size:16px;color:var(--accent)}
.report table{border-collapse:collapse;font-size:13.5px;margin:10px 0}
.report th{background:var(--accent-soft);text-align:left;padding:6px 10px;border:1px solid var(--line);white-space:nowrap}
.report td{padding:6px 10px;border:1px solid var(--line)}
.report .tblwrap{overflow-x:auto}
.report hr{border:none;border-top:1px solid var(--line);margin:22px 0}
.report li{margin:4px 0;font-size:14.5px}
.report p{font-size:14.5px}
footer{margin-top:40px;font-size:12.5px;color:var(--muted);display:flex;gap:14px;flex-wrap:wrap}
@media (prefers-reduced-motion: no-preference){.chip{transition:background .15s,color .15s}}
</style>

<div class="wrap">
<header class="top">
  <h1>BD 攻堅工作台</h1>
  <span class="date mono" id="latestDate"></span>
  <div class="counts" id="counts"></div>
</header>

<nav class="topnav">
  <a href="#sec-today">今日行動</a>
  <a href="#sec-deals">跟單</a>
  <a href="#sec-money">收入資產</a>
  <a href="#sec-pipeline">Pipeline</a>
  <a href="#sec-db">資料庫</a>
  <a href="#sec-history">歷史</a>
  <a href="#sec-playbook">攻堅手冊</a>
  <a href="#sec-reports">日報</a>
</nav>

<div class="eyebrow" id="sec-today">今日必打(A 級)</div>
<div class="top3" id="top3"></div>
<div id="dueBox"></div>

<div class="eyebrow" id="sec-deals">跟單(進行中的案子)</div>
<p class="dealhint">用 Telegram 管理:「<code>開案 公司 方案 月費</code>」開新案 →「<code>公司 報價</code>」「<code>公司 談判</code>」「<code>公司 簽約 15%</code>」「<code>公司 上線</code>」推進 →「<code>公司 進度 70%</code>」修成功率 →「<code>公司 收入 1200</code>」記帳。</p>
<div class="tablewrap"><table class="leads" style="min-width:900px">
  <thead><tr><th>案子</th><th>方案</th><th>階段</th><th>成功率</th><th>預估月費</th><th>傭金%</th><th>預估月傭金</th><th>下一步</th><th>開案日</th></tr></thead>
  <tbody id="dealsBody"></tbody>
</table></div>

<div class="eyebrow" id="sec-money">收入資產</div>
<div class="counts" id="moneyChips" style="margin-left:0"></div>
<div class="tablewrap" style="margin-top:10px"><table class="leads" style="min-width:520px">
  <thead><tr><th>月份</th><th>公司</th><th>金額(USD)</th><th>類型</th><th>備註</th></tr></thead>
  <tbody id="incomeBody"></tbody>
</table></div>

<div class="eyebrow" id="sec-pipeline">Pipeline 狀態</div>
<div class="filters" id="statusChips"></div>
<div class="tablewrap"><table class="leads" style="min-width:820px">
  <thead><tr><th>公司</th><th>評分</th><th>城市/地區</th><th>方案</th><th>入庫</th><th>已過天數</th><th>狀態</th></tr></thead>
  <tbody id="overdueBody"></tbody>
</table></div>

<div class="eyebrow" id="sec-db">Lead 資料庫</div>
<div class="filters" id="filters"></div>
<div class="tablewrap"><table class="leads">
  <thead><tr><th>日期</th><th>公司</th><th>行業</th><th>類型</th><th>國家</th><th>城市</th><th>地區</th><th>訊號</th><th>方案</th><th>預估月消費</th><th>評分</th><th>狀態</th><th>來源</th><th>備註</th></tr></thead>
  <tbody id="tbody"></tbody>
</table><div class="empty" id="empty" hidden>沒有符合篩選的 Lead</div></div>

<div class="eyebrow" id="sec-history">歷史紀錄(每日產出)</div>
<div class="tablewrap"><table class="leads" style="min-width:520px">
  <thead><tr><th>日期</th><th>A</th><th>B</th><th>C</th><th>當日合計</th><th>累積</th></tr></thead>
  <tbody id="historyBody"></tbody>
</table></div>

<div class="eyebrow" id="sec-playbook">攻堅手冊(開發技巧 + 窗口怎麼找)</div>
<article class="report" id="playbook"></article>

<div class="eyebrow" id="sec-reports">日報全文</div>
<div class="tabs" id="tabs"></div>
<article class="report" id="report"></article>

<footer>
  <span>資料來源:leads/leads.csv + reports/*.md</span>
  <span>生成於 <span class="mono" id="generated"></span>(台北時間)</span>
  <span>由 /bd-daily 每日自動更新</span>
</footer>
</div>

<script>
const DATA = __DATA__;
const VCOLOR = {"AI":"var(--v-ai)","iGaming":"var(--v-ig)","成人":"var(--v-ad)","賽事":"var(--v-sp)"};
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const $ = id => document.getElementById(id);

$("latestDate").textContent = DATA.latestDate;
$("generated").textContent = DATA.generated;
$("counts").innerHTML =
  `<span class="count sA">今日 A <strong>${DATA.today.A}</strong></span>` +
  `<span class="count sB">今日 B <strong>${DATA.today.B}</strong></span>` +
  `<span class="count">今日 C <strong>${DATA.today.C}</strong></span>` +
  `<span class="count">累積 <strong>${DATA.totals.all}</strong></span>`;

const vdot = v => `<span class="dot" style="background:${VCOLOR[v]||"var(--muted)"}"></span>${esc(v)}`;

const todayA = DATA.leads.filter(l => l.score === "A" && l.date_added === DATA.latestDate);
$("top3").innerHTML = todayA.length ? todayA.slice(0, 3).map(l => `
  <div class="card">
    <h3>${esc(l.company)}</h3>
    <div class="meta"><span class="pill A">A</span><span>${vdot(l.vertical)}</span><span>${esc(l.type)}</span><span>${esc(l.city || l.region)}</span></div>
    <p>${esc(l.signal)}</p>
    <p>${(l.solutions || "").split(";").filter(Boolean).map(x => `<span class="soltag">${esc(x)}</span>`).join("")}</p>
    <p class="why">${esc(l.notes)}</p>
    <p><a href="${esc(l.source_url)}" target="_blank" rel="noopener">來源 ↗</a></p>
  </div>`).join("") : `<div class="card" style="border-left-color:var(--c)"><p>今日無 A 級 Lead(依「寧缺勿濫」原則如實回報)。</p></div>`;

if (DATA.dueFollowups.length) {
  $("dueBox").innerHTML = `<div class="eyebrow">跟進到期提醒</div><div class="due">以下 A 級 Lead 入庫已滿 7 天仍未接觸:<ul>` +
    DATA.dueFollowups.map(l => `<li><strong>${esc(l.company)}</strong>(${esc(l.date_added)} 入庫)— ${esc(l.signal)}</li>`).join("") + `</ul></div>`;
}

// ---- 跟單 + 收入資產 ----
const STAGE_ZH = {open:"已開案", quoted:"已報價", negotiating:"談判中", signed:"已簽約", live:"上線收款", churned:"丟單", paused:"暫停"};
const NEXT_HINT = {open:"首次觸達+約 15 分鐘通話", quoted:"報價後 48h 內追一次,附成本對比", negotiating:"找出卡點(價格/合規/技術),拉供應商資源", signed:"盯上線時程,順勢開第二方案", live:"每月對帳;90 天內做擴售(cross-sell)", paused:"設 30 天後回訪提醒", churned:"記錄丟單原因進週報"};
const activeDeals = (DATA.deals || []).filter(d => d.stage !== "churned");
const commOf = d => {
  const mrr = parseFloat(d.est_mrr_usd) || 0;
  const pct = parseFloat(d.commission_pct) || 15;  // 未填以 15% 估
  return mrr * pct / 100;
};
$("dealsBody").innerHTML = activeDeals.map(d => `<tr>
  <td><strong>${esc(d.company)}</strong></td>
  <td class="nowrap">${esc(d.solution)}</td>
  <td class="nowrap"><span class="pill ${d.stage === "live" || d.stage === "signed" ? "A" : "B"}">${esc(STAGE_ZH[d.stage] || d.stage)}</span></td>
  <td class="mono">${esc(d.probability)}%</td>
  <td class="mono nowrap">$${esc(d.est_mrr_usd || "0")}</td>
  <td class="mono">${esc(d.commission_pct || "15*")}%</td>
  <td class="mono nowrap">$${Math.round(commOf(d))}</td>
  <td>${esc(d.next_action || NEXT_HINT[d.stage] || "")}<br><span class="why" style="font-size:12px">${esc(NEXT_HINT[d.stage] || "")}</span></td>
  <td class="mono nowrap">${esc(d.start_date)}</td></tr>`).join("") ||
  '<tr><td colspan="9" class="empty">尚無進行中案子——TG 說「開案 公司名 方案 月費」開第一單</td></tr>';

const signedMonthly = activeDeals.filter(d => d.stage === "signed" || d.stage === "live").reduce((s, d) => s + commOf(d), 0);
const weighted = activeDeals.filter(d => !["signed","live"].includes(d.stage)).reduce((s, d) => s + commOf(d) * (parseFloat(d.probability) || 0) / 100, 0);
const incThisMonth = (DATA.incomes || []).filter(i => i.month === DATA.thisMonth).reduce((s, i) => s + (parseFloat(i.amount_usd) || 0), 0);
const incTotal = (DATA.incomes || []).reduce((s, i) => s + (parseFloat(i.amount_usd) || 0), 0);
$("moneyChips").innerHTML =
  `<span class="count">本月已收 <strong>$${Math.round(incThisMonth)}</strong></span>` +
  `<span class="count">累計已收 <strong>$${Math.round(incTotal)}</strong></span>` +
  `<span class="count sA">簽約月傭金(經常性) <strong>$${Math.round(signedMonthly)}</strong></span>` +
  `<span class="count sB">加權 pipeline 預期/月 <strong>$${Math.round(weighted)}</strong></span>` +
  `<span class="count">進行中案子 <strong>${activeDeals.length}</strong></span>`;
$("incomeBody").innerHTML = (DATA.incomes || []).slice().reverse().map(i => `<tr>
  <td class="mono nowrap">${esc(i.month)}</td><td>${esc(i.company)}</td>
  <td class="mono">$${esc(i.amount_usd)}</td><td class="nowrap">${esc(i.type)}</td><td>${esc(i.notes)}</td></tr>`).join("") ||
  '<tr><td colspan="5" class="empty">尚無收入紀錄——簽約後 TG 說「公司名 收入 金額」記第一筆</td></tr>';

// ---- Pipeline 狀態 + 逾期追蹤 ----
const STATUS_LABEL = {new:"未接觸", contacted:"已接觸", replied:"有回覆", meeting:"已約談", won:"成交", lost:"失單", cold:"冷凍", dropped:"放棄"};
const dayDiff = d => Math.floor((new Date(DATA.latestDate) - new Date(d)) / 86400000);
const statusCounts = {};
DATA.leads.forEach(l => { statusCounts[l.status] = (statusCounts[l.status] || 0) + 1; });
$("statusChips").innerHTML = Object.entries(statusCounts).map(([s, n]) =>
  `<span class="count">${esc(STATUS_LABEL[s] || s)} <strong>${n}</strong></span>`).join("") +
  `<span class="count sA">A 級逾期(>7天未接觸) <strong>${DATA.leads.filter(l => l.score === "A" && l.status === "new" && dayDiff(l.date_added) >= 7).length}</strong></span>`;

const attention = DATA.leads
  .filter(l => l.status === "new" && (l.score === "A" || l.score === "B"))
  .map(l => ({...l, age: dayDiff(l.date_added), limit: l.score === "A" ? 7 : 14}))
  .filter(l => l.age >= l.limit - 1)
  .sort((a, b) => (b.age - b.limit) - (a.age - a.limit));
$("overdueBody").innerHTML = attention.map(l => `<tr>
  <td><strong>${esc(l.company)}</strong></td>
  <td><span class="pill ${esc(l.score)}">${esc(l.score)}</span></td>
  <td class="nowrap">${esc(l.city || l.region)}</td>
  <td class="sols">${(l.solutions || "").split(";").filter(Boolean).map(x => `<span class="soltag">${esc(x)}</span>`).join("")}</td>
  <td class="mono nowrap">${esc(l.date_added)}</td>
  <td class="mono nowrap" style="color:${l.age >= l.limit ? "var(--a)" : "var(--b)"}">${l.age} 天${l.age >= l.limit ? "(逾期)" : ""}</td>
  <td class="nowrap">${esc(STATUS_LABEL[l.status] || l.status)}</td></tr>`).join("") ||
  '<tr><td colspan="7" class="empty">沒有待追蹤的 A/B 級 Lead 🎉</td></tr>';

// ---- 歷史紀錄 ----
const byDate = {};
DATA.leads.forEach(l => {
  const d = l.date_added; byDate[d] = byDate[d] || {A:0, B:0, C:0};
  byDate[d][l.score] = (byDate[d][l.score] || 0) + 1;
});
let cum = 0;
$("historyBody").innerHTML = Object.keys(byDate).sort().map(d => {
  const c = byDate[d]; const day = (c.A||0)+(c.B||0)+(c.C||0); cum += day;
  return `<tr><td class="mono nowrap">${esc(d)}</td><td class="mono">${c.A||0}</td><td class="mono">${c.B||0}</td><td class="mono">${c.C||0}</td><td class="mono">${day}</td><td class="mono">${cum}</td></tr>`;
}).join("");

const state = { score: "", vertical: "", status: "", country: "", city: "", sol: "", q: "" };
const cityClean = l => (l.city || "").split("?")[0].trim();
const SOL_TAGS = ["DDoS高防", "CDN", "GPU", "模型折扣", "SMS", "直播加速", "雲主機"];
// 國家 → 城市 對照(依現有資料建立;城市按該國 Lead 數排序)
const COUNTRY_CITIES = {};
DATA.leads.forEach(l => {
  const cn = l.country || "待查", c = cityClean(l);
  (COUNTRY_CITIES[cn] = COUNTRY_CITIES[cn] || new Set());
  if (c) COUNTRY_CITIES[cn].add(c);
});
const countByCountry = {};
DATA.leads.forEach(l => { countByCountry[l.country || "待查"] = (countByCountry[l.country || "待查"] || 0) + 1; });
const COUNTRY_LIST = Object.keys(countByCountry).sort((a, b) => countByCountry[b] - countByCountry[a]);

function renderFilters() {
  const chip = (key, v, label) => `<button class="chip" data-key="${key}" data-val="${esc(v)}" aria-pressed="${state[key] === v}">${esc(label || v)}</button>`;
  const grp = (title, html) => `<div class="fgrp"><span class="flabel">${title}</span>${html}</div>`;
  // 城市選項:選了國家就只顯示該國城市,否則顯示全部(去重)
  const cityPool = state.country
    ? [...(COUNTRY_CITIES[state.country] || [])]
    : [...new Set(DATA.leads.map(cityClean).filter(Boolean))];
  $("filters").innerHTML =
    grp("評分", ["A", "B", "C"].map(v => chip("score", v)).join("")) +
    grp("行業", DATA.verticals.map(v => chip("vertical", v)).join("")) +
    grp("國家", COUNTRY_LIST.map(v => chip("country", v, `${v}·${countByCountry[v]}`)).join("")) +
    grp("城市" + (state.country ? `(${state.country})` : ""), cityPool.length ? cityPool.map(v => chip("city", v)).join("") : '<span class="fnote">此國無城市顆粒</span>') +
    grp("方案", SOL_TAGS.map(v => chip("sol", v)).join("")) +
    grp("狀態", [...new Set(DATA.leads.map(l => l.status))].map(v => chip("status", v)).join("")) +
    `<input type="search" id="q" placeholder="搜尋公司/訊號/城市…" aria-label="搜尋" value="${esc(state.q)}">`;
}
renderFilters();

function renderTable() {
  const rows = DATA.leads.filter(l =>
    (!state.score || l.score === state.score) &&
    (!state.vertical || (l.vertical || "").includes(state.vertical)) &&
    (!state.status || l.status === state.status) &&
    (!state.country || (l.country || "") === state.country) &&
    (!state.city || cityClean(l) === state.city) &&
    (!state.sol || (l.solutions || "").includes(state.sol)) &&
    (!state.q || [l.company, l.signal, l.region, l.city, l.country, l.solutions, l.notes, l.type].join(" ").toLowerCase().includes(state.q)));
  const solTags = s => (s || "").split(";").filter(Boolean).map(x => `<span class="soltag">${esc(x)}</span>`).join("");
  $("tbody").innerHTML = rows.map(l => `<tr>
    <td class="mono nowrap">${esc(l.date_added)}</td>
    <td><strong>${esc(l.company)}</strong></td>
    <td class="nowrap">${vdot(l.vertical)}</td>
    <td class="nowrap">${esc(l.type)}</td>
    <td class="nowrap">${esc(l.country || "")}</td>
    <td class="nowrap">${esc(l.city)}</td>
    <td>${esc(l.region)}</td>
    <td class="sig">${esc(l.signal)}</td>
    <td class="sols">${solTags(l.solutions)}</td>
    <td class="nowrap mono" style="font-size:12.5px">${esc(l.est_value || "")}</td>
    <td><span class="pill ${esc(l.score)}">${esc(l.score)}</span></td>
    <td class="nowrap">${esc(l.status)}</td>
    <td class="nowrap"><a href="${esc(l.source_url)}" target="_blank" rel="noopener">連結 ↗</a></td>
    <td>${esc(l.notes)}</td></tr>`).join("");
  $("empty").hidden = rows.length > 0;
}
$("filters").addEventListener("click", e => {
  const b = e.target.closest(".chip"); if (!b) return;
  const { key, val } = b.dataset;
  state[key] = state[key] === val ? "" : val;
  if (key === "country") {
    // 切換國家時,若已選城市不屬於該國則清掉,並重繪城市選項
    if (state.city && state.country && !(COUNTRY_CITIES[state.country] || new Set()).has(state.city)) state.city = "";
    renderFilters();
  } else {
    document.querySelectorAll(`.chip[data-key="${key}"]`).forEach(x =>
      x.setAttribute("aria-pressed", String(state[key] === x.dataset.val)));
  }
  renderTable();
});
$("filters").addEventListener("input", e => {
  if (e.target.id === "q") { state.q = e.target.value.trim().toLowerCase(); renderTable(); }
});
renderTable();

// ---- 迷你 Markdown 渲染(針對日報模板的子集:標題/表格/清單/粗體/連結/分隔線) ----
function inline(s) {
  return esc(s)
    .replace(/\\*\\*([^*]+)\\*\\*/g, "<strong>$1</strong>")
    .replace(/\\[([^\\]]+)\\]\\((https?:[^)\\s]+)\\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/(^|[(\\s(]|(?:^|\\s)\\()(https?:\\/\\/[^\\s()<>]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>')
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}
function renderMd(md) {
  const lines = md.split(/\\r?\\n/); const out = []; let list = false, i = 0;
  const closeList = () => { if (list) { out.push("</ul>"); list = false; } };
  while (i < lines.length) {
    const L = lines[i];
    if (/^\\|/.test(L) && /^\\|[\\s:|-]+\\|$/.test(lines[i + 1] || "")) {
      closeList();
      const cells = r => r.split("|").slice(1, -1).map(c => c.trim());
      out.push('<div class="tblwrap"><table><thead><tr>' + cells(L).map(h => `<th>${inline(h)}</th>`).join("") + "</tr></thead><tbody>");
      i += 2;
      while (i < lines.length && /^\\|/.test(lines[i])) {
        out.push("<tr>" + cells(lines[i]).map(c => `<td>${inline(c)}</td>`).join("") + "</tr>"); i++;
      }
      out.push("</tbody></table></div>"); continue;
    }
    const h = L.match(/^(#{1,4})\\s+(.*)/);
    if (h) { closeList(); out.push(`<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`); }
    else if (/^---+\\s*$/.test(L)) { closeList(); out.push("<hr>"); }
    else if (/^>\\s?/.test(L)) { closeList(); out.push(`<p class="why">${inline(L.replace(/^>\\s?/, ""))}</p>`); }
    else if (/^(?:[-*]|\\d+\\.)\\s+/.test(L)) { if (!list) { out.push("<ul>"); list = true; } out.push(`<li>${inline(L.replace(/^(?:[-*]|\\d+\\.)\\s+/, ""))}</li>`); }
    else if (L.trim() === "") { closeList(); }
    else { closeList(); out.push(`<p>${inline(L)}</p>`); }
    i++;
  }
  closeList(); return out.join("\\n");
}

const tabs = $("tabs");
tabs.innerHTML = DATA.reports.map((r, idx) =>
  `<button class="chip mono" data-i="${idx}" aria-pressed="${idx === 0}">${r.date}</button>`).join("") || "";
function showReport(i) {
  $("report").innerHTML = DATA.reports.length ? renderMd(DATA.reports[i].md) : '<p class="empty">尚無日報</p>';
  tabs.querySelectorAll(".chip").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.i === i)));
}
tabs.addEventListener("click", e => { const b = e.target.closest(".chip"); if (b) showReport(+b.dataset.i); });
showReport(0);
$("playbook").innerHTML = renderMd(DATA.playbook || "*尚未建立手冊(config/playbook.md)*");
</script>
"""
    body = body.replace("__DATA__", payload)
    full = ('<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            "</head>\n<body>\n" + body + "\n</body>\n</html>\n")
    return body, full


def main():
    DOCS.mkdir(exist_ok=True)
    leads, reports = load_leads(), load_reports()
    body, full = build(leads, reports)
    (DOCS / "artifact.html").write_text(body, encoding="utf-8")
    (DOCS / "index.html").write_text(full, encoding="utf-8")
    print(f"dashboard built: {len(leads)} leads, {len(reports)} reports embedded")


if __name__ == "__main__":
    main()
