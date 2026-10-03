# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 926, paragraphs 55–60."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 68))
specs=[
 ('jiuwudaishi-037-926-luwenjin-arrival',P/'sources/library/jiuwudaishi-037-926-luwenjin-arrival','b987ace4','薛居正等'),
 ('jiuwudaishi-037-926-winter-clothes-and-maozhang',P/'sources/library/jiuwudaishi-037-926-winter-clothes-and-maozhang','b987ace4','薛居正等'),
 ('jiuwudaishi-073-maozhang-bianwei',P/'sources/library/jiuwudaishi-073-maozhang-bianwei','b987ace4','薛居正等'),
 ('jiuwudaishi-090-lichengyue-maozhang',P/'sources/library/jiuwudaishi-090-lichengyue-maozhang','b987ace4','薛居正等'),
 ('jiuwudaishi-097-luwenjin-letter',P/'sources/library/jiuwudaishi-097-luwenjin-letter','b987ace4','薛居正等'),
 ('liaoshi-003-927-deguang-accession',P/'sources/library/liaoshi-003-927-deguang-accession','b987ace4','脱脱等'),
 ('liaoshi-003-927-empress-honors',P/'sources/library/liaoshi-003-927-empress-honors','b987ace4','脱脱等'),
 ('liaoshi-071-xiaowen',P/'sources/library/liaoshi-071-xiaowen','b987ace4','脱脱等'),
 ('liaoshi-074-hanyanhui-earlier-office',P/'sources/library/liaoshi-074-hanyanhui-earlier-office','b987ace4','脱脱等'),
 ('tongjian-275-926-autumn-offices',P/'sources/library/tongjian-275-926-autumn-offices','b987ace4','司马光等'),
 ('tongjian-275-926-deguang-succession',P/'sources/library/tongjian-275-926-deguang-succession','b987ace4','司马光等'),
 ('xinwudaishi-026-maozhang-transfer',P/'sources/library/xinwudaishi-026-maozhang-transfer','b987ace4','欧阳修'),
 ('xinwudaishi-048-luwenjin-return',P/'sources/library/xinwudaishi-048-luwenjin-return','b987ace4','欧阳修'),
 ('xinwudaishi-072-yaokun-return',P/'sources/library/xinwudaishi-072-yaokun-return','b987ace4','欧阳修'),
 ('xinwudaishi-068-yanhan',ROOT/'content/books/zizhi-tongjian/vol-273/year-0925/part-02/sources/library/xinwudaishi-068-yanhan','b76f75cc','欧阳修'),
 ('jiuwudaishi-037-926-chu-offices',YEAR/'part-06/sources/library/jiuwudaishi-037-926-chu-offices','0da9df19','薛居正等'),
 ('jiuwudaishi-137-926-yaokun',YEAR/'part-05/sources/library/jiuwudaishi-137-926-yaokun','f5afcc0c','薛居正等'),
 ('xinwudaishi-072-926-anduanshaojun',YEAR/'part-05/sources/library/xinwudaishi-072-926-anduanshaojun','f5afcc0c','欧阳修'),
 ('xinwudaishi-006-926-may-offices',YEAR/'part-03/sources/library/xinwudaishi-006-926-may-offices','5c38857d','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-275-926-deguang-succession','tongjian-275-926-autumn-offices']
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0926-p055-p060',
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
for n in range(55, 61):
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
        citation = f'卷275·同光四年（926）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_275_0926_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','述律后':'述律平','太后':'述律平','天皇王':'耶律德光','德光':'耶律德光','突欲':'耶律倍','延翰':'王延翰','审知':'王审知','璋':'毛璋','承约':'李承约','李继严':'李继曮','卢文时':'卢文进','文进':'卢文进'}
NEW_ALIASES={'萧温':['蕭温','蕭溫'],'阿思没骨馁':['阿思沒骨餒','没骨馁','沒骨餒'],'边蔚':['邊蔚']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷275同光四年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='926年本段；确日未载', note='', year=926, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_275_0926_' + code
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
        edge = 'participation_zztj_275_0926_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_275_0926_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('shulu_prepares_deguang_choice','述律后到西楼，命德光与突欲骑马立帐前，让酋长执辔择立',55,'契丹述律后','汝曹择可立者执其辔。”',[('述律后','偏爱德光、提出择立者'),('德光','受择立的中子'),('突欲','同在帐前的长子')],when='《通鉴》926年九月条叙契丹继统，未具日；辽正式即位另记927年',place='契丹西楼',note='偏爱和命择为史叙，不把二子皆爱话语当独立真实心理证据；诸奠长疑酋长原字保留。')
E=ev('deguang_installed_tianhuangwang','酋长争执德光辔，述律后以众意为由立其为天皇王',55,'酋长知其意','遂立之为天皇王，',[('述律后','立子及表述众意者'),('德光','被立天皇王者')],when='《通鉴》编于926年九月条；《辽史》记天显二年冬十一月壬戌即帝位',place='契丹西楼据主书',note='保留主编年926而辽正式即位927的不同定位。知后意为作者归因，争执辔是史述拥立，不推有现代投票制度或所有部族一致自愿。')
claim('event',E,'time_original','辽太宗纪记天显二年冬十一月壬戌，人皇王倍请后立皇子大元帅，后从之，当日即皇帝位。',55,'冬十一月壬戌，人皇王倍率羣臣請于后曰：「皇子大元帥勳望，中外攸屬，宜承大統。」后從之。是日即皇帝位。','本段前有天显二年及明年秋标题，年界上下文另存sources/context；与主926纪年及倍失望叙法均不同，不静默统一为926或927。',source='liaoshi-003-927-deguang-accession',relation='conflicts')
claim('event',E,'description','新契丹传也记诸部顺述律之意共立德光。',55,'然述律尤愛德光。德光有智勇，素已服其諸部，安端已去，而諸部希述律意，共立德光。','补同类拥立叙法，未给精确年日不能充当辽即位纪年相同的确证；不扩录前批安端身份。',source='xinwudaishi-072-926-anduanshaojun',relation='corroborates')
E=ev('bei_attempts_tang_stopped_return_dongdan','突欲率数百骑欲奔唐，被巡逻者阻止；述律后不罪，遣回东丹',55,'突欲愠','遣归东丹。',[('突欲','未遂奔唐并回东丹者'),('述律后','不加罪、遣返者')],when='《通鉴》926年契丹继位叙事之后，具体日未载',place='西楼附近及东丹',note='欲奔而被遏是未遂，不能与930年实际渡海奔唐合为同一次成功行动；不造未名巡逻者人物，数百不是精确百人。')
E=ev('deguang_honors_shulu_dominates_affairs','德光尊述律后为太后，史书称国事皆由太后决定',55,'天皇王尊','国事皆决焉。',[('天皇王','尊母者'),('太后','被尊、书载决国事者')],when='《通鉴》926年继统后；辽记天显二年十二月庚辰尊号',place='契丹朝廷',note='国事皆决是主概括权力叙述，不把每项未见政令补成太后所发；辽尊号阶段与主有年差。')
claim('event',E,'time_original','辽太宗纪天显二年十二月庚辰记皇后尊应天皇太后。',55,'十二月庚辰，尊皇太后為太皇太后，皇后為應天皇太后，立妃蕭氏為皇后。','原两代母后称号区别，不把太皇太后也当述律平；同卷前天显二年上下文已导出。',source='liaoshi-003-927-empress-honors',relation='conflicts')
relationship('述律后','德光','母亲',55,'契丹述律后爱中子德光，','述律平是德光母亲，原中子明确，未凭外貌或统属猜亲属。')
E=ev('shulu_niece_empress_xiaowen','述律后纳其侄辈女子为天皇王后，辽史对应靖安皇后萧温',55,'太后复纳','为天皇王后。',[('太后','主书所述安排立后者'),('天皇王','皇后配偶'),('萧温','辽本传明确身份的皇后')],when='《通鉴》926年继统后叙；辽帝纪天显二年十二月庚辰立妃萧氏后',place='契丹朝廷',note='主未具侄名，辽本传温为淳钦后弟室鲁女及同太宗配偶定位。主纳后与辽早年纳妃、即位立后是不同阶段，不强填某日已首次成婚。')
claim('person',people['萧温'],'description','辽后妃传称太宗靖安皇后萧氏、小字温，为淳钦皇后弟室鲁之女。',55,'太宗靖安皇后蕭氏，小字温，淳欽皇后弟室魯之女。','同太宗皇后及述律侄辈配偶校主未名侄身份；温/溫展示统一，未另造两人，纸本未核。',source='liaoshi-071-xiaowen',relation='adds')
claim('event',E,'description','辽萧氏传记德光为大元帅时纳她为妃，即位后才立为皇后。',55,'帝爲大元帥，納爲妃，生穆宗。及即位，立爲皇后。','只补成妃和立后的先后，穆宗出生非本批主线不另建出生事件或任帝关系；不把后段935死亡提前到926。',source='liaoshi-071-xiaowen',relation='adds')
relationship('萧温','天皇王','妻子',55,'太后复纳其侄为天皇王后。','萧温是德光妻子，同配偶身份由辽本传补明；仅一条妻子边，不反向另造丈夫。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','辽后妃传记太宗纳萧氏为妃，及即位立为皇后。',55,'帝爲大元帥，納爲妃，生穆宗。及即位，立爲皇后。','正式婚与册后时间区别，关系不硬填926首次建立。',source='liaoshi-071-xiaowen',relation='corroborates')
relationship('述律后','萧温','姑母',55,'太后复纳其侄为天皇王后。','主侄含侄辈、辽明确弟室鲁之女，述律是其姑母而非生母，不造同代母女。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','辽史称萧温是淳钦皇后弟室鲁之女，故述律是其姑母。',55,'淳欽皇后弟室魯之女。','关系由明示弟女导出，与主侄印证；未在本批扩建未出现于主线的室鲁主体或祖辈谱系。',source='liaoshi-071-xiaowen',relation='adds')
E=ev('deguang_obedience_to_mother_portrayed','史书描写德光侍母：母不食亦不食，遇母不悦即退避、非召不见',55,'天皇王性孝谨','非复召不敢见也。',[('天皇王','被描写孝谨及退避者'),('太后','德光所侍之母')],year=None,when='《通鉴》契丹继位段的人物行为概述，各次发生日期未载',place='契丹宫帐',note='性孝谨和惧为史人物评价；母病、不食、不称旨是概括场景，不造一个精确日期的疾病事件或诊断。')
E=ev('hanyanhui_zhengshiling_in_succession_narrative','《通鉴》在契丹继位叙事中记以韩延徽为政事令',55,'以韩延徽','为政事令。',[('韩延徽','受任政事令者'),('天皇王','本段国主、任官所归者')],when='《通鉴》926年继统条；辽本传另记太祖时期已有此职',place='契丹朝廷',note='该职非因此可认首次创置或韩首次任相；太祖时期先任记录另引，主本段任命是否复任待核。')
claim('event',E,'description','辽韩传记他返回太祖处后已受任守政事令、崇文馆大学士。',55,'即命為守政事令、崇文館大學士，中外事悉令參決。','辽本传句主是此前太祖、时间未具，不移到德光任官确日；前职与本段书述任官并存，未自造罢复任环节。',source='liaoshi-074-hanyanhui-earlier-office',relation='adds')
E=ev('yaokun_allowed_return_report','契丹准姚坤归唐复命',55,'听姚坤','归复命，',[('姚坤','获准归国复命使者'),('天皇王','主本段准归所归国主')],when='《通鉴》926年继统条；旧新另叙随述律后护丧回西楼后返回',place='契丹西楼至后唐',note='听归为准许，不具抵达洛阳日；此前拘禁未遂杀与本事分开，书间与德光立先后不同。')
claim('event',E,'description','旧契丹传记姚坤随述律护丧归西楼，得报而还，其后才叙德光为渠帅。',55,'其妻舒嚕氏自率眾護其喪歸西樓，坤亦從行，得報而還。既而舒嚕氏立其次子德光為渠帥，','旧先后与主继位后听归不同，不把现有时序自动视同；舒嚕字形是既有述律名译，不造新人。',source='jiuwudaishi-137-926-yaokun',relation='conflicts')
claim('event',E,'description','新契丹传记述律护丧归西楼、立元帅太子，姚坤从至西楼而还。',55,'述律護其喪歸西樓，立其次子元帥太子耀屈之。坤從至西樓而還。','耀屈之为此传名译，不凭新音译新建人物，未写姚坤已经提前被杀。',source='xinwudaishi-072-yaokun-return',relation='corroborates')
E=ev('asimogunei_sent_mourning_envoy','契丹遣阿思没骨馁向后唐告阿保机之哀',55,'遣其臣',None,[('阿思没骨馁','契丹告哀使者'),('天皇王','本段遣使所归国主')],when='《通鉴》926年继统条；新明宗纪十月辛丑记没骨馁来告哀',place='契丹至后唐',note='派遣与到唐日期不同，姓名短译与全译由同告阿保机哀、同年校；不是新派姚坤二次使团。')
claim('person',people['阿思没骨馁'],'description','新明宗纪称契丹使没骨馁来告阿保机哀。',55,'辛丑，契丹使沒骨餒來告阿保機哀，廢朝三日。','同年度同告哀校短译没骨馁与全名同人；废朝为新所记礼仪，不生成其个人死亡。',source='xinwudaishi-006-926-may-offices',relation='adds')
claim('event',E,'time_original','旧明宗纪记十月辛丑契丹来告国主七月二十七日卒。',55,'辛丑，契丹遣使來告哀，言國主安巴堅以今年七月二十七日卒。','七月二十七为被报死亡日，十月辛丑为到朝告哀日，不混为阿保机十月才去世；安巴坚译名沿既有阿保机身份。',source='jiuwudaishi-037-926-luwenjin-arrival',relation='adds')
E=ev('lijiyan_renamed_congyan','李嗣源赐李继曮名李从曮',56,'壬午',None,[('帝','赐名者'),('李继严','获赐名的凤翔节度使')],when='926年九月壬午据主书；旧明宗纪作辛巳',place='后唐朝廷及凤翔',note='主李继拆字及从拆字沿既有李继曮/李从曮同凤翔主体校，不与客省使李严混一人。原私用字快照留存不重写。')
claim('person',people['李继曮'],'aliases','主书记李继拆字获赐从拆字名，沿既有规范名李继曮及李从曮。',56,'赐李继严名从严。','本段赐名延续旧主体，未新建李从严人物；拆字不靠繁简映射自动猜人。')
claim('event',E,'description','旧明宗纪辛巳诏凤翔节度使李严于本名上加从字。',56,'詔曰：「鳳翔節度使李嚴，世聯宗屬，任重藩宣，慶善有稱，忠勤顯著。既在維城之列，宜新定體之文。是降寵光，以隆惇敘，俾煥成家之美，貴崇猶子之親。宜於本名上加『從』字。」','旧李严是凤翔任者，区别同名客省使；旧辛巳/主壬午日期不合，原漏拆字等异文待纸本核。制书猶子之亲为宗属用语，不据此新建实际收养父子。',source='jiuwudaishi-037-926-chu-offices',relation='conflicts')
E=ev('court_spring_winter_clothes_extended','后唐开始向文武官赐春冬衣',57,'冬，十月',None,[('帝','赐衣制度发令者')],when='926年十月甲申朔',place='后唐朝廷',note='初在本文指本次普及制度，旧证明此前近臣已得冬服，不能写此前所有官员从未获赐衣。')
claim('event',E,'description','旧明宗纪记甲申朔赐百僚冬服绵帛，李嗣源问任圜后将近臣例推及外臣。',57,'冬十月甲申朔，詔賜文武百僚冬服綿帛有差。','旧先冬服、本主概括春冬，并非同日发两季全额实物都经核实。',source='jiuwudaishi-037-926-winter-clothes-and-maozhang',relation='adds')
claim('event',E,'description','旧纪记任圜与安重诲据品秩差等定春冬赐例，后来成为常例。',57,'圜遂與安重誨據品秩之差，以定春冬之賜，其後遂以為常。','补制度参与及分品秩，主不名二人只在事实引用补，不扩本批前后无关官仪；其后非本日一次事件。',source='jiuwudaishi-037-926-winter-clothes-and-maozhang',relation='adds')
E=ev('wangyanhan_claims_great_min_king','王延翰自称大闽国王',58,'昭武节度使','自称大闽国王。',[('延翰','自称大闽国王者')],when='926年十月己丑',place='闽、福州',note='主昭武节度疑威武，既有威武任职另证，原军名留而不新建昭武同名人物。骄淫残暴为史评价，不等同一项具体司法裁判；自称不等后唐已册此王号。')
claim('event',E,'description','新闽世家记十月王延翰建国称王，但仍用唐正朔。',58,'十月，延翰建國稱王，而猶稟唐正朔。','补仍奉唐历，不把称王断定已另改年号或完全断绝唐关系；新未具己丑不能强独立确日。',source='xinwudaishi-068-yanhan',relation='adds')
E=ev('min_palaces_and_offices_imperial_model','王延翰建宫殿置百官，仪物仿天子、群下称殿下',58,'立宫殿','曰殿下。',[('延翰','设置官制宫殿及受称者')],when='926年十月称王条，各项完成确日未载',place='闽国、福州',note='主概括制度仿天子，不补宫殿形制坐标或已造完所有工程的独立时间；百官是官员群体，不当精确一百人。')
E=ev('min_yanhan_amnesty','王延翰赦境内',58,'赦境内','赦境内，',[('延翰','赦令发布者')],when='926年十月称王条，赦日未单列',place='闽境内',note='赦范围主只境内，未具全部刑种免除，不写所有罪都免且全部已释放。')
E=ev('wangshenzhi_posthumously_zhaowu_king','王延翰追尊其父王审知为昭武王',58,'追尊其父',None,[('延翰','追尊者'),('审知','获追尊的已故父亲')],when='926年十月称王条',place='闽国',note='追尊不是王审知本年生前新掌王位；既有925卒已录，不改为926卒。')
relationship('审知','延翰','父亲',58,'追尊其父审知曰昭武王。','复用已有王审知父亲→王延翰关系和key，不再新建反向或重复边。')
E=ev('maozhang_train_arm_ambition_report','史书记毛璋骄僭不法，训练士卒、修整兵器，有跋扈之志',59,'静难节度使毛璋','有跋扈之志，',[('璋','被记训卒缮兵及有异志者')],year=None,when='926年十月调任条前背景，具体发生年月未载',place='静难军据主书',note='有志是史作者动机判断，不当已经发兵叛乱；概述无确起点，不直接填本月开始。')
claim('event',E,'description','旧毛传亦记招致部下、缮理兵仗，并以骄僭不法评价之。',59,'璋既家富於財，有蜀之妓樂，驕僭自大，動多不法，招致部下，繕理兵仗。','独立本传补行为与评价，后段罪狱死亡非本批不提前展开。',source='jiuwudaishi-073-maozhang-bianwei',relation='corroborates')
E=ev('lichengyue_assigned_watch_maozhang','李嗣源命颍州团练使李承约为节度副使，以察毛璋',59,'诏以颍州','以察之。',[('帝','派察命令者'),('承约','受命节度副使'),('璋','受察的节度使')],when='926年十月毛璋移任前，副使任命日未载',place='静难军据主书；旧李传称泾州副使',note='主未再列副使所属州，结合毛静难节度主句定位但旧泾州有差，保留不同说法，不伪造官告原称。')
claim('event',E,'description','旧李承约传称他被命为泾州节度副使，承密旨往偵毛璋。',59,'天成中，以邠州節度使毛璋將圖不軌，乃命為涇州節度副使，且承密旨往偵之。','旧邠州毛与泾州副使名称不完全一致，留异；天成中无独立本年确日，不默认临时转两镇。',source='jiuwudaishi-090-lichengyue-maozhang',relation='adds')
E=ev('maozhang_transfer_zhaoyi','朝廷徙毛璋为昭义节度使',59,'壬辰','为昭义节度使。',[('帝','移任发令者'),('璋','移任昭义者')],when='926年十月壬辰',place='静难邠州至昭义潞州',note='先调任，再拒命意向，再说谕受代，不把同段动作均视壬辰当天已完成。')
claim('event',E,'description','旧明宗纪壬辰记邠州节度使毛璋移镇潞州。',59,'壬辰，邠州節度使毛璋移鎮潞州。','军名与州名配对可证同一调任，与主壬辰一致；新毛传称从华州移昭义另存而不合成先后两次任命。',source='jiuwudaishi-037-926-winter-clothes-and-maozhang',relation='corroborates')
claim('event',E,'description','新毛传概叙从华州移镇昭义，初欲拒命。',59,'在鎮多不法，議者疑其有異志，乃徙璋鎮昭義。璋初欲拒命，其判官邊蔚切諫諭之，乃聽命。','新此句接华州任职，与主静难及旧纪邠州出发镇不同；同毛同昭义同边蔚拒命说谕校同事留异，不造未经证实第二次同昭义调任。',source='xinwudaishi-026-maozhang-transfer',relation='conflicts')
E=ev('lichengyue_bianwei_persuade_maozhang','毛璋欲拒诏，李承约与边蔚说谕，过后毛璋才肯受代',59,'璋欲不奉诏',None,[('璋','欲拒诏后受代者'),('承约','说谕者'),('边蔚','长安人、观察判官、说谕者')],when='926年十月壬辰调任后久之，接受确日未载',place='毛璋旧镇',note='未奉诏意图不等已正式举兵叛国，久之不可硬填壬辰当日；边蔚不并边光范或边归谠等不同人。')
claim('event',E,'description','旧毛传称判官边蔚密言规责，毛璋勉强承命。',59,'璋謀欲不奉詔，判官邊蔚密言規責，乃僶勉承命。','同职同事补识别边蔚，未将僶勉简化成主动自愿。',source='jiuwudaishi-073-maozhang-bianwei',relation='corroborates')
claim('event',E,'description','旧李承约传称承约善言谕毛璋，毛璋乃受代。',59,'既至，以善言諭之，璋乃受代。','独立李传补其参与，与毛传单记边并存，不要求另一书必须列全共同参与者才识别同事。',source='jiuwudaishi-090-lichengyue-maozhang',relation='corroborates')
E=ev('youzhou_reports_luwenjin_arrival','幽州奏卢文进从契丹来奔',60,'庚子','来奔。',[('文进','来奔的契丹所署卢龙节度使')],when='926年十月庚子奏报；旧本传另有明宗即位之明年叙法',place='幽州及后唐朝廷',note='主开头卢文时与同段文进及旧同职同来奔校同一人，卢文时疑字原文留，不另建卢文时。奏报不是直接断他在本日才出平州。')
claim('event',E,'description','旧明宗纪庚子记契丹平州守将、所署幽州节度使卢文进率户口归顺。',60,'庚子，幽州奏，契丹平州守將偽署幽州節度使盧文進，率戶口歸順，百僚稱賀。','纪与主同日同地同职，卢文时/进据完整同事识别；伪署为旧作者政治评价，不把所有归附者写成现役战兵。',source='jiuwudaishi-037-926-luwenjin-arrival',relation='corroborates')
E=ev('siyuan_sends_secret_envoy_to_luwenjin','追叙卢文进为契丹守平州，李嗣源即位后派间使劝其归附',60,'初，文进','无复嫌怨。',[('文进','契丹平州守将、被招劝者'),('帝','遣间使招劝者')],when='926年李嗣源即位后至十月来奔前，间使出发日未载',place='后唐至平州',note='以易代无嫌怨是招劝说辞，不认过往矛盾已完全解除；未名间使不造具体使者。')
E=ev('lu_kills_pingzhou_khitan_guards','卢文进杀在平州的契丹戍守者',60,'文进所部','契丹戍平州者，',[('文进','率部杀契丹戍者')],when='926年十月归附前；旧本传上表自称十月十日决计杀守城契丹',place='平州',note='所部思归是书述共同心理，不当现代全部人口调查；敌戍人数与是否全族未具，未造精确杀敌数。')
claim('event',E,'time_original','旧本传引卢文进自述十月十日决计杀城内契丹、十一日离州、十四日到幽州。',60,'臣十月十日，決計殺在城契丹，取十一日離州，押七八千車乘，領十五萬生靈，十四日已達幽州','这是归附奏表自述日期和人数，旧传开篇却作即位之明年，与主及帝纪926相异各留；不认十日决计就是全部处决完成时刻。',source='jiuwudaishi-097-luwenjin-letter',relation='conflicts')
E=ev('lu_leads_population_carts_return','卢文进率其众十余万、车帐八千乘归附后唐',60,'帅其众',None,[('文进','率众归附者')],when='926年十月据主及旧纪；旧传概叙明宗即位之明年',place='平州至幽州',note='众与车帐各单位，十余万不等十余万战斗兵，八千乘不等精确八千辆某单一车型。旧十五万/七八千、新数万各据书保留，不平均。')
claim('event',E,'description','旧卢传概称明宗即位之明年，率十余万众自平州来奔。',60,'及明宗即位之明年，文進自平州率所部十餘萬眾來奔。','传明年字面为927而同书纪及主926，记为日期异说不静默勘掉或另造927第二归附。',source='jiuwudaishi-097-luwenjin-letter',relation='conflicts')
claim('event',E,'description','旧卢传所引上表自称押七八千车、领十五万生灵。',60,'押七八千車乘，領十五萬生靈，','奏表口径与主十余万八千乘不完全相同，生灵包括人口不等十五万军人；自称而非现代实测。',source='jiuwudaishi-097-luwenjin-letter',relation='adds')
claim('event',E,'description','新卢传作明宗即位后自平州率众数万归唐。',60,'明宗即位，文進自平州率眾數萬歸唐，','新数万与主旧十余万不同，未取其中一数覆盖其他书，不扩录主后段才来的义成正式任命。',source='xinwudaishi-048-luwenjin-return',relation='conflicts')
claim('event',E,'description','旧纪丁未奏归附户口、牲畜在平州西首尾约七十里。',60,'丁未，幽州奏，盧文進所率降戶孳畜人口在平州西，首尾約七十里。','长度为报告约数，户口牲畜人口混合队伍，非七十里战阵或精确现代公里，不据此反推人数。',source='jiuwudaishi-037-926-luwenjin-arrival',relation='adds')

review='连续55—60段逐句校核。契丹择执辔拥立主编于926，辽太宗即位天显二年927冬十一月壬戌及后十二月尊母立妃与主日期和倍角色异叙分别保留；已导出辽年界context标题及明年秋，不当同主确年确证。主诸奠长疑酋长原字保留。倍率数百欲奔被遏是未遂，不提前930实际奔唐；述律母德、萧温妻德、述律姑温按主中子侄及辽弟室鲁女具体关系，不猜未名皇后或建生母错误边。辽萧妃大元帅时纳/即位立后与主太后纳侄分阶段，935后死不提前。德孝谨侍母概括无确时置null，非疾病诊断或每次确证。韩政事令主本段任官、辽太祖前任同职并存，不称首次任相或自补罢复官。姚主继位后听归/旧先归后德立/新同西楼后还分先后异说，短译耀屈之同德光身份不另建，没骨馁全短译以同告阿保机哀校同人，十月告哀日与七月死亡日分开。李继拆字沿已有曮/从曮凤翔同人，不并客省李严，主九月壬午/旧辛巳存异、猶子宗属语不造收养边。甲申赐春冬衣结合旧先冬服再品秩常例区分，不说此前所有官从未有衣。王自称大闽国王非后唐册王，新十月建国仍稟唐正朔；主昭武节度疑威武原字留不改档案，宫官仿天子群下殿下非精确百官数，赦范围不外推，父追尊与既有925实卒分开、父边复用。毛训缮志为史心理、李副使主静难/旧泾州与毛邠州名异，主旧壬辰静难邠至昭义潞/新传华州到昭义同边拒命事留异不造两调。李及边共同谕和久之受代不强同壬辰，不提前后狱死。卢文时/同段文进及旧同职同庚子奏校主疑字不新建。间使劝归、杀戍、率人口车帐、幽奏各分动作。所部华人思归为史述群体心理，十余万不是战兵，主八千车帐/旧表七八千车十五万生灵/新数万分别，旧奏十月10决计、11离、14至属自述，旧传明年927/主纪926留异不造第二归附，丁未队伍约七十里不换公里反算人数。简体展示、逐字原文和哈希保留，纸本未核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(55,61):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
contexts=[]
for path in sorted((P/'sources/context').iterdir()):
 record=json.loads((path/'paragraph.json').read_text());contexts.append(dict(paragraph_id=record['id'],file=str((path/'source.txt').relative_to(P/'sources')),sha256=hashlib.sha256((path/'source.txt').read_bytes()).hexdigest(),purpose='辽太宗即位天显二年年界上下文；标题不生成史事实体'))
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(55,61)],next_paragraph=Q[61]['id'],next_volume=275,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷275第55—60段，原文件60—65行；契丹继统与母后皇后使臣、李继曮赐名、百官赐衣、闽王自称及追尊、毛调任受代、卢杀戍归附。926年110正文段累计103，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(55,61)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
