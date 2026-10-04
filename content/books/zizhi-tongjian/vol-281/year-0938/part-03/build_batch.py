# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 938 paragraphs 13–16."""
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
specs=[(d.name,d,'b6102df6b68d4c58675c5a80afe032a10353cc33','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-938-palace-and-policy']:
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
main_sources = ['tongjian-281-938-palace-and-policy']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0938-p013-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-077-june':'卷77·晋高祖纪·天福三年六月','jiuwudaishi-077-july':'卷77·晋高祖纪·天福三年七月'}
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
for n in range(13, 17):
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
    labels={'jiuwudaishi-077-june':'卷77·晋高祖纪·天福三年六月','jiuwudaishi-077-july':'卷77·晋高祖纪·天福三年七月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '六月条下' if n<15 else '七月条下'
        citation = f'卷281·后晋天福三年（938；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0938_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'经铸（后晋金部郎中）':'后晋金部郎中。938年六月奏请调整垦田农户承担徭役的条件，石敬瑭接受建议。姓名沿《资治通鉴》电子底本，生卒年和其他经历未载。',
'刘皞（后晋编敕官）':'后晋官员。《旧五代史》记载，938年七月以驾部员外郎兼侍御史知杂事的身份参与编订唐明宗时期的诏敕。生卒年未载。',
'张仁彖（后晋大理正）':'后晋大理正。《旧五代史》记载，938年七月参与编订唐明宗时期的诏敕。生卒年未载。'}
NEW_ALIASES={'经铸（后晋金部郎中）':['经铸','經鑄'],'刘皞（后晋编敕官）':['刘皞','劉皞'],'张仁彖（后晋大理正）':['张仁彖','張仁彖']}

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
    if when is None:when='938年六月，具体日期未记载' if n<15 else '938年七月，具体日期未记载'
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

ALIASES.update({'经铸':'经铸（后晋金部郎中）','刘皞':'刘皞（后晋编敕官）','张仁彖':'张仁彖（后晋大理正）'})
add('gao_requests_luoyang_palace','高行周奏请修缮洛阳宫',13,'河南留守','奏修洛阳宫。',[('高行周','以河南留守身份奏请修缮洛阳宫')],year=None,when='938年六月丙戌薛融进谏之前，奏请的具体日期未载',place='洛阳宫',note='奏请与施工执行分开；本句没有给出高行周奏请的具体日期。')
add('xue_opposes_palace_works','薛融建议暂缓修缮洛阳宫',13,'丙戌，','营之未晚。”',[('薛融','以左谏议大夫身份建议暂缓修宫'),('帝','收到薛融暂缓修宫的建议')],when='938年六月丙戌',place='洛阳宫',description='薛融指出魏城尚未攻下、国家和百姓都处于困窘之中，建议等局势安定后再修缮洛阳宫。',note='困窘和修宫时机是薛融的进谏内容；帝尧和汉文帝是他引用的历史例子，不作为938年事件参与者。')
add('shi_accepts_xue_advice','石敬瑭接受薛融的建议，并下诏表扬他',13,'上纳其言，',None,[('帝','接受暂缓修宫的建议，并下诏表扬薛融'),('薛融','进谏被接受，并获得诏书表扬')],when='938年六月丙戌条下',place='洛阳宫',note='帝接受建议与后来停止营造分开；主书此句没有记工程停止的具体日期。')
sup('shi_accepts_xue_advice',13,'jiuwudaishi-077-june','左諫議大夫薛融上疏，請停修洛京大內。優詔褒之，尋罷營造。','《旧五代史》也记薛融请求停止修缮洛阳宫，朝廷下诏表扬他，随后停止营造。','《旧五代史》记在六月，但没有单列进谏日；不将相邻甲申当作此事发生日。')
event('luoyang_palace_works_stop','洛阳宫的修缮工程随后停止',13,'左諫議大夫薛融上疏，請停修洛京大內。優詔褒之，尋罷營造。',[],source='jiuwudaishi-077-june',year=None,when='薛融进谏获接受之后，具体日期未载',place='洛京大内',note='《旧五代史》明确写随后停止营造；寻表示时间接近但不是确定日期，年份字段留空，保留六月记载的上下文。')
add('jing_zhu_reports_farmers_burden','经铸报告垦田农户被过早征派徭役的问题',14,'己丑，','更思他适。',[('经铸','以金部郎中身份报告农户遭遇赋役压力'),('帝','收到经铸的报告')],when='938年六月己丑',description='经铸报告，有些流动农户愿意耕种定居，却在种树未满十年、垦田未到三顷时，就被县里征派徭役、催缴重赋，因而放弃经营并考虑迁往别处。',note='农户处境按经铸奏报呈现，不推为所有地区的普遍统计；顷为史载单位，不自行折算现代面积。')
add('jing_zhu_proposes_service_threshold','经铸建议调整垦田农户承担徭役的条件',14,'乞自今','乃听县司徭役。”',[('经铸','建议垦田达到五顷以上，三年之后才允许县里征派徭役'),('帝','收到调整徭役条件的建议')],when='938年六月己丑',description='经铸建议，今后农户垦田达到五顷以上，三年之后才允许县里征派徭役。',note='保留五顷以上和三年外两项条件；原文未交代三年具体从哪一行政登记日起算，也未明说五顷以下农户永远免役，不补出这些规则。')
add('shi_accepts_farming_service_rule','石敬瑭接受经铸调整徭役条件的建议',14,'乞自今',None,[('经铸','调整垦田徭役条件的建议被接受'),('帝','接受经铸的建议')],when='938年六月己丑条下',description='石敬瑭接受经铸的建议：农户垦田达到五顷以上，三年之后才允许县里征派徭役。',note='从之说明接受建议，不证明各县已经落实；经铸姓名保留电子底本字形，尚无其他书证确认，不猜改为景铸或荆铸。')
add('secretariat_proposes_edict_compilation','中书建议整理唐明宗时期和清泰年间的诏敕',15,'秋，七月，','编次之。”',[],when='938年七月，奏请的具体日期未载',description='中书建议派官员收集唐明宗时期和清泰年间的诏敕，选出可以长期施行的条文，整理编订。',note='朝代虽殊是奏请中的论述，不表示所有旧条文都自动继续有效；明宗及清泰属于旧朝背景，不新增当时已故君主的参与关系。')
add('xue_appointed_edict_compilation','石敬瑭命薛融等官员审核编订旧诏敕',15,'己酉，',None,[('帝','命薛融等官员审核编订旧诏敕'),('薛融','以左谏议大夫身份受命审核旧诏敕')],when='938年七月己酉',description='石敬瑭命左谏议大夫薛融等官员审核编订唐明宗时期和清泰年间的诏敕。',note='主书日期为七月己酉；任命与最终编订完成分开，原文没有记书成。')
old='jiuwudaishi-077-july';oq=source_span(old,'七月丙午朔，','同共詳定唐明宗朝編敕。')
sup('xue_appointed_edict_compilation',15,old,oq,'《旧五代史》将任命编敕官记为七月丙午朔，并列出薛融、吕琦、刘皞、司徒诩和张仁彖。','《资治通鉴》为己酉，《旧五代史》为丙午朔；两书日期分别保留，不强行认作同日，也不新增一次重复任命事件。',relation='conflicts',field='time_original')
sup('xue_appointed_edict_compilation',15,old,oq,'《旧五代史》补充编敕官包括秘书监吕琦、驾部员外郎兼侍御史知杂事刘皞、刑部郎中司徒诩和大理正张仁彖，记整理对象为唐明宗时期的诏敕。','主书还包括清泰时敕；该书只写明宗朝，两种记载各自保留。编敕官姓名采用简体展示，刘皞不因形近擅改为刘昊。',relation='adds')
for name,role in [('吕琦','以秘书监身份受命参与编订唐明宗时期的诏敕'),('刘皞','以驾部员外郎兼侍御史知杂事身份受命参与编敕'),('司徒诩','以刑部郎中身份受命参与编敕'),('张仁彖','以大理正身份受命参与编敕')]:
 pk=person(name,15,role,oq,source=old);key='participation_zztj_281_0938_edict_compilation_'+pk
 B['person_events'].append(dict(key=key,person_key=pk,event_key=E['xue_appointed_edict_compilation'],role=role,status='draft'))
 claim('person_event',key,'role',f'{name}：{role}。',15,oq,'参与身份来自《旧五代史》，日期异说随事件独立引用保留；司徒诩沿用已有主体，司徒为姓氏，不当作本次官职。',source=old)
add('shi_orders_mandate_seal','石敬瑭下令制作受命宝',16,'辛酉，',None,[('帝','下令制作受命宝，并确定印文')],when='938年七月辛酉',description='石敬瑭下令制作受命宝，印文为“受天明命，惟德允昌”。',note='敕作是制作命令，此句不能证明印章已在当日完成；印文保持原词，不扩写为已举行封禅。')
sup('shi_orders_mandate_seal',16,old,'辛酉，制皇帝受命寶，以「受天明命，惟德允昌」為文。','《旧五代史》也记七月辛酉制作皇帝受命宝，印文为“受天明命，惟德允昌”。','两书正文日期与印文一致；《旧五代史》夹注所引《五代会要》的六月记载并非独立采集的原书，暂不用于改动七月正文日期。')
reviews={13:'请求修宫、薛融进谏、皇帝接受表扬和后来停工分别记录；旧史明确停工，寻不赋确日，尧及汉文帝不作当时参与者。',14:'经铸奏报问题、门槛建议与皇帝接受分录；五顷以上、三年外原条件保留，不推以下永免或各县已执行。姓名尚缺其他书证，保留底本不猜改。',15:'中书奏请与任命编敕官分开；主书己酉、旧史丙午朔与范围差异独立引用。补四位编敕官，吕琦及司徒诩复用，刘皞及张仁彖未见既有主体，以职务限定。',16:'制作命令与当日完成不混同；两书正文七月辛酉与印文一致，旧史夹注六月记载留待版本校核。'}
assert not (P/'publication.json').exists()
for n in range(13,17):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=938,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(13,17)],next_paragraph=Q[17]['id'],next_volume=281,next_year=938,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第13—16段，原79—82行；修宫请求与停工、垦田徭役、编订旧诏敕、制作受命宝。938年未完成。',source_issues_review='逐行回查原文；旧五代史卷77六月及七月帝纪补证。编敕日期、范围及旧史夹注月份异说保留，经铸姓名暂无其他书证，不猜改。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(13,17)],plain_language_review='首次逐条检查展示字段，明确主语、请求/命令/执行、奏报归属和未明日期，原文不改字。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
