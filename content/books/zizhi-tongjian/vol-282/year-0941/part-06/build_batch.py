# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 941 paragraphs 30–38."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,39))
specs=[(d.name,d,'058e3fb21c9297c339adaaf269129242f63ad9e2','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-282-941-autumn-winter','jiuwudaishi-080-an-congjin-battle','xinwudaishi-069-an-congjin-aid']:
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
main_sources = ['tongjian-282-941-autumn-winter','tongjian-282-941-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0941-p030-p038',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-282-941-year-end':'卷282·天福六年十二月','jiuwudaishi-098-zongcheng':'卷98·安重荣传·宗城之战','xinwudaishi-051-zongcheng':'卷51·安重荣传·宗城之战','xinwudaishi-065-liu-yan-rename':'卷65·南汉世家·刘龑改名'}
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
lines = (ROOT / 'resources/derived/tongjian/282.txt').read_text().splitlines()
for n in range(30, 39):
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
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'tongjian-282-941-year-end':'卷282·天福六年十二月','jiuwudaishi-098-zongcheng':'卷98·安重荣传·宗城之战','xinwudaishi-051-zongcheng':'卷51·安重荣传·宗城之战','xinwudaishi-065-liu-yan-rename':'卷65·南汉世家·刘龑改名'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '年末条下及相关追述' if n==30 else '十二月条下'
        citation = f'卷282·后晋天福六年（941；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0941_06_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=941, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='941年十二月条下，具体日期未载'
    key = 'event_zztj_282_0941_' + code
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
        edge = 'participation_zztj_282_0941_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_282_0941_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=ev(code,title,n,start,end,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
def source_span(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end);return t[a:b]

# Curated opening paragraphs.
ALIASES.update({'张昭远':'张昭（五代宋初）','契丹主':'耶律德光'})






ALIASES.update({'唐主':'李昪','曦':'王延羲','楚王希范':'马希范','汉主':'刘岩','重贵':'石重贵','从贵':'安从贵','佶':'张佶','弘佐':'钱弘佐'})
NEW_DESCRIPTIONS={
'王绍颜':'南唐内侍。941年向李昪上书，指出春季以来许多群臣获罪，朝廷内外疑惧。李昪亲笔解释缘由，命王绍颜告知内外。生卒年未载。',
'李端':'荆南都指挥使。941年十二月受高从诲派遣，率数千水军到南津，协助高行周讨安从进，并运粮供应。生卒年未载。',
'张少敌':'楚国天策都军使，张佶之子。941年十二月受马希范派遣，率一百五十艘战舰进入汉江，协助高行周讨安从进，并运粮供应。生卒年未载。',
'赵彦之':'深州人，早年与安重荣同为散指挥使，相互交好。安重荣镇成德后，赵彦之从关西归来，受命募众；安重荣后来只任他排陈使，赵彦之怨恨。941年十二月宗城战中卷旗来降后晋，被官军杀死并分取银饰装备。出生年未载。',
'安从贵':'安从进的弟弟。941年奉兄长派遣，率兵迎击均州刺史蔡行遇，被焦继勋截击击败，被俘并遭断足后送回。出生年及死亡年未载。',
'蔡行遇':'后晋均州刺史。941年安从进派其弟安从贵率兵迎击蔡行遇，焦继勋截击安从贵并取胜。生卒年未载。',
'王重胤':'后晋指挥使，宛丘人。941年十二月戊戌宗城战中，劝杜重威不要退军，建议分兵攻击镇州军两翼，自己直冲中军。杜重威接受建议。生卒年未载。',
'张建武':'后晋冀州刺史。941年十二月庚子与其他将领攻取赵州。生卒年未载。'}
NEW_ALIASES={'王绍颜':['王紹顏'],'李端':[],'张少敌':['張少敵'],'赵彦之':['趙彥之'],'安从贵':['安從貴'],'蔡行遇':[],'王重胤':['王重𦙍'],'张建武':['張建武']}
old='jiuwudaishi-098-zongcheng';new='xinwudaishi-051-zongcheng';ann='jiuwudaishi-080-an-congjin-battle';col='tongjian-282-941-year-end-collation'
claim('person',person('唐主',30,'史书记其生活节俭，勤于政务',span(30,'唐主性节俭','服饰粗略。')),'biography','《资治通鉴》记李昪生活节俭，常穿蒲草鞋，用铁盆洗脸，夏天睡在葛布帷帐内，衣饰简朴。',30,span(30,'唐主性节俭','服饰粗略。'),'这些是长期生活习惯的概述，不造一场941年单日节俭事件；宫人相貌的贬称保留在原文，不扩为网站人物评价。')
add('li_bian_pays_fallen','李昪规定为国事而死者，即使是普通士卒，也给禄三年',30,'死国事者','皆给禄三年。',[('唐主','规定对为国事而死者给禄三年')],year=None,when='李昪在位期间，具体年月未载',note='三年为给禄期限，不补每人钱额或假定每份给付已完成。')
add('li_bian_surveys_taxes','李昪派使者察看民田，按土地肥瘠确定税额',30,'分遣使者','以肥瘠定其税，',[('唐主','派使者查田并按肥瘠确定税额')],year=None,when='李昪在位期间，具体年月未载',note='使者未具名，税率及具体田块未载。')
claim('event',E['li_bian_surveys_taxes'],'description','《资治通鉴》记百姓认为这种田税安排较为公平，此后江淮调兵、征役和其他赋敛都以税钱为基准。',30,'民间称其平允。自是江、淮调兵兴役及它赋敛，皆以税钱为率，至今用之。','民间称为史书记述的反应，至今用之为作者回顾，不确定其最后适用日期。')
claim('person',people['李昪'],'biography','《资治通鉴》记李昪日夜处理政务，从江都返回后不再宴乐，但也批评他过于急躁。',30,'唐主勤于听政，以夜继昼，还自江都，不复宴乐；颇伤躁急，','评价与在位期间行为概述保留，不重复造一场941年返回江都的新行程。')
add('wang_shaoyan_petition','王绍颜上书，指出群臣接连获罪使内外疑惧',30,'内侍王绍颜','中外疑惧。”',[('王绍颜','向李昪上书反映内外疑惧'),('唐主','收到内侍的劝告')],when='941年年末条下，具体日期未载',description='内侍王绍颜向李昪上书，说从当年春天以来，许多群臣获罪，朝廷内外疑虑恐惧。',note='疑惧程度为王绍颜的报告，不补受罚名单或人数。')
add('li_bian_explains_punishments','李昪亲笔解释处罚群臣的缘由，命王绍颜告知内外',30,'唐主手诏',None,[('唐主','亲笔解释处罚缘由并要求传达'),('王绍颜','受命将解释告知内外')],when='941年王绍颜上书后，具体日期未载',note='解释具体内容未载，不替皇帝补写辩解。')
add('chonggui_king_qi_yedu','石敬瑭将石重贵改封齐王，任邺都留守',31,'十二月，','充鄴都留守；',[('帝','改封石重贵并任命邺都留守'),('重贵','由郑王改封齐王并任邺都留守')],when='941年十二月丙戌朔',place='邺都')
add('li_dechong_east_capital','石敬瑭任李德珫为东都留守',31,'以李德珫',None,[('帝','任命东都留守'),('李德珫','获任东都留守')],when='941年十二月丙戌朔',place='东都',note='与十一月权东京留守临时任命分开。')
add('gao_heads_xiangzhou_campaign','石敬瑭命高行周主管襄州行府事务',32,'丁亥，','知襄州行府事。',[('帝','命高行周主管行府'),('高行周','受命主管襄州行府事务')],when='941年十二月丁亥',place='襄州')
add('shi_orders_south_support','石敬瑭命荆南、湖南共同讨伐襄州',32,'诏荆南','共讨襄州。',[('帝','命两地协同讨伐安从进')],when='941年十二月丁亥条下',place='襄州',note='诏令与随后实际派援军分录。')
add('gao_sends_li_duan','高从诲派李端率数千水军到南津援助讨伐',32,'高从诲遣','将水军数千至南津，',[('高从诲','派水军协助讨伐'),('李端','率数千水军到达南津')],when='941年十二月诏令后，具体日期未载',place='南津',note='数千为史载概数，不补舰船数量。')
sup('gao_sends_li_duan',32,'xinwudaishi-069-an-congjin-aid','晉師致討，從誨遣將李端以舟師為應，','《新五代史》同记高从诲派李端率舟师响应后晋讨伐。','同一荆南援军的补证，主书补出数千水军和南津地点；不提前录入安从进败亡。')
add('ma_sends_zhang_shaodi','马希范派张少敌率一百五十艘战舰入汉江助高行周',32,'楚王希范遣','入汉江助行周，',[('楚王希范','派楚国水军援助高行周'),('张少敌','率一百五十艘战舰进入汉江'),('高行周','获得楚国水军援助')],when='941年十二月诏令后，具体日期未载',place='汉江',note='一百五十为舰船数，不转为士兵数。')
add('southern_allies_supply_grain','荆南和楚国各运粮供应高行周军',32,'仍各运粮','以馈之。',[('高从诲','荆南方面运粮支援'),('楚王希范','楚国方面运粮支援'),('高行周','军队得到两地粮食供应')],when='941年十二月援军出动后，具体日期未载',note='粮食总量与运输路线未载，不补精确供应能力。')
relationship('佶','张少敌','父亲',32,'少敌，佶之子也。','承接楚国将领张少敌，佶为已有楚国张佶主体，方向为张佶是张少敌的父亲。')
add('an_gathers_hungry_people','安重荣得知安从进起兵，聚数万饥民南向邺都',33,'安重荣闻','南向鄴都，',[('安重荣','得知安从进反叛后，聚饥民数万南行')],place='邺都方向',note='数万为史载概数，未将饥民全部等同正规骑兵；声言不朝字形另据同书版本和传记校读。')
sup('an_gathers_hungry_people',33,col,'衆至數萬南向鄴都聲言入朝','《资治通鉴》四部丛刊本电子转录写安重荣南向邺都，声称前往朝觐。','本电子底本声言不朝与同书第163页固定修订1471339的入朝不同；展示按版本校读，原TXT不改，影印字形与纸本待核，不算独立史书确证。')
sup('an_gathers_hungry_people',33,new,'是歲，鎮州大旱、蝗，重榮聚飢民數萬，驅以嚮鄴，聲言入覲。','《新五代史》补记当年镇州旱灾、蝗灾，安重荣聚饥民数万南向邺都，声称入觐。','旱蝗为传记补充的当年背景，入觐与同书校读入朝对应；未把对外说法当真实目的。',relation='adds')
add('an_zhao_early_friendship','安重荣与赵彦之早年同为散指挥使，关系亲密',33,'初，重荣与','相得欢甚。',[('安重荣','与赵彦之同职并交好'),('赵彦之','与安重荣同职并交好')],year=None,when='安重荣任成德节度使以前，具体年月未载',note='初引出往事，深州为赵彦之籍贯，不套941年任官。')
add('zhao_recruits_for_an','赵彦之从关西投安重荣，受到优待并受命募众',33,'重荣镇成德，','使彦之招募党众；',[('赵彦之','从关西投安重荣并受命招募部众'),('安重荣','优待赵彦之并委派募众')],year=None,when='安重荣任成德节度使期间，起兵以前，具体年月未载',note='优待与内心猜忌分别保留，不从交好推为永久盟友。')
add('zhao_resents_rank','安重荣起兵时只任赵彦之为排陈使，赵彦之怨恨',33,'然心实忌之，','彦之恨之。',[('安重荣','因猜忌只任赵彦之为排陈使'),('赵彦之','因所任职位而怨恨')],note='排陈使保留官职，不擅自改成先锋使。')
add('shi_orders_attack_an','石敬瑭派三十九个马步指挥，命杜重威统军讨安重荣',33,'帝闻重荣反，',None,[('帝','派护圣等三十九个马步指挥讨伐'),('杜重威','任招讨使统军'),('马全节','任副将'),('王周','任马步都虞候')],when='941年十二月壬辰',note='三十九指挥是军队编制单位数量，不是三十九个人，也不补每指挥兵额。')
add('an_conggui_intercepts_cai','安从进派弟弟安从贵率兵迎击均州刺史蔡行遇',34,'安从进遣','均州刺史蔡行遇，',[('安从进','派弟弟率兵迎击'),('从贵','率兵迎击蔡行遇'),('蔡行遇','成为安从贵迎击的目标')],note='逆在本军事语境为迎击，不译成蔡行遇已归顺安从进。')
relationship('从贵','安从进','弟弟',34,'安从进遣其弟从贵将兵','弟弟身份有明文，不补父母和出生年。')
add('jiao_captures_conggui','焦继勋截击安从贵，击败并俘获后断足送回',34,'焦继勋邀击，',None,[('焦继勋','截击安从贵，获胜并俘虏'),('从贵','被俘并遭断足后送回')],note='归之为送回，具体送回地点未载；断足不表示当场死亡。')
add('zongcheng_meeting','杜重威与安重荣军在宗城西南遭遇',35,'戊戌，','遇于宗城西南，',[('杜重威','率官军遇安重荣军'),('安重荣','在宗城西南与官军遭遇')],when='941年十二月戊戌',place='宗城西南')
add('an_crescent_defends','安重荣布偃月阵，抵住官军两次进攻',35,'重荣为偃月陈，','不动；',[('安重荣','布偃月阵抵住进攻'),('杜重威','所率官军两次进攻未动其阵')],when='941年十二月戊戌',place='宗城西南',note='再击为两次进攻，不扩为长期围攻。')
add('wang_chongyin_plan','杜重威想退军，王重胤建议分击两翼、直冲中军，杜重威接受',35,'重威惧，','重威从之。',[('杜重威','害怕欲退，后接受进攻方案'),('王重胤','劝阻退兵，提出两翼与中军配合进攻')],when='941年十二月戊戌',place='宗城西南',description='杜重威害怕，想退军。王重胤说退军是兵家所忌，镇州精兵集中在中军，应分精锐攻击两翼，由他直冲中军。杜重威接受。',note='原文以契丹指冲击所用力量，未另外给人数或编制；本条只记建议及接受，不把提议当作已完成全套战术。')
add('zhao_attempts_surrender','镇州军阵稍退，赵彦之卷旗策马向官军投降',35,'镇人陈稍却，','来降。',[('赵彦之','在军阵退却时卷旗策马来降')],when='941年十二月戊戌',place='宗城西南')
add('zhao_killed_for_silver','官军杀死来降的赵彦之，分取其银饰铠甲和鞍具',35,'彦之以银饰','官军杀而分之。',[('赵彦之','来降后遭官军杀害，银饰装备被瓜分')],when='941年十二月戊戌',place='宗城西南',note='官军士卒未具名，不推杜重威本人下杀降命令。')
sup('zhao_killed_for_silver',35,new,'晉軍不知其來降，爭殺而分之。','《新五代史》补记晋军不知道赵彦之是来投降，争杀并分取其装备。','不知来降是新史补充原因，主书只记杀而分之；未把此解释当作独立查实的全部杀人动机。',relation='adds')
add('an_hides_in_baggage','安重荣得知赵彦之叛离，害怕而躲入辎重中',35,'重荣闻彦之叛，','退匿于辎重中，',[('安重荣','因赵彦之叛离害怕，躲入辎重中')],when='941年十二月戊戌',place='宗城西南')
add('jin_routs_an_army','官军趁势击溃镇州军，史书记斩首一万五千',35,'官军从而乘之，','斩首万五千级。',[('杜重威','所率官军趁势击溃镇州军'),('安重荣','所率部众遭大败')],when='941年十二月戊戌',place='宗城西南',note='战果数字按史书记载，不声称已独立核实，也不与后面战死冻死二万余人直接相加。')
add('an_shelters_zongcheng','安重荣收拢残部，逃入宗城',35,'重荣收馀众，','走保宗城，',[('安重荣','收拢残部退保宗城')],when='941年十二月戊戌战败后',place='宗城')
add('jin_takes_zongcheng','官军继续攻打宗城，夜半攻克',35,'官军进攻，','夜分，拔之。',[('杜重威','所率官军继续进攻并夜半攻克宗城')],when='941年十二月戊戌战后夜半',place='宗城',note='夜分为夜半，不自行换算公历跨日。')
add('an_returns_zhenzhou','安重荣率十多骑逃回镇州，闭城自守',35,'重荣以十馀骑','婴城自守。',[('安重荣','率十多骑逃回镇州，闭城守御')],when='941年十二月宗城失守后',place='镇州',note='当前只到闭城，不提前录入942年被捕处死。')
sup('an_returns_zhenzhou',35,old,'重榮至鎮，取牛馬革旋為甲，使郡人分守夾城以待王師。','《旧五代史》补记安重荣回镇后，急用牛马皮制甲，派郡中人分守夹城。','归镇后准备守御的补充，不提前录入后面的水碾门导军及安重荣被杀。',relation='adds')
add('zhenzhou_cold_casualties','严寒中，镇州方面战死和冻死者达二万多人',35,'会天寒，','二万馀人。',[],when='941年十二月宗城战败后',place='具体地点未载',description='《资治通鉴》记，当时天气严寒，镇州方面战死和冻死者二万多人。',note='战死与冻死为合称，范围与此前斩首数可能重叠，不相加成三万五千余人；确切死亡地点未载。')
sup('zhenzhou_cold_casualties',35,old,'其下部眾，屬嚴冬寒冽，殺戮及凍死者二萬餘人。','《旧五代史》同记严冬中安重荣部众被杀及冻死二万多人。','同类数字的传记记载，不能当成另外又死二万多人。')
add('khitan_releases_yang','契丹得知安重荣反叛，准许杨彦询返回',35,'契丹闻重荣反，',None,[('杨彦询','获准从契丹返回')],when='941年十二月条下，具体准归日期未载',place='契丹',note='听还为准许返回，不等于本日已抵后晋；不补朝廷此前扣留原因。')
add('zhang_jianwu_takes_zhaozhou','张建武等攻取赵州',36,'庚子，',None,[('张建武','以冀州刺史身份与其他将领攻取赵州')],when='941年十二月庚子',place='赵州',note='其他将领未具名，不凭同场军队推参与者名单。')
add('liu_yan_renames','南汉刘岩病中听僧人说龚名不利，改名为龑',37,'汉主寝疾，',None,[('汉主','病中因僧人说旧名不利而改名')],when='941年十二月条下，具体日期未载',place='南汉',description='刘岩病中，一名外来僧人说龚这个名字不利。刘岩造字龑，取飞龙在天之意，读音如俨，并以此为名。',note='电子底本以私用区字符记录此字，新史明确写龑，展示据其校读；僧人的不利说法不当确证或医学因果。')
sup('liu_yan_renames',37,'xinwudaishi-065-liu-yan-rename','龑乃採周易「飛龍在天」之義為「龑」字，音「儼」，以名焉。','《新五代史》明确记取周易飞龙在天之义造龑字，音俨，用作名字。','私用区字符据此规范展示龑，保留主书原字；传记连叙白龙改元等前事，不把全部连叙定为941年十二月。')
add('shi_confirms_hongzuo','石敬瑭任钱弘佐为镇海、镇东节度使兼中书令，封吴越国王',38,'庚戌，',None,[('帝','以制书正式授官封王'),('弘佐','获后晋授镇海镇东节度使兼中书令及吴越国王')],when='941年十二月庚戌',place='吴越',note='与八月地方承制及九月吴越即位分期，不能当此前未成为吴越统治者。')
sup('shi_confirms_hongzuo',38,ann,'庚戌，以權知吳越國事錢宏佐為起復鎮軍大將軍、檢校太師、兼中書令、杭州越州大都督、鎮海鎮東等軍節度使，封吳越國王。','《旧五代史》补全钱弘佐的起复镇军大将军、检校太师、杭州越州大都督等授官名号。','宏佐为本纪姓名异写，对应同次授官钱弘佐；额外职衔来自独立出处，未改主书。',relation='adds')
for row in B['people']:
 if row['name']=='赵彦之':
  row['death_year']=941
  claim('person',row['key'],'death_year','赵彦之于941年十二月戊戌宗城战中被官军杀死。',35,'彦之以银饰铠胄及鞍勒，官军杀而分之。','死亡日承接本段戊戌，出生年未载。')
reviews={30:'节俭、勤政及田税制度为在位期间概述，未知确年；王绍颜今春以来上书和解释为941年条下，未载具体处罚名单。',31:'十二月朔正式邺东留守与上批十一月临时任命分开。',32:'丁亥知行府与协讨诏令、荆南李端数千水军及楚张少敌百五十战舰和粮运分录；张佶父亲关系有明文。',33:'聚饥民起兵与早年赵彦之交好、归投募众分期；不朝据同书固定版本入朝及两传记入觐校读，原文不改；三十九指挥为编制而非人头。',34:'安从贵弟弟身份明确，迎击蔡行遇与焦继勋截击获胜、俘获断足归之记录，不因断足认作已死。',35:'戊戌遭遇、偃月阵抵抗、王重胤建议、赵彦之来降和被杀、镇军溃败、宗城被攻克、安重荣归镇及战冻死亡分期。原以契丹字样保留，未推兵数；一万五千斩首与二万多战冻死可能重叠，不相加。契丹准许杨彦询归国与实际到达分开，未提前录942年攻镇及安重荣被杀。',36:'十二月庚子赵州取城，其他将领未名，不造名单。',37:'龑字依据新史规范显示，主书私用区字保留；造字、音义与僧人说法分别说明，不将白龙改元背景强定当年。',38:'十二月庚戌后晋正式授钱弘佐官封与吴越本地即位分期，旧史补官衔，宏佐姓名字形保留。'}
assert not (P/'publication.json').exists()
for n in range(30,39):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
ledger[29]['claim_keys']=[x['key'] for x in B['claims'] if Q[30]['id'] in x['citation']]
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=941,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(30,39)],next_paragraph='zztj-v283-y0942-p001',next_volume=283,next_year=942,supplements=supplements,excluded_non_body=[],source_contexts=[],coverage='连续第30—38段，原115—123行；年末及相关追述。全年38段至卷末，后接卷283的942年第1段。',source_issues_review='不朝与同书固定转录入朝校读、新旧史入觐相对照；原以契丹字样及南汉改名私用区字符保留原文，龑据新史规范。宗城死亡数字可能重叠，书间后续叙事不提前给942年定时。纸本及异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(30,39)],plain_language_review='首次检查人物介绍、事件说明、参与角色、关系方向、时间与事实引用；长期习惯、制度概述、战争步骤、建议和实际行动分开，未知年份及原文异字保留，旧主体字段不扩大改写。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
