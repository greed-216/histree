# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 285, year 945 paragraphs 1–10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,24))
COMMIT='e77e2ab2ec0aa76443441349e3b3533923c10437'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['xinwudaishi-009-945','xinwudaishi-068-li-ren-da','jiuwudaishi-084-945-august','jiuwudaishi-109-du-leaves','jiuwudaishi-089-feng-yu']:
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
main_sources = ['tongjian-285-945-august-november']
B = {'format_version': 1, 'batch_key': 'zztj-v285-y0945-p001-p010',
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
lines = (ROOT / 'resources/derived/tongjian/285.txt').read_text().splitlines()
for n in range(1, 11):
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
    for a,b in [('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('旧史','《旧五代史》'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
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
        citation = f'卷285·后晋开运二年（945年八月至九月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_285_0945_01_{len(B["claims"])+1:04d}'
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
    key = 'event_zztj_285_0945_' + code
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
        edge = 'participation_zztj_285_0945_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_285_0945_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'石重贵','杜威':'杜重威','唐主':'李璟','汉主':'刘弘熙','刘晟':'刘弘熙','闽主':'王延政','弘雅':'刘弘雅','李彦韬':'李彦韬（后晋宣徽使）','弘义':'李仁达','李弘义（福州）':'李仁达','冯延己':'冯延巳'})
NEW_ALIASES={'王建封':[],'王钦祚':['王欽祚']}
NEW_DESCRIPTIONS={'王建封':'上元人，南唐将领。945年《资治通鉴》记他以先锋桥道使身份率先登上建州城墙，南唐军随后攻破建州。生卒年本段未载。','王钦祚':'后晋殿中监。945年暂掌恒州事务，奉命征购军粮，把杜重威在恒州的十余万斛粮食登记上报。杜重威上表指责此事，朝廷召王钦祚回京。《旧五代史》也记他奉命在镇州买粮，并在王瑜传记其父钦祚曾任殿中监。生卒年本段未载。'}
a='945年八月条下，具体日未载';s='945年九月条下，具体日未载'
oa='jiuwudaishi-084-945-august';os='jiuwudaishi-084-945-september';ny='xinwudaishi-009-945';mi='xinwudaishi-068-li-ren-da';my='xinwudaishi-068-fall-year';hy='xinwudaishi-065-hongya-death';dl='jiuwudaishi-109-du-leaves';fy='jiuwudaishi-089-feng-yu';wq='jiuwudaishi-096-wang-qinzuo'
add('august_solar_eclipse','史书记载八月初一发生日食',1,'八月，',None,[],when='945年八月甲子朔',place='后晋',note='按史书观测记录保留，不推断日食覆盖地区与天文参数。')
sup('august_solar_eclipse',1,oa,'八月甲子朔，日有蝕之。','《旧五代史》同记八月甲子朔日食。','同日观测记录，未加入现代天文换算。')
# 2: appointments and a sequence of practices, assessments and rejected advice.
add('he_ning_leaves_chancellorship','和凝罢相，保留右仆射本官',2,'丙寅，','本官。',[('和凝','罢去宰相职务，保留右仆射本官')],when='945年八月丙寅',place='后晋朝廷',note='罢守本官不是撤去全部官职，本官由其右仆射身份与旧本纪确认。')
sup('he_ning_leaves_chancellorship',2,oa,'丙寅，宰臣和凝罷相，守右僕射。','《旧五代史》明确和凝罢相后守右仆射。','同日任免，不能写成辞去右仆射。')
sup('he_ning_leaves_chancellorship',2,ny,'丙寅，和凝罷。','《新五代史》同记丙寅和凝罢相。','简略本纪与同日具体官命对读。')
add('feng_yu_becomes_chancellor','石重贵加冯玉中书侍郎、同平章事，将大小政事交给他',2,'加枢密使、','委之。',[('帝','加冯玉宰相职，将大小政事交给他'),('冯玉','以枢密使、户部尚书身份加中书侍郎、同平章事')],when='945年八月丙寅',place='后晋朝廷',note='这是八月加相职，二月授枢密使已在之前批次，不重复生第二次初任枢密使。')
sup('feng_yu_becomes_chancellor',2,oa,'以樞密使馮玉為中書侍郎、平章事，使如故。','《旧五代史》同记冯玉任中书侍郎、平章事，仍任枢密使。','使如故指枢密使职不变，不误作撤去枢密使。',relation='adds')
sup('feng_yu_becomes_chancellor',2,ny,'馮玉為中書侍郎、同中書門下平章事。','《新五代史》同记冯玉任中书侍郎、同中书门下平章事。','同次加相职，各书官名详略保留。')
add('shi_assumes_safety_after_yangcheng','石重贵在阳城胜利后认为天下安稳，史书记其奢侈加剧',2,'帝自阳城之捷，','益甚。',[('帝','阳城胜利后自认为天下无虞，史书记其奢侈加剧')],when='945年阳城战胜之后的情形，具体日未载',place='后晋朝廷',note='天下无虞是石重贵判断，骄侈是史书评价，不写成实际上边境已经安全。')
add('shi_keeps_regional_treasures','四方进献的珍奇物品都收入石重贵内库',2,'四方贡献','内府。',[('帝','将各地进献珍奇收归内府')],when='阳城胜利之后的朝廷常态，具体起止年月未载',year=None,place='后晋宫廷',note='内府为宫廷内库，不加未经核实的进献总额。')
add('shi_expands_palaces_and_luxury','石重贵大量制作器玩，扩建宫室并装饰后宫',2,'多造器玩，','莫之及。',[('帝','大量制作器玩、扩建宫室和装饰后宫')],when='阳城胜利之后的宫廷营建，具体起止年月未载',year=None,place='后晋宫廷',note='近朝莫之及是史书比较评价，未列建筑清单不自行补项目。')
add('shi_builds_weaving_tower','石重贵建织锦楼，用数百织工织地毯，历时一年完成',2,'作织锦楼','乃成。',[('帝','营建织锦楼，征用数百织工织地毯')],when='阳城胜利后的营建追述，历时期年，开始与完成的确切年份未载',year=None,place='后晋宫廷',note='期年是历时，不能把工程开始和完成都写成945年八月；地衣指铺地织物，不是现代生物地衣。')
add('shi_rewards_entertainers_excessively','史书记石重贵对优伶的赏赐没有节制',2,'又赏赐','无度。',[('帝','对优伶赏赐频繁，史书记为无度')],when='945年八月条下所述朝廷常态，具体起止日未载',place='后晋宫廷',note='无度为史书评价，不补准确赏赐总额。')
add('sang_warns_soldiers_about_rewards','桑维翰比较战士与优伶所得，警告赏赐失衡会使士卒离心',2,'桑维翰谏曰：','乎！”',[('桑维翰','以伤兵所得远少于优伶为由，劝石重贵纠正赏赐失衡'),('帝','受到桑维翰关于士卒离心的警告')],when=a,place='后晋朝廷',note='战士议论为桑维翰谏辞中的设问，不造具名说话战士，也不把士卒解体的风险写成此时已全军哗变。')
add('shi_rejects_sang_reward_advice','石重贵不听桑维翰关于赏赐的劝谏',2,'帝不听。','帝不听。',[('帝','不采纳纠正赏赐失衡的建议'),('桑维翰','劝谏未被采纳')],when=a,place='后晋朝廷')
add('feng_wins_favor_by_accommodation','冯玉迎合石重贵的意愿，得到更多宠信',2,'冯玉每善','有宠。',[('冯玉','通过迎合石重贵意愿增加宠信'),('帝','更加宠信冯玉')],when='945年八月条下的朝廷情形，具体起止日未载',place='后晋朝廷',note='迎合与得宠为史书描述，不为每次迎合造具体行动。')
sup('feng_wins_favor_by_accommodation',2,fy,'玉每善承迎帝意，由是益有寵。','《旧五代史》馮玉传的补阙按语引《资治通鉴》，也载迎合得宠。'.replace('馮','冯'),'这是补阙按语明确引《通鉴》，属于相互依赖文本，不算另一份独立确证。')
add('shi_waits_for_feng_appointments','冯玉患病在家时，石重贵令刺史以上任命等他回来才办理',2,'尝有疾在家，','其倚任如此。',[('冯玉','患病在家，石重贵让重要任命等他复出'),('帝','宣布刺史以上官职的任命须等冯玉回来')],when='冯玉患病在家时，具体年月日未载',year=None,place='后晋朝廷',note='尝有疾是追述一次情况，不把复出时间推为当前八月；除指任命官职，不是除去官员。')
sup('shi_waits_for_feng_appointments',2,fy,'嘗有疾在家，帝謂諸宰相曰：「自刺史以上，俟馮玉出，乃得除。」','《旧五代史》补阙按语引用《通鉴》的同一句任官等待记载。','依赖性引用保留定位，不能当作第二份独立证据。')
add('feng_receives_bribes','史书记冯玉乘势弄权，各地贿赂集中到他家',2,'玉乘势','益坏。',[('冯玉','借宠信弄权，接受四方集中送来的贿赂')],when='945年八月条下的朝政情形，具体起止日未载',place='后晋朝廷、冯玉私第',note='朝政益坏是史书评价，不补具体贿赂金额与未名送礼者。')
sup('feng_receives_bribes',2,fy,'玉乘勢弄權，四方賂遺，輻輳其門，由是朝政日壞。','《旧五代史》补阙按语引用《通鉴》，同记冯玉弄权受贿及朝政败坏。','保留依赖关系，不作为独立数字或独立判断。')
# 3: loyalty under a long siege; speaking and response are separate.
add('jianzhou_people_waver','建州被长期围困，城内人心动摇',3,'唐兵围','离心。',[],when=a,place='建州',note='既久没有给出准确围城天数，不换算开始日；人心动摇不等同所有军民已经叛变。')
add('dong_advised_to_choose_side','有人劝董思安及早决定去留',3,'或谓董思安：','就？”',[('董思安','被劝在围城困境中及早决定去留')],when=a,place='建州',note='劝者未具名，不造占位人物；去就是去留选择，尚未执行倒戈。')
add('dong_refuses_betrayal','董思安表示世代侍奉王氏，不能在危难时背叛',3,'思安曰',None,[('董思安','表示不能在王氏危难时背叛，众人受感动而未叛')],when=a,place='建州',note='世事王氏为董思安自述，未列祖先姓名不添谱系；众无叛者限定该场景，不否认其他地区投降。')
# 4: storming, surrender, losses and civilian welcome followed by destruction.
add('wang_jianfeng_first_climbs','王建封率先登上建州城墙',4,'丁亥，','先登，',[('王建封','以南唐先锋桥道使身份率先登城')],when='945年八月丁亥',place='建州',note='上元为籍贯，先登是登城不是首先到建州；先锋桥道使是官职称号。')
add('tang_takes_jianzhou','南唐军攻破建州',4,'遂克建州，','遂克建州，',[],when='945年八月丁亥；《新五代史》记为保大四年（946年）',place='建州',note='主书日次明确；另书纪年异说并列，未凭电子本裁出唯一正确年份。')
sup('tang_takes_jianzhou',4,mi,'而景兵攻破建州，遷延政族於金陵，封鄱陽王。是歲，景保大四年也。','《新五代史》闽世家也记南唐攻破建州，但该书纪年为保大四年。','本次只补破城与纪年，迁族和封王留后续对应主线；纪年异说保留。')
sup('tang_takes_jianzhou',4,my,'晉開運三年丙午，南唐保大四年也。是歲，李景兵破建州，王氏滅。','《新五代史》的纪年说明明确把建州陷落放在开运三年、保大四年（946年）。','《资治通鉴》在945年八月记破城；《新五代史》按语还驳《江南录》保大三年说，分歧不能删去或只当本段日次缺失。',relation='conflicts',field='time_original')
add('wang_yanzheng_surrenders','王延政在建州陷落后向南唐投降',4,'闽主延政降。','闽主延政降。',[('闽主','建州陷落后向南唐投降')],when='945年八月丁亥；《新五代史》相关叙事纪年为946年',place='建州')
sup('wang_yanzheng_surrenders',4,my,'留從効聞延政降唐，','《新五代史》也在留从效后续行动的叙事中明确王延政降唐。','只据听闻句补降唐事实，不把留从效执王继勋与此日视为同一时刻。')
add('wang_zhongshun_dies_jianzhou','王忠顺在建州陷落时战死',4,'王忠顺战死，','王忠顺战死，',[('王忠顺','在建州战事中战死')],when='945年八月丁亥',place='建州',note='战死与董思安带兵撤往泉州为不同结局，不混同人物。')
claim('person',people['王忠顺'],'death_year','王忠顺于945年建州战事中战死。',4,'王忠顺战死，','本年明确死亡记事，不覆盖已有发布档案，也不补年龄。')
add('dong_withdraws_quanzhou','董思安整顿部众，撤往泉州',4,'董思安','泉州。',[('董思安','整顿部众，从建州撤往泉州')],when='945年八月建州陷落时',place='建州至泉州',note='整众奔是带部众撤退，不写成被俘或独自逃走。')
add('jianzhou_people_clear_road_for_tang','建州百姓苦于王氏战乱与杨思恭征敛，伐木开路迎南唐军',4,'初，唐兵之来，','迎之。',[('杨思恭','其重敛被史书记为建州百姓迎唐的背景')],when='南唐军最初到建州时，具体年月日未载',year=None,place='建州周边',note='初明确追叙，未用破城日作迎军日；重敛为史书所述背景，不造杨思恭当场下令或亲率迎军。')
add('tang_plunders_jianzhou','南唐军攻破建州后大肆抢掠',4,'及破建州，','大掠，',[],when='945年八月丁亥建州陷落后',place='建州',note='纵兵说明放任士兵抢掠，具体发令者未名，不把查文徽等推成亲手抢掠者。')
add('tang_burns_jianzhou_buildings','南唐军在建州焚烧宫殿和民居',4,'焚宫室','俱尽。',[],when='945年八月丁亥建州陷落后',place='建州',note='俱尽为史书对烧毁程度的描述，不补建筑数量或当代地址。')
add('jianzhou_people_die_cold_rain','建州陷落当夜下冷雨，许多人冻死，百姓失望',4,'是夕，','失望。',[],when='945年八月丁亥夜',place='建州',note='冻死者相枕无准确统计，不写成明确死亡人数；建人失望为史书概述。')
add('li_jing_leaves_troops_unpunished','李璟以攻城有功为由，没有追究南唐军在建州的行为',4,'唐主以',None,[('唐主','因攻城功劳，没有追究军队抢掠焚烧建州的行为')],when='945年建州陷落后，具体日未载',place='南唐朝廷、建州',note='皆不问为不追究责任，不把它写成李璟事前逐项命令烧民居。')
# 5: Southern Han king, already registered as Hongya with a variant 洪雅.
add('liu_sheng_kills_hongya','刘晟杀死韶王刘弘雅',5,'汉主',None,[('汉主','杀死韶王刘弘雅'),('弘雅','被刘晟杀死')],when=a,place='南汉',note='本段汉主是刘晟，沿用已登记的刘弘熙稳定主体，不能沿用已去世刘岩；弘雅与新史洪雅沿用已登记字形异名。')
sup('liu_sheng_kills_hongya',5,hy,'三年，殺其弟洪雅，','《新五代史》同记乾和三年刘晟杀弟刘洪雅。','前两段已核乾和改元及二年，三年对应945；主书八月条下，新史未列月日。保留弘洪异字。')
claim('person',people['刘弘雅'],'death_year','刘弘雅于945年被刘晟杀死。',5,'汉主杀韶王弘雅。','原文明确死亡，人物身份与既有韶王匹配，不新建刘洪雅重复主体。')
relationship('刘晟','刘弘雅','兄长',5,'三年，殺其弟洪雅，','《新五代史》明确被杀者是刘晟的弟弟，方向为刘晟是刘弘雅的兄长，未补生年或排行。',source=hy)
# 6: separate city submissions, distinct from earlier submissions to Zhu/Wang.
for code,name,city,start,end in [('xu_submits_tingzhou','许文稹','汀州','九月，许文稹','汀州，'),('wang_jixun_submits_quanzhou','王继勋','泉州','王继勋','泉州，'),('wang_jicheng_submits_zhangzhou','王继成','漳州','王继成',None)]:
 # Keep the final shared predicate in every excerpt so it supports the destination.
 add(code,f'{name}以{city}向南唐投降',6,'九月，',None,[(name,f'率{city}向南唐投降')],when=s,place=city,note='本句三州共享皆降于唐谓语，摘录包含完整句；此前降朱文进或王延政属于不同阶段。')
add('tang_establishes_yongan_jianzhou','南唐在建州设永安军',6,'唐置',None,[],when=s,place='建州',note='军镇建制变化，不解释为迁走建州全部人口。')
# 7.
add('jing_deputy_north_commander','后晋任景延广为北面行营副招讨使',7,'丙申，',None,[('景延广','以西京留守、兼侍中身份任北面行营副招讨使')],when='945年九月丙申',place='后晋北面行营')
sup('jing_deputy_north_commander',7,os,'九月丙申，以西京留守、北面馬步軍都排陣使景延廣為北面行營副招討使。','《旧五代史》同日任命景延广为北面行营副招讨使。','原有职衔各书详略不同，不能写成景当日首次任西京留守。')
# 8: grain registers, complaint, recalls and compensation.
add('wang_qinzuo_administers_hengzhou','殿中监王钦祚暂掌恒州事务',8,'殿中监','恒州事。',[('王钦祚','以殿中监身份暂掌恒州事务')],when=s,place='恒州',note='权知是暂掌事务，不能写成正式任恒州节度使。')
claim('person',people['王钦祚'],'description','《旧五代史》王瑜传记其父王钦祚曾任殿中监。',8,'王瑜，其先范陽人也。父欽祚，仕至殿中監，出為義州刺史。','姓名与殿中监官职回查作身份补证；义州刺史任期未明，不当作945年新官命，也不提前展开王瑜后半生。',source=wq)
add('jin_orders_wang_buy_grain','恒州缺乏军粮，后晋命王钦祚征购民粮',8,'会乏军储，','民粟。',[('王钦祚','奉朝廷命令征购恒州民粮')],when=s,place='恒州',note='籴为购粮，不能仅凭括字就改成无偿没收。')
sup('jin_orders_wang_buy_grain',8,dl,'會鎮州軍食不繼，遣殿中監王欽祚就本州和市，','《旧五代史》记镇州军粮不足，王钦祚被派到本州和市购粮。','恒州与镇州为同一军镇的不同史称；和市说明购买方式，不能把后续杜重威指责直接当作官方承认没收。',relation='adds')
add('wang_registers_du_grain','王钦祚登记杜重威在恒州的十余万斛粮食，上报朝廷',8,'杜威有','以闻。',[('王钦祚','把杜重威在恒州的十余万斛粟登记上报'),('杜威','在恒州存有十余万斛粮食，被登记奏报')],when=s,place='恒州',note='举籍以闻是登记上报，不擅补粮食已全部运到某仓库；不与五月报献十万斛合成确定同一批已到账粮。')
sup('wang_registers_du_grain',8,dl,'重威私第有粟十餘萬斛，遂錄之以聞。','《旧五代史》同记登记上报杜重威私第十余万斛粟。','数量为概数，不补精确斛数或现代吨数。')
add('du_accuses_grain_confiscation','杜重威上表发怒，指责王钦祚没收他的粮食',8,'威大怒，','臣粟！”',[('杜威','上表质问自己有何罪，指责王钦祚没收粮食'),('王钦祚','被杜重威在奏表中指责没收粮食')],when=s,place='后晋朝廷',note='籍没是杜重威指责，前文记登记购粮，不能将指责改为已证实非法没收。')
sup('du_accuses_grain_confiscation',8,dl,'重威大忿曰：「我非反逆，安得籍沒耶！」','《旧五代史》也记杜重威以自己并非反叛者为由，指责粮食被没收。','两书保留当事人的指责；旧史在发怒前先记给绢偿粟，与主书先抱怨后赐的叙述顺序不同。')
add('jin_recalls_wang_qinzuo','后晋朝廷因杜重威的申诉召王钦祚回京',8,'朝廷为之','祚还，',[('王钦祚','因杜重威申诉被召回'),('杜威','其申诉使朝廷召回王钦祚')],when=s,place='恒州至后晋朝廷',note='召还不等同被处死、流放或永久罢官。')
add('jin_rewards_du_for_reassurance','后晋朝廷厚赐杜重威，安抚他的不满',8,'仍厚赐',None,[('杜威','得到朝廷厚赐安抚')],when=s,place='后晋朝廷',note='原文未给厚赐数额；旧史另述给绢补偿粟价，两书分别描述，不把补价与赏赐认定为同一笔支付。'.replace('不不','不'))
extra('jin_pays_du_grain_price','《旧五代史》记朝廷给杜重威数万匹绢，补偿粟价',8,dl,'朝廷給絹數萬匹，償其粟直。',[('杜威','据《旧五代史》得到数万匹绢作为粮价补偿')],when='945年杜重威粮食被登记奏报时，具体月日未载',place='后晋朝廷、恒州',note='旧史在此后才写杜发怒，与主书先诉后厚赐次序不同；粮价补偿与赏赐可能相涉，保留两书各自动作和次序，不造确定两次支付总额。')
# 9 and 10.
add('jin_establishes_weixin_caozhou','后晋在曹州设威信军',9,'戊申，',None,[],when='945年九月戊申',place='曹州',note='军镇设立不是新建一座曹州城市。')
sup('jin_establishes_weixin_caozhou',9,os,'戊申，升曹州為節鎮，以威信軍為軍額。','《旧五代史》明确升曹州为节镇，以威信军为军额。','同日同事，补建制含义。',relation='adds')
add('li_shouzhen_garrisons_chanzhou','后晋派李守贞驻守澶州',10,'遣侍卫',None,[('李守贞','以侍卫马步都指挥使身份受命驻守澶州')],when=s,place='澶州',note='戍为驻守，不能写成新任澶州节度使；未写独立日，不机械套前段戊申。')
sup('li_shouzhen_garrisons_chanzhou',10,os,'詔李守貞率兵屯澶州。','《旧五代史》也记诏李守贞率兵驻澶州。','该句紧接戊申条，但主书未给独立日，保持各书定位，不强加精确纪日。')
reviews={1:'日食保留史书观察与原纪日，不推现代覆盖图；卷首标题和年标题不录成事件。',2:'和罢相仍右仆射、冯加相仍枢密职分清。阳城后安全感为帝判断；织楼数百织工期年是历时非八月完成，起讫年不明。谏辞风险和战士设问不作实际哗变。旧冯传按语明引通鉴，依赖性注明。',3:'既久无精确日数；匿名劝去留、董世事王氏自述与人未叛保留限定，不推所有闽城同一选择。',4:'王先登、破城、王降、忠顺死、董带兵去泉分别录。迎军初事与破城日分开，杨重敛是背景非现场动作。抢掠焚屋冻死与唐不问分开。新史明确开运三年保大四年破城与通鉴945冲突，未裁定；未提前迁族官命。',5:'汉主刘晟，弘雅洪雅同主体；新史乾和三年顺前后原文核945。兄长方向依据杀其弟，未加排行与生年；未来刘思潮等死留下一段。',6:'三州降唐分别写完整共有谓语，不与前降朱或王混同；永安军为制度设立。留从效执王继勋等尚未到主线，不提前展开。',7:'副招讨任命与此前原职分清，主旧同日；不造新任西京留守。',8:'暂知非节度正式任，乏粮诏征购与登记杜粟、杜指责、召还、厚赐分开。旧史和市与给绢补价单记，先补价后发怒与主书先诉后赏各保次序；不裁成无偿没收。五月报献是否同粟未证。',9:'曹州升节镇与军额，同主旧戊申。',10:'戍澶非授澶节度，主书独立段无日，不强套戊申；旧纪保原对应位置。'}
assert not (P/'publication.json').exists()
for n in range(1,11):
 assert ledger[n-1]['status']=='pending' or (ledger[n-1]['status']=='reviewed' and ledger[n-1]['batch_key']==B['batch_key'])
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=285,year=945,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph=Q[11]['id'],next_volume=285,next_year=945,supplements=supplements,excluded_non_body=[],coverage='卷285原6—15行连续第1—10段，八月至九月及追述。945年跨卷284、285已有35段，本批10段，发布后累计45/58，全年未完成。',source_contexts=[dict(source_key=key,note=note) for key,note in [(main_sources[0],'原文片段包含卷首与后续，但当前只处理1—10正文，不把标题或尚未读段录入。'),(mi,'只补南唐破建州和新史保大四年异说；迁族封王留十月对应主线。'),(my,'用明确的开运三年保大四年破城纪年说明登记异说；留从效未来行动不提前。'),(hy,'只取刘晟杀弟洪雅及兄弟身份；刘思潮等未来记事留下一段，不展开同传后事。'),(dl,'只取王钦祚购粟、登记、给绢和杜指责；未来降契丹等未展开。'),(fy,'当前补阙按语明确引通鉴，不算独立证据。'),(wq,'只取父钦祚任殿中监的身份补证，未把全篇王瑜生平录入。')]],source_issues_review='建州破城945与新史946明确并列；刘弘雅洪雅沿用既有规范。王钦祚买粟和杜称籍没是两种视角，旧补价与主厚赐顺序不同。织锦楼期年不算945八月完工，旧冯传引用通鉴为依赖文本。全部电子本待纸本校核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,11)],plain_language_review='首次逐条核对标题、人物介绍、事件描述、参与和关系方向、时间与事实引用说明，简体白话并明确主语。裁撤职务、实际战争、指控、设问风险、长期追述和具体行动分清；逐字引文保持原底本。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
