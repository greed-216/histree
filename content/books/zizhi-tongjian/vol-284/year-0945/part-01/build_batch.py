# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 284, year 944 year 945 paragraphs 1–8."""
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
COMMIT='ac10110d193f69ce3499423e4fa4db294584e2ff'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='xinwudaishi-050-zhe-origins']
for key in ['tongjian-284-944-leap','xinwudaishi-050-zhe-congruan']:
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
main_sources = ['tongjian-284-944-leap','tongjian-284-945-january']
B = {'format_version': 1, 'batch_key': 'zztj-v284-y0945-p001-p008',
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
for n in range(1, 9):
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
        citation = f'卷284·后晋开运二年（945年正月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_284_0945_01_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'石重贵','契丹主':'耶律德光','折从阮':'折从远'})
NEW_ALIASES={'慕容彦超':['慕容彥超'],'杜知敏':[],'符彦伦':['符彥倫']}
NEW_DESCRIPTIONS={
 '慕容彦超':'后晋濮州刺史，原属吐谷浑，与刘知远同母。945年正月随皇甫遇侦察契丹军，在榆林店受围，与皇甫遇共同救回杜知敏，得到安审琦援军后返回相州。出生及死亡年本段未载。',
 '杜知敏':'皇甫遇的随从。945年榆林店交战中，将自己的马给皇甫遇，之后被契丹俘获，又被皇甫遇与慕容彦超救回。生卒年本段未载。',
 '符彦伦':'945年正月知相州事。张从恩等退军后将安阳桥守兵收进相州，鼓噪示警，又派五百甲士在城北戒备，契丹最终退走。与符彦卿、符彦饶分别识别，生卒年本段未载。'}
old='jiuwudaishi-083-945-january';ob='jiuwudaishi-095-huangfu-yu-battle';nb='xinwudaishi-047-huangfu-yu-battle';nj='xinwudaishi-009-945';liao='liaoshi-004-945-january';zhe='xinwudaishi-050-zhe-congruan'
# 1: troop assignments, an alarm report, and the Khitan advance.
add('zhao_zaili_returns_chanzhou','石重贵命赵在礼回驻澶州',1,'春，正月，','还屯澶州，',[('帝','命赵在礼回驻澶州'),('赵在礼','奉诏回驻澶州')],when='945年正月，主书本句未列日；旧本纪己亥条下',place='邺都至澶州')
sup('zhao_zaili_returns_chanzhou',1,old,'己亥，張從恩部領兵士自邢州退至相州，人情震恐。趙在禮還屯澶州，馬全節歸鄴都，','《旧五代史》将赵在礼回澶州、马全节回邺都记在己亥相关调军条下。','此前邢州退军已在944年末处理，此处只补回驻日期上下文，不重建旧过程。',relation='adds',field='time_original')
add('ma_quanjie_returns_yedu','石重贵命马全节回驻邺都',1,'马全节还','鄴都；',[('帝','命马全节回邺都'),('马全节','奉诏回邺都')],when='945年正月，主书未列日；旧本纪己亥条下',place='相州方向至邺都')
add('zhang_yanze_liyang','石重贵派张彦泽驻军黎阳',1,'又遣右神武统军张彦泽','屯黎阳，',[('帝','派张彦泽驻军黎阳'),('张彦泽','以右神武统军身份赴黎阳驻军')],when='945年正月，主书未列日；旧本纪己亥条下',place='黎阳')
sup('zhang_yanze_liyang',1,old,'遣右神武統軍張彥澤屯黎陽，','《旧五代史》也记派右神武统军张彦泽屯黎阳。','驻黎阳与后段趣相州是两个阶段。')
add('jing_yanguang_huliang_guard','石重贵命景延广由滑州引军守胡梁渡',1,'西京留守景延广','胡梁渡。',[('帝','命景延广率军守胡梁渡'),('景延广','以西京留守身份从滑州引兵守胡梁渡')],when='945年正月，主书未列日；旧本纪己亥条下',place='滑州至胡梁渡')
sup('jing_yanguang_huliang_guard',1,old,'詔西京留守景延廣將兵守胡梁渡。','《旧五代史》也记诏景延广守胡梁渡。','保留史载渡口，坐标未核。')
add('zhang_reports_xingzhou_alarm','张从恩奏报契丹迫近邢州',1,'庚子，','邢州，',[('张从恩','奏报契丹逼近邢州'),('帝','收到邢州告急奏报')],when='945年正月庚子',place='邢州至后晋朝廷',note='庚子为奏报日，不直接规定契丹抵达日。')
add('jin_orders_renewed_advance','石重贵命滑州和邺都部队再进军抵御契丹',1,'诏滑州，','拒之。',[('帝','命滑州和邺都再次进军抵御契丹')],when='945年正月庚子条下',place='滑州、邺都至邢州方向')
add('huangfu_yu_to_xingzhou','皇甫遇率军赶往邢州',1,'义成节度使皇甫遇','邢州。',[('皇甫遇','以义成节度使身份领兵赴邢州')],when='945年正月庚子条下；旧本纪乙巳记诏令',place='滑州至邢州',note='滑州节度使与义成军节度使在同一军镇识别；主书行动条下与旧本纪派军诏令日期分开。')
sup('huangfu_yu_to_xingzhou',1,old,'乙巳，帝復常膳。以左武衛上將軍袁{山義}為客省使，上將軍如故。詔滑州節度使皇甫遇率兵赴邢州，馬全節赴相州。','《旧五代史》在正月乙巳条下记诏皇甫遇赴邢州、马全节赴相州。','只补具名派军诏令日期与地点，不录同句未解析字形的袁氏任官。',relation='adds',field='time_original')
add('khitan_raids_xing_ming_ci','契丹攻掠邢、洺、磁三州，进入邺都境内',1,'契丹寇邢、','鄴都境。',[],when='945年正月庚子条下',place='邢州、洺州、磁州、邺都境内',note='杀掠殆尽是史书程度描述，不补全部居民死亡的精确人口数。')
sup('khitan_raids_xing_ming_ci',1,liao,'八年春正月庚子，分兵攻邢、洺、磁三州，殺掠殆盡。入鄴都境。','《辽史》会同八年正月庚子也记分兵攻掠邢、洺、磁并进入邺都境。','表述与通鉴近似，可能存在史源依赖，独立列出处但不当作完全独立确证。',relation='adds',field='time_original')
# 2: scouting, fierce fighting, rescue of a servant and of the scouting unit.
add('jin_arrays_anyang_south','张从恩、马全节、安审琦将数万行营兵列于安阳水南',2,'壬子，','之南。',[('张从恩','与马全节、安审琦领行营兵列阵安阳水南'),('马全节','与张从恩、安审琦会兵列阵'),('安审琦','与张从恩、马全节会兵列阵')],when='945年正月壬子',place='相州安阳水南',note='数万为概数，不拆各将领分别有数万。')
sup('jin_arrays_anyang_south',2,old,'壬子，王師與契丹相拒於相州北安陽河上，','《旧五代史》同记正月壬子双方在相州北安阳河上相拒。','水名河名分书保留，不自动补现代河流坐标。')
add('huangfu_murong_scout','皇甫遇、慕容彦超率数千骑侦察契丹军',2,'皇甫遇与','前觇契丹，',[('皇甫遇','与慕容彦超率数千骑侦察契丹军'),('慕容彦超','以濮州刺史身份随皇甫遇率骑兵侦察')],when='945年正月壬子',place='相州至邺县',note='觇是侦察，不建双方已经达成和议的使行事件。')
sup('huangfu_murong_scout',2,liao,'皇甫遇與濮州刺史慕容彥超將兵千騎來覘遼軍。','《辽史》记侦察骑兵为千骑，《资治通鉴》和《新五代史》写数千骑。','兵数不同分别保留，不按多数文本强定精确兵数。',relation='conflicts')
add('huangfu_murong_fighting_retreat','皇甫遇、慕容彦超在邺县遇契丹数万兵，边战边退',2,'至鄴县，','且战且却。',[('皇甫遇','欲渡漳水时遇数万契丹军，边战边退'),('慕容彦超','与皇甫遇边战边退')],when='945年正月壬子',place='邺县、漳水附近')
sup('huangfu_murong_fighting_retreat',2,nb,'遇渡漳河，逢虜數萬，轉戰十餘里，至榆林，為虜所圍，','《新五代史》记皇甫遇渡漳河遇契丹军，转战十余里到榆林被围。','主书将渡、新史渡河，渡河阶段略异，分别保留，不由十余里推精确坐标。',relation='adds')
sup('huangfu_murong_fighting_retreat',2,ob,'轉鬥二十里至鄴南榆林店。','《旧五代史》皇甫遇传记转战二十里到邺南榆林店。','与新史十余里不同，距离分别保存；传记以出帝在位次序记三年，与本纪开运二年纪年写法不同，不改为946年的第二战。',relation='adds')
add('yulin_two_generals_hold','皇甫遇、慕容彦超在榆林店停兵列阵，力战百余回合',2,'至榆林店，','伤甚众。',[('皇甫遇','与慕容彦超在榆林店列阵力战'),('慕容彦超','与皇甫遇自午至未力战百余回合')],when='945年正月壬子，自午至未',place='榆林店',note='双方伤亡甚众，没有各方精确损失，不补死者名单。')
sup('yulin_two_generals_hold',2,ob,'遂自辰及未，戰百餘合，所傷甚眾。','《旧五代史》皇甫遇传记自辰至未交战，主书和新史写自午至未。','时段起点不同，保留书内差异，不把辰自动改午。',relation='conflicts',field='time_original')
add('huangfu_horse_dies','皇甫遇战马死去，改为步战',2,'遇马毙，','步战；',[('皇甫遇','战马死亡后继续步战')],when='945年正月壬子交战中',place='榆林店')
sup('huangfu_horse_dies',2,old,'皇甫遇、慕容彥超率前鋒與敵騎戰於榆林店，遇馬中流矢，僅而獲免。','《旧五代史》本纪补记皇甫遇的马中了流矢。','本纪本句只说马中箭，马死还据主书及传记；不把人写成已死。',relation='adds')
add('du_zhimin_gives_horse','杜知敏将自己的马给皇甫遇，使其继续骑马作战',2,'其仆杜知敏','复战。',[('杜知敏','把自己的马交给皇甫遇'),('皇甫遇','骑杜知敏的马继续交战')],when='945年正月壬子交战中',place='榆林店')
sup('du_zhimin_gives_horse',2,nb,'遇馬中箭而踣，得其僕杜知敏馬，乘之以戰。','《新五代史》也记皇甫遇得杜知敏之马继续作战。','杜知敏身份为随从，主书仆、旧传纪纲分别保留，不凭此建血亲关系。')
add('du_zhimin_captured','杜知敏在榆林店交战中被契丹俘获',2,'久之，','契丹所擒，',[('杜知敏','在交战中被契丹俘获')],when='945年正月壬子交战中',place='榆林店')
add('two_generals_rescue_du','皇甫遇、慕容彦超冲入契丹阵中，救回杜知敏',2,'遇曰：“知敏','而还。',[('皇甫遇','认为不能丢下杜知敏，与慕容彦超冲阵救人'),('慕容彦超','与皇甫遇冲入契丹阵救杜知敏'),('杜知敏','被皇甫遇和慕容彦超救回')],when='945年正月壬子交战中',place='榆林店')
sup('two_generals_rescue_du',2,ob,'遂與彥超躍馬取知敏而還，敵騎壯之。','《旧五代史》也记皇甫遇与慕容彦超救回杜知敏，并称契丹骑兵赞其勇。','敌骑壮信为书内评价，不据此建双方友好关系。',relation='adds')
add('khitan_reinforces_yulin','契丹投入新的兵力，皇甫遇、慕容彦超决定死战',2,'俄而契丹','报国耳。”',[('皇甫遇','面对契丹新兵，与慕容彦超决定继续死战'),('慕容彦超','与皇甫遇决定以死报国、继续交战')],when='945年正月壬子交战中',place='榆林店',note='死战决心不等于二人当场阵亡。')
add('an_receives_scouts_trapped_report','安审琦判断侦察军被困，随后骑兵报告皇甫遇等受围',2,'日且幕，','数万所围；',[('安审琦','因侦察军未还判断其被困，随后收到受围报告')],when='945年正月壬子傍晚',place='安阳水附近',note='报告者未具名，不虚构其身份。')
add('zhang_objects_an_rescue','张从恩怀疑求援消息，劝安审琦不要前往',2,'审琦即引','公往何益！”',[('张从恩','怀疑受围消息，担忧援兵不足，反对安审琦前往'),('安审琦','准备援救皇甫遇等时受到张从恩劝阻')],when='945年正月壬子傍晚',place='安阳水附近',note='反对救援不等同后续与皇甫遇有长期仇敌关系。')
add('an_crosses_water_to_rescue','安审琦坚持救援，率骑兵渡水前进',2,'审琦曰：','而进。',[('安审琦','坚持不能丢下皇甫遇，率骑兵渡水救援')],when='945年正月壬子傍晚',place='安阳水至榆林店')
sup('an_crosses_water_to_rescue',2,nb,'即引騎渡河，諸軍皆從而北，拒虜十餘里，','《新五代史》还记安审琦渡河后其他军队跟随北上，抵抗契丹十余里。','主书只明安审琦率骑兵救援，其他军队跟随为此书补充，未编造具名将领也亲自加入。',relation='adds')
add('khitan_leaves_yulin_relieved','契丹看见援军扬尘便退去，皇甫遇等得以返回',2,'契丹望见','俱归相州，',[('皇甫遇','获安审琦救援后与诸将返回相州'),('慕容彦超','获救后与皇甫遇返回相州'),('安审琦','救回两将并一同返回相州')],when='945年正月壬子傍晚',place='榆林店至相州')
sup('khitan_leaves_yulin_relieved',2,ob,'遇與彥超中數創得還，時諸軍嘆曰：「此三人皆猛將也！」','《旧五代史》补记皇甫遇、慕容彦超身中数处伤仍返回，诸军赞三人为猛将。','数创没有具体伤位，不补医疗细节，三人指含援救者安审琦。',relation='adds')
claim('person',people['慕容彦超'],'description','慕容彦超原属吐谷浑，与刘知远同母。',2,'彦超本吐谷浑也，与刘知远同母。','族属与同母关系原文明示，不补母亲姓名或两人长幼。')
relationship('慕容彦超','刘知远','兄弟',2,'彦超本吐谷浑也，与刘知远同母。','二人为同母兄弟，长幼本段未载，保留对称兄弟关系，不强定哥哥弟弟。')
# 3–4: both sides withdraw; Xiangzhou faces and deters a returning force.
add('khitan_alarm_of_jin_army','契丹军退却时互相惊传晋军全来了',3,'契丹亦','悉至矣！”',[],when='945年正月榆林交战后',place='榆林店附近',note='晋军悉至是惊慌传言，不写成后晋所有部队确已到场。')
add('yelu_flees_handan_gucheng','耶律德光在邯郸闻讯，连夜北退到鼓城',3,'时契丹主','至鼓城。',[('契丹主','在邯郸听到惊传后急退至鼓城')],when='945年正月榆林交战后，途中未再停宿',place='邯郸至鼓城',note='不再宿只支持急行，没有精确出发到达时刻。')
sup('yelu_flees_handan_gucheng',3,old,'戎王在邯鄲聞之，即時北遁，官軍亦南保黎陽。','《旧五代史》也记契丹主在邯郸闻讯北退，晋军同时南保黎阳。','双方撤退情况分别记，不解成后晋已进占契丹本土。')
sup('yelu_flees_handan_gucheng',3,nj,'壬子，馬全節及契丹戰于榆林，兩軍皆潰。','《新五代史》本纪以两军皆溃概括壬子榆林交战后的双方撤退。','这是该书对整体结果的概括，和主书救回两将的具体过程分别保留，不能用救援局部成功推整场战争大胜。',relation='adds')
add('zhang_proposes_liyang_food','张从恩等担忧相州粮不足十日，讨论退往黎阳仓',4,'是夕，','议未决，',[('张从恩','担忧城中粮不足十日，讨论退到黎阳仓倚河防守')],when='945年正月壬子交战后当晚',place='相州',note='缺粮与潜在泄密围城风险是军议理由；万一奸人告敌是设想，不当已发生间谍事件。')
add('zhang_first_leaves_xiangzhou','军议未决，张从恩先引军撤走，诸军跟随并发生混乱损失',4,'从恩引兵先发，','邢州之时。',[('张从恩','军议未决便先引军撤出相州'),('马全节','诸军随后退至黎阳，混乱发生')],when='945年正月壬子交战后当晚',place='相州至黎阳',note='马全节在本段后文明驻黎阳，与退军集体对应；扰乱失亡没有具体死者数，不把数字500解成此时死伤。')
add('jin_leaves_anyang_bridge_guard','张从恩等留下五百步兵守安阳桥',4,'从恩等留步兵','安阳桥，',[('张从恩','在撤军时留下五百步兵守安阳桥')],when='945年正月壬子交战后当晚',place='安阳桥')
add('fu_yanlun_recalls_bridge_guard','符彦伦认为五百疲兵难守桥，将其收进相州城防守',4,'夜四鼓，','乘城为备。',[('符彦伦','判断守桥兵不足，将五百人收进相州登城防守')],when='945年正月壬子之后夜四鼓',place='安阳桥至相州城',note='夜四鼓保留原计时，不换算精确现代时刻。')
sup('fu_yanlun_recalls_bridge_guard',4,old,'既而知州符彥倫與軍校謀曰：「此夜紛紜，人無固誌，五百疲兵，安能守橋！」即抽入相州，嬰城為備。','《旧五代史》也记符彦伦与军校商议后将五百守桥兵收进相州。','原文知州与主书知相州事连续识别，不与符彦卿混同。')
add('fu_yanlun_flags_drums','天明契丹数万骑列安阳水北，符彦伦令城上举旗鼓噪',4,'至曙，','契丹不测。',[('符彦伦','见契丹军列水北，命城上举旗鼓噪、整顿戒备')],when='945年正月壬子之后天明',place='相州、安阳水北',note='书内说契丹无法判断城内虚实，不录成对方永久放弃全部战争。')
sup('fu_yanlun_flags_drums',4,old,'至曙，賊軍萬餘騎已陣於安陽河北，彥倫令城上揚旗鼓噪，賊不之測。','《旧五代史》将契丹骑兵数记为万余，主书写数万。','不同概数分别保留，不强定唯一数字。',relation='conflicts')
add('zhao_crosses_anyang_water','赵延寿与一名契丹惕隐率军渡安阳水，绕相州南行',4,'日加辰，','相州而南，',[('赵延寿','与一名契丹惕隐率军渡水，绕相州南行')],when='945年正月壬子之后，日加辰',place='安阳水、相州',note='惕隐是官号，人物本段未具名，不擅自认成曾任该职的任何已有主体。')
add('zhang_yanze_to_xiangzhou','石重贵命张彦泽率军赴相州',4,'诏右神武统军','趣相州。',[('帝','命张彦泽赴相州'),('张彦泽','奉诏率兵赴相州')],when='945年正月赵延寿等渡水南下时，确日未载',place='黎阳方向至相州')
add('zhao_returns_from_tangyin','赵延寿等到汤阴，听说晋军来援后于甲寅退回',4,'延寿等至汤阴，','引还；',[('赵延寿','到汤阴后听说张彦泽来援，于甲寅率军退回')],when='945年正月甲寅',place='汤阴至相州方向',note='听闻援军不同于已经和张彦泽部发生战斗。')
add('ma_declines_pursuit','马全节等拥大军在黎阳，未追击契丹',4,'马全节等拥大军','不敢追。',[('马全节','带大军驻黎阳，未追击契丹军')],when='945年正月甲寅退军时',place='黎阳',note='不敢追为书内叙述，没有具名会议或惩处，不另造失职处分。')
add('zhao_armored_cavalry_city','赵延寿将甲骑列相州城下，作势攻城',4,'延寿悉陈','攻城状，',[('赵延寿','将甲骑列相州城下，呈将要攻城的阵势')],when='945年正月甲寅退回条下',place='相州城下',note='若将攻城状不等于实际已经破城。')
add('fu_yanlun_deters_khitan','符彦伦判断契丹将退，派五百甲士出城戒备，契丹最终退去',4,'符彦伦曰：','引去。',[('符彦伦','判断敌军要退，派五百甲士列于城北戒备'),('赵延寿','所率契丹甲骑最终退走')],when='945年正月甲寅退回条下',place='相州城北',note='此五百甲士与前夜五百步兵是否全为同一批未明确，不强认一支部队；未记实际交战杀敌数。')
sup('fu_yanlun_deters_khitan',4,old,'乃出甲士五百於城北，張弓弩以待之，契丹果引去。','《旧五代史》补记符彦伦派出的五百甲士张弓弩戒备，契丹果然离去。','补戒备兵器，不推实际射杀人数。',relation='adds')
# 5–8: a capital assignment, northern operations, preparations and renaming.
add('zhang_congen_capital_deputy','后晋任张从恩暂代东京留守',5,'以天平节度使','东京留守。',[('张从恩','以天平节度使身份暂代东京留守')],when='945年正月，主书未列日；旧本纪己未，新本纪戊午',place='东京大梁',note='权为暂代；新旧本纪任命日不同分别保留，东京按后晋都城识别。')
sup('zhang_congen_capital_deputy',5,old,'己未，以前許州節度使李從溫為北面行營都招撫使，以鄆州節度使張從恩權東京留守。','《旧五代史》在己未记张从恩权东京留守。','郓州节度使与天平军节度使为同一军镇，不另建同人。',relation='adds',field='time_original')
sup('zhang_congen_capital_deputy',5,nj,'戊午，幸南莊，張從恩留守東都。','《新五代史》在戊午记张从恩留守东都。','与旧史己未相差一日，原纪日分别保存，待纸本校核；不自行择一覆盖主书。',relation='conflicts',field='time_original')
add('zhe_congyuan_besieges_shengzhou','折从远攻击契丹，围攻胜州',6,'庚申，','围胜州，',[('折从远','以振武节度使身份攻击契丹、围胜州')],when='945年正月庚申',place='胜州',note='围攻不直接写成已经攻陷胜州；折从阮初名已确认，复用折从远主体。')
add('zhe_congyuan_attacks_shuozhou','折从远围胜州后进攻朔州',6,'遂攻','朔州。',[('折从远','围胜州后继续攻朔州')],when='945年正月庚申条下',place='朔州',note='遂为先后承接，不证明两处都在同一时刻，更不能补已经夺下朔州。')
claim('person',people['折从远'],'aliases','折从阮原名折从远，后来为避刘知远名字而改名；两名复用同一主体。',6,'折從阮字可久，初名從遠，避漢高祖名，改為阮，','这是本传明文证据；当前945年仍按主书名折从远，不把后汉改名提前写成已实行。',source=zhe)
add('shi_prepares_campaign_after_recovery','石重贵病情稍好，因河北不断告急而部署诸将准备出行',7,'帝疾小愈，',None,[('帝','病情稍好后部署诸将，准备出行抵抗契丹')],when='945年正月，亲征诏令之前',place='后晋朝廷',note='小愈是部分好转，不写成全愈；此段准备出行不同于已离大梁。')
sup('shi_prepares_campaign_after_recovery',7,old,'帝曰：「北敵未平，固難安寢，當悉眾一戰，以救朔方生靈。若宴安遲疑，則大河以北，淪為寇壤矣。」即日命諸將點閱，以定行計。','《旧五代史》也记石重贵决定点阅诸将，安排亲征行程。','本纪其后辛酉亲征诏令与主书下一段壬戌不同，具体诏令留下一批处理，不提前写已亲征。')
add('wuding_renamed_tianwei','后晋将武定军改名为天威军',8,'更命',None,[],when='945年正月，主书本句未列日；旧本纪甲寅条下',place='后晋诸道',note='军名变化，不把天威军虚构成新的独立国家或编出具体新增兵数。')
sup('wuding_renamed_tianwei',8,old,'改諸道武定軍為天威軍。','《旧五代史》说明此次将诸道武定军改名为天威军。','主书未明范围，旧本纪补诸道；不当单一州镇改名。',relation='adds')
reviews={1:'回驻、派兵、庚子奏报与后续出兵分开；皇甫遇行动条下与旧本纪乙巳诏令纪日并列，辽史庚子攻三州不自动套成奏报发生时。',2:'侦察、转战、力战、马死授马、被俘救回、请求救援、反对救援、渡水来援、返回分录；兵数千与数千、转战距离、辰午时间起点分别保留。同母兄弟不推长幼，族属按原文明示。',3:'晋军悉至是惊传，两军退却而非晋全面获胜；新本纪两军皆溃作为整体结果补充，不改救援的具体事实。',4:'军议设想不当确有内奸，主将先退、桥防撤入、城上鼓噪、南下回撤与城下戒备分开；契丹惕隐无姓名不擅认主体，两处五百兵不强定同一部队。',5:'权为暂代，东京东都为同一后晋都城称谓；新本纪戊午旧本纪己未纪日并列，未强定唯一日。',6:'折从远与折从阮已有初名明证，复用主体；围胜州攻朔州不写成两城已陷，后汉改名不提前。',7:'病情稍好、安排出行与下一段亲征诏令离京分开，不补病名或全愈。',8:'改军名与新增兵员区别，旧本纪补诸道范围。'}
assert not (P/'publication.json').exists()
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=284,year=945,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=284,next_year=945,supplements=supplements,excluded_non_body=[],coverage='卷284原52—59行连续8段，945年正月。945年跨卷284、285共58正文，本批未完成全年。',source_contexts=[dict(source_key=key,note=note) for key,note in [(main_sources[0],'只取945年第1—2段，快照内此前944年三段已处理，不重复。'),(main_sources[1],'只取945年第3—8段，后续亲征、闽事、二月祁州等留后续。'),(old,'只补当前派兵、榆林战事、相州城防、任留守、备行和改军名；其他官员任命和亲征诏令留对应段。'),(ob,'只补本段榆林战事，传记起点辰与主书午、距离二十里与新史十余里分列；后晋灭亡自杀未提前。'),(nj,'只补榆林整体结果与留守纪日，年内其余未处理事实留后续。'),(zhe,'复用已归档本传初名证据，折氏早年既有事实不重建。')]],source_issues_review='侦察千骑与数千、转战距离、交战辰午起点、留守戊午己未任命日分别保留。辽史与主书近似句和旧本纪内引辽史不视多份独立确证。未具名惕隐不推人名。纸本异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],plain_language_review='首次逐条自查全部展示字段，主语明确，命令、侦察、被俘、救援、军议设想、撤军、攻城阵势和实际结果分清；引用保持原字，说明使用简体白话。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
