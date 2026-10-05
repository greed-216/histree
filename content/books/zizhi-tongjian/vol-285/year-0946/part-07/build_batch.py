# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 285, year 946 paragraphs 45–50."""
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
COMMIT='ecde5726bec9b8402d248a26c53a28ede8152696'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-285-946-surrender-capital','jiuwudaishi-085-946-december','xinwudaishi-009-946']:
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
main_sources = ['tongjian-285-946-surrender-capital','tongjian-285-946-captive-emperor']
B = {'format_version': 1, 'batch_key': 'zztj-v285-y0946-p045-p050',
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
for n in range(45, 51):
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
        citation = f'卷285·后晋开运三年（946年十二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_285_0946_07_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'石重贵','契丹主':'耶律德光','杜威':'杜重威','李彦韬':'李彦韬（后晋宣徽使）','傅住兒':'傅住儿','太后':'永宁公主（石敬瑭妻）','皇后':'冯氏（石重贵后）','延煦':'石延煦','延宝':'石延宝','李筠':'李筠（后晋控鹤指挥使）','丁氏':'丁氏（楚国夫人）','李涛':'李涛（后晋宋初官员）'})
NEW_ALIASES={'孟承诲':['孟承誨'],'薛超':[],'李筠（后晋控鹤指挥使）':['李筠（後晉控鶴指揮使）'],'乌氏公主':['烏氏公主'],'丁氏（楚国夫人）':['丁氏（楚國夫人）']}
NEW_DESCRIPTIONS={'孟承诲':'后晋宣徽使。946年十二月张彦泽入京后，石重贵召他商议，他躲藏未到，随后被张彦泽捕杀。《资治通鉴》还称他此前凭巧言得宠，属于史家评价；出生年未载。','薛超':'后晋亲军将。946年十二月癸酉，石重贵准备与后宫人员投火自尽时，他将皇帝拦住。生卒年、籍贯未载。','李筠（后晋控鹤指挥使）':'后晋控鹤指挥使。946年十二月甲戌，张彦泽派他率兵看守被迁到开封府的石重贵，内外联系断绝。与晚唐897年被杀的捧日都头李筠不是同一人，分别建档；生卒年本批未核。','乌氏公主':'石重贵的姑母。946年十二月甲戌，贿赂守门人进入开封府，与被拘的石重贵告别，回到宅第后自缢。原文称乌氏公主，个人名字、出生年及婚配尚未核。','丁氏（楚国夫人）':'楚国夫人，石延煦的母亲。946年十二月条下记张彦泽强行把她带走。原文未给个人名字、婚配或生卒年；母亲身份按本段明确记载。'}
NEW_DEATH_YEARS={'乌氏公主':946,'孟承诲':946}
dec='946年十二月';j='jiuwudaishi-085-946-december';jp='jiuwudaishi-085-shi-surrender-memorial';np='xinwudaishi-017-shi-surrender-memorial';nw='xinwudaishi-009-946';sg='jiuwudaishi-089-sang-captive'
add('huangfu_not_part_of_surrender_plan','史书记皇甫遇起初没有参与杜重威的投降谋议',45,'杜威之降也，','初不预谋。',[('皇甫遇','被记为起初未参与降议')],when=dec+'杜重威投降之时',place='晋军行营',note='初不预谋只限起初谋议，不因此补皇甫遇始终完全未归入降军的结论。')
add('huangfu_declines_capital_attack','皇甫遇拒绝耶律德光让他率兵先取大梁的安排，并向亲近人表达不愿再攻旧主',45,'契丹主欲','图其主乎！”',[('契丹主','打算让皇甫遇先领兵入大梁'),('皇甫遇','拒绝任务，认为不能再图害旧主')],when=dec+'晋军降后',place='契丹军中',note='欲遣被拒，不写皇甫遇已经领契丹兵入京。')
add('huangfu_suicide_pingji','皇甫遇到平棘，称数日未食、不愿南行，随后自杀',45,'至平棘，',None,[('皇甫遇','在平棘向从者表明心意后自杀')],when=dec+'晋军降后，具体日未载',place='平棘',note='不食累日为本人所言，未推最后进食日期；扼吭死不扩写具体死亡器物。')
claim('person','person_皇甫遇','death_year','皇甫遇在946年十二月晋军降后自杀。',45,span(45,'至平棘，',None),'年按卷285本年条下，日期未载；不直接修改已发布人物档案。')
add('zhang_crosses_baima_at_night','张彦泽疾行，夜渡白马津',46,'张彦泽倍道','夜度白马津。',[('张彦泽','率先锋疾行并夜渡白马津')],when=dec+'进入大梁前，具体夜未载',place='白马津',note='先叙疾行，后壬申帝闻，不把夜渡强定为壬申同夜。')
add('shi_learns_du_surrender','石重贵收到杜重威等投降的消息',46,'壬申，','威等降。',[('帝','得知晋军投降')],when=dec+'壬申',place='后晋朝廷',note='这是收到消息日，投降实际丙寅已在前批录入。')
sup('shi_learns_du_surrender',46,j,'壬申，始聞杜威、李守貞等以此月十日率諸軍降於契丹。','《旧五代史》同记壬申得知十二月十日杜重威等投降。','得讯与投降日分开，不重复创建降军事件。')
add('shi_council_proposes_liu_rescue','石重贵晚间得知张彦泽到滑州，召李崧、冯玉、李彦韬商议，打算召刘知远救援',46,'是夕，','发兵入援。',[('帝','召臣商议，拟让刘知远救援'),('李崧','入禁中商议'),('冯玉','入禁中商议'),('李彦韬','入禁中商议'),('刘知远','被拟议召来救援')],when=dec+'壬申晚',place='滑州消息至后晋宫廷',note='欲诏是打算，未记诏已送达刘知远或已发兵救援。')
add('zhang_breaks_fengqiu_gate','张彦泽从封丘门破门进入大梁，李彦韬率五百禁兵阻挡失败',46,'癸酉，','不能遏。',[('张彦泽','破封丘门入京'),('李彦韬','率五百禁兵抵御而未能阻挡')],when=dec+'癸酉天未亮',place='大梁封丘门',note='禁兵五百为本次抵御人数，二千先锋在上批部署已录，不合并算兵数。')
sup('zhang_breaks_fengqiu_gate',46,j,'是夜，相州節度使張彥澤受契丹命，率先鋒二千人，自封丘門斬關而入。癸酉旦，張彥澤頓兵於明德門外，京城大擾。','《旧五代史》记壬申夜入城、癸酉旦驻明德门，与主书天未亮叙述可为跨夜过程。','夜与旦界限按各书保留，不据此将主书日期改为壬申。')
sup('zhang_breaks_fengqiu_gate',46,nw,'壬申，張彥澤犯京師，殺開封尹桑維翰。契丹滅晉。','《新五代史》将犯京和杀桑概述系在壬申，与主书分叙癸酉入京、后日杀桑不同。','这里只校核入京日期；杀桑具体执行在后批续录，不提前把死亡合在破城事件。',relation='conflicts',field='time_original')
add('zhang_camps_mingde_gate','张彦泽驻军明德门外，京城大乱',46,'彦泽顿兵','城中大扰。',[('张彦泽','驻兵明德门外')],when=dec+'癸酉',place='大梁明德门外')
add('xue_stops_shi_fire_suicide','石重贵准备带后宫人员投火自尽，薛超拦住皇帝',46,'帝于宫中起火，','所持。',[('帝','宫中起火后持剑带后宫人员准备赴火'),('薛超','以亲军将身份拦住皇帝')],when=dec+'癸酉',place='后晋宫中',note='将赴是未遂，不写石重贵在此死亡；未名后宫人员不造个体。')
add('zhang_delivers_khitan_reassurance','张彦泽从宽仁门送契丹主给皇帝、太后的慰抚书，并传召桑维翰、景延广',46,'俄而彦泽','景延广，',[('张彦泽','转达慰抚书及召臣命令'),('契丹主','通过书信慰抚并召臣'),('帝','收到慰抚书'),('太后','收到慰抚书'),('桑维翰','受到传召'),('景延广','受到传召')],when=dec+'癸酉',place='大梁宽仁门',note='本段太后表自称李氏，识别为石敬瑭妻李氏即已有永宁公主，不混安太妃。')
add('shi_extinguishes_fire_opens_palace','石重贵命灭宫火，打开宫城各门',46,'帝乃命','宫城门。',[('帝','命灭火并打开宫门')],when=dec+'癸酉',place='后晋宫城')
add('fan_zhi_drafts_surrender_memorial','石重贵与后妃在苑中哭泣，召范质起草降表，自称孙男臣重贵',46,'帝坐苑中，','次。',[('帝','召学士草降表，谦称孙男臣'),('范质','以翰林学士身份起草降表')],when=dec+'癸酉',place='后晋宫苑',note='这是降表自称及待罪表态，不当实际血缘关系或已在郊外面缚。底本妻马氏与新旧史降表妻冯氏不同，保留原字且不建马氏人物。')
sup('fan_zhi_drafts_surrender_memorial',46,jp,'臣與太后並妻馮氏及舉家戚屬，見於郊野面縛俟罪次。','《旧五代史》降表写与太后及妻冯氏举家待罪，主书底本在妻姓处写马氏。','冯姓与已有皇后身份及新史对应，马氏字形仍在快照并列，不据疑字造另一皇后。',relation='conflicts')
sup('fan_zhi_drafts_surrender_memorial',46,np,'臣與太后、妻馮氏於郊野面縛俟罪次。','《新五代史》所载降表也写妻冯氏。','别书独立引用保留来源，不把原书转录字悄悄替换。',relation='conflicts')
add('shi_sends_sons_seal_gifts','石重贵在降表中表示派石延煦、石延宝奉国宝一枚、金印三枚迎接契丹主',46,'遣男镇宁','出迎。”',[('帝','在表中表示派二子奉宝印出迎'),('延煦','被派奉宝印迎接'),('延宝','被派奉宝印迎接')],when=dec+'癸酉',place='大梁至契丹牙帐',note='先记录表中所述任务，后续两子自牙帐返还在下一批；表中职镇与旧本纪不同称谓保留。')
sup('shi_sends_sons_seal_gifts',46,jp,'所有國寶一面、金印三面，今遣長子陜府節度使延煦、次子曹州節度使延寶管押進納，並奉表請罪，陳謝以聞。','《旧五代史》同载两子押送国宝一面、金印三面，称延煦为陕府节度使、延宝为曹州节度使。','主书称镇宁及威信；旧陕府与本年十月任命对应，地镇称谓分别保留，不将这次奉送当新授各职。',relation='adds')
add('li_taihou_surrender_memorial','李太后上降表，自称新妇李氏妾',46,'太后亦上表','李氏妾”。',[('太后','上表谦称新妇李氏妾')],when=dec+'癸酉',place='后晋宫廷',note='新妇是政治礼辞，不建其与耶律德光的真实婚姻。')
add('fu_announces_khitan_order_shi_changes_clothes','傅住儿宣读契丹主命令，石重贵脱黄袍换素衫，再拜受命',46,'傅住兒入宣','皆掩泣。',[('傅住兒','入宫传宣契丹主命'),('帝','改素衫再拜接受命令')],when=dec+'癸酉',place='后晋宫中')
add('zhang_refuses_shi_summons','石重贵两次召张彦泽商议，张以无颜相见为辞，始终不应召',46,'帝使召张彦泽，',None,[('帝','两次召张彦泽商议'),('张彦泽','拒绝应召，第二次微笑不应')],when=dec+'癸酉',place='后晋宫中及张彦泽驻地')
add('sang_refuses_flight','有人劝桑维翰逃走，他称自己是大臣，无处可逃，坐等命令',47,'或劝桑维翰','俟命。',[('桑维翰','拒绝逃走，坐等命令')],when=dec+'张彦泽入京后',place='大梁',note='未名劝者不新造人物，也不等于自杀。')
sup('sang_refuses_flight',47,sg,'左右勸使逃避，維翰曰：「吾國家大臣，何所逃乎！」即坐以俟命。','《旧五代史》也记桑维翰拒绝逃避，坐等命令。','传记称十六日陷城，时序与主书跨夜分别保留，不改变主书段序。')
add('zhang_summons_sang_to_guard_office','张彦泽以皇帝命令召桑维翰，桑在天街遇李崧，随后被带往侍卫司',47,'彦泽以帝命','侍卫司。',[('张彦泽','以帝命传召桑维翰'),('桑维翰','到天街遇李崧后被带往侍卫司'),('李崧','在天街与桑维翰交谈')],when=dec+'张彦泽入京后',place='大梁天街至侍卫司',note='主书只称以帝命召；旧传对少帝密旨及贪家财的背景另作独立说法，不替作已经证实的唯一动机。')
sup('zhang_summons_sang_to_guard_office',47,sg,'張彥澤既受少帝密旨，復利維翰家財，乃稱少帝命召維翰。','《旧五代史》称张彦泽受少帝密旨，又贪桑维翰家财，因而以少帝命传召。','该传上文解释为杀桑之谋，主书本段未明写这一密杀原因；保留别书说法，实际杀桑在下一批。',relation='adds')
add('sang_challenges_li_song','桑维翰责问李崧为何国亡反让自己死，李崧露愧色',47,'维翰知不免，','愧色。',[('桑维翰','责问当政的李崧'),('李崧','受到责问，露愧色')],when=dec+'被引往侍卫司时',place='大梁天街',note='桑言自己将死是预感与责问，此时仍未写实际死亡。')
add('sang_rebukes_zhang_then_detained','桑维翰责问张彦泽负恩，张无言应答，派兵看守他',47,'彦泽倨坐','遣兵守之。',[('桑维翰','以此前保全任用之恩责问张彦泽'),('张彦泽','无以回应并派兵看守桑')],when=dec+'入京后',place='侍卫司',note='去年保全是桑此次发言中的前事，不新造日期不详的保官事件，前批已录职任不重复。')
add('meng_hides_and_is_killed','石重贵召孟承诲商议，孟躲藏不到，张彦泽将他捕杀',47,'宣徽使孟承诲','杀之。',[('帝','召孟承诲商议'),('孟承诲','躲藏未应召，后被捕杀'),('张彦泽','捕杀孟承诲')],when=dec+'张彦泽入京后',place='大梁',note='素佞巧为史家评价，不从此推唯一杀因。')
claim('person','person_孟承诲','death_year','孟承诲在946年十二月被张彦泽捕杀。',47,span(47,'至是，帝召承诲','杀之。'),'原文捕杀明确，具体日未标。')
add('zhang_allows_two_days_looting','张彦泽纵兵掳掠，部分贫民也杀富户夺财，两日后才停止',47,'彦泽纵兵','都城为之一空。',[('张彦泽','纵兵在大梁掳掠')],when=dec+'入京后两日内，结束日未具体标',place='大梁',note='都城一空是史书夸张性描述，不当所有居民房屋消失或库存精确清零；部分贫民不能概括所有贫民。')
add('zhang_boasts_loot_loyal_banners','张彦泽堆积财宝饮酒作乐，以赤心为主旗帜出行，史书记见者发笑',47,'彦泽所居','见者笑之。',[('张彦泽','自认有功，积财饮乐并打出忠心旗帜')],when=dec+'入京后',place='大梁',note='旗帜是其自我表态，不据此建忠诚人物关系或认可其行为。')
add('zhang_executes_without_inquiry','张彦泽不问被捕者所犯，竖三指便让军士带出去处死',47,'军士擒罪人','腰领。',[('张彦泽','不查罪行便示意处死被捕者')],when=dec+'控制京城时',place='大梁',note='罪人是原文用词，未核违法事实；展示称被捕者，不造具体名单或数量。')
add('zhang_kills_gao_relatives','张彦泽醉后到高勋家，杀其叔父和弟弟，并把尸体放在门前',47,'彦泽素与','不寒而栗。',[('张彦泽','醉后到高勋家杀其亲属'),('高勋','叔父和弟弟被杀')],when=dec+'控制京城时',place='大梁高勋宅',note='叔父及弟未给姓名，不新造具名人物；不由素不协推单一政治集团永久敌对。')
add('li_tao_resolves_meet_zhang','李涛认为逃避也难免，决定去见张彦泽',47,'中书舍人李涛','不若往见之。”',[('李涛','以中书舍人身份决定见张彦泽')],when=dec+'张彦泽掳掠期间',place='大梁',note='这是李涛表态，不写他实际先逃入沟渠；复用已核后晋宋初官员主体，不使用887年以来吴军同名将领。')
add('li_tao_confronts_zhang_drinks_leaves','李涛自称曾上疏请杀张彦泽，前往请死；张接待饮酒，李饮后离开',47,'乃投刺',None,[('李涛','当面表明曾请杀张彦泽，饮酒后离开'),('张彦泽','接见李涛并置酒')],when=dec+'控制京城时',place='张彦泽驻地',note='昔年奏疏为本次对话提及，不创建新的同一奏疏重复事件；此时李涛没有被杀。')
add('zhang_moves_shi_to_prefecture','张彦泽把石重贵、太后和皇后迁到开封府，宫中哭泣，宫人宦者步行随从',48,'甲戌，','见者流涕。',[('张彦泽','强令迁出皇宫'),('帝','被迁到开封府'),('太后','随皇帝被迁'),('皇后','随皇帝被迁')],when=dec+'甲戌',place='后晋宫城至开封府',note='太后为李氏既有主体、皇后为冯氏；宫人宦者十余为合称，不分别各十余。')
add('zhang_seizes_palace_treasures','石重贵带内库金珠，张彦泽逼其交出并择取珍货，封存其余待契丹',48,'帝悉以内库','以待契丹。',[('帝','交出带来的内库金珠'),('张彦泽','索取后挑走珍货并封余')],when=dec+'甲戌迁府时',place='开封府',note='讽之为暗示施压，归之不当财物本来属于张；不补财产数量和价值。')
add('li_jun_guards_captive_shi','张彦泽派控鹤指挥使李筠率兵看守石重贵，内外联系断绝',48,'彦泽遣控鹤','内外不通。',[('张彦泽','派李筠看守皇帝'),('李筠','以控鹤指挥使身份率兵看守'),('帝','被守禁，内外不通')],when=dec+'甲戌',place='开封府',note='与897年已被斩的晚唐同名李筠是异人，使用限定姓名；本批不提前建立其后周任官。')
add('wu_princess_bribes_farewell','乌氏公主贿赂守门人，入府与侄子石重贵告别，相拥哭泣',48,'帝姑乌氏','相持而泣，',[('乌氏公主','贿守门者，进入告别'),('帝','与姑母相拥哭泣')],when=dec+'甲戌',place='开封府',note='乌氏为底本名称，不推夫名和亲生父母；原文明姑，建立姑母方向关系。')
relationship('乌氏公主','帝','姑母',48,span(48,'帝姑乌氏','相持而泣，'),'原文明示乌氏公主是石重贵的姑母，方向为姑母指向侄子；不猜其父母姓名。')
add('wu_princess_suicide','乌氏公主与石重贵告别后回宅，自缢身亡',48,'归第','自经死。',[('乌氏公主','回宅自缢身亡')],when=dec+'甲戌',place='乌氏公主宅第')
add('zhang_controls_surrender_correspondence','石重贵与李太后给契丹主的表章，都须先交张彦泽查看',48,'帝与太后','然后敢发。',[('帝','表章须先交张彦泽'),('太后','表章须先交张彦泽'),('张彦泽','控制表章发送前的审看')],when=dec+'被迁开封府后',place='开封府至契丹牙帐')
add('shi_denied_cloth','石重贵想取内库几段帛，管理者称已不是皇帝财物而拒绝',48,'帝使取','非帝物也。”',[('帝','索取内库帛而被拒')],when=dec+'迁开封府后',place='开封府及内库',note='主者未具名，不新建官员；几段不是一个确定数字。')
add('shi_denied_wine_audience','石重贵求李崧送酒、求见李彦韬，两人各以理由拒绝，皇帝惆怅',48,'又求酒',None,[('帝','求酒和求见均被拒'),('李崧','以他故不送酒'),('李彦韬','拒绝前往见皇帝')],when=dec+'迁开封府后',place='开封府及京城')
add('feng_yu_seeks_to_deliver_seal','冯玉讨好张彦泽，求亲送传国宝，希望契丹再用自己',49,'冯玉',None,[('冯玉','请求送宝以求再次任用'),('张彦泽','受到冯玉讨好')],when=dec+'降京期间',place='大梁',note='求与冀是请求和希望，未写契丹已重任冯玉。')
relationship('丁氏','延煦','母亲',50,span(50,'楚国夫人丁氏','母也，'),'明确记丁氏是石延煦的母亲；石延煦为石重贵养子沿既有记录，未从本句猜丁氏婚配及父名。')
claim('person','person_丁氏（楚国夫人）','description','《资治通鉴》称楚国夫人丁氏有美色。',50,span(50,'楚国夫人丁氏','有美色。'),'美色是史书记载的评价，不补画像外貌细节。')
add('zhang_forcibly_takes_ding','张彦泽派人索取丁氏，李太后迟疑未交，张斥骂后强行载走她',50,'彦泽使人',None,[('张彦泽','索取丁氏，斥骂后强行带走'),('丁氏','被张彦泽强行带走'),('太后','迟疑未交出丁氏')],when=dec+'迁开封府后条下，具体日未载',place='大梁',note='本句未载后续遭遇或死亡，不扩写未载身体侵害；五十段不强定仍在甲戌当日。')
reviews={45:'皇甫遇不预谋、拒领取京、平棘自杀分次；不食为其表态，死日未定。',46:'白马夜渡日期未明；壬申得讯非丙寅降日。主癸酉未明入京与旧壬申夜癸酉旦、新壬申不同分别。宫火未遂与薛超阻止不写帝死。降表妻马氏与旧新冯氏保留校读，不建另一皇后；孙男新妇是礼辞非亲属。延煦延宝奉宝及官镇称谓按来源分存。',47:'李涛复用后晋宋初官员主体，不误用吴军同名人；桑拒逃与被拘不提前录后日杀桑；旧受密旨贪财为別书动机说。孟捕杀明载，城两日掠、行旗、任意杀、杀高无名亲属、李涛饮离逐项，不把对话中的前疏重新造同一事。',48:'李筠897斩与后晋控鹤将明确异人；乌氏姑母关系方向明示，未知婚配不猜。甲戌迁府夺财看守、告别自缢与控制书信、拒帛酒会分别，太后后均复用稳定主体。',49:'冯请送宝是请求，求契丹任用未当结果。',50:'丁母石延煦明载母亲，不臆推生父与婚配。太后迟延而张强取保留动作，未推未载后续侵害或死亡，具体日未标。'}
assert not (P/'publication.json').exists()
for n in range(45,51):
 assert ledger[n-1]['status']=='pending' or (ledger[n-1]['status']=='reviewed' and ledger[n-1]['batch_key']==B['batch_key'])
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=285,year=946,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(45,51)],next_paragraph=Q[51]['id'],next_volume=285,next_year=946,supplements=supplements,excluded_non_body=[],coverage='卷285原75—80行连续六段，发布后946年累计50/56，余6段。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(45,51)],source_contexts=[dict(source_key=main_sources[0],note='续录45—47段，前43—44不重复。'),dict(source_key=main_sources[1],note='只录48—50，杀桑、阳城问罪、两子返、宝疑及迎礼景拘留后批。'),dict(source_key=sg,note='只补拒逃、召桑的别书密旨贪财说，传记后续死亡不提前。')],source_issues_review='妻马冯异文与入京跨夜记日、两子职镇称谓保留；晚唐897已死李筠与控鹤将分档，礼辞不作血缘。',plain_language_review='首次逐条检查展示字段、事件角色、史料事实和核对说明；主体明确、计划表态执行区分，原字逐字摘录保留，未用内部简称展示。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
