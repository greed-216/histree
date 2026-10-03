# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 926, paragraphs 13–15."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 33))
specs=[
 ('jiuwudaishi-038-march-horses',P/'sources/library/jiuwudaishi-038-march-horses','c7025a3a','薛居正等'),
 ('xinwudaishi-069-shu-goods',P/'sources/library/xinwudaishi-069-shu-goods','c7025a3a','欧阳修'),
 ('xinwudaishi-069-jingnan-conflict',P/'sources/library/xinwudaishi-069-jingnan-conflict','c7025a3a','欧阳修'),
 ('tongjian-275-927-offices-and-khitan',YEAR/'part-02/sources/library/tongjian-275-927-offices-and-khitan','6ee141a6','司马光等'),
 ('jiuwudaishi-038-wuzhen-shi',YEAR/'part-02/sources/library/jiuwudaishi-038-wuzhen-shi','6ee141a6','薛居正等'),
 ('xinwudaishi-006-927-opening',YEAR/'part-01/sources/library/xinwudaishi-006-927-opening','d50fed5c','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-275-927-offices-and-khitan']
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0927-p013-p015',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/275.txt').read_text().splitlines()
for n in range(13, 16):
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
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷275·天成二年（927）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_275_0927_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','高季兴':'高季昌','魏王继岌':'李继岌','西方鄴':'西方邺'}
NEW_ALIASES={'韩珙':['韓珙']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷275天成二年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='927年正月本段；确日未载', note='', year=927, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_275_0927_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', title+'。', n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_275_0927_' + code + '_' + pk
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
    pa=person(a,n,f'{b}之{kind}',quote,source=source); pb=person(b,n,f'与{a}关系对象',quote,source=source)
    a=next(x['name'] for x in B['people'] if x['key']==pa); b=next(x['name'] for x in B['people'] if x['key']==pb)
    matches={}
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_275_0927_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('guocongqian_jingzhou_appointment','郭从谦任景州刺史',13,'丙申','景州刺史，',[('帝','任命者'),('郭从谦','从马直指挥使、获任者')],when='927年二月丙申',place='景州',note='景不是荆南荆州，任命与到任后被杀分事。')
claim('event',E,'description','旧明宗纪同日记郭从谦任景州刺史，后令中使诛其族。',13,'丙申，以從馬直指揮使郭從謙為景州刺史，尋令中使誅之，夷其族，以其首謀大逆以弑莊宗也。','新旧从謙/主从谦字形同人；后诛原因属于旧书叙说，不把任命本身当赦免其旧事。',source='jiuwudaishi-038-wuzhen-shi',relation='corroborates')
E=ev('guocongqian_clan_execution','郭从谦到景州后，朝廷遣使族诛',13,'丙申','族诛之。',[('帝','遣使执行所归朝廷'),('郭从谦','到任后被族诛者')],when='927年二月丙申任命后，既至景州之时，诛日未载',place='景州',note='族诛人数与亲属名单未载，不造具名家属或精确总数。')
claim('person',people['郭从谦'],'death_year','郭从谦于927年任景州刺史到任后被诛。',13,span(13,'丙申','族诛之。'),'任命日与诛日不等同。')
claim('event',E,'description','新明宗纪称郭从谦为景州刺史，既而杀之。',13,'郭從謙為景州刺史，既而殺之。','同事补证；新注对君臣罪责是史家论断，不另生成法律定罪结果。',source='xinwudaishi-006-927-opening',relation='corroborates')
E=ev('gao_requests_familial_prefects','高季兴得三州后，请朝廷不另除刺史而由其子弟任职，未获准',13,'高季兴既得','不许。',[('高季兴','请求自行任子弟者'),('帝','未许所归朝廷')],year=None,when='得三州之后、927年二月削夺前，确日未载',place='荆南与三州',note='子弟未具名，不猜高从诲已经任某一州；复用高季昌同人主体。')
claim('event',E,'description','新荆南世家称唐虽给夔忠等州仍自除刺史，季兴拒不接纳。',13,'季興屢請，雖不得已而與之，而唐猶自除刺史，季興拒而不納。','补朝廷保留人事权背景；后续不克、吴册王尚未按主线读到，不本批提前录完。',source='xinwudaishi-069-jingnan-conflict')
E=ev('gao_seizes_kuizhou','夔州刺史潘炕罢官后，高季兴遣兵突入州城，杀戍兵占州',13,'及夔州','而据之。',[('潘炕','此前夔州刺史、罢官者'),('高季兴','遣兵夺州者')],year=None,when='潘炕罢官之后、削官讨伐之前，确日未载',place='夔州',note='罢官不等潘被杀；戍兵无名数，不虚构人物。')
E=ev('gao_rejects_xifangye_and_fails_fuzhou','朝廷任西方邺为夔州刺史，高季兴不受；又袭涪州未克',13,'朝廷除','不克。',[('帝','任西方邺所归朝廷'),('西方鄴','奉圣指挥使、获任夔州刺史'),('高季兴','拒受刺史及袭涪州者')],year=None,when='夺夔州以后、927年二月讨伐之前，任刺史与袭涪确日未载',place='夔州及涪州',note='涪不是福州；未克不写占领，西方原字鄴与规范邺同人。')
E=ev('jiji_sends_hangong_shu_goods','魏王李继岌遣韩珙等押送蜀珍货金帛四十万，浮江下行',13,'魏王继岌','浮江而下，',[('魏王继岌','遣运所归魏王'),('韩珙','押牙、押送者')],year=None,when='破蜀之后、李继岌卒前的运货旧事，主本段未具日',place='蜀中沿江至峡口方向',note='四十万未具钱缗重量单位，珍货金帛不得擅换40万两；不能因本段927就说926已死继岌仍发令。')
claim('event',E,'description','新荆南世家称魏王破蜀所得金帛四十余万自峡而下，适值庄宗之难。',13,'魏王繼岌已破蜀，得蜀金帛四十餘萬，自峽而下，而莊宗之難作。','主四十万/新四十余万数量略异分存，庄宗难为旧事背景，不强排确运日。',source='xinwudaishi-069-shu-goods',relation='conflicts')
E=ev('gao_kills_hangong_seizes_goods','高季兴在峡口杀韩珙等并尽掠蜀货',13,'季兴杀','尽掠取之。',[('高季兴','截杀掠货者'),('韩珙','被杀押送者')],year=None,when='主927讨伐段追叙运蜀货旧事，确日未载；新系庄宗之难',place='峡口',note='主无人数、新十余人另补，不把四十万当被杀人数；不能把魏王旧命安排在其死后。')
claim('event',E,'description','新荆南世家称季兴闻京师有变后悉留蜀物，杀使者韩珙等十余人。',13,'季興聞京師有變，乃悉邀留蜀物，而殺其使者韓珙等十餘人。','十余是新的人数概记，不伪造同行名单或与主的财物量相乘。',source='xinwudaishi-069-shu-goods',relation='adds')
E=ev('court_questions_gao_water_god_reply','朝廷诘问蜀货使者失踪，高季兴以应问水神作答',13,'朝廷诘之','按问水神。”',[('帝','诘问所归朝廷'),('高季兴','作水神答语者')],year=None,when='截杀押送使者之后、927年二月削官之前，确日未载',place='荆南与后唐朝廷',note='答语欲知覆溺为推托，不当韩等真正溺亡或水神存在的事实。')
E=ev('gao_titles_stripped','后唐削夺高季兴官爵',13,'帝怒','官爵，',[('帝','削夺者'),('高季兴','被削官爵者')],when='927年二月壬寅',place='后唐朝廷、荆南',note='削官不等已灭荆南或高此日死。')
E=ev('liu_xia_south_campaign','刘训任南面招讨兼知荆南行府事，夏鲁奇任副招讨，率步骑四万讨荆南',13,'以山南东道','四万讨之。',[('刘训','山南东道节度使、南面招讨及知行府'),('夏鲁奇','忠武节度使、副招讨')],when='927年二月壬寅',place='山南东道至荆南',note='四万为此路步骑部署，不与未给数的川楚军相加为全军精确总数；本句未叙攻城结果。')
claim('event',E,'description','旧明宗纪称刘训襄州节度使、夏鲁奇许州节度使，统蕃汉马步四万进讨。',13,'仍令襄州節度使劉訓充南面招討使、知荊南行府事，許州節度使夏魯奇為副招討使，統蕃漢馬步四萬人進討，','补兵种与州称谓，同军镇异称不造再次任命。',source='jiuwudaishi-038-wuzhen-shi',relation='adds')
claim('event',E,'time_original','新明宗纪以二月戊戌记刘训为南面招讨伐荆南，与主旧壬寅不同。',13,'戊戌，山南東道節度使劉訓為南面招討使，以伐荊南。','存干支异说，同役不另造第二讨伐。',source='xinwudaishi-006-927-opening',relation='conflicts')
E=ev('dong_xifangye_chu_three_sides','董璋任东南面招讨、西方邺为副，川军下峡并会湖南军三面进攻',13,'东川节度使',None,[('董璋','东川节度使、东南面招讨'),('西方鄴','新夔州刺史、副招讨')],when='927年二月壬寅讨伐部署',place='东川、夔州下峡及湖南至荆南',note='三面是进攻部署不是已取得三场战胜；東南名号按原文，不因地理方位静默改西南。')
claim('event',E,'description','旧明宗纪同时令湖南节度使马殷以全军会合。',13,'又命湖南節度使馬殷以湖南全軍會合。','补命令受者，未载楚军人数或当日已会师。',source='jiuwudaishi-038-wuzhen-shi',relation='adds')
pa=person('马殷',13,'湖南节度使、受命以全军会合者','又命湖南節度使馬殷以湖南全軍會合。',source='jiuwudaishi-038-wuzhen-shi')
edge='participation_zztj_275_0927_dong_xifangye_chu_three_sides_'+pa
B['person_events'].append(dict(key=edge,person_key=pa,event_key=E,role='湖南节度使、受命会师者',status='draft'))
claim('person_event',edge,'role','马殷受命以湖南全军会合。',13,'又命湖南節度使馬殷以湖南全軍會合。','与同一讨伐部署挂接，受命不是证明已会师。',source='jiuwudaishi-038-wuzhen-shi')
E=ev('lijingzhou_wuxin_court_confirmation','朝廷任李敬周为武信留后',14,'三月',None,[('帝','朝廷任命者'),('李敬周','武信留后')],when='927年三月甲寅',place='遂州、武信军',note='与正月孟知祥地方先任后奏属于不同任命阶段，不当新换另一个李敬周。')
claim('event',E,'description','旧明宗纪同日称西川节度副使李敬周任遂州武信军留后。',14,'甲寅，以西川節度副使李敬周為遂州武信軍留後。','补前衔和驻州，不重复另任。',source='jiuwudaishi-038-march-horses',relation='corroborates')
E=ev('horse_breeding_supervision','后唐初置监牧以繁息国马',15,'丙辰',None,[('帝','设监牧所归朝廷')],when='927年三月丙辰',place='后唐诸处',note='监牧为养马机构，未具各场地名马数不补地图点。')
claim('event',E,'description','旧明宗纪记任圜奏选孳生马、分置监牧，获准。',15,'又請選孳生馬，分置監牧。」並從之。','同日正文所承宰臣判三司任圜，引用具体请与准词；内引五代会要不新增独立来源。',source='jiuwudaishi-038-march-horses',relation='adds')
pk=person('任圜',15,'宰臣判三司、奏请监牧获准者','丙辰，宰臣判三司任圜奏：「諸道藩府，請依天復三年已前許貢綾絹金銀，隨其土產折進馬之直。又請選孳生馬，分置監牧。」並從之。',source='jiuwudaishi-038-march-horses')
edge='participation_zztj_275_0927_horse_breeding_supervision_'+pk
B['person_events'].append(dict(key=edge,person_key=pk,event_key=E,role='奏请选孳生马分置监牧获准者',status='draft'))
claim('person_event',edge,'role','任圜提出选孳生马分置监牧，朝廷同意。',15,'丙辰，宰臣判三司任圜奏：「諸道藩府，請依天復三年已前許貢綾絹金銀，隨其土產折進馬之直。又請選孳生馬，分置監牧。」並從之。','补制度倡议者，不独立增加所引会要。',source='jiuwudaishi-038-march-horses')
review='连续13—15段逐句校核。郭景州任命丙申及到后族诛分事，景与荆不同，死亡年927但不套任日，族人数名单未具。高季兴沿既有高季昌同主体；三州子弟任请求未许，无名子弟不猜从诲。潘罢官不等被杀，夔戍兵杀无数；西方鄴沿邺，拒受与袭涪不克保留，涪福不同。魏王发运蜀货属平蜀后旧事，年日主未具null不把926已卒者写927发令；新庄宗之难背景独引。主金帛四十万/新四十余万，未具单位不添缗银两，韩等十余是新人数不混财物量。峡口杀及诘答各录，覆溺水神是高答推托非真实死因。壬寅削爵与刘夏四万、董西方及楚会军部署分别，四万是一路不乱加未给数诸路，部署非战果；新纪戊戌/主旧壬寅日期異说并存。东南面原号不因所处位置改西南。旧补马殷受命不强已会师。三月甲寅李敬周朝命与正月孟地方先任不同阶段。丙辰监牧任圜奏获准独立补证，未具各场马数地名不猜，旧所引专书不新增范围外来源。摘录原字，展示简体，纸本待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(13,16):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=927,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(13,16)],next_paragraph='zztj-v275-y0927-p016',next_volume=275,next_year=927,supplements=supplements,excluded_non_body=[],coverage='卷275连续13—15段、原文件87—89行；郭诛、荆南讨伐背景部署、武信朝命与监牧。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(13,16)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
