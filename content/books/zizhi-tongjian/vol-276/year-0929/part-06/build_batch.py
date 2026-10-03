# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 929, paragraphs 33–36."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 37))
specs=[
 ('tongjian-276-929-winter-end',YEAR/'part-05/sources/library/tongjian-276-929-winter-end','fce44f4b','司马光等'),
 ('xinwudaishi-046-kangfu-appointment',YEAR/'part-05/sources/library/xinwudaishi-046-kangfu-appointment','fce44f4b','欧阳修'),
 ('xinwudaishi-061-929-wu-change',YEAR/'part-05/sources/library/xinwudaishi-061-929-wu-change','fce44f4b','欧阳修'),
 ('jiuwudaishi-040-929-december',P/'sources/library/jiuwudaishi-040-929-december','53f24ccd','薛居正等'),
 ('xinwudaishi-064-two-sichuans',P/'sources/library/xinwudaishi-064-two-sichuans','53f24ccd','欧阳修'),
 ('xinwudaishi-068-wangyanbing-identity',P/'sources/library/xinwudaishi-068-wangyanbing-identity','53f24ccd','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-929-winter-end']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0929-p033-p036',
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
for n in range(33, 37):
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
        citation = f'卷276·天成四年（929）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0929_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','福':'康福','重诲':'安重诲','知祥':'孟知祥','璋':'董璋','仁矩':'李仁矩','知询':'徐知询','知诰':'李昪','廷禀':'王延禀','继雄':'王继雄','虔裕':'武虔裕','渐高':'申渐高'}
NEW_ALIASES={'申渐高':['申漸高'],'王继雄':['王繼雄'],'武虔裕':[]}

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

def event(code, title, n, quote, actors, when=None, note='', year=929, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when=('929年赴镇途中；战事确月日未独载' if n==33 else '929年十二月本段；确日未载' if n<=35 else '929年十月置保宁军后；本段未独纪月日')
    key = 'event_zztj_276_0929_' + code
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
        edge = 'participation_zztj_276_0929_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_276_0929_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
# Final four consecutive paragraphs of 929, preserving uncertainty and variants.
kf='xinwudaishi-046-kangfu-appointment';wu='xinwudaishi-061-929-wu-change';dec='jiuwudaishi-040-929-december';sc='xinwudaishi-064-two-sichuans';minshu='xinwudaishi-068-wangyanbing-identity'
E=ev('kangfu_defeats_interception_fangqu','康福赴镇至方渠，击退出兵拦截的羌胡',33,'康福行至','福击走之；',[('福','赴镇遭拦、击退对方者')],place='方渠',note='本段未独纪日；承十月赴镇后，十一月段后排列不证明全部战事都十一月。羌胡是史书集称，无实名不补族首姓名。')
claim('event',E,'description','新康福传同记行至方渠，羌夷出邀，福击走之。',33,'行至方渠，而羌夷果出邀福，福以兵擊走之。','同案互证，羌夷/羌胡称法保留，不定现代民族归属。',source=kf,relation='corroborates')
E=ev('kangfu_shenyu_surprise_qinggang','康福至青刚峡，遣卫审𡷣突袭未觉唐兵到的吐蕃野利、大虫二族，主记大破、杀获殆尽',33,'至青刚峡','杀获殆尽。',[('福','命突袭者'),('卫审𡷣','奉命掩击者')],place='青刚峡',note='数千帐是帐落不是精确人数；杀获是杀及俘合称，不写所有人均死。卫规范字沿上批校核、原摘录保留私用字；不与方渠拦截混成同一地战。')
claim('event',E,'description','新康福传作青冈峡，记遇雪登山见烟火、分兵三道出其不意袭吐蕃，获玉璞绫锦羊马。',33,'至青岡峽，遇雪，福登山望見川谷中煙火，有吐蕃數千帳，不覺福至，福分其兵為三道，出其不意襲之。','青刚/青冈地名异形保留；雪和三道为新补，不把数千帐改数千人；新后杀之殆尽更强于主杀获，未据此统一全死。',source=kf,relation='adds')
claim('event',E,'description','旧明宗纪十二月丁酉载康福奏破野利、大虫两族三百余帐于方渠、获牛羊三万。',33,'十二月丁酉，靈武康福奏：「破野利、大蟲兩族三百餘帳於方渠，獲牛羊三萬。」','同两族战报与主青刚峡数千帐在地点及帐数上有差，不用奏报时间差掩盖；并列待核，三万是牛羊不是俘兵。丁酉是奏报纪时，不倒作主战日。',source=dec,relation='conflicts')
E=ev('kangfu_reaches_lingzhou','康福威声大振，进入灵州，主书记自此朔方始受朝廷派代',33,'由是威声',None,[('福','以新任主帅入灵州者')],place='灵州、朔方',note='受代是军镇开始接受朝廷派代，不是改朝换代；威声为史述，未推全河西征服。')
E=ev('xuzhigao_appointed_zhongshuling_ningguo','吴加徐知诰兼中书令，领宁国节度使',34,'十二月，','领宁国节度使。',[('知诰','加兼中书令、领宁国者')],when='929年十二月',place='吴、宁国军职',note='徐知诰沿李昪，不另造人物；不同前徐知询留镇海。')
claim('event',E,'time_original','新吴世家将徐知诰为中书令列于三年十一月徐知询来朝、吴改元同段。',34,'以徐知誥為中書令。','新段三年十一月概叙与主十二月纪时口径不同，并列不造确定两次加授；宁国由主明载。',source=wu,relation='conflicts')
E=ev('xuzhigao_toasts_xuzhixun','徐知诰召徐知询饮，以金杯酌酒相赐，祝弟寿千岁',34,'知诰召','愿弟寿千岁。”',[('知诰','设饮酌酒相赐者'),('知询','受召受赐酒者')],note='金钟按酒器金杯展示、原钟字不改；祝寿是话语，不当真实寿数，不直接断定此句已证下毒。')
E=ev('xuzhixun_suspects_poison_shares_wine','徐知询疑酒有毒，以另一器均分，跪献徐知诰，祝各享五百岁',34,'知询疑','愿与兄各享五百岁。”',[('知询','疑毒、均酒献兄者'),('知诰','被献另一份酒者')],note='疑为其判断，不独证现代毒物成分或徐知诰蓄意杀弟；寿语非实年龄。')
E=ev('xuzhigao_refuses_shared_wine','徐知诰变色顾左右而不受，徐知询捧酒不退，左右不知所为',34,'知诰变色','左右莫知所为，',[('知诰','不肯受献酒者'),('知询','捧酒不退者')],note='反应按原记，不由不受反推出确定投毒动机；左右未名不猜周宗在场。')
E=ev('shenjiangao_drinks_combined_wine','伶人申渐高诙谐解围，取两份酒合饮，怀金杯趋出',34,'伶人申渐高','怀金钟趋出，',[('渐高','以诙谐语解围、合饮两份酒者')],note='解围为行为语境，未明自愿赴死动机；取两酒不写两整壶，申新人物不因字形与申渐高异体再造人。')
E=ev('xuzhigao_sends_remedy_shenjiangao','徐知诰密遣人用良药为申渐高解之',34,'知诰密遣','以良药解之，',[('知诰','遣人施药者'),('渐高','被施药者')],note='解之为史载用药尝试，未明药方、毒物或救治成功；使人未名。')
E=ev('shenjiangao_dies_after_wine','申渐高合饮后脑溃而卒，施药未及挽救',34,'已脑溃而卒。',None,[('渐高','酒宴后去世者')],note='脑溃底本原病状字保留、未改肠溃或现代诊断；结合前后记事，未确断投毒者、成分或主动自杀。此段二十四史未检得同案独立补证，主独证。')
E=ev('wangyanbing_retires_claiming_illness','奉国节度使、知建州王延禀称疾，退居里第',35,'奉国节度使','退居里第，',[('廷禀','称疾退居的奉国节度使、知建州者')],place='建州',note='按此前同任建州王延禀稳定主体复用，廷禀/延禀异名并列，未改原摘录；称疾非诊断已实病或退出所有官衔。')
E=ev('wangyanbing_petitions_son_jianzhou','王延禀请以建州授其子王继雄',35,'请以建州','授其子继雄；',[('廷禀','请子承建州者'),('继雄','被请任者')],place='建州',note='请任与庚子诏任分；主父子明确，身份据同建州、后新闽同子继雄回查，不与闽其他王姓混。')
relationship('廷禀','继雄','父亲',35,'请以建州授其子继雄；','王延禀（主此处王廷禀）→王继雄为父亲，不建反向儿子重复边。')
claim('person',people['王继雄'],'description','新闽世家另在后续战事中称延禀之子继雄，支持本批父子身份对照。',35,'使其子繼雄轉海攻其南門，','本句承延禀主语，仅补同人及亲属定位；其长兴二年战及死亡留931对应主段，不提前录成929事件。',source=minshu,relation='corroborates')
E=ev('wangjixiong_appointed_jianzhou','朝廷诏王继雄为建州刺史',35,'庚子，',None,[('继雄','获建州刺史任者')],when='929年十二月庚子',place='建州',note='朝廷诏与父请不同，不称儿子当天即奉国节度使；未补实际到任日。')
E=ev('anchonghui_sends_lirenju_wuqianyu_troops','安重诲使李仁矩与绵州刺史武虔裕各率兵赴治',36,'安重诲既','皆将兵赴治。',[('重诲','安排率兵赴治者'),('仁矩','镇阆州、率兵赴治者'),('虔裕','绵州刺史、率兵赴治者')],place='阆州、绵州',note='既以仁矩镇承十月任命，不另造第二次任命；均率兵无各自人数，此处不自动将新一般牙队500至3000作为二人确额。')
claim('person',people['武虔裕'],'description','本段称武虔裕为李嗣源故吏、安重诲外兄。',36,'虔裕，帝之故吏，重诲之外兄也。','故吏为旧任职关系无具体时年，外兄新孟传作表兄，未混安重诲亲兄安重璋。')
relationship('虔裕','重诲','表兄',36,'而虔裕，重誨表兄，','新孟传明确表兄，武虔裕→安重诲为表兄；与主外兄对照，不猜具体父系母系或新造共同祖辈。',source=sc)
E=ev('anchonghui_orders_dongzhang_surveillance','安重诲令李仁矩侦察董璋反状',36,'重诲使','诇董璋反状，',[('重诲','令侦察者'),('仁矩','受命侦察者'),('璋','被侦察对象')],place='阆州对东川',note='反状是调查目标，不等此时董已正式举兵反叛。')
E=ev('lirenju_embellishes_dongzhang_report','李仁矩增饰所探董璋情况，上奏朝廷',36,'仁矩增饰','而奏之。',[('仁矩','增饰并上奏者'),('璋','被报告对象')],note='增饰为主书性质判断，不列未载详细罪状，不把报内容当确证反叛。')
E=ev('court_strengthens_suizhou_xialuqi','朝廷令夏鲁奇修遂州城隍、缮甲兵，并增驻兵',36,'朝廷又使','益兵戍之。',[('夏鲁奇','武信节度使、奉命修城备军者')],place='遂州',note='城隍为城防及壕沟，非建城隍庙；无兵额不猜屯兵数或战果。')
E=ev('dongzhang_fears_military_reinforcement','董璋对朝廷加强军镇兵备大惧',36,'璋大惧。','璋大惧。',[('璋','感到恐惧者')],note='恐惧为史述，不凭情绪造已发生进攻。')
E=ev('rumored_mianlong_division_meng_fears','道路传言朝廷将割绵、龙为节镇，孟知祥亦惧',36,'时道路传言','孟知祥亦惧。',[('知祥','闻军镇分割传言而惧者')],place='绵州、龙州、西川',note='道路传言未独证已置绵龙新军镇；不生成已完成分割或确定疆域边界。')
E=ev('dongzhang_requests_meng_marriage','董璋与孟知祥素有隙、未通问，此时遣使赴成都为子求娶孟女',36,'璋素与','请为其子娶知祥女；',[('璋','遣使为子求婚者'),('知祥','女方父、受求婚者')],place='东川至成都',note='素隙为背景，不新记929才开始交恶；未名子女不猜董光业等、不新造夫妻或双方已姻亲边。')
E=ev('mengzhixiang_accepts_marriage_coalition','孟知祥许婚，与董璋谋合力拒朝廷',36,'知祥许之，',None,[('知祥','许婚、谋联合者'),('璋','谋联合对象')],place='两川',note='主许是答应求婚，未明礼成；谋并力不是当日已发动930反叛或已正式建蜀国。')
claim('event',E,'description','新孟传称知祥本欲不许，问赵季良；赵认为宜合纵拒唐，知祥遂许。',36,'而知祥心恨璋，欲不許，以問趙季良，季良以為宜合從以拒唐，知祥乃許。','补咨询和改变决定，未把新随后连表请罢唐官及慰诏直接倒赋929十二月，主930二月另有共同表需后续对读。',source=sc,relation='adds')
E=event('zhaojiliang_advises_two_sichuans_union','新孟传补赵季良建议合纵拒唐，促成孟知祥允婚',36,'以問趙季良，季良以為宜合從以拒唐，知祥乃許。',[('知祥','问谋、接受建议者'),('赵季良','提出合纵建议者')],year=None,when='两川求婚决定的补述；本句确月日未独载',place='成都',source=sc,note='本句相对于结亲决定的先后，未补确日或930实际开战；与主许婚同过程，不另造第二次婚姻。')
review='卷276连续929年第33—36段，原119—122行。康方渠邀击与青刚峡突袭分，数千帐非人数、杀获非全杀；新青冈、雪三道补，旧十二月丁酉战报两族三百余帐方渠和牛羊三万与主峡数千帐在地数有差并列，丁酉为奏日非战日。卫规范字沿上批，原私用字保留；入灵州受代是朝廷派代制度，不是改朝。十二月徐加中书令宁国与新十一月概叙不同，不造两授。金钟展示酒器，寿语非年龄，知询疑毒非已确证知诰下毒；拒杯、申诙谐合饮出、密药、脑溃卒分，脑字原留不改肠或现代诊断；申未检二十四史同案，主独证。王廷禀沿建州王延禀稳定身份，廷延并列、同子继雄由后新闽对照，后931战死不提前。称疾退居不是诊断，父请、庚子诏刺史分；父边王延禀→继雄，无反向重复。安既用仁矩镇承十月，不再授一次；武故吏外兄、新表兄明方向武→安，未猜父母线。仁矩诇反目标与增饰奏非当时董确反。遂城隍是防城壕非庙，无兵额；绵龙分割仅道路传言。董孟素隙为旧背景，求子女婚主只许未礼成、未名子女不造夫妻姻亲。谋拒唐非已发生930反叛；新孟赵问劝和许可补，后共同表与慰诏留930原主比对。原摘录不改，展示简体，纸本异文待核。929全年36段已逐段整理，整年完成仍须最后公开审计。'
contexts=[]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(33,37):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=929,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(33,37)],next_paragraph='zztj-v277-y0930-p001',next_volume=277,next_year=930,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷276连续929年第33—36段、原119—122行；康福到镇、徐氏宴、建州父子任命与两川求婚拒唐。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(33,37)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
