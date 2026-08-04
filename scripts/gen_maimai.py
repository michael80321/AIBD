#!/usr/bin/env python3
"""生成 reports/maimai-lookup.md:全部中文客戶的「大陸窗口作戰卡」。
每家給:脈脈篩選職稱 + 企查查/IT桔子/BOSS直聘該查什麼 + 是否阿里系可引薦。
不含真人姓名/電話(登入牆個資+不可捏造);僅提供精準查詢配方,供人工查證。"""
import csv, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
rows = [r for r in csv.DictReader((ROOT/'leads/leads.csv').open(encoding='utf-8')) if r['company'].strip()]
CN = {'中國', '香港', '台灣'}
def is_cn(r): return r.get('country') in CN or bool(re.search(r'[一-鿿]', r['company']))
def titles(v, t):
    if '合作夥伴' in t: return '商務拓展/合作/渠道總監'
    if '短劇' in v or '串流' in v: return '技術總監/海外技術負責人/運維總監/採購'
    if 'iGaming' in v: return '技術長/技術總監/運維負責人/採購'
    if '成人' in v: return '創辦人/站長/營運負責人'
    if '遊戲' in v: return '海外技術負責人/發行技術總監/採購'
    if 'AI' in v: return '創辦人/CTO/基礎設施負責人/算力負責人/採購'
    return '技術負責人/採購'
def name(c): return re.sub(r'[\(（][^)）]*[)）]', '', c).strip() or c
def ali(r):
    blob = r['signal'] + r['notes']
    return '✅ 阿里系可引薦' if any(k in blob for k in ['阿里','螞蟻','Alibaba','Ant ','阿里雲']) else '—'
cn = [r for r in rows if is_cn(r)]
cn.sort(key=lambda r: ({'A':0,'B':1,'C':2}.get(r['score'],3), r.get('country','')))
out = [f"# 大陸/華語窗口作戰卡 — 全部中文客戶(共 {len(cn)} 家)\n",
"> **大陸組合拳**:①企查查/天眼查 查法人+高管姓名 → ②脈脈 用下列職稱篩到那個人 → ③IT桔子 查投資方(阿里系走內部引薦)→ ④微信 成交。**大陸別猜 email。**\n",
"> ⚠️ 系統不代查真人姓名/電話(登入牆個資+不可捏造原則);以下為查詢配方,人工於各平台查證即可精準命中,避開 HR/客服。\n",
"| 優先 | 公司(各平台搜此名) | 國家 | 行業 | 脈脈/企查查篩職稱 | 阿里系引薦 |",
"|---|---|---|---|---|---|"]
for r in cn:
    out.append(f"| {r['score']} | {name(r['company'])} | {r.get('country','')} | {r['vertical']} | {titles(r['vertical'], r['type'])} | {ali(r)} |")
out += ["\n## 各平台用途速查",
"- **企查查/天眼查**:法人+高管姓名、註冊電話、融資、子公司(工商公開資訊)",
"- **脈脈**:搜公司名→篩上表職稱→共同好友引薦/私訊",
"- **IT桔子/烯牛/鯨準**:查投資方→投資人引薦(阿里系見上表 ✅)",
"- **BOSS直聘/拉勾**:招 infra/MLOps/運維=買方訊號,可從招聘認識技術負責人",
"- **微博/小紅書/知乎**:創辦人親自發文,私訊暖場;**微信**=成交終點"]
(ROOT/'reports/maimai-lookup.md').write_text('\n'.join(out)+'\n', encoding='utf-8')
n_ali = sum(1 for r in cn if ali(r).startswith('✅'))
print(f"作戰卡: {len(cn)} 家, 阿里系可引薦 {n_ali} 家")
