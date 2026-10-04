# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 939 paragraphs 28–32."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,42))
specs=[(d.name,d,('5efcbcb0eb59aa562545d6da167437d1e8fb96be' if d.name.endswith('-editorial-note') else 'edf81ef2a20318750c60f3a1d5fdfb06de275ef4'),'电子本校勘注，署名未核' if d.name.endswith('-editorial-note') else '司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-282-939-intercalary']:
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
main_sources = ['tongjian-282-939-intercalary','tongjian-282-939-autumn']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0939-p028-p032',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-078-august':'卷78·晋高祖纪·天福四年八月','jiuwudaishi-133-ma-xifan':'卷133·马希范传','xinwudaishi-068-min-mutiny':'卷68·闽世家·宸卫军与政变','xinwudaishi-068-min-pursuit':'卷68·闽世家·追杀王继鹏','xinwudaishi-068-jiye-editorial-note':'卷68·闽世家·王继业亲属校勘注'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type=('reference' if key.endswith('-editorial-note') else 'primary'), author=author, edition=('维基文库固定修订1769092；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/282.txt').read_text().splitlines()
for n in range(28, 33):
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
    labels={'jiuwudaishi-078-august':'卷78·晋高祖纪·天福四年八月','jiuwudaishi-133-ma-xifan':'卷133·马希范传','xinwudaishi-068-min-mutiny':'卷68·闽世家·宸卫军与政变','xinwudaishi-068-min-pursuit':'卷68·闽世家·追杀王继鹏','xinwudaishi-068-jiye-editorial-note':'卷68·闽世家·王继业亲属校勘注'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '闰七月后续及追述' if n<=29 else '八月' if n<=31 else '八月至九月战事'
        citation = f'卷282·后晋天福四年（939；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0939_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'王继隆':'王继鹏的堂弟。《资治通鉴》记他在饮酒时失礼，被王继鹏杀死；此事为此前追述，具体年份未载。生年未载。',
'王延羲':'闽国宗室，王继鹏的叔父，曾任左仆射、同平章事。939年被政变军队拥立，自称威武节度使、闽国王，更名王曦，改元永隆。生卒年暂未核实。',
'朱文进':'永泰人，闽国拱宸军将领。《资治通鉴》记他与连重遇多次受王继鹏侮辱而心怀不满，《新五代史》还记二人因宸卫军待遇优厚而激怒部众。生卒年未载。',
'连重遇':'光山人，闽国控鹤军将领。939年率拱宸、控鹤军起兵攻击王继鹏，拥立王延羲。生卒年未载。',
'陈郯':'闽国内学士。939年私下告诉连重遇，王继鹏怀疑他与纵火有关、想将他杀死。《新五代史》还记他曾受王继鹏亲信。生卒年未载。',
'王继业':'闽国前汀州刺史。939年受王延羲派遣追赶王继鹏，随后将王继鹏带回并杀死。《资治通鉴》称他为王延羲兄长的儿子，《新五代史》称为王延羲之子，亲属异说暂未裁定。生卒年未载。',
'李真':'闽国官员。939年王延羲即位后，将已以太子太傅身份退休的李真任为司空兼中书侍郎、同平章事。生卒年未载。',
'彭士愁':'溪州刺史。939年率蒋州、锦州部众一万多人进攻辰州、澧州，并向后蜀求援，未获同意。生卒年未载。',
'刘勍':'楚国左静江指挥使。939年九月与决胜指挥使廖匡齐率衡山兵五千讨伐彭士愁。生卒年未载。'}
NEW_ALIASES={'王继隆':['王繼隆'],'王延羲':['王曦'],'朱文进':['硃文进','朱文進','硃文進'],'连重遇':['連重遇'],'陈郯':['陳郯'],'王继业':['王繼業'],'李真':[],'彭士愁':[],'刘勍':['劉勍']}

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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=939, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='939年'+('闽国政变期间及其后，具体日期未载' if n==28 else '八月条之前，具体月日未载' if n==29 else '八月，具体日期未载' if n<=31 else '九月楚军出兵之前，具体月日未载')
    key = 'event_zztj_282_0939_' + code
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
        edge = 'participation_zztj_282_0939_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_282_0939_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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




ALIASES.update({'闽惠宗':'王延钧','闽太祖':'王审知','康宗':'王继鹏','闽主':'王继鹏','李后':'李春燕','延羲':'王延羲','曦':'王延羲','继隆':'王继隆','继业':'王继业','硃文进':'朱文进','重遇':'连重遇','元璟':'钱传瓘','元瓘':'钱传瓘','郑王重贵':'石重贵','楚王希范':'马希范','蜀主':'孟昶','林兴':'林兴（闽国巫者）'})
mutiny='xinwudaishi-068-min-mutiny';pursuit='xinwudaishi-068-min-pursuit';aug='jiuwudaishi-078-august';ma='jiuwudaishi-133-ma-xifan'
prior='闽国政变以前的追述，具体年份及日期未载';night='939年闰七月辛巳夜';morning='939年闰七月辛巳夜政变后的次日清晨';after='939年闽国政变后，具体日期未载'
add('min_old_guards','王延钧以王审知的旧部组成拱宸、控鹤军',28,'初，','为拱宸、按鹤都，',[('闽惠宗','将王审知的旧部编成拱宸、控鹤军'),('闽太祖','旧部被编入拱宸、控鹤军')],year=None,when=prior,description='王延钧以王审知的旧部组成拱宸、控鹤两军。所用《资治通鉴》电子本在句首写按鹤，后文写控鹤；展示采用后文及《新五代史》的控鹤名称，原文保留。',note='闽惠宗为王延钧，太祖为王审知；这是军队来源的追述，不把死后的庙号当作当时正式称号，也不认按鹤是另一个军队。')
add('min_chengwei_new_guard','王继鹏另募二千壮士组成宸卫军，给予更厚待遇',28,'及康宗立，','禄赐皆厚于二都；',[('康宗','另募二千壮士为心腹宸卫军，给予更厚禄赐')],year=None,when=prior,description='王继鹏即位后另募二千壮士作为心腹，称宸卫都，禄赐比拱宸、控鹤两军更优厚。',note='康宗是王继鹏后来的庙号；本句追述即位后的安排，不强定为939年首次募兵。')
sup('min_chengwei_new_guard',28,mutiny,'而募勇士為宸衞都以自衞，其賜予給賞，獨厚於佗軍。','《新五代史》也记王继鹏募勇士为宸卫军，待遇高于其他军队。','此书把募兵接在王继严被解除兵权之后，通鉴按即位后追述；各书叙述次序保留，未断定只有一次确日募兵。')
add('min_split_guards_plan','王继鹏听信两军将作乱的说法，打算分派到漳州、泉州',28,'或言二都','二都益怒。',[('闽主','听到两军怨望将作乱的说法，打算将两军分隶漳州、泉州')],year=None,when=prior,place='漳州、泉州',description='有人称拱宸、控鹤军因待遇不满而准备作乱。王继鹏打算将两军分派到漳州、泉州，这让两军更加愤怒。',note='有人说将作乱属于当时传言，分隶是王继鹏的计划；没有记成已经执行调防。')
add('min_night_drinking_spies','王继鹏通宵饮酒、强迫群臣喝酒，并让人寻找他们的过失',28,'闽主好为','伺其过失；',[('闽主','强迫群臣饮酒，等他们醉后让近侍寻找过失')],year=None,when=prior,note='原文是习惯性作风概述；没有补宴饮频次、酒量或未载受害官员姓名。')
add('min_kills_jilong','王继鹏因王继隆醉后失礼，将他杀死',28,'从弟继隆','斩之。',[('闽主','因堂弟王继隆醉后失礼而杀死他'),('继隆','醉后失礼，被王继鹏杀死')],year=None,when=prior,note='从弟按堂弟解释，父亲姓名未载；追述不强定939年死亡。')
relationship('王继隆','王继鹏','堂弟',28,'从弟继隆醉失礼，斩之。','从弟表示同宗旁系较年幼的男性亲属，这里按堂弟记录；没有补其父亲或具体排行。')
add('min_yanxi_feigns_madness','王延羲为躲避王继鹏杀害宗室，装作疯癫',28,'屡以猜怒','以避祸，',[('闽主','因猜忌、愤怒多次杀害宗室'),('延羲','以左仆射、同平章事身份装疯避祸')],year=None,when=prior,description='王继鹏因猜忌、愤怒多次杀害宗室。叔父王延羲当时任左仆射、同平章事，装作疯癫愚钝来避祸。',note='装疯是避祸手段，不确诊精神疾病；未列被杀宗室姓名，不补名单。')
relationship('王延羲','王继鹏','叔父',28,'叔父左仆射、同平章事延羲阳为狂愚以避祸，','王延羲是王继鹏的叔父，关系由叔父指向侄辈；不根据后面的王继业异说添加父子关系。')
add('min_yanxi_wuyi_confinement','王继鹏将王延羲送到武夷山，召回后又关在私宅',28,'闽主赐以','幽于私第。',[('闽主','赐王延羲道士服、送到武夷山，随后召回并幽禁'),('延羲','先被送到武夷山，召回后被幽禁于私宅')],year=None,when=prior,place='武夷山、私宅',note='先送走再召回幽禁的顺序明确；私宅主人和现代位置未载，不补具体地址。')
add('min_guard_commanders_resent','朱文进、连重遇因多次被王继鹏侮辱而怨恨',28,'闽主数侮','二人怨之。',[('闽主','多次侮辱拱宸、控鹤军使'),('硃文进','受王继鹏侮辱而怨恨'),('重遇','受王继鹏侮辱而怨恨')],year=None,when=prior,description='王继鹏多次侮辱拱宸、控鹤军使。永泰人朱文进、光山人连重遇因此心怀怨恨。',note='籍贯按原文保留，没有换成出生坐标；两人军职对应由《新五代史》明确补证。')
sup('min_guard_commanders_resent',28,mutiny,'控鶴都將連重遇、拱宸都將朱文進，皆以此怒激其軍。','《新五代史》明确记连重遇为控鹤都将、朱文进为拱宸都将，并记二人因宸卫军待遇优厚而激怒部众。','补军职对应与激怒部众的行动；侮辱和待遇两种不满来源分别引用，不混为单一动机。',relation='adds')
add('min_clears_fire_debris','王继鹏命连重遇率军清理北宫火灾废墟，士卒不堪重役',28,'会北宫火，','士卒甚苦之。',[('闽主','因北宫起火后未查获纵火嫌疑人，命连重遇率军清理'),('重遇','率内外营兵清理火灾废墟')],when='939年七月北宫火灾后、辛巳政变前，具体日期未载',place='闽国北宫',description='北宫火灾后，没有找到被追查的纵火嫌疑人。王继鹏命连重遇率内外营兵清理废墟，每天役使一万人，士卒深受其苦。',note='求贼不获表示未查获所追查的人，不能据此认定确有纵火者；万人是每日役使人数，未推为固定总兵力。')
add('min_chen_warns_lian','陈郯私下告知连重遇，王继鹏怀疑他知情并想杀他',28,'又疑重遇','私告重遇。',[('闽主','怀疑连重遇知道纵火之谋，想将他杀死'),('陈郯','私下向连重遇通报王继鹏的怀疑和杀人意图'),('重遇','获悉皇帝怀疑自己与纵火有关并想杀自己')],when='939年辛巳政变前，具体日期未载',note='知纵火之谋是王继鹏的怀疑，欲诛是计划；没有写成连重遇已被定罪或已被处死。')
sup('min_chen_warns_lian',28,mutiny,'昶疑重遇軍士縱火。內學士陳郯素以便佞為昶所親信，昶以火事語之，郯反以告重遇。','《新五代史》也记陈郯把王继鹏对连重遇军士的纵火怀疑告诉连重遇，并补陈郯此前受王继鹏亲信。','两书怀疑对象及转告内容详略不同，不能将怀疑当成纵火事实。')
add('min_lian_starts_mutiny','连重遇率两军焚烧长春宫，攻击王继鹏',28,'辛巳夜，','以攻闽主，',[('重遇','值宿时率拱宸、控鹤两军焚烧长春宫并攻击王继鹏'),('闽主','受到连重遇所率军队攻击')],when=night,place='长春宫',note='此次焚宫是原文明确的起兵行动，与此前未查明原因的北宫火灾分开；未补朱文进直接下令纵火。')
sup('min_lian_starts_mutiny',28,mutiny,'重遇懼，夜率衞士縱火焚南宮，','《新五代史》也记连重遇夜间率兵纵火起事，但称被焚为南宫。','《资治通鉴》称长春宫，该书称南宫，两个名称分别保留，未凭名称相近认定全部宫殿都是同一处。',relation='conflicts')
add('min_yanxi_acclaimed','政变军队迎出王延羲，呼喊万岁拥立他',28,'使人迎延羲','呼万岁；',[('重遇','派人迎出王延羲'),('延羲','被军队从瓦砾中迎出并拥立')],when=night,description='连重遇派人从瓦砾中迎出王延羲，军队呼喊万岁，拥立他。',note='欢呼与拥立是本段行动；随后自称节度使、闽国王另录，不把呼万岁直接等同已完成称帝仪式。')
sup('min_yanxi_acclaimed',28,pursuit,'重遇迎延羲立之。','《新五代史》同样记连重遇迎立王延羲。','该书本句简略，未补欢迎人数或具体仪式。')
add('min_chengwei_resists','外营兵加入攻击，王继鹏与李春燕转往宸卫军',28,'复召外营兵','如宸卫都。',[('重遇','召外营兵共同进攻王继鹏'),('闽主','与李春燕转往仍在抵抗的宸卫军'),('李后','与王继鹏转往宸卫军')],when=night,place='宸卫军',description='连重遇又召外营兵共同攻击王继鹏。只有宸卫军抵抗，王继鹏与李皇后李春燕转往宸卫军。',note='李皇后沿此前王继鹏贤妃、皇后李春燕身份复用，不与后晋皇后混淆；没有把他国同称李后者合并。')
add('min_king_flees_wutong','宸卫军战败，王继鹏与李春燕逃到梧桐岭',28,'比明，','众稍逃散。',[('闽主','与李春燕在宸卫余众保护下出北关，逃到梧桐岭'),('李后','随王继鹏逃到梧桐岭')],when=morning,place='北关、梧桐岭',description='次日清晨，政变军队焚烧宸卫军驻地，宸卫军战败。一千多名余众护送王继鹏和李春燕出北关，到了梧桐岭后，士卒渐渐逃散。',note='比明按起兵夜后的清晨解释，不补公历日期；逃散是逐渐过程，没有写作全部当即逃走。')
add('min_jiye_pursues','王延羲派王继业追赶王继鹏，在村舍追上',28,'延羲使兄子','及于村舍；',[('延羲','派前汀州刺史王继业率兵追赶王继鹏'),('继业','率兵在村舍追上王继鹏'),('闽主','在村舍被追兵赶上')],when='939年闽国政变逃亡期间，具体日期未载',place='村舍',description='王延羲派前汀州刺史王继业率兵追赶王继鹏，在村舍追上。《资治通鉴》称王继业为王延羲兄长的儿子，《新五代史》称为他的儿子，两书亲属记载有异。',note='追赶行动明确，亲属身份有异说；不据其中一种直接创建确定父子关系，也未补村名。')
sup('min_jiye_pursues',28,pursuit,'延羲令其子繼業率兵襲昶，[3]及之；','《新五代史》也记王继业奉王延羲命追袭王继鹏，但称王继业为王延羲之子。','《资治通鉴》称兄子，两书亲属异说并列；电子本脚注标记[3]保留，未冒充已核纸本。',relation='conflicts')
claim('person',people['王继业'],'description','王继业的亲属身份有异说：《资治通鉴》称王延羲兄长之子，《新五代史》称王延羲之子。',28,'延羲使兄子前汀州剌史继业将兵追之，及于村舍；','只明确异说，不添加未经裁定的父子关系。')
claim('person',people['王继业'],'description','所用《新五代史》电子本的校勘注也指出，通鉴称王继业为王延羲兄长之子，并转引另书称从子。',28,(sources['xinwudaishi-068-jiye-editorial-note']/'source.txt').read_text().strip(),'这是电子本校勘注，不是欧阳修正文；所转引《十国春秋》未在本次直接校核，因此不作为新增独立书证。亲属异说继续保留，未建确定父子关系。',source='xinwudaishi-068-jiye-editorial-note',relation='adds')
add('min_king_shoots_pursuers','王继鹏射杀数名追兵，随后弃弓质问王继业',28,'闽主素善射，','卿臣节安在！”',[('闽主','射杀数名追兵，见追兵聚集后弃弓质问王继业'),('继业','受到王继鹏关于臣节的质问')],when='939年闽国政变追杀期间，具体日期未载',description='王继鹏善射，持弓射杀数人。追兵随后聚集，他知道难以逃脱，弃弓质问王继业为何不守臣节。',note='素善射是以往技能背景，射杀及弃弓是本次行动；数人未给精确人数，不补数字。')
add('min_jiye_replies_loyalty','王继业以君主无德回应王继鹏，并辩称新旧君都是亲族',28,'继业曰：','闽主不复言。',[('继业','以君主无德回应臣节质问，称新君是叔父、旧君是昆弟'),('闽主','听王继业回应后不再说话')],when='939年闽国政变追杀期间，具体日期未载',description='王继业回答，君主没有君德，臣子也就没有臣节。他又称新君是叔父、旧君是昆弟，反问谁亲谁疏。王继鹏不再说话。',note='这是王继业的辩解，不作为网站的道德裁断；昆弟与叔父称谓保留在言论证据中，亲属异说未裁定，不补具体长幼链。')
add('min_king_strangled','王继业将王继鹏带到陀庄，趁他酒醉绞死',28,'继业与之俱还，','醉而缢之，',[('继业','将王继鹏带到陀庄，给他喝酒，趁他醉后绞死'),('闽主','在陀庄醉后被王继业绞死')],when='939年闽国政变期间，具体日期未载',place='陀庄',note='明确杀死行动及方式，不说王继鹏自然病死或阵亡；未把投弓直接翻成自杀。')
sup('min_king_strangled',28,pursuit,'繼業執而殺之，','《新五代史》同样记王继业抓住并杀死王继鹏。','该书没有本句中的酒醉、绞杀细节，死亡方式仍依《资治通鉴》。')
claim('person',people['王继鹏'],'death_year','939年闽国政变中，王继鹏被王继业杀死。',28,span(28,'继业与之俱还，','醉而缢之，'),'新增死亡出处，原已发布人物档案保持不变。')
add('min_queen_family_die','李春燕、王继鹏的儿子及王继恭同时遇害',28,'并李后','王继恭皆死。',[('李后','在王继鹏被杀时同时遇害'),('王继恭','在王继鹏被杀时同时遇害')],when='939年闽国政变期间，具体日期未载',description='李皇后李春燕、王继鹏的儿子，以及王继恭，都在这次追杀中死亡。',note='本句皆死未逐人交代执行者与死法，不将王继鹏的绞杀方式自动套给所有人。诸子未具名，不增匿名人物。')
sup('min_queen_family_die',28,pursuit,'及其妻、子皆死無遺類。','《新五代史》同样记王继鹏妻子、子女全部被杀。','妻子身份沿既有李春燕，子女本句未具名；不据概述造完整死者名单。')
add('min_survivors_wuyue','宸卫军残余部众逃往吴越',28,'宸卫馀众','奔吴越。',[],when='939年闽国政变后，具体日期未载',place='吴越',note='逃往吴越的余众人数本句未载，不套用之前一千多人护驾的数字。')
add('min_yanxi_titles_renames','王延羲自称威武节度使、闽国王，改名王曦',28,'延羲自称','更名曦，',[('延羲','自称威武节度使、闽国王，并改名王曦')],when=after,note='自称是当事人采用的头衔，不写成后晋已正式册封；更名沿同一稳定人物，未新增王曦主体。')
claim('person',people['王延羲'],'aliases','939年即位后，王延羲更名王曦。',28,'延羲自称威武节度使、闽国王，更名曦，','名字变化有主书明文，王曦作为别名保留。')
add('min_yanxi_yonglong_amnesty','王延羲改元永隆、赦免囚犯，并颁发赏赐',28,'改元永隆，','颁赉中外。',[('延羲','改元永隆、赦免在押囚犯并颁发赏赐')],when=after,note='只录所载改元、赦囚和赏赐，不补赦免范围、发放数额或未载仪式。')
add('min_blames_chengwei','王延羲向邻国宣称宸卫军杀死王继鹏',28,'以宸卫弑','赴于邻国；',[('延羲','向邻国通报，声称宸卫军杀死王继鹏')],when=after,description='王延羲向邻国通报王继鹏之死，将弑君归到宸卫军名下。',note='这是对外通报的说法，与前文王继业追杀记载分开；不写成宸卫军已经被查实为杀害者。')
add('min_king_posthumous_honors','王延羲为王继鹏加谥号，定庙号康宗',28,'谥闽主曰','庙号康宗。',[('延羲','为王继鹏追定谥号、庙号'),('闽主','被追谥，庙号康宗')],when=after,description='王延羲为王继鹏追谥为圣神英睿文明广武应道大弘孝皇帝，庙号康宗。',note='谥号与庙号明确区分，使用主书用语；《新五代史》本处的谥昶曰康宗说法另列，不混成同一种号。')
sup('min_king_posthumous_honors',28,pursuit,'延羲立，謚昶曰康宗。','《新五代史》在此写王延羲即位后谥王昶为康宗，《资治通鉴》则明确把康宗列为庙号。','王昶沿王继鹏的既有别名；谥、庙号用语差异保留，不覆盖主书记录。',relation='conflicts')
add('min_yanxi_submits_jin','王延羲派商人秘密向后晋递表称藩',28,'遣商人','称籓于晋；',[('延羲','派商人沿小道向后晋递表称藩')],when=after,note='递表称藩是本句实际外交行动，商人未具名；本句未载后晋接受或正式册封的结果。')
add('min_yanxi_imperial_offices','王延羲在国内按天子制度设置百官',28,'然其在国，','皆如天子之制。',[('延羲','在国内按天子制度设置百官')],when=after,description='王延羲向后晋称藩，但在闽国内按天子制度设置百官。',note='这是国内官制安排，不把前面自称闽国王直接升级为已经在本次正式称帝。')
add('min_li_zhen_chancellor','王延羲任李真为司空兼中书侍郎、同平章事',28,'以太子太傅','同平章事。',[('延羲','任已退休的李真为司空兼中书侍郎、同平章事'),('李真','由太子太傅致仕重新获任司空兼中书侍郎、同平章事')],when=after,note='太子太傅致仕是任命前的身份，新官命按本句录；不补同名他国官员关系。')
add('min_chen_shouyuan_killed','陈守元在宫中换装准备逃跑，被士兵杀死',28,'连重遇之攻康宗也，','兵人杀之。',[('陈守元','在宫中换装准备逃跑，被士兵杀死')],when='939年连重遇攻击王继鹏期间，具体日期未载',place='闽国宫中',note='欲逃不等于已经逃离，杀人军士未具名，不直接归给王继业或王延羲。')
claim('person',people['陈守元'],'death_year','939年连重遇攻击王继鹏时，陈守元被宫中士兵杀死。',28,span(28,'连重遇之攻康宗也，','兵人杀之。'),'仅新增死亡事实出处，不修改此前原始批次。')
add('min_cai_shoumeng_executed','连重遇抓住蔡守蒙，以卖官罪名将他斩杀',28,'重遇执蔡守蒙，','斩之。',[('重遇','抓住蔡守蒙，指责他卖官并将他斩杀'),('蔡守蒙','被连重遇以卖官罪名斩杀')],when='939年闽国政变期间，具体日期未载',note='卖官罪名是连重遇指责的内容；抓捕及斩杀已发生，但不补审判程序、账目和数额。')
claim('person',people['蔡守蒙'],'death_year','939年闽国政变中，蔡守蒙被连重遇斩杀。',28,'重遇执蔡守蒙，数以卖官之罪而斩之。','人物沿既有蔡守蒙主体，原文无死亡月日。')
add('min_lin_xing_killed','王延羲即位后，派人到泉州杀死林兴',28,'闽王曦既立，',None,[('曦','即位后派人诛杀林兴'),('林兴','在泉州被王延羲派人杀死')],when=after,place='泉州',note='前段六月记流放泉州，本段明确王延羲即位后派人诛杀，因此可补先流放、后被杀的顺序；具体死亡月日未载。')
claim('person',people['林兴（闽国巫者）'],'death_year','939年王延羲即位后，林兴在泉州被杀。',28,'闽王曦既立，遣使诛林兴于泉州。','死亡年依据本年即位后的明确行动，未补确日；旧档案未知死亡年的字段不直接覆盖。')
add('bozhou_river_breach','亳州发生河道决口',29,'河决',None,[],when='939年八月条之前，具体月日未载',place='亳州',description='《资治通鉴》记，亳州发生河道决口。',note='本段只写河决亳州，未展开具体河道位置和灾情；不与旧史八月博平决河、甘陵大水自动合并，未补古河道坐标。')
add('feng_situ_shizhong','石敬瑭任冯道为守司徒兼侍中',30,'八月，','守司徒兼侍中。',[('帝','任冯道为守司徒兼侍中'),('冯道','获任守司徒兼侍中')],when='939年八月辛丑',note='守为官衔用语，未据此推代理时长；官职与次日掌印权限分录。')
sup('feng_situ_shizhong',30,aug,'辛丑，以守司空兼門下侍郎、平章事、宏文館大學士馮道為守司徒、兼侍中，封魯國公。','《旧五代史》同记八月辛丑冯道任守司徒兼侍中，并补封鲁国公。','本条补封爵和此前官衔，不把鲁国公视为拥有独立国家。',relation='adds')
add('feng_controls_seal','石敬瑭规定中书印只交首相掌管，政务集中到冯道',30,'壬寅，','悉委于道。',[('帝','规定中书印只委首相掌管'),('冯道','以首相身份掌印，受托处理政务')],when='939年八月壬寅',description='石敬瑭下诏，中书印只交首相掌管。《资治通鉴》记，此后不论大小事务，都交给冯道处理。',note='上相按首相身份解释；大小事务悉委是史书概述，不推皇帝从此完全不再决策。')
sup('feng_controls_seal',30,aug,'壬寅，詔曰：「皇圖革故，庶政惟新，宜設規程，以諧公共。其中書印只委上位宰臣一人知當。」','《旧五代史》也记八月壬寅将中书印只交给居首位的宰臣掌管。','诏文印证掌印规定，没有扩大为废除其他宰相官职。')
add('feng_declines_military_advice','石敬瑭问冯道军事谋略，冯道请皇帝自行决定征伐',30,'帝尝访','帝以为然。',[('帝','向冯道询问军谋，并认可他的回答'),('冯道','表示征伐应由皇帝决定，自己只守历代成规')],year=None,when='冯道受石敬瑭信任期间的轶事，具体年份及日期未载',note='尝为轶事追述，未强定八月壬寅当天；回答是本人表态，未补未载军事方案。')
add('feng_returns_to_office','冯道称病求退，石敬瑭派石重贵探望并促他处理政务',30,'道尝称疾','道乃出视事。',[('冯道','称病求退，得到皇帝慰问后重新处理政务'),('帝','派石重贵探望冯道，并表示将亲自前往'),('郑王重贵','奉命到冯道宅第探望')],year=None,when='冯道受石敬瑭信任期间的轶事，具体年份及日期未载',description='冯道曾称病请求退职。石敬瑭派郑王石重贵到他宅第探望，并传话说，如果冯道次日仍不出，皇帝就亲自前往。冯道随后重新处理政务。',note='称病不是已确诊疾病，请退没有变成获准退休；帝表示将往，不等于实际亲自到访。')
add('feng_exceptional_favor','史书记述冯道受到的宠遇超过当时其他群臣',30,'当时宠遇，',None,[('冯道','被史书记为受到格外宠遇')],year=None,when='冯道受石敬瑭信任期间的概述，具体年份及日期未载',description='《资治通鉴》评价，冯道当时得到的宠遇，其他群臣无人可比。',note='这是一句史书比较评价，不创建未具名群臣关系，也不视作可以量化的待遇统计。')
add('qian_marshal','石敬瑭任钱传瓘为天下兵马元帅',31,'己酉，',None,[('帝','任吴越王钱传瓘为天下兵马元帅'),('元璟','获任天下兵马元帅')],when='939年八月己酉',description='石敬瑭任吴越王钱传瓘为天下兵马元帅。《资治通鉴》所用电子本此处写元璟，《旧五代史》同日官命明确写钱元瓘，沿用已核钱传瓘主体。',note='同日、同封号、同授职由旧史补证，元璟保留在引用中作为字形问题，不建立钱元璟新人或新增未经核实的别名。')
sup('qian_marshal',31,aug,'己酉，以天下兵馬副元帥、鎮海鎮東等軍節度使、檢校大師、行中書令、吳越王錢元瓘為天下兵馬元帥。','《旧五代史》明确记八月己酉吴越王钱元瓘由天下兵马副元帅升为天下兵马元帅。','钱元瓘沿既有钱传瓘身份复用；副元帅至元帅是官衔变化，不表示实际统率后晋所有军队。',relation='adds')
add('peng_attacks_chen_li','彭士愁率一万多人攻辰州、澧州，焚烧掠夺驻防设施',32,'黔南巡内','焚掠镇戍，',[('彭士愁','以溪州刺史身份率蒋州、锦州部众一万多人进攻辰州、澧州')],place='辰州、澧州',description='溪州刺史彭士愁率蒋州、锦州部众一万多人进攻辰州、澧州，并焚烧、掠夺当地驻防设施。',note='族群称谓在原文保留，展示写部众，没有替换为未经校核的现代民族；一万多人不是一万整。')
sup('peng_attacks_chen_li',32,ma,'谿州洞蠻彭士愁寇辰、澧二州，','《旧五代史》马希范传也记彭士愁进攻辰州、澧州。','谿与溪按地名字形识别；此处只印证进攻，后面的讨平和乞盟结果留待对应连续段落处理。')
add('peng_shu_aid_refused','彭士愁向后蜀求援，孟昶因路远拒绝',32,'遣使乞师','不许。',[('彭士愁','派使者向后蜀请求援军'),('蜀主','认为路途太远，拒绝出兵')],note='求援及拒绝分清结果，不把孟昶写成已与彭士愁结盟或已经派兵。')
add('ma_sends_liu_liao','马希范派刘勍、廖匡齐率五千衡山兵讨伐彭士愁',32,'九月，',None,[('楚王希范','派刘勍、廖匡齐率五千衡山兵讨伐彭士愁'),('刘勍','以左静江指挥使身份率军出征'),('廖匡齐','以决胜指挥使身份率军出征'),('彭士愁','成为楚军讨伐对象')],when='939年九月辛未',place='衡山、辰州、澧州',note='五千是两将所率衡山兵的合计，不给每人各配五千；命令与出兵已记，战果本句未载。')
reviews={28:'逐项处理军队背景、待遇差异、调防计划、宴饮及王继隆被杀、王延羲避祸、将领怨恨、火后重役、告密、起兵拥立、抵抗逃亡、追杀对话、王继鹏及家属死亡、残部出逃、新君称号改元、对外死因说法、谥庙号、称藩与官制、李真任官和陈守元蔡守蒙林兴被杀。此前追述不强定939年，辛巳夜与次日清晨分开；北宫火原因未查、长春宫纵火明确。王继业兄子与其子异说未裁定，不建确定父链；按鹤/控鹤、南宫/长春宫与谥庙号用语保留。林兴死亡补前段先流后杀顺序。',29:'亳州决河未记确日，不与旧史八月博平、甘陵水灾合并，不补古河道坐标。',30:'八月辛丑任冯道守司徒侍中与壬寅委首相掌印分日处理，旧史补封鲁国公。军谋、称疾慰问和宠遇为轶事概述，尝不强定八月；欲亲往不当已到访，求退未当获准退休。',31:'吴越王元璟电子本字形保留；同日旧史钱元瓘官命确认钱传瓘稳定主体，元帅封号不当实际全国统军。',32:'彭士愁攻辰澧、向蜀求援未获准、九月辛未楚两将率五千出兵分别记，前两事确日未载；族群不推现代民族，旧史只补进攻，不提前把未来平叛乞盟录成本段战果。'}
assert not (P/'publication.json').exists()
for n in range(28,33):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n');(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=939,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(28,33)],next_paragraph=Q[33]['id'],next_volume=282,next_year=939,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第28—32段，原33—37行，闽国政变及八月至九月政事；939年剩余9段待录。',source_issues_review='王继业兄子与其子异说未裁定；按鹤/控鹤、南宫/长春宫、谥康宗/庙号康宗和吴越王元璟/元瓘按各书保留。林兴本段死亡明确发生于王延羲即位后，补前段流放后的顺序。纸本和版本异文仍待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(28,33)],plain_language_review='首次逐条检查标题、人物介绍、事件说明、角色、关系、时间地点和事实说明；各条具明确主语，引用保持原字。背景追述、传言、猜疑、计划、政治辩解、史书评价与实际行动分别表达；未把异说合成唯一结论。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
