# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 62–68."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,93))
COMMIT='f2c47323ed0300cae625304e870298722acfa1ce'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['tongjian-286-947-xuzhou-march','jiuwudaishi-099-march-rising','xinwudaishi-067-fuzhou-relief']:
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
main_sources = ['tongjian-286-947-xuzhou-march','tongjian-286-947-return-april']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p062-p068',
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
lines = (ROOT / 'resources/derived/tongjian/286.txt').read_text().splitlines()
for n in range(62, 69):
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
    for a,b in [('主書','《资治通鉴》'),('補','补'),('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('旧史','《旧五代史》'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
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
        citation = f'卷286·天福十二年（947年三月至四月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_12_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=947, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='947年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_286_0947_' + code
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
        edge = 'participation_zztj_286_0947_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'是{a}的{kind}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_286_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','唐主':'李璟','契丹主':'耶律德光','崇':'刘崇（刘知远弟）','信':'刘信（刘知远从弟）','张筠':'张筠（吴越统军使）'})
NEW_ALIASES={'刘崇（刘知远弟）':['劉崇（劉知遠弟）','刘旻','劉旻'],'刘信（刘知远从弟）':['劉信（劉知遠從弟）'],'张筠（吴越统军使）':['張筠（吳越統軍使）'],'鲍修让':['鮑修讓'],'王继弘':['王繼弘','王继宏','王繼宏'],'王章':[]}
NEW_DESCRIPTIONS={
'刘崇（刘知远弟）':'刘知远的弟弟，后来名刘旻。947年任太原尹、知府事。与朱温早年寄居的萧县刘崇分别建档，具体生卒年尚未录入。',
'刘信（刘知远从弟）':'刘知远的从弟，后汉将领。947年领义成节度使，兼侍卫马军都指挥使。与先前吴国将领刘信分别建档，生卒年尚未录入。',
'张筠（吴越统军使）':'吴越统军使。《新五代史》记钱弘佐派他与赵承泰等救援福州；《资治通鉴》947年条记他返回钱唐。与早期后梁将领张筠分别建档，生卒年未载。',
'鲍修让':'吴越东南安抚使。947年钱弘佐派他率军驻守福州。生卒年未载。',
'王继弘':'后汉相州节度使。《资治通鉴》记他后来收葬相州城中遗骨；《旧五代史》作王继宏，将发现遗骨记在乾祐年间。生卒年未载。',
'王章':'魏州南乐人，曾任孔目官，随刘知远到太原。947年任权三司使。具体生卒年尚未录入。'}
j='jiuwudaishi-099-march-rising';a='jiuwudaishi-099-april-appointments';lx='jiuwudaishi-105-liu-xin';lm='xinwudaishi-070-liu-min';wz='xinwudaishi-030-wang-zhang';fz='xinwudaishi-067-fuzhou-relief'
t='947年三月条下，具体日未载'
add('liu_congxiao_returns_quanzhou','留从效率领军队返回泉州',62,'留从效引兵','还泉州，',[('留从效','率军回泉州')],when=t,place='泉州')
add('liu_congxiao_requests_tang_garrison_leave','留从效称泉州贫瘠、赋税沉重，劝南唐驻军离开',62,'谓唐戍将曰：','岂劳大军久戍于此！”',[('留从效','向南唐驻将陈述负担，劝其撤军')],when=t,place='泉州',note='地险土瘠及冬征夏敛是留从效劝驻军离开的言辞，不另推实际税率或经济产值。')
add('nantang_garrison_leaves_quanzhou','留从效设宴饯行，南唐驻将不得已率军离开泉州',62,'置酒饯之，','引兵归。',[('留从效','设宴送走南唐驻军')],when=t,place='泉州',note='驻将未点名，不猜为福州战事中的某位将领。')
add('li_jing_honors_liu_congxiao','李璟未能约束留从效，加授他检校太傅',62,'唐主不能制，',None,[('唐主','加授留从效检校太傅'),('留从效','获加检校太傅')],when=t,place='南唐朝廷至泉州',note='不能制是史书记述的控制状况，不由此补出合谋或其他未载交易。')
add('khitan_leaves_daliang','耶律德光离开大梁，带走晋朝官员、军人、宫人及府库财物',63,'壬寅，','所留乐器仪仗而已。',[('契丹主','离开大梁并带走晋朝人员、财物')],when='947年三月壬寅',place='大梁',description='耶律德光离开大梁。史书记随行晋朝文武官员数千人、军吏士卒数千人、宫女宦官数百人，并载走府库财物，只留下乐器和仪仗。',note='各组人数为史书约数，未合算成精确总数；留下物品的表述限定于本段搬运府库的叙述。')
sup('khitan_leaves_daliang',63,j,'壬寅，契丹主發自東京還本國。','《旧五代史》同记三月壬寅契丹主从东京北归。','东京在此即大梁，复用同一出发事件，不另建第二次北归。')
add('khitan_posts_reassurance_but_looting_continues','耶律德光宿赤冈，命张榜招抚百姓，骑兵仍在劫掠',63,'夕宿赤冈，','然竟不禁胡骑剽掠。',[('契丹主','见村落无人，命张榜招抚，但未禁止骑兵劫掠')],when='947年三月壬寅晚',place='赤冈及附近村落',note='数百通是榜文数量的约数，不是获救人数；张榜不等于招抚已成功。')
add('khitan_crosses_white_horse_ferry','耶律德光从白马渡河，向高勋表示能回国便无遗憾',63,'丙午，',None,[('契丹主','渡河并向高勋表达返国心情'),('高勋','以宣徽使身份听耶律德光谈返国')],when='947年三月丙午',place='白马渡口',note='契丹［主］保留补字括号；死无恨矣是本人言语，不是本日死亡记录。')
sup('khitan_crosses_white_horse_ferry',63,j,'契丹自黎陽濟河，遂趨相州。','《旧五代史》记契丹从黎阳渡河，随后向相州进发。','主书作白马，补书作黎阳，分别保留地名，不据此认定同一坐标或第二次渡河。',relation='adds')
add('sun_hanshao_attacks_fengzhou','孙汉韶率二万兵进攻凤州，驻固镇并分兵扼守散关',64,'蜀孙汉韶',None,[('孙汉韶','率二万兵攻凤州，分兵扼守散关阻援')],when=t,place='凤州、固镇、散关',note='二万是本次孙汉韶所率兵数；部署目的为切断援路，不等于已攻破凤州或已阻断所有援兵。')
add('wuyue_generals_return_qiantang','张筠和余安返回钱唐',65,'张筠、余安','皆还钱唐，',[('张筠','福州救援后返回钱唐'),('余安','返回钱唐')],when=t,place='福州至钱唐',note='张筠按吴越统军使另建主体，早期后梁同名将领不合并；先前946年救援批次同名关联保留待修订。')
sup('wuyue_generals_return_qiantang',65,fz,'乃遣其統軍使張筠、趙承泰等率兵三萬，水陸赴之。','《新五代史》说明福州救援中的张筠是吴越统军使。','此引文只补证人物身份，不把先前派三万兵的行动强定为947年返回钱唐当日。',relation='adds')
add('bao_xiurang_garrisons_fuzhou','钱弘佐派鲍修让率军驻守福州',65,'吴越王弘佐','将兵戍福州，',[('钱弘佐','派鲍修让守福州'),('鲍修让','以东南安抚使身份领兵驻福州')],when=t,place='福州',note='未载此次驻军人数，不采用前次救援军的三万人数。')
add('qian_hongcong_becomes_chancellor','钱弘佐任命钱弘倧为丞相',65,'以东府',None,[('钱弘佐','任命钱弘倧为丞相'),('钱弘倧','从东府安抚使获任丞相')],when=t,place='吴越朝廷')
add('liu_chong_administers_taiyuan','刘知远任命弟弟刘崇行太原尹、知府事',66,'庚戌，',None,[('帝','任命弟弟管理太原府'),('崇','从北京马步都指挥使转任太原尹、知府事')],when='947年三月庚戌',place='太原',note='皇弟崇是刘知远弟、后名刘旻，不是朱温早年寄居家庭中的萧县刘崇。')
sup('liu_chong_administers_taiyuan',66,j,'庚戌，帝以北京馬步軍都指揮使、泗州防禦使、檢校太保劉崇為太原尹、檢校太尉','《旧五代史》同在庚戌记刘崇任太原尹，并列先前职衔。','补书省略知府事而列检校官，保留各书措辞，不推第二次授职。')
sup('liu_chong_administers_taiyuan',66,lm,'劉旻，漢高祖母弟也。初名崇','《新五代史》说明刘旻是刘知远的弟弟，初名刘崇。','同一人物后名作为检索别名，不把后续即位或其他经历提前录在947年。',relation='adds')
relationship('刘知远','刘崇（刘知远弟）','兄长',66,span(66,'以皇弟',None),'皇弟明确相对于刘知远为弟弟，方向表示刘知远是刘崇的兄长。')
add('liang_hui_requests_surrender','契丹将攻相州，梁晖请降，耶律德光允赦并许任防御使',67,'辛亥，','许以为防御使。',[('契丹主','答应赦梁晖，许任防御使'),('梁晖','在契丹将攻相州时请降')],when='947年三月辛亥',place='相州',note='许以为是承诺，不能写成梁晖已正式接受任职。')
add('liang_hui_resumes_resistance','梁晖怀疑耶律德光的承诺，再次登城抵抗',67,'晖疑其诈，','复乘城拒守。',[('梁晖','怀疑对方欺骗，继续守城抵抗')],when='947年三月辛亥请降之后，具体日未载',place='相州',note='诈为梁晖怀疑，不独立证明赦免承诺必是骗局。')
add('khitan_captures_xiangzhou','耶律德光命军队急攻相州，在食时攻破城池',67,'夏，四月，己未，','食时克之，',[('契丹主','命蕃汉军急攻相州')],when='947年四月己未，天未明至食时',place='相州',note='食时为史书时段，不换成现代精确时刻。')
sup('khitan_captures_xiangzhou',67,a,'是日，契丹主取相州，殺留後梁暉。','《旧五代史》也记四月己未契丹攻取相州，并记梁晖被杀。','本纪己未条与其后叙述四日的写法保留，不用既有摘录中的宋史转引作为独立宋史出处。',relation='adds')
add('khitan_massacre_xiangzhou','契丹攻破相州后，大规模杀害城中男子、掳走妇女并杀害婴儿',67,'悉杀城中男子，','以为乐。',[],when='947年四月己未攻破相州后',place='相州',note='原文总述悉杀，下文仍记男女遗民七百余人，不据此声称每个男子均被杀；不补精确当日死亡总数。')
add('gao_tangying_keeps_xiangzhou','耶律德光留下高唐英守相州，高唐英清查遗民七百余人',67,'留高唐英','七百馀人。',[('契丹主','留下高唐英守相州'),('高唐英','留守并清查城中遗民')],when='947年四月相州陷落后，清查具体日未载',place='相州',note='七百余人是清查遗民的史书记数，不是战前人口数。')
sup('gao_tangying_keeps_xiangzhou',67,a,'翌日，契丹主北去，命高唐英鎮之，唐英閱城中遺民，得男女七百人而已。','《旧五代史》记攻城翌日契丹主北去，命高唐英镇守，清查遗民男女七百人。','主书七百余、补书七百分别保留，不强改为一致精确数字。',relation='adds')
add('wang_jihong_buries_xiangzhou_remains','王继弘后来收葬相州城中遗骨，史书记十余万具头骨',67,'其后节度使王继弘','凡得十馀万。',[('王继弘','收集并埋葬相州城中遗骨')],when='相州陷落以后；《旧五代史》记乾祐年间，具体年日未载',year=None,place='相州',note='十余万是后来收葬头骨的史书记数，不等同于四月己未当日死亡统计；主书其后未定年，结构年份保持未知。')
sup('wang_jihong_buries_xiangzhou_remains',67,a,'乾祐中，王繼宏鎮相州，奏於城中得髑髏十餘萬','《旧五代史》记王继宏在乾祐年间镇相州，奏报城中发现十余万具头骨。','通鉴王继弘与旧史王继宏为同职同地同事的异写，登记别名；乾祐年间不压成唯一公元年。',relation='adds')
add('khitan_questions_li_gu','有人告发李谷打算归附后汉，耶律德光拘问六次；李谷要求出示证据，最终获释',67,'或告磁州',None,[('李谷','否认指控并要求出示证据，最终获释'),('契丹主','拘问李谷，佯示有文书，最终释放')],when='947年四月相州陷落叙述之后，具体日未载',place='契丹北归途中，具体审问地点未载',note='谋举州应汉是未名告发者的指控，不作李谷已举州归附事实。若取所获文书是作势，不是查获文书证据。六诘不是六日。')
add('liu_xin_commands_cavalry','刘知远命刘信领义成节度使、充侍卫马军都指挥使',68,'帝以从弟','侍卫马军都指挥使，',[('帝','任命从弟刘信领义成并统领侍卫马军'),('信','获任义成节度使和侍卫马军都指挥使')],when='947年四月条下；《旧五代史》系己未',place='后汉朝廷、义成军',note='从弟为刘知远亲属，与先前吴国同名将领分别建档，不补具体父系连接。')
sup('liu_xin_commands_cavalry',68,a,'夏四月己未，以北京馬軍都指揮使、集州刺史劉信為滑州節度使，充侍衛馬軍都指揮使、檢校太傅','《旧五代史》在四月己未记刘信任滑州节度使兼侍卫马军都指挥使。','滑州与义成军为本次记载的州镇和军号，保留书中不同职衔写法。')
sup('liu_xin_commands_cavalry',68,lx,'蔡王信，高祖之從弟也。','《旧五代史》刘信传说明他是刘知远的从弟。','传记追封蔡王不提前写为947年已经封王；从弟不补具体叔伯父姓名。',relation='adds')
relationship('刘知远','刘信（刘知远从弟）','从兄',68,span(68,'帝以从弟','侍卫马军都指挥使，'),'从弟明确长幼与亲属范围，方向表示刘知远是刘信的从兄，不补两人父亲的具体关系。')
add('shi_hongzhao_commands_infantry','刘知远命史弘肇领忠武节度使、充步军都指挥使',68,'武节都','步军都指挥使，',[('帝','任命史弘肇统领步军'),('史弘肇','领忠武节度使兼步军都指挥使')],when='947年四月条下；《旧五代史》系己未',place='后汉朝廷、忠武军')
sup('shi_hongzhao_commands_infantry',68,a,'以北京武節都指揮使、雷州刺史宏肇為許州節度使，充待衛步軍都指揮使、檢校太傅','《旧五代史》四月己未记史宏肇任许州节度使兼步军都指挥使。','主書弘与补书宏复用同一已知人物，待卫原字保留，展示作侍卫。')
add('yang_bin_acting_privy_chief','刘知远任命杨邠为权枢密使',68,'右都押牙','权枢密使，',[('帝','任命杨邠暂掌枢密使事务'),('杨邠','从右都押牙任权枢密使')],when='947年四月条下；《旧五代史》系己未',place='后汉朝廷')
sup('yang_bin_acting_privy_chief',68,a,'以北京隨使、右都押衙楊邠為權樞密使、檢校太保','《旧五代史》同记杨邠任权枢密使。','权职为暂任，未提前写成其后来正式任命。')
add('guo_wei_acting_privy_deputy','刘知远任命郭威为权副枢密使',68,'蕃汉兵','权副枢密使，',[('帝','任命郭威暂掌副枢密使事务'),('郭威','从蕃汉兵马都孔目官任权副枢密使')],when='947年四月条下；《旧五代史》系己未',place='后汉朝廷',note='主书副枢密使与补书本条权枢密使写法不同，明确保留差异，不默改为相同官衔。')
sup('guo_wei_acting_privy_deputy',68,a,'以蕃漢兵馬都孔目官郭威為權樞密使、檢校司徒','《旧五代史》此条写郭威为权枢密使、检校司徒，与《资治通鉴》的权副枢密使有官衔差异。','不得把补书本条自行加副字；保留原字与差异，待进一步职官校核。',relation='conflicts')
add('wang_zhang_acting_finance_chief','刘知远任命王章为权三司使',68,'两使都',None,[('帝','任命王章暂掌三司事务'),('王章','从两使都孔目官任权三司使')],when='947年四月条下；《旧五代史》系己未',place='后汉朝廷',note='南乐为王章籍贯，不是本次授官所在地。')
sup('wang_zhang_acting_finance_chief',68,a,'以兩使都孔目官王章為權三司使、檢校太保。','《旧五代史》同记王章任权三司使，并列检校太保。','保留各书职衔细节，未提前录入其后来转为正式三司使。')
sup('wang_zhang_acting_finance_chief',68,wz,'王章，魏州南樂人也。','《新五代史》说明王章是魏州南乐人。','籍贯只补人物身份，不把传中其他早年行动全部放在947年。',relation='adds')
reviews={62:'留从效回泉州、劝驻军、饯行撤军及李璟加官分录，言辞与史家解释不推未载税率或密谋。',63:'北归实际出发与前批计划分别录入；人数按史书约数，招抚与仍劫掠并列；白马、黎阳原地名分别保留，补字括号不删。',64:'二万兵攻凤州与固镇驻军、散关阻援部署不写成攻破凤州。',65:'吴越张筠区别后梁同名人物，先前946年关联保留待修；鲍守福州与钱弘倧任丞相分别录入。',66:'刘知远弟刘崇复核新史后名旻，与萧县同名人物分开，皇弟关系明确方向。',67:'请降承诺、怀疑抵抗、攻破、屠杀、留守清查、其后收葬、李谷受讯分录；十余万不作当日伤亡，乾祐区间不强定年；告发不作归附事实。',68:'刘信区别吴将同名；官任逐条录入，旧史四月己未与主书条下位置分别说明；郭威权枢密与副枢密异写保留。'}
assert not (P/'publication.json').exists()
for n in range(62,69):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(62,69)],next_paragraph=Q[69]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原67—73行连续七段，累计68/92，947年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(62,69)],source_issues_review='刘崇、刘信同名人物分开；张筠吴越身份另建并保留先前关联待修；头骨记数及乾祐区间保留；郭威官衔异说未消除。',plain_language_review='首次逐条阅读本批全部标题、正文、参与、关系、人物、时间地点、出处和事实说明；明确主语，区分承诺、怀疑、指控、部署及实际行为，原文摘录保持底本原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
