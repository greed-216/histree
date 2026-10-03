# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 926, paragraphs 7–12."""
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
 ('jiuwudaishi-038-conghou',P/'sources/library/jiuwudaishi-038-conghou','6ee141a6','薛居正等'),
 ('jiuwudaishi-038-anzhonghui-kongxun',P/'sources/library/jiuwudaishi-038-anzhonghui-kongxun','6ee141a6','薛居正等'),
 ('jiuwudaishi-038-wuzhen-shi',P/'sources/library/jiuwudaishi-038-wuzhen-shi','6ee141a6','薛居正等'),
 ('liaoshi-002-tianxian-era',P/'sources/library/liaoshi-002-tianxian-era','6ee141a6','脱脱等'),
 ('liaoshi-002-taizu-burial',P/'sources/library/liaoshi-002-taizu-burial','6ee141a6','脱脱等'),
 ('liaoshi-071-shulv-wrist',P/'sources/library/liaoshi-071-shulv-wrist','6ee141a6','脱脱等'),
 ('tongjian-275-927-offices-and-khitan',P/'sources/library/tongjian-275-927-offices-and-khitan','6ee141a6','司马光等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-275-927-offices-and-khitan']
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0927-p007-p012',
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
for n in range(7, 13):
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
    ck = f'claim_zztj_275_0927_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','从厚':'李从厚','从荣':'李从荣','徐知诰':'李昪','吴王':'杨溥','述律太后':'述律平'}
NEW_ALIASES={'李从厚':['李從厚','后唐闵帝'],'赵思温':['趙思溫']}
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
E=ev('conghou_henan_and_six_guards','皇子李从厚加同平章事，任河南尹、判六军诸卫事',7,'癸酉','诸卫事。',[('帝','任命者'),('从厚','皇子、获任者')],when='927年正月癸酉',place='河南府及后唐朝廷',note='不将同平章事一衔单独等同实际执政宰相；未称本年储君。')
claim('event',E,'description','旧明宗纪称第三子从厚加检校太保、同平章事、河南尹、判六军诸卫事。',7,'癸酉，第三子金紫光祿大夫、檢校司徒從厚加檢校太保、同平章事、河南尹，判六軍諸衛事。','补子次与检校衔，不反推生年。',source='jiuwudaishi-038-conghou',relation='adds')
relationship('帝','从厚','父亲',7,'以皇子从厚同平章事，充河南尹，判六军诸卫事。','帝为李嗣源，父至子；不另建反向边。')
relationship('从荣','从厚','兄长',7,'从厚，从荣之母弟也。','母弟明确同母且从厚为弟，从荣至从厚兄长方向，未载母名不猜。')
E=ev('congrong_displeased_conghou','李从荣听说李从厚任官后不悦',7,'从荣闻之',None,[('从荣','史书记不悦者')],when='927年正月癸酉任命之后，确日未另载',place='后唐',note='不悦属史叙反应，不推本日已谋反或新增敌人关系。')
E=event('conghou_takes_henan_office','李从厚到河南府领事，郑珏以下宰相会送，旧史称非例',7,'戊寅，皇子從厚領事於河南府，宰相鄭玨已下會送，非例也。',[('从厚','到府领事者'),('郑珏','会送宰相')],when='927年正月戊寅，据旧明宗纪',place='河南府',source='jiuwudaishi-038-anzhonghui-kongxun',note='补同次任命之后就职，不将非例作违法判决；旧郑玨与已有郑珏同宰相字形校。')
E=ev('anzhonghui_adds_shizhong','枢密使安重诲加兼侍中',8,'己卯','兼侍中，',[('帝','加官所归者'),('安重诲','枢密使、加兼侍中')],when='927年正月己卯',place='后唐朝廷')
claim('event',E,'description','旧明宗纪同日另载安重诲加开府仪同三司、检校太傅兼侍中。',8,'己卯，樞密使、光祿大夫、檢校太保、行兵部尚書安重誨加開府儀同三司、檢校太傅、兼侍中；','完整加衔补证，不把各衔拆成几次任命。',source='jiuwudaishi-038-anzhonghui-kongxun',relation='adds')
E=ev('kongxun_adds_pingzhang','枢密使孔循加同平章事',8,'己卯',None,[('帝','加官所归者'),('孔循','枢密使、加同平章事')],when='927年正月己卯',place='后唐朝廷',note='引用整句以承己卯及枢密身份，不新增无证统属关系。')
claim('event',E,'description','旧明宗纪称孔循加检校太傅、同平章事。',8,'樞密使、檢校太保、守秘書監孔循加檢校太傅、同平章事。','补检校加衔。',source='jiuwudaishi-038-anzhonghui-kongxun',relation='adds')
E=ev('chai_military_dress_censured','吴马军都指挥使柴再用穿戎服入朝，被御史弹劾而不服',9,'吴马军','不服。',[('柴再用','戎服入朝、遭弹不服者')],place='吴朝廷',note='恃功是书评价，未载御史姓名、处分结果，不造罚俸给柴。')
E=ev('xu_self_impeaches_after_feigned_error','徐知诰故意在便殿误通起居，退后自劾，吴王优诏不问',9,'侍中徐知诰','优诏不问。',[('徐知诰','侍中、故作误礼并自劾'),('吴王','优诏不问者')],place='吴便殿及朝廷',note='徐知诰沿既有李昪主体，927展示叙述用史载名；阳为佯意原字保留；吴王据当前杨溥，不提前称本段已登帝。')
E=ev('xu_requests_month_salary_deduction','徐知诰坚持请求扣一月俸，史书称中外肃然',9,'知诰固请',None,[('徐知诰','主动请扣俸者')],place='吴朝廷',note='主固请为请求，未载具体执行账或金额，不直接写扣俸已完成；肃然为作者总体评价。')
E=ev('khitan_tianxian_era','《通鉴》本段记契丹改元天显',10,'契丹改元','天显，',[],place='契丹',when='主927年正月段；辽史天显元年二月（926）',note='主按所在年段保留927，辽改元发生926的异年并存；不把改元施事写阿保机已死后继续操作。')
claim('event',E,'time_original','《辽史》太祖纪将改元记在天显元年二月，属926年，与主书927年段不同。',10,'壬辰，以青牛白馬祭天地。大赦，改元天顯。','年界前段天显元年春正月已逐字归档为context；跨书异年不造第二次同名改元。',source='liaoshi-002-tianxian-era',relation='conflicts')
E=ev('abaoji_burial','阿保机下葬，主书记在木叶山',10,'契丹改元','木叶山。',[('阿保机','受葬的故主')],place='木叶山（主）；祖陵（辽）',when='主927年正月段，确日未载；辽天显二年八月丁酉',note='葬不是当日卒，沿已合并阿保机主体；不把木叶山和祖陵擅定为完全同址，不填写坐标。')
claim('event',E,'time_original','《辽史》记天显二年八月丁酉葬太祖于祖陵。',10,'二年八月丁酉，葬太祖皇帝於祖陵，','辽卷二上承天显元年与太祖卒，二年927；主当前正月段与辽八月分存。',source='liaoshi-002-taizu-burial',relation='conflicts')
claim('event',E,'description','《辽史》称置祖州天城军节度使以奉陵寝。',10,'置祖州天城軍節度使以奉陵寢。','补陵寝管理设置；不套之后统和重熙追谥入本次927。',source='liaoshi-002-taizu-burial',relation='adds')
E=ev('shulv_sends_retinue_to_dead_emperor','述律太后令部分左右到墓传语而杀之，史书记前后以百数',10,'述律太后','以百数。',[('述律太后','派人到墓并杀左右者')],year=None,when='阿保机卒后至本段葬礼相关叙述，前后各次时间未具',place='契丹、阿保机墓所',note='前后以百数为概数非精确100；桀黠书评价，不把所有左右都写为犯罪，不虚构受害者姓名。')
E=ev('zhaosiwen_refuses_death_mission','赵思温拒往墓所，以太后先行自己继之回应',10,'最后，平州人','后行，臣则继之。”',[('赵思温','平州人、拒行回应者'),('述律太后','质问者')],year=None,when='述律派左右赴墓传语杀人后，具体日未载',place='契丹',note='亲近为对话所述，不造生前具体官职或平州刺史仅凭人籍；回应是假设殉死不是已赴死。')
E=ev('shulv_explains_cannot_follow_emperor','述律太后以嗣子幼弱国家无主为说辞，解释不随先帝入地下',10,'后曰：“吾非','不得往耳。”',[('述律太后','解释者')],year=None,when='赵思温回应之后，同次对话确日未载',place='契丹',note='说辞不作为嗣子精确年龄或真实国家无人掌政的独立事实。')
E=ev('shulv_cuts_wrist','述律太后断一腕，令置墓中；赵思温因而得免',10,'乃断',None,[('述律太后','断腕命置墓者'),('赵思温','获免死者')],year=None,when='主述律与赵对话之后未具确日；辽后妃传系及葬',place='契丹、阿保机墓所',note='一腕主未明左右，辽补右腕；不把太后写当时已经殉死。')
claim('event',E,'description','《辽史》后妃传称及葬太后欲身殉，亲戚百官力谏，因断右腕纳柩。',10,'及葬，欲以身殉，親戚百官力諫，因斷右腕納於柩。','补右腕与纳柩；主赵问答/辽亲戚百官谏为不同叙事，不覆盖其一；未借本传后时953卒写927死亡。',source='liaoshi-071-shulv-wrist',relation='adds')
E=ev('wuzhen_three_grain_convoys','李嗣源此前令冀州刺史乌震三次领兵运粮入幽州',11,'帝以','入幽州，',[('帝','运粮安排者'),('乌震','冀州刺史、三次领兵运粮')],year=None,when='927年二月戊子任命前的三次运粮，各次确日未载',place='冀州至幽州',note='三将兵为三次将兵，不是三个名叫乌震的人或三位将军，不把三次强放戊子同日。')
E=ev('wuzhen_hebei_deputy_ningguo','乌震任河北道副招讨，领宁国节度使，屯卢台军',11,'二月','屯卢台军。',[('帝','任命者'),('乌震','副招讨、领宁国、卢台驻屯者')],when='927年二月戊子',place='卢台军',note='领节度军额不等本人离卢台至宣州到任；后续乱杀尚未本批录入。')
claim('event',E,'description','旧明宗纪同日称前北面水陆转运招抚使、冀州刺史乌震领宣州节度使。',11,'戊子，以前北面水陸轉運招撫使、守冀州刺史烏震領宣州節度使。','补前转运招抚衔；主宁国/旧宣州不同军州称谓并列，未造两任赴任。',source='jiuwudaishi-038-wuzhen-shi',relation='adds')
E=ev('fang_returns_yanzhou','乌震代房知温，房知温归兖州',11,'代泰宁',None,[('乌震','承前句替任者'),('房知温','泰宁节度使、同平章事、归镇者')],when='927年二月戊子任命相关，归抵日未另载',place='卢台军至兖州',note='主归镇概叙，后文实际未交印与卢台乱将连续录入，不把本句写为已完成交印抵兖。')
E=ev('shi_six_guards_deputy','保义节度使石敬瑭加兼六军诸卫副使',12,'庚寅',None,[('帝','加官所归者'),('石敬瑭','加兼六军诸卫副使')],when='927年二月庚寅',place='后唐朝廷、保义军',note='兼副使不误作新晋皇帝，本段不提前936称帝。')
claim('event',E,'description','旧明宗纪同日称陕州节度使石敬瑭加检校太傅兼六军诸卫副使。',12,'庚寅，陝州節度使、檢校司徒石敬瑭加檢校太傅兼六軍諸衛副使。','补检校太傅及州名，同职同日只补一次任命。',source='jiuwudaishi-038-wuzhen-shi',relation='adds')
review='连续7—12段逐句回查。从厚皇子第三子身份与从荣母弟明确：父李嗣源至从厚、从荣兄长至从厚；不猜母名、储君或因不悦推已反。旧戊寅到河南领事会送与癸酉任命不同阶段。己卯两枢密加衔分主体。柴戎服御史弹未服未记实际处罚；徐佯误起居自劾优诏不问再固请一月俸为请求不是执行账，肃然作者概述，徐沿李昪旧主体、吴王沿杨溥。契丹改元主927段/辽元年二月926，辽前元年上下文逐字归档；葬主正月段木叶/辽二年八月丁酉祖陵，不擅合墓址，不把葬日作死日。述左右桀黠为书评价、百数概数，各次时间未具null；赵平州籍不擅添官，亲近是对话，幼弱无主为后说辞非实测；断腕主一腕/辽右腕，赵免死/亲戚百官谏不同叙事并列，太后未殉死。阿保机沿已应用合并主体。乌三将兵为三次运粮，未知前日null，戊子加副招讨领宁国与旧宣州同日同人不复制任；房归只安排方向，不提前已交印抵兖，后文未读不标完成。石兼副使及检校补衔不提前帝号。简体展示，原文异体保留，纸本及异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(7,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=927,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(7,13)],next_paragraph='zztj-v275-y0927-p013',next_volume=275,next_year=927,supplements=supplements,excluded_non_body=[],coverage='卷275天成二年连续7—12段，原文件81—86行；皇子、枢密加官、吴纪律、契丹改元葬礼及幽州军务。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(7,13)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
context=sources['liaoshi-002-tianxian-era']/'context'
r=json.loads((context/'paragraph.json').read_text())
assert '天顯元年春正月' in r['text']
cov=json.loads((P/'coverage.json').read_text())
cov['chronology_context']=[dict(file=str((context/'source.txt').relative_to(P)),paragraph_id=r['id'],sha256=hashlib.sha256((context/'source.txt').read_bytes()).hexdigest(),note='辽卷二改元前段元年年界正文；仅用于定位，不生成无关渤海史事。')]
(P/'coverage.json').write_text(json.dumps(cov,ensure_ascii=False,indent=2)+'\n')
