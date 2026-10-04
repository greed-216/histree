# coding: utf-8
"""Build the reviewed 936 Jinan evidence explanations; preserve frozen archives."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path)
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 audit=old_plan.with_name('readback-audit.json')
 if not audit.exists():continue
 proof=read(audit);assert proof['verified'] and proof['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
assert read(P/'round-07/readback-audit.json')['verified'], 'Verify the preceding round before constructing fresh baselines'
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-09';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json')
changes={};unchanged=[]
def patch(table,rid,field,value,review):
 base=rows[table][rid];old=base[field]
 if old==value:
  unchanged.append(dict(table=table,id=rid,fields=[field],baseline=base,review=review));return
 key=(table,rid)
 if key not in changes:changes[key]=dict(table=table,id=rid,before={},after={},baseline=base,review=review)
 c=changes[key];c['before'][field]=old;c['after'][field]=value
for event in batch['events']:
 rid=ids[event['key']];assert rows['event'][rid]['location_note']=='仅保留史载地名；未核坐标。'
 patch('event',rid,'location_note','只保留史书记载的地名，尚未核定地理坐标。','展开地点说明的省略词，保留坐标尚未核定的状态，不新增地点或坐标。')
for rid,copy in read(P/'source-copy-936-part09.json').items():
 for field,value in copy.items():patch('source',rid,field,value,'展开出处和版本介绍，保留书名、卷次、段落ID及待核状态；来源URL、作者和引用对象保持不变。')
round_dir=P/'round-08';assert not (round_dir/'publication.json').exists()
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
write(round_dir/'changes.json',dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年第54—70段的47个事件地点说明及14个尚未审阅出处的标题、版本说明和备注；保留引用定位和未核状态。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False))
from collections import Counter
print(dict(changed_rows=len(changes),changed_fields=sum(len(c['after']) for c in changes.values()),by_table=dict(Counter(c['table'] for c in changes.values())),unchanged_reviewed_fields=len(unchanged)))
