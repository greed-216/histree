# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 284, year 944 year 945 paragraphs 9–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,36))
COMMIT='7ec152ca6b93afb639ad0febcd3c8be43a631b52'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-284-945-january','jiuwudaishi-083-945-january','xinwudaishi-009-945','xinwudaishi-062-min-campaign','jiuwudaishi-073-wen-tao']:
 prior=next(x for f in (ROOT/'content').rglob('content-batch.json') for x in json.loads(f.read_text())['sources'] if x['key']==key)
 commit,relative=prior['url'].split('/blob/')[1].split('/',1)
 specs.append((key,(ROOT/relative).parent,commit,prior['author']))

# Reuse already published source identities, including the earlier Zhou Gui biography.
prior_source_registry={x['key']:x for f in sorted((ROOT/'content').rglob('content-batch.json')) if f.parent != P for x in json.loads(f.read_text())['sources']}
normalized=[]
for key,path,commit,author in specs:
 if key in prior_source_registry:
  archived=prior_source_registry[key]['url'].split('/blob/',1)[1];commit,relative=archived.split('/',1);old_path=(ROOT/relative).parent
  assert (old_path/'source.txt').read_bytes()==(path/'source.txt').read_bytes(),key
  path=old_path
 normalized.append((key,path,commit,author))
specs=normalized

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-284-945-january','tongjian-284-945-february-march']
B = {'format_version': 1, 'batch_key': 'zztj-v284-y0945-p009-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=record.get('edition_note','选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/284.txt').read_text().splitlines()
for n in range(9, 17):
    assert Q[n]['text'] == lines[Q[n]['source_line'] - 1]
registry = {}
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    for row in json.loads(path.read_text())['people']:
        old = registry.get(row['name'])
        if old:
            assert old['key'] == row['key'], (row['name'], path)
        registry[row['name']] = row
for revision in sorted((ROOT/'content/revisions').glob('*/aliases.json')):
    if not (revision.parent/'publication.json').exists():continue
    for corrected in json.loads(revision.read_text()).get('people',[]):
        if corrected['name'] in registry:registry[corrected['name']]=dict(registry[corrected['name']],aliases=corrected['after'])
for name,extra in [('荝剌',['荝刺']),('耶律倍',['李赞华','李贊華'])]:
    if name in registry:registry[name]=dict(registry[name],aliases=list(dict.fromkeys(registry[name]['aliases']+extra)))
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    for a,b in [('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
        note=note.replace(a,b)
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷284·后晋开运二年（945年正月至三月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_284_0945_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={'王威（王处直之子）':'《资治通鉴》与《旧五代史》记为王处直之子，因王都夺权逃往契丹。939年契丹要求后晋让他承袭父亲旧地，石敬瑭拒绝直接授节度使。生卒年未载。是否与早期记载的王郁有关，尚待校核，未作合并。'}
NEW_ALIASES={'王威（王处直之子）':['王威']}

ALIASES.update({'景通':'李璟','徐知诰':'李昪','徐诰':'李昪','元瓘':'钱传瓘','钱元瓘':'钱传瓘','闽主':'王继鹏','蜀主':'孟昶','汉主':'刘岩','梁均王':'朱友贞'})



ALIASES.update({'张彦琦':'张彦琪','张彦琪':'张彦琪','曹太后':'曹氏（李嗣源后）','刘皇后':'刘氏（李从珂后）','太相温':'太相温（契丹将）','大相温':'太相温（契丹将）','汉主':'刘岩','吴主':'杨溥','杨光远':'杨檀','景岩':'刘景岩','刘延郎':'刘延朗','李赞华':'耶律倍','李懿':'李懿（后唐亲将）'})

# Follow already verified merges so hidden legacy entities are never revived.
registry_by_key={r['key']:r for r in registry.values()}
for plan_file in sorted((ROOT/'content/revisions').glob('*/plan.json')):
 audit_file=plan_file.parent/'publication.json'
 if not audit_file.exists():continue
 plan=json.loads(plan_file.read_text());audit=json.loads(audit_file.read_text())
 if not (audit.get('verified') and audit.get('canonical_person_id') and audit.get('hidden_duplicate_person_id')):continue
 canonical=registry_by_key.get(plan.get('canonical_key'));duplicate=registry_by_key.get(plan.get('duplicate_key'))
 if canonical and duplicate:
  canonical=dict(canonical,aliases=list(dict.fromkeys(canonical.get('aliases',[])+plan.get('aliases_to_add',[]))))
  registry[canonical['name']]=canonical
  for alias in [duplicate['name']]+duplicate.get('aliases',[]):ALIASES[alias]=canonical['name']

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=945, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='945年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_284_0945_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=description or title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='采用史书记载的地点名称，地理坐标尚未核实。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按《资治通鉴》及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_284_0945_' + code + '_' + pk
        existing = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['person_events'] if (x['person_key'],x['event_key'])==(pk,key)] if stable_key else []
        if existing:
            assert len({x['key'] for x in existing})==1
            er=dict(existing[0],status='draft');edge=er['key'];reused.add(edge)
        else:er=dict(key=edge,person_key=pk,event_key=key,role=role,status='draft')
        B['person_events'].append(er)
        claim('person_event', edge, 'role', f'{next(x["name"] for x in B["people"] if x["key"]==pk)}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。',source=source)
    return key

def relationship(a,b,kind,n,quote,note,source=None):
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'与{a}存在原文明示的亲属关系',quote,source=source)
    a=next(x['name'] for x in B['people'] if x['key']==pa); b=next(x['name'] for x in B['people'] if x['key']==pb)
    matches={}
    corrections={}
    import uuid
    namespace=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content')
    people_ids={str(uuid.uuid5(namespace,x['key'])):x['key'] for x in registry.values()}
    for revision in sorted((ROOT/'content/revisions').glob('*/relations.json')):
        if not (revision.parent/'publication.json').exists():continue
        for revision_row in json.loads(revision.read_text()).get('relations',[]):corrections[revision_row['key']]=revision_row['after']
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if x['key'] in corrections:
                c=corrections[x['key']];x=dict(x,person_a_key=people_ids[c['person_a']],person_b_key=people_ids[c['person_b']],relation_type=c['relation_type'])
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_284_0945_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=event(code,title,n,span(n,start,end),actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
def extra(code,title,n,source,quote,actors,**kw):
 E[code]=event(code,title,n,quote,actors,source=source,**kw);return E[code]
ALIASES.update({'帝':'石重贵','高祖':'石敬瑭','唐主':'李璟','殷主':'王延政','闽主':'王延政','杜威':'杜重威','继昌':'王继昌','李彦韬':'李彦韬（后晋宣徽使）'})
NEW_ALIASES={'王继昌':['王繼昌'],'黄仁讽':['黃仁諷'],'沈斌':[],'何敬洙':[],'姚凤':['姚鳳'],'李彦韬（后晋宣徽使）':['李彥韜（後晉宣徽使）']}
NEW_DESCRIPTIONS={
 '王继昌':'王延政的从子，任门下侍郎、同平章事。945年王延政因南唐来攻而暂不迁都，任他都督南都内外诸军事，驻福州。父亲姓名及生卒年本次引文未载。',
 '黄仁讽':'闽国飞捷指挥使。945年王延政任他为镇遏使，率军作为王继昌的后援。生卒年本段未载。',
 '沈斌':'字安时，徐州下邳人，曾任梁拱辰都指挥使，后唐从魏王李继岌伐蜀、平康延孝。开运元年任后晋祁州刺史，945年契丹攻祁州后死亡。主书和新史传记写自杀，《辽史》写被杀，具体日期按各书分别保留。出生年未载。',
 '何敬洙':'南唐天威都虞候。945年李璟任他为建州行营招讨马步都指挥使，与祖全恩、姚凤率数千兵增援查文徽，攻建州。生卒年本段未载。',
 '姚凤':'南唐将领。945年李璟任他为建州行营都监，与何敬洙、祖全恩率军增援查文徽。生卒年本段未载。',
 '李彦韬（后晋宣徽使）':'太原人，早年曾侍奉阎宝，后来入石敬瑭帐下并留在太原侍奉石重贵。945年任宣徽北院使、暂代侍卫马步都虞候，与冯玉争桑维翰的权力。与早期曾名李彦韬的温韬分档，温韬在后唐明宗时已被赐死。生卒年本段未载。'}
NEW_DEATH_YEARS={'沈斌':945}
jan='jiuwudaishi-083-945-january';feb='jiuwudaishi-083-945-february';mar='jiuwudaishi-083-945-march';newyear='xinwudaishi-009-945';minbook='xinwudaishi-062-min-campaign';shen='xinwudaishi-033-shen-qizhou';origin='xinwudaishi-033-shen-origins';liao='liaoshi-004-945-march';sang='xinwudaishi-029-sang-feng-strife';deqing='jiuwudaishi-080-941-deqing';wen='jiuwudaishi-073-wen-tao'
# 9: a proposal based on a surrenderer's report, followed by mobilisation and departure.
add('ma_proposes_attack_youzhou','马全节等据降者说法，建议趁契丹分散时直袭幽州',9,'北面副招讨使','幽州。”',[('马全节','据降者说法建议趁契丹分散时袭幽州')],when='945年正月，亲征诏令前',place='后晋行营至朝廷',note='虏众不多来自降者转述，宜袭幽州是奏议，不写成已攻陷幽州。')
add('shi_levies_troops_for_youzhou','石重贵接受马全节等建议，征调各道兵马',9,'帝以为然，','诸道。',[('帝','接受袭幽州建议，征调各道兵马'),('马全节','其出兵建议获得采纳')],when='945年正月，亲征诏令前',place='后晋诸道',note='征兵范围诸道，没有精确兵员总数，不据建议倒推已完成全部集结。')
add('shi_orders_personal_campaign','石重贵下诏亲征契丹',9,'壬戌，','亲征；',[('帝','下诏亲征契丹')],when='945年正月壬戌；旧本纪记辛酉',place='后晋朝廷',note='亲征诏令与实际离京分开，保留新旧史不同纪日。')
sup('shi_orders_personal_campaign',9,jan,'辛酉，下詔親征。','《旧五代史》把亲征诏令记在辛酉，主书记壬戌。','相差一日，分别保留，不修改主书原字或据此虚构两次不同亲征令。',relation='conflicts',field='time_original')
add('shi_leaves_daliang_campaign','石重贵从大梁出发亲征',9,'乙丑，',None,[('帝','率军从大梁出发亲征')],when='945年正月乙丑',place='大梁')
sup('shi_leaves_daliang_campaign',9,jan,'乙丑，車駕發離京師。','《旧五代史》同记乙丑皇帝离京。','诏令日期有异而离京日相同，两类行动分别记录。')
sup('shi_leaves_daliang_campaign',9,newyear,'乙丑，北征，契丹去。','《新五代史》同记乙丑北征，并以契丹退去概括此时局势。','契丹先前退军已录，不能据此概括句另造乙丑晋军攻破契丹事件。',relation='adds')
# 10: restoration of the Min name, delegation of Fuzhou and dispatch of reinforcements.
add('min_former_officials_request_return','闽国旧臣迎王延政，请他回福州',10,'闽之故臣','请归福州，',[('殷主','被闽国旧臣请求回福州')],when='945年正月福州政变后，具体日未载',place='福州至建州',note='迎请是请求，王延政下一句尚未迁都，不写实际已经回福州。')
add('yanzheng_restores_min_name','王延政将国号由殷改回闽',10,'改国号','曰闽。',[('殷主','将殷国国号改为闽')],when='945年正月条下，具体日未载',place='建州、闽国',note='改国号与另立新君区分，王延政仍是同一主体。')
add('yanzheng_defers_fuzhou_capital','王延政因南唐军来攻，暂未迁都福州',10,'延政以','徙都，',[('殷主','因南唐来攻而暂未迁都福州')],when='945年正月条下',place='建州',note='未暇徙都是未执行迁都，不能由旧臣迎请推实际已迁都。')
add('wang_jichang_fuzhou_command','王延政任王继昌都督南都诸军事，驻福州',10,'以从子门下侍郎、','镇福州；',[('殷主','任从子王继昌都督南都内外诸军事，驻福州'),('继昌','以门下侍郎、同平章事身份驻福州，总督南都军务')],when='945年正月条下',place='福州')
sup('wang_jichang_fuzhou_command',10,minbook,'延政遣其從子繼昌守福州。','《新五代史》也记王延政派从子王继昌守福州。','只补本次任官守城，传记后续李仁达杀继昌留下一段，不提前写已死。')
relationship('继昌','殷主','族侄',10,'以从子门下侍郎、同平章事继昌都督南都内外诸军事，镇福州；','王继昌是王延政的从子，记录族中侄辈；父亲姓名与具体亲支未列，不补父子关系。')
add('huang_renfeng_supports_fuzhou','王延政任黄仁讽为镇遏使，率军支援王继昌',10,'以飞捷指挥使黄仁讽','后卫之。',[('殷主','任黄仁讽为镇遏使，令其率军为王继昌后援'),('黄仁讽','由飞捷指挥使任镇遏使，率军为王继昌后援')],when='945年正月条下',place='福州',note='之承接王继昌，未补援军人数或行军路线。')
add('lin_renhan_receives_small_reward','林仁翰到福州后受王延政薄赏，未曾自夸功劳',10,'林仁翰至','其功。',[('林仁翰','到福州后获薄赏，没有自述功劳'),('闽主','给林仁翰的赏赐很少')],when='945年正月条下',place='福州',note='原文王延政赏之不证明王本人在福州现场，王尚未迁都；未曾自言其功是书内评价。')
add('fuzhou_troops_sent_jianzhou','闽国调南都侍卫及两军一万五千甲士赴建州抗唐',10,'发南都侍卫',None,[('闽主','调福州兵一万五千赴建州抵抗南唐')],when='945年正月条下',place='福州至建州',note='一万五千为原载调兵数，两军未列军名不虚构；后续被杀留七月对应段。')
# 11: imperial itinerary and a strategic criticism.
add('shi_arrives_huazhou','石重贵到达滑州',11,'二月，','至滑州，',[('帝','抵达滑州')],when='945年二月壬辰朔；旧本纪记戊辰朔',place='滑州',note='主书月朔壬辰与旧史戊辰不同，保留纪日异文，不自行计算并改字。')
sup('shi_arrives_huazhou',11,feb,'二月戊辰朔，車駕次滑州。','《旧五代史》记二月戊辰朔皇帝驻滑州。','与主书壬辰朔字不同，不能假定双方都是两个不同月朔，待纸本核对。',relation='conflicts',field='time_original')
extra('shi_visits_liyang_troops','石重贵渡浮桥到黎阳慰军，当晚回滑州',11,feb,'己巳，渡浮橋，幸黎陽勞軍，至晚還滑州。',[('帝','渡浮桥到黎阳慰军，晚间返回滑州')],when='945年二月己巳',place='滑州至黎阳再回滑州',note='这是旧本纪补充行程，与下一段离滑赴澶是不同阶段。')
sup('shi_visits_liyang_troops',11,newyear,'二月己巳，幸黎陽。','《新五代史》也记二月己巳皇帝到黎阳。','只印证赴黎阳，返滑细节来自旧史。')
add('an_shenqi_yedu_order','石重贵命安审琦驻军邺都',11,'壬申，','屯鄴都。',[('帝','命安审琦驻邺都'),('安审琦','奉诏驻军邺都')],when='945年二月壬申',place='邺都')
add('shi_leaves_huazhou','石重贵离开滑州继续北行',11,'甲戌，','发滑州；',[('帝','从滑州出发继续北行')],when='945年二月甲戌',place='滑州至澶州')
sup('shi_leaves_huazhou',11,feb,'甲戌，幸澶州，','《旧五代史》将赴澶州的行动记在甲戌。','主书甲戌发滑州、乙亥到澶州，可能为离京和到达不同阶段，保留各书表述，不强改成同一天。',relation='adds',field='time_original')
add('shi_arrives_chanzhou','石重贵到达澶州',11,'乙亥，','至澶州。',[('帝','到达澶州')],when='945年二月乙亥',place='澶州')
add('ma_armies_move_north','马全节等各军依次北上',11,'己卯，','北上。',[('马全节','与各军依次北上')],when='945年二月己卯',place='河北',note='具体各军先后与到达地未列，不补精确行军表。')
sup('ma_armies_move_north',11,feb,'戊寅，北面行營副招討使馬全節、行營都監李守貞、右神武統軍張彥澤等以前軍先發。','《旧五代史》写戊寅马全节、李守贞、张彦泽等以前军先行。','主书己卯各军依次北上与前军戊寅先发可为不同阶段，保留所载行程，不另造第二次同一军出发。',relation='adds')
add('liu_criticizes_offensive','刘知远认为中原疲弊，反对主动挑起与契丹大战',11,'刘知远闻之',None,[('刘知远','得知大军北上后，批评疲弊时主动挑战契丹的策略')],when='945年二月晋军北上时',place='河东',note='这是刘知远的战略评价，不写成皇帝已采纳停止亲征。')
# 12: a sortie exploited by the enemy, refusal to submit, and the fall of Qizhou.
add('shen_bin_sortie_qizhou','沈斌见契丹弱兵赶牛羊经过祁州，出兵攻击',12,'契丹自恒州还，','出兵击之；',[('沈斌','以祁州刺史身份出兵攻击城下经过的契丹兵')],when='945年，主书接二月条下；城陷另有三月戊戌记载',place='祁州',note='羸兵驱牛羊是所见，不一定真实反映契丹军整体弱势；原文未明确说故意诱敌，不自行补谋略。')
sup('shen_bin_sortie_qizhou',12,shen,'斌以謂契丹深入晉地而歸兵羸乏可擊，即以州兵邀之。','《新五代史》补记沈斌认为深入后撤的契丹兵疲弱可攻，因此率州兵迎击。','这是沈斌的判断，不写成准确侦察出的全部敌兵状态。',relation='adds')
claim('person',people['沈斌'],'description','沈斌字安时，为徐州下邳人，早年为军卒，曾任梁拱辰都指挥使。',12,'沈斌字安時，徐州下邳人也。少為軍卒，事梁為拱辰都指揮使。','军将身份与主书下邳祁州刺史相符，不与后世同名文人合并；字与籍贯据本传，不补出生年月。',source=origin)
claim('person',people['沈斌'],'description','沈斌后来侍奉后唐，随魏王李继岌伐蜀、平康延孝，因功任虢州刺史，后来历任随州、赵州等八州刺史。',12,'後事唐，從魏王繼岌破蜀，平康延孝，以功為虢州刺史，歷隨、趙等八州刺史。','本传补早年履历，不能把这些官任系945年；魏王继岌沿用已知后唐皇子身份。',source=origin)
claim('person',people['沈斌'],'description','沈斌于开运元年任祁州刺史。',12,'晉開運元年，為祁州刺史。','这是944年的任职，并非945年新任；本批作为人物履历补证，不另造944年精确任命日。',source=shen)
add('khitan_seizes_qizhou_gate','契丹精骑夺祁州城门，外出的州兵无法返回',12,'契丹以精骑','不得还。',[('沈斌','其外出州兵因契丹夺门而无法回城')],when='945年祁州城陷之前，具体日未列',place='祁州城门')
sup('khitan_seizes_qizhou_gate',12,shen,'契丹以精騎剗門，斌兵多死，城中無備，','《新五代史》还记沈斌州兵大量死亡，城中没有防备。','多死未列人数，不将所有州兵写成全灭。',relation='adds')
add('zhao_attacks_qizhou','赵延寿得知祁州无余兵，率契丹军急攻',12,'赵延寿知','急攻之；',[('赵延寿','得知祁州缺少守兵后领契丹军急攻')],when='945年祁州城陷之前',place='祁州')
add('zhao_urges_shen_surrender','赵延寿以旧交身份劝沈斌投降',12,'斌在［城］上，','不早降！”',[('赵延寿','称与沈斌有旧交，劝其早降'),('沈斌','在城上受到赵延寿劝降')],when='945年祁州城陷之前',place='祁州城上',note='吾之故人为当事人说辞，不据此新建确定的终身好友关系；［城］保留底本标记。')
add('shen_refuses_surrender','沈斌斥责赵延寿父子引敌攻国，拒绝投降',12,'斌曰：','公所为！”',[('沈斌','拒绝投降，称宁可为国家而死'),('赵延寿','被沈斌斥责带契丹兵侵扰故国')],when='945年祁州城陷之前',place='祁州城上',note='指责话语有主语归属，弓折矢尽为沈斌言辞，不另补所有城防武器精确耗尽数字。')
add('qizhou_falls','契丹攻陷祁州',12,'明日，','城陷，',[('赵延寿','其率领的契丹军攻陷祁州'),('沈斌','所守祁州陷落')],when='945年劝降次日；新旧五代史及辽史记三月戊戌',place='祁州',note='主书接二月条下并写明日，其他书给三月戊戌；不自行换算公历或覆盖相对日。')
sup('qizhou_falls',12,mar,'三月戊戌，契丹陷祁州，刺史沈斌死之。','《旧五代史》记三月戊戌祁州陷落、沈斌死。','城陷与死亡在同句，具体死亡方式另据主书与传记；日期与主书上下文差别保留。',relation='adds',field='time_original')
sup('qizhou_falls',12,newyear,'三月戊戌，契丹陷祁州，刺史沈斌死之。','《新五代史》本纪也记三月戊戌祁州陷落。','新旧史本纪相同日期独立保存出处，不以一致强删主书相对记时。',relation='adds',field='time_original')
add('shen_bin_dies_qizhou','祁州陷落后沈斌死亡，主书记为自杀',12,'明日，','斌自杀。',[('沈斌','祁州陷落后死亡，主书记为自杀')],when='945年祁州陷落时；主书写劝降次日，诸本纪记三月戊戌',place='祁州',note='主书及新传自杀与辽史杀其刺史有异说，标题保留核心死亡事实并说明版本，不造两次死亡。')
sup('shen_bin_dies_qizhou',12,shen,'已而城陷，斌自盡，其家屬皆沒于虜。','《新五代史》也记沈斌在城陷后自尽，其家属全部落入契丹控制。','没于虏在此指被敌方控制，不能翻成家属全被杀；家属另录事件。')
sup('shen_bin_dies_qizhou',12,liao,'三月戊戌，師拔祁州，殺其刺史沈斌。','《辽史》记三月戊戌攻下祁州后杀其刺史沈斌。','死因行动者与主书及新传的自尽不同，保留异说不调和成强定的先自杀后杀。',relation='conflicts')
claim('person',people['沈斌'],'death_year','沈斌于945年祁州陷落时死亡。',12,'明日，城陷，斌自杀。','死亡事实有主书及新旧史，方式与具体日期分别保留异说，未补年龄。')
extra('shen_family_captured','祁州陷落后沈斌家属被契丹控制',12,shen,'已而城陷，斌自盡，其家屬皆沒于虜。',[('沈斌','死后其家属全部落入契丹控制')],when='945年祁州陷落后，传记未单列日',place='祁州',note='家属未具名不建虚构人物，没于虏不作全家阵亡。')
# 13–14: reinforcements and division of political power.
add('du_wei_joins_ma_advance','石重贵命杜重威率本镇兵与马全节等会合进军',13,'丙戌，',None,[('帝','命杜重威率本镇军会马全节等进军'),('杜威','以北面行营都招讨使身份领本镇兵会军'),('马全节','获令与杜重威会合进军')],when='945年二月丙戌',place='恒州及后晋北面行营',note='杜威是杜重威避少帝名的称呼；命会兵不补本句未载实际会合日期。')
sup('du_wei_joins_ma_advance',13,feb,'詔恒州杜威與馬全節等會合進軍。','《旧五代史》也记诏恒州杜威与马全节等会合进军。','该句位于辛巳与丙戌之间，未单列干支；不能反推正好丙戌发令，保留主书具体日。')
add('feng_li_slander_sang','冯玉、李彦韬倚仗皇帝宠信，多次诋毁桑维翰',14,'端明殿学士、','数毁之。',[('冯玉','与李彦韬倚皇帝宠信、反对并多次诋毁桑维翰'),('李彦韬','以宣徽北院使、暂代侍卫马步都虞候身份与冯玉诋毁桑维翰'),('桑维翰','遭冯玉和李彦韬多次诋毁')],when='945年冯玉任枢密使前，具体日未列',place='后晋朝廷',note='此李彦韬是太原籍晚晋近臣，与已在明宗时被赐死的温韬另行建档；政治冲突只限当前记事，不建终身仇敌。')
sup('feng_li_slander_sang',14,sang,'內客省使李彥韜、端明殿學士馮玉用事，共讒之。','《新五代史》桑维翰传也记李彦韬、冯玉共同诋毁桑维翰，李彦韬官衔写内客省使。','内客省使为该传官称，与主书当前宣徽北院使分别保留，不忽略已任官迁转，也不与温韬合并。',relation='adds')
claim('person',people['李彦韬（后晋宣徽使）'],'description','后晋宣徽使李彦韬与早期曾称李彦韬的温韬为不同人物，本站分档。',14,'明宗即位，流於德州，俄賜死。','此句传主为温韬，其早年在李茂贞部下称彦韬，且明宗时已被赐死；不能让945年石重贵近臣复用温韬主体。',source=wen)
extra('li_yantao_deputy_guards','后晋命李彦韬暂代侍卫马步都虞候',14,'jiuwudaishi-083-945-january','詔李守貞領兵屯滑州，以宣徽北院使李彥韜權侍衛馬步都虞候。',[('李彦韬','以宣徽北院使身份暂代侍卫马步都虞候')],when='945年正月甲寅相关任官条下',place='后晋朝廷',note='本事件实际记录暂代侍卫都虞候，宣徽北院使是已任身份，不当成正月再次授宣徽使。',description='后晋命已任宣徽北院使的李彦韬暂代侍卫马步都虞候。')
add('shi_considers_dismiss_sang','石重贵想罢免桑维翰的政务职权',14,'帝欲罢','政事，',[('帝','有意罢免桑维翰政务职权'),('桑维翰','面临罢免政务职权的打算')],when='945年冯玉任枢密使前',place='后晋朝廷',note='欲罢是打算，下一句劝止，不能写成已经完全免职。')
add('li_liu_prevent_sang_dismissal','李崧、刘昫力谏，阻止罢免桑维翰',14,'李崧、','而止。',[('李崧','与刘昫坚持劝阻皇帝罢免桑维翰'),('刘昫','与李崧劝止罢免桑维翰'),('帝','在李崧、刘昫力谏后停止罢免打算')],when='945年冯玉任枢密使前',place='后晋朝廷')
sup('li_liu_prevent_sang_dismissal',14,sang,'帝欲驟黜維翰，大臣劉昫、李崧皆以為不可，','《新五代史》也记刘昫、李崧反对骤然罢黜桑维翰。','只补当前劝阻，传记后文实际罢维翰为开封尹留年末，不提前。')
add('sang_proposes_feng_deputy','桑维翰知受谗后，请任冯玉为枢密副使，冯玉不满',14,'维翰知之，','不平。',[('桑维翰','请求任冯玉为枢密副使'),('冯玉','对枢密副使的拟任很不满')],when='945年二月丙申正式任命前',place='后晋朝廷',note='请以副使不等于实际任副使，实际任枢密使另录。')
add('feng_yu_shumishi','石重贵以宫中诏命任冯玉为户部尚书、枢密使',14,'丙申，','之权。',[('帝','以宫中诏命任冯玉为户部尚书、枢密使，分桑维翰权力'),('冯玉','获任户部尚书、枢密使'),('桑维翰','其枢密职权因冯玉任命而被分掌')],when='945年二月丙申',place='后晋朝廷',note='中旨保留皇帝宫中发命的含义；分权不等于此日桑维翰已经被罢全部职位。')
sup('feng_yu_shumishi',14,feb,'丙申，以端明殿學士、尚書戶部侍郎馮玉為戶部尚書，充樞密使。','《旧五代史》同记二月丙申任冯玉为户部尚书、枢密使。','原任端明殿学士、户部侍郎与新任官职区分。')
sup('feng_yu_shumishi',14,newyear,'丙申，端明殿學士、尚書戶部侍郎馮玉為戶部尚書、樞密使。','《新五代史》本纪也记丙申此项任命。','保留独立本纪定位，不取其后八月宰相任命当本日已发生。')
add('li_yantao_serves_yanbao','李彦韬早年为阎宝随从，后来进入石敬瑭帐下',14,'彦韬少事阎宝，','帐下。',[('李彦韬','早年侍奉阎宝，后转入石敬瑭帐下'),('阎宝','早年曾受李彦韬侍奉'),('高祖','后来将李彦韬收入帐下')],when='追述早年，具体年月未载',year=None,place='阎宝与石敬瑭军中',note='早年经历不系945年；无证据建父子或养父子，仆夫为侍从身份。')
add('shi_jingtang_leaves_yantao_chonggui','石敬瑭从太原南下时，留下李彦韬侍奉石重贵',14,'高祖自太原南下，','有宠。',[('高祖','南下时留下李彦韬侍奉石重贵'),('李彦韬','留在太原侍奉石重贵，成为亲信'),('帝','受到李彦韬侍奉，后来宠信他')],when='追述石敬瑭从太原南下时，原句未列年日',year=None,place='太原',note='高祖为石敬瑭，帝为石重贵；不将亲信人物写成在945年才开始侍奉，也不靠背景自动定日。')
add('li_yantao_influences_appointments','李彦韬与受宠近臣结交，参与将相升黜议论',14,'性纤巧，','得预议。',[('李彦韬','与受宠近臣结交，获得皇帝信任，参与将相升黜'),('帝','信任李彦韬，使其参与高官任免议论')],when='石重贵统治时的持续情形，具体始末年未列',year=None,place='后晋朝廷',note='纤巧、蔽耳目为史书评价，参与任免不同于李彦韬可独自决定所有官任。')
add('li_yantao_wants_remove_civil_officials','李彦韬扬言不知文官何用，想逐步全部撤去',14,'常谓人曰：',None,[('李彦韬','扬言要逐步撤去文官')],when='石重贵统治时期，具体年月未载',year=None,place='后晋朝廷',note='这是其言辞和打算，没有记载实际废除全部文官，不当已实施制度改革。')
# 15: the Jianzhou reinforcement, forced engagement and a defensive response.
add('cha_requests_more_troops','查文徽上表请求增兵',15,'唐查文徽','益兵，',[('查文徽','向李璟上表请求增兵'),('唐主','收到查文徽增兵请求')],when='945年二月条下，具体日未载',place='建州战场至南唐朝廷')
add('he_jingshu_campaign_command','李璟任何敬洙为建州行营招讨马步都指挥使',15,'唐主以天威都虞候何敬洙','都指挥使，',[('唐主','任命何敬洙为建州行营招讨马步都指挥使'),('何敬洙','由天威都虞候任建州行营招讨马步都指挥使')],when='945年二月条下',place='南唐朝廷、建州')
add('zu_quanen_relief_command','李璟任祖全恩为应援使',15,'将军祖全恩','应援使，',[('唐主','任祖全恩为应援使'),('祖全恩','以将军身份获任应援使')],when='945年二月条下',place='南唐朝廷、建州')
add('yao_feng_campaign_monitor','李璟任姚凤为都监',15,'姚凤','为都监，',[('唐主','任姚凤为建州战场都监'),('姚凤','获任都监，随军增援建州战场')],when='945年二月条下',place='南唐朝廷、建州')
add('tang_troops_chong_an_chiling','何敬洙、祖全恩、姚凤率数千兵增援，自崇安进驻赤岭',15,'将兵数千','赤岭。',[('何敬洙','与祖全恩、姚凤率数千兵增援，自崇安进驻赤岭'),('祖全恩','与何敬洙、姚凤率兵增援并进驻赤岭'),('姚凤','随何敬洙、祖全恩增援建州战场')],when='945年二月条下',place='崇安至赤岭',note='数千为三将所领的合计概数，不拆为各人数千；攻建州不是当时建州已经陷落。')
add('yang_chen_defend_south_water','王延政派杨思恭、陈望率万人抵御，在水南立营栅',15,'闽主延政遣','列栅水南，',[('闽主','派杨思恭和陈望率万人抵御南唐'),('杨思恭','以仆射身份与陈望率军，在水南立栅'),('陈望','以统军使身份领军抵御，在水南布营')],when='945年二月条下',place='建州战场水南',note='水名本句未列，不自动指定为建溪某一现代河段。')
add('jianzhou_ten_days_standoff','闽军与南唐军十余日未战，南唐不敢逼近',15,'旬馀','不敢逼。',[('陈望','所领闽军与南唐军对峙十余日'),('何敬洙','所属南唐军在对峙时未敢逼近')],when='945年二月，十余日对峙；起止日未载',place='建州战场水南',note='旬余不换算精确开始日，唐人未具名单不编出每个主将各自惧怕的心理。')
add('yang_demands_chen_attack','杨思恭依据王延政之命，督促陈望出战',15,'思恭以','督望战。',[('杨思恭','奉王延政之命督促陈望出战'),('陈望','受到杨思恭出战督促'),('闽主','下命要求出战，由杨思恭传督')],when='945年二月对峙后',place='建州战场')
add('chen_warns_tang_strength','陈望指出南唐军精锐、将领熟兵，主张慎重交战',15,'望曰：','后动。”',[('陈望','认为南唐军精锐，国家安危在此，主张准备周全再战')],when='945年二月对峙后',place='建州战场',note='这是陈望的军事判断，不推他已经下令全军退却。')
add('yang_pressures_chen_numbers','杨思恭以闽军兵多及王延政忧急为由，强逼陈望进攻',15,'思恭怒曰：','陛下乎！”',[('杨思恭','以兵数优势和王延政忧虑为由，催逼陈望进攻'),('陈望','面对杨思恭以兵数与君命施加的出战压力')],when='945年二月对峙后',place='建州战场',note='敌不出数千与己万余是杨思恭的说辞，不用其言辞校正前句万人为确定多出多少；寝不交睫为动员描写。')
add('chen_crosses_water_to_fight','陈望被迫率军涉水与南唐军交战',15,'望不得已，','唐战。',[('陈望','被催逼后率军涉水与南唐交战')],when='945年二月对峙后，具体日未载',place='建州战场水边',note='原文水没有实名，坐标待核；不得已为史书过程说明，不建与杨思恭长期敌对关系。')
add('tang_flanks_defeats_min','祖全恩等正面迎击并派奇兵绕后，大破闽军',15,'全恩等以大兵','大破之。',[('祖全恩','与诸军正面迎击陈望，同时以奇兵绕后击败闽军'),('陈望','所率闽军在正面及后方夹击下大败')],when='945年二月陈望出战时',place='建州战场',note='等未列全体执行将领，不把各人都推为亲自指挥奇兵；大破不同于南唐已夺建州城。')
add('chen_wang_killed','陈望在闽军败战中死亡',15,'望死，','望死，',[('陈望','在与南唐交战的败军中死亡')],when='945年二月条下，具体日未载',place='建州战场')
add('yang_sigong_escapes','杨思恭在闽军败战后仅以自身脱逃',15,'思恭仅','身免。',[('杨思恭','在闽军败战后脱逃，仅保全自身')],when='945年二月条下，具体日未载',place='建州战场',note='仅以身免不同于后来投降南唐，不能提前记为已死。')
add('yanzheng_holds_jianzhou','王延政因败战恐惧，坚守建州',15,'延政大惧，','自守，',[('闽主','得知军败后在建州闭城固守')],when='945年二月败战后',place='建州')
add('dong_wang_quanzhou_relief','王延政召董思安、王忠顺率五千泉州兵赴建州分守要害',15,'召董思安、',None,[('闽主','召董思安、王忠顺率泉州兵五千赴建州守要害'),('董思安','与王忠顺率泉州兵五千赴建州'),('王忠顺','与董思安率泉州兵赴建州分守要害')],when='945年二月败战后',place='泉州至建州',note='五千为两将所率合计，不能解为每将五千；此前一万五千福州援兵是另一支。')
# 16: the earlier fort and its new construction.
add('shi_jingtang_establishes_deqing','石敬瑭曾在澶州旧城设德清军',16,'初，','故澶州城，',[('高祖','在澶州旧城设德清军')],when='此前；旧本纪可定位天福六年八月（941），本句追述未单列日',year=941,place='澶州旧城',note='初为追述，年月由独立旧本纪天福六年八月支持，不系945年新设。')
sup('shi_jingtang_establishes_deqing',16,deqing,'己亥，至鄴，左右金吾六軍儀仗排列如儀，迎引入內。改舊澶州為德清軍。','《旧五代史》在天福六年八月己亥到邺相关条下记改旧澶州为德清军。','独立本纪提供941年八月上下文，改军句未再次列日，时间解释保留相关条下。',relation='adds',field='time_original')
add('khitan_overruns_chan_ye_forts','契丹进攻后，澶州与邺都之间城堡驻地陷落',16,'乃契丹入寇，','俱陷。',[],when='945年筑新城之前，具体月日未载',year=None,place='澶州与邺都之间',note='初段追述背景，未单列发生年，不硬写所有城戍在945年同日陷落。')
add('jin_approves_midway_fort','后晋采纳在澶州、邺都之间筑城以接应南北的建议',16,'议者以','从之。',[('帝','采纳在澶州与邺都中途筑城的建议')],when='945年三月筑城前，建议具体日未载',place='澶州与邺都之间',note='相距五十里是史书说法，不据此给出未核现代坐标；建议者未具名。')
add('jin_rebuilds_deqing','后晋重筑德清军城，将德清、南乐居民合并安置于城中',16,'三月，',None,[('帝','采纳筑城方案后重筑德清军，并调居民充实城内')],when='945年三月戊戌',place='德清军城',note='合民以实之是居民移置充城，不推两地行政完全合并或确定户数；941年设军与945年重筑分开。')
claim('person',people['陈望'],'death_year','陈望于945年建州附近与南唐交战时死亡。',15,'望死，','陈望在前文明确为统军使，望死承接败战；不将随后逃脱的杨思恭也记为死。')
reviews={9:'降者说法与出兵建议区分，征兵、亲征诏令和离京分录；壬戌辛酉诏令异说并列，乙丑离京两纪印证。',10:'迎请与实际未迁都、改国号和王继昌驻福州分开。族侄不补父名，黄仁讽后卫对象识别继昌；赏林仁翰不推王本人在福州，福州一万五千援建与下文泉兵五千不混。',11:'壬辰朔与戊辰朔不同保留，滑州黎阳往返、离滑到澶、安审琦派军和诸军北上分阶段，刘知远战略评论不当皇帝采纳。',12:'沈斌为下邳军将有新传职历相合，不与后世文人合并。主书二月条下与诸纪三月戊戌、主新传自杀与辽被杀分别保留；家属没于虏是被控制不是全家死亡。',13:'杜威复用杜重威，诏会本道兵是派令，未补具体会军日；旧本纪同事未单独列干支，不反套丙戌。',14:'侍奉石重贵的太原李彦韬与早期温韬别名另分，温明宗时已死；政治谗言、欲罢、劝止、建议副使和实际枢密使任命分阶段。早年和持续事况年未知留空，去文官是言辞而非执行。',15:'请求增兵、三将各任、数千援军、水南万人布营、十余日对峙、奉命督战、谨慎主张、催逼与夹击结果分开。陈望死杨思恭逃不同，建州只是固守未陷，泉州五千援兵与福州万五千分开。',16:'德清设军941由旧本纪独立支持，初段城戍陷落未确年留空；建议中途筑城与三月戊戌实际重筑区别，不推行政合县、兵数或现代精确坐标。'}
assert not (P/'publication.json').exists()
for n in range(9,17):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=284,year=945,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],next_volume=284,next_year=945,supplements=supplements,excluded_non_body=[],coverage='卷284原60—67行连续第9—16段，正月至三月及追述；下一段李仁达与福州政变。945年全年未完成。',source_contexts=[dict(source_key=key,note=note) for key,note in [(main_sources[0],'只处理第9—14段，前8段已发表不重建。'),(main_sources[1],'只处理第15—16段，快照内之后福州政变、北军进退和阳城战事留后续。'),(jan,'只补亲征诏令、离京和当前晚晋李彦韬暂代军职，之前布防战事已录不重建。'),(minbook,'只补继昌守福州，后文继昌遇害留下一段。'),(mar,'本次只取祁州陷落与沈斌死亡日期，后文阳城等战事留后续。'),(sang,'只取冯李谗桑、刘李谏止，后文年末桑免职未提前。'),(wen,'只用于区别温韬和晚晋李彦韬，不重建早期温韬事件。'),(deqing,'只补941年设德清军的独立纪年，不重建其他当年诏令。')]],source_issues_review='亲征壬戌辛酉、二月壬辰戊辰朔、祁州陷落相对日与三月戊戌分别保留。沈斌自尽与辽史杀其刺史异说独立。温韬早期李彦韬别名与晚晋同名人严格分档；同名保护只将晚晋人别名限定身份，不复活已合并旧主体。纸本与史源依赖待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,17)],plain_language_review='首次逐条核对标题、人物、事件、参与、关系、日期与事实说明，说明简体白话且主语明确；将计划、派令、忧虑、评价、战果、被俘、死亡及异说分开，引用保留底本原字。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
