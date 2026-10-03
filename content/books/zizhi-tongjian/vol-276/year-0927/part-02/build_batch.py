# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 927, paragraphs 7–10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 26))
specs=[
 ('tongjian-276-july-opening',YEAR/'part-01/sources/library/tongjian-276-july-opening','e38f4580','司马光等'),
 ('xinwudaishi-066-chu-offices',P/'sources/library/xinwudaishi-066-chu-offices','e2f62270','欧阳修'),
 ('jiuwudaishi-133-chu-institutions',P/'sources/library/jiuwudaishi-133-chu-institutions','e2f62270','薛居正等'),
 ('jiuwudaishi-038-september-offices',P/'sources/library/jiuwudaishi-038-september-offices','e2f62270','薛居正等'),
 ('jiuwudaishi-038-fu-surname',P/'sources/library/jiuwudaishi-038-fu-surname','e2f62270','薛居正等'),
 ('xinwudaishi-006-927-opening',ROOT/'content/books/zizhi-tongjian/vol-275/year-0927/part-01/sources/library/xinwudaishi-006-927-opening','d50fed5c','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-july-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0927-p007-p010',
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
lines = (ROOT / 'resources/derived/tongjian/276.txt').read_text().splitlines()
for n in range(7, 11):
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
        citation = f'卷276·天成二年（927）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0927_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'李彦超':'符彦超','李鐸':'李铎','楚王殷':'马殷','王晏球':'杜晏球','帝':'李嗣源','仁赞':'孟昶','琼华':'琼华长公主','李从严':'李继曮','楚王殷':'马殷','高季兴':'高季昌'}
NEW_ALIASES={'李铎':['李鐸'],'崔颖':['崔穎'],'拓跋恒':['元恒'],'张彦瑶':['張彥瑤'],'张迎':[],'马讯':[],'李序':[]}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷276天成二年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='927年八月册礼后本段；确日未载', note='', year=927, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_276_0927_' + code
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
        edge = 'participation_zztj_276_0927_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_276_0927_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
chu='xinwudaishi-066-chu-offices'
E=ev('chu_investiture_envoys_arrive','册礼使到长沙',7,'册礼使','至长沙，',[],place='长沙',note='主未具使者姓名与到日；使团到达不同六月封号决定。')
claim('event',E,'description','新楚世家称朝廷遣尚书右丞李序持节，以竹册封马殷。',7,'乃遣尚書右丞李序持節以竹冊封之。','补使者身份、仪物；新未具使到日，不将派遣等同当日到达。',source=chu,relation='adds')
E=event('li_xu_sent_chu_bamboo_investiture','朝廷遣尚书右丞李序持节，以竹册封马殷',7,'明宗封殷楚國王，有司言無封國王禮，請如三公用竹冊，乃遣尚書右丞李序持節以竹冊封之。',[('李序','尚书右丞、持节册礼使'),('马殷','册封所涉楚国王')],source=chu,when='927年天成二年，遣使确月日未载；到长沙前',place='后唐至楚',note='派遣与实际使到分事；不重复创建六月丙申楚国王封号决定。')
E=ev('chu_palaces_offices_established','册礼后马殷建国承制，立宫殿、置百官',7,'楚王殷','或微更其名：',[('楚王殷','建国承制、设置百官者')],place='长沙、楚',note='此为册礼后仪制设置，不将楚政权起源日期改成927；如天子及微更名为史书概叙。')
claim('event',E,'description','新楚世家称马殷以潭州为长沙府，建国承制、自置官属。',7,'殷以潭州為長沙府，建國承制，自置官屬，','补州府称谓变化；未具现代坐标，不把旧潭州迁到新地点。',source=chu,relation='adds')
E=ev('chu_offices_and_command_styles','楚改翰林学士为文苑学士、知制诰为知辞制、枢密院为左右机要司，群下称殿下、令称教',7,'翰林学士','令曰教。',[('楚王殷','所立官制及称谓所归者')],place='楚、长沙',note='三个机构或官职和两种称谓分别保留；不等称帝或所有制度完全复制。')
E=event('chu_earlier_wenyuan_background','旧史记马殷在梁时请依诸王行台置天官幕府，已有文苑学士之号',7,'既封楚王，仍請依唐諸王行臺故事，置諸天官幕府，有文苑學士之號，知詔令之名，',[('马殷','请置行台幕府者')],source='jiuwudaishi-133-chu-institutions',year=None,when='旧传梁贞明中至唐同光初之前的概叙，确年日未载',place='楚',note='早期背景单列，年不硬归927；旧知诏令与主知辞制名称并存，不视为927才首次出现文苑学士。')
for code,name,office,start,end,newquote in [
 ('yaoyanzhang_left_chancellor','姚彦章','左丞相','以姚彦章','左丞相，','姚彥章為左相，'),
 ('xudexun_right_chancellor','许德勋','右丞相','许德勋','右丞相，','許德勳為右相，'),
 ('liduo_situ','李铎','司徒','李鐸','司徒，','李鐸為司徒，'),
 ('cuiying_sikong','崔颖','司空','崔颖','司空，','崔穎為司空，'),
 ('tuobaheng_pushe','拓跋恒','仆射','拓跋恒','仆射，','拓拔常為僕射，'),
]:
 E=ev(code,name+'获任楚国'+office,7,start,end,[(name,'楚国'+office+'获任者')],place='楚、长沙')
 claim('event',E,'description','新楚世家记'+name+'为'+office+'。',7,newquote,'同批楚国官属授任补证；拓拔常对应主拓跋恒，同册命同职识人，名字差异保留待纸本校核，不靠繁简转换改原字。' if name=='拓跋恒' else '主简体与新原字相合，丞相与相职名并列。',source=chu,relation='corroborates')
E=ev('zhangyanyao_zhangying_jiy aosi'.replace(' ',''),'张彦瑶、张迎判楚国机要司',7,'张彦瑶','判机要司。',[('张彦瑶','判机要司者'),('张迎','判机要司者')],place='楚、长沙',note='两人同职同事，不凭共事建立亲属或盟友关系。')
E=ev('chu_acting_officials_and_governors_rules','楚管内官属皆称摄，朗桂节度使先自行任命再请朝命',7,'然管内','请命。',[('楚王殷','楚国任官制度所归者')],place='楚、朗州、桂州',note='摄为代理职衔；先除后请仅本句朗桂例外，不扩展成所有方镇皆同规。')
E=ev('tuobaheng_changes_surname_taboo','拓跋恒本姓元，主书记其避马殷父讳改姓',7,'恒本姓','改焉。',[('拓跋恒','避讳改姓者')],year=None,when='927年任官段所附身份背景，改姓确年未载',place='楚',note='姓元为身份信息，避殷父讯原字保留；新父元丰异文使原因有疑，不据此强校为避元字或注册拓拔常正式别名。')
relationship('马讯','楚王殷','父亲',7,'恒本姓元，避殷父讯改焉。','主明称殷父讯，先按主书建父亲主体；新父元丰异名存说明，暂不作为正式别名。')
claim('person',people['马讯'],'description','新楚世家记马殷父名元丰，与主本句殷父讯的文字不同。',7,'父元豐曰景莊，','同父角色的姓名异文保留，不自动并为已证别名或另建重复父亲。',source=chu,relation='conflicts')
E=ev('siyuan_reports_false_order_against_scholars','李嗣源向安重诲称李从荣左右矫宣旨意，令其不接儒生',7,'九月','恐弱人志气者。',[('帝','指控矫宣旨意者'),('安重诲','受告者'),('李从荣','伪旨所指皇子')],when='927年九月，确日未载',place='后唐朝廷与李从荣藩镇',note='这是皇帝所陈指控，匿名左右不建人物；不凭此确认李从荣已实际逐儒生。')
E=ev('siyuan_explains_scholar_guidance','李嗣源称为年轻的李从荣择名儒辅导，并欲斩矫旨者',7,'朕以','欲斩之；',[('帝','说明辅导安排、拟处死者'),('李从荣','名儒辅导对象')],when='927年九月，确日未载',place='后唐朝廷',note='选择名儒为皇帝自述；欲斩为意向，未录已杀，未具儒者姓名不虚构。')
E=ev('anzhonghui_requests_admonition_only','安重诲请求只严戒李从荣身边矫旨者',7,'重诲请',None,[('安重诲','建议仅严戒者')],when='927年九月，确日未载',place='后唐朝廷',note='请严戒为建议，本句未明记皇帝批准或执行，不写已获赦免。')
E=ev('fuyancha o_requests_surname'.replace(' ',''),'北都留守李彦超请求恢复符姓',8,'北都','复姓符，',[('李彦超','北都留守、请求复姓者')],when='927年九月，确日未载',place='北都至后唐朝廷',note='李彦超按已有别名复用符彦超，不新建另一个人物。')
claim('event',E,'description','旧明宗纪记李彦超自称先父存审本姓符，武皇赐姓，故请还本姓。',8,'北京留守李彥超上言：「先父存審，本姓符氏，蒙武皇賜姓，乞卻還本姓。」從之。','北京与北都称谓并列；此句在庚申事项后乙丑前，未另具日，不强认复姓诏本身为庚申。',source='jiuwudaishi-038-fu-surname',relation='adds')
relationship('符存审','符彦超','父亲',8,'北京留守李彥超上言：「先父存審，本姓符氏，蒙武皇賜姓，乞卻還本姓。」從之。','上言明确父存审，沿已有符存审主体，先父是已死称谓不另造死亡事件。',source='jiuwudaishi-038-fu-surname')
E=ev('fuyanchao_surname_restoration_allowed','朝廷允许李彦超恢复符姓',8,'北都',None,[('李彦超','复姓获准者')],when='927年九月，确日未载',place='后唐朝廷',note='从之明确许可，既有主体名符彦超继续复用。')
E=ev('kongxun_eastern_capital_deputy','枢密使孔循兼东都留守',9,'丙寅',None,[('孔循','枢密使、兼东都留守获授者')],when='927年九月丙寅',place='东都',note='兼任，不推已罢枢密使或此日已经迁居到任。')
claim('event',E,'description','旧明宗纪同记丙寅孔循兼东都留守。',9,'丙寅，樞密使孔循兼東都留守。','同日同职补证。',source='jiuwudaishi-038-september-offices',relation='corroborates')
E=ev('khitan_seeks_friendship','契丹向后唐请求修好',10,'壬申','来请修好，',[],when='927年九月壬申',place='契丹至后唐朝廷',note='主未具来使姓名；与旧梅老没古来贡是同月关联资料，不强确认恰为这次修好使者。')
claim('event',E,'description','新明宗纪同记九月壬申契丹使梅老来。',10,'壬申，契丹使梅老來。','同日使者名补证，但新仅来、不录具体议和内容；旧梅老没古字形保留未立多使身份。',source='xinwudaishi-006-927-opening',relation='adds')
E=ev('tang_replies_khitan_friendship','后唐遣使回复契丹修好请求',10,'壬申',None,[],when='927年九月壬申条，遣使确日未另记',place='后唐至契丹',note='使者匿名不虚构；报之为回复，不据此宣告永久联盟或正式条约成立。')
review='连续7—10段逐句校核。册使到长沙、唐派李序竹册和马立宫置百官分阶段，六月封号旧事不重复创建，楚政权起源不改到927。主官制三名两称谓及摄官朗桂先除后请悉录；旧梁时已有文苑官署为追叙null，非927第一次。七任官分事，李鐸展示李铎，崔颖新崔穎同人，拓跋恒与新拓拔常同册同仆射对应但异名待校，不注册常正式别名；本姓元、避主父讯改姓确年未载，主父讯/新父元丰异文不自动正式别名、不重复建父。张两判共同职不推出亲属。九月帝控从荣左右矫旨为话语，拟斩非实杀，安请严戒非已许可执行；儒者匿名不建。李彦超按旧别名符彦超复用，旧先父存审明确父符，复姓请求和许可分开，旧庚申事项后未另具日不硬定命日。孔丙寅兼东都未罢枢密或强到日。契丹壬申求好与唐遣回复分事，新同日梅老来补使者但不将旧梅老没古同月来贡强等此次主使，也不宣布永久盟约。简体展示原字引用，纸本及异名待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(7,11):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=927,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(7,11)],next_paragraph='zztj-v276-y0927-p011',next_volume=276,next_year=927,supplements=supplements,excluded_non_body=[],coverage='卷276连续7—10段、原文件12—15行；楚册礼官制任官、从荣辅导、符姓恢复及外交。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(7,11)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
