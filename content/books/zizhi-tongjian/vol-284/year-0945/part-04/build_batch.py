# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 284, year 945 paragraphs 25–35."""
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
COMMIT='364ae8263b649ce7f7349c1b24424be505327bcc'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['xinwudaishi-009-945','xinwudaishi-068-li-ren-da']:
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
main_sources = ['tongjian-284-945-may-july','tongjian-284-945-july-ending']
B = {'format_version': 1, 'batch_key': 'zztj-v284-y0945-p025-p035',
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
for n in range(25, 36):
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
        citation = f'卷284·后晋开运二年（945年五月至七月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_284_0945_04_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'石重贵','契丹主':'耶律德光','杜威':'杜重威','唐主':'李璟','闽主':'王延政','岩明':'卓岩明','希范':'马希范','希杲':'马希杲','冯延己':'冯延巳','延鲁':'冯延鲁','述律太后':'述律平','宋国长公主':'乐平长公主（杜重威妻）','李彦韬':'李彦韬（后晋宣徽使）','张晖':'张晖（后晋求和使者）'})
NEW_ALIASES={'时厚卿':['時厚卿'],'张晖（后晋求和使者）':['張暉（後晉求和使者）']}
NEW_DESCRIPTIONS={'时厚卿':'南唐将领。945年《资治通鉴》记他在汀州战事中被许文稹俘获。生卒年与其他履历本段未载。','张晖（后晋求和使者）':'后晋开封军将，945年石重贵授予供奉官身份，派他向契丹奉表称臣求和。《新五代史》景延广传也记载此次出使。未证明与937年博州守将张晖或后来的北汉同名将领为同一人，暂以身份限定主体。生卒年未载。'}
m='945年五月条下，具体日未载';j='945年六月条下，具体日未载';jul='945年七月条下，具体日未载'
om='jiuwudaishi-084-945-may';oj='jiuwudaishi-084-945-june';oa='jiuwudaishi-084-945-august';dw='jiuwudaishi-109-du-wife';dl='jiuwudaishi-109-du-leaves';jp='xinwudaishi-029-jing-peace';ny='xinwudaishi-009-945';mi='xinwudaishi-068-li-ren-da'
# 25: national amnesty, independent from April's capital-only pardon.
add('may_amnesty','石重贵在五月初一宣布大赦',25,'五月，',None,[('帝','宣布大赦')],when='945年五月丙申朔',place='大梁',note='五月大赦与此前四月还京赦京城囚犯是两次处置。')
sup('may_amnesty',25,om,'開運二年夏五月丙申朔，帝御崇元殿受朝，大赦天下。','《旧五代史》明确石重贵在崇元殿受朝后大赦天下。','同日同次大赦，补殿名与受朝，不并入此前四月赦囚。',relation='adds')
sup('may_amnesty',25,ny,'五月丙申朔，大赦。','《新五代史》同记五月丙申朔大赦。','同日同事，保留独立书证。')
# 26: longstanding actions and assessments are not newly dated May occurrences.
add('du_extorts_defense_funds','杜重威长期以备边为名征敛钱帛，收入私库',26,'顺国节度使杜威，','私藏。',[('杜威','以边防为名向官吏和百姓敛取钱帛，收入私库')],when='杜重威长期镇守恒州期间，具体起止年未载',year=None,place='恒州及所辖地区',note='久镇与每以描述长期作为，不把全部征敛强定五月单日；贪残是史书记载的评价。')
sup('du_extorts_defense_funds',26,dw,'至鎮，復重斂於民，稅外加賦，境內苦之','《旧五代史》记杜重威到镇后在税外加征，境内百姓深受其苦。','传记先叙安重荣败后任镇，说明这是长期征敛，不另造945年新一次征税。')
add('du_seizes_household_wealth','杜重威强取富户珍货、女子与骏马，有时诬罪杀人并没收家产',26,'富室有','其家。',[('杜威','强取富户财物、女子和马匹，有时诬罪杀人并没收其家产')],when='杜重威镇守恒州期间的反复行为，具体年月未载',year=None,place='恒州及所辖地区',note='或诬为部分事例，未具名受害者不建立占位人物；名姝指被强取女子，不改写成自愿婚配。')
add('du_closes_city_avoids_rescue','杜重威见契丹骑兵入境便闭城，未拦救被掳百姓',26,'又畏懦过甚，','无意邀取。',[('杜威','在契丹骑兵入境时闭城，未出兵拦救被掳百姓')],when='契丹连年攻晋、杜重威镇恒州期间，具体年月未载',year=None,place='恒州',note='电子本目字前有私用字，原文保留；行为按前后文写出，不凭乱码恢复字形。人数千百为史书概述，不推单次准确统计。')
sup('du_closes_city_avoids_rescue',26,dl,'每敵騎數十驅漢人千萬過城下，如入無人之境，重威但登陴註目，略無邀取之意。','《旧五代史》也记杜重威在城上旁观，未出兵拦救；该书被掳人数写千萬。','《资治通鉴》千百与《旧五代史》千萬不同，保留底本文字，不据此计算精确人口损失。',relation='conflicts')
add('hengzhou_settlements_destroyed','契丹军破坏恒州所辖城邑，杜重威未出兵救援',26,'由是虏','殆尽。',[('杜威','面对所辖城邑遭屠掠，未派兵救援')],when='杜重威镇恒州、契丹连年攻晋期间，具体起止年月未载',year=None,place='恒州所辖城邑村落',note='千里与村落殆尽为史书对毁坏的概述，不换算地理半径或精确村数。')
sup('hengzhou_settlements_destroyed',26,dl,'部內城邑相繼破陷，一境生靈受屠戮，重威任居方面，未嘗以一土一騎救之。','《旧五代史》也记恒州辖境城邑相继失陷，杜重威未派兵救援。','原文一土一骑疑有字形问题，逐字保留；不靠自动转换校订纸本。')
add('du_repeatedly_requests_court_visit','杜重威多次请求入朝，石重贵不批准',26,'威见所部','帝不许；',[('杜威','因辖境残破、民怨和惧敌，多次上表请求入朝'),('帝','拒绝杜重威的入朝请求')],when=m,place='恒州与后晋朝廷',note='请求动机来自史书叙述，不推成已准备投敌。')
add('du_abandons_hengzhou_for_court','杜重威未等朝廷答复，擅自离开恒州入朝',26,'威不俟报，','惊骇。',[('杜威','未等答复便离镇入朝，引起朝廷震惊')],when=m,place='恒州至大梁')
sup('du_abandons_hengzhou_for_court',26,dl,'重威遂無留意，連上表乞歸朝，不俟報即時上路。','《旧五代史》也记杜重威多次请求归朝，未等答复就上路。','擅离与最终到达分阶段，传记不列出发日。')
add('sang_asks_remove_du','桑维翰建议石重贵撤去杜重威职权，防止后患',26,'桑维翰言于帝曰：','帝不悦。',[('桑维翰','以擅离边镇、无意守御为由建议撤去杜重威职权'),('帝','听后不悦')],when=m,place='后晋朝廷',note='废之是建议撤去职权，不写成已处死或已获准免职。')
add('sang_proposes_small_nearby_post','桑维翰退而建议让杜重威改任近京小镇',26,'维翰曰：“陛下','雄籓。”',[('桑维翰','建议改授杜重威近京小镇，停止委任大藩镇')],when=m,place='后晋朝廷',note='备选建议并未在本句执行，雄藩是大藩镇，不制造具体拟任军镇。')
add('shi_defends_du_due_kinship','石重贵以亲属关系为由，认定杜重威没有异心',26,'帝曰：“威，','为疑！”',[('帝','称杜重威是亲属、不会有异志，并以公主想见面解释入朝'),('杜威','被石重贵以亲属身份维护'),('宋国长公主','被石重贵说成希望与他见面')],when=m,place='后晋朝廷',note='没有异志是石重贵的判断，公主想相见为石重贵所言，不把这些判断当作客观证明。宋国公主按杜重威妻子、石敬瑭妹身份对应已有乐平长公主。')
claim('person',people['乐平长公主（杜重威妻）'],'description','《旧五代史》记杜重威之妻是石敬瑭的妹妹，累封宋国大长公主。',26,'其妻即晉高祖妹也，累封宋國大長公主。','公主按丈夫与兄长身份匹配既有乐平长公主主体；后来的封号作为出处补充，不新造一位宋国公主。',source=dw)
add('sang_refrains_and_requests_resignation','桑维翰此后不再谈国事，以脚病为由请求辞职',26,'维翰自是','辞位。',[('桑维翰','不再谈论国事，借脚病请求辞职')],when='945年五月谏杜重威之后，具体日未载',place='后晋朝廷',note='辞位是请求，不能把后文正式罢相时间提前到本句。')
add('du_arrives_daliang_may','杜重威于丙辰到达大梁',26,'丙辰，',None,[('杜威','从恒州到大梁入朝')],when='945年五月丙辰',place='大梁')
sup('du_arrives_daliang_may',26,om,'丙辰，杜威來朝。','《旧五代史》同记丙辰杜重威入朝。','同日同事，不能用此日倒推擅离恒州的具体日期。')
# 27: killing, staged surprise, competing diplomatic ties and later appointment.
add('li_invites_zhuo_review','李仁达举行大阅，请卓岩明观看军队',27,'丁巳，','临视。',[('李仁达','大阅军队并邀请卓岩明观看'),('岩明','被请到场观看军队')],when='945年五月丁巳',place='福州')
add('li_arranges_zhuo_assassination','李仁达暗中授意军士登阶，刺杀卓岩明',27,'仁达阴教','岩明。',[('李仁达','暗中指使军士刺杀卓岩明'),('岩明','在阅兵时被军士刺杀')],when='945年五月丁巳',place='福州',note='军士未具名，不虚构杀手人物；李仁达是暗中指使者，不写成亲手刺杀。')
sup('li_arranges_zhuo_assassination',27,mi,'已而又殺儼明，乃自立，送款于李景，','《新五代史》也记李仁达杀卓俨明后自立，向李璟表示归附。','卓儼明对应同寺同场所立僧人；该传末记保大四年，与《资治通鉴》编年不同，不将传末年份套到所有前述行动。')
claim('person',people['卓岩明'],'death_year','卓岩明于945年五月丁巳被刺杀。',27,'仁达阴教军士突前登阶，刺杀岩明。','依据本年连续记事与明确纪日补死亡事实，未修改已有发布人物基线。')
add('li_feigns_surprise_and_seated','李仁达假装吃惊逃走，军士将他拉到卓岩明座位上',27,'仁达阳惊，','之坐。',[('李仁达','假装受惊逃走，随后被军士拉到卓岩明座位上')],when='945年五月丁巳，卓岩明遇害后',place='福州',note='执仁达在这里是拥立动作，不解为逮捕后治罪；阳惊按原文明确伪装惊慌。')
add('li_claims_weiwu_deputy','李仁达自称威武留后，改用南唐保大年号',27,'仁达乃','年号，',[('李仁达','自称威武军留后，采用南唐保大年号')],when='945年五月丁巳政变后',place='福州',note='自称留后与后来南唐正式授节度使分开；使用保大不是李仁达自创年号。')
add('li_submits_to_southern_tang','李仁达上表向南唐称臣',27,'奉表称籓于唐，','奉表称籓于唐，',[('李仁达','上表向南唐称臣')],when='945年五月福州政变后',place='福州至南唐')
add('li_sends_tribute_to_jin','李仁达向南唐称臣的同时，也派使者向后晋进贡',27,'亦遣使','于晋；',[('李仁达','派使者向后晋进贡')],when='945年五月福州政变后',place='福州至后晋',note='两处外交行为分别保留，不能因奉唐年号就删去对晋进贡。')
add('li_kills_zhuo_father','李仁达杀死卓岩明的父亲',27,'并杀','之父。',[('李仁达','杀死卓岩明的父亲')],when='945年五月福州政变后',place='福州',note='卓岩明之父未具名，不为他造名字或占位人物；此前尊太上皇身份保留在原对应事件。')
add('tang_appoints_li_weiwu','李璟任李仁达为威武节度使，加同平章事',27,'唐以仁达','同平章事，',[('唐主','任命李仁达为威武节度使、同平章事'),('李仁达','得到南唐的节度使任命与加号')],when='945年五月福州政变后，任命具体日未载',place='福州、南唐朝廷')
sup('tang_appoints_li_weiwu',27,mi,'景以仁達為威武軍節度使，更其名曰弘義。','《新五代史》也记李璟授李仁达威武军节度使，并改名弘义。','同次任命；改名另列事件。传末保大四年纪年待核，不覆盖主书945编年。')
add('tang_renames_li_hongyi','李璟赐李仁达名弘义，并编入南唐宗籍',27,'赐名','属籍。',[('唐主','赐李仁达名弘义，并列入宗籍'),('李仁达','获赐名弘义、列入宗籍')],when='945年五月福州政变后，具体日未载',place='南唐朝廷、福州',note='列入属籍是政治宗籍安排，不建立没有明示的生父或养父血缘；李弘义存在其他同名人物，不自动合并。')
claim('person',people['李仁达'],'aliases','李仁达获南唐赐名弘义，本段随后称他弘义。',27,'赐名弘义，编之属籍。弘义又遣使修好于吴越。','这是同段明示改名，后续弘义须按福州将领身份对应李仁达；不与其他李弘义同名者自动合并。')
add('li_seeks_wuyue_friendship','李仁达获赐名弘义后，派使者与吴越修好',27,'弘义又',None,[('李仁达','派使者与吴越建立友好关系')],when='945年五月福州政变后',place='福州至吴越')
# 28: contributions are reported, not assumed transferred.
add('du_offers_four_thousand_troops','杜重威献步骑四千人及甲兵器械',28,'己未，','并铠仗，',[('杜威','献出部曲步骑共四千人及铠甲兵器')],when='945年五月己未',place='后晋朝廷',note='献兵人数为史书记载，后续隶属和请求自留另录。')
add('du_reports_grain_fodder_offering','杜重威报献粟十万斛、草二十万束，称物资还在本镇',28,'庚申，','本道。',[('杜威','奏报献粟十万斛、草二十万束，并称都在本镇')],when='945年五月庚申',place='恒州与后晋朝廷',note='云皆在本道是杜重威奏报，不写成粮草已运抵大梁、交入国库或经核实入账。')
add('shi_assigns_offered_troops','石重贵将杜重威所献骑兵编入扈圣军，步兵编入护国军',28,'帝以','隶护国，',[('帝','命所献骑兵归扈圣军，步兵归护国军'),('杜威','所献步骑由皇帝安排隶属')],when=m,place='后晋朝廷',note='军号按底本扈圣、护国原字保留，不据同音惯用名擅改。')
add('du_asks_keep_troops_state_pay','杜重威请求把献兵留作牙队，军饷仍由朝廷支付',28,'威复请','仰县官。',[('杜威','请求献兵仍作自己的牙队，但让朝廷支付军饷')],when=m,place='后晋朝廷',note='县官在此指朝廷，不能译成县级官员；请以为牙队是请求，不把全军正式移交后的实际驻地补成定案。')
add('du_seeks_tianxiong_via_princess','杜重威让公主向石重贵请求天雄军，石重贵答应',28,'威又令',None,[('杜威','通过公主请求改任天雄军'),('宋国长公主','替杜重威向石重贵求天雄节钺'),('帝','答应杜重威改任天雄军的请求')],when=m,place='后晋朝廷',note='五月答应请求与六月癸酉正式任命分开。')
# 29 and 30.
add('tang_beats_quanzhou_relief','南唐军围建州，多次击败泉州兵',29,'唐兵','泉州兵。',[],when=m,place='建州及围城战区',note='两军人数与具体指挥者本句未明，不凭同战区其他记载补入。')
add('xu_defeats_tang_at_tingzhou','许文稹在汀州击败南唐军',29,'许文稹','于汀州，',[('许文稹','在汀州击败南唐军')],when=m,place='汀州')
add('xu_captures_shi_houqing','许文稹在汀州战事中俘获南唐将领时厚卿',29,'许文稹',None,[('许文稹','俘获南唐将领时厚卿'),('时厚卿','在汀州战事中被许文稹俘获')],when=m,place='汀州',note='被俘不等于被杀；不补时厚卿后续下落。')
add('du_appointed_tianxiong','石重贵正式任杜重威为天雄节度使',30,'六月，',None,[('帝','任杜重威为天雄节度使'),('杜威','由恒州调任天雄节度使')],when='945年六月癸酉',place='恒州至天雄军')
sup('du_appointed_tianxiong',30,oj,'癸酉，以恒州節度使杜威為天雄軍節度使，充鄴都留守；以鄴都留守馬全節為恒州節度使；','《旧五代史》同记癸酉杜重威任天雄节度使，兼任邺都留守；马全节改任恒州节度使。','同日官命，补杜兼任留守与继任者，不与四月马全节天雄任命混为一次。',relation='adds')
extra('ma_replaces_du_hengzhou','后晋任马全节为恒州节度使，接替杜重威',30,oj,'以鄴都留守馬全節為恒州節度使；',[('马全节','从邺都调任恒州节度使，接替杜重威')],when='945年六月癸酉',place='恒州',note='马全节此前天雄军官职保留在四月事件；这里是六月新任命，不提前去世。')
# 31: reported costs, speeches and aborted negotiations.
add('jin_border_suffers_repeated_war','契丹连年攻晋，后晋边境百姓遭受严重损害',31,'契丹连岁','边民涂地；',[],when='契丹连年攻晋的背景，具体起止年月未载',year=None,place='后晋边境',note='中国在本段指当时后晋辖境，不把它改成现代行政疆界。')
add('khitan_people_tire_of_war','契丹人畜也损失众多，民众厌倦战争',31,'契丹人畜','厌苦之。',[],when='契丹连年攻晋的背景，具体起止年月未载',year=None,place='契丹辖境',note='不补具体伤亡人数或民意调查比例。')
add('shulu_questions_rule_han','述律平质问耶律德光为何想统治汉地',31,'述律太后','汉主？”',[('述律太后','以汉人能否统治契丹为问，质疑儿子统治汉地的愿望'),('契丹主','答汉人不能做契丹君主，受到母亲追问')],when=j,place='契丹',note='为史书记载的母子对话，不等同实际已统治大梁。')
add('yelu_invokes_shi_ingratitude','耶律德光称石氏负恩，不能容忍',31,'曰：“石氏','不可容。”',[('契丹主','以石氏负恩解释继续对后晋用兵')],when=j,place='契丹',note='负恩是耶律德光的政治判断与开战理由，不作为客观伦理事实。')
add('shulu_warns_occupation_difficulty','述律平警告耶律德光，即使取得汉地也难以久居',31,'太后曰：“汝今','何所及！”',[('述律太后','警告取得汉地也难以久居，失败后后悔无及'),('契丹主','受到母亲对南征风险的警告')],when=j,place='契丹',note='虽得、万一是对未来的假设和风险警告，不写成契丹军此时已经取得汉地。')
add('shulu_offers_conditional_peace','述律平向臣下表示，汉人若改变意向，她愿意议和',31,'又谓其群下','与和！”',[('述律太后','向臣下表达有条件接受汉人求和的意愿')],when=j,place='契丹',note='但闻汉和蕃未闻蕃和汉是述律平所说的外交立场，不据此断言历代外交史。')
add('sang_urges_renewed_peace','桑维翰多次劝石重贵再向契丹求和，缓解国难',31,'桑维翰屡','国患，',[('桑维翰','多次劝石重贵再次向契丹求和'),('帝','受到桑维翰求和建议')],when=j,place='后晋朝廷')
add('shi_sends_zhang_hui_peace','石重贵授张晖供奉官身份，派他奉表向契丹称臣谢过',31,'帝假','谢过。',[('帝','授开封军将张晖供奉官身份，派他奉表称臣求和'),('张晖','以供奉官身份出使契丹，奉上称臣谢过的表文')],when=j,place='后晋至契丹',note='假供奉官为临时授予身份，供奉官不是僧人；张晖不自动与博州或北汉同名人合并。')
sup('shi_sends_zhang_hui_peace',31,jp,'後帝亦追悔，遣供奉官張暉奉表稱臣以求和，','《新五代史》景延广传也记石重贵派供奉官张晖奉表称臣求和。','同场同身份使者匹配，传记未列月日；不取后文中渡降敌提前到945。')
add('yelu_demands_ministers_and_two_commands','耶律德光要求景延广、桑维翰来见，并割镇定两道，才愿议和',31,'契丹主曰：','可和。”',[('契丹主','以景延广、桑维翰来见和割镇定两道作为议和条件'),('景延广','被契丹点名要求前往'),('桑维翰','被契丹点名要求前往')],when=j,place='契丹、镇州、定州',note='要求并未获准，不写成两人已赴契丹或后晋已割地。')
sup('yelu_demands_ministers_and_two_commands',31,jp,'德光報曰：「使桑維翰、景延廣來，而割鎮、定與我，乃可和。」','《新五代史》同记耶律德光要求桑维翰、景延广来见并割镇定。','议和条件与实际履行分清。')
add('jin_abandons_peace_request','后晋朝廷认为契丹没有诚意，停止此次求和',31,'朝廷以','乃止。',[],when=j,place='后晋朝廷',note='无和意是晋廷对回复的判断，不当作双方共同确认的外交事实。')
sup('jin_abandons_peace_request',31,jp,'晉知其不可，乃止。','《新五代史》也记晋廷认为条件不能接受，停止求和。','同次失败议和，不另造一场双方签约或正式开战。')
add('yelu_later_regrets_no_second_envoy','耶律德光后来进入大梁，向李崧等称再有晋使就可以避免交战',31,'及契丹主',None,[('契丹主','进入大梁后，向李崧等表达对晋使未再来的看法'),('李崧','在大梁听耶律德光谈先前议和')],when='契丹主进入大梁后；本段追叙后来谈话，具体日期未载',year=None,place='大梁',note='及字后为后事追叙，不能标为945年六月；南北不战是耶律德光事后假设，不能据此认定再遣使必能避免战争。')
# 32–35: accusations, provisioning pressures, appeal and poisoning.
add('fuzhou_relief_accused','有人告发福州援兵谋反',32,'秋，七月，','谋叛，',[],when=jul,place='建州',note='告谋叛是指控，原文不证明援军已实际反叛；告发者未具名不造人物。')
add('wang_disarms_and_sends_relief','王延政收缴福州援兵铠甲武器，将他们遣返',32,'闽主延政','遣还，',[('闽主','收缴援军甲兵后令其返回')],when=jul,place='建州至福州',note='援兵在建州被围背景下受处置；遣还是行程安排，不补他们已经到福州。')
add('wang_ambushes_fuzhou_relief','王延政在险隘伏兵杀福州援军，史书称死者八千余人',32,'伏兵于隘，','八千馀人，',[('闽主','伏兵于险隘杀被遣返的福州援军')],when=jul,place='福州援军返程险隘，具体隘口未载',note='八千余是史书记载的人数，未当作精确统计；不臆定险隘现代坐标。')
add('wang_makes_human_flesh_food','王延政将被杀援军的肉制成肉干，带回作为食物',32,'脯其肉',None,[('闽主','将被杀援军的肉制成肉干，带回为食')],when=jul,place='建州围城战区',note='脯是制为肉干的动作，不扩写屠杀场景，也不添确切分食者。')
add('bian_takes_tanzhou','边镐攻取镡州',33,'唐边镐','镡州，',[('边镐','率南唐军攻取镡州')],when=jul,place='镡州',note='镡州沿用底本地名，不与楚潭州因音近混同。')
add('wei_feng_support_fujian_campaign','魏岑、冯延巳、冯延鲁因出兵有功，积极支持攻闽',33,'查文徽之党','赞成之。',[('魏岑','积极支持南唐攻闽'),('冯延己','积极支持南唐攻闽'),('延鲁','积极支持南唐攻闽')],when=jul,place='南唐',note='之党是史书对与查文徽同一政治集团的描述，不据此建立亲属或每一对人物的同盟关系。')
add('tang_war_supply_depletes_treasury','南唐攻闽征调军需，使府库耗竭，洪饶抚信百姓受苦',33,'征求供亿，',None,[],when=jul,place='洪州、饶州、抚州、信州',note='军需负担与民生后果来自原文，不补具体税率或耗费金额。')
add('wang_submits_wuyue_for_rescue','王延政向吴越称臣，请求作为附庸获得救援',34,'延政遣使',None,[('闽主','派使上表向吴越称臣，申请附庸地位求救')],when=jul,place='建州至吴越',note='求救与实际援军到达不是同一事实，本句不证明吴越已出兵。')
add('ma_xifan_spies_on_xigao','马希范疑忌马希杲得人心，派人监视',35,'楚王希范','伺之。',[('希范','因疑忌马希杲得人心而派人监视'),('希杲','受到马希范监视')],when=jul,place='朗州',note='得人心是史书所述怀疑的背景，不虚构马希杲谋反或具体支持人数。')
add('ma_xigao_requests_return','马希杲因害怕而称病求归，马希范不准',35,'希杲惧，','不许；',[('希杲','因害怕称病求归'),('希范','拒绝马希杲求归')],when=jul,place='朗州',note='称疾不等同经证实患病，求归目的地本句未明，不补确切家乡。')
add('ma_xifan_poison_xigao','马希范派医生探视马希杲，借机将他毒死',35,'遣医',None,[('希范','派医生探病并借机毒杀马希杲'),('希杲','被借探病之机毒死')],when=jul,place='朗州',note='医生未具名，不虚构主体；不改写成马希范亲手下毒。')
sup('ma_xifan_poison_xigao',35,oa,'戊子，湖南奏，靜江軍節度使馬希杲卒。','《旧五代史》记八月戊子湖南奏报马希杲去世。','《资治通鉴》七月叙毒杀，《旧五代史》八月为奏报日，不能据奏报日改成八月才死亡；本纪不说明死因。',relation='adds')
claim('person',people['马希杲'],'death_year','马希杲于945年被毒杀；《旧五代史》八月收到其去世奏报。',35,'遣医往视疾，因毒杀之。','死亡与奏报日期分清，不倒推精确公历日期；人物原档案保持不改。')
reviews={25:'五月大赦与四月京城赦囚分开，主新旧纪日一致。',26:'长期征敛、掳女、闭城未救与五月入朝请求分开，不把久镇强定本年；私用字保留于原文，解释不校字；主千百旧千萬并列。公主按杜妻与高祖妹身份对应乐平公主，旧传补宋国封号。辞位是请求非本月已罢相。',27:'阅兵诱杀、假惊走与被推上座、留后自称、唐晋两边外交、杀未名父、南唐官命、赐名宗籍、修好吴越分开；李仁达非亲手刺僧，编属籍不推血缘。卓岩儼异名承前；新史传末保大四年不套全段。',28:'献步骑甲仗、报献尚在本道的粮草、皇帝隶军、请自留牙队由朝廷支付、借妻求节钺分阶段，未将报告写成到账；扈圣护国按底本，不擅校军名。',29:'围建破泉州、许破唐军和俘时厚卿分开；俘不等于死，不补具名围城将。',30:'六月癸酉正式任命区别五月请准，旧纪补邺都留守与马接恒州，未提前马全节卒。',31:'两国战争损耗为长期背景，母子假设、态度与臣下议和分别注明说话人；景桑赴契丹与镇定割地均为要求非执行，停止求和与后来入梁谈话分开；张晖限后晋使者身份，未自动合博州或北汉同名人。',32:'谋叛是有人指控不作已叛确证；缴械、遣还、伏杀八千余与制肉干分开，未知隘口不补坐标、未名者不造人。',33:'镡不混潭；三人赞攻与军需府库民生后果分开，集团称呼不建无证盟友关系。',34:'称臣、请附庸与求援是王延政主动请求，不推吴越已准或已出兵。',35:'疑得人心、派监视、称疾求归遭拒、遣医毒杀分开；七月叙死与八月戊子奏报不同，保留具体日期角色。'}
assert not (P/'publication.json').exists()
for n in range(25,36):
 assert ledger[n-1]['status']=='pending'
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=284,year=945,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(25,36)],next_paragraph='zztj-v285-y0945-p001',next_volume=285,next_year=945,supplements=supplements,excluded_non_body=[],coverage='卷284原76—86行连续第25—35段，五月至七月末及追述，卷284正文结束。945年仍须接卷285前23段，全年未完成。',source_contexts=[dict(source_key=key,note=note) for key,note in [(main_sources[0],'对应25—33段，长期与后来谈话均按原文区分时间。'),(main_sources[1],'对应34—35段；卷末空行并未算正文。'),(mi,'只补杀卓与李受官改名，建州破与王迁留到下一卷主线；传末保大四年不裁全段年份。'),(dl,'只补恒州不救与擅离；其他未来降敌、后汉反叛等未提前录入。'),(dw,'只补长期税外征敛及妻为晋高祖妹、宋国公主身份，未重录早年同事。'),(oj,'只补同日杜任邺留守与马继任恒州，后续马卒暂留。'),(oa,'只补马希杲死亡奏报日，其他八月事留下一卷。'),(jp,'只补张晖使者与求和条件、停止，景延广后来中渡事未提前录入。')]],source_issues_review='私用字、人数千百千萬、新史保大四年与主书编年、军号扈圣护国和死亡奏报日区别均保留具体校核说明；未校纸本。卓死亡、李改名、公主异封号与马死亡以新事实引用补充，不改旧发布档案。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(25,36)],plain_language_review='首次逐条阅读标题、描述、参与、时间与事实说明，简体白话、明确主语。计划、请求、指控、奏报、长期背景与后来追叙均与实际行动分开。引用保留底本原字，无二次全面重写旧批次。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
