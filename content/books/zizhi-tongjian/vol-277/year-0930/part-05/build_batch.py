# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 930, paragraphs 36–45."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 56))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'f7d30617','薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))
specs.extend([
 ('tongjian-277-930-autumn-winter',YEAR/'part-04/sources/library/tongjian-277-930-autumn-winter','73f70bd8','司马光等'),
 ('jiuwudaishi-041-930-october',YEAR/'part-04/sources/library/jiuwudaishi-041-930-october','73f70bd8','薛居正等'),
 ('xinwudaishi-064-meng-campaign',YEAR/'part-04/sources/library/xinwudaishi-064-meng-campaign','73f70bd8','欧阳修'),
 ('xinwudaishi-062-jing-name',ROOT/'content/books/zizhi-tongjian/vol-272/year-0923/part-09/sources/library/xinwudaishi-062-jing-name','83be3260','欧阳修'),
 ('jiuwudaishi-030-923-zhongdu',ROOT/'content/books/zizhi-tongjian/vol-272/year-0923/part-06/sources/library/jiuwudaishi-030-923-zhongdu','460d5032','薛居正等'),
])

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-930-autumn-winter']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0930-p036-p045',
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
for n in range(36, 46):
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
        citation = f'卷277·长兴元年（930）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_277_0930_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'汉主':'刘岩','承美':'曲美','知祥':'孟知祥','璋':'董璋','仁罕':'李仁罕','鲁奇':'夏鲁奇','镠':'钱镠','传瓘':'钱传瓘','光业':'董光业','殷':'马殷','希声':'马希声','知诰':'李昪','景通':'李璟'}
NEW_ALIASES={'梁克贞':['梁克貞'],'李守鄜':['李守鄘'],'李进（南汉交州将）':['李進（南漢交州將）'],'高敬柔':[],'康文通':[],'裴羽':[],'袁彦超':['袁彥超']}

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

def event(code, title, n, quote, actors, when=None, note='', year=930, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='930年本段；主句未独纪月日' if n==36 else '930年十月本段；确日未独载'
    key = 'event_zztj_277_0930_' + code
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
        edge = 'participation_zztj_277_0930_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_277_0930_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
jiao='xinwudaishi-065-930-jiaozhou';xia='xinwudaishi-033-xialuqi-siege';peinew='xinwudaishi-057-peiyu-return';peiold='jiuwudaishi-128-peiyu-return';feng='jiuwudaishi-041-930-fengyun';quold='jiuwudaishi-135-quchengmei';qushort='jiuwudaishi-006-qumei';october='jiuwudaishi-041-930-october';meng='xinwudaishi-064-meng-campaign';jing='xinwudaishi-062-jing-name';kang='jiuwudaishi-030-923-zhongdu'
E=ev('han_sends_generals_jiaozhou','刘岩遣梁克贞、李守鄜攻交州',36,'汉主遣其将','攻交州，',[('汉主','遣将攻交州者'),('梁克贞','受命攻交州的南汉将'),('李守鄜','受命攻交州的南汉将')],place='南汉、交州',note='未独月日；后段起十月不倒定本句九月。李守鄜与新李守鄘按同役同俘同主识别，非繁简字自动转换。')
claim('person',people['李守鄜'],'description','《新五代史》作李守鄘，同与梁克贞攻交趾、擒曲承美。',36,'遣將李守鄘、梁克貞攻交趾，擒曲承美等。','姓名字异保留；同役同俘者认同主体，展示沿主李守鄜，不改摘录。',source=jiao,relation='conflicts')
claim('event',E,'time_original','《新五代史》系于大有三年（930），未独载月日。',36,'三年，遣將李守鄘、梁克貞攻交趾，擒曲承美等。','承前大有改元，旧南汉传白龙四年改大有元年可校其年；不自行换算月日。',source=jiao,relation='corroborates')
E=ev('han_takes_jiaozhou','南汉军攻拔交州',36,'攻交州，','拔之，',[('梁克贞','攻拔交州将领'),('李守鄜','攻拔交州将领')],place='交州',note='之承交州，交州交趾称法沿各书；不填全境现代坐标或精确边界。')
E=ev('han_captures_quchengmei','南汉军执静海节度使曲承美归南汉',36,'执静海','以归，',[('承美','被执的静海节度使'),('梁克贞','攻交州并执曲者'),('李守鄜','攻交州并执曲者')],place='交州至南汉',note='沿911静海节度使曲美主体；职地及梁授旄旧记、全名曲承美新旧对照，非另建曲承美。归非释放。')
claim('person',people['曲美'],'description','曲美与本段静海节度使曲承美按官地、梁授节及同一地方曲氏承袭身份识别。',36,'安南兩使留後曲美，','既有911主体沿用短名；此句电子本夹注《通鉴》不冒称独立同日实录确证，姓名全短须结合南汉传核。',source=qushort,relation='adds')
claim('person',people['曲美'],'description','旧南汉传称交州曲承美送款于梁，获正式旄钺。',36,'交州土豪曲承美亦專據其地，送款於梁，因正授旄鉞。','补全名及同一梁授节身份；旧传未独纪此事之年，不在930重建任命。',source=quold,relation='adds')
claim('event',E,'description','旧南汉传另称刘陟遣李知顺伐曲承美、执而献。',36,'陟不平之，遣將李知順伐之，執承美以獻，','旧未独纪年、叙在称帝段之前，与主新主将姓名有差；并列异叙，不把李知顺自动等同李守鄜，不据传文先后强定917前发生。',source=quold,relation='conflicts')
E=ev('han_li_jin_garrisons_jiaozhou','刘岩以李进守交州',36,'以其将李进',None,[('汉主','命将守交州者'),('李进（南汉交州将）','南汉守交州将')],place='交州',note='李进加南汉交州将消歧标识，原句未称刺史，不凭未来段提前补正式官衔。')
E=event('han_receives_qu_at_yifeng','曲承美至南海，刘岩登义凤楼受俘',36,'承美至南海，龑登義鳳樓受俘，',[('承美','被献俘者'),('汉主','登义凤楼受俘者')],when='《新五代史》大有三年（930）交州战事后；确日未载',place='南海、义凤楼',source=jiao,note='龑沿既有刘岩异名主体；受俘为补传环节，无坐标。')
E=event('han_pardons_quchengmei','曲承美顿首伏罪，刘岩赦之',36,'承美頓首伏罪，乃赦之。',[('承美','顿首伏罪、获赦者'),('汉主','赦曲者')],when='《新五代史》大有三年（930）受俘时；确日未载',place='南海',source=jiao,note='赦不等同归还静海、释放返交州或继续任官，均未明载。')
relationship('曲颢','承美','父亲',36,'承美，顥子也。','顥按交州曲氏承袭及同书上下文识曲颢；沿既有曲颢、曲美，父亲方向为曲颢→曲美。',source=jiao)
E=ev('lirenhan_besieges_suizhou','李仁罕围遂州',37,'冬，十月，','李仁罕围遂州，',[('仁罕','率军围遂州者')],when='930年十月癸巳',place='遂州')
E=ev('xialuqi_holds_suizhou','夏鲁奇婴城固守遂州',37,'夏鲁奇婴城','夏鲁奇婴城固守；',[('鲁奇','固守遂州者')],place='遂州')
claim('event',E,'description','新夏传记董璋反而攻遂州，夏闭城拒之。',37,'東川董璋反，攻遂州，魯奇閉城拒之，','新概叙董攻，主具围城将李仁罕；不硬推董当日亲至遂州，后粮尽自刎属后文未提前录。',source=xia,relation='corroborates')
E=ev('gaojingrou_builds_siege_wall','孟知祥命高敬柔率资州义军二万人筑长城环遂州',37,'孟知祥命','筑长城环之。',[('知祥','命围城工事者'),('高敬柔','都押牙、率义军筑围城工事者')],place='资州、遂州',note='长城是本役环城围垒，非万里长城；二万为史载义军数，不作为全部正规军统计。')
E=ev('xia_sends_kang_sortie','夏鲁奇遣马军都指挥使康文通出战',37,'鲁奇遣','康文通出战，',[('鲁奇','遣将出战者'),('康文通','马军都指挥使、出战者')],place='遂州')
claim('person',people['康文通'],'description','旧庄宗纪载923年被擒梁将名单中有康文通。',37,'康文通、王山興等將吏二百餘人','同名康文通、由梁入唐军职背景佐核，不混康文爽或宋文通；不把二百余全算康本人兵力或本年被擒。',source=kang,relation='adds')
E=ev('kang_surrenders_lirenhan','康文通闻阆州陷，以其众降李仁罕',37,'文通闻阆州陷，',None,[('康文通','闻阆陷而率众投降者'),('仁罕','受降者')],place='遂州',note='闻为康掌握消息，降未独日，不强同癸巳；众人数未具，不自动沿前义军二万。')
E=ev('dong_moves_lizhou_rain_retreat','董璋引兵趣利州，遇雨且粮运不继，还阆州',38,'戊戌，','还阆州。',[('璋','进利州而遇雨缺粮退阆者')],when='930年十月戊戌',place='利州、阆州',note='趣为赴向利州，不等已夺利州；还保留阆州。')
E=ev('meng_criticizes_dong_retreat','孟知祥闻董璋退阆，批评其远弃剑阁、僻处阆州非计',38,'知祥闻之，','非计也。”',[('知祥','闻报后评军略者'),('璋','被批退守者')],place='阆州、利州、漫天、剑阁',note='利帅必遁、获仓廪、北军不能救是孟对原计划的判断，不建已获粮已夺漫天事件。')
E=ev('meng_proposes_jianmen_reinforcement','孟知祥欲遣兵三千助守剑门',38,'欲遣兵三千','助守剑门；',[('知祥','提出援剑门计划者')],place='剑门',note='欲遣是意图，不改写成三千已出发或抵达。')
E=ev('dong_declines_meng_reinforcement','董璋固辞孟知祥剑门援军，称已有备',38,'璋固辞曰：',None,[('璋','辞援、称有备者'),('知祥','援军建议被辞者')],place='剑门',note='有备是董说法，不替其创建已查证守军规模。')
E=ev('qian_attaches_peiyu_apology','钱镠因册闽王使裴羽归还，附表引咎',39,'钱镠因','附表引咎；',[('镠','附使上表引咎者'),('裴羽','返使携表者')],place='吴越至后唐',note='主使都疑字保留，展示称使者而不据疑字造都使职；返使日期按主本段，不把引咎当每项罪状实证。')
claim('person',people['裴羽'],'description','新裴传记明宗时裴羽为吏部郎中，出使闽地。',39,'唐明宗時，為吏部郎中，與右散騎常侍陸崇使于閩，','同册闽返使身份；引用含陆崇背景，不为本段未名同伴重建实体或重复其已发布死亡。',source=peinew,relation='adds')
claim('event',E,'description','新裴传同记钱镠遣裴羽归还，附表自归。',39,'後鏐遣羽還，羽求載崇尸與俱歸。','新经岁与后返为传叙，载陆丧可佐返程背景，不强定全程各事930确日。',source=peinew,relation='corroborates')
claim('event',E,'time_original','旧裴传系归还于安重诲死、吴越复通后，与主930返使叙时不同。',39,'後重誨死，後吳越復通中國，羽始得還。','保留旧传先后说法；不静改通鉴时间，也不把旧概传全部当930已发生。',source=peiold,relation='conflicts')
E=ev('qian_chuanguan_petitions','钱传瓘与将佐屡为钱镠上表自诉',39,'其子传瓘','上表自诉。',[('传瓘','为父屡上表者'),('镠','由子与将佐上表自诉者')],place='吴越至后唐',year=None,when='钱镠受处分后，钱传瓘与将佐屡次上表；起止年日未独载',note='屡为多次状态，起止未具，年字段留空；不造每表日期或匿名将佐姓名。')
E=ev('court_releases_zhejiang_mission','后唐敕听两浙纲使自便',39,'癸卯，',None,[('镠','其两浙使团获准自便的吴越主')],when='930年十月癸卯',place='后唐、两浙',note='纲使自便为本敕范围，不扩成钱全部官爵即时恢复；新复通为概叙，勿等同本日恢复所有制度。')
E=ev('fengyun_beidu_appointment','冯赟由宣徽北院使任左卫上将军、北都留守',40,'以宣徽',None,[('冯赟','受任北都留守者')],place='北都',note='主承十月但未独干支；与旧七月甲子、南院右卫的纪日官衔差并列，不擅解释为两次已证任命。')
claim('event',E,'description','旧明宗纪记七月甲子以宣徽南院使、行右卫上将军、判三司冯赟为北京留守、太原尹。',40,'秋七月甲子，以宣徽南院使、行右衛上將軍、判三司馮贇為北京留守、太原尹。','主十月北院左卫与旧七月南院右卫异叙并列；馮贇与冯赟繁简同人，不新增第二冯。',source=feng,relation='conflicts')
E=ev('court_executes_dongguangye_family','后唐族诛董光业',41,'丁未，',None,[('光业','被族诛者')],when='930年十月丁未',place='后唐',note='族范围由旧补妻子，未名家属不造实名；此前父反不推所有罪证独立查明。')
claim('event',E,'description','旧明宗纪同丁未记宫苑使董光业与妻子斩于都市。',41,'丁未，宮苑使董光業並妻子並斬於都市，璋之子也。','妻子为妻与子女，非只配偶；都市为处刑地点名词不任意填现代街址。',source=october,relation='adds')
E=ev('mayin_ill_requests_succession','马殷寝疾，遣使请传位马希声',42,'楚王殷寝疾，','其子希声。',[('殷','病中遣使请求传位者'),('希声','父所请传位对象')],place='楚至后唐',note='请求不等朝廷已授或马殷已死；使未具名。')
relationship('殷','希声','父亲',42,'请传位于其子希声。','马殷→马希声为父亲，复用已有方向关系，不建立反向重复。')
E=ev('court_suspects_mayin_dead','朝廷疑马殷已死',42,'朝廷疑','殷已死，',[('殷','被朝廷怀疑已死的楚王')],note='疑为当时判断，不能据此登记真实死亡日；后段马卒另行录。')
E=ev('maxisheng_wuan_shizhong','后唐以马希声起复武安节度使兼侍中',42,'辛亥，',None,[('希声','受任武安节度使兼侍中者')],when='930年十月辛亥',place='武安',note='起复称法不作为父已死证据；朝疑父死与真实死亡分。')
claim('event',E,'description','旧明宗纪同辛亥记马希声授武安节度使加兼侍中，因父久病请以子为帅。',42,'時湖南馬殷奏，久病不任軍政，乞以男希聲為帥，故有是命。','旧明确久病请帅，与主疑死并列；不把未证死写入马殷死亡年字段。',source=october,relation='corroborates')
E=ev('zhangwu_xialu_commander','孟知祥以张武为峡路行营招收讨伐使，率水军趣夔州',43,'孟知祥以','将水军趣夔州，',[('知祥','任命峡路统兵者'),('张武','故蜀镇江节度使、率水军向夔州者')],place='峡路、夔州',note='复用904以来蜀峡路张武；趣夔为进军方向，不等已夺夔，新概称下峡取渝未强定同地点动作。')
claim('event',E,'description','新孟传概记孟遣张武下峡取渝州。',43,'又遣張武下峽取渝州。','新记行动目标渝、主趣夔保留不同层次；不将下一段已取渝州或张病卒提前录入。',source=meng,relation='adds')
E=ev('yuanyanchao_appointed_deputy','孟知祥以左飞棹指挥使袁彦超为张武副将',43,'以左飞棹','袁彦超副之。',[('知祥','任副将者'),('袁彦超','左飞棹指挥使、受任副将者'),('张武','峡路统兵主将')],place='峡路',note='副之承张武，非替张主将；新后张病卒袁代将属未来段，本批不强提前。')
E=ev('dongchuan_takes_five_prefectures','东川兵陷征、合、巴、蓬、果五州',43,'癸丑，',None,[('璋','东川兵所属主将')],when='930年十月癸丑',place='征、合、巴、蓬、果五州',note='征字疑讹留底本，不自行改成渠或补现代位置；东川兵并非明确董亲临每州，无名带兵将不造。')
E=ev('yankeqiu_dies','吴左仆射、同平章事严可求卒',44,'丙辰，','严可求卒。',[('严可求','去世的吴左仆射、同平章事')],when='930年十月丙辰',place='吴',note='本案二十四史未找到具体同条补句，主独证不造第二证。')
E=ev('jing_bingbu_canzheng','徐知诰以长子徐景通为兵部尚书、参政事',44,'徐知诰以','参政事，',[('知诰','任长子参政者'),('景通','大将军、授兵部尚书参政事者')],place='吴',note='徐知诰沿李昪、徐景通沿李璟既有实体，历史当时名保留标题；参政事与新参知政事原叙差，不借未来帝名让其930称帝。')
claim('person',people['李璟'],'description','新南唐世家记李景初名景通，为李昪长子，后来改名璟。',44,'景，初名景通，昪長子也。既立，又改名璟。','只校身份异名；既立改名为后时身份沿既有主体，不把改名或即位提前930。',source=jing,relation='adds')
claim('event',E,'description','新世家记李昪以景通为兵部尚书、参知政事。',44,'昪專政，以為兵部尚書、參知政事。','新徐温死后概叙与明年镇金陵，不自行强定每事927/928或当主同日；随后司徒同平章不提前。',source=jing,relation='corroborates')
relationship('知诰','景通','父亲',44,'徐知诰以其长子大将军景通','复用李昪→李璟父亲关系；长子明示但不新增所有未名兄弟。')
E=ev('xu_plans_jinling_station','徐知诰拟出镇金陵，为授景通参政的背景',44,'知诰将',None,[('知诰','拟出镇金陵者')],place='金陵',note='将是计划，非本句已离广陵到金陵；后年出镇另录，不写成当前驻地变更已实现。')
E=ev('liangkezhen_raids_champa','梁克贞入占城，取宝货归',45,'汉将',None,[('梁克贞','入占城掠宝货归的南汉将')],place='占城至南汉',note='本句未独月日，承十月记事不强同前丙辰；占城不直接补精确现代疆域。')
claim('event',E,'description','新南汉世家同记梁克贞又攻占城，掠宝货归。',45,'克貞又攻占城，掠其寶貨而歸。','同梁氏同役后占城回军复用事件，不另造新书重复战役；掠宝货为原载，不推永久吞并占城。',source=jiao,relation='corroborates')
reviews={
36:'交州拔、执曲、李进守、受俘赦分。新大有三年校930；未独月不硬赋九月。李守鄜/鄘同役识别而非繁简字，李知顺旧异不自动合。曲美沿911梁静海短名主体，旧承美梁授旄新顥子补身份，曲颢→曲美父亲；旧篇先后不强917前。龑刘岩沿旧主体。',
37:'癸巳围遂与后筑垒出战降分别，未独日不强同日。二万资州义军，高都押牙筑环城长城非万里长城；康马军指挥沿梁入唐身份，不混康文爽宋文通。新概称董攻不证亲临，未来夏死未提前。',
38:'戊戌趋利遇雨缺粮返阆实际，孟评仓廪漫天和北救为假设军略非已得；三千欲遣非已派，董辞有备为自述。',
39:'裴使都疑字不造都使衔，新吏部郎中同人。旧安死后返与主930冲突留；经岁返及载陆丧为补传背景不全强本年。钱子与将佐屡表无日期名单；癸卯纲使自便非全面官爵已复。',
40:'冯赟沿馮贇；主十月北院左卫，旧七月甲子南院右卫判三司北留太原差并列，未擅解释成已证两任。',
41:'丁未族诛，旧妻子并斩都市补，妻子妻与儿女非单妻，无名家属不造。',
42:'马病请传、朝疑死、辛亥任希声分，起复不证马已死；旧父久病请帅补，复用既有父亲。',
43:'张武同故蜀峡路将复用；任主水军趣夔、袁副分，新下峡取渝叙目标不提前已夺及张死袁代。癸丑五州征疑字保留不改渠、地名无坐标，董兵非本人亲临逐州。',
44:'丙辰严卒主独证；李昪李璟稳定主体，徐当时名与新景通改璟身份相合。参政与新参知原叙留，不强新徐温死后概年；将出镇非已经出镇，既有父亲复用，司徒未来未提前。',
45:'梁入占城取宝归与新同事复用，不推吞并占城；未独日不承丙辰。全年尚余第46—55段。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(36,46):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=930,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(36,46)],next_paragraph='zztj-v277-y0930-p046',next_volume=277,next_year=930,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续930年第36—45段、原41—50行；南汉交州占城、遂州围城、董退阆、钱表返使、冯任北留、董族诛、马请传、峡路水军和吴参政。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(36,46)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
