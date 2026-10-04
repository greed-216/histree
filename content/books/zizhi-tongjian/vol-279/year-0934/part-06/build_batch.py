# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 934 paragraphs 24–34."""
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
 specs.append((directory.name,directory,'fb64c2b0','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [
 ('tongjian-279-934-accession-aftermath',YEAR/'part-05/sources/library/tongjian-279-934-accession-aftermath','8468a699','司马光等'),
 ('jiuwudaishi-046-tax-and-death-reports',YEAR/'part-05/sources/library/jiuwudaishi-046-tax-and-death-reports','8468a699','薛居正等'),
 ('xinwudaishi-064-two-towns-join-shu',YEAR/'part-05/sources/library/xinwudaishi-064-two-towns-join-shu','8468a699','欧阳修'),
 ('jiuwudaishi-066-kang-surrender',YEAR/'part-04/sources/library/jiuwudaishi-066-kang-surrender','d4437e45','薛居正等'),
 ('xinwudaishi-008-congke-eastmarch',YEAR/'part-04/sources/library/xinwudaishi-008-congke-eastmarch','d4437e45','欧阳修'),
 ('xinwudaishi-027-liu-yanlang',YEAR/'part-03/sources/library/xinwudaishi-027-liu-yanlang','62cb1bdd','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-accession-aftermath']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0934-p024-p034',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    if key in {'jiuwudaishi-096-liu-suiqing','jiuwudaishi-093-li-zhuanmei','xinwudaishi-027-yao-death','xinwudaishi-047-chang-release'}:
        label={'jiuwudaishi-096-liu-suiqing':'卷96·刘遂清传','jiuwudaishi-093-li-zhuanmei':'卷93·李专美传','xinwudaishi-027-yao-death':'卷27·药彦稠传','xinwudaishi-047-chang-release':'卷47·苌从简传'}[key]
        record=dict(record,section_title=label,citation='《'+record['book']+'》'+label+'，段落 '+record['id']+'；传首及正文已核，纸本及异文待核。')
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
for n in range(24, 35):
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
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in {'jiuwudaishi-096-liu-suiqing','jiuwudaishi-093-li-zhuanmei','xinwudaishi-027-yao-death','xinwudaishi-047-chang-release'}:
        label={'jiuwudaishi-096-liu-suiqing':'卷96·刘遂清传','jiuwudaishi-093-li-zhuanmei':'卷93·李专美传','xinwudaishi-027-yao-death':'卷27·药彦稠传','xinwudaishi-047-chang-release':'卷47·苌从简传'}[source]
        record=dict(record,citation='《'+record['book']+'》'+label+'，段落 '+record['id']+'；传首及正文已核，纸本及异文待核。')
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷279·清泰元年（934；四月条下，改元前为应顺元年）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0934_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','蜀':'孟知祥','太后':'曹氏（李嗣源后）','太妃':'王淑妃','苌长简':'苌从简'}
NEW_ALIASES={'刘遂清':['劉遂清'],'郝琼':['郝瓊'],'韩昭胤':['韓昭胤','韩昭裔','韓昭裔'],'李专美':['李專美'],'刘琪（刘遂清父）':['劉琪（劉遂清父）']}

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
    if when is None:when='934年四月条下；确日未独载'
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




# Consecutive paragraphs 24–34: several short entries plus the withdrawal and reward dispute.
ev('shi_jingtang_comes_to_court','四月己卯石敬瑭入朝',24,'己卯，','石敬瑭入朝。',[('石敬瑭','入朝者')],when='934年四月己卯',place='洛阳',note='此前从卫州趋洛为行程，此段记实际入朝；不提前处理五月请归河东。')
ev('liu_xu_administers_three_commissions','四月庚辰刘昫受命判三司',25,'庚辰，','以刘昫判三司。',[('刘昫','判三司获任者'),('帝','命判三司者')],when='934年四月庚辰',place='洛阳',note='刘昫与旧本劉煦沿已核同一主体；判三司为此命，不把后文审计积年逋欠前移。')
ev('shu_changes_era_mingde','四月辛巳孟知祥改元明德',26,'辛巳，','改元明德。',[('蜀','改元明德者')],when='934年四月辛巳',place='蜀',note='主前句蜀在赦疑字保留；只录明确改元，不无证把在改大或判定赦免范围。新孟世家独立记四月改元明德，不具辛巳。')
ev('congke_summons_liu_suiqing_background','追记李从珂起兵凤翔时召刘遂清，刘迟疑未至',27,'帝之起凤翔也，','迟疑不至。',[('帝','召兴州刺史者'),('刘遂清','兴州刺史、迟疑未至者')],when='934年起兵凤翔时的追叙；本句未独载月日',place='凤翔、兴州',note='同年本次起兵背景，召与未至分层于同句；不当刘其时已到洛阳，也不补迟疑原因。')
ev('liu_suiqing_collects_garrisons_returns','刘遂清闻李从珂入洛，集三泉等四处戍兵归朝',27,'闻帝入洛，','桑林戍兵以归，',[('刘遂清','集四处戍兵归朝者')],place='三泉、西县、金牛、桑林',note='归朝为文中行程，实际入朝在癸未另录；四戍名逐字保，不猜人数及具体现代地点。')
ev('southern_towns_abandoned_go_to_shu','刘遂清弃散关以南城镇，诸城镇皆为蜀人所有',27,'自散关','皆为蜀人所有。',[('刘遂清','撤兵弃城镇者'),('蜀','得到城镇的政权君主')],place='散关以南城镇',note='皆为蜀人所有是主概述，不扩成每城同日被武力攻占；孟知祥为蜀主，不当其亲自攻城。')
ev('liu_suiqing_comes_to_court','四月癸未刘遂清入朝',27,'癸未，','入朝，',[('刘遂清','入朝者')],when='934年四月癸未',place='洛阳')
ev('congke_plans_to_punish_suiqing','李从珂欲治刘遂清之罪',27,'帝欲治','其罪，',[('帝','欲治罪者'),('刘遂清','拟被治罪者')],when='934年四月癸未',place='洛阳',note='欲是意向，下一句赦免，不记已定罪行刑。')
ev('congke_pardons_suiqing_return','李从珂因刘遂清能自行归朝而赦免他',27,'以其能自归，','乃赦之。',[('帝','因自归而赦者'),('刘遂清','被赦者')],when='934年四月癸未',place='洛阳',note='本句明载赦由自归，保这一个理由，不扩成此前弃城无责或新授官职。')
relationship('刘遂清','刘鄩','侄子',27,span(27,'遂清。','鄩之侄也。'),'主明说鄩之侄；A—侄子→B表示刘遂清是刘鄩的侄子。父辈长幼未载，不反建伯父或叔父。')
ev('zhang_ye_enters_xingyuan_yangzhou','四月甲申张业率兵进入兴元、洋州',28,'甲申，','将兵入兴元、洋州。',[('张业','蜀将、领兵入两州者')],when='934年四月甲申',place='兴元、洋州',note='与前段遣兵屯大漫天迎降为不同阶段；此段才记入州，不泛称攻破城池。')
ev('congke_changes_era_qingtai','四月乙酉李从珂改元清泰',29,'乙酉，','改元，',[('帝','改元者')],when='934年四月乙酉',place='洛阳',note='主本句只改元，清泰名称由卷年标题及旧末帝纪具体改应顺为清泰的制书补证；不是乙亥即位时已改。')
ev('congke_general_amnesty','四月乙酉李从珂大赦',29,'乙酉，','大赦。',[('帝','大赦者')],when='934年四月乙酉',place='后唐',note='主大赦明确，与第26段蜀在赦疑文分开；旧补常赦不原者亦赦，实际释放名单未载。')
ev('hao_qiong_provisionally_heads_privy','四月丁亥郝琼权判枢密院',30,'丁亥，','郝琼权判枢密院，',[('郝琼','主称宣徽南院使、权判枢密院获任者'),('帝','命权判者')],when='934年四月丁亥',place='洛阳',note='权判不当已正式授枢密使；旧本原宣徽北院改南院并权判，主原称南院，职序差并列。')
ev('wang_mei_north_xuanhui','四月丁亥王玫从前三司使转任宣徽北院使',30,'前三司使王玫','为宣徽北院使，',[('王玫','前三司使、获宣徽北院使者'),('帝','任官者')],when='934年四月丁亥',place='洛阳',note='前三司与现任北院区别，不能把此前报府数百万当仍掌三司新任；不直接造刘昫和王玫的排挤边。')
ev('han_zhaoyin_adviser_duanming','四月丁亥韩昭胤受左谏议大夫并充端明殿学士',30,'凤翔节度判官','充端明殿学士。',[('韩昭胤','原凤翔节度判官、获谏议大夫及端明学士者'),('帝','任官者')],when='934年四月丁亥',place='洛阳',note='旧同日同职作韓昭裔，新刘延朗传及本主作昭胤，同职同阶段据以匹配，保两个书名形，不另造韩昭裔。')
ev('congke_executes_kang_yicheng','四月戊子李从珂斩康义诚',31,'戊子，','康义诚，',[('帝','下令斩者'),('康义诚','河阳节度使、判六军诸卫兼侍中，被斩者')],when='934年四月戊子',place='地点本段未详（旧传补兴教门外）',note='前段暂宥与今斩分；行刑地点由旧康传补，不以当前河阳节度职位推其死在河阳。')
ev('congke_exterminates_kang_clan','李从珂诛灭康义诚族',31,'斩河阳节度使、','灭其族。',[('帝','族灭命令归责者'),('康义诚','被灭族的康氏主体')],when='934年四月戊子',place='地点未详',note='族灭范围未逐名，不编人数、亲属姓名或每人同一行刑方式。')
ev('congke_executes_yao_yanchou','四月己丑李从珂杀药彦稠',32,'己丑，','诛药彦稠。',[('帝','杀药彦稠的君主'),('药彦稠','被杀者')],when='934年四月己丑',place='地点未详',note='主今己丑、旧末帝纪戊子削夺诏提药、新废帝纪戊子康药并杀，诏书与实际行刑异说分列；不把旧削夺诏直接当行刑已完成。')
ev('congke_releases_wang_jingkan','四月庚寅李从珂释放王景戡',33,'庚寅，','释王景戡、苌长简。',[('帝','释放者'),('王景戡','被释放者')],when='934年四月庚寅',place='地点未详',note='此前被部下执降为另一动作，今释放才独载；并列苌从简另录。')
ev('congke_releases_chang_congjian','四月庚寅李从珂释放苌从简',33,'庚寅，','释王景戡、苌长简。',[('帝','释放者'),('苌长简','被释放者')],when='934年四月庚寅',place='地点未详',note='本主苌长简字形保；此前同卷同案作苌从简，新苌传同兵溃被执、废帝责其不降而释，复用已有从简，不自动将从长视为繁简转换。')
ev('officials_collect_sixty_thousand','有司多方征民财，仅得六万',34,'有司百方','仅得六万，',[],place='洛阳',note='此阶段六万主未再写单位，语境承赏军钱财，不补新独立币值；与先前数日数万及后总集二十万是不同层次，不相加重复算。')
ev('congke_imprisons_patrol_commissioner','李从珂发怒，将军巡使下狱并昼夜督责',34,'帝怒，','昼夜督责，',[('帝','下军巡使狱、督责的君主')],place='洛阳',note='军巡使未具名，不强套既有京城巡检安从进；军巡使与京城巡检不同职称。')
ev('forced_collection_imprisons_and_suicides','征财囚系满狱，贫者出现自缢、投井',34,'囚系满狱，','自经、赴井。',[],place='洛阳',note='此为主所述征财后果，无具体人数姓名，不伪造统计或每案具体执行官。')
ev('soldiers_show_arrogance_in_markets','军士游市肆显露骄色',34,'而军士游','皆有骄色，',[],place='洛阳市肆',note='主对军士态度的叙述，不写每个军人都实际犯罪。')
ev('residents_criticize_soldiers_rewards','市民聚集责骂军士，质问为什么百姓被逼出财作赏',34,'市人聚诟之曰：','独不愧天地乎！”',[],place='洛阳市肆',note='这是市人责骂的转述，含反诘讥刺，不据为军士真有主力战功或百姓各案事实的独立证据。')
ev('court_uses_stores_contributions_regalia','朝廷竭左藏旧物与诸道贡献，并取太后太妃器服簪珥，才集二十万缗',34,'是时，','才及二十万缗，',[('太后','器服簪珥被用于筹赏者'),('太妃','器服簪珥被用于筹赏者')],place='洛阳',note='主器物皆出与旧太后太妃出衣服助军互证；不说两人本人盘点或亲自出售各物，不把总额当已经发给军士。')
ev('congke_blames_li_zhuanmei_for_reward_shortfall','李专美夜直时，李从珂因赏军财不足责问其才何用',34,'帝患之，','留才安所施乎！”',[('帝','责问者'),('李专美','夜直、被责问者')],place='洛阳宫中',note='夜直未给独日，不强定壬辰前一夜；君主责备不是李专美真实主管三司的依据。')
ev('li_zhuanmei_disclaims_reward_responsibility','李专美自谦才劣，表示军赏不给并非其责',34,'专美谢曰：','非臣之责也。',[('李专美','答辩军赏非己责者'),('帝','听答者')],place='洛阳宫中',note='这是李的自辩，不外推最终依法责任判定。')
ev('li_zhuanmei_explains_treasury_exhaustion','李专美认为长兴末频赏、山陵及出师耗尽府藏，骄卒欲望难满',34,'窃思自长兴之季，','而得天下。',[('李专美','分析府藏与骄卒者'),('帝','听分析者')],place='洛阳宫中',note='史载进言中的因果分析，不生成各事件确定因果边；从珂拱手得天下也是此人论述。')
ev('li_zhuanmei_urges_laws_over_repeated_rewards','李专美劝李从珂修法度、立纪纲，警告再困百姓可能危及存亡',34,'夫国之存亡，','存亡未可知也。',[('李专美','劝修纪纲并警告者'),('帝','受劝者')],place='洛阳宫中',note='警告和原则是进言，不当亡国已发生或从珂已经完成制度改革。')
ev('li_zhuanmei_proposes_limit_rewards','李专美请按现有财力均给，不必全践原许赏数额',34,'今财力尽于此矣，','何必践初言乎！”',[('李专美','提出量财均给者'),('帝','受建议者')],place='洛阳宫中',note='均给是据现存財而给的原则，后诏仍分将校、军人和在京三档，不误写所有人同额。')
ev('congke_accepts_li_reward_proposal','李从珂认可李专美的量财给赏建议',34,'帝以','为然。',[('帝','认可建议者'),('李专美','建议获认可者')],place='洛阳宫中',note='认可与壬辰具体赏诏分别。')
ev('congke_rewards_yang_yin_commanders','四月壬辰诏赏杨思权、尹晖等各二马一驼、钱七十缗',34,'壬辰，','钱七十缗，',[('帝','下诏给赏者'),('杨思权','凤翔归命将校、七十缗等获赏对象'),('尹晖','凤翔归命将校、七十缗等获赏对象')],when='934年四月壬辰',place='洛阳',note='诏定待遇，不当财货已送到每人手中；等不补其余未名将校名单。')
ev('congke_rewards_fengxiang_soldiers_twenty','四月壬辰诏凤翔归命军人钱二十缗',34,'下至军人','钱二十缗，',[('帝','下诏给军人二十缗者')],when='934年四月壬辰',place='洛阳',note='承上归命者等级，普通军人二十与将校七十不同，不补未名军人数量。')
ev('congke_rewards_capital_soldiers_ten','四月壬辰诏在京军人各钱十缗',34,'其在京者','各十缗。',[('帝','下诏给在京军人十缗者')],when='934年四月壬辰',place='洛阳',note='诏语与前两档分开，不把在京者也当凤翔归命普通军人二十缗。')
ev('soldiers_grumble_bodhisattva_iron_song','军士仍怨望，以除菩萨扶生铁作谣',34,'军士无厌，','有悔心故也。',[],place='洛阳',note='歌谣原文保；主说闵帝仁弱、从珂刚严及悔心为史家解释，不让已死闵帝在当场参与唱谣。')

oldappoint='jiuwudaishi-046-934-cleansing';oldreward='jiuwudaishi-046-934-reward-edict'
oldsui='jiuwudaishi-096-liu-suiqing';oldli='jiuwudaishi-093-li-zhuanmei';newyao='xinwudaishi-027-yao-death';newchang='xinwudaishi-047-chang-release'
oldtax='jiuwudaishi-046-tax-and-death-reports';oldkang='jiuwudaishi-066-kang-surrender';newchron='xinwudaishi-008-congke-eastmarch';newshu='xinwudaishi-064-two-towns-join-shu';newliu='xinwudaishi-027-liu-yanlang'
def excerpt(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);return t[a:t.index(end,a)+len(end)]
def supp(code,source,start,end,text,n,relation='corroborates',note='同一主体及动作对照，电子本纸本及异文待核。'):
 claim('event','event_zztj_279_0934_'+code,'description',text,n,excerpt(source,start,end),note,source=source,relation=relation)
supp('liu_xu_administers_three_commissions',oldtax,'庚辰，','以宰臣劉煦判三司。','旧末帝纪同庚辰刘煦判三司，沿已核刘昫别名。',25)
supp('shu_changes_era_mingde',newshu,'四月，','知祥改元曰明德。','新孟知祥世家同四月改元明德，无具体日与赦范围。',26)
q=excerpt(oldsui,'劉遂清，','父琪，以鴻臚卿致仕。')
claim('person',people['刘遂清'],'description','《旧五代史》刘遂清传载其字得一、青州北海人、为刘鄩犹子，父琪以鸿胪卿致仕。',27,q,'旧传独立谱系、籍贯与字可补，犹子与主侄吻合；其后引通鉴潞王纪的撤兵整段是依赖转引，不能计作独立第二确证。',source=oldsui,relation='adds')
relationship('刘琪（刘遂清父）','刘遂清','父亲',27,q,'父琪在刘遂清传头明载；以父子关系消歧命名，不和其他同名刘琪自动合并。父退休年份未明，不另造934退休事件。',source=oldsui)
claim('person',people['刘遂清'],'description','《旧五代史》载刘遂清早在梁为保銮军使，庄宗入汴不改职；明宗时历典易、棣及淄、兴、登等郡。',27,excerpt(oldsui,'遂清少敏惠，','咸有善政。'),'前职按原书顺序补人物经历，不用934作全部任官年份，善政为史书评价。后晋官职和开运死亡为后来主线暂不新增事件。',source=oldsui,relation='adds')
# Explicitly mark the dependent Tongjian quotation in the old biography.
supp('congke_pardons_suiqing_return',oldsui,'〈（《通鑒潞王紀》：','乃赦之。）〉','旧刘传附注转引通鉴潞王纪的撤戍、归朝及赦免整段，可作传注索引。',27,relation='adds',note='这是明确引用通鉴的后加附注，非旧史正文独立证据；不将它算成两部独立史料共同证明此细节。')
supp('congke_changes_era_qingtai',oldappoint,'乙酉，','為清泰元年，','旧末帝纪具体记乙酉明堂宣制，改应顺元年为清泰元年。',29,relation='adds')
supp('congke_general_amnesty',oldappoint,'大赦天下，','咸赦除之。','旧补大赦天下、常赦不原者亦赦。',29,relation='adds')
supp('congke_general_amnesty',newchron,'乙酉，','大赦，改元。','新废帝纪同乙酉大赦改元。',29)
supp('hao_qiong_provisionally_heads_privy',oldappoint,'丁亥，','權判樞密院；','旧记郝琼从宣徽北院使转南院并权判枢密，主以南院使为其原职。',30,relation='conflicts',note='同人同日权判一致，原北与主原南职序不同保来源；权判不是正式枢密使。')
supp('wang_mei_north_xuanhui',oldappoint,'以前三司使','王玫為宣徽北院使。','旧同王玫前三司转宣徽北院。',30)
supp('han_zhaoyin_adviser_duanming',oldappoint,'鳳翔節度判官韓昭裔','充端明殿學士；','旧同丁亥韩昭裔由凤翔节度判官任谏议及端明学士，主昭胤为同人異名。',30,relation='adds',note='同日同出身职务及同一授职行动支持同人；别名昭裔保原字，不由胤裔近义自动合人。')
claim('person',people['韩昭胤'],'aliases','韩昭胤在《旧五代史》此授职条作韩昭裔。',30,excerpt(oldappoint,'鳳翔節度判官韓昭裔','充端明殿學士；'),'同日同前职同新职的实名异写，用别名匹配而不另建重复主体。',source=oldappoint,relation='adds')
claim('person',people['韩昭胤'],'description','《新五代史》刘延朗传记韩昭胤为李从珂在凤翔的节度判官，与李专美等共谋。',30,excerpt(newliu,'劉延朗，','皆此五人謀之。'),'补先前角色背景，同传的初为追叙；不得当丁亥才共谋起兵，也不由共事造亲属或永久盟友边。',source=newliu,relation='adds')
supp('congke_executes_kang_yicheng',oldappoint,'戊子，','康義誠伏誅。','旧末帝纪同戊子康义诚伏诛。',31)
supp('congke_executes_kang_yicheng',oldkang,'清泰元年四月，','斬於興教門外，','旧康传补四月斩在兴教门外。',31,relation='adds',note='补处刑地点，不以本人河阳任职推地点；本传本句未有干支。')
supp('congke_exterminates_kang_clan',oldkang,'清泰元年四月，','夷其族。','旧康传同四月斩并夷族。',31)
supp('congke_executes_yao_yanchou',newchron,'戊子，','殺康義誠及藥彥稠。','新废帝纪将杀康、药并在戊子，主康戊子药己丑分日。',32,relation='conflicts',note='日期归并与主一日后杀药差异保，不擅改主干支。')
supp('congke_executes_yao_yanchou',oldappoint,'是日，詔曰：','仍削奪官爵雲。','旧末帝纪戊子诏列药彦稠等罪并削夺官爵，保诏文宣告，不作为独立已行刑证据。',32,relation='adds',note='诏言宜行显戮及削夺官爵与实际执行时间区分，朱冯孟王此前已死，更不能把此诏全视作当日死亡。')
supp('congke_executes_yao_yanchou',newyao,'潞王從珂反，','已而殺之。','新药传同记兵败东走、被俘囚华州、后被杀，未给独日。',32)
supp('congke_releases_chang_congjian',newchang,'廢帝舉兵於鳳翔，','廢帝釋之，','新苌传同凤翔兵溃后东走被执、因不敢二心答而获释，可校主体从简。',33,relation='adds',note='新此段不具庚寅，不把此前主与王同被部下执、后释的层次改成一个确定捕俘流程。其后拜颍团练为补传叙事，本次只引用到释之。')
claim('person',people['苌从简'],'description','本底本庚寅释人条作苌长简，前同案及《新五代史》苌从简传对应已有苌从简。',33,span(33,'庚寅，','苌长简。'),'从、长是疑字，非繁简转换；同卷被执释放上下文与新传对应同主体，原文保持长字，纸本待核。')
supp('forced_collection_imprisons_and_suicides',oldtax,'至是，以府藏空匱，','京城庶士自絕者相繼。','旧末帝纪同记府藏空、配率下京城士庶相继自绝。',34,relation='adds',note='旧此处置丙子丁丑征率条后，不当所有人的具体自尽日；主贫者自经赴井更细，两处不编人数。')
supp('court_uses_stores_contributions_regalia',oldtax,'癸未，','以助賞軍。','旧末帝纪癸未太后太妃出宫中衣服器用助赏军，主此处概述收集到二十万。',34,relation='adds',note='旧给出器服单项日期，不把总集二十万或李夜直也全部定癸未。')
supp('congke_blames_li_zhuanmei_for_reward_shortfall',oldli,'初，末帝起自鳳翔，','留才術何施也！」','旧李传同记许厚赏、库不足与率民、李宿禁中被召责才无用，补帝说词。',34,relation='adds',note='库二三万与主前段金帛三万为书内数字差；只作旧独立记述，不将数据倒填此前批次或把主数字改成区间。')
supp('li_zhuanmei_disclaims_reward_responsibility',oldli,'專美惶恐待罪，','非臣之罪也。','旧李传同答财库空、赏不给非己罪。',34)
supp('li_zhuanmei_urges_laws_over_repeated_rewards',oldli,'臣以爲國之存亡，','存亡未可知也。','旧李传记宜刑政及赏功罚罪，不可为赏无赖军困民，补进言内容。',34,relation='adds')
supp('li_zhuanmei_proposes_limit_rewards',oldli,'今宜取見在財賦','希茍悅。」','旧李传同请取现存财赋给军，不必践前言。',34)
supp('congke_accepts_li_reward_proposal',oldli,'末帝然之。','由專美之敷揚也。','旧李传补从珂采纳、军虽不满而洛阳户民获免鞭笞的效果。',34,relation='adds',note='旧因专美敷扬是本传归因及成效叙述，主未独载完全解除征率，保旧来源，不造无争议的因果边。')
supp('congke_rewards_yang_yin_commanders',oldreward,'壬辰，詔賜','錢帛各有差。','旧末帝纪正文同壬辰诏赏禁军及凤翔归命将校，未在正文列具体数额。',34,relation='adds',note='后附通鉴注有二马一驼七十等数字，依赖主书，不当第二份独立数字验证。')
supp('soldiers_grumble_bodhisattva_iron_song',oldreward,'初，帝離岐下，','其無厭如此。','旧正文同至京赏不满而作谣，歌词为去却生菩萨、扶起一条铁，与主除去菩萨、扶立生铁不同措辞。',34,relation='adds',note='两种歌词措辞并列，不擅改为同一字句；旧正文期不次赏与主悔仁弱异叙保。')
q=excerpt(oldli,'李專美，','京兆萬年人也。')
claim('person',people['李专美'],'description','《旧五代史》李专美传载其字翊商、京兆万年人。',34,q,'字及籍贯据传首，未经地理坐标核对，不把万年直接当出生点。',source=oldli,relation='adds')
claim('person',people['李专美'],'description','旧传记李专美不游科举，以父樞覆试被落为缘由；梁时为陆浑尉、舞阳令，后从李从珂移凤翔为记室。',34,excerpt(oldli,'專美少篤學文，','遷爲記室。'),'这是此前经历补证，原父樞名保原字，不随意补科举中第年份；梦占内容是传中故事，不录为已实现的预言。',source=oldli,relation='adds')
# Both deaths have explicit year and separate sources; do not overwrite the reused person rows.
for name,code,n in [('康义诚','congke_executes_kang_yicheng',31),('药彦稠','congke_executes_yao_yanchou',32)]:
 c=next(x for x in B['claims'] if x['subject_key']=='event_zztj_279_0934_'+code and x['field_path']=='description')
 quote=c['note'][3:].split('；核对说明：',1)[0]
 claim('person',people[name],'death_year',name+'于934年本条被杀。',n,quote,'只增有出处的死亡年份引用，保旧主体和档案；药日期异说不改变共同本年。')

reviews={24:'己卯实际入朝，与前段趋洛及后五月留归分。',25:'庚辰刘昫判三司，旧煦为已有别名；后逋欠核查不前移。',26:'辛巳蜀改元明德明确，新世家四月同；在赦疑字保，不自行改大或判赦范围。',27:'凤翔召未至、闻入洛集四戍归、散关以南弃为蜀有、癸未入朝欲罚赦分别；同年战事追记不泛定当日。主遂清为鄩侄，旧传犹子父琪谱系补；旧附引通鉴段为依赖证据不计独立。刘琪父名以关系消歧，不补退休年。',28:'甲申张业入两州，与前遣屯迎不同阶段，不当全州均同日被攻破。',29:'乙酉改元大赦，清泰具体名旧制补，旧新同日；不前移乙亥登基。',30:'丁亥郝权判、王玫北院、韩谏议端明分；权非正式枢密使。旧郝北改南与主原南职序不同；主韩胤旧裔同职同日另列别名，新刘传胤同前职。',31:'戊子康斩与族灭分，前宥今杀；地点旧补兴教门外，不凭河阳职猜地点，族无名单不编。',32:'主己丑药死、新戊子康药一起、旧戊子削夺诏非实际行刑证明，保异说；新药传囚华州后杀无独日。',33:'庚寅王和苌释放分别，长简与前从简、新苌传同凤翔被执获释对应复用；不是繁简互换，原长字待纸。新释后拜颍团练本次不前移到主当日。',34:'征财六万、军巡使被囚督、贫者自经投井、市人责骂、出库贡献和太后太妃器服总二十万、李夜直受责答辩进言采纳、壬辰三档诏赏、仍怨作谣分。钱财层次不混算，未名军巡不当安巡检。市谩言为引语，李归因警告非确定因果；均給原则不当三档同额。旧器服癸未不带夜直定日，旧李效果补但非主明文完全解除征率，旧赏数字附引通鉴依赖不独证。'}
contexts=[]
for directory in sorted((P/'sources/context').iterdir()):
 r=json.loads((directory/'paragraph.json').read_text());contexts.append(dict(file=os.path.relpath(directory/'source.txt',P/'sources'),sha256=hashlib.sha256((directory/'source.txt').read_bytes()).hexdigest(),paragraph_id=r['id'],purpose='传首核对；不向后主线自动新增传中往事',url='https://github.com/greed-216/histree/blob/fb64c2b0/'+str((directory/'source.txt').relative_to(ROOT))))
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(24,35):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(24,35)],next_paragraph='zztj-v279-y0934-p035',next_volume=279,next_year=934,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷279连续934年第24—34正文段，原29—39行；入朝判三司、蜀明德、撤戍弃地归朝赦、张入两州、改元赦及授职、康药杀与王苌释、征财进言三档诏赏。第35段明宗葬待录，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(24,35)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
