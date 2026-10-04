# coding: utf-8
"""Review remaining chronology, supplementary facts and introductions for paragraphs 9-12."""
import gzip, hashlib, json, re
from pathlib import Path
from datetime import datetime, timezone
P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/review-public-history-copy.py').exists())
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
snapshot_path = Path('/private/tmp/histree-public-prose-20261004.json')
snapshot = read(snapshot_path)
assert sha(snapshot_path) == read(P / 'progress.json')['inventory_sha256']
assert read(P / 'round-39/readback-audit.json')['verified']
rows = {t: {r['id']: dict(r) for r in records} for t, records in snapshot['tables'].items()}
for path in sorted(P.glob('round-*/changes.json')):
    proof = path.with_name('readback-audit.json')
    if not proof.exists(): continue
    assert read(proof)['verified'] and read(proof)['plan_sha256'] == sha(path)
    for c in read(path)['changes']: rows[c['table']][c['id']].update(c['after'])
part = ROOT / 'content/books/zizhi-tongjian/vol-280/year-0936/part-02'
batch = read(part / 'content-batch.json')
ids = read(part / 'sql/key-map.json')
times = read(P / 'times-936-part02.json')
facts = read(P / 'claims-936-part02-remaining.json')
profiles = read(P / 'profiles-936-part02.json')
with gzip.open(P / 'review-ledger.jsonl.gz', 'rt', encoding='utf-8') as f:
    pending = {(x['table'], x['id'], x['field']) for x in map(json.loads, f) if x['status'] == 'pending'}
changes = {}; unchanged = []; support = []
def patch(table, rid, field, new, review):
    assert (table, rid, field) in pending
    base = rows[table][rid]; old = base[field]
    if old == new:
        unchanged.append(dict(table=table, id=rid, fields=[field], baseline=base, review=review)); return
    key = (table, rid)
    if key not in changes: changes[key] = dict(table=table, id=rid, baseline=base, before={}, after={}, review=review)
    c = changes[key]; c['before'][field] = old; c['after'][field] = new
    if table == 'event' and field == 'time_original':
        c['preserved_original_dates'] = '保留936年、四月、五月及庚寅、辛卯、甲午等原干支日期；追述起年仍未知，拟议与发生分开，未单独记载的日期仍未记载，不换算公历。'
for original in batch['events']:
    rid = ids[original['key']]; r = rows['event'][rid]
    if ('event', rid, 'time_original') not in pending: continue
    new = times.get(r['time_original'], r['time_original'])
    if new == r['time_original']: assert new.startswith('936年') and '条下' not in new
    patch('event', rid, 'time_original', new, '核读各事件原文，展开追述和时序说明；保留原纪年、干支、相对时间以及未确定日期，不换算公历。')
for original in batch['claims']:
    rid = ids[original['key']]; r = rows['fact_claim'][rid]
    if ('fact_claim', rid, 'claim_text') not in pending: continue
    code = original['key'].split('_')[-1]
    if code in facts: new = facts[code]
    elif r['claim_text'] in times: new = times[r['claim_text']]
    else:
        assert r['field_path'] == 'time_original' and r['claim_text'].startswith('936年'), (code, r['claim_text'])
        new = r['claim_text']
    patch('fact_claim', rid, 'claim_text', new, '核读这条引用，展开完整书名、人物、动作和时间解释；原文、出处、身份、状态与历史日期保持不变。')
for original in batch['people']:
    rid = ids[original['key']]; r = rows['person'][rid]
    if ('person', rid, 'description') not in pending: continue
    name = r['name']; old = r['description']; new = profiles[name]
    candidates = [c for c in snapshot['tables']['fact_claim'] if c['subject_table'] == 'person' and c['subject_id'] == rid and c['field_path'] == 'description']
    if '本批' in old:
        role = old.split('，', 1)[1][:-1]
        candidates = [c for c in candidates if c['claim_text'].endswith('：' + role + '。')]
    else:
        match = re.search(r'卷(\d+)(.+?)条', old); assert match
        candidates = [c for c in candidates if '卷' + match[1] in c['citation'] and match[2] in c['citation']]
    assert candidates, name
    claim = rows['fact_claim'][candidates[0]['id']]
    support.append(dict(person_id=rid, claim_id=claim['id'], baseline=claim, review='依据原简介对应的既有引用和原文上下文改写，保留原有经历；不补写未经出处支持的完整生平。'))
    patch('person', rid, 'description', new, '去掉录入模板，依据原简介的既有引用写清人物身份和行动；人物姓名、家庭、日期及其他字段保持原值。')
assert len(support) == len(profiles) == 11
for original in batch['sources']:
    rid = ids[original['key']]; r = rows['source'][rid]
    if ('source', rid, 'title') in pending:
        patch('source', rid, 'title', r['title'], '具体书名、卷次及片段标题已清楚，作为来源定位保留，链接和正文不改变。')
D = P / 'round-40'; assert not (D / 'publication.json').exists(); D.mkdir(parents=True, exist_ok=True)
archives = [dict(batch=str(part.relative_to(ROOT)), batch_sha256=sha(part / 'content-batch.json'), source_files=[dict(path=str(f.relative_to(ROOT)), sha256=sha(f)) for f in sorted((part / 'sources').rglob('source.txt'))])]
plan = dict(created_at=datetime.now(timezone.utc).isoformat(), scope='936年第9—12段批次剩余事件时间、补证与时间事实、11位人物原简介和出处标题的语言审阅；原纪年、引用、身份和关系保持不变，全站目标仍未完成。', inventory_sha256=sha(snapshot_path), changes=list(changes.values()), reviewed_unchanged=unchanged, supporting_claims=support, archives=archives, full_goal_complete=False)
(D / 'changes.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
print(dict(changed_rows=len(changes), changed_fields=sum(len(c['after']) for c in changes.values()), unchanged_fields=sum(len(c['fields']) for c in unchanged)))
