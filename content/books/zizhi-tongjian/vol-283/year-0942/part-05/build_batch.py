# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 283, year 942 paragraphs 34–40."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,41))
specs=[(d.name,d,'f7f6cfbef8465951e2f967177b4e0970e9d71ed0','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-283-942-autumn-winter','xinwudaishi-009-942-succession','xinwudaishi-065-zhang-yuxian-battle','xinwudaishi-068-min-li-empress']:
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
main_sources = ['tongjian-283-942-autumn-winter']
B = {'format_version': 1, 'batch_key': 'zztj-v283-y0942-p034-p040',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-081-942-salt':'卷81·晋少帝本纪·天福七年十一月','xinwudaishi-029-jing-khitan':'卷29·景延广传·晋与契丹交涉','xinwudaishi-072-jin-khitan':'卷72·四夷附录·出帝初立交涉'}
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
for n in range(34, 41):
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
    labels={'jiuwudaishi-081-942-salt':'卷81·晋少帝本纪·天福七年十一月','xinwudaishi-029-jing-khitan':'卷29·景延广传·晋与契丹交涉','xinwudaishi-072-jin-khitan':'卷72·四夷附录·出帝初立交涉'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '十月至十二月条下及追述'
        citation = f'卷283·后晋天福七年（942；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_283_0942_05_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=942, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='942年年初条下，具体日期未载'
    key = 'event_zztj_283_0942_' + code
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
        edge = 'participation_zztj_283_0942_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_283_0942_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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

ALIASES.update({'帝':'石重贵','曦':'王延羲','楚王希范':'马希范','契丹主':'耶律德光'})
NEW_DESCRIPTIONS={
'刘传':'南汉循州刺史。942年十月丙子，张遇贤攻陷循州，刘传被杀。出生年未载。',
'董遇':'后晋三司使。942年十一月本纪记他从金吾卫大将军、权判三司任三司使；通鉴记他加重盐商征税以求财利，官营卖盐随后恢复。生卒年未载。',
'李仁遇':'闽国盐铁使、右仆射，史称李敏之子、王延羲之甥。942年十二月任左仆射兼中书侍郎、同平章事。父亲李敏与已录同名人物是否同人尚待核对，未直接连接父亲关系。生卒年未载。',
'李光准':'闽国翰林学士、吏部侍郎。942年十二月任中书侍郎兼户部尚书、同平章事。史书回顾他在酒宴中醉酒触怒王延羲，被下令处死，但官吏未执行，次日又恢复职位。生卒年未载。',
'周维岳':'闽国翰林学士。史书记他在王延羲宴饮中被关入狱中，王延羲酒醒后将他释放；另一次宴中险被剖腹，因有人劝阻而免于被杀。具体年月及生卒年未载。'}
NEW_ALIASES={'刘传':['劉傳'],'董遇':[],'李仁遇':[],'李光准':['李光準'],'周维岳':['周維岳']}
ann='jiuwudaishi-081-942-salt';new='xinwudaishi-029-jing-khitan';khitan='xinwudaishi-072-jin-khitan';south='xinwudaishi-065-zhang-yuxian-battle';family='xinwudaishi-068-min-li-empress';jin='xinwudaishi-009-942-succession'
add('zhang_takes_xunzhou','张遇贤攻陷循州，杀死南汉刺史刘传',34,'冬，',None,[('张遇贤','攻陷循州并杀刺史'),('刘传','循州被攻陷时遭杀害')],when='942年十月丙子',place='循州')
sup('zhang_takes_xunzhou',34,south,'妖人張遇賢，自稱中天八國王，攻陷循州。','《新五代史》也记张遇贤称中天八国王并攻陷循州。','新史没有给此次具体月日，妖人为史家称谓，展示未据此认作医学诊断。')
add('ma_builds_tiance_mansion','马希范建造装饰奢华的天策府',35,'楚王希范作','秋冬用木绵。',[('楚王希范','建造装饰奢华的天策府')],year=None,when='马希范在位期间，具体兴建年月未载',place='楚国',description='《资治通鉴》记马希范建天策府，门窗栏槛饰金玉，墙壁涂丹砂数十万斤；地上铺物春夏用角簟，秋冬用木绵。',note='此为建筑及季节陈设概述，不将春夏秋冬分别造942年定日换装事件；数十万斤为史载概数。')
add('ma_feasts_at_tiance','马希范与子弟僚属在天策府游宴',35,'与子弟',None,[('楚王希范','与子弟僚属在府中游宴')],year=None,when='天策府建成以后，具体年月未载',place='天策府',note='子弟僚属未列名，不凭其他子女名单自动推参与者。')
add('shi_jingtang_buried','后晋将石敬瑭葬于显陵，庙号高祖',36,'十一月，',None,[('石敬瑭','死后葬于显陵，庙号高祖')],when='942年十一月庚寅',place='显陵')
sup('shi_jingtang_buried',36,ann,'十一月庚寅，葬高祖皇帝於顯陵。','《旧五代史》同记十一月庚寅葬石敬瑭于显陵。','本纪高祖为石敬瑭，不误认南汉刘岩。')
sup('shi_jingtang_buried',36,jin,'庚寅，葬聖文章武孝皇帝于顯陵。','《新五代史》也记十一月庚寅葬高祖于显陵。','谥号字数与主书有差，按各书原字保留，不改原文快照。')
add('jin_prior_state_salt','河南河北诸州先由官府卖海盐，并配给蚕盐收钱',37,'先是，','散蚕盐敛民钱。',[],year=None,when='石敬瑭放开盐禁以前，具体年月未载',place='河南、河北诸州',note='每年十七万缗为通鉴收入记载，蚕盐另项未给金额；旧纪数字异记独立保存。')
add('advisors_propose_salt_tax','有人建议允许百姓贩盐，将官府卖盐收入改按年向民户征收食盐钱',37,'言事者称','谓之食盐钱；',[],year=None,when='石敬瑭在位期间，具体年月未载',place='后晋',description='进言者说，百姓因私贩盐获罪者多，建议准许民间贩盐，改以官府原卖盐收入按年向百姓征钱，称为食盐钱。',note='进言者未具名，抵罪者众为奏议理由，不补人数。')
add('shi_accepts_salt_tax','石敬瑭接受放开盐禁、改征食盐钱的建议',37,'高祖从之。','高祖从之。',[('石敬瑭','接受建议允许民间贩盐并改征食盐钱')],year=None,when='石敬瑭在位期间，具体年月未载',place='后晋')
sup('shi_accepts_salt_tax',37,ann,'遂開鹽禁，許通商，令州郡配征人戶食鹽錢，上戶千文，下戶二百，分為五等，','《旧五代史》补记放开盐禁后，令州郡按五等户征食盐钱，上户千文、下户二百。','这是过去政策及分户额，不当董遇十一月的新盐商关税。',relation='adds')
add('salt_price_falls','放开盐禁后盐价下降，每斤降至十钱',37,'俄而盐价','每斤至十钱。',[],year=None,when='石敬瑭盐政改制不久后，具体年月未载',place='后晋',note='俄而不换算固定天数；价格为史书概述，不推所有地方同价。')
add('dong_yu_reimposes_salt_taxes','董遇加重盐商征税，每斤过境征七钱、当地出售征十钱',37,'至是，','留卖者十钱。',[('董遇','为增加财利加重对盐商征税')],when='942年十一月条下，具体日期主书未载',place='后晋',note='主书省略计量单位，旧纪明确按斤，另有引用支持；增求羡利为史书对动机的解释。')
sup('dong_yu_reimposes_salt_taxes',37,ann,'詔：「州郡稅鹽，過稅斤七錢，住稅斤十錢，州府鹽院並省司差人勾當。」','《旧五代史》在十一月辛丑列诏令：每斤过税七钱、住税十钱，并由省司派人管州府盐院。','计量单位及诏令列日由旧纪补充，主书只列十一月条下。',relation='adds')
E['dong_yu_three_departments']=event('dong_yu_three_departments','石重贵任董遇为三司使',37,'辛丑，以金吾衛大將軍、權判三司董遇為三司使。',[('帝','任董遇为三司使'),('董遇','由金吾卫大将军、权判三司任三司使')],when='942年十一月辛丑',source=ann)
add('state_salt_sales_return','盐商经营几乎断绝，官府恢复卖盐',37,'由是盐商','而官复自卖。',[],when='942年董遇加重盐税后，具体日期未载',place='后晋',note='殆绝为几乎断绝，不写成已查明所有盐商消失。')
claim('event',E['state_salt_sales_return'],'description','《资治通鉴》回顾说，官府恢复卖盐后，食盐钱仍照旧征收。',37,'其食盐钱，至今敛之如故。','至今是作者回顾，不自动将征收末年填为942年或后晋灭亡年。')
claim('event',E['jin_prior_state_salt'],'description','《旧五代史》电子底本记旧海盐收入为一千七万贯。',37,'每年海鹽界分約收鹽價錢一千七萬貫，','与通鉴十七万缗差异明显，原字原数保留待版本核对，不取一书数字覆盖另一书或自行猜改。',source=ann,relation='conflicts')
pk=person('李仁遇',38,'盐铁使、右仆射，史称李敏之子、王延羲之甥',span(38,'闽盐铁使','得幸于曦。'))
claim('person',pk,'biography','《资治通鉴》称李仁遇的父亲名李敏，李仁遇为王延羲之甥，年轻、容貌美，受到王延羲宠爱。',38,span(38,'闽盐铁使','得幸于曦。'),'父李敏是否与已录闽宰相同人未证，不连接到唐昭宗旧名或直接认作该宰相；甥的具体亲属支系待核，不补中间亲属。')
claim('person',pk,'biography','《新五代史》同称李仁遇为王延羲之甥，因容貌受到宠爱并被用为相。',38,'李仁遇曦甥也，以色嬖之，用以為相。','嬖之为史書宠爱描述，不额外确立原文未明说的具体性行为或关系；书间同称甥不补母亲身份。',source=family,relation='corroborates')
add('li_renyu_appointed','王延羲任李仁遇为左仆射兼中书侍郎、同平章事',38,'十二月，','兼中书侍郎，',[('曦','任命李仁遇为左仆射兼中书侍郎、同平章事'),('李仁遇','获得左仆射兼中书侍郎、同平章事职衔')],when='942年十二月，具体日期未载',place='闽国',note='两人并同平章事承接本句下文，事实说明所据完整引文另列，不推首次参与全部政务。')
claim('event',E['li_renyu_appointed'],'description','本次李仁遇和李光准均加同平章事。',38,'十二月，以仁遇为左仆射兼中书侍郎，翰林学士、吏部侍郎李光准为中书侍郎兼户部尚书，并同平章事。','并同平章事同时修饰两人，单独保存完整原文以支持职衔。')
add('li_guangzhun_appointed','王延羲任李光准为中书侍郎兼户部尚书、同平章事',38,'翰林学士、','并同平章事。',[('曦','任李光准为中书侍郎兼户部尚书、同平章事'),('李光准','由翰林学士、吏部侍郎获任新职')],when='942年十二月，具体日期未载',place='闽国')
add('wang_orders_guangzhun_killed','李光准夜宴醉酒触怒王延羲，王延羲下令将他押到集市处死',38,'曦荒淫无度，','命执送都市斩之；',[('李光准','夜宴醉酒触怒王延羲后，被下令押到集市处死'),('曦','下令将李光准押到集市处死')],year=None,when='王延羲在位期间的一次夜宴，具体年月未载',place='闽国',note='尝夜宴为追述，处死命令下一句未执行，不写李光准已经死亡。')
add('officials_jail_guangzhun','官吏不敢杀李光准，把他关入狱中',38,'吏不敢杀，','系狱中。',[('李光准','未被处死，改被关入狱中')],year=None,when='上述处死命令之后，当夜，具体年月未载',place='闽国',note='官吏未具名，不补违命动机或将其认作周维岳本人。')
add('guangzhun_restored_next_day','王延羲次日上朝，召李光准恢复职位',38,'明日，视朝，','召复其位。',[('曦','次日召李光准恢复职位'),('李光准','恢复原职位')],year=None,when='李光准被关押的次日，具体年月未载',place='闽国')
add('zhou_weiyue_jailed','王延羲当晚再宴，把翰林学士周维岳关进狱中',38,'是夕，又宴，','收翰林学士周维岳下狱。',[('曦','宴饮时把周维岳关入狱中'),('周维岳','被关入狱中')],year=None,when='李光准复职同日的晚上，具体年月未载',place='闽国')
add('zhou_weiyue_released','狱吏劝周维岳勿忧，王延羲酒醒后释放他',38,'吏拂榻待之，','醒而释之。',[('周维岳','得到狱吏安慰，随后获释'),('曦','酒醒后释放周维岳')],year=None,when='周维岳被关押后，具体年月未载',place='闽国',note='醒而释之承接君主醉后处置，不写成狱吏自行赦免。')
add('wang_plans_to_examine_wine_gut','另一次宴饮，王延羲因酒有别肠的说法，命拖周维岳下殿，想剖看酒肠',38,'他日，又宴，','欲剖视其酒肠。',[('曦','听信酒有别肠说法，命拖人下殿并计划剖看'),('周维岳','因饮酒量被君主计划剖看肠胃')],year=None,when='王延羲在位期间另一场宴饮，具体年月未载',place='闽国',note='酒有别肠为左右说法，不当现代解剖事实；欲剖未执行，不造已剖腹事件。')
add('zhou_spared_after_intercession','有人劝王延羲留下能陪他饮酒的周维岳，周维岳免于被杀',38,'或曰：“杀维岳，',None,[('曦','听从劝阻而放过周维岳'),('周维岳','因有人劝阻而免于被杀')],year=None,when='上述拟剖酒肠事件中，具体年月未载',place='闽国',note='劝者未具名，不补与周维岳的亲属或结党关系。')
add('jing_proposes_grandson_letter','石重贵初即位时，景延广提议向契丹称孙，不称臣',39,'帝之初即位也，','而不称臣。',[('景延广','反对奉表称臣，提议致书称孙'),('帝','在初即位时听取交涉称谓建议')],when='942年六月石重贵初即位时，具体讨论日未载',note='政治称孙不新建生物血缘祖孙关系；不是十二月新即位或首次才商议。')
sup('jing_proposes_grandson_letter',39,new,'初，出帝立，晉大臣議告契丹，致表稱臣，延廣獨不肯，但致書稱孫而已，','《新五代史》也记出帝初立，景延广拒绝奉表称臣，只主张致书称孙。','同一初立交涉讨论，其他后续言论发生日期未载，不强定全在六月即位当天。')
add('li_song_warns_khitan_war','李崧劝石重贵为保国家向契丹称臣，警告拒绝称臣将来可能引发战争',39,'李崧曰：','于时悔无益矣。”',[('李崧','劝称臣并警告将来可能开战')],when='942年石重贵初即位时，具体讨论日未载',note='他日必战是李崧的警告，不当作此时已经发生的战争。')
add('shi_accepts_jing_letter','景延广坚持意见，冯道态度不定，石重贵最终采纳景延广建议',39,'延广固争，','帝卒从延广议。',[('景延广','坚持致书称孙不称臣'),('冯道','在争议中态度不定'),('帝','最终采纳景延广建议')],when='942年初即位交涉讨论中，具体日期未载',note='依违为态度不定，不直接写冯道明确赞成或反对。')
add('khitan_reproaches_succession','契丹因石重贵未先请示即位而愤怒，派使者责问',39,'契丹大怒，','遽即帝位？”',[('耶律德光','契丹方面因即位未先请示而责问'),('帝','受到契丹使者责问')],when='942年即位交涉后，具体日期未载',note='使者原文未具名，不把责问日期直接套六月或十二月某日。')
sup('khitan_reproaches_succession',39,khitan,'高祖崩，出帝即位，德光怒其不先以告，而又不奉表，不稱臣而稱孫，數遣使者責晉。','《新五代史》四夷附录补明耶律德光因未先告即位以及不称臣而屡派使者责晋。','屡遣使者为概述，不凭此造若干无详情外交事件；后接944年战争不提前录入。',relation='adds')
add('jing_replies_disrespectfully','景延广以不恭敬的言辞答复契丹使者',39,'延广复',None,[('景延广','以不恭敬言辞答复契丹使者')],when='942年契丹责问初立交涉时，具体日期未载',note='不逊为史书评价，细节由新史独立补证，不把威胁当已验证军械统计。')
sup('jing_replies_disrespectfully',39,new,'且晉有橫磨大劍十萬口，翁要戰，則來，','《新五代史》记景延广向契丹使者夸称晋有横磨大剑十万口，并说如要战便来。','十万口为谈话中声称的军械数，不录作已核实库存；翁为外交祖辈称谓，不立血亲关系。',relation='adds')
add('zhao_yanshou_urges_attack','赵延寿想取代后晋在中原称帝，多次劝契丹攻晋，耶律德光颇为认可',40,'契丹卢龙',None,[('赵延寿','想取代后晋称帝，劝契丹攻晋'),('契丹主','对赵延寿的建议颇为认可')],when='942年年末条下，起意及各次劝说日期未载',note='欲与颇然是企图和态度，不写赵延寿已成为中原皇帝或已在本段出兵。')
for row in B['people']:
 if row['name']=='刘传':
  row['death_year']=942
  claim('person',row['key'],'death_year','刘传于942年十月丙子循州被攻陷时遭杀害。',34,'冬，十月，丙子，张遇贤陷循州，杀汉刺史刘传。','死亡日与刺史身份明确，出生年未载。')
reviews={34:'十月丙子循州陷与刘传死，接前起事不重复十月日期；新史只补陷城不强补同日。',35:'天策府奢华建筑及季节地衣、子弟僚属游宴为在位概述，确年未载为空，不拆虚构季节换装事件。',36:'十一月庚寅石敬瑭显陵及庙号，有新旧同日补证，谥号字数各书保原。',37:'先是旧官营、建议放开、石敬瑭接受及盐价下降为旧事日期为空；董遇加税、旧纪十一月辛丑正式任命和盐诏、官复卖盐分别录。单位斤由旧纪补，至今为作者回顾；十七万缗与旧电子一千七万贯差异保留待核，不猜改。',38:'李仁遇父名李敏尚未证与已录闽宰相同人，保文字不建误父边；甥支系未证不造母亲。十二月两任命并同平章事引完整句；尝夜宴、翌复、当夕周囚醒释与他日拟剖免均为未知年月，不补李光准或周维岳已经被杀。',39:'初即位六月追述不套十二月，称孙政治称谓不造血缘；建议、李崧警告、冯道依违、帝接受、契丹责问和景答分期。十万剑为谈话声称不库存；四夷附录后944战事不提前。',40:'赵延寿欲帝及屡劝攻晋、契丹主态度为计划不已称帝；各次日期未载不造无详情多条战役。'}
assert not (P/'publication.json').exists()
for n in range(34,41):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=283,year=942,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(34,41)],next_paragraph='zztj-v283-y0943-p001',next_volume=283,next_year=943,supplements=supplements,excluded_non_body=[],source_contexts=[],coverage='连续第34—40段，原39—45行；十月至十二月及追述。第46行齐王上为结构标题、第47—48行为943年界；正文后接943年第1段。',source_issues_review='海盐收入电子数字差异、谥号字数、李仁遇父名与甥支系保待核；命杀和欲剖未执行，称孙为外交称谓，军械数字为声称；原文保留，纸本及异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(34,41)],plain_language_review='首次逐项核对人物、标题、参与动作、时间与事实引用，现代白话说明与逐字原文分开；追述、计划、诏令、实际行为有别，未经证明亲属不误连。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
