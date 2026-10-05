# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 948 paragraphs 33–42."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,70))
COMMIT='e4f57a30a26d134a760f4628c87dbbe735d6f3c2'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-288-948-april-august','xinwudaishi-064-zhang-ye-fall']:
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
main_sources = ['tongjian-288-948-april-august','tongjian-288-948-august-september']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0948-p033-p042',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'songshi-262-li-tao-dismissal':'卷262·李涛传·免相','tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
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
lines = (ROOT / 'resources/derived/tongjian/288.txt').read_text().splitlines()
for n in range(33, 43):
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
    labels={'songshi-262-li-tao-dismissal':'卷262·李涛传·免相','tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷288·乾祐元年（948年七月至八月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0948_06_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=948, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='948年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_288_0948_' + code
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
        edge = 'participation_zztj_288_0948_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_288_0948_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'崇':'刘崇（刘知远弟）','刘旻':'刘崇（刘知远弟）','刘崇':'刘崇（刘知远弟）','蜀主':'孟昶','汉帝':'刘承祐','钱弘亻叔':'钱弘俶'})
NEW_ALIASES={'徐光溥':['徐光溥（后蜀官员）'],'郑珙':['鄭珙'],'常思':[],'扈彦珂':['扈彥珂']}
NEW_DESCRIPTIONS={
 '徐光溥':'后蜀官员。948年由翰林学士、兵部侍郎任中书侍郎兼礼部尚书，与李昊一同加同平章事。生卒年未据本段确定。',
 '郑珙':'青州人，刘崇的节度判官。刘崇因与郭威有嫌隙而忧惧时，郑珙劝他谋求自保；《新五代史》也记类似谋议，但安排在郭威讨平三镇之后，与《资治通鉴》的叙述顺序不同。生卒年未据本次原文确定。',
 '常思':'后汉昭义节度使。948年讨伐李守贞等三镇时曾驻潼关，后来与郭威、白文珂、刘词分三路进攻河中。生卒年未据本段确定。',
 '扈彦珂':'后汉镇国节度使。948年郭威督军讨伐三镇时，建议先攻作为盟主的李守贞，避免先攻长安、凤翔而腹背受敌，郭威采纳。生卒年未据本次原文确定。'}
aug='jiuwudaishi-101-august-948';dispatch='xinwudaishi-011-guo-dispatch';rewards='xinwudaishi-011-guo-rewards';liuzheng='xinwudaishi-070-liu-zheng-counsel';hu='songshi-254-hu-hezhong-strategy';zhao='xinwudaishi-064-zhang-ye-fall';j='948年七月，具体日未载';a='948年八月，具体日未载'
add('li_hao_shu_chancellor','李昊任门下侍郎兼户部尚书、同平章事',33,'蜀主以','兼户部尚书，',[('孟昶','任命李昊为门下侍郎兼户部尚书，并加同平章事'),('李昊','由翰林承旨、尚书左丞升任')],when=j,place='后蜀朝廷',note='并同平章事在全段末尾同时用于李昊和徐光溥，两人任命分别录入。')
# Extend the evidence span to include the shared final chancellor title.
for c in B['claims']:
 c['note']=c['note'].replace('原文：'+span(33,'蜀主以','兼户部尚书，')+'；','原文：'+Q[33]['text']+'；')
add('xu_guangpu_shu_chancellor','徐光溥任中书侍郎兼礼部尚书、同平章事',33,'蜀主以',None,[('孟昶','任命徐光溥为中书侍郎兼礼部尚书，并加同平章事'),('徐光溥','由翰林学士、兵部侍郎升任')],when=j,place='后蜀朝廷',note='光溥按原字识别，不凭近形字或与李昊同任而合并人物。')
add('an_accuses_zhao_tingyin','安思谦指控赵廷隐谋反，企图取代其军职',34,'蜀安思谦','欲代其位，',[('安思谦','谋划排除旧将，指控赵廷隐并想取代其位'),('赵廷隐','以卫圣都指挥使兼中书令身份受到指控')],year=None,when='948年七月甲戌解职以前，指控具体年月未载',place='后蜀',note='谋、欲是意图，谮是史书对指控的定性，不能将指控当成赵廷隐确实谋反。')
add('an_soldiers_surround_zhao_house','安思谦夜间派兵包围赵廷隐宅邸',34,'夜，','发兵围其第。',[('安思谦','夜间发兵围宅'),('赵廷隐','宅邸被包围')],year=None,when='948年七月甲戌解职之前的一夜，具体年月日未载',place='赵廷隐宅邸',note='其第承接被指控的赵廷隐；围宅是已发生行动，不补搜查、逮捕或战斗伤亡。')
add('li_tinggui_defends_zhao','李廷珪为赵廷隐申辩，赵廷隐得以免罪',34,'会山南','乃得免。',[('李廷珪','以山南西道节度使身份入朝，力陈赵廷隐无罪'),('赵廷隐','因李廷珪申辩得以免罪')],year=None,when='948年七月甲戌解职之前，具体月日未载',place='后蜀朝廷',note='乃得免承接谋反指控处置；未补原文没有的审判程序或免除某种具体刑罚。')
add('zhao_tingyin_released_military_office','赵廷隐以病请求解除军职，孟昶准许',34,'廷隐因称疾，',None,[('赵廷隐','以病为由反复请求解除军职'),('孟昶','在甲戌准许赵廷隐请求')],when='948年七月甲戌准许，提出请求日未载',place='后蜀朝廷',note='称疾是本人理由，不判定实际疾病；解除军职不等于免去所有官爵。')
sup('zhao_tingyin_released_military_office',34,zhao,'王處回、趙廷隱相次致仕，','《新五代史》把王处回、赵廷隐离开职务概括为相继致仕。','该句未列甲戌，也不独立记李廷珪申辩；赵廷隐此后仍获官爵及问政安排，不能写成完全失去政治身份。',relation='adds')
add('zhao_hui_reaches_changan','凤翔节度使赵晖到达长安',35,'风翔','至长安。',[('赵晖','以凤翔节度使身份到长安')],when='948年七月乙亥上表之前，到达具体日未载',place='长安',note='底本风翔为地名异写，展示统一凤翔，逐字引用保留；到长安不是已进入凤翔城。')
add('zhao_hui_requests_attack_wang','赵晖上表报告王景崇反叛，请求进兵',35,'乙亥，',None,[('赵晖','上表报告反叛并请求进兵'),('王景崇','成为上表报告及拟进攻对象')],when='948年七月乙亥',place='长安至后汉朝廷',note='上表日期与进兵实际发生日分开，不写成乙亥已经攻克凤翔。')
add('liu_chong_guo_wei_old_rivalry','刘崇在河东任职时与郭威争权，结下嫌隙',36,'初，高祖','争权，有隙。',[('刘崇','在刘知远镇河东时任马步都指挥使，与郭威争权'),('郭威','任蕃汉都孔目官时与刘崇争权'),('刘知远','当时镇守河东')],year=None,when='刘知远镇守河东时的追叙，具体年月未载',place='河东',note='崇沿已有刘崇，后改名刘旻；初段不是948年八月发生，也不沿南汉刘岩主体。')
add('zheng_counsels_liu_self_protection','刘崇忧惧郭威掌权，郑珙劝他谋求自保',36,'及威执政，','珙，青州人也。',[('刘崇','因郭威执政而忧惧，接受自保建议'),('郑珙','作为节度判官劝刘崇谋求自保'),('郭威','成为刘崇忧惧的掌权者')],year=None,when='《资治通鉴》置于948年八月募兵前的追述，谋议具体年月未载',place='河东',note='接受自保建议不等于此时称帝或公开与后汉决裂；郑珙籍贯青州据此句。')
sup('zheng_counsels_liu_self_protection',36,liuzheng,'隱帝少，政在大臣，周太祖為樞密使，新討三叛，立大功，而與旻素有隙，旻頗不自安，','《新五代史》也记刘崇与郭威不和，但把忧惧和郑珙谋议放在郭威新讨三叛、立功以后。','主书把谋议置于948年八月募兵前，传记叙述则接讨平三叛；时序差异保留，不据传记标题强定同一日。',relation='conflicts',field='time_original')
sup('zheng_counsels_liu_self_protection',36,liuzheng,'旻曰：「子言，乃吾意也。」乃罷上供征賦，收豪傑，籍丁民以益兵。','《新五代史》也记刘崇接受建议，停止上供、收纳豪杰并扩充兵员。','动作相合，但该书安排在郭威讨三叛之后；不以动作相合消除时序差异。')
add('liu_chong_requests_four_units','刘崇上表请求招募四个指挥的兵员',36,'八月，','崇表募兵四指挥，',[('刘崇','上表请求募兵四个指挥')],when='948年八月庚辰',place='河东至后汉朝廷',note='四指挥是军队编制名称，不解释成四个人或擅自换算兵力；表是奏请，不补朝廷已准。')
add('liu_chong_builds_local_resources','刘崇以防备契丹为名扩充兵备，停止向朝廷上供',36,'自是选募',None,[('刘崇','开始选募、招纳逃亡者、修整甲兵充实府库，停止上供并多不奉诏')],when='948年八月庚辰募兵奏请之后，后续持续时段未载',place='河东',description='刘崇此后开始选募勇士、招纳逃亡者、修整甲兵并充实府库，停止向朝廷上供财赋，均以防备契丹为名；朝廷诏令也多不遵从。',note='皆以备契丹为名是原文所述名义，不判定契丹正在进攻；多不禀承不是断言所有诏令都拒绝。')
add('han_generals_deployment_before_guo','后汉诸将分驻潼关、同州、咸阳，讨伐三镇',37,'自河中','赵晖屯咸阳。',[('常思','以昭义节度使身份驻潼关'),('白文珂','驻同州'),('赵晖','驻咸阳'),('李守贞','据河中拒命，成为讨伐对象'),('赵思绾','据永兴拒命，成为讨伐对象'),('王景崇','据凤翔拒命，成为讨伐对象')],when='948年八月郭威督军之前的部署，具体日未载',place='潼关、同州、咸阳',note='驻地与各自奉命讨伐对象按原文分清；不将旧部署当作壬午郭威任命后的新命令。')
sup('han_generals_deployment_before_guo',37,dispatch,'隱帝遣白文珂、郭從義、常思等分討之，久皆無功。','《新五代史》也记刘承祐先派白文珂、郭从义、常思等分头讨伐，久未取得成果。','此句印证先行分讨及进展迟缓，没有独立列明各驻地。')
add('guo_congyi_wang_jun_stalemate','郭从义和王峻在长安附近设营，因不和而迟迟不战',37,'惟郭从义、','莫肯攻战。',[('郭从义','与王峻置栅近长安，二人不和，迟迟不攻'),('王峻','与郭从义置栅近长安，二人不和，迟迟不攻')],when='948年春至秋，具体日未载',place='长安附近',note='相恶如水火为史书对不和程度的描述，不据此扩大为终身仇敌；相持未攻与已经战败分开。')
add('liu_chengyou_plans_senior_supervision','刘承祐因战事停滞，打算派重臣督军',37,'帝患之，','欲遣重臣临督。',[('刘承祐','忧虑战事停滞，拟派重臣临督')],when='948年八月壬午任命前，具体日未载',place='后汉朝廷',note='帝为后汉隐帝刘承祐；计划与下一句实际任命分开。')
add('guo_wei_west_supervisor','郭威任西面军前招慰安抚使，统管诸军',37,'壬午，','诸军皆受威节度。',[('郭威','受命为西面军前招慰安抚使，诸军受其节制'),('刘承祐','任命郭威统管西面诸军')],when='948年八月壬午',place='后汉朝廷、西面行营',note='本次督军职与七月庚申加同平章事分开，不重复建立已发布的加衔事件。')
sup('guo_wei_west_supervisor',37,aug,'壬午，命樞密使郭威赴河中府軍前，詔河府、永興、鳳翔行營諸軍，一稟威節制。','《旧五代史》同记八月壬午命郭威赴河中，河府、永兴、凤翔行营均受其节制。','本纪印证日期及统辖范围，不以赴军前诏令证明此日已经到达河中。')
sup('guo_wei_west_supervisor',37,dispatch,'乃加拜威同中書門下平章事，使西督諸將。','《新五代史》把郭威加同平章事与督军合并叙述。','该书没有分列七月加衔和八月督军的日期，按《通鉴》分别录入并保留传记概述。',relation='adds')
add('feng_dao_counsels_guo_rewards','冯道建议郭威用赏赐争取士卒，削弱李守贞的依靠',37,'威将行，','则夺其所恃矣。”',[('郭威','出发前向冯道问策'),('冯道','建议不要吝惜官物，用赏赐争取士卒'),('李守贞','其士卒支持被列为需要削弱的依靠')],when='948年八月郭威将出发时，具体日未载',place='后汉，问策地点未载',note='这是策略建议，不把守贞亡或三镇已平作为已发生结果；冯道官职太师据此句。')
add('guo_follows_reward_advice','郭威采纳冯道建议，开始赢得士卒支持',37,'威从之。',None,[('郭威','采纳建议，用赏赐争取士卒支持')],when='948年八月问策以后，具体日未载',place='郭威军中',note='由是为史书对士卒归附原因的解释，不写成所有原属李守贞士卒已同时投降。')
sup('guo_follows_reward_advice',37,rewards,'上所賜予，與諸將會射，恣其所取，其餘悉以分賜士卒，將士皆懽樂。','《新五代史》补记郭威把皇帝所赐物品供诸将射取，剩余分给士卒，将士欢喜。','该段没有再提冯道，不将其作为冯道建议的独立证明，只补郭威实际赏赐。',relation='adds')
add('bai_ordered_hezhong','后汉命白文珂赶赴河中',38,'诏白文珂','趣河中，',[('白文珂','奉诏赶赴河中')],when='948年八月壬午督军诏令之后，具体日未载',place='河中',note='趣为催促前往，不能据命令写成已经到达或攻克河中。')
add('zhao_hui_ordered_fengxiang','后汉命赵晖赶赴凤翔',38,'赵晖',None,[('赵晖','奉诏赶赴凤翔')],when='948年八月壬午督军诏令之后，具体日未载',place='凤翔',note='底本风翔照留引用，展示统一凤翔；指令与实际抵城分开。')
add('zhao_tingyin_song_prince','孟昶任赵廷隐为太傅，封宋王',39,'甲申，','赐爵宋王，',[('孟昶','任赵廷隐为太傅，封宋王'),('赵廷隐','解军职后获太傅官职和宋王爵位')],when='948年八月甲申',place='后蜀朝廷',note='宋王是爵号，不是成为宋朝君主；仍沿既有赵廷隐人物。')
add('meng_consults_zhao_home','孟昶安排国家大事到赵廷隐宅邸咨询',39,'国有大事，',None,[('孟昶','安排国有大事时到赵廷隐宅邸咨询'),('赵廷隐','退职后仍获咨询国事的安排')],when='948年八月甲申任官时所载安排，具体咨询日期未载',place='赵廷隐宅邸',note='这是遇国事咨询的安排，不虚构一次具体会议内容、参加者或日期。')
add('shu_renames_fengxiang_qiyang','后蜀将凤翔改称岐阳军',40,'戊子，','曰岐阳军，',[('孟昶','将凤翔改称岐阳军')],when='948年八月戊子',place='凤翔、岐阳军',note='记录后蜀所定军号，不当作后汉也已认可此名称或后蜀军已实际占领凤翔。')
add('shu_appoints_wang_qiyang','后蜀授王景崇岐阳节度使、同平章事',40,'己丑，',None,[('孟昶','任命王景崇为岐阳节度使、同平章事'),('王景崇','接受后蜀所授岐阳节度使、同平章事')],when='948年八月己丑',place='后蜀、岐阳军',note='授爵与后蜀出兵占领分开；两朝任命背景保留，不覆盖此前李守贞授官事件。')
add('han_confirms_qian_hongchu','后汉授钱弘俶东南兵马都元帅等官职与吴越国王爵',41,'乙未，',None,[('钱弘俶','获东南兵马都元帅、镇海镇东节度使兼中书令、吴越国王官爵'),('刘承祐','授予钱弘俶相关官爵')],when='948年八月乙未',place='后汉朝廷、吴越',note='底本钱弘亻叔为拆字写法，沿已有钱弘俶；这是朝廷授官封爵，不将其此前在吴越掌权起点改成此日。')
sup('han_confirms_qian_hongchu',41,aug,'乙未，兩浙節度使、檢校太尉、兼侍中、吳越國王錢宏俶加檢校太師、兼中書令、東南面兵馬都元帥。','《旧五代史》同记八月乙未钱弘俶获加官，写钱宏俶，并列检校太师、兼中书令、东南面兵马都元帅。','弘与宏的异写沿同一吴越主体；本纪前衔和加衔与主书所列完整官爵分别保留。',relation='adds')
add('generals_propose_changan_fengxiang','诸将建议郭威先攻长安、凤翔',42,'郭威与','先取长安、凤翔。',[('郭威','与诸将讨论讨伐次序')],when=a,place='后汉西面行营',note='诸将未具姓名，不把后来提出反对意见的扈彦珂也记为支持此方案的人。')
add('hu_counsels_hezhong_first','扈彦珂建议先攻河中，郭威采纳',42,'镇国节度使','威善之。',[('扈彦珂','建议先击作为三镇盟主的李守贞，避免腹背受敌'),('郭威','赞同先攻河中的建议'),('李守贞','被视为三镇盟主及优先攻击对象')],when=a,place='后汉西面行营',note='守贞亡则两镇自破是战略判断，不写成此时三镇已经被平定。')
sup('hu_counsels_hezhong_first',42,hu,'彥珂曰：「三叛連衡，推守貞為主，宜先擊河中；河中平，則永興、鳳翔失勢矣。今舍近圖遠，若景崇、思綰逆戰於前，守貞兵其後，腹背受敵，為之奈何？」周祖從其言，','《宋史》同记扈彦珂建议先攻河中，郭威听从。','周祖为郭威，属于后世传记称号；不将当时郭威写成已称帝，也未以此完成后续平河中事件。')
add('three_routes_attack_hezhong','郭威、白文珂、刘词和常思分三路进攻河中',42,'于是威自','三道攻河中。',[('郭威','从陕州出兵河中'),('白文珂','与刘词从同州出兵河中'),('刘词','与白文珂从同州出兵河中'),('常思','从潼关出兵河中')],when=a,place='陕州、同州、潼关至河中',note='三道是分路进攻，不是三名将领；刘词军号主书宁江、旧史夔州分别保留，未据此新建另一人。')
sup('three_routes_attack_hezhong',42,aug,'癸巳，以奉國左廂都指揮使、閬州防禦使劉詞為夔州節度使，充侍衛步軍都指揮使兼河中行營都虞候；','《旧五代史》补记刘词在八月癸巳任夔州节度使、侍卫步军都指挥使兼河中行营都虞候。','此句作为出兵时职务补证，癸巳是任官日期，不当三路出兵日期；主书称宁江，与夔州军州表述分别保留。',relation='adds')
add('guo_wei_cares_for_soldiers','郭威厚赏军功、慰问伤兵，并宽和接纳将士意见',42,'威抚养士卒，',None,[('郭威','与士卒同苦乐、厚赏军功、探视伤兵，并宽和接纳意见')],when='948年八月出兵河中时所述治军作风，具体各行动日期未载',place='郭威军中',description='郭威与士卒同甘共苦，有小功也重赏，受轻伤也亲自探视；将士有所陈述时，他温和接纳，对冒犯及小过不轻易责罚。史书说将卒因此归心于他。',note='这是书中概括的治军作风，未补具体赏赐数目或无条件免除一切军法。')
sup('guo_wei_cares_for_soldiers',42,rewards,'威居軍中，延見賓客，褒衣博帶，及臨陣行營，幅巾短後，與士卒無異；','《新五代史》也记郭威临阵时穿着简便，与士卒没有区别。','补充与士卒相近的衣着细节，该段后文的围城、攻克属于后续，未提前录入。',relation='adds')
reviews={33:'李昊与徐光溥任官分录，段末并同平章事共同限定；引用完整句以支持李昊加衔。',34:'安思谦谋排旧将及指控、夜围宅、李廷珪申辩与甲戌解军职分录；谋反指控不当证实，称疾不作诊断。',35:'赵晖到长安与乙亥请进兵分录；底本风翔展示按凤翔，引用不改。',36:'河东争权及郑珙建议为未定年月追叙，庚辰表募四指挥及随后充实兵备停止上供分录。新史把谋议放在讨三叛立功后，保留时序差异。',37:'各将驻地、郭王不和停战、隐帝拟派重臣、壬午郭威任职、冯道建议与采纳分录。新史合述七月加衔及出征不合并成一日，赏赐不能提前写平定结局。',38:'白文珂趣河中与赵晖趣凤翔两项命令分录，指令不等于已抵城。',39:'甲申太傅宋王与有大事到宅问政安排分录，不推任宋朝君主或具体会议。',40:'戊子改军号与己丑授王景崇官爵分录，不等于后蜀已经实占凤翔。',41:'钱弘亻叔沿规范主体钱弘俶，旧史钱宏俶印证；官爵授予日不当实际继位日。',42:'诸将先攻两城方案与扈彦珂先河中方案分录，郭威采纳后四将三路出兵及治军作风分录；扈与霍彦珂经家族出处区分，旧史刘词癸巳任官只作为职务补证。'}
assert not (P/'publication.json').exists()
for n in range(33,43):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=948,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(33,43)],next_paragraph=Q[43]['id'],next_volume=288,next_year=948,supplements=supplements,excluded_non_body=[],coverage='卷288原39—48行连续十段，本卷42/69；卷287已19段，全年61/88，未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(33,43)],source_issues_review='底本风翔及钱弘亻叔展示规范化、引用原字保留。刘崇沿既有刘崇（刘知远弟）主体，与萧县同名人物分开；郑珙谋议在新史的叙述时序不同，独立保留。郭威加衔和督军日期分开；扈彦珂不与霍彦威之弟混同。',plain_language_review='首次逐条检查全部新人物、事件、时间说明、参与角色及事实说明；明确人物主语，区分指控、计划、命令、执行和史书评价。引文逐字保留，未定年月追叙为null，不把策略预期写成平定结果，不安排发布后二次全文重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
