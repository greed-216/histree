# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 287, year 948 paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,20))
COMMIT='81c86a2a7b16e48591c2de043347d16f153f6a6a'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-287-947-year-end-wuyue']:
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
main_sources = ['tongjian-287-947-year-end-wuyue','tongjian-287-948-return-to-han','tongjian-287-948-january-february']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0948-p001-p008',
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
lines = (ROOT / 'resources/derived/tongjian/287.txt').read_text().splitlines()
for n in range(1, 9):
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
        citation = f'卷287·乾祐元年（948年正月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0948_01_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=948, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='948年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_287_0948_' + code
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
        edge = 'participation_zztj_287_0948_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_287_0948_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','暠':'刘知远','匡赞':'赵匡赞','贊':'赵匡赞','赵贊':'赵匡赞','赵赞':'赵匡赞','景崇':'王景崇','恕':'李恕（赵匡赞判官）','李恕':'李恕（赵匡赞判官）','弘亻叔':'钱弘俶','弘倧':'钱弘倧','承训':'刘承训','思绾':'赵思绾'})
NEW_ALIASES={'齐藏珍':['齊藏珍'],'李恕（赵匡赞判官）':['李恕（晋昌判官）'],'薛温':['薛溫'],'赵思绾':['趙思綰']}
NEW_DESCRIPTIONS={'齐藏珍':'后汉将军。948年正月与王景崇率禁军迎接回鹘贡使并经略关西。其后建议杀赵思绾，王景崇没有听从。生卒年未载。','李恕（赵匡赞判官）':'晋昌节度判官，曾在赵延寿幕下受信任，后随其子赵匡赞。948年劝赵匡赞不要入蜀，代其入朝申明归降后蜀的原因，请求入朝，获刘知远同意。与其他年代同名人物是否有关，未作无证合并。生卒年未载。','薛温':'吴越匡武都头。948年正月奉钱弘俶命，率亲兵守护被废的钱弘倧，并受密令抵御异常处置。生卒年未载。','赵思绾':'魏州人，原在赵在礼军中，后来成为赵匡赞牙将。948年王景崇试图令赵匡赞牙兵刺面防逃时，主动提出先刺自己以率众。齐藏珍建议将其杀死，王景崇不听。生卒年尚未录入。'}
j='jiuwudaishi-100-january-948';zhao='songshi-254-zhao-kuangzan-li-shu';xue='songshi-480-xue-wen-protection';old='jiuwudaishi-109-zhao-siwan-origin';new='xinwudaishi-053-zhao-siwan-tattoo';commission='xinwudaishi-053-zhao-siwan-commission';t='948年正月，具体日未载'
add('ganyou_amnesty','刘知远大赦，改元乾祐',1,'春，',None,[('帝','大赦并改元乾祐')],when='948年正月乙卯',place='后汉朝廷',note='乾祐名据本年标题与旧本纪明确改元；不换算现代月日。')
sup('ganyou_amnesty',1,j,'乙卯，制：「大赦天下，改天福十三年為乾祐元年。自正月五日昧爽已前，犯罪人除十惡五逆外，罪無輕重，咸赦除之。」','《旧五代史》同记乙卯改元乾祐，补明大赦除十恶五逆外、以正月五日黎明前为界。','只记录诏令范围，不推所有囚犯都已出狱或政治罪案全无例外。',relation='adds')
add('liu_concerned_western_coalition','刘知远担忧赵匡赞、侯益与蜀军共同侵扰',2,'帝以','患之。',[('帝','担忧关西形势'),('匡赞','被记为与蜀兵共同侵扰'),('侯益','被记为与蜀兵共同侵扰')],when=t,place='后汉朝廷、关西',note='患之为史家叙述的担忧，不额外推有签署固定同盟条约。')
add('uyghur_envoys_request_escort','回鹘贡使诉称遭党项阻路，请后汉出兵接应',2,'会回鹘入贡，','乞兵应接。',[],when=t,place='回鹘来贡线路',note='党项阻碍是贡使诉称，未具具体交战地点、使者姓名或死伤，均不补造。')
add('wang_qi_western_commission','刘知远派王景崇、齐藏珍率禁军迎回鹘并经略关西',2,'诏右卫大将军',None,[('帝','派两将率数千禁军接应，兼经略关西'),('景崇','以右卫大将军身份率军'),('齐藏珍','以将军身份共同率军')],when=t,place='后汉朝廷至关西',note='数千为约数，派遣命令区别到长安及战蜀的实际行动。')
sup('wang_qi_western_commission',2,commission,'高祖遣王景崇至永興，與齊藏珍以兵迎回鶻，陰以西事屬之。','《新五代史》也记派王景崇与齐藏珍迎回鹘，并暗中托付西部事务。','该传写永兴，主书此时长安军号仍晋昌，之后更名另录；不据后用军号提前改名。',relation='adds')
add('li_shu_prior_service','李恕曾在赵延寿幕下，受派辅佐赵匡赞',3,'晋昌节度判官','延寿使之佐匡赞。',[('李恕','曾在赵延寿幕下，受派佐赵匡赞'),('赵延寿','派李恕辅佐其子'),('匡赞','得到李恕辅佐')],year=None,when='948年正月之前的幕府经历，具体起年未载',place='赵延寿及赵匡赞幕府',note='久在表示长期，不能据此反推出具体任职年。')
sup('li_shu_prior_service',3,zhao,'判官李恕者，本延壽賓佐，深所委賴，至家事亦參之。及贊出鎮，從為上介。','《宋史》记李恕深受赵延寿信赖，参与家事，赵匡赞出镇后随任上介。','上介为幕府上佐，此句没有具体初任年月；赵贊沿赵匡赞主体。',relation='adds')
add('li_shu_dissuades_zhao_shu','李恕劝赵匡赞不要入蜀，建议谢罪归朝',3,'匡赞将入蜀，','必保富贵。',[('匡赞','准备入蜀，受到劝阻'),('恕','建议谢罪归后汉')],when=t,place='长安',note='赵延寿入契丹非自愿、归朝必保富贵及入蜀不全是李恕劝说内容，归属说话者，不直接当作命运事实。')
claim('event',E['li_shu_dissuades_zhao_shu'],'description','李恕还说入蜀难保全，以蹄涔不容尺鲤劝赵匡赞改变计划。',3,span(3,'入蜀非全计也','公必悔之。”'),'原分段把同一劝说拆在相邻两条，分别引用逐字快照，保留来源边界。')
sup('li_shu_dissuades_zhao_shu',3,zhao,'公若泥首歸朝，必保富貴，狠狽入蜀，理難萬全。','《宋史》也记李恕劝归朝、认为入蜀难保全。','狠狽字形照底本保留，劝说的保证不等于朝廷已授官；该书后来的具体任命暂不提前录。')
add('zhao_sends_li_shu_petition','赵匡赞派李恕奉表请求入朝',3,'匡赞乃遣','恕奉表请入朝。',[('匡赞','派判官奉表'),('恕','奉表请求赵匡赞入朝')],when=t,place='长安至后汉朝廷',note='奉表请求与获准、本人实际入见分别整理。')
add('li_shu_explains_zhao_motive','李恕先到朝廷，向刘知远解释赵匡赞附蜀的原因',3,'景崇等未行','故遣臣来祈哀。”',[('恕','在王景崇出发前到朝廷，解释赵匡赞担忧不被接纳'),('帝','询问赵匡赞为何附蜀'),('匡赞','其附蜀原因由判官作解释')],when='948年正月王景崇等出发之前，具体日未载',place='后汉朝廷',note='解释是李恕的陈述，不用此句确认赵延寿当时处境的全部事实，也不记王景崇已出发。')
add('liu_allows_zhao_to_court','刘知远表示不忍加害赵匡赞，准其入朝',3,'帝曰：','即听其入朝。',[('帝','说父子受困契丹不幸，同意赵匡赞入朝'),('匡赞','入朝请求获准')],when=t,place='后汉朝廷',note='帝说延寿方坠槛阱属于此时言论，与947年赵延寿死讯传闻及异说分别保留，不据此强定生卒日。')
sup('liu_allows_zhao_to_court',3,zhao,'漢祖曰：「贊之父子亦吾人也，事契丹出於不幸。今聞延壽落於陷穽，吾忍不容贊耶？」','《宋史》也记刘知远以赵氏父子受困契丹为不幸，表示愿接纳赵匡赞。','记录当事人所言，不以宋传转述填赵延寿实际死亡日。')
add('hou_requests_birthday_audience','侯益请求在二月四日圣寿节赴朝祝寿',3,'侯益亦请','圣寿节上寿。',[('侯益','请求赴刘知远生日庆典')],when='948年正月提出请求，拟赴二月四日圣寿节',place='凤翔至后汉朝廷（拟赴）',note='二月四日是拟赴节日，不作为请求提出或实际到达日期。')
add('liu_secret_discretion_order','刘知远密令两将，按赵匡赞、侯益是否入朝决定处置',3,'景崇等将行，',None,[('帝','出发前私下授权两将视赵侯是否入朝作处置'),('景崇','受到密令'),('齐藏珍','随王景崇共同受密令'),('匡赞','成为密令所涉对象'),('侯益','成为密令所涉对象')],when='948年正月两将出发之前，具体日未载',place='皇帝卧内',note='便宜从事为依情况酌处的授权，不能直接写成无条件密令杀赵侯；已入朝勿问这一条件必须保留。')
add('liu_renames_gao','刘知远改名暠',4,'己未，',None,[('帝','改名为暠')],when='948年正月己未',place='后汉朝廷',note='刘知远与刘暠是同人，沿稳定主体，不新建皇帝。')
sup('liu_renames_gao',4,j,'己未，改御名為暠。','《旧五代史》同记己未改御名暠。','保留暠字，不误作皓、晧；本站主体仍复用刘知远。')
add('feng_dao_grand_preceptor','冯道获任太师',5,'以前',None,[('冯道','以前威胜节度使身份获任太师')],when=t,place='后汉朝廷',note='原文未给任命独立干支，不把前句己未自动当授官日。')
sup('feng_dao_grand_preceptor',5,j,'以前鄧州節度使、燕國公馮道為守太師，進封齊國公。','《旧五代史》记冯道由前邓州节度使、燕国公任守太师，并进封齐国公。','邓州与威胜为州名军号对应，补书增加原爵及新爵，不自动继承前句辛酉为此任命日。',relation='adds')
add('qian_moves_protects_brother','钱弘俶将钱弘倧迁到衣锦军私第，派薛温率亲兵保护',6,'壬戌，','将亲兵卫之。',[('弘亻叔','迁故王并派兵保护'),('弘倧','被迁入衣锦军私第，受保护'),('薛温','以匡武都头身份率亲兵守卫')],when='948年正月壬戌',place='衣锦军私第',note='衣锦军为主书地点，宋传称越州、前新史东府属不同叙述；不虚构实际迁徙路线。')
sup('qian_moves_protects_brother',6,xue,'初，俶為胡進思所立，廢其兄倧，徙越州，資給豐厚。','《宋史》钱俶传记故王钱弘倧被迁越州，供给丰厚。','与通鉴衣锦军地点不同，书别位置各自保留，不据广域词硬作完全相同驻处。',relation='conflicts')
add('qian_secret_order_xue','钱弘俶密令薛温以死抵御针对故王的异常命令',6,'潜戒之曰：',None,[('弘亻叔','密戒异常处置不代表己意，要求死拒'),('薛温','受密令保护故王'),('弘倧','成为秘密保护对象')],when='948年正月壬戌',place='吴越',note='异常命令不等于合法王命，后续胡伪命害王待下段实际记载；此时不提前录薛已击杀刺客。')
sup('qian_secret_order_xue',6,xue,'俶慮進思害倧，遣親將薛溫為倧守衛，戒之曰：「委汝以保全廢王，苟有非常，汝當以死捍之。」','《宋史》同记钱俶担忧胡进思害故王，派薛温守卫，令其以死捍卫。','该传补明所忧对象是胡进思，后句刺客与胡卒不能提前为正月壬戌当天。',relation='adds')
add('liu_ill_after_son_death','刘知远因刘承训去世悲痛，甲子开始生病',7,'帝自',None,[('帝','因儿子死后悲痛过度而病'),('承训','此前死亡成为史述病因背景')],when='948年正月甲子',place='后汉',note='悲痛过甚与病因关联为主书叙述，不作现代医学诊断，不提前记为当日死亡。')
sup('liu_ill_after_son_death',7,j,'甲子，帝不豫。','《旧五代史》同记甲子皇帝生病。','该句没有独立确认悲痛病因，病名与症状未载，不补医学解释。')
add('zhao_enters_court','赵匡赞没等李恕回来，就离开长安入见刘知远',8,'赵匡赞不俟','丙子，入见。',[('匡赞','未等判官返命即离镇，丙子入见'),('恕','其返命尚未被赵等待'),('帝','接受赵匡赞入见')],when='948年正月丙子入见，离开长安日未载',place='长安至后汉朝廷',note='离镇与丙子入见不是同一日，未臆造路程时长。')
sup('zhao_enters_court',8,zhao,'恕未還，贊已離鎮入朝，','《宋史》也记李恕未回，赵匡赞已离镇入朝。','与主书丙子入见相合于过程，不提供独立干支。')
add('wang_recruits_zhao_troops','王景崇到长安后，征调当地与赵匡赞牙兵抵御蜀军',8,'王景崇等至长安，','同拒之。',[('景崇','因兵少，征调本道及赵匡赞牙兵'),('齐藏珍','与王景崇赴长安共御蜀兵'),('匡赞','其牙兵被调发')],when='948年正月王景崇抵长安后，具体日未载',place='长安、秦川',note='千余是调发所述约数，不作为其原有禁军总数；闻蜀已入秦川与战斗获胜分录。')
add('wang_proposes_face_tattoo','王景崇担忧牙兵逃走，暗示想在他们脸上刺字',8,'景崇恐','微露风旨。',[('景崇','担忧逃兵，暗示刺面意图')],when='948年正月关西行军期间，具体日未载',place='长安一带',note='欲文其面及微露是意图与暗示，刺面指在脸上刺字，未明载全军已完成。')
add('zhao_siwan_volunteers_tattoo','赵思绾请求先在自己脸上刺字带头，王景崇赞许',8,'军校赵思绾，','景崇悦。',[('思绾','提出先给自己刺面以带头'),('景崇','对提议表示满意')],when='948年正月关西行军期间，具体日未载',place='长安一带',note='首请为主动请求，不直接写成已执行刺面；以帅下指率其部下，不误译为斩首。')
sup('zhao_siwan_volunteers_tattoo',8,old,'景崇微露風旨，思綰厲聲先請自刺，以率其下，景崇壯之。','《旧五代史》赵思绾传也记暗示刺面、赵先请自刺、王赞许。','传记仍写请求，不据此断定具体刺面完成日。')
sup('wang_proposes_face_tattoo',8,new,'景崇用思綰兵擊走之。遂與思綰俱西，然以非己兵，懼思綰等有二心，意欲黥其面以自隨，','《新五代史》把用赵思绾兵击退蜀军，接在西行拟刺面之前。','与主書在段内先叙拟刺面再叙击蜀次序不同，保留其叙事顺序，不据此覆盖主书纪时。',relation='adds')
add('qi_proposes_kill_zhao_rejected','齐藏珍建议杀赵思绾，王景崇没有听从',8,'齐藏珍窃言曰：','景崇不听。',[('齐藏珍','认为赵难制，秘密建议杀他'),('景崇','没有听从杀人建议'),('思绾','成为被提议杀害对象，未被执行')],when='948年正月关西行军期间，具体日未载',place='关西军中',note='凶暴难制为齐的评价，主书记未听，不能记成赵此时已死。')
sup('qi_proposes_kill_zhao_rejected',8,new,'齊藏珍惡之，竊勸景崇殺思綰，景崇不聽，與俱西。','《新五代史》也记齐藏珍密劝杀赵思绾，王景崇不听，继续共同西行。','恶之为该书心理描述，未增添无载处罚。')
claim('person',people['赵思绾'],'description','赵思绾是魏州人。',8,'思绾，魏州人也。','籍贯与当前军中所在地分清。')
claim('person',people['赵思绾'],'description','《旧五代史》记赵思绾早先隶属赵在礼，后来随赵匡赞。',8,'唐同光末，趙在禮之據魏城也，思綰隸於帳下，累從之。','这是同光末起的早期经历，不当作948年首次从军；赵贊沿赵匡赞。',source=old,relation='adds')
add('li_tinggui_plans_retreat','李廷珪将到长安，得知赵匡赞入朝后打算退兵',8,'蜀李廷珪将','欲引归，',[('李廷珪','将到长安，闻赵入朝后欲退'),('匡赞','其入朝消息改变蜀军动向')],when='948年正月，具体日未载',place='长安附近',note='将至不等于已经入城，欲归是意图，实际被邀击后退另录。')
add('wang_defeats_li_ziwu','王景崇拦击李廷珪，在子午谷将其击败',8,'王景崇邀之，','败廷珪于子午谷。',[('景崇','截击蜀军并获胜'),('李廷珪','在子午谷遭击败')],when=t,place='子午谷',note='邀之为军事截击，不写成礼仪邀请；未载损失人数，不补造。')
add('zhang_stalls_baoji','张虔钊到宝鸡，因诸将意见不合而按兵不进',8,'张虔钊至宝鸡，','按兵未进。',[('张虔钊','驻宝鸡，因诸将议不协未进军')],when=t,place='宝鸡',note='未载参与争议各将姓名，不能把全军称为已溃逃，此时先记停驻。')
add('hou_rejects_shu_forces','侯益得知李廷珪西返，闭城拒绝蜀军',8,'侯益闻','因闭壁拒蜀兵，',[('侯益','闭城不纳蜀军'),('李廷珪','其西返消息成为侯益闭城背景')],when=t,place='凤翔',note='与此前请降蜀、请求援兵明确区分立场变化，未写侯益此时已经到朝廷。')
add('zhang_retreats_at_night','张虔钊势孤，连夜撤兵',8,'虔钊势孤，','引兵夜遁。',[('张虔钊','孤立后夜间撤走')],when='948年正月侯益闭城拒蜀兵之后，具体夜未载',place='凤翔、宝鸡一带',note='未载每路撤军地点与人数，不补精确路线。')
add('wang_pursues_shu_sanguan','王景崇率六州兵追击，在散关败蜀军、俘四百人',8,'景崇帅',None,[('景崇','率凤翔陇邠泾鄜坊兵追击，俘蜀将卒')],when=t,place='散关',note='四百是主书记获俘数，不能当战死数；六州兵是不同地方部队，未载各州兵数。')
reviews={1:'乙卯改元乾祐据本年标题与旧本纪，赦令范围补十恶五逆例外与时界，未写全体出狱。',2:'帝刘知远，回鹘诉党项阻路为使者陈述；命王景崇齐藏珍迎贡兼关西经略，命令与实际行军区别，新史后用永兴不提前改晋昌名。',3:'李恕久幕为追叙未知年，劝归朝保证与附蜀原因归说话者；奉表、李先至解释、获准、侯拟寿节、出发前便宜敕分录，非无条件杀令。帝说赵父困契丹不据此定赵延寿死日。',4:'更名暠沿刘知远不另建人，己未旧本纪相合。',5:'冯太师授官未独立干支，邓威胜同军州称，旧补齐国公，不套前辛酉。',6:'壬戌迁故王与派薛温、密戒分别录；主衣锦军与宋越州各保位置，不提前后续刺客案。',7:'甲子始病与旧本纪相合，悲痛病因属史家记述，不下现代诊断或提前当卒日。',8:'赵离长安与丙子入见不同日；调千余牙兵、拟刺面、赵主动请、齐杀议被拒、李欲退与子午击败、张宝鸡停、侯拒、张夜退、散关追俘分录。新史先击后拟刺叙次不同，未造全军刺完；俘四百不当死亡。'}
assert not (P/'publication.json').exists()
for n in range(1,9):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=948,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=287,next_year=948,supplements=supplements,excluded_non_body=[],coverage='卷287原83—90行连续八段，本卷累计8/19，948年跨卷287、288累计8/88，未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],source_issues_review='故王迁居衣锦军与宋越州表述、拟刺面与击蜀军叙次并列保留。李恕限定判官身份；赵贊沿赵匡赞，更名暠沿刘知远。旧新原文夹后续叛乱，不提前录入。',plain_language_review='首次核对全部展示与事实说明，写明确主语；授权条件、提议、预测、告发与实际动作分清，旧事未知年用null，逐字摘录原字保留。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
