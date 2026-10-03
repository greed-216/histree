# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 928, paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 53))
specs=[
 ('tongjian-276-late-927-opening',YEAR.parent/'year-0927/part-04/sources/library/tongjian-276-late-927-opening','e00f3e22','司马光等'),
 ('jiuwudaishi-039-january',P/'sources/library/jiuwudaishi-039-january','c991ab36','薛居正等'),
 ('jiuwudaishi-039-february',P/'sources/library/jiuwudaishi-039-february','c991ab36','薛居正等'),
 ('jiuwudaishi-039-march',P/'sources/library/jiuwudaishi-039-march','c991ab36','薛居正等'),
 ('jiuwudaishi-073-maozhang',P/'sources/library/jiuwudaishi-073-maozhang','c991ab36','薛居正等'),
 ('xinwudaishi-006-928',P/'sources/library/xinwudaishi-006-928','c991ab36','欧阳修'),
 ('jiuwudaishi-092-zhangjun-inquiry',YEAR.parent/'year-0927/part-04/sources/library/jiuwudaishi-092-zhangjun-inquiry','755ad621','薛居正等'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-late-927-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0928-p001-p008',
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
for n in range(1, 9):
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
        citation = f'卷276·天成三年（928）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0928_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','吴主':'杨溥','宣帝':'杨隆演','琏':'杨琏','璘':'杨璘','璆':'杨璆','玢':'杨玢','西方鄴':'西方邺'}
NEW_ALIASES={'杨琏':['楊璉'],'杨璘':['楊璘'],'杨璆':['楊璆']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷276天成三年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='928年二月本段；确日未载', note='', year=928, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_276_0928_' + code
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
        edge = 'participation_zztj_276_0928_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_276_0928_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
jan='jiuwudaishi-039-january';feb='jiuwudaishi-039-february';mar='jiuwudaishi-039-march';mao='jiuwudaishi-073-maozhang';new='xinwudaishi-006-928';zhang='jiuwudaishi-092-zhangjun-inquiry'
for code,name,title,start,end in [
 ('yanglian_jiangdu','琏','江都王','春，正月','江都王，'),
 ('yanglin_jiangxia','璘','江夏王','璘为','江夏王，'),
 ('yangqiu_yichun','璆','宜春王','璆为','宜春王，'),
 ('yangfen_nanyang','玢','南阳王','宣帝子',None),
]:
 E=ev(code,'吴主杨溥封'+ALIASES[name]+'为'+title,1,start,end,[(name,'获封'+title+'者')],when='928年正月丁巳',place='吴',note='同段丁巳统四封王，杨溥三子与宣帝子区分；前公号后王号均复用主体，不把封国等同本人已前往治所。')
for name in ['琏','璘','璆']:
 relationship('吴主',name,'父亲',1,Q[1]['text'],'吴主立子统琏璘璆三人，吴主是其父亲；不因琏璉繁简另建同人。')
relationship('宣帝','玢','父亲',1,'宣帝子庐陵公玢为南阳王。','宣帝沿已发布杨隆演追尊身份识别，其子玢，原公号王号同人。')
E=ev('maozhang_robe_drunken_play','史书记毛璋赭袍、纵酒为戏的僭越行为',2,'昭义节度使','纵酒为戏，',[('毛璋','被记骄僭行为的昭义节度使')],year=None,when='毛璋被征召前的行为，确年日未载',place='昭义',note='主时报赭袍疑时服，原字保留；旧传明确服赭黄，不用自动繁简转换改讹字；行为发生确年未明。')
claim('event',E,'description','旧毛璋传记其在潞州拥川妓、服赭黄、纵酒，令作王衍在蜀之戏。',2,'洎至潞州，狂妄不悛，每擁川妓於山亭院，服赭黃，縱酒，令為王衍在蜀之戲。','补所扮戏与潞州语境，不把王衍已亡人物加入928现场；服与主报的疑字保留待核。',source=mao)
E=ev('maozhang_kills_remonstrator','《通鉴》记毛璋剖心杀害劝谏者',2,'左右有谏者','剖其心而视之。',[('毛璋','主书所记杀害劝谏者')],year=None,when='被征召前，确年日未载',place='昭义',note='受害左右未具名，不虚构人物；所选旧传摘录没有此具体动作，不冒称该细节获其独立印证。')
E=ev('maozhang_recalled_right_jinwu','李嗣源闻毛璋行事，征为右金吾卫上将军',2,'帝闻之',None,[('帝','闻事后征召者'),('毛璋','右金吾卫上将军被征授者')],when='928年正月，本句未具日；旧纪补辛酉',place='昭义至后唐朝廷',note='征召任命不扩为同日已抵京；保留主卫字与旧纪略称右金吾上将军。')
claim('event',E,'description','旧明宗纪在辛酉记毛璋由前潞州节度使任右金吾上将军。',2,'辛酉，以前潞州節度使毛璋為右金吾上將軍，','具体干支补官职，前潞州与昭义镇名并存，不据其余同日任命新增与本段无关人物。',source=jan,relation='corroborates')
claim('event',E,'description','旧毛璋传也记事闻于朝后征为金吾上将军。',2,'事聞於朝，征為金吾上將軍。','只印证征召概称；传后其年秋及赐死另事不提前录成本段已完成。',source=mao,relation='corroborates')
E=ev('khitan_captures_pingzhou','契丹攻陷平州',3,'契丹',None,[],when='928年正月，主本句未具日',place='平州',note='原未具主将、兵数与战法，不推人名；新明宗纪补丁巳，旧方陷在辛酉项后不强同日。')
claim('event',E,'time_original','新明宗纪记928年正月丁巳契丹陷平州。',3,'三年春正月丁巳，契丹陷平州。','三年接天成年号；主未载日，保留新具体纪时。',source=new)
claim('event',E,'description','旧明宗纪正月辛酉任官项后记契丹方陷平州。',3,'契丹方陷平州。','方陷是简记，不能直接当辛酉发生日以否定新丁巳。',source=jan,relation='corroborates')
E=ev('february_solar_eclipse','《通鉴》记二月丁丑朔日食',4,'二月',None,[],when='928年二月丁丑朔',place='观察地点本句未载',note='纪日原样保留，不自行换算公历或推全国可见与食分。')
claim('event',E,'description','旧明宗纪记二月丁丑朔有司奏太阳应亏，但有云未见，群官表贺。',4,'二月丁丑朔，有司上言，太陽合虧，既而有雲不見，群官表賀。','主记日食与旧因云未见的观测记载并列，不据日食句推每处确见，也不据云遮否定发生。',source=feb)
E=ev('siyuan_plans_yedu_trip','李嗣源计划前往邺都',5,'帝将','帝将如鄴都，',[('帝','计划巡行者')],place='后唐朝廷至邺都',note='将为计划，后句不果行；不能建已到邺都。')
E=ev('escort_families_recent_daliang_move','扈驾诸军家属此前刚迁到大梁',5,'时扈驾','甫迁大梁，',[],year=None,when='928年二月本段巡行计划之前，甫迁确年日未载',place='大梁',note='甫是相对时间，未强迁移发生年；军属未具名，不扩为全军所有家属全数搬迁。')
E=ev('escort_families_discontent_yedu_plan','扈驾诸军家属闻将赴邺都不悦，并有流言',5,'时扈驾','詾詾有流言。',[],place='大梁',note='群体反应，不造具体将领或声称已发动兵变；詾詾底本原字保留，展示概述。')
E=ev('siyuan_cancels_yedu_trip','李嗣源闻流言后未成行邺都',5,'帝闻之',None,[('帝','未成行者')],place='大梁、拟赴邺都',note='不果行为本次计划停止，不能推长期禁巡行。')
claim('event',E,'description','旧明宗纪在二月丁丑朔条记诏停巡幸邺都。',5,'詔巡幸鄴都宜停。','此引用印证停巡令；何泽补事另列独立事实。',source=feb,relation='corroborates')
claim('event',E,'description','旧明宗纪另记何泽因伏阁劝谏巡行邺都，由仓部郎中迁吏部郎中。',5,'以倉部郎中何澤為吏部郎中，獎伏閣諫巡幸鄴都也。','补停巡相关劝谏者和奖励，未具该任命确日，不能强赋丁丑。',source=feb)
E=event('heze_rewarded_remonstrance','何泽因谏巡幸邺都，由仓部郎中迁吏部郎中',5,'以倉部郎中何澤為吏部郎中，獎伏閣諫巡幸鄴都也。',[('何泽','伏阁进谏及获迁者')],source=feb,when='928年二月，旧本句未具干支',place='后唐朝廷',note='从旧明宗纪独补相关奖励事件，与停巡令的丁丑不同，未强定任命同日。')
E=ev('wu_tang_envoy_exchange_background','庄宗灭梁后至本段，吴与后唐使者往来不绝',6,'吴自','使者往来不绝。',[],year=None,when='自庄宗灭梁以来至本段的交往背景，非928单次出使',place='吴与后唐',note='这是期间概述，不重复制造923灭梁事件或把所有来往同赋928。')
E=ev('wu_envoy_arrives','吴使者到后唐',6,'庚辰','吴使者至，',[],when='928年二月庚辰',place='后唐朝廷',note='使者未具名；旧补杨溥遣来贡贺，不推所携数量或签盟。')
claim('event',E,'description','旧明宗纪记杨溥遣使贡献，祝贺诛朱守殷。',6,'庚辰，偽吳楊溥遣使貢獻，賀誅朱守殷。','补来使目的；偽为史家政治称谓，本站展示采用吴，不改原摘录；朱死亡为既有927事实，不重造928死亡。',source=feb)
E=ev('anzhonghui_rejects_wu_envoy','安重诲以吴抗礼并遣使窥探为由，拒绝接待吴使',6,'安重诲','拒而不受，',[('安重诲','拒接吴使者')],when='928年二月庚辰',place='后唐朝廷',note='抗礼与窥觇为安重诲所作判断，不当吴使已证间谍；以为杨原疑缺字不自行补原文。')
claim('event',E,'description','旧明宗纪将不纳遣还记为明宗因荆南拒命及与吴相连所作决定。',6,'帝以荊南拒命，通連淮夷，不納其使，遣還。','主执行人物安重诲、旧帝为朝廷决定所归；并列政治理由，不据此推战争已经爆发。',source=feb)
E=ev('tang_cuts_wu_contacts','后唐自拒使后与吴断绝使者交往',6,'自是',None,[],when='928年二月庚辰拒使之后',place='后唐与吴',note='断绝承接使者外交往来语境，不推全部民间贸易或永久断交。')
E=ev('zhangjun_denied_changan_entry','张筠到长安，守兵闭门拒纳',7,'张筠','守兵闭门拒之；',[('张筠','被守兵拒纳者')],place='长安',note='与927授西都留守是不同阶段；守将未具名，不推由其个人预谋叛朝。')
claim('event',E,'description','旧张筠传同记到长安时守兵闭门不纳。',7,'及至長安，守兵閉門不納，','同一事件印证，不把传后天福二年归长安及卒提前到928。',source=zhang,relation='corroborates')
E=ev('zhangjun_rides_to_court','张筠单骑入朝',7,'筠单骑','筠单骑入朝，',[('张筠','单骑入朝者')],place='长安至后唐朝廷',note='单骑只是本次赴朝方式，不扩其从前军力。')
claim('event',E,'description','旧张筠传记东朝于洛，诏遣归第。',7,'筠東朝於洛，詔遣歸第。','补朝廷在洛及遣归私第叙法；主后授左卫与旧遣归并列，不说因此已入职禁军。',source=zhang)
E=ev('zhangjun_left_guard_general','《通鉴》记张筠获授左卫上将军',7,'筠单骑',None,[('张筠','主书所载左卫上将军获任者')],note='主左卫、旧左骁卫官职异文并列，不静默改主或重造一次未经证明的二次转官。')
claim('event',E,'description','旧明宗纪在二月辛卯记张筠授左骁卫上将军。',7,'辛卯，以山南西道節度使張筠為左驍衛上將軍。','官职与主左卫不同，所记原任仍山南西道而非西都，保留两书叙法；不强判另一次新任，纸本待核。',source=feb,relation='conflicts')
E=ev('xifangye_captures_guizhou','宁江节度使西方邺攻取归州',8,'壬辰','攻拔归州；',[('西方鄴','宁江节度使、攻取者')],when='928年二月壬辰',place='归州',note='主行动日在二月，不将后面旧三月奏报强定为同一日。')
claim('event',E,'description','旧明宗纪在三月条记西方邺上言收复归州。',8,'西方鄴上言，收復歸州。','本句仅支持收复奏报；后击败数量另句引用，不拼接非连续原文。',source=mar)
claim('event',E,'description','旧明宗纪三月条另记西方邺奏在归州击败荆南军数千人。',8,'西方鄴奏，於歸州殺敗荊南賊軍數千人。','数千为所奏概数，不当逐人核实死亡名单；三月奏报与主二月攻取区分。',source=mar)
claim('event',E,'time_original','新明宗纪将西方邺克归州列于三月。',8,'西方鄴克歸州。','回查整段三月纪年区间；主二月壬辰行动与新三月克州存纪月差异，新未为此句另具干支，不强赋前句癸亥。',source=new,relation='conflicts')
E=ev('jingnan_retake_guizhou','荆南不久后重新取归州',8,'未几',None,[],when='928年西方邺取归州后未几，确月日未载',place='归州',note='未几是相对时间，旧三月奏报不自动等此后再失；未具荆南将名，不虚构高季兴本人参战。')
review='连续928年1—8段逐句校核。丁巳四封王三杨溥子、杨隆演子玢按稳定key及父亲方向；三新琏璘璆保留繁体匹配，封国不当已赴治所。毛璋僭越赭袍纵酒和杀劝谏左右为征前背景null；主时报疑服保留原字，旧服赭黄及王衍戏补证，不当王衍928现场，原旧后秋案与赐死不提前。征金吾主未日旧辛酉，征非已抵。契丹平州新正月丁巳补日，旧方陷在辛酉后不强辛酉。主日食与旧应亏云未见并列，不扩食分或全国可见。巡邺计划、军属甫迁null、不悦流言、帝不果分阶段，无实际抵达或兵变；旧诏停与何泽谏获迁补证不把后任命同丁丑。吴往来庄宗灭梁以来为期间背景null，不重造923灭梁；庚辰使到与目的、安拒与判断、旧帝决定及荆吴相连理由、后断外交分事，不当已证间谍战争或永久全贸易终止。张筠到长安被拒、单骑朝、授官不同927授西都；旧东朝洛遣第补地点与过程；主左卫/旧二月辛卯左骁卫及原衔不同并列，不造二次转官。归州主二月壬辰攻取、旧三月收复奏报/击败概数、新三月克州不同纪法，后荆南未几再取仅相对不赋月日或主将。原字摘录、简体展示、纸本异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=928,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph='zztj-v276-y0928-p009',next_volume=276,next_year=928,supplements=supplements,excluded_non_body=[],coverage='卷276连续928年第1—8段、原文件33—40行；年初封王、毛璋征召、平州、日食、停巡邺都、拒吴使、张筠回朝与归州攻守。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(1,9)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
