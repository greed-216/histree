# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 48–53."""
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
COMMIT='2acb872f407f87ecc1c683ebe4afe35ab5af384e'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-289-950-assassination-orders','xinwudaishi-010-han-court-killings']:
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
main_sources = ['tongjian-289-950-assassination-orders','tongjian-289-950-guo-march']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p048-p053',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-103-guo-march':'卷103·隐帝本纪·郭威起兵与滑州','xinwudaishi-011-guo-march':'卷11·周本纪·郭威南下','songshi-461-zhao-xiuji-career':'卷461·赵修己传·离开李守贞至翰林天文','tongjian-289-950-guo-march':'卷289·乾祐三年·南下与禁军赏赐','jiuwudaishi-107-wang-zhang-finance':'卷107·王章传·财政措施','xinwudaishi-010-han-court-killings':'卷10·汉本纪·乾祐三年十一月','tongjian-289-950-ministers-conspiracy':'卷289·乾祐三年·诛杀计划及追述','tongjian-289-950-assassination-orders':'卷289·乾祐三年·丙子诛杀与密诏','jiuwudaishi-103-november-950':'卷103·隐帝本纪·乾祐三年十一月','jiuwudaishi-124-wang-yin-origin':'卷124·王殷传·籍贯与驻澶州','tongjian-289-950-november-start':'卷289·乾祐三年·十月至十一月','xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
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
for n in range(48, 54):
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
    labels={'jiuwudaishi-103-guo-march':'卷103·隐帝本纪·郭威起兵与滑州','xinwudaishi-011-guo-march':'卷11·周本纪·郭威南下','songshi-461-zhao-xiuji-career':'卷461·赵修己传·离开李守贞至翰林天文','tongjian-289-950-guo-march':'卷289·乾祐三年·南下与禁军赏赐','jiuwudaishi-107-wang-zhang-finance':'卷107·王章传·财政措施','xinwudaishi-010-han-court-killings':'卷10·汉本纪·乾祐三年十一月','tongjian-289-950-ministers-conspiracy':'卷289·乾祐三年·诛杀计划及追述','tongjian-289-950-assassination-orders':'卷289·乾祐三年·丙子诛杀与密诏','jiuwudaishi-103-november-950':'卷103·隐帝本纪·乾祐三年十一月','jiuwudaishi-124-wang-yin-origin':'卷124·王殷传·籍贯与驻澶州','tongjian-289-950-november-start':'卷289·乾祐三年·十月至十一月','xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年十一月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_08_{len(B["claims"])+1:04d}'
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








ALIASES.update({'帝':'刘承祐','王殷':'王殷（后汉后周将）','赵修已':'赵修己','荣':'柴荣','永宁公主':'永宁公主（石敬瑭女）'})
NEW_ALIASES={'陈光穗':['陳光穗'],'鸗脱':['鸗脫','驡脫'],'宋延渥':[],'永宁公主（石敬瑭女）':[]}
NEW_DESCRIPTIONS={
'陈光穗':'950年任澶州副使，奉王殷命将杀害将帅的密诏带给郭威。《旧五代史》说王殷与李洪义共同派遣。生卒年未载，不因同名自动并入早期河东使者。',
'鸗脱':'后汉内养。950年奉刘承祐命侦察郭威，被郭威抓获后携奏表返回大梁。《新五代史》写驡脫，按相同职务与行动对应，原字保留。生卒年未载。',
'宋延渥':'洛阳人，950年任义成节度使，郭威南下时在滑州迎降。他的妻子是后晋石敬瑭的女儿永宁公主。迎降纪日两部史书有差异，生卒年未载。',
'永宁公主（石敬瑭女）':'后晋石敬瑭的女儿，宋延渥的妻子。与石敬瑭妻子曾获永宁公主封号的李氏分开建档。具体姓名、生卒年与婚期未载。'}
old='jiuwudaishi-103-guo-march';new='xinwudaishi-011-guo-march';han='xinwudaishi-010-han-court-killings';song='songshi-461-zhao-xiuji-career'
add('li_hongyi_shows_meng','李洪义不敢执行密诏，将孟业引见王殷',48,'丁丑，','乃引孟业见殷。',[('李洪义','担心王殷知情，不敢发出杀人密诏'),('孟业','到澶州传诏，被引见王殷'),('王殷','获见携密诏的使者')],when='950年十一月丁丑',place='澶州',note='使者到达承前段孟业，密诏未执行，不写王殷遇害；畏懦为史书评语。')
sup('li_hongyi_shows_meng',48,old,'丁丑，澶州節度使李洪義受得密詔，知事不克，乃引使人見王殷。','《旧五代史》同日也记李洪义把使者引见王殷。','同一澶州使者，职名镇宁节度使与本纪澶州节度使为不同称呼，未另造同人。')
add('wang_yin_detains_meng','王殷囚禁孟业，派陈光穗把密诏送给郭威',48,'殷囚业，','以密诏示郭威。',[('王殷','囚禁使者，派副使送诏'),('孟业','被囚禁'),('陈光穗','将密诏送给郭威'),('郭威','收到杀害将帅的密诏')],when='950年十一月丁丑条下，具体送达时刻未载',place='澶州至邺都',note='派使与告知据本句，未造孟业被处死；送诏不是郭威亲自到澶州才获悉。')
sup('wang_yin_detains_meng',48,old,'殷與洪義遣本州副使陳光穗賫所受密詔，馳至鄴都。','《旧五代史》说王殷与李洪义共同派陈光穗持诏到邺都。','补充共同遣使者与目的地，与《资治通鉴》王殷派使不矛盾；此身份不等于早年河东供奉官陈光穗同人已核。',relation='adds')
add('wei_renpu_opposes_passive_death','魏仁浦劝郭威不能坐待被杀',48,'威召枢密吏魏仁浦，','不可坐而待死。”',[('郭威','向魏仁浦展示诏书并询问对策'),('魏仁浦','认为不能靠解释消除杀身危险，劝郭威不可坐等')],when='950年十一月丁丑条下，郭威得密诏之后',place='邺都',note='这是对策建议，未把大功或群小构陷等话语作独立证实的司法结论。')
sup('wei_renpu_opposes_passive_death',48,old,'魏仁浦曰：「公有大功於朝廷，握強兵，臨重鎮，以讒見疑，豈可坐而待斃！」','《旧五代史》引《东都事略》也记魏仁浦反对郭威坐待被杀。','引用层次为嵌入引书，不算旧本纪作者独立目击。')
add('guo_informs_commanders','郭威向郭崇威、曹威等说明密诏，提出让他们杀自己交差',48,'威乃召郭崇威、','庶不相累。”',[('郭威','告知三臣被杀与密诏，表示诸将可奉诏取其首'),('郭崇威','听取郭威告知'),('曹威','听取郭威告知')],when='950年十一月丁丑条下，具体召见时刻未载',place='邺都',note='取吾首是对诸将的说辞，不是已被处决；冤死、托孤等按郭威话语呈现，不据此新增早年托孤仪式。')
add('commanders_support_guo','郭崇威等拒绝杀郭威，表示愿随他入朝自诉',48,'郭崇威等皆泣曰：','受千载恶名。”',[('郭崇威','带头表示愿随郭威入朝申诉'),('郭威','得到将领支持')],when='950年十一月丁丑条下，诸将听取密诏后',place='邺都',note='群小所为是诸将解释，不推皇帝完全不知密诏；等所指未逐一具名，不给曹威强加逐字发言。')
sup('commanders_support_guo',48,old,'崇等願從公入朝，面自洗雪。','《旧五代史》也记将领愿随郭威入朝自辩。','本纪写郭崇、曹英，与《资治通鉴》郭崇威、曹威的名单差异保留；不单凭叙事位置合并曹英与曹威。')
add('zhao_urges_south','赵修己劝郭威顺从军心，率兵南下',48,'翰林天文赵修已','此天启也。”',[('赵修已','以翰林天文身份建议郭威拥兵南下'),('郭威','听取率兵南下建议')],when='950年十一月丁丑至戊寅出兵前，具体进言时刻未载',place='邺都',note='主书修已、宋史修己按由李守贞幕府转任翰林天文的履历衔接；天启为他的说法，不认定神意。')
claim('person',people['赵修己'],'description','《宋史》赵修己传记他离开李守贞幕府后，朝廷召其为翰林天文。',48,(sources[song]/'source.txt').read_text().strip(),'同传写李守真，与《资治通鉴》的李守贞写法不同；传中浚仪籍贯、滑州司户、劝幕主与辞疾归里经历，与既有主体对应，补上此后的官职衔接；不改旧档案，主书修已异字保留。',source=song)
add('chai_stays_ye','郭威留下养子柴荣镇守邺都',48,'郭威乃留其养子荣','镇鄴都，',[('郭威','留下养子守邺都'),('荣','留守邺都')],when='950年十一月戊寅南下之前',place='邺都',note='荣沿既有柴荣郭荣主体；明确养子，不改写成郭威亲生子。')
relationship('郭威','柴荣','养父',48,'郭威乃留其养子荣镇鄴都，','郭威是柴荣养父，复用已有关系，不另建同端点重复边。')
add('guo_chongwei_vanguard','郭威命郭崇威率骑兵先行',48,'命郭崇威','将骑兵前驱，',[('郭威','命骑兵先行'),('郭崇威','率骑兵担任前锋')],when='950年十一月戊寅大军南下前，具体命令时刻未载',place='邺都向南',note='前驱是先锋，不补骑兵数或同日已到达地点。')
add('guo_south_departure','郭威于戊寅亲率大军南下',48,'戊寅，',None,[('郭威','亲率大军跟随骑兵南下')],when='950年十一月戊寅',place='邺都向南',note='大军未给总数，不把旧本纪到澶州日期直接替换主书出发日。')
sup('guo_south_departure',48,old,'翌日，郭威以眾南行。戊寅，鄴兵至澶州。','《旧五代史》记郭威次日南下，并把邺兵到澶州记在戊寅。','主书戊寅记郭威率大军继进，到澶州置后文己卯条下，两书到达日期差异保留。',relation='conflicts')
add('murong_arrives_command','慕容彦超接诏立即入朝，刘承祐将军事交给他',49,'慕容彦超方食，','帝悉以军事委之。',[('慕容彦超','接诏放下餐具入朝，获委军事'),('帝','把军事交由慕容彦超负责')],when='950年十一月，己卯吴虔裕入朝之前，具体慕容到达日未载',place='后汉京师',note='得诏停食为紧急应召，不推其当时在何具体城宅；悉委为军事责任，不造具体最高官名任命。')
add('wu_qianyu_arrives','吴虔裕于己卯入朝',49,'己卯，',None,[('吴虔裕','奉召入朝')],when='950年十一月己卯',place='后汉京师',note='沿前批郑州防御使主体，此次明确到达，与此前召令分开。')
add('hou_yi_proposes_family_persuasion','侯益建议闭城守御，让北军家属招劝军队',50,'帝闻郭威','可不战而下也。”',[('帝','得知郭威南下，与臣下议兵'),('侯益','建议守城并利用城中军人家属招劝')],when='950年十一月己卯条下，具体议兵时刻未载',place='后汉京师',note='不战而下是侯益预期，本句未记家属已登城或北军已降。')
add('murong_rejects_hou_plan','慕容彦超讥讽侯益的守城建议',50,'慕容彦超曰：','为懦夫计耳。”',[('慕容彦超','认为侯益的建议怯懦'),('侯益','其守城建议被讥讽')],when='950年十一月己卯条下',place='后汉朝廷',note='衰老懦夫为慕容的评价，不作侯益客观能力定论。')
add('han_sends_four_chan','刘承祐派侯益等四人率禁军前往澶州',50,'帝乃遣益',None,[('帝','派禁军前往澶州'),('侯益','受命率禁军'),('阎晋卿','受命率禁军'),('吴虔裕','入朝后受命率禁军'),('张彦超','以前保大节度使身份受命率禁军')],when='950年十一月己卯条下，《旧五代史》系庚辰',place='京师至澶州方向',note='趣是趋往，不是本段已到；原职保大军与旧本纪鄜州为军镇不同称呼，不新建同名。')
sup('han_sends_four_chan',50,old,'是日，詔前開封尹侯益、前鄜州節度使張彥超、權侍衛馬軍都指揮使閻晉卿、鄭州防禦使吳虔裕等，率禁軍赴澶州守捉。','《旧五代史》也记四人率禁军赴澶州，系于此前庚辰条下。','与主书己卯条下遣军纪日不同，保留两说，不猜测诏下与出发分日来消除差异。',relation='conflicts',field='time_original')
add('li_hongyi_admits_guo','李洪义接纳已到澶州的郭威',51,'是日，','李洪义纳之。',[('郭威','到澶州获接纳'),('李洪义','接纳郭威')],when='950年十一月己卯条下，是日承接前段；旧本纪记邺兵戊寅已到澶州',place='澶州',note='主书是日沿己卯条序，旧本纪另说戊寅，不消除到达纪日差异。')
add('wang_yin_crosses_with_guo','王殷迎见郭威哭泣，率所部随郭威渡河',51,'王殷迎谒恸哭，','从郭威涉河。',[('王殷','迎见郭威，率部随其渡河'),('郭威','获王殷率部同行')],when='950年十一月己卯条下，具体渡河时刻未载',place='澶州黄河方向',note='涉河由澶州南下语境指渡河，未给渡口名称或兵数。')
add('longtuo_spies_captured','刘承祐派鸗脱侦察郭威，鸗脱被捕',51,'帝遣内养鸗脱','威获之，',[('帝','派内养侦察郭威'),('鸗脱','侦察时被郭威捕获'),('郭威','捕获侦察使者')],when='950年十一月己卯条下，具体派遣与被捕时刻未载',place='郭威军中，具体捕获处未载',note='觇为侦察，不补暗杀计划；内养身份保留，不猜测姓名本字或出身。')
sup('longtuo_spies_captured',51,new,'又遣內養驡脫覘威所嚮。驡脫為威所得，','《新五代史》也记内养驡脫侦察郭威后被捕。','鸗脱驡脫按同一内养、相同侦察被捕与带奏任务对应，原字保留。')
add('guo_sends_petition_by_longtuo','郭威将奏表放入鸗脱衣领，遣其回报刘承祐',51,'以表置鸗脱',None,[('郭威','遣使带奏表，声称受诸将逼迫南行并请求交出进谗者'),('鸗脱','衣领中携郭威奏表返京'),('帝','成为奏表请求的对象')],when='950年十一月己卯条下，鸗脱被捕后返京之前',place='郭威军中至大梁',description='郭威把奏表放在鸗脱衣领中让他回京，向刘承祐声称自己求死而诸将不许，逼其南行请罪，并请求交出进谗者。他表示若办到，愿劝军队退回邺都。',note='奏表是郭威自述与条件承诺，不当作此前没有自主决策或必定退军的证明；此处尚未记奏表送达。')
sup('guo_sends_petition_by_longtuo',51,new,'威乃附脫奏請縛李業等送軍中。','《新五代史》明确记郭威请求把李业等捆送军中。','主书此表用若实有谮臣者的条件说法，补书明确姓名，分来源并列，不替换原表词。',relation='adds')
add('guo_advances_hua','郭威于庚辰向滑州进军',52,'庚辰，','郭威趣滑州。',[('郭威','向滑州进军')],when='950年十一月庚辰',place='澶州至滑州',note='趣为进军方向，与迎降另日分开，不强认本句已经进入城内。')
add('song_yanwo_surrenders','宋延渥在滑州迎降郭威',52,'辛巳，','宋延渥迎降。',[('宋延渥','以义成节度使身份迎降'),('郭威','接受迎降')],when='950年十一月辛巳；新旧五代史系庚辰',place='滑州',note='主书辛巳与新旧史庚辰不同，保留差异，不猜测先请降后开门分日。')
sup('song_yanwo_surrenders',52,old,'庚辰，至滑州，節度使宋延渥開門迎降。','《旧五代史》把郭威至滑州、宋延渥开门迎降系于庚辰。','与主书辛巳差一干支日，原文并列，不覆盖。',relation='conflicts',field='time_original')
sup('song_yanwo_surrenders',52,han,'庚辰，義成軍節度使宋延渥叛附于威。','《新五代史》同样系宋延渥归附郭威于庚辰。','《新五代史》与《旧五代史》同日并不自动证明《资治通鉴》必错，各书记载保留。',relation='conflicts',field='time_original')
# Marriage and parentage are background statements, not dated wedding events.
family=span(52,'延渥，洛阳人，','永宁公主也。')
person('永宁公主',52,'石敬瑭的女儿、宋延渥的妻子',family)
person('石敬瑭',52,'永宁公主的父亲',family)
relationship('永宁公主（石敬瑭女）','宋延渥','妻子',52,family,'宋延渥妻为石敬瑭女，方向为公主是宋延渥妻子；婚期未知，不套迎降日。')
relationship('石敬瑭','永宁公主（石敬瑭女）','父亲',52,family,'晋高祖指石敬瑭，方向为石敬瑭是此公主父亲；与石敬瑭妻子曾用永宁公主号的李氏分开。')
claim('person',people['宋延渥'],'description','宋延渥是洛阳人。',52,'延渥，洛阳人，','籍贯原文明示，不补出生地或生日。')
add('guo_rewards_hua_stores','郭威取滑州府库物品犒劳将士',52,'郭威取滑州','以劳将士，',[('郭威','取滑州库物犒劳将士')],when='950年十一月辛巳迎降后，具体分发时刻未载',place='滑州',note='未给物品总量或每人份额，不补征收程序。')
add('guo_questions_fighting_han','郭威向将士说与侯益军交战不合入朝名义，再提出愿奉诏死',52,'且谕之曰：','吾死不恨！”',[('郭威','向将士提出交战与被收编的两难，说愿奉诏死')],when='950年十一月辛巳条下',place='滑州军中',note='侯益督军南来是郭威听闻的情况；奉诏死是发言，不是实际死亡。')
add('troops_reaffirm_support','将士表示国家负郭威，愿继续为他作战',52,'皆曰：','侯益辈何能为乎！”',[('郭威','得到将士继续支持')],when='950年十一月辛巳条下',place='滑州军中',note='万人争奋是军中话语，不作为精确军队人数；本句诸将未具名不补发言人。')
add('wang_jun_promises_plunder','王峻向军队宣称攻下京城后可抢掠十日',52,'王峻徇于众曰：',None,[('王峻','宣称得到郭威指示，许诺克京城后抢掠十日')],when='950年十一月辛巳条下，尚未攻占京城',place='滑州军中',note='我得公处分为王峻所宣称的授权，不在本段单独推郭威私下已发何命令；许诺抢掠不是本日已在京城实施。')
add('longtuo_returns_daliang','鸗脱于辛巳返回大梁',53,'辛巳，','鸗脱至大梁。',[('鸗脱','携郭威奏表返回大梁')],when='950年十一月辛巳',place='大梁',note='返回对应前段携表使命，但本句没有当面呈表仪式细节。')
add('emperor_cancels_chan_trip','刘承祐原拟亲往澶州，得知郭威到河上后停止',53,'前此帝议','河上而止。',[('帝','取消亲往澶州的计划')],when='950年十一月辛巳之前，具体议行与取消日未载',place='京师、拟往澶州',note='前此表先前计划，未写成辛巳当日；此为950年近日事件而非数年前背景。')
add('emperor_regrets_to_dou','刘承祐私下对窦贞固说此前处置过于草率',53,'帝甚有悔惧之色，','属者亦太草草。”',[('帝','表现悔惧，私下说此前太草率'),('窦贞固','听到皇帝私话')],when='950年十一月辛巳条下，具体私话时刻未载',place='后汉宫廷，具体私谈处未载',note='属者指前些时候，不另补原文未列的承认书或撤销诛杀诏令。')
add('li_ye_su_reward_dispute','李业等求倾府库赏军，苏禹珪反对后被李业当面恳求',53,'李业等请','勿惜府库！”',[('李业','要求大赏诸军并当面拜求苏禹珪'),('苏禹珪','认为尚不可倾府库赏军'),('帝','在场听取争论')],when='950年十一月辛巳条下',place='后汉宫廷',note='相公为苏禹珪，拜是李业对他行礼请求，不是任命苏为新官。')
add('han_rewards_guard_families','后汉赏禁军每人二十缗，并以家信招诱北方将士',53,'乃赐禁军',None,[('帝','朝廷在其统治下给军队赏钱并招诱北方军人')],when='950年十一月辛巳条下',place='后汉京师及北军家属所在处',description='后汉给禁军每人二十缗，下军减半；将士在北方的，把赏钱给其家属，并允许传递家信以招诱他们。',note='下军按原称保留，不能套现代具体军种；未给军队总数，不计算无根据总支出，家信招诱未表成功。')
reviews={48:'丁丑使者到澶州、王殷囚使派陈、郭威得诏询魏、告诸将、诸将支持、赵劝南、留养子、命前锋与戊寅出军分开。宋史赵传衔接李守贞幕府和翰林天文，复用既有人；赵修已己原字保留。旧本纪曹英与主曹威差异不无证合并；到澶纪日冲突保留。',49:'慕容应召与获委军事无确日，不套己卯；吴虔裕己卯入朝明确，与前批召令分开。',50:'侯益闭城用家属招劝为建议，慕容嘲讽为意见，四将出军为命令不等于到达。主书己卯条下与旧本纪庚辰差异保留。',51:'是日承前段己卯，旧本纪戊寅到澶之说并列。王殷沿后汉后周主体；鸗脱驡脫同内养侦察带表事件对应。郭威被迫南行是奏表自述，与此前主动决策并列，不当事实替代。',52:'庚辰进滑与辛巳宋迎降分录，新旧史系庚辰差异保留。石敬瑭女永宁公主与妻李太后同号分开；婚期未知不套归附日。犒军、对话与王峻许抢掠十日分开，授权为王峻宣称，未提前写实际抢京。',53:'鸗脱辛巳到大梁明确；前此亲行计划取消不套当天。悔语不造撤诏；赏军请求争论与实际赏钱家信分开，下军保留历史类别，未算无据总支出或招诱成功。'}
assert not (P/'publication.json').exists()
for n in range(48,54):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(48,54)],next_paragraph=Q[54]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原53—58行连续六段；发布后首53/83正文已录，余30段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(48,54)],source_issues_review='赵修已己依宋传职掌衔接复用；公主同封号分人。旧曹英主曹威名单差异、到澶与滑州迎降纪日差异保留；主书是日沿己卯条序。宋传和旧本纪相互嵌引不当独立目击。纸本与转录异文待核。',plain_language_review='首次逐条自查现代白话、主体、关系、时间和原文；建议与执行、奏表自述与实际行动、劫掠许诺与后续行为分开。引用原字保留，别字不无证建重复人。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
