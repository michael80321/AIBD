#!/usr/bin/env python3
"""生成 reports/maimai-lookup.md:全部中文客戶的脈脈搜尋職稱配方。
不含真人姓名/電話(登入牆個資+不可捏造);僅提供精準搜尋配方,供人工於脈脈查證。"""
import csv, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
rows = [r for r in csv.DictReader((ROOT/'leads/leads.csv').open(encoding='utf-8')) if r['company'].strip()]
CN = {'中國', '香港', '台灣'}
def is_cn(r): return r.get('country') in CN or bool(re.search(r'[一-鿿]', r['company']))
def titles(v, t):
    if '合作夥伴' in t: return '商務拓展負責人 / 合作負責人 / 渠道總監'
    if '短劇' in v or '串流' in v: return '技術總監 / 海外技術負責人 / 運維總監 / 採購'
    if 'iGaming' in v: return '技術長 / 技術總監 / 運維負責人 / 採購'
    if '成人' in v: return '創辦人 / 站長 / 營運負責人'
    if '遊戲' in v: return '海外技術負責人 / 發行技術總監 / 採購'
    if 'AI' in v: return '創辦人 / CTO / 基礎設施負責人 / 算力負責人 / 採購'
    return '技術負責人 / 採購'
def name(c): return re.sub(r'[\(（][^)）]*[)）]', '', c).strip() or c
cn = [r for r in rows if is_cn(r)]
cn.sort(key=lambda r: ({'A':0,'B':1,'C':2}.get(r['score'],3), r.get('country','')))
out = [f"# 脈脈搜尋配方 — 全部中文客戶(共 {len(cn)} 家)\n",
"> 打開脈脈 → 搜「公司名」→ 用「職稱」篩選 → 找到人後透過共同好友請求引薦或私訊。避開 HR/招聘/客服。\n",
"> ⚠️ 系統不代查真人姓名/電話(登入牆個資+不可捏造原則);以下為搜尋配方,人工查證即可精準命中。\n",
"| 優先 | 公司(脈脈搜此名) | 國家 | 行業 | 脈脈篩選職稱 | 避開 |",
"|---|---|---|---|---|---|"]
for r in cn:
    out.append(f"| {r['score']} | {name(r['company'])} | {r.get('country','')} | {r['vertical']} | {titles(r['vertical'], r['type'])} | HR/招聘/客服 |")
(ROOT/'reports/maimai-lookup.md').write_text('\n'.join(out)+'\n', encoding='utf-8')
print(f"maimai-lookup.md: {len(cn)} companies")
