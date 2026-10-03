# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 926, paragraphs 1–6."""
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
 ('jiuwudaishi-038-name-change',P/'sources/library/jiuwudaishi-038-name-change','d50fed5c','薛居正等'),
 ('jiuwudaishi-038-january-offices',P/'sources/library/jiuwudaishi-038-january-offices','d50fed5c','薛居正等'),
 ('xinwudaishi-006-927-opening',P/'sources/library/xinwudaishi-006-927-opening','d50fed5c','欧阳修'),
 ('xinwudaishi-028-chancellor-dispute',P/'sources/library/xinwudaishi-028-chancellor-dispute','d50fed5c','欧阳修'),
 ('tongjian-275-926-yearend-and-927-opening',YEAR.parent/'year-0926/part-08/sources/library/tongjian-275-926-yearend-and-927-opening','d0d4d8bd','司马光等'),
 ('xinwudaishi-064-926-monitor',YEAR.parent/'year-0926/part-08/sources/library/xinwudaishi-064-926-monitor','d0d4d8bd','欧阳修'),
 ('jiuwudaishi-136-liyan-monitor',YEAR.parent/'year-0926/part-08/sources/library/jiuwudaishi-136-liyan-monitor','d0d4d8bd','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-275-926-yearend-and-927-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0927-p001-p006',
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
        citation = f'卷275·天成二年（927）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_275_0927_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','知祥':'孟知祥','严':'李严','硃弘昭':'朱弘昭','弘照':'朱弘昭','延禀':'王延禀','延钧':'王延钧'}
NEW_ALIASES={'李绍文':['李紹文'],'李敬周':[],'丁知俊':[],'杨令芝':['楊令芝'],'李同':[],'王彦铢':['王彥銖']}
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
E=ev('mingzong_changes_name_dan','李嗣源更名亶',1,'春，',None,[('帝','更名者')],when='927年正月癸丑朔',place='后唐朝廷',note='帝为明宗李嗣源；更名不新增另一个李亶主体。')
claim('person',people['李嗣源'],'aliases','明宗李嗣源于天成二年正月更名亶，李亶是同一人的更名。',1,Q[1]['text'],'沿用已有稳定主体，不新增同人。')
claim('event',E,'description','旧明宗纪记正月癸丑朔在明堂殿受朝贺，仗卫如常仪。',1,'天成二年春正月癸丑朔，帝御明堂殿受朝賀，仗衛如常儀。','同日仪式补证，改名文本另见同段；不将仪式视另一帝。',source='jiuwudaishi-038-name-change')
claim('event',E,'description','旧明宗纪所载制书称今改名为亶，宣制后百官称贺、告郊庙社稷。',1,'今改名為亶，凡在中外，宜體朕懷。」宣製訖，百僚稱賀，有司告郊廟社稷。','保留制书原字，未凭诏内修辞外推真实天下统一。',source='jiuwudaishi-038-name-change',relation='corroborates')
claim('event',E,'time_original','新明宗纪亦记二年正月癸丑朔更名亶。',1,'二年春正月癸丑朔，更名亶。','主旧新纪日相合。',source='xinwudaishi-006-927-opening',relation='corroborates')
E=ev('meng_prepares_monitor_reception','孟知祥闻李严将来监军，拒绝奏请阻止的建议，派吏到绵剑迎候',2,'孟知祥闻','迎候。',[('知祥','迎候安排者'),('严','将来监军者')],place='西川、绵州与剑州',note='吾有以待之为意向；此时不提前写已诛李严。')
claim('event',E,'description','新蜀世家称掌书记毋昭裔及诸将吏请阻李严入境，孟知祥说将有所待。',2,'掌書記毋昭裔及諸將吏皆請止嚴而無內，知祥曰：「吾將有以待其來！」','补请止者身份，不凭本句造毋昭裔发出实际拒关命令。',source='xinwudaishi-064-926-monitor',relation='adds')
E=ev('lishaowen_dies','武信节度使李绍文去世',2,'会武信','李绍文卒，',[('李绍文','武信节度使、去世者')],place='武信军',note='会为本段时序，未具死亡干支，不将后面壬戌当死亡日。')
claim('person',people['李绍文'],'death_year','武信节度使李绍文于927年本段去世。',2,'会武信节度使李绍文卒，','本书纪时，确日与死因未载。')
E=ev('meng_assigns_lijingzhou_suizhou','孟知祥先任李敬周为遂州留后并催赴任，然后上表',2,'知祥自言','然后表闻。',[('知祥','地方先任后奏者'),('李敬周','西川节度副使、内外马步军都指挥使、遂州留后')],when='927年正月壬戌',place='成都至遂州',note='密诏许便宜是孟自言，未见原诏，不作独立证实；此为地方任命，后续三月朝廷任命尚待连续录入。')
E=ev('meng_shows_armor_to_liyan_envoy','李严先遣使至成都，孟知祥向使者陈甲兵，期望李严惧而退回',2,'严先遣使',None,[('严','遣使者'),('知祥','向使者陈兵者')],place='成都',note='旧恩无具体内容，不建恩师亲缘边；不以为意表示未达恫吓目的，不当李严已入城。')
claim('event',E,'description','新蜀世家亦记李严境上遣书使，孟盛兵见使，李严闻后自若。',2,'嚴至境上，遣人持書候知祥，知祥盛兵見之，冀嚴懼而不來，嚴聞之自若。','与主同事，遣使不另造有名使臣。',source='xinwudaishi-064-926-monitor',relation='corroborates')
E=ev('anzhonghui_heeds_kongxun','安重诲认为孔循熟悉宫廷旧事与朝士才能，多听其言',3,'安重诲以','多听其言。',[('安重诲','采纳意见者'),('孔循','少侍宫禁、意见提供者')],year=None,when='927年正月置相议事所述背景，开始时间未载',place='后唐朝廷',note='安的判断非独立人才评鉴；不新增无明示期限的统属边。')
E=ev('kongxun_recommends_cuixie','孔循在豆卢革韦说获罪后的置相议中荐崔协，任圜主张李琪',3,'豆卢革','任圜欲用御史大夫李琪；',[('孔循','此前荐郑珏、此荐崔协'),('崔协','太常卿、被荐者'),('任圜','主张李琪者'),('李琪','御史大夫、被荐者')],year=None,when='豆卢革韦说获罪之后至927年正月任相前的议事，起日未载',place='后唐朝廷',note='先已荐郑珏为前事，不另造郑珏当日新拜相；主朝延疑朝廷保留原字。')
E=ev('kongxun_obstructs_liqi','郑珏素恶李琪，孔循向安重诲批评李琪不廉，力荐崔协',3,'郑珏素恶','足以仪刑多士矣。”',[('郑珏','史叙称素恶李琪者'),('孔循','阻荐李琪者'),('安重诲','听取意见者'),('李琪','被批评者')],year=None,when='927年正月任相前议事，确日未载',place='后唐朝廷',note='不廉为孔循评价，不作李琪已核犯罪；素恶不推明确起日的敌对关系。')
E=ev('renhuan_challenges_cuixie_emperor_suggests_fengdao','安重诲荐崔协，任圜当面反对；李嗣源认为冯道可以任相',3,'它日议于上前','此可相矣。”',[('帝','主持议相、提冯道'),('安重诲','向帝荐崔协'),('任圜','反对增任崔协'),('崔协','被质疑才学者'),('冯道','帝称冯书记、拟荐者')],year=None,when='927年正月任相前它日议事，确日未载',place='后唐朝廷',note='任圜识字甚少与帝多才博学均为说话者评价；不改写为现代识字测验结果。')
claim('event',E,'description','新任圜传在同次议相叙述中还记明宗提到易州刺史韦肃，继而提冯书记即冯道。',3,'然吾在藩時，識易州刺史韋肅，世言肅名家子，且待我甚厚，置之此位可乎？肅或未可，則馮書記先朝判官，稱為長者，可以相矣！」馮書記者，道也。','补候选韦肃，仅是提议未获任；新以秋起叙，整体跨年前议至本年，不将所有对话强定癸亥。',source='xinwudaishi-028-chancellor-dispute')
E=ev('kongxun_leaves_refuses_court','孔循不揖而去，言任圜专断并坚持崔协任相，随后称疾不朝数日',3,'既退','方入。',[('孔循','离席、称疾不朝后返朝者'),('帝','遣安重诲谕者'),('安重诲','传谕者')],year=None,when='议相之后、癸亥任相之前数日',place='后唐朝廷',note='崔协暴死则已是激语假设，不写成崔协本年死亡；称疾不确定实际患病。')
E=ev('renhuan_rejects_cuixie_temporary_seat','安重诲私议让崔协暂备相位，任圜以苏合丸与蛣蜣比喻反对',3,'重诲私谓圜','取蛣蜣之转也。”',[('安重诲','私议暂备员者'),('任圜','反对者')],year=None,when='927年正月任相前私议，确日未载',place='后唐朝廷',note='比喻为原话而非独立事实物品交换。')
E=ev('kong_an_promote_cuixie_fengdao_appointed','孔循安重诲持续誉崔协短李琪，冯道崔协同日拜相',3,'循与重诲','同平章事。',[('孔循','支持崔协、贬抑李琪'),('安重诲','支持崔协者'),('冯道','端明殿学士、拜相者'),('崔协','拜相者'),('帝','朝廷任命所归者')],when='927年正月癸亥',place='后唐朝廷',note='主中书议郎疑侍郎；旧新均中书侍郎，保留原字并列，不造两任。')
claim('event',E,'description','旧明宗纪癸亥授冯道中书侍郎、平章事、集贤殿大学士，崔协中书侍郎、平章事。',3,'以端明殿學士、尚書兵部侍郎馮道為中書侍郎、平章事、集賢殿大學士；以太常卿崔協為中書侍郎、平章事。','补冯职及学士兼衔；主议郎与旧侍郎用字差异待校。',source='jiuwudaishi-038-january-offices',relation='conflicts')
claim('event',E,'time_original','新明宗纪亦记癸亥冯道崔协拜相，官名中书侍郎。',3,'癸亥，端明殿學士兵部侍郎馮道、太常卿崔協為中書侍郎：同中書門下平章事。','同日，原冒号保留；不自动改底本。',source='xinwudaishi-006-927-opening',relation='corroborates')
claim('person',people['崔协'],'description','主书称崔协为邠之曾孙。',3,'协，邠之曾孙也。','曾孙身份保留，不填无证父祖名；此句只称邠，暂不新建姓氏未经回查的祖先主体。')
E=ev('yanbing_returns_jianzhou_warns_yanjun','王延禀返建州，王延钧相送；延禀以守先人基业警告，延钧逊谢而色变',4,'戊辰',None,[('延禀','返建州、警告者'),('延钧','送行、逊谢者')],when='927年正月戊辰',place='闽、福州至建州',note='老兄口称不单独确定养兄长幼或新造亲生兄弟边；勿烦再下为警告，不当已发动第二次战役。')
E=ev('ten_day_personal_prisoner_review','后唐初令天下长吏每旬亲自引问审查在押囚犯',5,'庚午',None,[('帝','敕令所归明宗')],when='927年正月庚午',place='天下州府',note='引虑为审查囚情，不误作每旬释放所有囚犯。')
claim('event',E,'description','旧明宗纪记左拾遗李同建议长吏每旬亲自引问系囚、核真虚再依法论处，获准。',5,'左拾遺李同上言：「天下係囚，請委長吏逐旬親自引問，質其罪狀真虛，然後論之以法，庶無枉濫。」從之。','补倡议者及目的；旧前记戊辰而主庚午，此建议日与颁令日不强视同日，保留时序。',source='jiuwudaishi-038-january-offices')
person('李同',5,'左拾遗、请逐旬亲问囚者','左拾遺李同上言：「天下係囚，請委長吏逐旬親自引問，質其罪狀真虛，然後論之以法，庶無枉濫。」從之。',source='jiuwudaishi-038-january-offices')
E=ev('meng_hosts_liyan_accuses_monitor','孟知祥厚礼李严，召见时责其昔日请兵伐蜀及独监西川',6,'孟知祥礼遇','何也？”',[('知祥','接待并质问者'),('严','监军、被质问者')],place='成都',note='两国俱亡为孟责语，不能据此认李严一人导致所有亡国；遂朝次月异记另列。')
E=ev('meng_executes_liyan','李严求哀，孟知祥以众怒不可遏为由将其斩杀',6,'严惶怖','斩之。',[('严','求哀、被斩者'),('知祥','处斩命令者')],place='成都',note='本段位于正月，斩日未载；只说明动作及说辞，不将众怒当独立民意调查。')
claim('person',people['李严'],'death_year','李严于927年在成都被孟知祥斩杀。',6,span(6,'孟知祥礼遇','斩之。'),'确年跨书相合，月份主正月/新纪二月/新世家正月分存。')
claim('event',E,'time_original','新明宗纪在二月壬午朔之后记孟知祥杀兵马都监李严，与主书正月段落有月异。',6,'二月壬午朔，新羅使張芬來。西川節度使孟知祥殺其兵馬都監李嚴。','未把壬午朔前事新罗来使日期直接当杀严确日。',source='xinwudaishi-006-927-opening',relation='conflicts')
claim('event',E,'description','新蜀世家称正月李严到成都出诏欲诛焦彦宾，孟知祥不听，命王彦铢执严下斩。',6,'天成二年正月，嚴至成都，知祥置酒召嚴。是時，焦彥賓雖罷，猶在蜀，嚴於懷中出詔示知祥以誅彥賓，知祥不聽，因責嚴曰：「今諸方鎮已罷監軍，公何得來此？」目客將王彥銖執嚴下，斬之。','补出诏及执者，新纪世家自己有月份差异；不当焦彦宾已被诛。',source='xinwudaishi-064-926-monitor')
person('王彦铢',6,'客将、奉孟示意执李严下斩者','目客將王彥銖執嚴下，斬之。',source='xinwudaishi-064-926-monitor')
claim('event',E,'description','旧僭伪列传亦记李严到蜀受厚接，孟知祥遣人拽下阶、斩于阶前。',6,'即遣人拽下階，斬於階前。','旧列传前句案疑舛误且辑存有缺，本动作可补地点层级，不把所引专书新增独立source。',source='jiuwudaishi-136-liyan-monitor',relation='corroborates')
E=ev('dingzhijun_ordered_bury_liyan','孟知祥召丁知俊，令其为昔日同使李严瘗尸',6,'又召','为我瘗之。”',[('知祥','命瘗者'),('丁知俊','左厢马步都虞候、受命者'),('严','被埋遗体所属')],place='成都',note='受命瘗之不直接证明已完成安葬；主丁曾为副使可识同职人物，不建泛故人关系边。')
E=ev('meng_submits_accusatory_report','孟知祥奏称李严诈宣口敕欲代己赴阙并擅许优赏，史书称该奏诬奏',6,'因诬奏','臣辄已诛之。”',[('知祥','上奏者'),('严','被奏指控者')],place='成都上奏后唐朝廷',note='诬奏为作者定性，报告内容为指控，不写李严确有诈诏。')
E=ev('yanglingzhi_flees_lutou','内八作使杨令芝入蜀至鹿头关，闻李严死而奔还',6,'内八作使','奔还。',[('杨令芝','入蜀闻死返回者')],place='鹿头关',note='所办事未载，奔还不补确抵洛阳日。')
E=ev('zhuhongzhao_escapes_east_shu','朱弘昭在东川闻李严死而惧，董璋派其入奏，弘昭伪辞后离蜀得免',6,'硃弘昭',None,[('硃弘昭','闻讯惧、借奏事离蜀者'),('董璋','遣其入奏者')],place='东川至后唐朝廷方向',note='硃弘昭/弘照据同段同职同动作识朱弘昭，弘照疑昭原字保留；得免不等董璋已决定杀他。')
# Supplement actors attach to the already identified same event, rather than duplicating it.
for name,code,n,role,quote,source in [
 ('李同','ten_day_personal_prisoner_review',5,'左拾遗、提出逐旬亲问囚情获准者','左拾遺李同上言：「天下係囚，請委長吏逐旬親自引問，質其罪狀真虛，然後論之以法，庶無枉濫。」從之。','jiuwudaishi-038-january-offices'),
 ('王彦铢','meng_executes_liyan',6,'客将、奉孟知祥示意执李严下斩者','目客將王彥銖執嚴下，斬之。','xinwudaishi-064-926-monitor')]:
 edge='participation_zztj_275_0927_'+code+'_'+people[name]
 B['person_events'].append(dict(key=edge,person_key=people[name],event_key='event_zztj_275_0927_'+code,role=role,status='draft'))
 claim('person_event',edge,'role',name+'：'+role+'。',n,quote,'其他史书记载的参与者挂接同一主体事件，保留独立出处。',source=source)

review='逐句核对卷275天成二年正月连续1—6段。更名亶复用李嗣源，诏修辞不等真实统一；监军迎候、李绍文卒、孟自言密诏、地方先任李敬周后表、使者陈兵分事。密诏仅自言，李死亡不套后任壬戌。置相背景跨此前，先荐郑珏不新任；素恶/不廉/识字少等均有说话者，未造已核犯罪或无起讫敌对边。议事含推荐、离席称疾、传谕返朝、私议反对与癸亥任命，崔协暴死是假设未死。主中书议郎疑侍郎，旧新同中书侍郎并列；邠曾孙只保留字面不猜父祖链。新任圜传补韦肃提议未任。王延禀警告老兄不足独建长幼关系。引虑是亲问囚情非释放，旧李同建议前接戊辰、主颁令庚午区分不武断同日。孟对李严亡国指责是话语，斩杀实际；主正月/新纪二月/新世家正月存在月异，新纪壬午朔属于来使不强作杀日。新世家焦彦宾诏未执行及王彦铢执严补证独存，旧列传辑存正文有校注不引内专史独立扩源。丁受瘗命不写已葬；诬奏指控非事实；杨至鹿头闻死返，朱硃/弘照疑昭同人但不静默改原文。简体展示，逐字底本引用；纸本及异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,7):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=927,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,7)],next_paragraph='zztj-v275-y0927-p007',next_volume=275,next_year=927,supplements=supplements,excluded_non_body=[],coverage='卷275天成二年连续1—6段，原文件75—80行；改名、蜀监军、议相、闽警告、囚犯复核及李严被杀。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(1,7)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
