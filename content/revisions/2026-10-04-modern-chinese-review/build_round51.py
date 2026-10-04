# coding: utf-8
"""Expand a complete location caveat, without changing historical places or coordinates."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snapshot_path=Path('/private/tmp/histree-public-prose-20261004.json');snapshot=read(snapshot_path);assert sha(snapshot_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-49/readback-audit.json')['verified']
all_rows={t:{r['id']:dict(r) for r in records} for t,records in snapshot['tables'].items()};rows=all_rows['event'];overlays=[]
for path in sorted(P.glob('round-*/changes.json')):
 proof=path.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(path)
 overlays.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
 for c in read(path)['changes']:
  all_rows[c['table']][c['id']].update(c['after'])
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:fields=[json.loads(line) for line in f]
part03=ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-04';ids=read(part03/'sql/key-map.json')
changes=[];corrections=[]
values={
'event_zztj_279_0935_ye_qiao_remonstrates_for_li_consort':{'description':'叶翘说，梁国夫人与先帝有亲属关系，原文称她为“先帝之甥”，又是依礼聘娶的妻子，不应因为新宠而抛弃她。王继鹏不高兴，从此疏远叶翘。原文未说明中间的母系亲属，具体亲等仍保留待核，不据此另定外甥女身份。'},
'event_zztj_279_0935_min_chen_shouyuan_tianshi':{'title':'王昶赐陈守元天师称号','description':'闽王王昶，即王继鹏，赐洞真先生陈守元“天师”称号，并信任、重视他。《新五代史》也记载陈守元获天师称号，但该书相关段落另有时间层次，不能把后续三年的事合入935年。'},
'event_zztj_279_0935_min_consults_chen_shouyuan':{'title':'王昶与陈守元商议政务','description':'《资治通鉴》说，闽王王昶，即王继鹏，连将相任免、刑罚、选官等事务都与陈守元商议。这是史书对其影响力的概括，不能据此认定每项具体政务都已有逐案记载。'},
'event_zztj_279_0935_chen_shouyuan_bribery_petitions':{'description':'《资治通鉴》说，陈守元收受贿赂、代人请托，王昶对他所说的话都予以听从，往来其门庭的人很多。这是史书的概括，原文没有列出每笔贿赂的金额或每次请托的对象。'}
}
for key,new in values.items():
 rid=ids[key];r=all_rows['event'][rid]
 before={field:r[field] for field in new}
 for field in new:
  assert any(x['table']=='event' and x['id']==rid and x['field']==field and x['status']=='reviewed_verified' and x['round']=='round-49' for x in fields)
  corrections.append(dict(table='event',id=rid,field=field,previous_round='round-49'))
 changes.append(dict(table='event',id=rid,baseline=r,before=before,after=new,review='根据当前原文上下文与既有校核记录复核主语和亲属范围：935年末闽主为王昶，原甥称谓未说明中间母系，不强定外甥女身份。已审字段纠正，不重复计入新增进度。'))
part=ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-04'
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-51';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='复核第49轮六个已审事件字段：明确王昶为年末闽主，梁国夫人亲属范围按原甥称谓保留，不强定外甥女；不重复增加已审数。',inventory_sha256=sha(snapshot_path),verified_overlays=overlays,changes=changes,reviewed_unchanged=[],archives=archives,already_reviewed_corrections=corrections,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print('Prepared',len(corrections),'wording corrections; no newly reviewed fields.')
