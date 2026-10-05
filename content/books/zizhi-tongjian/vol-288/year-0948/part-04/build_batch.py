# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 948 paragraphs 17–24."""
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
COMMIT='dc1b74e793e7a84b95e7f13cfd591806b7129dca'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-288-948-march-april-conflict','jiuwudaishi-101-april-dingzhou-948']:
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
main_sources = ['tongjian-288-948-march-april-conflict','tongjian-288-948-april-august']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0948-p017-p024',
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
        citation = f'卷288·乾祐元年（948年四月至六月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0948_04_{len(B["claims"])+1:04d}'
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
ALIASES.update({'徐彦':'徐彦（后蜀凤州刺史）','禅奴':'禅奴利','故晋主':'石重贵','契丹主':'耶律阮','蜀主':'孟昶'})
NEW_ALIASES={'尚洪迁':['尚洪遷'],'禅奴利':['禅奴','禪奴','禅奴舍利'],'石重贵之女（948年被赐给禅奴者）':[],'徐彦（后蜀凤州刺史）':['徐彦（凤州刺史）']}
NEW_DESCRIPTIONS={
 '尚洪迁':'后汉将领。948年《资治通鉴》记其任宁江节度使、侍卫步军都指挥使，四月乙未被任为西面行营都虞候；《旧五代史》写西南面行营。生卒年尚未录入。',
 '禅奴利':'契丹皇帝耶律阮的妻兄，《通鉴》后文简称禅奴，《旧五代史》写禅奴舍利。948年向被俘的石重贵求其未婚幼女，遭拒后，耶律阮强行取女赐给他。各书行程月份及旧史末句受赐者译名差异分别保留，生卒年未载。',
 '石重贵之女（948年被赐给禅奴者）':'石重贵未具姓名的幼女，948年尚未出嫁。禅奴利求娶时，石重贵以年幼拒绝；后来耶律阮派人强行带走，将她赐给禅奴利。具体出生年、母亲及婚礼是否举行均未载，以本次经历限定身份，不合并其他未具名女儿。',
 '徐彦（后蜀凤州刺史）':'948年任后蜀凤州刺史。王景崇致书请求互市，孟昶命徐彦回信招引王景崇。与闽国同名巫者徐彦分开，未作无证合并。生卒年未载。'}
apr='jiuwudaishi-101-april-dingzhou-948';oldjin='jiuwudaishi-085-jin-captive-audience-948';newjin='xinwudaishi-017-jin-captive-daughter-948';may='jiuwudaishi-101-may-948';june='jiuwudaishi-101-june-948';daughter='石重贵之女（948年被赐给禅奴者）';a='948年四月，具体日未载'
add('guo_congyi_yongxing_deployment','郭从义任永兴行营都部署，率侍卫兵讨赵思绾',17,'以镇宁','将侍卫兵讨赵思绾。',[('郭从义','任行营都部署，率侍卫兵讨赵思绾'),('赵思绾','成为奉命讨伐的目标')],when=a,place='长安、永兴军',note='任命及率兵讨伐与攻城成功分开；主书这句没独立干支，旧本纪在壬午条记任命。')
sup('guo_congyi_yongxing_deployment',17,apr,'是日，以澶州節度使郭從義為永興軍一行兵馬都部署。','《旧五代史》四月壬午条同记郭从义任永兴行营部署，前职写澶州节度使。','是日承接本纪壬午；镇宁为军号、澶州为州名，不因表述不同建另一郭从义。',relation='adds')
add('bai_wenke_hezhong_deployment','白文珂任河中行营都部署',17,'戊子，','河中行营都部署，',[('白文珂','由保义节度使充河中行营都部署')],when='948年四月戊子',place='河中',note='这是部署任命，不写成当天已经击败李守贞。')
sup('bai_wenke_hezhong_deployment',17,apr,'以陜州節度使白文珂為河中府城下一行都部署。','《旧五代史》戊子条同记白文珂任河中府城下行营部署，前职写陕州节度使。','保义与陕州是军州称谓；独立原文任职表述保留。')
add('wang_jun_campaign_supervisor','王峻任河中行营都监',17,'戊子，','内客省使王峻为都监。',[('王峻','由内客省使任河中行营都监')],when='948年四月戊子',place='河中行营',note='承接前文白文珂河中行营，不能把两人任命合为同一人。旧本纪所列行营范围不同，另记。')
sup('wang_jun_campaign_supervisor',17,apr,'以客省使王峻為西南面行營兵馬都監。','《旧五代史》四月任官段将王峻职写为西南面行营兵马都监。','主书承河中行营都监，旧史写西南面，行营范围表述分别保留，不据此另造一次无日期的调任。',relation='adds')
add('li_shouzhen_stripped_and_attacked','后汉削夺李守贞官爵，命白文珂等会兵讨伐',17,'辛卯，','命文珂等会兵讨之。',[('李守贞','被削官爵并成为讨伐对象'),('白文珂','奉命会合兵马讨李守贞')],when='948年四月辛卯',place='后汉朝廷、河中',note='削夺是实际朝廷处分，讨伐命令不等于已收复河中。')
sup('li_shouzhen_stripped_and_attacked',17,apr,'辛卯，削奪李守貞在身官爵。','《旧五代史》同记辛卯削夺李守贞官爵。','该句只印证处分，不独立证明军队已完成会师或攻克。')
add('shang_campaign_yuhou','尚洪迁任西面行营都虞候',17,'乙未，',None,[('尚洪迁','以宁江节度使、侍卫步军都指挥使身份任行营都虞候')],when='948年四月乙未',place='西面行营',note='都虞候是军职，不等于此时已经在长安战死；人物新建，未提前采入下一段尚未录的死亡记载。')
sup('shang_campaign_yuhou',17,apr,'以侍衛步軍都指揮使尚洪遷充西南面行營都虞候，','《旧五代史》同记尚洪迁任行营都虞候，名称写西南面行营。','独立段未重复乙未，日期按主书；西面与西南面表述分别保留。',relation='adds')
add('wang_defies_binzhou_transfer','王景崇迟迟不赴邠州，募集凤翔壮丁并向邠州发兵牒',18,'王景崇',None,[('王景崇','不赴邠州，集壮丁，假称讨赵思绾，要求邠州会兵'),('赵思绾','成为王景崇所用讨伐说辞的目标')],when=a,place='凤翔、邠州',description='王景崇迟迟不赴邠州任职，在凤翔集结壮丁，假称要讨赵思绾，又发牒要求邠州会兵。',note='诈言归史书判断，不写为真实讨赵计划；向邠州发牒不等于对方已经出兵。')
add('ruan_audience_jin_captives','耶律阮到辽阳，石重贵、晋太后和皇后谒见',19,'契丹主如辽阳，','皇后皆谒见。',[('耶律阮','到辽阳，接受被俘晋廷家属谒见'),('石重贵','与太后、皇后谒见契丹皇帝'),('永宁公主（石敬瑭妻）','以晋太后身份参加谒见'),('冯氏（石重贵后）','以晋皇后身份参加谒见')],when=a,place='辽阳',note='故晋主是石重贵，太后是石敬瑭妻李氏，皇后为冯氏，不因失国改建人物或误用后汉李太后。')
sup('ruan_audience_jin_captives',19,oldjin,'漢乾祐元年四月，永康王至遼陽，帝與太后並詣帳中，','《旧五代史》同记乾祐元年四月永康王耶律阮到辽阳，石重贵与太后到帐中谒见。','永康王沿耶律阮；该句未列晋皇后，不能当作逐人完全独立印证。')
sup('ruan_audience_jin_captives',19,oldjin,'帝御白衣紗帽，永康止之，以常服謁見。帝伏地雨泣，自陳過咎，永康使左右扶帝上殿，慰勞久之，因命設樂行酒，從容而罷。','《旧五代史》补记石重贵原着白衣纱帽，被要求改常服，伏地流泪陈述过错，耶律阮命扶上殿并设乐酒。','补同次谒见细节，不增原文未载的赦免或释放结论。',relation='adds')
add('channu_requests_daughter_refused','禅奴利求娶石重贵未婚幼女，石重贵以年幼拒绝',19,'有禅奴利者，','晋主辞以幼。',[('禅奴利','以契丹皇帝妻兄身份求石重贵之女'),('石重贵','以女儿年幼为由拒绝'),(daughter,'被求娶，当时未婚')],when='948年相关辽阳行程；主书四月条，新史放五月',place='辽阳及契丹行程',note='请求未获同意，不记为双方自愿定婚。幼女未具名，按本次经历限定，不合其他未具名女儿。')
relationship('禅奴利','耶律阮','妻兄',19,'有禅奴利者，契丹主之妻兄也，','A是B的妻兄表示A是B妻子的兄长；契丹主为耶律阮，妻子此段未具名，不无证建立另一妻主体。')
relationship('石重贵',daughter,'父亲',19,'闻晋主有女未嫁，诣晋主求之，晋主辞以幼。','晋主沿石重贵，原文明确是他的女儿。只建父女，不据皇后同时在场推定生母。')
add('ruan_forcibly_takes_jin_daughter','耶律阮派人强取石重贵幼女，赐给禅奴利',19,'后数日，',None,[('耶律阮','派人驰取石重贵女儿，赐给禅奴利'),('石重贵','女儿在其拒绝后仍被带走'),(daughter,'被契丹派人强行带走'),('禅奴利','获得被强行带来的石重贵之女')],when='948年求女遭拒后数日；主书四月条，新史记五月',place='契丹境内',note='后数日是相对间隔，未推算精确日；已强取赐人，不补婚礼已经举行、具体同居或女儿生卒。')
sup('ruan_forcibly_takes_jin_daughter',19,newjin,'五月，永康王上陘，','《新五代史》把这次求女与强取放在永康王五月上陉避暑的行程中。','与主书四月条编排不同，时间分别保留，不静默统一成四月或五月。',relation='conflicts',field='time_original')
sup('ruan_forcibly_takes_jin_daughter',19,newjin,'永康王妻兄禪奴愛帝小女，求之，帝辭以尚幼。永康王馳一騎取之，以賜禪奴。','《新五代史》同记妻兄禅奴求石重贵幼女遭拒，耶律阮派骑兵强取后赐给禅奴。','角色与结果相合，未载女儿姓名、母亲或实际婚礼日期。')
sup('ruan_forcibly_takes_jin_daughter',19,oldjin,'後數日，永康王馳取帝幼女而去，以賜綽諾錫裏。','《旧五代史》也记数日后驰取幼女，但末句受赐者写绰诺锡里。','同段前文求女者为禅奴舍利，末句另译名与主书不同；未将绰诺锡里直接并入禅奴利的确定别名。',relation='adds')
add('wang_requests_shu_trade','王景崇写信给后蜀徐彦，请求互市',20,'王景崇遗蜀','求通互市。',[('王景崇','向后蜀凤州刺史致书请求互市'),('徐彦','以凤州刺史身份收取请求')],when='948年四月壬戌复书之前，原信具体日未载',place='凤翔至后蜀凤州',note='遗书指送信，不是遗嘱；请求互市不等于已经设立贸易市场，徐彦限定后蜀身份。')
add('meng_orders_xu_recruit_wang','孟昶命徐彦回信招引王景崇',20,'壬戌，',None,[('孟昶','命凤州刺史回信招王景崇'),('徐彦','奉命复书招引王景崇'),('王景崇','成为回信招引对象')],when='948年四月壬戌',place='后蜀、凤州、凤翔',note='招引和回信与正式归附分开，主书下一段其后请降留待连续后续录入。')
add('xu_taifu_detained_youzhou','契丹将徐台符留在幽州',21,'契丹主','于幽州，',[('徐台符','作为晋翰林学士被契丹留在幽州')],year=None,when='徐台符五月逃归之前的留置经历，具体留置年月未载',place='幽州',note='逃归在五月据独立本纪，但留置起点未给日期；不反推全部留置都从948四月开始，也不无证指定最初下令留置的契丹皇帝。')
add('xu_taifu_escapes_home','徐台符从幽州逃归',21,'台符逃归',None,[('徐台符','逃离幽州返回后汉')],when='948年五月丁卯，据《旧五代史》；主书此段未载日',place='幽州至后汉方向',note='主书接四月叙述，旧本纪明确五月丁卯；依据独立补证记日期，不直接套前段壬戌。')
sup('xu_taifu_escapes_home',21,may,'丁卯，前翰林學士徐臺符自幽州逃歸。','《旧五代史》明确将徐台符从幽州逃归记在五月丁卯。','臺符沿台符规范主体；书卷年条和逐字原文保留。',relation='adds')
add('huazhou_reports_yuchi_breach','滑州报告黄河在鱼池决口',22,'五月，',None,[],when='948年五月乙亥奏报，实际决口日未载',place='滑州鱼池',note='滑州言为报告，乙亥不是独立确认的决口日；鱼池采用史载地名，未给现代坐标、死伤或洪灾面积。')
sup('huazhou_reports_yuchi_breach',22,may,'乙亥，河決滑州魚池。','《旧五代史》同记五月乙亥滑州鱼池黄河决口。','主书记地方报告，本纪简写决口，各书表述保留。')
add('solar_eclipse_june_948','史书记948年六月朔发生日食',23,'六月，',None,[],when='948年六月戊寅朔',place='史书未载具体观测地点',note='仅记录日食记载；未独立天文核算，不补食分、类型、观测地或灾异预言。')
sup('solar_eclipse_june_948',23,june,'六月戊寅朔，日有食之。','《旧五代史》同记六月戊寅朔日食。','这是第二书的记载，不称已经由现代天文计算验证。')
add('liu_ci_hezhong_yuhou','刘词任河中行营马步都虞候',24,'辛巳，',None,[('刘词','由奉国左厢都虞候充河中行营马步都虞候')],when='948年六月辛巳',place='河中行营',note='这是本次任官，后续八月升任与军号另录，不以八月记载覆盖本次六月职位。')
reviews={17:'郭永兴部署、白河中部署、王都监、辛卯削李讨令、乙未尚虞候分录。主无郭具体日，旧壬午补。白前军州称对应，王河中与旧西南面行营表述保留。尚初建不提前后来战死。',18:'迟赴邠、集丁壮、诈称讨赵和发牒会兵；命令不作邠州兵已到或真意讨赵。',19:'耶律阮辽阳行、石重贵与永宁李太后冯后谒见；旧补四月及礼遇。禅奴利妻兄、求女拒、数日后强取赐人分，主四月条与新五月行程保留。旧末绰诺锡里译名未硬合；女按事限定，父关系不据皇后在场推母或婚礼。',20:'送信互市请求与壬戌回信招引分，不提前正式请降。徐彦限定蜀刺史，别闽巫者。',21:'留置起点未知null，逃归五月丁卯独立本纪补，不套前四月壬戌。徐台符沿已有人物。',22:'五月乙亥地方报告鱼池决河，主报告日不作实际发生日，地名坐标损失未补。',23:'六月朔戊寅日食两书相合，不称现代计算确证或补食分类型观测地。',24:'六月辛巳刘词虞候任命，具体官衔与后续升任区分。'}
assert not (P/'publication.json').exists()
for n in range(17,25):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=948,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],next_volume=288,next_year=948,supplements=supplements,excluded_non_body=[],coverage='卷288原23—30行连续八段，本卷24/69；卷287已19段，全年43/88，未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,25)],source_issues_review='主旧行营范围差异；被俘晋廷身份沿旧主体。求女强取主四月编排、新五月及旧末译名差异保留。徐台符逃归五月丁卯明载，留置年月未造；徐彦别闽巫者，幼女母名婚礼不推。',plain_language_review='首次逐条核对所有人物、事件、时间、角色、关系和事实说明；原文保留，写清请求与执行、任官与获胜、报告与实际发生日期。妻兄、父亲方向明确，无证个人名及生母不补，不设发布后二次文案重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
