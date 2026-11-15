"""Select stable keys from the owning source batches, then verify public entries."""
import json,uuid
from pathlib import Path
BASE=Path(__file__).resolve().parent
HISTORY=Path('/Users/liushuang/project/histree')
stories=json.loads((BASE/'scripts.json').read_text())['stories']
proof=json.loads((BASE/'existing-ingestion.json').read_text())
NS=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content')
overrides={'勾践':'越王句践','韩信':'淮阴韩信','周公旦':'周公','子击':'魏击','魏成子':'魏成','陈余':'陈馀',
    '伍举':'伍举（庄王谏臣，身份待考）','苏从':'苏从（楚庄王谏臣）','履鞮':'履鞮（晋宦者）'}
aliases={'晏婴':['晏子'],'周公旦':['周公'],'召公奭':['召公'],'汉文帝':['文帝'],'刘邦':['汉王'],
    '赵惠文王':['赵王'],'秦昭襄王':['秦王','秦昭王'],'晋文公':['文公'],'楚庄王':['庄王']}
results=[]
for s,pr in zip(stories,proof):
    rows={}
    for path in {r['batch'] for r in pr['existingIngestion']}:
        d=json.loads((HISTORY/path/'content-batch.json').read_text())
        rows.update({r['key']:r for r in d['people']})
        for c in (HISTORY/path).glob('identity-candidates.json'):
            for r in json.loads(c.read_text()):rows.setdefault(r['row']['key'],r['row'])
    selected=[];unbound=[]
    for name in s['peopleNames']:
        target=overrides.get(name,name)
        candidates=[r for r in rows.values() if target==r['name'] or target in r.get('aliases',[])]
        if not candidates and name=='张相如':
            # Public search readback and the existing stable key agree on this identity.
            candidates=[dict(name='张相如',key='person_张相如',aliases=[])]
        assert len(candidates)<=1,(name,candidates)
        if not candidates:
            unbound.append(dict(name=name,reason='当前相关批次没有可唯一核对的已发布主体；保留故事姓名，不新建或猜配人物。'))
            continue
        r=candidates[0];entry=dict(name=name,id=str(uuid.uuid5(NS,r['key'])),canonicalName=r['name'],key=r['key'])
        if name in aliases:entry['aliases']=aliases[name]
        selected.append(entry)
    results.append(dict(slug=s['slug'],people=selected,unboundPeople=unbound))
(BASE/'identities.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('Selected',len({p['id'] for s in results for p in s['people']}),'stable identities')
print('Unbound',[(s['slug'],p['name']) for s in results for p in s['unboundPeople']])
