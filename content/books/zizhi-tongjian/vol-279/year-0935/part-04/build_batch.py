# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 935 paragraphs 29–37."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,38))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'dcde85d9','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [
 ('tongjian-279-935-jinzhou-min',YEAR/'part-03/sources/library/tongjian-279-935-jinzhou-min','53d64599','司马光等'),
 ('xinwudaishi-068-chunyan-request',YEAR/'part-03/sources/library/xinwudaishi-068-chunyan-request','53d64599','欧阳修'),
 ('jiuwudaishi-090-ma-quanjie',YEAR/'part-03/sources/library/jiuwudaishi-090-ma-quanjie','53d64599','薛居正等'),
 ('xinwudaishi-061-935-tianzuo',YEAR/'part-03/sources/library/xinwudaishi-061-935-tianzuo','53d64599','欧阳修'),
 ('xinwudaishi-068-chen-jinfeng',YEAR/'part-01/sources/library/xinwudaishi-068-chen-jinfeng','104a22bf','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-935-jinzhou-min','tongjian-279-935-min-november','tongjian-279-935-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0935-p029-p037',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'xinwudaishi-055-sikong-duties':'卷55·马胤孙传（司空职掌议论）','songshi-483-sun-guangxian':'卷483·孙光宪传','xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
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
lines = (ROOT / 'resources/derived/tongjian/279.txt').read_text().splitlines()
for n in range(29, 38):
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
for name,extra in [('王继鹏',['王昶']),('刘岩之女（王延钧妻）',['清远公主','清遠公主'])]:
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
    labels={'xinwudaishi-055-sikong-duties':'卷55·马胤孙传（司空职掌议论）','songshi-483-sun-guangxian':'卷483·孙光宪传','xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '十月条下及追叙、史评' if n<=32 else '十一月条下及追叙' if n<=34 else '十二月条下及年末总述'
        citation = f'卷279·清泰二年（935；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0935_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','吴主':'杨溥','徐知诰':'李昪','闽主':'王延钧','陈后':'陈金凤','汉主':'刘岩','昶':'王继鹏','继鹏':'王继鹏','继韬':'王继韬','清远公主':'刘岩之女（王延钧妻）','敏':'李敏（闽臣）','李亻放':'李仿','希范':'马希范'}
NEW_ALIASES={'归守明':['歸守明','归郎','歸郎'],'李可殷':[],'李仿':['李倣','李亻放'],'王继韬':['王繼韜'],'林延遇':[],'林延皓':['林延皓（闽）'],'王继严':['王繼嚴'],'叶翘':['葉翹'],'李氏（王继鹏元妃）':['梁国夫人李氏','梁國夫人李氏']}

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

def event(code, title, n, quote, actors, when=None, note='', year=935, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='935年'+('十月' if n<=32 else '十一月' if n<=34 else '十二月')+'条下；确日未独载'
    key = 'event_zztj_279_0935_' + code
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
        edge = 'participation_zztj_279_0935_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_279_0935_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
add('min_chen_affairs_background','追述陈皇后与归守明、李可殷私通的史述',29,'初，闽主','莫敢言。',[('陈后','被记与近臣私通者'),('归守明','闽主幸臣、被记私通者'),('李可殷','百工院使、被记私通者')],year=None,when='十月政变前所附往事；开始年份未载',place='闽',note='主叙国人皆恶为概括，不当所有人心理独证；病名保风疾不作现代诊断。')
sup('min_chen_affairs_background',29,'xinwudaishi-068-chen-jinfeng','初，鏻有嬖吏歸守明者，以色見倖，號歸郎，鏻後得風疾，陳氏與歸郎奸。','新闽世家也记归守明号归郎、陈氏与其私通。','归郎沿归守明，新原字保；背景始年未载，不算本年才开始。')
claim('person',people['归守明'],'aliases','归守明号归郎。',29,'初，鏻有嬖吏歸守明者，以色見倖，號歸郎，','新明确别号，不把归郎另建人物。',source='xinwudaishi-068-chen-jinfeng')
add('min_resentments_background','追述李可殷谮李仿、陈匡胜无礼于王继鹏，使二人怨恨',29,'可殷尝谮','皆恨之。',[('李可殷','被记进谗者'),('李仿','皇城使、被谮者'),('陈匡胜','陈后族人、被记对福王无礼者'),('继鹏','被记怨恨者')],year=None,when='十月政变前所附往事；尝字未具年',place='闽',note='谮、无礼、恨均主书叙述，不编具体言词或把怨恨当实施政变的唯一已证原因。')
add('min_illness_and_fang_prediction','闽主病重，李仿以为其不能痊愈',29,'闽主疾甚，','必不起，',[('闽主','被记病重者'),('继鹏','被记有喜色者'),('李仿','预测闽主不能病愈者')],when='935年十月己卯之前；病重起日未载',place='闽',note='必不起是李仿判断，不能作实际已死或现代医学结论。')
add('li_fang_kills_li_keyin','十月己卯李仿遣壮士击杀李可殷',29,'冬，十月，己卯，','中外震惊。',[('李仿','派壮士者'),('李可殷','被击杀者')],when='935年十月己卯',place='闽',note='壮士未名不造人物，持白梃为原器具；新明确在家，主未载具体地点。')
sup('li_fang_kills_li_keyin',29,'xinwudaishi-068-chunyan-request','乃令壯士先殺李可殷于家。','新闽世家也记李倣命壮士先杀李可殷于家。','同官职及下一日行动核李倣与李仿；新未干支日，不借主日当独立日证。')
add('min_ruler_questions_li_keyin_death','十月庚辰闽主病稍好转，陈后诉事，闽主视朝询问李可殷死因',29,'庚辰，','仿惧而出，',[('闽主','视朝诘问者'),('陈后','诉告者'),('李仿','被问后出者')],when='935年十月庚辰',place='闽')
add('li_fang_troops_enter_palace','李仿退出朝廷后率部兵鼓噪入宫',29,'俄顷，','入宫。',[('李仿','率兵入宫者')],when='935年十月庚辰',place='闽宫',note='主此句仅明李仿率兵，新另明与继鹏同行，作为补证不擅改主行动主体。')
sup('li_fang_troops_enter_palace',29,'xinwudaishi-068-chunyan-request','倣懼而出，與繼鵬率皇城衞士而入。','新闽世家记李倣退出后与王继鹏率皇城卫士入宫。','补主省略王继鹏同行的信息；保不同书叙述层次。')
add('min_ruler_stabbed_and_killed','闽主藏于九龙帐下被乱兵刺伤，随后由未名宫人结束其生命',29,'闽主闻变，','为绝之。',[('闽主','遇害者')],when='935年十月庚辰',place='九龙帐下',note='主先刺未绝后宫人为绝，两阶段合记终局但不归全为李仿亲手；未名宫人不造实名或臆测身份。')
sup('min_ruler_stabbed_and_killed',29,'xinwudaishi-068-chunyan-request','衞士刺之不殂，宮人不忍其苦，為絕之。','新闽世家同记卫士刺未死、宫人后绝之。','两书记载死亡过程互核，非现代医学诊断。')
claim('person',people['王延钧'],'death_year','王延钧于935年十月政变中遇害。',29,span(29,'闽主闻变，','为绝之。'),'死亡明示，纪日沿主书庚辰，摘录过程保持原字。')
add('li_fang_jipeng_kill_chen_and_others','李仿与王继鹏杀陈皇后、陈守恩、陈匡胜、归守明及王继韬',29,'仿与继鹏杀','相恶故也。',[('李仿','主书列为杀害者'),('继鹏','主书列为杀害者'),('陈后','遇害者'),('陈守恩','遇害者'),('陈匡胜','遇害者'),('归守明','遇害者'),('继韬','继鹏弟、遇害者')],when='935年十月庚辰政变条下',place='闽',note='同日条下叙，不能编具体杀害地点或每人亲手凶手；新归倣所杀，与主二人合列分别保。')
sup('li_fang_jipeng_kill_chen_and_others',29,'xinwudaishi-068-chunyan-request','繼韜及陳后、歸郎皆為倣所殺。','新闽世家明确将王继韬、陈后、归郎之死归于李倣。','主仿与继鹏合列、新归倣，归责层次差别；不由新未列陈守恩陈匡胜推二人未死。',relation='adds')
relationship('继鹏','继韬','兄长',29,'仿与继鹏杀陈后、陈守恩、陈匡胜、归守明及继鹏弟继韬；','主明确弟，A是B兄长，不建重复反向边。')
add('wang_jipeng_regency_and_accession','十月辛巳王继鹏称皇太后令监国，并于当天即皇帝位',29,'辛巳，','即皇帝位。',[('继鹏','监国、即位者')],when='935年十月辛巳',place='闽',note='称太后令为王继鹏所称，不确认未名太后亲自发令或臆造太后姓名。')
add('wang_jipeng_changes_name_chang','王继鹏即位后更名昶',29,'更名昶。','更名昶。',[('继鹏','更名者')],when='935年十月辛巳即位条下',place='闽',note='王昶沿王继鹏稳定UUID，与蜀孟昶不同人；既有名字保留并补别名。')
claim('person',people['王继鹏'],'aliases','王继鹏即位后更名昶，可称王昶。',29,'是日，即皇帝位。更名昶。','稳定主体不新建王昶，原名保检索。')
sup('wang_jipeng_changes_name_chang',29,'xinwudaishi-068-jipeng-name','繼鵬，鏻長子也。既立，更名昶，','新闽世家也记王继鹏即位后更名昶。','新紧接改元通文为压缩叙法，不借其文字把主后续936改元提前。')
relationship('闽主','继鹏','父亲',29,'谥其父曰齐肃明孝皇帝，庙号惠宗。','其父承上王继鹏，受谥者为前文遇害王延钧；复用已有父子方向边。')
add('jipeng_honors_yanjun_posthumously','王继鹏谥父为齐肃明孝皇帝、庙号惠宗',29,'谥其父','庙号惠宗。',[('继鹏','上谥庙号者'),('闽主','受谥及庙号者')],when='935年十月辛巳即位条下；典礼确日未另载',place='闽',note='主惠宗、新太宗异说保，不校覆盖；庙号不当在位名。')
sup('jipeng_honors_yanjun_posthumously',29,'xinwudaishi-068-chunyan-request','鏻立十年見殺，謚曰惠皇帝，廟號太宗。','新闽世家记王鏻谥惠皇帝、庙号太宗。','与主齐肃明孝皇帝、惠宗不同，电子两本异说并列，待纸本核。',relation='conflicts')
add('jipeng_petitions_tang_and_amnesty','王继鹏自称权知福建节度事，遣使奉表后唐，并大赦境内',29,'既而自称','大赦境内；',[('继鹏','自称节度事、遣表和赦令主体')],when='935年十月即位之后；确日未载',place='闽、后唐',note='自称不等于后唐已经正式册封；奉表与已获批准分。')
add('jipeng_makes_chunyan_consort','王继鹏立李春燕为贤妃',29,'立李春燕','为贤妃。',[('继鹏','立妃者'),('李春燕','获立贤妃者')],when='935年十月即位之后；确日未载',place='闽',note='贤妃与新后文淑妃皇后是不同阶段，不提前写当前为皇后。')
relationship('李春燕','继鹏','妻子',29,'立李春燕为贤妃。','妃属于后妃婚姻身份，A是B妻子；本条为贤妃非皇后，保所授位。')
E['min_marriage']=event('min_qingyuan_marriage_background','追述王延钧娶汉主女清远公主',29,'初，闽惠宗娶汉主女清远公主，',[('闽主','娶公主者'),('清远公主','汉主女、王延钧妻')],when='本段追叙婚事；复用已发布917年婚姻事件',year=None,place='闽',note='与917主越主刘岩之女嫁同一王延钧婚事核同主体；当前不是935新婚。不与主两娶刘氏中的另一刘氏或新金氏无证合并。',stable_key='event_zztj_270_0917_wang_yanjun_marries_liu_yan_daughter')
claim('person',people['刘岩之女（王延钧妻）'],'aliases','汉主女、王延钧妻在本段称清远公主。',29,'初，闽惠宗娶汉主女清远公主，','与917汉主刘岩女嫁王延钧核同对象，规范名及UUID保留，清远仅补别名。')
relationship('汉主','清远公主','父亲',29,'初，闽惠宗娶汉主女清远公主，','汉主沿刘岩，复用917已发布父女边；未擅定生母。')
relationship('清远公主','闽主','妻子',29,'初，闽惠宗娶汉主女清远公主，','复用既有妻子方向，婚事917已记，不把当前追叙当新婚。')
add('lin_yanyu_mission_background','追述王延钧派宦者林延遇在番禺置邸掌国信',29,'使宦者闽清','专掌国信。',[('闽主','派遣者'),('林延遇','闽清宦者、国信事务受命者')],year=None,when='本段所附往事；置邸派遣年份未载',place='番禺',note='闽清为史载地籍；婚事有917前证不能自动将置邸同定917。')
add('han_ruler_questions_lin_background','汉主赐林延遇宅第、优厚给赐并多次问闽事，林不回答',29,'汉主赐以','延遇不对，',[('汉主','赐宅给赐及询问者'),('林延遇','未回答闽事者')],year=None,when='置邸后的多次交往；具体年份未载',place='南汉',note='数问为概括不统计次数，不把问事当林已泄密。')
add('lin_explains_confidentiality_background','林延遇向人说明不应在别国宫禁谈论原国事务',29,'退，谓人曰：','可如是乎！”',[('林延遇','阐明守密意见者')],year=None,when='置邸交往中的言论；年份未载',place='南汉',note='退后向人说，听者匿名；去闽语闽、去越语越按原句保，不推所有外交政策。')
add('han_appoints_lin_inner_attendant_background','汉主闻林延遇言论，任其为内常侍，令核诸司事',29,'汉主闻而贤之，','使钩校诸司事。',[('汉主','任命与委派者'),('林延遇','内常侍、核诸司事受命者')],year=None,when='置邸交往之后；任官年份未载',place='南汉')
add('lin_requests_return_mourns_min_ruler','林延遇闻闽惠宗遇害，请归未获准，素服向闽哭三日',29,'延遇闻惠宗',None,[('林延遇','请归及向闽哭者')],when='935年十月闽主遇害之后；闻讯日未载',place='南汉',note='不许是拒请结果，原句未明下令人不硬造刘岩拒令参与；三日为哭持续日数，不换日期。')
add('gao_respects_liang_background','主书叙高从诲礼贤委梁震，以兄礼待之',30,'荆南节度使','震常谓从诲为郎君。',[('高从诲','委任并尊敬梁震者'),('梁震','受委任者、称高为郎君者')],year=None,when='本段所附长期交往；起始年未载',place='荆南',note='以兄事是尊敬，不建亲兄弟、结义或生父关系；郎君非梁之子。')
add('gao_admires_ma_xifan_luxury','高从诲听人夸楚王马希范盛况，向僚佐表示羡慕',30,'楚王希范','可谓大丈夫矣。”',[('高从诲','对僚佐谈论者')],when='935年十月条下所附谈话；确年月未载',year=None,place='荆南',note='马为被谈论者，未在场，不添其参加谈话边；奢靡为主史评。')
add('sun_advises_gao_against_luxury','孙光宪劝高从诲勿羡马希范奢侈僭越',30,'孙光宪对曰：','又足慕乎！”',[('孙光宪','进谏者'),('高从诲','受谏者')],when='本段附载谈话；确年月未载',year=None,place='荆南',note='危亡无日为孙警告，不是主已记录楚国在935灭亡；乳臭子为孙评价，展示不据此推年龄。')
claim('person',people['孙光宪'],'description','孙光宪字孟文，陵州贵平人。',30,'孫光憲字孟文，陵州貴平人。','宋卷483传首明确，原EPUB分段核孙传，不把籍贯填出生坐标。',source='songshi-483-sun-guangxian')
add('gao_accepts_advice_reduces_extravagance','高从诲久后认可劝谏，向梁震自省，弃玩好、读经史、省刑薄赋',30,'从诲久而悟，','境内以安。',[('高从诲','接受意见、自省及施政者'),('梁震','听高自省者')],when='前述劝谏久后、它日；确年月未载',year=None,place='荆南',note='久与它日不强定本年十月；境内以安是主概括效果，不给精确治安指标。')
add('liang_requests_retirement','梁震称高从诲已能自立，表示年老不再事人，坚请退居',30,'梁震曰：','遂固请退居。',[('梁震','请退者'),('高从诲','请退对象')],year=None,when='前述政事之后；请退确年月未载',place='荆南',note='先王属嗣王是梁所述前事，不造本年高季兴托孤事件。')
add('gao_builds_liang_home','高从诲留梁震不成，为他在士洲筑室',30,'从诲不能留，','筑室于士洲。',[('高从诲','筑室者'),('梁震','退居受室者')],when='请退之后；确年月未载',year=None,place='士洲',note='史载地名不硬改龙山或填现代坐标。')
add('liang_retires_calls_himself_hermit','梁震退居自称荆台隐士，来府常骑黄牛',30,'震披鹤氅，','至听事。',[('梁震','自称隐士并访府者')],year=None,when='退居后常态；确年月未载',place='荆南')
add('gao_visits_supports_liang','高从诲时访梁震家，四时厚赐',30,'从诲时过其家，','四时赐与甚厚。',[('高从诲','访家赐与者'),('梁震','受访受赐者')],year=None,when='梁退居后常态；年份未载',place='荆南')
add('gao_entrusts_sun_government','梁震退居后高从诲将政事交孙光宪',30,'自是悉以',None,[('高从诲','委政者'),('孙光宪','受委者')],year=None,when='梁震退居之后；确年月未载',place='荆南',note='悉为主概括，不创永久统属关系。')
add('sima_guang_comment_jingnan','司马光评论孙光宪能谏、高从诲能改、梁震能退',31,'臣光曰：',None,[],when='《资治通鉴》编纂时的史家评论；非935年在场言论',year=None,place='史评',note='完整保存臣光曰评论段，不当935政治事件发生日，不造宋作者在五代与三人会谈参与边；亡国反问属评价非事件结果。')
add('wu_grants_qi_state_titles','吴授徐知诰尚父、太师、大丞相、大元帅，封齐王，以十州为齐国',32,'吴加中书令','十州为齐国；',[('吴主','吴君、加衔封国主体'),('徐知诰','获加衔与封齐国者')],when='935年十月条下；确日未载',place='升、润、宣、池、歙、常、江、饶、信、海十州',note='吴国内封齐国，不当937南唐已建立；十州全保，升与润不互换。')
sup('wu_grants_qi_state_titles',32,'xinwudaishi-061-935-tianzuo','知誥進位太師、天下兵馬大元帥，封齊王。','新吴世家将徐知诰进太师、大元帅封齐王接在七年九月条。','主十月条下、新九月邻接层次有别，新三年建齐国还在后文，封爵与完整建国礼不混作一步。',relation='conflicts',field='time_original')
add('xu_declines_shangfu_chancellor_rites','徐知诰辞尚父、丞相，不受殊礼',32,'知诰辞',None,[('徐知诰','辞部分衔及殊礼者')],when='935年十月授衔后；确日未载',place='吴',note='辞的是尚父丞相殊礼，不说所有衔与齐王皆已拒。')
add('li_fang_controls_power_wang_plots','主书叙李仿专权养死士，王继鹏与林延皓等谋除之',33,'闽皇城使','等图之。',[('李仿','皇城使判六军诸卫、被谋除者'),('昶','闽主、谋除者'),('林延皓','拱宸指挥使、参与谋除者')],when='935年十一月壬子之前；确日未载',place='闽',note='李亻放为电子拆字，核与前李仿及新李倣同皇城使；林延皓非唐刘延皓。专制、阴养为主史述。')
add('lin_yanhao_feigns_alignment','林延皓等假意亲附李仿，使其未疑',33,'延皓等诈','待之不疑。',[('林延皓','诈亲附者'),('李仿','被记未疑者')],when='935年十一月壬子之前；确日未载',place='闽',note='等未名不猜完整名单，不造真实盟友关系。')
add('lin_yanhao_captures_kills_fang','十一月壬子林延皓等在内殿伏数百卫士，擒斩李仿，枭首朝门',33,'十一月，壬子，','枭首朝门。',[('林延皓','伏兵及擒斩者'),('李仿','入朝遇害者')],when='935年十一月壬子',place='闽内殿、朝门',note='卫士数百为概数不造精确人数；主朝门、新市，位置异说保。')
sup('lin_yanhao_captures_kills_fang',33,'xinwudaishi-068-li-fang-killed','昶患之，因大享軍，伏甲擒倣殺之，梟其首于市。','新闽世家记昶因大享军伏甲杀李倣，枭首于市。','主入朝林伏内殿、新大享军枭市，同事件保不同叙法；新未壬子日，不称独立确日。',relation='adds')
add('fang_troops_attack_burn_escape','李仿部兵千余攻应天门不克，焚启圣门，夺首奔吴越',33,'亻放部兵','奔吴越。',[],when='935年十一月壬子杀李仿之后',place='应天门、启圣门、吴越',note='死后的李仿本人未指挥此次，不给亡者行动参与边；千余为部兵数不是全部吴越军。')
sup('fang_troops_attack_burn_escape',33,'xinwudaishi-068-li-fang-killed','倣部曲千人叛，燒啟聖門，奪倣首，奔於錢塘。','新闽世家同记李倣部曲烧启圣门、夺首奔钱塘。','主千余、新千人保各量词；钱塘为吴越方向具体地，不把主说成明确抵某现代城区。')
add('min_proclaims_fang_crimes','闽朝廷下诏宣布李仿弑君、杀王继韬等罪告谕内外',33,'诏暴','告谕中外。',[('李仿','诏中归罪对象'),('昶','闽主、发布诏令主体')],when='935年十一月杀李仿之后；独立诏日未载',place='闽',note='诏书归罪与先前实际行动的史述分开；不以宣罪洗去主先前继鹏合杀记载。')
add('wang_jiyan_ye_qiao_appointments','闽以王继严权判六军诸卫、叶翘任内宣徽使参政事',33,'以建王','参政事。',[('王继严','建王、权判六军诸卫获任者'),('叶翘','永泰人、原六军判官、内宣徽使参政事获任者'),('昶','闽主、任官主体')],when='935年十一月条下；确日未另载',place='闽',note='权判为暂掌，不补具体亲属；王继严非继韬。')
add('ye_qiao_tutor_background','追述王延钧擢叶翘为福王友，王继鹏尊为师傅，宫称国翁',33,'翘博学','“国翁”。',[('闽主','擢福王友者'),('叶翘','福王友及受师礼者'),('昶','福王时以师礼待之者')],year=None,when='继位前福王时期追叙；任官起年未载',place='闽',note='师傅是辅导身份，国翁为宫中敬称，不造王继鹏与叶父子。')
add('wang_neglects_ye_qiao_consultation','王继鹏继位后不与叶翘讨论国事',33,'昶既嗣位，','不与翘议国事。',[('昶','被记不与叶议事者'),('叶翘','被记不受咨询者')],when='935年十月继位后；具体起日未载',place='闽',note='骄纵为史评，不从本句推全部政策失败。')
add('ye_requests_retirement_wang_retains','叶翘穿道士服趋出求退，王继鹏召回拜谢，厚赐慰留复位',33,'一旦，','令复位。',[('叶翘','求退者'),('昶','召还、自责与慰留者')],when='王继鹏继位后一旦；确年月未载',year=None,place='闽',note='叶称即位无一善为谏语，非客观统计；复位是慰留不是叶已去世复活。')
add('wang_favors_chunyan_neglects_first_consort','主书叙王继鹏宠李春燕，薄待元妃梁国夫人李氏',33,'昶元妃','待夫人甚薄。',[('昶','被记偏宠薄待者'),('李春燕','被宠者'),('李氏（王继鹏元妃）','梁国夫人、被薄待者')],year=None,when='继位后所附后妃背景；具体起始年月未载',place='闽',note='元妃与贤妃分人，李氏姓名未明不猜；敏为已建闽臣李敏，非唐昭宗李敏。')
relationship('敏','李氏（王继鹏元妃）','父亲',33,'昶元妃梁国夫人李氏，同平章事敏之女，','明示女，敏补李姓据李氏及既有闽臣李敏身份；A是B父亲。')
relationship('李氏（王继鹏元妃）','昶','妻子',33,'昶元妃梁国夫人李氏，同平章事敏之女，','元妃是婚姻身份，保梁国夫人位，不说她已为皇后；只存一个方向。')
add('ye_qiao_remonstrates_for_li_consort','叶翘以元妃为先帝之甥、礼聘之妻劝王继鹏勿弃新爱，王不悦而疏远叶',33,'翘谏曰：','由是疏之。',[('叶翘','谏者'),('昶','被谏及疏远者')],year=None,when='元妃受薄待后的进谏；确年月未载',place='闽',note='先帝之甥保历史称谓及女眷语境，具体母系中间人未载，暂不造确定舅甥亲等边。')
claim('person',people['李氏（王继鹏元妃）'],'description','叶翘在谏语中称梁国夫人李氏为先帝之甥，且曾礼聘。',33,'夫人先帝之甥，聘之以礼，','先帝承闽惠宗王延钧，甥称谓保而不凭一语确定中间母系人物。')
add('ye_qiao_exiled_home_after_petition','叶翘再上书言事，王继鹏批一叶随风落御沟，放他归永泰',33,'未几，','遂放归永泰，',[('叶翘','上书后放归者'),('昶','批纸并放归者')],year=None,when='上次进谏未几之后；确年月未载',place='永泰',note='未几不定935十二月；批语为王语不是叶纸内容本身。')
add('ye_qiao_later_death','主书末附叶翘寿终',33,'以寿终。','以寿终。',[('叶翘','后来寿终者')],year=None,when='归永泰之后；卒年未载',place='永泰',note='不能因附935年条就填935卒年或具体寿数。')
add('congke_summons_ma_quanjie_reward','李从珂嘉奖马全节守金州功，召入朝廷',34,'帝嘉','召诣阙。',[('帝','嘉功召见者'),('马全节','受召者')],when='935年十一月乙卯任命之前；召日未载')
add('liu_yanlang_seeks_ma_bribe_jiangzhou','刘延朗向马全节索贿未得，想授绛州刺史，引起众议',34,'刘延朗求赂，','群议沸腾。',[('刘延朗','索贿及拟授绛州者'),('马全节','无以行贿者')],when='935年十一月乙卯任命之前；确日未载',note='欲除是拟任，不说马已到绛州为刺史；群议未名不擅加具体大臣。')
sup('liu_yanlang_seeks_ma_bribe_jiangzhou',34,'jiuwudaishi-090-ma-quanjie','時劉延朗為樞密副使，邀其厚賄，全節無以賂之，','旧马全节传也记刘延朗索厚贿、马全节无以给贿。','旧本传正文为独立书证；旧帝纪引通鉴附注不重复算独证。')
sup('liu_yanlang_seeks_ma_bribe_jiangzhou',34,'jiuwudaishi-090-ma-quanjie','皇子重美為河南尹，聞而奏焉。','旧马传补皇子李重美任河南尹，闻众议后奏帝。','补帝闻之的信息来源，未借乙卯给这奏报定日。',relation='adds')
add('ma_quanjie_henghai_regent','十一月乙卯李从珂闻众议，任马全节横海留后',34,'帝闻之，',None,[('帝','任命者'),('马全节','横海留后获任者')],when='935年十一月乙卯',place='横海军',note='横海军与旧沧州是军号地镇层次；留后不称正式节度旌节已授。')
sup('ma_quanjie_henghai_regent',34,'jiuwudaishi-047-935-november','乙卯，以前金州防禦使馬全節為滄州留後。','旧末帝纪十一月乙卯记马全节为沧州留后。','只引旧正文命，不把后附通鉴索贿文字当独立补证。')
add('han_zhaoyin_huguo','十二月壬申韩昭胤带同平章事出任护国节度使',35,'十二月，',None,[('韩昭胤','由枢密宰辅出任护国节度使者'),('帝','任命者')],when='935年十二月壬申',place='护国军',note='旧韩昭裔沿已核异名，主护国军旧河中地镇一致；主原职原字保。')
sup('han_zhaoyin_huguo',35,'jiuwudaishi-047-935-december','壬申，以中書侍郎兼兵部尚書、充樞密使韓昭裔為檢校司空、同平章事，充河中節度使。','旧末帝纪同记壬申韩昭裔任河中节度使，并记检校司空衔。','主护国旧河中同镇军地，检校司空非冯道正拜司空，二人两官不混。')
add('feng_dao_sikong_935','主书十二月乙酉冯道由前匡国节度使任司空',36,'乙酉，','冯道为司空。',[('冯道','司空获任者'),('帝','任命者')],when='935年十二月乙酉；旧帝纪同官命记己丑',note='主乙酉旧己丑日期不同，保两说，不擅校或造两次任命。')
sup('feng_dao_sikong_935',36,'jiuwudaishi-047-935-december','己丑，以前同州節度使馮道為司空，','旧末帝纪把冯道任司空记在十二月己丑。','同州是匡国军地镇；同人官命主乙酉、旧己丑，明确异说不涂改。',relation='conflicts',field='time_original')
add('lu_proposes_sikong_ritual_sweeping','因久无正拜三公，朝议司空职掌，卢文纪拟令冯道掌祭祀扫除',36,'时久无','欲令掌祭祀扫除，',[('卢文纪','拟定职掌者'),('冯道','职掌被议的司空')],when='冯道任司空后；议事确日未载',note='欲令为方案不是冯已长期执行；不从久无改写历史所有司空皆无职掌。')
sup('lu_proposes_sikong_ritual_sweeping',36,'xinwudaishi-055-sikong-duties','而宰相盧文紀獨以謂司空之職，祭祀掃除而已。','新马胤孙传也记卢文纪主张司空职为祭祀扫除。','卷55段首胤孙承马胤孙传，不能将电子卷题直接当冯道传；新还记马未决与班位争，当前不扩无关争论。')
add('feng_dao_accepts_sweeping','冯道表示司空扫除属职，自己无所惧',36,'道闻之曰：','吾何惮焉。”',[('冯道','回应职掌方案者')],when='任司空后职掌争议中；确日未载',note='言论不表示扫除已执行或自愿辞官。')
add('lu_abandons_sikong_proposal','卢文纪后来认为方案不妥，停止令司空掌祭祀扫除',36,'既而文纪',None,[('卢文纪','停止方案者')],when='职掌议论之后；确日未载')
add('min_chen_shouyuan_tianshi','闽主赐陈守元天师号并信重之',37,'闽主赐','信重之，',[('昶','闽主、赐号者'),('陈守元','洞真先生、获赐天师号者')],when='935年末条所记；确月日未载',place='闽',note='闽主在十月已继位王昶，非已死王延钧；洞真称号沿已有陈守元。')
sup('min_chen_shouyuan_tianshi',37,'xinwudaishi-068-chen-shouyuan','又拜陳守元為天師，','新闽世家昶事中也记拜陈守元为天师。','只取同人同号，不把段后三年暴行、李春燕淑妃皇后提前到本年。')
add('min_consults_chen_shouyuan','主书称闽主在将相更易、刑罚、选举等事均与陈守元商议',37,'乃至更易','皆与之议；',[('昶','向陈议政者'),('陈守元','议政者')],year=None,when='赐天师后常态概述；起止年月未载',place='闽',note='皆是主概括，未列全部案件，不造具体官员任免和永久统属。')
add('chen_shouyuan_bribery_petitions','主书称陈守元受贿为人请托，往来门庭者多',37,'守元受赂',None,[('陈守元','被记受贿请托者')],year=None,when='获信任后常态；案件及起止年月未载',place='闽',note='其门如市为比喻，不定位市集；言无不从为概括，未具名请托人不造名单。')
for name in ['李可殷','李仿','归守明','王继韬']:
 row=next(x for x in B['people'] if x['name']==name);assert row['key'] not in reused;row['death_year']=935
 n=33 if name=='李仿' else 29
 quote=span(n,'十一月，壬子，','枭首朝门。') if n==33 else span(29,'冬，十月，己卯，','中外震惊。') if name=='李可殷' else span(29,'仿与继鹏杀','相恶故也。')
 claim('person',row['key'],'death_year',name+'于935年遇害。',n,quote,'本年卒事明确；具体日沿主书条次，原文可回查，不编未名凶手。')
reviews={29:'初背景与十月己卯杀可殷、庚辰闽主遇害并杀陈等、辛巳监国即位分。李仿/倣/亻放同皇城使，归郎沿守明。主惠宗齐肃明孝、新太宗惠皇帝异说保；未名宫人和太后不猜。王昶沿继鹏别名，清远沿917汉主女婚事复用；林置邸任职往事年null、闻弑求归哭3日本年。贤妃非后。',30:'以兄事只是尊敬不亲兄弟，郎君非儿子；马是谈话对象非在场。久、它日、退居后常态起年不具为null，孙警告亡国不是935实际灭楚。宋卷483补孙字籍；旧梁附注来自非当前基础专书不伪作独证。',31:'臣光曰整段保存为史评，年null，无宋作者在五代谈话参与边；反问为评价非亡国结果。',32:'加衔十州封齐国与辞尚父丞相殊礼分；新九月接封爵、三年建齐国压缩层次保，不把吴国内封国当937南唐建立。',33:'李亻放沿李仿，非新人物，林延皓非唐刘延皓。伏兵杀、死后部曲攻门焚门夺首、诏宣罪、二任官分，新枭市主朝门各保。叶福王友追叙年null，国翁师傅非父。求退慰留、谏元妃、上书放归与后寿终确年不具均null；李敏闽臣非唐昭宗。甥称保，未推母系具体人物。',34:'嘉功召、刘索拟绛州、帝乙卯任横海留后分，欲除不当已到绛任；旧马传补重美闻奏，旧帝纪通鉴附注不算独证，只正文沧州官命互核。',35:'主护国旧河中军地名分，韩昭裔沿韩昭胤，检校司空非冯道正官司空。壬申两书同。',36:'主乙酉旧己丑冯任司空日异；同州匡国军地同，保两说。卢拟祭祀扫除、冯回应、后卢止分，方案不当已执行；新卷55马胤孙传核传主，不冠冯传名。',37:'当前闽主王昶非王延钧；天师号主新同，新后三年情节不提前。赐号与咨政受贿常态分，常态始年null；其门如市比喻，未名行贿者不造人。'}
context_path=YEAR.parent/'year-0934/part-02/sources/library/xinwudaishi-055-ma-yinsun/source.txt'
contexts=[dict(file=os.path.relpath(context_path,P/'sources'),sha256=hashlib.sha256(context_path.read_bytes()).hexdigest(),paragraph_id='xin-wudaishi-b08f244b9241-p002152',purpose='回查卷55马胤孙传首，确认下一段司空职掌讨论的传主；不扩录他段',url='https://github.com/greed-216/histree/blob/2ec8cf50/'+str(context_path.relative_to(ROOT)))]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(29,38):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=935,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(29,38)],next_paragraph='zztj-v280-y0936-p001',next_volume=280,next_year=936,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷279连续935年第29—37正文段，原113—121行；闽政变王昶继位、荆南劝谏退休与史评、吴齐封国、闽除李仿叶翘、马任留后、唐年末韩冯官命及闽陈天师。本年最后9段，发布核验后才可记整年完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(29,38)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
