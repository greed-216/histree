# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 280, year 936 paragraphs 13–20."""
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
 specs.append((directory.name,directory,'1382703d','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [
 ('tongjian-280-936-may-councils',ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-02/sources/library/tongjian-280-936-may-councils','51c8f3ea','司马光等'),
 ('jiuwudaishi-048-936-may-background',ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-02/sources/library/jiuwudaishi-048-936-may-background','51c8f3ea','薛居正等'),
 ('xinwudaishi-016-liu-yanhao',ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-02/sources/library/xinwudaishi-016-liu-yanhao','0a39d9d7','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-280-936-may-councils','tongjian-280-936-may-july-revolts']
B = {'format_version': 1, 'batch_key': 'zztj-v280-y0936-p013-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'xinwudaishi-066-xiguang-brother':'卷66·楚世家·马希广','xinwudaishi-056-lv-qi-peace':'卷56·吕琦传（对契丹和议）','xinwudaishi-055-sikong-duties':'卷55·马胤孙传（司空职掌议论）','songshi-483-sun-guangxian':'卷483·孙光宪传','xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
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
for n in range(13, 21):
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
    labels={'xinwudaishi-066-xiguang-brother':'卷66·楚世家·马希广','xinwudaishi-056-lv-qi-peace':'卷56·吕琦传（对契丹和议）','xinwudaishi-055-sikong-duties':'卷55·马胤孙传（司空职掌议论）','songshi-483-sun-guangxian':'卷483·孙光宪传','xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '五月条下及追叙' if n<=14 else '五月至六月' if n==15 else '六月' if n<=17 else '七月条下及追叙'
        citation = f'卷280·后唐清泰三年（936；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_280_0936_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_ALIASES={'皇甫立':[],'张彦琪':['張彥琪'],'武廷翰':[],'方太':[],'安审信':['安審信'],'安重荣':['安重榮'],'张令昭':['張令昭'],'徐景遂':['景遂'],'石重英':['石重殷','重英','重殷'],'石重裔':['重裔'],'石敬德':['敬德'],'石敬威':['敬威'],'桑迁':['桑遷'],'沙彦珣':['沙彥珣','沙彦昫']}
ALIASES.update({'杨光远':'杨檀','皇后':'刘氏（李从珂后）','重殷':'石重英','重裔':'石重裔','敬德':'石敬德','敬威':'石敬威','彦昫':'沙彦珣','景遂':'徐景遂'})

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
    if when is None:when='936年'+('五月' if n<=15 else '六月' if n<=17 else '七月')+'条下；确日未独载'
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
add('huangfu_reports_revolt','五月戊戌皇甫立奏报石敬瑭反',13,'戊戌，','奏敬瑭反。',[('皇甫立','昭义节度使、报告者'),('石敬瑭','被报告者')],when='936年五月戊戌',note='奏报日期与实际发兵起日分，非皇甫当日才首次知晓。')
sup('huangfu_reports_revolt',13,'jiuwudaishi-048-936-may-background','戊戌，昭義奏，河東節度使石敬瑭叛。','旧同日记昭义奏报。','旧未具奏者名字，主明皇甫立。')
add('shi_requests_xu_prince_succession','石敬瑭上表称李从珂为养子不应承祀，要求传位许王',13,'敬瑭表：','请传位许王。”',[('石敬瑭','上表要求者'),('帝','被指责、被要求者')],note='养子不应承祀为石的政治指责，不作为网站认定继位非法；许王不靠称号臆造新人物。')
sup('shi_requests_xu_prince_succession',13,'jiuwudaishi-048-936-may-background','許王先朝血緒，養德皇闈，','旧也记石表强调许王先朝血绪。','政治诉求不是已经传位。',relation='adds')
add('congke_tears_shi_memorial','李从珂撕表抵地，诏以鄂王及卫州事反驳石敬瑭',13,'帝手裂','何人肯信！”',[('帝','毁表、答诏者'),('石敬瑭','答诏对象')],note='提卫州往事不重造934事件，诏中责难归帝说法。')
add('shi_stripped_titles','五月壬寅制削夺石敬瑭官爵',13,'壬寅，','官爵。',[('石敬瑭','被削夺者')],when='936年五月壬寅',note='削官非此日被杀；诏命与后来的军队执行分。')
sup('shi_stripped_titles',13,'jiuwudaishi-048-936-may-background','壬寅，削奪石敬瑭官爵，便令張敬達進軍攻討。','旧同日并补令张敬达进军。','补诏令，不直接当已抵城。',relation='adds')
add('jingda_array_commission','五月乙巳张敬达兼太原四面排陈使',13,'乙巳，','四面排陈使，',[('张敬达','兼任者')],when='936年五月乙巳',place='太原',note='与丙午部署、六月招讨分职分日；旧乙卯授四面部署不同层次另留说明。')
sup('jingda_array_commission',13,'jiuwudaishi-048-936-may-background','乙卯。以晉州節度使張敬達為太原四面兵馬都部署，尋改為招討使；','旧写乙卯任四面部署，寻改招讨，主乙巳排陈、丙午部署。','主旧干支、官衔层次不同，不能改主日期或称同一精确官命已两书一致。',relation='conflicts',field='time_original')
for code,title,start,end,name in [('zhang_yanqi_commander','张彦琪任太原四面马步军都指挥使','河阳节度使张彦琪','为马步军都指挥使，','张彦琪'),('an_shenqi_cavalry','安审琦任太原四面马军都指挥使','以安国节度使安审琦','为马军都指挥使，','安审琦'),('xiangli_infantry','相里金任太原四面步军都指挥使','以保义节度使相里金','为步军都指挥使，','相里金'),('wu_trench_commission','武廷翰任太原四面壕寨使','以右监门上将军武廷翰','为壕寨使。','武廷翰')]:
 add(code,'五月乙巳'+title,13,start,end,[(name,'获任者')],when='936年五月乙巳条下',place='太原',note='逐项任命无另日，承乙巳，非每位皆已抵任所。')
add('jingda_four_sides_command','五月丙午张敬达任太原四面兵马都部署',13,'丙午，','为太原四面兵马都部署，',[('张敬达','获任者')],when='936年五月丙午',place='太原')
add('yang_guangyuan_deputy','五月丙午杨光远任太原四面副部署',13,'以义武节度使杨光远','为副部署。',[('杨光远','义武节度使、获副部署者')],when='936年五月丙午条下',place='太原',note='沿杨檀既有主体与已应用杨光远别名，不造新杨光远。')
sup('yang_guangyuan_deputy',13,'jiuwudaishi-048-936-may-background','丙辰，以定州節度使楊光遠為太原四面兵馬副部署、兼馬步都虞候，','旧丙辰任副部署并兼马步都虞候。','主丙午与旧丙辰日期异，不暗自替换。',relation='conflicts',field='time_original')
add('jingda_field_office','五月丁未张敬达知太原行府事',13,'丁未，','知太原行府事，',[('张敬达','领行府事者')],when='936年五月丁未',place='太原')
add('gao_xingzhou_pacification','五月丁未高行周任太原四面招抚、排陈等使',13,'以前彰武节度使高行周','为太原四面招抚、排陈等使。',[('高行周','获任者')],when='936年五月丁未条下',place='太原',note='未记本次已抵城；同人旧七月乙未另有潞州授职，层次保留不提前扩录。')
add('fang_tai_quells_dingzhou','杨光远出行后定州军乱，牙将方太讨平',13,'光远既行，',None,[('杨光远','离定州者'),('方太','讨平军乱者')],when='936年五月杨光远行后；确日未载',place='定州',note='千乘为方太籍贯，不当讨乱地点；未名叛军不造人。')
add('jingda_camps_jinan','张敬达率军驻晋安乡，主书兵数字作后三万',14,'张敬达将后三万','营于晋安乡，',[('张敬达','驻军将领')],place='晋安乡',note='将后三万疑后字转录讹，展示保疑字不硬把后解释兵种；兵数待底本复核。')
add('anshenxin_deserts_report','五月戊申张敬达奏安审信叛奔晋阳',14,'戊申，','叛奔晋阳。',[('张敬达','报告者'),('安审信','西北先锋马军都指挥使、转投者')],when='936年五月戊申奏报',place='晋阳',note='奏报日与下面追叙出发过程分。')
sup('anshenxin_deserts_report',14,'jiuwudaishi-048-936-may-revolts','戊申，張敬達奏，西北面先鋒都指揮使安審信率雄義左第二指揮二百二十七騎，並部下共五百騎，剽劫百井，叛入太原。','旧同日记总共五百骑，其中雄义227骑，劫百井入太原。','主数百骑与旧具体细项各保，不把227当所有转投军队合计。',relation='adds')
sup('anshenxin_deserts_report',14,'xinwudaishi-007-936-revolts','戊申，先鋒指揮使安審信叛降于石敬瑭。','新末帝纪同戊申记转投石敬瑭。','同日相应记载，太原晋阳同地不同称。')
claim('person',person('安金全',14,'主安审信之弟子称谓中的金全',span(14,'审信，','敬瑭与之有旧。')),'description','主称安审信为金全之弟子，并与石敬瑭有旧。',14,'审信，金全之弟子也，敬瑭与之有旧。','弟子古义可能指弟之子，本次无明确证据拆成师徒或叔侄边，保持待考，不合李金全。')
add('anyuanxin_garrisons_dai','追叙安元信率所部六百余人戍代州，刺史张朗善待',14,'先是，','张朗善遇之，',[('安元信','雄义都指挥使、戍将'),('张朗','代州刺史、善遇者')],year=None,when='先是，转投晋阳之前；驻屯起年未载',place='代州',note='马邑籍贯不当驻所；旧写伏州异地名保在补证。')
sup('anyuanxin_garrisons_dai',14,'jiuwudaishi-048-936-may-revolts','先是，雄義都在伏州屯戍，其指揮使安元信謀殺伏州刺史張朗，','旧前驻地和张朗职记作伏州，主代州。','伏代字形或电子本异文不私改，人物同名同事沿旧主体，地名异保待核。',relation='conflicts')
add('anyuanxin_urges_zhang','安元信密劝张朗通石敬瑭以自全，张不从，互相猜忌',14,'元信密说朗曰：','互相猜忌。',[('安元信','劝说者'),('张朗','拒绝者')],year=None,when='转投晋阳前追叙；确年日未载',place='代州',note='石举事必成为安的预测，未记张实际通石。')
add('anyuanxin_failed_plot','安元信谋杀张朗不成，率众奔安审信',14,'元信谋杀朗，','帅其众奔审信，',[('安元信','谋杀未遂、奔军者'),('张朗','谋杀对象'),('安审信','所奔军主将')],when='936年五月转投前；确日未载',note='不克为未遂，张朗不填此时死亡。')
add('an_troops_plunder_baijing','安审信与安元信率数百骑掠百井奔晋阳',14,'审信遂帅麾下','奔晋阳。',[('安审信','领骑者'),('安元信','同奔者')],place='百井、晋阳',note='麾下数百骑与先前六百余所部非直接可相加的独立总数。')
add('shi_questions_anyuanxin','石敬瑭问安元信为何舍强归弱',14,'敬瑭谓元信曰：','舍强而归弱？”',[('石敬瑭','询问者'),('安元信','被问者')],place='晋阳')
add('anyuanxin_explains_choice','安元信以主上失信论强弱，预测其亡而说明归石原因',14,'对曰：','何强之有！”',[('安元信','解释选择者'),('石敬瑭','听解释者')],place='晋阳',note='非知星识气、帝失信及亡国预测归安之言，不当站点已验证事实。')
add('shi_entrusts_anyuanxin','石敬瑭听安元信说法而喜，委以军事',14,'敬瑭悦，','委以军事。',[('石敬瑭','委任者'),('安元信','获委者')],place='晋阳',note='委以军事未具新官名，勿拟造某节度使。')
add('anzhongrong_deserts','安重荣自代北率步骑五百奔晋阳',14,'振武西北巡检使','重荣，朔州人也。',[('安重荣','转投者')],place='代北、晋阳',note='朔州籍贯；主步骑五百，旧五百骑、晋纪数千另记异表述。')
sup('anzhongrong_deserts',14,'jiuwudaishi-048-936-may-revolts','己酉，振武節度使安叔千奏，西北界巡檢使安重榮驅掠戍兵五百騎叛入太原。','旧己酉奏安重荣驱掠戍兵五百骑入太原。','补奏报日及兵为骑，与主步骑不同，不暗改主兵种。',relation='adds')
sup('anzhongrong_deserts',14,'xinwudaishi-007-936-revolts','己酉，振武戍將安重榮叛降于石敬瑭。','新也以己酉记安重荣降石。','补纪日，不把主无日独记改成主也明具日。',relation='adds',field='time_original')
add('song_shenqian_ningguo','宋审虔改任宁国节度使、侍卫马军都指挥使',14,'以宋审虔',None,[('宋审虔','获改任者')],place='宁国军',note='原待卫疑侍卫，摘录保待；前批河东任命与此次另记。')
sup('song_shenqian_ningguo',14,'jiuwudaishi-048-936-may-revolts','以新授河東節度使宋審虔為宣州節度使，充侍衛馬軍都指揮使。','旧称新授河东宋改宣州节度、侍卫马军。','宁国军治宣州，两称同府，旧侍字明确供校读。',relation='adds')
add('liuyan_hao_government_abuses','主书称刘延皓在天雄恃后族骄纵，夺财、减军赐、宴饮无度',15,'天雄节度使','宴饮无度。',[('刘延皓','被史书描述的节度使')],year=None,when='魏博兵变前治理背景；各次起止年日未具',place='天雄军',note='恃后族与行为由主史概述，逐项保留不添受害者、金额。')
sup('liuyan_hao_government_abuses',15,'xinwudaishi-016-liu-yanhao','以后故用事，受賕，掠人園宅，在鄴下不恤軍士，軍士皆怨。','新刘氏传附刘延皓补受赇、掠园宅等。','新前素谨厚后改节评价保自书，未给各行为硬定本年。',relation='adds')
add('zhang_lingzhao_seizes_weibo','张令昭谋以魏博应河东，癸丑未明率众攻克牙城',15,'捧圣都虞候张令昭','克之；',[('张令昭','兵变领头者')],when='936年五月癸丑未明（主书）',place='魏博牙城',note='谋应河东不当已达成实质共同指挥。')
sup('zhang_lingzhao_seizes_weibo',15,'jiuwudaishi-048-936-may-revolts','壬子，鄴都屯駐捧聖都虞候張令昭逐節度使劉延皓，據城叛。','旧壬子记逐刘据城叛，新末帝纪也作壬子。','主癸丑与旧壬子相差一日，并列不消除差异。',relation='conflicts',field='time_original')
add('liuyan_hao_flees_looting','刘延皓从牙城脱身，乱兵大掠',15,'延皓脱身走，','乱兵大掠。',[('刘延皓','脱身者')],place='魏博',note='未名乱兵不都当张个人亲自抢夺；新补先走相州，与主后至洛阳分阶段。')
sup('liuyan_hao_flees_looting',15,'xinwudaishi-016-liu-yanhao','延皓走相州。','新补其逃走相州。','主随后至洛阳不必矛盾，保阶段不当主本句写洛阳。',relation='adds')
add('zhang_lingzhao_requests_flag','张令昭奏称抚安士卒而权领军府，请赐旌节',15,'令昭奏：','乞赐旌节！”',[('张令昭','自述领府、求旌节者')],note='自称抚安不当第三方已证稳定军队；求旌节非已经正式任天雄节度。')
add('emperor_orders_liuyan_exile','刘延皓至洛阳，李从珂怒，命远贬',15,'延皓至洛阳，','命远贬；',[('刘延皓','至洛阳、初被命贬者'),('唐主','下远贬命者')],place='洛阳',note='命远贬与后改处置分，未见他已到远州。')
add('empress_intercedes_liuyan','皇后为刘延皓求情',15,'皇后为之请，','皇后为之请，',[('皇后','求情者'),('刘延皓','求情对象')],note='沿既有刘氏（李从珂后），不合庄宗刘后或另造刘皇后。')
add('liuyan_stripped_private_home','六月庚申刘延皓止削官爵，归私第',15,'六月，庚申，',None,[('刘延皓','被削官、归私第者')],when='936年六月庚申（主）',note='止削不是被处死；原远贬命随后变。')
sup('liuyan_stripped_private_home',15,'jiuwudaishi-048-936-june-armies','六月辛酉，天雄軍節度使劉延皓削奪官爵，勒歸私第。','旧官爵削归私第作六月辛酉。','主庚申旧辛酉差一日，保双定位。',relation='conflicts',field='time_original')
add('xu_jingqian_ill_removal','六月辛酉徐景迁因病罢太保、同平章事',16,'辛酉，','以疾罢，',[('徐景迁','因病罢职者')],when='936年六月辛酉',place='吴',note='以疾罢非卒年，不填已死亡。')
add('xu_jingsui_succeeds_office','六月辛酉徐景遂代兄为门下侍郎、参政事',16,'以其弟',None,[('徐景遂','获任者'),('徐景迁','被弟代职的前任')],when='936年六月辛酉条下',place='吴',note='原弟明确长幼，吴官而非937南唐帝位。')
relationship('徐景迁','徐景遂','兄长',16,'以其弟景遂代为门下侍郎、参政事。','承前景迁，其弟明确；A是B兄长。')
add('lingzhao_provisional_command','六月癸亥张令昭获任右千牛卫将军、权知天雄军计事',17,'癸亥，','权知天雄军计事。',[('唐主','授官者'),('张令昭','获权任者')],when='936年六月癸亥',place='天雄军',note='原计事疑军事、府事异写保原；非正式天雄节度。')
sup('lingzhao_provisional_command',17,'jiuwudaishi-048-936-june-armies','癸亥，以天雄軍守禦、右捧聖第二軍都虞候張令昭為檢校司空，行右千牛將軍，權知天雄軍府事。','旧同日补检校司空与府事表述。','主计事保字，旧明确府事供校读，尚非节旄授节度。',relation='adds')
add('lingzhao_accepts_pending','张令昭因调发未集，暂受新命',17,'令昭以调发未集，','且受新命。',[('张令昭','暂受者')],note='且暂时，不当已经彻底服从朝廷。')
add('lingzhao_qizhou_transfer','不久诏张令昭移齐州防御使',17,'寻有诏','徙齐州防御使，',[('张令昭','被命移职者')],place='齐州',note='寻未具日，新诏与是否赴任分。')
sup('lingzhao_qizhou_transfer',17,'jiuwudaishi-048-936-june-armies','以權知魏府事、右千牛將軍張令昭為齊州防禦使，','旧补齐州调职同官命，接辛未条下。','旧前许寂卒辛未、本命无独立日；不偷换主寻为確辛未。',relation='adds')
add('lingzhao_waits_hedong','张令昭托称士卒挽留，主书称其实等待河东成败',17,'令昭托以','实俟河东之成败。',[('张令昭','留任观望者')],note='托词与史家判断各分层，不直接引用其伪装为真实群众挽留。')
add('lingzhao_kills_envoy','李从珂遣使谕张令昭，张杀使者',17,'唐主遣使谕之，','令昭杀使者。',[('唐主','遣使者'),('张令昭','杀使者者')],note='使者未具名，不猜邢立等。')
add('fan_yanguang_weibo_command','六月甲戌范延光任天雄四面行营招讨使、知魏博行府事',17,'甲戌，','知魏博行府事，',[('范延光','获任讨魏博主帅')],when='936年六月甲戌',place='魏博')
sup('fan_yanguang_weibo_command',17,'jiuwudaishi-048-936-june-armies','甲戌，以汴州節度使範延光為天雄軍四面招討使，知行府事。','旧同日同讨魏博官命。','宣武军治汴州两称，不合别的范。')
add('jingda_taiyuan_campaign','六月甲戌张敬达改充太原四面招讨使',17,'以张敬达充','太原四面招讨使，',[('张敬达','获改官者')],when='936年六月甲戌条下',place='太原',note='与五月排陈、部署分；旧前寻改招讨只补层次不统一日。')
add('yang_guangyuan_campaign_deputy','六月甲戌杨光远为太原四面副招讨使',17,'以杨光远','为副使。',[('杨光远','获任副使者')],when='936年六月甲戌条下',place='太原',note='沿杨檀实体，承太原招讨不是魏博副使。')
add('li_zhou_weibo_deputy','六月丙子李周任天雄军四面行营副招讨使',17,'丙子，',None,[('李周','西京留守、获副招讨命者')],when='936年六月丙子',place='天雄军')
sup('li_zhou_weibo_deputy',17,'jiuwudaishi-048-936-june-armies','丙子，以西京留守李周為天雄軍四面副招討使兼兵馬都監。','旧同日补兼兵马都监。','同命补官，不推李周已率兵出发。',relation='adds')
add('shi_sons_hide','石敬瑭二子重殷、重裔闻其举兵，藏于民间井中',18,'石敬瑭之子','匿于民间井中。',[('重殷','右卫上将军、藏匿者'),('重裔','皇城副使、藏匿者')],when='936年石敬瑭举兵后，七月捕获前；确日未载',note='右卫同职同藏同死对旧重英，主体规范石重英，主重殷留别名；不凭别名混其弟敬殷。')
sup('shi_sons_hide',18,'jiuwudaishi-048-936-july-revolts','時重英等匿於民家井中，獲而誅之，並族所匿之家。','旧重英等同样藏民井而被获。','旧重英对主重殷按官职、同行重裔、行动一致识别异名，不另造第三儿子。',relation='adds')
claim('person',people['石重英'],'aliases','主重殷与旧石重英按同官、同重裔藏井被诛识别同一人，保异名。',18,'誅右衛上將軍石重英、皇城副使石重裔，皆敬瑭之子也。','与主逐要素对照；同家族敬殷、重胤不因此并入。',source='jiuwudaishi-048-936-july-revolts')
for child in ['重殷','重裔']:relationship('石敬瑭',child,'父亲',18,'石敬瑭之子右卫上将军重殷、皇城副使重裔','主明之子，A是B父亲；不据未明生母造母子。')
add('shijingde_kills_family_escapes','石敬德杀妻女后逃走',18,'弟沂州都指挥使敬德','而逃，',[('敬德','沂州都指挥使、杀家属并逃者')],when='936年兄举兵后，七月条前追述；确日未载',place='沂州',note='未名妻女不造姓名，原行为直录不添人数、原因或逃亡地点。')
relationship('石敬瑭','敬德','兄长',18,'弟沂州都指挥使敬德','前石敬瑭之弟，明示长幼。')
add('shijingde_captured_dies','石敬德逃后被捕，主称死于狱中',18,'寻捕得，','死狱中，',[('敬德','被捕、死狱者')],when='936年逃后寻被捕，七月条前附述；确日未载',note='主死狱不是明确斩于某日，旧七月辛卯诛及族家说另留。')
sup('shijingde_captured_dies',18,'jiuwudaishi-048-936-july-revolts','辛卯，沂州奏，誅都指揮使石敬德，並族其家，敬瑭之弟也。','旧七月辛卯沂州奏诛敬德并族其家。','主死狱与旧奏诛表述不同，保处置及奏日层次，不在主字段填确定斩日。',relation='conflicts')
add('shijingwei_suicide','石敬瑭从弟彰圣都指挥使石敬威自杀',18,'从弟彰圣','敬威自杀。',[('敬威','自杀者')],when='936年兄举兵后，七月捕二子前附述；确日未载',note='从弟非亲弟，同宗身份保称谓，不猜他的父亲。')
relationship('石敬瑭','敬威','从兄',18,'从弟彰圣都指挥使敬威自杀。','从弟明示旁系较幼，对向用从兄；保古称，不擅限定亲父或几代共同祖先。')
add('shi_sons_executed','七月戊子石重英（主作重殷）、石重裔被捕诛，藏匿之家也被族诛',18,'秋，七月，',None,[('重殷','被捕诛者'),('重裔','被捕诛者')],when='936年七月戊子（主）',note='藏匿家族未名不造人；主戊子与旧己丑差日，死亡同年确载，时间干支不擅调。')
sup('shi_sons_executed',18,'jiuwudaishi-048-936-july-revolts','己丑，誅右衛上將軍石重英、皇城副使石重裔，皆敬瑭之子也。','旧七月己丑诛同二子。','主戊子旧己丑差一日，重殷/重英异名核要素沿同人。',relation='conflicts',field='time_original')
add('ma_xifan_returns_north','七月庚寅马希范自桂州北还',19,'庚寅，',None,[('马希范','北还者')],when='936年七月庚寅',place='桂州',note='承前四月赴桂，同王同旅程；北还未独具目的城。')
add('sang_qian_accuses_yin','桑迁奏称尹晖逐云州节度使沙彦珣，收兵应河东',20,'云州步军指挥使桑迁','收其兵应河东。',[('桑迁','奏称者'),('尹晖','被指称者'),('沙彦珣','奏称中被逐者')],note='只作为桑迁奏称，与下面沙自报相对；私用字名用旧明确沙彥珣核身份，不当尹确已叛。')
add('sha_reports_sang_rebellion','七月丁酉沙彦珣表桑迁谋叛应河东、引兵围子城',20,'丁酉，','引兵围子城。',[('沙彦珣','报告者'),('桑迁','被报作乱者')],when='936年七月丁酉奏表',place='云州子城',note='原彦私用字保快照，丁酉是奏表日，兵围真实起日旧补七月2夜。')
sup('sha_reports_sang_rebellion',20,'jiuwudaishi-048-936-july-revolts','丁酉，雲州節度使沙彥珣奏，此月二日夜，步軍指揮使桑遷作亂，以兵圍子城，','旧丁酉奏并补实际围城七月二日夜，明确沙彥珣。','分事件发生与上表时间，主私用字靠旧同官同事记名，不改原快照。',relation='adds',field='time_original')
claim('person',people['沙彦珣'],'aliases','沙彦珣主文见彦昫及私用字拆件名，旧明确沙彥珣。',20,'雲州節度使沙彥珣奏，','按同日、同官、同桑迁围城核身份；昫珣非繁简转换，原字保、待纸本。',source='jiuwudaishi-048-936-july-revolts')
add('sha_breaks_siege','沙彦珣突围出西山，据雷公口',20,'彦昫犯围','据雷公口，',[('沙彦珣','突围者')],when='936年七月围城时；主未独日',place='西山、雷公口',note='犯围为突围情境，据雷公口非弃军逃出国境。')
add('sha_reenters_city','翌日沙彦珣收兵入城击乱兵，桑迁败走，军城复安',20,'明日，','军城复安。',[('沙彦珣','收兵击乱军者'),('桑迁','败走者')],when='936年七月突围翌日；旧补七月三日',place='云州',note='明日承突围，不能据奏表丁酉强换成戊戌发生；旧二夜三日回查。')
sup('sha_reenters_city',20,'jiuwudaishi-048-936-july-revolts','三日，招集兵士入城誅亂軍，軍城如故。','旧明确七月三日招兵入城诛乱军。','与奏表时序分别，三日不是丁酉翌日的干支算术。',relation='adds',field='time_original')
add('yin_captures_sang','是日尹晖执桑迁送洛阳',20,'是日，','执迁送洛阳，',[('尹晖','擒送者'),('桑迁','被擒送者')],when='936年七月平乱日条下；确干支未独载',place='云州、洛阳',note='是日可能连平乱日，主叙连奏报中，保相对称谓不强指丁酉或三日。')
add('sang_qian_executed','桑迁被送洛阳后遭斩',20,'尹晖执迁送洛阳，',None,[('桑迁','被斩者')],when='936年七月擒送洛阳后；斩日未独载',place='洛阳',note='斩之属后送达处置，不能以是日称一日云州擒拿、远送洛阳、行刑皆已完成。')
for name,n,quote in [('石重英',18,'秋，七月，戊子，获重殷、重裔，诛之，并族所匿之家。'),('石重裔',18,'秋，七月，戊子，获重殷、重裔，诛之，并族所匿之家。'),('石敬德',18,'寻捕得，死狱中，'),('石敬威',18,'从弟彰圣都指挥使敬威自杀。'),('桑迁',20,'是日，尹晖执迁送洛阳，斩之。')]:
 row=next(x for x in B['people'] if x['name']==name);assert row['key'] not in reused
 row['death_year']=936
 claim('person',row['key'],'death_year',name+'本年身亡。',n,quote,'按连续本年捕诛、死狱或自杀明确叙述定卒年，确日按事件主异文另记。')
reviews={13:'上表与答诏的政治指责归说话者，奏反、削爵、四面军任、定州平乱全收；乙巳丙午与旧乙卯丙辰官命差日保。杨光远沿杨檀已应用别名。',14:'后三万、待卫疑字原保。金全弟子不擅造师徒。代州/伏州、数百总五百、安重荣步骑/骑差异保；先是驻屯未知年，劝说预测归安。宋宁国宣州同府。',15:'治理背景和兵变分，癸丑与旧新壬子、削官庚申与旧辛酉并列；新走相州与主至洛阳作阶段。刘后沿李从珂后，求情≠同谋；权领非授节度。',16:'徐景迁以疾罢不是卒，弟景遂任参政吴官非即位；兄弟方向具体。',17:'受权任、暂受、移齐州、托词与史家等待判断、杀使和两军指挥任全收；杨光远副使属于太原不归魏博。主计事旧府事保异字。',18:'重殷与旧重英同官同重裔同藏井被诛沿一人；不混敬殷或新重胤。主戊子旧己丑、敬德死狱与旧奏诛并列。父子和弟/从弟原称保，未名妻女藏家不造。',19:'北还承前赴桂，无未载目的城或新战果。',20:'桑与沙两份奏内容分，不当尹确叛。沙名私用字对旧明确记名，昫珣异字保。丁酉奏表、二夜围三日平乱分，明日是日不盲算干支；擒送与斩日分。'}
contexts=[]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(13,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=280,year=936,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(13,21)],next_paragraph=Q[21]['id'],next_volume=280,next_year=936,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='连续第13—20段原18—25行：讨河东、转投、魏博变、吴换参政、两行营任命、石氏家属、楚归、云州桑沙奏变。后50段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(13,21)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
