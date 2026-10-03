# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 933 paragraphs 1–7."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,13))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'5d053db4','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [('tongjian-278-933-yearend',YEAR.parent/'year-0933/part-07/sources/library/tongjian-278-933-yearend','1ab64add','司马光等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-933-yearend']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0934-p001-p007',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    if key.startswith('songshi-262-'):record=dict(record,section_title='卷262·赵上交传',citation='《宋史》卷262·赵上交传，段落 '+record['id']+'；EPUB卷题李濤傳沿卷内另一传主，正文已回查赵上交传，纸本待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/278.txt').read_text().splitlines()
for n in range(1, 8):
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
    if source.startswith('songshi-262-'):record=dict(record,citation='《宋史》卷262·赵上交传，段落 '+record['id']+'；EPUB卷题李濤傳沿卷内另一传主，正文已回查赵上交传，纸本待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷278·清泰元年（934；正月闵帝应顺元年）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0934_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从厚','闵帝':'李从厚','明宗':'李嗣源','明帝':'李嗣源','潞王':'李从珂','从珂':'李从珂','弘昭':'朱弘昭','赟':'冯赟','义诚':'康义诚','洪实':'朱洪实','彦威':'安彦威','从宾':'张从宾','遇':'皇甫遇','重吉':'李重吉','惠明':'李幼澄','元瓘':'钱传瓘','徐知诰':'李昪','吴主':'杨溥'}
NEW_ALIASES={'安彦威':['安彥威'],'张从宾':['張從賓'],'皇甫遇':[],'李幼澄':['李惠明','惠明大师','惠明（李从珂女）','幼澄']}

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=934, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='934年正月条下；确日未独载'
    key = 'event_zztj_278_0934_' + code
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
        edge = 'participation_zztj_278_0934_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_278_0934_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




# Consecutive paragraphs 1–7; retrospective passages remain undated.
ev('conghou_newyear_amnesty','正月戊寅闵帝大赦天下',1,'春，','闵帝大赦，',[('闵帝','发布大赦者')],when='934年正月戊寅',note='卷年题用后来清泰元年统年，此时闵帝在位并将改应顺，不当李从珂此时已即位。')
ev('conghou_yingshun_era','正月戊寅闵帝改元应顺',1,'春，','改元应顺。',[('闵帝','改元者')],when='934年正月戊寅',note='933十二月即位与今改元分；本年后改清泰，主卷年题清泰不混此时年号。')
ev('kang_shizhong_six_guards','正月壬午康义诚加兼侍中、判六军诸卫事',1,'壬午，',None,[('义诚','原河阳节度兼侍卫都指挥使、获加衔及判事者'),('闵帝','诏加时在位君主')],when='934年正月壬午',note='河阳及侍卫为原职，不再造此日新任河阳；兼侍中与判事按原文保，不当成为唯一丞相。')
ev('zhu_feng_suspect_guard_commanders','史叙朱弘昭、冯赟忌安彦威、张从宾两禁军将',2,'硃弘昭、','张从宾，',[('弘昭','忌旧禁军将的执政者'),('赟','忌旧禁军将的执政者'),('彦威','侍卫马军都指挥使、宁国节度使'),('从宾','侍卫步军都指挥使、忠正节度使')],year=None,when='甲申换将前执政者忌惮的持续概述；起讫未知',note='忌是史书动机叙述，不能自动作两将实际叛乱，也不派生永久敌对关系。')
ev('anyanwei_huguo','正月甲申安彦威出任护国节度使',2,'甲申，','出彦威为护国节度使，',[('彦威','由侍卫马军出任护国者'),('闵帝','任命时在位君主')],when='934年正月甲申',place='护国军',note='任命不等同日抵任；旧同日河中对应军治。')
ev('hongshi_cavalry_command','正月甲申朱洪实接侍卫马军都指挥使',2,'以捧圣马军','代之；',[('洪实','原捧圣马军都指挥使、接侍卫马军者'),('闵帝','任命时在位君主')],when='934年正月甲申',note='代之承安彦威原侍卫马军职，不当代护国外镇；旧另带宁国节度补。')
ev('zhangcongbin_zhangyi','正月甲申张从宾出任彰义节度使',2,'出从宾','彰义节度使，',[('从宾','由侍卫步军出任彰义者'),('闵帝','任命时在位君主')],when='934年正月甲申',place='彰义军',note='旧同日泾州对应军治，不新增重复两个镇；出任不当已叛。')
ev('huangfuyu_infantry_command','正月甲申皇甫遇接侍卫步军都指挥使',2,'以严卫步军','代之。',[('遇','原严卫步军都指挥使、接侍卫步军者'),('闵帝','任命时在位君主')],when='934年正月甲申',note='代之承张从宾原侍卫步军职，不当代彰义镇；旧另带忠正节度补。')
claim('person',people['安彦威'],'description','安彦威为崞人。',2,'彦威，崞人；','籍称崞，不自行换现代行政区或给坐标。')
claim('person',people['皇甫遇'],'description','皇甫遇为真定人。',2,'遇，真定人也。','籍称真定保，不加原文无姓氏族谱或出生年。')
q=span(3,'戊子，','并兼中书令。')
for code,name,role in [('zhu','弘昭','枢密使、获诏加者'),('feng','赟','枢密使、获诏加而随后辞受者'),('shi','石敬瑭','河东节度兼侍中、获诏加者')]:
 event('zhongshuling_'+code,'正月戊子诏加'+ALIASES.get(name,name)+'兼中书令',3,q,[(name,role),('闵帝','诏加时在位君主')],when='934年正月戊子',note='冯赟后辞并改侍中，此处只记诏加，不当其已实际受中书令。主同中书门下二品原衔不另改成三品或独造新实际职。')
ev('feng_declines_zhongshuling','冯赟以超迁太过坚辞中书令',3,'赟以超迁','坚辞不受；',[('赟','坚辞不受者')],when='934年正月戊子诏加后、己丑改衔前',note='以超迁太过为辞受理由，不当朱石也都辞不受。')
ev('feng_shizhong_instead','正月己丑冯赟改加兼侍中',3,'己丑，',None,[('赟','由未受中书令改兼侍中者'),('闵帝','改衔时在位君主')],when='934年正月己丑')
ev('gaoconghui_nanping_king','正月壬辰高从诲获封南平王',4,'壬辰，','为南平王，',[('高从诲','原荆南节度使、获封南平者'),('闵帝','封授君主')],when='934年正月壬辰',place='荆南、后唐朝廷',note='当次册授王号，不当此前全无继位或封爵，也不把荆南此前独立州全新征服。')
ev('maxifan_chu_king','正月壬辰马希范获封楚王',4,'武安、',None,[('马希范','原武安武平节度使、获封楚者'),('闵帝','封授君主')],when='934年正月壬辰',place='湖南、后唐朝廷',note='既有932继位与今后唐封王分，不把此前亡父马殷误作此次封授人。')
ev('qian_wuyue_king','正月甲午钱元瓘获封吴越王',5,'甲午，',None,[('元瓘','原镇海镇东节度使、吴王、进封吴越者'),('闵帝','封授君主')],when='934年正月甲午',place='吴越、后唐朝廷',note='元瓘沿钱传瓘，同一钱氏主体；受封不当此时首次继父掌吴越。')
ev('xu_builds_private_residence','徐知诰在金陵另治私第',6,'吴徐知诰','别治私第于金陵，',[('徐知诰','另治私第者')],when='934年正月乙未迁居前附记；确日未独载',place='金陵',note='别治与正式迁居分，未给开工年月与建筑规格不补。')
ev('xu_moves_private_residence','正月乙未徐知诰迁居金陵私第',6,'乙未，','迁居私第，',[('徐知诰','迁居私第者')],when='934年正月乙未',place='金陵私第')
ev('xu_vacates_office_for_wu','徐知诰腾空府舍以待吴主',6,'虚府舍','虚府舍以待吴主。',[('徐知诰','虚府舍等待君主者'),('吴主','拟接待的吴国君主')],when='934年正月乙未迁居后附记',place='金陵',note='以待是准备，不写杨溥此时已经迁都进居，也不当徐已称帝。')
ev('congke_shi_service_background','史叙李从珂、石敬瑭少随明宗征伐，有功名得众心',7,'凤翔节度使','得众心。',[('从珂','少从征伐、当前凤翔兼侍中潞王'),('石敬瑭','少从征伐者'),('明宗','早年带领征伐者')],year=None,when='少从明帝征伐的过往概述；具体年月未知',note='明帝承明宗，原称不当闵帝李从厚；功名得众是主概述，未给具体战场不重复造已录战。')
ev('zhu_feng_suspect_congke_shi','朱弘昭、冯赟掌朝政后忌位望高的李从珂、石敬瑭',7,'硃弘昭、','皆忌之。',[('弘昭','掌政而忌之者'),('赟','掌政而忌之者'),('从珂','被忌的节度使'),('石敬瑭','被忌的节度使')],year=None,when='朱冯掌政后的持续动机概述；确起讫未载',note='史叙位望比较与忌惮，不等二节度使此时已联合叛乱，不建永久盟友边。')
ev('congke_sends_wife_to_sick_mingzong','明宗有疾时李从珂屡遣夫人入省侍',7,'明宗有疾，','入省侍；',[('明宗','受省侍的患病君主'),('潞王','屡遣夫人者')],year=None,when='明宗有疾时的追叙；未独定具体患病年月',place='后唐宫廷',note='夫人未名不猜是哪一刘氏；屡遣无各次日不编次数，不能写从珂本人已入京。')
ev('congke_absent_mingzong_funeral','明宗去世后李从珂称疾未赴',7,'及明宗殂，','辞疾不来，',[('潞王','辞疾未赴者')],when='明宗933年十一月戊戌殂后追叙；不来具体日未知',year=None,note='殂后不来跨年叙，不硬定934正月一日，不把称疾当医学诊断。')
ev('envoys_claim_congke_secrets','朝廷使臣到凤翔，有人自称察得李从珂阴事',7,'使臣至凤翔','阴事。',[('潞王','被使臣称察阴事者')],year=None,when='明宗殂后、子女处置前追叙；确日未知',place='凤翔',note='或自言为使臣报告，不能当阴谋已经核实；未名使臣不造人。')
ev('chongji_bozhou_posting','正月己亥李重吉由控鹤都指挥使出任亳州团练使',7,'时潞王长子','亳州团练使。',[('重吉','潞王长子、旧控鹤都指挥使、出亳州者'),('弘昭','不欲其掌禁兵的执政者'),('赟','不欲其掌禁兵的执政者'),('闵帝','出任时在位君主')],when='934年正月己亥',place='亳州',note='官名与933控鹤指挥身份沿一人，出任不同后续下狱或被杀，不提前记死亡。')
ev('youcheng_palace_summons','在洛阳为尼的李从珂女惠明被召入禁中',7,'潞王有女','亦召入禁中。',[('惠明','潞王女、在洛阳为尼、被召入宫者'),('闵帝','朝廷召入时在位君主')],when='934年正月己亥出重吉相邻记；未独日',place='洛阳、宫中',note='惠明大师为幼澄同女的称号，旧后文皇长女明确；仅核身份，不提前记后来被杀，不凭召入一语说已经严刑。')
ev('congke_suspicion_after_children','李从珂因子女被调离及召入而疑惧',7,'潞王由是',None,[('潞王','因子女处置生疑惧者')],when='934年正月子女处置后附记',note='疑惧为史述，不当已在此日发动兵变或被拥立帝。')
relationship('从珂','重吉','父亲',7,'时潞王长子重吉','同父子边已在933兵变批次建立，复用UUID，本段补长子与新职，不新造反向边。')
relationship('从珂','惠明','父亲',7,'潞王有女惠明为尼','李从珂→女幼澄为父亲，惠明为同人称号，旧明确皇长女尼惠明大师幼澄。')
old='jiuwudaishi-045-934-newyear-appointments';amnesty='jiuwudaishi-045-934-amnesty';new='xinwudaishi-007-934-newyear';hostages='jiuwudaishi-046-congke-hostages';name='jiuwudaishi-046-youcheng-name'
def excerpt(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);return t[a:t.index(end,a)+len(end)]
def supp(code,source,start,end,text,n,relation='corroborates',note='主段与旧新史同日或同人核对，繁简异字保；后段事件尚未到主线不提前新增。'):
 claim('event','event_zztj_278_0934_'+code,'description',text,n,excerpt(source,start,end),note,source=source,relation=relation)
supp('conghou_yingshun_era',amnesty,'戊寅，','改長興五年為應順元年。','旧闵帝纪戊寅记明堂大赦、改长兴五年为应顺元年。',1,relation='adds')
supp('conghou_newyear_amnesty',new,'戊寅，','大赦，改元，用樂。','新闵帝纪同戊寅记大赦改元用乐。',1,relation='adds')
supp('kang_shizhong_six_guards',old,'壬午，','判六軍諸衛事。','旧同壬午加康义诚检校太尉、兼侍中，判六军诸卫事；旧带检校补。',1,relation='adds')
supp('anyanwei_huguo',old,'甲申，以侍衛馬軍','安彥威為河中節度使；','旧同甲申安彦威由马军宁国出河中，主护国为军治对应。',2)
supp('zhangcongbin_zhangyi',old,'以侍衛步軍','並加檢校太傅；','旧同甲申张从宾由步军忠正出泾州，加检校太傅，主彰义为军治对应。',2,relation='adds')
supp('hongshi_cavalry_command',old,'以捧聖左右廂','充侍衛馬軍都指揮使；','旧同甲申朱洪实带宁国节度及检校太保，接侍卫马军，旧原钦州刺史补。',2,relation='adds')
supp('huangfuyu_infantry_command',old,'以嚴衛左右廂','充侍衛步軍都指揮使。','旧同甲申皇甫遇带忠正节度、检校太保，接侍卫步军，旧原岩州刺史补。',2,relation='adds')
supp('zhongshuling_zhu',old,'戊子，樞密使、','並加兼中書令。','旧同戊子朱宏昭、冯贇诏加兼中书令；朱宏昭与主朱弘昭同人异字保。',3)
supp('zhongshuling_shi',old,'北京留守、河東','石敬瑭加兼中書令；','旧同戊子石敬瑭加兼中书令，旧并详北京留守与四军蕃汉总管等原衔。',3,relation='adds')
supp('feng_shizhong_instead',old,'樞密使馮贇表','封邠國公。','旧冯赟表坚让中书令，改兼侍中并封邠国公；主己丑改，旧本句未独日。',3,relation='adds')
supp('gaoconghui_nanping_king',old,'壬辰，荊南','高從誨封南平王；','旧同壬辰高从诲封南平王。',4)
supp('maxifan_chu_king',old,'湖南節度使','馬希範封楚王。','旧同壬辰马希范封楚王。',4)
supp('qian_wuyue_king',old,'甲午，兩浙','進封吳越王；','旧同甲午钱元瓘由吴王进封吴越王。',5)
supp('congke_suspicion_after_children',hostages,'既而帝子重吉','帝方憂不測。','旧废帝纪以子重吉出亳州、女尼入宫记从珂忧不测，印证子女处置后的疑惧。',7)
claim('person',people['李幼澄'],'aliases','旧废帝纪记皇长女尼为惠明大师幼澄；主女惠明沿同人。',7,'皇長女尼惠明大師幼澄','同父长女尼身份及同胞长子重吉对应，惠明为大师称号，幼澄姓名字保；只核身份，不将旧后文举哀死亡事件提前至正月。',source=name,relation='adds')
reviews={1:'戊寅赦、改应顺与壬午康加兼侍中判六军分。卷统年题清泰是后来年号，不当此时从珂已帝；旧长兴五改应顺、新戊寅同日及用乐补。河阳侍卫为原职，不新授一次。',2:'忌为动机概述未定年，甲申四人出换分。旧河中/主护国、旧泾州/主彰义军治对应；朱代原马军、皇甫代原步军，非代外镇。旧补新所带宁国忠正及检校，旧原职钦岩州不编新授日，籍崞真定无坐标。',3:'戊子朱冯石诏加与冯辞、己丑改侍中分。冯诏加不等实际受，旧封邠国公补。朱旧宏主弘异字同人，不造朱宏昭；原同中书门下二品衔不擅改三品。',4:'壬辰两王封授分，既有继位与此唐封王区分，不当此前未管荆南楚，也不将父高季兴马殷误为受封者。',5:'甲午元瓘进吴越王，沿钱传瓘而非另一人；此时原吴王与带镇海镇东保，不当首次继父掌吴越。',6:'金陵别治、乙未移私第、虚府待吴三个动作。待是未实现的接待准备，不当吴主已迁都，不提前录知诰称帝。无二十四史同句不虚增补证。',7:'少从明帝为明宗往事未定年；朱冯忌、夫人屡省、帝殂后辞疾、使臣自称阴事分，未名夫人使臣不猜。己亥重吉出亳州与女尼召入、生疑惧分，不提前帝兵变或子女被杀。重吉父边复用，惠明据旧惠明大师幼澄建同一女、父边。未因旧后文举哀而填正月死亡年日。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,8):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,8)],next_paragraph='zztj-v278-y0934-p008',next_volume=278,next_year=934,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷278连续934年第1—7正文段、原95—101行；应顺改元、禁军换将、兼衔封王、吴迁居及潞王子女处置。第8段建州战事长叙待录，全934年跨卷共89正文段。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,8)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
