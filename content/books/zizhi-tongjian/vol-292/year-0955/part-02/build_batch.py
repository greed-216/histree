# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 955 paragraphs 9–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,40))
COMMIT='6a163584ccc696d903a1d677cbce57a2328b297b'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-292-955-february','jiuwudaishi-115-luyankou-defense','jiuwudaishi-128-wangpu-career']:
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
main_sources = ['tongjian-292-955-february','tongjian-292-955-qinfeng-first-order']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0955-p009-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
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
lines = (ROOT / 'resources/derived/tongjian/292.txt').read_text().splitlines()
for n in range(9, 17):
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
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷292·显德二年（955年二月至五月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0955_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=955, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='955年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_292_0955_' + code
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
        edge = 'participation_zztj_292_0955_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_292_0955_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 if kw.get('source'):
  t=(sources[kw['source']]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);quote=t[a:b]
 else:quote=span(n,start,end)
 E[code]=event(code,title,n,quote,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)










ALIASES.update({'上':'柴荣','帝':'柴荣','唐主':'李璟','蜀主':'孟昶','王溥':'王溥（后周宋初）','王景':'王景（后晋耀州团练使）'})
NEW_ALIASES={'王万迪':['王萬迪'],'昝居润':['昝居潤']}
NEW_DESCRIPTIONS={'王万迪':'后蜀凤州刺史。955年赵季札巡视边备后，向孟昶批评王万迪与雄武节度使韩继勋不能御敌。这里只保存他人评价，不据此确认其必无将才。生卒年未载。','昝居润':'高唐人，后周客省使。955年奉柴荣命与向训、王景同赴秦凤。《宋史》记其善书计，早年为枢密院小吏，后任军器库使，高平战功后任客省使；同一秦凤役中任行营都监。生卒年留待后续史料补录。'}
city='jiuwudaishi-115-city-essay-orders';strategy='jiuwudaishi-128-wangpu-strategy';career='jiuwudaishi-128-wangpu-career';nw='xinwudaishi-31-wangpu-essay';fort='jiuwudaishi-115-luyankou-defense';wpast='songshi-252-wangjing-earlier-posts';wqin='songshi-252-wangjing-qinfeng-order';zanid='songshi-262-zan-jurun-identity';zanqin='songshi-262-zan-jurun-qinfeng'
add('yanxu_chancellor','李璟任严续为门下侍郎、同平章事',9,Q[9]['text'],None,[('唐主','任严续为宰相'),('严续','由中书侍郎知尚书省转任门下侍郎同平章事')],when='955年二月求言诏以后、三月段以前，具体日未载',place='南唐朝廷',note='唐主是南唐李璟，不是已亡后唐君主；严续复用旧主体。')
add('jingan_military_district','柴荣将李晏口设置为静安军',10,Q[10]['text'],None,[('帝','设置静安军军额')],when='955年三月辛未',place='李晏口',note='与正月疏河筑城戍守部署分开，此时新增军额。')
sup('jingan_military_district',10,fort,'三月辛未，以李晏口為靜安軍，','《旧五代史》同日记李晏口设静安军。','沿史载军号，不把城、军额、疏河等所有阶段合并为正月一天。')
add('chairong_unification_ambition','柴荣高平获胜后，有平定分裂疆域的志向',11,'帝常愤广明以来','慨然有削平天下之志。',[('帝','高平战后增强统一意图')],year=None,when='954年高平获胜之后至955年本条的回述，具体时间未载',place='后周朝廷',note='这是志向与主书动机概述，不是已经统一各国的结果。')
add('qin_people_propose_recovery','秦州民众到大梁献策，请恢复旧疆，柴荣采纳',11,'会秦州民夷',None,[('帝','采纳来自秦州民众的恢复旧疆建议')],when='955年三月部署以前，具体使行日未载',place='秦州至大梁',note='民夷为原书对来者的称谓，姓名未载；不造族群名单或未经证据的使者身份。')
add('zhao_jizha_inspects_border','孟昶派赵季札巡视边备',12,'蜀主闻之，','赵季札案视边备。',[('蜀主','派客省使检查边备'),('赵季札','奉命巡视边防')],when='955年三月丙申任命以前',place='后蜀北部边境')
add('zhao_jizha_criticizes_commanders','赵季札返奏，认为韩继勋、王万迪不能御敌',12,'季札素以文武才略自任，','不足以御大敌。”',[('赵季札','自许文武才略并批评两将'),('韩继勋','被赵季札批评'),('王万迪','被赵季札批评')],when='955年边备巡视后、三月丙申任命以前',place='后蜀朝廷',note='两将缺乏才能是赵季札判断，不当作本站已核定的能力结论。')
add('zhao_jizha_volunteers_border','孟昶问谁能去边地，赵季札自请承担',12,'蜀主问：','季札自请行。',[('蜀主','询问合适人选'),('赵季札','自请赴边')],when='955年三月丙申任命以前',place='后蜀朝廷',note='请行与受任、实际到边地分开，后续是否到任按后段继续处理。')
add('zhao_jizha_border_monitor','孟昶任赵季札为雄武监军使，给宿卫精兵千人',12,'丙申，',None,[('蜀主','任监军并授兵'),('赵季札','获任雄武监军，获千宿卫兵')],when='955年三月丙申',place='雄武军秦州方向',note='任命与兵力授予明确，此段未说赵季札已抵秦州，不提前记录赴任成功。')
add('daliang_outer_city_edict','柴荣因大梁拥挤下诏扩外城，先立标志分期施工',13,'帝以大梁城中迫隘，','以渐成之。',[('帝','下诏扩城并安排分期施工')],when='955年四月乙卯',place='大梁外城',note='主书安排今冬农隙开工、农忙停工、来年续作，诏令与实际竣工分开。')
sup('daliang_outer_city_edict',13,city,'乙卯，詔於京城四面別築羅城，期以來春興役。','《旧五代史》同日记京城四面另筑罗城，预定来春兴役。','主书今冬农隙开工、旧史来春兴役的季节差别并列，不强行改成同一开工日。',relation='conflicts')
add('daliang_burial_limit','柴荣规定此后葬埋须在扩城标志七里以外',13,'且令自今葬埋','皆出所标七里之外，',[('帝','规定扩城区域外的葬埋界限')],when='955年四月乙卯',place='大梁外城标志之外',note='七里沿原书，不给现代坟场位置；未写成已经迁走全部旧墓。')
add('daliang_city_planning','柴荣要求官府划街道、仓场、营署，剩余标内区域准民建屋',13,'其标内',None,[('帝','安排扩城规划和民居建设规则')],when='955年四月乙卯',place='大梁外城标内',note='允许随便筑室是在官府划定公用区域以后，不译为完全不受规划的任意建屋。')
add('wang_zhaoyuan_checks_north','孟昶命王昭远检查北边城寨和兵器装备',14,Q[14]['text'],None,[('蜀主','命王昭远检查北边装备城防'),('王昭远','奉命按行城寨甲兵')],when='955年四月丙辰',place='后蜀北边城寨')
add('chairong_commissions_essays','柴荣命近臣写治君治臣论和开边策供他阅读',15,'上谓宰相曰：','朕将览焉。”',[('上','命近臣提出治国与统一策略')],when='955年四月丙辰以后所记，具体日未载',place='后周朝廷',note='寝令疑为寝食，说明只保留反复思考治国之意；未把吴蜀幽并不统一的陈述当作已全部消灭。')
sup('chairong_commissions_essays',15,city,'是月，詔翰林學士承旨徐臺符已下二十餘人，各撰《為君難為臣不易論》、《平邊策》各一首，帝親覽之。','《旧五代史》同月记徐台符以下二十余人各写治君治臣论与平边策。','主书开边策、旧史平边策名称不同，保留各书题名和人数详略。',relation='adds')
sup('chairong_commissions_essays',15,career,'二年夏，世宗命朝廷文學之士二十餘人，各撰策論一首，以試其才。時朴獻《平邊策》，云：','《旧五代史》王朴传也记显德二年夏命二十余文士作策论，王朴献平边策。','传记二年夏提供年代上下文，不用生平篇未及全部同日来推具体日期。')
add('wangpu_presents_strategy','王朴献策，主张先内治、后用兵，先南唐江北，后图其他地区',15,'比部郎中王朴献策，','上欣然纳之。',[('王朴','以比部郎中身份提出分期用兵策略'),('上','阅读并采纳王朴献策')],when='955年四月征策以后，具体献策日未载',place='后周朝廷',description='王朴主张先用人、轻赋、节用以加强国力，再先易后难：轻兵扰南唐，取江北、进江南，随后谋岭南巴蜀与燕地，最后处理河东。他所说强弱和攻取成效是战略判断及预期，未记为已经执行的战果。',note='整篇策略作为同次献策保存，各项主张分别补事实引用，不造未来地区已被攻下的事件。')
for start,end,text,note in [
 ('中国之失吴、蜀、幽、并，','莫若反其所为而已。','王朴认为失地源于君暗臣邪、兵骄民困及内外权力失序，建议反其道治理。','这些原因是王朴的历史政治分析，不当所有失地的唯一已证因果。'),
 ('夫进贤退不肖，','所以阜其民也。','王朴建议进贤、施恩守信、赏功罚罪、去奢节用、按时役使并减轻征敛。','恩隐字句按底本保留，施政条目作为建议，不代表已逐项施行。'),
 ('俟群才既集，','功无不成矣！','王朴主张人才、政事、财用与民心准备后再用兵。','功无不成为其预期，不作保证。'),
 ('彼之人观我有必取之势，','天意必从矣。','王朴预期优势和民心能吸引对方知情者做间谍、熟悉山川者作向导。','未把假设中的间谍向导建成具名人物，天意为原作者论证。'),
 ('凡攻取之道，','且以轻兵扰之。','王朴主张先攻易处，以轻兵袭扰南唐无备之地，察虚实后避强击弱。','约二千里为策略中的边境概数，不画未经考证的疆界。'),
 ('南人懦怯，','如此，江北诸州将悉为我有。','王朴预计反复扰动能使南唐疲于动员，民困财竭，或使周军乘虚取江北。','对南人的概括是王朴观点，不作本站对群体的判断；取得江北是预期。'),
 ('既得江北，','席卷可平矣。','王朴规划江北之后取江南，再促岭南巴蜀归附，继而谋燕地，不附则攻。','各地归附、席卷可平仍是计划，不另建已统一南方和燕地的事件。'),
 ('惟河东必死之寇，','然后伺间一举可擒也。','王朴认为河东北汉难以恩信招诱，应以强兵制之，但宜待其他地区平定后再图。','敌情强弱判断随原文保存，不解释为北汉已失去所有作战能力。'),
 ('今士卒精练，','宜自夏秋蓄积实边矣。','王朴认为军队已经具备条件，建议夏秋积蓄边粮，并预期一年以后可以出师。','期年为预期准备时间，不从中反推每场真实战役的确定出师日期。')
 ]:
 claim('event',E['wangpu_presents_strategy'],'description',text,15,span(15,start,end),note)
sup('wangpu_presents_strategy',15,strategy,'攻取之道，從易者始，當今吳國，東至海，南至江，可撓之地二千里。','《旧五代史》保存王朴同类先易后难、袭扰江淮的平边策略。','旧文称吴国，主书称唐，在此指江南政权及其地域；题名与措辞差别保留，勿新造同时存在的另一个吴国敌人。')
sup('wangpu_presents_strategy',15,nw,'朴謂江淮為可先取。','《新五代史》也记王朴提出先取江淮。','传记此前用新即位和高平背景概括，无独立献策月日，不据此强改主书955年时序。')
claim('person',people['王朴'],'evaluation','《通鉴》称王朴机敏果断、善谋，筹画合柴荣意，因此获重视。',15,'惟朴神峻气劲，有谋能断，凡所规画，皆称上意，上由是重其器识。','保留主书人物评价，不把评价写成所有军政结果都由王朴独自决定。')
add('wangpu_promoted_kaifeng','王朴随后升左谏议大夫，知开封府事',15,'未几，',None,[('王朴','献策获重视后升任左谏议大夫、知开封府事')],when='955年献策之后未几，具体升任日未载',place='开封府',note='未几不是确定天数，不把升任日期强定为四月丙辰。')
add('chairong_seeks_qinfeng_commanders','柴荣谋取秦凤，寻找合适将领',16,'上谋取秦、凤，','求可将者。',[('上','为秦凤战事选将')],when='955年五月出兵以前',place='后周朝廷')
add('wangpu_recommends_xiang','王溥推荐向训领兵征秦凤',16,'王溥荐','镇安节度使向训。',[('王溥','推荐向训'),('向训','以宣徽南院使、镇安节度使身份被荐')],when='955年五月出兵以前',place='后周朝廷',note='推荐人王溥复用后周宋初主体，不与王朴或901年王溥混同。')
relationship('王溥','向训','推荐人',16,span(16,'王溥荐','镇安节度使向训。'),'955年秦凤出师选将时，王溥是向训的推荐人，限定该次举荐。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='955年秦凤出师选将时，王溥是向训的推荐人。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
add('qinfeng_joint_order','柴荣命向训、王景、昝居润同赴秦凤',16,'上命训','昝居润偕行。',[('上','安排三人西征'),('向训','奉命与王景昝居润同行'),('王景','以凤翔节度使身份奉命同行'),('昝居润','以客省使身份奉命同行')],when='955年五月出兵以前',place='后周至秦凤方向',note='王景复用原后晋耀州团练使主体，宋传连续履历另补；不将三人同行自动建为私人盟友。')
claim('person',people['王景（后晋耀州团练使）'],'description','《宋史》记王景天福初任相州刺史，拒范延光后迁耀州团练使。',16,'天福初，授相州刺史。范延光據鄴叛，屬郡多為所脅從，景獨分兵拒守，晉祖嘉之，遷耀州團練使。','同传前部明确早期相州耀州履历，印证已有主体；后部凤翔秦凤行役来自同一传主，非仅凭同名合并。',source=wpast)
sup('qinfeng_joint_order',16,wqin,'廣順初入朝，民周環等數百人，遮道留之不獲，有截景馬鐙者，俄以景為護國軍節度，歲餘，遷鎮鳳翔。','《宋史》王景传记他任护国军节度使后，年余迁镇凤翔。','为本条凤翔王景与早期相州耀州主体的连续履历补证；此段迁镇不是955年新命令。',relation='adds')
claim('person',people['昝居润'],'description','《宋史》说昝居润是博州高唐人，善书计，早年曾在枢密院为小吏。',16,'昝居潤，博州高唐人。善書計。後唐長興中，隸樞密院為小吏，以謹願稱。','电子总题名误识李濤傳，但本段及同EPUB第3节明确传主昝居润；新来源按卷262昝居润传显示，不修改原TXT。',source=zanid)
sup('qinfeng_joint_order',16,zanqin,'從向拱西征，為行營都監，','《宋史》记昝居润参加向拱西征，任行营都监。','秦凤同役对应主书昝居润与向训，向拱为宋传称名；此句未具具体授任日，不提前录秦凤平后的任职。',relation='adds')
add('wangjing_departure_sanguan','王景从散关出兵，向秦州进军',16,'五月，',None,[('王景','从散关率军趋秦州')],when='955年五月戊辰朔',place='散关至秦州')
sup('wangjing_departure_sanguan',16,wqin,'先是，秦、鳳陷蜀，州旁蕃漢戶詣闕請收復，世宗命景與向拱率兵出大散關進討，','《宋史》同记秦凤居民请收复，柴荣命王景与向拱出大散关进讨。','宋传没有此句的独立月日；只补出军，不把后续寨栅和秦州归降提前纳入当前覆盖。')
reviews={9:'唐主为南唐李璟，严续任相日未载，不套求言诏壬戌。',10:'三月新增静安军军额与正月筑城部署分开，补书同日印证。',11:'高平后统一志向为回述，秦州来者姓名未载；采纳建议不等已经攻取秦凤。',12:'赵季札巡视、批评、自请与丙申受任分开。他批评两将能力不是本站定论，给兵不当已经到任。',13:'扩城命令、标志、分期施工、葬埋界限与规划后民居安排分开。今冬与旧来春开工差异保存，未录已竣工。',14:'孟昶遣王昭远检查北边，主体与柴荣区分。',15:'完整长篇策略按主张附同次献策引用，不造已攻下地区。官号与人数、开边和平边题名差别并列；人才财用、袭扰动员、次序与河东后图均已处理。',16:'王溥推荐与三将奉命、五月实际出兵分开。王景通过宋传相州耀州至凤翔连续履历复用；昝居润传电子题名误识已说明。未来秦凤平后任职未录。'}
assert not (P/'publication.json').exists()
for n in range(9,17):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=955,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],next_volume=292,next_year=955,supplements=supplements,excluded_non_body=[],coverage='原41—48行连续八段，从二月任相至五月秦凤出军；原快照所含未来战役段落未计覆盖。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,17)],source_issues_review='扩城今冬与旧来春差别保留，开边策与平边策题名异文保留；寝令及恩隐疑字不改原文。宋262总题名误识李濤傳，昝居润由明确姓名和同节上下文识别。王景同名通过连续履历回查，纸本待核。',plain_language_review='首次逐条检查所有标题、人物介绍、角色、关系、时间、策论事实与校核说明。策略与预期不当已执行战果，诏令与竣工、受命与实际出兵分开，引用保持原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
