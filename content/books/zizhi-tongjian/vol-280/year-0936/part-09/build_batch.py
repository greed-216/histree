# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 280, year 936 paragraphs 54–70."""
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
 key={'jiuwudaishi-097-lu-wenjin':'jiuwudaishi-097-lu-wenjin-flight','xinwudaishi-048-lu-wenjin':'xinwudaishi-048-lu-wenjin-flight'}.get(directory.name,directory.name)
 specs.append((key,directory,'b603079e','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('liaoshi') else '欧阳修'))
specs += [('tongjian-280-936-tang-fall',YEAR/'part-08/sources/library/tongjian-280-936-tang-fall','d2115d00','司马光等'),('jiuwudaishi-076-jin-advance',YEAR/'part-07/sources/library/jiuwudaishi-076-jin-advance','660186cb','薛居正等')]

# Reuse already published source identities, including the earlier Zhou Gui biography.
prior_source_registry={x['key']:x for f in sorted((ROOT/'content').rglob('content-batch.json')) if f.parent != P for x in json.loads(f.read_text())['sources']}
normalized=[]
for key,path,commit,author in specs:
 if key in prior_source_registry:
  archived=prior_source_registry[key]['url'].split('/blob/',1)[1];commit,relative=archived.split('/',1);old_path=(ROOT/relative).parent
  assert (old_path/'source.txt').read_bytes()==(path/'source.txt').read_bytes(),key
  path=old_path
 normalized.append((key,path,commit,author))
specs=normalized

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-280-936-tang-fall','tongjian-280-936-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v280-y0936-p054-p070',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-076-year-end': '卷76·晋高祖纪（石敬瑭）', 'jiuwudaishi-096-zheng-ruan': '卷96·郑阮传', 'jiuwudaishi-094-mi-qiong': '卷94·秘琼传', 'jiuwudaishi-095-zhou-gui': '卷95·周瑰传', 'jiuwudaishi-088-zhang-xichong': '卷88·张希崇传', 'jiuwudaishi-091-fang-zhiwen': '卷91·房知温传', 'jiuwudaishi-069-zhang-yanlang': '卷69·张延朗传', 'jiuwudaishi-069-liu-yanlang': '卷69·刘延朗传', 'jiuwudaishi-097-lu-wenjin-flight': '卷97·卢文进传', 'xinwudaishi-048-lu-wenjin-flight': '卷48·卢文进传', 'xinwudaishi-008-year-end': '卷8·晋高祖纪', 'xinwudaishi-008-lu-date': '卷8·晋高祖纪·天福二年', 'xinwudaishi-062-zhou-quanjin': '卷62·南唐世家', 'jiuwudaishi-076-jin-advance': '卷76·晋高祖纪（石敬瑭）'}
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
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/280.txt').read_text().splitlines()
for n in range(54, 71):
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
    labels={'jiuwudaishi-076-year-end': '卷76·晋高祖纪（石敬瑭）', 'jiuwudaishi-096-zheng-ruan': '卷96·郑阮传', 'jiuwudaishi-094-mi-qiong': '卷94·秘琼传', 'jiuwudaishi-095-zhou-gui': '卷95·周瑰传', 'jiuwudaishi-088-zhang-xichong': '卷88·张希崇传', 'jiuwudaishi-091-fang-zhiwen': '卷91·房知温传', 'jiuwudaishi-069-zhang-yanlang': '卷69·张延朗传', 'jiuwudaishi-069-liu-yanlang': '卷69·刘延朗传', 'jiuwudaishi-097-lu-wenjin-flight': '卷97·卢文进传', 'xinwudaishi-048-lu-wenjin-flight': '卷48·卢文进传', 'xinwudaishi-008-year-end': '卷8·晋高祖纪', 'xinwudaishi-008-lu-date': '卷8·晋高祖纪·天福二年', 'xinwudaishi-062-zhou-quanjin': '卷62·南唐世家', 'jiuwudaishi-076-jin-advance': '卷76·晋高祖纪（石敬瑭）'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '闰十一月条下' if n == 54 else '十二月条下'
        citation = f'卷280·后唐清泰三年／后晋天福元年（936；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_280_0936_09_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_ALIASES={'郑阮':['鄭阮','郑玩','鄭玩'],'石重立':[],'秘琼':['秘瓊','祕瓊'],'门铎':['門鐸','门鐸'],'周弘祚':['弘祚'],'李肃':['李肅'],'胡章':[],'冯知兆':['馮知兆'],'杜重贵':['杜重貴']}


ALIASES.update({'张彦琦':'张彦琪','张彦琪':'张彦琪','曹太后':'曹氏（李嗣源后）','刘皇后':'刘氏（李从珂后）','太相温':'太相温（契丹将）','大相温':'太相温（契丹将）','汉主':'刘岩','吴主':'杨溥','杨光远':'杨檀','景岩':'刘景岩','刘延郎':'刘延朗','李赞华':'耶律倍','李懿':'李懿（后唐亲将）'})

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
    if when is None:when='936年闰十一月条下；确日未独载' if n==54 else '936年十二月条下；确日未独载'
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
def source_span(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end);return t[a:b]

# Paragraph 54: financial grievance, amnesty exceptions and subsequent deaths.
add('zhang_takes_he_dong_surplus','追述张延朗尽收河东应留使之外财赋，石敬瑭怀恨',54,'初，帝在河东，','帝以是恨之。',[('帝','河东受限制、记恨者'),('张延朗','判三司、收财赋者')],year=None,when='石敬瑭在河东、唐朝猜忌时追叙；独立年日未载',place='河东',note='初为此前积怨，不把全部多年财赋征收归到936甲申当日。应留使之外限定不略。')
sup('zhang_takes_he_dong_surplus',54,'jiuwudaishi-069-zhang-yanlang','係官財貨留使之外，延朗悉遣取之，晉高祖深銜其事。','旧张传同留使外悉取、石深衔。','本传张延朗非刘延朗，已以传首上下文确认；不改主原文。')
add('shi_arrests_zhang_yanlang','壬午百官见石敬瑭，张延朗独付御史台，其他谢恩',54,'壬午，','馀皆谢恩。',[('帝','收付者'),('张延朗','被付御史台者')],when='936年闰十一月壬午',place='洛阳',note='收付是羁押阶段，不与随后斩合成同一动作。')
add('shi_enters_palace_amnesty','甲申石敬瑭入宫大赦，旧朝中外官吏原则不问',54,'甲申，','应中外官吏一切不问，',[('帝','入宫、颁赦者')],when='936年闰十一月甲申',place='洛阳宫',note='不是辛巳当晚入旧宅。一般赦后仍有张刘等例外，不能写旧朝人员全获赦。')
sup('shi_enters_palace_amnesty',54,'jiuwudaishi-076-jin-advance','甲申，車駕入內，禦文明殿受朝賀，用唐禮樂。','旧晋纪补文明殿朝贺用唐礼乐。','同甲申入内，不移到辛巳入洛。',relation='adds')
add('amnesty_excludes_zhang_lius','赦令列张延朗、刘延皓、刘延朗为不予容贷的例外',54,'惟贼臣张延朗、','罪难容贷；',[('帝','下诏者'),('张延朗','赦令例外对象'),('刘延皓','赦令例外对象'),('刘延朗','赦令例外对象')],when='936年闰十一月甲申赦令',note='奸邪等为诏书罪评，展示归于赦令，不把诏方评价当现代已完成司法调查。')
add('amnesty_four_dismissed','马胤孙、房暠、李专美、韩昭胤获释罪除名',54,'中书侍郎、平章事马胤孙、','并释罪除名；',[('帝','赦令者'),('马胤孙','释罪除名对象'),('房暠','释罪除名对象'),('李专美','释罪除名对象'),('韩昭胤','释罪除名对象')],when='936年闰十一月甲申',note='主除名并非留任旧官，旧马裔孙、韩昭裔为已核别名，不新建同人。')
sup('amnesty_four_dismissed',54,'jiuwudaishi-076-jin-advance','其有宰臣馬裔孫、樞密使房暠、宣徽使李專美、河府節度使韓昭裔等四人，並令釋放。','旧晋纪同四人释放，马韩名字异写。','旧只释放、主除名两层分别保存，不能说旧也明记四人官职保留。')
add('early_submitters_reassigned','赦令命中书门下另任先归顺臣僚',54,'中外臣僚先归顺者，','委中书门下别加任使。',[('帝','发布任使安排者')],when='936年闰十一月甲申',note='安排非所有人已有具体新官，未造匿名任官名单。')
add('liu_yanhao_hides_hangs','刘延皓匿于成门数日后自缢',54,'刘延皓匿于成门，','自经死。',[('刘延皓','躲藏后自缢者')],when='936年晋入洛后数日；独立死日未载',place='成门（底本原称）',note='成门疑字待核，保原称不自动改为已定位城门；死因原自经与另一刘被捕处杀分。')
add('liu_yanlang_caught_killed','刘延朗欲奔南山，被捕杀',54,'刘延朗将奔南山，','捕得，杀之。',[('刘延朗','逃亡被捕杀者')],when='936年晋入洛后；确日未独载',place='南山（拟奔处，捕获地点未详）',note='将奔是意向、不能定位实际死于南山；杀者未署名，不凭赦诏补石亲行斩。')
sup('liu_yanlang_caught_killed',54,'jiuwudaishi-069-liu-yanlang','延朗將竄於南山，','旧刘传同欲逃南山。','张刘同名尾延朗按传首及履历分，不合。')
sup('liu_yanlang_caught_killed',54,'jiuwudaishi-069-liu-yanlang','尋捕而殺之。','旧刘传同随后被捕杀。','其私第钱三十万为临逃自言可补但不当已查账总资产，本批不另扩。')
add('zhang_executed_shi_regrets','张延朗被斩，石敬瑭后来难选三司使而后悔',54,'斩张延朗；',None,[('张延朗','被斩者'),('帝','后来选任困难、后悔者')],when='936年入洛后斩；选使及悔为既而追叙，具体日未载',note='悔为史书所记，非撤销已执行死刑，既而不定同甲申时刻。')
sup('zhang_executed_shi_regrets',54,'jiuwudaishi-069-zhang-yanlang','晉高祖入洛，送台獄以誅之。其後以選求計使，難得其人，甚追悔焉。','旧张传同诛后选计使难、石追悔。','以独立本传印证而非旧附引通鉴。')
for name,quote in [('张延朗','斩张延朗；'),('刘延皓','刘延皓匿于成门，数日，自经死。'),('刘延朗','刘延朗将奔南山，捕得，杀之。')]:
 claim('person',people[name],'death_year',name+'于936年晋入洛后去世。',54,quote,'本年明确死事；复用主体年份更新由带旧值守卫的独立修订执行。')
# Paragraphs 55–60.
add('min_reacts_tang_fall','闽人闻后唐亡，叹潞王罪未闻并忧本国君主',55,'闽人',None,[],note='这是匿名群众言辞，不凭吾君补具体发言者或断言君主已经获罪。')
add('shi_farewell_khitan_heyang','十二月乙酉朔石敬瑭赴河阳饯太相温和契丹归军',56,'十二月，',None,[('帝','赴河阳饯送者'),('太相温','受饯归国者')],when='936年十二月乙酉朔',place='河阳',note='此前护送令与当前归国饯送分，不因旧不同音译造第二个人。')
sup('shi_farewell_khitan_heyang',56,'jiuwudaishi-076-year-end','十二月乙酉朔，幸河陽，餞送大詳袞、蕃部兵士歸國，','旧同日河阳饯送称大详衮。','主太相温、前段旧大相温，旧大详衮本处随同饯送同一任务链，为称谓异文，未据音译另合迪离毕。')
add('congke_posthumous_demotion','晋朝追降已亡李从珂为庶人',57,'追废唐主',None,[('唐主','死后追降对象')],when='936年十二月乙酉朔饯归条下',note='追废是死后处置，不把唐主复位后又在场当新发生废黜。')
sup('congke_posthumous_demotion',57,'jiuwudaishi-076-year-end','詔降末帝為庶人。','旧记诏降末帝庶人。','上承乙酉饯归原语境，不给诏执行者建匿名人物。')
add('feng_dao_chancellor_jin','丁亥冯道兼门下侍郎、同平章事',58,'丁亥，',None,[('冯道','受兼相职者')],when='936年十二月丁亥')
sup('feng_dao_chancellor_jin',58,'jiuwudaishi-076-year-end','丁亥，制以司空馮道守本官兼門下侍郎、平章事、宏文館大學士，','旧补司空守本官、宏文馆大学士。','同兼任不是由门下侍郎反向升司空已证，主省职不否旧多职。',relation='adds')
add('shi_zhongli_kills_zheng','石重立趁乱杀曹州刺史郑阮并杀其家',59,'曹州刺史',None,[('郑阮','曹州刺史、被杀者'),('石重立','指挥使、趁乱杀者')],when='936年十二月丁亥后辛卯前条下；新纪己丑',place='曹州',note='贪暴是史家评价；族其家为家庭整体受害，不造未具名子女身份。')
sup('shi_zhongli_kills_zheng',59,'jiuwudaishi-096-zheng-ruan','高祖建義入洛，阮自郡來朝，旋為本州指揮使石重立所殺，舉族無孑遺。','旧郑传补自郡来朝后遭石重立杀及族害。','来朝与被杀叙顺不猜在哪座门，末句史家概称不录现代逐口家属统计。',relation='adds')
sup('shi_zhongli_kills_zheng',59,'xinwudaishi-008-year-end','己丑，曹州指揮使石重立殺其刺史鄭玩。','新帝纪作郑玩，记十二月己丑。','以同曹州刺史及石重立杀链核异字别名，主旧郑阮不改；己丑来自新不是主具载。',relation='adds',field='time_original')
claim('person',people['郑阮'],'death_year','郑阮在936年十二月被石重立杀。',59,'曹州刺史郑阮贪暴，指挥使石重立因乱杀之，族其家。','主年度与旧来朝被杀、新己丑交核。')
next(x for x in B['people'] if x['key']==people['郑阮'])['death_year']=936
add('yao_yi_justice_minister','辛卯姚顗任刑部尚书',60,'辛卯，',None,[('姚顗','由唐中书侍郎改任刑部尚书者')],when='936年十二月辛卯')
sup('yao_yi_justice_minister',60,'jiuwudaishi-076-year-end','辛卯，以舊相姚顗為刑部尚書。','旧同日刑部尚书任命。','旧相与主旧中书官描述各自保，非两人。')
# Paragraph 61: retrospective frontier government and reappointment.
add('zhang_xichong_tuntian','追述张希崇守朔方获民夷信服、兴屯田省漕运',61,'初，朔方节度使','以省漕运；',[('张希崇','经营朔方、屯田者')],year=None,when='张希崇前任朔方期间追述；独立年未载',place='朔方',note='威信、爱之为史家评价；追叙五年整体不可按本年一日计。')
sup('zhang_xichong_tuntian',61,'jiuwudaishi-088-zhang-xichong','希崇乃告諭邊士，廣務屯田，歲餘，軍食大濟。','旧传补告谕边士、岁余军食大济。','旧此前灵州粮运背景，不把岁余换成936末一年。',relation='adds')
add('zhang_xichong_requests_inland','张希崇在镇五年求内徙，李从珂任其静难节度使',61,'在镇五年，','唐潞王以为静难节度使。',[('张希崇','求内徙、受任者'),('唐主','先前任命者')],year=None,when='后唐李从珂在位期间追叙；确年日未载',place='朔方至静难',note='在镇五年是主时长，不按936减五推首任年；旧邠州与军号静难地职对应，具体辖界未核。')
sup('zhang_xichong_requests_inland',61,'jiuwudaishi-088-zhang-xichong','清泰中，希崇厭其雜俗，頻表請覲，詔許之。','旧补清泰中频表请觐获准。','旧正文厌杂俗为史家描述，与主求徙不冲突但不能替主直接增评价。',relation='adds')
add('shi_returns_zhang_shuofang','癸巳石敬瑭虑契丹再取灵武，复任张希崇朔方节度使',61,'帝与契丹修好，',None,[('帝','虑边地、任命者'),('张希崇','复任朔方者')],when='936年十二月癸巳',place='朔方、灵武',note='恐复取为担忧，不当契丹已再取城的事件。')
sup('shi_returns_zhang_shuofang',61,'jiuwudaishi-076-year-end','癸巳，以邠州節度使張希崇為靈武節度使，','旧同日邠州改灵武。','主静难/朔方和旧州地衔对读，未因此新设两个受任人。')
sup('shi_returns_zhang_shuofang',61,'jiuwudaishi-088-zhang-xichong','及高祖入洛，與契丹方有要盟，慮為其所取，乃復除靈武。','旧张传同因契丹要盟虑被取而复灵武。','其指前叙灵州地，未扩成全部旧唐边防撤空事实。')
# Paragraph 62: capture precedes the usurpation; no presumed captive deaths.
add('dong_uses_mi_qiong','追述董温琪积巨财并以秘琼为腹心',62,'初，成德节度使','秘琼为腹心。',[('董温琪','成德节度使、用腹心者'),('秘琼','平山籍、牙内都虞侯、受倚者')],year=None,when='董温琪任成德期间追述；独立年日未载',place='成德',note='主贪暴为史家评价，不能从腹心自动建立忠诚不变的关系边。')
sup('dong_uses_mi_qiong',62,'jiuwudaishi-094-mi-qiong','清泰中，董溫琪為鎮州節度使，擢瓊為衙內指揮，倚以腹心。','旧秘传补清泰中擢衙内指挥。','主牙内都虞侯、旧衙内指挥职称差原留，不任意统一某一衔。',relation='adds')
add('dong_captured_with_zhao','董温琪与赵德钧陷于契丹',62,'温琪与赵德钧','俱没于契丹，',[('董温琪','同陷契丹者'),('赵德钧','同陷契丹者')],when='936年唐北军溃败后追述；独立确日未载',note='没在本处陷俘非死亡，不能据此给董死年936。赵后年卒已有独立出处。')
add('mi_kills_dong_family_takes_wealth','秘琼杀董温琪家属合葬一坎，取其财货',62,'琼尽杀','而取其货，',[('秘琼','杀家属、取财者'),('董温琪','财货与家属所属主体')],note='董为被杀家属的关联对象，未在场、未在本句被杀；匿名家属不造名。',place='镇州')
sup('mi_kills_dong_family_takes_wealth',62,'jiuwudaishi-094-mi-qiong','瓊乃害溫琪之家，載其屍，都以一坎瘞之。','旧同杀家一坎埋葬。','被杀是家属，秘取财另句与主同，董俘于蕃不可写被秘现场杀。')
add('mi_claims_acting_commander','秘琼自称成德留后，奏称军乱',62,'自称留后，',None,[('秘琼','自称留后、上表者')],note='自称不等晋朝已正式任命，表称军乱是其奏报内容。',place='镇州')
sup('mi_claims_acting_commander',62,'jiuwudaishi-094-mi-qiong','遂自稱留後。','旧同自称留后。','后文安重荣代及夏津死属于后续进度，不本段顺带填卒年。')
# Independent chronicle adds named victims of this same revolt.
event('mi_expels_li_yanqi','旧晋纪补秘琼逐副使李彦琦',62,'鎮州衙內都虞候秘瓊作亂，逐副使李彥琦，',[('秘琼','作乱逐人者'),('李彦琦','节度副使、被逐者')],source='jiuwudaishi-076-year-end',place='镇州',when='936年十二月癸巳之后条下；新纪系癸巳',note='补证同军变明署被逐副使，与张彦琪不是同人。')
E['mi_expels_li_yanqi']='event_zztj_280_0936_mi_expels_li_yanqi'
sup('mi_expels_li_yanqi',62,'xinwudaishi-008-year-end','癸巳，鎮州牙內都虞候祕瓊逐其節度副使李彥琦。','新同逐李、明确癸巳。','主此事件确日未独载；用新提供日期仍注来自新纪。',relation='adds',field='time_original')
event('mi_kills_hu_zhang','旧晋纪补秘琼杀都指挥使胡章',62,'鎮州衙內都虞候秘瓊作亂，逐副使李彥琦，殺都指揮使胡章。',[('秘琼','杀者'),('胡章','镇州都指挥使、被杀者')],source='jiuwudaishi-076-year-end',when='936年十二月军变条下；独立日未载',place='镇州',note='只本次镇州都指挥使；906延州刺史胡章同名但30年前异职证不足，未合。')
claim('person',people['胡章'],'death_year','胡章在936年十二月镇州军变中被秘琼杀。',62,'鎮州衙內都虞候秘瓊作亂，逐副使李彥琦，殺都指揮使胡章。','旧本年帝纪明确死事，未与早年同名者贸然合。',source='jiuwudaishi-076-year-end')
next(x for x in B['people'] if x['key']==people['胡章'])['death_year']=936
# Paragraphs 63–68.
add('men_duo_kills_yang','同州小校门铎杀节度使杨汉宾，焚掠州城',63,'同州小校',None,[('门铎','杀节度、焚掠者'),('杨汉宾','节度使、被杀者')],place='同州',note='门鐸展示为门铎并保原字别名，不是另有门铎繁体人物；职随主小校，旧新同事。')
sup('men_duo_kills_yang',63,'jiuwudaishi-076-year-end','同州小校門鐸殺節度使楊漢賓，燒劫州城。','旧同同州杀杨、烧劫。','主焚掠旧烧劫同实事异词，不凭杀将自动录杨全家遇害。')
sup('men_duo_kills_yang',63,'xinwudaishi-008-year-end','同州裨將門鐸殺其將楊漢賓。','新同门杀杨，称裨将。','新接癸巳条下、无另日，主此条也未独日，不把同句时间强换为精准现代日期。')
claim('person',people['杨汉宾'],'death_year','杨汉宾在936年十二月被门铎杀。',63,'同州小校门鐸杀节度使杨汉宾，焚掠州城。','沿已有同人，卒年用独立字段修订，旧档不改。')
add('bei_posthumous_yan_title','晋朝赠李赞华燕王，并遣使送丧归国',64,'诏赠',None,[('李赞华','死后赠王、归丧对象')],note='沿耶律倍别名；归国指送契丹，本人为丧葬对象，非获封后活着出使。')
sup('bei_posthumous_yan_title',64,'jiuwudaishi-076-year-end','詔封故東丹王李贊華為燕王，遣前單州刺史李肅部署歸葬本國。','旧补故东丹王与送葬使李肃。','原丙申举曹后哀之后无独另日，主也无日；送葬和早前杀倍不同。',relation='adds')
event('li_su_returns_bei_coffin','旧晋纪补李肃部署李赞华归葬契丹',64,'詔封故東丹王李贊華為燕王，遣前單州刺史李肅部署歸葬本國。',[('李肃','前单州刺史、部署归葬使'),('李赞华','归葬对象')],source='jiuwudaishi-076-year-end',when='936年十二月丙申哀后条下；独立日未载',note='李肃前单州刺史身份，不合唐末政事中另一李肃无证；单州不是葬地。')
add('zhang_lang_submits','张朗率其众入朝',65,'张朗',None,[('张朗','率众入朝者')],note='张朗沿先前襄州将领，未写此处有具体受任职。')
add('lu_wenji_civil_appointment','庚子卢文纪任吏部尚书',66,'庚子，','为吏部尚书。',[('卢文纪','唐旧相、晋任吏部尚书者')],when='936年十二月庚子')
sup('lu_wenji_civil_appointment',66,'jiuwudaishi-076-year-end','以舊相盧文紀為吏部尚書；','旧同卢文纪吏部任。','上承庚子帝纪日，不认卢姚在辛巳罢相就已无后任何官。')
add('zhou_gui_three_offices_offer','庚子晋命皇城使周瑰为大将军、充三司使',66,'以皇城使晋阳周瑰','充三司使；',[('周瑰','皇城使、受拟任者')],when='936年十二月庚子',note='受命后辞获准，不能写长年实际主持三司；晋阳是籍贯不事件现场。')
sup('zhou_gui_three_offices_offer',66,'jiuwudaishi-076-year-end','以皇城使周環為大將軍，充三司使；','旧帝纪姓名作周环，主及旧传周瑰。','同皇城使、大将军、三司任职且同庚子，旧周传更同晋阳与辞任链，核异写沿周瑰，原环不悄改。',relation='conflicts')
sup('zhou_gui_three_offices_offer',66,'jiuwudaishi-095-zhou-gui','及即位，命權判三司事，','旧周传称权判三司事。','与纪充三司使衔写差保；传首晋阳、腹心书计、随后辞不济足核同人。',relation='adds')
add('zhou_gui_refuses_shi_accepts','周瑰自称才不称职请辞，石敬瑭准许',66,'瑰辞曰：',None,[('周瑰','自陈不称职请辞者'),('帝','允辞者')],when='936年十二月庚子任命条下',note='才不称职是周自陈，不能据此断定能力差已独立考核。')
sup('zhou_gui_refuses_shi_accepts',66,'jiuwudaishi-095-zhou-gui','高祖可之。','旧周传同高祖允辞。','下文数月安州和被害为将来，未并录到936。')
add('fang_zhiwen_death_report','石敬瑭闻平卢节度使房知温去世',67,'帝闻平卢节度使','房知温卒，',[('帝','闻讣者'),('房知温','讣报亡者')],note='闻日与死亡日不同，主未独记死日；旧本传补十二月辛巳，不能把庚子闻报当辛巳死日的严密顺序已证。')
sup('fang_zhiwen_death_report',67,'jiuwudaishi-091-fang-zhiwen','天福元年冬十二月辛巳，卒於鎮。','旧房传明确本年冬十二月辛巳卒镇。','主庚子条下闻卒与旧辛巳卒时间疑差，保异而不改主原序；两者同年936。',relation='conflicts',field='time_original')
claim('person',people['房知温'],'death_year','房知温于936年去世，旧传记天福元年冬十二月辛巳。',67,'天福元年冬十二月辛巳，卒於鎮。','两书同年，但闻讣与独立传记日差另保，死年936由守卫修订。',source='jiuwudaishi-091-fang-zhiwen')
add('wang_jianli_qingzhou_patrol','晋遣天平节度使王建立领兵巡抚青州',67,'遣天平节度使',None,[('帝','遣巡抚者'),('王建立','天平节度、带兵巡抚者')],place='青州',note='遣巡抚不等已正式兼平卢节度任，主无表说杀副使，未把新另事默认为同次派兵目的。')
sup('wang_jianli_qingzhou_patrol',67,'jiuwudaishi-076-year-end','青州奏，節度使房知溫卒，詔鄆州王建立以所部牙兵往青州安撫。','旧补青州奏、所部牙兵，王郓州至青州。','上承庚子年末条，下有生日奏非此巡抚，未扩录不相干新帝纪杀李彦赟。',relation='adds')
add('xingtang_renamed_guangjin','晋改兴唐府为广晋府',68,'改兴唐府',None,[],place='兴唐府、广晋府',note='地名沿原名与新名并列，不据名称改为疆界大幅变更，坐标留空。')
# Paragraph 69: the same departure has inconsistent chronology and extra victims.
add('lu_wenjin_fears_khitan_flees_wu','辛丑卢文进因晋受契丹拥立，虑自身曾叛契丹，弃安远镇奔吴',69,'安远节度使','弃镇奔吴。',[('卢文进','安远节度、弃镇奔吴者'),('帝','其获契丹拥立是卢所闻背景对象')],when='936年十二月辛丑；新晋纪次年正月癸亥异日',place='安远至吴',note='帝是政治背景未在卢奔逃现场；原自以本契丹叛将为虑，不能说晋已命捕卢。')
sup('lu_wenjin_fears_khitan_flees_wu',69,'jiuwudaishi-097-lu-wenjin-flight','及高祖即位，與契丹敦好，文進以嘗背契丹，居不自安。','旧同晋契丹敦好、卢以曾背契丹不安。','此旧正文是独立证，后夹引马令非本次新增第三专书。')
sup('lu_wenjin_fears_khitan_flees_wu',69,'xinwudaishi-008-lu-date','二年春正月癸亥，安遠軍節度使盧文進叛降于吳。','新晋纪记天福二年正月癸亥奔吴。','与主旧传元年冬十二月、同书新卢传元年冬不一致，保三记纪时；不改主年或把新传当唯一新史说法。',relation='conflicts',field='time_original')
sup('lu_wenjin_fears_khitan_flees_wu',69,'xinwudaishi-048-lu-wenjin-flight','晉高祖立，與契丹約為父子，文進懼不自安。天福元年冬，','新卢传元年冬及其不安。','同书本纪二年正月与传元年冬冲突，原各自保存，不能为了整齐只引一边。',relation='conflicts',field='time_original')
add('lu_wenjin_tells_route_garrisons','卢文进沿途告各镇戍主将逃离缘故，众拜辞而退',69,'所过镇戍，',None,[('卢文进','召主将告缘故者')],when='936年十二月奔吴途中；各镇独立日未载',note='各主将未具名，不能把沿途众拜辞画成具名归降或跟随。')
sup('lu_wenjin_tells_route_garrisons',69,'xinwudaishi-048-lu-wenjin-flight','告以避契丹之意，將士皆再拜為訣，乃南奔。','新传同避契丹别将士再拜诀。','新自至营告将士与主沿途告镇主将叙地点和对象略不同，分别写不硬合一场会见。',relation='adds')
event('lu_kills_feng_du_before_flight','旧新卢传补卢文进杀冯知兆、杜重贵后南奔',69,'天福元年十二月，乃殺行軍司馬馮知兆、節度副使杜重貴等，率其部眾渡淮奔於金陵。',[('卢文进','杀二官、率众南奔者'),('冯知兆','行军司马、被杀者'),('杜重贵','节度副使、被杀者')],source='jiuwudaishi-097-lu-wenjin-flight',when='旧传天福元年十二月（936），新传元年冬',place='安远镇至金陵',note='主省略杀二官，他书记同奔链补；不能因部众南奔把二死者角色作随行投吴。')
E['lu_kills_feng_du_before_flight']='event_zztj_280_0936_lu_kills_feng_du_before_flight'
sup('lu_kills_feng_du_before_flight',69,'xinwudaishi-048-lu-wenjin-flight','殺其行軍司馬馮知兆、副使杜重貴，送款於李昪，昪遣兵迎之。','新同杀冯杜，补送款李昪及遣兵迎。','徐知诰沿李昪同人，其他后授宣润本批不扩大录；同链送款动作可独立展示。',relation='adds')
for name in ['冯知兆','杜重贵']:
 next(x for x in B['people'] if x['key']==people[name])['death_year']=936
 claim('person',people[name],'death_year',name+'据旧新卢文进传在936年南奔前被杀。',69,'天福元年十二月，乃殺行軍司馬馮知兆、節度副使杜重貴等，率其部眾渡淮奔於金陵。','传记明确元年冬十二月，不借冲突的新帝纪来把死事改937。',source='jiuwudaishi-097-lu-wenjin-flight')
event('li_bian_receives_lu_submission','新卢传补卢文进送款李昪，李昪遣兵迎',69,'送款於李昪，昪遣兵迎之。',[('卢文进','送款者'),('徐知诰','遣兵迎者')],source='xinwudaishi-048-lu-wenjin-flight',when='新卢传天福元年冬（936）；帝纪另记次年正月',note='归吴时李昪当时名徐知诰，沿既有stable key，未写其本年已受禅称帝。')
# Paragraph 70: political pressure and speeches, followed by a separate Korean account.
add('li_bian_seeks_veteran_endorsement','徐知诰欲使李德诚、周本领众推戴',70,'徐知诰以','欲使之帅众推戴，',[('徐知诰','谋推戴者'),('李德诚','拟领众推戴者'),('周本','拟领众推戴者')],note='主李德诚职写荆南疑镇南，保原衔在摘录和校记，不将他合荆南高从诲或造新任命；欲与已表分。')
add('zhou_ben_objects_endorsement','周本称受杨氏先王大恩，不能再助推戴徐氏',70,'本曰：','可乎！”',[('周本','反对表态者')],note='先王大恩为周话，语境杨氏非徐温，未必对哪一王独立命名，不给杨行密捏在场。')
add('zhou_hongzuo_pressures_father','周弘祚强迫父亲周本参与推戴',70,'其子弘祚强之，','不得已',[('周弘祚','逼父参加者'),('周本','受子逼迫者')],note='弘祚沿周本其子补姓周，非此前监军张弘祚，父子明示可建有向父亲边。')
relationship('周本','周弘祚','父亲',70,'本曰：“我受先王大恩，自徐温父子用事，恨不能救杨氏之危，又使我为此，可乎！”其子弘祚强之，','其子上承周本，A父亲→B；未录匿名母或长幼。')
add('zhou_li_petition_wu_for_li_bian','周本与李德诚领将赴江都向杨溥上表，请为徐知诰行册命',70,'不得已与德诚','请行册命；',[('周本','被迫领表者'),('李德诚','同领诸将表者'),('吴主','受表的吴主'),('徐知诰','功德及册命所指对象')],place='江都',note='陈功德是表文内容，不同史家独立证其功德；请册命与后来正式禅位不同，未录为936已建唐国。')
add('zhou_li_jinling_quanjin','周本与李德诚再赴金陵劝进徐知诰',70,'又诣金陵劝进。',None,[('周本','同领劝进者'),('李德诚','同领劝进者'),('徐知诰','劝进对象')],place='金陵',note='又表赴金陵与此前江都表杨溥两场不同，地点不能全挂扬州。')
sup('zhou_li_jinling_quanjin',70,'xinwudaishi-062-zhou-quanjin','周本與諸將至金陵勸進，','新南唐世家也记周本赴金陵劝进。','新置天祚三年受禅后追写，主936及937再次劝进，可能压缩或另场，不能当逐日对应已确证；后憤惋而死不补936卒年。',relation='conflicts',field='time_original')
add('song_qiqiu_rebukes_li_merit','宋齐丘对李建勋称其父李德诚开国功业今扫地',70,'宋齐丘谓','今日扫地矣。”',[('宋齐丘','评价者'),('李建勋','听话的德诚之子'),('李德诚','评价指向父亲、未必在场')],note='扫地是宋对推戴的评价，不当已经撤勋官；太祖元勋语境吴杨氏开国不是宋朝赵匡胤。')
relationship('李德诚','李建勋','父亲',70,'宋齐丘谓德诚之子建勋曰：','德诚之子建勋明确，先查全站关系及方向修订后复用，原引用不改。')
add('wu_palace_omens_speech','史载吴宫多妖，杨溥忧吴祚将终，左右称天意',70,'于是吴宫多妖，','非人事也。”',[('吴主','忧国祚表态者')],note='多妖为古代史家异兆叙事，左右天意是当时言辞；非本站科学事实论断，未命名左右群臣。')
add('goryeo_wang_jian_defeats_neighbors','史载高丽王建击破新罗、百济',70,'高丽王建','用兵击破新罗、百济，',[('王建（高丽）','高丽王、出兵者')],when='936年末条下汇记；两国战事未各具独立日',place='高丽、新罗、百济',note='沿高丽王建稳定主体，不合前蜀王建；末条压缩两国事迹，不擅认两国都是936同日被军事灭亡。')
add('goryeo_extent_report','史载邻国附高丽，辖二京、六府、九节度、一百二十郡',70,'于是东夷诸国',None,[('王建（高丽）','史载高丽治者')],when='936年末条下概记；体制形成各日未载',place='高丽',note='数据只作本书史载概数和制度名称，未核近代边界或每郡清单；诸国皆附为古概称。')
reviews={54:'前河东财赋怨与壬午拘捕、甲申入宫赦、张刘例外、四人释放除名、刘自缢/捕杀、张斩及悔分录。成门疑字待核，逃南山只是意向。三名死年936有守卫修订。',55:'闽民无名引语，不把吾君猜名生成现场参与。',56:'乙酉朔河阳饯太相温及军归，旧大详衮同任务称谓异保，不合另一迪离毕。',57:'已死李从珂追降庶人，非在场再被废。',58:'丁亥冯道兼相，旧补司空守本官及宏文馆大学士。',59:'郑阮旧与新郑玩同曹州刺史、石重立杀链核异字；新补己丑。族害匿名，未造子女。',60:'辛卯姚顗任刑部，沿同人，无和新御札求言混一事。',61:'前五年经营屯田与内徙不机械从936推年；癸巳复朔方与旧灵武同职链，担忧取地不是已侵占。',62:'董与赵没为陷俘非死。秘杀董家、取财、自称留后、表称乱分；旧新补逐李彦琦和旧杀胡章。同名旧906延州胡章证不足不合，不提前录秘937死。',63:'门鐸规范简体门铎，主旧新同杀杨焚掠；杨卒936另修订。',64:'倍死后赠燕王送丧，旧补李肃前单州刺史，未当倍活受任。',65:'张朗率众朝，未推任官。',66:'周瑰旧帝纪周环异写，旧传同晋阳、计财、任三司辞才不济可允链核同人。937死不是已死936，不建重复主体；有命不等长期实际任。',67:'闻讣、旧传十二月辛巳卒、遣王巡抚分；主庚子条下闻与旧辛巳日疑差保，死年同936。王无平卢节度正式任已证。',68:'兴唐改广晋名称，不外推疆界。',69:'主936十二月辛丑、旧936十二月、新传元年冬、新纪937正月癸亥日年差并列。旧新补冯杜被杀、送款徐知诰迎兵，不把死亡对象作随行；匿名沿途主将不造名。',70:'徐推戴意向、周反对、子强、江都表吴、金陵劝进、宋评价、吴异兆言辞、高丽战与制度分。德诚荆南疑镇南原保未核；新周劝进于937受禅后压写不得硬对应。高丽王建不合蜀王，击破两国不自动定936同日灭。'}
contexts=[]
for d in sorted((P/'sources/context').iterdir()):
 rec=json.loads((d/'paragraph.json').read_text());f=d/'source.txt'
 contexts.append(dict(file=os.path.relpath(f,P/'sources'),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),paragraph_id=rec['id'],purpose='确认卷69前文传主张延朗，与刘延朗分清',url='https://github.com/greed-216/histree/blob/b603079e/'+str(f.relative_to(ROOT))))
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
assert not (P/'publication.json').exists(),'published builder must not rewrite an immutable archive'
for n in range(54,71):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=280,year=936,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(54,71)],next_paragraph='zztj-v281-y0937-p001',next_volume=281,next_year=937,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='连续第54—70段原59—75行：旧朝臣处分，晋朝任官、地方军变、送契丹归军与丧，卢文进奔吴，徐氏推戴及高丽汇记。全年度末17正文均逐段处理。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(54,71)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
