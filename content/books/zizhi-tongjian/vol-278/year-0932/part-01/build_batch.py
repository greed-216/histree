# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 932 paragraphs 1–10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 29))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'24e32443','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))
V277=YEAR.parent.parent/'vol-277/year-0932'
specs += [('jiuwudaishi-043-932-qian-report',V277/'part-02/sources/library/jiuwudaishi-043-932-qian-report','e9aa70e4','薛居正等'),('jiuwudaishi-043-932-princess-report',V277/'part-01/sources/library/jiuwudaishi-043-932-princess-report','585a188b','薛居正等'),('xinwudaishi-064-meng-peace',V277/'part-03/sources/library/xinwudaishi-064-meng-peace','0a9c7504','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-932-july']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0932-p001-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/278.txt').read_text().splitlines()
for n in range(1, 11):
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
        citation = f'卷278·长兴三年（932）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0932_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'上':'李嗣源','帝':'李嗣源','元瓘':'钱传瓘','希声':'马希声','希范':'马希范','知祥':'孟知祥','昊':'李昊','季良':'赵季良','福庆公主':'琼华长公主'}
NEW_ALIASES={'潘约':['潘約']}

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

def event(code, title, n, quote, actors, when=None, note='', year=932, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='932年七月本段；确日未独载' if n<=8 else '932年八月本段；确日未独载'
    key = 'event_zztj_278_0932_' + code
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
        edge = 'participation_zztj_278_0932_' + code + '_' + pk
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
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_278_0932_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive ten body paragraphs in the next volume of the same year.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
old='jiuwudaishi-043-932-qian-report';report='jiuwudaishi-043-932-princess-report';aug='jiuwudaishi-043-932-august';xisheng='xinwudaishi-066-xisheng-death';xifan='xinwudaishi-066-xifan-succession';peace='xinwudaishi-064-meng-peace'
E=ev('shuofang_reports_dangxiang_raid','七月辛巳朔方奏夏州党项入寇，被击败并追至贺兰山',1,'秋，七月，',None,[],when='932年七月辛巳奏；实际入寇与追击具体日未独载',place='夏州界至贺兰山',note='日期是奏闻，不保证全战发生当日；不凭朔方前帅康福自动添康为此次领兵。')
claim('event',E,'description','旧明宗纪记灵武奏党项七百骑侵扰，出师破之、生擒五十骑、追至贺兰山。',1,'靈武奏，夏州界党項七百騎侵擾，當道出師擊破之，生擒五十騎，追至賀蘭山下。','主朔方旧灵武同镇奏及同地域追击为此役补；七百来寇、五十俘骑分别，未把主辛巳奏套全部具体战日。',source=old,relation='adds')
E=ev('qian_zhongshuling','己丑钱元瓘获加中书令',2,'己丑，',None,[('元瓘','镇海、镇东军节度使、被主记加中书令者')],when='932年七月己丑',place='吴越',note='钱元瓘是钱传瓘改名，沿稳定主体，不造第二人；主中书令与旧尚书令不同，不自动改衔。')
claim('event',E,'description','旧明宗纪同己丑记两浙节度使钱元尞起复，加守尚书令。',2,'己丑，兩浙節度使錢元尞起復，加守尚書令。','旧元尞姓名疑异字，按同己丑两浙继承人识同元瓘，但原字保留；主加中书令与旧守尚书令不同，并列待纸本核，不把两官当同义。',source=old,relation='conflicts')
E=ev('li_cungui_arrives_meng_receives','庚寅李存瑰至成都，孟知祥拜泣受诏',3,'庚寅，',None,[('李存瑰','前受遣供奉官、到成都赐诏者'),('知祥','拜泣受诏者')],when='932年七月庚寅',place='成都',note='到蜀与六月帝遣分，不重复建使出发；李存瑰与新瓌旧瑰同人。')
claim('event',E,'description','旧明宗纪回报时追述李瑰至蜀，陈述朝廷厚待，孟称藩如初。',3,'瑰至蜀，具述朝廷厚待之意，知祥稱藩如初，','旧九月回报叙到蜀非独到日；主拜泣与新见瓌倨慢立场差见另一出处，未据旧否定。',source=report,relation='adds')
claim('event',E,'description','新孟世家记李瓌至蜀时，孟知祥见之倨慢。',3,'知祥見瓌倨慢。','主受诏拜泣、新见使倨慢分别针对受诏与见使场景，有不同笔法，不直接抹掉一条或当永远态度一致。',source=peace,relation='adds')
ev('xisheng_closes_temples','湖南连年旱，马希声命关闭南岳及境内神祠，仍未降雨',4,'武安、静江节度使马希声','竟不雨。',[('希声','以旱为由命闭神祠者')],year=None,when='追述湖南比年旱至马希声卒前；闭祠确年、月日未独载',place='湖南、南岳及境内神祠',note='闭门是其应对旱举措，不当现代气候归因；比年不推每年起止或所有降雨全无。')
E=ev('ma_xisheng_dies','辛卯马希声卒',4,'辛卯，','希声卒，',[('希声','去世的武安、静江节度使')],when='932年七月辛卯',place='湖南，卒地未独载',note='与前旱、闭祠毗连叙述不等确知因旱死亡。')
claim('event',E,'description','新楚世家记长兴三年希声卒，追封衡阳王。',4,'長興三年，希聲卒，追封衡陽王。','补追封称号不从此推精确授封日，更不把衡阳王当生前一直所称爵。',source=xisheng,relation='corroborates')
claim('event',E,'time_original','旧明宗纪八月己亥记以湖南节度使马希声卒废朝。',4,'己亥，以湖南節度使馬希聲卒廢朝。','旧段首八月，己亥是朝廷废朝记，不改主七月辛卯卒日，未提前本批另建八月废朝事件。',source=aug,relation='adds')
E=ev('yuan_pan_welcome_xifan','袁诠、潘约等迎朗州的马希范而立之',4,'六军使袁诠、',None,[('袁诠','六军使、迎立者'),('潘约','同迎立者'),('希范','镇南节度使、朗州被迎立者')],when='932年七月马希声卒后；迎立具体日未独载',place='朗州',note='辛卯独载希声卒，迎立不强套同一日；后八月到长沙正式袭位另记。袁六军使明确，潘不凭并列自动推同六军使。')
claim('event',E,'description','新楚世家同记希声卒后弟希范立。',4,'弟希範立。','同继承人，新不独载袁潘迎及朗州，迎立名单仍据主。',source=xisheng,relation='corroborates')
relationship('希范','希声','弟弟',4,'弟希範立。','新明称弟，马希范→马希声弟弟；同日生不否定史称弟，未据此猜生母相同或双胞胎。',source=xisheng)
claim('person',people['马希范'],'name','马希范字宝规。',4,'希範字寶規，','字明确，新繁範展示范，沿旧马希范稳定key。',source=xifan,relation='adds')
claim('person',people['马希范'],'description','新楚世家记马希范为马殷第四子，希声与希范同日生。',4,'希範字寶規，殷第四子也。殷子十餘人，嫡子希振長而賢，其次希聲與希範同日生，','同日生不填未知出生年及具体日，也不推同母双胞胎；未新增未具名十余兄弟。',source=xifan,relation='adds')
E=ev('meng_sends_li_home_memorial','乙未孟知祥遣李存瑰还，表谢罪并告福庆公主之丧',5,'乙未，','且告福庆公主之丧。',[('知祥','遣还及上表者'),('李存瑰','被遣还朝的使者'),('福庆公主','被报告丧事的已故孟妻')],when='932年七月乙未遣还；到京及奏闻确日未独载',place='成都至后唐',note='公主丧事已经正月录过，当前是报告不是再次死亡；前琼华改福庆同主体。主七月遣与旧新九月回奏分层留。')
claim('event',E,'time_original','旧明宗纪九月壬辰记李瑰从西川回，带孟表及公主正月卒的报告。',5,'壬辰，供奉官李瑰自西川回，節度使孟知祥附表陳敘隔絕之由，並進物，','摘录保留底本繁字；九月到报不是七月遣还日的冲突，未知全程时长不擅算。',source=report,relation='adds')
ev('meng_resumes_submission','史书述孟知祥自此复称藩，但愈加骄倨',5,'自是复称籓，',None,[('知祥','被史述复称藩及骄倨者')],year=None,when='遣使谢罪后持续姿态；具体起止未独年',place='西川与后唐',note='复称藩是政名姿态，骄倨是史评价，不等实际辖区被中央收回。')
E=ev('congke_fengxiang_appointment','庚子李从珂由西京留守出任凤翔节度使',6,'庚子，',None,[('李从珂','西京留守、同平章事、赴凤翔任者')],when='932年七月庚子',place='凤翔',note='只录职务任命，不提前934起兵称帝。')
claim('event',E,'description','旧明宗纪七月记皇子西京留守、京兆尹李从珂为凤翔节度使。',6,'以皇子西京留守、京兆尹從珂為鳳翔節度使。','旧此句接己亥段但未另记任命干支，保留定位不自称旧明确庚子或强判主错；旧京兆尹为补旧称衔。',source=old,relation='corroborates')
E=ev('wuxing_army_abolished','朝廷废武兴军，复以凤、兴、文三州隶山南西道',7,'废武兴军，',None,[],place='凤、兴、文三州及山南西道',note='未独日，不套前庚子；这是军州行政隶属变更，不画新确定疆界。')
claim('event',E,'description','旧明宗纪记废凤州武兴军节制为防御使，所管兴文二州依旧隶兴元府。',7,'廢鳳州武興軍節制為防禦使，並所管興、文二州並依舊隸興元府。','主三州复隶山南与旧凤改防御、兴文归兴元两层表述保留，不把军治兴元与道名当两个不同接收政权。',source=old,relation='adds')
E=ev('zhaofeng_anguo_appointment','丁未赵凤同平章事，出任安国节度使',8,'丁未，',None,[('赵凤','门下侍郎、同平章事、被外任安国者')],when='932年七月丁未',place='安国军',note='原保同平章事衔，未单凭外任断所有宰相荣衔已剥。')
claim('event',E,'description','旧明宗纪同丁未记赵凤检校太傅、同平章事，任邢州节度使。',8,'丁未，以門下侍郎兼吏部尚書、同平章事、監修國史趙鳳為檢校太傅、同平章事，充邢州節度使。','安国军治邢州军州称法对应同人同日，不另建一次任命；前后职衔各书保留。',source=old,relation='corroborates')
ev('xifan_arrives_changsha','八月庚申马希范至长沙',9,'八月，庚申，','马希范至长沙；',[('希范','被迎后到长沙者')],when='932年八月庚申',place='长沙',note='到城不是七月已到城；长沙与朗州分。')
E=ev('xifan_formal_succession','八月辛酉马希范袭位',9,'辛酉，','袭位。',[('希范','袭位的楚继承者')],when='932年八月辛酉',place='长沙',note='与七月被迎立过程分，不另建第二个马希范人物，也未把此当已获所有后唐新爵。')
claim('event',E,'description','新楚世家记希范以次立、袭马殷官爵封楚王。',9,'希聲卒，而希範以次立，襲殷官爵，封楚王。','新概述包括袭爵封王，主此时仅袭位；封爵具体日未独，不静改主为辛酉帝已授楚王、天册上将军等后来衔。',source=xifan,relation='adds')
ev('meng_orders_five_liuhou_petition','甲子孟令李昊为赵季良等五留后草表，请封孟蜀王行墨制并为诸将求旌节',9,'甲子，','仍自求旌节，',[('知祥','令草表者'),('昊','被命为五留后草表者'),('季良','武泰留后、拟上表主体代表')],when='932年八月甲子',place='两川',note='这是原拟由群下求封表，未完成获批；五留后本句只明赵，未把别书名单无差别全塞参与。')
ev('lihao_warns_petition_power','李昊认为由诸将为自己求节钺及为孟求封将使轻重之权在群下，劝孟自请',9,'昊曰：','岂不可邪！”',[('昊','提出权柄风险并劝改表者'),('知祥','受劝者')],when='932年八月甲子草表议中',place='两川',note='节铖为主疑字保留，展示按上下文节钺；权在群下为李分析，不造群将已夺政权。')
E=ev('meng_revises_petition','孟采李昊建议，改由自己请行墨制补两川刺史以下，又请赵季良等五留后授节度使',9,'知祥大悟，',None,[('知祥','改为自请并请授诸将者'),('昊','草改表者'),('季良','拟正授节度使的留后之一')],when='932年八月甲子本段；上达与获准日期未独载',place='两川至后唐',note='表请仍不是中央已授封；刺史以下自补不包括本句已获得节度使任免全权。')
claim('event',E,'time_original','旧明宗纪九月壬辰记回使所带孟表请五将节钺及许墨制补授。',9,'又表立功將校趙季良等五人，乞授節鉞；部內刺史令錄已下官，乞許墨製補授。','旧是回报时收到表，主八月草表，请而未已允；十月正式处置待后段不提前。',source=report,relation='corroborates')
# Retrospective background supports the present request; earlier dated events stay archived.
ev('an_uses_east_troops_as_escort','通鉴追述安重诲欲图两川，刺史任命以东兵牙队卫送，小州不减五百，夏等各数千',10,'初，安重诲欲图两川，','皆以牙队为名。',[('安重诲','追述谋两川并借卫送布兵者'),('知祥','被图及曾杀李严的川帅'),('夏鲁奇','以数千牙队赴任者'),('李仁矩','以数千牙队赴任者'),('武虔裕','以数千牙队赴任者')],year=None,when='初，追述孟杀李严后、两川战前布兵；各任年份分见既有档案',place='两川',note='已过人物参与是追叙身份，不造安、夏、李死后在932复生；不重建此前已录任命或杀李严事件。小州至少五百，不当所有州整齐五百；各数千不猜总额。')
ev('meng_has_east_soldiers_aggregate','通鉴合述孟克六镇后得东兵约三万人，担忧朝廷征还',10,'及知祥克遂、阆、利、夔、黔、梓六镇，','恐朝廷征还，',[('知祥','兼诸镇后得东兵并忧征还者')],year=None,when='初追叙相继克六镇至兼东川后；各镇已录不同年月，不独定合计日',place='遂、阆、利、夔、黔、梓六镇',note='无虑三万人约数合述，不为六镇各建同年新克复；不与汉州八千、廷三万相加成全国兵籍。恐征还是忧虑，未本句已征还。')
E=ev('meng_requests_troop_families','孟知祥上表，请将所得东兵的妻子家属送入川',10,'表请其妻子。',None,[('知祥','请东兵家属入川者')],year=None,when='兼两川后请求，主置初追叙未独年；他书同前后段补',place='两川与后唐',note='妻子为兵之家属，不造具体妻或未名子女；表请不等朝廷已遣家属，后来拒允待主后段。')
claim('event',E,'description','新孟世家记唐兵在蜀数万人，孟厚给衣食，因请送其家属。',10,'唐兵先在蜀者數萬人，知祥皆厚給其衣食，因請送其家屬，','仅取请求及其背景，后明宗不许在后主段核录；新语段在长兴四年二月封王后，主初追叙层次不同，未把本请强定当今八月。',source='xinwudaishi-064-troop-families',relation='adds')
reviews={1:'七月辛巳是朔方奏闻非整役确日，旧灵武七百寇五十俘同地域补，不凭前朔方康福添其领兵。',2:'钱元瓘与钱传瓘改名同主体；主中书令旧守尚书令同己丑不同官并列，旧元尞疑字按同两浙继承人识不改摘录，纸本待核。',3:'七月庚寅到成都与六月遣分。旧九月回报追述到蜀不移到日；主拜泣受诏、新见使倨慢不同场景笔法各留。',4:'比年旱闭祠无独年null，不推死亡因旱。主辛卯卒旧八月己亥废朝为不同阶段，不改卒日。袁潘迎朗州后八月长沙袭分，潘不自动套袁六军使衔。新希声弟希范明，弟方向明确；同日生不推同母双胞胎，字宝规补，无未知出生年。',5:'乙未遣还表谢告丧，旧九月壬辰回奏层次分；公主已正月卒当前报丧不复死。复称藩、骄倨概叙持续yearnull，不当中央已收回川权。',6:'主七月庚子赴凤翔，旧七月接己亥段任命未独干支，不硬造两天矛盾；同西京留守从珂识，京兆衔补，不提前934帝位。',7:'武兴军废三州复山南隶属，旧凤防御兴文归兴元两层留。不套前庚子或造实际地理坐标。',8:'丁未赵凤外任安国旧邢州同军治，保同平章事名衔；未断任相荣衔全撤或重复建另一外任。',9:'八月庚申到辛酉袭楚分；新概述封楚日期不强套当日，不提前天册职。甲子原由五留后草求王、李权柄风险劝、孟改自表请墨制及诸将节分；请非已准，五名单仅主明赵不无条件加其他四。主节铖疑字原保留，新旧表朝九月奏闻不是八月草日冲突。',10:'初布兵及相继六镇东兵合述yearnull，先已死安夏李只是过去参与，既有杀李严或任命不重复。五百小州下限、各数千与总约三万口径分，不加前战军额。请兵家属未独日期null，妻子家属不造未名人物；新上下文年层次异留，后朝廷不许待主续段。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,11):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=932,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph='zztj-v278-y0932-p011',next_volume=278,next_year=932,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷278连续932年第1—10段、原6—15行；党项奏、钱加衔、李使抵返、楚旱马卒希范迎立袭位、从珂赵凤出镇、武兴废、孟墨制表及东兵背景家属请。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,11)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
