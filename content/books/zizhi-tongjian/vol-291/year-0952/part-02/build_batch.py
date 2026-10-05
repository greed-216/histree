# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 952 paragraphs 8–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,26))
COMMIT='13c4dafe3d5c65d384d4d803f7681d5baf78489e'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-291-952-september']:
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
main_sources = ['tongjian-291-952-september','tongjian-291-952-october']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0952-p008-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-952-september':'卷291·广顺二年·九月至十月及卷首年界','tongjian-291-952-october':'卷291·广顺二年十月至十二月','jiuwudaishi-112-october-952':'卷112·太祖本纪三·广顺二年十月','jiuwudaishi-112-november-952-hunan':'卷112·太祖本纪三·广顺二年十一月荆南奏报','jiuwudaishi-112-december-952-hunan':'卷112·太祖本纪三·广顺二年十二月刘言奏报','jiuwudaishi-112-january-953-yeji':'卷112·太祖本纪三·广顺三年正月','xinwudaishi-66-liuyan-hunan':'卷66·楚世家第六·刘言','xinwudaishi-66-zhouxingfeng-hunan':'卷66·楚世家第六·周行逢'}
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
lines = (ROOT / 'resources/derived/tongjian/291.txt').read_text().splitlines()
for n in range(8, 17):
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
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if key in prior_source_registry}, []

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
    labels={'tongjian-291-952-september':'卷291·广顺二年·九月至十月及卷首年界','tongjian-291-952-october':'卷291·广顺二年十月至十二月','jiuwudaishi-112-october-952':'卷112·太祖本纪三·广顺二年十月','jiuwudaishi-112-november-952-hunan':'卷112·太祖本纪三·广顺二年十一月荆南奏报','jiuwudaishi-112-december-952-hunan':'卷112·太祖本纪三·广顺二年十二月刘言奏报','jiuwudaishi-112-january-953-yeji':'卷112·太祖本纪三·广顺三年正月','xinwudaishi-66-liuyan-hunan':'卷66·楚世家第六·刘言','xinwudaishi-66-zhouxingfeng-hunan':'卷66·楚世家第六·周行逢'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·广顺二年（952年十月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0952_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=952, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='952年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0952_' + code
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
        edge = 'participation_zztj_291_0952_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0952_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','唐主':'李璟','谷':'李谷','薄公益':'蒲公益','王进逵':'王逵'})
NEW_ALIASES={'郭再诚':['郭再誠'],'刘承遇':['劉承遇'],'李师德':['李師德'],'宋德权':['宋德權'],'郭彦钦':['郭彥欽']}
NEW_DESCRIPTIONS={'郭再诚':'南唐指挥使。952年十月受边镐派遣率兵驻益阳，抵御朗州军。生卒年未载。','刘承遇':'南唐驻沅江都监。952年十月王逵等攻下沅江时被俘。生卒年未载。','李师德':'南唐裨将。952年十月沅江被攻下时率五百人投降王逵等。生卒年未载。','宋德权':'南唐岳州刺史。952年十月朗州军攻岳州时逃走，《旧五代史》奏报也记其弃城。生卒年未载。','郭彦钦':'后周庆州刺史。《资治通鉴》记其为索取贿赂而侵扰野鸡族，导致当地反抗及商旅遭抢掠。生卒年未载。'}
oldoct='jiuwudaishi-112-october-952';oldnov='jiuwudaishi-112-november-952-hunan';olddec='jiuwudaishi-112-december-952-hunan';oldjan='jiuwudaishi-112-january-953-yeji';newliu='xinwudaishi-66-liuyan-hunan';newzhou='xinwudaishi-66-zhouxingfeng-hunan'
add('langzhou_advances_changsha','王逵等分路进军长沙，以孙朗、曹进为先锋',8,'冬，十月，','以孙朗、曹进为先锋使，',[('王逵','率军分路进军长沙'),('孙朗','担任先锋使'),('曹进','担任先锋使')],when='952年十月，出兵日《通鉴》未载',place='朗州至长沙',note='底本长少疑为长沙之讹，依据同段长沙、潭州及旧史趋长沙校读展示；摘录保持长少原字。')
sup('langzhou_advances_changsha',8,oldnov,'朗州大將劉言，以今年十月三日領兵趨長沙，十五日至潭州，','《旧五代史》十一月荆南奏报称刘言率军于十月三日向长沙进发、十五日至潭州。','该奏报以刘言领兵，与《通鉴》王逵等实际出兵的叙述范围不同；分别保留统率表述，不能据奏报认定刘言亲自参加所有战斗。',relation='adds')
add('bian_sends_guo_yiyang','边镐派郭再诚等率军驻益阳抵御朗州军',8,'边镐遣指挥使郭再诚','以拒之。',[('边镐','派郭再诚等驻军益阳迎敌'),('郭再诚','率兵驻守益阳')],when='952年十月朗州军进发后',place='益阳')
add('wang_captures_yuanjiang','王逵等攻下沅江，俘获刘承遇，李师德率五百人投降',8,'戊子，逵等克沅江，','帅众五百降之。',[('王逵','率军攻下沅江'),('刘承遇','以都监身份被俘'),('李师德','率五百人投降')],when='952年十月戊子',place='沅江')
add('wang_captures_yiyang','朗州军举小船遮蔽身体，攻破益阳营寨，杀死二千名守军',8,'壬辰，逵等命军士','杀戍兵二千人。',[('王逵','命军士举船遮蔽并攻下益阳')],when='952年十月壬辰',place='益阳',note='数量为史书记载的守军死亡数，没有换算现代精确统计；小舟自蔽不解释为火器或装甲。')
sup('wang_captures_yiyang',8,newzhou,'進逵攻邊鎬，行逢別破益陽，殺李景兵二千餘人，擒其將李建期。','《新五代史》周行逢传记周行逢另攻益阳，杀南唐兵二千余人，俘获李建期。','主书王逵等与传记周行逢另攻互补，伤亡二千与二千余并列；不把李建期与主书此前郭再诚合为一人。',relation='adds')
for name,role in [('周行逢','据《新五代史》率军另攻益阳'),('李建期','据《新五代史》在益阳被俘')]:
 quote='進逵攻邊鎬，行逢別破益陽，殺李景兵二千餘人，擒其將李建期。';pk=person(name,8,role,quote,source=newzhou);edge='participation_zztj_291_0952_wang_captures_yiyang_'+pk
 B['person_events'].append(dict(key=edge,person_key=pk,event_key=E['wang_captures_yiyang'],role=role,status='draft'));claim('person_event',edge,'role',name+'：'+role+'。',8,quote,'本条参与依据周行逢传，未外推该传后续任职到本次战斗。',source=newzhou)
add('bian_appeals_for_help','边镐向南唐告急求援',8,'边镐告急于唐。','边镐告急于唐。',[('边镐','向南唐告急请求援助')],when='952年十月益阳失守后',place='湖南、南唐')
add('wang_captures_qiaokou_xiangyin','王逵等攻下桥口与湘阴',8,'甲午，逵等克桥口','及湘阴，',[('王逵','率军攻下桥口、湘阴')],when='952年十月甲午',place='桥口、湘阴')
add('wang_reaches_tanzhou','王逵等抵达潭州，边镐守城，援军尚未到达',8,'乙未，至潭州。','城中兵少。',[('王逵','率军抵达潭州'),('边镐','在城中兵少、援军未至时守城')],when='952年十月乙未抵达潭州；守城情况承接此事',place='潭州')
add('bian_abandons_tanzhou','边镐夜间弃潭州逃走，吏民随之溃散',8,'丙申夜，镐弃城走，','吏民俱溃。',[('边镐','夜间弃城逃走')],when='952年十月丙申夜',place='潭州')
sup('bian_abandons_tanzhou',8,newliu,'言不從，遣進逵與行軍司馬何景真等攻鎬於長沙，鎬敗走。','《新五代史》也记刘言派王进逵、何景真等攻长沙，边镐败走。','王进逵为既有人物王逵的别名；何景真与何敬真按同役同官对应作姓名异文补证，未另造同场人物。')
sup('bian_abandons_tanzhou',8,olddec,'於十月十三日，與節度副使王進逵、行軍司馬何敬貞、指揮使周行逢等，同共部領戰棹，攻收湖南，偽節度使邊鎬當夜出奔，王進逵等已入潭州。','《旧五代史》十二月刘言奏报则记十月十三日共同率舟军进攻，边镐当夜逃走、王进逵等已入潭州。','十二月为奏报时间，不是战事时间；十三日与十一月奏报十五日至潭州有差异，保留两条奏报及主书记日，不强定公历。',relation='conflicts',field='time_original')
add('liling_bridge_disaster','潭州溃散时醴陵门桥断裂，史书记载死亡一万余人',8,'醴陵门桥折，','死者万馀人，',[],when='952年十月边镐弃城、吏民溃散时',place='潭州醴陵门桥',note='醴陵门为潭州城门名称，不能将地点直接写为醴陵县；万人为原书估计，未给死者逐一身份。')
add('liao_yan_killed','道州刺史廖偃被乱兵杀死',8,'道州刺史廖偃','为乱兵所杀。',[('廖偃','在潭州溃散时被乱兵杀死')],when='952年十月边镐弃城后的混乱中',place='潭州',note='不将乱兵擅自指定为某一方的某名将领。')
add('wang_claims_command_tanzhou','王逵进入潭州，自称武平节度副使并暂掌军府，任何敬真为行军司马',8,'丁酉旦，王逵入城，','以何敬真为行军司马。',[('王逵','入城后自称节度副使、暂掌军府并任命何敬真'),('何敬真','获任行军司马')],when='952年十月丁酉早晨',place='潭州',note='自称不等于已获后周正式册授，权知军府事为暂掌军府。')
add('he_jingzhen_pursues_bian','王逵派何敬真等追击边镐，没有追上，追兵杀死五百人',8,'遣敬真等追镐，','斩首五百级。',[('王逵','派何敬真等追击'),('何敬真','追击边镐未赶上，所部斩首五百')],when='952年十月王逵进入潭州后',place='潭州外追击途中',note='五百人的逐一身份未载，不当作边镐被俘或阵亡。')
add('pu_captures_yuezhou','蒲公益攻岳州，宋德权逃走，刘言让蒲公益暂掌岳州',8,'薄公益攻岳州，','刘言以公益权知岳州。',[('薄公益','攻岳州并受命暂掌岳州'),('宋德权','以南唐岳州刺史身份逃走'),('刘言','让公益暂掌岳州')],when='952年十月湖南反攻期间，具体攻城日未载',place='岳州',note='前段十指挥使写蒲公益，此处写薄公益；结合公益之名及连续反攻军府复用蒲公益，保留姓氏异文，纸本未核。')
claim('person',people['蒲公益'],'aliases','《通鉴》前段写蒲公益，本段攻岳州时写薄公益，按连续军府行动复用主体，保留姓氏异文。',8,'薄公益攻岳州，唐岳州刺史宋德权走，刘言以公益权知岳州。','异文尚未核纸本，暂不改规范姓名或据此另建人物；此条仅保存不同写法的证据。')
sup('pu_captures_yuezhou',8,oldnov,'淮南所署湖南節度使邊鎬、岳州刺史宋德權並棄城遁去。','《旧五代史》荆南奏报也称宋德权弃城逃走。','该句未给岳州被攻下的具体日，不把前句十五日至潭州当作岳州攻城日期。')
add('liuyan_recovers_hunan','南唐湖南守将相继逃走，刘言收复马氏岭北故地，郴州与连州已入南汉',8,'唐将守湖南诸州者，',None,[('刘言','收复马氏岭北故地')],when='952年十月长沙失守后',place='湖南、郴州、连州',note='仅按原书概述恢复范围，不能据此画出确定疆域；郴连归南汉是范围说明，未擅定两州归属改变之日。')
add('khitan_flood_displacement','契丹瀛、莫、幽州发生大水，数十万流民进入河北，契丹州县未禁止',9,'契丹瀛、莫、幽州', '契丹州县亦不之禁。',[],when='952年十月条下，具体洪灾起止未载',place='瀛州、莫州、幽州至河北',note='数十万人为史书群体规模，未认定每个人均为原被掳人口。')
add('guo_relief_displaced','郭威命流民所在地赈济安置，此前被契丹掳走者有五六成得以回归',9,'诏所在赈给存处之，',None,[('帝','命各地救济并安置入境流民')],when='952年十月流民入河北以后',place='河北',note='什五六为主书所记回归比例，非全部流民的族属比例，未当精确现代人口统计。')
sup('khitan_flood_displacement',9,oldoct,'丁未，滄州奏，自十月已前，蕃歸漢戶萬九千八百戶。是時，北境饑謹，人民轉徙，繈負而歸中土者，散居河北州縣，凡數十萬口。','《旧五代史》记十月丁未沧州奏报，此前归入后周者一万九千八百户，并概述北境饥荒及数十万人迁入河北。','户与口是不同计数，奏报一地户数不能换算全部流民人数；旧书强调饥荒，主书记洪灾，分别保留。',relation='adds')
add('ligu_requests_resignation','李谷臂伤长期未愈，三次上表请求辞职',10,'丁未，谷以病臂','三表辞位，',[('谷','因臂伤未愈三次请求辞职')],when='952年十月丁未，《通鉴》纪日',place='后周朝廷')
sup('ligu_requests_resignation',10,oldoct,'甲辰，宰臣李穀以臂傷未愈，上表辭位，凡三上章，詔報不允。','《旧五代史》记李谷三次辞职及未获准，纪日为十月甲辰。','三次辞职与拒绝相合，甲辰与《通鉴》丁未不同，可能记录不同环节，尚未校定，不覆盖主书记日。',relation='conflicts',field='time_original')
add('guo_refuses_ligu_resignation','郭威派中使劝李谷，并在金祥殿拒绝其辞职，李谷恢复办公',10,'帝遣中使谕指曰：','谷不得已复视事。',[('帝','派中使劝慰，并当面拒绝辞职'),('谷','入金祥殿陈述后恢复办公')],when='952年十月李谷请求辞职以后',place='金祥殿',note='郭威允许其不必勉强参加朝礼，不将此写成免除三司工作。')
add('ligu_uses_name_seal','李谷仍不能执笔，郭威准许他刻姓名印处理三司事务',10,'谷未能执笔，',None,[('谷','因无法执笔获准使用姓名印'),('帝','准许刻名印处理三司事务')],when='952年十月李谷恢复办公后',place='后周三司',note='刻名印为处理繁重事务的安排，不推出任何后世签章制度。')
add('guo_litigation_hierarchy','郭威规定诉讼先由县、州和观察使处理，不公时才可向台省申诉',11,'辛亥，敕：','乃听诣台省，',[('帝','规定诉讼处理层级及向台省申诉的条件')],when='952年十月辛亥',place='后周',note='台省保留当时官署称谓，不直接套为现代法院。')
add('guo_petition_writing_rules','郭威规定代写诉状者须注明姓名住所，无人代写可持白纸申诉',11,'或自不能书牒，','听执素纸。',[('帝','规定代写人登记及无法书写时的申诉办法')],when='952年十月辛亥',place='后周')
add('guo_prohibits_proxy_litigation','郭威规定诉讼须为本人之事，禁止夹带私怨替他人争讼',11,'所诉必须己事，',None,[('帝','禁止以私人动机替他人提起诉讼')],when='952年十月辛亥',place='后周',note='挟私客诉按上下文解释为怀私代人争讼，未推成全面禁止任何诉讼代理；引文保留敕令原字。')
add('guo_yanqin_extorts_yeji','郭彦钦为索贿侵扰多有羊马的野鸡族，引起反抗及商旅遭劫',12,'庆州刺史郭彦钦','剽掠纲商。',[('郭彦钦','为索取贿赂故意侵扰野鸡族')],when='952年十月条下，侵扰与反抗的具体起止未载',place='庆州',note='野鸡族为原书记载的部族名，未自动映射现代民族；性贪为史书评价。')
add('guo_orders_ninghuan_campaign','郭威命宁州、环州合兵讨伐野鸡族',12,'帝命宁、环二州',None,[('帝','命宁州、环州合兵讨伐')],when='952年十月条下，《通鉴》记载的命令',place='宁州、环州、庆州')
sup('guo_orders_ninghuan_campaign',12,oldjan,'邠州奏，慶州略蕃部野雞族略奪商旅，侵擾州界。詔遣寧州刺史張建武等率兵掩襲，仍先賜敕書安撫，如不從命，即進軍問罪。','《旧五代史》在953年正月记同一地区野鸡族劫掠，并命张建武等率军，先以敕书安抚，不从再进兵。','两书记载命令的时间和细节不同，可能涉及同一冲突的后续部署；保持953年与先安抚的条件，未提前断言952年已执行该具体步骤。',relation='adds')
add('liuyan_reports_hunan_recovery','刘言派使上表后周，称未奉诏而集兵收复湖南',13,'刘言遣使奉表来告，',None,[('刘言','派使向后周报告收复湖南')],when='952年十月湖南反攻后，具体奉表日未载',place='湖南至后周朝廷',note='邻寇与义兵是刘言上表中的自述，不作为本站对南唐的定性；不奉诏指未经后周命令举兵。')

# Southern Tang aftermath continues the same uninterrupted October narrative.
ALIASES.update({'冯延己':'冯延巳'})
add('bian_exiled_rao','李璟剥夺边镐官爵，将他流放饶州',14,'唐主削边镐官爵，','流饶州。',[('唐主','剥夺边镐官爵并流放饶州'),('边镐','被剥夺官爵、流放饶州')],when='952年十月湖南失守后，处分日未载',place='南唐、饶州')
add('bian_jianzhou_mercy','边镐此前随查文徽攻建州时保全俘虏，建州人称他为边佛子',14,'初，镐以都虞候','建人谓之“边佛子”；',[('边镐','以都虞候身份参战并保全俘虏'),('查文徽','率军攻取建州')],year=None,when='攻取建州时的追述，具体年月本段未载',place='建州',note='初明确引出此前经历，不归入952年；边佛子为建州人的称呼，未将评价当作宗教身份。')
add('bian_tanzhou_orderly_entry','边镐攻下潭州后商铺照常营业，潭州人称他为边菩萨',14,'及克潭州，','潭人谓之“边菩萨”；',[('边镐','入潭州后维持市场营业，获得边菩萨称呼')],year=951,when='951年南唐攻取潭州后，此处为追述',place='潭州',note='年份依据此前已录卷290广顺元年潭州被南唐接收的连续主线；当前事件记录入城后的市场及评价，不重复建立攻城事件。')
add('bian_rituals_disappoint_tanzhou','边镐任节度使后政务缺乏秩序，频繁设斋修佛事，潭州人失望称他为边和尚',14,'既而为节度使，',None,[('边镐','任节度使期间频繁设斋修佛事，被潭州人批评')],year=None,when='951年接管湖南后至952年失守前的概述，具体起止未载',place='潭州',note='边和尚为民众失望后的称呼，不能据此说边镐已经正式出家；不是反复记录某天的具体斋会。')
add('feng_sun_request_punishment','冯延巳与孙晟上表请求受罚，李璟都予以宽免',15,'左仆射同平章事冯延己','皆释之。',[('冯延己','上表请求受罚，获宽免'),('孙晟','上表请求受罚，获宽免')],when='952年十月湖南失守后的南唐善后，具体上表日未载',place='南唐朝廷',note='左、右仆射同平章事为原官职；释之解释为宽免所请罪罚，不编为曾被投入监狱。')
add('feng_sun_removed_chancellorship','孙晟持续请求处分，最终与冯延巳一同罢相，保留本官',15,'晟陈请不已，',None,[('孙晟','继续请求处分，随后罢相保留本官'),('冯延己','与孙晟一同罢相，保留本官')],when='952年十月两人请求受罚以后',place='南唐朝廷',note='皆罢守本官为罢同平章事而守本官，不解释为罢尽所有官职或流放。')
add('li_jing_discusses_rest','李璟因连续出兵无功，提出停止战争、让百姓休息',16,'唐主以比年出师无功，','乃议休兵息民。',[('唐主','因连年出兵无功而讨论休兵息民')],when='952年十月湖南失守后',place='南唐朝廷',note='议为提出讨论，不当作此后已经永久停战。')
add('li_jing_promises_no_more_war','有人建议数十年不动兵，李璟表示打算终身不用兵',16,'或曰：','何数十年之有！”',[('唐主','回应劝谏，表示打算终身不用兵')],when='952年十月休兵讨论时',place='南唐朝廷',note='这是当时的言论与计划，不是对其后来统治实际战争情况的结论；劝谏者未具名。')
add('ouyang_guang_jishui_magistrate','李璟想起欧阳广此前的建议，任命他为吉水县令',16,'唐主思欧阳广之言，',None,[('唐主','想到欧阳广此前建议并任命其为县令'),('欧阳广','获任家乡吉水县令')],when='952年十月湖南失守、讨论休兵后',place='南唐、吉水县',note='本县依据此前同卷段5欧阳广为吉水人的明确记载；不是任命为朗州或潭州县令。')

reviews={8:'逐步拆分出兵、沅江、益阳、桥口湘阴、潭州、溃散灾害、任职追击、岳州及范围概述；长少展示校读长沙，原字不改。两次旧史奏报日期不同，周行逢与李建期来自新史独立补证；蒲薄姓氏保留异文。',9:'洪灾、跨境流民及救济分录；旧书饥荒与一地户数补充，户口计数不混用。',10:'辞职、劝留复职、名印分录；李谷依据当前朝廷与旧纪宰臣明名复用，甲辰与丁未纪日并列。',11:'诉讼层级、代写登记和本人诉事分别录入，不直接等同现代诉讼制度。',12:'郭彦钦侵扰与郭威调兵分录；旧史953年部署作后续补证，不编为952年确实执行的同一步。',13:'上表中的邻寇、义兵为刘言自述，事件只记报告与未经诏命举兵。',14:'边镐处分与建州、潭州的回述分开；此前攻城的年月不按952年强定，市不易肆及民众称呼分别保存，边和尚不推为出家。',15:'请求受罚获宽免与后续罢相守本官分开，冯延己复用冯延巳稳定主体。',16:'提出休兵、终身不用兵的言论及任县令分开；计划不写成后来已完成的结果，本县据欧阳广吉水籍贯解释。'}
assert not (P/'publication.json').exists()
for n in range(8,17):
 assert ledger[n-1]['status'] in ('pending','reviewed');ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=952,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(8,17)],next_paragraph=Q[17]['id'],next_volume=291,next_year=952,supplements=supplements,excluded_non_body=[],coverage='卷291原13—21行连续九段，952年尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(8,17)],source_issues_review='长少疑为长沙、蒲薄姓氏异文、何景真与何敬真同役写法均保留原字。两次旧史湖南奏报、李谷纪日以及野鸡族命令时间分别说明，不合并为无争议日期。电子底本纸本未核。',plain_language_review='首次检查全部标题、说明、人物、参与角色、时间地点及事实引用解释，明确主语与计划、行动、奏报、评价的区别；原文保持底本字形。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
