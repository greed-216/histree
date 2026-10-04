# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 934 paragraphs 19–23."""
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
 if directory.name=='jiuwudaishi-066-song-lingxun':continue
 specs.append((directory.name,directory,'8468a699','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [('jiuwudaishi-066-song-lingxun',YEAR.parent.parent/'vol-278/year-0933/part-07/sources/library/jiuwudaishi-066-song-lingxun','1ab64add','薛居正等'),('tongjian-279-934-weizhou',YEAR/'part-04/sources/library/tongjian-279-934-weizhou','d4437e45','司马光等'),('xinwudaishi-008-congke-eastmarch',YEAR/'part-04/sources/library/xinwudaishi-008-congke-eastmarch','d4437e45','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-weizhou','tongjian-279-934-accession-aftermath']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0934-p019-p023',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    if key.startswith('songshi-262-'):record=dict(record,section_title='卷262·赵上交传',citation='《宋史》卷262·赵上交传，段落 '+record['id']+'；EPUB卷题李濤傳沿卷内另一传主，正文已回查赵上交传，纸本待核。')
    if key=='xinwudaishi-048-conghou-death':record=dict(record,section_title='卷48·王弘贽传',citation='《新五代史》卷48·王弘贽传，段落 '+record['id']+'；前段传首与同一EPUB分部已核，纸本及异文待核。')
    if key=='xinwudaishi-015-kong-empress':record=dict(record,section_title='卷15·孔皇后传',citation='《新五代史》卷15·孔皇后传，段落 '+record['id']+'；前项孔皇后标题与正文已核，纸本及异文待核。')
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
for n in range(19, 24):
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
    if source=='xinwudaishi-048-conghou-death':record=dict(record,citation='《新五代史》卷48·王弘贽传，段落 '+record['id']+'；传首及同一EPUB分部已核，纸本及异文待核。')
    if source=='xinwudaishi-015-kong-empress':record=dict(record,citation='《新五代史》卷15·孔皇后传，段落 '+record['id']+'；孔皇后标题与正文已核，纸本及异文待核。')
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷279·清泰元年（934；四月条下，改元前为应顺元年）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0934_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'潞王':'李从珂','王':'李从珂','帝':'李从珂','闵帝':'李从厚','少帝':'李从厚','太后':'曹氏（李嗣源后）','太妃':'王淑妃','蜀主':'孟知祥','孔妃':'孔氏（李从厚妃）','秦王':'李从荣'}
NEW_ALIASES={'王玫':[],'王峦':['王巒']}

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




# Consecutive paragraphs 19–23. Plans, petitions, commands and executions stay separate.
ev('zhang_leaves_sun_in_xingyuan','追记张虔钊讨凤翔时，留孙汉韶守兴元',19,'山南西道节度使','守兴元。',[('张虔钊','山南西道节度使、留守安排者'),('孙汉韶','武定节度使、受留守兴元者')],when='934年讨凤翔时的追叙；本句未独载月日',place='兴元',note='留守是原出讨时安排，不当四月新授武定节度使；前批出讨已录，此处只补留守安排。')
ev('zhang_returns_xingyuan_after_defeat','张虔钊败后奔回兴元',19,'虔钊既败，','奔归兴元，',[('张虔钊','败后奔归者')],place='兴元',note='此句承凤翔兵败；只记奔归，不重建前批凤翔战败事件。')
ev('zhang_sun_submit_two_towns_to_shu','张虔钊、孙汉韶举两镇之地降蜀',19,'与汉韶','降于蜀；',[('张虔钊','山南西道降者'),('孙汉韶','武定降者'),('蜀主','受两镇降的君主')],place='山南西道、武定',note='两镇以两人前列节度对应，不扩写当日所有州县均已交割。主四月条下无独日，新孟知祥世家置三月事后，分别保留。')
ev('shu_sends_li_zhao_to_lizhou','孟知祥命李肇率五千兵还利州迎接降镇',19,'蜀主命奉銮','还利州，',[('蜀主','遣兵迎降者'),('李肇','奉銮肃卫马步都指挥使、昭武节度使、奉命领五千兵者')],place='利州',note='命令与抵达分；五千为主书军数，李肇既有职衔不当本句新授。')
ev('shu_sends_zhang_ye_to_damantian','孟知祥命张业率一万兵屯大漫天迎接降镇',19,'右匡圣','以迎之。',[('蜀主','遣兵迎降者'),('张业','右匡圣马步都指挥使、宁江节度使、奉命领一万兵者')],place='大漫天',note='此为遣军屯驻安排；尚待后段甲申入兴元洋州，不提前把抵达两州写入此处。')
ev('congke_reaches_jiangqiao','四月壬申李从珂到蒋桥，百官在路旁列班迎接',20,'壬申，','百官班迎于路，',[('潞王','到蒋桥受迎者')],when='934年四月壬申',place='蒋桥')
ev('congke_defers_meeting_before_coffin','李从珂传教尚未拜梓宫，暂不可与百官相见',20,'传教以','未可相见。',[('潞王','传教暂缓相见者')],when='934年四月壬申',place='蒋桥',note='暂缓相见不当最终拒绝所有朝见；随后西宫班见另录。')
ev('feng_first_petition_accession_arrival','冯道等在李从珂入洛时上笺劝进',20,'冯道等皆','上笺劝进。',[('冯道','上笺劝进者'),('潞王','被劝进者')],when='934年四月壬申',place='洛阳',note='这是第一轮笺，随后班见再劝进分录；劝进不当已即位。')
ev('congke_visits_dowager_and_taifei','李从珂入宫谒见曹太后与王太妃',20,'王入谒','太后、太妃，',[('潞王','入谒者'),('太后','受谒太后'),('太妃','受谒太妃')],when='934年四月壬申',place='洛阳宫中',note='沿已有曹氏和花见羞主体，不因太后称号新增亲生母子关系。')
ev('congke_cries_at_coffin_explains','李从珂赴西宫伏梓宫恸哭，陈述来京缘由',20,'诣西宫，','自陈诣阙之由。',[('潞王','哭梓宫、陈述者')],when='934年四月壬申',place='西宫',note='此句未转述缘由具体内容，不补拟陈词；梓宫承明宗丧事，不把死者列为当场参与者。')
ev('feng_officials_audience_congke_returns_bow','冯道率百官班见，李从珂答拜',20,'冯道帅','王答拜。',[('冯道','率百官班见者'),('潞王','答拜者')],when='934年四月壬申',place='洛阳')
ev('feng_second_petition_accession','冯道等在班见后再次上笺劝进',20,'道等复','上笺劝进，',[('冯道','再次劝进者'),('潞王','再次被劝进者')],when='934年四月壬申',place='洛阳')
ev('congke_declares_wait_for_emperor_return','李从珂声称将等待李从厚返京及园寝礼毕，再还守藩镇',20,'王立谓道等曰：','甚无谓也！”',[('潞王','作此声明者'),('冯道','听声明者')],when='934年四月壬申',place='洛阳',note='声明及将来打算按原话呈现，不当已经迎还闵帝或退回藩镇；不臆断真假动机。')
ev('dowager_deposes_conghou_e','四月癸酉曹太后下令废李从厚为鄂王',21,'癸酉，','废少帝为鄂王，',[('太后','下令废帝者'),('少帝','被废为鄂王者')],when='934年四月癸酉',place='洛阳',note='这是废黜及降封命令，不等于李从厚已死；旧闵纪记七日而旧末帝纪与主同癸酉，日期异说并列。')
ev('dowager_authorizes_congke_state_affairs','曹太后命李从珂知军国事，暂用书诏印施行',21,'以潞王','权以书诏印施行。',[('太后','命监理军国事者'),('潞王','被命知军国事、暂用书诏印者')],when='934年四月癸酉',place='洛阳',note='知军国事与后来即位分；权用书诏印不扩写已经取得所有皇帝名位。')
ev('officials_wait_for_blame_congke_restores_posts','百官在至德宫门待罪，李从珂命各复其位',21,'百官诣','王命各复其位。',[('潞王','令百官复位者')],when='934年四月癸酉',place='至德宫门',note='各复位不编未名官员名单或新的具体职位。')
ev('dowager_orders_congke_accession','四月甲戌曹太后下令李从珂宜即皇帝位',21,'甲戌，','宜即皇帝位；',[('太后','命宜即位者'),('潞王','受即位令者')],when='934年四月甲戌',place='洛阳',note='正式即位在乙亥，不能把甲戌令当已完成登基。')
ev('congke_accession_at_coffin','四月乙亥李从珂在柩前即皇帝位',21,'乙亥，','即位于柩前。',[('潞王','柩前即位者')],when='934年四月乙亥',place='洛阳西宫',note='主本句只写柩前，西宫由前段和旧末帝纪补证；此段未改元，后续乙酉改元另录。旧闵纪五日与旧末帝纪乙亥六日不合，保异说。')
ev('congke_promises_hundred_min_on_arrival','追记李从珂自凤翔出发时，许入洛后每名军士赏钱一百缗',22,'帝之发凤翔也，','入洛人赏钱百缗。',[('帝','向军士许赏者')],when='934年自凤翔出发时的追叙；本句未独载月日',place='凤翔',note='许赏是承诺，不当已经足额给付；前批李从厚二百缗承诺为另一主体另一次行动。')
ev('congke_questions_wang_mei_treasury','李从珂入洛后问王玫府库实数，王答有数百万',22,'既至，','对有数百万在。',[('帝','询问府库者'),('王玫','三司使、报数者')],place='洛阳',note='数百万为王玫报告而非实盘，本句没有在这个报数后独载货币单位，不补缗字。')
ev('treasury_audit_thirty_thousand','核查府库后，金帛不过三万两、匹，估计赏军需五十万缗',22,'既而阅实，','计应用五十万缗。',[('帝','赏军需求所涉君主')],place='洛阳府库',note='金、帛计量为两、匹，赏军需求以缗计，不把三种量直接相加或等值换算；主未指具体盘库执行人。')
ev('wang_mei_proposes_collect_residents_money','李从珂发怒，王玫请征京城居民财物以补赏军',22,'帝怒，','以足之，',[('帝','因实数不足发怒者'),('王玫','请率民财者')],place='洛阳',note='请议与数日后征得数目分；旧末帝纪另记丙子诏河南府率民财。')
ev('capital_collection_only_tens_thousands','征集数日，仅得数万缗',22,'数日，','仅得数万缗，',[],place='洛阳',note='主此处数万为初次收集阶段，不以尚待后段总得六万及总集二十万回填本句。')
ev('congke_asks_balance_rewards_people','李从珂向执政表示军须赏、民须恤，询问如何处理',22,'帝谓执政曰：','今将奈何？”',[('帝','向执政询策者')],place='洛阳',note='这是君主询策语句，不当已解决赏军与民生矛盾。')
ev('ministers_propose_five_months_rent_advance','执政请按房屋征率，士庶自住或租住者皆预借五个月租金，李从珂同意',22,'执政请','从之。',[('帝','同意预借租金者')],place='洛阳',note='五月僦直是五个月租金，不是农历五月。执政未具名，不径指冯道等个人为本次主议者；建议、批准及征收结果区分。')
ev('wang_hongzhi_moves_conghou_office','王弘贽将李从厚安置到州廨',23,'王弘贽迁','帝于州廨，',[('王弘贽','迁置闵帝者'),('闵帝','被迁到州廨者')],place='卫州州廨',note='迁置发生在杀前，本句未给独日，不硬定戊寅。')
ev('congke_sends_wang_luan_poison','李从珂遣殿直王峦往卫州鸩杀李从厚',23,'帝遣弘贽','殿直峦往鸩之。',[('帝','遣使鸩杀者'),('王峦','殿直、奉命往卫州者'),('闵帝','被谋鸩杀者')],place='卫州',note='帝承新即位李从珂；往鸩是命令及意图，主随后拒饮、缢杀另录，不当毒杀已成。')
ev('wang_luan_arrives_silent','四月戊寅王峦到卫州谒李从厚，被问来意而不答',23,'戊寅，','不对。',[('王峦','到卫州而不答来意者'),('闵帝','问来意者')],when='934年四月戊寅',place='卫州')
ev('wang_hongzhi_offers_poison_conghou_refuses','王弘贽数次进酒，李从厚知有毒，拒绝饮用',23,'弘贽数进酒，','不饮，',[('王弘贽','数次进酒者'),('闵帝','知毒拒饮者')],when='934年四月戊寅',place='卫州州廨',note='毒酒未饮是主明确叙述；新王弘贽传反记每日献酒建立信任后饮毒酒不疑，不强行调和。')
ev('wang_luan_kills_conghou','四月戊寅王峦缢杀李从厚',23,'峦缢','杀之。',[('王峦','缢杀执行者'),('闵帝','被缢杀者')],when='934年四月戊寅',place='卫州州廨',note='缢杀是主结局，旧闵纪遇鸩而崩、新王传饮毒酒死另列异说；新帝纪同戊寅记弑鄂王，不据此反证具体方法。')
ev('wang_luan_returns_kong_questioned','王峦返回后，李从珂使人向孔妃问重吉等何在',23,'孔妃尚在宫中，','重吉辈何在？”',[('王峦','已返回的殿直'),('潞王','遣人责问者'),('孔妃','被问重吉等所在者')],place='洛阳宫中',note='此为王回后问话，不据此记已死重吉复现，也不把未名传话人强指王峦。')
ev('congke_kills_kong_and_four_sons','李从珂杀孔妃及其四子',23,'遂杀妃，','并其四子。',[('潞王','下令杀害者'),('孔妃','与四子一同被杀者')],place='洛阳宫中',note='四子集体明载但此段未逐名，不凭同年皇孙称谓补出四人身份。王峦已回不当四月戊寅同日必杀妃，旧记回后即日而未独载回日。')
ev('song_sends_inquiries_conghou_weizhou','李从厚在卫州时，宋令询遣使问起居',23,'闵帝之在卫州也，','遣使问起居，',[('宋令询','磁州刺史、遣使问起居者'),('闵帝','受起居问询者')],place='卫州、磁州',note='主惟宋问为本段独特记述，不编所有其他官员的行为；旧宋传补每日令人奔问。')
ev('song_lingxun_mourns_hangs_himself','宋令询闻李从厚遇害，恸哭半日后自缢',23,'闻其遇害，','自经死。',[('宋令询','闻死讯后恸哭、自缢者')],place='地点未详（宋令询任磁州刺史）',note='主未独载宋死亡干支，新帝纪置戊寅条，旧末帝纪辛巳邢州报其死为奏报日期，不能用报日当死亡日；磁州为所任刺史州，并未证明具体自缢处。')

# Kinship is directional; reuse previous spouse and father IDs when available.
relationship('王弘贽','王峦','父亲',23,span(23,'帝遣弘贽','殿直峦往鸩之。'),'弘贽之子明确；A—父亲→B表示王弘贽是王峦的父亲，职殿直不是姓名的一部分。')

# Main narrative evaluation is quoted as an evaluation, not converted into causal edges.
q=span(23,'闵帝性仁厚，','以致祸败焉。')
for name,role in [('闵帝','被主书评价性仁厚及待兄弟坦怀者'),('秦王','主书追述忌疾李从厚者'),('潞王','主書说闵帝对之亦无嫌者'),('朱弘昭','被主书指为横生猜间者'),('孟汉琼','被主书指为横生猜间者')]:
 person(name,23,role,q)
claim('person',people['李从厚'],'description','《通鉴》评价李从厚性仁厚、待兄弟坦怀，并认为朱弘昭、孟汉琼等猜间使其致败。',23,q,'这是史家评价及归因，保来源措辞，不据此生成确定因果边或让此前已死的朱、孟成为杀帝当场执行者。')
for name,code in [('李从厚','wang_luan_kills_conghou'),('孔氏（李从厚妃）','congke_kills_kong_and_four_sons'),('宋令询','song_lingxun_mourns_hangs_himself')]:
 ek='event_zztj_279_0934_'+code
 c=next(x for x in B['claims'] if x['subject_key']==ek and x['field_path']=='description')
 quote=c['note'][3:].split('；核对说明：',1)[0]
 claim('person',people[name],'death_year',name+'在934年本段遇害或自缢。',23,quote,'本年连续条下死亡，未知独日者不补干支；复用旧主体，仅新增有出处的事实引用，不覆盖原发布人物档案。')

oldarrival='jiuwudaishi-046-congke-arrival';oldaccess='jiuwudaishi-046-congke-accession'
oldtax='jiuwudaishi-046-tax-and-death-reports';olddeath='jiuwudaishi-045-conghou-death'
oldsong='jiuwudaishi-066-song-lingxun';newshu='xinwudaishi-064-two-towns-join-shu'
newdeath='xinwudaishi-048-conghou-death';newkong='xinwudaishi-015-kong-empress';newchron='xinwudaishi-008-congke-eastmarch'
def excerpt(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);return t[a:t.index(end,a)+len(end)]
def supp(code,source,start,end,text,n,relation='corroborates',note='同一主体及动作对照；电子本，纸本及异文待核。'):
 claim('event','event_zztj_279_0934_'+code,'description',text,n,excerpt(source,start,end),note,source=source,relation=relation)
supp('zhang_sun_submit_two_towns_to_shu',newshu,'三月，','皆以其地附于蜀。','新孟知祥世家在三月举兵、思同兵溃后记张虔钊、孙汉韶以地附蜀；主四月条下未独日。',19,relation='adds',note='书内编次与主位置分别保；六月到成都及孟病卒属后文，不前移为本次归降已发生。')
supp('congke_reaches_jiangqiao',oldarrival,'夏四月壬申，','立班奉迎，','旧末帝纪同壬申到蒋桥、百官奉迎。',20)
supp('congke_reaches_jiangqiao',newchron,'夏四月壬申，','王辭不見。','新废帝纪同壬申入京、冯道率百官蒋桥迎、王辞不见。',20,relation='adds')
supp('congke_defers_meeting_before_coffin',oldarrival,'教旨以','俟會於至德宮，','旧末帝纪同未拜梓宫暂不见，并补约会至德宫。',20,relation='adds')
supp('congke_visits_dowager_and_taifei',oldarrival,'是日，帝入謁','太后、太妃，','旧同记入谒太后、太妃。',20)
supp('congke_cries_at_coffin_explains',oldarrival,'至西宮，','伏梓宮慟哭，','旧同记西宫伏梓宫恸哭。',20)
supp('feng_officials_audience_congke_returns_bow',newchron,'入哭于西宮，','王答拜。','新同记西宫后见群臣、冯道拜、王答拜。',20)
supp('congke_declares_wait_for_emperor_return',oldarrival,'馮道等上箋','信無謂也。」','旧同记冯道劝进、潞王声称俟主上归阙及园陵礼终退守藩服。',20)
supp('dowager_deposes_conghou_e',oldarrival,'癸酉，','降閔帝為鄂王。','旧末帝纪同癸酉太后下令降为鄂王。',21)
supp('dowager_deposes_conghou_e',olddeath,'五日，即位。','七日，廢帝為鄂王。','旧闵帝纪记五日即位、七日废为鄂王，与主及旧末帝纪先癸酉四日废、乙亥六日即位不合。',21,relation='conflicts',note='两篇旧帝纪自有日期和顺序差，电子本未以一条校正另一条，纸核待办。')
supp('dowager_authorizes_congke_state_affairs',oldarrival,'可起今月四日','權以書詔印施行。','旧太后令明记四日起知军国事、权以书诏印施行。',21,relation='adds',note='这是令文规定四日起，而非以文中皇长子称谓推曹亲生从珂。')
supp('officials_wait_for_blame_congke_restores_posts',oldarrival,'是日，監國在至德宮，','乃退。','旧同宫门待罪、监国请复位，并转述相公诸人何罪。',21,relation='adds')
supp('dowager_orders_congke_accession',oldarrival,'甲戌，太后令曰：','宜即皇帝位。」','旧同甲戌太后令宜即帝位。',21)
supp('congke_accession_at_coffin',oldaccess,'乙亥，','宣冊書曰：','旧末帝纪乙亥西宫柩前告奠即位，补李愚摄中书令宣册。',21,relation='adds',note='补宣册身份不当正式改授中书令或李愚撰写整份册书。')
supp('congke_accession_at_coffin',newchron,'乙亥，','皇帝即位。','新废帝纪同乙亥即位。',21)
supp('congke_accession_at_coffin',olddeath,'四月三日，','五日，即位。','旧闵帝纪三日入洛、五日即位，五日与主及旧末帝纪乙亥六日不同。',21,relation='conflicts')
q=excerpt(oldaccess,'攝中書令','宣冊書曰：');person('李愚',21,'摄中书令、宣册者',q,source=oldaccess)
claim('event','event_zztj_279_0934_congke_accession_at_coffin','description','《旧五代史》补李愚以摄中书令身份宣册。',21,q,'动作与摄官职由本句明载，补到同一即位事件，不另造重复登基。',source=oldaccess,relation='adds')
# This supplementary participant has its own direct quotation.
pk=people['李愚'];edge='participation_zztj_279_0934_congke_accession_at_coffin_'+pk
B['person_events'].append(dict(key=edge,person_key=pk,event_key='event_zztj_279_0934_congke_accession_at_coffin',role='摄中书令、宣册者（旧史补证）',status='draft'))
claim('person_event',edge,'role','李愚以摄中书令身份宣册。',21,q,'补证参与者，不将摄职当正式升任。',source=oldaccess,relation='adds')
supp('congke_promises_hundred_min_on_arrival',oldtax,'帝素輕財好施，','人賞百千。」','旧同记在岐下向军士承诺入洛人赏百千。',22,relation='adds',note='百千钱与主百缗按史文并列，不因兑换惯例补实际发放或总军人数。')
supp('wang_mei_proposes_collect_residents_money',oldtax,'丙子，','以助賞軍。','旧末帝纪补丙子诏河南府率京城居民财助赏军。',22,relation='adds',note='旧给征财诏日期，主本段王请议无独日，不把旧丙子挪作王开口日。')
supp('ministers_propose_five_months_rent_advance',oldtax,'丁丑，','一概施行。','旧末帝纪补丁丑诏预借五个月房课，士庶一概施行。',22,relation='adds',note='五个月房课与主五月僦直对应时长，不误释成农历五月租金。')
supp('ministers_propose_five_months_rent_advance',newchron,'丙子，','借民房課五月以賞軍。','新同丙子率河南民财、丁丑借民房课五月赏军。',22,relation='adds')
supp('wang_hongzhi_moves_conghou_office',newdeath,'弘贄奉帝','居于州廨。','新王弘贽传同奉闵帝居州廨。',23)
supp('congke_sends_wang_luan_poison',newdeath,'弘贄有子巒，','遣巒持鴆與弘贄。','新同王弘贽子峦为殿直、废帝入立遣持鸩给弘贽。',23,relation='adds')
supp('wang_luan_kills_conghou',olddeath,'九日，巒至，','時年二十一。','旧闵帝纪记四月九日王峦至、帝遇鸩而崩，二十一岁；主同九日戊寅却记拒酒后缢杀。',23,relation='conflicts',note='死亡方法异说并列；二十一为旧载年龄，不自行逆推生年。')
supp('wang_luan_kills_conghou',newdeath,'初，愍帝在衞州，','遂崩。','新王弘贽传记先使酒家日献一觞建立信任，后饮鸩酒不疑而崩，与主知毒不饮、王峦缢杀不同。',23,relation='conflicts',note='保新完整叙述，不把饮毒死与拒毒缢死混成一个确定流程。')
supp('wang_luan_kills_conghou',newchron,'戊寅，','慈州刺史宋令詢死之。','新废帝纪同戊寅弑鄂王，并记宋令询死之；其职州写慈，主旧作磁。',23,relation='adds',note='帝纪弑只印证遇害及纪日，不独证缢杀方法；慈磁字不擅改原文。')
supp('wang_luan_kills_conghou',oldtax,'己卯，衛州奏，','此月九日鄂王薨。','旧末帝纪己卯卫州奏鄂王本月九日死，奏报与死亡日期分。',23,relation='adds')
supp('congke_kills_kong_and_four_sons',olddeath,'皇后孔氏在宮中，','即日與其四子並遇害。','旧同孔氏在宫、王峦回来即日与四子遇害。',23,relation='adds',note='即日承王峦回，不是必承四月九日，主亦王既还后被杀。')
supp('congke_kills_kong_and_four_sons',newkong,'愍帝出奔，','后及四子皆見殺。','新孔后传补闵帝出奔时后病、子幼不能从，废帝入立后及四子皆被杀。',23,relation='adds',note='补不能随奔缘由为此书记载，不由子幼定出生年份，四人未名不猜名单。')
supp('song_sends_inquiries_conghou_weizhou',oldsong,'閔帝蒙塵於衛，','令詢日令人奔問。','旧宋令询传补闵帝在卫时每天令人奔问。',23,relation='adds')
supp('song_lingxun_mourns_hangs_himself',oldsong,'及聞帝遇害，','自經而卒。','旧宋传同闻帝遇害恸哭半日后自经。',23)
supp('song_lingxun_mourns_hangs_himself',oldtax,'辛巳，邢州奏，','磁州刺史宋令詢自經而卒。','旧末帝纪辛巳邢州奏宋自经死，报日不当死亡日。',23,relation='adds')
claim('person',people['宋令询'],'description','《旧五代史》宋传称其知书乐善、动皆由礼，闵帝在藩时从客将迁都押衙，闵帝嗣位后出任磁州刺史。',23,excerpt(oldsong,'宋令詢，','乃出為磁州刺史。'),'籍贯原书不知何许人，不能补籍贯；知书乐善是书中评价。前职经历只补人物事实，不倒置为934新授。',source=oldsong,relation='adds')
claim('person',people['孔氏（李从厚妃）'],'description','《新五代史》孔后传称其有贤行、生四子；闵帝即位后立为皇后，未及册命而难作。',23,excerpt(newkong,'愍帝哀皇后孔氏，','未及冊命而難作。'),'贤行为史书评价；立后与未及册命并列，不当完成册礼；哀为追谥而非934新名。',source=newkong,relation='adds')
relationship('孔循','孔妃','父亲',23,excerpt(newkong,'愍帝哀皇后孔氏，','父循，橫海軍節度使。'),'新传父循明示，复用已发布同方向父亲关系；横海为史书父职概括，不定本年新授。',source=newkong)
relationship('李从厚','孔妃','丈夫',23,excerpt(newkong,'愍帝哀皇后孔氏，','未及冊命而難作。'),'新传闵帝孔皇后关系明示，复用李从厚—丈夫→孔氏旧边，不再建反向妻子重复边。',source=newkong)

reviews={19:'出讨时留孙守兴元为前事追记；败归、两镇降、遣李五千还利州和张一万屯大漫天分。不把遣军当甲申已入两州，新孟世家三月兵败后附蜀与主四月附录位置分列。',20:'壬申蒋桥迎、未拜梓宫暂不见、两轮劝进、谒太后太妃、西宫恸哭陈由、冯率官见答拜、声称待帝归退藩逐项分。不把声明当已经退守或笺当即位；曹王用既有主体。',21:'癸酉废鄂王、知军国及权印、待罪复位、甲戌宜即位令、乙亥柩前即位分。旧末帝纪与新废帝纪同主，旧闵纪五日即位七日废不同日期和顺序保。不前移乙酉改元；旧补李愚摄中书令宣册不当正式升官。',22:'凤翔许赏百缗为本次出发追叙，不同闵帝前段二百承诺。王玫报数百万与实际三万两匹、估需五十万缗不能混量；请率民财、数日数万、帝问策、按屋预借五个月租金分别。旧丙子征财诏与丁丑房课补，不把诏日当王请议日；五月是时长不农历五月。后段六万二十万不回填。',23:'迁州廨、遣殿直王峦鸩杀、戊寅到问不答、王数进酒帝知毒拒、王峦缢杀分。旧遇鸩、新酒家日日献酒后饮鸩而崩异说并列；新帝纪弑同日不独证缢。孔及四子王回后被杀不强定戊寅，未名四子不猜身份；新孔病子幼不能从补。宋在卫遣问、闻害半日哭自缢与旧辛巳奏报日区分；新慈与主旧磁字保。主仁厚和猜间致败为史家评价，不造因果边。'}
contexts=[]
for directory in sorted((P/'sources/context').iterdir()):
 r=json.loads((directory/'paragraph.json').read_text());contexts.append(dict(file=os.path.relpath(directory/'source.txt',P/'sources'),sha256=hashlib.sha256((directory/'source.txt').read_bytes()).hexdigest(),paragraph_id=r['id'],purpose='传首或标题核对；结构项不生成史事',url='https://github.com/greed-216/histree/blob/8468a699/'+str((directory/'source.txt').relative_to(ROOT))))
directory=P/'sources/library/jiuwudaishi-066-song-lingxun'
assert (directory/'source.txt').read_bytes()==(sources['jiuwudaishi-066-song-lingxun']/'source.txt').read_bytes()
contexts.append(dict(file=os.path.relpath(directory/'source.txt',P/'sources'),sha256=hashlib.sha256((directory/'source.txt').read_bytes()).hexdigest(),paragraph_id='jiu-wudaishi-205deb4a7860-p001706',purpose='本次导出与933已发布快照逐字一致；实际引用复用旧source及固定提交',url='https://github.com/greed-216/histree/blob/8468a699/'+str((directory/'source.txt').relative_to(ROOT))))
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(19,24):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(19,24)],next_paragraph='zztj-v279-y0934-p024',next_volume=279,next_year=934,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷279连续934年第19—23正文段，原24—28行；两镇降蜀、入洛废立、赏军筹资与闵帝孔氏宋令询遇害。第24段石敬瑭入朝待录，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(19,24)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
