# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 48–54."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,93))
COMMIT='a5f6c36376aec96cc635a266cd774a64d3733ea7'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['tongjian-286-947-li-wuyue','jiuwudaishi-098-zhao-titles','xinwudaishi-010-accession']:
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
main_sources = ['tongjian-286-947-li-wuyue','tongjian-286-947-xuzhou-march']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p048-p054',
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
lines = (ROOT / 'resources/derived/tongjian/286.txt').read_text().splitlines()
for n in range(48, 55):
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
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷286·天福十二年（947年二月至三月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_10_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=947, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='947年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_286_0947_' + code
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
        edge = 'participation_zztj_286_0947_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'是{a}的{kind}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_286_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'蜀主':'孟昶','契丹主':'耶律德光','述律太后':'述律平','明宗':'李嗣源','周密':'周密（后晋节度使）','高彦询':'高彦珣','万金':'高万金','从益':'李从益','淑妃':'王淑妃','昭序':'符昭序','明宗女':'李氏（赵延寿继室）'})
NEW_ALIASES={'高允权':['高允權'],'周密（后晋节度使）':['周密（後晉節度使）'],'高彦珣':['高彥珣','高彦询','高彥詢'],'李氏（赵延寿继室）':['李氏（趙延壽繼室）'],'李仁恕':[],'符昭序':[],'陈守习':['陳守習']}
NEW_DESCRIPTIONS={
'高允权':'高万金之子。947年延州军队攻周密，高允权获推为留后、据西城。《通鉴》称录事参军，《新五代史》追记开运时任肤施令、罢后居家，任职时点及写法分别保留。生卒年暂未录入。',
'周密（后晋节度使）':'应州人，后晋彰武节度使。947年延州将士攻他，战败后退保东城，与获推留后的高允权分据两城。与南宋同名作者区分，生卒年未载。',
'高彦珣':'丹州都指挥使。947年杀契丹委任的刺史，自管州务。当前《通鉴》此段写高彦珣，后段及《新五代史》写高彦询，《旧五代史》写高彥珣，依同一职务与事件识别为同人，引用保留各书字形。生卒年未载。',
'李氏（赵延寿继室）':'后唐明宗李嗣源的小女儿。947年赵延寿在大梁娶她为继室，王淑妃赴大梁参与婚礼。与此前赵延寿妻兴平公主区分，未据本段补封号、名字或生卒年。',
'李仁恕':'947年率数万人攻徐州的武装首领，曾拉住符彦卿的马，想随他进城。陈守习公开表示徐州不会因符彦卿被困而投降后，李仁恕一方请赦，誓约后撤去。生卒年未载。',
'符昭序':'符彦卿之子。947年守徐州城时，遣军校陈守习缒城而出，公开说明即使符彦卿受胁迫，攻城也不能得逞。生卒年未载。',
'陈守习':'徐州军校。947年受符昭序派遣，从城中缒下，到攻城武装中喊话，表明城池不会因符彦卿受制而交出。生卒年未载。'}
g='xinwudaishi-040-gao-yunquan';j='jiuwudaishi-099-march-rising';jc='jiuwudaishi-051-li-congyi';z='jiuwudaishi-098-zhao-titles';nw='xinwudaishi-010-accession'
t='947年二月条下，具体日未载'
add('meng_promotes_he_zhongjian','孟昶加雄武节度使何重建同平章事',48,'蜀主',None,[('蜀主','给何重建加同平章事'),('何重建','获加同平章事')],when=t,place='后蜀朝廷、雄武军（任职范围）',note='同平章事按原官衔记录，不自动写成何重建已到成都执掌全部朝政。')
add('yanzhou_soldiers_attack_zhou_mi','延州将士攻周密，周密败后退保东城',49,'彰武节度使','保东城。',[('周密','被将士攻击，战败后保东城')],when=t,place='延州东城',note='暗而贪是史家评价，不补具体罪案及金额；军乱没有逐名将士名单。主書叙述在二月，《新五代史》三月辛卯记逐周密，分别引用。')
sup('yanzhou_soldiers_attack_zhou_mi',49,nw,'辛卯，延州軍亂，逐其節度使周密。','《新五代史》在三月辛卯记延州军乱逐周密。','主书二月条下记攻守，后文三月辛卯另记高允权归降；不把两书记事范围压成唯一发生日。',relation='adds',field='time_original')
add('gao_yunquan_chosen_liuhou','延州军队因高允权家世在延州任帅，推他为留后，控制西城',49,'众以允权','据西城。',[('高允权','获推留后并据西城')],when=t,place='延州西城',note='家世延帅是推举理由，不据此补出高家每代官员名单；留后不等于已经正式任节度使。')
sup('gao_yunquan_chosen_liuhou',49,g,'契丹滅晉，延州軍亂，逐密，密守東城，而西城之兵以允權為留後。','《新五代史》同记周密守东城、西城兵推高允权留后。','该书军额前文作彰信，主书作彰武，保留底本文字与校注标记，不悄改来源。')
claim('person',person('高允权',49,'延州录事参军',span(49,'延州录事参军','万金之子也。')),'description','高允权在《通鉴》本段中任延州录事参军。',49,span(49,'延州录事参军','万金之子也。'),'职务按主书本段明确记载。')
claim('person',people['高允权'],'description','《新五代史》记高允权在开运时任肤施令，罢职后居家。',49,'萬金子允權，開運中為膚施令，罷居于家。','任职时期与主书不同，各自保留，不凭不同职务新建同一人的副本。',source=g)
relationship('高万金','高允权','父亲',49,span(49,'延州录事参军','万金之子也。'),'万金按前文家世及《新五代史》卷40确认同已有人物高万金；方向是高万金为高允权之父。')
claim('person',people['周密（后晋节度使）'],'description','周密（后晋节度使）是应州人。',49,span(49,'密，应州人也。'),'籍贯按段末记录，保留历史地名，不补坐标。')
add('gao_yanxun_kills_khitan_prefect','丹州都指挥使高彦珣杀契丹所任刺史，自管州务',50,'丹州',None,[('高彦珣','杀契丹委任刺史并自行管理丹州')],when=t,place='丹州',note='被杀刺史未名，不补身份。主书本段珣与后段询、旧史珣、新史詢分别保留，当前尚不提前记三月正式归附。')
sup('gao_yanxun_kills_khitan_prefect',50,j,'壬辰，丹州都指揮使高彥珣殺偽命刺史，據城歸命。','《旧五代史》三月壬辰条记高彦珣杀契丹刺史并据城归附。','主书二月记杀刺史、自领州务，三月另记归附；补书在壬辰连叙，各自保留叙述范围。',relation='adds',field='time_original')
add('shulu_sends_gifts_for_jin_conquest','述律平遣使赐耶律德光酒食、脯果，祝贺灭晋',51,'契丹述律太后','贺平晋国。',[('述律太后','遣使送国中酒食果脯贺灭晋'),('契丹主','收到母亲所赐食品')],when=t,place='契丹境内至大梁',note='本句只写国中，没有确定出发城；食品没有数量和价值，不补贡物清单。')
add('khitan_banquets_stands_for_mothers_wine','耶律德光与群臣宴于永福殿，每次饮太后所赐酒都站起，称不敢坐饮',51,'契丹主与',None,[('契丹主','宴饮时为太后所赐酒站起')],when=t,place='大梁永福殿',note='这是原书记载的礼仪与本人解释，不当证明其全部政治行为皆出孝心；群臣未逐一名单。')
add('zhao_yanshou_marries_mingzong_daughter','赵延寿娶后唐明宗女为妻，王淑妃到大梁参加婚礼',52,'赵延寿娶','淑妃诣大梁会礼。',[('赵延寿','娶明宗女为妻'),('明宗女','嫁给赵延寿'),('淑妃','从洛阳赴大梁参与婚礼')],when=t,place='洛阳至大梁',note='《旧五代史》明确复娶明宗小女为继室，区别此前兴平公主。不把王淑妃参礼写成新妇生母的证据。')
sup('zhao_yanshou_marries_mingzong_daughter',52,z,'延壽在汴州，復娶明宗小女為繼室。','《旧五代史》明确记赵延寿在汴州复娶明宗小女为继室。','来源同一传记前段已引用，但此婚配按当前主书段落补入。小女未在此句给公主封号，不沿用兴平公主主体。',relation='adds')
relationship('赵延寿','李氏（赵延寿继室）','丈夫',52,span(52,'赵延寿娶','为夫人，'),'赵延寿是该继室的丈夫，方向明示；不将继室与前妻兴平公主合并。')
relationship('李嗣源','李氏（赵延寿继室）','父亲',52,span(52,'赵延寿娶','为夫人，'),'明宗按后唐明宗李嗣源识别，明宗女支持父女关系；未据此推母亲。')
add('khitan_greets_wang_as_sisterinlaw','耶律德光见王淑妃，向她行拜礼，称她为嫂',52,'契丹主见','吾嫂也。”',[('契丹主','向王淑妃行拜礼并称嫂'),('淑妃','受到拜礼与嫂的称呼')],when=t,place='大梁',note='吾嫂是礼仪称呼，不能据此新建亲兄弟与真实嫂媳关系。')
add('liu_suining_seeks_office_through_wang','刘遂凝通过王淑妃请求节度使职位',52,'统军刘遂凝','求节钺，',[('刘遂凝','以统军身份通过王淑妃求节度职位'),('淑妃','成为刘遂凝求职的转达渠道')],when=t,place='大梁',note='求节钺为求节度使职任，不字面写请求一面旌旗；转达不证明接受财物。')
add('khitan_restores_li_congyi_prince','耶律德光封李从益为许王、任威信节度使',52,'契丹主以从益','威信节度使，',[('契丹主','封李从益许王并授威信节度使'),('从益','获许王爵与威信节度使任命')],when=t,place='大梁、曹州（遥任地）',note='从益已曾封许王后改郇公，此次为再授。任命不等于实际到曹州。')
sup('khitan_restores_li_congyi_prince',52,jc,'開運末，契丹主至汴，以從益遙領曹州節度使，復封許王','《旧五代史》记李从益遥领曹州节度使、复封许王。','该传使用开运末概括契丹入汴背景，主书在947年二月条下记授职，不硬定为946年另一次任命。曹州为主书威信军对应任职地。',relation='adds')
add('khitan_appoints_liu_suining_anyuan','耶律德光任刘遂凝为安远节度使',52,'遂凝为','安远节度使。',[('契丹主','任刘遂凝为安远节度使'),('刘遂凝','获任安远节度使')],when=t,place='安远军（任职地）',note='只记授职，不补到任日或实际占领情况。')
add('wang_declines_li_congyi_post_returns_luoyang','王淑妃因李从益年幼，辞去赴镇安排，带他回洛阳',52,'淑妃以从益幼，','复归于洛。',[('淑妃','以从益年幼为由辞不赴镇，返回洛阳'),('从益','未赴军镇，返回洛阳')],when=t,place='大梁至洛阳',note='辞不赴镇不一定等于许王爵被取消；年幼不据此推具体年龄。')
sup('wang_declines_li_congyi_post_returns_luoyang',52,jc,'與王妃尋歸西京。','《旧五代史》同记李从益与王妃不久返回西京。','西京为洛阳，补书未给确切日。')
add('khitan_appoints_zhang_li_chancellor','耶律德光任张砺为右仆射兼门下侍郎、同平章事',52,'契丹主以张砺','同平章事，',[('契丹主','任张砺为宰相并授右仆射等职'),('张砺','获任右仆射兼门下侍郎、同平章事')],when=t,place='大梁朝廷',note='官衔完整保留，不合并为单一仆射任命；不补任职年限。')
add('khitan_appoints_he_ning_chancellor','耶律德光加左仆射和凝中书侍郎、同平章事',52,'左仆射和凝','同平章事。',[('契丹主','给和凝加中书侍郎、同平章事'),('和凝','兼任中书侍郎、同平章事')],when=t,place='大梁朝廷',note='左仆射为原句已有职务，兼任内容按原文，不写成首次担任全部官职。')
add('liu_xu_retires_with_eye_disease','刘昫因眼疾辞去宰相职务，改为太保',52,'司空兼门下',None,[('刘昫','因眼疾辞去宰相职务，改任太保')],when=t,place='大梁朝廷',note='眼疾没有明确诊断，不补为全盲；改太保不写成当时死亡。')
add('eastern_groups_capture_three_prefectures','东方武装群体起事，攻陷宋州、亳州、密州',53,'东方群盗','密三州。',[],when='947年二月条下，具体日未载',place='宋州、亳州、密州',note='群盗是史书称谓，展示称武装群体；未载每州首领，不把李仁恕自动列为三城全部行动的首领。')
add('khitan_sends_an_fu_back_to_commands','耶律德光感叹中原人难以控制，急遣安审琦、符彦卿等归镇，派契丹兵护送',53,'契丹主谓','仍以契丹兵送之。',[('契丹主','因各州变动派节度使归镇并遣兵护送'),('安审琦','以泰宁节度使身份被遣归镇'),('符彦卿','以武宁节度使身份被遣归镇')],when='947年二月条下，具体日未载',place='大梁至泰宁军、武宁军',note='中国之人难制是耶律德光说法，不当历史民族群体的固定性质；护送兵未载具体人数。')
add('li_renshu_besieges_xuzhou','符彦卿到埇桥时，李仁恕率数万人急攻徐州',53,'彦卿至埇桥，','急攻徐州。',[('符彦卿','归镇途中抵达埇桥'),('李仁恕','率数万人急攻徐州')],when='947年二月条下，具体日未载',place='埇桥、徐州',note='数万人是概述规模，不填确切人数；埇字按当前底本保留，不换现代坐标。')
add('li_renshu_grips_fu_horse','符彦卿带数十骑到徐州城下，想招谕李仁恕，李仁恕拉住他的马要求同行入城',53,'彦卿与数十骑','请从相公入城。',[('符彦卿','率数十骑到城下准备招谕'),('李仁恕','拉住符彦卿的马，要求一起进城')],when='947年二月条下，具体日未载',place='徐州城下',note='相公指符彦卿；不把控马要求译为符彦卿已自愿投降，也不补数十骑精确人数。')
add('fu_zhaoxu_sends_chen_out','符昭序从徐州城内派陈守习缒城而出，告知对方即使胁迫符彦卿也不能取城',53,'彦卿子昭序，','城不可得也。”',[('昭序','派军校出城公开表明守城立场'),('陈守习','缒城出外，向攻城者喊话'),('符彦卿','成为喊话中被胁迫的主帅')],when='947年二月条下，具体日未载',place='徐州城内外',note='虎口是陈守习对处境的比喻，不字面当作被猛兽所伤；相公助贼攻城是假设，不写符彦卿已经真的助攻。')
relationship('符彦卿','符昭序','父亲',53,span(53,'彦卿子昭序，','自城中遣军校陈守习缒而出，'),'彦卿子昭序明确父子关系，方向为符彦卿是符昭序的父亲。')
add('xuzhou_attackers_seek_pardon_withdraw','攻徐州者得知不能挟符彦卿取城，向他下拜求赦，誓约后离去',53,'贼知不可劫，',None,[('符彦卿','与求赦者立誓约'),('李仁恕','所率武装求赦后撤去')],when='947年二月条下，具体日未载',place='徐州城下',note='誓约未载具体条款，不补永久归附或免死全部人员；乃解去不等于所有武装都被歼灭。')
add('khitan_march_entry_court_rite','耶律德光在三月朔着赭袍坐崇元殿，百官行入阁礼',54,'三月，',None,[('契丹主','着赭袍在崇元殿接受入阁礼')],when='947年三月丙戌朔',place='大梁崇元殿',note='百官没有逐一姓名，不自动连入所有前晋官员。本段没有任命萧翰，相关任命在后续主书位置处理。')
sup('khitan_march_entry_court_rite',54,j,'是日，契丹主坐崇元殿行入閣之禮','《旧五代史》三月丙戌朔条也记崇元殿行入阁礼。','是日承接该原段三月丙戌朔，已回查句首；不引用同段其他日期混入本事件。')
reviews={48:'加同平章事与雄武原职分清，不补为在成都执政。',49:'高允权官职与补书前任肤施令分时记载，父高万金沿旧主体；东城西城与获推留后分别。旧新书三月记事范围不强定主书二月发生日。',50:'高彦珣与询按同职同事识别，杀刺史和后来归附分开，旧书三月壬辰并叙保留。',51:'述律母后送酒与站饮礼仪，不补具体贡品数与使者姓名。',52:'赵延寿继室与兴平公主分开，明宗小女父女与丈夫关系明确；吾嫂是称呼不建真实亲属。封任、辞赴镇、返回及三项朝官变化分清。',53:'三州群体不自动合并为李仁恕军；控马、缒城喊话与求赦誓约撤去按次序，未虚构自愿助攻与誓约条款。',54:'三月丙戌朔入阁礼与旧史同日互证，不把同段萧翰任命提前加入本主段。'}
assert not (P/'publication.json').exists()
for n in range(48,55):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(48,55)],next_paragraph=Q[55]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原53—59行连续七段，累计54/92，947年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(48,55)],source_issues_review='高允权官职与周密军额、丹州彦珣询字形保留异说；赵延寿继室不与前妻混同；三月补书记日与主书二月排列的范围分别。',plain_language_review='首次逐条核对标题、说明、参与、关系及事实说明，保留原文与各书差异，区分请求、任命、未赴任、比喻及已发生行动。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
