# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 54–61."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,84))
COMMIT='31afc3e1ec4e5fd38b43b1838d117faa32a182d4'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-289-950-guo-march','xinwudaishi-010-han-court-killings','xinwudaishi-011-guo-march']:
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
main_sources = ['tongjian-289-950-guo-march','tongjian-289-950-battle-deaths','tongjian-289-950-capital-disorder']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p054-p061',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-289-950-battle-deaths':'卷289·乾祐三年·刘子陂交战与帝死','tongjian-289-950-capital-disorder':'卷289·乾祐三年·京师劫掠与禁止','jiuwudaishi-103-liuzi-battle':'卷103·隐帝本纪·刘子陂交战','jiuwudaishi-103-han-emperor-death':'卷103·隐帝本纪·帝死与京师劫掠','jiuwudaishi-108-zhang-yun-death':'卷108·张允传·仕宦与墜屋','xinwudaishi-045-yuan-sons':'卷45·袁象先传·二子','songshi-261-liu-chongjin-interpreter':'卷261·刘重进传·契丹通事','songshi-261-liu-chongjin-dengzhou':'卷261·刘重进传·汉初邓州','songshi-261-liu-chongjin-han-general':'卷261·刘重进传·乾祐末拒郭威','jiuwudaishi-103-guo-march':'卷103·隐帝本纪·郭威起兵与滑州','xinwudaishi-011-guo-march':'卷11·周本纪·郭威南下','songshi-461-zhao-xiuji-career':'卷461·赵修己传·离开李守贞至翰林天文','tongjian-289-950-guo-march':'卷289·乾祐三年·南下与禁军赏赐','jiuwudaishi-107-wang-zhang-finance':'卷107·王章传·财政措施','xinwudaishi-010-han-court-killings':'卷10·汉本纪·乾祐三年十一月','tongjian-289-950-ministers-conspiracy':'卷289·乾祐三年·诛杀计划及追述','tongjian-289-950-assassination-orders':'卷289·乾祐三年·丙子诛杀与密诏','jiuwudaishi-103-november-950':'卷103·隐帝本纪·乾祐三年十一月','jiuwudaishi-124-wang-yin-origin':'卷124·王殷传·籍贯与驻澶州','tongjian-289-950-november-start':'卷289·乾祐三年·十月至十一月','xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
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
lines = (ROOT / 'resources/derived/tongjian/289.txt').read_text().splitlines()
for n in range(54, 62):
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
    labels={'tongjian-289-950-battle-deaths':'卷289·乾祐三年·刘子陂交战与帝死','tongjian-289-950-capital-disorder':'卷289·乾祐三年·京师劫掠与禁止','jiuwudaishi-103-liuzi-battle':'卷103·隐帝本纪·刘子陂交战','jiuwudaishi-103-han-emperor-death':'卷103·隐帝本纪·帝死与京师劫掠','jiuwudaishi-108-zhang-yun-death':'卷108·张允传·仕宦与墜屋','xinwudaishi-045-yuan-sons':'卷45·袁象先传·二子','songshi-261-liu-chongjin-interpreter':'卷261·刘重进传·契丹通事','songshi-261-liu-chongjin-dengzhou':'卷261·刘重进传·汉初邓州','songshi-261-liu-chongjin-han-general':'卷261·刘重进传·乾祐末拒郭威','jiuwudaishi-103-guo-march':'卷103·隐帝本纪·郭威起兵与滑州','xinwudaishi-011-guo-march':'卷11·周本纪·郭威南下','songshi-461-zhao-xiuji-career':'卷461·赵修己传·离开李守贞至翰林天文','tongjian-289-950-guo-march':'卷289·乾祐三年·南下与禁军赏赐','jiuwudaishi-107-wang-zhang-finance':'卷107·王章传·财政措施','xinwudaishi-010-han-court-killings':'卷10·汉本纪·乾祐三年十一月','tongjian-289-950-ministers-conspiracy':'卷289·乾祐三年·诛杀计划及追述','tongjian-289-950-assassination-orders':'卷289·乾祐三年·丙子诛杀与密诏','jiuwudaishi-103-november-950':'卷103·隐帝本纪·乾祐三年十一月','jiuwudaishi-124-wang-yin-origin':'卷124·王殷传·籍贯与驻澶州','tongjian-289-950-november-start':'卷289·乾祐三年·十月至十一月','xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年十一月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_09_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=950, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='950年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_289_0950_' + code
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
        edge = 'participation_zztj_289_0950_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_289_0950_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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









ALIASES.update({'帝':'刘承祐','太后':'李氏（刘知远妻）','袁{山义}':'袁嶬','刘重进':'刘重进（契丹通事）','李荣':'李筠（原名李荣）','赵凤':'赵凤（枣强将领）','王殷':'王殷（后汉后周将）','後匡赞':'后匡赞'})
NEW_ALIASES={'袁嶬':['袁义','袁義'],'贾延徽':['賈延徽'],'赵凤（枣强将领）':[]}
NEW_DESCRIPTIONS={
'袁嶬':'袁象先的儿子，950年任左神武统军，受命与刘重进等率禁军在赤冈会师，战败时秘密拜见郭威。通鉴电子本把名写成山义拆字，《新五代史》袁象先传写嶬，《宋史》同次出师写袁义。原字保留，生卒年未载。',
'贾延徽':'后汉作坊使，受刘承祐宠信。史书记他想侵占邻居魏仁浦的住宅，多次向皇帝进谗；950年京师动乱中被人抓获交给魏仁浦，魏仁浦拒绝趁乱报怨。生卒年未载。',
'赵凤（枣强将领）':'枣强人，950年任右千牛卫大将军。京师动乱中在巷口持弓射杀劫掠者，史书记街坊因此得以保全。与后唐宰相赵凤分开建档，生卒年未载。'}
oldbattle='jiuwudaishi-103-liuzi-battle';olddeath='jiuwudaishi-103-han-emperor-death';new='xinwudaishi-011-guo-march';han='xinwudaishi-010-han-court-killings';yuan='xinwudaishi-045-yuan-sons';zhang='jiuwudaishi-108-zhang-yun-death'
add('guo_reaches_fengqiu','郭威军于壬午到封丘，京师人心惊惧',54,'壬午，','人情忷惧。',[('郭威','率军到封丘')],when='950年十一月壬午',place='封丘',note='人情惊惧是来源概括，不当作逐人调查。')
sup('guo_reaches_fengqiu',54,han,'壬午，威犯封丘，','《新五代史》也记郭威壬午到封丘。','犯为该书叙事措辞，原字保留，不追加本句未载屠城。')
add('han_lady_regrets_li_tao','李太后哭泣，后悔没有采纳李涛建议',54,'太后泣曰：','宜其亡也！”',[('太后','哭泣并提及未用李涛建议')],when='950年十一月壬午条下',place='后汉宫廷',note='没有另复建此前李涛建议事件；宜亡为太后忧虑和责备，不是已完成后汉灭亡。')
add('murong_boasts_then_fears','慕容彦超夸口擒郭威，询问兵将后又感到畏惧',54,'慕容彦超恃其骁勇，','未易轻也！”',[('慕容彦超','先向皇帝夸口，后询问北军情况转而畏惧'),('帝','听到慕容的擒敌承诺'),('聂文进','被询问北军兵数和将领姓名')],when='950年十一月壬午条下',place='后汉宫廷',note='蠛蠓为轻视敌军的比喻，未把预期活捉写成战果；本句没有给实际兵数，不补。')
add('yuan_liu_reinforce_chigang','刘承祐再派袁嶬、刘重进等率禁军会师赤冈',54,'帝复遣左神武统军','与侯益等会屯赤冈。',[('帝','增派禁军会师'),('袁{山义}','以左神武统军身份受命领兵'),('刘重进','以前威胜节度使身份受命领兵'),('侯益','成为会师部队的既有统领')],when='950年十一月壬午条下',place='赤冈',note='袁嶬按父亲袁象先及新史同一子对应，宋史同次出师写袁义；原文拆字保留。刘重进由宋传串联契丹通事与乾祐末领军，复用已有主体，不创建同名节度使。')
for key,quote,text,note in [
('songshi-261-liu-chongjin-interpreter','契丹主以其敏慧，留為帳前通事；俄南侵，署重進忠武軍節度。','《宋史》刘重进传记他曾为契丹帐前通事，后获忠武军节度使。','同传由通事转任方镇，连接既有刘重进（契丹通事）主体；不将本句早年授职强定950年。'),
('songshi-261-liu-chongjin-dengzhou','漢初，移鎮鄧州。','《宋史》记同一刘重进在后汉初年移镇邓州。','处于同传连续三段之间，作为履历衔接，不另造具体移镇日。'),
('songshi-261-liu-chongjin-han-general','乾佑末，罷鎮來朝。周祖起兵至封丘，詔重進與左神武統軍袁義率兵拒之，重進望塵退走。','《宋史》记刘重进乾祐末罢镇来朝，与左神武统军袁义受命抵拒郭威。','同名同官同次出师接续前文通事经历，支持复用身份。望尘退走为补书概述，不拆为额外确日战事；乾佑原字保留。')]:
 sup('yuan_liu_reinforce_chigang',54,key,quote,text,note,relation='adds')
 claim('person',people['刘重进（契丹通事）'],'description',text,54,quote,note,source=key)
person('袁象先',54,'袁嶬的父亲',span(54,'{山义}，','象先之子也。'))
relationship('袁象先','袁嶬','父亲',54,'{山义}，象先之子也。','象先指已有袁象先，方向为袁象先是袁嶬父亲；嶬名据同一父子的新史记载规范，不造出生年。')
claim('person',people['袁嶬'],'description','《新五代史》袁象先传列其二子为正辞和嶬。',54,'象先二子，正辭官至刺史，嶬周世宗時為橫海軍節度使。','支持拆字姓名与父子对应；周世宗时期任横海是后述履历，不拿来认定950年即任该职。',source=yuan)
add('murong_tun_qilidian','慕容彦超率大军驻七里店',54,'彦超以大军',None,[('慕容彦超','率大军驻七里店')],when='950年十一月壬午条下',place='七里店',note='未给总兵数，大军不是现代固定编制名。')
sup('murong_tun_qilidian',54,oldbattle,'慕容彥超以大軍駐於七里郊，掘塹以自衛，','《旧五代史》还记慕容彦超在七里郊掘壕自卫。','七里郊七里店保留原称，掘壕是补书细节，不补壕沟长度。',relation='adds')
add('two_armies_meet_liuzi','南北两军于癸未相遇刘子陂',55,'癸未，','刘子陂。',[],when='950年十一月癸未',place='刘子陂',note='遇不等于本句已经交战，至暮不战与次日交战另录。')
add('han_lady_urges_stay','李太后劝刘承祐守城下诏劝郭威，勿轻出慰军',55,'帝欲自出劳军，','帝不从。',[('帝','想出城慰军，拒听守城劝告'),('太后','建议守城、发诏观察郭威意向')],when='950年十一月癸未',place='后汉宫廷',note='建议未被采纳，不造劝谕诏已送达；太后说郭威家故旧和死迫切身是劝说理由。')
add('nie_boasts_escort_safe','李太后叮嘱聂文进谨慎，聂文进夸口可擒百个郭威',55,'时扈从军甚盛，','可擒也！”',[('太后','派使叮嘱聂文进留意安全'),('聂文进','夸口能够擒郭威')],when='950年十一月癸未；《旧五代史》此戒语置甲申',place='随驾军中、宫廷传话',note='百人郭威是夸口比喻，不填百位同名将领；旧本纪戒语时序不同保留。')
sup('nie_boasts_escort_safe',55,oldbattle,'太后以帝至晚在外，遣中使謂聶文進曰：「賊軍在近，大須用意！」','《旧五代史》也记太后派使戒聂文进，但置皇帝甲申再出后的傍晚。','主书置癸未，旧纪置甲申，未推两次完全同词戒语来消除时序差异。',relation='conflicts',field='time_original')
add('emperor_returns_no_battle','两军癸未未交战，刘承祐傍晚还宫，慕容请次日再出',55,'至暮，',None,[('帝','傍晚返回宫中'),('慕容彦超','夸口次日不用交战即可喝退敌军，请皇帝再出')],when='950年十一月癸未傍晚',place='刘子陂至后汉宫廷',note='次日擒破为慕容预期，未当实际战果。')
add('emperor_against_lady_out','刘承祐甲申再次出城，不听李太后劝阻',56,'甲申，','不可。',[('帝','再次出城'),('太后','强力劝止未获采纳')],when='950年十一月甲申',place='后汉京师至军阵',note='未补具体出城时刻。')
add('guo_orders_not_first_strike','郭威以诛近侍为名，告诫军队勿先攻击',56,'既陈，','慎勿先动。”',[('郭威','自称不敌天子，命部众不要先动')],when='950年十一月甲申，两军列阵后',place='刘子陂',note='吾来诛群小为其声明，未当作客观排除所有争权意图的证明。')
add('murong_charge_defeated','慕容彦超骑兵先攻，被郭崇威与李筠击退',56,'久之，','稍稍降于北军。',[('慕容彦超','率轻骑先攻，马倒后退兵'),('郭崇威','率骑兵迎击'),('李荣','以前博州刺史身份率骑兵迎击')],when='950年十一月甲申',place='刘子陂',description='慕容彦超率轻骑先攻，郭崇威与原名李荣的李筠率骑兵抵抗。慕容马倒，险被俘，退兵后麾下死者百余，南军开始陆续归降北军。',note='几获为险被俘，未被擒；百余是来源概数。李荣沿已核改名李筠主体，与李昪父李荣分开。')
sup('murong_charge_defeated',56,oldbattle,'郭威命何福進、王彥超、李筠等大合騎以乘之。','《旧五代史》写郭威命何福进、王彦超、李筠等集合骑兵反击。','主书记郭崇威李荣，旧史增加何福进王彦超并用李筠名；不同名单按书证保存，不补主书未具名者为主书参与。',relation='adds')
add('five_han_commanders_visit_guo','侯益等五名南军统领秘密拜见郭威，被遣回营',56,'侯益、吴虔裕、','威各遣还营，',[('侯益','秘密拜见郭威后被遣回'),('吴虔裕','秘密拜见郭威后被遣回'),('张彦超','秘密拜见郭威后被遣回'),('袁{山义}','秘密拜见郭威后被遣回'),('刘重进','秘密拜见郭威后被遣回'),('郭威','接见五人，遣回各营')],when='950年十一月甲申交战失利后',place='郭威军营',note='潜见不直接写成五人同刻正式交城；还营是郭威遣回，不造处决或拘押。')
add('song_yanwo_failed_escort','郭威让宋延渥护驾并请帝来营，宋遇乱兵未能进入御营',56,'又谓宋延渥曰：','不敢进而还。',[('郭威','让宋延渥率牙兵护帝，并请求皇帝来营'),('宋延渥','领命但御营前混乱，不敢进而返回'),('帝','成为拟护卫与邀请对象')],when='950年十一月甲申，傍晚南军溃散之前',place='郭威军营至御营',note='近亲沿前批石敬瑭女婚姻，不新造宋是刘承祐血亲；请求未达成，未写皇帝已赴郭营。')
add('murong_flees_yanzhou','南军多归北军，慕容彦超率十余骑逃兖州',56,'比暮，','奔还兗州。',[('慕容彦超','率麾下十余骑逃回兖州')],when='950年十一月甲申傍晚',place='刘子陂至兖州方向',note='十余是随行概数，不推整个南军全部投降或均阵亡。')
add('emperor_overnight_qilizhai','刘承祐仅与三位宰相和数十从官宿七里寨',56,'是夕，','馀皆逃溃。',[('帝','在七里寨过夜')],when='950年十一月甲申夜',place='七里寨',note='三相未在本句分别具名，不按猜测添加三位当夜参与角色；七里寨与七里店各保史称。')
add('guo_seeks_emperor_flags','郭威见帝旗后下马脱盔前往，刘承祐已离开',56,'乙酉旦，','帝已去矣。',[('郭威','见帝旗在高坡上，下马脱盔趋见'),('帝','郭威到达前已经离开')],when='950年十一月乙酉清晨',place='高坡帝旗所在处，具体地名未载',note='未实际会见，不造握手、投降或当面谏言。')
add('liu_zhu_shoots_emperor_retinue','刘承祐至玄化门欲还宫，刘铢在门上射其左右',56,'帝策马将还宫，','因射左右。',[('帝','试图还宫'),('刘铢','在门上问兵马所在，并向皇帝左右射箭')],when='950年十一月乙酉',place='玄化门',note='本句射左右，未写直接射中皇帝或有多少人死；不能把射箭与后来皇帝遇弑合成已知同一凶手。')
add('han_emperor_killed_zhaocun','刘承祐转至赵村，进入民宅后被乱兵杀死',56,'帝回辔，','为乱兵所弑。',[('帝','转往赵村，被追及后进入民宅，遭乱兵杀死')],when='950年十一月乙酉',place='赵村民家',note='主書未点名凶手，其他史书点名郭允明的说法独立附引用，不把不同来源压成唯一结论。')
sup('han_emperor_killed_zhaocun',56,olddeath,'郭允明知事不濟，乃剚刃於帝而崩，時年二十。','《旧五代史》说郭允明刺杀刘承祐，记帝年二十。','主书只写乱兵，旧史明确郭允明；古代记龄不据此直接反算出生年，凶手指认并列保留。',relation='conflicts')
sup('han_emperor_killed_zhaocun',56,new,'郭允明反，弒隱帝于趙村。','《新五代史》同样说郭允明在赵村杀刘承祐。','《新五代史》与《旧五代史》同说不自动构成两个独立目击，主书不具名的版本仍保留。',relation='conflicts')
claim('person',people['刘承祐'],'death_year','刘承祐于950年十一月乙酉在赵村被杀。',56,span(56,'乙酉旦，','为乱兵所弑。'),'纪日从本段乙酉承到帝死，凶手异说另附；只追加事实引用，不改旧档案。')
add('su_yan_guo_suicides','苏逢吉、阎晋卿、郭允明自杀',56,'苏逢吉、阎晋卿、','皆自杀。',[('苏逢吉','自杀'),('阎晋卿','自杀'),('郭允明','自杀')],when='950年十一月乙酉，刘承祐死后条下',place='京师附近，三人各自地点未载',note='主书没有给三人具体方式或每人地点，不套皇帝民宅为三人同死处。')
for name in ['苏逢吉','阎晋卿','郭允明']:
 claim('person',people[name],'death_year',name+'于950年十一月乙酉条下自杀。',56,'苏逢吉、阎晋卿、郭允明皆自杀。','按本段时序追加死亡引用，不猜具体方式。')
add('nie_wenjin_caught_killed','聂文进独自逃走，被军士追上杀死',56,'聂文进挺身走，','追趕斩之。',[('聂文进','独自逃走，被军士追斩')],when='950年十一月乙酉条下',place='京师附近逃路，具体地点未载',note='挺身走为独自或脱身逃走，不译挺身战斗；军士未具名不填亲手凶手。')
claim('person',people['聂文进'],'death_year','聂文进于950年十一月乙酉条下逃跑时被追兵杀死。',56,'聂文进挺身走，军士追趕斩之。','原趕字保持，展示简体；不推军士所属确切编制。')
add('li_ye_flees_shanzhou','李业逃往陕州',56,'李业奔陕州，','李业奔陕州，',[('李业','逃往陕州')],when='950年十一月乙酉条下',place='陕州方向',note='本句逃往，不提前录后续死亡或擒获。')
add('hou_kuangzan_flees_yan','后匡赞逃往兖州',56,'後匡赞奔兗州。','後匡赞奔兗州。',[('後匡赞','逃往兖州')],when='950年十一月乙酉条下',place='兖州方向',note='沿同一后匡赞后赞主体，未把与慕容都去兖州推成两人同行。')
add('guo_laments_emperor_death','郭威得知刘承祐被杀，哭称这是自己的罪过',56,'郭威闻帝遇弑，','老夫之罪也！”',[('郭威','得知帝死后哭泣自责')],when='950年十一月乙酉，得知帝死后',place='京师附近，具体闻讯处未载',note='这是所载感情与自责话语，不单据此认定亲手杀害或法律责任。')
add('guo_enters_yingchun','刘铢在玄化门射城外，郭威改从迎春门入京',56,'威至玄化门，','归私第，',[('郭威','到玄化门受阻，自迎春门入城回私宅'),('刘铢','在玄化门向城外密集射箭')],when='950年十一月乙酉条下',place='玄化门、迎春门、郭威私宅',note='雨射为密集射箭，不写实际下雨；未造郭威中箭。')
add('he_fujin_guards_mingde','郭威派何福进率兵守明德门',56,'遣前曹州防御使何福进','将兵守明德门。',[('郭威','派兵守门'),('何福进','以前曹州防御使身份率兵守明德门')],when='950年十一月乙酉入京后',place='明德门',note='未给兵数，不补城门换防过程。')
add('capital_army_plunder_night','诸军在京师大肆劫掠，整夜多处起火',56,'诸军大掠，','通夕烟火四发。',[],when='950年十一月乙酉入京后至夜间',place='后汉京师',note='诸军为来源概称，不把全部普通市民写成参加劫掠者；未给火灾面积或死伤总数。')
sup('capital_army_plunder_night',56,olddeath,'諸軍大掠，煙火四發，翌日至晡方定。','《旧五代史》也记军队劫掠与多处烟火，翌日傍晚才稳定。','翌日至晡为后续平定的补证，不将此时写成已停止。')
sup('capital_army_plunder_night',56,new,'丙戌，威入京師，縱火大掠。','《新五代史》将郭威入京师与纵火大掠记在丙戌。','主书在乙酉帝死后记入城，新史系丙戌；叙事主语与日期不同均保留，不用新句抹去主书诸军大掠。',relation='conflicts',field='time_original')
add('bai_zairong_robbed_killed','军士劫白再荣宅，抢财后杀死白再荣',56,'军士入前义成节度使',None,[('白再荣','家宅遭军士抢劫，随后被杀')],when='950年十一月乙酉夜的京师劫掠中',place='白再荣宅',note='军士自称曾为其部下，未有姓名，不补施害者身份；先抢财后杀人分清，不造确切财产额。')
sup('bai_zairong_robbed_killed',56,olddeath,'前滑州節度使白再筠為亂兵所害，','《旧五代史》也记前滑州节度使被乱兵杀害，姓名写白再筠。','与主书前义成节度使白再荣同职同次遇害对应，姓名再筠再荣异文保留，纸本待核，不另建同名遇害者。')
claim('person',people['白再荣'],'death_year','白再荣于950年十一月京师劫掠中被军士杀死。',56,span(56,'军士入前义成节度使',None),'乙酉夜沿本段时序，旧史写白再筠另保异字；不改旧档案。')
add('zhang_yun_falls_freezes','张允藏身佛殿顶部，坠落遭剥衣后冻死',57,'是夕，',None,[('张允','藏在佛殿藻井上，坠落后衣服被军士抢走，冻死')],when='950年十一月乙酉夜，承前段京师劫掠之夕',place='佛殿藻井处，主书未具寺名',note='板坏坠落、剥衣与冻死按顺序保留，不改成战死或自杀；家资万计不是确切货币总额。')
claim('person',people['张允'],'description','《资治通鉴》记张允家财多而吝啬，连钥匙也常自己保管。',57,span(57,'吏部侍郎张允，','行如环佩。'),'吝啬为史书描述，不推妻子对其死亡负责；万计未列具体计价单位。')
sup('zhang_yun_falls_freezes',57,zhang,'及北軍入京師，允匿於佛殿藻井之上，墜屋而卒，時年六十五。','《旧五代史》张允传也记藏佛殿藻井后坠屋去世，记六十五岁。','旧传未提剥衣冻死，少细节不等于否定；古代岁数不反算出生年。',relation='adds')
claim('person',people['张允'],'death_year','张允于950年京师劫掠之夜坠落后被剥衣，冻死。',57,Q[57]['text'],'主书死因明确为冻卒，旧传概称坠屋而卒；身份沿既有后晋常侍及旧传至吏部侍郎履历，不新建同名。')
add('jia_slanders_neighbor_wei','贾延徽想侵占魏仁浦住宅，多次向皇帝进谗',58,'初，','几至不测。',[('贾延徽','想扩大住宅，占邻居屋，屡次进谗'),('魏仁浦','因邻宅争夺遭进谗')],year=None,when='950年十一月京师动乱以前的追述，具体年月未载',place='后汉京师相邻住宅',note='初为背景，不强系乙酉当天；欲并宅未说已经吞并，几至不测未说魏已被杀。')
add('wei_refuses_revenge_jia','有人把贾延徽交给魏仁浦，魏拒绝趁乱报仇',58,'至是，','吾所不为也！”',[('贾延徽','被未具名者抓获，交给魏仁浦'),('魏仁浦','拒绝趁乱报怨')],when='950年十一月乙酉至丙戌的京师动乱中，具体日未单列',place='京师，具体交付地点未载',note='不造未具名捕人者，拒报怨没有明确后续释放手续，未写郭威下令释放。')
add('guo_respects_wei_more','郭威得知魏仁浦拒报怨，对他更为优厚',58,'郭威闻之，',None,[('郭威','得知拒报怨后更优待魏仁浦'),('魏仁浦','获得郭威进一步礼遇')],when='950年十一月京师动乱中，具体日未单列',place='京师',note='益厚为待遇关系的概述，不造具体升官或赏钱事件。')
add('zhao_feng_protects_lane','枣强将领赵凤守巷口射杀劫掠者，保护街坊',59,'右千牛卫大将军',None,[('赵凤','在巷口持弓射杀劫掠者')],when='950年十一月乙酉至丙戌的京师动乱中，具体日未单列',place='京师一处街巷，名称未载',note='赵凤右千牛卫将军、枣强籍与后唐宰相同名分开；其话语认为非郭威本意，不据此客观免除郭威责任，邻里保全为书中结果概述。')
add('liu_li_hongjian_captured','刘铢、李洪建于丙戌被捕入狱',60,'丙戌，','囚之。',[('刘铢','被捕入狱'),('李洪建','被捕入狱')],when='950年十一月丙戌',place='京师，具体监禁处未载',note='未点名捕获者，不猜郭威亲手抓捕；本句尚未处决。')
add('liu_zhu_wife_reply','刘铢问妻子将来是否为婢，妻子责其行为',60,'铢谓其妻曰：',None,[('刘铢','担心自己死后妻子沦为婢女，向妻询问')],when='950年十一月丙戌被囚之后',place='监禁相关场所，具体地址未载',note='妻子未具名不造姓氏；妻答是道德责备，不是她已成为奴婢或刘铢已死。')
add('wang_guo_warn_plunder','王殷与郭崇威劝郭威制止劫掠',61,'王殷、郭崇威','今夕止有空城耳。”',[('王殷','警告劫掠将使京师被掏空'),('郭崇威','共同劝止劫掠'),('郭威','听到制止劫掠的劝告')],when='950年十一月丙戌条下',place='京师',note='空城为警告性措辞，不是当时人口物资皆已为零。')
add('guo_stops_plunder','郭威命诸将分区止掠，不从者斩，至傍晚稳定',61,'威乃命诸将',None,[('郭威','命分部制止劫掠，对违令者用斩刑')],when='950年十一月丙戌，至晡时局势稳定',place='京师',note='分部指分区或分派部众，不补部署名单；斩为命令惩罚，未给实际被斩人数，乃定不推此后永无抢掠。')
reviews={54:'壬午到封丘与旧新史对应，太后悔语不是已亡结果，慕容前后态度和增军驻营分开。袁拆字据新传父子对应为嶬，宋同出师写袁义；刘重进由宋同传连接契丹通事与汉军统领，复用既有key。',55:'癸未两军相遇未战、太后劝止、聂夸口、帝暮归与慕容请再出分录。旧史太后戒语置甲申与主癸未差异保留，不凭同词造两次完全同样事件。',56:'甲申出军交战败退与乙酉帝死入京分时序，几获非擒。李荣沿李筠原名，宋未进御营不写护驾完成。帝乱兵弑与新旧郭允明弑异说并列，死者、逃者分别记；诸军劫掠与禁掠后果不虚构人数，白再荣旧作再筠保异字。',57:'是夕承乙酉夜，张允坠落剥衣冻卒与旧传坠屋概记并列，旧六十五不反算出生年；吝啬背景为来源描述。',58:'初进谗夺宅为时间未知追述，现场擒交、魏拒报怨与郭益厚分开，不补贾已死或正式获释。',59:'枣强右千牛卫赵凤与后唐宰相同名分开，非郭本意为其话语，保护邻里结果限书载。',60:'丙戌捕囚未处决，刘铢妻未具名不造姓氏；妻婢担忧不是已成身份。',61:'劝止、禁掠命令和至晡稳定分清，不计无据斩人数量或把空城比喻当真实人口归零。'}
assert not (P/'publication.json').exists()
for n in range(54,62):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(54,62)],next_paragraph=Q[62]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原59—66行连续八段；发布后首61/83正文已录，余22段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(54,62)],source_issues_review='袁拆字和嶬义鳷各底本文字保留；规范名以新史同父子嶬对应，旧本纪袁鳷不静默改原文。宋同传连接刘重进主体。郭允明是否直接弑帝、太后戒语日、入京日、白再荣再筠姓名及张允死因细节有差异，分来源记录。纸本及转录异文待核。',plain_language_review='首次逐条检查现代白话、人物身份、方向、时间和证据。夸口、建议、命令、自责与实际结果分开；未具名人物不造姓名。原文保持异字与拆字，展示采用可读姓名。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
