# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 283, year 943 paragraphs 34–42."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,43))
COMMIT='e4284fc6d71535dbdd9b85d19ca37d8bb9add577'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-283-943-autumn','xinwudaishi-009-943-return','xinwudaishi-062-li-bian-death']:
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
main_sources = ['tongjian-283-943-autumn','tongjian-283-943-year-end','tongjian-283-943-chu-tax','tongjian-283-943-min-liu-zan']
B = {'format_version': 1, 'batch_key': 'zztj-v283-y0943-p034-p042',
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
lines = (ROOT / 'resources/derived/tongjian/283.txt').read_text().splitlines()
for n in range(34, 43):
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
    for a,b in [('旧纪','《旧五代史》本纪'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
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
        month = '十一月至年末条下及追述'
        citation = f'卷283·后晋天福八年（943；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_283_0943_05_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=943, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='943年年末条下，具体日期未载'
    key = 'event_zztj_283_0943_' + code
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
        edge = 'participation_zztj_283_0943_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_283_0943_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=ev(code,title,n,start,end,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
ALIASES.update({'帝':'石重贵','高祖':'石敬瑭','唐主':'李璟','闽主':'王延羲','曦':'王延羲','契丹主':'耶律德光','杜威':'杜重威','王绪':'王绪（杜重威判官）','刘赞':'刘赞（闽御史中丞）'})
NEW_ALIASES={'仰氏（钱弘佐妃）':[],'何超':[],'郭谨':['郭謹'],'翟进宗':['翟進宗'],'莫彦殊':['莫彥殊'],'王绪（杜重威判官）':['王緒（杜重威判官）'],'李沼':[],'邓懿文':['鄧懿文'],'周陟':[],'区弘练':['區弘練'],'刘赞（闽御史中丞）':['劉贊（閩御史中丞）']}
NEW_DESCRIPTIONS={
'仰氏（钱弘佐妃）':'仰仁诠的女儿，943年十一月戊子被吴越王钱弘佐纳为妃。个人名字与生卒年未载。',
'何超':'金城人，后晋左飞龙使。943年十一月庚子，在杨承祚逃往青州后，被任命暂时主持单州事务。生卒年未载。',
'郭谨':'后晋侍卫步军都指挥使。943年十一月壬寅奉命率兵驻守郓州。生卒年未载。',
'翟进宗':'后晋淄州刺史。943年十二月被杨光远派兵劫往青州；《新五代史》本纪还记其在杨光远反叛中死亡，具体死亡情境与日期本批未核。',
'莫彦殊':'宁州酋长，943年条下记其率所部温那等十八州归附楚国。史书记这些州未设官府，楚国以立牌和恩威维持羁縻关系。生卒年未载。',
'王绪（杜重威判官）':'后晋顺国节度使杜重威的判官。943年向杜重威提出搜括粮食的办法。与晚唐光州刺史王绪为不同人物，也未证与后晋太常丞王绪同人。生卒年未载。',
'李沼':'后晋杜重威的判官。943年受命向民间借粮，所得粮食在次年春出售。生卒年未载。',
'邓懿文':'楚国营田使，受马希范命登记逃亡民户留下的田地，招募民众耕种缴租。具体任职与行动年月未载。',
'周陟':'楚国孔目官。943年提出在常税之外追加各县贡米的办法，马希范采用。拓跋恒上书请求撤销贡米令、处死周陟，原文未记该请求被执行。生卒年未载。',
'区弘练':'楚国客将，拓跋恒被马希范拒绝接见后，向他表达对楚国前景的忧虑。生卒年未载。',
'刘赞（闽御史中丞）':'闽国御史中丞。王延羲因嫁女时有朝士未道贺，准备杖责未弹劾他们的刘赞。郑元弼劝谏后，刘赞被释放；《资治通鉴》还记他最终忧郁而死，确切年月未载。与前蜀嘉州司马刘赞及后唐秦王傅刘赞分别建档。'}
# 34–35: marriage, retrospective horse loan, flight and garrisons.
add('hongzuo_yang_consort','钱弘佐纳仰仁诠之女为妃',34,'戊子，',None,[('钱弘佐','纳仰仁诠之女为妃'),('仰氏（钱弘佐妃）','被钱弘佐纳为妃')],when='943年十一月戊子',place='吴越')
relationship('仰仁诠','仰氏（钱弘佐妃）','父亲',34,'仰氏，仁诠之女也。','父女关系明确；纳妃不擅改为册立皇后，不新增未具名婚礼主持者。')
add('shi_lends_yang_horses','石敬瑭将三百匹马借给杨光远',35,'初，','杨光远，',[('高祖','将三百匹马借给杨光远'),('杨光远','借用石敬瑭的三百匹马')],year=None,when='石敬瑭在世时的追述，具体年月未载',place='后晋')
add('jing_recalls_yang_horses','景延广按诏令向杨光远收回马匹，杨光远认为朝廷怀疑自己',35,'景延广','是疑我也。”',[('景延广','按诏令收回马匹'),('杨光远','生气并声称朝廷怀疑自己')],when='943年十一月杨承祚逃归前，具体日期未载',place='后晋',note='是疑我也是杨光远的判断，不据此断言朝廷已查明他谋反。')
add('yang_summons_chengzuo','杨光远秘密召儿子杨承祚回来',35,'密召','承祚，',[('杨光远','秘密召在单州任刺史的儿子回来'),('杨承祚','受到父亲秘密召回')],when='943年十一月戊戌之前，确切日期未载',place='单州、青州')
add('chengzuo_flees_shanzhou','杨承祚称母亲有病，夜间开城门逃往青州',35,'戊戌，','奔青州。',[('杨承祚','称母亲有病，夜间开单州城门逃往青州')],when='943年十一月戊戌夜',place='单州至青州',note='母病是杨承祚所称理由，不另建其母实际患病事件。')
relationship('杨光远','杨承祚','父亲',35,'密召其子单州刺史承祚，','其子明确，杨光远沿用杨檀主体，复用既有父子方向记录。')
add('he_chao_shanzhou','后晋任左飞龙使何超暂时主持单州事务',35,'庚子，','权知单州。',[('帝','任命何超暂时主持单州事务'),('何超','以左飞龙使身份权知单州')],when='943年十一月庚子',place='单州',note='权知为临时主持，不直接改成正式节度使；金城是何超籍贯。')
add('yang_gifts_pacification','后晋派内班人员赐杨光远玉带、御马与金帛，试图安抚他',35,'遣内班','以安其意。',[('帝','派人赐物安抚杨光远'),('杨光远','收到朝廷赐物')],when='943年十一月条下，具体日期未载',place='青州',note='安其意是行动目的，不保证杨光远因此停止谋反。')
add('guo_jin_yunzhou','后晋派郭谨率兵驻守郓州',35,'壬寅，',None,[('帝','派郭谨率兵驻守郓州'),('郭谨','以侍卫步军都指挥使身份率兵驻郓州')],when='943年十一月壬寅',place='郓州')
# 36–37: burial, rebellion and preparations; actual invasion is next year's mainline.
add('li_bian_yongling_burial','南唐将李昪安葬于永陵，庙号烈祖',36,'唐葬',None,[('李昪','被安葬于永陵，庙号烈祖')],place='永陵',note='李昪去世已在943年二月条录入；本条是安葬与庙号，不另造一次死亡。唐号按新史明确庙号校读，原字不改。')
sup('li_bian_yongling_burial',36,'xinwudaishi-062-li-bian-death','廟號烈祖，陵曰永陵。','《新五代史》明确李昪庙号烈祖、陵名永陵。','只支持庙号与陵名，不声称该书给本次安葬日期。')
add('cai_yunzhou_garrison','后晋派蔡行遇率兵驻守郓州',37,'十二月，','戍郓州。',[('帝','派蔡行遇率兵驻守郓州'),('蔡行遇','以左领军卫将军身份率兵驻郓州')],when='943年十二月乙巳朔',place='郓州')
sup('cai_yunzhou_garrison',37,'jiuwudaishi-082-943-winter','十二月乙巳朔，遣左領軍衛將軍蔡行遇押兵士屯於鄆州，','《旧五代史》也记十二月乙巳朔派蔡行遇驻郓州。','两书记官职与日一致，原文鄆字保留。')
add('yang_kidnaps_zhai','杨光远派骑兵入淄州，将刺史翟进宗劫往青州',37,'杨光远遣骑兵','归于青州。',[('杨光远','派骑兵劫走淄州刺史'),('翟进宗','被劫往青州')],when='943年十二月条下，具体日期未载',place='淄州至青州',note='此句仅写劫持，不将被劫当日直接作为死亡日。')
sup('yang_kidnaps_zhai',37,'jiuwudaishi-082-943-winter','淄州奏，青州節度使楊光遠反，遣兵士取淄州，劫刺史翟進宗入青州。','《旧五代史》也载淄州奏报杨光远反叛，并派兵取淄州、劫翟进宗入青州。','奏报放在十二月丁卯条后，发生日未单列，不把奏日当作劫持日。')
E['zhai_dies_rebellion']=event('zhai_dies_rebellion','《新五代史》记翟进宗在杨光远反叛中死亡',37,'平盧軍節度使楊光遠反，淄州刺史翟進宗死之。',[('翟进宗','在杨光远反叛中死亡')],source='xinwudaishi-009-943-return',when='943年十二月，具体日期未载',place='地点未载',note='独立记死亡，不把主书劫往青州直接解释为同日杀害；死之不补具体行刑者。')
for x in B['people']:
 if x['name']=='翟进宗':x['death_year']=943
claim('person',people['翟进宗'],'death_year','《新五代史》本纪记翟进宗于943年十二月杨光远反叛中死亡。',37,'平盧軍節度使楊光遠反，淄州刺史翟進宗死之。','死亡明确，具体日期与方式未载。',source='xinwudaishi-009-943-return',relation='adds')
add('chengzuo_dengzhou','后晋调杨承祚为登州刺史，以迁就他',37,'甲寅，','以从其便。',[('帝','将杨承祚调为登州刺史'),('杨承祚','被调任登州刺史')],when='943年十二月甲寅',place='登州')
sup('chengzuo_dengzhou',37,'jiuwudaishi-082-943-winter','甲寅，以單州刺史楊承祚為登州刺史，從其便也。','《旧五代史》也记十二月甲寅调杨承祚为登州刺史。','调任不等于证明其已到任。')
add('yang_invites_khitan_attack','杨光远密告契丹，声称后晋饥困、违盟，劝其趁机进攻',37,'光远益骄，','一举可取；',[('杨光远','密告契丹并劝趁后晋饥困进攻')],when='943年十二月条下，具体日期未载',place='青州、契丹',note='国中困竭和一举可取是杨光远对契丹的说法；灾荒另有年末记载，一举可取不当事实结论。')
add('zhao_urges_attack_again','赵延寿也劝契丹进攻后晋',37,'赵延寿','亦劝之。',[('赵延寿','在杨光远密告时也劝契丹进攻后晋')],place='契丹',note='承接本段密告场景，不与此前943年其他外交劝攻记录强合为同一次。')
add('khitan_gathers_fifty_thousand','耶律德光集山后和卢龙兵五万人，由赵延寿统率',37,'契丹主乃集','经略中国，',[('契丹主','集兵五万，交赵延寿统率并筹划夺取中原'),('赵延寿','统率五万人，负责筹划夺取中原')],place='山后、卢龙',note='原文兵数五万保留；集兵和委任不等于此刻已经攻陷后晋。')
add('khitan_promises_zhao_throne','耶律德光许诺攻取中原后立赵延寿为帝，赵延寿因此尽力谋划',37,'曰：“若得之，','之策。',[('契丹主','以取得中原为条件，许诺立赵延寿为帝'),('赵延寿','相信许诺，尽力为契丹筹划夺取中原')],place='契丹',note='许诺和指称未来之主，不建立赵延寿已经即帝位的事件。')
add('jin_fortifies_south_le','后晋得知契丹谋划，派人筑南乐及德清军城防并征调附近兵力',37,'朝廷颇闻',None,[('帝','派人筑城、征调附近军队防备契丹')],when='943年十二月丙辰',place='南乐、德清军',note='城为筑修城防，不新造同名城市；近道未列具体军额。')
# 38–39: factional conflict and loosely administered frontier submission.
add('zhou_complains_song','周宗向李璟哭诉宋齐丘结党排挤，李璟因此疏远宋齐丘',38,'唐侍中','薄齐丘。',[('周宗','向李璟哭诉受到宋齐丘排挤'),('宋齐丘','结党排挤周宗，受到李璟疏远'),('唐主','听周宗哭诉后疏远宋齐丘')],place='南唐',note='唐王、唐主均结合在位上下文指李璟，不另外建立唐王人物。')
add('song_zhenhai_transfer','陈觉被疏远后，李璟将宋齐丘调出任镇海节度使',38,'既而陈觉','节度使。',[('陈觉','受到疏远'),('唐主','将宋齐丘调出任镇海节度使'),('宋齐丘','调出任镇海节度使')],place='镇海',note='原文未展开陈觉被疏远的具体缘由，不补为其已被流放。')
add('song_requests_jiuhua','宋齐丘愤怒，上表请求回九华山旧隐居地，李璟批准',38,'齐丘忿怼，','公志。”',[('宋齐丘','上表请求回九华山隐居'),('唐主','批准请求并赐信说明不挽留')],place='九华山',note='知其诈是史书对李璟判断的记载，不把欺诈动机写为独立确证。')
add('song_qingyang_title','李璟赐宋齐丘九华先生号，封青阳公，给一县租税',38,'仍赐号','租税。',[('唐主','赐号、封爵并给宋齐丘一县租税'),('宋齐丘','获九华先生号、青阳公爵及一县租税')],place='青阳')
add('song_builds_qingyang','宋齐丘在青阳建大宅，服饰和随从如王公，仍很愤懑',38,'齐丘乃治',None,[('宋齐丘','在青阳建大宅，服饰及随从规模如王公')],place='青阳',note='如王公是史书比较，不代表宋齐丘在此称王。')
add('mo_submits_chu','宁州酋长莫彦殊率温那等十八州归附楚国',39,'宁州',None,[('莫彦殊','率所部温那等十八州归附楚国')],place='宁州、温那等十八州',note='史称十八州无官府、立牌羁縻，不按现代行政州界绘制或补坐标。')
# 40: yearly disaster, collection policies and next-spring grain sale.
add('drought_spring_summer','943年春夏发生旱灾',40,'是岁，','春夏旱，',[],when='943年春夏',place='史书未逐州列出旱灾范围')
add('flood_autumn_winter','943年秋冬发生水灾',40,'秋冬水，','秋冬水，',[],when='943年秋冬',place='史书未逐州列出水灾范围')
add('locusts_year_end','943年大范围蝗灾，竹木叶被吃尽',40,'蝗大起，','竹木叶俱尽。',[],when='943年，具体月份未载',place='东至海边、西至陇坻、南逾江湖、北抵幽蓟',note='这是蝗灾描述的范围，不将同一范围自动用于旱灾与水灾。')
add('grain_collection_seals_mills','后晋催征民粮，封闭舂米和磨粮设施，处死藏粮者，部分县令辞职',40,'重以官括','自劾去。',[],when='943年征粮期间，具体日期未载',place='后晋',note='封碓硙为禁止加工粮食，不能直接译成没收全部磨坊；未具名官吏不造人物。')
add('famine_deaths_year','《资治通鉴》记943年数十万人饿死，流亡者众多',40,'民馁死者','不可胜数。',[],when='943年全年概述',place='后晋灾区',note='数十万为史书记数，流亡不可胜数不自行补精确总数。')
sup('famine_deaths_year',40,'jiuwudaishi-082-943-winter','是冬大饑，河南諸州餓死者二萬六千餘口。','《旧五代史》另记当年冬季河南诸州饥荒，饿死二万六千余人。','冬季河南诸州与主书全年更广范围不同，独立保留不相加，也不据数字不同断言冲突。',relation='adds')
add('officials_donate_supplies','后晋留守、节度使及将军等献马、金帛和粮草助国',40,'于是留守','以助国。',[],place='后晋',note='集体行动未逐一具名，不把全站所有节度使自动列为参与者。')
add('heng_ding_exemption','后晋因恒州、定州饥荒特别严重，免除两州搜括民粮',40,'朝廷以恒、','不括民谷。',[('帝','因两州饥荒严重而免搜括民粮')],place='恒州、定州')
add('du_requests_collection','杜重威以军粮不足请求照其他州搜括民粮，朝廷批准',40,'顺国节度使','许之。',[('杜威','以军粮不足请求搜括民粮'),('帝','批准杜重威请求')],place='恒州',note='沿用杜重威稳定主体，杜威为避讳时用名；许之明确批准，搜括结果另记。')
add('du_wang_collect_million','杜重威采用判官王绪的办法，搜括粮食一百万斛',40,'威用判官','得百万斛。',[('杜威','采用王绪办法搜括粮食'),('王绪','提出搜括民粮的办法')],place='恒州',note='王绪是本地判官，与885年光州王绪不同；与其他后晋同名者未证同人。')
add('du_underreports_grain','杜重威只上报三十万斛，其余搜得粮食收入自己家中',40,'威止奏','入其家；',[('杜威','只上报三十万斛，将其余粮食收入私家')],place='恒州',note='不自动折算现代重量或自行推算隐瞒比例。')
add('li_zhao_borrows_grain','杜重威又命李沼向百姓借粮，所得再达一百万斛',40,'又令判官','复满百万斛，',[('杜威','命判官李沼向民间借粮'),('李沼','向百姓借粮，所得达一百万斛')],place='恒州',note='称贷是借粮，不与前一百万斛搜括记录合成同一次收粮。')
add('du_sells_grain_next_spring','杜重威将所借粮食在次年春出售，得钱二百万缗',40,'又令判官','阖境苦之。',[('杜威','在次年春出售借得粮食，得二百万缗')],year=944,when='944年春，943年末条追述后续结果',place='恒州',note='来春明确跨到944年春；当前录入943年段落，不因此标944年主线已完成。')
add('ma_refuses_collection','马全节拒绝定州官吏援例搜括民粮，称应以养民为职',40,'定州吏',None,[('马全节','拒绝官吏请求，不愿效仿杜重威搜括民粮')],place='定州',note='吾为观察使是马全节的话，不覆盖史书所列义武节度使职衔。')
# 41: prior reign-wide conduct has no fixed start year; 943 levy is explicit.
oldtime=dict(year=None,when='马希范在位期间的政策或行为概述，具体年月未载',place='楚国',note='此段先概述在位行为，直到是岁才明确943年；不把此前全部措施强定943年。')
add('chu_gold_weapons','马希范制作金饰长枪大槊，史书记其可持而难以实用',41,'为长枪','不可用。',[('马希范','制作金饰长枪大槊')],**oldtime)
add('chu_silver_spear_corps','马希范招募富户年轻人八千名，组成银枪都',41,'募富民','银枪都。',[('马希范','招募八千名富户年轻人组成银枪都')],**oldtime)
add('chu_nine_dragon_hall','马希范建九龙殿，以八条沉香金饰龙绕柱，将自己比作第九条龙',41,'作九龙殿，','以象龙角。',[('马希范','建九龙殿并以自己的装束象征第九条龙')],**oldtime)
sup('chu_nine_dragon_hall',41,'xinwudaishi-066-chu-palace','希範又作九龍殿，以八龍繞柱，自言身一龍也。','《新五代史》也记马希范建九龙殿，八龙绕柱，自称为另一龙。','下文晋亡背景属于其他后续事，不据此把建殿自动定为947年。')
add('chu_inflates_acreage','楚国用度不足而加赋，查田使者以增加登记亩数为功，百姓因租赋逃亡',41,'用度不足，','何忧无谷！”',[('马希范','因用度不足加赋，并称只要田在便不愁粮')],**oldtime)
add('deng_registers_abandoned_fields','马希范命邓懿文登记逃田、招募新耕户缴租，百姓迁移后失去原有生计',41,'命营田使','各失其业。',[('马希范','命邓懿文登记逃田、招民耕种缴租'),('邓懿文','登记逃田、招募新耕户')],**oldtime)
add('chu_sells_offices','楚国允许交钱获官，按财物多少定官职高低',41,'又听人','布在列位。',[('马希范','允许按交付财物多少授官')],**oldtime)
add('chu_requires_official_gifts','楚国外任官员回来时，被要求贡献财物',41,'外官还者，','必责贡献。',[('马希范','要求外任官员返回时献财物')],**oldtime)
add('chu_unequal_penalties','楚国按财富和体力区别处置有罪者，贫弱者受刑',41,'民有罪，','惟贫弱受刑。',[('马希范','统治下出现富者交财、强者充军、贫弱受刑的处罚方式')],**oldtime)
add('chu_anonymous_accusations','楚国设函收匿名告密书，曾有人因此遭灭族',41,'又置函，','至有灭族者。',[('马希范','设函收匿名告密书')],**oldtime)
add('chu_extra_rice_levy','马希范采周陟建议，在常税外加征各县贡米，无米者交布帛',41,'是岁，用孔目官','无米者输布帛。',[('马希范','采用周陟建议加征贡米'),('周陟','提出追加贡米办法')],when='943年，具体月份未载',place='楚国',description='马希范采用周陟建议，在常税之外令大县贡米二千斛、中县一千斛、小县七百斛；无米者交布帛。')
add('tuoba_petition_against_levy','拓跋恒上书批评马希范奢侈，建议罢贡米、处死周陟并减工程',41,'天策学士','王大怒。',[('拓跋恒','上书批评奢侈和重赋，提出罢贡米、处死周陟等建议'),('马希范','收到劝谏后生气')],when='943年贡米令后，具体日期未载',place='楚国',note='奏疏中的邻国威胁和民怨为拓跋恒的判断；请求诛周陟不等于周陟已被处死。')
add('tuoba_audience_refused','拓跋恒求见马希范，马希范以午睡为由拒绝',41,'他日，','辞以昼寝。',[('拓跋恒','在劝谏后再次求见'),('马希范','以午睡为由拒绝接见')],when='943年上书后另一天，确切日期未载',place='楚国',note='辞以昼寝是拒绝理由，不单独证明马希范此刻确在睡觉。')
add('tuoba_warns_qu','拓跋恒向区弘练表示，马希范纵欲拒谏，家族可能面临流离',41,'恒谓客将','无日矣。”',[('拓跋恒','向区弘练表达对马氏家族前景的忧虑'),('区弘练','听取拓跋恒的话')],when='943年上述求见被拒之后，具体日期未载',place='楚国',note='千口飘零为拓跋恒的预言，不记成马氏家族此时已经流亡。')
add('ma_stops_receiving_tuoba','马希范更加生气，此后终身不再接见拓跋恒',41,'王益怒，',None,[('马希范','此后不再接见拓跋恒'),('拓跋恒','此后未再受到马希范接见')],year=None,when='943年劝谏后直到马希范去世的回顾，未据本句确定终点年份',place='楚国',note='终身为追述跨度，不把终止接见与终身终点都记成943年。')
claim('event',E['tuoba_petition_against_levy'],'description','《新五代史》另记马希范建会春园、嘉宴堂时加赋，拓拔常反对。',41,'希範作會春園、嘉宴堂，其費鉅萬，始加賦於國中，拓拔常切諫以為不可。','加赋场景与主书贡米令不强认同一次，拓拔常与拓跋恒姓名异文待核，不自动合并新主体。',source='xinwudaishi-066-chu-palace',relation='adds')
# 42: another Liu Zan; marriage and death dates are not explicit.
mt=dict(year=None,when='王延羲在位时嫁女相关记载，确切年月未载',place='闽国')
add('min_punishes_noncongratulation','王延羲嫁女，查班簿后杖责十二名未道贺的朝士',42,'闽主曦','杖之于朝堂。',[('曦','查班簿并杖责十二名未道贺朝士')],**mt,note='未具名女儿与十二朝士不虚建人物；新史尝嫁女也为追述，无精确日期。')
add('min_orders_liu_zan_caning','王延羲因刘赞未弹劾朝士而准备杖责他，刘赞想自杀',42,'以御史中丞','欲自杀。',[('曦','准备杖责未弹劾朝士的御史中丞'),('刘赞','不愿受辱，产生自杀念头')],**mt,note='将杖与欲自杀均未写执行，不登记已经受杖或此时自杀身亡。')
add('zheng_saves_liu_zan','郑元弼劝谏王延羲，王延羲怒气缓解，释放刘赞',42,'谏议大夫','乃释赞，',[('郑元弼','劝王延羲不要杖责御史中丞'),('曦','听劝后释放刘赞'),('刘赞','获得释放')],**mt,note='魏征和唐太宗仅作为对话中的比喻，不建立他们参与此次闽国事件的图谱边。')
sup('min_punishes_noncongratulation',42,'xinwudaishi-068-liu-zan','曦嘗嫁女，朝士有不賀者笞之。','《新五代史》也记王延羲嫁女时杖责未道贺朝士。','该书未给十二人数，不用它单独支持具体人数。')
sup('zheng_saves_liu_zan',42,'xinwudaishi-068-liu-zan','曦喜，乃釋贊不笞。','《新五代史》记王延羲听郑元弼劝谏后高兴，释放刘赞，没有杖责。','主书写怒稍解，新史写喜，各自保留情绪表述；都支持释放，不支持已杖。')
add('liu_zan_min_dies','《资治通鉴》记闽国刘赞获释后最终忧郁而死',42,'赞竟',None,[('刘赞','获释后最终忧郁而死')],year=None,when='上述释放后的追述，死亡确切年月未载',place='闽国',note='竟以忧卒是后续结果，不据此直接填943年死亡；不与前蜀或秦王傅刘赞混同。')
reviews={34:'仰氏个人名未知，纳妃与皇后区分，父女关系明确。',35:'石敬瑭借马追述年份空；杨光远疑朝廷与承祚称母病均为当事人说法。秘密召、夜逃、权知单州、赐物和郭谨戍郓分开。',36:'安葬与此前二月死亡分开，唐号据新史廟號校读，原字保留。',37:'蔡戍、翟被劫、调任、密告、劝攻、集兵、许诺与后晋防备分开。翟死由新史独补，具体死日不造；赵受帝位是条件许诺。',38:'唐王唐主均指李璟；党争、调任、乞归获准、赐号封爵租税与造宅分开。',39:'十八州无官府，羁縻不等现代行政接管，无坐标。',40:'春夏旱与秋冬水及蝗灾范围分别处理。粮征、刑罚、饥死、捐献、豁免、杜请求获准与搜括隐报借粮、944春卖粮和马拒征分开。河南冬二万六千与全域数十万不相加；王绪判官与晚唐同名人分开。',41:'是岁之前为在位概述未知年份；贡米943明确。建殿、军队、行田逃田、卖官、处罚告密逐项录。奏议不变事实，处死建议无已执行；终身拒见终点不定943。拓拔常异文待核。',42:'闽御史中丞刘赞与923前蜀嘉州司马、秦王傅分档；将杖、欲自杀非已执行，获释忧卒未知年。比喻人物不参与。'}
assert not (P/'publication.json').exists()
for n in range(34,43):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=283,year=943,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(34,43)],next_paragraph='zztj-v283-y0944-p001',next_volume=283,next_year=944,supplements=supplements,excluded_non_body=[],source_contexts=[dict(source_key='tongjian-283-943-min-liu-zan',note='快照跨到944年开篇，本批只引用943年界前嫁女、劝谏及死亡追述，944主线未录。'),dict(source_key='xinwudaishi-066-chu-palace',note='只补楚国加赋、劝谏和建殿背景，晋亡及丁思覲后续本批未录。')],coverage='连续第34—42段，原82—90行，943年末正文完成后接卷283的944年开篇。',source_issues_review='王绪判官和闽刘赞分别与既有同名人物分档；拓拔常与拓跋恒异文待核；唐号按新史庙号校读。年末概述与追述分时，数字范围并列，纸本待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(34,43)],plain_language_review='首次逐项检查标题、正文、人物、参与角色、亲属关系和事实说明，明确行动主语；诏令、声称、劝谏、执行与追述分清，引用原字保留。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
