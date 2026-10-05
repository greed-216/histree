# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 952 paragraphs 17–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,38))
COMMIT='a94812079efe6f0dad4431d10d0651494739b7f1'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-290-952-january-continuation']:
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
main_sources = ['tongjian-290-952-january-continuation','tongjian-290-952-april-may']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0952-p017-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-290-952-april-may':'卷290·广顺二年·四五月亲征兖州及相邻记事','jiuwudaishi-112-april-952':'卷112·太祖本纪三·广顺二年四月','jiuwudaishi-112-may-952':'卷112·太祖本纪三·广顺二年五月','xinwudaishi-053-murong-death':'卷53·杂传四十一·慕容彦超传·城破与死亡','songshi-263-dou-yi-clemency':'卷263·列传二十二·窦仪传·请赦兖州胁从'}
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
lines = (ROOT / 'resources/derived/tongjian/290.txt').read_text().splitlines()
for n in range(17, 25):
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
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if key in prior_source_registry}, []

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
    labels={'tongjian-290-952-april-may':'卷290·广顺二年·四五月亲征兖州及相邻记事','jiuwudaishi-112-april-952':'卷112·太祖本纪三·广顺二年四月','jiuwudaishi-112-may-952':'卷112·太祖本纪三·广顺二年五月','xinwudaishi-053-murong-death':'卷53·杂传四十一·慕容彦超传·城破与死亡','songshi-263-dou-yi-clemency':'卷263·列传二十二·窦仪传·请赦兖州胁从'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺二年（952年三月至五月及相邻追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0952_03_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=globals().get("NEW_BIRTH_YEARS",{}).get(name),death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=952, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='952年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_290_0952_' + code
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
        edge = 'participation_zztj_290_0952_' + code + '_' + pk
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
    a=ALIASES.get(a,a); b=ALIASES.get(b,b)
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'史书记{a}是{b}的{kind}',quote,source=source)
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
        row=dict(key=f'relationship_zztj_290_0952_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','唐主':'李璟','延己':'冯延巳','冯延己':'冯延巳','景运':'徐景运','继勋':'慕容继勋'})
NEW_ALIASES={'郭崇':[],'李建期':[],'侯训':['侯訓'],'慕容继勋':['慕容繼勳']}
NEW_DESCRIPTIONS={'郭崇':'后周侍卫马军都指挥使。952年郭威亲征兖州时，充在京都巡检。生卒年尚未录入。','李建期':'南唐将领。南唐取湖南以后，受李璟之命驻益阳、谋取朗州，较长时间没有取得成果。生卒年未载。','侯训':'南唐统军使。952年奉李璟之命率五千兵从吉州路赴全州，与张峦合攻桂州，战败身死。生年未载。','慕容继勋':'慕容彦超之子。952年五月兖州城破后逃走，被追获杀死。《新五代史》另记率部五百人出奔被擒。生年未载。'}
NEW_DEATH_YEARS={'侯训':952,'慕容继勋':952}
apr='jiuwudaishi-112-april-952';may='jiuwudaishi-112-may-952';murong='xinwudaishi-053-murong-death';dou='songshi-263-dou-yi-clemency'
add('xiao_yan_attacks_feng','萧俨多次上疏批评冯延巳',17,'大理卿萧俨','数上疏攻之，',[('萧俨','以大理卿身份多次批评冯延巳'),('延己','成为批评对象')],year=None,when='冯延巳当政时期多次批评的概述，具体起止年月未载',place='南唐朝廷',note='恶其为人是萧俨的态度，不作本站对冯延巳的结论；数上疏未列次数。')
add('xiao_yan_wrongful_death_conviction','萧俨因错判他人为死罪获罪，钟谟、李德明等主张杀他',17,'会俨坐失入人死罪，','必欲杀之，',[('萧俨','因错判他人为死罪被追究'),('钟谟','主张杀萧俨'),('李德明','主张杀萧俨')],when='952年任相后相邻记事，具体裁判日未载',place='南唐',note='失入为误将案件判入重罪；下文冯延巳说误杀一妇人，分别说明，不把想杀写成已经杀萧俨。')
add('feng_defends_xiao_yan','冯延巳为曾批评自己的萧俨请求宽免，萧俨获免',17,'延己曰：','人亦以此多之。',[('延己','以萧俨有直声、所犯已逢赦为由请求宽免'),('萧俨','因冯延巳求情而获免')],when='952年萧俨被追究后，具体获免日未载',place='南唐朝廷',note='有直声及已会赦是冯延巳奏言的理由；人多之为史家记人们赞许此举，不泛化为所有人支持其全部政务。')
add('xu_jingyun_removed','徐景运不久罢相，改任太子少傅',17,'景运寻罢',None,[('景运','罢宰相后任太子少傅')],when='952年三月任相后不久，具体罢免日未载',place='南唐朝廷',note='本句未说因萧俨案被罢，不把相邻记事推成因果。')
add('april_solar_eclipse','史书记载四月丙戌朔发生日食',18,'夏，四月，',None,[],when='952年四月丙戌朔',place='后周',note='记录史书纪时，未另做天文换算，不给未经核实的现代观测地点。')
sup('april_solar_eclipse',18,apr,'夏四月丙戌朔，日有食之，帝避正殿，百官守司。','《旧五代史》同日记日食，并补郭威避正殿、百官守职。','避殿为当时礼制行为，原文未说明观测经纬度。',relation='adds')
add('guo_orders_yanzhou_personal_campaign','郭威因兖州久攻未克，下诏亲征',19,'帝以曹英等','乙卯，下诏亲征，',[('帝','决定亲征兖州')],when='952年四月乙卯',place='后周朝廷至兖州',note='底本攻克兖州久未克有重复字样，按久攻未克理解，原字保留；命令未等于已出发。')
sup('guo_orders_yanzhou_personal_campaign',19,apr,'乙卯，詔取來月五日，車駕赴兗州城下，慰勞將士。','《旧五代史》同日补记拟下月初五到兖州城下慰劳将士。','主书实际五月庚申出发、戊辰到城，拟定日程与实际行程分别登记，不把诏定初五直接当到达日。',relation='adds')
add('li_gu_capital_regent','郭威让李谷暂掌东京留守并判开封府',19,'以李谷','兼判开封府，',[('帝','命李谷留守东京并判开封府'),('李谷','暂掌留守与府务')],when='952年四月乙卯',place='东京、开封府')
sup('li_gu_capital_regent',19,apr,'以中書侍郎、平章事、判三司李穀為權東京留守，兼判開封府事。','《旧五代史》也记李谷暂掌东京留守、兼判开封府。','补记此前职衔，不据权字说他已终身任留守。')
add('zheng_palace_guard','郭威命郑仁诲暂掌大内都点检',19,'郑仁诲权','大内都点检，',[('帝','命郑仁诲掌宫城守备'),('郑仁诲','暂掌大内都点检')],when='952年四月乙卯',place='后周宫城')
sup('zheng_palace_guard',19,apr,'以樞密副使鄭仁誨為右衛大將軍，依前充職，兼權大內都點檢；','《旧五代史》补记郑仁诲授右卫大将军、仍充原职，并暂兼大内都点检。','不把新授大将军解释为已罢枢密副使。',relation='adds')
add('guo_chong_capital_patrol','郭威让郭崇充在京都巡检',19,'又以侍卫马军都指挥使郭崇',None,[('帝','安排郭崇负责京城巡检'),('郭崇','以侍卫马军都指挥使身份充在京都巡检')],when='952年四月乙卯',place='后周京城',note='郭崇与郭威分别为两人，不因同姓或均在京合并。')
add('li_jianqi_yiyang_garrison','李璟派李建期驻益阳，谋取朗州',20,'唐主既克湖南，','以图朗州，',[('唐主','派将领驻益阳，计划进取朗州'),('李建期','率军驻益阳，成为进取朗州的部署')],year=None,when='951年取湖南后至952年桂州战事前的追述，具体驻军日未载',place='益阳、朗州',note='图朗州是计划，不写成已经占领朗州。')
add('zhang_luan_guizhou_recruiting','李璟让张峦兼桂州招讨使，长期未取得成果',20,'以知全州张峦','久之，未有功。',[('唐主','让张峦兼桂州招讨使'),('张峦','以知全州身份兼招讨使，谋桂州而未有成果')],year=None,when='951年知全州以后至952年桂州战事前，具体兼任日未载',place='全州、桂州',note='知全州已录，仅新增兼任及进取未成，不造同一次任全州事件。')
add('li_jing_proposes_pullback','李璟提出停桂州战役、撤益阳驻军，并授刘言节度使旌节',20,'唐主谓冯延己、孙晟曰：','何如？”',[('唐主','提出减轻楚地负担、停止战役与承认刘言的方案'),('冯延己','被征询退兵授节方案'),('孙晟','被征询退兵授节方案')],when='952年四月条下，具体商议日未载',place='南唐朝廷',note='抚疮痍与来苏为李璟对取楚后责任的自述；停战撤戍授节仍为方案，未记已经执行。')
add('sun_feng_pullback_debate','孙晟赞同退兵，冯延巳担心失地威望，建议交边将判断',20,'晟以为宜然。','请委边将察其形势。”',[('孙晟','赞同李璟退兵方案'),('冯延己','反对立即退兵，建议交边将察势')],when='952年李璟提出退兵授节方案后',place='南唐朝廷',note='三分丧二、人将轻我为冯延巳的判断，不换算为已证实丢失领土比例。')
add('hou_xun_guizhou_expedition','李璟派侯训率五千人从吉州赴全州，与张峦合攻桂州',20,'唐主乃遣','合兵攻桂州。',[('唐主','派侯训增兵攻桂州'),('侯训','以统军使身份率五千兵从吉州路赴全州'),('张峦','与侯训合兵攻桂州')],when='952年退兵讨论以后、桂州交战以前',place='吉州路、全州至桂州')
add('tang_defeated_at_guizhou','南汉伏兵与城内军夹击疲惫唐军，侯训战死',20,'南汉伏兵于山谷，','训死，',[('侯训','所部在桂州城下遭夹击，战败身死'),('张峦','参与桂州攻城，军队被击败')],when='952年四月条下，具体交战日未载',place='桂州城下、周边山谷',note='没有具名南汉指挥官，不默认就是前役吴怀恩或潘崇彻。')
add('zhang_luan_flees_quanzhou','张峦收集数百败兵逃回全州',20,'峦收散卒数百',None,[('张峦','收集数百败兵逃回全州')],when='952年桂州战败以后',place='桂州至全州',note='数百为逃回聚集人数，不据此倒算唐军全部战死数字。')
add('guo_leaves_daliang','郭威从大梁出发亲征兖州',21,'五月，庚申，','帝发大梁。',[('帝','率亲征队伍从大梁出发')],when='952年五月庚申',place='大梁至兖州')
sup('guo_leaves_daliang',21,may,'庚申，車駕發京師。','《旧五代史》同日记郭威从京师出发。','实际出发节点与四月下诏分开。')
add('guo_reaches_yanzhou','郭威抵达兖州',21,'戊辰，','至兗州。',[('帝','抵达兖州城下')],when='952年五月戊辰',place='兖州城下')
sup('guo_reaches_yanzhou',21,may,'戊辰，至兗州城下。','《旧五代史》同日也记到兖州城下。','城下不等于郭威此时已入城。')
add('guo_invites_murong_surrender','郭威派人招谕慕容彦超，城上人出言不逊',21,'己巳，','城上人语不逊。',[('帝','派人招谕慕容彦超'),('慕容彦超','成为招谕对象')],when='952年五月己巳',place='兖州城外与城上',note='不逊者原文为城上人，未认定慕容彦超亲自说出该话。')
add('guo_orders_yanzhou_assault','郭威命各军进攻兖州',21,'庚午，',None,[('帝','命各军进攻城池')],when='952年五月庚午',place='兖州',note='进攻命令不等于此日城已陷。')
add('murong_astrological_prayer','慕容彦超受术士星占说辞诱导，立祠祈祷并命民户立黄幡',22,'先是，术者绐彦超云：','令民家皆立黄幡。',[('慕容彦超','相信星占福佑说辞，立祠祈祷并命民户立黄幡')],year=None,when='兖州城破以前的追述，具体星占与立祠年份未载',place='兖州',note='镇星、角亢分野与其下有福是术士说辞，不当客观天文或福祸规律；术者无名不补身份。')
add('murong_hides_treasure_desertions','慕容彦超在城急攻时仍埋藏珍宝，将卒失去斗志，接连出降',22,'彦超性贪吝，','将卒相继有出降者。',[('慕容彦超','在攻城紧急时继续藏财')],when='952年五月兖州城破以前',place='兖州',note='贪吝与斗志变化是史家叙述，不猜每名将卒是否出降或具体埋宝地点。')
add('zhou_takes_yanzhou','后周军攻克兖州',22,'乙亥，','官军克城，',[],when='952年五月乙亥',place='兖州')
sup('zhou_takes_yanzhou',22,may,'乙亥，收復兗州，','《旧五代史》同日记收复兖州。','同一城破节点，不重复建立另一场破城。')
add('murong_couple_die_in_well','慕容彦超力战失败，烧镇星祠，与妻子投井而死',22,'彦超方祷镇星祠，','与妻赴井死。',[('慕容彦超','战败后烧祠，与妻子投井而死')],when='952年五月乙亥城破时',place='兖州',note='妻子未具名，不猜姓名；战斗与投井是主书记载，旧史斩杀异说另保留。')
sup('murong_couple_die_in_well',22,murong,'彥超夫妻皆投井死，','《新五代史》也记慕容彦超夫妻投井而死。','该传明年五月与前文951反叛对应952，不套新的纪年。')
sup('murong_couple_die_in_well',22,may,'斬慕容彥超，夷其族。','《旧五代史》同日条记斩慕容彦超、夷族。','死法与《资治通鉴》《新五代史》投井不同，并列保留，不擅自解释成死后再斩首。',relation='conflicts')
claim('person',people['慕容彦超'],'death_year','慕容彦超在952年五月乙亥兖州城破时死亡。',22,'乙亥，官军克城，彦超方祷镇星祠，帅众力战，不胜，乃焚镇星祠，与妻赴井死。','死亡年与城破日明确，死法异说独立注明。')
add('murong_jixun_captured_killed','慕容继勋城破后逃走，被追获杀害',22,'子继勋出走，','追获，杀之。',[('继勋','逃走后被追获、杀害')],when='952年五月兖州城破以后',place='兖州及逃亡路上',note='子继勋承慕容彦超，冠父姓标识，未编具体追获地点或执行者姓名。')
relationship('慕容彦超','慕容继勋','父亲',22,'子继勋出走，追获，杀之。','子承上文慕容彦超，父亲方向明确，名字按慕容继勋保存。')
sup('murong_jixun_captured_killed',22,murong,'其子繼勳率其徒五百人出奔被擒，','《新五代史》补记继勋率五百人出奔被擒。','被擒规模为此书补证，不把五百人都断言为同日被杀。',relation='adds')
add('yanzhou_sack_deaths','后周军城破后大肆抢掠，城中死者近万人',22,'官军大掠，','城中死者近万人。',[],when='952年五月兖州城破以后',place='兖州城内',note='死者近万人为史书概数，未给平民与军人分别人数，不擅自全计为战场阵亡。')
add('murong_earlier_bandit_recruitment','慕容彦超反叛前招来二千余盗众，史书记为最终未能发挥作用',22,'初，彦超将反，',None,[('慕容彦超','反叛前招募二千余盗众置于帐下')],year=None,when='951年末至952年初反叛筹备期的追述，具体招募日未载',place='泰宁军',note='与此前授旗招募属于同一筹备背景，本次补明确帐下人数及未被用评价，不重新录每个邻境抢掠行动。')
add('dou_feng_fan_request_clemency','窦仪与冯道、范质共同请求赦免被胁从的兖州将吏，郭威答允',23,'帝欲悉诛兗州将吏，','乃赦之。',[('帝','原想诛兖州将吏，听劝后赦免'),('窦仪','与冯道、范质共同请求宽免'),('冯道','参与向郭威请求赦免'),('范质','参与向郭威请求赦免')],when='952年五月兖州城破以后',place='后周兖州行营',note='彼皆胁从为请赦理由，不逐一认定所有将吏的真实动机；同一赦免不重复建四条。')
sup('dou_feng_fan_request_clemency',23,dou,'初，周祖平兗州，議將盡誅脅從者。儀白馮道、范質，同請於周祖，皆得全活。','《宋史》窦仪传也记三人同请，胁从者得以保全。','只用兖州请赦条，不提前录显德滁州府库、赵普与宋初去世等后文。')
add('yan_kan_yanzhou_acting','郭威任颜衎暂掌兖州事务',23,'丁丑，','权知兗州事。',[('帝','任颜衎暂掌兖州'),('颜衎','以端明殿学士身份权知兖州事')],when='952年五月丁丑',place='兖州')
sup('yan_kan_yanzhou_acting',23,may,'詔端明殿學士顏衎權知兗州軍州事。','《旧五代史》在乙亥破城条后也记颜衎权知兖州军州事。','旧书未另列丁丑，编排在破城条内不直接证明任命与破城同日，主书丁丑保留。')
add('guo_yanzhou_general_pardon','郭威赦兖州管内，准逃匿党人一月内自首，已处死者亲属获赦',23,'壬午，','赦其亲戚。',[('帝','赦兖州辖区，并规定自首与亲属宽免')],when='952年五月壬午',place='兖州管内',note='一月为自首期限，不猜实际自首名单；已伏诛者亲属获赦不等于死者复活或翻案。')
sup('guo_yanzhou_general_pardon',23,may,'壬午，曲赦兗州管內罪人，取五月二十七日已前所犯罪，大辟已下，咸赦除之。','《旧五代史》同日进一步写明赦五月二十七日前所犯罪，大辟以下都免除。','具体赦罪截止日与主书一月自首期限分别保留，不混成同一时间限制。',relation='adds')
add('taining_reduced_defense_prefecture','郭威把泰宁军降为防御州',23,'癸未，',None,[('帝','降低泰宁军军镇等级')],when='952年五月癸未',place='泰宁军、兖州',note='降为防御州为等级变化，不直接译成废除兖州或迁走全部人口。')
add('li_jianxun_final_instructions_death','李建勋去世，临终要求不筑坟丘、不立碑，以免墓被掘',24,'唐司徒致仕李建勋卒，','免为他日开发之标。”',[('李建勋','临终要求家人不筑坟丘、不立碑，随后去世')],when='952年五月条下，具体死亡日未载',place='南唐',note='良死幸矣是临终自述；勿封土为不筑明显坟丘，不写成遗体没有埋葬。')
claim('person',people['李建勋'],'death_year','李建勋在952年五月条下去世，具体日未载。',24,'唐司徒致仕李建勋卒，','同年明确，已致仕司徒沿既有主体。')
add('li_jianxun_tomb_unlocated','史书追述南唐灭亡时贵人墓多被掘，李建勋墓却无人知道位置',24,'及江南之亡也，',None,[],year=None,when='南唐灭亡时的后世追述，此事不发生在952年死亡当时，具体掘墓日未载',place='南唐旧境',note='无不发是史家概括，不列未具名墓葬；没有具体定位或独立考古证据，不给现代坐标。')
reviews={17:'萧多疏、误判死罪、钟李欲杀与冯请求宽免获免分清，妇人误杀为冯讲话说明。徐景运罢相相邻不当因萧案而罢。',18:'四月丙戌朔日食旧本纪印证，礼制避殿与未核天文坐标分清。',19:'乙卯亲征令与李谷留守、郑大内守、郭崇京巡分别录；旧记下月初五为拟定行程，不覆盖实际五月戊辰到兖。',20:'驻益阳与兼桂招为取湖南后追述，不重复知全州。罢役撤戍授刘言为讨论，孙赞与冯反、侯五千增援、伏兵夹击侯死、张收数百回全州分开，不把谈判方案当已实行。',21:'庚申发梁、戊辰城下、己巳招谕、庚午攻令分录；不逊者为城上人，不替慕亲说。',22:'术士欺词与立祠黄幡为反叛前追述，藏财与兵降为史述，乙亥破城、慕夫妻投井、继勋被获杀、官军掠与死数分别录。旧斩夷与主新投井并列。二千帐下盗众补筹备人数，不重造每次招募抢掠。',23:'欲诛未行、窦冯范请赦与实际宽免相连，宋窦传印证。丁丑颜任与旧书破城条编排不同不强同日；壬午曲赦、亲属免及癸未降州分开。',24:'952李死与临终不封土立碑解释清楚，开发为掘墓；江南亡时墓后事是多年后追述，不强系952发生或给未核墓址。'}
assert not (P/'publication.json').exists()
for n in range(17,25):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=952,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],next_volume=290,next_year=952,supplements=supplements,excluded_non_body=[],coverage='卷290原106—113行连续八段；本年跨卷290、291，后续仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,25)],source_issues_review='逐字引文保持底本，纸本未核。攻克久未克疑重复字不改源；拟初五与实际出发到城分清。慕死法主新投井与旧斩夷、颜任纪时编排分别保留。宋窦传按正文核传主，李墓后事不当952史事。',plain_language_review='首次逐条检查标题、人物、角色、关系方向、日期和引用解释。请求与结果、拟定与实际、人物看法与史家评价、比喻与事实明确区分，展示白话而引用保原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
