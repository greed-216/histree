# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 937 paragraphs 9–12."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,43))
specs=[(d.name,d,'4a35069cfc3928f34adb41bee7eced8805e1e876','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-937-min-and-year-end']:
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
main_sources = ['tongjian-281-937-min-and-year-end','tongjian-281-938-palace-and-policy']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0938-p009-p012',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-097-yang-family':'卷97·杨光远传','xinwudaishi-062-yang-pu-moves':'卷62·南唐世家'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订1769092；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
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
    labels={'jiuwudaishi-097-yang-family':'卷97·杨光远传','xinwudaishi-062-yang-pu-moves':'卷62·南唐世家'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '四月至五月跨月条' if n==9 else '五月条下' if n<12 else '六月条下'
        citation = f'卷281·后晋天福三年（938；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0938_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'杨承祚':'杨光远的儿子。938年五月被任命为左威卫将军，并与石敬瑭的女儿长安公主结婚。',
'杨承信':'杨光远的儿子。《资治通鉴》称他为次子，938年五月与杨承祚同获优厚任官，具体官名未载。',
'长安公主（石敬瑭女）':'后晋皇帝石敬瑭的女儿，以长安公主为封号。938年五月与杨承祚结婚，个人姓名和生卒年此段未载。',
'公孙圭':'南唐官员。原任客省使，938年五月在杨溥迁居丹杨宫的安排中被任命为监军使。',
'马思让':'徐诰的亲近吏员。938年五月被任命为丹杨宫使，参与杨溥迁居后的管理安排。',
'杨嗣（南唐留守判官）':'南唐留守判官。938年六月请求改姓羊，徐玠反对更改带有吴、杨名称或姓氏的做法，徐诰接受徐玠的意见。杨嗣并未在此段被记为已经改姓。'}
NEW_ALIASES={'杨承祚':['楊承祚'],'杨承信':['楊承信'],'长安公主（石敬瑭女）':['长安公主','長安公主'],'公孙圭':['公孫圭'],'马思让':['馬思讓'],'杨嗣（南唐留守判官）':['杨嗣','楊嗣']}

ALIASES.update({'景通':'李璟','徐知诰':'李昪','徐诰':'李昪','元瓘':'钱传瓘','钱元瓘':'钱传瓘','闽主':'王继鹏','蜀主':'孟昶','汉主':'刘岩','梁均王':'朱友贞'})



ALIASES.update({'张彦琦':'张彦琪','张彦琪':'张彦琪','曹太后':'曹氏（李嗣源后）','刘皇后':'刘氏（李从珂后）','太相温':'太相温（契丹将）','大相温':'太相温（契丹将）','汉主':'刘岩','吴主':'杨溥','杨光远':'杨檀','景岩':'刘景岩','刘延郎':'刘延朗','李赞华':'耶律倍','李懿':'李懿（后唐亲将）'})

# Follow already verified merges so hidden legacy entities are never revived.
registry_by_key={r['key']:r for r in registry.values()}
for plan_file in sorted((ROOT/'content/revisions').glob('*/plan.json')):
 audit_file=plan_file.parent/'publication.json'
 if not audit_file.exists():continue
 plan=json.loads(plan_file.read_text());audit=json.loads(audit_file.read_text())
 if not (audit.get('verified') and audit.get('canonical_person_id') and audit.get('hidden_duplicate_person_id')):continue
 canonical=registry_by_key.get(plan.get('canonical_key'));duplicate=registry_by_key.get(plan.get('duplicate_key'))
 if canonical and duplicate:
  canonical=dict(canonical,aliases=list(dict.fromkeys(canonical.get('aliases',[])+plan.get('aliases_to_add',[]))))
  registry[canonical['name']]=canonical
  for alias in [duplicate['name']]+duplicate.get('aliases',[]):ALIASES[alias]=canonical['name']

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=938 if name in ['武彦和','王氏（守卫军使王宏之子）'] else None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=938, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='938年五月，具体日期未记载' if n<12 else '938年六月，具体日期未记载'
    key = 'event_zztj_281_0938_' + code
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
          '按《资治通鉴》及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_281_0938_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_281_0938_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'张昭远':'张昭（五代宋初）','契丹主':'耶律德光'})
ALIASES.update({'唐主':'李昪','让皇':'杨溥','帝':'石敬瑭','承祚':'杨承祚','承信':'杨承信','长安公主':'长安公主（石敬瑭女）','王舆':'王舆（吴光州刺史）','杨嗣':'杨嗣（南唐留守判官）','吴王璟':'李璟'})
add('yang_pu_requests_move','杨溥多次请求离开旧宫，李德诚等也劝其迁居',9,'吴让皇','亦亟以为言。',[('让皇','坚决辞谢旧宫，多次请求迁居'),('李德诚','多次为迁居安排进言')],year=None,when='受禅后至938年五月迁居安排之前，具体请求年月未载',note='请求不是已经迁出，亟为反复进言，不把相邻五月戊午当所有请求的发生日。')
add('li_bian_creates_danyang_palace','徐诰将润州牙城改为丹杨宫',9,'五月，戊午，','为丹杨宫，',[('唐主','将润州牙城改为丹杨宫，安排杨溥居住')],when='938年五月戊午',place='润州牙城、丹杨宫',note='牙城是原有城署区域，改宫不写成完全另建一座新城；丹杨沿主书字形，另一书丹阳分别保留。')
add('li_jianxun_receives_yang_pu','李建勋被任命为迎奉杨溥的使者',9,'以李建勋',None,[('唐主','任命李建勋为迎奉让皇使'),('李建勋','被任命迎接和奉侍杨溥'),('让皇','李建勋迎奉的吴国旧主')],when='938年五月戊午条下',note='任命使者与实际迁居分开，不写成戊午杨溥已到丹杨宫。')
add('yang_guangyuan_interferes_court','杨光远依仗重兵干预朝政，石敬瑭常迁就他',10,'杨光远','帝常屈意从之。',[('杨光远','依仗重兵干预朝政，多次强硬上奏'),('帝','常迁就杨光远的奏请')],year=None,when='杨光远掌握重兵期间，具体起止年月未载',note='持续行径不硬定庚申当天，杨光远沿用已合并的杨檀主体；不另造终身盟友关系。')
sup('yang_guangyuan_interferes_court',10,'jiuwudaishi-097-yang-family',source_span('jiuwudaishi-097-yang-family','兵柄在手，','高祖亦曲從之。'),'《旧五代史》也记杨光远掌握兵权后干预朝政，石敬瑭迁就他的奏请。','以为高祖惧己是该书对杨光远想法的描述，不作为石敬瑭本人承认害怕的证据。')
add('yang_chengzuo_left_guard','杨承祚被任命为左威卫将军',10,'庚申，','为左威卫将军，',[('帝','任命杨承祚为左威卫将军'),('承祚','被任命为左威卫将军')],when='938年五月庚申')
add('yang_chengzuo_marriage','杨承祚与石敬瑭的女儿长安公主结婚',10,'庚申，','尚帝女长安公主，',[('帝','将女儿长安公主嫁给杨承祚'),('承祚','与长安公主结婚'),('长安公主','与杨承祚结婚')],when='938年五月庚申条下',note='尚公主是婚姻，不译为崇尚或另给公主任官；公主用父亲身份限定，避免与其他时期同封号人物合并。')
sup('yang_chengzuo_marriage',10,'jiuwudaishi-097-yang-family','復下詔以其子承祚尚長安公主，次子承信皆授美官。','《旧五代史》也记杨光远之子杨承祚娶长安公主，杨承信获授优厚官职。','该传不列庚申，印证婚姻与父子身份，不补为独立确认同日婚礼。')
add('yang_chengxin_appointment','杨承信也获授优厚官职',10,'次子承信','宠冠当时。',[('帝','给杨承信授予优厚官职'),('承信','获授官职，与家族受到特别宠遇')],when='938年五月庚申条下',note='未具具体官名，不造左威卫或其他同组官职；宠冠为史书记述，不据此量化权力排名。')
relationship('杨光远','承祚','父亲',10,span(10,'庚申，','尚帝女长安公主，'),'其子承祚承接杨光远，父亲方向明确。')
relationship('杨光远','承信','父亲',10,Q[10]['text'],'次子承信承接杨光远，明确父亲方向；不由次子反推承祚就是长子。')
relationship('帝','长安公主','父亲',10,span(10,'庚申，','尚帝女长安公主，'),'帝女明确石敬瑭是公主的父亲。')
relationship('承祚','长安公主','丈夫',10,span(10,'庚申，','尚帝女长安公主，'),'尚公主明确婚姻，方向为杨承祚是长安公主的丈夫。')
add('wang_yu_zhenhai','王舆被任命为镇海留后',11,'壬戌，','为镇海留后，',[('唐主','任命王舆为镇海留后'),('王舆','由左宣威副统军被任命为镇海留后')],when='938年五月壬戌',place='镇海军',note='复用930年由吴光州刺史转任控鹤都虞候的王舆主体：同属徐知诰辖下宿卫官，吴至南唐政权延续；不因本次职名变化另建同名人物。')
sup('wang_yu_zhenhai',11,'xinwudaishi-062-yang-pu-moves','以王輿為浙西節度使、馬思讓為丹陽宮使，以嚴兵守之。','《新五代史》写王舆为浙西节度使，并记以严兵守杨溥。','镇海留后与浙西节度使的职衔差异保留，不直接覆盖或假定在同一天由留后升为正式节度使。',relation='conflicts')
add('gongsun_gui_monitor','公孙圭被任命为监军使',11,'客省使公孙圭','为监军使，',[('唐主','任命公孙圭为监军使'),('公孙圭','由客省使被任命为监军使')],when='938年五月壬戌',place='杨溥迁居丹杨宫的管理安排',note='本句未独列监军辖区，不造全部镇海军的确切监军权限。')
add('ma_sirang_palace_director','马思让被任命为丹杨宫使',11,'亲吏马思让','为丹杨宫使，',[('唐主','任命亲吏马思让为丹杨宫使'),('马思让','被任命为丹杨宫使')],when='938年五月壬戌',place='丹杨宫')
sup('ma_sirang_palace_director',11,'xinwudaishi-062-yang-pu-moves','以王輿為浙西節度使、馬思讓為丹陽宮使，以嚴兵守之。','《新五代史》也记马思让为丹阳宫使，并以严兵守杨溥。','丹杨与丹阳字形分别保留，守卫的补充说明不据此造未具名守卫人物。',relation='adds')
add('yang_pu_moves_danyang','杨溥被迁往丹杨宫居住',11,'徙让皇','居丹杨宫。',[('唐主','将杨溥迁往丹杨宫'),('让皇','迁往丹杨宫居住')],when='938年五月壬戌',place='润州丹杨宫',note='这是实际迁居，与前段请求和戊午改牙城任迎奉使分别记录。')
sup('yang_pu_moves_danyang',11,'xinwudaishi-062-yang-pu-moves','二年四月，遷楊溥於潤州丹陽宮。','《新五代史》把杨溥迁往润州丹阳宫记为二年四月。','南唐升元二年相接938年；主书五月壬戌与该书四月不同，各保原纪时，不强行统一。',relation='conflicts',field='time_original')
add('song_qiqiu_blames_courtiers','宋齐丘称受左右离间，徐诰发怒，他回家穿白衣待罪',11,'宋齐丘复自陈','白衣待罪。',[('宋齐丘','自称被君主左右离间，随后回家穿白衣等待处分'),('唐主','听到宋齐丘的陈述后发怒')],when='938年五月迁居条后，具体日期未记载',note='离间是宋齐丘自述，不认定某个未具名官员实际诬陷；白衣待罪不等于已经正式免职。')
add('li_bian_recalls_song','徐诰命李璟持亲笔诏书召回宋齐丘',11,'或曰：',None,[('唐主','听取不要轻弃旧臣的劝说后，命李璟召回宋齐丘'),('吴王璟','持徐诰亲笔诏书召宋齐丘'),('宋齐丘','被亲笔诏书召回')],description='有人劝徐诰不要因小过抛弃旧臣宋齐丘。徐诰评价宋齐丘有才却不识大体，随后命吴王璟持亲笔诏书召他。',note='评价归徐诰，不作为网站自行定论；匿名劝者不造姓名，召回不证明已给宋齐丘新职或全面恢复政务权限。')
add('li_bian_rejects_poison','徐诰拒绝别人献上的毒酒配方',12,'六月，壬午，','安用此为！”',[('唐主','拒绝毒酒配方，表示犯法者已有常刑')],when='938年六月壬午',note='匿名献方者不造姓名；只记拒绝，不新增实际毒杀、配方细节或刑罚执行。')
add('ministers_request_name_changes','群臣请求改掉机构和地名中的吴、杨字',12,'群臣争请','名有吴及杨者，',[('唐主','收到群臣更名的请求')],when='938年六月壬午条下',note='府寺是官署机构，不能只译为佛寺；这是更名请求，未记已经全部改名。')
add('yang_si_requests_sheep_surname','留守判官杨嗣请求改姓羊',12,'留守判官','请更姓羊，',[('杨嗣','以留守判官身份请求改姓羊'),('唐主','收到杨嗣改姓请求')],when='938年六月壬午条下',note='杨嗣与唐代杨嗣复时代和职务不同，使用限定主体；请求不等于已改姓，羊不录为既成别名。')
add('xu_jie_opposes_name_changes','徐玠反对更名改姓，徐诰接受他的意见',12,'徐玠曰：',None,[('徐玠','反对为避吴、杨字而更改名称和姓氏'),('唐主','接受徐玠的意见')],when='938年六月壬午条下',description='徐玠认为改掉带吴、杨的名称和姓氏是迎合之举，并非急务，建议不要采纳。徐诰认可他的意见。',note='应天顺人、非逆取是徐玠对君主的陈述，不作为网站对受禅合法性的结论；不把反对意见写成已执行大规模更名。')
for name,n,start,end in [('杨承祚',10,'庚申，','尚帝女长安公主，'),('杨承信',10,'庚申，',None),('长安公主（石敬瑭女）',10,'庚申，','尚帝女长安公主，'),('公孙圭',11,'客省使公孙圭','为监军使，'),('马思让',11,'亲吏马思让','为丹杨宫使，'),('杨嗣（南唐留守判官）',12,'群臣争请',None)]:
 claim('person',people[name],'description',NEW_DESCRIPTIONS[name],n,span(n,start,end),'简介只使用明确身份和行动，生卒家世未记的部分留空；请求和实际任官分开。')
reviews={9:'杨溥辞旧宫、反复请求与李德诚进言时日未明，不当已迁；五月戊午改牙城为宫及任迎奉使分别记。',10:'杨光远持续干政与庚申儿子任官、婚姻分录；既有杨光远合并主体仍用杨檀key。父亲、丈夫方向明确，不推完整兄弟长幼；承信美官未具名不造官职。',11:'五月壬戌王舆留后、公孙监军、马宫使与杨溥迁居分录；王舆复用吴光州及宿卫原主体。新史四月/主五月、浙西节度/镇海留后、丹阳/丹杨独立引用。宋离间自述和君主评价各归说话者，待罪与召回不推罢职或复职。',12:'六月壬午拒毒酒方，不造匿名献方者和毒杀事实。群臣更机构地名与杨嗣请求改姓是请求，徐玠反对并被采纳；不将羊记既成别名，杨嗣不与唐杨嗣复混同。'}
assert not (P/'publication.json').exists()
for n in range(9,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n');(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=938,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,13)],next_paragraph=Q[13]['id'],next_volume=281,next_year=938,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第9—12段，原75—78行；杨溥请求及迁居安排、杨家任官婚姻、五月丹杨宫任官和宋齐丘争执、六月拒毒方与更名改姓建议。938年未完成。',source_issues_review='原文逐行回查，新旧五代史卷和传主已核。迁居月份及王舆职衔异说保留；王舆与既有吴官主体沿用，不按职名再建；杨嗣用南唐留守判官限定，不与唐杨嗣复混同。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,13)],plain_language_review='首次逐条自查展示字段，明确请求/安排/实际迁居、亲属方向、匿名人物、原话归属及未知日期；引用原字不改。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
