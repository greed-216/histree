# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 941 paragraphs 1–6."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,39))
specs=[(d.name,d,'652233df546823980246fe2d04ddc59b70526578','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='tongjian-282-941-spring']
for key in ['tongjian-282-940-autumn-winter','xinwudaishi-051-an-chongrong-tuyuhun']:
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
main_sources = ['tongjian-282-940-autumn-winter']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0941-p001-p006',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-282-941-spring':'卷282·天福六年春夏','jiuwudaishi-098-zhang-shi':'卷98·张彦泽传·张式遭迫害','xinwudaishi-052-zhang-shi':'卷52·张彦泽传·张式遭迫害'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=record.get('edition_note','选定TXT逐字导出；电子本，纸本及异文待核。'),
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
for n in range(1, 7):
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
    labels={'tongjian-282-941-spring':'卷282·天福六年春夏','jiuwudaishi-098-zhang-shi':'卷98·张彦泽传·张式遭迫害','xinwudaishi-052-zhang-shi':'卷52·张彦泽传·张式遭迫害'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '正月' if n<=2 else '二月条下' if n<=5 else '二月至三月'
        citation = f'卷282·后晋天福六年（941；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0941_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={'王威（王处直之子）':'《资治通鉴》与《旧五代史》记为王处直之子，因王都夺权逃往契丹。939年契丹要求后晋让他承袭父亲旧地，石敬瑭拒绝直接授节度使。生卒年未载。是否与早期记载的王郁有关，尚待校核，未作合并。'}
NEW_ALIASES={'王威（王处直之子）':['王威']}

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

def event(code, title, n, quote, actors, when=None, note='', year=941, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='941年'+('正月' if n<=2 else '二月' if n<=5 else '二月至三月')+'条下，具体日期未载'
    key = 'event_zztj_282_0941_' + code
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
        edge = 'participation_zztj_282_0941_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_282_0941_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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




ALIASES.update({'唐主':'李昪','蜀主':'孟昶','曦':'王延羲','延政':'王延政','张公鐸':'张公铎'})
NEW_DESCRIPTIONS={
'张澄':'后晋供奉官。941年正月受石敬瑭派遣，带两千兵搜寻并驱逐并、镇、忻、代四州山谷中的吐谷浑部众。生卒年未载。',
'张式':'张彦泽的掌书记，曾受到信任。941年劝阻张彦泽杀子，遭射箭、谗言和追捕；李周为他上报朝廷后，仍被石敬瑭交还张彦泽，二月癸未在泾州遇害。新旧五代史对逃亡路线有异说。出生年未载。',
'郑元昭':'张彦泽的行军司马。941年前往后晋朝廷要求交还张式，并转述张彦泽的威胁。生卒年未载。',
'李文谦':'凉州留后。941年凉州发生军乱，李文谦闭门自焚而死。出生年及军乱原因未载。',
'刘英图':'后蜀散骑常侍。941年三月甲戌受孟昶任命，主管保宁军。生卒年未载。',
'崔銮':'后蜀谏议大夫。941年三月甲戌受孟昶任命，主管武信军。生卒年未载。',
'谢从志':'后蜀给事中。941年三月甲戌受孟昶任命，主管武泰军。生卒年未载。',
'张赞':'后蜀将作监。941年三月甲戌受孟昶任命，主管宁江军。电子底本将姓名中的字拆写为部件，同书四部丛刊本电子转录写作張讚，展示采用简体张赞，影印字形及纸本仍待核。生卒年未载。'}
NEW_ALIASES={'张澄':['張澄'],'张式':['張式'],'郑元昭':['鄭元昭'],'李文谦':['李文謙'],'刘英图':['劉英圖'],'崔銮':['崔鑾'],'谢从志':['謝從志'],'张赞':['張讚','张讚']}
old='jiuwudaishi-098-zhang-shi'; new='xinwudaishi-052-zhang-shi'; col='tongjian-282-941-sibu-collation'
add('shi_sends_zhang_cheng','石敬瑭派张澄率两千兵搜寻并驱逐吐谷浑部众',1,'春，',None,[('帝','派供奉官领兵搜寻并驱逐吐谷浑部众'),('张澄','率两千兵执行搜寻和驱逐命令')],when='941年正月丙寅',place='并、镇、忻、代四州山谷',description='石敬瑭派供奉官张澄率两千兵，搜寻并、镇、忻、代四州山谷中的吐谷浑部众，驱逐他们返回原居地。',note='两千指执行命令的士兵，不是被驱逐的部众人数；不补驱逐完成率或伤亡。')
sup('shi_sends_zhang_cheng',1,'xinwudaishi-051-an-chongrong-tuyuhun','乃遣供奉官張澄以兵二千搜索并、鎮、忻、代山谷中吐渾，悉驅出塞。','《新五代史》也记张澄率两千兵搜寻四州山谷中的吐谷浑部众，并驱逐出塞。','同次行动的官职、兵数与范围相合；本批不提前录入后续部众返回的记载。')
add('yan_builds_jianzhou','王延政修筑建州城，城周二十里',2,'王延政城','周二十里，',[('延政','修筑建州城')],place='建州',note='二十里按原文保留，不换算现代长度。')
add('yan_requests_we iwu'.replace(' ',''),'王延政请求将建州设为威武军，并由自己任节度使',2,'请于闽王曦，','自为节度使。',[('延政','提出设军和自任节度使的请求'),('曦','收到弟弟的请求')],place='建州',note='这是请求，王延羲没有批准威武军这个名称。')
add('xi_sets_zhenan','王延羲在建州设置镇安军，任王延政为节度使并封富沙王',2,'曦以威武军','封富沙王；',[('曦','因福州已有威武军，改设镇安军并授官封王'),('延政','获任镇安军节度使及富沙王')],place='建州')
add('yan_renames_zhenwu','王延政自行将镇安军改称镇武军',2,'延政改',None,[('延政','自行改用镇武军名称')],place='建州',note='自行改称不写成王延羲批准的新军名。')
add('desheng_bridge','德胜口修建浮桥',3,'二月，',None,[],when='941年二月壬辰',place='德胜口',description='《资治通鉴》记，二月壬辰在德胜口修建浮桥。原文没有记明主持施工者、桥长或坐标。')
add('zhang_shi_remonstrates','张式劝阻张彦泽杀死自己的儿子',4,'彰义节度使','谏止之。',[('张彦泽','打算杀死自己的儿子'),('张式','以掌书记身份劝阻张彦泽')],when='941年二月癸未张式遇害以前，具体日期未载',note='杀子是张彦泽的意图，不录成儿子已经被杀；素受厚是此前背景。')
add('zhang_yanze_shoots','张彦泽因张式劝谏而发怒，向张式射箭',4,'彦泽怒，','射之；',[('张彦泽','因劝谏发怒并射箭'),('张式','因劝谏遭张彦泽射箭')],when='941年二月癸未以前，具体日期未载',note='主书未说射中，不补受伤结果。')
sup('zhang_yanze_shoots',4,new,'彥澤怒，引弓射式，式走而免。','《新五代史》补记，张式逃走，避开张彦泽的射箭。','避开射箭来自传记，不把主书射之理解成已经中箭。',relation='adds')
add('zhang_shi_leaves','张式遭张彦泽左右进谗，告病离开',4,'左右素恶式，','谢病去，',[('张式','因谗言害怕，告病离开')],when='941年二月癸未以前，具体日期未载',description='张彦泽左右的人原本厌恶张式，又向张彦泽进谗。张式害怕，以生病为由离开。',note='左右未具名，不造人物；长期厌恶的起年未载。')
add('zhang_yanze_pursues','张彦泽派兵追捕张式',4,'彦泽遣兵','追之，',[('张彦泽','派兵追捕离开的张式'),('张式','出走后遭追捕')],when='941年二月癸未以前，具体日期未载')
add('li_zhou_reports','张式到达邠州，李周向朝廷上报',4,'式至邠州，','李周以闻，',[('张式','逃到邠州'),('李周','作为静难节度使向朝廷上报')],when='941年二月癸未以前，具体日期未载',place='邠州')
sup('li_zhou_reports',4,old,'式懇告刺史，遂差人援送到汾州。節度使李周驛騎以聞，','《旧五代史》记张式向刺史求助，被护送到汾州，李周派驿骑上报。','《资治通鉴》及《新五代史》记邠州，《旧五代史》此处记汾州；保留地名差异，不强行统一。',relation='conflicts')
sup('li_zhou_reports',4,new,'式至衍州，刺史以兵援之邠州，節度使李周留式，馳騎以聞，','《新五代史》补记张式先到衍州，由刺史派兵护送到邠州，李周收留后上报。','衍州是传记补充的逃亡阶段；没有据此改写主书邠州，也未借用旧史汾州。',relation='adds')
add('shi_exiles_zhang_shi','石敬瑭顾忌张彦泽，将张式流放商州',4,'帝以彦泽故，','流式商州。',[('帝','顾忌张彦泽，将张式流放商州'),('张式','被朝廷判流放商州')],when='941年二月癸未以前，具体日期未载',place='商州',note='流放决定不等于张式已经到达商州。')
add('zheng_demands_zhang_shi','郑元昭到朝廷要求交还张式，并转述张彦泽的威胁',4,'彦泽遣行军司马','恐致不测。”',[('张彦泽','派行军司马要求交还张式'),('郑元昭','到朝廷提出要求并转述威胁')],when='941年二月癸未以前，具体日期未载',description='张彦泽派行军司马郑元昭到朝廷要求交还张式。郑元昭说，如果张彦泽得不到张式，恐怕会出现难以预料的后果。',note='恐致不测是威胁性言论，不写成已经发生的叛乱。')
add('shi_hands_over_zhang_shi','石敬瑭将张式交给张彦泽',4,'帝不得已，','与之。',[('帝','接受要求，交还张式'),('张式','被交还张彦泽')],when='941年二月癸未以前，具体日期未载')
add('zhang_shi_killed','张式被送到泾州后，遭张彦泽下令虐杀',4,'癸未，',None,[('张式','到达泾州后被虐杀'),('张彦泽','下令虐杀张式')],when='941年二月癸未',place='泾州',description='二月癸未，张式被送到泾州。张彦泽下令撕裂他的嘴、剖出心脏并砍断四肢，张式遇害。',note='本句记具体纪日；死亡结果还由新旧五代史传记明确印证。')
sup('zhang_shi_killed',4,old,'既至，決口割心，斷手足而死之。','《旧五代史》明确记张式到达后被虐杀而死。','死亡结果明确，未使用后面其父申诉及王周代任的后续记载。')
add('liangzhou_mutiny','凉州发生军乱',5,'凉州军乱，','凉州军乱，',[],place='凉州',note='军乱原因和参加者未载，不自行补出主谋。')
add('li_wenqian_dies','凉州留后李文谦闭门自焚而死',5,'留后李文谦',None,[('李文谦','军乱时闭门自焚而死')],place='凉州',note='自焚不写成叛军直接杀害，具体日期未载。')
add('shu_garrison_problems','后蜀军镇由留成都的节度使委托僚佐管理，史书记其弊端',6,'蜀自建国以来，','民无所诉。',[],year=None,when='后蜀建国后至941年改革以前，具体年月未载',place='后蜀军镇',description='《资治通鉴》记，后蜀建国以后，不少节度使兼领禁兵或其他职务，留在成都，将军镇事务交给僚佐。史书批评他们聚敛财物、政务失治，百姓无处申诉。',note='这是对此前制度与弊端的概述，不强定941年开始，也不把评价推广到全部节度使。')
add('meng_removes_military_governors','孟昶给赵廷隐、王处回和张公铎加检校官，免去其节度使职',6,'蜀主知其弊，','并罢其节度使。',[('蜀主','调整兼领军镇的三名官员'),('赵廷隐','获加检校官并免去武德节度使职'),('王处回','获加检校官并免去武信节度使职'),('张公鐸','获加检校官并免去保宁节度使职')],when='941年二月丙辰',place='后蜀',note='只免节度使职，不写成全部官职均被罢免；原文未列检校官具体名号。')
for code,title,start,end,name,role,place in [
('li_hao_wude','孟昶任李昊主管武德军','三月，甲戌，','知武德军，','李昊','以翰林学士承旨身份主管武德军','武德军'),
('liu_yingtu_baoning','孟昶任刘英图主管保宁军','散骑常侍刘英图','知保宁军，','刘英图','以散骑常侍身份主管保宁军','保宁军'),
('cui_luan_wuxin','孟昶任崔銮主管武信军','谏议大夫崔銮','知武信军，','崔銮','以谏议大夫身份主管武信军','武信军'),
('xie_congzhi_wutai','孟昶任谢从志主管武泰军','给事中谢从志','知武泰军，','谢从志','以给事中身份主管武泰军','武泰军'),
('zhang_zan_ningjiang','孟昶任张赞主管宁江军','将作监张讠赞',None,'张赞','以将作监身份主管宁江军','宁江军')]:
 add(code,title,6,start,end,[(name,role)],when='941年三月甲戌',place=place,note='沿用本段孟昶任官的主语；知军是主管该军，不擅自改成授节度使。')
sup('zhang_zan_ningjiang',6,col,source_span(col,'將作監張讚知','寧江軍'),'《资治通鉴》四部丛刊本电子转录写作将作监張讚主管宁江军。','同书固定修订1471325用于姓名校读，规范展示为张赞；没有改动电子底本张讠赞的原文，也不算另一部独立史书的确证。影印字形及纸本待核。')
for row in B['people']:
 if row['name'] in ['张式','李文谦']:
  row['death_year']=941
  n=4 if row['name']=='张式' else 5
  claim('person',row['key'],'death_year',row['name']+'于941年去世。',n,span(n,'癸未，' if n==4 else '留后李文谦'),'死亡结果与本段纪年相合，出生年未载。')
reviews={1:'两千是张澄所率士兵；驱逐与此前吐谷浑归附、契丹责问的未知年月分开，新五代史补证同次行动。',2:'设威武军是王延政的请求；王延羲实际设置镇安军，王延政自行改称镇武。城周二十里不换算现代长度。',3:'浮桥施工者未载，保留二月壬辰，不虚构具名参与人。',4:'杀子意图、射箭、谗言、逃亡、追捕、上报、流放决定、索人、交人及虐杀分别记录。新旧五代史补证死亡及路线，邠州、汾州异说保留；此前各阶段不共用癸未日期，未提前录入次年追责。',5:'军乱与李文谦闭门自焚分别记录，未补乱因与凶手。',6:'旧有军镇弊端用未知年，二月丙辰免三人节度使与三月甲戌五人知军分开。张讠赞据同书固定版本校读为張讚，展示张赞，原字保留，影印与纸本待核。'}
assert not (P/'publication.json').exists()
for n in range(1,7):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=941,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,7)],next_paragraph=Q[7]['id'],next_volume=282,next_year=941,supplements=supplements,excluded_non_body=[],coverage='连续第1—6段，原86—91行；正月至三月。全年38段，剩余32段待录。',source_issues_review='张式逃亡路线邠州与汾州存在异说；张赞姓名据同书电子版本校读，原拆分字保留。纸本及影印字形待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,7)],plain_language_review='首次整理逐条检查新增人物介绍、事件标题与说明、参与角色、时间、事实说明及核对说明；引用保留原字，明确主语及行动阶段。复用人物主体字段保留线上已有值，旧内容不在本批扩大改写，新增引用补充当前身份。未新增固定二次文案审阅。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
