# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 930, paragraphs 1–9."""
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
specs=[
 ('tongjian-277-930-spring',P/'sources/library/tongjian-277-930-spring','238471e3','司马光等'),
 ('jiuwudaishi-041-930-february',P/'sources/library/jiuwudaishi-041-930-february','238471e3','薛居正等'),
 ('jiuwudaishi-041-930-march',P/'sources/library/jiuwudaishi-041-930-march','238471e3','薛居正等'),
 ('xinwudaishi-006-930',P/'sources/library/xinwudaishi-006-930','238471e3','欧阳修'),
 ('xinwudaishi-061-930-crown-prince',P/'sources/library/xinwudaishi-061-930-crown-prince','238471e3','欧阳修'),
 ('xinwudaishi-051-lirenju-dongzhang',ROOT/'content/books/zizhi-tongjian/vol-276/year-0929/part-03/sources/library/xinwudaishi-051-lirenju-dongzhang','0a803f54','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-930-spring']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0930-p001-p009',
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
for n in range(1, 10):
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
    ck = f'claim_zztj_277_0930_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','璋':'董璋','知祥':'孟知祥','季良':'赵季良','仁罕':'李仁罕','业':'张业','澈':'杨澈','吴主':'杨溥','琏':'杨琏','从曮':'李继曮','弘照':'朱弘昭','福':'康福'}
NEW_ALIASES={'郭在徽':[],'都延昌':[],'王行本':[],'李彦钊':['李彥釗']}

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
    if when is None:when='930年'+('正月' if n<=3 else '二月' if n<=5 else '三月')+'本段；确日未载'
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
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# Consecutive nine paragraphs, chronological facts and independently located supplements.
feb='jiuwudaishi-041-930-february';mar='jiuwudaishi-041-930-march';ann='xinwudaishi-006-930';wu='xinwudaishi-061-930-crown-prince';dong='xinwudaishi-051-lirenju-dongzhang'
E=ev('dongzhang_builds_jianmen_seven_forts','董璋遣兵在剑门筑七寨',1,'春，正月，','筑七寨于剑门。',[('璋','遣兵筑寨者')],place='剑门',note='正月无确日，筑寨不是已与唐军接战；七为寨数，非七支军总兵数。')
claim('event',E,'description','新董传补记派将李彦钊扼剑门关为七砦，关北增关号永定。',1,'又遣其將李彥釗扼劍門關為七砦，於關北增置關，號永定。','新此段承天成四年后连谋，未独系930正月；主筑寨与新扼关叙法对应，不把新随后戍兵惩罚和九月事提前。',source=dong,relation='adds')
E=event('liyanzhao_defends_jianmen_yongding','新董传记李彦钊扼剑门七砦，并记关北增置永定关',1,'又遣其將李彥釗扼劍門關為七砦，於關北增置關，號永定。',[('璋','遣守将者'),('李彦钊','受派扼剑门者')],year=None,when='剑门七寨的补述；新本句未独纪年日',place='剑门、永定关',source=dong,note='守寨与主筑寨不同动作，永定关另记增置；新连叙未具确年，不断定李本人施工或关寨同物，李彦钊不与李彦超李彦珣混。')
E=ev('zhaojiliang_sent_zizhou_peace','孟知祥遣赵季良赴梓州修好',1,'辛巳，',None,[('知祥','遣修好使者'),('季良','赴梓州修好者')],when='930年正月辛巳',place='成都至梓州',note='修好为外交行动，不提前判断两川永远同盟或彼此没有戒心。')
E=ev('guozaihui_proposes_large_coins','鸿胪少卿郭在徽奏请铸当五千、三千、一千的大钱',2,'鸿胪少卿','一千大钱；',[('郭在徽','建议铸大钱者')],note='奏请未获实铸证明，数值为拟当值不是铸量，不自动加文或重量单位。')
E=ev('guozaihui_demoted_for_coin_proposal','朝廷以郭在徽所言指虚为实、无识妄言，左迁其为卫尉少卿同正',2,'朝廷以',None,[('郭在徽','被降职者')],note='指虚等为朝廷评价，不当现代货币政策必定不合理的结论；同正是原职衔尾，未补同正员脱字或具体官阶。郭在徽未检二十四史同案，主独证，不与郭在钧混。')
E=ev('yangche_title_dehua','吴改封平原王杨澈为德化王',3,'吴徙',None,[('澈','由平原王徙德化王者')],place='吴',note='徙爵非明确迁居某城市，不填未经证实的德化地理坐标；杨澈复用927封爵主体。')
E=ev('zhaojiliang_returns_chengdu','赵季良自梓州返回成都',4,'二月，乙未朔，','赵季良还成都，',[('季良','修好使行后返成都者')],when='930年二月乙未朔',place='梓州至成都',note='返程日期主明确，未推原外交任务完全失败。')
E=ev('zhaojiliang_warns_about_dongzhang','赵季良对孟知祥评价董璋贪残好胜、志大谋短，恐终为西川患',4,'谓孟知祥曰','终为西川之患。”',[('季良','提出警告者'),('知祥','受警告者'),('璋','被评价对象')],when='930年二月乙未朔还成都后',place='成都',note='性质评语与未来忧患为赵的话，未当董当日已经进攻西川；董仅谈话对象不当在场。')
E=ev('lirenhan_zhangye_plan_banquet','都指挥使李仁罕、张业欲置宴召孟知祥',4,'都指挥使','欲置宴召知祥；',[('仁罕','拟设宴邀知祥者'),('业','拟设宴邀知祥者'),('知祥','受拟邀对象')],when='930年二月戊戌赴宴前',place='成都',note='欲设宴不是已宴，称二人都指挥使依主句，不推张业新改名或新任该职。')
E=ev('nun_accuses_generals_banquet_murder','赴宴前两日，有尼姑告称李仁罕、张业欲于宴日谋害孟知祥',4,'先二日，','谋以宴日害知祥；',[('仁罕','被尼姑指控者'),('业','被尼姑指控者'),('知祥','被告知谋害目标者')],when='930年二月，宴前两日；原文未另标干支',place='成都',note='尼姑未名不造实名，谋害是告言而非真实谋反；不自行把先二日算某公历日或替原文补丁酉/丙申。')
E=ev('mengzhixiang_inquiry_finds_no_evidence','孟知祥诘问告言，无谋害实据',4,'知祥诘之','无状，',[('知祥','诘问告言者')],when='930年二月赴宴前',place='成都',note='无状与先告相连，不能将后刑视为确认二将有罪；未名具体被诘者不猜另有证人。')
E=ev('duyanchang_wangxingben_executed','孟知祥追究始言者军校都延昌、王行本，将其腰斩',4,'丁酉，','腰斩之。',[('知祥','推查始言者并处刑者'),('都延昌','被追究、腰斩的军校'),('王行本','被追究、腰斩的军校')],when='930年二月丁酉',place='成都',note='被杀是始言者二人非李仁罕张业；推查和腰斩原明，不新增被杀尼姑或二将死亡事件。')
E=ev('mengzhixiang_attends_banquet_alone','孟知祥去尽随从，独赴李仁罕宅就宴',4,'戊戌，','独诣仁罕第；',[('知祥','去随从独赴宴者'),('仁罕','宅中设宴者')],when='930年二月戊戌',place='成都、李仁罕宅',note='独诣为该次赴宴，未说明正式解除全部卫军；张业先拟宴不独证当时在席，不猜其出席。')
E=ev('lirenhan_pledges_loyalty_at_banquet','李仁罕叩头流涕，称惟尽死报德，主记诸将由此亲附服孟',4,'仁罕叩头',None,[('仁罕','席间表忠者'),('知祥','受报德表忠者')],when='930年二月戊戌宴中',place='成都',note='尽死是誓言非已死亡；诸将亲附为史述未给名单，不新增所有同场军将永久统属或盟友边。此宴案二十四史未检同案补证，主独证。')
E=ev('two_sichuans_joint_petition_fears','孟知祥、董璋共同上表，称两川因阆中建节、绵遂增兵而忧恐',5,'壬子，','无不忧恐。”',[('知祥','共同表奏者'),('璋','共同表奏者')],when='930年二月壬子',place='两川至后唐朝廷',note='无不忧恐为表文自述，不是统计全体军民；阆中建节承929保宁，未另建新军。与新孟传连表请罢唐官异详不强同一个表或930本日请求所有罢官。')
E=ev('emperor_reassures_two_sichuans','李嗣源以诏书慰谕孟知祥、董璋',5,'上以诏书','慰谕之。',[('帝','诏慰者'),('知祥','受慰者'),('璋','受慰者')],when='930年二月壬子表后；诏发确日未独载',note='慰谕不是已撤阆绵遂驻军，不能把安抚写成双方即消除所有疑虑。')
E=ev('emperor_sacrifices_yuanqiu','李嗣源祀圆丘',5,'乙卯，','上祀圆丘，',[('帝','亲行郊祀者')],when='930年二月乙卯',place='圆丘、南郊',note='这是完成郊祀，不与929筹备郊祀贡钱事件重合；圆丘名原保留，地点未经核坐标。')
claim('event',E,'description','旧明宗纪乙卯记祀昊天上帝于圜丘，柴燎礼毕，郊宫受贺。',5,'乙卯，祀昊天上帝於圜丘，柴燎禮畢，郊宮受賀。','圜丘/圆丘为字形称法差，原摘录分别留；未补具体现代遗址。',source=feb,relation='corroborates')
claim('event',E,'description','新明宗纪同乙卯记有事南郊。',5,'乙卯，有事于南郊，大赦，改元。','与旧主同日互证，本句其他赦及改元在独立事件分录。',source=ann,relation='corroborates')
E=ev('tang_general_amnesty_after_sacrifice','后唐郊祀后大赦',5,'乙卯，','大赦，',[('帝','大赦发布者')],when='930年二月乙卯',note='大赦不等全部罪一律免刑，具体例外由旧诏补；不增实际出狱人数。')
claim('event',E,'description','旧明宗纪赦诏列十恶五逆、放火劫舍、屠牛、官典犯赃、伪行印信、合造毒药等为例外。',5,'大赦天下，除十惡五逆、放火劫舍、屠牛、官典犯贓、偽行印信、合造毒藥外，罪無輕重，咸赦除之。','按史载赦范围限定，未替换古法罪名为现代刑法分类。',source=feb,relation='adds')
E=ev('era_changes_tiancheng_to_changxing','后唐改元长兴',5,'乙卯，','大赦，改元。',[('帝','改元者')],when='930年二月乙卯，天成五年改长兴元年',note='主只改元，改长兴由旧明确补；年标题长兴为后置编年标识，不推930正月已用长兴。')
claim('event',E,'description','旧明宗纪记御五凤楼宣制，改天成五年为长兴元年。',5,'是日，禦五鳳樓，宣製：改天成五年為長興元年；','同日正式改元，不把公元930从正月起全称长兴即当时原纪年。',source=feb,relation='adds')
E=ev('lijiyan_attends_sacrifice','凤翔节度使兼中书令李继曮入朝陪祀',5,'凤翔节度使','入朝陪祀，',[('从曮','凤翔节度使、入朝陪祀者')],when='930年二月郊祀前后；入朝确日未独载',place='凤翔至后唐朝廷',note='原李从私用字严据已有李继曮/李从曮身份及旧同月李从严凤翔佐核，沿原稳定人物，不与皇子李从珂混；入朝日不强乙卯当天。')
E=ev('lijiyan_transferred_xuanwu','朝廷制徙李继曮为宣武节度使',5,'三月，壬申，',None,[('从曮','由凤翔徙宣武节度者')],when='930年三月壬申',place='凤翔至宣武军职',note='制徙为任命，不推同日已抵汴州；行事年月不同于前二月陪祀。')
claim('event',E,'description','旧明宗纪同日记凤翔李从严进封岐国公、移镇汴州。',5,'壬申，鳳翔節度使李從嚴進封岐國公，移鎮汴州。','宣武治汴州，同一移镇不同称法；李从严原字与曮疑字分别存，岐国公补不另造三月改名事件。',source=mar,relation='corroborates')
E=ev('yanglian_crown_prince','吴主杨溥立江都王杨琏为太子',6,'癸酉，',None,[('吴主','立太子者'),('琏','江都王、被立太子者')],when='930年三月癸酉',place='吴',note='太子不是已即帝位，不与928江都王封爵重合。')
claim('event',E,'time_original','新吴世家大和二年记册江都王璉为太子。',6,'二年，冊其子江都王璉為太子。','二年承上大和改元929，对应930；璉/琏只规范人物名，原保留；未补纸本未明日。',source=wu,relation='corroborates')
relationship('吴主','琏','父亲',6,'二年，冊其子江都王璉為太子。','杨溥→杨琏为父亲，新其子明确；复用已有父边，不反向再造儿子边。',source=wu)
E=ev('zhuhongzhao_appointed_fengxiang','后唐以朱弘昭为凤翔节度使',7,'丙子，',None,[('弘照','宣徽使、获任凤翔节度者')],when='930年三月丙子',place='凤翔',note='主硃弘照、旧朱宏昭、新朱弘昭按同职同日沿已存朱弘昭，不新人物；不悄改原文照/昭。')
claim('event',E,'description','旧明宗纪同丙子授宣徽使朱宏昭凤翔节度。',7,'丙子，以宣徽使朱宏昭為鳳翔節度使；','宏昭与主弘照是人名字异形，凭同日同职及已有身份复用，不当新宏昭另人。',source=mar,relation='corroborates')
E=ev('kangfu_reports_baojing_capture','康福奏报攻克保静镇',8,'康福奏','克保静镇，',[('福','报克镇者')],when='930年三月本段；奏报及实际攻克确日未独载',place='保静镇',note='奏为报告语境，不将本段排列倒成三月丙子实际克城；承929李匡宾据镇，不重复929方渠与青刚峡战。')
E=ev('kangfu_reports_likuangbin_execution','康福奏报斩李匡宾',8,'康福奏',None,[('福','奏报斩叛将者'),('李匡宾','被报斩者')],when='930年三月本段；奏报及执行确日未独载',place='保静镇军务',note='沿929李匡宾同人，李从宾/李宾异名校核说明保留不新增同案人物；二十四史未检得同案克镇杀李明确补证，旧灵武杀蕃二千非本条同事件，不冒充补证。')
E=ev('anyi_restored_zhaoyi_name','朝廷复以安义军为昭义军',9,'复以',None,[],place='安义军、昭义军',note='军镇复名非新建潞州城或分出新州，未具诏日不继用前丙子日期。')
review='卷277连续930年第1—9段、原6—14行。年标题长兴元年为编年标识，二月乙卯才实际天成五年改长兴。董主正月筑7寨与新董遣李彦钊扼7砦、增永定关区别，补书连叙未独年用null，新将明确不与彦超彦珣混，后9月战和酷刑不提前。辛巳赵赴梓、二月乙未朔还成都，评董未来患为赵发言非实战。郭请当5千3千1千为面值非枚数，请铸非获准实铸，降卫尉同正照原尾、朝廷无识评语归其说；郭无二十四史同案，不混在钧。吴澈徙爵非迁城。李张欲宴与匿名尼先二日告谋、孟诘无状、丁酉推始言军校都王腰斩、戊戌独赴宅、仁罕誓与诸将附分；谋害指控未证实，不杀李张，不猜尼姑名死或在席张，二十四史未检同案。壬子两川表忧为其陈述，阆建承929不重设，诏慰非已撤兵。乙卯圆丘实祀、赦、改元分；旧圜丘补礼名，赦有十恶等例外，不全赦，天成5改长兴1由旧明示。李从私用字严复用李继曮/从曮身份，旧同月从严补，不混皇子从珂；二月陪祀与三月壬申制徙不同日，旧补岐国公汴州。癸酉吴杨琏太子、新大和2册父明，复用父边，不等即帝。朱主弘照旧宏昭新弘昭同职同日沿已有朱弘昭，原照昭留。康克保静杀李为奏报，实际日未具，沿929李匡宾；旧灵武杀蕃2000不同事不虚补，二十四史未检同案。安义复昭义为军名非新城，无具体诏日。原摘录保留底本，展示简体，纸本异文待核。第10段曹淑妃册后及后续尚未处理，全年未完成。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,10):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=930,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,10)],next_paragraph='zztj-v277-y0930-p010',next_volume=277,next_year=930,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续930年第1—9段、原6—14行；剑门两川交往、郭铸钱、吴徙爵、李张告谋宴案、郊祀改元及三月任授克镇军复名。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(1,10)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
