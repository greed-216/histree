# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 280, year 936 paragraphs 42–47."""
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
 if directory.name=='jiuwudaishi-070-zhang-jingda':continue
 specs.append((directory.name,directory,'660186cb','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('liaoshi') else '欧阳修'))

specs += [('jiuwudaishi-070-zhang-jingda',ROOT/'content/books/zizhi-tongjian/vol-278/year-0932/part-03/sources/library/jiuwudaishi-070-zhang-jingda','747dcc12','薛居正等'),('tongjian-280-936-sang-rescue-plans',YEAR/'part-06/sources/library/tongjian-280-936-sang-rescue-plans','7ec8616b','司马光等'),('jiuwudaishi-048-dan-militia',YEAR/'part-06/sources/library/jiuwudaishi-048-dan-militia','7ec8616b','薛居正等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-280-936-sang-rescue-plans','tongjian-280-936-defeat-retreat']
B = {'format_version': 1, 'batch_key': 'zztj-v280-y0936-p042-p047',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-070-kang-death':'卷70·康思立传','jiuwudaishi-070-zhang-jingda':'卷70·张敬达传','jiuwudaishi-070-zhang-burial':'卷70·张敬达传','jiuwudaishi-076-jin-advance':'卷76·晋高祖纪（石敬瑭）','jiuwudaishi-081-chonggui-family':'卷81·晋少帝纪（石重贵）','jiuwudaishi-098-zhao-surrender':'卷98·赵德钧传','xinwudaishi-027-kang-death':'卷27·康思立传','liaoshi-003-relief-defeat':'卷3·太宗纪','liaoshi-076-gao-mohan':'卷76·高模翰传','jiuwudaishi-048-dan-militia':'卷48·唐末帝纪（李从珂）'}
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
prior_sources={x['key']:x for f in [YEAR/'part-06/content-batch.json',ROOT/'content/books/zizhi-tongjian/vol-278/year-0932/part-03/content-batch.json'] for x in json.loads(f.read_text())['sources']}
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/280.txt').read_text().splitlines()
for n in range(42, 48):
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
    labels={'jiuwudaishi-070-kang-death':'卷70·康思立传','jiuwudaishi-070-zhang-jingda':'卷70·张敬达传','jiuwudaishi-070-zhang-burial':'卷70·张敬达传','jiuwudaishi-076-jin-advance':'卷76·晋高祖纪（石敬瑭）','jiuwudaishi-081-chonggui-family':'卷81·晋少帝纪（石重贵）','jiuwudaishi-098-zhao-surrender':'卷98·赵德钧传','xinwudaishi-027-kang-death':'卷27·康思立传','liaoshi-003-relief-defeat':'卷3·太宗纪','liaoshi-076-gao-mohan':'卷76·高模翰传','jiuwudaishi-048-dan-militia':'卷48·唐末帝纪（李从珂）'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '闰十一月条下'
        citation = f'卷280·后唐清泰三年／后晋天福元年（936；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_280_0936_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_ALIASES={'石重贵':['石重貴'],'石敬儒':[],'安氏（石重贵母）':['安氏'],'高谟翰':['高謨翰','高模翰'],'张彦琦':['張彥琦'],'时赛':['時賽']}

ALIASES.update({'汉主':'刘岩','吴主':'杨溥','杨光远':'杨檀','景岩':'刘景岩','刘延郎':'刘延朗','李赞华':'耶律倍','李懿':'李懿（后唐亲将）'})

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
    if when is None:when='936年闰十一月条下；确日未独载'
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

add('jinyang_sorties_fail','晋安被围数月，高行周、符彦卿数次率骑出战无功',42,'晋安寨被围数月，','皆无功。',[('高行周','多次出战者'),('符彦卿','多次出战者')],when='936年晋安被围期间，甲子降前；各次出战日未载',place='晋安寨',note='众寡不敌为主解释，数不硬定次数，与九月城外初战分，未战死不造阵亡。')
add('jinyang_famine_horses','晋安刍粮尽，喂马、马互啖、死马分食，援兵未到',42,'刍粮俱竭，','援兵竟不至。',[],when='936年晋安围内粮竭，闰十一月甲子降前',place='晋安寨',note='削A081是转录占位，不据其造器物实体；保原引，旧有削木篩糞，另补不是悄悄改原字。')
sup('jinyang_famine_horses',42,'jiuwudaishi-070-zhang-jingda','始則削木篩糞，以飼其馬，日望朝廷救軍，及漸羸死，則與將士分食之，馬盡食殫。','旧张传记削木筛粪喂马、死马分食。','旧概述马尽与主降时近五千需分叙述阶段和异说，不能计算剩余全归零。',relation='adds')
sup('jinyang_famine_horses',42,'jiuwudaishi-048-dan-militia','軍士毀居屋茅、淘馬糞、削鬆甗以供秣飼，馬尾鬛相食俱盡。','旧唐纪列屋茅、马粪、削松甗饲马。','鬆甗底本字形保，不依字猜已核物种或把主占位强改。',relation='adds')
claim('person',person('张敬达',42,'被围招讨主帅','张敬达性刚，时谓之“张生铁。”'),'aliases','主记张敬达性刚，人称张生铁。',42,'张敬达性刚，时谓之“张生铁。”','沿已有张敬达与生铁别名；性刚为史叙，不当心理诊断。')
claim('person',people['张敬达'],'aliases','旧张传称字志通、小字生铁。',42,'張敬達，字志通，代州人，小字生鐵。','生铁为小字与主时称兼容，现有张志通、生铁别名保，代州籍不当战地。',source='jiuwudaishi-070-zhang-jingda')
add('yang_an_urge_surrender','杨光远、安审琦劝张敬达降契丹',42,'杨光远、安审琦，','劝敬达降于契丹，',[('杨光远','劝降者'),('安审琦','劝降者'),('张敬达','被劝降者')],when='936年闰十一月甲子前围寨粮竭时',place='晋安寨',note='杨光远沿杨檀已有主体，劝降不是每个人随后已共同执行杀将。')
add('jingda_refuses_waits_relief','张敬达称受两帝恩、不愿降，暂待援兵；势穷可杀己携首降',42,'敬达曰：','未为晚也。”',[('张敬达','拒降并提出困极杀己条件者')],when='936年闰十一月甲子前围寨粮竭时',place='晋安寨',note='旦暮援到为敬达预计，不当救援真已临门；条件杀己不推其主动此时自杀；明宗及今上是已故李嗣源与现李从珂，非石。')
sup('jingda_refuses_waits_relief',42,'jiuwudaishi-070-zhang-jingda','待勢窮，則請殺吾，攜首以降，亦未為晚。','旧同拒降、待穷可杀己携首。','条件话与实际斩首分事件，不能据此称已完成自愿投降。')
add('yang_signals_kill_an_hesitates','杨光远示意安审琦杀张敬达，安未忍',42,'光远目审琦','审琦未忍。',[('杨光远','示意杀将者'),('安审琦','未忍者')],when='936年闰十一月甲子前',note='未忍主明确，后旧与辽共同杀说另外保存，不把其据主认定个人动刀。')
add('gao_protects_jingda','高行周知杨欲杀张，常率壮骑尾随保护',42,'高行周知光远','尾而卫之，',[('高行周','护卫者'),('张敬达','受保护者')],when='936年闰十一月甲子前',place='晋安寨',note='常尾护不造友情或终身效忠边；高知杨意为主叙。')
add('jingda_questions_gao_stops','张敬达不明高保护用意，发问后高不敢再跟随',42,'敬达不知其故，','行周乃不敢随之。',[('张敬达','发问者'),('高行周','停止随护者')],when='936年闰十一月甲子前',note='原不敢随不是正式处罚高行周，未具命罢其军职。')
add('yang_kills_jingda','闰十一月甲子杨光远趁高行周、符彦卿未至斩张敬达',42,'诸将每旦集于','斩敬达首，',[('杨光远','主所记斩将者'),('张敬达','被杀主帅')],when='936年闰十一月甲子',place='晋安寨',note='高与符未至只作情境不当实际参加杀将；杨对应既有杨檀。')
sup('yang_kills_jingda',42,'jiuwudaishi-076-jin-advance','閏十一月甲子，晉安寨副招討使楊光遠等殺上將張敬達，以諸軍來降。','旧晋纪同甲子杨等杀张降。','等未具每个执行姓名，不自动据等认安亲自持刀。')
sup('yang_kills_jingda',42,'liaoshi-003-relief-defeat','閏月甲子，楊光遠、安審琦殺敬達以降。','辽明确杨光远与安审琦共同杀张降。','与主安未忍、后杨斩有叙法差异，作为辽说并列，不改主参与边。',relation='conflicts')
sup('yang_kills_jingda',42,'jiuwudaishi-070-zhang-jingda','光遠、審琦知敬達意未決，恐坐成魚肉，遂斬敬達以降。','旧张传也合写杨、安斩张降。','作者叙动机恐鱼肉，不当二人自述；主未忍和合杀说保。',relation='conflicts')
add('yang_submits_troops_khitan','杨光远率诸将上表降契丹',42,'帅诸将上表','降于契丹。',[('杨光远','率将上表降者'),('耶律德光','契丹受降一方')],when='936年闰十一月甲子',place='晋安寨',note='杀将、向契丹降、之后将卒交石三层分，不能当甲子已经赵父子降。')
add('deguang_rewards_taunts_surrender','德光慰劳降将赐裘帽，又戏称吃战马万匹，杨等惭',42,'契丹主素闻诸将名，','光远等大惭。',[('耶律德光','慰赐与戏言者'),('杨光远','受慰赐、惭一方')],when='936年闰十一月甲子降后',place='晋安寨',note='万匹是戏语史载概数，不能拿来计算实吃整万或每位同样获何种帽；与降时余马不同。')
add('deguang_buries_praises_jingda','德光称张敬达忠，命葬祭并劝诸将效之',42,'契丹主嘉张敬达之忠，','当效敬达也。”',[('耶律德光','葬祭命与忠评价者'),('张敬达','获葬祭者')],when='936年闰十一月甲子被杀后',note='获葬者不是生时参加仪式；忠为德光评，不补正式追谥。')
sup('deguang_buries_praises_jingda',42,'liaoshi-003-relief-defeat','上聞敬達至死不變，謂左右曰：「凡為人臣，當如此也！」命以禮葬。','辽同嘉不变命礼葬。','上沿太宗德光，礼葬不具具体墓址，不填经纬。')
sup('deguang_buries_praises_jingda',42,'jiuwudaishi-070-zhang-burial','契丹主告其部曲及漢之降者曰：「為臣當如此人！」令部人收葬之。','旧同告降者效张、命收葬。','旧未独载祭祀，主祭另证，末帝哀慟在本传另补。')
event('congke_mourns_jingda','旧张传补李从珂闻张敬达死而悲恸',42,'末帝聞其歿也，愴慟久之。',[('李从珂','闻死悲恸者')],source='jiuwudaishi-070-zhang-burial',when='936年闻张敬达死后；独立报告日未载',note='旧末帝是李从珂，不是新晋帝；与第44段己巳知降报告不能无证当同一日。')
add('khitan_takes_jinyang_equipment','主记降时马近五千、铠仗五万，契丹取回国',42,'时晋安寨马犹','取以归其国，',[],when='936年闰十一月甲子降后',place='晋安寨',note='铠仗五万原未明确套件单位不猜五万套；取归动作与送马给晋辽异说分。')
sup('khitan_takes_jinyang_equipment',42,'jiuwudaishi-048-dan-militia','時馬猶有五千匹，戎王主以漢軍與石敬瑭，其馬及甲仗即齎驅出塞。','旧唐纪同剩马五千、马甲驱出塞，汉军与石。','主近五千，旧五千，概数和整数不同保；戎王主疑王主重字不擅改。')
sup('khitan_takes_jinyang_equipment',42,'liaoshi-003-relief-defeat','所降軍士及馬五千匹以賜晉帝。','辽说降卒及五千马赐晋帝。','与主、旧唐纪剩马取出塞不合，作为处分异说，不强辩同一批马有两去向。',relation='conflicts')
add('deguang_hands_troops_to_shi','德光将后唐降将卒交石敬瑭，命勉事新主',42,'悉以唐之将卒','勉事而主。”',[('耶律德光','交将卒者'),('帝','受将卒者')],when='936年闰十一月甲子降后',note='兵卒匿名不逐个造人员，不额外创几万总数；此帝沿新晋石。')
add('kang_sili_dies_after_surrender','康思立闻降愤惋而死',42,'马军都指挥使康思立','愤惋而死。',[('康思立','主记愤惋而死者')],when='936年闰十一月甲子降寨后；独立卒日未载',note='主愤惋为叙述情境，不当正式医学死因或被契丹诛杀。')
sup('kang_sili_dies_after_surrender',42,'jiuwudaishi-070-kang-death','俄而楊光遠以大軍降於太原，思立因憤激，疾作而卒焉。','旧康传称因愤激疾作卒。','旧病情不具诊断与卒地点，不能外推心脏病。',relation='adds')
sup('kang_sili_dies_after_surrender',42,'xinwudaishi-027-kang-death','未至，而敬達死，楊光遠降晉，思立疾，卒于道。','新康传说援军未至、康病卒道路。','补未到围寨及卒于道，不能把主段次认康在晋安被杀。',relation='adds')
E['jin_posthumous_kang_honor']=event('jin_posthumous_kang_honor','旧康传补晋高祖为康思立辍朝一日、赠太子少师',42,'晉高祖即位，追其宿舊，為輟朝一日，贈太子少師。',[('石敬瑭','辍朝追赠者'),('康思立','获追赠者')],source='jiuwudaishi-070-kang-death',when='晋高祖即位、康卒后；具体年月日未独载',year=None,note='传体即位表述非再次登坛，赠令确日未载，不强系甲子；未写亲生友情。')
sup('jin_posthumous_kang_honor',42,'xinwudaishi-027-kang-death','晉高祖入立，贈太子少師。','新同入立后赠太子少师。','新未具辍朝一日，只补同追赠。')
add('shi_notifies_surrender','石敬瑭以晋安已降遣使告各州',42,'帝以晋安已降，','遣使谕诸州。',[('帝','遣使者')],when='936年闰十一月甲子降后',note='诸州笼统无全名单，别猜某宣诏官；此次使者与此前致书何福、吕都不同。')
add('zhang_lang_kills_jin_envoy','代州刺史张朗斩晋使',42,'代州刺史张朗','斩其使；',[('张朗','斩使者')],when='936年闰十一月晋安降后',place='代州',note='复用全站后唐张朗，非张敬达；匿名使臣不造人，不录公元确日。')
add('lv_qi_kills_jin_envoy_xinzhou','奉唐诏劳军吕琦至忻州，遇晋使斩之',42,'吕琦奉唐主诏','亦斩之，',[('吕琦','劳军途中斩使者')],when='936年闰十一月晋安降后',place='忻州',note='此前犒赵都统与当前劳北军相续任务无证不能直接同事件，杀使主体吕非刺史丁。')
add('lv_qi_urges_wutai_retreat','吕琦劝丁审琦率兵民由五台奔镇州',42,'谓刺史丁审琦曰：','自五台奔镇州。”',[('吕琦','建议撤退者'),('丁审琦','受议忻州刺史')],place='忻州、五台、镇州',note='还日无全理是吕预计，不当所有民将死已证；建议路线与实际哪条路分。')
add('ding_shenqi_refuses_retreat','临行丁审琦反悔，闭牙城不从',42,'将行，','闭牙城不从。',[('丁审琦','反悔闭城者')],place='忻州',note='闭牙城不是现在逃至镇州，未造整体所有忻州兵跟他。')
add('lv_qi_prevents_internal_assault','州兵欲攻丁，吕琦劝止相屠而率州兵往镇州',42,'州兵欲攻之，','趣镇州，',[('吕琦','劝止内斗并率队者')],place='忻州、镇州',note='欲攻是意向、未记实际攻陷；率州兵不推已带全城百姓或哪条五台路真正完成。')
add('ding_shenqi_surrenders_khitan','丁审琦降契丹',42,'审琦遂','降契丹。',[('丁审琦','投降者')],place='忻州',note='吕队去镇与丁降并列，不把丁认为随吕队去镇；契丹受降个人未明不猜高谟。')
# Death years on reused people are published as claims, with guarded revisions later.
for name,quote,note in [('张敬达','光远乘其无备，斩敬达首，','主甲子明被杀，旧及辽归本年，不因杀者异说改变卒年。'),('康思立','马军都指挥使康思立愤惋而死。','主旧新明本年降寨后卒；无独立卒日，不把甲子作为其具体死日。')]:
 claim('person',people[name],'death_year',name+'于936年去世。',42,quote,note)

add('deguang_recommends_sang_chancellor','德光称桑维翰尽忠，建议石敬瑭任桑为相',43,'契丹主谓帝曰：','宜以为相。”',[('耶律德光','荐相者'),('帝','受议者'),('桑维翰','被荐者')],note='忠评价归德光，建议与丙寅相命分动作，非德光独立行晋相诏。')
add('zhao_ying_jin_chancellor','闰十一月丙寅赵莹任门下侍郎同平章事',43,'丙寅，','并同平章事；',[('赵莹','获相命者')],when='936年闰十一月丙寅',note='同句含桑官另记；不是上批己亥翰林初任。')
sup('zhao_ying_jin_chancellor',43,'jiuwudaishi-076-jin-advance','丙寅，制以翰林學士承旨、知河東軍府、戶部侍郎、知制誥趙瑩為門下侍郎同中書門下平章事，監修國史。','旧同日赵相命，补监修国史。','前职全列是旧前任，不当此时新任另一翰林；新兼监修独立補。',relation='adds')
add('sang_jin_chancellor','闰十一月丙寅桑维翰任中书侍郎同平章事，仍权知枢密',43,'桑维翰为中书侍郎，','仍权知枢密使事。',[('桑维翰','获相命兼枢密者')],when='936年闰十一月丙寅',note='仍权知与上批原权命相接，不能略成此次正式枢密使。')
sup('sang_jin_chancellor',43,'jiuwudaishi-076-jin-advance','以翰林學士、權知樞密事、禮部侍郎、知制誥桑維翰為中書侍郎、同中書門下平章事、集賢殿大學士，依前知樞密院事，並賜推忠興運致理功臣。','旧补桑集贤殿大学士，赵桑并赐功臣号。','并承赵桑，不具旁人；旧依前知与主仍权知原衔并列，功臣号不是父子或盟友边。',relation='adds')
add('yang_jin_guards_commander','杨光远任侍卫马步军都指挥使',43,'以杨光远为','侍卫马步军都指挥使，',[('杨光远','投降后获晋命者')],when='936年闰十一月丙寅条下',note='同年唐副招讨与现晋守军职分，沿杨檀已改名别名，不建新杨光远。')
add('liu_zhiyuan_baoyi_inspector','刘知远任保义节度使、侍卫马步军都虞侯',43,'以刘知远为','侍卫马步军都虞侯。',[('刘知远','获晋新命者')],when='936年闰十一月丙寅条下',note='本次都虞侯和上批都指挥使不同职位，不顺手改前批；原侯字保不擅改候。')
add('shi_asks_son_to_hold_hedong','石敬瑭将南下，向德光咨询留一子守河东；德光令诸子出供选',43,'帝与契丹主将引兵而南，','自择之。',[('帝','问留守人选者'),('耶律德光','令出诸子择者')],place='河东',note='将南下为准备阶段，不当已经入洛，诸子未名不根据晚年名单补在场者。')
add('chonggui_family_background','主追述石重贵为石敬瑭兄子，敬儒早卒后石养为子',43,'帝兄子重贵，','貌类帝而短小，',[('石重贵','被叙侄子及养子身份者'),('石敬瑭','养育者')],year=None,when='石重贵幼年家庭背景；生父卒、收养确年未载',note='名字石据家族身份与旧少帝纪核，敬儒亡者只录关系不当936在场；貌类是主叙外貌不作遗传验证。')
relationship('石敬儒','石重贵','父亲',43,'帝兄子重贵，父敬儒早卒，帝养以为子，','敬儒为石敬瑭兄、重贵生父，主养关系另录，不给敬儒卒年936。')
relationship('石敬瑭','石重贵','养父',43,'帝兄子重贵，父敬儒早卒，帝养以为子，','帝石敬瑭明确养以为子，方向养父→养子，不逆建第二条。')
relationship('石敬儒','石敬瑭','兄长',43,'帝兄子重贵，父敬儒早卒，','兄子+父敬儒相接明长幼；从子不是敬儒也是其养子。')
sup('chonggui_family_background',43,'jiuwudaishi-081-chonggui-family','少帝，名重貴，高祖之從子也。考諱敬儒，母安氏，以唐天祐十一年六月二十七日生帝於太原汾陽裏。敬儒嘗為後唐莊宗騎將，早薨，高祖以帝為子。','旧少帝纪同生父敬儒、养父高祖，补母安氏和出生记载。','高祖石、少帝重贵，不能互换两个帝；旧从子泛侄，主兄子明长幼。',relation='adds')
relationship('安氏（石重贵母）','石重贵','母亲',43,'考諱敬儒，母安氏，以唐天祐十一年六月二十七日生帝於太原汾陽裏。','旧少帝纪明母安氏，专名限定重贵母，不与其他皇后安氏混；不明是否为敬儒正式妻，不造夫妻边。',source='jiuwudaishi-081-chonggui-family')
row=next(x for x in B['people'] if x['name']=='石重贵');assert row['key'] not in reused;row['birth_year']=914
claim('person',row['key'],'birth_year','石重贵生于唐天祐十一年（914）。',43,'以唐天祐十一年六月二十七日生帝於太原汾陽裏。','据旧少帝本纪确年天祐十一为914；原月日仍保阴历，不换算公历月日。',source='jiuwudaishi-081-chonggui-family')
claim('person',row['key'],'description','旧少帝纪记石重贵生于太原汾阳里。',43,'以唐天祐十一年六月二十七日生帝於太原汾陽裏。','保当时地名，未核现代坐标；出生地不是留守官职所在地的新推断。',source='jiuwudaishi-081-chonggui-family')
add('deguang_selects_chonggui','德光指石重贵称大目者可留守',43,'契丹主指之曰：','此大目者可也。”',[('耶律德光','择留守者'),('石重贵','被选择者')],note='大目是外貌选择原话，非已具能力考核成败证明。')
add('chonggui_beijing_regent','石重贵任北京留守、太原尹、河东节度使',43,'乃以重贵为','河东节度使。',[('石重贵','获留守官命者')],when='936年闰十一月丙寅条下、南下前',place='太原、河东',note='北京为太原，此河东命与辽选人非现代北京；现仍石之养子不提前他为皇帝。')
sup('chonggui_beijing_regent',43,'jiuwudaishi-081-chonggui-family','遂以帝為北京留守，授金紫光祿大夫、檢校司徒，行太原尹，知河東管內節度觀察事。','旧少帝纪同留守太原，具知河东节度观察事、散阶检校官。','旧帝代称重贵，当时任命者仍石；主河东节度、旧知管内事叙法并列。',relation='adds')
add('gao_mohan_vanguard','契丹用高谟翰为前锋，与唐降卒同进',43,'契丹以其将高谟翰','与降卒偕进。',[('高谟翰','契丹前锋将领')],note='辽本传高模翰按同936太原战争、同军身份核为异写，前锋不是全部降卒皆其私属关系。')
claim('person',people['高谟翰'],'aliases','主高谟翰与辽传高模翰按同战争同契丹将身份核为同人。',43,'高模翰，一名松，渤海人。','名模谟異写非简单繁简。结合本传天显十一张敬达、石敬瑭、降寨战争人物链核身份；不提前扩录后946等战争。',source='liaoshi-076-gao-mohan')
claim('person',people['高谟翰'],'description','辽高模翰传记其渤海人、一名松。',43,'高模翰，一名松，渤海人。','补明确籍与异名，不把太祖平渤海的叙时全部定在此936。',source='liaoshi-076-gao-mohan')
add('tuanbai_relief_army_rout','闰十一月丁卯契丹至团柏与唐军战，赵父子先逃，符张二刘随后、军众踩踏大溃',43,'丁卯，',None,[('赵德钧','先退者'),('赵延寿','先退者'),('符彦饶','继退者'),('张彦琦','继退者'),('刘延朗','继退者'),('刘在明','继退者')],when='936年闰十一月丁卯（主）；辽庚午追击、辛未过谷异时序',place='团柏',note='主先循疑先遁，结合后南奔及旧溃走记作退逃，原不改；死者万计为概述非确数，各将退不当各亲手踩死人。')
sup('tuanbai_relief_army_rout',43,'liaoshi-003-relief-defeat','庚午，僕射蕭酷古只奏趙德鈞等諸援兵將遁，詔夜發兵追擊。德鈞等軍皆投戈棄甲，自相蹂踐，擠于川谷者不可勝紀。','辽把奏将遁和夜追系庚午，记弃甲践踏。','主丁卯战退与辽庚午追击分期异说，不把奏报日和原溃日定成同日。',relation='adds',field='time_original')
sup('tuanbai_relief_army_rout',43,'liaoshi-003-relief-defeat','辛未，兵度團柏谷，以酒肴祀天地。俄追及德鈞父子，乃率眾降。','辽辛未过团柏、后追及赵父子降。','主丁卯到团柏与辽辛未过谷日有异，不用两记制造二次一模一样决战。',relation='conflicts',field='time_original')
sup('tuanbai_relief_army_rout',43,'jiuwudaishi-098-zhao-surrender','及楊光遠以晉安寨降於契丹，德鈞父子自團柏谷南走潞州，一行兵士，投戈棄甲，自相騰踐，死者萬計。','旧赵传同降寨后赵父子南走、军乱踩踏万计。','旧不具丁卯独立日，概数不硬定10000整数；后去潞另有地理阶段。')
add('liuyanlang_zaiming_report_defeat','闰十一月己巳刘延朗、刘在明到怀州，李从珂始知石已帝与杨降',44,'己巳，','杨光远降。',[('刘延朗','到怀州传消息者'),('刘在明','到怀州传消息者'),('唐主','始知者')],when='936年闰十一月己巳',place='怀州',note='帝这里指石、唐主李；己巳是到达获知，不当石即位或杨降发生日。')
add('court_proposes_weizhou_refuge','众议称天雄完整、契丹惮山东，建议车驾赴魏州',44,'众议以','车驾宜幸魏州。”',[],note='众议未名，不猜所有宰相主张；秘惮原字保，畏惮是群臣估计非契丹正式声明。',place='魏州',when='936年闰十一月己巳到怀州报告后议')
add('congke_consults_li_song','李从珂因李崧与范延光相善召问迁驾',44,'唐主以李崧','召崧谋之。',[('唐主','召议者'),('李崧','被召者')],note='善为史载私人相善，但不据此次一句增永久盟友边；范未在场不作此召议参与。')
add('li_song_sends_xue_away','薛文遇继至，帝怒变色，李崧踩其足示退，薛离去',44,'薛文遇不知','文遇乃去。',[('薛文遇','继至被示退者'),('唐主','怒色者'),('李崧','示薛退者')],note='蹑足是示意具体行为，未添打架案，薛不知原未明所不知全部内容。')
add('congke_threatens_xue_li_dissuades','李从珂称几欲拔刀刺薛，李崧批薛浅谋但刺更丑',44,'唐主曰：“我见','刺之益丑。”',[('唐主','述刺意者'),('李崧','劝勿刺者')],note='几欲不当已刺、肉颤为帝原话不诊断病；文遇小人为李崧评价。')
add('congke_accepts_south_return','李崧劝李从珂南还，帝采纳',44,'崧因劝',None,[('李崧','劝南还者'),('唐主','采纳者')],note='当前采纳与壬申实际到河阳分阶段，不造已当日回洛阳。')
add('luoyang_residents_flee','洛阳闻北军败，居民惊而四逃山谷',45,'洛阳闻北军败，','逃窜山谷。',[],place='洛阳、山谷',note='原居人无名与数，不虚拟全城总人口或所有民都跑；听闻日未独载。')
add('chongmei_allows_flight','守门者请禁居民出，雍王李重美称不应禁求生，令任去，众稍安',45,'门者请禁之，',None,[('李重美','河南尹雍王、准居民去者')],place='洛阳',note='此前封雍与姓名已存；不若、事宁自还是其政见及预计，差安不当全城永久安定，匿名门者不猜具体城门官。')
add('congke_returns_heyang_defense','闰十一月壬申李从珂到河阳，命诸将分守南北城',46,'壬申，','南、北城。',[('唐主','到达及分守命者')],when='936年闰十一月壬申',place='河阳南北城',note='诸将无名单不把前被败各将全部在河阳命令里；到河阳不当已到洛。')
add('zhang_yanlang_proposes_huazhou','张延朗请李从珂赴滑州以接魏博，帝犹豫未决',46,'张延朗请',None,[('张延朗','提出滑州方案者'),('唐主','未决者')],when='936年闰十一月壬申条下',place='滑州',note='滑非华，计划未行不在地图画成已完成去滑路线。')
add('zhaos_flee_luzhou','赵德钧、赵延寿南奔潞州，败兵陆续跟随',47,'赵德钧、','稍稍从之，',[('赵德钧','南奔者'),('赵延寿','南奔者')],place='潞州',note='承团柏溃后旅程，与战退事件分地点阶段，不按稍稍估确人数。')
add('shi_sai_returns_yuyang','赵军将时赛率卢龙轻骑东回渔阳',47,'其将时赛','东还渔阳。',[('时赛','率轻骑东回者')],place='渔阳',note='时赛是人名，非每时比赛行为；此主所属赵属军，不把东回算随赵南去潞。')
sup('shi_sai_returns_yuyang',47,'jiuwudaishi-098-zhao-surrender','時德鈞有愛將時賽，率輕騎東還漁陽，其部曲尚千餘人，與散亡之卒俱集於潞州。','旧记爱将时赛东回，又述部曲千余与散卒潞州集。','其部曲代称可回指赵或时，原有歧义，不把千余硬定时赛东还骑兵数。',relation='adds')
add('shi_sends_gao_prepare_food','石敬瑭先遣昭义节度使高行周回潞州备粮',47,'帝先遣','还具食，',[('帝','遣先备粮者'),('高行周','昭义节度使、受遣者')],place='潞州',when='936年闰十一月甲戌晋军至潞州之前',note='回具食是任务，后告城中无斗粟不可直接证明备粮已成功；先前唐昭义衔沿原，不创造另次晋首任。')
add('gao_advises_zhao_receive_jin','高行周城下见赵父子，称乡人告无粮宜迎石驾',47,'至城下，','速迎车驾。”',[('高行周','告粮况劝迎者'),('赵德钧','被劝者'),('赵延寿','城上父子另一人')],place='潞州城',note='无斗粟可宁疑可食，旧可食明；作为高告而非实测仓储，乡曲不造血亲乡族边。')
sup('gao_advises_zhao_receive_jin',47,'jiuwudaishi-098-zhao-surrender','城中無鬥粟可食，請大王速迎車駕，自圖安計，無取後悔焉。','旧高忠告作无斗粟可食、速迎车驾。','可食补主疑可宁字，原不改；呼大王指赵北平王不是当时正式唐天子。',relation='adds')
add('jin_khitan_arrive_luzhou','闰十一月甲戌石敬瑭与德光至潞州',47,'甲戌，','至潞州，',[('帝','抵潞州者'),('耶律德光','抵潞州者')],when='936年闰十一月甲戌',place='潞州')
sup('jin_khitan_arrive_luzhou',47,'jiuwudaishi-076-jin-advance','甲戌，車駕至昭義，受趙德鈞、延壽降。','旧晋纪同甲戌至昭义受赵降。','昭义治潞同史行政层，保两地原称不多出第二程；旧无高河地名补明日。')
add('zhaos_greet_at_gaohe','赵父子于高河迎拜石敬瑭，德光慰谕，石不理问安',47,'德钧父子迎谒','亦不与之言。',[('赵德钧','迎拜问安者'),('赵延寿','迎拜者'),('耶律德光','慰谕者'),('帝','不理者')],when='936年闰十一月甲戌条下',place='高河',note='不顾不言为具体反应不推永久敌对关系；契丹慰谕并不代表随后免囚。')
sup('zhaos_greet_at_gaohe',47,'jiuwudaishi-098-zhao-surrender','高祖至，德鈞父子迎謁於馬前，高祖不禮之。','旧同父子迎马前、石不礼。','旧不具高河仅印证行为，不将未礼化为已处决。')
add('deguang_kills_silver_saddle_unit','德光问银鞍契丹直所在，赵指示后命杀潞州西郊三千',47,'契丹主谓德钧曰：','凡三千人。',[('耶律德光','询问并命杀者'),('赵德钧','指示部队所在者')],when='936年闰十一月甲戌条下到潞州后',place='潞州西郊',note='三千为银鞍契丹直人数，非所有唐降兵全部或全契丹族人数；赵指示不是本人持刀执行，匿名执行者不造人。')
sup('deguang_kills_silver_saddle_unit',47,'jiuwudaishi-098-zhao-surrender','德鈞指示之，契丹盡殺於潞之西郊，遂鎖德鈞父子入蕃。','旧赵传同指队、西郊尽杀再锁赵父子。','旧段正文未具三千数，只补行为地点；数字主独载，不虚说两书都确三千。')
add('zhaos_shackled_sent_khitan','赵德钧、赵延寿被锁送契丹',47,'遂琐德钧、',None,[('赵德钧','被锁送者'),('赵延寿','被锁送者')],when='936年闰十一月甲戌条下受降后',note='琐疑锁，旧鎖明，原保；送归命及行程不当该日在北都已见述律，下一段追叙另处理。')

reviews={42:'粮竭削A081占位保，旧正文削木筛粪等并列。杨安劝降、安未忍、护张、甲子杨杀、辽旧合杀不同叙法保。军马处置主旧出塞与辽赐晋异说保；康病卒于道、无独卒日。唐主李从珂与晋帝石分；张朗丁审琦吕及忻州去镇/留降角色分。',43:'丙寅赵桑相命与旧额外兼衔、杨刘新命分。石重贵生父敬儒、养父石、祖母未知；旧明确母安氏另限定。兄长边有主兄子与父敬儒相接依据，亲属追叙不把收养或父卒定936。北京太原不现代京。高谟高模同契丹将；主丁卯团柏与辽庚午追/辛未过不同阶段日期保。',44:'己巳为刘二人回怀州与帝始知报告，不当晋即位或杨降日。众魏州建议未名不猜，李薛会议、未刺、采南还分，不创造已刺罪案。',45:'主雍王重美沿李重美已封雍，河南尹职与许可居民出分；众稍安不当全部民都不逃。',46:'壬申到河阳与守两城命，张滑州计划未决分；滑非华州，魏博是方略接应非已实现。',47:'赵南奔潞与时赛东回分，旧其部曲千余回指歧义不硬定时赛骑数；高准备粮、告无粮、甲戌受降、银鞍三千被杀、赵锁送分。原可宁及琐留校核，旧可食鎖补；不认当天已见太后。'}
contexts=[]
for d in sorted((P/'sources/context').iterdir()):
 rec=json.loads((d/'paragraph.json').read_text());f=d/'source.txt'
 contexts.append(dict(file=os.path.relpath(f,P/'sources'),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),paragraph_id=rec['id'],purpose='确认康思立、赵德钧传主；不扩录整段其他年度生平',url='https://github.com/greed-216/histree/blob/660186cb/'+str(f.relative_to(ROOT))))
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(42,48):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=280,year=936,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(42,48)],next_paragraph=Q[48]['id'],next_volume=280,next_year=936,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='连续第42—47段原47—52行：晋安粮竭杀将降军、晋官留守、团柏溃败、唐帝南还和潞州赵父子降囚。后23段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(42,48)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
