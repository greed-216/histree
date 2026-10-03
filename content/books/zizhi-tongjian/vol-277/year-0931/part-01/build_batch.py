# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 931, paragraphs 1–10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 51))
PREVIOUS=YEAR.parent/'year-0930'
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'91251854','司马光等' if directory.name.startswith('tongjian') else '薛居正等'))
specs.extend([
 ('tongjian-277-930-year-end',PREVIOUS/'part-07/sources/library/tongjian-277-930-year-end','bfff83e2','司马光等'),
 ('xinwudaishi-064-meng-campaign',PREVIOUS/'part-04/sources/library/xinwudaishi-064-meng-campaign','73f70bd8','欧阳修'),
 ('xinwudaishi-033-xialuqi-siege',PREVIOUS/'part-05/sources/library/xinwudaishi-033-xialuqi-siege','f7d30617','欧阳修'),
 ('xinwudaishi-024-an-supervises',PREVIOUS/'part-07/sources/library/xinwudaishi-024-an-supervises','bfff83e2','欧阳修'),
 ('xinwudaishi-051-lirenju-dongzhang',ROOT/'content/books/zizhi-tongjian/vol-276/year-0929/part-03/sources/library/xinwudaishi-051-lirenju-dongzhang','0a803f54','欧阳修'),
])

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-930-year-end','tongjian-277-931-february']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0931-p001-p010',
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
lines = (ROOT / 'resources/derived/tongjian/277.txt').read_text().splitlines()
for n in range(1, 11):
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
        citation = f'卷277·长兴二年（931）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_277_0931_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'知祥':'孟知祥','仁罕':'李仁罕','鲁奇':'夏鲁奇','敬瑭':'石敬瑭','廷隐':'赵廷隐','弘昭':'朱弘昭','重诲':'安重诲','汉琼':'孟汉琼','季良':'赵季良','璋':'董璋'}
NEW_ALIASES={'李彦琦':['李彥琦','李彦珂','李彥珂']}

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

def event(code, title, n, quote, actors, when=None, note='', year=931, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='931年'+('正月' if n<=6 else '二月')+'本段；确日未独载'
    key = 'event_zztj_277_0931_' + code
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
        edge = 'participation_zztj_277_0931_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_277_0931_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive nine paragraphs, chronological facts and independently located supplements.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
jan='jiuwudaishi-042-931-january';xiaold='jiuwudaishi-070-xialuqi-death';xianew='xinwudaishi-033-xialuqi-siege';meng='xinwudaishi-064-meng-campaign';an='xinwudaishi-024-an-supervises';dong='xinwudaishi-051-lirenju-dongzhang'
E=ev('meng_submits_thanks','孟知祥奉表谢',1,'春，',None,[('知祥','奉谢表者')],when='931年正月壬戌',note='主仅载奉表谢，未具所谢事项或请降内容，不补为投降宣誓。')
E=ev('lirenhan_captures_suizhou','李仁罕攻陷遂州',2,'庚午，','李仁罕陷遂州，',[('仁罕','攻陷遂州者')],when='931年正月庚午',place='遂州',note='与930围城分阶段，不将九月三万出兵当城已陷。')
claim('event',E,'time_original','新孟世家记长兴二年正月李仁罕克遂州。',2,'二年正月，李仁罕克遂州，夏魯奇死之，','支持931正月，电子本原年号承上长兴；同书不同传异叙分别记录。',source=meng,relation='corroborates')
claim('event',E,'time_original','新董璋传另系孟知祥陷遂州于长兴元年九月，与主及新孟世家不同。',2,'長興元年九月，知祥攻陷遂州，璋攻陷閬州，','930九月与931正月冲突并列，概将孟和李统层次不擅改为两次都已证明陷遂；同新史也有内部差异，不当两个独立一致确证。',source=dong,relation='conflicts')
E=ev('xialuqi_suicide_suizhou','遂州陷落，夏鲁奇自杀',2,'夏鲁奇',None,[('鲁奇','自杀殉守的遂州主将')],when='931年正月庚午',place='遂州',note='自杀为主明言，不改成被李直接斩杀或病卒；精确时刻未具。')
claim('event',E,'description','旧夏传记夏鲁奇守城援路断绝、兵尽食穷。',2,'援路斷絕，兵盡食窮，','补围城绝援粮尽背景；不将旧夹引九国志作独立已查书源，不倒算精确出生日期。',source=xiaold,relation='adds')
claim('event',E,'description','新夏传亦记久无救兵、食尽，夏自刎死，年四十九。',2,'旬月救兵不至，城中食盡，魯奇自刎死，年四十九。','新传概叙，无独日，主庚午为主纪；旬月不换成精确三十日，49岁原述不改主体出生年。',source=xianew,relation='corroborates')
E=ev('shi_returns_jianzhou_north_hill','石敬瑭再引兵至剑州，屯北山',3,'癸酉，','屯于北山。',[('敬瑭','再进军剑州者')],when='931年正月癸酉',place='剑州北山',note='复是此前退剑门后再来，不当930十二月同一次驻屯重复；未具新兵数。')
E=ev('meng_displays_xialuqi_head','孟知祥枭夏鲁奇首示石敬瑭军',3,'孟知祥枭','以示之。',[('知祥','枭首示敌者'),('鲁奇','死后被示首者'),('敬瑭','受示的唐主将')],place='剑州唐军前',note='枭为死后首级展示，夏前句已自杀，不生成孟活杀夏的新死亡事件。')
claim('event',E,'description','新孟世家记使驰夏首示石军。',3,'遣人馳魯奇首示敬瑭軍，','同战示首环节，不抹主其后还战及二月才退的过程为新紧接班师同日。',source=meng,relation='corroborates')
E=ev('xia_sons_request_head_burial','夏鲁奇二子随石敬瑭在军，泣请取父首葬',3,'鲁奇二子','葬之，',[('鲁奇','二子请葬的亡父'),('敬瑭','受夏二子请者')],place='石敬瑭军中',note='二子无名，不造实名或二条反向亲属；随军是当前状态，不倒作父子在世同营会面。')
E=ev('shi_reassures_xia_sons','石敬瑭劝夏二子，认为孟知祥必葬其父',3,'敬瑭曰：','身首异处乎！”',[('敬瑭','劝慰、推测将葬者'),('知祥','被认为将葬夏者'),('鲁奇','被议收葬者')],note='长者必葬为石评价和预测，实际收葬下一动作独录；而父为你们父亲，不擅改逐字原字。')
E=ev('meng_buries_xialuqi','孟知祥收葬夏鲁奇',3,'既而知祥','收葬之。',[('知祥','收葬者'),('鲁奇','被收葬者')],place='两川',note='既而未独日，不硬赋癸酉同刻，墓地坐标未载。')
E=ev('shi_loses_zhao_retreats_jianmen','石敬瑭与赵廷隐战不利，再还剑门',3,'敬瑭与赵',None,[('敬瑭','战不利退军者'),('廷隐','对战蜀将')],place='剑州至剑门',note='本正月新战不重复930十二月战；不利未具死伤数，非石已被俘。')
E=ev('gaoconghui_zhongshuling','后唐加高从诲兼中书令',4,'丙戌，',None,[('高从诲','受加兼中书令者')],when='931年正月丙戌',place='荆南')
claim('event',E,'description','旧明宗纪同丙戌记高从诲落起复、加兼中书令。',4,'丙戌，荊南節度使高從誨落起復，加兼中書令。','补落起复与本镇，主加衔不等进入朝廷专任中书事务。',source=jan,relation='corroborates')
E=ev('dongchuan_returns_hezhou_wuxin','东川归合州于武信军',5,'东川',None,[('璋','东川主将、归合州一方')],place='合州、武信军',note='归为军辖归属动作，不误解为本人返合州；未独日，不强同前丙戌。')
E=ev('zhuhongzhao_former_favor','追叙朱弘昭谄事安重诲，连得大镇',6,'初，','连得大镇。',[('弘昭','史述谄事安并得镇者'),('重诲','被谄事的枢密使')],year=None,when='朱弘昭此前得镇往事；具体年日未载',note='初追叙年留空，谄为主史评价，不凭此建终身主仆或列未具具体大镇任命日期。')
E=ev('zhu_hosts_an_fengxiang','安重诲过凤翔，朱弘昭迎拜馆舍，延入寝室，妻子拜奉酒食',6,'重诲过凤翔，','礼甚谨。',[('重诲','途经受馆者'),('弘昭','迎拜款待者')],when='安赴西方军前途中；主追叙未独年月日',year=None,place='凤翔',note='妻子为妻与子女，无实名不造；追叙途经可能跨930年末931年初，不强现年当天。')
claim('event',E,'description','新安传亦记朱弘昭延安入寝室，妻子奉事。',6,'重誨過鳳翔，節度使朱弘昭延之寢室，使其妻子奉事左右甚謹。','同一次途中接待，来源原朱弘昭沿已有主体，主硃/朱繁异不另人。',source=an,relation='corroborates')
E=ev('an_tells_zhu_slander','安重诲泣对朱弘昭言此前受谗险不免，赖帝明察保族',6,'重诲为弘昭','得保宗族。”',[('重诲','泣诉者'),('弘昭','听泣诉者')],year=None,when='凤翔途中馆舍谈话；追叙未独年月日',place='凤翔',note='受谗为安自述，不独证具体谗人罪或其宗族此后永全。')
E=ev('zhu_reports_an_resentment','朱弘昭在安离去后奏称安怨望有恶言，恐到行营夺石敬瑭兵柄',6,'重诲既去，','恐夺石敬瑭兵柄。”',[('弘昭','奏谗指称者'),('重诲','被指怨望夺兵柄者'),('敬瑭','被称兵柄或遭夺的主将')],year=None,when='安离凤翔后，召还前；主追叙未独年月日',place='凤翔至后唐',note='怨望夺兵为弘昭指控和预测，不录为安已真实篡兵事件。')
E=ev('zhu_warns_shi_to_stop_an','朱弘昭致石敬瑭书，称安举措孟浪会惊溃军，请逆止',6,'又遗敬瑭书，','宜逆止之。”',[('弘昭','致警告书者'),('敬瑭','受书者'),('重诲','被要求拦阻者')],year=None,when='安赴军前途中，召还前；书未独年月日',place='凤翔至军前',note='不战溃为书中预测，非当时已全面不战自溃；不建安与所有将士永久敌关系。')
E=ev('shi_petitions_recall_an','石敬瑭惧而上言安至恐有变，请急召还',6,'敬瑭大惧，','宜急征还。”',[('敬瑭','请召安回者'),('重诲','被请召者')],when='安召还前；主未独月日',note='恐有变为石评估，不把未知兵变当已发生。')
E=ev('menghanqiong_reports_an_faults','孟汉琼自西方还，亦言安重诲过恶',6,'宣徽使孟汉琼','亦言重诲过恶，',[('汉琼','西方返后奏安过恶者'),('重诲','被指过恶者')],note='指控归说话者，无独罪证不转成证实罪名，不列无名具体罪状。')
E=ev('court_recalls_an_from_front','朝廷诏召安重诲还',6,'有诏召',None,[('重诲','被召还者')],note='下诏与三泉得诏、凤翔拒入、东返分别，不当已经回洛阳。')
E=ev('shi_burns_camp_retires_north','石敬瑭因遂阆陷、粮运不继，烧营北归',7,'二月，己丑朔，','烧营北归。',[('敬瑭','烧营退军者')],when='931年二月己丑朔',place='剑门军营至北方',note='退兵与前两次退剑门不同，本次北归，不将新传紧接示首简叙当一月退全军。')
claim('event',E,'description','新孟世家在示夏首后接记石敬瑭班师。',7,'敬瑭乃班師。','新概叙班师未独月日，主一月仍再战二月方北归，保留层次而不抹主。',source=meng,relation='corroborates')
E=ev('meng_hides_retreat_letter_tests_zhao','军前告孟唐兵退，孟匿书故问赵季良北军渐进如何',7,'军前以告','北军渐进，奈何？”',[('知祥','匿真退报而试问者'),('季良','被问者')],place='成都',note='北军渐进是孟隐书问语，实前已退，不创建新的真实唐进军事件。')
E=ev('zhaojiliang_predicts_retreat_mianzhou','赵季良称北军不过绵州必遁，解释蜀逸唐劳与粮尽，孟笑示退军书',7,'季良曰：',None,[('季良','未见退书而判断将遁者'),('知祥','笑而出示书者')],place='成都、绵州军略话语',note='绵州为假设进路界限，非北军本句已到绵；天下战略效力为当时判断非已取得天下。')
E=ev('an_receives_recall_sanquan','安重诲至三泉，得诏亟归',8,'安重诲至','得诏亟归；',[('重诲','三泉受召回者')],place='三泉')
claim('event',E,'description','新安传亦记行至三泉被召还。',8,'重誨行至三泉，被召還。','同地点同召，未具确日不强赋二月己丑。',source=an,relation='corroborates')
E=ev('zhu_refuses_an_fengxiang_return','安重诲归过凤翔，朱弘昭拒入；安惧驰骑东返',8,'过凤翔，',None,[('重诲','遭拒后惧而东驰者'),('弘昭','拒纳者')],place='凤翔至东行',note='不内/不纳同动作，非第一次迎拜馆舍相矛盾事件，两次经过方向阶段有别；东驰不证本句已到京。')
claim('event',E,'description','新安传记朱拒不纳，安惧驰趋京师。',8,'過鳳翔，弘昭拒而不納，重誨懼，馳趨京師。','同归程拒入，后未至拜河中为后主线未提前。',source=an,relation='corroborates')
E=ev('shu_pursues_shi_lizhou','两川兵追石敬瑭至利州',9,'两川兵追','至利州，',[('敬瑭','被追的退军主将')],place='剑门至利州',note='追兵匿名，不把孟董每人均亲追本人到利州；追至不等俘石。')
E=ev('liyanqi_abandons_lizhou','昭武节度使李彦琦弃利州城走',9,'壬辰，','弃城走；',[('李彦琦','弃利州的昭武节度使')],when='931年二月壬辰',place='利州',note='本李彦琦新李彦珂按同城同弃城职事识别；与李彦温李彦超不因近字混，未独证茂贞养子传身份不加父亲关系。')
claim('person',people['李彦琦'],'description','新孟世家作利州李彦珂，闻唐军东归弃城走。',9,'利州李彥珂聞唐軍敗東歸，乃棄城走，','珂/琦非繁简机械互换，同地同退役对应后规范沿主李彦琦，保留别名字形。',source=meng,relation='adds')
E=ev('shu_enters_lizhou','两川兵入利州',9,'甲午，','两川兵入利州。',[],when='931年二月甲午',place='利州',note='入城与守将壬辰弃城不同日，不将无名攻城将补猜赵廷隐本人当天首先冲城。')
E=ev('zhaotingyin_zhaowu_liuhou','孟知祥以赵廷隐为昭武留后',9,'孟知祥以赵','为昭武留后，',[('知祥','任留后者'),('廷隐','受任昭武留后者')],place='昭武、利州',note='留后不写成已经朝廷正式册节度使；未独干支不硬赋甲午。')
claim('event',E,'description','新孟世家亦记孟以赵为昭武军留后。',9,'知祥以趙廷隱為昭武軍留後。','同任命复用事件，不提前后兼两川赵保宁李肇昭武的另一阶段。',source=meng,relation='corroborates')
E=ev('zhao_requests_plot_against_dong','赵廷隐密请孟知祥借董璋至剑州劳军时图之，称董多诈将为患，欲并两川',9,'廷隐遣使密言','得志于天下。”',[('廷隐','密陈图董计划者'),('知祥','受密陈者'),('璋','被图谋对象')],place='利州至成都、剑州计划',note='多诈未来患为赵判断，图之为建议未执行，不创建董已被赵杀或孟已经并两川事件。')
E=ev('meng_refuses_zhao_plot','孟知祥不许赵廷隐图董璋之谋',9,'知祥不许','知祥不许。',[('知祥','拒绝建议者'),('廷隐','建议被拒者'),('璋','被建议谋图对象')],note='不许拒本次建议，不等无条件永远不会同董开战。')
E=ev('dong_stays_zhao_camp_leaves','董璋入赵廷隐营，留宿后离去',9,'璋入廷隐营','留宿而去。',[('璋','劳军途中入营宿者'),('廷隐','董所入营主将')],place='赵廷隐营',note='宿而去非当场被杀；同营不推永久盟友或结义。')
E=ev('zhao_laments_plot_refusal','赵廷隐叹不从其谋，祸难未已',9,'廷隐叹',None,[('廷隐','叹未来祸患者')],note='未已为其判断，不当该日两川已经新的大乱。')
E=ev('lirenhan_xialu_commander_east','孟知祥以李仁罕为峡路行营招讨使，命率水军东略地',10,'庚子，',None,[('知祥','任招讨命东略者'),('仁罕','武信留后、受峡路招讨率水军者')],when='931年二月庚子',place='峡路东向',note='任命与东略指令未具此日攻陷具体城，不提前夔州安崇阮奔。')
reviews={1:'壬戌奉表谢仅动作，不造表内容、所谢事或已投降；朝廷削爵和战仍可与奉表并存。',2:'庚午陷遂夏自杀分。新孟二年正月支持，新董元年九月陷遂相冲并列，同书内部差不可冒两独立一致源；旧绝援兵食穷、新旬月食尽49岁补，电子原年龄不倒精确生日。',3:'癸酉石再北山而非930同屯。孟死后枭首非孟活杀夏；二子无名不造实名，石必葬判断与孟收葬实际分，战不利退剑门不同二月北归。新示首接班师概叙不抹一月再战。',4:'丙戌高加中书旧同落起复佐核，职衔不等亲自中书部门当值。',5:'东川归合武信是军辖转属，未独日不承丙戌；不绘现代边界。',6:'初朱得镇null；安赴程经过凤翔接待及泣诉、朱报和石书追叙未独年null，不强931当日。妻子妻与子女无名不造；谄史评、安受谗自说、朱怨恶夺柄石惧军变皆归说者，未证兵变不建事实。孟汉琼奏过与诏召分，下诏与三泉接诏不同。',7:'二月己丑烧营北归与此前两退剑门分；新示首紧接班师未独日按主分阶段。孟匿真退书问北军渐进为试问非实际进军，赵不过绵州预测非唐已到绵。',8:'三泉得诏归、凤翔二过被拒东返分，前迎拜与归拒是两次经过，东驰尚非已到洛，后河中拜新来源未提前。',9:'追至利不等获石。壬辰李彦琦弃城、甲午入城分；新作李彦珂同利弃役校，近字不混李彦温、未加无证茂贞养父边。赵昭武留后未正式朝册；密图董是建议被拒，董宿营去实际，赵多诈未来患叹语不独证新乱已发，后并两川未提前。',10:'庚子任李峡路招讨与东略指令，不提前夔州陷及安崇阮逃；李武信留后由新孟遂陷后任命可回查，职身份用于识人。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,11):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=931,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph='zztj-v277-y0931-p011',next_volume=277,next_year=931,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续931年第1—10段，原63—72行；遂陷夏死、石再战退北、安途中告诏归、利州弃入与图董被拒、李东略任命。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,11)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
