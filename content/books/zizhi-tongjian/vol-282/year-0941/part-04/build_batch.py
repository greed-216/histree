# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 941 paragraphs 16–21."""
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
specs=[(d.name,d,'85c74eda9d678a1a70ddae003a8d3b3ce4e7932a','薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
prior=next(x for f in (ROOT/'content').rglob('content-batch.json') for x in json.loads(f.read_text())['sources'] if x['key']=='tongjian-282-941-autumn')
commit,relative=prior['url'].split('/blob/')[1].split('/',1)
specs.append((prior['key'],(ROOT/relative).parent,commit,prior['author']))

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
main_sources = ['tongjian-282-941-autumn']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0941-p016-p021',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-080-941-eighth-month':'卷80·晋高祖纪·天福六年八月','xinwudaishi-067-wuyue-fire':'卷67·吴越世家·钱元瓘火灾与患病','xinwudaishi-067-hongzuo-age':'卷67·吴越世家·钱弘佐继位年龄'}
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
lines = (ROOT / 'resources/derived/tongjian/282.txt').read_text().splitlines()
for n in range(16, 22):
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
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'jiuwudaishi-080-941-eighth-month':'卷80·晋高祖纪·天福六年八月','xinwudaishi-067-wuyue-fire':'卷67·吴越世家·钱元瓘火灾与患病','xinwudaishi-067-hongzuo-age':'卷67·吴越世家·钱弘佐继位年龄'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '七月条下' if n<=17 else '八月条下' if n<=20 else '八月至九月'
        citation = f'卷282·后晋天福六年（941；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0941_04_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=941, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='941年'+('七月' if n<=17 else '八月' if n<=20 else '八月至九月')+'条下，具体日期未载'
    key = 'event_zztj_282_0941_' + code
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
        edge = 'participation_zztj_282_0941_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_282_0941_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
def source_span(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end);return t[a:b]

# Curated opening paragraphs.
ALIASES.update({'张昭远':'张昭（五代宋初）','契丹主':'耶律德光'})






ALIASES.update({'唐主':'李昪','曦':'王延羲','延政':'王延政','元瓘':'钱传瓘','重贵':'石重贵','弘佐':'钱弘佐','弘侑':'钱弘侑'})
NEW_DESCRIPTIONS={
'潘承祐':'镇武军节度判官，晋江人。王延羲与王延政交战时，多次劝王延政停战修好；王延政向闽王使者展示军队、言语傲慢时，潘承祐长跪劝谏，受到威胁仍继续进谏。具体年月及生卒年未载。',
'章德安':'吴越内都监，处州人。941年钱传瓘临终时，建议让年轻的钱弘佐继位，并受托辅佐。钱传瓘死后，暂不公布死讯，与诸将商议后拘杀被告谋立钱弘侑的戴恽。生卒年未据本段确定。',
'戴恽':'吴越内牙指挥使，曾受钱传瓘信任，受委掌管军事。戴恽妻子与钱弘侑的乳母有亲属关系。941年钱传瓘去世后，戴恽被告谋立钱弘侑，八月壬子入府时被伏兵拘杀。告发不等于谋立已经查实，出生年未载。',
'钱弘侑':'钱传瓘的养子，本姓孙。941年钱传瓘去世后，有人告发戴恽谋立钱弘侑；章德安与诸将拘杀戴恽，钱弘侑被废为平民，恢复孙姓并幽禁明州。生卒年未载。'}
NEW_ALIASES={'潘承祐':[],'章德安':['章徳安'],'戴恽':['戴惲'],'钱弘侑':['錢弘侑','孙弘侑','孫弘侑']}
old='jiuwudaishi-080-941-eighth-month';fire='xinwudaishi-067-wuyue-fire';age='xinwudaishi-067-hongzuo-age'
add('wuyue_offices_burn','吴越府署失火，宫室和府库几乎烧尽',16,'吴越府署火，','宫室府库几尽。',[],place='吴越',note='几尽是几乎烧尽，不给未载火因、伤亡或损失金额。')
sup('wuyue_offices_burn',16,fire,'天福六年，杭州大火，燒其宮室迨盡，','《新五代史》记天福六年杭州大火，钱传瓘宫室几乎烧尽。','杭州地名由独立传记补充，主书未记具体起火地点，未据此设置地理坐标。',relation='adds')
add('qian_yuanguan_ill','钱传瓘因火灾惊惧而患病',16,'吴越王元瓘','发狂疾，',[('元瓘','因火灾惊惧而患病')],place='吴越',description='钱传瓘因吴越府署火灾惊惧，患上史书所称的狂疾。',note='狂疾是史书记病称谓，不据此诊断现代具体疾病。')
sup('qian_yuanguan_ill',16,fire,'元瓘避之，火輒隨發，元瓘大懼，因病狂，','《新五代史》记，钱传瓘避火后又发生火灾，因极度恐惧而病狂。','火輒隨發保留为史书记述，不补纵火者或把它解释为已经证实的超自然现象。',relation='adds')
add('tang_proposes_exploiting_fire','南唐有人建议李昪乘吴越灾后衰弱攻取吴越',16,'唐人争劝','乘弊取之，',[('唐主','收到乘吴越灾后衰弱出兵的建议')],note='建议者没有姓名，不建立具名人物，建议不当已出兵。')
add('li_bian_rejects_fire_attack','李昪拒绝乘吴越火灾攻取其地',16,'唐主曰：','奈何利人之灾！”',[('唐主','拒绝利用吴越火灾出兵')],description='李昪说，不能利用别人的灾难获利，拒绝乘吴越灾后衰弱出兵的建议。')
add('li_bian_sends_fire_relief','李昪派使者慰问吴越，并帮助补足灾后所缺',16,'遗使唁之，',None,[('唐主','派使者慰问并救济吴越')],note='所缺财物种类与数量未载，使者也未具名。')
add('xi_claims_min_emperor','王延羲自称大闽皇，兼领威武节度使',17,'闽主曦自称','领威武节度使，',[('曦','自称大闽皇并兼领威武节度使')],when='941年七月条下，称号开始采用的具体日期未载',place='闽国')
add('min_brothers_continue_war','王延羲与王延政持续交战，福州与建州之间死伤惨重',17,'与王延政治兵','暴骨如莽。',[('曦','与王延政持续交战'),('延政','与王延羲持续交战')],year=None,when='王延羲在位期间，具体年月未载（见941年条）',place='福州、建州之间',note='互有胜负是连续战争概述，不重复造一场具体胜败；白骨如草的比喻译为死伤惨重，不补人数。')
add('pan_urges_peace','潘承祐多次劝王延政停战修好，王延政不听',17,'镇武节度判官','延政不从。',[('潘承祐','多次建议停战修好'),('延政','拒绝停战修好的建议')],year=None,when='王延羲与王延政交战期间，具体年月未载',place='建州',note='晋江是潘承祐籍贯；屡请为重复行为，不给固定次数。')
add('yan_displays_army','王延政向闽王使者展示军队，并以傲慢言语回应',17,'闽主使者至，','语甚悖慢；',[('延政','向使者展示军队并以傲慢言语回应')],year=None,when='闽王使者到王延政处时，具体年月未载（见941年条）',place='建州',note='使者未具名，悖慢是史书对言语的评价，不补原文未载的具体言辞。')
add('pan_faces_threat','潘承祐长跪劝谏，王延政以吃其肉相威胁，潘承祐仍继续进谏',17,'承祐长跪','声色愈厉，',[('潘承祐','长跪进谏，受威胁仍继续劝谏'),('延政','发怒，以吃判官之肉的言语威胁')],year=None,when='王延政向闽王使者展示军队时，具体年月未载',description='潘承祐长跪劝谏，王延政发怒，问左右是否能吃判官的肉。潘承祐不顾威胁，继续以更严厉的语气进谏。',note='问肉可食是威胁性言论，没有发生杀害或食人。')
add('xi_kills_jiyan','王延羲因王继严受人拥戴，将其召回后毒杀',17,'闽主曦恶泉州',None,[('曦','因王继严得人心而将其罢归并毒杀'),('王继严','从泉州刺史被罢归后遭毒杀')],place='闽国',note='罢归不补返回城市；鸩杀明确毒杀，毒物种类未载。')
add('chonggui_tokyo_regent','石敬瑭任石重贵为东京留守',18,'八月，',None,[('帝','任命东京留守'),('重贵','由开封尹、郑王受任东京留守')],when='941年八月戊子朔',place='东京')
sup('chonggui_tokyo_regent',18,old,'八月戊子朔，以皇子開封尹、鄭王重貴為東京留守，','《旧五代史》同记八月戊子朔任石重贵为东京留守。','皇子是帝纪称谓，本条不新建未经本句证明的血缘父子关系。')
add('feng_li_recommend_du','冯道、李崧多次称赞杜重威的才能，推荐其统领禁军',19,'冯道，李崧','杜重威之能，',[('冯道','多次推荐杜重威'),('李崧','多次推荐杜重威'),('杜重威','受两位宰相推荐')],when='941年八月杜重威任都指挥使以前，具体日期未载',note='才能评价属于荐举者，不作为网站对杜重威的评价。')
add('du_replaces_liu','杜重威受任都指挥使、随驾御营使，接替刘知远',19,'以为都指挥使，','代刘知远，',[('杜重威','受任都指挥使和随驾御营使'),('刘知远','禁军统领职由杜重威接替')],description='冯道、李崧多次推荐后，杜重威被任命为都指挥使，兼随驾御营使，接替刘知远。',note='职务接替不当作刘知远同时被免去已授河东职。')
sup('du_replaces_liu',19,old,'以天平軍節度使兼侍衛親軍馬步軍副都指揮使杜重威為侍衛親軍馬步軍都指揮使，','《旧五代史》将杜重威升都指挥使列在八月戊子朔。','主书本段没有单列日干支，帝纪补明确任命日；不把宰相历次推荐都定为朔日。',field='time_original',relation='adds')
add('liu_resents_chancellors','刘知远因杜重威接替而怨恨冯道、李崧',19,'知远由是','恨二相，',[('刘知远','因职务被替而怨恨两位宰相'),('冯道','受到刘知远怨恨'),('李崧','受到刘知远怨恨')],note='这是史书记人物态度，不据此建立永久仇敌关系。')
add('du_corruption_and_boast','史书记杜重威贪财使百姓逃亡，并借市人多为自己辩解',19,'重威所至',None,[('杜重威','被史书批评贪财，并以市人仍多为自己辩解')],year=None,when='杜重威任官期间，具体年月未载（见941年条）',description='《资治通鉴》批评杜重威到任各地时贪求财物，使许多百姓逃亡。一次经过集市，他对左右说，人们说自己赶走了百姓，为什么集市里仍有这么多人。',note='所至是任官行为概述，未具名集市，不补城名与逃亡人数。')
add('shi_departs_daliang','石敬瑭从大梁启程北行',20,'壬辰，','帝发大梁。',[('帝','从大梁启程')],when='941年八月壬辰',place='大梁')
sup('shi_departs_daliang',20,old,'壬辰，車駕發東京。','《旧五代史》同记八月壬辰皇帝从东京启程。','东京与本句大梁为同一出发城的称谓，不另造一次出发。')
add('shi_arrives_yedu','石敬瑭抵达邺都',20,'己亥，','至鄴都。',[('帝','北行抵达邺都')],when='941年八月己亥',place='邺都')
add('shi_issues_amnesty','石敬瑭抵邺后颁布大赦',20,'壬寅，','大赦。',[('帝','颁布大赦')],when='941年八月壬寅',place='邺都')
sup('shi_issues_amnesty',20,old,'壬寅，制：「應天福六年八月十五日昧爽已前，諸色罪犯，常赦所不原者，咸赦除之；','《旧五代史》保存八月壬寅赦诏，规定赦免范围以本月十五日天亮前所犯为界。','保留诏书自身的八月十五日，不自行换算公历；其后不同罪类和条件另按原文引用。',relation='adds')
for code,title,quote,description in [
('shi_remits_prior_taxes','石敬瑭赦诏免除天福五年末以前的欠税','天福五年終已前殘稅並放。','八月壬寅大赦诏规定，免除天福五年末以前所欠的税款。'),
('shi_remits_trampled_fields','石敬瑭赦诏减免沿路被行幸踩损田苗的当年租税','自東京至鄴都緣路，昨因行幸，有損踐田苗處，據頃畝與放今年租稅。','大赦诏规定，从东京到邺都的沿路田地，因皇帝行幸被踩损田苗的，按受损面积减免当年租税。'),
('shi_allows_farm_tool_casting','石敬瑭赦诏允许百姓自行铸造农具','天下農器，並許百姓自鑄造。','大赦诏允许天下百姓自行铸造农具。')]:
 E[code]=event(code,title,20,quote,[('帝','在大赦诏中规定此项措施')],source=old,when='941年八月壬寅',description=description,note='独立补自旧五代史同次赦诏；这是颁布措施，不保证所有地方已执行完毕。')
add('shi_warns_an','石敬瑭下诏告诫安重荣，不要以一镇对抗契丹',20,'帝以诏谕','无取后悔！”',[('帝','下诏告诫安重荣'),('安重荣','收到告诫诏书')],when='941年八月抵邺后，具体日期未载',description='石敬瑭告诫安重荣，自己因契丹帮助取得天下，安重荣则因自己而获富贵，不应忘恩；以整个后晋仍臣事契丹，一镇难以对抗，劝安重荣慎思，避免后悔。',note='这些理由为诏书中的劝说，不替史书裁定服从契丹政策正确与否，不套壬寅赦日。')
add('an_contacts_congjin','安重荣得诏后更加骄纵，暗中派使者与安从进通谋',20,'重荣得诏',None,[('安重荣','听闻安从进异志后派使者通谋'),('安从进','与安重荣暗中通谋')],when='941年八月石敬瑭告诫诏书以后，具体日期未载',note='密使未具名，不补具体商议内容；通谋按明确动作记入事件，不扩大为永久盟友。')
add('qian_discusses_succession','钱传瓘病中与章德安讨论继位，章德安支持钱弘佐',21,'吴越文穆王','吾无忧矣。”',[('元瓘','因钱弘佐年少提出择宗族长者继位，后接受辅佐安排'),('章德安','支持钱弘佐继位，受托辅佐'),('弘佐','被讨论为继位人选')],when='941年八月辛亥钱传瓘去世以前，具体日期未载',place='吴越',note='择长者是病中王的提议，章德安劝其不必担忧后获托辅佐，不写成长者已被选定。文穆为死后谥号。')
claim('person','person_章德安','biography','章德安是处州人。',21,'德安，处州人也。','籍贯名称按史载保留，不补现代坐标。')
add('qian_yuanguan_dies','吴越王钱传瓘去世',21,'辛亥，','元瓘卒。',[('元瓘','病中去世')],when='941年八月辛亥',place='吴越')
sup('qian_yuanguan_dies',21,fire,'是歲卒，年五十五，謚曰文穆。子佐立。','《新五代史》同记钱传瓘天福六年去世，五十五岁，谥文穆，其子钱弘佐继位。','死亡年印证，年龄为史载数值，不据此推精确出生年。')
claim('person','person_钱传瓘','death_year','钱传瓘于941年八月辛亥去世。',21,'辛亥，元瓘卒。','已有主体不改档案字段，以本次直接死亡记载补充可检索出处。')
add('dai_entrusted_military','戴恽此前受钱传瓘信任，受委掌管军事',21,'初，内牙指挥使戴恽，','悉以军事委之。',[('戴恽','受钱传瓘信任并掌管军事'),('元瓘','将军事交给戴恽')],year=None,when='钱传瓘生前，具体年月未载',note='初引出此前经历，不套钱传瓘去世日。')
relationship('元瓘','弘侑','养父',21,'元瓘养子弘侑乳母，恽妻之亲也，','养子关系有明文，方向为钱传瓘是钱弘侑的养父。乳母与戴恽妻子的亲属类型未载，不补具体中间人物。')
add('dai_accused_succession_plot','有人告发戴恽谋立钱弘侑',21,'或告恽','谋立弘侑。',[('戴恽','被告谋立钱弘侑'),('弘侑','成为告发所称的继位人选')],when='941年钱传瓘去世前后，具体日期未载',note='谋立为告发内容，没有独立确认，未具名告发者不建主体。')
add('zhang_hides_death_prepares_trap','章德安暂不公布钱传瓘死讯，与诸将商议并设伏',21,'德安秘','伏甲士于幕下；',[('章德安','暂不发丧，与诸将商议设伏')],when='941年八月辛亥钱传瓘死后至壬子以前',note='诸将及伏兵未具名，不补完整政变参与名单。')
add('dai_yun_killed','戴恽进入府署，被拘捕并杀死',21,'壬子，','执而杀之，',[('戴恽','入府时被设伏者拘捕并杀死')],when='941年八月壬子',place='吴越府署',note='设伏安排由章德安与诸将作出，直接行刑者未载，不补行刑人。')
add('hongyou_deposed_imprisoned','钱弘侑被废为平民，恢复孙姓并幽禁明州',21,'废弘侑','幽之明州。',[('弘侑','被废为平民，恢复孙姓并幽禁')],when='941年八月壬子条下',place='明州',note='复姓孙按主书保留，钱弘侑与孙弘侑归同一主体，不新建第二人。')
add('hongzuo_military_governor','将吏据钱传瓘遗命，拥钱弘佐为节度使',21,'是日，将吏','时年十四。',[('弘佐','据父亲遗命获立为节度使')],when='941年八月壬子',description='将吏依据钱传瓘遗命，承制任镇海、镇东副大使钱弘佐为节度使。《资治通鉴》记他当时十四岁。',note='是日承接壬子，任节度使与九月即王位区分。')
sup('hongzuo_military_governor',21,age,'佐字祐，立時年十三，','《新五代史》记钱弘佐字祐，继位时十三岁。','主书本段十四岁、新史十三岁，分别保留；不据其中一个年龄倒推精确出生年，字祐以原字保留。',relation='conflicts')
relationship('元瓘','弘佐','父亲',21,'是歲卒，年五十五，謚曰文穆。子佐立。','传主为钱元瓘，即钱传瓘，子佐明确指钱弘佐；复用既有父子关系时保留稳定key与方向，不另建反向重复关系。',source=fire)
claim('person','person_钱弘佐','biography','《新五代史》记钱弘佐字祐。',21,'佐字祐，','祐是表字，不作为另一个人物，年龄异说另行引用。',source=age)
add('hongzuo_ascends_throne','钱弘佐即吴越王位',21,'九月，庚申，','弘佐即王位，',[('弘佐','正式即吴越王位')],when='941年九月庚申',place='吴越')
add('cao_regent','钱弘佐命曹仲达摄政',21,'命丞相曹仲达','摄政。',[('弘佐','任命摄政者'),('曹仲达','以丞相身份受命摄政')],when='941年九月庚申条下',place='吴越')
add('cao_resolves_soldier_protest','军中因赏赐不均持兵器抗议，曹仲达亲自劝说，使其放下兵器',21,'军中言赐与','皆释仗而拜。',[('曹仲达','亲自劝说抗议军人，使其放下兵器')],when='钱弘佐继位、曹仲达摄政以后，具体年月未载',year=None,description='军中抱怨赏赐不均，举起兵器拒绝接受赏赐，诸将无法制止。曹仲达亲自劝说，军人都放下兵器行礼。',note='具体年月及军人数未载，不补战斗或杀伤结果。')
claim('person','person_钱弘佐','biography','《资治通鉴》称钱弘佐温和谦恭，好读书、礼遇士人，勤于政务且能揭发奸弊。',21,'弘佐温恭，好书，礼士，躬勤政务，发擿奸伏，人不能欺。','这是史书的人物评价，不造一场单日完成全部政务的事件。')
add('hongzuo_asks_reserves','有人献嘉禾，钱弘佐询问粮食储备，仓吏答称足供十年',21,'民有献嘉禾者，','对曰：“十年。”',[('弘佐','见人献嘉禾后询问粮食储备')],year=None,when='钱弘佐即位后，具体年月未载',description='有人向钱弘佐献嘉禾，钱弘佐询问仓吏现有多少储备。仓吏回答说可供十年。',note='十年是仓吏回答，不作为已经独立核定的实际库存；献禾者与仓吏未具名。')
add('hongzuo_remits_taxes','钱弘佐据粮储充足的报告，下令免境内税三年',21,'王曰：“然则',None,[('弘佐','据粮储报告，下令免税三年')],year=None,when='钱弘佐即位后，具体年月未载',description='钱弘佐认为军粮足够，可以减轻百姓负担，下令免除境内税收三年。',note='复税在此是免税，不能翻成恢复征税；明确下令，未据此确认三年措施已全部执行。')
for row in B['people']:
 if row['name']=='戴恽':
  row['death_year']=941
  claim('person',row['key'],'death_year','戴恽于941年八月壬子被杀。',21,'壬子，恽入府，执而杀之，','死亡纪年与本段明确日期相合，出生年未载。')
reviews={16:'火灾、钱传瓘惊惧患病、建议乘灾攻击、李昪拒绝及派使救济分开；新史补杭州地点，不补火因或现代诊断。',17:'自称大闽皇与双方长期交战区分，持续战争及潘承祐屡次进谏用未知年；展示兵力、侮慢、长跪劝谏与威胁不当杀人，王继严罢归与毒杀明录，未补归处和毒物。',18:'八月戊子朔石重贵东京留守，旧史印证；皇子称谓不凭本句新建血缘关系。',19:'冯李推荐、杜重威接替及刘知远怨恨分录，帝纪补戊子朔任命，不把推荐都套同日；贪财与市中辩解为未明日期的概述，未硬填八月。',20:'八月壬辰出发、己亥到邺、壬寅赦令分开；旧史保存同次税收及农具措施，颁令不当全部已执行。告诫安重荣没有明载赦日，安重荣随后通谋以具体动作记，未扩永久盟友。',21:'钱传瓘病中属事、辛亥卒、秘丧设伏、壬子杀戴恽及废弘侑、钱弘佐任节度使与九月即王位分期。谋立为告发，弘侑养子及恢复孙姓有明文。钱弘佐十四与十三岁异说保留，不推生年；政务评价、赏赐争执、献嘉禾问储及免税无明确年月，用人物引用或未知年。'}
assert not (P/'publication.json').exists()
for n in range(16,22):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=941,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(16,22)],next_paragraph=Q[22]['id'],next_volume=282,next_year=941,supplements=supplements,excluded_non_body=[],source_contexts=[],coverage='连续第16—21段，原101—106行；七月至九月记载及相关追述。全年38段，累计21段，剩余17段待录。',source_issues_review='钱弘佐继位时十四岁与十三岁分别引用，未据此计算生年；狂疾保留史书记病称谓，长期战争及继位后政务未明年月保留未知。纸本及异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(16,22)],plain_language_review='首次检查新增人物介绍、事件标题与说明、参与角色、关系方向、时间和事实引用；明确建议、告发、威胁、颁令、追述与实际行为。原文及旧主体字段保留，旧内容不扩大回改。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
