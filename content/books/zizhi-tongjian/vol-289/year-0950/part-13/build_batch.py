# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 77–83."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,84))
COMMIT='57e21ee3cc42021b75390decc78b600e3618c9fb'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-289-950-chu-yun-north','jiuwudaishi-103-december-expedition']:
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
main_sources = ['tongjian-289-950-chu-yun-north','tongjian-289-950-last-december']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p077-p083',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-289-950-last-december':'卷289·乾祐三年·年末处置','xinwudaishi-011-december-950':'卷11·周本纪·十二月北返与监国','xinwudaishi-018-yun-songzhou':'卷18·刘赟传·宋州夺兵','xinwudaishi-018-yun-detained':'卷18·刘赟传·拘禁与杀其随从','xinwudaishi-018-yun-deposed':'卷18·刘赟传·被废诰令','xinwudaishi-065-liu-sheng-court':'卷65·南汉世家·刘晟时内侍掌权概述'}
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
lines = (ROOT / 'resources/derived/tongjian/289.txt').read_text().splitlines()
for n in range(77, 84):
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
    for a,b in [('主書','《资治通鉴》'),('補','补'),('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('旧史','《旧五代史》'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
        note=note.replace(a,b)
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'tongjian-289-950-last-december':'卷289·乾祐三年·年末处置','xinwudaishi-011-december-950':'卷11·周本纪·十二月北返与监国','xinwudaishi-018-yun-songzhou':'卷18·刘赟传·宋州夺兵','xinwudaishi-018-yun-detained':'卷18·刘赟传·拘禁与杀其随从','xinwudaishi-018-yun-deposed':'卷18·刘赟传·被废诰令','xinwudaishi-065-liu-sheng-court':'卷65·南汉世家·刘晟时内侍掌权概述'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年十一月至十二月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_13_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=globals().get("NEW_BIRTH_YEARS",{}).get(name),death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=950, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='950年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_289_0950_' + code
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
        edge = 'participation_zztj_289_0950_' + code + '_' + pk
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
    a=ALIASES.get(a,a); b=ALIASES.get(b,b)
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'史书记{a}是{b}的{kind}',quote,source=source)
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
        row=dict(key=f'relationship_zztj_289_0950_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=event(code,title,n,span(n,start,end),actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)










ALIASES.update({'太后':'李氏（刘知远妻）','赟':'刘赟','王殷':'王殷（后汉后周将）','赵上交':'赵远','马鐸':'马铎','刘信':'刘信（刘知远从弟）','南汉主':'刘弘熙','刘晟':'刘弘熙'})
NEW_ALIASES={'马铎':['马鐸','馬鐸'],'张令超':['張令超'],'董裔':[],'贾贞':['賈貞','贾正','賈正'],'卢琼仙':['盧瓊仙'],'黄琼芝':['黃瓊芝'],'刘福（刘赟将领）':[],'夏昭度':[]}
NEW_DESCRIPTIONS={
'马铎':'前申州刺史。950年十二月受派率兵到许州巡检，随后率军入城，刘信在惶恐中自杀。生卒年未载。',
'张令超':'刘赟的护圣指挥使。950年十二月在宋州率部护卫刘赟，受到郭崇威暗中招诱后率部归附郭崇威。生卒年未载。',
'董裔':'刘赟的徐州判官。950年在宋州建议刘赟夺郭崇威兵、招募士卒逃往晋阳，刘赟犹豫未决，未实行该计划；随后在刘赟被拘禁时遭杀害。生年未载。',
'贾贞':'刘赟的客将，950年宋州局势紧张时以眼色示意想杀冯道，被刘赟制止；随后遭郭崇威一方杀害。《新五代史》同一客将、辞别和被杀场景写贾正，保留别名。生年未载。',
'卢琼仙':'南汉宫人。950年与黄琼芝获刘晟任命为女侍中，穿戴朝服冠带，参与决断政务。《新五代史》还记她与宦官林延遇掌权。生卒年未载。',
'黄琼芝':'南汉宫人。950年与卢琼仙获刘晟任命为女侍中，穿戴朝服冠带，参与决断政务。生卒年未载。',
'刘福（刘赟将领）':'《新五代史》刘赟传所记牙内都虞候。刘赟在宋州被拘禁时，与董裔、贾正、夏昭度等遭杀害。与同名人物无同人证据，生卒年月未定。',
'夏昭度':'《新五代史》刘赟传所记孔目官。刘赟在宋州被拘禁时，与董裔、贾正、刘福等遭杀害。生卒年月未定。'}
NEW_DEATH_YEARS={'董裔':950,'贾贞':950}
dec='jiuwudaishi-103-december-expedition';zhou='xinwudaishi-011-december-950';song='xinwudaishi-018-yun-songzhou';det='xinwudaishi-018-yun-detained';dep='xinwudaishi-018-yun-deposed';han='xinwudaishi-065-liu-sheng-court'
add('guo_crosses_river_chan','郭威于壬子渡河，住宿澶州',77,'壬子，','馆于澶州。',[('郭威','渡河后住宿澶州')],when='950年十二月壬子',place='澶州',note='馆为住宿驻扎，不写建新官署。')
sup('guo_crosses_river_chan',77,dec,'壬子，樞密使郭威次澶州，何福進已下及諸軍將士，扶擁威請為天子，即日南還。','《旧五代史》也记郭威壬子到澶州，但把将士拥立和南还也记在当日。','通鉴壬子抵达、癸丑兵变，旧本纪壬子兼记兵变，纪日差异保留。',relation='conflicts',field='time_original')
sup('guo_crosses_river_chan',77,zhou,'癸丑，至澶州而旋。','《新五代史》将郭威到澶州并返回记在癸丑。','新本纪到达日与通鉴壬子不同，不合并成唯一日期。',relation='conflicts',field='time_original')
add('chan_army_demands_guo','澶州将士于癸丑早晨闯入郭威住处，要求他做皇帝',77,'癸丑旦，','不可立也！”',[('郭威','命令关门，面对将士闯入要求拥立')],when='950年十二月癸丑早晨',place='澶州郭威住处',description='郭威准备出发时，数千将士突然喧闹；郭威命人关门，将士翻墙登屋闯入，说他们已与刘氏结仇，要求郭威亲自做皇帝，不能再立刘氏。',note='数千是原载规模，未具名将士不造名单；将士关于结仇和不能立的说法不写为刘赟已下报复令。')
add('yellow_flag_guo_south','将士将撕裂的黄旗披在郭威身上，拥他南行',77,'或裂黄旗','因拥威南行。',[('郭威','被将士披黄旗、扶拥南行')],when='950年十二月癸丑',place='澶州至南行路上',note='原文黄旗，不能改成赵匡胤陈桥黄袍；军中呼万岁与正式即位分开。被拥不证明没有事先策划，也不凭猜测写有策划。')
add('guo_promises_han_ancestral','郭威上书李太后，表示愿供奉汉宗庙、像对待母亲一样侍奉太后',77,'威乃上太后笺，','事太后为母。',[('郭威','向太后承诺供奉汉宗庙、像对待母亲一样侍奉太后'),('太后','收到郭威的政治承诺')],when='950年十二月癸丑军变后至丙辰前，具体上书日未载',place='南行途中、后汉朝廷',note='愿奉与事为政治承诺，不建立血缘母子或已完成收养礼关系，也不写汉宗庙永久获保。')
add('guo_weicheng_assurance','郭威于丙辰到韦城，发书安抚大梁士民',77,'丙辰，','勿有怀疑。',[('郭威','到韦城后发书安抚大梁士民')],when='950年十二月丙辰',place='韦城、大梁',description='郭威到韦城后发书给大梁士民，称自己离开河上后沿途没有侵扰，请他们不必怀疑担忧。',note='秋毫不犯是书中自述，不当现代逐路调查已证明；昨离不反推为前一公历日。')
add('dou_welcomes_guo_qili','郭威于戊午到七里店，窦贞固率百官迎拜劝进',77,'戊午，','因劝进。',[('郭威','到七里店，受到百官迎拜劝进'),('窦贞固','率百官出迎拜见，劝郭威即位')],when='950年十二月戊午',place='七里店',note='劝进是请求接受帝位，此时正式登基尚未发生；百官未列不补名单。')
sup('dou_welcomes_guo_qili',77,zhou,'戊午，次皋門，漢宰門相竇貞固、蘇禹珪來勸進。','《新五代史》也记戊午窦贞固、苏禹珪前来劝进，地点写皋门。','通鉴迎拜在七里店随后营皋门村，新本纪合记皋门并列苏禹珪，不据差异造两次同日独立劝进；宰门相为底本异常原字保留。',relation='adds')
add('guo_camps_gaomen','郭威返京前在皋门村扎营',77,'威营于皋门村。','威营于皋门村。',[('郭威','在皋门村扎营')],when='950年十二月戊午到七里店后，具体扎营日未单列',place='皋门村',note='营为驻扎，未正式即位；不混入951年从皋门入宫事件。')
add('yun_reaches_songzhou','刘赟西行已经抵达宋州',78,'武宁节度使赟','已至宋州，',[('赟','西行抵达宋州，尚未入京')],when='950年十二月澶州军变及派兵控制时，具体到达日未载',place='宋州',note='已至为此前达到，不能强套癸丑或戊午到达日。')
add('wangs_send_guo_chongwei','王峻、王殷听闻兵变，派郭崇威率七百骑拦阻刘赟',78,'王峻、王殷闻','往拒之，',[('王峻','与王殷派郭崇威拦阻刘赟'),('王殷','与王峻派七百骑拦阻刘赟'),('郭崇威','率七百骑往宋州拦阻'),('赟','成为被拦阻的嗣君')],when='950年十二月澶州军变后，具体派遣日未载',place='京师方面至宋州',note='拒是拦阻，与郭崇威面对刘赟称来护卫的解释分开，不把话语当全部行动目的。')
sup('wangs_send_guo_chongwei',78,song,'王峻慮贇左右生變，遣侍衞馬軍指揮使郭崇以兵七百騎衞贇。','《新五代史》刘赟传也记王峻派郭崇率七百骑到刘赟所在处。','郭崇按同职、七百骑、宋州夺兵场景对应郭崇威；新传写卫，通鉴写拒，保留表述差异与各书主体名单，不独断已验证政治动机。')
add('ma_duo_sent_xuzhou_xu','王峻、王殷派马铎率军到许州巡检',78,'又遣前申州刺史','许州巡检。',[('王峻','与王殷派马铎到许州'),('王殷','与王峻派马铎到许州'),('马鐸','以前申州刺史身份率兵巡检')],when='950年十二月澶州军变后，具体派遣日未载',place='许州',note='许州不是徐州；马铎展示转简体，原马鐸保留。巡检派遣与随后实际入城分开。')
add('guo_chongwei_songzhou_gate','郭崇威突然抵宋州府门列阵，刘赟关门登楼询问',78,'崇威忽至宋州，','无他也。”',[('郭崇威','在府门外列阵，称受郭威派遣来护卫'),('赟','惊惧，关门登楼问来意')],when='950年十二月澶州军变后，具体列阵日未载',place='宋州府门',note='宿卫是郭崇威对刘赟所作解释，不改写前句拦阻为完全无政治限制。')
add('feng_mediates_guo_yun','冯道劝郭崇威登楼，刘赟握手哭泣，郭崇威安抚',78,'赟召崇威，','崇威以郭威意安谕之。',[('赟','召郭崇威，握其手哭泣'),('郭崇威','经冯道劝说登楼，按郭威意思安抚'),('冯道','出面与郭崇威交谈，促其登楼')],when='950年十二月宋州府门问答后，具体日未载',place='宋州府楼',note='安谕不等于郭威确定同意刘赟即位，原文未记详细保证词，不补。')
sup('feng_mediates_guo_yun',78,song,'贇召崇，崇不敢進，馮道出與崇語，崇乃登樓見贇，已而奪贇部下兵。','《新五代史》也记冯道与郭崇交谈后促其登楼见刘赟，随后刘赟所部兵被夺。','同场同职对应，夺兵的过程另据通鉴张令超归附事件记录。')
add('zhang_lingchao_yun_guard','张令超在宋州率部护卫刘赟',78,'少顷，崇威出，','为赟宿卫，',[('张令超','以护圣指挥使身份率部护卫刘赟'),('赟','由张令超所部护卫')],when='950年十二月宋州会面时，护卫起始日未载',place='宋州',note='少顷为会面后不久，任职与宿卫起始未给，不推当日首次任命。')
add('dong_yi_proposes_escape','董裔劝刘赟夺郭崇威兵，招募士卒北逃晋阳',78,'徐州判官董裔','赟犹豫未决。',[('董裔','提议让张令超夜袭夺兵、掠金募兵北走晋阳'),('赟','听到方案，犹豫未决'),('张令超','被方案拟为夜袭夺兵者'),('郭崇威','成为方案拟袭击夺兵对象')],when='950年十二月宋州会面后、当晚张令超归附前',place='宋州、拟逃晋阳',description='董裔判断郭崇威另有图谋，劝刘赟让张令超夜袭夺其兵，次日夺取睢阳金帛招募士卒、北逃晋阳。刘赟犹豫，未作决定。',note='道路说郭威已为帝是传闻，不提前当正式登基；夺兵、掠金募兵和北逃均是未实行建议，不给实际抵达晋阳坐标。')
add('zhang_lingchao_defects','郭崇威当晚暗中招诱张令超，张率部归附',78,'是夕，',None,[('郭崇威','暗中招诱张令超'),('张令超','率部归附郭崇威'),('赟','失去护卫部队后惊惧')],when='950年十二月董裔建议后的当晚，确切日未载',place='宋州',note='是夕是本场同晚，不强套澶州军变日；密诱未给利益数额，不编贿赂。')
add('guo_letter_recalls_feng','郭威致信刘赟称受军队逼迫，召冯道回京',79,'郭威遗赟书，','王度奉侍。',[('郭威','致书自称为诸军所迫，召冯道先回'),('赟','收到郭威来书，仍由使者奉侍'),('冯道','被召先回京'),('赵上交','奉命留下侍奉刘赟'),('王度','奉命留下侍奉刘赟')],when='950年十二月郭威南返、刘赟在宋州时，具体书信日未载',place='郭威所在军营与宋州',note='被迫为郭威书中说法，不以自述证明策划有无；赵上交沿赵远，奉侍不等于刘赟已安全获准继位。')
sup('guo_letter_recalls_feng',79,det,'太祖以書召道先歸，留其副趙上交、王度奉贇入朝太后。','《新五代史》也记郭威致书召冯道先回，留赵上交、王度陪同刘赟。','新传说奉赟入朝是安排，未当刘赟已经到京；主书奉侍保留。')
add('yun_questions_feng','刘赟问冯道如何应对被夺护卫兵，冯道沉默',79,'道辞行，','道默然。',[('赟','在冯道辞行时说明信任旧相，问如何应对危局'),('冯道','面对刘赟问计沉默')],when='950年十二月冯道离宋州前，具体日未载',place='宋州',note='三十年旧相是刘赟话语，未据此计算冯道任相精确累计年数；沉默不补心理动机。')
add('jia_zhen_threatens_feng','贾贞以眼色示意想杀冯道，刘赟制止',79,'客将贾贞','此无预冯公事。”',[('贾贞','多次以眼色示意想杀冯道'),('冯道','受到贾贞威胁'),('赟','制止部属，认为此事不关冯道')],when='950年十二月冯道辞行时',place='宋州',note='数目为多次用眼色示意，不译现代人数；欲杀未执行，不写冯道被杀。')
sup('jia_zhen_threatens_feng',79,det,'贇客將賈正等數目道，欲圖之。贇曰：「勿草草，事豈出於公邪！」','《新五代史》同场记客将贾正以眼色示意想对冯道动手，刘赟阻止。','贾正与通鉴贾贞同客将身份、辞别场景及后来被杀事件相接，按同人保留异名字形，不新建第二人。')
add('guo_chongwei_detains_yun','郭崇威将刘赟迁入外馆拘禁，杀董裔、贾贞等',79,'崇威迁赟',None,[('郭崇威','将刘赟迁外馆，杀其亲信'),('赟','被迁入外馆拘禁，亲信被杀'),('董裔','被郭崇威一方杀害'),('贾贞','被郭崇威一方杀害')],when='950年十二月宋州辞行问答之后，具体杀害日未载',place='宋州外馆',note='外馆沿史载名称，不当具体监狱坐标；刘赟被拘而非本句已杀，亲信等数人未以数目猜总人数。')
sup('guo_chongwei_detains_yun',79,det,'道已去，郭崇幽贇于外館，殺賈正及判官董裔、牙內都虞候劉福、孔目官夏昭度等。','《新五代史》也记郭崇将刘赟拘禁外馆、杀贾正和董裔，并补列刘福、夏昭度。','新传明确在冯道离去后；人物姓名职务按独立书证补充，刘福加身份限定，与其他同名人物不合并。',relation='adds')
for name in ['董裔','贾贞']:
 claim('person',people[name],'death_year',name+'于950年十二月在刘赟被拘禁宋州时遭杀害。',79,'崇威迁赟于外馆，杀其腹心董裔、贾贞等数人。','本段尚未记刘赟被杀，不将其亲信死亡与951年刘赟死亡混作一件。')
# Supplement-only participants rely on their independently exported biography text.
q='道已去，郭崇幽贇于外館，殺賈正及判官董裔、牙內都虞候劉福、孔目官夏昭度等。'
for name,role in [('刘福（刘赟将领）','以牙内都虞候身份，在刘赟被拘禁宋州时遭杀害'),('夏昭度','以孔目官身份，在刘赟被拘禁宋州时遭杀害')]:
 pk=person(name,79,role,q,source=det);key='participation_zztj_289_0950_guo_chongwei_detains_yun_'+pk
 B['person_events'].append(dict(key=key,person_key=pk,event_key=E['guo_chongwei_detains_yun'],role=role,status='draft'))
 claim('person_event',key,'role',name+'：'+role+'。',79,q,'姓名与职务出自《新五代史》刘赟传，通鉴本句只列董裔、贾贞等；补证指向同一拘禁事件，不套未载确日。',source=det)
add('lady_deposes_yun','李太后于己未下诰，废刘赟为湘阴公',80,'己未，',None,[('太后','下诰废嗣君刘赟为湘阴公'),('赟','失去嗣君身份，被封湘阴公')],when='950年十二月己未',place='后汉朝廷、宋州',note='废嗣并非废实际在位皇帝，刘赟尚未入京登基。')
sup('lady_deposes_yun',80,dec,'己未，太后誥曰：','《旧五代史》也将废刘赟的太后诰令记在己未。','已读全文诰的封湘阴公及爵秩内容；旧本纪把监国条列在前而废诰己未后列，保持各书原序不按排列推新日期。',field='time_original')
sup('lady_deposes_yun',80,dep,'太祖已監國，太后乃下誥曰：','《新五代史》刘赟传先说郭威已监国，随后记废刘赟诰令。','与通鉴己未废嗣、庚申监国的先后不同；新传末贇以幽死不定确日，刘赟死亡留待951年主书纪事核对，不能据此提前写950年被杀。',relation='conflicts',field='time_original')
add('ma_duo_enters_xu_liu_xin_dies','马铎率军进入许州，刘信在惶恐中自杀',81,'马鐸引兵',None,[('马鐸','率军进入许州'),('刘信','在惶恐中自杀')],when='950年十二月己未废嗣后条下，具体入城和死亡日未单列',place='许州',note='沿忠武节度使刘信（刘知远从弟）主体，不与无身份限定旧刘信混用。未记马铎杀刘信，不把自杀改成被处死。')
sup('ma_duo_enters_xu_liu_xin_dies',81,dec,'許州巡檢、前申州刺史馬鐸奏，節度使劉信自殺。','《旧五代史》也记马铎奏报节度使刘信自杀。','旧本纪排列在郭威庚申到北郊之后，没有给自杀日；奏报时间不自动作为实际死亡日。')
claim('person',people['刘信（刘知远从弟）'],'death_year','刘信于950年马铎率军入许州时自杀。',81,Q[81]['text'],'主体按忠武节度使和许州核对，原文惶惑为其状态，未确证具体恐惧对象。')
add('lady_names_guo_regent','李太后于庚申下诰，命郭威监国',82,'庚申，','以侍中监国。',[('太后','下诰命侍中郭威监国'),('郭威','获命以侍中身份监国')],when='950年十二月庚申',place='后汉朝廷',note='侍中指承前郭威，监国是代行国政，不能写当日正式登基或后周已改元。')
sup('lady_names_guo_regent',82,zhou,'庚申，太后制以威監國。','《新五代史》周本纪也记庚申太后命郭威监国。','同日相符，周本纪不同于刘赟传先监国后废嗣的叙事顺序。',field='time_original')
sup('lady_names_guo_regent',82,dec,'壬戌，奉太后誥，命樞密使侍中郭威監國，中外庶事，並取監國處分。','《旧五代史》将太后命郭威监国记在壬戌，并记各项事务由监国处理。','通鉴及新周本纪庚申、旧汉本纪壬戌纪日不同，保留两说，不据此猜成两次任命。',relation='conflicts',field='time_original')
add('officials_petition_guo_throne','百官与藩镇接连上表，请郭威即位',82,'百官籓镇','上表劝进。',[('郭威','接到百官与藩镇接连劝进的表章')],when='950年十二月庚申命监国后，具体各表日未载',place='后汉朝廷、各藩镇',note='劝进为请求、不是已经执行登基；没有名单不补每个藩帅表章。')
add('guo_executes_drunken_infantry','郭威于壬戌夜处死醉酒扬言另行拥立的步兵将校',82,'壬戌夜，',None,[('郭威','以监国身份处死醉酒扬言的步兵将校')],when='950年十二月壬戌夜',place='郭威军营',description='军营中一名步兵将校醉酒，声称此前澶州骑兵已拥立，这次步兵也想拥立。郭威将其斩首。',note='将校无姓名，不补拟拥立者或谋反细节；对照此前骑兵拥立为其话语，不另造一次实际步兵兵变。')
add('liu_sheng_female_counsellors','刘晟任卢琼仙、黄琼芝为女侍中，参与政务决断',83,'南汉主以','参决政事。',[('南汉主','任两名宫人为女侍中，让她们参与决断政务'),('卢琼仙','获任女侍中，穿戴朝服冠带参与决断政务'),('黄琼芝','获任女侍中，穿戴朝服冠带参与决断政务')],when='950年十二月条下，具体任命日未载',place='南汉',note='南汉主为刘晟，沿943年更名事实复用刘弘熙主体；女侍中是史载官名，不改成现代首相。')
add('southern_han_old_elite_losses','刘晟统治时，南汉宗室和旧功臣多遭杀害',83,'宗室勋旧，','诛戮殆尽，',[('南汉主','统治时宗室和旧功臣多遭杀害')],year=None,when='刘晟统治期间截至950年条下的概述，未逐项列杀害年月',place='南汉',description='史书在950年条下概述，南汉宗室和旧功臣大多已遭杀害。',note='殆尽是概述，不把所有受害者列为950年同一日死亡，不补未载姓名；各个已有死亡事件仍保留原年。')
add('lin_yanyu_controls_han','南汉政务由林延遇等宦官掌权',83,'惟宦官林延遇',None,[('林延遇','与其他宦官掌握南汉政务'),('南汉主','统治时政务由宦官掌权')],when='950年十二月条下的政局概述，掌权起始日未载',place='南汉',note='林延遇沿935年已在番禺掌国信的闽清宦者主体；等未具名不造其他宦官，未写每项政务均不经君主。')
sup('lin_yanyu_controls_han',83,han,'宦者林延遇、宮人盧瓊仙。內外專恣為殺戮，晟不復省。','《新五代史》也记林延遇、卢琼仙掌权，任意施行杀戮，刘晟不再过问。','本来源前句九年冬为951年，以下为刘晟统治概述，不用来独立证明950年女侍中任命日期，也不把任意杀戮均强系950年。',relation='adds')
reviews={77:'壬子到澶州、癸丑将士闯入黄旗拥南、政治承诺、丙辰韦城书、戊午七里店迎拜及营皋门分录。旧史壬子兵变、新史癸丑到达和皋门迎拜差异保留；事母不造血缘，黄旗不改黄袍，书信不侵扰为自述。',78:'刘赟抵宋、派七百骑拦阻和许州巡检、门外列阵称宿卫、冯调解见楼、张护卫、董拟夺兵逃晋阳、张实际归附分开。道路称郭已为帝是传闻，未执行董方案；郭崇同职同场对应崇威。',79:'郭自称被迫书、召冯留两使、刘问冯沉默、贾眼色欲杀被止、郭拘刘并杀亲信分录。贾贞正同场异名保留；新传补刘福夏昭度职务与参与只用其独立书证，刘福限定身份。尚未记刘赟死亡。',80:'己未废嗣沿主旧，新刘赟传先监国后废的顺序并列，幽死不强系950。未将尚未正式登基的刘赟写成在位皇帝。',81:'马铎入许、刘信惶惑自杀，沿忠武节度使从弟主体，不与旧无身份限定人混用，不改马杀刘。旧史奏报日与死亡日不混。',82:'庚申命监国、接连劝进、壬戌醉步将校被斩分别录。旧汉本纪壬戌监国与主新庚申并列，不造二任。步军言论不造第二场实际拥立，正式登基属951年。',83:'南汉主刘晟沿943更名事实映刘弘熙，不新建人；女侍中两人任职、宗室旧臣多遭杀害概述、宦官掌权分别录。追述死者不全集到950，林沿番禺国信宦者。新史九年冬后概述不当950任命日期独立证据。'}
assert not (P/'publication.json').exists()
for n in range(77,84):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(77,84)],next_paragraph='zztj-v290-y0951-p001',next_volume=290,next_year=951,supplements=supplements,excluded_non_body=[],coverage='卷289原82—88行连续七段；本批发布并逐批审计通过后，950年83/83正文完成；卷末后周纪书名不作史事。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(77,84)],source_issues_review='澶州抵达与兵变纪日、郭威监国纪日及新传废嗣顺序差异并列。贾贞正同人异名保留，刘福加身份限定。新周本纪将刘赟被杀列950年十二月，通鉴951年正月另记，尚不在此生成其死亡事件。南汉新史概述不能独证950任命日期，纸本与转录异文待核。',plain_language_review='首次逐条检查标题、正文、参与动作、人物介绍及事实说明，使用现代白话并保留原引文。事母不作血缘，拥立和监国不作正式登基，传闻、自述、计划和已执行动作区分；未知时间和异说明示，未安排固定二次文案审阅。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
