# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 280, year 936 paragraphs 9–12."""
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
 specs.append((directory.name,directory,'51c8f3ea','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [('tongjian-280-936-opening',ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-01/sources/library/tongjian-280-936-opening','6a17b2b9','司马光等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-280-936-opening','tongjian-280-936-may-councils']
B = {'format_version': 1, 'batch_key': 'zztj-v280-y0936-p009-p012',
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
for n in range(9, 13):
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
        month = '四月条下及追叙' if n<=11 else '五月条下及追叙'
        citation = f'卷280·后唐清泰三年（936；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_280_0936_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_ALIASES={'马希杲':['馬希杲'],'裴仁照':[],'孙德威':['孫德威'],'华夫人（马希杲母）':['华夫人','華夫人'],'马希广':['馬希廣','德丕'],'赵莹':['趙瑩'],'薛融':[],'宋审虔':['宋審虔'],'桑维翰':['桑維翰'],'杨彦询':['楊彥詢']}
ALIASES['华夫人']='华夫人（马希杲母）'

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
    if when is None:when='936年'+('四月' if n<=11 else '五月')+'条下；确日未独载'
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
# Continuous text; reported motives and counsels stay attributed.
add('ma_xigao_good_government','主书称静江马希杲有善政',9,'静江节度使','有善政，',[('马希杲','静江节度使')],year=None,when='四月军情前附述；政绩始年未载',place='静江',note='政绩为史家概括，不添治理措施与始年。')
add('pei_accuses_xigao','裴仁照向马希范指称马希杲收众心，楚王生疑',9,'监军裴仁照','希范疑之。',[('裴仁照','进言者'),('马希杲','被指称者'),('马希范','闻言生疑者')],year=None,when='四月军情前背景；确日与始年未独载',place='楚',note='谮之是主史判断，收众心保裴指称，不作马希杲确已谋反。')
add('sun_dewei_invades_meng_gui','四月汉将孙德威进侵蒙、桂二州',9,'夏，四月，','蒙、桂二州，',[('孙德威','南汉进侵将领')],place='蒙州、桂州',note='汉为南汉，不当后汉；侵地保两州，不推已占领。')
add('ma_xiguang_deputizes','马希范命弟马希广权知军府事',9,'希范命其弟','权知军府事，',[('马希范','委任者'),('马希广','武安节度副使，临时领府者')],place='楚',note='权知非本年继位楚王。')
relationship('马希范','马希广','兄长',9,'希范命其弟武安节度副使希广','A是B兄长，主明其弟。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','马希范是马希广的同母兄长。',9,'希廣字德丕，希範同母弟也。','新楚世家补同母和表字，只取身份关系，不提前录947继位等后事。',source='xinwudaishi-066-xiguang-brother',relation='adds')
claim('person',people['马希广'],'aliases','马希广字德丕，繁体马名原作馬希廣。',9,'希廣字德丕，','沿同传身份，表字入别名，原文保繁体。',source='xinwudaishi-066-xiguang-brother')
add('ma_xifan_leads_five_thousand','马希范自将步骑五千赴桂州，马希杲惧',9,'自将步骑五千','希杲惧，',[('马希范','亲率步骑者'),('马希杲','感惧者')],place='桂州',note='原五千步骑合计，非五千骑；不推针对希杲已下捕杀命令。')
add('hua_meets_xifan','华夫人在全义岭迎马希范，请削封邑、洒扫夜庭以赎儿子之罪',9,'其母华夫人','以赎希杲罪。”',[('华夫人','迎谢请罪者'),('马希范','受迎听请者'),('马希杲','母为其请罪的对象')],place='全义岭',note='只是华夫人求赎之辞，未记王实际削邑或令洒扫；原夜庭不擅改掖庭。')
relationship('华夫人','马希杲','母亲',9,'其母华夫人逆希范于全义岭','原明母亲，未具本名，不合其他华氏。')
add('xifan_explains_visit','马希范对华夫人称闻马希杲治行优异，此来视察没有他意',9,'希范曰：','无它也。”',[('马希范','解释者'),('华夫人','听解释者')],place='全义岭',note='原对话解释保为他说法，与前疑虑并列，不消除史家先叙疑心。')
add('han_withdraws_meng','汉兵自蒙州引去',9,'汉兵自蒙州','引去，',[],place='蒙州',note='原未明退军决策者，孙德威不自动附参与；未记战果或因果。')
add('xigao_moves_lang','马希杲被调为知朗州',9,'徙希杲',None,[('马希杲','调知朗州者')],place='朗州',note='官命无另日，沿四月条，不推削静江节度全部头衔。')
add('gao_urges_xu_accession','高从诲遣使奉笺劝徐知诰即帝位',10,'高从诲',None,[('高从诲','遣使劝进者'),('徐知诰','受劝对象')],place='荆南、吴',note='劝进非已经即位；徐沿李昪，匿名使者不造人。')
add('shi_requests_transfer','追叙石敬瑭累次上表称羸疾，请解兵柄移他镇以试探帝意',11,'初，石敬瑭','移他镇。',[('石敬瑭','屡次上表试意者')],year=None,when='初，五月移镇之前追叙；各次上表年日未载',place='河东',note='底本赢疾疑羸疾原字保；称病为上表内容，不诊断确有病，也不把每次都定936。')
add('emperor_considers_yunzhou','李从珂与执政商议准石敬瑭请求移镇郓州',11,'帝与执政','移镇郓州。',[('帝','商议者'),('石敬瑭','拟调者')],year=None,when='初，正式五月诏命前商议；确年日未独载',place='郓州',note='只是拟从其请，不重复当已正式调任。')
sup('emperor_considers_yunzhou',11,'jiuwudaishi-048-936-may-background','翌日，欲移石敬瑭於鄆州，房暠等堅言不可，','旧末帝纪也记欲移郓州与房暠力阻。','旧将此连在帝夜问流言翌日，主隔段以初追叙，保相对时间，不算另一次任命。',relation='adds',field='time_original')
add('fang_li_lv_oppose_transfer','房暠、李崧、吕琦力谏移镇，帝久犹豫',11,'房暠、',None,[('房暠','力谏者'),('李崧','力谏者'),('吕琦','力谏者'),('帝','犹豫者')],year=None,when='初，正式五月诏命前；久之不具起日',note='三谏臣全收，久之不自行换算。')
add('xue_alone_advises','五月庚寅夜李崧请急在外，薛文遇独直，劝帝先图河东',12,'五月，庚寅夜，','不若先事图之。”',[('李崧','请急在外者'),('薛文遇','独直进言者'),('帝','听言者')],when='936年五月庚寅夜',note='李崧明确不在场，角色保请急在外；移亦反是薛判断不是已发生两次反叛。')
sup('xue_alone_advises',12,'jiuwudaishi-048-936-may-background','石敬瑭除亦叛，不除亦叛，不如先事圖之。','旧也记薛文遇以除亦叛不除亦叛劝先图。','旧此段未具庚寅，不作为独立确日依据。')
add('diviner_predicts_adviser','追叙术者称国家今年应得贤佐，帝以为指薛文遇',12,'先是，术者言','帝意文遇当之，',[('帝','把预测联系薛文遇者'),('薛文遇','被帝视作贤佐者')],year=None,when='先是，庚寅夜前占验；术者言今年，确起日未载',note='未名术者不造人，占验只是所言；未作国家确获贤佐历史事实。')
sup('diviner_predicts_adviser',12,'jiuwudaishi-048-936-may-background','先是，有人言國家明年合得一賢佐主謀，平定天下，帝意亦疑賢佐者屬在文遇，','旧叙有人言明年得贤佐，帝也联想到文遇。','主今年、旧明年不一致，两种原词并存，不据占验强定事件年份。',relation='conflicts',field='time_original')
add('congke_orders_draft_transfer','李从珂闻薛言大喜，决意调任，写除目交学士院草制',12,'闻其言，大喜，','使草制。',[('帝','决策、发草制命者'),('薛文遇','前述建议者')],when='936年五月庚寅夜条下',note='草制与翌日正式宣制分开，匿名学士不臆定马胤孙。')
sup('congke_orders_draft_transfer',12,'jiuwudaishi-048-936-may-background','即令手書除目，子夜下學士院草制。','旧补子夜下学士院草制。','同一命令加相对时刻，不添新一份诏书。',relation='adds',field='time_original')
add('shi_tianping_transfer','五月辛卯诏石敬瑭为天平节度使',12,'辛卯，以敬瑭','为天平节度使，',[('石敬瑭','获移镇诏者')],when='936年五月辛卯',place='天平军、郓州',note='命移镇与赴任分，后拒命不表示从未有诏。')
sup('shi_tianping_transfer',12,'jiuwudaishi-048-936-may-transfers','為鄆州節度使，進封趙國公。','旧同日称郓州节度使并补进封赵国公。','天平军与郓州为同军府城称，封爵为补充，非单凭地名新造任命。',relation='adds')
add('song_shenqian_hedong','同日宋审虔由马军都指挥使、河阳节度使任河东节度使',12,'以马军都指挥使','为河东节度使。',[('宋审虔','获任河东者')],when='936年五月辛卯',place='河东',note='主前职马军、旧称侍卫马步军保官衔异表述，不在主字段悄改。')
sup('song_shenqian_hedong',12,'jiuwudaishi-048-936-may-transfers','以河陽節度使、充侍衛馬步軍都指揮使宋審虔為河東節度使。','旧同官命，前职写侍卫马步军都指挥使。','主马军与旧马步军别记，仍沿同名同调任者。',relation='adds')
add('officials_alarm_transfer','宣制时两班听到石敬瑭名，相顾失色',12,'制出，','相顾失色。',[],when='936年五月辛卯宣制时',note='匿名两班不造人物，情绪表现不推全部官员反对诏令。')
sup('officials_alarm_transfer',12,'jiuwudaishi-048-936-may-background','翌日，宣制之際，兩班失色。','旧也记翌日宣制两班失色。','对照同情景，不把翌日独立换算新公历。')
add('zhang_jingda_northwest','五月甲午张敬达任西北蕃汉马步都部署，诏催石敬瑭赴郓州',12,'甲午，','趣敬瑭之郓州。',[('张敬达','获任部署者'),('石敬瑭','受催赴镇者')],when='936年五月甲午',place='西北、郓州',note='趣为催促，非张已经押送敬瑭上路；建雄节使底本简称保。')
sup('zhang_jingda_northwest',12,'jiuwudaishi-048-936-may-transfers','甲午，以前晉州節度使、大同彰國振武威塞等軍蕃漢副總管張敬達充西北面蕃漢馬步都部署，落副總管。','旧同日补此前副总管、此任落副总管。','张敬达沿既有人，建雄军晋州同府地名，不合张敬方。',relation='adds')
add('shi_discusses_response','石敬瑭向将佐诉前许终身不代，拟表称疾试意，宽则事帝、加兵则改图',12,'敬瑭疑惧，','我则改图耳。”',[('石敬瑭','诉疑、提出条件性方案者')],when='936年五月甲午催赴镇后；确日未载',place='河东',note='终身许诺为石自述，不凭本句增另一已证诏；我不兴乱朝廷发之也是辩辞，非编者确认。称疾尚拟表，与已上旧表分。')
add('duan_opposes','段希尧极言反对石敬瑭方案，石因其朴直未责',12,'幕僚段希尧','不责也。',[('段希尧','反对者'),('石敬瑭','未责者')],when='936年五月催赴镇后讨论；确日未载',note='拒之据上下文为反对拒命方案，不当段已拒朝廷诏。')
add('zhao_ying_urges_yunzhou','华阴节度判官赵莹劝石敬瑭赴郓州',12,'节度使判官华阴','赴郓州；',[('赵莹','劝赴任者'),('石敬瑭','被劝者')],when='936年五月将佐议后；确日未载',place='河东、郓州',note='华阴是籍贯不当谈话地点；并不等于劝说被采纳或赵已赴郓州。')
add('xue_rong_disclaims_military','平遥观察判官薛融称自己书生不习军旅',12,'观察判官平遥','不习军旅。”',[('薛融','自述者')],when='936年五月将佐讨论；确日未载',note='平遥籍贯，不与薛文遇混；不擅归他支持反叛或主和一方。')
add('liu_zhiyuan_urges_resistance','刘知远称河东形胜士马强，劝石敬瑭称兵传檄而不要赴任',12,'都押牙刘知远','自投虎口乎！”',[('刘知远','主张称兵者'),('石敬瑭','听建议者')],when='936年五月将佐讨论；确日未载',place='河东',note='帝业可成是预测，不当已经称帝或已经发布檄书；都押牙沿主职。')
add('sang_weihan_urges_khitan','桑维翰以明宗遗爱、石为爱婿及契丹近云应，劝屈节事契丹求援',12,'掌书记洛阳桑维翰','何患无成。”',[('桑维翰','主张自全、求援者'),('石敬瑭','听建议者')],when='936年五月将佐讨论；确日未载',place='河东',note='天意、庶孽群情不附、朝呼夕至均桑的论说，不作中立判定。洛阳是籍贯，尚未实际召援；前已兄弟盟约不当亲兄弟。')
add('shi_resolves','听诸议后石敬瑭意决',12,'敬瑭意遂决。',None,[('石敬瑭','下决定者')],when='936年五月将佐讨论后；确日未载',note='只记意决，起兵与上表由后续段分别处理。')
add('yang_yanxun_monitor_post','追叙朝廷因疑石敬瑭，任宝鼎羽林将军杨彦询为北京副留守',12,'先是，朝廷疑敬瑭，','为北京副留守，',[('杨彦询','获任副留守者')],year=None,when='先是，石将举事之前；任命确年日未载',place='北京（太原）',note='北京为后唐北都太原，非现代北京；宝鼎籍贯不作任所。')
add('shi_tells_yang_plan','石敬瑭将举事，告情杨彦询；杨询河东兵粮能否敌朝廷',12,'敬瑭将举事，','能敌朝廷乎？”',[('石敬瑭','告情者'),('杨彦询','询问兵粮实力者')],when='936年五月将举事时；确日未载',place='河东',note='未附兵粮实际数量，杨疑问不推已通报朝廷。')
add('shi_protects_yang','左右请杀杨彦询，石敬瑭表示亲保，制止再言',12,'左右请杀彦询，',None,[('杨彦询','被请杀、获保护者'),('石敬瑭','拒绝杀议者')],when='936年五月告情后；确日未载',note='匿名左右不归刘桑；请杀非已杀，明确保之不填此年死亡。')
reviews={9:'裴收众心为指称，马善政常态不硬定936。汉南汉侵蒙桂、楚五千步骑、希广权知、母华请赎、王解释、汉退、马徙分。夜庭原字保，未称已削邑；马希杲≠希萼，同母兄弟由新楚补。',10:'高遣使劝进不等于徐本年即位，沿李昪无名使不造。',11:'初屡表和拟移、力谏未具年不强定936，与五月正式任命分。赢疾疑羸疾保原字；帝与执政拟从不是已执行。',12:'庚寅夜、辛卯宣制、甲午任官催行分，独直与李请急角色不作在场。主今年旧明年占验异文并列；群情天意等归说话者。赵莹≠赵延乂，薛融≠薛文遇；主北京太原。匿名术者、将佐左右不臆定，杀议被拒非死亡。'}
contexts=[]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=280,year=936,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,13)],next_paragraph=Q[13]['id'],next_volume=280,next_year=936,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='连续第9—12段原14—17行：楚汉边政、吴劝进、石敬瑭移镇及朝野两方讨论；剩58段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,13)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
