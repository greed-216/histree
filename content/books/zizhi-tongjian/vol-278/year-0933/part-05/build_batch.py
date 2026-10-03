# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 933 paragraphs 40–42."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 58))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'ba163460','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))

specs += [('xinwudaishi-006-933-princes',YEAR/'part-02/sources/library/xinwudaishi-006-933-princes','0f922712','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-933-coup','tongjian-278-933-aftermath']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0933-p040-p042',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
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
for n in range(40, 43):
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
        citation = f'卷278·长兴四年（933）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0933_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','上':'李嗣源','闽王':'王延钧','文杰':'薛文杰','继图':'王继图','李赞化':'耶律倍','李赞华':'耶律倍','知诰':'李昪','徐知诰':'李昪','从荣':'李从荣','秦王':'李从荣','延光':'范延光','赟':'冯赟','汉琼':'孟汉琼','义诚':'康义诚','彝超':'李彝超'}
NEW_ALIASES={'马处钧':['馬處鈞'],'李重吉':['李重吉'],'朱洪实':['朱弘实','朱弘實','硃洪实','朱洪實'],'刘氏（秦王妃）':[],'安从益':['安從益']}

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

def event(code, title, n, quote, actors, when=None, note='', year=933, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='933年十一月条下；确日未独载'
    key = 'event_zztj_278_0933_' + code
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
        edge = 'participation_zztj_278_0933_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_278_0933_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

# Consecutive body paragraphs 40–42; separate movements, reports, decisions, and results.
ev('mingzong_relapse','十一月戊子明宗疾病复作',40,'戊子，','帝疾复作，',[('帝','患病君主')],when='933年十一月戊子',place='后唐宫廷')
ev('congrong_visits_sick_father','己丑李从荣入宫问疾，王淑妃告明宗而未获回应',40,'己丑，','帝不应。',[('帝','病危而未回应者'),('从荣','入宫问疾者'),('王淑妃','告知秦王在此者')],when='933年十一月己丑',place='后唐宫廷',note='未回应不等已经死亡；不据疾病作现代诊断。')
ev('congrong_mistakes_death','李从荣听到宫中哭声，误以为明宗已死',40,'从荣出，','意帝已殂，',[('从荣','因哭声作出判断者')],note='已殂是秦王判断；同段明宗当夕小愈证明非实际死亡。')
ev('congrong_absent_next_morning','李从荣次晨称疾不入宫',40,'明旦，','称疾不入。',[('从荣','称疾未入宫者')],when='933年十一月己丑问疾次晨',place='后唐京师')
ev('mingzong_temporary_recovery','明宗当夕病情稍愈，李从荣不知',40,'是夕，','而从荣不知。',[('帝','病情稍愈者'),('从荣','未获知病情者')],when='933年十一月己丑问疾当夕',note='原叙先次晨再追是夕，保原相对时序，不编公历日。')
ev('congrong_plans_armed_entry','李从荣恐不得继位，与党谋以兵入侍、先制权臣',40,'从荣自知','先制权臣。',[('从荣','谋划率兵入侍者')],note='恐不得为嗣是心理与谋划；尚未实行的制臣计划不作已擒杀权臣，未名党人不猜名单。')
ev('ma_consults_zhu_feng','辛卯马处钧奉李从荣命问朱弘昭、冯赟率牙兵入宫止处',40,'辛卯，','王自择之。”',[('马处钧','秦王都押牙、传问者'),('从荣','遣使问入宫部署者'),('朱弘昭','答王自择者'),('冯赟','答王自择者')],when='933年十一月辛卯',place='后唐京师')
ev('zhu_feng_admonish_loyalty','朱弘昭、冯赟私劝马处钧转告秦王竭心忠孝、勿信浮言',40,'既而私于','不可妄信人浮言。”',[('朱弘昭','托使者劝诫者'),('冯赟','托使者劝诫者'),('马处钧','听受劝诫的使者')],when='933年十一月辛卯')
ev('congrong_threatens_families','李从荣怒，复遣马处钧以家族威胁朱弘昭、冯赟',40,'从荣怒，','何敢拒我！”',[('从荣','以家族威胁者'),('马处钧','再传威胁者'),('朱弘昭','受威胁者'),('冯赟','受威胁者')],when='933年十一月辛卯',note='威胁不等已经杀害二人家族。')
ev('zhu_feng_report_palace','朱弘昭、冯赟入告王淑妃、孟汉琼，议召康义诚',40,'二人患之，','乃召义诚谋之，',[('朱弘昭','入告及召谋者'),('冯赟','入告及召谋者'),('王淑妃','受告参与议论者'),('孟汉琼','宣徽使、受告议论者'),('义诚','被召商议者')])
ev('kang_withholds_opinion','康义诚不作决断，仅称惟相公所使',40,'义诚竟无言，','惟相公所使。”',[('义诚','回避决断者')],note='有言将校不预议，不把竟无言写作全程完全未说话。')
ev('zhu_private_consultation','朱弘昭夜邀康义诚至私第，康答复如初',40,'弘昭疑义诚','其对如初。',[('朱弘昭','邀私询者'),('义诚','仍未明确决断者')],place='朱弘昭私第',note='时为壬辰行动前夜，原未独载日干支；不把疑不欲众言视为已证密谋。')
ev('congrong_marches_tianjin','壬辰李从荣自河南府常服率步骑千人陈于天津桥',40,'壬辰，','陈于天津桥。',[('从荣','率牙兵列阵者')],when='933年十一月壬辰',place='河南府、天津桥',note='千人按原数记；率兵事实与孟汉琼后来称反的报告层分。')
ev('ma_final_ultimatum','壬辰黎明马处钧再告冯赟秦王决入兴圣宫并威胁宗族',40,'是日黎明，','祸福在须臾耳。”',[('从荣','遣使提出入宫意向者'),('马处钧','传最后告言者'),('冯赟','受告者')],when='933年十一月壬辰黎明',place='冯赟第',note='且居兴圣宫是计划，不当已经入宫居住。')
ev('ma_consults_kang_again','马处钧又见康义诚，康表示奉迎',40,'又遣处钧','王为则奉迎。”',[('马处钧','再次问康者'),('义诚','答奉迎者')],when='933年十一月壬辰',note='王为则奉迎疑来字，保底本；只记奉迎答复，不据疑字补具体迎接行动。')
ev('feng_warns_kang_at_gate','冯赟入右掖门告四人，责康义诚勿因儿在秦府顾望',40,'赟驰入','义诚未及对，',[('冯赟','转告并责康者'),('朱弘昭','聚谋者'),('义诚','受责者'),('汉琼','聚谋者'),('孙岳','三司使、聚谋者')],when='933年十一月壬辰',place='中兴殿门外',note='康子未名，前批已录遣子；不猜其姓名。')
ev('gate_report_and_meng_enters','监门报秦兵至端门外，孟汉琼入殿，朱弘昭等随入',40,'监门白','亦随之入。',[('汉琼','起而入殿主张拒兵者'),('朱弘昭','随入者'),('冯赟','随入者'),('义诚','随入者')],when='933年十一月壬辰',place='端门、中兴殿',note='指衣疑拂衣，不另造指衣动作；本句弘照承前弘昭，同主体不造朱弘照。')
ev('meng_reports_rebellion','孟汉琼向明宗报告李从荣反并攻端门，朱弘昭等答已闭门',40,'汉琼见帝','阖门矣。”',[('汉琼','报告称反者'),('帝','受告并询问者'),('朱弘昭','答有兵并已闭门者'),('冯赟','答有兵并已闭门者')],when='933年十一月壬辰',place='后唐宫廷',note='反及攻端门为孟报告层；新帝纪评以兵自助而不书反，保不同史述立场，不覆盖率兵事实。')
ev('mingzong_orders_kang_response','明宗命康义诚处置而勿惊百姓',40,'帝指天','勿惊百姓！”',[('帝','下令者'),('义诚','受处置命令者')],when='933年十一月壬辰',note='命令不等康实际亲率兵出击，主后述孟朱出兵另录。')
ev('mingzong_recalls_congke_aid','明宗对李重吉追述李从珂曾在战阵救己',40,'帝曰：“吾与尔父，','数脱吾于厄；',[('帝','追述受救者'),('李从珂','追述战阵救助者'),('李重吉','听受追述的控鹤指挥使')],year=None,when='壬辰谈话所追述的过往战阵；具体年月未知',note='冒矢石及救险为往事，不能当933当日新战斗。')
ev('mingzong_proposes_congke_command','明宗表示当召李从珂授兵柄',40,'当呼尔父','授以兵柄耳。',[('帝','提出召授意向者'),('李从珂','拟召授兵柄者'),('李重吉','受告者')],when='933年十一月壬辰',note='当呼为意向，不写已经召到或已授新职。')
ev('chongji_guards_palace','李重吉奉命率控鹤兵守宫门',40,'汝为我','守宫门。',[('帝','命闭宫门者'),('李重吉','控鹤指挥使、率兵守门者')],when='933年十一月壬辰',place='后唐宫门')
relationship('李从珂','李重吉','父亲',40,'控鹤指挥使李重吉，从珂之子也，','李从珂→李重吉为父亲，方向表示前者是后者父亲，不另造反向重复边。')
ev('meng_orders_hongshi_cavalry','孟汉琼披甲乘马，召朱洪实率五百骑讨李从荣',40,'孟汉琼被甲','讨从荣。',[('汉琼','召骑军并令讨者'),('朱洪实','马军都指挥使、率五百骑者'),('从荣','被讨秦王')],when='933年十一月壬辰',place='后唐宫廷',note='朱洪实与新朱弘实同战同五百骑，繁简异文同人；不同侯弘实。')
ev('congrong_sends_for_kang','李从荣坐天津桥，遣左右召康义诚',40,'从荣方据','召康义诚。',[('从荣','派召者'),('义诚','被召者')],when='933年十一月壬辰',place='天津桥',note='召不等康实际赴秦王军中。')
ev('congrong_learns_cavalry','秦王使者从左掖门隙见朱洪实骑兵，回报李从荣',40,'端门已闭，','走白从荣。',[('朱洪实','率骑北来者'),('从荣','获报者')],when='933年十一月壬辰',place='左掖门',note='使者未名，不将之认成此前马处钧。')
ev('congrong_arms_himself','李从荣获报后取铁掩心并调弓矢',40,'从荣大惊，','坐调弓矢。',[('从荣','取护身具并备弓矢者')],when='933年十一月壬辰',place='天津桥')
ev('congrong_retreat_and_scatter','骑兵到来，李从荣归府、僚佐逃匿，牙兵掠嘉善坊溃去',40,'俄而骑兵大至，','牙兵掠嘉善坊溃去。',[('从荣','战败归府者')],when='933年十一月壬辰',place='河南府、嘉善坊',note='未名僚佐与牙兵按群体记，不据聚散创建政治盟友边。')
ev('an_kills_congrong_couple','安从益斩匿床下的李从荣与刘妃，并杀其子、献首',40,'从荣与妃刘氏','以其首献。',[('从荣','被斩秦王'),('刘氏（秦王妃）','与秦王同被斩的妃'),('安从益','皇城使、执行斩杀者')],when='933年十一月壬辰',place='河南府',note='安从益与前宫苑使安重益异字身份尚待核，不仅因形近合并；未名儿子不猜李重光。')
relationship('刘氏（秦王妃）','从荣','妻子',40,'从荣与妃刘氏匿床下，','刘妃→李从荣为妻子，不给刘氏裸名别名造成同姓后宫混淆。')
ev('sun_advises_zhu_feng','孙岳曾参与内廷密谋，为朱弘昭、冯赟陈说秦王祸福',40,'初，孙岳','康义诚恨之，',[('孙岳','为冯朱陈说祸福者'),('朱弘昭','忧秦王并受说者'),('冯赟','忧秦王并受说者'),('义诚','史载怨恨孙岳者')],year=None,when='初所追述的内廷议论；具体日期未知',note='初为追叙，不定壬辰；怨恨为主书解释，不能推长期绝对敌对关系。')
E=ev('kang_kills_sun_yue','康义诚乘乱密遣骑士射杀孙岳',40,'至是，','密遣骑士射杀之。',[('义诚','遣骑射杀者'),('孙岳','被射杀的三司使')],when='933年十一月兵变期间；主未独日，新纪记乙未',note='主附兵变叙而未独载日；新帝纪乙未明确康杀孙，旧纪乙未为乱兵所害廢朝不一定即死日，保并列。')
ev('mingzong_worsens_after_son_death','明宗闻李从荣死，绝而复苏两次，病情加重',40,'帝闻从荣死，','由是疾复剧。',[('帝','闻子死而病剧者'),('从荣','其死引发病情变化者')],when='933年十一月壬辰后',note='此处仍未死亡，帝死在后续戊戌段。')
ev('congrong_palace_child_killed','诸将请求处死宫中所养秦王幼子，明宗悲泣而最终交出',40,'从荣一子尚幼，','不得已，竟与之。',[('帝','泣问幼子何罪而最终交出者'),('从荣','幼子的父亲')],when='933年十一月兵变后；未独日',place='后唐宫中',note='原竟与之承前请除；未名幼子不猜名字，不强认前安斩之子为同一人；新传二幼子皆从死作为人数并列证。')
ev('feng_visits_mingzong','十一月癸巳冯道率群臣入见明宗，帝泣言家事',41,'癸巳，',None,[('冯道','率群臣入见者'),('帝','见群臣泣诉家事者')],when='933年十一月癸巳',place='雍和殿',note='家事惭见为帝言论，不写全群臣已一致支持杀子。')
ev('meng_summons_conghou','十一月甲午遣孟汉琼召李从厚，并令孟权知天雄军府',42,'宋王从厚','权知天雄军府事。',[('李从厚','原天雄节度使、被召宋王'),('汉琼','被遣征召并权知军府者'),('帝','朝廷遣召时在位君主')],when='933年十一月甲午',place='天雄军、后唐朝廷',note='天雄节度为从厚既有身份，不造此日新任；征召不等已抵京即位，权知主语是孟。')
# Independently preserved secondary-book evidence, attached to the corresponding main paragraph.
old='jiuwudaishi-044-933-coup-aftermath';end='jiuwudaishi-051-congrong-end';battle='xinwudaishi-015-qin-coup-battle';deaths='xinwudaishi-015-qin-coup-deaths';new6='xinwudaishi-006-933-princes';sun='xinwudaishi-027-sun-yue-killed'
def supplement(code,source,quote,text,n=40,note='同段跨书核对；异字保留，不据未名人推身份。',relation='corroborates'):
 claim('event','event_zztj_278_0933_'+code,'description',text,n,quote,note,source=source,relation=relation)
supplement('mingzong_relapse','xinwudaishi-015-mingzong-illness','十一月戊子，雪，明宗幸宮西士和亭，得傷寒疾。己丑，從榮與樞密使朱弘昭、馮贇入問起居於廣壽殿，帝不能知人。王淑妃告曰：「從榮在此。」又曰：「弘昭等在此。」皆不應。從榮等去，乃遷於雍和殿，宮中皆慟哭。至夜半後，帝蹶然自興於榻，而侍疾者皆去，顧殿上守漏宮女曰：「夜漏幾何？」對曰：「四更矣！」帝即唾肉如肺者數片，溺涎液斗餘。守漏者曰：「大家省事乎？」曰：「吾不知也。」有頃，六宮皆至，曰：「大家還魂矣！」因進粥一器。至旦，疾少愈，而從榮稱疾不朝。','新唐家人传记十一月戊子明宗幸士和亭而伤寒；疾病经过属于史载，未作现代诊断。',n=40)
supplement('ma_consults_zhu_feng','xinwudaishi-015-qin-coup-message','初，從榮常忌宋王從厚賢於己，而懼不為嗣。其平居驕矜自得，及聞人道宋王之善，則愀然有不足之色。其入問疾也，見帝已不知人，既去，而聞宮中哭聲，以謂帝已崩矣，乃謀以兵入宮。使其押衙馬處鈞告弘昭等，欲以牙兵入宿衞，問何所可以居者。弘昭等對曰：「宮中皆王所可居，王自擇之。」因私謂處鈞曰：「聖上萬福，王宜竭力忠孝，不可草草。」處鈞具以告從榮，從榮還遣處鈞語弘昭等曰：「爾輩不念家族乎？」弘昭、贇及宣徽使孟漢瓊等入告王淑妃以謀之，曰：「此事須得侍衞兵為助。」乃召侍衞指揮使康義誠，謀於竹林之下。義誠有子在秦王府，不敢決其謀，謂弘昭曰：「僕為將校，惟公所使爾！」弘昭大懼。','新唐家人传也记马处钧往来传秦王率兵入侍之意，康因子在府而不决。',n=40)
supplement('chongji_guards_palace','xinwudaishi-015-qin-palace-orders','明日，從榮遣馬處鈞告馮贇曰：「吾今日入居興聖宮。」又告義誠，義誠許諾。贇即馳入內，見義誠及弘昭、漢瓊等坐中興殿閤議事，贇責義誠曰：「主上所以畜養吾徒者，為今日爾！今安危之機，間不容髮，奈何以子故懷顧望，使秦王得至此門，主上安所歸乎？吾輩復有種乎？」漢瓊曰：「賤命不足惜，吾自率兵拒之。」即入見曰：「從榮反，兵已攻端門。」宮中相顧號泣。明宗問弘昭等曰：「實有之乎？」對曰：「有之。」明宗以手指天泣下，良久曰：「義誠自處置，毋令震動京師。」潞王子重吉在側，明宗曰：「吾與爾父起微賤，至取天下，數救我危窘。從榮得何氣力，而作此惡事！爾亟以兵守諸門。」重吉即以控鶴兵守宮門。','新唐家人传记明宗命李重吉守宫门，重吉为潞王从珂之子。',n=40)
supplement('an_kills_congrong_couple','jiuwudaishi-051-congrong-end','長興中，以本官充天下兵馬大元帥。從榮乃請以嚴衛、捧聖步騎兩指揮為秦府衙兵，每入朝，以數百騎從行，出則張弓挾矢，馳騁盈巷。既受元帥之命，即令其府屬僚佐及四方遊士，各試《檄淮南書》一道，陳己將廓清宇內之意。初，言事者請為親王置師傅，明宗顧問近臣，執政以從榮名勢既隆，不敢忤旨，即奏云：「王官宜委。」從榮乃奏刑部侍郎劉讚為王傅，又奏翰林學士崔棁為元帥府判官。明宗曰：「學士代予詔令，不可擬議。」衣榮不悅，退謂左右曰：「既付以元帥之任，而阻予請僚佐，又未諭製旨也。」復奏刑部侍郎任讚，從之。〈（《宋史·趙上交傳》：秦王從榮開府兼判軍衛，以上交為虞部員外郎，充六軍諸衛推官。李澣、張沆、魚崇遠皆白衣在秦府，悉與上交友善。累遷司封郎中，充判官。從榮素豪邁，不遵禮法，好昵群小，上交從容言曰：「王位尊嚴，當修令德以慰民望。王忍為此，獨不見恭世子、戾太子之事乎？」從榮怒，出之。曆涇、秦二鎮節度判官。從榮及禍，僚屬皆坐斥。上交由是知名。）〉後舉兵犯宮室，敗死，廢為庶人。〈（《通鑒·明宗紀》云：己丑，大漸，秦王從榮入問疾，帝俯首不能舉。王淑妃曰：「從榮在此。」帝不應。從榮出，聞宮中皆哭。從榮意帝已殂，明旦，稱疾不入。是夕，帝實小愈，而從榮不知。從榮自知不為時論所與，恐不得為嗣，與其黨謀，欲以兵入侍，先製權臣。壬辰，從榮自河南府常服將步騎千人陳於天津橋。孟漢瓊被甲乘馬，召馬軍都指揮使朱洪實，使將五百騎討從榮，從榮方據胡床，坐橋上，遣左右召康義誠。端門已閉，叩左掖門，從門隙窺之，見朱洪實引騎兵北來，走白從榮，從榮大驚，命取鐵掩心擐之，坐調弓矢。俄而騎兵大至，從榮走歸府，僚佐皆竄匿，牙兵掠嘉善坊潰去。從榮與妃劉氏匿床下，皇城使安從益就斬之，以其首獻。丙申，追廢從榮為庶人。《五代會要》云：清泰元年，葬以公禮。從之。《五代史補》：秦王從榮，明宗之愛子。好為詩，判河南府，辟高輦為推官。輦尤能為詩，賓主相遇甚歡。自是出入門下者，當時名士有若張杭、高文蔚、何仲舉之徒，莫不分廷抗禮。更唱迭和。時干戈之後，武夫用事，睹從榮所為，皆不悅。於是康知訓等竊議曰：「秦王好文，交遊者多詞客，此子若一旦南面，則我等轉死溝壑，不如早圖之。」高輦知其謀，因勸秦王托疾：「此輩須來問候，請大王伏壯士，出其不意皆斬之，庶幾免禍矣。」從榮曰：「至尊在上，一旦如此，得無危乎？」輦曰：「子弄父兵，罪當笞爾；不然，則悔無及矣。」從榮猶豫不決，未幾及禍，高輦棄市。初，從榮之敗也，高輦竄於民家，且落發為僧。既擒獲，知訓以其毀形難認，復使巾幘著緋，驗其真偽，然後用刑。輦神色自若，屬聲曰：「朱衣才脫，白刃難逃。 」觀者笑之。）〉','旧宗室传也记秦王与刘妃匿床，皇城使安从益斩之献首。',n=40)
supplement('congrong_palace_child_killed','xinwudaishi-015-qin-coup-deaths','從榮二子尚幼，皆從死。','新唐家人传记李从荣二子尚幼，皆从死；未名且与主宫中一子叙述层次不同，不强合个体。',n=40)
supplement('kang_kills_sun_yue','xinwudaishi-027-sun-yue-killed','及從榮死，義誠始引兵入河南府，召岳檢閱從榮家貲。岳至，義誠乘亂，使人射之，岳走至通利坊見殺，明宗不能詰。','新康义诚传补秦王死后康召孙岳检秦家财，乘乱射之；孙逃至通利坊而死。',n=40)
supplement('meng_summons_conghou','jiuwudaishi-044-933-coup-aftermath','甲午，賜宰臣、樞密使禦衣玉帶，康義誠已下錦帛鞍馬有差。遣宣徽使孟漢瓊召宋王於鄴都。','旧明宗纪同甲午记遣宣徽使孟汉琼召宋王于邺都；另赐衣带鞍马的是宰臣、枢密使及康义诚等。',n=42)
event('an_cavalry_first_attack','新史记安从益率三百骑先冲，秦王射之使稍退',40,'是日，從榮自河南府擁兵千人以出。從榮寮屬甚眾，而正直之士多見惡，其尤所惡者劉贊、王居敏，而所昵者劉陟、高輦。從榮兵出，與陟、輦並轡耳語，行至天津橋南，指日景謂輦曰：「明日而今，誅王居敏矣！」因陣兵橋北，下據胡牀而坐，使人召康義誠。而端門已閉，叩左掖門，亦閉，而於門隙中見捧聖指揮使朱弘實率騎兵從北來，即馳告從榮。從榮驚懼，索鐵厭心，自調弓矢。皇城使安從益率騎兵三百衝之，從榮兵射之，從益稍却。弘實騎兵五百自左掖門出，方渡河，而後軍來者甚眾，從榮乃走歸河南府，其判官任贊已下皆走出定鼎門，牙兵劫嘉善坊而潰。從榮夫妻匿牀下，從益殺之。',[('安从益','率三百骑先冲者'),('从荣','射来骑者')],when='933年十一月壬辰',place='天津桥',source=battle,note='新传补同战先后，不把全部原文群体当各个人行动。')
supplement('meng_orders_hongshi_cavalry',battle,'是日，從榮自河南府擁兵千人以出。從榮寮屬甚眾，而正直之士多見惡，其尤所惡者劉贊、王居敏，而所昵者劉陟、高輦。從榮兵出，與陟、輦並轡耳語，行至天津橋南，指日景謂輦曰：「明日而今，誅王居敏矣！」因陣兵橋北，下據胡牀而坐，使人召康義誠。而端門已閉，叩左掖門，亦閉，而於門隙中見捧聖指揮使朱弘實率騎兵從北來，即馳告從榮。從榮驚懼，索鐵厭心，自調弓矢。皇城使安從益率騎兵三百衝之，從榮兵射之，從益稍却。弘實騎兵五百自左掖門出，方渡河，而後軍來者甚眾，從榮乃走歸河南府，其判官任贊已下皆走出定鼎門，牙兵劫嘉善坊而潰。從榮夫妻匿牀下，從益殺之。','新传朱弘实率五百骑自左掖门出渡河，与主朱洪实同场同兵数；姓名异文归同人。')

q=(sources[new6]/'source.txt').read_text(); a=q.index('乙未'); b=q.index('。',a)+1
supplement('kang_kills_sun_yue',new6,q[a:b],'新明宗纪明确十一月乙未康义诚杀三司使孙岳；主附兵变叙未独日，两层纪日并列。',note='乙未作为新纪证，不强改主附壬辰叙事为同日。',relation='adds')
for name in ['李从荣','刘氏（秦王妃）','孙岳']:
 row=next(x for x in B['people'] if x['key']==people[name]);row['death_year']=933
 claim('person',row['key'],'death_year',name+'于933年十一月兵变及其后处死或遇害。',40,span(40,'从荣与妃刘氏','密遣骑士射杀之。'),'死亡年份明，孙岳确日有主叙与新纪不同层，未换算公历。')
reviews={40:'长叙逐动作拆分。帝病与秦误信已殂、谋划与执行、孟称反与新纪不书反分层。朱洪实/弘实同战同骑军识同人，未混侯弘实；李重吉父明确；刘妃限定身份；安从益与既存安重益字异尚待考，不盲合。王为、指衣、弘照原字保，奉迎及入殿动作据上下文，未以疑字造人。孙岳主附兵变、新纪乙未、旧乙未廢朝并列，不硬定同日。明宗拟召从珂不当已授；初孙议与战阵往事年未定。幼子不名，不猜重光或强合个体。',41:'癸巳雍和殿冯道率见、帝泣家事原言；非已崩或群臣一致政治表态。',42:'从厚天雄为既有职，甲午孟征召及权知分清主体；不提前写到京即位。旧同日鄴都、赐衣鞍马补。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(40,43):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=933,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(40,43)],next_paragraph='zztj-v278-y0933-p043',next_volume=278,next_year=933,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷278连续933年第40—42正文段、原75—77行；秦王兵变长叙、癸巳群臣问疾、甲午征召宋王。第43段追废与官属处分仍待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(40,43)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
