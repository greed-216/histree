# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 955 paragraphs 1–8."""
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
COMMIT='ff2825de598cdd120a803b4e1262b653a990b093'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-292-954-hunan-yearend','songshi-271-zhangcangying']:
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
main_sources = ['tongjian-292-954-hunan-yearend','tongjian-292-955-february']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0955-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
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
for n in range(1, 9):
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
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷292·显德二年（955年正月至二月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0955_01_{len(B["claims"])+1:04d}'
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










ALIASES.update({'上':'柴荣','帝':'柴荣','蜀主':'孟昶','李彝兴':'李彝殷','仁毅':'孟仁毅'})
NEW_ALIASES={};NEW_DESCRIPTIONS={}
nom='jiuwudaishi-115-nominations-955';date='jiuwudaishi-115-remonstrance-date';ed='jiuwudaishi-115-remonstrance-edict';defense='jiuwudaishi-115-luyankou-defense';song='songshi-271-zhangcangying'
add('transport_losses_background','后晋后汉以来漕运未给损耗额度，很多纲吏因亏欠被处死',1,'春，正月，庚辰，','纲吏多以亏欠抵死，',[],year=None,when='后晋后汉以来至955年正月以前的制度背景',place='漕运沿线',note='自晋汉以来是跨朝概述，不把此前全部处刑归为柴荣所为，也不造具体人数。')
add('transport_loss_allowance','柴荣诏令漕运每斛给一斗损耗额度',1,'诏自今','每斛给耗一斗。',[('上','规定每斛给一斗耗额')],when='955年正月庚辰',place='后周漕运',note='斛、斗沿史载计量；给耗是运输损耗额度，不写成每斛实发一斗奖励，更不换算现代公斤。')
add('li_yiyin_blocks_zhou_envoys','李彝殷不愿与折德扆同列节度使，堵路阻挡周使',2,'定难节度使李彝兴','塞路不通周使。',[('李彝兴','因折德扆同列节度而阻路'),('折德扆','其节度任职引发李彝殷不满')],when='955年正月癸未朝议以前',place='夏州至府州相关使路',note='李彝兴复用既有李彝殷主体，保留史书后称；不因此在955年另录更名。')
add('chancellors_advise_appeasing_xia','柴荣问宰相，宰相认为应优待夏州、先劝慰李彝殷',2,'癸未，上谋于宰相，','庶全大体。”',[('上','与宰相商议夏州府州矛盾')],when='955年正月癸未',place='后周朝廷',note='宰相未点姓名，不按当时名单指定范质、王溥或他人；府州轻重是宰相意见。')
add('chairong_defends_zhe_deyi','柴荣认为折德扆长期拒北汉有功，不可舍弃，并提出对夏州贸易施压',2,'上曰：“德扆数年以来，','彼何能为！”',[('上','拒绝舍弃折德扆，阐述贸易施压'),('折德扆','受到柴荣对其抗北汉贡献的肯定')],when='955年正月癸未',place='后周朝廷',note='绝贸易是柴荣所说的制约办法，未在本句记为已执行全面禁运；夏州物产贸易为其论证，不当精确经济统计。')
add('qi_cangzhen_rebukes_li','柴荣派齐藏珍持诏责问，李彝殷惶恐谢罪',2,'乃遣供奉官齐藏珍',None,[('上','派供奉官持诏责问'),('齐藏珍','持诏赴李彝殷处责问'),('李彝兴','收到责问后谢罪')],when='955年正月癸未朝议后',place='后周朝廷至夏州',note='底本招书疑诏书，引用原字保留，说明采用持诏；謝罪不等于本文已另记道路完全恢复。')
add('shu_sets_weiwu_army','后蜀在凤州设置威武军',3,Q[3]['text'],None,[('蜀主','在凤州设威武军')],when='955年正月戊子',place='凤州',note='后蜀当前君主为孟昶，不能与后周君主柴荣混同。')
add('recommend_local_officials','柴荣令翰林学士及两省官举荐地方官，任命时记录举主姓名',4,'辛卯，','仍署举者姓名，',[('上','命官员举荐令录并记录举主')],when='955年正月辛卯',place='后周朝廷及地方官选任',note='令录沿用原官类称谓；只有政策而无本次具名举主名单，不造人物推荐关系。')
sup('recommend_local_officials',4,nom,'在朝文班，各舉堪為令錄者一人，雖姻族近親，亦無妨嫌。授官之日，各署舉主姓名，','《旧五代史》同日诏在朝文官各举可任令录者一人，亲族亦可推荐，任命时署举主姓名。','旧本纪范围写在朝文班，主书为翰林学士与两省官，保留范围详略差别。',relation='adds')
add('sponsor_accountability','被荐官员贪污失职时，举荐者须负连带责任',4,'若贪秽败官，',None,[('上','规定举主对贪污失职承担连带责任')],when='955年正月辛卯',place='后周选官制度',note='这是当时诏令规定，不编造本次已有某人被连坐。')
sup('sponsor_accountability',4,nom,'若在官貪濁不任、懦弱不理，並量事狀重輕，連坐舉主。','《旧五代史》还列不任、懦弱不理的情况，并规定按情节轻重连坐举主。','仅补当时制度适用范围，不转成当代法律规则。',relation='adds')
add('khitan_raids_hebei_background','后晋后汉以来契丹骑兵深入河北，郊野居民遭杀掠',5,'契丹自晋、汉以来','效野之民每困杀掠。',[],year=None,when='后晋后汉以来的河北边患回述，具体历次年日未载',place='河北',note='效野疑为郊野，说明采用郊野，引用保持原字；跨朝历次入侵不全绑定为耶律璟个人行为。')
add('proposal_dredge_hulu','有人建议疏浚深州冀州之间的胡卢河，阻止契丹骑兵奔突',5,'言事者称深、冀之间','可浚之以限其奔突。',[],when='955年正月工程诏令以前',place='深、冀之间胡卢河',note='建言者匿名，不补姓名；数百里为史载长度，尚无现代线路与坐标校核。')
add('wang_han_dredging_orders','柴荣命王彦超、韩通率兵夫疏浚胡卢河',5,'是月，诏忠武节度使','将兵夫浚胡卢河，',[('帝','命王彦超韩通主持疏浚'),('王彦超','率兵夫疏浚胡卢河'),('韩通','率兵夫疏浚胡卢河')],when='955年正月',place='胡卢河',note='命令与数月后的工程成果区分，不把全工程竣工强定在正月。')
add('fort_garrison_orders','柴荣安排在李晏口筑城，留军驻守',5,'筑城于李晏口，','留兵戍之。',[('帝','命筑李晏口城并留军戍守'),('王彦超','参与筑城驻守部署'),('韩通','参与筑城驻守部署')],when='955年正月工程部署',place='李晏口',note='三月设静安军军额留待对应主书段落，本条只处理筑城戍守安排。')
sup('fort_garrison_orders',5,defense,'其軍南距冀州百里，北距深州三十里，夾胡盧河為壘。','《旧五代史》在三月设静安军条补李晏口军堡南距冀州百里、北距深州三十里，夹胡卢河为垒。','补工程地理上下文，不把三月设军额计为本批已覆盖，也不按里数直接画现代坐标。',relation='adds',field='location_name')
add('chairong_asks_zhang_frontier_plan','柴荣召德州刺史张藏英，询问防边方案',5,'帝召德州刺史张藏英，','问以备边之策，',[('帝','向张藏英问备边之策'),('张藏英','以德州刺史身份入对')],when='955年正月边防部署前后，具体日未载',place='后周朝廷')
add('zhang_frontier_proposal','张藏英提出设戍兵、厚给招募边人，愿亲自带兵机动讨击',5,'藏英具陈地形要害，','随便宜讨击。',[('张藏英','提出驻防募兵与自任主将的方案'),('帝','听取张藏英的方案')],when='955年召问张藏英时',place='河北边境',note='厚禀给未具数量，不补军饷数；便宜讨击是依情势处置，不等于无条件越权。')
sup('zhang_frontier_proposal',5,song,'藏英請於深州李晏口置砦，及誘境上亡命者以隸軍，願為主將，得便宜討擊。','《宋史》也记张藏英请在深州李晏口置寨、招边境亡命者入军，自愿为主将。','主书写边人骁勇者，宋传强调亡命者，两书记述范围并列，不把所有招募者定为罪犯。',relation='adds')
add('zhang_frontier_commander','柴荣采纳张藏英建议，任其沿边巡检招收都指挥使',5,'帝皆从之，','以藏英为沿边巡检招收都指挥使。',[('帝','采纳边防方案并任指挥使'),('张藏英','获任沿边巡检招收都指挥使')],when='955年召问张藏英后',place='河北边境')
sup('zhang_frontier_commander',5,song,'世宗悉從之。以為緣邊招收都指揮使，賜名馬、金帶。','《宋史》也记柴荣采纳方案，任张藏英缘边招收都指挥使，赐名马金带。','宋传省巡检二字，名马金带为额外赏赐细节；同人同役对应。',relation='adds')
add('zhang_recruits_frontier_troops','张藏英到任数月，募得千余人',5,'藏英到官数月，','募得千馀人。',[('张藏英','数月内招募千余边军')],when='955年任职以后数月，具体完成月未载',place='河北边境',note='数月后的募兵结果不写为正月同日完成，千余为主书记数。')
sup('zhang_recruits_frontier_troops',5,song,'藏英遂築城李晏口，累月，募得勁兵數千人。','《宋史》记张藏英筑城李晏口，数月募得精兵数千人。','主书千余与宋传数千不同，保留不同记数及筑城参与，未统一精确总数。',relation='conflicts')
add('wang_yanchao_surrounded','王彦超巡视工役时，曾被契丹兵包围',5,'王彦超等行视役者，','尝为契丹所围。',[('王彦超','巡视工役时被围')],when='955年边防工程开展后，具体月日未载',place='胡卢河、李晏口相关工程一带',note='等没有点其余姓名，不确定韩通也在同次包围中。')
add('zhang_rescues_wang','张藏英率新募兵驰援，击败围住王彦超的契丹军',5,'藏英引所募兵驰击，','大破之。',[('张藏英','率新募军驰援破敌'),('王彦超','得到张藏英解围')],when='955年募兵数月后，王彦超被围时',place='河北边防工地一带')
sup('zhang_rescues_wang',5,song,'會遣鳳翔節度王彥超巡邊，為契丹所圍，藏英率新募兵馳往擊之，轉戰十餘里，契丹解去。','《宋史》补记张藏英驰援、转战十余里，使契丹解去。','宋传称王彦超凤翔节度，主书称忠武，保留职称差别；未知援救日期不推成正月同日。',relation='adds')
claim('event',E['zhang_rescues_wang'],'description','《通鉴》说此后契丹不敢越胡卢河，河以南居民得到休息。',5,'自是契丹不敢涉胡卢河，河南之民始得休息。','河南指胡卢河以南，不直接理解为现代河南省；这是主书效果概述，不外推此后绝无袭扰。')
add('february_eclipse','史书记二月初一发生日食',6,Q[6]['text'],None,[],when='955年二月庚子朔',place='史书未列观测地点',note='只录史载日食，不自行补观测点、食分或换算公历。')
add('meng_renyi_dies','后蜀夔王孟仁毅去世',7,Q[7]['text'],None,[('仁毅','以夔王身份去世')],when='955年二月庚子朔与壬戌条之间，具体日未载',place='后蜀，具体地点未载',note='仁毅复用950年受封夔王的已核主体，恭孝为此处谥称，不据紧接初一便认同日死亡。')
claim('person',people['孟仁毅'],'death_year','孟仁毅在955年二月条所记时段去世。',7,Q[7]['text'],'死亡年依据显德二年连续正文，不无守卫覆盖既有主体字段。')
add('chairong_calls_candid_advice','柴荣诏群臣尽言政事得失，以言行观察才能与忠心',8,'壬戌，',None,[('帝','要求群臣直言得失，并说明如何察才察忠')],when='955年二月壬戌',place='后周朝廷',note='诏书对臣子直言、君主纳谏责任的表述保留为当时政策宣示，不推定随后所有劝谏都已被采纳。')
sup('chairong_calls_candid_advice',8,date,'壬戌，詔曰：','《旧五代史》同记二月壬戌发布诏书。','该段是诏书引首，正文另有独立片段，二者按同一连续段落序列回查。')
sup('chairong_calls_candid_advice',8,ed,'朕於卿大夫才不能盡知，面不能盡識，若不采其言而觀其行，審其意而察其忠，則何以見器量之深淺，知任用之當否？若言之不入，罪實在予；茍求之不言，咎將誰執！','《旧五代史》保存同一诏书中听言观行、判断任用及纳谏责任的表述。','器略与器量等措辞差别保留原字，诏书责任说法不当作已经发生的处罚案件。')
reviews={1:'给耗是运输损耗额度，不造给钱奖赏；晋汉制度背景不全绑定柴荣。',2:'李彝兴复用李彝殷，宰相匿名不按名单硬点；贸易制约是所说办法，未造已执行禁运，持诏责问及谢罪明示，招书疑字保留。',3:'设置威武军的蜀主为孟昶，凤州史载地点不补坐标。',4:'举荐规则与举主连坐分录，官类令录沿史称，旧史补各举一人及任亲范围；政策不伪造具名推荐关系或既成处罚。',5:'契丹侵扰为跨朝回述，胡卢河倡议、工程部署、问策、采纳任职、数月募兵、解围逐项处理。千余与数千、忠武与凤翔职称差别保留，河南指河以南，三月设军额未算本批覆盖。',6:'庚子朔日食只按史载，观测位置及现代历法未补。',7:'孟仁毅复用已核夔王，死亡日未独立标明，不能套初一；旧字仕毅的身份对应保留既有说明。',8:'求言诏日期与正文分别引用旧史片段，君主自陈责任是宣示，不当已兑现全部纳谏结果。'}
assert not (P/'publication.json').exists()
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=955,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=292,next_year=955,supplements=supplements,excluded_non_body=[],coverage='原33—40行连续八段；源快照含954年旧事或955年后续段落，不计本批覆盖。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],source_issues_review='招书与效野疑字保留；宋传募兵数和王彦超职称与主书并列，河以南居民不套现代省名。数月后行动不强定正月，孟仁毅确日未载。纸本待核。',plain_language_review='首次逐条检查标题、人物、角色、时间及事实说明。匿名官员与建言者不造姓名，诏令、建议、任职、数月后成果和实际交战分开，单位与字形保持原引。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
