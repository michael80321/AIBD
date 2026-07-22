#!/usr/bin/env python3
"""Telegram 雙向狀態同步:讀取 bot 收到的訊息,解析「公司名 + 狀態」並更新 leads.csv。

用法:在 Telegram 對 bot 說「AIsa 已接觸」「PolyBuzz 有回覆」「GIM 成交」即可。
由 .github/workflows/telegram-status.yml 每小時執行;offset 存於 .github/tg_offset。
"""
import csv
import io
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OFFSET_FILE = ROOT / ".github" / "tg_offset"
CSV_PATH = ROOT / "leads" / "leads.csv"

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
API = f"https://api.telegram.org/bot{TOKEN}"

DEALS_PATH = ROOT / "deals" / "deals.csv"
INCOME_PATH = ROOT / "finance" / "income.csv"

STAGE_WORDS = {"報價": "quoted", "談判": "negotiating", "簽約": "signed", "上線": "live", "丟單": "churned", "暫停": "paused"}
STAGE_PROB = {"open": 10, "quoted": 40, "negotiating": 60, "signed": 90, "live": 100, "churned": 0, "paused": 5}

STATUS_WORDS = {  # 關鍵詞 → status 值(長詞優先比對)
    "已接觸": "contacted", "接觸了": "contacted", "contacted": "contacted",
    "有回覆": "replied", "回覆了": "replied", "已回": "replied", "replied": "replied",
    "約談": "meeting", "約了": "meeting", "meeting": "meeting",
    "成交": "won", "won": "won",
    "失單": "lost", "lost": "lost",
    "冷凍": "cold", "cold": "cold",
    "放棄": "dropped", "dropped": "dropped",
    "重啟": "new", "未接觸": "new",
}


def api_call(method, params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{API}/{method}", data=data)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def send(text):
    try:
        api_call("sendMessage", {"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print(f"WARN send failed: {e}", file=sys.stderr)


def main():
    if not TOKEN or not CHAT_ID:
        print("no credentials, skip")
        return
    offset = 0
    if OFFSET_FILE.exists():
        offset = int(OFFSET_FILE.read_text().strip() or 0)

    updates = api_call("getUpdates", {"offset": offset + 1, "timeout": 0}).get("result", [])
    if not updates:
        print("no new messages")
        return

    with CSV_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    taipei = timezone(timedelta(hours=8))
    today = datetime.now(taipei).strftime("%m/%d")
    changed = False
    max_id = offset

    # 讀 deals / income
    def load(path):
        with path.open(encoding="utf-8") as f:
            r = csv.DictReader(f)
            return r.fieldnames, list(r)
    deal_fields, deals = load(DEALS_PATH)
    inc_fields, incomes = load(INCOME_PATH)
    deals_changed = inc_changed = False
    today_full = datetime.now(taipei).strftime("%Y-%m-%d")
    month = datetime.now(taipei).strftime("%Y-%m")

    def find_deal(name):
        m = [d for d in deals if name.lower() in d["company"].lower() and d["stage"] not in ("churned",)]
        return m

    import re as _re

    for u in updates:
        max_id = max(max_id, u.get("update_id", 0))
        msg = u.get("message") or {}
        if str((msg.get("chat") or {}).get("id")) != str(CHAT_ID):
            continue
        text = (msg.get("text") or "").strip()
        if not text:
            continue

        # ---- 案子指令(優先於 Lead 狀態) ----
        # 開案 公司 方案 月費(usd) —— 例:開案 AIsa GPU 8000
        m = _re.match(r"^開案\s+(\S+)\s+(\S+)\s*(\d+)?", text)
        if m:
            name, sol, mrr = m.group(1), m.group(2), m.group(3) or "0"
            deals.append({k: "" for k in deal_fields} | {
                "deal_id": f"D{len(deals)+1:03d}", "company": name, "solution": sol,
                "stage": "open", "probability": "10", "est_mrr_usd": mrr,
                "commission_pct": "", "start_date": today_full, "channel": "",
                "next_action": "首次觸達", "next_date": today_full, "notes": ""})
            deals_changed = True
            send(f"📂 開案 {name}({sol},預估月費 ${mrr})→ stage=open")
            continue
        # 收入 —— 例:AIsa 收入 1200
        m = _re.match(r"^(\S+)\s+收入\s+(\d+(?:\.\d+)?)", text)
        if m:
            name, amt = m.group(1), m.group(2)
            incomes.append({"month": month, "company": name, "amount_usd": amt, "type": "傭金", "notes": f"TG 記帳 {today_full}"})
            inc_changed = True
            send(f"💰 已記收入:{name} ${amt}({month})")
            continue
        # 進度 % —— 例:AIsa 進度 70%
        m = _re.match(r"^(\S+)\s+進度\s+(\d+)%?", text)
        if m:
            name, pct = m.group(1), m.group(2)
            ds = find_deal(name)
            if len(ds) == 1:
                ds[0]["probability"] = pct
                deals_changed = True
                send(f"📈 {ds[0]['company']}({ds[0]['solution']})成功率 → {pct}%")
            else:
                send(f"❓ 案子「{name}」找到 {len(ds)} 筆,請用更完整名稱")
            continue
        # 階段詞 —— 例:AIsa 簽約 15% / AIsa 談判
        stage_hit = next((kw for kw in STAGE_WORDS if kw in text), None)
        if stage_hit:
            name = text.split(stage_hit)[0].strip(" ,,:→-")
            ds = find_deal(name) if name else []
            if len(ds) == 1:
                d = ds[0]
                d["stage"] = STAGE_WORDS[stage_hit]
                d["probability"] = str(STAGE_PROB[d["stage"]])
                pm = _re.search(r"(\d+(?:\.\d+)?)\s*%", text)
                if pm:
                    d["commission_pct"] = pm.group(1)
                if d["stage"] in ("signed", "live"):
                    d["close_date"] = d.get("close_date") or today_full
                deals_changed = True
                comm = f",傭金 {d['commission_pct']}%" if d.get("commission_pct") else ""
                send(f"📋 {d['company']}({d['solution']})→ {stage_hit}({d['probability']}%){comm}")
                continue
            elif name and len(ds) > 1:
                send(f"❓ 案子「{name}」符合多筆,請用更完整名稱")
                continue
            # 找不到案子則落到 Lead 狀態處理

        # ---- Lead 狀態關鍵詞(長詞優先) ----
        status = None
        kw_hit = None
        for kw in sorted(STATUS_WORDS, key=len, reverse=True):
            if kw in text.lower() or kw in text:
                status, kw_hit = STATUS_WORDS[kw], kw
                break
        if not status:
            continue  # 非狀態指令,忽略(日報等其他訊息)
        name_part = text.replace(kw_hit, "").strip(" ,,:→-")
        if not name_part:
            send(f"❓「{text}」缺公司名,格式:公司名 + 狀態(例:AIsa 已接觸)")
            continue
        # 模糊比對公司名(不分大小寫、子字串)
        matches = [r for r in rows if name_part.lower() in r["company"].lower()]
        if len(matches) == 1:
            r = matches[0]
            old = r["status"]
            r["status"] = status
            r["notes"] = (r.get("notes", "") + f";{today} {old}→{status}").strip(";")
            changed = True
            send(f"✅ {r['company']}:{old} → {status}")
        elif len(matches) == 0:
            send(f"❓ 找不到「{name_part}」,請用 leads.csv 內的公司名(可只打部分字)")
        else:
            names = "、".join(m["company"] for m in matches[:5])
            send(f"❓「{name_part}」符合多筆:{names}——請打更完整的名稱")

    def save(path, flds, rws):
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=flds, quoting=csv.QUOTE_MINIMAL, extrasaction="ignore")
        w.writeheader()
        w.writerows(rws)
        path.write_text(out.getvalue(), encoding="utf-8")

    if changed:
        save(CSV_PATH, fields, rows)
        print("leads updated")
    if deals_changed:
        save(DEALS_PATH, deal_fields, deals)
        print("deals updated")
    if inc_changed:
        save(INCOME_PATH, inc_fields, incomes)
        print("income updated")
    OFFSET_FILE.parent.mkdir(exist_ok=True)
    OFFSET_FILE.write_text(str(max_id))
    print(f"processed {len(updates)} updates, offset={max_id}")


if __name__ == "__main__":
    main()
