# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 940 paragraphs 11–20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,36))
specs=[(d.name,d,'c41515820cdf0fa2e63ec5eb0e14bf77c385f320','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-282-940-spring']:
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
main_sources = ['tongjian-282-940-spring','tongjian-282-940-summer']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0940-p011-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-282-940-summer':'卷282·天福五年夏秋','jiuwudaishi-079-anyuan-campaign':'卷79·晋高祖纪·天福五年五月至六月','xinwudaishi-047-ma-quanjie-anyuan':'卷47·马全节传·安州战事','xinwudaishi-008-tianfu-five':'卷8·晋本纪·天福五年'}
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
lines = (ROOT / 'resources/derived/tongjian/282.txt').read_text().splitlines()
for n in range(11, 21):
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
    labels={'tongjian-282-940-summer':'卷282·天福五年夏秋','jiuwudaishi-079-anyuan-campaign':'卷79·晋高祖纪·天福五年五月至六月','xinwudaishi-047-ma-quanjie-anyuan':'卷47·马全节传·安州战事','xinwudaishi-008-tianfu-five':'卷8·晋本纪·天福五年'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '四月' if n==11 else '四月至五月' if n==12 else '五月' if n==13 else '六月条下' if n<=17 else '七月条下'
        citation = f'卷282·后晋天福五年（940；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0940_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=940, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='940年'+('四月' if n<=12 else '五月' if n==13 else '六月' if n<=17 else '七月')+'条下，具体日期未载'
    key = 'event_zztj_282_0940_' + code
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
        edge = 'participation_zztj_282_0940_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_282_0940_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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




ALIASES.update({'唐主':'李昪','闽王':'王延羲','闽主曦':'王延羲','曦':'王延羲','延政':'王延政','璟':'李璟','刘康':'刘康（后晋将领）','张纬':'张纬（李金全推官）'})
NEW_DESCRIPTIONS={
'安审晖':'安审琦的兄长。940年任保大节度使，受命副马全节讨李金全，追击南唐军，黄花谷、云梦战事获胜。《新五代史》《旧五代史》写安審暉，展示使用简体。生卒年未据本段确定。',
'李承裕':'南唐鄂州屯营使。940年与段处恭奉命迎接李金全，随后据安州，与后晋军交战战败被俘，遭马全节杀死。遇害地点、顺序和原因各书记载有异。出生年未载。',
'段处恭':'南唐将领。940年与李承裕奉命迎接李金全，在黄花谷被后晋追兵击败时战死。出生年未载。',
'尚全恭':'南唐客省使。940年受李昪派遣，前往闽国调解王延羲、王延政兄弟的争端。生卒年未载。',
'张建崇':'南唐将领。940年安州战事中据云梦桥抵抗后晋军，使安审晖停止追击返回。生卒年未载。',
'杜光业':'南唐监军。940年安州战败后，与其他被俘者被送到大梁；石敬瑭遣返，李昪拒绝接收，后来被后晋授官。《旧五代史》在相关记载中写杜光鄴，字形待核。生卒年未载。',
'祖全恩':'南唐将领。李昪命他带兵迎接逃往吴国的卢文进，并告诫在城外接应、不得抢掠。本处是回述此前经历，具体日期未载。生卒年未载。',
'刘康（后晋将领）':'后晋旧将。940年石敬瑭将被南唐拒收的士卒编为显义都，命刘康统领。生卒年未载。',
'桑千':'安州马步副都指挥使。940年因不跟随李金全拒命而死，七月获后晋朝廷追赠官职。出生年未载。',
'王万金':'安州威和指挥使。940年因不跟随李金全拒命而死，七月获后晋朝廷追赠官职。出生年未载。',
'成彦温':'安州威和指挥使。940年因不跟随李金全拒命而死，七月获后晋朝廷追赠官职。出生年未载。',
'庞守荣':'安州马步都指挥使。李金全拒命时，讥笑不肯从叛而死的桑千等，以迎合李金全。940年七月被石敬瑭派人处死。出生年未载。'}
NEW_ALIASES={'安审晖':['安審暉'],'李承裕':[],'段处恭':['段處恭'],'尚全恭':[],'张建崇':['張建崇'],'杜光业':['杜光業'],'祖全恩':[],'刘康（后晋将领）':['刘康','劉康'],'桑千':[],'王万金':['王萬金'],'成彦温':['成彥溫'],'庞守荣':['龐守榮']}
NEW_DESCRIPTIONS['李守贞']='后晋内客省使。940年五月受命担任马全节讨伐李金全军队的都监，职务由《旧五代史》本纪补充。生卒年未据本段确定。'
NEW_ALIASES['李守贞']=['李守貞']
old='jiuwudaishi-079-anyuan-campaign';ma='xinwudaishi-047-ma-quanjie-anyuan';ann='xinwudaishi-008-tianfu-five'
add('qian_hongzun_dies','吴越世子钱弘僔去世',11,'甲子，',None,[('钱弘僔','作为吴越世子去世')],when='940年四月甲子',note='孝献为死后谥号，不补死亡原因或公历日期；沿已有钱弘僔主体。')
add('yan_asks_relief_withdrawal','吴越援军抵达后，王延政送牛酒慰劳，请求撤军',12,'吴越仰仁诠','请班师；',[('仰仁诠','率吴越援军到达建州'),('延政','以福州军已退为由犒军，请援军撤回')],place='建州',description='仰仁诠等率吴越军到达建州。王延政说福州军已经败退，送牛酒慰劳，并请求吴越军撤回。',note='衔接前批派援军命令；此处才是实际抵达。')
add('wuyue_refuses_withdrawal','仰仁诠等拒绝撤军，在建州西北设营',12,'仁诠等不从，','城之西北。',[('仰仁诠','拒绝王延政撤军请求并设营'),('延政','撤军请求被拒绝')],place='建州西北')
add('yan_asks_min_relief','王延政因惧怕吴越援军，转向王延羲求援',12,'延政惧，','于闽王。',[('延政','向此前交战的兄长求援'),('闽王','收到弟弟求援')],note='兄弟此前交战与本次共同对付吴越是不同阶段，不自动建立永久盟友关系。')
add('min_sends_jiye','王延羲派王继业率两万兵救援王延政',12,'闽王以','将兵二万救之；',[('闽王','派遣两万人救援弟弟'),('王继业','任行营都统，率军救援'),('延政','获得兄长派遣的救援')],place='建州',note='王继业沿已有主体，其父亲仍有异说，本句不新增父子关系。')
add('min_cuts_wuyue_supplies','王延羲写信责问吴越，并派轻兵截断吴越粮道',12,'且移书','粮道。',[('闽王','责问吴越，并下令截断其军粮道')],place='吴越军粮道')
add('wuyue_supplies_run_out','长时间下雨，吴越军粮食耗尽',12,'会久雨，','食尽，',[],description='《资治通鉴》记，当时长时间下雨，吴越军的粮食耗尽。',note='此前截断粮道与久雨分别保留；未给降雨量或断粮的单一精确原因。')
add('yan_defeats_wuyue','王延政出兵大败吴越军，俘虏与斩杀人数以万计',12,'五月，','俘斩以万计。',[('延政','出兵击败吴越军')],when='940年五月，具体日期未载',place='建州',note='俘斩以万计是俘虏与杀伤合称，不写成斩首整一万人。')
add('yang_renquan_retreats','仰仁诠等撤离建州',12,'癸未，',None,[('仰仁诠','在吴越军战败后撤离')],when='940年五月癸未',description='《资治通鉴》记，癸未，仰仁诠等撤离建州。电子底本写作仁诠等诠遁，重复字形保留在原文。',note='按上下文识别撤退主体；不修改源文本重复诠字，也不补其他未明撤退将领。')
add('hu_hears_appeal','胡汉筠听说贾仁沼的两个儿子准备向朝廷申诉',13,'胡汉筠既','欲诉诸朝；',[('胡汉筠','拒绝入朝后，又听说贾仁沼之子准备申诉')],when='940年李金全拒命以前，具体月日未载',note='既违诏命是此前背景，本条只新增听闻申诉动向；两个儿子的姓名未载，不造人物。')
add('hu_deceives_li','胡汉筠欺骗李金全，说朝廷将在交接后追查贾仁沼之死',13,'及除马全节','金全大惧。',[('胡汉筠','以追查死案的说法恐吓李金全'),('李金全','听信说法后害怕')],when='940年马全节接任安州的命令传到以后，具体月日未载',description='马全节受命接替李金全后，胡汉筠谎称进奏吏送来消息，说朝廷将在李金全交接后追查贾仁沼死亡情况，并怀疑李金全有异谋。李金全因此害怕。',note='史书明言绐，朝廷将查案的说法是胡汉筠传述的谎言，不记成已经证实的朝廷计划。')
add('li_refuses_and_joins_tang','胡汉筠劝李金全拒绝朝命、归附南唐，李金全听从',13,'汉筠因说','金全从之。',[('胡汉筠','劝李金全拒命归附南唐'),('李金全','听从拒命归附建议')],when='940年五月丙戌后晋获报以前，具体日期未载')
sup('li_refuses_and_joins_tang',13,ann,'五月丙戌，安遠軍節度使李金全叛附于唐。','《新五代史》晋本纪记五月丙戌李金全叛附南唐。','本纪纪日与通鉴皇帝获报并下令讨伐的丙戌对应；不据此断定筹谋、实际拒命及获报均在同一刻。')
add('shi_orders_anyuan_campaign','石敬瑭命马全节讨伐李金全，安审晖为副',13,'丙戌，','以保大节度使安审晖为之副。',[('帝','命各州出兵讨伐李金全'),('马全节','受命统军讨伐'),('安审晖','受命为副将'),('李金全','因拒命成为讨伐对象')],when='940年五月丙戌',description='石敬瑭得知李金全拒命归附南唐，命马全节率汴、洛、汝、郑、单、宋、陈、蔡、曹、濮、申、唐等州兵讨伐，以保大节度使安审晖为副将。',note='通鉴列十二州，旧史列十州，分别保留，不用旧史州数替换本句。')
sup('shi_orders_anyuan_campaign',13,old,'丙戌，安州節度使李金全叛，詔新授安州節度使馬全節以洛、汴、汝、鄭、單、宋、陳、蔡、曹、濮十州之兵討之。以前鄜州節度使安審暉為副，以內客省使李守貞為都監，','《旧五代史》同记五月丙戌讨伐，列十州兵，并补李守贞为都监。','主书列十二州，旧史十州，参战范围差异保留；李守贞身份来自此独立出处。',relation='adds')
E['li_shouzhen_supervises']=event('li_shouzhen_supervises','石敬瑭任李守贞为讨伐李金全军队的都监',13,'以內客省使李守貞為都監，',[('帝','任命讨伐军都监'),('李守贞','受命监督讨伐军')],source=old,when='940年五月丙戌',description='《旧五代史》补记，石敬瑭任内客省使李守贞为讨伐军都监。',note='主书未列此人，独立补充到本次出兵行动，不把原句冒作通鉴记载。')
# Supplement the army strength without changing the primary list of prefectures.
sup('shi_orders_anyuan_campaign',13,ma,'高祖發兵三萬，使全節與安審暉討之，','《新五代史》马全节传补记后晋出兵三万人，由马全节与安审晖讨伐。','兵数来自传记，通鉴本句未给总数；不将三万套给南唐援军。',relation='adds')
relationship('安审晖','安审琦','兄长',13,'审晖，审琦之兄也。','原文明示安审晖是安审琦的兄长；不推父母身份。')
add('li_sends_zhang_wei','李金全派张纬向南唐递交降表',13,'李金全遣','请降于唐，',[('李金全','派推官递交降表'),('张纬','携降表向南唐请降')],note='张纬沿已有李金全推官主体；奉表请求与南唐派兵接应分录。')
add('tang_sends_reception','李昪派李承裕、段处恭率三千兵接应李金全',13,'唐主遣',None,[('唐主','派军接应李金全'),('李承裕','与段处恭率军接应'),('段处恭','与李承裕率军接应')],description='李昪派鄂州屯营使李承裕、段处恭率三千兵接应李金全。',note='此处出发兵数三千，后文损失四千各依原文保留，未补出增援或将两数强行校同。')
add('shang_mediates_min','李昪派尚全恭调解王延羲、王延政的争端',14,'唐主遣','及王延政。',[('唐主','派使者调解闽国兄弟冲突'),('尚全恭','受命前往闽国调解'),('曦','成为调解对象'),('延政','成为调解对象')],when='940年六月盟誓以前，具体月日未载',place='闽国')
add('min_swears_peace','王延政派人携誓书与香炉到宣陵，与王延羲盟誓',14,'六月，','盟于宣陵。',[('延政','派牙将和女奴携物参加盟誓'),('曦','在宣陵与弟弟一方盟誓')],when='940年六月，具体日期未载',place='福州宣陵',description='王延政派牙将和女奴，携带誓书与香炉到福州，在宣陵与王延羲盟誓。',note='原文明确使者到场，不写王延政本人前往福州；使者姓名未知，不建人物。')
add('min_distrust_persists','盟誓以后，王延羲与王延政仍互相猜忌',14,'然兄弟',None,[('曦','盟誓后仍猜忌弟弟'),('延政','盟誓后仍猜忌兄长')],description='《资治通鉴》记，盟誓以后，王延羲、王延政兄弟仍像此前一样互相猜忌。',note='不能把举行盟誓解释为矛盾已经完全解决。')
add('tang_reaches_anzhou','李承裕等率南唐军抵达安州',15,'癸卯，','至安州。',[('李承裕','率南唐军抵达安州')],when='940年六月癸卯',place='安州')
sup('tang_reaches_anzhou',15,ann,'六月癸卯，李昪遣其將李承裕入于安州，金全奔于唐，','《新五代史》晋本纪也记六月癸卯李承裕进入安州、李金全投奔南唐。','年月日与主书对应；入安州不改成无交接背景的普通驻军。')
add('li_joins_tang_camp','李金全率数百部下到南唐营中，李承裕夺其资财并据安州',15,'是夕，','承裕入据安州。',[('李金全','夜间率数百部下前往南唐军'),('李承裕','夺取李金全的妓妾资财并据安州')],when='940年六月癸卯夜',place='安州',description='当夜，李金全率数百部下前往南唐军。李承裕夺取他的妓妾和资财，随后进入安州据守。',note='不得将接应描绘为善意安置；妓妾被夺沿史书实际记载，不猜人数和具体身份。')
sup('li_joins_tang_camp',15,old,'癸卯，淮南使李承裕代李金全，金全南走，承裕以淮兵二千守其城。','《旧五代史》记李金全南走、李承裕以两千南唐兵据守安州。','两千是此处守城兵数，主书此前派三千、后文失亡四千，未将不同阶段数字合并。',relation='adds')
add('ma_defeats_tang_south','马全节从应山进军大化镇，在安州城南击败李承裕',15,'甲辰，','大破之。',[('马全节','进军后在城南击败南唐军'),('李承裕','在城南交战失利')],when='940年六月甲辰；《旧五代史》另记戊申交战',place='应山、大化镇、安州城南',note='主书记甲辰同条进军和战胜，旧史区分甲辰进军、戊申交战，纪日差异保留。')
sup('ma_defeats_tang_south',15,old,'甲辰，馬全節自應山縣進軍於大化鎮。戊申，與鄂州賊軍陣於安陸之南，三戰而後克之，斬首三千級，生擒千餘人。','《旧五代史》记甲辰进军大化镇、戊申在安陆城南三战获胜，并列斩首三千、生擒千余。','与主书同条甲辰交战不同，未擅定为两场确定不同的城南之战。',relation='conflicts')
add('ma_enters_anzhou','李承裕掠夺安州后南逃，马全节进入安州',15,'承裕掠','全节入安州。',[('李承裕','掠夺安州后南逃'),('马全节','进入安州')],when='940年六月甲辰交战以后，具体日期存在书间差异',place='安州',note='主书未对本句另列日期；旧史与新史将入城记在丁巳，不与甲辰强校同日。')
sup('ma_enters_anzhou',15,ann,'丁巳，克安州，承裕奔于雲夢，','《新五代史》晋本纪列丁巳克安州、李承裕奔向云梦。','本纪与主书逐日追击顺序不同，日期各自保留。',relation='conflicts',field='time_original')
add('duan_dies_huanghua','安审晖在黄花谷追败南唐军，段处恭战死',15,'丙午，','段处恭战死。',[('安审晖','追击并击败南唐军'),('段处恭','在黄花谷战死')],when='940年六月丙午',place='黄花谷')
add('an_captures_li','安审晖在云梦泽再败南唐军，俘获李承裕等',15,'丁未，','虏承裕及其众。',[('安审晖','追败南唐军并俘获其将领与部众'),('李承裕','在云梦泽被俘')],when='940年六月丁未',place='云梦泽')
sup('an_captures_li',15,ma,'審暉追至雲夢，執承裕及其兵二千人，','《新五代史》马全节传也记安审晖追至云梦，俘获李承裕及两千兵。','传记补兵数，没有本段逐日纪时；不同书的俘获与处置数量分别保留。',relation='adds')
add('zhang_defends_bridge','张建崇据云梦桥抵抗，安审晖返回',15,'唐将张建崇','审晖乃还。',[('张建崇','据云梦桥抵抗后晋军'),('安审晖','遇桥上抵抗后返回')],when='940年六月丁未追击条下，具体日期未另载',place='云梦桥',note='原文没有张建崇被俘或死亡，不补归宿；返回不推为整个晋军战败。')
add('ma_executes_li','马全节杀死李承裕及其部众一千五百人',15,'马全节斩','于城下，',[('马全节','处死李承裕及其部众'),('李承裕','被马全节杀死')],when='940年六月被俘以后，具体日期及遇害顺序各书有异',place='安州城下（《通鉴》所载）',description='《资治通鉴》记，马全节在城下杀死李承裕及其部众一千五百人。《新五代史》马全节传则记李承裕被送往京师后，因扬言告发马全节取财而被杀。',note='一千五百人是原句处决数量，未另增一千五百零一；遇害地点顺序原因不强行裁定。')
sup('ma_executes_li',15,ma,'全節斬千五百人，以其餘兵并承裕獻于京師。承裕謂全節曰：「吾掠城中，所得百萬計，將軍皆取之矣。吾見天子，必訴此而後就刑。」全節懼，因殺承裕，高祖置而不問，','《新五代史》记先斩一千五百兵，再送其余兵与李承裕到京师；李承裕扬言告发，马全节因害怕杀他，皇帝未问。','与《通鉴》李承裕及众在城下同时被斩的表述有异；告发财物属于书中人物言论，未当作已经查实贪污。',relation='conflicts')
add('du_sent_to_daliang','马全节将杜光业等五百零七人送往大梁',15,'送监军','于大梁。',[('马全节','送监军和其他被俘者赴大梁'),('杜光业','作为南唐监军被送往大梁')],when='940年六月安州战事以后，具体日期未载',place='大梁',note='五百零七按主书；旧史五百余是概数，两数不作完全同数证明。')
sup('du_sent_to_daliang',15,old,'執其偽都監杜光鄴，及淮南軍五百餘人，露布獻於闕下。','《旧五代史》也記监军及五百余人送往京师，监军名写杜光鄴。','职务与行动对应，光鄴与光业字形差异待核，不直接将杜光鄴列为已核正式别名。',relation='adds')
add('shi_releases_tang_prisoners','石敬瑭认为被俘者无罪，赐马与衣物器具，遣返南唐',15,'上曰：','而归之。',[('帝','认为被俘者没有罪，赐物遣返'),('杜光业','与其他被俘者获赐物遣返')],when='940年六月安州战事以后，具体日期未载',description='石敬瑭说这些人有什么罪，给他们马、器具和衣服，并让他们返回南唐。',note='皇帝无罪判断以其言论表述；遣返不等于南唐已经接收。')
sup('shi_releases_tang_prisoners',15,old,'帝曰：此輩何罪，皆厚給放還。','《旧五代史》同样记皇帝认为被俘者无罪，厚给资物后释放。','印证释放决定，不据此略去后续南唐拒收及后晋安置。')
add('zu_receives_lu','李昪此前派祖全恩迎接卢文进，并禁止入城抢掠',15,'初，','无得剽惊。',[('唐主','派军迎接卢文进，并告诫不得入城或抢掠'),('祖全恩','受命在城外接应并护送卢文进'),('卢文进','被安排由祖全恩迎接护送')],year=None,when='卢文进投奔吴国时的追述，本处未列年月',place='安州城外',description='卢文进此前投奔吴国时，李昪派祖全恩带兵迎接，告诫不要进入安州城，应在城外等候，待卢文进出来后护送返回，不得抢掠、惊扰。',note='唐主是史书以后来的身份称李昪；实际背景为卢文进投奔吴国，不误记为940年新出逃。')
add('li_receives_same_orders','李昪迎接李金全时，也告诫李承裕不得入城抢掠',15,'及李承裕','戒之如全恩；',[('唐主','给李承裕与祖全恩相同的禁掠告诫'),('李承裕','出兵接应李金全时受到约束')],when='940年五月南唐军接应李金全以前，具体日期未载',note='戒之如全恩承接上句完整禁令，命令与其后违反行为区分。')
add('tang_loss_and_regret','南唐军失亡四千人，李昪懊恼，认为自己告诫不够周密',15,'承裕贪','戒敕之不熟也。',[('李承裕','抢掠后与晋军交战失败'),('唐主','懊恼多日，并归因于自身告诫不周')],when='940年六月安州战败后的概述，具体日期未载',description='《资治通鉴》说，李承裕贪图抢掠，与晋军交战失败，失亡四千人。李昪惋惜懊恼多日，认为是自己的告诫不够周密。',note='失亡为损失与死亡的合称，不当四千人全部阵亡；与此前派兵三千存在范围疑问，未虚构增兵。')
add('tang_refuses_returnees','李昪以违令战败为由拒收杜光业等，将他们送回淮北',15,'杜光业等至唐，','复送于淮北，',[('唐主','拒收被后晋遣返的将士'),('杜光业','抵达南唐后又被送往淮北')],when='940年安州战败后遣返过程，具体月日未载',place='南唐、淮北')
add('tang_explains_to_shi','李昪致信石敬瑭，称边将贪功据垒，双方都不能容于军法',15,'遗帝书曰：','彼此不可。”',[('唐主','致信解释拒收及对边将的指责'),('帝','收到南唐来信')],when='940年遣返交涉期间，具体月日未载',description='李昪给石敬瑭写信，称边地将领贪功、趁机占据营垒；按军法与朝廷章程，双方都不能容许这种行为。',note='这是李昪的书信说法，不据此认可拒收士卒的法律判断。')
add('tang_blocks_second_return','石敬瑭再次遣返将士，李昪派战舰阻止渡淮',15,'帝复遣之归，','乃还。',[('帝','再次派人送将士返回南唐'),('唐主','派战舰阻止渡淮')],when='940年第二次遣返时，具体月日未载',place='桐墟、淮河',description='石敬瑭再次派人送他们返回。使者准备从桐墟渡淮时，李昪派战舰拦阻，使者只得返回。',note='未补水战或战舰数量，也未把使者返回记成将士已成功进入南唐。')
add('shi_settles_tang_troops','石敬瑭授南唐将领官职，将士卒编为显义都，由刘康统领',15,'帝悉授',None,[('帝','授官并编组被拒收的南唐将士'),('刘康','受命统领显义都'),('杜光业','属于此前被遣返又遭拒收的南唐将领')],when='940年南唐两次拒收以后，具体月日未载',description='石敬瑭给这些南唐将领授官，将他们的士卒编为显义都，命后晋旧将刘康统领。',note='杜光业按前述将领群体识别，具体所授官职未载；刘康与其他同名人物按后晋旧将身份区分。')
# Paragraph 16 is an editorial argument, not another occurrence of the battle.
used[16]=[]
claim('person',people['李昪'],'biography','《资治通鉴》的史论批评李昪拒收被遣返的士卒，认为应追究违令将领的责任并安抚士卒，不应抛弃士卒以增强敌国。',16,Q[16]['text'],'这是对前段南唐拒收士卒的作者议论，不是已发生的杀将或抚军。电子底本巨光曰称谓字形待核，原文保留，不新建具名评论者。')
add('li_exposes_eunuch','李昪指出祭庐山的宦官曾买鱼肉，驳斥其全程吃素的说法',17,'唐主使','宦者惭服。',[('唐主','指出宦官途中买鱼肉的情况')],year=None,when='李昪在位期间的轶事，具体年月未载',place='庐山及返程',description='李昪派宦官祭庐山，回来后夸其行事精洁。宦官自称奉诏以来一直吃素，李昪却指出他在某处某日买鱼肉煮食，宦官惭愧认服。',note='宦官无姓名，地名日期仅用某处某日，不猜身份或皇帝获取消息的方式。')
add('li_questions_surplus_grain','仓吏献万余石结余粮，李昪质疑是否盘剥百姓和军队',17,'仓吏',None,[('唐主','对仓吏献出的结余粮提出质疑')],year=None,when='李昪在位期间某年岁末，具体年份未载',description='仓吏在岁末献出一万多石结余粮。李昪认为收支有数，质问若没有盘剥百姓、苛扣军粮，怎么会有这些结余。',note='盘剥与苛扣是皇帝的质疑，不写成已查明的罪行；岁末轶事不能硬定在940年六月。')
add('min_fuzhou_wall','王延羲修筑福州西郭城墙，以防建州军',18,'秋，七月，','以备建人。',[('曦','修筑福州西郭以防备建州军')],when='940年七月，具体日期未载',place='福州西郭',note='城作为筑城动作，不把建人推成现代民族称谓；防备目的沿原书。')
add('min_ordains_many_monks','闽国准许一万一千人出家，许多人借此避重赋',18,'又度民',None,[('曦','在闽国准许百姓出家为僧')],when='940年七月条下，具体起止日期未载',description='闽国又准许百姓出家为僧，许多百姓借此逃避沉重赋税，史书记人数共一万一千。',note='人数与避税动机沿史书，不推全部僧人都为避税出家或所有出家者永久免税。')
add('shi_returns_min_envoys','石敬瑭赐郑元弼等绢帛，送他们回闽国',19,'乙丑，','遣归。',[('帝','赐使者绢帛并遣归'),('郑元弼','获赐绢帛返回闽国')],when='940年七月乙丑',note='正月获释与七月遣归分阶段，不重造一次释放。')
add('loyal_anzhou_officers_die','桑千、王万金、成彦温因不跟随李金全拒命而死',19,'李金全之叛也，','不从而死，',[('桑千','不肯跟随李金全拒命而死'),('王万金','不肯跟随李金全拒命而死'),('成彦温','不肯跟随李金全拒命而死'),('李金全','其拒命遭军官反对')],when='940年李金全拒命期间，具体遇害日期未载',place='安州',note='主书说不从而死，未明直接杀害者和具体死亡方式，不写李金全亲自杀人。')
add('pang_mocks_loyal_officers','庞守荣讥笑桑千等愚蠢，以迎合李金全',19,'马步都指挥使','金全之意。',[('庞守荣','讥笑不肯跟从而死的军官'),('李金全','受到庞守荣迎合')],when='940年李金全拒命期间，具体日期未载',description='马步都指挥使庞守荣讥笑桑千等愚蠢，以迎合李金全。',note='愚蠢是庞守荣的评价，不成为网站对死者的判断。')
add('shi_honors_loyal_officers','石敬瑭追赠贾仁沼、桑千等官职',19,'己巳，','诏赠贾仁沼及桑千等官，',[('帝','下诏追赠死者官职'),('贾仁沼','获追赠官职'),('桑千','获追赠官职'),('王万金','属于前述受追赠的死者'),('成彦温','属于前述受追赠的死者')],when='940年七月己巳',note='桑千等承接前文三名不从而死者；具体追赠官阶未载，不补官名。')
add('shi_executes_pang','石敬瑭派人到安州处死庞守荣',19,'遣使诛', '于安州。',[('帝','派使者处死庞守荣'),('庞守荣','被处死')],when='940年七月己巳',place='安州',note='执行者姓名未载，不补审判或处刑方式。')
add('tang_treats_li_coldly','李金全到金陵后，李昪待他冷淡',19,'李金全至',None,[('李金全','抵达金陵，受到冷淡待遇'),('唐主','对李金全待遇淡薄')],when='940年李金全投奔南唐后，具体月日未载',place='金陵',note='待之甚薄不等于被囚或处死，具体待遇未载。')
add('li_jing_crown_prince','李昪立李璟为太子，兼大元帅、录尚书事',20,'丁巳，',None,[('唐主','册立太子并授兼任职务'),('璟','由齐王立为太子，兼大元帅、录尚书事')],when='940年七月丁巳',note='李璟沿已有主体及齐王身份，录尚书事为原官称，不误写为编写尚书史料。')
for name,n,quote in [('钱弘僔',11,'弘僔卒'),('段处恭',15,'段处恭战死'),('李承裕',15,'马全节斩承裕'),('桑千',19,'桑千、威和指挥使王万金、成彦温不从而死'),('王万金',19,'桑千、威和指挥使王万金、成彦温不从而死'),('成彦温',19,'桑千、威和指挥使王万金、成彦温不从而死'),('庞守荣',19,'遣使诛守荣于安州')]:
 row=next(x for x in B['people'] if x['name']==name)
 if row['key'] not in reused:row['death_year']=940
 claim('person',row['key'],'death_year',f'{name}在940年去世。',n,quote,'年份据编年与本次拒命战事对应；未将不明遇害日补成后续追赠日期。')
reviews={11:'钱弘僔四月甲子死亡，沿已录世子主体，孝献为谥。',12:'援军实际抵达、犒军请退、拒撤设营、转向兄长求援、王继业救援、断粮、五月败兵及癸未撤离分阶段；二万救援与此前四万吴越援军不混。诠遁重复字原文保留。',13:'胡汉筠欺骗与朝廷实际命令区分，拒命、奉表及南唐派接应军分录。张纬沿推官主体。安审晖是安审琦兄长。十二州与旧史十州兵、南唐三千与后文失亡四千数量各自保留。',14:'尚全恭调解，六月使者盟于宣陵，王延政本人未记赴福州；盟誓后仍猜忌。',15:'安州接应、夺财、据城、城南之战、入城、黄花谷与云梦追击、桥上抵抗、处决及两次遣返和安置按原顺序细录。甲辰/戊申、丁巳/丁未日期各列；李承裕城下遇害与送京后因告发被杀异说保留。杜光鄴与光业字形待核。失亡不等于全部阵亡。卢文进旧事与新禁令区分，追述未知年月留空。',16:'本段是对拒收士卒的史论，完整原文保留于出处上下文；不生成另一场真实历史事件，不为其拟议杀将及安抚士卒建立已发生行动。巨光曰作者称谓字形待核，未补具名作者。',17:'宦官饮食及仓吏献粮是未确年月的轶事；岁终不硬定940年六月，质疑盘剥不当作已查实罪行。',18:'七月筑福州西郭、防建州及度一万一千人为僧分录，避税动机限定史书所载部分百姓。',19:'正月释放与七月乙丑遣归区分；三人拒命而死在此前战事，不套己巳追赠日期，直接凶手未载。庞守荣讥笑与被杀、李金全抵金陵受冷淡分别录。',20:'七月丁巳李璟立太子，兼大元帅及录尚书事；任官与史料编写无关。'}
assert not (P/'publication.json').exists()
for n in range(11,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
ledger[15]['claim_keys']=[x['key'] for x in B['claims'] if Q[16]['id'] in x['citation']]
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=940,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(11,21)],next_paragraph=Q[21]['id'],next_volume=282,next_year=940,supplements=supplements,source_contexts=[dict(paragraph_id=Q[16]['id'],source_key=choose_source(16,Q[16]['text']),text=Q[16]['text'],claim_keys=ledger[15]['claim_keys'],note=reviews[16])],excluded_non_body=[],coverage='连续第11—20段，原59—68行；四月至七月记载。第16段史论完整归档，不虚构史事。全年35段，剩余15段待录。',source_issues_review='安州城南战与入城日期、李承裕被杀顺序地点原因、讨伐州数与南唐兵数存在书间或段间差异；杜光鄴与光业、仁诠等诠遁、巨光曰字形保留待核。未以电子本改字代替校勘。纸本仍待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(11,21)],plain_language_review='首次检查展示文案、人物身份、时间与关系方向，欺骗、质疑、计划、史论与已发生行动区分；诸书异说分别引用，原文保留底本字形。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
