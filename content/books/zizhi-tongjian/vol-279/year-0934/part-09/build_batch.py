# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 934 paragraphs 59–68."""
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
 specs.append((directory.name,directory,'bf8c4dac','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [
 ('tongjian-279-934-meng-name-decree',YEAR/'part-08/sources/library/tongjian-279-934-meng-name-decree','5f4233fa','司马光等'),
 ('xinwudaishi-007-934-may',YEAR/'part-07/sources/library/xinwudaishi-007-934-may','651c7870','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-meng-name-decree']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0934-p059-p068',
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
for n in range(59, 69):
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
        month = '八月条下' if n<=61 else '九月条下' if n<=64 else '九月至十月' if n==65 else '十月条下'
        citation = f'卷279·清泰元年（934；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0934_09_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','蜀主':'孟昶','徐知诰':'李昪','吴主':'杨溥'}
NEW_ALIASES={'高延赏':['高延賞'],'宋从会':['宋從會'],'韩继勋':['韓繼勳'],'韩保贞':['韓保貞'],'安思谦':['安思謙'],'李继宏':['李繼宏'],'文景琛':[],'李延厚':[]}

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
    if when is None:when='934年'+('八月' if n<=61 else '九月' if n<=64 else '十月')+'条下；确日未独载'
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




E={}
E['liu_office']=ev('liu_replaces_wang_background','追述李从珂因王玫报告库财失实而命刘昫代判三司',59,'初，','代判三司。',[('帝','因报告失实换判三司者'),('刘昫','代判三司者')],when='934年四月庚辰任命的后文追述；本段初句未独列日',note='复用第25段刘昫判三司事件与参与边，四月日来自前已发布条；此段补王失实原因，不造八月第二次判三司任命。',stable_key='event_zztj_279_0934_liu_xu_administers_three_commissions')
claim('person',person('王玫',59,'报告左藏现财失实者',span(59,'帝以王玫','故以刘昫代判三司。')),'description','本段追述王玫报告左藏现财失实，成为被刘昫替换的原因。',59,'帝以王玫对左藏见财失实，故以刘昫代判三司。','主有故字，限定本次任命原因；失实并不证明故意贪污，见财为现财字样原保。')
E['audit']=ev('liu_orders_gao_tax_audit','刘昫命判官高延赏核查积年税款欠账',59,'昫命判官','皆积年逋欠之数，',[('刘昫','命核查者'),('高延赏','判官、受命核账者')],when='934年刘昫判三司后、八月庚午免税前；确日未载',note='皆积年逋欠之数为核查所见账项，不将其直接当现钱或可收真实税收。')
claim('event',E['audit'],'description','主书解释奸吏保留积欠账目，是为了借追责向民众勒取。',59,'奸吏利其征责丐取，故存之。','理由归于主书叙述，未名吏不擅造名单；积年旧行径不标934首次发生。')
E['proposal']=ev('liu_proposes_collectable_and_unpayable','刘昫奏报核账结果，请催可征旧欠、蠲无力偿还者',59,'昫具奏','悉蠲之，',[('刘昫','报告并提两类处置建议者')],when='934年核查积欠后、八月庚午诏前；确日未载',note='可征催、必无可偿免两个层次；奏请不是已经全部实施，也不当建议所有旧欠一律免。')
ev('han_supports_tax_remission','韩昭胤极力支持刘昫处理税欠的方案',59,'韩昭胤','极言其便。',[('韩昭胤','支持处置方案者'),('刘昫','方案提出者')],when='934年八月庚午免税诏前；确日未载',note='极言其便为支持意见，不扩成枢密使亲自核账或实际免税机关。')
E['remit']=ev('congke_tax_arrears_remission','八月庚午诏免账载旧欠租三百三十八万',59,'八月，庚午，','咸蠲免勿征。',[('帝','下蠲免诏者')],when='934年八月庚午',note='主未列数字单位，不补万贯、万缗或粮石；长兴以前原字保，与旧长兴四年十二月已前范围分别说明。')
claim('event',E['remit'],'description','旧末帝纪记八月庚午免长兴四年十二月以前天下残欠税。',59,'八月庚午，詔蠲放長興四年十二月已前天下所欠殘稅。','旧明确截至长兴四年十二月，主长兴以前表述压缩，不擅解为929以前；旧不具338万数，不能独证数额单位。',source='jiuwudaishi-046-934-august',relation='corroborates')
claim('event',E['remit'],'description','新刘昫传亦记核账后蠲除残租积负，民间喜而三司吏怨。',59,'乃句計文簿，覈其虛實，殘租積負悉蠲除之。','新传独立支持核查及减免，不具庚午或338万；不把句計转为新建另一场审计。',source='xinwudaishi-055-liu-tax-audit',relation='corroborates')
ev('poor_delight_officials_resent_remission','免税后贫民大悦，三司吏怨恨',59,'贫民大悦，','而三司吏怨之。',[],when='934年八月庚午免税诏后；未独载反应日',note='记群体反应，不造未名贫民或吏人物；十月闻罢相相贺是后阶段另录。')
claim('event',E['remit'],'description','新刘昫传解释积年负账被吏隐匿以把持州县求贿，蠲除后民欢而吏怨。',59,'往時吏幸積年之負蓋而不發，因以把持州縣求賄賂，及昫一切蠲除，民間歡然以為德，而三司吏皆沮怨。','新作者对旧弊和反应的描述，未载具体涉吏人数或金额，不能当统计；独立书证限定同事。',source='xinwudaishi-055-liu-tax-audit')
E['yao']=ev('yao_yi_chancellor','八月辛未姚顗受任中书侍郎、同平章事',60,'辛未，','同平章事。',[('姚顗','中书侍郎、同平章事获任者'),('帝','任命者')],when='934年八月辛未',place='洛阳',note='七月夹瓶次得姚是择人，此次实际命相，不混日。')
for source,quote in [('jiuwudaishi-046-934-august','辛未，以前尚書左丞姚顗為中書侍郎、平章事。'),('xinwudaishi-007-934-may','八月辛未，尚書左丞姚顗為中書侍郎、同中書門下平章事。')]:
 claim('event',E['yao'],'description','旧新末帝纪同记八月辛未姚顗由尚书左丞任相。',60,quote,'原前职与任命日一致，各书官衔长短保原。',source=source,relation='corroborates')
E['suo_death']=ev('suo_zitong_drowns','八月戊子索自通退朝过洛水，自投水中去世',61,'右龙武统军','自投于水而卒。',[('索自通','右龙武统军、自投水死者')],when='934年八月戊子',place='洛水',note='河中之隙、心不自安为主所叙心理与旧隙，不新造皇帝已令杀或现代诊断；旧丁亥日期异说另保。')
claim('person',people['索自通'],'death_year','索自通于934年八月去世，主记戊子投水，旧纪记丁亥卒。',61,'右龙武统军索自通，以河中之隙，心不自安，戊子，退朝过洛，自投于水而卒。','年一致，具体日并列，不以补书覆盖主日。')
claim('event',E['suo_death'],'time_original','旧末帝纪记八月丁亥右龙武统军索自通卒，与主戊子不同。',61,'丁亥，右龍武統軍索自通卒。','旧未具投水过程，日异说保；同年同官同人，不造两次死亡。',source='jiuwudaishi-046-934-august',relation='conflicts')
ev('congke_posthumous_suo_taiwei','李从珂闻索自通死讯惊讶，追赠太尉',61,'帝闻之','赠太尉。',[('帝','闻讯追赠者'),('索自通','被追赠者')],when='934年八月索自通死后；赠命确日未独载',note='追赠非生前新任职，帝惊为主所记反应。')
E['zhao']=ev('zhao_feng_taizi_taibao','八月丙申赵凤受任太子太保',61,'丙申，','为太子太保。',[('赵凤','前安国节度使同平章事、太子太保获任者'),('帝','任命者')],when='934年八月丙申',note='旧记乙未、前邢州，同人同新职但日和前镇写法不同，分别保留。')
claim('event',E['zhao'],'time_original','旧末帝纪记八月乙未以前邢州节度使赵凤为太子太保。',61,'乙未，以前邢州節度使趙鳳為太子太保。','与主丙申不同；前邢州、主安国属州和军号，不当不同人物；前职前字非当前两镇并领。',source='jiuwudaishi-046-934-august',relation='conflicts')
ev('fengxiang_order_eastan_defence','九月癸卯诏凤翔增兵守东安镇以备蜀',62,'九月，癸卯，','守东安镇以备蜀。',[('帝','下增兵守镇诏者')],when='934年九月癸卯',place='凤翔、东安镇',note='防备诏令，未载部将兵数与是否交战，不画已控制边界或现代坐标。')
ev('renhan_requests_six_armies','李仁罕以宿将功劳及受顾托为由请求判六军',63,'蜀卫圣诸军','求判六军，',[('李仁罕','卫圣诸军都指挥使武信节度使、请求判六军者')],when='934年九月甲寅获任前；确日未载',note='自恃为主叙，不推其已有谋叛；请求与授命分。')
ev('song_conghui_pressures_shumi','李仁罕令进奏吏宋从会向枢密院传达判六军意向',63,'令进奏吏','以意谕枢密院，',[('李仁罕','令传达者'),('宋从会','进奏吏、向枢密院传意者')],when='934年九月甲寅获任前；确日未载',note='进奏吏宋复合姓从会全名明确，未在枢密院任枢密使，不造两机构人。')
ev('appointment_draft_checked','有人又至学士院侦问任命文书草拟情况',63,'又至学士院','侦草麻。',[],when='934年九月甲寅获任前；确日未载',note='又至主语省略，可能承李仁罕或宋从会，本句不强定到院者、不建其参与边；草麻为任命文书起草，不编全文或学士名单。')
ev('renhan_six_armies_zhongshuling','九月甲寅孟昶加李仁罕兼中书令、判六军事',63,'蜀主不得已，','判六军事；',[('蜀主','加授者'),('李仁罕','兼中书令判六军事获任者')],when='934年九月甲寅',place='成都',note='不得已为主作者判断；判六军事正式命在此，不提前到请求或顾托。')
ev('zhao_tingyin_deputy_armies','九月甲寅赵廷隐兼侍中，为李仁罕判六军之副',63,'以左匡圣','为之副。',[('赵廷隐','左匡圣都指挥使保宁节度使、兼侍中副职获任者'),('蜀主','任命者')],when='934年九月甲寅',place='成都',note='为副限定此次判六军事，不造终身统属，未独立另一日。')
E['cloud']=ev('yunzhou_reports_khitan_raid','九月己未云州奏报契丹入寇',64,'己未，','契丹入寇，',[],when='934年九月己未',place='云州',note='己未为奏报日，不必是袭扰开始日；契丹将领及兵数未具。')
claim('event',E['cloud'],'description','旧末帝纪九月己未也记云州奏契丹寇境。',64,'己未，雲州奏，契丹寇境。','同奏报日与地区互核；未具体将领不擅添。',source='jiuwudaishi-046-934-september',relation='corroborates')
ev('shi_reports_baijing_defence','石敬瑭奏报亲领兵屯百井防契丹',64,'北面招讨使','屯百井以备契丹。',[('石敬瑭','北面招讨使、奏自领兵屯百井者')],when='934年九月己未奏报条下；出屯日未独载',place='百井',note='奏报行为与所报屯防分层，具体驻屯开始日未记；旧十月又记屯代州为后阶段，不拿来改九月百井。')
ev('shi_reports_yang_tan_repels_khitan','九月辛酉石敬瑭奏报杨檀在境上击退契丹',64,'辛酉，','却之。',[('石敬瑭','奏报者'),('杨檀','振武节度使、奏报中击退契丹者')],when='934年九月辛酉奏报；交战日未独载',place='振武境上',note='辛酉是奏日，不擅等同战日；境上无精确位置，不把云州当此战已证地点。')
ev('li_zhao_delays_shu_court','李肇闻孟昶即位后观望，未及时入朝',65,'蜀奉銮肃卫','不时入朝，',[('李肇','奉銮肃卫都指挥使昭武节度使兼侍中、迟入朝者')],when='934年七月孟昶即位后至十月庚午之间的叙述；确日未载',note='顾望为主叙，不等于已武装叛；不在闻即位时先杀。')
ev('li_zhao_lingers_hanzhou','李肇到汉州，与亲戚宴饮停留十余日',65,'至汉州，','燕饮逾旬；',[('李肇','汉州留饮者')],when='934年十月庚午入成都之前；留饮逾旬，起止日未载',place='汉州',note='逾旬为时长不倒算日期，未名亲戚不造关系端点。')
E['staff']=ev('li_zhao_staff_no_bow','十月庚午李肇到成都，自称足疾，扶杖见孟昶而不拜',65,'冬，十月，庚午，','见蜀主不拜。',[('李肇','称足疾扶杖入朝不拜者'),('蜀主','受见未被行拜礼者')],when='934年十月庚午',place='成都',note='称足疾为本人说法，不能确诊真实足病或说装病；癸未释杖另录。')
claim('event',E['staff'],'description','新孟世家也记李肇自镇来朝，杖入见、称疾不拜。',65,'是時，李肇自鎮來朝，杖而入見，稱疾不拜，','独立印证姿态，无庚午及汉州停留，不伪称各细节均有两书。',source='xinwudaishi-064-renhan-zhao',relation='corroborates')
E['li_dismiss']=ev('li_yu_dismissed_chancellorship','十月戊寅李愚罢相，守左仆射本官',66,'戊寅，','李愚罢守本官，',[('李愚','罢相守左仆射者'),('帝','罢相者')],when='934年十月戊寅',note='罢相与本官保留分层，不记完全失官。')
E['liu_dismiss']=ev('liu_xu_dismissed_right_pushe','十月戊寅刘昫罢相为右仆射',66,'吏部尚书','罢为右仆射。',[('刘昫','罢相转右仆射者'),('帝','罢相者')],when='934年十月戊寅',note='原兼衔含判三司，但本句罢为右仆射，不凭此断言另有独立撤三司使诏。')
for key in ['li_dismiss','liu_dismiss']:
 claim('event',E[key],'description','旧末帝纪记十月戊寅李愚、刘煦罢相，分别守左、右仆射。',66,'戊寅，宰臣李愚、劉煦罷相，以愚守左僕射，煦守右僕射。','刘煦沿已核刘昫主体，左右官不调换。',source='jiuwudaishi-046-934-october',relation='corroborates')
claim('event',E['liu_dismiss'],'description','新刘昫传记两相相诋诟、史吏扬言后，废帝并罢之，刘昫为右仆射。',66,'相府史吏惡此兩人剛直，因共揚言，其事聞，廢帝並罷之，以昫為右僕射。','新给罢相叙述与评价，未具戊寅；恶刚直为书所叙，不当所有史吏内心可独立测知。',source='xinwudaishi-055-liu-dismissed')
E['clerks']=ev('clerks_celebrate_liu_dismissal','三司吏闻刘昫罢相相互庆贺，无人随他归宅',66,'三司吏闻昫罢相，','无一人从归第者。',[('刘昫','罢相后无人从归者')],when='934年十月戊寅罢相之后',note='主相驾疑贺，新刘传欢呼相贺校读，摘录底字保原；新无一人从归不是其记载，分别说明。')
claim('event',E['clerks'],'description','新刘昫传记三司吏提印立月华门外，闻罢相欢呼相贺，称自此快活。',66,'三司諸吏提印聚立月華門外，聞宣麻罷昫相，皆歡呼相賀曰：「自此我曹快活矣！」','新原相贺支持主相驾疑字校读，地点和引语为补证；不把主无人从归伪称新也具。',source='xinwudaishi-055-liu-dismissed',relation='corroborates')
ev('four_served_meng_princely_background','追记张公铎、韩继勋、韩保贞、安思谦曾事孟昶藩邸',67,'蜀捧圣控鹤','皆事蜀主于籓邸，',[('张公铎','捧圣控鹤都指挥使、曾事藩邸者'),('韩继勋','医官使、曾事藩邸者'),('韩保贞','丰德库使、曾事藩邸者'),('安思谦','茶酒库使、曾事藩邸者'),('蜀主','藩邸时受侍奉者')],year=None,when='孟昶即位前事藩邸的追叙；具体起止年未载',note='旧藩邸服务不强定为934首次发生；句列官职为当前身份，不当其藩邸时都已任当前官。')
ev('four_accuse_renhan_disloyalty','张公铎等向孟昶谗称李仁罕有异志',67,'素凶李仁罕，','云仁罕有异志；',[('张公铎','谗称异志者'),('韩继勋','谗称异志者'),('韩保贞','谗称异志者'),('安思谦','谗称异志者'),('李仁罕','被谗称者')],when='934年十月李仁罕被执杀前；确日未载',note='主素凶疑字保，不据字面造暴力；共谮说明指控，不能将异志变为已证谋反。')
ev('meng_orders_plot_against_renhan','孟昶令韩继勋等与赵季良、赵廷隐谋处置李仁罕',67,'蜀主令继勋','赵廷隐谋，',[('蜀主','命谋者'),('韩继勋','受命与二赵谋者'),('赵季良','受命参与谋者'),('赵廷隐','受命参与谋者')],when='934年十月李仁罕被执杀前；确日未载',note='等未独具名，前四人不都擅加此句参与边；谋与实际武士执杀分。')
E['renhan_death']=ev('meng_seizes_kills_renhan','孟昶趁李仁罕入朝，命武士将其捕杀',67,'因仁罕入朝，','执而杀之。',[('蜀主','命捕杀者'),('李仁罕','入朝被捕杀者')],when='934年十月癸未公布罪诏之前；捕杀确日未独列',place='成都',note='癸未为下诏暴罪日，不擅等同捕杀日；未名武士不造具体刽子手。')
claim('person',people['李仁罕'],'death_year','李仁罕于934年十月孟昶命捕杀。',67,'因仁罕入朝，命武士，执而杀之。','死亡年据本年当月叙事，确日未独载；未来改名不适用。')
E['edict']=ev('meng_renhan_crimes_edict','十月癸未孟昶下诏公布李仁罕的罪名',67,'癸未，','下诏暴其罪，',[('蜀主','下公布罪诏者'),('李仁罕','被公布罪名者')],when='934年十月癸未',note='公布罪名为诏书立场，不将罪名自动当现代证实事实；本句未列全文不编。')
E['others_death']=ev('li_jihong_song_executed','李仁罕之子李继宏、宋从会等数人被处死',67,'并其子继宏','数人皆伏诛。',[('李继宏','李仁罕子、被处死者'),('宋从会','被处死者')],when='934年十月癸未罪诏条下；各执行日未独载',note='主只列这二人及数人，未知余名单不编全家；新并族其家另列，不能把此数人等于已证全族名单。')
relationship('李仁罕','李继宏','父亲',67,'并其子继宏及宋从会等数人皆伏诛。','其子承前仁罕，继宏补姓李；A父亲→B具体方向，不反建儿子重复边。')
for name in ['李继宏','宋从会']:
 claim('person',people[name],'death_year',name+'于934年十月条下被处死。',67,'并其子继宏及宋从会等数人皆伏诛。','与诏书条相连无各执行独日，不给无证生年或死因详情。')
claim('event',E['renhan_death'],'description','新孟世家记孟昶即位数月后执杀李仁罕，并族其家。',67,'昶即位數月，執仁罕殺之，并族其家。','独立确认捕杀，数月不倒算确日；新家族范围更广，主列子宋等数人，各保描述不补未名家属。',source='xinwudaishi-064-renhan-zhao',relation='corroborates')
E['bow']=ev('li_zhao_discards_staff_bows','十月癸未李肇放下手杖向孟昶行拜礼',67,'是日，','李肇释杖而拜。',[('李肇','释杖行拜礼者'),('蜀主','被行拜礼者')],when='934年十月癸未',place='成都',note='是日承癸未，与此前庚午杖不拜分；行为改变不是医学证明当初伪疾。')
claim('event',E['bow'],'description','新孟世家亦记李肇闻李仁罕死后立即释杖而拜。',67,'及聞仁罕死，遽釋杖而拜。','新明确闻死与行为次序，无独日；保出处，不新造已被杀的李肇。',source='xinwudaishi-064-renhan-zhao',relation='corroborates')
ev('wen_jingchen_quzhou_revolt','渠州都押牙文景琛据城叛蜀',67,'蜀渠州都押牙','据城叛，',[('文景琛','渠州都押牙、据城叛者')],when='934年十月癸未后戊子前条下；确日未独载',place='渠州',note='本段普通顺叙，日期仅段落位置，不擅造乱因、兵数或影响边界。')
ev('li_yanhou_suppresses_wen','果州刺史李延厚讨平文景琛之叛',67,'果州刺史','讨平之，',[('李延厚','果州刺史、讨平者'),('文景琛','被讨平的叛首')],when='934年十月条下；讨平日未独载',place='渠州',note='讨平不等于明言文被杀；只录平叛结果，不填俘获或刑罚。')
ev('attendants_request_li_zhao_execution','孟昶左右以李肇倨慢为由请求杀他',67,'蜀主左右','请诛之；',[('李肇','被左右请诛者'),('蜀主','受请者')],when='934年十月戊子处置李肇前；确日未载',note='左右未名，不擅指定此前张韩安；请诛是请求，后致仕非已杀。')
ev('li_zhao_retires_qiongzhou','十月戊子李肇以太子少傅致仕并迁邛州',67,'戊子，','徙邛州。',[('李肇','太子少傅致仕、被迁邛州者'),('蜀主','处置者')],when='934年十月戊子',place='邛州',note='致仕与迁徙为此命，不补实际抵达日；不写诛杀。')
ev('wu_offers_xu_honours','杨溥加徐知诰大丞相、尚父、嗣齐王及九锡',68,'吴主加徐知诰','九锡，',[('吴主','加授者'),('徐知诰','被加授荣位九锡者')],note='加命与辞不受分，不等于最终接受，也不等于已受禅。旧书935后封齐及后九锡是另一阶段，未据此补本次受领。')
ev('xu_declines_honours','徐知诰辞不接受大丞相等荣位和九锡',68,'辞不受。','辞不受。',[('徐知诰','辞不受者')],note='辞承本句诸荣位九锡，不将后受其他命前移，不编辞表全文。')

reviews={59:'初王财失实换刘为四月庚辰同任复用，主补缘由；核账奏请催可征免无偿、韩支持、八月庚午诏与贫悦吏怨分。338万无单位不补贯，旧长兴4年12月前明确，主以前压缩不解929前；新核负求赂蠲及反应独立。',60:'八月辛未姚实际命相，前瓶夹名候选不重复同命，旧新同日。',61:'主索戊子投水旧丁亥卒异日，死年同；后惊赠未独日，不造帝杀。赵主丙申旧乙未异日，安国邢州军号地名同人。',62:'九癸卯增兵东安备蜀为诏，未具将兵数结果，不画疆界。',63:'李自恃请求、令宋传意、学士院侦草麻（又至主语省略不强定李或宋）、甲寅判六加中书令与赵副分；请求不是已任，副限定本次。',64:'己未云奏主旧同，日期为奏非战起；石奏自屯百井、辛酉奏杨却契丹分，战日无载，旧十月代州不替主九月百井。',65:'李闻即位迟朝、汉州亲饮逾旬、十庚午成都称足疾杖不拜分；时长不倒算，称病非医学证实伪真；新仅朝杖不拜同，没汉停日。',66:'戊寅李罢相守左、刘转右主旧同，新官及相吏扬言原因补；主相驾新相贺校读保源。新月华门提印引语补，主无人从归不是新也载。',67:'旧藩四人服务不定年，当前官与旧时分；素凶疑字保，共谮異志为指控。令韩等两赵谋、武士执杀（癸未前未独日）、癸未罪诏、子宋等死、李释杖分。新并族其家范围较主子等数人广，未名不编。文据渠叛、李延厚讨平不推文已死，左右请诛未名不当张等，戊子李致仕徙非杀。',68:'吴加荣位九锡与辞不受分，未成受禅；旧书后封齐加九锡为后阶段不支持本次已领。'}
contexts=[]
for directory in sorted((P/'sources/context').iterdir()):
 r=json.loads((directory/'paragraph.json').read_text());contexts.append(dict(file=os.path.relpath(directory/'source.txt',P/'sources'),sha256=hashlib.sha256((directory/'source.txt').read_bytes()).hexdigest(),paragraph_id=r['id'],purpose='新卷55刘昫传首核对；不提前扩录传中其他往事',url='https://github.com/greed-216/histree/blob/bf8c4dac/'+str((directory/'source.txt').relative_to(ROOT))))
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(59,69):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(59,69)],next_paragraph='zztj-v279-y0934-p069',next_volume=279,next_year=934,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷279连续934年第59—68正文段，原64—73行；核逋诏免、姚任索死赵任、东安备蜀及边奏、蜀六军授职李迟朝、唐两相罢、李仁罕被谗杀族及李肇致仕、吴加荣辞受。第69段围文州待录，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(59,69)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
