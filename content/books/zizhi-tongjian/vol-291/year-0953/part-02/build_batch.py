# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 952 paragraphs 11–20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,47))
COMMIT='0712155a855a3f88decd328f54992920391e363e'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-291-953-january-intercalary']:
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
main_sources = ['tongjian-291-953-january-intercalary','tongjian-291-953-hunan-conflict','tongjian-291-953-february-march']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0953-p011-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-953-january-intercalary':'卷291·广顺三年正月至闰正月','tongjian-291-953-hunan-conflict':'卷291·广顺三年湖南将领冲突回述','tongjian-291-953-february-march':'卷291·广顺三年二月至五月','jiuwudaishi-112-february-953':'卷112·太祖本纪三·广顺三年二月','jiuwudaishi-130-wangjun-dismissal':'卷130·王峻传','xinwudaishi-50-wangjun-dismissal':'卷50·杂传第三十八·王峻','xinwudaishi-66-he-zhu-killed':'卷66·楚世家第六·刘言'}
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
for n in range(11, 21):
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
    labels={'tongjian-291-953-january-intercalary':'卷291·广顺三年正月至闰正月','tongjian-291-953-hunan-conflict':'卷291·广顺三年湖南将领冲突回述','tongjian-291-953-february-march':'卷291·广顺三年二月至五月','jiuwudaishi-112-february-953':'卷112·太祖本纪三·广顺三年二月','jiuwudaishi-130-wangjun-dismissal':'卷130·王峻传','xinwudaishi-50-wangjun-dismissal':'卷50·杂传第三十八·王峻','xinwudaishi-66-he-zhu-killed':'卷66·楚世家第六·刘言'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·广顺三年（953年闰正月至三月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0953_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=953, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='953年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0953_' + code
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
        edge = 'participation_zztj_291_0953_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0953_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','荣':'柴荣','折从阮':'折从远','全琇':'朱全琇','硃全琇':'朱全琇','敬真':'何敬真','王殷':'王殷（后汉后周将）','承诲':'王承诲','张图':'张匡图'})
NEW_ALIASES={'李仲迁':['李仲遷'],'符会':['符會'],'王承诲':['王承誨'],'张怀贞':['張懷貞'],'张匡图':['張匡圖','张图','張圖'],'蒋光远':['蔣光遠']}
NEW_DESCRIPTIONS={'李仲迁':'朗州指挥使。所部三千人长期驻潭州，953年何敬真命其先赴岭北，部将符会等劫持他并擅自返回朗州。生卒年未载。','符会':'李仲迁部下都头。953年利用士卒想归乡的情绪，劫持李仲迁擅自回朗州。后刘言在收到王逵诛杀何敬真的通知后处死符会等。生年未载。','王承诲':'后汉后周将领王殷之子，任尚食使。953年王峻被贬后，郭威派他前往父亲所在的邺都，解释王峻获罪的情况。生卒年未载。','张怀贞':'后周供奉官。953年奉命率禁军两指挥驻鄜州、延州，以控制高绍基所在军府。生卒年未载。','张匡图':'雄武军副使。953年高绍基在朝廷调兵压力下把军府事务交给他。《旧五代史》同一交接记作张图，结合同日背景与副使身份保留别名，不与张图英混同。生卒年未载。','蒋光远':'后周供奉官。《旧五代史》王峻传记953年受命押送被贬的王峻赴商州。生卒年未载。'}
NEW_DEATH_YEARS={'符会':953}
oldfeb='jiuwudaishi-112-february-953';oldwang='jiuwudaishi-130-wangjun-dismissal';newwang='xinwudaishi-50-wangjun-dismissal';newliu='xinwudaishi-66-he-zhu-killed'
add('zhe_reports_twentyone_groups','折从阮奏报使野鸡族二十一个部落归附',11,'戊申，',None,[('折从阮','奏报二十一个部落归附')],when='953年闰正月戊申奏报',place='静难军、庆州',note='二十一族为原书部落计数，不能写成二十一名首领或二十一户；奏报日不等同各部落同时归附日。')
add('shao_tang_warns_southward_threat','邵棠向李璟进言，担心后周南征，建议南唐准备防御',12,'唐草泽邵棠上言：',None,[('邵棠','以民间人士身份报告所闻并建议防御')],when='953年闰正月条下，具体上言日未载',place='南唐、淮上',note='周主恭俭是邵棠所闻，南征是其忧虑，不写成郭威已下南征命令；草泽为未仕身份，不当作地点名。')
for code,name,office,start,end in [
 ('he_jingzhen_deputy_after_tan','何敬真','静江节度副使','以指挥使何敬真','为静江节度副使，'),
 ('zhu_quanxiu_deputy_after_tan','硃全琇','武安节度副使','硃全琇为','武安节度副使，'),
 ('zhang_wenbiao_deputy_after_tan','张文表','武平节度副使','张文表为','武平节度副使，'),
 ('zhou_sima_after_tan','周行逢','武安行军司马','周行逢为','武安行军司马。')]:
 add(code,f'王逵攻下潭州后，任命{ALIASES.get(name,name)}为{office}',13,start,end,[('王逵','任命部将为'+office),(name,'受王逵任命为'+office)],year=None,when='952年攻下潭州后、953年正式授职前的回述，具体授任日未载',place='潭州',note='这段记录王逵在湖南的安排，与后周随后正式授职分开；旧任职阶段不覆盖已有朝廷授职。')
add('he_zhu_split_command','何敬真与朱全琇各设亲兵，与王逵分厅办事，吏民无所适从',13,'敬真、全琇各置牙兵，','吏民莫知所从。',[('敬真','自设亲兵，与王逵分厅办事'),('全琇','自设亲兵，与王逵分厅办事'),('王逵','与两将分别处理军府事务')],year=None,when='952年湖南收复后至953年冲突前的回述',place='潭州',note='牙兵为亲兵，不补各方兵数；无所适从为史书描述，未外推为所有命令都未执行。')
add('wang_favors_zhou_zhang','宴会中诸将酒后失礼，周行逢与张文表仍尽礼，王逵亲近两人',13,'每宴集，','逵亲爱之。',[('周行逢','在诸将宴集时对王逵尽礼'),('张文表','在诸将宴集时对王逵尽礼'),('王逵','亲近守礼的两将')],year=None,when='湖南军府将领冲突以前的一段时期概述',place='潭州',note='亲爱为政治亲近，不据此新建血亲或恋爱关系。')
add('he_returns_lang_plots','何敬真与王逵不和，回朗州后也难以事奉刘言，与朱全琇谋划作乱',13,'敬真与逵不协，','与全琇谋作乱。',[('敬真','离开王逵回朗州，并与朱全琇谋划'),('全琇','与何敬真共同谋划')],year=None,when='953年二月被杀前的回述，具体返回与谋划日未载',place='潭州至朗州',note='谋作乱为史书记述的谋划，未将后续被捕写成已经成功反叛。')
add('liuyan_suspects_wang','刘言忌惮王逵势力，疑其派何敬真监视自己，准备讨伐；王逵闻讯害怕',13,'言素忌逵之强，','逵闻之，甚惧。',[('刘言','怀疑何敬真替王逵监视自己，准备讨伐'),('王逵','听到刘言准备讨伐的消息后害怕')],year=None,when='953年二月何敬真被杀前的回述',place='朗州、潭州',note='疑为刘言的怀疑，不认定王逵确实已下监视命令；将讨为准备而非已交战。')
add('zhou_advises_removing_he_zhu','周行逢建议王逵先对付刘言、何敬真等，王逵表示赞同',13,'行逢曰：','夫复何忧！”',[('周行逢','劝王逵尽早处理与刘言、何敬真、朱全琇的冲突'),('王逵','赞同共同排除对手、控制潭朗的主张')],year=None,when='953年二月处决前的谋划',place='潭州',note='凶党为王逵对对手的称呼，不当本站定性；此时仍是主张与赞同。')
add('southern_han_invades_three_prefectures','南汉进犯全州、道州与永州',13,'会南汉寇全、道、永州，','会南汉寇全、道、永州，',[],when='953年初湖南将领冲突期间，具体进犯日未载',place='全州、道州、永州',note='主书未具名该次统兵将领，不自动填为潘崇彻。')
add('zhou_plans_trap','周行逢提出去朗州劝刘言派何敬真、朱全琇南征，再在长沙设局；王逵同意',13,'行逢请：','逵从之。',[('周行逢','提出借南征机会把两将引到长沙的计策'),('王逵','采纳计策')],when='953年初南汉进犯三州后',place='潭州、朗州',note='俟至长沙以计取之为计划，实际逮捕另录。')
add('liuyan_sends_he_zhu_south','周行逢到朗州后，刘言命何敬真为招讨使、朱全琇为先锋，带百余亲兵赴潭州会军',13,'行逢至朗州，','以御南汉。',[('周行逢','到朗州劝刘言部署两将南征'),('刘言','任命何敬真与朱全琇率亲兵会潭州军'),('敬真','获任南面行营招讨使'),('全琇','获任先锋使')],when='953年初，二月辛亥处决前',place='朗州至潭州',note='百余牙兵为两将赴会所带亲兵，不当作全部对南汉军队规模。')
add('wang_delays_he_at_banquets','王逵迎接两将，在长沙连日宴饮并以美女引诱，何敬真滞留不进军',13,'二人至长沙，','敬真因淹留不进。',[('王逵','以宴饮和美女使两将留在长沙'),('敬真','因宴饮滞留，未继续进军'),('全琇','与何敬真到长沙并受宴迎')],when='953年初两将赴长沙以后',place='长沙',note='使人滞留的行动据原文保留，不编具体女子姓名或未载身体行为。')
add('he_orders_li_zhongqian_forward','何敬真命长期驻潭州的李仲迁所部三千人先赴岭北',13,'朗州指挥使李仲迁','趣岭北，',[('李仲迁','率三千驻军受命先赴岭北'),('敬真','令李仲迁先行')],when='953年初何敬真在潭州滞留时',place='潭州至岭北')
add('fu_hui_seizes_li_returns','符会等利用士卒思乡，劫持李仲迁，擅自返回朗州',13,'都头符会等','擅还朗州。',[('符会','趁士卒想归乡劫持李仲迁并擅自回朗州'),('李仲迁','被所属都头劫持')],when='953年初李仲迁所部奉命先行后',place='潭州至朗州',note='擅还为未经授权返回，不推断李仲迁已被杀。')
add('wang_imprisons_he_by_false_envoy','王逵趁何敬真醉酒，假冒刘言使者传命，把何敬真关入监狱',13,'逵乘敬真醉，','因收系狱。',[('王逵','派人冒充刘言使者拘捕何敬真'),('敬真','被伪传命令拘禁')],when='953年二月辛亥处决以前',place='长沙',note='太师命械公归是伪使所传，不写成刘言确实已命逮捕；荒宴怠战指控与实际设局分开。')
add('zhu_flees_is_pursued','朱全琇逃走，王逵派兵追捕',13,'全琇逃去，','遣兵追捕之。',[('全琇','逃走后被追捕'),('王逵','派兵追捕朱全琇')],when='953年二月何敬真被处决前后，具体逃走日未载',place='长沙及追捕途中')
add('wang_executes_he','王逵处死何敬真，以警告军众',13,'二月，辛亥朔，','斩敬真以徇。',[('王逵','处死何敬真并示众警告'),('敬真','被王逵处死')],when='953年二月辛亥朔',place='长沙')
sup('wang_executes_he',13,oldfeb,'己巳，朗州劉言奏，當道先遣行軍司馬何敬貞率兵掩擊廣賊，行及潭州，部眾奔潰，湖南王進逵以敬貞失律，已梟首訖。','《旧五代史》二月己巳记刘言奏报何敬贞所部溃散，王进逵以失律罪名将其处死。','己巳为奏报，已梟首表明此前执行；失律为奏报解释，与主书设局冒使叙述并列，不当唯一完整原因。',relation='adds')
add('wang_executes_zhu_party','不久王逵捕获朱全琇及十余名同党，将他们全部处死',13,'未几，获全琇',None,[('王逵','捕获并处死朱全琇等'),('全琇','逃走后被捕处死')],when='953年二月何敬真被处决后不久，具体日未载',place='湖南',note='其党十余为朱全琇以外同党规模，未据此认定总数固定为十人或推定各人身份。')
sup('wang_executes_zhu_party',13,newliu,'言信之，遣景真、全琇往，至皆見殺，','《新五代史》也记刘言派何景真、朱全琇赴会后，两人被杀。','该书将两人遇害概括在一起，主书区分何先被斩、朱逃后被捕；不据概述说二人同日处决。')
add('rong_returns_chanzhou','柴荣从朝廷返回澶州',14,'癸丑，',None,[('荣','以镇宁节度使身份返回澶州')],when='953年二月癸丑',place='后周朝廷至澶州')
add('zhou_makes_two_jade_seals','后周另以玉制作两枚国宝，主书追述此前晋国宝已被契丹带走',15,'初，契丹主德光北还，',None,[],when='953年二月条下，新宝制作日未载',place='后周朝廷',note='前半为契丹947年北还的回述，不把旧宝带走归入953年；旧纪说明新宝名称，不强认其为秦代原玺。')
sup('zhou_makes_two_jade_seals',15,oldfeb,'內制國寶兩座，詔中書令馮道書寶文，其一以「皇帝承天受命之寶」為文，其一以「皇帝神寶」為文。','《旧五代史》说明两枚新宝的文字分别为皇帝承天受命之宝、皇帝神宝，并命冯道书写。','该书未给此事单独纪日，不将前面的癸丑或后面的庚申默认作为制作日。',relation='adds')
E['feng_writes_seals']=event('feng_writes_seals','后周命冯道书写两枚新国宝的文字',15,'內制國寶兩座，詔中書令馮道書寶文，',[('冯道','以中书令身份奉命书写新宝文字')],when='953年二月条下，《旧五代史》未给单独日',place='后周朝廷',source=oldfeb,note='书宝文为奉命书写印文，不擅自说冯道亲手雕琢玉材。')
add('wang_reports_he_execution','王逵派使向刘言告知何敬真已被处死',16,'王逵遣使以斩何敬真','告刘言，',[('王逵','派使通知刘言何敬真被斩'),('刘言','收到王逵通知')],when='953年二月何敬真被处死后',place='潭州至朗州')
add('liuyan_executes_fu_hui','刘言处死符会等数人，史书称他不得已作此处置',16,'言不得己，',None,[('刘言','处死擅返朗州的符会等'),('符会','被刘言处死')],when='953年二月庚申',place='朗州',note='不得己原字疑为不得已，展示依上下文解释为被迫；数人并非给出全部名单，不把此前李仲迁列入被杀者。')
add('wang_jun_demands_chancellor_changes','王峻要求颜衎、陈观取代范质、李谷为相，郭威表示需要考虑',17,'枢密使、平卢节度使、同平章事王峻，','俟朕更思之。”',[('王峻','提出更换两名宰相'),('颜衎','被王峻推荐为宰相人选'),('陈观','被王峻推荐为宰相人选'),('范质','被王峻要求撤换'),('李谷','被王峻要求撤换'),('帝','表示宰辅进退须慎重考虑')],when='953年二月寒食假期间',place='后周朝廷',note='奏请与已任命区别明确，不记录颜衎陈观在此已升宰相。')
sup('wang_jun_demands_chancellor_changes',17,oldwang,'又奏請以顏愆、陳觀代範質、李穀為相。','《旧五代史》也记替换宰相的请求，颜衎在该电子本写作颜愆。','保存颜衎与颜愆写法差异，未据疑字另建人；原文范质作範质同样保留。',relation='adds')
sup('wang_jun_demands_chancellor_changes',17,newwang,'又請用頻衎、陳同代李穀、范質為相，','《新五代史》同一请求在人选处写作频衎、陈同，与主书颜衎、陈观有差别。','同一更相事件的异文并列，频字及陈同是否底本讹误仍待校核，未将二者当新宰相实体，也未自动当作别名。',relation='conflicts')
add('guo_defers_until_after_holiday','王峻不断争论，郭威到中午仍未进食，遂说寒食假结束后再办，王峻才退下',17,'峻力论列，',None,[('王峻','不断争论，待郭威表示假后办理才退下'),('帝','以寒食假后办理暂缓争论')],when='953年二月寒食假期间',place='后周朝廷',note='如卿所奏为当时回应，后续拘禁说明没有按此落实更相，不能提前记执行。')
add('guo_detains_wang_jun','郭威秘密召宰相与枢密使入宫，将王峻拘禁在别处',18,'癸亥，','幽峻于别所。',[('帝','召大臣入宫并拘禁王峻'),('王峻','被拘禁')],when='953年二月癸亥',place='后周宫廷')
add('guo_explains_wang_jun_offense','郭威向冯道等哭诉王峻逼逐大臣、阻隔柴荣入朝，且不断求权',18,'帝见冯道等，','谁则堪之！”',[('帝','向大臣陈述拘禁王峻的理由'),('冯道','听取郭威对王峻的指责')],when='953年二月癸亥拘禁王峻后',place='后周宫廷',note='这是郭威的当时陈述，不将全部指责当作无争议旁证；朕惟一子指柴荣的养子身份背景，不新建血亲。')
add('wang_jun_demoted_shangzhou','郭威将王峻贬为商州司马',18,'甲子，','孩抚朕躬。”',[('帝','贬王峻为商州司马'),('王峻','被贬往商州')],when='953年二月甲子',place='后周朝廷至商州',note='制辞比喻以原文保留，展示说明实际贬职，不机械翻译肉视孩抚。')
sup('wang_jun_demoted_shangzhou',18,oldfeb,'甲子，樞密使、平盧軍節度使、尚書左僕射、平章事、監修國史王峻責授商州司馬，員外置，所在馳驛發遣。','《旧五代史》同日也记王峻责授商州司马、员外置并驿送。','员外置为职务设置方式，不写成仍保留原宰相枢密职权。')
E['wang_jun_escorted']=event('wang_jun_escorted','郭威命徐台符等草拟贬王峻制书，蒋光远押送王峻赴商州',18,'即召翰林學士徐臺符等草制。其日，退朝宣制，貶授商州司馬，差供奉官蔣光遠援送赴商州。',[('徐台符','奉命草拟贬职制书'),('蒋光远','以供奉官身份押送王峻')],when='953年二月贬王峻时，《旧五代史》传记补充',place='后周朝廷至商州',source=oldwang,note='旧传其日与主书记拘禁、次日贬职的细分可能不同，保持相对时间，不强定制书起草为甲子或癸亥。')
add('guo_sends_wang_chenghui','郭威担心王殷不安，派其子王承诲赴邺都解释王峻获罪情况',18,'帝虑鄴都留守王殷','谕以峻得罪之状。',[('帝','派王承诲向王殷解释王峻获罪'),('王殷','收到朝廷解释与安抚'),('承诲','以尚食使身份赴父亲所在邺都传达情况')],when='953年二月王峻被贬以后',place='后周朝廷至邺都',note='复用后汉后周将王殷，与晚唐后梁同名者分开；王承诲与周承诲不混同。')
relationship('王殷','王承诲','父亲',18,'命殷子尚食使承诲诣殷，谕以峻得罪之状。','殷子明示父子，方向为后汉后周将王殷是王承诲的父亲。')
add('guo_allows_wife_visit_sick_wang','王峻到商州后患腹疾，郭威命其妻前往看望',18,'峻至商州，','命其妻往视之，',[('王峻','在商州患腹疾'),('帝','准许并命王峻之妻前往看望')],when='953年王峻贬居商州后、死亡前',place='商州',note='其妻未具名，不混入此前已故崔氏；保留未确定身份，不新建无证姓名。')
add('wang_jun_dies_shangzhou','王峻贬居商州后不久去世',18,'未几而卒。',None,[('王峻','在商州患病后不久去世')],when='953年贬居商州后；《旧五代史》记为三月',place='商州',note='年份和三月由独立旧传明确记时支持，主书未几只表示相对时间。')
sup('wang_jun_dies_shangzhou',18,oldwang,'未幾，死於貶所，時廣順三年三月也。','《旧五代史》王峻传明确记其广顺三年三月死于贬所。','这里取传记正文的日期，不将其后引《通鉴》的腹疾与探视文字当作独立旁证。',relation='adds',field='time_original')
sup('wang_jun_dies_shangzhou',18,newwang,'即貶商州司馬，卒于貶所。','《新五代史》也记王峻被贬商州司马，死于贬所。','该书不列死亡月日，不扩展为另一个不同死亡事件。')
add('guo_orders_yanzhou_garrison','郭威命折从阮分兵驻延州，高绍基开始害怕，屡次进献',19,'帝命折从阮','屡有贡献。',[('帝','命折从阮分兵驻延州'),('折从阮','受命分兵驻延州'),('高绍基','因朝廷驻军压力害怕，屡次进献')],when='953年二月延州处置期间，具体命令日未载',place='延州',note='贡献未列具体钱物，不编购买继任名额。')
add('zhang_huaizhen_deploys','郭威派张怀贞率禁军两指挥驻鄜州、延州，高绍基把军府事交给张匡图',19,'又命供奉官张怀贞','授副使张匡图。',[('帝','派张怀贞率禁军驻鄜延'),('张怀贞','率禁军两指挥驻鄜州延州'),('高绍基','将军府事务交给副使张匡图'),('张匡图','接掌军府事务')],when='953年二月朝廷调兵处置延州时',place='鄜州、延州',note='两指挥为部队编制数量，不自行换算为固定人数。')
sup('zhang_huaizhen_deploys',19,oldfeb,'延州牙內都指揮使高紹基奏，交割軍府與副使張圖。','《旧五代史》也记高绍基把军府交给副使张图。','同一交接、副使身份对应张匡图，保留简名张图，不与张图英同人；该条承二月戊辰附近，但未单独列日。')
claim('person',people['张匡图'],'aliases','《旧五代史》同一军府交接写副使张图，与《通鉴》张匡图对应。',19,'延州牙內都指揮使高紹基奏，交割軍府與副使張圖。','依据同一延州交接与副使职位校核，不仅按张姓相似合并。',source=oldfeb)
add('xiang_xun_controls_yanzhou','郭威命客省使向训暂掌延州',19,'甲戌，',None,[('向训','以客省使身份暂掌延州')],when='953年二月甲戌，《通鉴》纪日',place='延州')
sup('xiang_xun_controls_yanzhou',19,oldfeb,'命客省使向訓權知延州軍州事。','《旧五代史》二月也记命向训暂掌延州军州事。','该句在丁丑条后但未给单独纪日，保留主书甲戌，不擅以丁丑替换。')
add('rong_jin_prince_kaifeng','郭威任柴荣为开封尹，封晋王',20,'三月，甲申，','开封尹、晋王。',[('帝','任柴荣为开封尹并封晋王'),('荣','获任开封尹并封晋王')],when='953年三月甲申',place='开封')
add('zheng_renhui_zhenning','郭威任郑仁诲为镇宁节度使',20,'丙戌，',None,[('郑仁诲','由枢密副使获任镇宁节度使')],when='953年三月丙戌',place='澶州')

reviews={11:'二十一族为归附部落计数，戊申是奏报时间，不臆定各首领名单。',12:'邵棠民间身份与所闻、南征忧虑分别说明，未把忧虑录成后周作战令。',13:'收复潭州后的旧任命、军府分治失礼、猜疑与谋划、南汉入侵、诱将南征、醉宴假使拘捕、逃捕处决逐步拆录；初不强定953。新书概述与主书先何后朱、旧纪失律奏报并列。',14:'癸丑返澶承二月条，复用柴荣。',15:'新作两宝与947晋宝北去回述区分，旧纪补宝文及冯道书写；不直接当秦玺。',16:'通知何死与刘斩符会分开，不得己解释依上下文，原字保留，不把李仲迁列被杀。',17:'奏请替相与郭威暂缓回应分开，颜愆、频衎、陈同不同写法保留，不据疑字另造已上任宰相。',18:'拘禁、陈诉理由、贬职、草制押送、安抚王殷、患病探视与死亡分别记；旧传明确三月卒，不把引通鉴文字当独立证明；妻未具名且不能是此前已故崔氏。',19:'分兵与两指挥禁军、交接与暂掌分开；张匡图张图同副使同交接证明，甲戌不被旧条丁丑替换。',20:'柴荣开封尹晋王与郑仁诲镇宁节度使分开，日期各承主书。'}
assert not (P/'publication.json').exists()
for n in range(11,21):
 assert ledger[n-1]['status'] in ('pending','reviewed');ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=953,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(11,21)],next_paragraph=Q[21]['id'],next_volume=291,next_year=953,supplements=supplements,excluded_non_body=[],coverage='卷291原43—52行连续十段；953年尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(11,21)],source_issues_review='原连续长段被检索库拆为两块，引用分别取固定原片段，事件仍回指同一主段。姓名异文、奏报解释、相对日期均保留，纸本异文未核。',plain_language_review='首次逐条检查标题、人物、角色、关系方向及事实说明，人物推测和伪造命令不当真实授权；前事回述、当前行动及后续三月死亡分别说明，原文不改字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
