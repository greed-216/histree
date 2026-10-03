# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 927, paragraphs 1–6."""
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
 ('jiuwudaishi-036-926-may-offices',ROOT/'content/books/zizhi-tongjian/vol-275/year-0926/part-03/sources/library/jiuwudaishi-036-926-may-offices','5c38857d','薛居正等'),
 ('tongjian-276-july-opening',P/'sources/library/tongjian-276-july-opening','e38f4580','司马光等'),
 ('jiuwudaishi-038-august-eclipse',P/'sources/library/jiuwudaishi-038-august-eclipse','e38f4580','薛居正等'),
 ('jiuwudaishi-067-renhuan-retirement',P/'sources/library/jiuwudaishi-067-renhuan-retirement','e38f4580','薛居正等'),
 ('jiuwudaishi-038-july-reconquest',ROOT/'content/books/zizhi-tongjian/vol-275/year-0927/part-06/sources/library/jiuwudaishi-038-july-reconquest','0c15026c','薛居正等'),
 ('xinwudaishi-006-927-opening',ROOT/'content/books/zizhi-tongjian/vol-275/year-0927/part-01/sources/library/xinwudaishi-006-927-opening','d50fed5c','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-july-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0927-p001-p006',
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
for n in range(1, 7):
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
    ck = f'claim_zztj_276_0927_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'王晏球':'杜晏球','帝':'李嗣源','仁赞':'孟昶','琼华':'琼华长公主','李从严':'李继曮','楚王殷':'马殷','高季兴':'高季昌'}
NEW_ALIASES={}
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

def event(code, title, n, quote, actors, when='927年七月本段；确日未载', note='', year=927, place='五代十国', source=None, stable_key=None):
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
E=ev('wangyanqiu_north_deputy_commander','归德节度使王晏球获任北面副招讨使',1,'秋',None,[('王晏球','归德节度使、获任北面副招讨使')],place='后唐北面行营',note='未具具体敌军、部署人数与到任日；不把任命等同实际战斗。')
claim('event',E,'time_original','旧明宗纪记七月庚戌朔任宋州节度使王晏球为北面行营副招讨使。',1,'秋七月庚戌朔，以宋州節度使王晏球充北面行營副招討使。','主七月无日，旧补朔日；归德军与宋州职衔记法并列，同一人同任命不重复建事。',source='jiuwudaishi-038-july-reconquest',relation='adds')
claim('person',people['杜晏球'],'aliases','王晏球与旧称杜晏球、赐名李绍虔为同一人；本批沿用全站杜晏球主体。',1,'內李紹虔上言：「臣本姓王，後移杜氏，蒙前朝賜今姓名，乞復本姓。」詔並可之。李紹真復曰霍彥威，李紹英復曰房知溫，李紹虔復曰王晏球，','旧明宗纪上表自称本王后杜再赐李，恢复王晏球；作为本段身份补证，不重新创建926复姓名事件或另建王晏球。',source='jiuwudaishi-036-926-may-offices',relation='adds')
E=ev('kuizhou_upgraded_ningjiang','后唐将夔州升为宁江军',2,'丙寅','宁江军，',[],when='927年七月丙寅',place='夔州',note='军镇设置，不当新增城池或迁移州治。')
claim('event',E,'description','旧明宗纪亦记丙寅升夔州为宁江军。',2,'丙寅，升夔州為寧江軍，','同日设置补证；本段不重复前批三州收复战事。',source='jiuwudaishi-038-july-reconquest',relation='corroborates')
E=ev('xifangye_ningjiang_governor','西方邺获任宁江军节度使',2,'丙寅',None,[('西方邺','宁江军节度使获任者')],when='927年七月丙寅',place='宁江军、夔州',note='西方鄴与西方邺繁简同人，沿已有主体；任命不等兵力增援已到。')
claim('event',E,'description','旧明宗纪升宁江军后记以邺为节度使。',2,'丙寅，升夔州為寧江軍，以鄴為節度使。','承上夔州刺史西方邺，同一人补证。',source='jiuwudaishi-038-july-reconquest',relation='corroborates')
E=ev('douluge_weishuo_ordered_death','后唐以授高季兴夔忠万三州为罪，赐豆卢革、韦说死',3,'癸酉',None,[('豆卢革','被赐死者'),('韦说','被赐死者')],when='927年七月癸酉据主、新；旧纪壬申',place='豆卢革、韦说各流放地',note='以授州为罪是朝廷所列罪名，未据此认可归罪合理性；授州前事不重复创建，不称两人同在一地。')
claim('event',E,'description','旧明宗纪壬申诏陵州、合州刺史监赐豆卢革、韦说自尽，骨肉放逐便。',3,'是日，詔陵州、合州長流百姓豆盧革、韋說等，宜令逐處刺史監賜自盡，其骨肉並放逐便。','是日承同段壬申，与主、新癸酉异日并存；两个流地未强逐一配人，亲属免限制不推他们同遭处死。',source='jiuwudaishi-038-july-reconquest',relation='conflicts')
claim('event',E,'time_original','新明宗纪记七月癸酉杀豆卢革、韦说。',3,'癸酉，殺豆盧革、韋說。','主新同日，与旧壬申日期并列，暂不自行折公历。',source='xinwudaishi-006-927-opening',relation='corroborates')
E=ev('duanning_exiled_liaozhou','段凝被流放辽州',4,'流段凝','辽州，',[('段凝','被流放者')],place='辽州',note='本段无另具日，不强承癸酉；不当已经到达流地。')
claim('event',E,'time_original','旧明宗纪壬申记逐段凝于辽州。',4,'是日，逐段凝於遼州，劉訓於濮州，溫韜於德州。','旧是日承壬申，为命令纪日；不当抵达日。',source='jiuwudaishi-038-july-reconquest',relation='adds')
E=ev('wentao_exiled_dezhou','温韬被流放德州',4,'温韬','德州，',[('温韬','被流放者')],place='德州',note='未具本日抵达或执行细节，不提前其后死亡。')
claim('event',E,'time_original','旧明宗纪壬申记逐温韬于德州。',4,'是日，逐段凝於遼州，劉訓於濮州，溫韜於德州。','旧是日承壬申，主无具体日；保留流放而不外推赐死。',source='jiuwudaishi-038-july-reconquest',relation='adds')
E=ev('liuxun_exiled_puzhou','刘训被流放濮州',4,'刘训',None,[('刘训','被流放者')],place='濮州',note='此为后续流放，不等六月刺史贬授；不将两次处分合成同一次任命。')
claim('event',E,'time_original','旧明宗纪壬申记逐刘训于濮州。',4,'是日，逐段凝於遼州，劉訓於濮州，溫韜於德州。','旧补命令纪日，未具到流地日。',source='jiuwudaishi-038-july-reconquest',relation='adds')
E=ev('renhuan_requests_retirement_cizhou','任圜请求致仕并居磁州',5,'任圜','磁州，',[('任圜','请致仕居磁州者')],place='后唐朝廷、拟居磁州',note='请求和许可分录；不是五月辞三司或六月罢相的重复任命。')
claim('event',E,'description','旧明宗纪七月甲戌记任圜表请致仕，并到外地寻医。',5,'甲戌，太子少保任圜上表乞致仕，仍於外地尋醫，詔從之。','补请求纪日与寻医理由，旧本句未具磁州；不推现代疾病诊断。',source='jiuwudaishi-038-july-reconquest',relation='adds')
E=ev('renhuan_retirement_permission','朝廷允许任圜致仕居磁州',5,'任圜',None,[('任圜','获准致仕者')],when='927年七月，主未具日；旧纪甲戌请致仕并诏从',place='后唐朝廷',note='许可不等在许可当日已抵磁州。')
claim('event',E,'description','旧任圜传记天成二年任圜以太子少保致仕，出居磁州。',5,'天成二年，除太子少保致仕，出居磁州。','补官衔和后来实际居地，传本句未具到日；其后被杀属于待录十月段，不提前写入事件。',source='jiuwudaishi-067-renhuan-retirement',relation='adds')
E=ev('august_solar_eclipse','史书记八月己卯朔发生日食',6,'八月',None,[],when='927年八月己卯朔',place='观测地未载',note='只录史书日食记载，不补观测点、食分、路径、现代公历换算或政治因果。')
claim('event',E,'description','旧明宗纪同记八月己卯朔日有食之。',6,'八月己卯朔，日有食之。','主旧同干支和月朔，不算现代天文计算核验已完成。',source='jiuwudaishi-038-august-eclipse',relation='corroborates')
review='连续1—6段逐句校核。王晏球据旧恢复本姓记载复用杜晏球，不因改姓重复建人；王归德与旧宋州同主体军州衔并列，旧七月庚戌朔补命令纪日，未补战斗和敌军。夔升宁江与西方节授不同动作，本次不重造上批三州战；西方鄴简体识同人。豆卢革韦说主新癸酉与旧壬申异日并存；授三州罪名标为朝廷说法，旧陵合两流地未强逐人配地，骨肉放逐便不当亲属全杀。段辽、温德、刘濮三流放分录，主未具日不承癸酉，旧壬申为逐令不当抵达，刘流不同六月刺史贬授。任请致仕磁州与许之分录，旧甲戌补请致仕寻医，不诊病；旧传出居磁州补后来实际居地但到日未载，不提前十月死亡。日食主旧己卯朔，未自行定位、折公历或补食分路径因果。原字引用、简体展示，纸本及异日待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,7):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=927,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,7)],next_paragraph='zztj-v276-y0927-p007',next_volume=276,next_year=927,supplements=supplements,excluded_non_body=[],coverage='卷276连续1—6段、原文件6—11行；任官、宁江建置、赐死、流放、致仕与日食。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(1,7)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
