# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 934 paragraphs 1–4."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,78))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'570df7a6','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [('xinwudaishi-064-meng-emperor',YEAR.parent.parent/'vol-278/year-0934/part-02/sources/library/xinwudaishi-064-meng-emperor','a2ffb86d','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-february']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0934-p001-p004',
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
lines = (ROOT / 'resources/derived/tongjian/279.txt').read_text().splitlines()
for n in range(1, 5):
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
        citation = f'卷279·清泰元年（934；二月闵帝应顺元年）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0934_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'蜀主':'孟知祥','吴主':'杨溥','知诰':'李昪','徐知诰':'李昪','宗':'周宗','齐丘':'宋齐丘','潞王':'李从珂','从珂':'李从珂','帝':'李从厚','朱':'朱弘昭','冯':'冯赟'}
NEW_ALIASES={'李建勋':['李建勳']}

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
    if when is None:when='934年二月条下；确日未独载'
    key = 'event_zztj_279_0934_' + code
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
        edge = 'participation_zztj_279_0934_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_279_0934_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




# Consecutive paragraphs 1–4; retrospective and indeterminate later passages are undated.
ev('zhao_jiliang_chancellor','二月癸酉孟知祥授赵季良司空兼门下侍郎、同平章事',1,'二月，','领节度使如故。',[('蜀主','任官君主'),('赵季良','武泰节度使、获授宰辅职者')],when='934年二月癸酉',place='蜀',note='领原武泰节度使如故为保留，不新建同日首次授武泰。')
ev('zhou_opposes_capital_move','周宗向徐知诰陈述迁都劳费并违众心',2,'吴人多不欲迁都者，','且违众心。”',[('周宗','都押牙、陈述迁都不便者'),('知诰','受劝者')],note='吴人多不欲迁为主书概述；主上西迁公复须东行是周宗对拟议行程的论证，不当迁都已完成。')
ev('wu_halts_capital_move','二月丙子杨溥遣宋齐丘至金陵，谕徐知诰罢迁都',2,'丙子，','罢迁都。',[('吴主','遣使罢迁都的君主'),('齐丘','奉命往金陵者'),('知诰','被谕罢迁都者')],when='934年二月丙子',place='金陵',note='罢迁都与前卷虚府待吴相接；未迁成，不填吴主已到金陵。')
ev('xu_waits_for_succession_retrospective','追叙徐知诰有传禅之志，因吴主无失德而欲待嗣君',2,'先是，','欲待嗣君；',[('知诰','有禅代意愿而欲等待者'),('吴主','被认为无失德的现任君主')],year=None,when='先是追叙；谋划等待嗣君的具体起讫未载',note='欲待嗣君只是意愿，不记杨溥已经死、立嗣或传禅。')
ev('song_agrees_waiting','宋齐丘同意徐知诰等待嗣君的想法',2,'先是，','亦以为然。',[('齐丘','赞同等待想法者'),('知诰','谋议对象')],year=None,when='先是追叙；赞同谋议年月未知',note='亦以为然承欲待嗣君，不当宋齐丘已拥立新帝。')
ev('xu_laments_age','徐知诰临镜镊白髭，感叹国家安而自己已老',2,'一旦，','奈何？”',[('知诰','临镜感叹者')],year=None,when='先是追叙中一旦；确年月未载',note='主国家安与新功业已就为引语异文；未载年龄不倒推出生年。')
ev('zhou_requests_abdication_lobby','周宗请往江都，以传禅试探吴主并告宋齐丘',2,'周宗知其意，','且告齐丘。',[('周宗','请求游说传禅者'),('吴主','拟试探的君主'),('齐丘','拟告知的对象')],year=None,when='先是追叙；周宗请往江都的年月未载',place='江都（拟往）',note='请如、微以讽为请求和游说意图；新书说驰诣广陵见齐丘为执行记载补证，主句本身不当已获吴主禅让承诺。')
ev('song_resents_zhou_priority','史叙宋齐丘因周宗先己而心疾之',2,'齐丘以宗先己，','心疾之，',[('齐丘','因先后次序而生嫌者'),('宗','被嫌者')],year=None,when='先是追叙；确年月未载',note='心疾为史家动机叙述，不造永久敌对关系。')
ev('song_letter_opposes_abdication','宋齐丘驰使送手书至金陵，谏禅代时机未可',2,'遣使驰诣金陵，','知诰愕然。',[('齐丘','手书切谏者'),('知诰','接书愕然者')],year=None,when='先是追叙中周宗请行后；确年月未载',place='金陵',note='未名使者不造人；天时人事未可为宋谏辞，非历算或独立已证事实。')
ev('song_requests_zhou_execution','宋齐丘数日后到，要求斩周宗以谢吴主',2,'后数日，','请斩宗以谢吴主，',[('齐丘','到达并请斩者'),('宗','被请求处决者'),('吴主','拟致歉的君主')],year=None,when='先是追叙；驰书后数日，确年月未知',note='请斩与下句实际贬职分开，不填写周宗已被处决。')
ev('zhou_demoted_chizhou','周宗被黜为池州副使',2,'乃黜宗','池州副使。',[('宗','被黜者')],year=None,when='先是追叙中宋齐丘请斩后；确年月未载',place='池州',note='主书副使与新书刺史不同官名并列；不当同时新任两职。主省主语不擅指定正式诏发者。')
ev('li_xu_advocate_xu_accession','李建勋、徐玠等屡陈徐知诰功业，劝其早从民望',2,'久之，','宜早从民望，',[('李建勋','节度副使、屡陈功业者'),('徐玠','行军司马、屡陈功业者'),('知诰','受劝者')],year=None,when='久之所引后续；确年月与是否同年未载',note='久之不强定934二月；宜早是劝进，不写已经禅代。等未列姓名不扩大参与名单。')
ev('zhou_recalled_douyaya','周宗后来被召回复任都押牙',2,'久之，','召宗复为都押牙。',[('宗','被召回复职者')],year=None,when='久之所引后续；确年月未载',note='复为都押牙不是节度使，未强定本年；省主语不臆补召令签发人。')
ev('xu_distances_song','徐知诰由上述事疏远宋齐丘',2,'知诰由是','疏齐丘。',[('知诰','疏远者'),('齐丘','被疏远者')],year=None,when='久之复周宗后概述；具体起讫未载',note='疏是政治交往变化，未当已罢齐丘全部官职，不新造永久仇敌边。')
ev('zhu_feng_plan_three_transfers','朱弘昭、冯赟不欲石敬瑭久在太原，并欲召孟汉琼',3,'硃弘昭、','且欲召孟汉琼，',[('朱','筹划调动者'),('冯','筹划调动者'),('石敬瑭','被筹划调离者'),('孟汉琼','被筹划召回者')],note='欲召是执政意图，不当孟汉琼在本句已经回京或石已离太原。')
ev('fan_ordered_tianxiong','二月己卯范延光获令由成德徙天雄、代孟汉琼',3,'己卯，','代汉琼；',[('范延光','原成德节度使、获令徙天雄者'),('孟汉琼','拟被替代者')],when='934年二月己卯',place='天雄军',note='任命和抵任分；旧权知邺都留守为权摄名目异文，不写当日已经交接。')
ev('congke_ordered_hedong','二月己卯李从珂获令徙河东、兼北都留守',3,'徙潞王','兼北都留守；',[('潞王','原凤翔节度、获令徙河东者')],when='934年二月己卯',place='河东、北都',note='旧权北京留守与主河东兼北都职名层次并列；下一段拒命尚未录，不先当已到太原。')
ev('shi_ordered_chengde','二月己卯石敬瑭获令由河东徙成德',3,'徙石敬瑭','成德节度使。',[('石敬瑭','获令徙成德者')],when='934年二月己卯',place='成德军',note='只记调令，不当已离任抵镇；旧权知镇州军州事为权摄层补证。')
ev('transfers_by_xuan_without_edict','三镇调动不降制书，各由使臣持宣监送赴镇',3,'皆不降制书，',None,[('范延光','宣命监送对象'),('潞王','宣命监送对象'),('石敬瑭','宣命监送对象')],when='934年二月己卯调动条下',note='各遣监送为朝廷执行安排，不等三人均已顺利到镇；不虚拟使臣姓名。')
ev('wu_orders_xu_return_office','吴主诏徐知诰返回府舍',4,'吴主诏','还府舍。',[('吴主','下诏者'),('知诰','被诏返回者')],place='金陵',note='此前迁私第虚府待吴与此返回府舍前后不同；诏令与己丑实际复入分录。')
ev('jinling_fire_jiashen','二月甲申金陵大火',4,'甲申，','金陵大火；',[],when='934年二月甲申',place='金陵',note='无原文明示火因、损失数或纵火者，不造参与人。新吴世家闰正月火与本段二月时间异说保留。')
ev('jinling_fire_yiyou','二月乙酉金陵再次失火',4,'乙酉，','又火。',[],when='934年二月乙酉',place='金陵',note='又火按第二次明日记录，不把新闰正月一条机械对应到其中某一天。')
ev('xu_musters_guard_after_fire','徐知诰疑有变，勒兵自卫',4,'知诰疑有变，','勒兵自卫。',[('知诰','怀疑变故而勒兵自卫者')],place='金陵',note='疑有变为当事人猜疑，不填写实际已经发生政变，也不指定纵火者。')
ev('xu_returns_office_jichou','二月己丑徐知诰复入府舍',4,'己丑，',None,[('知诰','实际复入府舍者')],when='934年二月己丑',place='金陵府舍',note='府舍为此前虚出待吴的办公居处，不把复入当已称帝或占吴宫。')
old='jiuwudaishi-045-934-transfers';zhou='xinwudaishi-062-zhou-zong';fire='xinwudaishi-061-jinling-fire';shu='xinwudaishi-064-meng-emperor'
def excerpt(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);return t[a:t.index(end,a)+len(end)]
def supp(code,source,start,end,text,n,relation='corroborates',note='回查同一人及行动，繁简异字保原引用；电子本与纸本待核。'):
 claim('event','event_zztj_279_0934_'+code,'description',text,n,excerpt(source,start,end),note,source=source,relation=relation)
supp('zhao_jiliang_chancellor',shu,'以趙季良','平章事，','新蜀世家同记孟知祥授赵季良司空、同中书门下平章事。',1,note='新置称帝后相邻叙未独任命日，主二月癸酉明确；不倒写新本身也载癸酉。')
supp('xu_laments_age',zhou,'昪照鑑','奈何？','新南唐世家记徐知诰照镜见白须，叹功业已就而自己已老。',2,relation='conflicts',note='主国家安与新功业已就引语异文并列；两书均未独载此事确年，不强定934。')
supp('zhou_requests_abdication_lobby',zhou,'宗知其意，','謀禪代。','新南唐世家记周宗驰往广陵见宋齐丘，谋禅代。',2,relation='adds',note='广陵与江都地名对应；新明确实际驰见，主请如及微讽是另一细节，未载吴主承诺不补。')
supp('song_requests_zhou_execution',zhou,'齊丘以為未可，','以謝吳人，','新南唐世家同记宋齐丘认为未可，要求斩周宗以谢吴人。',2,note='请斩不是执行斩杀，不给周宗死亡年。')
supp('zhou_demoted_chizhou',zhou,'昪黜宗','池州刺史。','新南唐世家记徐知诰黜周宗为池州刺史，与主池州副使官名不同。',2,relation='conflicts',note='保留官名异说；主记副使、新记刺史，不压成两次独立任命，不强定日期。')
supp('congke_ordered_hedong',old,'是日，宣授鳳翔','權北京留守；','旧闵帝纪二月己卯同日宣授李从珂权北京留守。',3,relation='adds',note='旧权摄与主徙河东兼北都职名层次保留；同日宣授不当从珂已经赴任。')
supp('shi_ordered_chengde',old,'以北京留守石敬瑭','權知鎮州軍州事；','旧闵帝纪同己卯令石敬瑭权知镇州军州事。',3,relation='adds')
supp('fan_ordered_tianxiong',old,'以鎮州範延光','權知鄴都留守事；','旧闵帝纪同己卯令范延光权知邺都留守事，主记徙天雄代孟汉琼。',3,relation='adds')
supp('jinling_fire_jiashen',fire,'六年閏正月，','罷建都，','新吴世家大和六年写闰正月金陵火、罢建都，与主二月火、此前罢迁都时序不同。',4,relation='conflicts',note='前文二年太子、三年金陵尹、四年东海王、五年建都衔接，六年为934；只保新闰正月火与罢建都，不强对应甲申或乙酉，不提前录同段杨濛废徙。')
reviews={1:'癸酉赵季良宰辅任命与领武泰如故分；新蜀世家补司空同平章而未独日，不给其也编癸酉。',2:'迁都反对与丙子吴谕罢分；先是长有传禅志、待嗣、宋然、镜叹、周请行、宋嫉书谏请斩与黜周均追叙未定年。久之李徐劝、召周、疏宋未给确年不硬塞本年。新副使/刺史、镜叹国家安/功业就异文并列，未当已传禅或斩周。',3:'朱冯动机、己卯范潞石三调令与持宣监送无制书分；旧权北京/镇州/邺都对应层次保留，宣授不等已到任；孟欲召不当已归。下一段拒命及讨伐待录。',4:'吴诏还府、甲申大火、乙酉又火、疑变勒兵、己丑复入逐项分。无火因损失及具名纵火者不编；新吴六年闰正月火与主二月异说、罢建都先后差异保留，不机械绑定某次火。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,5):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,5)],next_paragraph='zztj-v279-y0934-p005',next_volume=279,next_year=934,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷279连续934年第1—4正文段，原6—9行；第5段凤翔拒命与西征长段仍待处理。本年跨卷89正文段。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,5)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
