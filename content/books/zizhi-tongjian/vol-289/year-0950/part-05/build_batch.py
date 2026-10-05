# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 29–35."""
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
COMMIT='bf28044c4a9f9f68546150cdc9ab0e618a0e3541'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-289-950-intercalary-month','xinwudaishi-066-pushezhou','xinwudaishi-062-chen-hui-later']:
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
main_sources = ['tongjian-289-950-intercalary-month']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p029-p035',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
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
for n in range(29, 36):
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
    labels={'xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年六月至十月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_05_{len(B["claims"])+1:04d}'
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





ALIASES.update({'帝':'刘承祐','蜀主':'孟昶','唐主':'李璟','晋李太后':'永宁公主（石敬瑭妻）','晋主':'石重贵','冯后':'冯氏（石重贵后）','吴越王':'钱弘俶','仕毅':'孟仁毅','陈璠':'陈璠（马希广将）'})
NEW_ALIASES={'陈璠（马希广将）':[],'张延嗣':['張延嗣'],'黄处超':['黃處超'],'崔洪琏':['崔洪璉','崔珙璉','崔珙琏'],'孟仁毅':['孟仕毅'],'孟仁贽':['孟仁贄'],'孟仁裕':[],'孟仁操':[],'孟玄喆':[],'孟玄珏':[]}
NEW_DEATH_YEARS={'陈璠（马希广将）':950,'张延嗣':950,'黄处超':950}
NEW_DESCRIPTIONS={
'陈璠（马希广将）':'马希广的指挥使。950年受命抵抗攻向益阳的军队，在淹溪作战失败身亡。与晚唐同名陈璠是否有联系没有证据，分开建档，出生年未载。',
'张延嗣':'迪田镇将。950年八月戊戌，迪田被马希萼所遣军队攻破时被杀。出生年及其他经历未载。',
'黄处超':'马希广的指挥使。950年受命救援迪田方向，在作战失败后身亡。具体死亡日未另列，出生年未载。',
'崔洪琏':'马希广的牙内指挥使。950年八月条下率七千兵屯玉潭。《新五代史》同职、同兵数、同驻地人物写崔珙璉，保留异字。生卒年未载。',
'孟仁毅':'孟昶的弟弟。950年八月获封夔王。《资治通鉴》所用电子本写仕毅，《新五代史》同一夔王写仁毅，按封号和亲属身份对应为同一人，原字保留。生卒年未载。',
'孟仁贽':'孟昶的弟弟。950年八月庚子获封雅王，《新五代史》也记同一雅王册封。生卒年未载。',
'孟仁裕':'孟昶的弟弟。950年八月《资治通鉴》记封为彭王，《新五代史》相关册封却写嘉王，王号差异保留。生卒年未载。',
'孟仁操':'孟昶的弟弟。950年八月庚子，《资治通鉴》记获封嘉王。《新五代史》相关册封未列其名，未凭省略认定不存在。生卒年未载。',
'孟玄喆':'孟昶的儿子。950年八月己酉获封秦王，《新五代史》也记封秦王并判六军事。生卒年未载。',
'孟玄珏':'孟昶的儿子。950年八月己酉获封褒王，《新五代史》相关记载称他为次子。生卒年未载。'}
chu='xinwudaishi-066-pushezhou';fuzhou='xinwudaishi-062-chen-hui-later';shu='xinwudaishi-064-shu-royal-titles';jin='jiuwudaishi-086-jin-empress-exile';sep='jiuwudaishi-103-september-950';october='jiuwudaishi-103-october-950'
add('ma_xie_recruits_mountain_groups','马希萼写信招引辰、溆州及梅山各族共同攻打湖南',29,'马希萼既败归，','欲与共击湖南。',[('马希萼','败归后写信招引辰、溆州与梅山各族，共同攻打湖南')],year=None,when='马希萼此前败归之后、950年七月换俘以前，具体招引起始未载',place='朗州、辰州、溆州、梅山',note='蛮为史书对相关群体的称呼，展示用各族，未指定现代民族族属；欲共击为计划。既败归衔接此前战事，不强定写信日为本年六月。')
add('groups_attack_yiyang','响应马希萼的军队攻打益阳',29,'蛮素闻','遂攻益阳。',[('马希萼','招引的军队出兵攻打益阳')],when='950年六月条下、七月换俘之前，具体攻击日未载',place='益阳',description='史书记相关群体听说长沙府库富有，纷纷出兵响应马希萼，随后攻打益阳。',note='动机是史书概述，未具领兵者名单、兵数或实际取得长沙财物。')
sup('groups_attack_yiyang',29,chu,'希萼去，誘溪洞諸蠻寇益陽。','《新五代史》也记马希萼败去后招引溪洞各族攻益阳。','传记概述没有单列年月，不能作950年六月日期独立确证。')
add('chen_fan_sent_yiyang','马希广派陈璠抵抗进攻益阳的军队',29,'楚王希广遣','陈璠拒之，',[('马希广','派指挥使陈璠抵抗对方'),('陈璠','以马希广指挥使身份出战')],when='950年六月条下，具体派兵日未载',place='益阳、淹溪方向',note='此为楚将陈璠，与晚唐同名记录不作无证合并；同名不能证明同人。')
add('chen_fan_dies_yanxi','陈璠在淹溪战败身亡',29,'战于淹溪，',None,[('陈璠','在淹溪作战失败后身亡')],when='950年六月条下，具体死亡日未载',place='淹溪',note='败死为战败身亡，未列谁亲手杀他、伤亡总数或具体死因。')
claim('person',people['陈璠（马希广将）'],'death_year','马希广的指挥使陈璠于950年淹溪战事中战败身亡。',29,'楚王希广遣指挥使陈璠拒之，战于淹溪，璠败死。','与晚唐同名人物分开，不给旧人物追加950年死亡。')
add('tang_returns_ma_exchange','南唐归还马先进等俘虏，以交换查文徽',30,'秋，七月，',None,[('李璟','南唐归还马先进等，以交换查文徽'),('马先进','被南唐归还吴越'),('查文徽','成为南唐以归还俘虏换回的对象')],when='950年七月，具体交换日未载',place='南唐、吴越之间',note='归还与此前俘获不是同一事件。等未具其他名单，不补人数；与前段钱弘俶献庙释放记载关联，不造第二次捕获。')
sup('tang_returns_ma_exchange',30,fuzhou,'景送先進還越，越亦歸景文徽。','《新五代史》也记李璟归还马先进，吴越归还查文徽。','同一双方互还俘虏，该传没有七月纪日，不把两次引用当两次交换。')
# Add the new chronological evidence to the previously published release without rewriting it.
release_key='event_zztj_289_0950_qian_releases_zha'
release=next(x for f in (ROOT/'content').rglob('content-batch.json') if f.parent!=P for x in json.loads(f.read_text())['events'] if x['key']==release_key)
B['events'].append(dict(release,status='draft'));reused.add(release_key);used[30].append(release_key)
claim('event',release_key,'time_original','《资治通鉴》在950年七月条记南唐归还马先进等，以交换查文徽。',30,Q[30]['text'],'补充此前献庙释放记录的换俘背景；本句未单独给钱弘俶献庙日，不把七月直接改成献庙的确切日期，原发布档案不改。')
add('ma_xie_sends_ditian_attack','马希萼又派各族军队进攻迪田',31,'马希萼又遣','攻迪田，',[('马希萼','派各族军队再次进攻，目标为迪田')],when='950年八月戊戌破迪田之前，具体派兵日未载',place='迪田',note='又遣指再次派军，不把派兵日强定为攻破日；未指定现代民族。')
add('ditian_falls_zhang_killed','迪田被攻破，镇将张延嗣被杀',31,'八月，','杀其镇将张延嗣。',[('张延嗣','迪田被攻破时被杀'),('马希萼','其所遣军队攻破迪田')],when='950年八月戊戌',place='迪田',note='被杀者是镇将张延嗣，不补其他死者名单，也不认定马希萼亲手杀人。')
claim('person',people['张延嗣'],'death_year','张延嗣于950年八月戊戌在迪田被攻破时被杀。',31,'八月，戊戌，破之，杀其镇将张延嗣。','死亡年日由同句支持，不补出生年。')
add('huang_chuchao_relief','马希广派黄处超救援迪田方向',31,'楚王希广遣','救之，',[('马希广','派指挥使黄处超救援'),('黄处超','奉命前往救援')],when='950年八月迪田被攻破后，具体出兵日未载',place='迪田方向',note='救之的救援目标沿上文迪田战事，未载实际行军路线与兵数。')
add('huang_chuchao_dies','黄处超救援失败，战败身亡',31,'处超败死。','处超败死。',[('黄处超','救援战败身亡')],when='950年八月条下，具体死亡日未载',place='迪田救援战区，具体战场未载',note='未将前段戊戌硬给黄处超死亡，也不补死亡方式与杀他的人。')
claim('person',people['黄处超'],'death_year','《资治通鉴》记黄处超于950年救援迪田方向时战败身亡。',31,'楚王希广遣指挥使黄处超救之，处超败死。','具体死亡日未单列，前面的戊戌只确定攻破迪田。')
add('cui_honglian_yutan','马希广派崔洪琏率七千兵屯玉潭',31,'潭人震恐，',None,[('马希广','潭州人惊恐后，派兵屯玉潭'),('崔洪琏','以牙内指挥使身份率七千兵屯玉潭')],when='950年八月条下，黄处超战败之后，具体日未载',place='玉潭',note='潭人指潭州人，七千为史书兵数；不写已在玉潭取胜。')
sup('cui_honglian_yutan',31,chu,'希廣遣崔珙璉以步卒七千屯湘鄉玉潭以遏諸蠻。','《新五代史》记同职将领崔珙璉率步卒七千屯湘乡玉潭，阻遏对方。','姓名洪琏、珙璉为不同字，按同一派兵者、兵数、驻地与任务对应；原文与异字保留，湘乡及步卒为补书细节。',relation='adds')
# Six royal appointments, without treating book omissions as nonexistence.
brothers_quote=span(32,'庚子，','仁操为嘉王。')
for code,name,rank in [('meng_renyi_kui','孟仁毅','夔王'),('meng_renzhi_ya','孟仁贽','雅王'),('meng_renyu_peng','孟仁裕','彭王'),('meng_rencao_jia','孟仁操','嘉王')]:
 E[code]=event(code,'孟昶封'+name+'为'+rank,32,brothers_quote,[('孟昶','册封弟弟'+name+'为'+rank),(name,'获封'+rank)],when='950年八月庚子',place='后蜀朝廷',note='主书同一句列四弟册封；仕毅与新史仁毅同一夔王，字形差异保留，孟仁裕封号异说另列。')
 relationship('孟昶',name,'兄长',32,brothers_quote,'其弟统摄本句四人，孟昶是各人的兄长；具体生年与长幼排序未载，不把各弟之间顺序推作排行。')
sup('meng_renyi_kui',32,shu,'弟仁毅夔王，仁贄雅王，仁裕嘉王。','《新五代史》也列弟仁毅为夔王、仁贽为雅王。','主书仕毅与新史仁毅按同一兄长和夔王封号对应，不能仅因一字差新建孟仕毅主体。')
sup('meng_renyu_peng',32,shu,'仁裕嘉王。','《新五代史》写孟仁裕为嘉王，与《资治通鉴》的彭王不同。','保留王号冲突，主书嘉王是仁操，新史未列仁操，不能将仁裕仁操两人强合或静默互换封号。',relation='conflicts')
sons_quote=span(32,'己酉，')
for code,name,rank in [('meng_xuanzhe_qin','孟玄喆','秦王'),('meng_xuanjue_bao','孟玄珏','褒王')]:
 E[code]=event(code,'孟昶封'+name+'为'+rank,32,sons_quote,[('孟昶','册封儿子'+name+'为'+rank),(name,'获封'+rank)],when='950年八月己酉',place='后蜀朝廷',note='己酉与前句庚子为不同册封日，未给爵位对应实际封疆或到任。')
 relationship('孟昶',name,'父亲',32,sons_quote,'立子统摄同句两人，孟昶是他们父亲；不据列举顺序单独推生母或出生年。')
sup('meng_xuanzhe_qin',32,shu,'封子玄喆秦王，判六軍事；次子玄珏褒王；','《新五代史》也列孟玄喆秦王、玄珏褒王，并记玄喆判六军事，称玄珏为次子。','册封内容对照，判六军事为补书职掌，该传未单列八月己酉，不直接把全部补书职务强定本日。',relation='adds')
add('jin_lady_illness_exile','后晋李太后在建州病重，缺少医药',33,'晋李太后','无医药，',[('晋李太后','流放建州期间卧病，缺少医药')],when='950年八月戊午去世之前，具体患病起始未载',place='契丹境内建州',note='沿永宁公主（石敬瑭妻）主体，不能混成后汉刘知远妻李太后；建州为流放地，不套福建建州。')
add('jin_lady_laments','后晋李太后与石重贵哭泣，指骂杜重威和李守贞',33,'惟与晋主','吾死不置汝！”',[('晋李太后','与石重贵哭泣，指骂杜重威、李守贞'),('晋主','与李太后哭泣')],when='950年八月李太后患病期间，具体日未载',place='契丹境内建州',note='话语为记载的怨恨表达，两人此前已死，未认定在现场；吾死不置汝不写成真实死后报复。')
add('jin_lady_death','后晋李太后在流放地建州去世',33,'戊午，','卒。',[('晋李太后','在建州去世')],when='950年八月戊午',place='契丹境内建州',note='月份承八月段序，旧史引书注文另记乾祐三年八月二十五日；原地名建州建丘异字保留。')
sup('jin_lady_death',33,jin,'漢乾祐三年八月二十五日，崩於蕃中之建丘。','《旧五代史》所引《五代会要》记李太后在乾祐三年八月二十五日死于契丹境内，地名写建丘。','嵌入的引书注文与旧史正文层次保留，不把它算成旧史作者独立目击；建丘与主书建州差异待核，不换算公历日。',relation='adds',field='time_original')
claim('person',people['永宁公主（石敬瑭妻）'],'death_year','后晋李太后，即石敬瑭妻子永宁公主，于950年八月去世。',33,span(33,'晋李太后','戊午，卒。'),'身份沿此前册封与婚姻记录核对；本段记患病至戊午去世，八月承上文，另有《旧五代史》引书八月二十五日对应。')
sup('jin_lady_illness_exile',33,jin,'三年秋八月，晉李太后病，無醫藥，仰天號泣，戟手罵杜重威、李守貞曰：「吾死不置汝。」','《旧五代史》引书也记三年八月李太后缺少医药、哭泣指骂。','引书在契丹天禄年次叙事中，未把三年误解为后晋开运三年；全文纪时与主书950年并列核对。')
add('later_report_jin_survivors','后周显德年间，契丹来者报告石重贵与冯后尚在世',33,'周显德中，',None,[('晋主','被后来的报告称仍在世'),('冯后','被后来的报告称仍在世')],year=None,when='后周显德年间，具体年份未载；950年条后附追述',place='从契丹传来的消息，具体报告地点未载',description='史书后附追述说，后周显德年间有从契丹回来的人报告，石重贵与冯后仍在世，随从中逃回和去世的人合计已过半。',note='这是未具名来者报告，不造具体访问或核实日期；亡归是逃归，物故是死亡，不能把过半全解为死者，显德内容不系950年。')
add('ma_xie_requests_capital_office','马希萼请求在后汉京师另设进奏务',34,'马希萼表请','于京师。',[('马希萼','请求在京师另设进奏务')],when='950年九月辛巳批复之前，具体上表日未载',place='朗州、后汉京师',note='进奏务为藩镇在京联络奏报机构，申请不等于已经独立设立。')
add('han_refuses_ma_office','后汉以湖南已有进奏务为由，拒绝马希萼请求',34,'九月，','不许。',[('刘承祐','拒绝马希萼另设进奏务的请求'),('马希萼','另设进奏务的申请被拒绝')],when='950年九月辛巳',place='后汉朝廷',note='不许的是另设机构，不直接推已取消朗州所有奏报权或褫夺全部官爵。')
sup('han_refuses_ma_office',34,sep,'九月辛巳，朗州節度使馬希萼奏請於京師別置邸院。不允。','《旧五代史》同日也记马希萼申请另设邸院被拒。','主书进奏务、旧史邸院为本次请求的不同表述，原称保留，不拆成两次拒绝。')
add('han_urges_ma_brothers_harmony','刘承祐下诏劝马希广与兄长和睦',34,'亦赐楚王希广','劝以敦睦。',[('刘承祐','向马希广下诏劝其与兄长和睦'),('马希广','收到劝与兄长和睦的诏令')],when='950年九月辛巳条下',place='后汉朝廷、楚',note='劝和不等于双方已停止战事；敦睦按兄弟和睦解释。')
sup('han_urges_ma_brothers_harmony',34,sep,'仍命降詔和解焉。','《旧五代史》也记后汉下诏调解马氏兄弟争端。','内容对应，未把诏令当作和解已经成功。')
add('ma_xie_seeks_tang_support','马希萼认为后汉偏袒弟弟，向南唐称臣求兵',34,'马希萼以','乞师攻楚。',[('马希萼','认为朝廷偏袒马希广，向南唐称臣请求援兵'),('李璟','收到马希萼称臣与求援')],when='950年九月后汉拒绝另设进奏务后，具体遣使日未载',place='朗州、南唐朝廷',note='偏袒是马希萼对朝廷意图的理解，未当作刘承祐明言；称藩求兵不等于朗州当时已被南唐实际占领。')
add('tang_honors_ma_xie','南唐给马希萼加同平章事',34,'唐加希萼','同平章事，',[('李璟','给马希萼加同平章事'),('马希萼','获加同平章事')],when='950年九月求援后，具体加官日未载',place='南唐朝廷、朗州',note='加同平章事为官衔，不认定马希萼已到金陵日常主持南唐宰相政务。')
add('tang_grants_ezhou_tax','南唐将鄂州当年租税赐给马希萼',34,'以鄂州','今年租税赐之，',[('李璟','将鄂州当年租税赐给马希萼'),('马希萼','获赐鄂州当年租税')],when='950年，九月求援后的条下记载，具体日未载',place='鄂州、朗州',note='今年沿主书950年，授予租税未给额度、实际到账日或运输路线，不写整州被割让。')
add('he_jingzhu_ordered_ma_support','李璟命楚州刺史何敬洙率兵援助马希萼',34,'命楚州刺史','将兵助希萼。',[('李璟','命何敬洙率兵支援马希萼'),('何敬洙','以楚州刺史身份奉命率兵援助'),('马希萼','成为南唐派兵支援的对象')],when='950年九月求援后，具体命令日未载',place='楚州至马希萼所在方向',note='这是派兵命令，本句未给兵数、实际到达和战果，楚州是州名不是楚王国全境。')
add('ma_xiguang_appeals_han','马希广报告三方谋分湖南，请后汉屯兵澧州',34,'冬，十月，',None,[('马希广','向后汉告急，报告三方谋分湖南并请求屯兵澧州'),('刘承祐','收到马希广的告急与求援表章')],when='950年十月丙午',place='楚、后汉朝廷、拟驻澧州',description='马希广派使上表告急，声称荆南、岭南、江南共同谋划瓜分湖南，请后汉派兵屯澧州，阻截江南、荆南援助朗州的通路。',note='联合谋划是求援表章的报告，不当作已独立证实的全部协同方案；拟屯澧州不是汉兵已经到达。')
sup('ma_xiguang_appeals_han',34,october,'丙午，湖南馬希廣遣使上章，且言荊南、淮南、廣南三道結構，欲分割湖、湘，乞聊發兵師，以為援助。','《旧五代史》同日也记马希广报告荆南、淮南、广南谋分湖湘并求援。','三方名称两书不同但均是表章报告，未依该句把三方君主列为已确定共同出兵的参与者。')
sup('ma_xiguang_appeals_han',34,october,'時朝廷方議起軍，會內難，不果行。','《旧五代史》还记后汉朝廷正议出兵，遇到内乱，未能成行。','跨时段结果作为书证补充，内难未在本句单列日期，不另造十月丙午已经发生的内乱或实际援军。',relation='adds')
add('qian_overall_marshal','后汉给钱弘俶加诸道兵马元帅',35,'丁未，',None,[('刘承祐','给吴越王钱弘俶加诸道兵马元帅'),('吴越王','以吴越王身份获加诸道兵马元帅')],when='950年十月丁未',place='后汉朝廷、吴越',note='弘亻叔沿钱弘俶拆字字形，沿用同一主体；加元帅是官号，未据此推他实际指挥所有藩镇军队。')
sup('qian_overall_marshal',35,october,'丁未，兩浙錢宏俶加諸道兵馬元帥。','《旧五代史》同日也记钱宏俶加诸道兵马元帅。','宏俶、弘俶为既有主体不同写法，不新建钱宏俶。')
reviews={29:'败归后的招引起始未明，既往动作不强定950六月；攻益阳、派陈与淹溪败死按本年条下，未补纪日。蛮为来源称呼，不指定现代民族。楚将陈璠与晚唐同名分开，不给旧主体追加950死亡。',30:'归俘交换与此前俘获分开，与已发布钱弘俶献庙释放同主体关联补时序；未把七月定为献庙的确切日，不重复建立第二次钱释放。其他俘虏未具名不补。',31:'派军、戊戌破迪田杀张、派黄救援和黄败死、派崔屯玉潭分开。黄死亡未套戊戌；崔洪琏新史珙璉同一派兵者兵数驻地对照，湘乡与步卒另补；七千为书载兵数，未造玉潭战胜。',32:'四弟庚子和二子己酉六册封分录。仕毅与仁毅同夔王亲属核对；仁裕彭王嘉王冲突、仁操新史未列不强合。兄父关系方向明确，不推各弟排行或生母；新史判六军与次子称谓未任意套己酉。',33:'后晋李太后沿石敬瑭妻永宁公主，与后汉李太后分开；契丹建州不套福建。戊午承八月，旧史引会要八月25与建丘异字保留，嵌引不是独立目击。怨语不是死后报复，显德来者报告追述year null，过半逃归或死不是全死。',34:'请设机构与九月批复、劝和、马认为偏佑、称藩求援、唐加官租税派军、十月告急分开。官号非实任南唐宰相，租税非整州割让；求援表中的三方连谋为报告，议援因内难未成的跨期结果不强系丙午。',35:'元帅加号不等于实际控制天下军队，钱拆字及弘宏沿同一主体，旧史同日印证。'}
assert not (P/'publication.json').exists()
for n in range(29,36):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(29,36)],next_paragraph=Q[36]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原34—40行连续七段；发布后首35/83正文已录，余48段待录。显德报告为本段附追述，不误标950已发生。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(29,36)],source_issues_review='后蜀仕毅仁毅、崔洪琏珙璉按亲属封号或军职驻地核同人，仁裕王号异说独立保留；新史不列仁操不是不存在。楚将陈璠与晚唐同名分开。旧史卷86引书李太后死记建丘与主建州待核，原引书层次保留。主换俘补七月不改旧献庙档案；显德报告年份未定。纸本及转录异文待核。',plain_language_review='首次逐条检查人物介绍、事件正文、角色、亲属方向、时间地点和出处解释。明确主体，不把计划、加号、求援声称、后述和统计概数当真实执行；未知时间留null，旧主体和旧档案保持，原字引用不改。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
