# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 937 paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,60))
specs=[(d.name,d,'bd256224ade10807719cc5b9dd08151101a79e9c','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-094-mi-qiong','xinwudaishi-008-lu-date']:
 prior=next(x for f in (ROOT/'content').rglob('content-batch.json') for x in json.loads(f.read_text())['sources'] if x['key']==key)
 commit,relative=prior['url'].split('/blob/')[1].split('/',1)
 specs.append((key,(ROOT/relative).parent,commit,prior['author']))

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
main_sources = ['tongjian-281-937-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0937-p001-p008',
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
lines = (ROOT / 'resources/derived/tongjian/281.txt').read_text().splitlines()
for n in range(1, 9):
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
        month = '正月条下' if n < 8 else '二月条下'
        citation = f'卷281·后晋天福二年（937；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0937_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_ALIASES={'王景崇':[], '张生（范延光所遇术士）':['张生'], '周廷玉':[], '徐氏（杨琏妃）':['徐知诰女']}
NEW_DESCRIPTIONS={'王景崇':'后晋官员。937年担任引进使，受命劝秘琼接受任命。史书记载他是邢州人。', '张生（范延光所遇术士）':'范延光所信任的术士，史书只称他为张生。他对范延光的仕途和梦境作出预测；其具体姓名和活动年份尚不清楚。', '周廷玉':'吴国官员，黟县人。937年由内枢判官出任徐知诰政权的内枢使。', '徐氏（杨琏妃）':'徐知诰（后来的李昪）的女儿，937年嫁给吴太子杨琏。此段没有记载她的名字。'}
ALIASES.update({'张生':'张生（范延光所遇术士）'})


ALIASES.update({'张彦琦':'张彦琪','张彦琪':'张彦琪','曹太后':'曹氏（李嗣源后）','刘皇后':'刘氏（李从珂后）','太相温':'太相温（契丹将）','大相温':'太相温（契丹将）','汉主':'刘岩','吴主':'杨溥','杨光远':'杨檀','景岩':'刘景岩','刘延郎':'刘延朗','李赞华':'耶律倍','李懿':'李懿（后唐亲将）'})

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',(row['description'] if name in NEW_DESCRIPTIONS else f'{name}：{role}。'),n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=937, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='937年正月，具体日期未记载' if n<8 else '937年二月，具体日期未记载'
    key = 'event_zztj_281_0937_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=description or title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='采用史书记载的地点名称，地理坐标尚未核实。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_281_0937_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'与{a}存在原文明示的亲属关系',quote,source=source)
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
        row=dict(key=f'relationship_zztj_281_0937_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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

# Curated opening paragraphs.
# Consecutive main text: appointments, political violence, administration and Wu.
add('january_eclipse','史书记载正月乙卯发生日食',1,'春，',None,[],when='937年正月乙卯',description='《资治通鉴》记载，天福二年正月乙卯发生日食。',note='这是史书的天象记录，未自行换算公历日期。')
sup('january_eclipse',1,'jiuwudaishi-076-937-january-a','乙卯，日有蝕之。','《旧五代史》也记载正月乙卯发生日食。','同段开头明确为天福二年正月，日期与《资治通鉴》一致。')
add('an_mi_appointments','石敬瑭任命安重荣为成德节度使、秘琼为齐州防御使',2,'诏以','齐州防御使。',[('帝','任命两人调整地方军职'),('安重荣','由北面招收指挥使出任成德节度使'),('秘琼','被任命为齐州防御使')],note='任命与到任分开记录，不根据任命直接断定秘琼已到齐州。')
sup('an_mi_appointments',2,'jiuwudaishi-094-mi-qiong','高祖即位，遣安重榮代之，授瓊齊州防禦使。','《旧五代史》秘琼传也记载安重荣接替秘琼，秘琼改任齐州防御使。','传记未另记具体日期，保留《资治通鉴》正月的时间范围。')
add('wang_jingchong_persuades_mi','王景崇受命劝秘琼接受任命',2,'遣引进使',None,[('王景崇','以引进使身份劝秘琼接受任命'),('秘琼','接受王景崇劝说的任命对象')],description='石敬瑭派引进使王景崇向秘琼说明利害。史书随后记载秘琼没有拒绝任命；王景崇是邢州人。',note='王景崇籍贯由本段末句确认，邢州不当作此次劝说地点。')
add('an_zhao_reach_zhenzhou','安重荣与赵思温到镇州，秘琼没有拒绝任命',2,'重荣与','琼不敢拒命。',[('安重荣','与赵思温一起到镇州接任'),('赵思温','作为契丹将领与安重荣同行'),('秘琼','没有拒绝任命')],place='镇州')
sup('an_zhao_reach_zhenzhou',2,'jiuwudaishi-094-mi-qiong','時重榮與蕃帥趙思溫同行，部曲甚眾，瓊不敢拒命，','《旧五代史》还记载同行军队人数很多，秘琼不敢拒绝任命。','不把人数很多换算成没有依据的具体兵力。',relation='adds')
add('an_reports_office','安重荣奏报已到任',2,'丙辰，','重荣奏已视事。',[('安重荣','向朝廷奏报已经到任处理事务')],when='937年正月丙辰',place='镇州',note='丙辰是奏报日期，到任的具体日期没有独立记载。')
add('youzhou_nanjing','契丹把幽州设为南京',3,'契丹',None,[],place='幽州',description='契丹把幽州设为南京。此处保留历史地名，不把它与今天的南京市混为一处。')
sup('youzhou_nanjing',3,'jiuwudaishi-076-937-january-a','定州奏，契丹改幽州為南京。','《旧五代史》也记载定州奏报契丹将幽州改为南京。','奏报与实际改设的日期不一定相同，保留正月范围。')
add('li_lu_hide_yique','李崧和吕琦曾躲藏在伊阙民间',4,'李崧、','伊阙民间。',[('李崧','曾躲藏在伊阙民间'),('吕琦','曾躲藏在伊阙民间')],year=None,when='937年正月任官条前追述，躲藏的起止日期未记载',place='伊阙',note='这段是任官前背景，不将逃藏起始时间强定为937年。')
add('shi_spares_li_lu','石敬瑭感谢李崧过去的帮助，也没有追究吕琦',4,'帝以','亦不责琦。',[('帝','感谢李崧过去的帮助，也不追究吕琦'),('李崧','过去曾帮助石敬瑭出镇河东'),('吕琦','没有受到石敬瑭追究')],note='没有追究不等于经过审判后宣布无罪；过去帮助的时间不由本段推算。')
add('lu_qi_secretary','石敬瑭任命吕琦为秘书监',4,'乙丑，','以琦为秘书监；',[('吕琦','被任命为秘书监')],when='937年正月乙丑')
sup('lu_qi_secretary',4,'jiuwudaishi-076-937-january-b','乙丑，以端明殿學士、禮部侍郎呂琦為檢校工部尚書、秘書監。','《旧五代史》补充吕琦原任端明殿学士、礼部侍郎，此次另加检校工部尚书。','同日任官，检校职衔不写成实际主持工部。',relation='adds')
add('li_song_finance','李崧被任命为兵部侍郎并掌管户部事务',4,'丙寅，',None,[('李崧','被任命为兵部侍郎、判户部')],when='937年正月丙寅',note='判户部指掌管户部事务，不等于官衔为户部尚书。')
sup('li_song_finance',4,'jiuwudaishi-076-937-january-b','以端明殿學士、戶部侍郎李崧為兵部侍郎、判戶部，','《旧五代史》同样记载李崧改任兵部侍郎、判户部，并补充其原职。','本纪上承丙寅，任职链与姓名一致。',relation='adds')
add('fan_trusts_diviner','范延光相信术士张生的预测，并产生称帝的念头',5,'初，','有非望之志。',[('范延光','相信术士对仕途和梦境的预测'),('张生','预测范延光会做将相，并把蛇入腹的梦解释成帝王征兆')],year=None,when='追述范延光早年及显贵后的经历，具体年份未记载',description='史书记载，术士张生曾预测范延光会做将相。范延光显贵后十分信任他，又请他解释蛇进入腹中的梦。张生把梦说成帝王征兆，范延光因此产生了称帝的念头。',note='预测、梦境和征兆解释是史书记载的言行，不作为客观预言成立的证明。张生姓名未详，使用带身份限定的主体。')
add('fan_returns_and_submits','赵德钧战败后，范延光从辽州回魏州并上表请降',5,'唐潞王','内不自安，',[('范延光','从辽州回魏州，上表请降，但心中不安'),('唐主','此前与范延光关系友好'),('赵德钧','其战败是范延光回军的背景')],year=936,when='追述936年赵德钧战败后的经历，具体日期未记载',place='辽州至魏州',note='唐潞王为李从珂；赵德钧战败在前一年。两人仅是背景对象，不认定在范延光回军现场。')
add('fan_invites_mi_plot','范延光秘密写信拉拢秘琼一起作乱，秘琼没有答复',5,'以书潜结','延光恨之。',[('范延光','秘密写信拉拢秘琼，并因没有得到答复而怨恨'),('秘琼','收到范延光的信但没有答复')],year=None,when='937年正月杀秘琼之前的经历，写信日期未记载',note='邀请共同作乱不等于双方已经结盟，不新增盟友关系。')
sup('fan_invites_mi_plot',5,'jiuwudaishi-094-mi-qiong','先是，鄴帥範延光將謀叛，遣牙將範鄴持書構瓊，瓊領書不答。','《旧五代史》秘琼传同样记载秘琼收到信后没有答复，并称送信人为牙将范邺。','这条补证与《资治通鉴》一致；范邺没有进一步身份依据，暂保留在事实说明中。',relation='adds')
sup('fan_invites_mi_plot',5,'jiuwudaishi-076-937-january-b','初，延光將萌異志，使人潛結於瓊，諾之。','《旧五代史》晋高祖纪却记载秘琼曾答应范延光。','同书本纪与秘琼传说法不同，不将“答应”和“没有答复”合并成一致结论。',relation='conflicts')
add('fan_kills_mi','范延光派兵在夏津杀死秘琼',5,'琼将之齐，','杀之。',[('范延光','派兵拦截并杀死秘琼'),('秘琼','赴齐州途中在夏津被杀')],place='夏津',description='秘琼前往齐州，途中经过魏州辖境。史书记载，范延光为灭口，也贪图秘琼携带的财物，派兵在夏津拦截并杀死他。',note='本段丁卯是后面的奏报日期，不能直接作为此书明确记载的杀人日期。')
sup('fan_kills_mi',5,'jiuwudaishi-094-mi-qiong','及聞瓊過其境，密使精騎殺瓊於夏津，以滅其口，一行金寶侍伎，皆為延光所有，','《旧五代史》秘琼传也记载夏津杀人，并补充秘琼随行的财宝与侍伎被范延光占有。','侍伎没有具名，不凭这句创建具体人物或婚姻关系。',relation='adds')
sup('fan_kills_mi',5,'xinwudaishi-008-lu-date','丁卯，天雄軍節度使范延光殺齊州防禦使祕瓊。','《新五代史》将杀秘琼记在天福二年正月丁卯。','《资治通鉴》同日记范延光奏报；杀人和奏报的日期口径不同，保留各书记法。',relation='conflicts',field='time_original')
claim('person',people['秘琼'],'death_year','秘琼于937年赴齐州途中被杀。',5,span(5,'琼将之齐，','杀之。'),'主书正月条与《新五代史》天福二年正月同年，死年确定；复用人物不直接覆盖其旧档案。')
add('fan_reports_accidental_killing','范延光奏称秘琼被捕盗兵误杀，石敬瑭没有追究',5,'丁卯，',None,[('范延光','向朝廷奏称秘琼被捕盗兵误杀'),('帝','没有追究此事')],when='937年正月丁卯',description='范延光向朝廷报告，称夏津捕盗兵误杀了秘琼。石敬瑭没有追究。史书前文已记范延光主动派兵杀人，因此“误杀”保留为奏报中的说法。',note='奏报说法与史家叙事分开，不把“误杀”当作本站确定的死因。')
sup('fan_reports_accidental_killing',5,'jiuwudaishi-076-937-january-b','魏府範延光奏：「當管夏津鎮捕賊兵士，誤殺卻新齊州防禦使秘瓊。」','《旧五代史》也保存范延光的误杀奏报。','本纪没有在这句单列丁卯，不能据此另补确定的奏报日。')
add('li_song_chancellor','李崧出任宰相并兼任枢密使',6,'戊寅，','充枢密使，',[('李崧','被任命为中书侍郎、同平章事并充枢密使')],when='937年正月戊寅')
sup('li_song_chancellor',6,'jiuwudaishi-076-937-january-b','戊寅，以兵部侍郎、判戶部李崧為中書侍郎、同中書門下平章事，充樞密使；','《旧五代史》记载李崧同日任中书侍郎、同中书门下平章事并充枢密使。','保留正式职衔，同平章事为宰相职务。')
sup('li_song_chancellor',6,'xinwudaishi-008-lu-date','戊寅，兵部侍郎李崧為中書侍郎、同中書門下平章事、樞密使。','《新五代史》也记载李崧在正月戊寅担任这些职务。','两书同日同职，独立保留出处。')
add('sang_shumishi','桑维翰兼任枢密使',6,'桑维翰','兼枢密使。',[('桑维翰','兼任枢密使')],when='937年正月戊寅',note='与李崧任官同属戊寅条，不推断两人权力大小。')
sup('sang_shumishi',6,'jiuwudaishi-076-937-january-b','以權知樞密使事、中書侍郎、同中書門下平章事、集賢殿學士桑維翰為樞密使。','《旧五代史》补充桑维翰此前已权知枢密使事，此次正式任命。','保留此前暂掌职务与正式任命的区别。',relation='adds')
add('jin_early_hardship','后晋初年藩镇不安，财政和民生困难',6,'时晋新得天下，','而契丹征求无厌。',[],description='史书记载，后晋刚建立时，不少藩镇尚未归服，归服者也有不安。战乱耗尽府库，百姓生活困苦，契丹又不断索求。',note='这段是史家对初年局势的概述，不把笼统描述换算成具体财政数据。')
add('sang_policy_advice','桑维翰建议安抚藩镇、维持契丹关系并发展生产贸易',6,'维翰劝帝','以丰货财。',[('桑维翰','向石敬瑭提出安抚藩镇、外交、军事和经济建议'),('帝','桑维翰提出治国建议的对象')],description='桑维翰建议石敬瑭以诚意安抚藩镇、放下旧怨，以谦辞厚礼维持与契丹的关系；同时训练军队、整修兵器，鼓励农桑增加储粮，畅通商业以增加财货。',note='记录的是建议；没有把每项建议都写成已经执行完成。')
add('jin_gradual_stability','史书概述后晋数年间局势逐渐安定',6,'数年之间，',None,[],year=None,when='937年条中追述此后数年的变化，终止年份未明确',description='《资治通鉴》在记述桑维翰的建议后，概括称此后数年间中原局势逐渐安定。',note='“数年之间”跨越当前年份，不把整个结果定为937年；这句也不足以证明变化仅由一人一项政策造成。')
add('yang_lian_marriage','吴太子杨琏迎娶徐知诰的女儿',7,'吴太子琏','为妃。',[('杨琏','迎娶徐知诰的女儿为太子妃'),('徐氏（杨琏妃）','嫁给吴太子杨琏'),('徐知诰','其女嫁给杨琏')],note='徐知诰沿用李昪的稳定主体，此时尚未称帝；女儿姓名未载，使用身份限定名称。')
relationship('徐知诰','徐氏（杨琏妃）','父亲',7,span(7,'吴太子琏','为妃。'),'“知诰女”明示父女关系，父亲方向为李昪指向徐氏。')
relationship('杨琏','徐氏（杨琏妃）','丈夫',7,span(7,'吴太子琏','为妃。'),'原文明示纳妃，丈夫方向为杨琏指向徐氏，不额外建立反向重复边。')
add('li_bian_temples','徐知诰建立太庙和社稷',7,'知诰始','太庙、社稷，',[('徐知诰','开始建立太庙和社稷')],place='金陵',note='此时筹备王国制度，不把建庙等同于已经取代吴国称帝。')
sup('li_bian_temples',7,'xinwudaishi-062-937-qi','天祚三年，建齊國，置宗廟社稷，','《新五代史》也记载天祚三年建立齐国并设置宗庙社稷。','天祚三年为937年；世家按年概述，不将其后十月受禅提前到正月。')
add('jinling_jiangning','徐知诰把金陵改为江宁府，并改称宫城和殿',7,'改金陵','厅堂曰殿；',[('徐知诰','将金陵改称江宁府，并调整牙城和厅堂的称呼')],place='金陵、江宁府',description='徐知诰把金陵改为江宁府，把牙城称为宫城，把厅堂称为殿。这些名称变化反映其筹备王国制度的措施。',note='不凭名称变化推定新增疆域。')
add('song_xu_chancellors','宋齐丘与徐玠分别出任左、右丞相',7,'以左、右司马','左、右丞相，',[('宋齐丘','由左司马出任左丞相'),('徐玠','由右司马出任右丞相'),('徐知诰','任命宋齐丘和徐玠为丞相')])
sup('song_xu_chancellors',7,'xinwudaishi-062-937-qi','以宋齊丘、徐玠為左、右丞相。','《新五代史》也记载宋齐丘、徐玠分别任左、右丞相。','按两书列举顺序对应左右，保留独立出处。')
add('zhou_inner_council','周宗和周廷玉出任内枢使',7,'马步判官','为内枢使。',[('周宗','由马步判官出任内枢使'),('周廷玉','由内枢判官出任内枢使，史书称其为黟县人')],note='两人为同段并列任官，不因共任内枢使建立私人关系；黟是籍贯。')
add('qi_offices_armies','徐知诰沿用吴国官制，并设置骑兵八军、步兵九军',7,'自馀百官',None,[('徐知诰','设置官员体系和军队编制')],description='徐知诰其余官员的设置依照吴国制度，并设置骑兵八军、步兵九军。',note='“军”是原文编制单位，不能换成兵员数量。')
add('lu_wenjin_wu_appointment','杨溥任命卢文进为宣武节度使并兼侍中',8,'二月，',None,[('吴主','任命卢文进为宣武节度使并兼侍中'),('卢文进','在吴国受任宣武节度使并兼侍中')],place='吴国',note='这是吴国任官，不能与中原宣武军任职混同；此前投吴的不同纪时已在936年批次保存。')
# Sources and date differences are reviewed with their corresponding records.
reviews={1:'日食只按史载纪日记录，旧纪同日补证。',2:'任命、劝说、到镇与丙辰奏报分开；赵思温为同行契丹将，不假定族属或血亲。王景崇邢州籍贯有原句。',3:'幽州南京与现代南京区分；旧纪为定州奏报，不作为实际改设日。',4:'李吕逃藏起止未记载；过去帮助和现在任官分开。旧纪补吕检校职、李原职。',5:'预测与梦境均为记述言行。范回军请降属936背景；秘密写信年份未确定。旧纪秘答应与旧传不答并列；杀秘、误杀奏报分开，新纪丁卯日期口径保留。',6:'李任相和桑任枢密分录。困难为史家概述，政策为建议，数年稍安不定937当年结果。',7:'徐知诰复用李昪，杨琏妃名字不详。父亲与丈夫均有向，太庙、改名、丞相、内枢、编制逐项处理。新世家按年记齐国制度不提前十月受禅。',8:'吴宣武职务不合中原宣武；此次任官与此前投吴不同事。'}
assert not (P/'publication.json').exists()
for n in range(1,9): ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=937,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=281,next_year=937,supplements=supplements,source_contexts=[],source_issues_review='主书导出快照涵盖937年全年，因此带有私用字及非原始段落标记。本批逐行核对原文件第6—13行，与独立账本完全一致，均无私用字；私用字位于尚未处理的第11、12段。本批不将整份快照视为全年已处理。补书三个新增导出段落无源问题标记，正文已核对帝纪与南唐世家上下文。',excluded_non_body=[],coverage='连续第1—8段（原文件第6—13行）。完整处理后晋初年任官和局势、范延光杀秘琼、徐知诰王国制度及吴国任卢文进。937年尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],plain_language_review='首次整理逐条核对全部新展示文案、参与角色、事实说明及核对说明；原文保持底本字形。复用对象保留已发布档案，早期简介完善另行安排。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
