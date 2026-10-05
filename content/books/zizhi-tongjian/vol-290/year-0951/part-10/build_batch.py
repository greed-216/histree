# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 951 paragraphs 71–76."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,83))
COMMIT='97a2c54a1eb33b08fa864fe14e9ca184db2402cc'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-290-951-october-november','xinwudaishi-065-hezhou-traps']:
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
main_sources = ['tongjian-290-951-october-november','tongjian-290-951-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0951-p071-p076',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-290-951-year-end':'卷290·广顺元年·十一月至十二月及年末追述','jiuwudaishi-112-december-expedition':'卷112·太祖本纪三·广顺元年十二月'}
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
lines = (ROOT / 'resources/derived/tongjian/290.txt').read_text().splitlines()
for n in range(71, 77):
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
    labels={'tongjian-290-951-year-end':'卷290·广顺元年·十一月至十二月及年末追述','jiuwudaishi-112-december-expedition':'卷112·太祖本纪三·广顺元年十二月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺元年（951年十一月至十二月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0951_10_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=951, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='951年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_290_0951_' + code
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
        edge = 'participation_zztj_290_0951_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_290_0951_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','唐主':'李璟','南汉主':'刘弘熙','刘晟':'刘弘熙','楚王':'马希萼'})
NEW_ALIASES={'马希隐':['馬希隱'],'彭彦晖':['彭彥暉'],'潘玄珪':[],'李承戬':['李承戩'],'郑好谦':['鄭好謙'],'郑麟':['鄭麟'],'张凝':['張凝']}
NEW_DESCRIPTIONS={'马希隐':'马殷的幼子，楚国静江节度副使、知桂州。951年面对南汉来信与吴怀恩军到城下，与许可琼率众逃往全州。生卒年未载。','彭彦晖':'楚国指挥使。受马希广派遣驻龙峒防南汉，马希萼在衡山时又任他为桂州都监、在城内外巡检使、判军府事。与许可琼在桂州城中交战，败后逃往衡山。生卒年未载。','潘玄珪':'马希隐的支使。951年马希隐与僚佐商议向南汉投降时，他反对投降。生卒年未载。','李承戬':'南唐先锋指挥使。951年十一月奉边镐之命率兵到衡山，催促马希萼入朝。生卒年未载。','郑好谦':'后周通事舍人。951年奉郭威之命前往安抚慕容彦超，并与其盟誓。生卒年未载。','郑麟':'慕容彦超的都押牙。951年多次受派入后周朝廷，表面表示诚意，史书记载实际上为侦察朝廷情况。生卒年未载。','张凝':'后周阁门使。951年十二月奉郭威之命率兵到郓州巡检，以防备慕容彦超。生卒年未载。'}
old='jiuwudaishi-112-december-expedition';nh='xinwudaishi-065-hezhou-traps'
relationship('马殷','马希隐','父亲',71,'楚静江节度副使、知桂州马希隐，武穆王殷之少子也。','原文明确马希隐为马殷之子，少子按幼子说明，不推未载的出生年。')
add('wu_huaien_frontier_command','刘晟任吴怀恩为西北招讨使，屯兵边境等待进取时机',71,'楚王希广、希萼兄弟争国，','伺间密谋进取。',[('南汉主','任吴怀恩为西北招讨使，谋划趁楚国内乱进取'),('吴怀恩','以内侍使身份受任，率兵屯在边境')],year=None,when='马希广与马希萼争国期间的追述，具体任命与屯兵年份未载',place='南汉、楚国边境',note='南汉君主沿已核刘弘熙改名刘晟主体；待机进取是计划，不直接认作已在此时攻克桂州。')
add('peng_yanhui_longdong','马希广派彭彦晖率兵驻龙峒，防备南汉',71,'希广遣指挥使彭彦晖','以备之。',[('马希广','派彭彦晖率兵驻龙峒'),('彭彦晖','以指挥使身份驻兵防备南汉')],year=None,when='马希广在位、争国期间的追述，具体派兵年份未载',place='龙峒',note='马希广已于950年失位，不能把此项追述记成951年他仍发号施令。')
add('peng_yanhui_guizhou_command','马希萼在衡山任彭彦晖掌桂州军务',71,'希萼自衡山遣使','判军府事，',[('楚王','派使者任彭彦晖桂州都监等职'),('彭彦晖','获任桂州都监、城内外巡检使、判军府事')],when='951年衡山立府后至十一月桂州失守以前，具体任命日未载',place='衡山至桂州',note='多个头衔是一项授任安排，不拆成不同人物或多个新城任职。')
add('ma_xiyin_informs_xu','马希隐反感彭彦晖获任，秘密通知许可琼',71,'希隐恶之，','潜遣人告蒙州刺史许可琼。',[('马希隐','反感桂州军务安排，秘密通知许可琼'),('许可琼','以蒙州刺史身份收到消息')],when='951年彭彦晖获任桂州军务以后',place='桂州至蒙州',note='本句未载通知内容的完整文字，不补一份具体反叛指令。')
add('xu_keqiong_leaves_mengzhou','许可琼惧怕南汉进逼，放弃蒙州，率兵赴桂州',71,'可琼方畏南汉之逼，','引兵趣桂州，',[('许可琼','放弃蒙州，率兵前往桂州')],when='951年十一月桂州失守以前，具体撤离日未载',place='蒙州至桂州')
add('xu_peng_guizhou_battle','许可琼与彭彦晖在桂州城中交战，彭彦晖败逃衡山',71,'与彦晖战于城中。','可琼留屯桂州。',[('许可琼','在桂州击败彭彦晖，并留兵驻守'),('彭彦晖','桂州交战败后逃往衡山')],when='951年十一月桂州失守以前',place='桂州至衡山',note='城中交战不是南汉军此时已攻入城内，两场战事分开。')
add('wu_huaien_mengzhou','吴怀恩占据蒙州并进兵侵掠，桂管地区动乱',71,'吴怀恩据蒙州，','桂管大扰，',[('吴怀恩','占据蒙州，继续进兵侵掠')],when='951年许可琼放弃蒙州以后、桂州失守以前',place='蒙州、桂管',note='桂管为当时地区称谓，不直接绘制现代行政范围。')
add('ma_xiyin_xu_distress','马希隐、许可琼无计可施，饮酒相对哭泣',71,'希隐、可琼不知所为，',None,[('马希隐','面对桂管局势无计可施，与许可琼饮酒哭泣'),('许可琼','与马希隐饮酒相对哭泣')],when='951年桂管受南汉军侵扰期间',place='桂州',note='行为与情绪为史书所载，不据此作医学或性格诊断。')
add('liu_sheng_letter_xiyin','刘晟致信马希隐，宣称出兵救援并可保留其镇守地位',72,'南汉主遗希隐书，','常居方面。”',[('南汉主','向马希隐致书，以两国交往、婚姻与援救为说辞'),('马希隐','收到南汉来信')],when='951年十一月桂州失守以前，具体递信日未载',place='南汉至桂州',note='书信中富强五十余年、三十五舅及三十舅、已发大军、永拥节旄等是刘晟的说辞与允诺，不独立证明全部史实或自动建立母系血缘关系。')
add('pan_xuangui_opposes_surrender','马希隐与僚佐商议降南汉，潘玄珪反对',72,'希隐得书，','支使潘玄珪以为不可。',[('马希隐','收到信后与僚佐商议投降'),('潘玄珪','以支使身份反对投降')],when='951年十一月收到南汉来信后',place='桂州',note='商议投降不等于已经完成降礼。')
add('wu_huaien_at_guizhou','吴怀恩军突然抵达桂州城下',72,'丙寅，','吴怀恩引兵奄至城下，',[('吴怀恩','率军突然到桂州城下')],when='951年十一月丙寅',place='桂州城下')
add('ma_xu_flee_quanzhou','马希隐、许可琼夜间破关逃往全州，桂州失守',72,'希隐、可琼帅其众，','桂州遂溃。',[('马希隐','率部夜间破关逃往全州'),('许可琼','与马希隐率部逃往全州')],when='951年十一月丙寅吴军到城以后，夜间',place='桂州至全州',note='斩关为打开关口逃走，不译成斩杀具名守将，也不写成他们向南汉投降。')
add('wu_huaien_lingnan_expansion','吴怀恩率军攻取宜、连等九州',72,'怀恩因以兵',None,[('吴怀恩','继续率军攻取宜、连、梧、严、富、昭、柳、象、龚等州')],when='951年桂州失守以后，各州具体攻取日未载',place='宜、连、梧、严、富、昭、柳、象、龚等州',description='吴怀恩继续率军攻取宜、连、梧、严、富、昭、柳、象、龚等州。史书记载南汉由此尽有岭南。',note='略定各州未给逐城战日，岭南是史家范围概括，不作为现代省界或全部辖地的证明。')
sup('wu_huaien_lingnan_expansion',72,nh,'珣等攻桂州及連、宜、嚴、梧、蒙五州，皆克之。掠全州而還。','《新五代史》在吴珣、吴怀恩攻楚的叙述中，也记攻取桂州及连、宜、严、梧、蒙五州，并掠全州而返。','此书记在早先求婚及攻贺州叙述之后，没有给本次951年丙寅日期。作为区域军事记载的对照，不断言与主书每项攻取都是同一次，也不据此改各州攻取年。',relation='adds')
add('li_chengjian_to_hengshan','边镐派李承戬率兵到衡山，催马希萼入朝',73,'辛未，','趣马希萼入朝。',[('边镐','派先锋指挥使李承戬率兵到衡山'),('李承戬','受命催促马希萼入朝'),('楚王','被催促前往南唐朝廷')],when='951年十一月辛未',place='长沙至衡山')
add('ma_xie_eastward','马希萼与将佐士卒万余人从潭州东下',73,'庚辰，',None,[('楚王','与将佐士卒万余人从潭州东下')],when='951年十一月庚辰',place='潭州东下',note='万人为将佐士卒合计，不写成马氏宗族人数；路线仅记东下，不编具体靠泊点。')
add('wang_jun_waits_shanzhou','王峻在陕州停留十天左右',74,'王峻留陕州旬日，','王峻留陕州旬日，',[('王峻','救援晋州途中在陕州停留')],when='951年十一月出征后至十二月初，停留旬日，具体起始日未载',place='陕州',note='旬日为约十天，不自行换算确切公历起止日期。')
add('guo_plans_personal_relief','郭威担心晋州失守，商议亲自率军由泽州会合王峻，并遣使通知',74,'帝以北汉攻晋州急，','且遣使谕峻。',[('帝','计划亲率兵经泽州会合救晋州，并派使通知王峻'),('王峻','成为会兵计划的通知对象')],when='951年十一月末至十二月戊子朔以前，具体商议日未载',place='后周朝廷、泽州路与陕州',note='议自将是计划，不写成郭威已率兵到泽州。')
add('guo_orders_western_expedition','郭威下诏定当月初三西征',74,'十二月，戊子朔，','下诏以三日西征。',[('帝','下诏计划当月初三西征')],when='951年十二月戊子朔',place='后周朝廷',note='初三为计划行期，不当作实际出发日。')
sup('guo_orders_western_expedition',74,old,'十二月戊子朔，詔以劉崇入寇，取當月三日暫幸西京。','《旧五代史》同日记因刘崇进攻，拟当月初三暂赴西京。','主书写西征、此书写幸西京，分别保留行动目的与表述，不据旧书写成已经巡幸。')
add('wang_jun_advises_guo_stay','王峻解释等待敌军疲惫的策略，并劝郭威留京防慕容彦超',74,'使者至陕，','大事去矣！”',[('王峻','通过使者解释驻兵等待，并劝郭威不要轻离京师'),('帝','收到王峻关于晋州与京师安全的劝告')],when='951年十二月戊子朔下诏后、庚寅撤令以前',place='陕州至后周朝廷',note='晋州城坚、敌锋锐及慕容彦超可能入汴都是王峻的判断，不写成慕容彦超已攻入汴州。底本“若年驾”疑车驾字形，原引文保留，解释按语境写明郭威出行。')
add('guo_cancels_expedition','郭威接受王峻劝告，撤回亲征命令',74,'帝闻之，',None,[('帝','听取劝告，停止亲征计划')],when='951年十二月庚寅',place='后周朝廷',note='自提耳及几败吾事是原书对郭威反应的记载，不扩大为实际已经败亡。')
sup('guo_cancels_expedition',74,old,'庚寅，詔巡幸宜停。時王峻駐軍陜府，聞帝西巡，遣使馳奏，不勞車駕順動，帝乃止。','《旧五代史》同日也记停止巡幸，原因是王峻驻陕府闻讯后驰奏劝止。','主书记借原使者传言，旧书记遣使驰奏，各书使者过程保留，不虚构两名具名使者。')
add('murong_secret_preparations','慕容彦超听说徐州被平定后，更加疑惧，招纳亡命、积聚薪粮并私联北汉',75,'初，泰宁节度使','吏获其书以闻。',[('慕容彦超','招纳亡命、积聚物资并以书信联络北汉')],when='951年三月徐州被平定之后至十二月防备部署以前的追述，具体各次行动日未载',place='泰宁军、北汉与后周朝廷',note='吏获书上报与联络行动相连；本句未证明北汉已作军事承诺，不自动建立永久盟友关系。')
add('murong_fake_merchants_tang','慕容彦超派人冒充商人向南唐求援',75,'又遣人诈为商人','求援于唐。',[('慕容彦超','派人冒充商人向南唐请求援助')],when='951年私联北汉前后至十二月，具体派遣日未载',place='泰宁军至南唐',note='使者未具名；求援不等于南唐军此时已出兵。')
add('zheng_haoqian_reassures','郭威派郑好谦安抚慕容彦超，并与其盟誓',75,'帝遣通事舍人郑好谦','与之为誓。',[('帝','派郑好谦安抚慕容彦超'),('郑好谦','以通事舍人身份前往安抚并盟誓'),('慕容彦超','接受郑好谦前来安抚及盟誓')],when='951年慕容彦超疑惧加深时，具体派遣日未载',place='后周朝廷至泰宁军',note='誓言内容未载，不编造互不征讨条款。')
add('zheng_lin_spies_court','慕容彦超多次派郑麟入朝，史书记载其实际为窥探朝廷情况',75,'彦超益不自安，','实觇机事。',[('慕容彦超','多次派郑麟入朝，表面表示诚意'),('郑麟','以都押牙身份入朝，史书记为侦察朝廷情况')],when='951年安抚盟誓以后至十二月，具体每次出使日未载',place='泰宁军至后周朝廷',note='伪输诚款、实觇机事为史书对其目的的叙述，不扩写具体窃得情报。')
add('murong_presents_gao_letter','慕容彦超呈交一封称出自高行周的信，郭威认为是骗局',75,'又献天平节度使高行周书，','此彦超之诈也！”',[('慕容彦超','呈交一封称高行周诋毁朝廷并与己相结的信'),('帝','认为这封信是慕容彦超的骗局')],when='951年十二月派张凝防备以前',place='泰宁军至后周朝廷',note='信中诋毁与相结不能认定为高行周已证实的行动；郭威判为诈保留人物判断性质。')
add('guo_shows_gao_letter','郭威把慕容彦超所献信示给高行周，高行周上表谢恩',75,'以书示行周，','行周上表谢恩。',[('帝','把所献信给高行周看'),('高行周','看信后上表谢恩')],when='951年十二月张凝赴郓以前',place='后周朝廷与天平军',note='谢恩不自动证明信件真伪的每个细节，也不新建高行周参与慕容反叛的关系。')
add('zhang_ning_yunzhou_patrol','郭威派张凝率兵赴郓州巡检，防备慕容彦超',75,'既而彦超反迹益露，',None,[('帝','派阁门使张凝率兵赴郓州防备'),('张凝','以阁门使身份率兵巡检郓州')],when='951年十二月丙申',place='郓州',note='是防备部署，不提前记慕容彦超已被平定。')
add('wang_jun_reaches_jiangzhou','王峻率救援军抵达绛州',76,'庚子，','王峻至绛州。',[('王峻','率救援军抵达绛州')],when='951年十二月庚子',place='绛州')
add('wang_jun_heads_jinzhou','王峻从绛州向晋州进军',76,'乙已，','引兵趣晋州。',[('王峻','继续率军向晋州进发')],when='951年十二月乙已（底本字形，干支疑为乙巳，待核）',place='绛州至晋州',note='乙已保留底本原字，未悄改摘录或生成公历日；行动与庚子抵绛州分别登记。')
add('vanguard_crosses_mengkeng','王峻担心北汉占据蒙坑，得知前锋已通过后感到欣喜',76,'晋州南有蒙坑，',None,[('王峻','得知前锋已通过险要蒙坑，认为救援进展有利')],when='951年十二月向晋州进军当日，底本纪日乙已待核',place='晋州以南蒙坑',note='担忧敌据不等于敌军确已占据蒙坑；吾事济矣是判断，不提前写成晋州已经解围。')
reviews={71:'父子方向明，吴怀恩与彭彦晖派兵为争国期追述不强系951新任。南汉主沿943已核刘弘熙改名刘晟。许可琼与彭城内互战、吴据蒙及马许饮哭分别录，不将楚军内战误作南汉攻城。',72:'书信救援与保官为南汉君主说辞，舅称不自动补生母族谱。议降未成实际降，吴丙寅到城、马许夜逃全州及扩九州分清。新书攻桂等州置早先攻贺叙述后，不强认全部同本次951战役。',73:'辛未催入朝与庚辰潭州东下分开；万人为将佐士卒，不计作马氏宗族。',74:'旬日驻陕跨十一至十二，郭威议亲征与初三行期为计划；王峻等待敌衰及慕容入汴是策略判断。旧书初三幸西京、庚寅停止印证，原若年驾疑字保留。',75:'徐州平后疑惧追述覆盖三月至十二，招亡命私书北汉、假商求唐、安抚誓、郑麟窥伺和所献高信分别记。信内容不当高行周反叛证据；丙申张凝巡郓是实际防备。',76:'庚子抵绛、乙已进晋、前锋过蒙坑分录。乙已疑干支字形不生成公历日，吾事济为欣喜判断不当已解围。'}
assert not (P/'publication.json').exists()
for n in range(71,77):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=951,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(71,77)],next_paragraph=Q[77]['id'],next_volume=290,next_year=951,supplements=supplements,excluded_non_body=[],coverage='卷290原76—81行连续六段长文；本年后续正文仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(71,77)],source_issues_review='逐字导出不改底本，纸本未核。乙已、若年驾疑字保留；南汉舅称为书信用语，不强补血缘。新五代史桂管征服与主书具体本次战役不强配，书信真伪按郭威判断说明。',plain_language_review='首次逐项检查标题、人物、事件说明、角色、关系方向、时间与事实说明。引用外用白话，明确计划、判断、请求与实际执行；不补无载主语、日期和动机。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
