# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 930, paragraphs 49–55."""
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
 specs.append((directory.name,directory,'bfff83e2','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('liaoshi') else '欧阳修'))
specs.extend([
 ('jiuwudaishi-041-930-november',YEAR/'part-06/sources/library/jiuwudaishi-041-930-november','696f1bdc','薛居正等'),
 ('xinwudaishi-064-meng-campaign',YEAR/'part-04/sources/library/xinwudaishi-064-meng-campaign','73f70bd8','欧阳修'),
])

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-930-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0930-p049-p055',
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
for n in range(49, 56):
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
    ck = f'claim_zztj_277_0930_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'希声':'马希声','突欲':'耶律倍','敬瑭':'石敬瑭','廷隐':'赵廷隐','王晖':'王晖（前蜀陵州刺史）','重诲':'安重诲','上':'李嗣源'}
NEW_ALIASES={}

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
    if when is None:when='930年'+('十一月' if n<=50 else '十二月')+'本段；确日未独载'
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
dec='jiuwudaishi-041-930-december';an='xinwudaishi-024-an-supervises';ma='xinwudaishi-066-maxisheng-posts';liaoann='liaoshi-003-930-bei-departure';liaobei='liaoshi-072-bei-sea';nov='jiuwudaishi-041-930-november';meng='xinwudaishi-064-meng-campaign'
E=ev('maxisheng_succeeds_reverts_fanzhen','马希声袭位，称遗命撤建国制度，恢复藩镇旧制',49,'丙戌，',None,[('希声','袭位并恢复藩镇旧制者')],when='930年十一月丙戌',place='楚',note='称遗命是希声所述，不把制度变化等同全部楚疆域不复存在；与父遗命兄弟相继分别。')
claim('event',E,'description','新楚世家记马希声立，授武安、静江等军节度使。',49,'希聲立，授武安、靜江等軍節度使。','袭位支持，授朝官与本段撤国制不是同一事项；未提前新随后食鸡葬父或932卒。',source=ma,relation='corroborates')
E=ev('bei_sails_dengzhou_to_tang','东丹王突欲因失职不满，率部曲四十人越海，自登州来奔后唐',50,'契丹',None,[('突欲','渡海来奔的东丹王')],place='东丹至登州、后唐',note='突欲沿926耶律倍同人；四十为部曲数，不是家属数或整个东丹迁徙，未独日不承前丙戌。')
claim('event',E,'description','旧明宗纪记青州转登州奏：阿保机子东丹王突欲越海归国。',50,'青州奏，得登州狀，契丹阿保機男東丹王突欲越海來歸國。','青州转奏为报告，来归国是后唐视角；夹注契丹国志不当另一本已独核的来源。',source=nov,relation='corroborates')
claim('event',E,'time_original','辽史记十一月戊寅东丹上报人皇王浮海适唐。',50,'十一月戊寅，東丹奏人皇王浮海適唐。','同930太宗纪连续年条，戊寅系东丹奏报，非全部船程抵登或洛阳日；唐来奔与辽适唐视角不同。',source=liaoann,relation='corroborates')
E=event('tang_secretly_invites_bei','补记后唐明宗遣人跨海持书密召耶律倍',50,'唐明宗聞之，遣人跨海持書密召倍。',[('上','遣人密召者'),('突欲','被密召者')],year=None,when='耶律倍渡海赴唐前；传记未独纪年日',place='后唐至东丹',source=liaobei,note='补书追叙不硬定第一次召使发生930；使者未名。')
E=event('bei_departure_with_books','补记耶律倍称让位后见疑，立木刻诗，携高美人载书浮海',50,'使再至，倍謂左右曰：「我以天下讓主上，今反見疑；不如適他國，以成吳太伯之名。」立木海上，刻詩曰：「小山壓大山，大山全無力。羞見故鄉人，從此投外國。」攜高美人，載書浮海而去。',[('突欲','说明渡海意图、携书出行者')],year=None,when='辽史耶律倍传渡海前后概叙；本句未独纪年日',place='东丹海上',source=liaobei,note='让位见疑是倍自述；高美人无名不造姓名，刻诗与携书为传补，出海事主已录不重复作第二次赴唐。')
E=ev('shi_arrives_jianmen_december','石敬瑭至剑门',51,'十二月，壬辰，','石敬瑭至剑门。',[('敬瑭','抵剑门主军将')],when='930年十二月壬辰',place='剑门',note='此前绕袭诸将克关与石主军此时抵达分，不倒赋十一月壬申本人到关。')
E=ev('shi_advances_north_jianzhou','石敬瑭进屯剑州北山',51,'乙未，','进屯剑州北山；',[('敬瑭','进屯北山者')],when='930年十二月乙未',place='剑州北山')
E=ev('shu_deploys_behind_tooth_city_bridge','赵廷隐列阵牙城后山，李肇、王晖列阵河桥',51,'赵廷隐陈于','陈于河桥。',[('廷隐','牙城后山布阵者'),('李肇','河桥布阵者'),('王晖','河桥布阵者')],place='剑州牙城后山、河桥',note='王晖沿前陵州主体，未名河桥不补现代桥名坐标。')
E=ev('shi_infantry_attacks_zhao_archer_ambush','石敬瑭以步兵击赵廷隐，赵择善射者五百伏归路，待近鼓噪攻击',51,'敬瑭引步兵','北军退走，',[('敬瑭','步兵进攻者'),('廷隐','部署五百善射伏兵、近击者')],place='剑州北山、归路',note='五百为伏兵分队数，非赵全军；按甲等待不当未交战已投降，矛稍底本不改现代武器测距。')
E=ev('tang_falls_down_hill_captured','北军退走颠坠下山，被俘斩百余人',51,'北军退走，','俘斩百馀人。',[('敬瑭','退走北军主将'),('廷隐','击败俘斩敌方者')],place='剑州北山',note='百余为俘与斩合计，非分别俘百斩百，非明确全因跌死；不造准确伤亡表。')
E=ev('shi_cavalry_bridge_stopped','石敬瑭使骑兵冲河桥，李肇以强弩拒之使不能进',51,'敬瑭又使骑兵','骑兵不能进。',[('敬瑭','派骑兵冲桥者'),('李肇','强弩拒骑兵者')],place='河桥',note='王晖前列阵不等本句本人操作弩，参与只按该明句主语。')
E=ev('zhao_pursues_combined_ambush_defeats_shi','薄暮石敬瑭退，赵廷隐追蹑与伏兵合击败之，石还屯剑门',51,'薄暮，',None,[('敬瑭','退回剑门者'),('廷隐','追击合伏兵取胜者')],place='剑州至剑门',note='之指北军石部；未载俘主将，不推石本人被俘或全军全灭。')
claim('event',E,'description','新孟传记十二月石敬瑭与赵廷隐战于剑门，唐师大败。',51,'十二月，敬瑭及廷隱戰于劍門，唐師大敗。','新概称剑门、主详剑州山桥，保留层次地点名差，不静换主地点；是同役不是新增另一战。',source=meng,relation='corroborates')
E=ev('kuizhou_reports_recapture_kaizhou','夔州奏报复取开州',52,'癸卯，',None,[],when='930年十二月癸卯',place='夔州、开州',note='癸卯为奏报日，实际收复日未独载；奏者将领未名，不造主将。')
E=ev('maxisheng_wuan_jingjiang_zhongshuling','后唐以马希声为武安、静江节度使，加兼中书令',53,'庚戌，',None,[('希声','受两军节度与中书令者')],when='930年十二月庚戌',place='武安、静江',note='任命与十一月袭位、十月武安侍中层次分，不重复同官同日；静江不直接等现代省界。')
claim('event',E,'description','旧明宗纪同庚戌记湖南马希声起复，加兼中书令。',53,'庚戌，湖南節度使馬希聲起復，加兼中書令。','同日授衔印证，旧湖南简称与主两军详称并列。',source=dec,relation='corroborates')
E=ev('campaign_supply_difficulties_banditry','讨蜀未有功，军前使多言道路难进，关右百姓疲转饷逃山聚盗',54,'石敬瑭征蜀','聚为盗贼。',[('敬瑭','未成功讨蜀主将')],place='蜀道、关右山谷',note='多言为使者报告与史述，未名百姓不造，往往不是全关右人人为盗；未有功为当时概括不抹前克剑门。')
claim('event',E,'description','新安传记川路险阻、每费一石致一斗，关西民苦输送逃聚山林。',54,'而川路險阻，糧運甚艱，每費一石，而致一斗。自關以西，民苦輸送，往往亡聚山林為盜賊。','量比为新史述，不无证生成财政精确损失或对每一批运输套90%固定损耗。',source=an,relation='adds')
E=ev('emperor_proposes_personal_campaign','李嗣源忧征蜀困难，向近臣称拟亲往',54,'上忧之，','吾当自行耳。”',[('上','提出亲往计划者')],when='930年十二月壬子',note='当自行为提议，后准安去不录为帝已亲征。')
E=ev('an_requests_supervision_emperor_approves','安重诲自责军威不振，请往督战，李嗣源准许',54,'安重诲曰：','上许之。',[('重诲','请往督战者'),('上','准安请者')],when='930年十二月壬子',note='臣之罪为安自责话，不是司法判决；批准与实际出发次日分。')
E=ev('an_departs_western_front','安重诲拜辞，翌日出发，日驰数百里',54,'重诲即拜辞，','日驰数百里。',[('重诲','拜辞出发赴督战者')],when='930年十二月癸丑',place='后唐至西方军前',note='数百里为史载夸宽数，不换算现代精确速度；与旧甲寅、翌日行叙时冲突保留。')
claim('event',E,'time_original','旧明宗纪作甲寅遣安赴西面军前，言讫辞翌日行，与主壬子请癸丑行不同。',54,'甲寅，遣樞密使安重誨赴西面軍前。','旧干支及下文翌日保持，不人为回填成主癸丑或选一个覆盖另说。',source=dec,relation='conflicts')
claim('event',E,'description','新安传亦记请行后日驰数百里，关西远近惊骇。',54,'而重誨日馳數百里，遠近驚駭。','同督战路行，新后凤翔酒谈、三泉召还跨931未提前录本批。',source=an,relation='corroborates')
E=ev('western_towns_fear_supply_losses','西方藩镇闻安重诲赴军前惶骇，日夜运钱帛刍粮往利州，人畜多毙山谷',54,'西方籓镇闻之，','不可胜纪。',[('重诲','赴军前引发督运震动者')],place='西方藩镇至利州、山谷',note='无不惶骇为史述概括，不列未名各镇真实心理；不可胜纪不造死亡人数，钱帛粮运非军队已全部抵战场。')
claim('event',E,'description','新安传记督趣粮运日夜不断，道路毙踣不可胜数。',54,'督趣糧運，日夜不絕，斃踣道路者，不可勝數。','同运输损耗概记；不把未具数改为确计百万，也不另造冤案实名。',source=an,relation='corroborates')
E=ev('shi_opposes_shu_campaign_after_an_leaves','李嗣源已疏安重诲，石敬瑭在安离帝侧后累表称蜀不可伐，帝颇赞同',54,'时上已疏重诲，',None,[('上','逐渐疏安并认可石奏者'),('重诲','离帝侧的枢密使'),('敬瑭','原不欲西征、累表反对者')],place='军前至后唐',note='本不欲为既有意向背景，累表起止未载不造每表日期；颇然非本句已诏全撤军，安离帝侧不是已经死亡。')
E=ev('emperor_releases_shu_kuizhou_garrison','李嗣源纵归此前戍夔州的西川兵一千五百人',55,'西川兵',None,[('上','准西川戍兵归者')],place='夔州至西川',note='先戍为原状态，始戍年未知，本事件为本年末纵归；千五百不是所有蜀戍兵总数，未具归营日或主将。')
reviews={49:'丙戌袭位与十月授武安十二月两军加衔分，称遗命去国制为希声说，不推楚人民归零或全域被灭，新希声立支持但食鸡葬父未来不提前。',50:'突欲沿926耶律倍，四十部曲非家属全数。旧青转登奏主来奔与辽十一月戊寅东丹奏适唐视角相照，奏日非到洛日。辽倍传密召、刻诗携书作追叙年null，见疑为倍自述，高美人无名不造；不提前后唐授东丹慕华李赞华衔或936遇害。',51:'壬辰石主军到关与十一月先锋克关分，乙未北山屯，赵后山李王桥列。赵五百善射分队，百余俘斩合计，骑冲弩拒，暮追合伏败退分。新概剑门主详剑州山桥地名层次留，非另战；王晖前陵州同人不混冯。',52:'癸卯夔州奏复开为报道日，实际收复日不另定，未知将不造。',53:'庚戌两军节度兼中书令，与十月武安侍中十一月袭位分别；旧同日湖南起复中书支持，未现代坐标。',54:'道路报告、帝拟自行、安请准壬子、安癸丑发、藩镇震督运、石累表帝颇然分别。旧甲寅遣翌日行与主壬子请癸丑行差留；新石斗量比不变财政常数。未有功当时概括不抹十一克关；日数百里不换现代速度；人畜不可胜纪无确数。石本不欲背景与累表未独日不造每表；帝颇然不等已撤全军，新凤翔三泉召还后时未提前。',55:'本年末纵归先戍夔的西川一千五百；始戍年未载，不倒造始戍930或整个三万蜀戍军全归。全年55段主线已处理，待全年度公开证据审计才标完成。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(49,56):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=930,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(49,56)],next_paragraph='zztj-v277-y0931-p001',next_volume=277,next_year=931,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续第49—55段，原54—60行；马希声袭位、东丹王来奔、十二月剑门战、开州报复、加马衔、安赴督战及纵归西川戍兵。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(49,56)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
