# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 280, year 936 paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,71))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'6a17b2b9','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [
 ('xinwudaishi-068-jipeng-name',ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-04/sources/library/xinwudaishi-068-jipeng-name','dcde85d9','欧阳修'),
 ('xinwudaishi-055-sikong-duties',ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-04/sources/library/xinwudaishi-055-sikong-duties','dcde85d9','欧阳修'),
 ('xinwudaishi-062-jing-name',ROOT/'content/books/zizhi-tongjian/vol-272/year-0923/part-09/sources/library/xinwudaishi-062-jing-name','83be3260','欧阳修'),
 ('tongjian-277-931-may',ROOT/'content/books/zizhi-tongjian/vol-277/year-0931/part-03/sources/library/tongjian-277-931-may','52e45d2f','司马光等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-280-936-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v280-y0936-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'xinwudaishi-056-lv-qi-peace':'卷56·吕琦传（对契丹和议）','xinwudaishi-055-sikong-duties':'卷55·马胤孙传（司空职掌议论）','songshi-483-sun-guangxian':'卷483·孙光宪传','xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/280.txt').read_text().splitlines()
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
for revision in sorted((ROOT/'content/revisions').glob('*/aliases.json')):
    if not (revision.parent/'publication.json').exists():continue
    for corrected in json.loads(revision.read_text()).get('people',[]):
        if corrected['name'] in registry:registry[corrected['name']]=dict(registry[corrected['name']],aliases=corrected['after'])
for name,extra in [('荝剌',['荝刺']),('耶律倍',['李赞华','李贊華'])]:
    if name in registry:registry[name]=dict(registry[name],aliases=list(dict.fromkeys(registry[name]['aliases']+extra)))
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'xinwudaishi-056-lv-qi-peace':'卷56·吕琦传（对契丹和议）','xinwudaishi-055-sikong-duties':'卷55·马胤孙传（司空职掌议论）','songshi-483-sun-guangxian':'卷483·孙光宪传','xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '正月条下' if n<=3 else '三月条下及附载背景'
        citation = f'卷280·后唐清泰三年（936；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_280_0936_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_ALIASES={}

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=936, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='936年'+('正月' if n<=3 else '三月')+'条下；确日未独载'
    key = 'event_zztj_280_0936_' + code
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
        edge = 'participation_zztj_280_0936_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_280_0936_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=ev(code,title,n,start,end,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
add('xu_builds_marshal_office','正月徐知诰建立大元帅府，幕职分掌六部及盐铁',1,'春，正月，',None,[('徐知诰','建立元帅府与分职者')],place='吴',note='吏户礼兵刑工与盐铁为幕府职掌，不说此时南唐正式国朝六部已成立；吴境军政发展承935封齐。')
add('li_chongmei_yong_prince','正月丁未李从珂封子李重美为雍王',2,'丁未，',None,[('帝','封王者'),('李重美','皇子、雍王获封者')],when='936年正月丁未',place='后唐',note='仍后唐清泰三年，卷题天福元年为后晋全年编年框架，不能提前认石敬瑭已经登帝位。')
sup('li_chongmei_yong_prince',2,'jiuwudaishi-048-936-january','丁未，皇子河南尹、判六軍諸衛事重美封雍王。','旧末帝纪清泰三年正月丁未同记李重美封雍王，并列河南尹判六军职。','重美沿934已建李重美，官衔補当前身份，不造首次受河南尹之年。')
relationship('帝','李重美','父亲',2,'唐主立子重美为雍王。','明子，复用既有父亲方向，不因公主与重美同场推其他亲属。')
add('princess_birthday_visit_requests_return','正月癸丑李从珂千春节设宴，晋国长公主上寿后辞归晋阳',3,'癸丑，','辞归晋阳。',[('帝','千春节设宴者'),('晋国长公主','上寿并辞归者')],when='936年正月癸丑',place='后唐、晋阳',note='上寿是祝寿不是上朝请死；辞归为请求离去，不自动说当日抵晋阳。')
add('congke_drunken_question_princess','李从珂醉后问公主是否急归与石敬瑭反叛',3,'帝醉，','欲与石郎反邪！”',[('帝','醉后质问者'),('晋国长公主','被质问者')],when='936年正月癸丑千春节宴',note='疑问是帝言，不作公主与石已经本日谋反的事实；石郎沿石敬瑭，尚未在场不添其参与。')
add('shi_fears_after_princess_question','石敬瑭闻李从珂对公主之言，更加忧惧',3,'石敬瑭闻之，',None,[('石敬瑭','闻言后被记益惧者')],when='936年正月癸丑言论之后；闻讯日未载',place='河东',note='闻不等于亲自在宴，惧是主书心理叙述，不据此认此时起兵已发生。')
add('ma_yinsun_chancellor_936','三月丙午马胤孙任中书侍郎、同平章事',4,'三月，丙午，','同平章事。',[('马胤孙','翰林学士礼部侍郎、获任宰辅者'),('帝','任命者')],when='936年三月丙午',place='后唐')
sup('ma_yinsun_chancellor_936',4,'jiuwudaishi-048-936-march','丙午，以翰林學士、禮部侍郎馬裔孫為中書侍郎、同平章事。','旧末帝纪同记三月丙午马裔孙任中书侍郎、同平章事。','马裔孙沿马胤孙已核别名，原裔字保，不另建人。')
add('ma_yinsun_three_not_open','主书称马胤孙任中书后事务凝滞、少接宾客，时称三不开',4,'胤孙性谨儒，',None,[('马胤孙','被记凝滞及获三不开称呼者')],year=None,when='任中书期间常态；各次及起止年月未载',place='后唐',note='三不开对应口印门，是同时人评价，不是三项精确政务指标；谨儒为史述不诊断人格。')
sup('ma_yinsun_three_not_open',4,'xinwudaishi-055-sikong-duties','當時號為「三不開」，謂其不開口以論議，不開印以行事，不開門以延士大夫也。','新马胤孙传解释三不开：不论议、不行印、不延士大夫。','引同时称谓，不把所有政务未做当已逐案核实；同传也载司空职掌议论已在935补过，不新造本年司空任命。')
add('shi_collects_assets_jinyang','石敬瑭将洛阳及诸道财货收归晋阳，以助军费为说辞',5,'石敬瑭尽收','人皆知其有异志。',[('石敬瑭','集货归晋阳者')],place='洛阳、诸道、晋阳',note='托言和人皆知为作者判断；收财动作明载，但不由此将所有人知情或已经反叛当独证。')
add('congke_consults_about_rumors','李从珂夜间与近臣谈石敬瑭亲近与流言，问失欢后如何解处，众未答',5,'唐主夜','皆不对。',[('帝','向近臣问计者')],when='936年三月条下某夜；确日未载',note='至亲无可疑是帝言，与史家评价分；未名近臣不配完整名单。')
add('li_song_asks_lv_qi_strategy','李崧退后问吕琦应如何谋划，以受恩深厚为理由',5,'端明殿学士','计将安出？”',[('李崧','端明殿学士给事中、向同僚问计者'),('吕琦','被问同僚')],when='前述夜间问计之后；确日未载',note='据同僚不新建永久统属或盟友关系。')
add('lv_qi_analyzes_khitan_background','吕琦分析河东异谋可能引契丹，述契丹求和及荝剌未获归的背景',5,'琦曰：','故和未成耳。',[('吕琦','陈述风险与背景者'),('李崧','听其分析者')],when='936年三月条下讨论；所述求和属此前背景',note='若有异谋为假设，不将当时石契丹已缔正式盟约写成事实。契丹母与赞华只被提及，不建在场边；求和背景起年未明。')
claim('person',person('契丹母',5,'吕琦谈话中被提及的契丹太后',span(5,'契丹母','故和未成耳。')),'description','吕琦以契丹母与赞华在中国的背景分析对方求和。',5,span(5,'契丹母','故和未成耳。'),'契丹母沿述律平，谈话所提及不意味太后在场。')
claim('person',person('赞华',5,'吕琦谈话中被提及居中国的东丹王',span(5,'契丹母','故和未成耳。')),'aliases','本段赞华沿耶律倍在后唐所赐姓名李赞华。',5,'契丹母以赞华在中国，','回查931主书赐名及东丹主体，保UUID。')
claim('person',people['耶律倍'],'aliases','长兴二年东丹慕华获赐姓名李赞华，耶律倍可按此名检索。',5,'秋，九月，己亥，更赐东凡慕华姓名曰李赞华。','931已发布同人赐名；底本东凡疑东丹，原字保。这里只补当前赞华身份，不重新发布931改名事件。',source='tongjian-277-931-may')
claim('person',person('荝剌',5,'吕琦所述被请求归还的人物',span(5,'但求荝剌','故和未成耳。')),'aliases','本段先写荝剌、后写荝刺，按同一返还对象沿荝剌。',5,'今诚归荝刺等与之和，','刺剌不是繁简字，依据同段同返还对象核异写，保持原字与原主体。')
add('lv_qi_proposes_returns_annual_gifts','吕琦提出归还荝剌等、每年给礼币约十余万缗，与契丹议和以断河东外援',5,'今诚归','无能为矣。”',[('吕琦','提出方案及效果预测者'),('李崧','听方案者')],note='十余万为拟岁礼价值缗，不是已经支付额；河东无能为是预测，不作已实施奏效事实。')
sup('lv_qi_proposes_returns_annual_gifts',5,'xinwudaishi-056-lv-qi-peace','不如與契丹通和，如漢故事，歲給金帛，妻之以女，使彊藩大鎮顧外無所引援，可弭其亂心。','新吕琦传明确补方案还包括岁给金帛、妻之以女，欲断强藩外援。','主未展开婚姻条款，新明确提出，独立补充；计划不是已嫁女，未名女子不猜惠明等人。',relation='adds')
add('li_song_consults_zhang_financing','李崧认可吕琦方案，因钱谷出三司而转告张延朗商议',5,'崧曰：','遂告张延朗，',[('李崧','转告商议者'),('吕琦','前述讨论对象'),('张延朗','受告的三司财政负责人')],note='张相沿张延朗，不是刘延朗；钱谷三司与军财如何支出仍在讨论。')
add('zhang_yanlang_supports_plan_financing','张延朗赞成和议，称可减边费并在军财之外筹措供给',5,'延朗曰：','捃拾以供之，',[('张延朗','赞成并愿筹措者')],note='省什九是其预算预测，若听从为条件，不记录已经省90%或实际筹款金额。原后句引号疑缺，快照不添字。')
sup('zhang_yanlang_supports_plan_financing',5,'xinwudaishi-056-lv-qi-peace','延朗欣然曰：「苟能紓國患，歲費縣官十數萬緡，責吾取足可也！」','新吕传也记张延朗愿筹每年十数万缗以纾国患。','记录条件性承诺，十数万与主十余万保原数字表述，尚非资金已交契丹。')
add('li_lv_propose_plan_congke_approves','另一夜李崧、吕琦向李从珂密陈方案，帝喜并称忠',5,'他夕，','称其忠，',[('李崧','密陈者'),('吕琦','密陈者'),('帝','当时认可称忠者')],when='936年三月条下另一夜；确日未载',note='初认可并不等于外交实施完成，后变意另录。')
add('li_lv_draft_khitan_letter_wait','李崧、吕琦私草遗契丹书，等待命令',5,'二人私草',None,[('李崧','草书待命者'),('吕琦','草书待命者')],note='俟命意味着待命，未写寄出，不能当正式使团已达或契丹已接受。')
add('congke_asks_xue_peace_plan','过一段时间李从珂将和议方案告薛文遇',6,'久之，','薛文遇，',[('帝','告方案者'),('薛文遇','枢密直学士、受告者')],when='前述方案之后久之；确日未载',note='久之不自行推算几日，依与三月丁巳官命的叙述联系仍列本年，不造准确日。')
add('xue_opposes_peace_warns_marriage','薛文遇以屈尊及契丹求尚公主为由反对和议，并引戎昱诗',6,'文遇对曰：','帝意遂变。',[('薛文遇','反对者'),('帝','被记改变意见者')],note='尚公主为薛提出的可能，不是契丹此时已提正式求婚文书；戎昱及昭君是所引旧诗，不建936在场人物。')
sup('xue_opposes_peace_warns_marriage',6,'xinwudaishi-056-lv-qi-peace','文遇大以為非，因誦戎昱「社稷依明主，安危託婦人」之詩，以誚琦等。','新吕琦传也记薛文遇反对并引戎昱诗，保存更完整引语。','诗仍是被引用唐旧诗，原託保，未当936诗新作。')
add('congke_angrily_summons_li_lv','李从珂一日急召李崧、吕琦至后楼，责其拟送女、输财方案',6,'一日，','其意安在？”',[('帝','急召并责问者'),('李崧','被责问者'),('吕琦','被责问者')],when='前述变意后一日；确日未载',place='后楼',note='一日是某日，不读为仅次日。帝称一女乳臭未具名，不合惠明或猜年龄；虽称弃女仍非实际已出嫁。')
add('li_lv_defend_plan_and_apologize','李崧、吕琦称为报国而非为契丹，反复拜谢，帝仍责骂',6,'二人惧，','帝诟责不已。',[('李崧','辩明意图并拜谢者'),('吕琦','辩明意图并拜谢者'),('帝','继续责问者')],when='后楼召对时；确日未载',note='惧汗流为史述身体与心理反应，不诊断疾病，拜谢无数不统计次数。')
add('lv_qi_exhausted_answers_congke','吕琦拜至气竭稍停，被责强项后表示愿受罪，反问多拜何益',6,'吕琦气竭，','多拜可为！”',[('吕琦','停拜与回应者'),('帝','责强项者')],when='后楼召对时；确日未载',note='强项为帝斥语不是特定官职或永久性格；愿治罪不等于已定刑罚。')
sup('lv_qi_exhausted_answers_congke',6,'xinwudaishi-056-lv-qi-peace','琦曰：「臣素病羸，拜多而乏，容臣少息。」','新吕传补吕琦自述素病羸、拜多而乏，求少息。','自述病羸不由此填现代诊断，主气竭与新说明分列。',relation='adds')
add('congke_ends_audience_peace_silenced','李从珂稍解怒，止拜赐酒遣出，此后群臣不敢再提和亲策',6,'帝怒稍解，','和亲之策。',[('帝','止拜赐酒遣出者'),('李崧','结束召对者'),('吕琦','结束召对者')],when='后楼召对及其后；确日未载',note='不敢复言为主概括，未名群臣不造名单，不把赐酒当和议获准。')
sup('congke_ends_audience_peace_silenced',6,'xinwudaishi-056-lv-qi-peace','賜酒一巵而遣之，其議遂寢。','新吕传明确记赐酒遣出，和议遂停。','一巵是酒杯量，不能据此推赐酒为正式外交诏批或实际支付。')
add('lv_qi_censor_march','三月丁巳吕琦任御史中丞',6,'丁巳，',None,[('吕琦','御史中丞获任者'),('帝','任命者')],when='936年三月丁巳',note='盖疏之为主解释，不改成官命明称贬斥诏；不把新后数月复任端明提前。')
sup('lv_qi_censor_march',6,'jiuwudaishi-048-936-march','丁巳，以端明殿學士呂琦為御史中丞。','旧末帝纪三月丁巳同记吕琦由端明殿学士任御史中丞。','只用正文官命独立互核，旧附案通鉴和亲策是依赖主书的注，不能重复作第二独证。')
add('xu_jingtong_deputy_marshal','徐知诰以子徐景通为太尉、副元帅',7,'吴徐知诰','副元帅，',[('徐知诰','任命者'),('景通','原副都统、太尉副元帅获任者')],place='吴',note='景通沿李璟（徐景通）稳定主体，不因改名另建；太尉是其新授衔，副元帅不是国君已经禅位。')
sup('xu_jingtong_deputy_marshal',7,'xinwudaishi-062-jing-name','景，初名景通，昪長子也。既立，又改名璟。','新南唐世家明确景初名景通、昪长子，后改璟。','用于同一主体身份，后即帝位改名不提前当936行为；主旧时称徐景通展示兼现规范李璟。',relation='adds')
relationship('徐知诰','景通','父亲',7,'吴徐知诰以其子副都统景通为太尉、副元帅，','明子，复用既有李昪与李璟父子边；养父徐温关系与此不混。')
add('song_xu_jie_marshal_sima','宋齐丘、徐玠分别任大元帅府左、右司马',7,'都统判官宋齐丘',None,[('宋齐丘','原都统判官、元帅府左司马获任者'),('徐玠','原行军司马、元帅府右司马获任者'),('徐知诰','任命者')],place='吴',note='原人名顺序与左右对应，不把左右司马误作左右丞相或长期统属。')
add('min_tongwen_era','闽主王昶改元通文',8,'闽主昶','改元通文，',[('昶','改元主体')],place='闽',note='主承三月条无确日；新把改通文连既立改名压缩在一段，不提前作935已改元。')
sup('min_tongwen_era',8,'xinwudaishi-068-jipeng-name','既立，更名昶，改元通文，','新闽世家将即位更名与通文改元压缩相连。','主935先更名、本年改元分别处理，新未具改元确月日，保叙法层次。',relation='adds',field='time_original')
add('min_chunyan_empress','闽主王昶立贤妃李氏为皇后',8,'立贤妃李氏','为皇后，',[('昶','立后者'),('贤妃李氏','原贤妃、获立皇后者')],place='闽',note='贤妃李氏承935明确李春燕，非元妃梁国夫人李氏；王昶沿王继鹏、与蜀孟昶分开。')
add('min_dowager_grand_dowager','闽朝廷尊皇太后为太皇太后',8,'尊皇太后',None,[('昶','尊号主体')],place='闽',note='皇太后未具名，不猜黄氏或新建未名重复人物；尊号不由此推本人亲自执行宫廷政变。')
# Add only relevant prerequisite appointments from an independently dated imperial record.
event('lv_qi_duanming_january','旧末帝纪补正月癸卯吕琦任端明殿学士',6,'癸卯，以給事中、充樞密院直學士呂琦為端明殿學士；',[('吕琦','由给事中枢密直学士任端明学士者')],source='jiuwudaishi-048-936-january',when='936年正月癸卯；补三月官命的前职任命',place='后唐',note='只补当前主对话、改官相关身份，不扩同段无关王彦镕等任命。')
event('xue_wenyu_shumi_january','旧末帝纪补正月癸卯薛文遇任枢密院直学士',6,'以六軍諸衛判官、尚書工部郎中薛文遇為樞密院直學士。',[('薛文遇','枢密直学士获任者')],source='jiuwudaishi-048-936-january',when='936年正月癸卯条下；补当前和议对话职衔',place='后唐',note='旧本此官命接癸卯、未另具日；935主已称枢密直学士与旧当前任命层次差别保，不推935所有轮值都同官首次。')
reviews={1:'吴元帅府分职非937南唐国朝六部，七职保六部盐铁全部。',2:'李重美沿934旧主体，父亲方向复用；主旧丁未封雍同，河南尹与判六军补当前衔，不新造亲属。',3:'设千春宴、公主上寿辞归、帝醉问、石闻益惧分；公主沿永宁已应用别名。帝疑问不当石公主已合谋，未名幼女不猜，闻不是在场。',4:'主旧丙午马裔孙沿马胤孙，任相与任中书期间三不开常态分，常态起止未载年null；新卷55实际马传而非冯传。',5:'石收财与作者异志判断分，夜问、李吕商讨风险背景、归荝剌岁币计划、张融资条件、密奏初赞、草书待命分。新吕传明确妻女方案并补，主未展开不否认；岁礼十余万缗和边费什九均计划预测不是已支付成效。荝刺沿荝剌异写，赞华沿耶律倍回查931赐名，别名另定向修订。',6:'久之某日不强定确日，薛反对与引旧诗、帝怒召质责、李吕辩明拜谢、吕气竭回应、帝赐遣停议、丁巳改官分。未名幼女不合惠明，婚姻提议非已嫁；盖疏之是史家解释，旧通鉴案注依赖不算独证。旧正月吕端明、薛枢直官命补当前身份，935主称薛枢直与旧当前任命层次保。',7:'李昪父李璟边复用，景通按初名同主体。宋徐与左右职按顺序对应，不错当937相位。',8:'王昶沿继鹏，改元本年与新既立压缩叙法分；贤妃李氏沿李春燕非元妃李氏，未名太后不猜身份。'}
context_path=ROOT/'content/books/zizhi-tongjian/vol-279/year-0934/part-02/sources/library/xinwudaishi-055-ma-yinsun/source.txt'
contexts=[dict(file=os.path.relpath(context_path,P/'sources'),sha256=hashlib.sha256(context_path.read_bytes()).hexdigest(),paragraph_id='xin-wudaishi-b08f244b9241-p002152',purpose='回查卷55马胤孙传首，三不开所承传主；不扩其他段',url='https://github.com/greed-216/histree/blob/2ec8cf50/'+str(context_path.relative_to(ROOT)))]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=280,year=936,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph='zztj-v280-y0936-p009',next_volume=280,next_year=936,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷280连续936年第1—8正文段原6—13行，吴府制、唐封王千春宴、马任相与三不开、石收财李吕和议、薛沮及吕改官、吴府任命、闽改元立后尊号。后62段待录。前段仍后唐清泰三年，不因全年后晋天福题提前改朝。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
