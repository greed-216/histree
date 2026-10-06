# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 954 paragraphs 36–38."""
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
COMMIT='cdbcdc30bc009005cdae849020ae9c421da992f5'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-114-april-supply-954','xinwudaishi-12-chairong-accession','jiuwudaishi-109-li-shouzhen-death']:
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
main_sources = ['tongjian-291-954-april-submissions']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0954-p036-p038',
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
lines = (ROOT / 'resources/derived/tongjian/291.txt').read_text().splitlines()
for n in range(36, 39):
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
        citation = f'卷291·显德元年（954年四月及史论所含追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0954_06_{len(B["claims"])+1:04d}'
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
    key = 'event_zztj_291_0954_' + code
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
        edge = 'participation_zztj_291_0954_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0954_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'柴荣','太祖':'郭威','符氏':'符氏（柴荣宣懿皇后）','郭言':'郭言（北汉岚州刺史）'})
NEW_ALIASES={'韩光愿':['韓光願'],'郭言（北汉岚州刺史）':[],'符氏（柴荣宣懿皇后）':[],'李崇训':['李崇訓'],'安彦进':['安彥進'],'李廷诲':['李廷誨'],'李勍':[],'赵皋':['趙皋','趙臯'],'杨耨姑':['楊耨姑']}
NEW_DESCRIPTIONS={'韩光愿':'太原人，北汉宪州刺史。954年四月符彦卿奏报他与岚州刺史郭言均举城向后周投降。生卒年未载。','郭言（北汉岚州刺史）':'北汉岚州刺史。954年四月举城向后周投降，由符彦卿奏报。与朱全忠属将、893年战死的晚唐郭言不同，分别建档。生卒年未载。','符氏（柴荣宣懿皇后）':'符彦卿之女、符存审之孙女，先嫁李守贞之子李崇训。河中城陷时躲过丈夫的杀害，郭威将她送回父亲处；后嫁柴荣，954年四月被立为皇后。与柴荣后来所立符氏皇后区分；生卒年待后续相应史料校核。','李崇训':'李守贞之子，符氏的前夫。《通鉴》及《旧五代史》符后传记他在河中城陷时杀弟妹，寻找妻子未果后自杀。与949年自焚名单中的李崇勋姓名和死法有差异，同人关系未证，暂不合并。','安彦进':'北汉石州刺史。954年四月后周王彦超、韩通攻克石州时被俘。生卒年未载。','李廷诲':'北汉沁州刺史。954年四月癸亥举城归降后周。生卒年未载。','李勍':'北汉忻州监军。954年四月癸酉杀死刺史赵皋及契丹通事杨耨姑，以城归降后周，获任忻州刺史。生卒年未载。','赵皋':'北汉忻州刺史。954年四月癸酉被监军李勍杀死。生年未载。','杨耨姑':'契丹通事。954年四月癸酉与北汉忻州刺史赵皋一同被李勍杀死。《旧五代史》称他为契丹大将，保留两书职务称谓。生年未载。'}
NEW_DEATH_YEARS={'李崇训':949,'赵皋':954,'杨耨姑':954}
old='jiuwudaishi-114-april-supply-954';new='xinwudaishi-12-chairong-accession';fu='jiuwudaishi-121-first-fu-empress';hezhong='jiuwudaishi-109-li-shouzhen-death'
add('han_guangyuan_submits_xianzhou','符彦卿奏报韩光愿以宪州投降后周',36,'辛酉，','皆举城降。',[('符彦卿','奏报宪岚二州归降'),('韩光愿','以宪州举城投降')],when='954年四月辛酉奏报，实际归降日未载',place='宪州',note='辛酉是奏报日，不直接定为韩光愿实际交城日。')
add('guoyan_submits_lanzhou','符彦卿奏报岚州刺史郭言以城投降后周',36,'辛酉，','皆举城降。',[('符彦卿','奏报岚州归降'),('郭言','以岚州举城投降')],when='954年四月辛酉奏报，实际归降日未载',place='岚州',note='此人是北汉岚州刺史，不复用893年已战死的朱全忠部将郭言。')
sup('guoyan_submits_lanzhou',36,old,'辛酉，符彥卿奏，嵐、憲二州歸順。','《旧五代史》同记辛酉符彦卿奏报岚、宪二州归顺。','旧本纪未点刺史姓名，只印证二州归降及奏报日。')
add('fu_marries_li_chongxun','符彦卿之女此前嫁给李守贞之子李崇训',36,'初，符彦卿有女','之子崇训，',[('符氏','嫁给李崇训'),('符彦卿','女儿嫁给李守贞之子'),('李守贞','儿子与符彦卿之女成婚'),('李崇训','娶符彦卿之女')],year=None,when='949年河中城陷以前，具体婚期未载',place='未载',note='初是回述，婚事不发生于954年立后当天。')
claim('person',people['李守贞'],'description','《通鉴》说相者预言儿媳将成为皇后，李守贞因此更坚定了反叛意图。',36,span(36,'相者言其贵当为天下母。','反意遂决。'),'这是史书对李守贞决意反叛的解释，不把相者预言当作超自然事实；已有948年叛事不重建为954年行动。')
add('li_chongxun_kills_siblings','河中城陷时，李崇训先杀弟妹，继而寻找符氏准备杀她',36,'及败，崇训先','次及符氏；',[('李崇训','杀害弟妹并准备杀妻'),('符氏','面临丈夫的杀害')],year=949,when='949年七月河中城陷时，954年本条回述',place='河中',note='城陷年由已录949年七月主线及旧史乾祐二年七月校核；符氏被杀是企图而未遂。')
sup('li_chongxun_kills_siblings',36,hezhong,'二年七月，城陷，','《旧五代史》李守贞传把河中城陷记在后汉乾祐二年七月。','结合同传与已发布949年主线确定背景年月；不把李崇勋自焚名单直接合并为本条李崇训。',relation='adds',field='time_original')
add('fu_hides_li_chongxun_suicide','符氏藏在帷幕后逃过杀害，李崇训未找到她便自杀',36,'符氏匿帏下，','遂自刭。',[('符氏','躲藏逃过丈夫的杀害'),('李崇训','寻找妻子未果后自杀')],year=949,when='949年七月河中城陷时的回述',place='河中',note='主书自刭与旧批李崇勋自焚有差异，身份未证前分别保留。')
sup('fu_hides_li_chongxun_suicide',36,fu,'崇訓自刃其弟妹，次將及後，後時匿於屏處，以帷箔自蔽，崇訓倉黃求後不及，遂自刎，後因獲免。','《旧五代史》符后传同记李崇训杀弟妹、符氏躲藏、李崇训自刎，符氏获免。','名称与自刎叙述印证本条，但不据此消除早前主书李崇勋自焚的差异。')
add('fu_warns_disordered_troops','符氏坐堂上斥责乱兵，称父亲与郭威如兄弟，要求勿失礼',36,'乱兵既入，','汝曹勿无礼！”',[('符氏','斥责入城乱兵并援引父亲与郭威的交情')],year=949,when='949年七月河中城陷后',place='河中',note='昆弟是符氏在情急时的说法，只记录她所称交情，不直接建立郭威与符彦卿的血缘或结义关系。')
add('guowei_returns_fu_to_father','郭威派人将符氏送回符彦卿处',36,'太祖遣使归之', '于彦卿。',[('太祖','派人送符氏回父亲处'),('符氏','被送回符彦卿处'),('符彦卿','女儿获送还')],year=949,when='949年河中城陷、符氏获免以后',place='河中至符彦卿处',note='此处太祖是郭威，时为后汉统兵大臣，庙号是后世称呼。')
sup('guowei_returns_fu_to_father',36,fu,'太祖入河中，令人訪而得之，即遣女使送於其父，','《旧五代史》补记郭威入河中后找到符氏，派女使送她到父亲处。','女使未具姓名，不补人物；太祖指郭威。',relation='adds')
add('fu_recognizes_guowei_fosterfather','符氏感念郭威救助，拜他为养父',36,'自是後常感太祖大惠，','拜太祖為養父。',[('符氏','拜郭威为养父'),('郭威','被符氏拜为养父')],year=None,when='949年获救以后，具体认养日期未载',place='未载',source=fu,note='此关系是旧史明记的认养，不据她称父与郭为昆弟反推。')
add('fu_marries_chairong','柴荣镇守澶州时，郭威为他娶符氏',36,'及帝镇澶州，','太祖为帝娶之。',[('帝','在镇澶州期间娶符氏'),('太祖','为柴荣安排婚事'),('符氏','嫁给柴荣')],year=None,when='符氏949年获救以后、954年立后以前，柴荣镇澶州期间',place='澶州',note='此处帝指柴荣，太祖指郭威；婚期未载，不以立后日替代成婚日。')
add('fu_made_empress','柴荣立符氏为皇后',36,'壬戌，','立为皇后。',[('帝','立符氏为皇后'),('符氏','被立为后周皇后')],when='954年四月壬戌',place='后周')
sup('fu_made_empress',36,old,'壬戌，制立衛國夫人符氏為皇后，仍令有司擇日備禮冊命。','《旧五代史》同记壬戌下制立卫国夫人符氏为皇后，并命择日备礼册命。','制书立后与另择日期正式册命分开，未把完整册礼认定已在壬戌完成。',relation='adds')
claim('person',people['符氏（柴荣宣懿皇后）'],'evaluation','《通鉴》称符皇后性情温和、仁厚又明断，柴荣很重视她。',36,'后性和惠而明决，帝甚重之。','保留史书评价，不据此补具体未载的政治行动。')
relationship('符彦卿','符氏','父亲',36,'符彦卿有女适李守贞之子崇训，','原文明称符氏是符彦卿之女，方向为父亲到女儿。')
relationship('李守贞','李崇训','父亲',36,'李守贞之子崇训，','只按崇训姓名建立父子，不合并崇勋。')
relationship('符氏','李崇训','妻子',36,'符彦卿有女适李守贞之子崇训，','先前婚姻终止于李崇训死亡，非954年仍同时为两人之妻。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='949年李崇训死亡以前，符氏是李崇训的妻子。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
relationship('符氏','柴荣','妻子',36,'及帝镇澶州，太祖为帝娶之。','符氏获救后改嫁柴荣，帝在此指柴荣。')
relationship('郭威','符氏','养父',36,'拜太祖為養父。','原文明称拜郭威为养父，不转为血缘父亲。',source=fu)
relationship('符存审','符氏','祖父',36,'宣懿皇后符氏，祖存審，','原文明称符存审是符氏祖父，不把符彦卿与符存审的代际颠倒。',source=fu)
add('wang_han_capture_shizhou','王彦超、韩通攻克石州，俘获刺史安彦进',37,'王彦超、韩通','执刺史安彦进。',[('王彦超','与韩通攻克石州'),('韩通','与王彦超攻克石州'),('安彦进','在石州被俘')],when='954年四月癸亥前的记载，具体交城日未载',place='石州',note='被俘与被杀分开，本段没有说安彦进被杀。')
sup('wang_han_capture_shizhou',37,old,'王彥超奏，收下石州，獲偽刺史安彥進。','《旧五代史》记王彦超奏报攻下石州、俘安彦进，列在壬戌之后。','奏報所载日期与实际攻克日不同，未直接把战斗固定在奏报日。')
add('li_tinghui_submits_qinzhou','沁州刺史李廷诲向后周投降',37,'癸亥，','沁州刺史李廷诲降。',[('李廷诲','向后周归降')],when='954年四月癸亥',place='沁州')
sup('li_tinghui_submits_qinzhou',37,old,'癸亥，偽沁州刺史李廷誨以城歸順。','《旧五代史》同日记李廷诲以沁州归顺。','誨与诲为繁简对应，复用同一主体。')
add('chairong_leaves_luzhou_for_jinyang','柴荣离开潞州，向晋阳进军',37,'庚午，','趣晋阳。',[('帝','离开潞州北进晋阳')],when='954年四月庚午',place='潞州至晋阳')
sup('chairong_leaves_luzhou_for_jinyang',37,old,'是日，車駕發潞州，親征劉崇。','《旧五代史》同记庚午车驾发潞州，亲征刘崇。','原文是离开潞州，未在此句说已到太原。')
add('li_qing_kills_xinzhou_officials','忻州监军李勍杀死赵皋和杨耨姑',37,'癸酉，','及契丹通事杨耨姑，',[('李勍','杀害赵皋和杨耨姑'),('赵皋','被李勍杀死'),('杨耨姑','被李勍杀死')],when='954年四月癸酉',place='忻州')
sup('li_qing_kills_xinzhou_officials',37,old,'癸酉，忻州偽監軍李殺刺史趙臯及契丹大將楊耨姑，以州城歸順。','《旧五代史》同日记忻州监军杀赵皋、杨耨姑后以城归顺；杨耨姑称契丹大将。','电子本文字李之后缺名，原文不补；主书李勍及通事职名另存，不把两职强行统一。',relation='adds')
add('li_qing_submits_xinzhou','李勍以忻州向后周投降',37,'举城降。','举城降。',[('李勍','以忻州归降后周')],when='954年四月癸酉',place='忻州')
sup('li_qing_submits_xinzhou',37,new,'忻州監軍李勍殺其刺史趙皋，叛于漢來附。','《新五代史》也记李勍杀赵皋后以忻州归附。','新史在四月段落中记此事，但本句未单列癸酉；不把汉误作已亡后汉朝廷。')
add('li_qing_appointed_xinzhou','柴荣任李勍为忻州刺史',37,'以勍',None,[('帝','任李勍为刺史'),('李勍','归降后获任忻州刺史')],when='954年四月癸酉归降记载后，具体任命日未另列',place='忻州')
add('wangkui_requests_langzhou_seat','王逵上表请求把使府治所迁回朗州',38,'王逵表请',None,[('王逵','请求迁回朗州治府')],when='954年四月卷末所记请求，具体日未载',place='使府至朗州',note='此处只记上表请求；卷292五月甲戌另记实际迁移，未把请求当作已经执行。')
reviews={36:'宪岚二州用辛酉奏报，不当实际投降日。岚州郭言区别于893年已死郭言；崇训与崇勋不强合。符氏河中旧事校回949，婚姻与认养日期未知，立后制书与正式册礼分开。所谓昆弟保存为她的说辞，未建血亲或结义。',37:'被俘安彦进不录被杀。李廷诲繁简对应，旧本纪李之后缺字不补原文；杨耨姑通事与大将称谓并列，归降与刺史任命分开。',38:'王逵上表为请求，下一卷另记执行，不提前完成迁移。卷末两空行属非正文，下一段接卷292五月。'}
assert not (P/'publication.json').exists()
for n in range(36,39):
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=954,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(36,39)],next_paragraph='zztj-v292-y0954-p001',next_volume=292,next_year=954,supplements=supplements,excluded_non_body=[],coverage='卷291原116—118行最后三段；卷末空行排除，954年仍须卷292全部25段。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(36,39)],source_issues_review='岚州郭言与晚唐郭言分开，李崇训与李崇勋身份待核，旧本纪忻州监军缺名不补，杨耨姑职称差别并列。旧符后传后续死亡纪年须在后续时间段另校，不提前按单一纪年录入。纸本待核。',plain_language_review='首次逐条检查标题、人物、角色、关系方向、婚姻时段、日期及事实说明；追述与本年行动分开，请求与执行分开，摘录保留原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
