# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 285, year 946 paragraphs 25–30."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,57))
COMMIT='bf9e990066dba1dacd217dcd86a7c0d28b93b91c'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-285-946-august-october','jiuwudaishi-084-946-zhao-correspondence']:
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
main_sources = ['tongjian-285-946-august-october','tongjian-285-946-october-november']
B = {'format_version': 1, 'batch_key': 'zztj-v285-y0946-p025-p030',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
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
lines = (ROOT / 'resources/derived/tongjian/285.txt').read_text().splitlines()
for n in range(25, 31):
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
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷285·后晋开运三年（946年九月至十月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_285_0946_04_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=946, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='946年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_285_0946_' + code
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
        edge = 'participation_zztj_285_0946_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'是{a}的{kind}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_285_0946_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'石重贵','唐主':'李璟','杜威':'杜重威','弘佐':'钱弘佐','弘亿':'钱弘亿','昭券':'水丘昭券','德昭':'元德昭','留从效':'留从效','公主':'乐平长公主（杜重威妻）'})
NEW_ALIASES={'王饶':['王饒'],'林赞尧':['林贊堯'],'周承义':['周承義'],'水丘昭券':[],'赵承泰':['趙承泰'],'元德昭':[]}
NEW_DESCRIPTIONS={'王饶':'后晋奉国左厢都指挥使。946年十月辛未，石重贵任命他为北征军的步军右厢都指挥使。《旧五代史》卷85记有相同部署。生卒年及籍贯未载。','林赞尧':'南唐漳州将领。946年十月条下记他作乱，杀监军使周承义及剑州刺史陈诲；泉州刺史留从效起兵将他逐出。陈诲死亡的这条记载与另一史书记载的后续活动有疑问，需进一步核对。林赞尧生卒年未载。','周承义':'南唐监军使。946年十月条下记漳州将林赞尧作乱时杀死他。原文未说明籍贯、年龄和亲属。','水丘昭券':'临安人，吴越内都监使。946年福州求救时，他主张出兵。钱弘佐让他掌管用兵，他因忌惮程昭悦而让出此事。原文未载生卒年。','赵承泰':'吴越统军使。946年十月壬午，钱弘佐派他与张筠率三万兵分水陆救援福州。《新五代史》卷67也记这次派兵。生卒年未载。','元德昭':'危仔倡之子。946年吴越出兵救福州时，钱弘佐把军事谋划交给他。其姓名与父亲异姓按史书记载保留，不据此猜测改姓原因或收养关系；生卒年未载。'}
NEW_DEATH_YEARS={'周承义':946}
sep='946年九月';oct='946年十月';undated='946年北征前的追述，具体年份和月日未载'
j9='jiuwudaishi-084-946-zhao-correspondence';j10='jiuwudaishi-085-946-october';w='xinwudaishi-067-fuzhou-relief'
add('ma_seeks_commander','马希范多次献珍玩给石重贵，请求任都元帅',25,'楚王希范','求都元帅。',[('马希范','多次献珍玩并请求都元帅职'),('帝','史书称其喜奢靡，接受马希范献物')],when='946年九月任命前的追述，献物各次日期未载',year=None,place='楚至后晋朝廷',note='多次献物是追述，未把每一次确定在946年；好奢靡是史书评价。')
add('ma_granted_commander','石重贵任马希范为诸道兵马都元帅',25,'甲辰，',None,[('马希范','被任命为诸道兵马都元帅'),('帝','作出任命')],when=sep+'甲辰',place='后晋朝廷')
sup('ma_granted_commander',25,j9,'甲辰，以天策上將軍、江南諸道都統、楚王馬希範兼諸道兵馬都元帥。','《旧五代史》同记九月甲辰马希范兼诸道兵马都元帅，并列出原有头衔。','只补这次任命，不将原有诸职当作甲辰同时新授。')
add('river_breaches_linhuang','黄河在澶州临黄决口',26,'丙辰，',None,[],when=sep+'丙辰',place='澶州临黄',note='本句河指黄河，不据决口推断死亡人数或现代坐标。')
add('liu_forges_surrender_letter','契丹让刘延祚写信给王峦，声称愿以瀛州归附后晋',27,'契丹使','举城内附。',[('刘延祚','奉契丹命写归附信'),('王峦','以乐寿监军身份收到归附信')],when=sep,place='瀛州至乐寿',note='书信为契丹诱敌安排，不能写成刘延祚真实归降。')
sup('liu_forges_surrender_letter',27,j9,'至是，瀛州守將劉延祚受契丹之命，詐輸誠款，以誘我軍，國家深以為信，遂有出師之議。','《旧五代史》明确说刘延祚奉契丹命假装输诚诱敌，后晋相信而议出兵。','引用本纪正文，不把更早另一次瀛州谋变事件合并到本次。')
add('liu_letter_promises_inside','刘延祚在信中称瀛州契丹兵不足千人，请派兵袭城并愿作内应',27,'且云：','内应。',[('刘延祚','在诱敌信中声称兵少并愿作内应'),('王峦','收到信中袭城建议')],when=sep,place='瀛州至乐寿',note='兵力与内应仅为书信说法，不作为已经核实的城防事实。')
add('liu_letter_claims_no_rescue','刘延祚的信声称多雨积水、契丹主远在牙帐，无法救援关南',27,'又，今秋','不能救也。”',[('刘延祚','在信中用积水路远说明契丹无法救援的说法')],when=sep,place='瓦桥以北、契丹牙帐及关南',note='此为诱敌信内容，不新造契丹主此时已回牙帐的确定行程。')
add('du_wang_recommend_yingmo','王峦与杜重威多次上奏，认为可趁机夺取瀛州、莫州',27,'峦与','可取，',[('王峦','屡奏瀛莫可取'),('杜威','以天雄节度使兼中书令身份共同奏议')],when=sep,place='乐寿、天雄军至后晋朝廷')
add('murong_offers_yingmo_map','慕容迁向后晋献《瀛莫图》',27,'深州刺史','《瀛莫图》。',[('慕容迁','以深州刺史身份献地图')],when=sep,place='深州至后晋朝廷',note='图名照原文；地图的形制、尺度和内容未载，不生成想象疆域。')
add('feng_li_plan_receive_defectors','冯玉、李崧相信归附说法，打算发大军迎接赵延寿和刘延祚',27,'冯玉、',None,[('冯玉','相信奏议，计划发军迎接'),('李崧','相信奏议，计划发军迎接'),('赵延寿','被视作拟迎接的归附者'),('刘延祚','被视作拟迎接的归附者')],when=sep,place='后晋朝廷',note='欲发为计划；不写赵刘已真实归降或此刻已发兵。')
add('du_gifts_li_shouzhen','杜重威厚待路过广晋的李守贞，多次赠送金帛和甲兵',28,'先是，','动以万计。',[('杜威','厚待并赠送大量金帛甲兵'),('李守贞','率军过广晋时受赠')],when=undated,year=None,place='广晋',note='动以万计是史书概数，赠物币值和每类数量未分别载明。')
add('li_du_friendship','李守贞因厚待赠财而与杜重威亲善',28,'守贞由是','亲善。',[('李守贞','因杜重威厚待而亲善'),('杜威','与李守贞建立亲善关系')],when=undated,year=None,place='广晋及后晋',note='亲善是明确叙述；不进一步推为结义或姻亲。')
relationship('李守贞','杜威','朋友',28,span(28,'守贞由是','亲善。'),'原文明示李守贞与杜重威亲善，关系表示政治交好，不推为结义或血亲。')
add('shi_praises_li_spending','石重贵慰劳李守贞，称听说他常用私财奖赏战士',28,'守贞入朝，','战士。”',[('李守贞','入朝接受慰劳'),('帝','称听说李守贞以私财奖士')],when=undated,year=None,place='后晋朝廷',note='闻为皇帝所闻，下一句说明钱财来源，不当作独立证实私财。')
add('li_attributes_rewards_du','李守贞把奖赏战士的钱财归功于杜重威资助，并表示愿共同北征',28,'对曰：','亦贤之。',[('李守贞','称钱财来自杜重威并表示愿协力北征'),('杜威','被李守贞称为资助者'),('帝','听后认为杜重威贤能')],when=undated,year=None,place='后晋朝廷',note='评价和协力表态保留说话人，不当作已经北征成功。')
add('shi_plans_du_commander','石重贵与冯玉、李崧商议，让杜重威统军、李守贞辅佐',28,'及将北征，','守贞副之。',[('帝','参加北征统帅商议'),('冯玉','参加统帅商议'),('李崧','参加统帅商议'),('杜威','拟被任为元帅'),('李守贞','拟辅佐杜重威')],when='946年十月辛未正式任命前',place='后晋朝廷')
add('zhao_opposes_du_command','赵莹私下劝冯玉、李崧只用李守贞领兵，意见未被采纳',28,'赵莹私谓','不从。',[('赵莹','认为杜重威不满足现有权势，劝只用李守贞'),('冯玉','未采纳赵莹建议'),('李崧','未采纳赵莹建议'),('杜威','受到赵莹反对掌兵的批评'),('李守贞','被赵莹推荐独任')],when='946年十月辛未正式任命前',place='后晋朝廷',note='杜重威欲未厌是赵莹的判断，仍明确引述身份，不当心理事实。')
# Each named commander receives a separate appointment, all with the same explicit day.
appointments=[('du_north_command','杜重威','北面行营都招讨使','以威为北面','都招讨使，'),('li_north_monitor','李守贞','兵马都监','以守贞','都监，'),('an_north_wings','安审琦','左右厢都指挥使','泰宁节度使','左右厢都指挥使，'),('fu_cavalry_left','符彦卿','马军左厢都指挥使','武宁节度使','马军左厢都指挥使，'),('huang_cavalry_right','皇甫遇','马军右厢都指挥使','义成节度使','马军右厢都指挥使，'),('liang_cavalry_array','梁汉璋','马军都排阵使','永清节度使','马军都排陈使，'),('song_infantry_left','宋彦筠','步军左厢都指挥使','前威胜节度使','步军左厢都指挥使，'),('wang_infantry_right','王饶','步军右厢都指挥使','奉国左厢都指挥使','步军右厢都指挥使，'),('xue_vanguard','薛怀让','先锋都指挥使','洺州团练使','先锋都指挥使。')]
oldquotes=['以鄴都留守杜威為北面行營都招討使，','以侍衛親軍都指揮使、鄆州節度使李守貞為兵馬都監，','兗州安審琦為左右廂都指揮使，','徐州符彥卿為馬軍左廂都指揮使，','滑州皇甫遇為馬軍右廂都指揮使，','貝州梁漢璋為馬軍都排陣使，','前鄧州宋彥筠為步軍左廂都指揮使，','奉國左廂都指揮使王饒為步軍右廂都指揮使，','洺州團練使薛懷讓為先鋒都指揮使。']
for (code,name,office,start,end),quote in zip(appointments,oldquotes):
 add(code,f'石重贵任{name}为{office}',28,start,end,[(name,f'被任命为{office}')],when=oct+'辛未',place='后晋北面行营',note='月日由同段冬十月辛未统一限定；原有节度职不是此次全部新授。')
 sup(code,28,j10,quote,f'《旧五代史》也记十月辛未{name}被任命为{office}。','本纪正文印证，州名与节镇名分别保留；括注引通鉴不是独立来源，不使用括注作确证。')
add('shi_announces_north_campaign','后晋发布北征敕榜，提出先取瀛莫，再取幽燕及塞北',28,'仍下敕榜','荡平塞北。”',[],when=oct+'辛未部署后',place='瀛州、莫州、关南、幽燕、塞北',note='这份敕榜记行动目标，不写已经占领这些地区。')
add('shi_rewards_capture_khitan','后晋承诺擒获契丹主者获上镇节度使及钱绢银赏赐',28,'又曰：','银万两。”',[],when=oct+'辛未部署后',place='后晋',note='承诺钱万缗、绢万匹、银万两；未记实际兑现。',description='后晋公布奖赏：擒获契丹主者授上镇节度使，赏钱一万缗、绢一万匹、银一万两。')
add('persistent_rain_hinders_army','六月以来持续降雨，至十月仍未停止，行军运粮艰苦',28,'时自六月',None,[],when='946年六月至十月',place='后晋北征道路',note='不从史载积雨推算每一日降雨量，也不新造具体灾民数。')
add('lin_rebels_kills_zhou_chen','林赞尧在漳州作乱，史书记载他杀周承义、陈诲',29,'唐漳州将','刺史陈诲。',[('林赞尧','作乱并被记为杀监军及刺史'),('周承义','以监军使身份被杀'),('陈诲','本句记剑州刺史陈诲被杀')],when=oct+'条下，具体日未载',place='漳州',note='陈诲死亡一事与《新五代史》卷62后来仍记陈诲参战存在疑问；本批保留通鉴此条及待核，不强改原文、不将人物death_year确定为946。')
sup('lin_rebels_kills_zhou_chen',29,'xinwudaishi-062-chen-hui-later','文徽與劍州刺史陳誨下舟閩江趨應之。','《新五代史》在南唐八年条下仍记剑州刺史陈诲随查文徽出兵，与946年被杀记载存在时序疑问。','本条只作死亡记载的异说校核，不提前录入八年战事，也不推定陈诲死年；须进一步核对底本、人物身份和纪年。',relation='conflicts')
add('liu_expels_lin','留从效起兵逐出林赞尧，让董思安暂掌漳州',29,'泉州刺史','权知漳州。',[('留从效','起兵逐出林赞尧，安排临时州政'),('林赞尧','被留从效逐出'),('董思安','以泉州裨将身份暂掌漳州')],when=oct,place='泉州、漳州')
add('dong_declines_zhangzhou','李璟任董思安为漳州刺史，董因父名章而推辞',29,'唐主以思安','父名章。',[('唐主','任命董思安为漳州刺史'),('董思安','因父亲名章而推辞')],when=oct,place='南唐朝廷及漳州',note='父亲未给全名，不臆造董章的新实体；章漳相避为其辞任理由。')
add('li_renames_nanzhou_orders_attack','李璟把漳州改为南州，命董思安、留从效带州兵攻福州',29,'唐主改','会攻福州。',[('唐主','改州名并命两人会攻'),('董思安','奉命带州兵攻福州'),('留从效','奉命带州兵攻福州')],when=oct,place='漳州改南州、泉州至福州')
add('tang_besieges_fuzhou_october','南唐州兵围攻福州',29,'庚辰，','围之。',[],when=oct+'庚辰',place='福州',note='围之承接两州兵会攻，不补战役人数或城墙坐标。')
add('fuzhou_envoy_wuyue_council','福州使者到钱塘求救，吴越诸将认为路远难救，水丘昭券主张援助',29,'福州使者','以为当救。',[('弘佐','召诸将商议福州求救'),('昭券','主张救福州')],when=oct,place='钱塘',note='未具名反对将领和福州使者不造人物；昭券的临安籍贯据句。')
add('qian_insists_fuzhou_relief','钱弘佐用唇亡齿寒的道理要求救福州，责问诸将',29,'弘佐曰：','安坐邪！”',[('弘佐','认为救邻道是元帅职责，责问诸将')],when=oct,place='钱塘',note='这是钱弘佐的主张，不将责问当作所有将领实际饱食安坐的事实。')
add('qian_sends_three_million_relief','钱弘佐派张筠、赵承泰率三万人分水陆救福州',29,'壬午，',None,[('弘佐','下令派三万兵救援'),('张筠','以统军使身份率军救福州'),('赵承泰','以统军使身份率军救福州')],when=oct+'壬午',place='吴越至福州',note='总兵三万，不分别算每位将领各三万；出兵不等于已解围。')
sup('qian_sends_three_million_relief',29,w,'乃遣其統軍使張筠、趙承泰等率兵三萬，水陸赴之。','《新五代史》也记钱弘佐派张筠、赵承泰等率三万兵水陆救援。','同传接着叙获胜是后续结果，尚不提前录入本段。')
add('qian_recruitment_shortfall','吴越此前募兵，长时间没有人响应',30,'先是募兵，','应者，',[],when='946年救福州前的追述，具体年份月日未载',year=None,place='吴越',note='未说明应募范围与已存在兵数，不扩大为吴越无人愿服役。')
add('qian_drafts_half_rations','钱弘佐下令征集士兵，并规定被征入伍者粮赐减半',30,'弘佐命纠之，','减半。”',[('弘佐','规定被征集入伍者粮赐减半')],when='946年救福州前的募兵追述，具体日期未载',year=None,place='吴越',note='纠解释为征集；应募者与征集者待遇区别，未记具体粮额。')
add('qian_volunteers_next_day','减半待遇规定公布后，次日应募者大量到来',30,'明日，','云集。',[],when='前述募兵规定次日，绝对年月日未载',year=None,place='吴越',note='次日是相对时间；不套为十月壬午次日。')
add('shuiqiu_yields_command','钱弘佐让水丘昭券掌用兵，昭券因忌惮程昭悦而让出',30,'弘佐命昭券','让之。',[('弘佐','让水丘昭券专掌用兵'),('昭券','忌惮程昭悦，提出让其掌用兵'),('程昭悦','成为水丘昭券让事的对象')],when='946年救援福州部署时，具体日未载',place='吴越',note='让之为提议或交让，随后正式任务另录，不造程昭悦任最高统帅。')
add('qian_assigns_logistics_strategy','钱弘佐让程昭悦管援军供给，把军事谋划交给元德昭',30,'弘佐命昭悦','元德昭。',[('弘佐','分别安排供给和军谋'),('程昭悦','掌援军供给运输'),('德昭','受委托掌军事谋划')],when='946年救援福州部署时，具体日未载',place='吴越')
relationship('危仔倡','德昭','父亲',30,span(30,'德昭，','之子也。'),'《资治通鉴》明确元德昭为危仔倡之子；异姓照录，不推收养或更名原因。')
add('qian_proposes_iron_money','钱弘佐提议铸铁钱，增加将士俸禄赏赐',30,'弘佐议','禄赐，',[('弘佐','提议铸铁钱增禄赐')],when='946年救援福州期间，具体日未载',place='吴越',note='议是提议，后文因劝谏停止；不写吴越已实行铁钱。')
add('qian_hongyi_eight_objections','钱弘亿提出铸铁钱的八项弊害，钱弘佐停止计划',30,'其弟牙内','弘佐乃止。',[('弘亿','以牙内都虞候身份提出八项反对意见'),('弘佐','听取劝谏，停止铸铁钱计划')],when='946年救援福州期间，具体日未载',place='吴越',note='八害是钱弘亿判断；第八项钱姓不祥属于其说法，不作为客观因果。',description='钱弘亿反对铸铁钱：他担心旧钱外流、跨境贸易受阻、私铸增加、重蹈闽国乱亡、显得财力不足、无故增赏引发无尽要求、制度变坏后难以恢复，并以钱为国姓提出不祥的说法。钱弘佐因此停止计划。')
relationship('弘亿','弘佐','弟弟',30,span(30,'其弟牙内','谏曰：'),'原文明示钱弘亿是钱弘佐的弟弟，方向为弟弟指向兄长；保留已有关系身份。')
add('du_li_march_from_guangjin','杜重威、李守贞在广晋会军，向北进发',30,'杜威、','北行。',[('杜威','在广晋会军北行'),('李守贞','会军并与杜重威北行')],when='946年十月北征，具体日未载',place='广晋北行')
add('du_requests_more_palace_troops','杜重威多次让公主上奏增兵，禁军集中北征使宫廷守卫空虚',30,'威屡使公主',None,[('杜威','借公主反复请求增兵'),('公主','入奏请求增兵')],when='946年十月北征，具体日未载',place='北征军至后晋朝廷',note='公主据已有杜重威妻乐平长公主身份识别；不新造未名传令者。全部禁军集中是原文概括，不虚补兵数。')
reviews={25:'献物是任命前追述，具体献物时间未定；甲辰授职据通鉴和旧五代史。',26:'黄河临黄决口据九月丙辰；灾情未补数量。',27:'瀛州来信是诱敌，兵力、内应和水阻均注明书信声称；旧五代史正文补明假降，地图只录献图事实。',28:'赠财交好与朝中褒扬为追述，年份未定；建议与十月辛未正式部署分开，九将逐项校核旧本纪；敕榜目标和奖赏未当执行结果。',29:'陈诲946被杀与新五代史后续陈诲活动疑问保留待核，不定人物死年；董思安父仅名章不新建无全名人。吴越派兵日壬午，三万为总数，不提前录后续胜仗。',30:'募兵相对明日不挂派兵次日。军谋与馈运职责分开，元危父子异姓不猜收养，弘亿明确为弟。八害是劝谏理由非客观结论；北征与宿卫空虚按明载，不补人数。'}
assert not (P/'publication.json').exists()
for n in range(25,31):
 assert ledger[n-1]['status']=='pending' or (ledger[n-1]['status']=='reviewed' and ledger[n-1]['batch_key']==B['batch_key'])
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=285,year=946,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(25,31)],next_paragraph=Q[31]['id'],next_volume=285,next_year=946,supplements=supplements,excluded_non_body=[],coverage='卷285原55—60行连续六段，发布后946年累计30/56，余26段。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(25,31)],source_contexts=[dict(source_key=main_sources[0],note='只续录25—28段，不重录19—24。'),dict(source_key=main_sources[1],note='只录29—30段，十一月行营、瀛州追战、中度桥等在后批继续。'),dict(source_key=w,note='只补救福州出兵三万；后续败南唐及俘将尚不提前。')],source_issues_review='陈诲死记与新史后续活动留待核，不改原文或确定人物死年；州名节镇名分别，追述和相对次日不强定日。',plain_language_review='首次逐项检查展示字段、事实说明、身份时间与关系方向；明确传闻、计划、劝谏和执行，原文摘录逐字保留。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
