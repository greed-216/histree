# -*- coding: utf-8 -*-
"""Initialize only pending 934 book-led ledgers, without overwriting existing work."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
for vol,start,end,header,excluded in [(278,95,106,94,[(92,'潞王上','本帝纪节题，已在933账本排除保留'),(93,'◎','年际分隔'),(107,'','卷尾空行'),(108,'','卷尾空行')]),(279,6,82,5,[(3,'潞王下','同帝纪下一卷节题'),(4,'◎','年际分隔'),(83,'◎','下一年分隔'),(84,'清泰二年乙未，公元九三五年','935年标题')])]:
 raw=ROOT/f'resources/derived/tongjian/{vol}.txt';lines=raw.read_text().splitlines();assert lines[header-1]=='清泰元年甲午，公元九三四年';assert all(lines[i-1].strip() and lines[i-1]!='◎' for i in range(start,end+1))
 for i,t,reason in excluded:assert lines[i-1]==t
 dest=ROOT/f'content/books/zizhi-tongjian/vol-{vol}/year-0934';dest.mkdir(parents=True,exist_ok=True)
 rows=[dict(id=f'zztj-v{vol}-y0934-p{n:03d}',source_line=i,text=lines[i-1],status='pending',event_keys=[],book='资治通鉴',volume=vol,year=934) for n,i in enumerate(range(start,end+1),1)]
 if (dest/'paragraphs.json').exists():assert json.loads((dest/'paragraphs.json').read_text())==rows,'Do not overwrite existing ingestion'
 else:write(dest/'paragraphs.json',rows)
 boundary=dict(book='资治通鉴',volume=vol,year=934,source_file=str(raw.relative_to(ROOT)),source_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),year_header_line=header,body_source_lines=[start,end],body_paragraphs=len(rows),ledger_source_lines=[start,end],ledger_records=len(rows),excluded_non_body=[dict(source_line=i,text=t,reason=reason) for i,t,reason in excluded],next_volume=279,next_year=934 if vol==278 else 935,next_body_source_line=6 if vol==278 else 85,note='934年本卷连续正文全待录，未新增事实或标段完成；全年跨卷278与279，共12+77=89正文段。')
 if (dest/'boundaries.json').exists():assert json.loads((dest/'boundaries.json').read_text())==boundary
 else:write(dest/'boundaries.json',boundary)
 (dest/'README.md').write_text(f'# 《资治通鉴》卷{vol} · 934年\n\n原{start}—{end}行{len(rows)}正文段全待录。934年跨卷278的12段和卷279的77段，全年89正文段；结构项另列，不计正文。\n')
print('934 ledgers initialized: 278=12, 279=77; all pending.')
