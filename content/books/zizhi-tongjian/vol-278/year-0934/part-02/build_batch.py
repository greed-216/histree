# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 933 paragraphs 8–12."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,13))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'a2ffb86d','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [('tongjian-278-934-jiang-name',YEAR.parent/'year-0933/part-06/sources/library/tongjian-278-934-jiang-name','8487026c','司马光等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-934-jiang-name']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0934-p008-p012',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    if key.startswith('songshi-262-'):record=dict(record,section_title='卷262·赵上交传',citation='《宋史》卷262·赵上交传，段落 '+record['id']+'；EPUB卷题李濤傳沿卷内另一传主，正文已回查赵上交传，纸本待核。')
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
for n in range(8, 13):
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
    if source.startswith('songshi-262-'):record=dict(record,citation='《宋史》卷262·赵上交传，段落 '+record['id']+'；EPUB卷题李濤傳沿卷内另一传主，正文已回查赵上交传，纸本待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷278·清泰元年（934；正月及闰正月闵帝应顺元年）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0934_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从厚','闵帝':'李从厚','硃':'朱弘昭','朱':'朱弘昭','冯':'冯赟','璘':'王延钧','继鹏':'王继鹏','太后':'黄氏（闽太后）','临川王濛':'杨濛','徐知诰':'李昪','吴太祖':'杨行密','皇后':'曹氏（李嗣源后）','李端':'李端（安州副使）','知祥':'孟知祥'}
NEW_ALIASES={'张彦柔':['張彥柔'],'王延宗':[],'张重进':['張重進'],'唐汭':[],'王希全':['佛留'],'任驾儿':['任駕兒','任货儿','任貨兒'],'李端（安州副使）':[]}

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

def event(code, title, n, quote, actors, when=None, note='', year=934, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='934年正月条下；确日未独载' if n==8 else '934年闰正月条下；确日未独载'
    key = 'event_zztj_278_0934_' + code
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
        edge = 'participation_zztj_278_0934_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_278_0934_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




# Consecutive paragraphs 8–12. Reports, intentions and retrospective passages remain distinct.
ev('jiang_pucheng_victory','蒋延徽在浦城击败闽兵',8,'吴蒋延徽','败闽兵于浦城，',[('蒋延徽','吴军主将')],place='浦城')
ev('jiang_besieges_jianzhou','蒋延徽进围建州',8,'吴蒋延徽','遂围建州，',[('蒋延徽','进围者')],place='建州')
ev('min_sends_jianzhou_relief','王延钧遣张彦柔、王延宗领万人救建州',8,'闽主璘遣','救建州。',[('璘','遣将君主'),('张彦柔','上军、领救援者'),('王延宗','骠骑大将军、领救援者')],place='建州',note='万人为史载兵数；只记发援，不等援军已抵建州。')
ev('min_troops_refuse_advance','王延宗所部要求交出薛文杰，否则不进兵',8,'延宗军及','不能讨贼。”',[('王延宗','所部不进的将领'),('薛文杰','士卒索取者')],place='赴建州途中',note='不得文杰不能讨贼是士卒条件，不当文杰在场发令。')
ev('wang_yanzong_reports_refusal','王延宗驰使报告军士不进',8,'延宗驰使','国人震恐。',[('王延宗','遣使报告者')],note='国人震恐为史书概述，未名使者不新建。')
ev('min_dowager_and_prince_appeal','闽太后与王继鹏劝王延钧自为谋',8,'太后及','卿自为谋。”',[('太后','向闽主哭诉者'),('继鹏','福王、向闽主哭诉者'),('璘','被劝自谋的君主')],note='沿933太后黄氏同一主体，不凭此段建立母子关系。')
ev('wang_jipeng_strikes_xue','王继鹏在启圣门外用笏击倒薛文杰',8,'文杰出，','击之仆地，',[('继鹏','伺机击打者'),('薛文杰','被击倒者')],place='启圣门外')
ev('xue_delivered_to_army','薛文杰被槛车送军前，市人以瓦砾投击',8,'槛车送','瓦砾击之。',[('薛文杰','被槛车押送及投击者')],place='赴军途中')
ev('xue_predicts_survival','薛文杰自称过三日便无患',8,'文杰善术数，','则无患。',[('薛文杰','自称占算者')],note='自云为本人预测，不把术数视作已证实的因果。')
ev('xue_escorted_two_days','押送者因薛文杰之言加速，两日抵军',8,'部送者闻之，','二日而至，',[('薛文杰','加速押送的对象')],when='934年正月条下；押送历二日，起日未知',note='二日是历时，不能解读为正月初二。')
ev('xue_killed_by_troops','军士将薛文杰杀死并脔食',8,'士卒见之','脔食之；',[('薛文杰','被军士杀害者')],place='闽军军前',note='依主书臠食记暴力行为；新书磔于市为另一叙述层，异文并列。')
ev('min_pardon_arrives_late','王延钧遣使赦薛文杰，未及阻止其死',8,'闽主亟遣','不及。',[('璘','急遣赦使者'),('薛文杰','未获及时赦免者')],note='赦之不及不写成功获释；新书记翌日使到补相对时序。')
ev('xue_cage_retrospective','追叙薛文杰改制带内向铁铓的槛车',8,'初，文杰','动辄触之。',[('薛文杰','改制槛车者')],year=None,when='初字追叙；改制槛车的年月未载',note='制作早于此次押送，不强塞934正月；原器物细节保留引用。')
ev('xue_first_occupant_of_cage','薛文杰成为自己所制槛车的首位囚者',8,'车成，','首自入焉。',[('薛文杰','首先被装入自制槛车者')],note='此句回扣本段押送，并非自愿乘车或另一次入狱。')
ev('sheng_tao_execution','盛韬一并被诛',8,'并诛盛韬。','并诛盛韬。',[('盛韬','同段被诛者')],note='复用933盛韬；新闽世家巫徐彦与盛韬不得凭相似情节自动合并。')
ev('xu_fears_jiang_supporting_meng','史叙徐知诰担心蒋延徽克建州后拥杨濛',8,'蒋延徽攻建州垂克，','以图兴复，',[('蒋延徽','接近克建州、被疑拥濛的将领'),('徐知诰','担忧者'),('临川王濛','被设想拥立的临川王')],note='恐为徐担忧，不当蒋已拥濛、濛已谋反或建州已陷。')
ev('xu_recalls_jiang','徐知诰遣使召回蒋延徽',8,'徐知诰以','遣使召之。',[('徐知诰','遣使召回者'),('蒋延徽','被召回者')],note='完整前句限定召之指蒋延徽，未名使臣不猜姓名。')
ev('jiang_withdraws_after_relief_report','蒋延徽听闻闽军及吴越军将至，引兵撤退',8,'延徽亦闻','引兵归；',[('蒋延徽','闻援将至后撤军者')],place='建州',note='闻将至是情报，不写援军已到或已交战；也不推吴越具体主将。')
ev('min_pursuit_defeats_jiang','闽军追击击败撤退的蒋延徽军，死伤甚众',8,'闽人追击，','死亡甚众，',[('蒋延徽','撤军被追败的主将')],place='建州撤军途中',note='死亡甚众未给确数，不编歼灭人数。')
ev('zhang_chongjin_executed','败军归罪都虞侯张重进，将其斩杀',8,'归罪于','斩之。',[('张重进','被归罪及斩杀的都虞侯')],note='原文未明命斩者，不指定徐知诰或蒋延徽为处决发令者。')
ev('jiang_demoted','徐知诰贬蒋延徽为右威卫将军',8,'知诰贬','右威卫将军，',[('徐知诰','贬官者'),('蒋延徽','被贬右威卫将军者')])
ev('xu_seeks_peace_with_min','徐知诰遣使向闽求好',8,'知诰贬延徽','遣使求好于闽。',[('徐知诰','遣使求好者')],note='求好是外交请求，不当已经缔盟或签订具体条约。')
relationship('蒋延徽','吴太祖','女婿',8,'徐知诰以延徽吴太祖之婿','蒋延徽→杨行密为女婿，吴太祖沿已有杨行密；妻子未名不猜姓名，不建反向重复边。')
claim('person',people['蒋延徽'],'description','蒋延徽与临川王杨濛素善。',8,'与临川王濛素善','素善是此前友好交往概述，未给具体结交年月；不等政治结盟。')
for code,name,role in [('tang','唐汭','原左谏议大夫'),('chen','陈乂','原膳部郎中、知制诰')]:
 ev(code+'_jishizhong','闰正月'+name+'授给事中、充枢密直学士',9,'闰月，','充枢密直学士。',[(name,role+'、获新授职者')],note='两人的授职分录；旧纪置癸卯段下补证，主未独载任命干支。')
ev('tang_retinue_background','追叙唐汭以文学随李从厚，历三镇幕府',9,'汭以文学','在幕府。',[('唐汭','以文学随从及历幕者'),('帝','此前任镇的从厚')],year=None,when='从厚即位前追叙；三镇任幕具体年月未载',note='三镇未逐一列名，不据泛叙编造任官年月。')
ev('zhu_feng_exclude_capable_retinue','朱弘昭、冯赟在闵帝即位后斥逐有才将佐',9,'及即位，','皆斥逐之。',[('朱','参与斥逐者'),('冯','参与斥逐者'),('帝','即位后的君主')],year=None,when='从厚933年即位后至934年闰月前的概述；确日未知',note='将佐未名，不生成被斥逐名单；此概述可能跨年，不强定934。')
ev('tang_placed_near_emperor_under_chen','朱弘昭、冯赟引唐汭于密近并使陈乂监之',9,'汭性过疏，','监之。',[('唐汭','被引入密近并受监者'),('陈乂','被安排监唐者'),('朱','安排者'),('冯','安排者')],note='主过疏与旧夹注迂疏为用字差异；旧夹注明引通鉴，不算独立确证。')
ev('cao_empress_dowager','闰正月丙午尊明宗皇后曹氏为皇太后',9,'丙午，',None,[('皇后','明宗皇后曹氏、获尊者'),('帝','尊号时在位君主')],when='934年闰正月丙午',note='皇后承明宗遗后曹氏，旧纪明确曹氏；与从厚生母夏氏分开。')
ev('fu_servants_plot','王希全、任驾儿谋杀符彦超并据安州附吴',10,'安远节度使','据安州附于吴，',[('符彦超','安远节度使、被谋杀对象'),('王希全','符氏奴、谋乱者'),('任驾儿','符氏奴、谋乱者')],place='安州',note='谋杀、据州附吴为策划，不能写安州已经成功归吴。')
ev('fu_yanchao_murder','王希全、任驾儿假称急递，夜杀符彦超',10,'夜，','二奴杀之，',[('符彦超','出至听事、被杀者'),('王希全','假急递参与杀害者'),('任驾儿','假急递参与杀害者')],when='934年闰正月条下、己酉旦讨乱前夜；旧本传作应顺元年正月',place='安州听事',note='主承闰月，旧纪闰月丁巳奏此月七日夜；旧本传写正月，月份分歧并列。不误把丁巳奏日当遇害日，未由旦反推干支。')
ev('fu_killers_forge_orders','符彦超遇害后，二奴冒其命召将并杀不从者',10,'因以彦超','辄杀之。',[('王希全','冒用节度使命令者'),('任驾儿','冒用节度使命令者'),('符彦超','被冒名的已遇害节度使')],place='安州',note='以彦超之命是冒命，不记为符本人下令杀将；诸将未名不猜。')
ev('li_duan_suppresses_revolt','闰正月己酉旦李端率州兵诛二奴及党',10,'己酉旦，',None,[('李端','安州副使、率州兵平乱者'),('王希全','被讨诛者'),('任驾儿','被讨诛者')],when='934年闰正月己酉旦；旧本传承正月记诘旦',place='安州',note='李端加安州副使消歧；主己酉旦与旧本传正月层分别保留，党众未名不虚建。')
ev('wang_shufei_taifei','闰正月甲寅王淑妃获尊太妃',11,'甲寅，',None,[('王淑妃','明宗淑妃、获尊太妃者'),('帝','尊号时在位君主')],when='934年闰正月甲寅',note='复用王淑妃花见羞，不混933被杀司衣王氏；旧纪皇太妃称号差异并列。')
ev('shu_officials_urge_accession','蜀将吏劝孟知祥称帝',12,'蜀将吏','称帝。',[('知祥','被劝称帝的蜀王')],place='蜀',note='将吏未名，不将下一卷即位后任官名单冒充本段劝进署名。')
ev('meng_emperor_chengdu','闰正月己巳孟知祥在成都即皇帝位',12,'己巳，',None,[('知祥','即皇帝位者')],when='934年闰正月己巳',place='成都',note='此处称帝与此前唐册蜀王分录；新蜀世家闰正月国号蜀补，不提前记七月死亡。')
old='jiuwudaishi-045-934-leap-month';fu='jiuwudaishi-056-fu-yanchaos-death';newmin='xinwudaishi-068-jianzhou-revolt';newshu='xinwudaishi-064-meng-emperor'
def excerpt(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);return t[a:t.index(end,a)+len(end)]
def supp(code,source,start,end,text,n,relation='corroborates',note='按对应段落及主体补证；原字保留，电子本及纸本异文待核。'):
 claim('event','event_zztj_278_0934_'+code,'description',text,n,excerpt(source,start,end),note,source=source,relation=relation)
supp('min_troops_refuse_advance',newmin,'是歲，吳人攻建州，','得文傑乃進。','新闽世家同记吴攻建州、王延宗援军要求得到薛文杰才肯进兵。',8)
supp('xue_delivered_to_army',newmin,'鏻惜之不與，','送文傑軍中。','新闽世家记王延钧起初惜薛不交，其子王继鹏请求交军以纾难，后用槛车送军中。',8,relation='adds',note='新书明确君主与继鹏交军争议，主记太后继鹏哭诉及继鹏击笏；两书不同细节并列，不猜杀巫徐彦同盛韬。')
supp('xue_killed_by_troops',newmin,'文傑善數術，','臠食立盡。','新闽世家记押送两日即到，军士磔薛文杰于市，闽人投瓦石并脔食。',8,relation='adds')
supp('min_pardon_arrives_late',newmin,'明日，','已不及。','新闽世家补使者在翌日带来赦令，已经不及。',8,relation='adds')
supp('xue_cage_retrospective',newmin,'初，文傑為鏻造檻車，','首被其毒。','新闽世家同记薛文杰改制槛车并首先受其害。',8,note='初字追叙仍未定年月，不把造车与受害当同一天。')
for code in ['tang_jishizhong','chen_jishizhong']:
 supp(code,old,'以諫議大夫唐汭、','充樞密院直學士。','旧闵帝纪闰月癸卯段下记唐汭、陈乂并为给事中，充枢密院直学士。',9,relation='adds',note='旧本文任官是独立补证；随后明引通鉴夹注不可再算一份独立动机证据。')
supp('cao_empress_dowager',old,'丙午，','皇太后曹氏。','旧闵帝纪丙午明确册皇太后曹氏，核主书皇后为明宗曹后。',9)
supp('fu_yanchao_murder',old,'丁巳，安州奏，','廢朝一日。','旧闵帝纪闰月丁巳收到安州奏报：此月七日夜符彦超被王希全害，废朝一日。',10,relation='adds',note='丁巳是奏报日期，不能用作死亡日；此月七日夜与主己酉旦讨诛分别记。')
supp('fu_yanchao_murder',fu,'應順元年正月，','挾刃害之。','旧符彦超传作应顺元年正月，佛留即王希全与任货儿谋乱，假急递害符彦超。',10,relation='conflicts',note='本传正月与主闰月、旧纪闰月奏报有月份分歧；任货儿与主任驾儿同案同谋定位，异字保别名。')
supp('li_duan_suppresses_revolt',fu,'詰旦，','殺之，','旧符彦超传记次旦李端召州兵杀佛留等。',10,relation='conflicts',note='次旦顺序互证，但旧传承正月，不能覆盖主闰月己酉。')
claim('person',people['王希全'],'aliases','王希全小字佛留，掌符彦超财货。',10,'彥超廝養中有王希全者，小字佛留，粗知書計，委主貨財，','旧本传直载小字，作为检索别名；掌财岁久为背景，不编开始年月。',source=fu,relation='adds')
claim('person',people['任驾儿'],'aliases','任驾儿在旧符彦超传写作任货儿。',10,'因與任貨兒等謀亂','同符彦超被害、佛留同谋与李端平乱对应，保同人异文，非单凭繁简转换判断。',source=fu,relation='conflicts')
supp('wang_shufei_taifei',old,'甲寅，','皇太妃王氏。','旧闵帝纪甲寅册皇太妃王氏，主书称太妃；沿同一王淑妃。',11,relation='conflicts')
supp('meng_emperor_chengdu',newshu,'十一月，明宗崩。','國號蜀。','新蜀世家承明宗933年十一月崩，记明年闰正月孟知祥即帝位，国号蜀。',12,relation='adds',note='明年依前文长兴四年即934；不将新后段任官提早补成具名劝进。')
reviews={8:'浦城胜、围建州、发援、拒进索薛、驰报、哭诉击笏、押送预测加速、军杀与赦不及逐项分录。初改槛车未定年；徐恐拥濛是担忧非既成拥立，闻援将至不是已到；撤退追败、归罪斩张、贬官求好分。蒋为杨行密女婿明示，素善不当盟约。主盛韬不自动合新徐彦；新吴英与主吴勖另案不混。',9:'两任官分，唐汭从帝历幕、朱冯斥才为追叙不强定934；陈监唐为本段安排不建永久统属。主过疏与旧引通鉴迂疏待校，旧夹注不独立确证。丙午皇后据旧册曹氏识别已有明宗后，非闵帝生母夏氏。',10:'谋附吴未实现、假急递夜杀、冒符令召杀诸将、己酉旦李端平乱分。旧纪丁巳为奏日、此月七日夜为所报死亡时；旧本传正月与主闰月分歧保。王希全小字佛留；任货儿同案对照主任驾儿为异名，不新造两人。李端加安州副使消歧，未名诸将党众不编。',11:'王淑妃花见羞沿已有主体，甲寅获太妃；旧皇太妃称号并列，不混933司衣王氏。',12:'劝进未名将吏与己巳成都即位分；旧新蜀史检索，新闰正月国号蜀补。旧卷136电子文字王稱我帝疑讹且注明原传缺由册府采补，未选作独立日期确证；七月死亡及后续任官待主线。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(8,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(8,13)],next_paragraph='zztj-v279-y0934-p001',next_volume=279,next_year=934,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷278连续934年第8—12正文段，原102—106行；本卷934的12段至此处理，卷279同年77段仍待录，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(8,13)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
