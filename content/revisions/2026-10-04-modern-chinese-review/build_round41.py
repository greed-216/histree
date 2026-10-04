# coding: utf-8
"""Expand two completely read, repeated evidence-note sentences; preserve quotations."""
import gzip, hashlib, json
from pathlib import Path
from datetime import datetime, timezone
P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/review-public-history-copy.py').exists())
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
snapshot_path = Path('/private/tmp/histree-public-prose-20261004.json')
snapshot = read(snapshot_path)
assert sha(snapshot_path) == read(P / 'progress.json')['inventory_sha256']
assert read(P / 'round-40/readback-audit.json')['verified']
rows = {r['id']: dict(r) for r in snapshot['tables']['fact_claim']}
overlays = []
for path in sorted(P.glob('round-*/changes.json')):
    proof = path.with_name('readback-audit.json')
    if not proof.exists(): continue
    assert read(proof)['verified'] and read(proof)['plan_sha256'] == sha(path)
    overlays.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path)))
    for c in read(path)['changes']:
        if c['table'] == 'fact_claim': rows[c['id']].update(c['after'])
with gzip.open(P / 'review-ledger.jsonl.gz', 'rt', encoding='utf-8') as f:
    pending = {x['id'] for x in map(json.loads, f) if x['table'] == 'fact_claim' and x['field'] == 'note' and x['status'] == 'pending'}
sentences = {
    '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。': '时间依据《资治通鉴》及相应补证分别记录；追述和其他史书的日期另作说明，不自行换算公历日期。',
    '核对同名、职务及行动后识别主体；展示简体，摘录保留原字。': '核对人物姓名、职务和行动后识别为同一主体；展示使用简体，引用保持底本原字。'}
owner_files = sorted((ROOT / 'content/books/zizhi-tongjian').glob('**/sql/key-map.json'))
owners = set()
for f in owner_files: owners.update(read(f).values())
changes = []; counts = {text: 0 for text in sentences}
for rid in sorted(pending):
    r = rows[rid]; note = r['note']
    if not note.startswith('原文：') or '；核对说明：' not in note: continue
    quote, explanation = note.split('；核对说明：', 1)
    if explanation not in sentences: continue
    if explanation.startswith('按主书'): assert rid in owners
    new = quote + '；核对说明：' + sentences[explanation]
    assert new.split('；核对说明：', 1)[0] == quote
    counts[explanation] += 1
    changes.append(dict(table='fact_claim', id=rid, baseline=r, before=dict(note=note), after=dict(note=new), review='匹配已核读的完整解释句子，展开为现代白话；时间说明的主书归属逐条通过《资治通鉴》批次UUID映射核对。不改原文、具体日期、事实正文、身份判断或出处。其他字段仍分别待审。'))
assert sorted(counts.values()) == [1501, 3269] and len(changes) == 4770
D = P / 'round-41'; assert not (D / 'publication.json').exists(); D.mkdir(parents=True, exist_ok=True)
plan = dict(created_at=datetime.now(timezone.utc).isoformat(), scope='全站4770条待审事实说明中的两种完整核对句式，仅展开解释区；时间说明逐条确认归属《资治通鉴》批次，逐字引用及其他字段保留。', inventory_sha256=sha(snapshot_path), verified_overlays=overlays, exact_sentence_counts=counts, sentence_map=sentences, book_ownership_evidence=[dict(path=str(f.relative_to(ROOT)), sha256=sha(f)) for f in owner_files], changes=changes, reviewed_unchanged=[], archives=[], full_goal_complete=False)
(D / 'changes.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
print(dict(selected=len(changes), exact_sentence_counts=counts), flush=True)
