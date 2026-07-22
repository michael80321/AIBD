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

    for u in updates:
        max_id = max(max_id, u.get("update_id", 0))
        msg = u.get("message") or {}
        if str((msg.get("chat") or {}).get("id")) != str(CHAT_ID):
            continue
        text = (msg.get("text") or "").strip()
        if not text:
            continue
        # 找狀態關鍵詞(長詞優先)
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

    if changed:
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
        CSV_PATH.write_text(out.getvalue(), encoding="utf-8")
        print("csv updated")
    OFFSET_FILE.parent.mkdir(exist_ok=True)
    OFFSET_FILE.write_text(str(max_id))
    print(f"processed {len(updates)} updates, offset={max_id}, changed={changed}")


if __name__ == "__main__":
    main()
