# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 933 paragraphs 31–39."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 58))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'18ef6e80','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))

specs += [('tongjian-278-933-september-october',YEAR/'part-03/sources/library/tongjian-278-933-september-october','8df19907','司马光等'),('jiuwudaishi-044-933-september',YEAR/'part-03/sources/library/jiuwudaishi-044-933-september','8df19907','薛居正等'),('liaoshi-072-bei-tang-names',ROOT/'content/books/zizhi-tongjian/vol-277/year-0931/part-02/sources/library/liaoshi-072-bei-tang-names','1066c58f','脱脱等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-933-september-october']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0933-p031-p039',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
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
for n in range(31, 40):
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
        citation = f'卷278·长兴四年（933）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0933_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','上':'李嗣源','闽王':'王延钧','文杰':'薛文杰','继图':'王继图','李赞化':'耶律倍','李赞华':'耶律倍','知诰':'李昪','徐知诰':'李昪','从荣':'李从荣','秦王':'李从荣','延光':'范延光','赟':'冯赟','汉琼':'孟汉琼','义诚':'康义诚','彝超':'李彝超'}
NEW_ALIASES={'王继图':['王繼圖'],'孙岳':['孫岳','孫嶽','孙嶽'],'王淑妃':['花见羞','花見羞']}

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
    if when is None:when='933年九月条下；确日未载' if n<=34 else '933年十月条下；确日未独载' if n<=37 else '933年十一月条下；确日未独载'
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
# Consecutive body paragraphs 31–39; paragraph 40's long coup narrative remains pending.
sep='jiuwudaishi-044-933-september';october='jiuwudaishi-044-933-october';nov='jiuwudaishi-044-933-november';fan='jiuwudaishi-066-fan-departure';kang='jiuwudaishi-066-kang-qin-son';newkang='xinwudaishi-027-kang-qin-son';wang='xinwudaishi-015-wang-consort';adoption='jiuwudaishi-051-congyi-adoption';liao='liaoshi-072-bei-tang-names';collation='tongjian-278-933-autumn-collation'
E=ev('bei_zhaoxin_nominal','九月庚子耶律倍受昭信节度使',31,'庚子，','昭信节度使，',[('李赞化','原义成节度使，受昭信节度使者'),('帝','任命君主')],when='933年九月庚子',place='后唐朝廷、洛阳',note='李赞化沿已有耶律倍，旧李讚华及辽李贊华同滑州原镇、遥领虔州识同人；军实辖何州待核，不把昭信强定位金州。')
claim('event',E,'description','旧明宗纪庚子条记李讚华由前滑州节度使遥领虔州节度使。',31,'以前滑州節度使李讚華遙領虔州節度使。','主义成军名旧滑州治名同原镇；主昭信旧虔州是同授叙，旧明写遥领，不当已实任攻取吴境。',source=sep,relation='adds')
E=ev('bei_stays_luoyang_salary','耶律倍留洛阳食昭信节度俸',31,'庚子，','留洛阳食其俸。',[('李赞化','留洛阳领俸的遥领节度使')],when='933年九月庚子任命附记',place='洛阳',note='未赴镇，领俸安排不当驻虔州或已赴金州；与任命分述行为。')
claim('person',people['耶律倍'],'aliases','《辽史》记倍复赐姓李，名赞华，移镇滑州、遥领虔州；主李赞化字异保。',31,'復賜姓李，名贊華。移鎮滑州，遙領虔州節度使。','身份沿耶律倍，不因赞化华异字造另一人；仅补李名及繁体字检索，辽后半生尚未到主线不提前新增事件。',source=liao,relation='adds')
claim('event',E,'location_name','通鉴音注对昭信所领地点提出虔州昭信、昭化节名讹字等疑问。',31,'贊華所領節，抑虔州之昭信軍歟？','校注为疑问保，非定论；不新增注转引专书为独立事实，原文不改昭信。',source=collation,relation='adds')
E=ev('congrong_rank_above_chancellors','九月辛丑诏李从荣大元帅位在宰相上',32,'辛丑，','宰相上。',[('从荣','获定元帅班位者'),('帝','定班位诏令者')],when='933年九月辛丑',note='八月任元帅、九月见礼、现在班位三件不同；仪位在上不当继皇位已受册。')
claim('event',E,'description','旧明宗纪同九月辛丑诏秦王大元帅班在宰臣上。',32,'辛丑，詔天下兵馬大元帥、秦王從榮班宜在宰臣之上。','同日同班位，旧夹注五代会要不新派生额外事件。',source=sep,relation='corroborates')
ev('xu_disaster_statement','徐知诰因吴国水火屡灾，称不应独乐',33,'吴徐知诰','吾安可独乐！”',[('徐知诰','因灾自陈不独乐者')],place='吴',note='徐知诰沿李昪，屡灾为本段概述不逐灾造地点年月；言论与后实际处置分。')
ev('xu_releases_attendants','徐知诰放遣侍妓',33,'悉纵遣侍妓','悉纵遣侍妓，',[('徐知诰','放遣侍妓者')],place='吴',note='侍妓本段无个人姓名、人数及去向，未说已废全吴音乐制度。')
ev('xu_burns_instruments','徐知诰取乐器焚毁',33,'取乐器','取乐器焚之。',[('徐知诰','焚乐器者')],place='吴',note='仅所取乐器，不说全吴民间乐器已禁毁，也不把言不乐等同后来登位新礼法。')
ev('xue_suppresses_clan_advice','薛文杰劝闽主抑挫宗室',34,'闽内枢密使','抑挫诸宗室；',[('文杰','史称闽内枢密使、劝抑宗室者'),('闽王','受劝的闽主')],place='闽',note='主本段称内枢密，前段中军国计身份沿同人，不猜另一次升官日期；说为劝说，不独推出全体宗室当时已受处罚。')
ev('wang_jitu_conspiracy','史载王继图不忿而谋反',34,'从子继图','谋反，',[('继图','史称闽主从子、谋反者')],place='闽',note='谋反是主书叙述，未给具体组织军队或方案；从子不推亲父或单一叔伯排行。')
ev('wang_jitu_executed','王继图因谋反坐诛',34,'从子继图','坐诛，',[('继图','被诛的闽宗室')],place='闽',note='主未独日，九月条下史述；未知具体执行人，不凭闽主身份添其亲手杀参与。')
ev('wang_jitu_collective_liability','王继图案连坐千余人',34,'连坐者','千馀人。',[('继图','引发连坐之案主体')],place='闽',note='连坐千余为原概数，不同坐诛措辞不能写千余全被处死，群体未名不造名单。')
relationship('继图','闽王','族侄',34,'从子继图','王继图→王延钧为族侄，保原从子称谓；未知亲父与具体叔伯长幼，不改成确定亲兄弟之子。')
next(x for x in B['people'] if x['key']==people['王继图'])['death_year']=933
claim('person',people['王继图'],'death_year','王继图在933年九月条下因谋反坐诛。',34,'从子继图不胜忿，谋反，坐诛，','本段当年叙事，不标具体死亡日或生年。')
E=ev('frontier_horse_cost_report','十月乙卯范延光、冯赟奏西北卖马与绢耗、国用问题',35,'冬，','计耗国用什之七，',[('延光','奏马政国用的枢密使'),('赟','奏马政国用的三司使')],when='933年十月乙卯',note='近五千匹及什之七是两臣奏称，不当现代年度决算；主日月绢疑字，校本日用，保原引文不读作每月。')
claim('event',E,'description','同书固定音注版作日用绢无虑五千匹，计耗国用什之七。',35,'日用絹無慮五千匹，計耗國用什之七，','原TXT日月绢与校本日用异字保留，日用是奏称日耗；勿改造固定全年金额或强换钱币。',source=collation,relation='conflicts')
ev('frontier_horse_select_vouchers','准范延光、冯赟所请，委沿边镇戍择良马给券上报数目',35,'请委缘边','从之。',[('延光','请调整买马方式者'),('赟','请调整买马方式者'),('帝','批准方案者')],when='933年十月乙卯',place='后唐沿边镇戍',note='择良给券上报为获准政策，未有执行账数不写已节省七成或实际买入五千马。')
E=ev('sun_yue_three_finances','十月戊午孙岳任三司使',35,'戊午，','三司使。',[('孙岳','主前武兴节度使、获任三司使者'),('帝','任命者')],when='933年十月戊午',note='岳嶽同人字形；主前武兴、旧前凤翔不同原职并列，不新造第二孙岳。')
claim('event',E,'description','旧明宗纪同戊午记前凤翔节度使孙嶽为三司使。',35,'戊午，以前鳳翔節度使孫嶽為三司使。','同日同新职，主武兴与旧凤翔前职不同待核，不能自动当军治对应关系。',source=october,relation='conflicts')
E=ev('fan_seeks_departure_via_palace','范延光屡通过孟汉琼、王淑妃求外任',36,'范延光屡','以求出。',[('延光','求出任外镇者'),('汉琼','为求出所借宫中渠道'),('王淑妃','为求出所借宫中渠道')],when='933年十月庚申任外镇前屡求；确日未知',note='通过二人求出不等明确金钱行贿或私人姻亲；多次请求不编各次日。')
claim('event',E,'description','旧朱弘昭传也记范延光因孟汉琼、王淑妃进说而获准去枢密。',36,'延光亦因孟漢瓊、王淑妃進說，故皆得免。','人物传补渠道，时序与前批赵延寿请求并列但不重复其出镇事件。',source=fan,relation='corroborates')
claim('person',people['王淑妃'],'description','新书记淑妃王氏出身邠州饼家，号花见羞。',36,'淑妃王氏，邠州餅家子也，有美色，號「花見羞」。','传首明宗后宫身份补身世；个人往事年未知，不当933新纳后宫，也不把称号当本名。',source=wang,relation='adds')
claim('person',people['王淑妃'],'description','王氏少时被卖给梁将刘鄩为侍儿，鄩卒后无所归。',36,'少賣梁故將劉鄩為侍兒，鄩卒，王氏無所歸。','人物早年背景补，具体年月未知；本句侍儿不直接当婚姻或认作刘鄩正妻。',source=wang,relation='adds')
claim('person',people['王淑妃'],'description','明宗夏夫人卒后求别室，经安重诲转荐而纳王氏。',36,'是時，明宗夏夫人已卒，方求別室，有言王氏於安重誨者，重誨以告明宗而納之。','人物过往入宫背景，未独载起年，不造933新纳宫或夏氏当年死事件。',source=wang,relation='adds')
claim('person',people['王淑妃'],'aliases','王淑妃号花见羞。',36,'號「花見羞」。','称号及繁简形式仅作检索；本名史文未载，避免与其他后宫王氏相混。',source=wang,relation='adds')
relationship('王淑妃','李从益','养母',36,'明宗命王淑妃母之，','王淑妃→李从益养母，旧从益传首另言宫嫔所生，不能记王为生母；抚育安排起年未明，不造933新收养事件。',source=adoption)
E=ev('fan_chengde','十月庚申范延光任成德节度使',36,'庚申，','成德节度使，',[('延光','由枢密出镇的成德节度使'),('帝','任命者')],when='933年十月庚申',place='后唐朝廷、成德军',note='受任不等当日抵镇；旧镇州同军治补。')
claim('event',E,'description','旧明宗纪同庚申记枢密使范延光任镇州节度使。',36,'庚申，以樞密使範延光為鎮州節度使，','成德军与镇州同新任，非另造两职；旧史采用另一字形，主体沿范延光。',source=october,relation='corroborates')
claim('event',E,'description','旧朱弘昭传十月记范延光出镇常山。',36,'十月，范延光出鎮常山，','常山与镇州同一镇区称，不据人物传倒推早一日已赴镇。',source=fan,relation='corroborates')
E=ev('feng_yun_pivot','十月庚申冯赟任枢密使',36,'以冯赟','枢密使。',[('赟','由三司转任枢密使者'),('帝','任命者')],when='933年十月庚申',note='同段新任，非仍以三司为主要新职。')
claim('event',E,'description','旧明宗纪同日记三司使冯贇任枢密使。',36,'以三司使馮贇為樞密使。','前职三司补，与孙岳接三司相衔；不将同二品衔重复新加一次。',source=october,relation='corroborates')
claim('event',E,'description','旧朱弘昭传记以三司使冯赟与朱弘昭对掌枢务。',36,'以三司使馮贇與弘昭對掌樞務，','补共同掌枢，未必每次同场办公，不新立永久政治盟友关系。',source=fan,relation='adds')
ev('mingzong_trusts_kang','明宗以康义诚为朴忠而亲任',36,'帝以亲军','亲任之。',[('帝','评价亲任康义诚者'),('义诚','亲军都指挥使、同平章事、受帝信任者')],year=None,when='帝对康义诚的长期评价和亲任概述；起讫未知',note='朴忠为帝看法，与后述持两端并存，不能当客观永恒品性；不虚构本段又加一次亲军指挥官。')
E=ev('kang_sends_son_to_qin','康义诚令其子事秦王，欲持两端自全',36,'时要近','冀得自全。',[('义诚','遣子事秦王、持两端者'),('秦王','其子所事的秦王')],when='933年秦王受元帅后、当前朝臣避祸时；确日未知',note='康子未名不猜后续人名或生年；冀自全为意向，不说终于自全成功，朝臣泛称不造姓名名单。')
claim('event',E,'description','旧康义诚传记明宗委遇而难解退，令子以弓马事秦王自结。',36,'義誠以明宗委遇，無以解退，乃令其子以弓馬事秦王以自結。','补弓马侍事，同子未名；不以传后934见降补为本段已叛。',source=kang,relation='adds')
claim('event',E,'description','新康义诚传也记大臣避秦王，义诚遣子事秦王府。',36,'唐諸大臣皆懼禍及，思自脫，獨義誠心結之，遣其子事秦王府。','并列书证，同情境不等已秘密加入秦王谋反计划，未提前录兵变。',source=newkang,relation='corroborates')
ev('yichao_apologizes','权知夏州李彝超表谢罪并求昭雪',37,'权知夏州','求昭雪；',[('彝超','上表谢罪、求昭雪者')],place='夏州、后唐朝廷',note='谢罪求昭雪为表述，不是史料证明其本来一定有罪或一定无罪；不可将后正式节度任命称春初已受任。')
E=ev('yichao_dingnan_full','十月壬戌李彝超正式任定难军节度使',37,'壬戌，','节充使。',[('彝超','由权知夏州转定难节度使者'),('帝','授任君主')],when='933年十月壬戌',place='夏州、定难军',note='主节充使疑节度字，旧及同书校版节度使清楚；保原引文不沿讹字造新职。与此前三月拟移彰武不同。')
claim('event',E,'description','旧明宗纪壬戌记权知夏州李彝超任夏州节度使，加检校司徒。',37,'壬戌，以權知夏州事、檢校司空李彝超為夏州節度使、檢校司徒。','主定难旧夏州军治对应，旧检校司空转司徒补，不当实任三公行政事务。',source=october,relation='adds')
claim('event',E,'description','同书固定音注版正文作定难军节度使。',37,'壬戌，以彝超爲定難軍節度使。','主节充与此节度字异校读，注去年秋讨时点与已录933夏州战事不合，不采作新年代事实。',source=collation,relation='corroborates')
ev('mingzong_farewell_fan','十一月甲戌明宗饯范延光，询离京前意见',38,'十一月，','事宜尽言。”',[('上','设饯并询事者'),('延光','将赴外镇的受饯者')],when='933年十一月甲戌',place='后唐京师',note='已经十月授成德与今饯离京分，不把授职日写到达任地日。')
E=ev('fan_warns_against_favorites','范延光劝明宗与辅臣参决，勿听群小之言',38,'对曰：','群小之言。”',[('延光','临别陈劝者'),('上','受劝君主')],when='933年十一月甲戌',note='主内久辅臣疑内外，引用原字保；群小泛称，史叙后解释孟党，不任意补全部名单。')
claim('event',E,'description','同书音注版作与内外辅臣参决，并释内辅为枢密、外辅为宰相。',38,'願陛下與內外輔臣參決，勿聽羣小之言。」{{*|內輔臣，謂樞密使；外輔臣，謂宰相。羣小，指孟漢瓊之黨。}}','原TXT内久与校本内外字异，不逐字改快照；释群小为孟党是同书注层，不推出孟本人已在场争辩。',source=collation,relation='conflicts')
ev('mingzong_fan_weeping_parting','明宗与范延光相泣而别',38,'遂相泣','而别。',[('上','临别泣者'),('延光','临别泣者')],when='933年十一月甲戌',place='后唐京师',note='泣别不是帝已死亡、范已被逐的证据，不倒采注预言。')
ev('meng_court_faction_report','史叙孟汉琼用事，其附者结党蔽惑上听',38,'时孟汉琼','故延光言及之。',[('汉琼','史叙宫廷权力及附党中心')],year=None,when='时孟汉琼用事的持续概述；起讫未知',note='主解释范临别所言，用事蔽惑是史叙评价，未名附党不补已知朱冯等为全部具体成员，不新造永久盟友关系。')
E=ev('shenzhou_zhaohua_rename','十一月庚辰慎州怀化军改为昭化军',39,'庚辰，','怀化军。',[('帝','朝廷改军名的君主')],when='933年十一月庚辰',place='慎州',note='主缺改后军名，旧同日明确昭化军；不把慎州等同后文洮州，地理与现代坐标未核。')
claim('event',E,'description','旧明宗纪十一月庚辰明记慎州怀化军改昭化军。',39,'庚辰，改慎州懷化軍為昭化軍，','以独立旧史明确补主缺语，不新增九域志或五代会要为基础出处；不推实际已迁治所。',source=nov,relation='adds')
E=ev('taozhou_baoshun_established','十一月庚辰在洮州置保顺军，领洮鄯等州',39,'置保顺军','洮、鄯等州。',[('帝','置军及定所领州的君主')],when='933年十一月庚辰',place='洮州、鄯州等',note='置节镇为制度安排，未有攻克叙述不当当日已征服洮鄯全域；仅主列二州及等，未知其余州不添。')
claim('event',E,'description','旧明宗纪同日作升洮州为保顺军，次日委洮鄯等州观察使。',39,'升洮州為保順軍。辛巳，以保大軍節度使、檢校太尉鮑君福為保順軍節度、洮鄯等州觀察等使；','补升州与领州依据，辛巳官名作为此制度书证不另外造当前主线未列的授职事件；新史名未增人物不等漏读主正文。',source=nov,relation='adds')
reviews={31:'九月庚子任昭信与留洛阳领俸分。主李赞化旧李讚华辽李贊华沿耶律倍；义成滑州同原镇，旧遥领虔州佐，不赴任不实统吴虔州。音注有昭信虔州或昭化讹字疑问，非定论，不定金州或现代点。',32:'九月辛丑元帅班位在相上，旧同日印证，与八月受任和九月见礼分；班位非已立储。',33:'徐知诰沿李昪，屡灾与不独乐声明、放侍妓、焚乐器三个动作，确日未知；未给各灾地年月不造逐次灾。不编人数去向，也不当全吴音乐尽禁。',34:'薛劝抑宗室、继图谋、坐诛、连坐分；内枢密为主本段身份，不造无日晋官；从子仅族侄，不猜亲父或叔伯长幼；千余连坐不说全杀、全案具体名单。继图死亡当年而无日。无二十四史同句不虚增补证。',35:'十月乙卯奏马费与择良给券奏准分，主日月绢同书日用校读，数字为奏称而非已审年度账；不说政策已节省。戊午孙岳三司、旧前凤翔主武兴异职保，岳嶽不造双人；不派生夹注专书新事实。',36:'屡借孟王求出、庚申范成德冯枢密、帝康朴忠评价与康遣子事秦分；军治成德镇州常山同镇；旧范求出渠道与十月出镇冯共枢佐，新旧康同未名子不猜名字，也不提前记兵变或934叛降。王淑妃新传身世称号补，不当本段新纳宫；旧从益传宫嫔生、命母之为养母非生母，起年未独。',37:'夏权知上表谢罪昭雪与十月壬戌正节度分，主节充疑节度、旧及校本明字；旧检校转衔补，不混三月拟调彰武。音注去年秋讨与主933围战不合，不作新年代确证。',38:'十一月甲戌饯、劝、相泣与孟党蔽听持续概述分；主内久同书内外校读，内外解释是注层，党名未明不指所有朱冯。评价不是已证各人永久品性；不采死期注推已经病终。',39:'十一月庚辰慎州改军名主缺后名旧补昭化，另洮州置保顺及领洮鄯。慎州与洮州两件不混，不据设军推新征服全域；现代地名坐标仍未知；旧次日具体委官仅作为领州补证、不抢新增主未列事件。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(31,40):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
context=ROOT/'content/books/zizhi-tongjian/vol-278/year-0933/part-02/sources/context/qian-yuanliao-name/response.json'
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=933,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(31,40)],next_paragraph='zztj-v278-y0933-p040',next_volume=278,next_year=933,supplements=supplements,source_contexts=[dict(file=os.path.relpath(context,P/'sources'),sha256=hashlib.sha256(context.read_bytes()).hexdigest(),note='通鉴固定音注版2115814原始API响应沿part-02归档。')],excluded_non_body=[],coverage='卷278连续933年第31—39段、原66—74行；李赞华昭信遥领、元帅班位、吴因灾遣妓焚器、闽宗室继图案、马政与孙岳、枢密换任及康王背景、夏州正授、临别陈劝及慎洮置军。第40段兵变长叙尚待逐动作校核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(31,40)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
