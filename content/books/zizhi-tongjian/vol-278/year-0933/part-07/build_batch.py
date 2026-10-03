# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 933 paragraphs 50–56."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
# The final ledger item is the next imperial section heading, not a 933 event.
raw_lines=(ROOT/'resources/derived/tongjian/278.txt').read_text().splitlines()
assert raw_lines[91:94]==['潞王上','◎','清泰元年甲午，公元九三四年']
assert ledger[56]['text']=='潞王上' and ledger[56]['source_line']==92 and not ledger[56]['event_keys']
ledger[56].update(kind='section_heading',status='excluded_non_body_verified',review='潞王上为下一帝纪节标题，后接934年年题；保原ID及行号，不生成历史事实，不计933正文。')
boundaries=json.loads((YEAR/'boundaries.json').read_text())
boundaries.update(body_source_lines=[36,91],body_paragraphs=56,ledger_source_lines=[36,92],ledger_records=57)
if not any(x['source_line']==92 for x in boundaries['excluded_non_body']):boundaries['excluded_non_body'].insert(0,dict(paragraph_id=ledger[56]['id'],source_line=92,text='潞王上',reason=ledger[56]['review']))
(YEAR/'boundaries.json').write_text(json.dumps(boundaries,ensure_ascii=False,indent=2)+'\n')
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 58))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'1ab64add','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [('tongjian-278-933-aftermath',YEAR/'part-05/sources/library/tongjian-278-933-aftermath','ba163460','司马光等'),('jiuwudaishi-045-conghou-succession',YEAR/'part-06/sources/library/jiuwudaishi-045-conghou-succession','8487026c','薛居正等'),('xinwudaishi-007-conghou-succession',YEAR/'part-06/sources/library/xinwudaishi-007-conghou-succession','8487026c','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-933-aftermath','tongjian-278-933-yearend']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0933-p050-p056',
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
for n in range(50, 57):
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
        citation = f'卷278·长兴四年（933）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0933_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从厚','闵帝':'李从厚','从荣':'李从荣','秦王':'李从荣','洪实':'朱洪实','元瓘':'钱传瓘','钱元珦':'钱传珦','元珦':'钱传珦','仁诠':'仰仁诠','闽主':'王延钧','希声':'马希声','希范':'马希范','希旺':'马希旺','希旦':'马希旺','王氏':'王氏（司衣）'}
NEW_ALIASES={'王氏（司衣）':['王氏（司衣乳母）'],'宋令询':['宋令詢'],'仰仁诠':['仰仁詮'],'马希旺':['馬希旺'],'袁德妃':['袁氏（马希声母）'],'陈氏（马希范母）':['陳氏（馬希範母）']}

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
    if when is None:when='933年十二月条下；确日未独载'
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



# Consecutive body paragraphs 50–56; last year item 57 is an excluded heading.
ev('palace_wang_defends_qin','司衣王氏向朱洪实妻评论秦王，认为以大逆论为厚诬',50,'秦王从荣既死，','惜哉！”',[('王氏（司衣）','与朱洪实妻谈论秦王者'),('从荣','被评论的死去秦王'),('洪实','被指最受秦王恩者')],when='933年十二月辛亥赐死前谈话；未独日',place='后唐宫廷',note='与朱妻谈，朱本人非在场；其评论不是网站裁定秦王法律责任。朱妻未名不编姓名。')
ev('hongshi_kang_accuse_palace_wang','朱洪实、康义诚向闵帝告司衣王氏言论，并指其私秦王、窥宫事',50,'洪实闻之，','为之诇宫中事，',[('洪实','闻言畏惧并告者'),('康义诚','一同向帝告者'),('闵帝','受告君主'),('王氏（司衣）','被指私秦王窥宫者')],when='933年十二月辛亥赐死前；未独日',note='私通及诇事在主为告言层，新后妃传另史述；不因被告自动建立确定配偶关系。')
ev('palace_wang_execution','十二月辛亥闵帝赐司衣王氏死',50,'辛亥，','赐王氏死。',[('闵帝','赐死君主'),('王氏（司衣）','被赐死者')],when='933年十二月辛亥',place='后唐宫廷',note='司衣王氏不同王淑妃；淑妃此时被疑而非同日被赐死。')
ev('conghou_suspects_wang_consort','司衣王氏案连王淑妃，闵帝因而怀疑淑妃',50,'事连王淑妃，',None,[('王淑妃','受牵连和猜疑者'),('闵帝','因案生疑者')],when='933年十二月司衣案后；未独日',note='素厚秦王为主解释，不等王淑妃本段谋反或被杀。')
ev('song_lingxun_cizhou','十二月丙辰宋令询由天雄左都押牙出任磁州刺史',51,'丙辰，','为磁州刺史。',[('宋令询','旧天雄左都押牙、出刺磁州者'),('闵帝','任外镇时在位君主')],when='933年十二月丙辰',place='磁州',note='任命不当已当日到磁州；旧纪元从都押衙与主左都押牙职名并列。')
ev('zhu_excludes_conghou_old_staff','史叙朱弘昭欲专政、不欲宋令询等旧人在帝侧而使之出',51,'硃弘昭以诛秦王','故出之。',[('朱弘昭','史称欲专朝政、排旧人者'),('宋令询','长期亲信而出镇者'),('闵帝','宋长期侍从的君主')],note='史叙动机与任命结果分，未列其他旧人不凭空加被逐名单。')
ev('conghou_displeased_song_departure','闵帝对宋令询出镇不悦而无可奈何',51,'帝不悦',None,[('闵帝','不悦而无可奈何者')],note='不悦为史述，未给召回命令，不造宋已抗命。')
ev('meng_predicts_court_disorder','孟知祥闻明宗死，称宋王幼弱、掌政者胥史小人，预料其乱',52,'孟知祥闻',None,[('孟知祥','闻明宗死并评新廷者'),('李从厚','被评价的宋王')],place='孟知祥幕府',note='对僚佐的评语和未来推测，不写此时宋王已经被推翻或天下已乱。')
ev('conghou_chongxing_audience','十二月辛未闵帝始御中兴殿',53,'辛未，','帝始御中兴殿。',[('闵帝','御中兴殿者')],when='933年十二月辛未',place='中兴殿')
ev('conghou_reads_government_classics','闵帝终易月丧制后，召学士读贞观政要、太宗实录',53,'帝自终','有致治之志；',[('闵帝','召学士读书、欲致治者')],when='933年十二月终易月制后附记；确日未独载',note='有志为史述，读书不等已经实现治理目标；书名是所读对象不新增这两书为本站基础出处。')
ev('conghou_softness_assessment','史叙闵帝不知治要、宽柔少断',53,'然不知其要，','宽柔少断。',[('闵帝','受史家治政评价者')],year=None,when='闵帝初政概述；起讫未独载',note='史家评价保为评价，不当现代人格诊断或单日政策。')
ev('li_yu_private_concern','李愚私向同列忧帝延访少及宰臣、位高责重，同列不敢应',53,'李愚私谓','众惕息不敢应。',[('李愚','私忧同列的宰相'),('闵帝','被忧议的君主')],note='同列未名不造具体名单，不当公开上谏或帝已答。')
ev('qian_yuanxiang_defies_requests','史叙明州钱元珦因所请不获，屡上书悖慢',53,'顺化节度使','辄上书悖慢。',[('钱元珦','顺化节度使、同平章事、判明州、上书者')],year=None,when='钱元珦在明州的持续行为概述；起讫未独载',place='明州、吴越王府',note='元珦沿已录钱传珦，吴越传改元避讳名模式识同主体，确切转名年月未核不新造改名日；各请内容不明，不编次数。')
ev('qian_yuanxiang_burns_official','钱元珦曾怒一吏，将其置铁床炙',53,'尝怒一吏，','臭满城郭。',[('钱元珦','炙吏者')],year=None,when='尝所追述的明州虐吏；具体年月未知',place='明州',note='吏未名不新造名字，不凭臭满城郭推受害者确切死亡年月。')
ev('qian_sends_yang_renquan','吴王钱元瓘遣仰仁诠至明州召钱元珦',53,'吴王元瓘','明州召之，',[('元瓘','遣牙将召人者'),('仁诠','受遣牙将'),('元珦','被召者')],place='明州、吴越',note='元瓘沿钱传瓘，元珦沿钱传珦；两人名不同，不误用元瓘自召。')
ev('yang_refuses_defensive_preparation','仰仁诠左右建议为难制的钱元珦预作准备，仰不从，常服入听事',53,'仁诠左右','常服径造听事。',[('仁诠','拒预备并常服赴厅者'),('元珦','左右称难制的被召者')],place='明州听事',note='左右未名，勸备不等实际另调围攻兵；元珦难制是左右担忧层。')
ev('qian_returns_qiantang','钱元珦见仰仁诠而惧，返回钱塘并被幽于别第',53,'元珦见仁诠至，','幽于别第。',[('元珦','返钱塘被幽者'),('仁诠','来召之牙将')],place='明州、钱塘别第',note='主股忄栗为拆字，校本股慄释恐惧；幽别第不当处死，无独日不附辛未确日。')
claim('person',people['仰仁诠'],'description','仰仁诠为湖州人。',53,'仁诠，湖州人也。','史载原籍，不未经验证给现代点。')
ev('fuzhou_changle_prefecture','闽主改福州为长乐府',54,'闽主改',None,[('闽主','改府名者')],place='福州、长乐府',note='行政名更改不当新筑全城或迁都；本条未独日。')
claim('person',people['王仁达'] if '王仁达' in people else person('王仁达',55,'有擒王延禀之功的亲从都指挥使',span(55,'亲从都指挥使','有擒王延禀之功，')),'description','本段记王仁达为亲从都指挥使，有擒王延禀之功。',55,'亲从都指挥使王仁达有擒王延禀之功，','之前931擒事已录，当前只补身份与功述，不重复新造933擒战事件。')
ev('min_fears_wang_renda_afterlife','闽主私言能御王仁达而非少主之臣',55,'闽主恶之，','非少主臣也。”',[('闽主','忌惮并私评者'),('王仁达','被认为不宜遗少主者')],year=None,when='王仁达遇害前私评追述；具体日期未知',note='智余及非少主臣是闽主看法，不写王已经叛变、已拥立少主或少主此时当政。')
ev('wang_renda_clan_execution','通鉴933年条记闽主诬王仁达以叛而族诛',55,'至是，',None,[('闽主','诬叛并族诛者'),('王仁达','被诬叛族诛者')],place='闽',note='主以叛属诬，不当确有叛乱；新闽世家将相近杀事置龙启三年段，其年代层另列，不硬断两书记同年。')
ev('ma_brothers_same_birthday','史载马希声、马希范同日出生',56,'初，','马希声、希范同日生。',[('希声','同日出生的兄弟之一'),('希范','同日出生的兄弟之一')],year=None,when='初所追述的出生；生年本段未载',note='两母不同，不称双胞胎；不把编年933当生年或自行判当日先后时辰。')
relationship('袁德妃','希声','母亲',56,'希声母曰袁德妃，','袁德妃→马希声为母亲，本站方向前者是后者母；不造反向重复边。')
relationship('陈氏（马希范母）','希范','母亲',56,'希范母曰陈氏。','陈氏→马希范母亲；限定母名，避免裸陈氏与前晚唐魏国夫人合。')
relationship('袁德妃','希旺','母亲',56,'希声母弟希旺','母弟为同母弟，袁是希声母，故同袁母；不当希范母陈。')
relationship('希旺','希声','弟弟',56,'希声母弟希旺','马希旺→马希声为弟弟，有母弟明文。与另一希范同日生不外推三者时辰长幼。')
ev('ma_xifan_resentment','马希范怨马希声先立，嗣位后不礼袁德妃',56,'希范怨','不礼于袁德妃。',[('希范','史称怨及不礼者'),('希声','先立的兄弟'),('袁德妃','受到不礼者')],year=None,when='马希范嗣位后追叙；具体年月未独载',note='主先立不止，校本先立不让异字保；主政治不满的解释不当希声必须让位希范的制度定论。')
ev('ma_xifan_rebukes_xiwang','马希范多次谴责亲从都指挥使马希旺',56,'希声母弟','希范多谴责之。',[('希旺','亲从都指挥使、被谴责者'),('希范','多次谴责者')],year=None,when='希范嗣位后、希旺被解军职前追叙；具体日期未知',note='多次无各日，不编每次事件；当前官职不独推某月新授。')
ev('yuan_petitions_xiwang_retirement','袁德妃请求纳马希旺官为道士，未获允许',56,'袁德妃请','不许，',[('袁德妃','请解子官为道士者'),('希旺','所请纳官者'),('希范','不许请求的在位者')],year=None,when='希范嗣位后追叙；具体年月未知',note='主希旦两处与同段希旺不一致，校本均希旺，规范同人；拒请不当已经当道士，不能混新世家马希振弃官为道士。')
ev('ma_xiwang_isolated','马希旺被解军职，居竹屋草门，不得参加兄弟宴集',56,'解其军职，','不得预兄弟燕集。',[('希旺','被解军职并隔离者'),('希范','在位处置者')],year=None,when='纳官为道士请不获后追叙；具体年月未知',note='不预宴集不是已被处死或全体兄弟被禁锢；未载地名不编具体道观。')
ev('yuan_defei_dies','追叙袁德妃去世',56,'德妃卒，','德妃卒，',[('袁德妃','追叙去世者')],year=None,when='初段追叙，希旺去世前；具体年月未知',note='整个初段追述，无独载卒年，不把附933当确定卒年。')
ev('ma_xiwang_dies_after_mother','追叙马希旺在母死后忧愤而卒',56,'德妃卒，',None,[('袁德妃','先去世的母亲'),('希旺','母死后忧愤去世者')],year=None,when='初段追叙，袁德妃卒后；具体年月未知',note='主末作希旦，校本希旺，保原文异字；忧愤为史家解释，不作现代医学死因。')
old='jiuwudaishi-045-conghou-succession';new='xinwudaishi-007-conghou-succession';song='jiuwudaishi-066-song-lingxun';palace='xinwudaishi-015-palace-wang';ma='xinwudaishi-066-ma-birth';renda='xinwudaishi-068-wang-renda-death';collation='tongjian-278-933-yearend-collation'
def excerpt(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);return t[a:t.index(end,a)+len(end)]
def supp(code,source,start,end,text,n,relation='corroborates',note='对应主段书证核对，保各书原字；源后文未到主线不提前派生事实。'):
 claim('event','event_zztj_278_0933_'+code,'description',text,n,excerpt(source,start,end),note,source=source,relation=relation)
supp('palace_wang_execution',old,'辛亥，賜司衣王氏死','坐秦王事也。','旧闵帝纪同辛亥记赐司衣王氏死，坐秦王事。',50)
supp('palace_wang_execution',new,'辛亥，殺司衣王氏','辛亥，殺司衣王氏。','新闵帝纪同辛亥杀司衣王氏。',50)
claim('person',people['王氏（司衣）'],'description','新唐家人传记司衣王氏是李从益乳母，曾教儿求见秦王，随儿往来秦府。',50,'從益乳母司衣王氏，見明宗已老而秦王握兵，心欲自託為後計，乃曰：「兒思秦王。」是時從益已四歲，又數教從益自言求見秦王。明宗遣乳嫗將兒往來秦府，','这是从荣死前背景，年月未独；与王淑妃养母为不同人不同关系，儿思秦王是所教言不当心理实证。',source=palace,relation='adds')
relationship('王氏（司衣）','李从益','乳母',50,'從益乳母司衣王氏','乳母不同生母或养母；王淑妃另已记养母，当前司衣王氏另人，关系年月未知。',source=palace)
claim('person',people['王氏（司衣）'],'description','新唐家人传史述司衣王氏与李从荣私通，受令察宫中动静。',50,'遂與從榮私通，從榮因使王氏伺察宮中動靜。','主为朱康告言、新传为叙述层，并列不抹书层；不据私通建立妻子关系。',source=palace,relation='adds')
supp('song_lingxun_cizhou',old,'丙辰，以天雄軍節度判官','元從都押衙宋令詢為磁州刺史。','旧闵帝纪同丙辰记元从都押衙宋令询为磁州刺史，主前衔为天雄左都押牙，原称并列。',51,relation='adds')
supp('zhu_excludes_conghou_old_staff',song,'及閔帝嗣位，','乃出為磁州刺史。','旧宋令询传记朱冯用事，不欲闵帝旧臣在侧，出令询为磁州刺史。',51,relation='adds')
claim('person',people['宋令询'],'description','旧传记宋令询籍贯不详，闵帝在藩补客将，长兴中迁都押衙，深受委任。',51,'宋令詢，不知何許人也。閔帝在藩時，補為客將，知書樂善，動皆由禮。長興中，閔帝連典大藩，遷為都押衙，參輔閫政，甚有時譽，閔帝深委之。','过往任职背景，不当933新补客将；传后934帝死自经不提前派生。',source=song,relation='adds')
supp('conghou_chongxing_audience',old,'辛未，帝御中興殿，','命徹之。','旧闵帝纪同辛未记御中兴殿，冯道进酒，帝以居丧沉痛命撤。',53,relation='adds')
supp('qian_yuanxiang_defies_requests',collation,'順化節度使、','輒上書悖慢。','同书音注对顺化军名提出遥领楚州节而镇明州的解释，不能仅据节号当控制吴楚州。',53,relation='adds',note='这是胡注地理推释并非独立旧史来源；未把注转引专书列作新基础出处，不给现代疆域点。')
supp('qian_returns_qiantang',collation,'元珦見仁詮至，','幽於別第。','同书校读作股慄，意为惧而返钱塘被幽别第，原TXT股忄栗拆字保。',53,relation='adds')
supp('wang_renda_clan_execution',renda,'龍啟三年，','卒誣以罪殺之。','新闽世家在龙启三年改永和段下记王仁达因功典亲兵、被忌而诬罪杀；主置933年，编排年代不同并列保。',55,relation='conflicts',note='龙启三年通常对应935，主长兴四年933；保不同编排，不硬说两书证实同日，不据新段补933已改永和。')
supp('ma_brothers_same_birthday',ma,'希範字寶規，','希振棄官為道士，居于家。','新楚世家也记希声希范同日生，希声以母袁夫人宠得立，嫡长希振弃官为道士。',56,relation='adds',note='两母不同不可称双胞胎；新希振主动为道士不同主希旺请纳官不许，不混人或把过往挂933新生事件。')
supp('ma_xifan_resentment',collation,'希範怨希聲','未當讓希範也。}}','同书正文作先立不让，注指出长幼序应让希振而未当让希范；主先立不止字异保。',56,relation='conflicts',note='同书版本和注释层，非另一史书独立确证；保政治解释分歧，不当希范制度上必应继长。')
supp('yuan_petitions_xiwang_retirement',collation,'袁德妃請納希旺','希旺憂憤而卒。','同书校版纳官及末卒两处均作希旺，主此两处作希旦，依同段同人物连续性校读为马希旺。',56,relation='conflicts',note='原TXT希旦不改字；显示马希旺，不另建未经核证的希旦实体或裸异名别名。')
next(x for x in B['people'] if x['key']==people['王氏（司衣）'])['death_year']=933
claim('person',people['王氏（司衣）'],'death_year','司衣王氏于933年十二月辛亥被赐死。',50,'辛亥，赐王氏死。','主旧新均明确同日；不得把王淑妃死年同步改933。')
reviews={50:'王司衣与淑妃分人。朱妻未名不猜；大逆厚诬是王议、私通窥事主为朱康告，新后妃叙述并列。司衣乳母与淑妃养母区分；原私通不作夫妻关系。辛亥赐死主旧新同日；淑妃受疑而未死。',51:'丙辰宋出磁州与朱专政动机、帝不悦分。旧元从押衙主左押牙原称并列；旧宋传藩任背景补，未知籍贯不猜，后934自经不提前录。',52:'孟闻帝殂后对宋王新廷的批评与预测，不当已证宋王被推翻、已全国乱；胥史小人为他的评价。',53:'辛未御殿、易月后读书、史评少断、李私忧同列分；旧同日撤酒补，不编学士姓名。钱传瓘及传珦沿已有钱氏主体，主元名、转名起日未定；虐吏尝追叙年未知，召仰、不备、常服、返幽分，不当辛未已明州战。胡注顺化遥领是推释非原TXT新史实；股忄栗拆字保。',54:'福州改长乐府为行政名，不当筑城迁都，未独日不硬干支。',55:'王功擒延禀已931不重复事件；忌惮言为王延钧私评、诬叛族诛非确叛。新闽世家置龙启三年段，主置933，年代异说保而不硬改旧主体死亡年。',56:'初段全为过往追叙，出生、嗣位后谴与隔离、袁及希旺死年月不独，均未定年；两母生同日非双胞胎。母弟有方向弟弟与母亲，未推希范时辰长幼。主先立不止校先立不让保；希旦两处校希旺，保原文而不盲建新人；新希振为道士不同本段希旺请未许，异书解释分层。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(50,57):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
context=YEAR/'part-02/sources/context/qian-yuanliao-name/response.json'
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=933,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(50,57)],next_paragraph='zztj-v278-y0934-p001',next_volume=278,next_year=934,supplements=supplements,source_contexts=[dict(file=os.path.relpath(context,P/'sources'),sha256=hashlib.sha256(context.read_bytes()).hexdigest(),note='固定音注版2115814完整原始API响应沿part-02归档，校版同书不算独立他书。')],excluded_non_body=[Q[57]['id']],coverage='卷278连续933年第50—56正文段、原85—91行；司衣案、初政、明州、闽府名及王仁达、楚兄弟。第57潞王上结构标题排除；933全正文处理完后仍须年度公开覆盖审计。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(50,57)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
