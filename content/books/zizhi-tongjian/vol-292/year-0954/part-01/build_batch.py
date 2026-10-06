# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 954 paragraphs 1–5."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,26))
COMMIT='2045d769bf64a5bf30604e638acd5ac322c1f6df'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['xinwudaishi-12-chairong-accession','songshi-253-zhe-deyi-family']:
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
main_sources = ['tongjian-292-954-may-siege']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0954-p001-p005',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
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
lines = (ROOT / 'resources/derived/tongjian/292.txt').read_text().splitlines()
for n in range(1, 6):
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
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷292·显德元年（954年五月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0954_01_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=954, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='954年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_292_0954_' + code
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
        edge = 'participation_zztj_292_0954_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_292_0954_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 if kw.get('source'):
  t=(sources[kw['source']]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);quote=t[a:b]
 else:quote=span(n,start,end)
 E[code]=event(code,title,n,quote,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)










ALIASES.update({'帝':'柴荣','契丹主':'耶律璟','杨兗':'杨衮','李筠':'李筠（原名李荣）','史彦超':'史彦超（后周将领）'})
NEW_ALIASES={'郑处谦':['鄭處謙'],'桑珪':[],'解文遇':[]}
NEW_DESCRIPTIONS={'郑处谦':'北汉代州防御使。954年五月拒绝契丹将杨衮召见，杀死守其城门的契丹骑兵后以城归降后周，被任为静塞军节度使。同月被代州将桑珪、解文遇杀死，两将诬称他暗通契丹。生年未载。','桑珪':'代州将领。954年五月与解文遇杀死已降后周的郑处谦，诬称郑暗通契丹。《新五代史》也记桑珪杀郑处谦并以城降周。生卒年本段未载，后续行动另随编年录入。','解文遇':'代州将领。954年五月与桑珪杀死郑处谦，诬告郑暗通契丹。生卒年未载。'}
NEW_DEATH_YEARS={'郑处谦':954}
old='jiuwudaishi-114-may-954';labor='jiuwudaishi-114-siege-labor-954';new='xinwudaishi-12-chairong-accession';shishi='xinwudaishi-33-shi-yanchao-death';sang='xinwudaishi-70-sang-gui-zheng';zhe='songshi-253-zhe-deyi-family'
add('wangkui_moves_to_langzhou','王逵从潭州迁回朗州',1,'五月，甲戌朔，','王逵自潭州迁于朗州。',[('王逵','从潭州迁治朗州')],when='954年五月甲戌朔',place='潭州至朗州',note='对应上一卷上表请求迁回朗州之后的实际迁移，不把请求与执行合并。')
add('zhou_xingfeng_administers_tanzhou','王逵任周行逢主持潭州事务',1,'以周行逢','知潭州事，',[('王逵','安排周行逢主持潭州事务'),('周行逢','获任知潭州事')],when='954年五月甲戌朔',place='潭州')
add('pan_shusi_yuezhou_commander','王逵任潘叔嗣为岳州团练使',1,'以潘叔嗣',None,[('王逵','任潘叔嗣为团练使'),('潘叔嗣','获任岳州团练使')],when='954年五月甲戌朔',place='岳州')
add('chairong_reaches_jinyang_walls','柴荣到达晋阳城下，周军旗帜环城四十里',2,'丙子，','旗帜环城四十里。',[('帝','到达晋阳城下围城')],when='954年五月丙子',place='晋阳城下',note='四十里按史书记述保留，不把旗帜分布范围画成已经核定的精确包围圈。')
sup('chairong_reaches_jinyang_walls',2,old,'丙子，車駕至太原城下。','《旧五代史》同记五月丙子柴荣到太原城下。','晋阳城下与太原城下按同一围城战地理解，坐标仍未核定。')
add('yang_gun_plots_against_zheng','杨衮怀疑郑处谦有意归周，借议事召见企图加害，郑未赴约',2,'杨兗疑北汉代州防御使','处谦知之，不往。',[('杨兗','怀疑郑处谦，试图借召见加害'),('郑处谦','知道杨衮的意图后不赴召')],when='954年五月丙子前后的代州记载，具体日未载',place='代州',note='怀疑郑向周是杨衮的判断，不写成已经证实的密约；企图加害未在此次召见中执行。')
add('zheng_kills_gate_guards','郑处谦杀死杨衮派来的数十契丹骑兵，闭门拒绝杨衮',2,'兗使胡骑数十','因闭门拒兗。',[('杨兗','派数十骑兵看守代州城门'),('郑处谦','杀守门契丹骑兵并闭门拒杨衮')],when='954年五月代州召见争执后',place='代州城门',note='数十为史载概数，不自行细分准确人数。')
add('yang_gun_returns_and_is_jailed','杨衮逃回契丹，耶律璟因他无功将其下狱',2,'兗奔归契丹。','囚之。',[('杨兗','逃回契丹后被囚'),('契丹主','因杨衮无功而将其下狱')],when='954年五月代州拒绝杨衮后',place='契丹',note='囚之是拘禁，不把杨衮写成已经处死。')
add('zheng_submits_daizhou','郑处谦以代州向后周投降',2,'处谦举城来降。','处谦举城来降。',[('郑处谦','以代州归降后周')],when='954年五月丙子前后的记载',place='代州')
sup('zheng_submits_daizhou',2,old,'是日，偽代州防禦使鄭處謙以城歸順。','《旧五代史》把郑处谦以城归顺记在柴荣到太原城下的五月丙子当天。','主书本段未给归降独立日期，补证保留旧史同日记载。',relation='adds',field='time_original')
add('jingse_military_district','柴荣在代州设置静塞军，任郑处谦为节度使',2,'丁丑，',None,[('帝','设置静塞军并任命节度使'),('郑处谦','获任静塞军节度使')],when='954年五月丁丑',place='代州')
sup('jingse_military_district',2,old,'升代州為節鎮，以靜塞軍為額，以鄭處謙為節度使。','《旧五代史》同记代州升节镇、军号静塞、郑处谦任节度使。','接在丁丑观兵之后，未将上一日归降与次日设军授职合并成同一件事。')
add('an_yanjin_executed_after_capture','柴荣因安彦进抵抗周军，将他在太原城下处死',2,'戊寅，','以其拒王師也。',[('柴荣','处死俘获的北汉石州刺史'),('安彦进','被俘后遭处死')],when='954年五月戊寅，《旧五代史》纪日',place='太原城下',source=old,note='补充上一批所记被俘之后的实际处刑；主书俘获记录未说处死，另据旧本纪当前日期立事件。')
claim('person',people['安彦进'],'death_year','安彦进在954年五月戊寅被后周处死。',2,'戊寅，斬偽命石州刺史安彥進於太原城下，以其拒王師也。','按《旧五代史》当前日期补死亡事实；既有主体字段不无守卫覆盖。',source=old)
add('khitan_aid_between_xin_dai','契丹数千骑驻忻州与代州之间，援助北汉',3,'契丹数千骑','为北汉之援，',[('契丹主','所派骑兵驻忻代之间援助北汉')],when='954年五月庚辰出兵前',place='忻州、代州之间',note='与四月答应发援军区分，此处记实际骑兵驻地；兵力仅数千，不把不同援军阶段合成精确总数。')
add('fu_moves_against_khitan_relief','柴荣命符彦卿等率万余步骑攻击契丹援军',3,'庚辰，','万馀击之。',[('帝','派符彦卿等攻击援军'),('符彦卿','率万余步骑出击契丹援军')],when='954年五月庚辰',place='晋阳至忻州')
sup('fu_moves_against_khitan_relief',3,old,'遣符彥卿、郭從義、向訓、白重贊、史彥超等，率步騎萬餘赴忻州。','《旧五代史》补列郭从义、向训、白重赞、史彦超同赴忻州。','按同日同一行军补将领名单，不把共同出军自动推成私人盟友。',relation='adds')
# The supplementary book names additional commanders of the same event.
for name in ['郭从义','向训','白重赞','史彦超']:
 quote='遣符彥卿、郭從義、向訓、白重贊、史彥超等，率步騎萬餘赴忻州。'
 pk=person(name,3,'据《旧五代史》奉命赴忻州迎击契丹援军',quote,source=old)
 ek='participation_zztj_292_0954_fu_moves_against_khitan_relief_'+pk
 row=dict(key=ek,person_key=pk,event_key=E['fu_moves_against_khitan_relief'],role='据《旧五代史》同赴忻州迎击契丹援军',status='draft');B['person_events'].append(row)
 claim('person_event',ek,'role',row['role'],3,quote,'旧本纪点明该将领同赴忻州，连接同一出军事件。',source=old)
add('khitan_retreat_to_xinkou','符彦卿进入忻州，契丹援军退守忻口',3,'彦卿入忻州，',None,[('符彦卿','进入忻州，契丹军退守忻口')],when='954年五月庚辰出兵后',place='忻州、忻口')
add('ninghua_military_district','柴荣在汾州设置宁化军，将石州、沁州归其管辖',4,'丁亥，','以石、沁二州隶之。',[('帝','设置宁化军并调整辖区')],when='954年五月丁亥',place='汾州、石州、沁州')
add('sang_xie_kill_zheng','桑珪、解文遇杀死郑处谦，诬告他暗通契丹',4,'代州将桑珪、',None,[('桑珪','与解文遇杀郑处谦并诬告其通敌'),('解文遇','与桑珪杀郑处谦并诬告其通敌'),('郑处谦','被两将杀害并受到通敌诬告')],when='954年五月丁亥条下，具体杀人日未另列',place='代州',note='诬奏不是已证实的通敌；与此前杨衮怀疑郑有意归周的情节分开。')
sup('sang_xie_kill_zheng',4,sang,'代州將桑珪殺防禦使鄭處謙，以城降周，','《新五代史》也记桑珪杀郑处谦并以城降周，仍称郑为防御使。','新史未列解文遇及诬告，也未在此简文交代郑先降周、任节度使的先后；保留主书更细的顺序。')
add('fu_requests_reinforcements','符彦卿上奏请求增兵',5,'符彦卿奏请益兵，','符彦卿奏请益兵，',[('符彦卿','上奏请求增派兵力')],when='954年五月癸巳增援命令以前',place='忻州军前',note='请求与下一句增派三千兵分别记录。')
add('li_zhang_sent_reinforcements','柴荣派李筠、张永德率三千兵援助符彦卿',5,'癸巳，','将兵三千赴之。',[('帝','增派三千兵力'),('李筠','与张永德率援军出发'),('张永德','与李筠率援军出发')],when='954年五月癸巳',place='忻州',note='李筠复用原名李荣、后来避柴荣讳的已核主体，与晚唐同名人及946年档案分开。')
add('fu_deploys_against_raiding_cavalry','契丹游骑屡至忻州城下，符彦卿率诸将列阵待敌',5,'契丹游骑时至','陈以待之。',[('符彦卿','列阵迎战前来袭扰的契丹骑兵')],when='954年五月丙申',place='忻州城下')
add('shi_li_initial_success_xinkou','史彦超率二十骑先战，李筠率军接应，史书记合击杀契丹二千人',5,'史彦超将二十骑','杀契丹二千人。',[('史彦超','率二十骑为先锋接敌'),('李筠','率兵接应先锋')],when='954年五月丙申忻州迎战',place='忻州、忻口一带',note='二千为史书记述战果，包含李筠后续兵力，不写成二十骑单独杀二千人。')
add('shi_yanchao_killed_xinkou','史彦超冒进远离主力，寡不敌众被杀，李筠仅身逃免',5,'彦超恃勇轻进，','周兵死伤甚众。',[('史彦超','远离主力，战死于契丹军'),('李筠','失利后仅身逃免')],when='954年五月丙申交战中',place='忻州、忻口一带',note='先前局部战果与随后失利分开，周军伤亡未给具体人数；不把李筠写成获胜后全军安全回营。')
sup('shi_yanchao_killed_xinkou',5,shishi,'周兵圍漢太原，契丹救漢，出忻、代。世宗遣符彥卿拒之，以彥超為先鋒，戰忻口，彥超勇憤俱發，左右馳擊，解而復合者數四，遂歿于陣。','《新五代史》史彦超传也记其任先锋、在忻口反复驰击后战死。','传记无独立日，按主书纪日保留；不把数四交合当四个已知日期。')
sup('shi_yanchao_killed_xinkou',5,new,'符彥卿及契丹戰于忻口，敗績，先鋒都指揮使史彥超死之。','《新五代史》本纪记符彦卿在忻口败于契丹，史彦超战死。','五月丁酉接续本纪记载与《通鉴》丙申交战叙述有日差，分别保留，不覆盖主书。',relation='conflicts')
claim('person',people['史彦超（后周将领）'],'death_year','后周将领史彦超在954年五月与契丹军交战时战死。',5,span(5,'彦超恃勇轻进，','为契丹所杀，'),'复用后周史彦超，与其他同名将领分开；死亡年明确，具体纪日异说保留。')
add('fu_retires_to_jinyang','符彦卿退守忻州，随后率军回晋阳',5,'彦卿退保忻州，','寻引兵还晋阳。',[('符彦卿','退守忻州后返回晋阳')],when='954年五月忻口失利之后',place='忻州至晋阳')
add('zhe_deyi_brings_prefecture_troops','折德扆率府州兵前来朝见柴荣',5,'府州防御使折德扆','将州兵来朝。',[('折德扆','率府州兵前来朝见')],when='954年五月辛丑设军以前',place='府州至后周行在')
add('yongan_restored_zhe_appointed','柴荣恢复府州永安军，任折德扆为节度使',5,'辛丑，','以德扆为节度使。',[('帝','恢复府州军号并任命节度使'),('折德扆','获任永安军节度使')],when='954年五月辛丑',place='府州')
sup('yongan_restored_zhe_appointed',5,old,'辛丑，升府州為節鎮，以永安軍為軍額，以本州防禦使折德扆為節度使。','《旧五代史》同记五月辛丑府州升节镇、军额永安、折德扆任节度使。','主书说复置，旧本纪说升节镇，两种表述并列，不据旧史省略断言此军号前所未有。')
sup('yongan_restored_zhe_appointed',5,zhe,'廣順間，周世宗建府州為永安軍，以德扆為節度使，','《宋史》折德扆传也记周世宗建府州永安军并任其节度使，但写作广顺间。','广顺为郭威年号，与同句周世宗及主书显德元年五月有不合；保留原字并注明疑年，不因此把当前任命改到951—953年。',relation='conflicts',field='time_original')
add('zhou_mobilizes_labor_but_fails','后周从怀孟至蒲陕大量征兵征夫，攻晋阳未下',5,'时大发兵夫，','以攻晋阳，不克。',[('帝','征发兵夫攻晋阳，未能攻下')],when='954年五月围晋阳期间',place='怀、孟至蒲、陕及晋阳',note='底本薄疑为蒲，结合旧史蒲陜并列，展示按蒲；原文薄字保留不改。')
sup('zhou_mobilizes_labor_but_fails',5,labor,'時大集兵賦，及征山東、懷、孟、蒲、陜丁夫數萬，急攻其城，旦夕之間，期於必取。','《旧五代史》记征山东、怀孟蒲陕数万丁夫攻太原。','该句在六月撤军条回述围城征发，未把全部征发定在六月朔；数万丁夫不当作精确战斗兵力。',relation='adds')
add('chairong_discusses_withdrawal','久雨使周军疲病，史彦超战死后，柴荣方面商议撤军',5,'会久雨，',None,[('帝','在围城受挫后商议撤军')],when='954年五月忻口失利后、六月撤军以前',place='晋阳城下',note='此处是议引还，实际撤离日期与后续行军留给下一段，不提前当作已经离开。')
sup('chairong_discusses_withdrawal',5,labor,'會大雨時行，軍士勞苦，復以忻口之師不振，帝遂決旋師之意。','《旧五代史》也以雨、军士劳苦和忻口失利说明柴荣决定撤军。','旧本纪在六月撤军条中概述缘由，实际撤军与此议论分开。')
reviews={1:'王逵请求后实际迁府与两项任职分开，稳定复用周行逢和潘叔嗣。',2:'杨衮怀疑与加害企图、郑拒绝和杀骑、杨被囚、郑降城与授职逐项分录。旧史戊寅安彦进实际处刑另补，不把上月被俘等同死亡。卷首太祖误题不参与识别，帝为柴荣。',3:'契丹实际屯兵与主书万余出军令分开，旧史额外将领挂同一事件，有对应参与引用；不建无证私人盟友关系。',4:'宁化军辖区按史载；桑珪和解文遇所奏通敌被主书定为诬告，未当事实。新史以防御使称郑及省略先降周过程，与主书详文并列。',5:'二十先锋骑与李筠援兵共同的战果不混成二十骑杀二千；战果与随后败亡分阶段，伤亡未造精数。新本纪丁酉与主书丙申日差保留；折德扆任职广顺疑年另列，薄与蒲原字分别保留。'}
assert not (P/'publication.json').exists()
for n in range(1,6):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=954,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,6)],next_paragraph=Q[6]['id'],next_volume=292,next_year=954,supplements=supplements,excluded_non_body=[dict(source_line=i,reason='卷年题名或结构项，已在boundaries.json核验；不作为史事') for i in range(1,6)],coverage='卷292原6—10行连续五段；原1—5行卷年结构不录为史事，原文快照还含未处理后续段落，不代表全片段已完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,6)],source_issues_review='卷首太祖题名疑误，不把954年帝识别成郭威。史彦超战死纪日、宋史折德扆广顺疑年、原薄与旧史蒲字差分别保留。纸本及异文待核。',plain_language_review='首次逐条检查标题、人物、角色、时间与事实说明，明确怀疑、诬告、囚禁、处刑、局部战果及后续失利的不同含义；请求与执行、商议与撤军分开，摘录保持底本原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
