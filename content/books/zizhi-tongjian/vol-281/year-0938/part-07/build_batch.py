# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 938 paragraphs 36–42."""
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
specs=[(d.name,d,'38057258b21c79a77db1740bb23708c7e75c602c','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修、宋祁' if d.name.startswith('xintangshu') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-938-late-year','jiuwudaishi-077-november']:
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
main_sources = ['tongjian-281-938-late-year']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0938-p036-p042',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-077-october':'卷77·晋高祖纪·天福三年十月','jiuwudaishi-077-november':'卷77·晋高祖纪·天福三年十一月','jiuwudaishi-077-december':'卷77·晋高祖纪·天福三年十二月','jiuwudaishi-088-wang-tingyin':'卷88·王庭胤传','xinwudaishi-062-yang-pu':'卷62·南唐世家'}
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
for n in range(36, 43):
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
    labels={'jiuwudaishi-077-october':'卷77·晋高祖纪·天福三年十月','jiuwudaishi-077-november':'卷77·晋高祖纪·天福三年十一月','jiuwudaishi-077-december':'卷77·晋高祖纪·天福三年十二月','jiuwudaishi-088-wang-tingyin':'卷88·王庭胤传','xinwudaishi-062-yang-pu':'卷62·南唐世家'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '十一月条下，含追述' if n<39 else '年末，未重列月份'
        citation = f'卷281·后晋天福三年（938；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0938_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'刘继勋':'汲县人，曾任淄州刺史。938年受石敬瑭派遣，将澶州迁到跨德胜津的位置，并迁移顿丘。生卒年未载。',
'王廷胤':'王处存的孙子，曾任贝州防御使。938年任彰德军节度使。《旧五代史》传记作王庭胤，记他字绍基，祖籍长安；同一传记及任官纪事又作王庭允。',
'王景（后晋耀州团练使）':'掖县人，曾任相州刺史。范延光叛乱时，他拒绝服从范延光。938年任耀州团练使。生卒年未载。',
'张彦泽':'太原人，938年任镇国军节度使，在华州截击并杀死东行的凤翔叛军。生卒年本段未载。'}
NEW_ALIASES={'刘继勋':['劉繼勳'],'王廷胤':['王庭胤','王庭允'],'王景（后晋耀州团练使）':['王景'],'张彦泽':['張彥澤']}

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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name in ['杨嗣复','萧仿'] else '五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=938, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='938年十一月条下，具体日期未载' if n<39 else '938年年末，主书未列具体日期'
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




ALIASES.update({'唐主':'李昪','唐王':'李昪','吴让皇':'杨溥','璟':'李璟','重贵':'石重贵','王景':'王景（后晋耀州团练使）','李从\ue4be严':'李继曮','从\ue4be严':'李继曮'})
nov='jiuwudaishi-077-november';dec='jiuwudaishi-077-december';bio='jiuwudaishi-088-wang-tingyin';nan='xinwudaishi-062-yang-pu'
add('sang_divide_tianxiong','桑维翰建议拆分天雄军兵力，以限制杨光远',36,'帝患','之众，',[('帝','担忧杨光远跋扈难以控制'),('桑维翰','建议拆分天雄军兵力'),('杨光远','受到拆分军队的建议针对')],description='石敬瑭担忧天雄节度使杨光远跋扈、难以控制。桑维翰建议拆分天雄军的兵力。',note='这是建议与动机；后面的设置军镇另录，不把建议本身当已经执行。')
add('yang_luoyang_heyang','石敬瑭加杨光远太尉，任西京留守兼河阳节度使',36,'加光远','河阳节度使。',[('帝','任命杨光远并加太尉'),('杨光远','任西京留守兼河阳节度使，加太尉')],place='西京、河阳')
sup('yang_luoyang_heyang',36,nov,source_span(nov,'楊光遠為守太尉','判六軍諸衛事。'),'《旧五代史》记杨光远任守太尉、洛京留守兼河阳节度使，并判六军诸卫事。','该条接十一月戊申任官记载。西京与洛京名称各依底本，不另造第二次任命。')
add('yang_complains_liao','杨光远因调任不满，私下送礼向契丹申诉',36,'光远由是','于契丹，',[('杨光远','因调任不满，私下以礼物向契丹申诉')],year=None,when='调任西京之后，具体年月未载',note='由是是叙事因果，未明确这次秘密申诉的日期；契丹受礼者未具名，不凭国君身份新增个人参与。')
add('yang_private_troops','史书记述杨光远养私兵千余人，并有异志',36,'养部曲','常蓄异志。',[('杨光远','养私兵千余人，被史书认为有异志')],year=None,when='调任西京后的追述，具体起止年月未载',description='《资治通鉴》记杨光远养私兵一千多人，并一直怀有异志。',note='这是持续行为和史书判断，不能据此录成938年已经发动另一场叛乱。')
add('guangjin_yedu','石敬瑭在广晋府设置邺都',36,'辛亥，','广晋府，',[('帝','在广晋府设置邺都')],when='938年十一月辛亥',place='广晋府')
sup('guangjin_yedu',36,nov,'辛亥，升廣晉府為鄴都，置留守。','《旧五代史》也记十一月辛亥升广晋府为邺都，并设置留守。','升府及设留守为同一制度安排，不与后面的任命高行周混成同一身份。')
add('zhangde_territory','石敬瑭在相州设置彰德军，辖澶州和卫州',36,'置彰德军','以澶、卫隶之；',[('帝','在相州设置彰德军，划入澶州、卫州')],when='938年十一月辛亥',place='相州、澶州、卫州')
add('yongqing_territory','石敬瑭在贝州设置永清军，辖博州和冀州',36,'置永清军','以博、冀隶之。',[('帝','在贝州设置永清军，划入博州、冀州')],when='938年十一月辛亥',place='贝州、博州、冀州')
add('liu_moves_chanzhou','石敬瑭派刘继勋迁澶州到德胜津，同时迁顿丘',36,'澶州旧治','并顿丘徙焉。',[('帝','担忧契丹造成长远威胁，派刘继勋迁澶州及顿丘'),('刘继勋','以原淄州刺史身份受命迁澶州和顿丘')],place='澶州、顿丘、德胜津',description='澶州原治顿丘。石敬瑭担忧契丹造成长远威胁，派汲县人、原淄州刺史刘继勋，将澶州迁到跨德胜津的位置，同时迁移顿丘。',note='原文说跨德胜津，不仅是迁到某个现代城市；不补现代坐标或跨河城墙结构。')
sup('liu_moves_chanzhou',36,nov,'其澶州仍升為防禦州，移於德勝口為治所。','《旧五代史》补记澶州为防御州，迁到德胜口。','德胜口与德胜津依各书保留；不据一句话推完整迁城路线。')
add('gao_yedu_liushou','高行周任广晋尹、邺都留守',36,'以河南尹','鄴都留守，',[('帝','任高行周为广晋尹、邺都留守'),('高行周','从河南尹任广晋尹、邺都留守')],place='广晋府、邺都')
sup('gao_yedu_liushou',36,nov,'以西京留守高行周為廣晉尹、鄴都留守；','《旧五代史》也记高行周任广晋尹、邺都留守，但将其原职记为西京留守。','《资治通鉴》原职为河南尹，两书职称并列保留，不建立两个同名人物。',relation='conflicts')
add('wang_zhangde','王廷胤从贝州防御使任彰德节度使',36,'贝州防御使','彰德节度使，',[('帝','任王廷胤为彰德节度使'),('王廷胤','从贝州防御使任彰德节度使')],place='贝州、相州')
sup('wang_zhangde',36,nov,source_span(nov,'廣晉府行營中軍使','充相州彰德軍節度使；'),'《旧五代史》记王庭允原为广晋府行营中军使、贝州防御使，加检校太傅，任相州彰德军节度使。','王庭允与本传王庭胤的贝州防御、平魏赏劳和相州任官相合；沿主书展示王廷胤，登记各书姓名异字。')
sup('wang_zhangde',36,bio,source_span(bio,'國初，','尋移鎮定州。'),'《旧五代史》王庭胤传记其参与讨范延光，兼贝州防御使，平定后任相州节度使。','本传同段又作庭允，与帝纪相州任官及主书祖父处存相合；后来的定州调任不强定为本次同日。')
add('wang_zhou_yongqing','王周任永清军节度使',36,'右神武统军','永清节度使。',[('帝','任王周为永清军节度使'),('王周','从右神武统军任永清节度使')],place='贝州')
relationship('王处存','王廷胤','祖父',36,'廷胤，处存之孙；','处存是王廷胤的祖父，方向依据明确孙关系；不凭祖孙关系猜未载父亲。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','《旧五代史》王庭胤传记其祖父为定州节度使王处存。',36,'祖處存，定州節度使。','本传开头承接王庭胤，与主书祖孙身份相合。',source=bio,relation='corroborates')
claim('person',people['王廷胤'],'aliases','《旧五代史》本传作王庭胤，字绍基；本传下文与帝纪又作王庭允。',36,'王庭胤，字紹基，其先長安人也。','同传字形和相州任官上下文用于识别，不把同名异字机械拆成新人。',source=bio)
claim('person',people['王周'],'description','王周是邺都人。',36,'周，鄴都人也。','沿用已有王周主体，不改变已有生卒年。')
add('fan_repeated_retirement','范延光多次请求退休',37,'范延光','屡请致仕，',[('范延光','多次请求退休')],year=None,when='获准退休之前，多次请求的起止日期未载',note='屡请与甲寅获准分开；未写每次都获准。')
sup('fan_repeated_retirement',37,nov,'庚戌，鄆州範延光上表乞休退，詔不允。','《旧五代史》补记十一月庚戌范延光请求退休，当时没有获准。','这是早于甲寅准退休的一次申请；不把两次决定写成同日自相矛盾。')
add('fan_retires_taizi','石敬瑭准范延光以太子太师身份退休',37,'甲寅，','以太子太师致仕，',[('帝','准范延光以太子太师身份退休'),('范延光','获准以太子太师身份退休')],when='938年十一月甲寅')
sup('fan_retires_taizi',37,nov,'甲寅，以範延光為太子太師致仕。','《旧五代史》也记十一月甲寅范延光以太子太师身份退休。','致仕为退休，不误作仍以太子太师主持军镇。')
add('fan_bian_banquets','范延光退休后住大梁，参加宴会仍按群臣待遇',37,'居于大梁，','与群臣无异。',[('范延光','退休后住大梁，参加朝廷宴会')],year=None,when='范延光退休之后，具体起止年月未载',place='大梁',note='每预宴会是持续待遇，不按甲寅当天的一次宴会处理。')
add('wang_jing_refuses_fan','王景在范延光叛乱时拒绝服从',37,'延光之反也，','拒境不从，',[('范延光','叛乱时未获相州刺史王景服从'),('王景','以相州刺史身份拒绝服从范延光')],year=None,when='范延光叛乱时的追述，本句未列具体年月',place='相州',note='王景为掖县人，身份与王景仁、王景崇等不同；拒境不从不扩写具体交战伤亡。')
add('wang_jing_yaozhou','石敬瑭任王景为耀州团练使',37,'戊午，',None,[('帝','任王景为耀州团练使'),('王景','任耀州团练使')],when='938年十一月戊午',place='耀州')
add('coinage_permit_standard','石敬瑭准公私铸铜钱，规定十钱重一两并禁掺铅铁',38,'癸亥，','为文。',[('帝','准公私铸铜钱，并规定钱重、材质和钱文')],when='938年十一月癸亥',description='石敬瑭允许官府和民间铸铜钱，禁止掺杂铅铁，规定每十枚钱重一两。钱文按《旧五代史》记为“天福元宝”；《资治通鉴》所用电子本此处作“天福无宝”，字形差异保留。',note='钱文展示依据独立旧史，主书原字不改；十钱一两不换算现代克数。')
sup('coinage_permit_standard',38,nov,'詔許天下私鑄錢，以「天福元寶」為文。','《旧五代史》也记准许私铸钱，钱文为“天福元宝”。','本条承十一月癸亥；主书电子本作天福无宝，展示说明两种字形，底本保留待纸本校核。',relation='conflicts')
add('coinage_molds_copperware','石敬瑭命盐铁机构颁发钱模，禁止私造铜器',38,'仍令盐铁',None,[('帝','命盐铁机构颁发钱模，禁止私造铜器')],when='938年十一月癸亥',note='模范按铸钱模型理解，不把禁私造铜器误写为禁一切私铸铜钱。')
add('shi_chonggui_zheng_kaifeng','石重贵获封郑王，任开封尹',39,'立右金吾卫',None,[('帝','封石重贵为郑王，任开封尹'),('重贵','以右金吾卫上将军身份获封郑王，任开封尹')],place='开封',note='主书未单列日期；旧史补十二月丙子。已有石重贵主体及家庭关系沿用，不增加推测的亲属关系。')
sup('shi_chonggui_zheng_kaifeng',39,dec,'以皇太子右金吾衛上將軍重貴為檢校太傅、開封尹，封鄭王，加食邑三千戶。','《旧五代史》在十二月丙子条记石重贵任检校太傅、开封尹，封郑王，加食邑三千户。','本句接丙子条，补任官封爵日期与职衔；本次不依据句首皇太子字样推断当时正式储位。',field='time_original')
add('coinage_weight_relaxed','石敬瑭因铜难取得，允许铸钱重量灵活掌握',40,'庚辰，',None,[('帝','因铜难取得，允许铸钱重量从便，但须铸造完整')],when='938年年末庚辰，主书未重列月份',description='石敬瑭此前已准公私铸钱，后来考虑到铜难以取得，允许铸钱轻重灵活掌握，但要求钱币没有缺漏。',note='轻重从便是放宽钱重要求，缺漏指铸造完整性；不推出已经废除所有材质限制。')
sup('coinage_weight_relaxed',40,dec,'是日，詔：「宜令天下無問公私，應有銅欲鑄錢者，一任取便酌量輕重鑄造。」','《旧五代史》在十二月戊寅条记允许公私自行酌量轻重铸钱。','该句是日承十二月戊寅；《资治通鉴》作庚辰，两书记日不同，不自行统一。',relation='conflicts',field='time_original')
add('yang_pu_dies','吴让皇杨溥去世',41,'辛丑，','吴让皇卒。',[('吴让皇','去世')],when='938年年末辛丑，主书未重列月份',note='吴让皇为已经禅位的杨溥，沿用既有人物；死因和本句死亡地点未载。')
sup('yang_pu_dies',41,nan,'楊溥卒於丹陽宮。','《新五代史》南唐世家补记杨溥死于丹阳宫。','此句本身未载月日，只补地点，不从其他上下文推精确死亡日期或死因。')
claim('person',people['杨溥'],'death_year','《资治通鉴》在938年年末条记杨溥去世。',41,'辛丑，吴让皇卒。','保留主书年度归属与具体纪日，未覆盖已有公开人物档案。')
add('li_bian_mourns_yang','李昪为杨溥停朝二十七天，追谥睿皇帝',41,'唐王废朝','睿皇帝。',[('唐王','为杨溥停朝二十七天，追谥睿皇帝'),('吴让皇','死后被追谥睿皇帝')],description='杨溥去世后，南唐君主李昪停止朝会二十七天，并追谥杨溥为睿皇帝。',note='李昪本年尚用徐诰姓名，沿统一主体；废朝不是废除朝廷，未推停朝结束的公历日期。')
add('li_jing_qiwang','李昪将李璟从吴王改封为齐王',41,'是岁，',None,[('唐主','将李璟从吴王改封为齐王'),('璟','从吴王改封为齐王')],when='938年，具体日期未载',note='是岁只标本年，不按前一辛丑日认定改封日期。')
add('li_congyan_policy_resentment','史书记述李从曮厚待文士农民，对武人和士卒苛严',42,'凤翔节度使','由是将士怨之。',[('李从\ue4be严','被史书记述厚待文士、爱护农民，但轻视武人、严待士卒')],year=None,when='凤翔兵变之前的追述，具体起止年月未载',place='凤翔',description='《资治通鉴》记凤翔节度使李从曮厚待文士、轻视武人，爱护农民、严待士卒，因此将士对他不满。',note='李从私用字严沿既有李继曮主体和李从曮别名，不另造新人；政策因果是史书记述。')
add('fengxiang_mutiny','凤翔出征士卒在郊外兵变，回城抢掠市场',42,'会发兵','剽掠于市。',[('李从\ue4be严','所辖士卒出征西边时发生兵变')],place='凤翔',description='凤翔派兵到西部边境戍守，士卒出城后作乱，又冲进城门，抢掠市场。',note='戌西边据出兵语境按戍守说明，底本字保留；匿名乱军不编将领姓名。')
add('li_congyan_counterattack','李从曮派帐下兵攻击叛军，叛军随后东行',42,'从\ue4be严发','东走，',[('从\ue4be严','派帐下兵攻击叛军')],place='凤翔',description='李从曮派帐下兵攻击叛军，叛军随后向东逃走。',note='电子本乱兵帐字义不通，留待版本校核；只录明确的攻击与后续东走，不猜改原字或扩大具体战果。')
add('zhang_yanze_kills_mutineers','凤翔叛军想向朝廷申诉，在华州被张彦泽截杀',42,'欲自诉',None,[('张彦泽','以镇国节度使身份，在华州截击并杀死东行叛军')],place='华州',description='叛军向东行进，想向朝廷申诉。到华州后，太原人、镇国节度使张彦泽截击他们，史书称这些叛军全部被杀。',note='欲自诉是意图，未记已经见到朝廷；尽诛不编叛军数量或扩大为凤翔全部士卒。')
reviews={36:'分军建议、杨光远调任、怨望私兵、邺都及两军辖州、迁澶州顿丘和三人任官分别记录。王廷胤与旧史庭胤、庭允依祖父和贝州相州经历识别；高行周原职异记保留。',37:'申请退休与获准分开，旧史庚戌不允补证。居大梁宴会待遇为持续追述；王景掖县相州身份与其他同名人物区别。',38:'准公私铸钱与禁私作铜器区分，十钱一两不换现代单位；钱文无宝、元宝底本异字保留。',39:'石重贵既有主体复用，主书日期未载，旧史十二月丙子与职衔食邑独立补充，不推正式太子身份。',40:'放宽铸钱重量与铜材短缺动机清楚；主庚辰、旧十二月戊寅并列，不强行统一。',41:'杨溥死亡、李昪停朝追谥、李璟改封分别记录；新史补丹阳宫。是岁改封不强系死亡日。',42:'李从私字严复用李继曮，张彦泽太原镇国身份单独识别；政策评价与兵变、反击东走、截杀分开。乱兵帐保留待校，未猜具体胜败细节。'}
assert not (P/'publication.json').exists()
for n in range(36,43):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=938,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(36,43)],next_paragraph='zztj-v282-y0939-p001',next_volume=282,next_year=939,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第36—42段，原102—108行，至卷281末；938年发布完成后另核全年账本及939年界。',source_issues_review='钱文无宝/元宝、铸钱敕令纪日及高行周原职差异分别保留；李从曮姓名私用字及乱兵帐不改原文，纸本及异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(36,43)],plain_language_review='首次逐条核对展示标题、人物、事件、参与、关系和出处解释，主语明确，建议、意图、行动、追述与评价分开；原文保持字形。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
