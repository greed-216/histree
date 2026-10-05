# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 76–85."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,93))
COMMIT='b3b93bddf1e9a9a2f37c080d778ddb034d0fc54c'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['jiuwudaishi-099-heyang-april','xinwudaishi-062-chen-jue-fuzhou']:
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
main_sources = ['tongjian-286-947-luoyang-fuzhou-dispositions']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p076-p085',
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
lines = (ROOT / 'resources/derived/tongjian/286.txt').read_text().splitlines()
for n in range(76, 86):
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
        citation = f'卷286·天福十二年（947年四月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_14_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=947, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='947年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_286_0947_' + code
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
        edge = 'participation_zztj_286_0947_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_286_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','唐主':'李璟','契丹主':'耶律德光','麻荅':'麻答','拽剌':'拽剌（西奚王）','冯延己':'冯延巳','硃乙':'朱乙'})
NEW_ALIASES={'朱乙':['硃乙'],'张遇':['張遇'],'方师朗':['方師朗'],'马诲':['馬誨'],'徐铉':['徐鉉'],'石奉頵':[]}
NEW_DEATH_YEARS={'朱乙':947,'方师朗':947}
NEW_DESCRIPTIONS={
'朱乙':'后梁嗣密王，曾逃难出家。947年被嵩山首领张遇拥立，随后遭张遇杀害。具体父系和生年尚未核定。',
'张遇':'947年嵩山武装首领，拥立后梁嗣密王朱乙为天子，率众袭击郑州，被方太击退，后杀朱乙请降。与南唐境内的张遇贤分别识别，生卒年未载。',
'方师朗':'方太之子。947年受父亲派遣，向契丹说明情况，被契丹将领麻答杀害。与全师朗（王宗朗）不是同一人。生年未载。',
'马诲':'后汉史弘肇所部先锋将领。947年率兵追击契丹军，史弘肇奏报战果。生卒年未载。',
'徐铉':'字鼎臣，南唐官员。947年与韩熙载上疏请求处死陈觉、冯延鲁，李璟未采纳。《资治通鉴》此处记会稽，《宋史》记扬州广陵人，籍贯差异保留。生卒年尚未录入。',
'石奉頵':'后晋宗属，任凤州防御使。947年四月乙亥举凤州归附后蜀。具体亲属连接和生卒年未载。'}
f='jiuwudaishi-094-fang-tai';j='jiuwudaishi-099-heyang-april';nt='xinwudaishi-062-chen-jue-fuzhou';xu='songshi-441-xu-xuan'
t='947年四月条下，具体日未载'
add('fang_sent_luoyang_inspection','契丹派方太赴洛阳巡检，方太到郑州',76,'契丹遣武定','至郑州。',[('方太','以武定节度使身份受派赴洛阳巡检，途中到郑州')],when=t,place='郑州、洛阳（受派巡检地）',note='方太沿此前同一将领，主书武定与旧史遥领洋州的职衔分别保留。')
sup('fang_sent_luoyang_inspection',76,f,'契丹犯闕，偽命遙領洋州節度使，充洛京巡檢','《旧五代史》记方太受契丹命遥领洋州节度使、充洛京巡检。','与主书武定节度使写法不同，保留各书职衔。',relation='conflicts')
add('zheng_garrison_forces_fang_king','郑州戍兵迫方太作郑王',76,'州有戍兵，','共迫太为郑王。',[('方太','被郑州戍兵迫为郑王')],when=t,place='郑州',note='共迫是军士行为，不写成方太主动称帝或已得刘知远册封。')
add('zhu_yi_becomes_monk','后梁嗣密王朱乙逃难出家为僧',76,'梁嗣密王硃乙','逃祸为僧，',[('硃乙','逃难出家为僧')],when='947年被张遇找到之前，具体出家年日未载',year=None,place='具体出家地点未载',note='逃祸出家可能是此前旧事，原文未标具体年，结构年份未知，不默认907、923或947。')
add('zhang_yu_enthrones_zhu_yi','张遇找到朱乙，拥立为天子，用嵩岳神像的衮冕给他穿戴',76,'嵩山贼帅','以衣之，',[('张遇','拥立朱乙并为他取神像衮冕'),('硃乙','被张遇拥立并穿戴衮冕')],when=t,place='嵩山',note='史书贼帅展示作武装首领，拥立不是后汉认可的帝位；不推朱乙宗支父亲。')
add('fang_defeats_zhang_yu_zhengzhou','张遇率万余人袭郑州，被方太击退',76,'帅众万馀','太击走之。',[('张遇','率万余人袭郑州'),('方太','击退张遇军')],when=t,place='郑州',note='万余为史书兵数，不换成精确兵力。')
sup('fang_defeats_zhang_yu_zhengzhou',76,f,'張遇以其眾攻鄭州，太與李瓊擊之，賊眾敗走','《旧五代史》同记张遇攻郑州、方太击退，并记李琼与方太一同出战。','此处引正文，旧史另夹引通鉴的师朗记载不作为独立确证。',relation='adds')
add('fang_leaves_zhengzhou_for_luoyang','方太劝戍兵同行西去，遭拒后逃往洛阳',76,'太以契丹尚强，','逃奔洛阳。',[('方太','担心契丹仍强，劝军士西去未成，独自逃洛阳')],when=t,place='郑州西门至洛阳',note='恐事不济为方太判断，未载所有戍兵跟随或立即投降后汉。')
add('zheng_garrison_accuses_fang','方太离开后，郑州戍兵向契丹告称方太胁迫他们作乱',76,'戍兵既失太，','云胁我为乱。',[('方太','被郑州戍兵向契丹指控为胁迫作乱者')],when=t,place='郑州至契丹方面',note='史书以谮评述此告发，指控不作为方太确实强迫军士作乱的证据。')
add('mada_kills_fang_shilang','方太派儿子方师朗向契丹申辩，麻答将方师朗杀害',76,'太遣子师朗','太无以自明。',[('方太','派儿子申辩，儿子被杀后无法说明'),('方师朗','奉父命向契丹申辩，被麻答杀害'),('麻荅','杀死方太之子')],when=t,place='契丹方面，具体地点未载',note='主书麻荅复用麻答；师朗是方太之子，不与全师朗合并。旧史这句括引通鉴不当独立补证。')
relationship('方太','方师朗','父亲',76,span(76,'太遣子师朗','太无以自明。'),'子明确父子，方向表示方太是方师朗的父亲。')
add('liu_xi_leaves_luoyang','武装人群攻洛阳，刘晞弃城逃往许州',76,'会群盗攻洛阳，','弃城奔许州，',[('刘晞','以契丹留守身份弃洛阳逃许州')],when=t,place='洛阳至许州',note='群盗未逐名，不推攻城者全为张遇所部。')
add('fang_pan_defend_luoyang','方太暂行洛阳留守事务，与潘环击退攻城武装',76,'太乃入府','击群盗却之，',[('方太','入府暂行留守事，参与守城'),('潘环','以巡检使身份与方太击退攻城者')],when=t,place='洛阳河南府',note='行留守事是暂行事务，不记成已被刘知远正式授西京留守。')
add('zhang_yu_kills_zhu_yi_surrenders','张遇杀死朱乙，向方太请降',76,'张遇杀硃乙','请降。',[('张遇','杀死朱乙并请降'),('硃乙','被张遇杀害'),('方太','收到张遇的请降')],when=t,place='嵩山至洛阳',note='主书请降未明对象，结合旧史传首于太核对为向方太；不写成已获后汉任官。')
sup('zhang_yu_kills_zhu_yi_surrenders',76,f,'嵩山賊帥張遇殺嗣密王，傳首於太','《旧五代史》记张遇杀嗣密王后，将其首级送给方太。','补充请降对象的上下文，人物同职同事，不另造第二次死亡。',relation='adds')
add('fang_defeats_yique_claimant','伊阙首领自称天子、誓众拟入洛阳，方太迎击将其击退',76,'伊阙贼帅','走之。',[('方太','迎击并击退拟攻洛阳的伊阙武装')],when=t,place='伊阙、洛阳南郊坛',note='首领未名，不与朱乙或张遇无证据合并；将入是意图，方太迎击为实际动作。')
add('wu_lures_kills_fang','武行德以让出河阳主帅位置诱方太前来，方太到河阳后被杀',76,'太欲自归于晋阳，',None,[('方太','原想归附晋阳，信使者承诺到河阳后被杀'),('武行德','派人诱方太来河阳并杀害他')],when='947年洛阳变动之后，具体日未载',place='洛阳至河阳',note='方太归晋阳是意图而非实际到达；武行德虚位相待是诱骗承诺，不建真实让位事件。')
sup('wu_lures_kills_fang',76,f,'河陽武行德遣使召太，詐言欲推之為帥，尋為行德所害。','《旧五代史》同记武行德诱召方太，称要推其为帅，随后杀害他。','寻不换算固定天数，死亡与主书复用同一事件。')
add('gao_escorts_liu_back_luoyang','萧翰派高谟翰护送刘晞从许州返回洛阳',77,'萧翰遣高谟翰','自许还洛阳，',[('萧翰','派高谟翰护送刘晞'),('高谟翰','率兵护送刘晞回洛阳'),('刘晞','获护送从许州回洛阳')],when=t,place='许州至洛阳')
sup('gao_escorts_liu_back_luoyang',77,j,'汴州蕭翰遣蕃將高牟翰將兵援送劉晞復歸於洛。','《旧五代史》也记萧翰遣高牟翰率兵护送刘晞回洛阳。','高牟翰与主书高谟翰同职同事，沿已有主体异名，不新建同人。')
add('liu_orders_pan_huan_killed','刘晞怀疑潘环煽动部下驱逐自己，令高谟翰杀潘环',77,'晞疑潘环',None,[('刘晞','因怀疑潘环而下令杀害'),('高谟翰','奉命杀潘环'),('潘环','被刘晞怀疑并遭杀害')],when=t,place='洛阳',note='构其众逐己为刘晞怀疑，不作潘环确实煽动逐人的已证事实。')
sup('liu_orders_pan_huan_killed',77,j,'牟翰至，殺前澶州節度使潘環於洛陽。','《旧五代史》也记高牟翰到洛阳后杀潘环，并列潘环前澶州节度使身份。','补书不交代怀疑动机，主书怀疑层保留。',relation='adds')
add('wu_xingyou_arrives_jinyang','武行友抵达晋阳',78,'戊辰，',None,[('武行友','携武行德表章抵达晋阳')],when='947年四月戊辰',place='晋阳',note='前段遣弟与本段到达分录，不把启程也定在戊辰。表章来自前段连续上下文。')
add('shi_reports_ma_hui_victory','史弘肇奏报马诲攻击契丹军，斩首千余级',79,'庚午，','斩首千馀级。',[('史弘肇','奏报先锋作战与战果'),('马诲','受遣攻击契丹军，战果由史弘肇奏报')],when='947年四月庚午（奏报日），实际战日未载',place='潞州、泽州附近战线，具体战地未载',note='庚午是奏报时间；千余为奏报战果，不转为独立核实伤亡统计。')
sup('shi_reports_ma_hui_victory',79,j,'蕃將耿崇美屯澤州，史宏肇遣先鋒將馬誨率兵擊之，崇美退保懷州。','《旧五代史》也记史宏肇遣马诲攻耿崇美，后者退保怀州。','补书这段置于戊辰叙述下，主书庚午明确奏报，各书时点分别保留。',relation='adds')
add('geng_cui_turn_south','耿崇美、崔廷勋到泽州，得知史弘肇兵已入潞州，转向南退',79,'时耿崇美，','引众而南。',[('耿崇美','闻后汉兵入潞州，率众南退'),('崔廷勋','与耿崇美到泽州后向南退')],when='947年四月庚午奏报条下，具体行动日未载',place='泽州、潞州战线',note='闻兵已入为本段提供的战局信息；不把不敢进转成实际已攻潞州。')
add('ma_hui_pursues_khitan_huaizhou','史弘肇派马诲追击获胜，耿崇美、崔廷勋与奚王退守怀州',79,'弘肇遣诲',None,[('史弘肇','派先锋追击'),('马诲','追击契丹军并获胜'),('耿崇美','败退保怀州'),('崔廷勋','败退保怀州'),('拽剌','与耿、崔退保怀州')],when='947年四月契丹军南退之后，具体日未载',place='泽州至怀州',note='奚王沿先前拽剌（西奚王）暂定主体，异写与身份仍待考；不将此前官号与每次奚将同名都合并。')
add('wu_xingde_formal_heyang_appointment','刘知远任命武行德为河阳节度使',80,'辛未，',None,[('帝','正式任武行德河阳节度使'),('武行德','从军众推举的都部署获朝廷任命')],when='947年四月辛未',place='后汉朝廷、河阳',note='任命主体沿本纪后汉朝廷上下文；占城、推都部署和正式授节度分开。')
sup('wu_xingde_formal_heyang_appointment',80,j,'辛未，以河陽都部署武行德為河陽節度使、檢校太尉，充一行馬步軍都部署。','《旧五代史》同日记武行德任河阳节度使，并加检校太尉、充一行马步军都部署。','补书具体职衔作独立引文，不修改主书省略内容。',relation='adds')
add('khitan_names_three_failures','耶律德光听说河阳变动，自称括钱、劫掠和迟遣节度使归镇是三项失误',81,'契丹主',None,[('契丹主','自述导致各地背离的三项失误')],when=t,place='契丹北归途中，具体地点未载',note='三失为本人归因，打草谷在此为契丹军劫掠取资，不当普通农作；不把这段言论当完整叛离原因。')
add('li_jing_pardons_generals_plans_execution','李璟认为陈觉、冯延鲁伪诏败军，赦诸将并议处死二人',82,'唐主以','以谢中外。',[('唐主','赦其他将领，议处死陈觉、冯延鲁'),('陈觉','被归责伪诏败军，面临议斩'),('冯延鲁','被归责败军，面临议斩')],when='947年四月壬申',place='南唐朝廷',note='议斩是议处计划，后文流放说明未在这里实际处死。')
add('jiang_impeaches_feng_wei','江文蔚当朝弹劾冯延巳、魏岑，指他们与败军将领同罪却未受相同处分',82,'御史中丞江文蔚','同罪异诛，人心疑惑。”',[('江文蔚','以御史中丞身份弹劾冯延巳、魏岑'),('冯延己','被指责弄权并与败军者同罪'),('魏岑','被指责弄权并与败军者同罪')],when='947年四月福州败军处分时，具体日未载',place='南唐朝廷',note='阴狡弄权、排斥忠良等为弹劾内容，不写为已独立证实的事实；虽伏辜也不译成陈、冯已执行死刑。')
add('jiang_warns_closed_information','江文蔚称李璟只依赖少数人，军政财权集中、将领争斗导致败军',82,'又曰：“上之视听，','系岑一言。”',[('江文蔚','继续陈述皇帝信息受限、权力集中及将领内讧的批评'),('魏岑','被江文蔚指称掌握征讨和府库支取')],when='947年四月弹劾时，具体日未载',place='南唐朝廷',note='数人控制听闻、岑折简与一言等均为江的批评，未转成已核实财政制度或逐条新增政治同盟关系。')
add('li_jing_demotes_jiang','李璟认为江文蔚言辞过分，将其贬为江州司士参军',82,'唐主以文蔚','司士参军。',[('唐主','因不满弹劾言辞而贬江文蔚'),('江文蔚','被贬江州司士参军')],when='947年四月弹劾后，具体日未载',place='南唐朝廷至江州',note='所言太过是李璟判断，不代替对弹劾事实的独立核实。')
sup('li_jing_demotes_jiang',82,nt,'景大怒，自答其疏，貶文蔚江州司士參軍','《新五代史》也记李璟怒、亲自答疏，贬江文蔚为江州司士参军。','补书把处分放在败军后的概述，与主书连续叙事相接，未补具体日期。',relation='adds')
add('chen_feng_escorted_jinling','陈觉、冯延鲁被戴械押送金陵',82,'械送觉、','至金陵。',[('陈觉','被戴械押送金陵'),('冯延鲁','被戴械押送金陵')],when='947年四月败军处分时，具体日未载',place='福州战事之后至金陵',note='械送表示带刑具押送，不补具体枷锁规格或已处刑。')
sup('chen_feng_escorted_jinling',82,nt,'景怒，遣使者鎖覺、延魯至金陵。','《新五代史》同记李璟派使者锁送陈觉、冯延鲁至金陵。','同一次押送，不另建第二次拘捕。')
add('song_qiqiu_submits_for_blame','宋齐丘因曾推荐陈觉出使福州，上表请受责',82,'宋齐丘','上表待罪。',[('宋齐丘','为推荐陈觉出使福州而上表待罪')],when='947年四月败军处分时，具体日未载',place='南唐朝廷',note='待罪是自请承担责任，未载在本句实际被定罪或免官。')
add('chen_feng_exiled','李璟下诏将陈觉流放蕲州、冯延鲁流放舒州',82,'诏流觉','延鲁于舒州。',[('唐主','改处陈觉、冯延鲁流放'),('陈觉','被流放蕲州'),('冯延鲁','被流放舒州')],when='947年四月败军议斩后，具体日未载',place='金陵至蕲州、舒州',note='议斩之后实际处分为流放，不建立二人已斩事件。')
sup('chen_feng_exiled',82,nt,'為稍解之，乃流覺蘄州、延魯舒州。','《新五代史》同记陈觉流蕲州、冯延鲁流舒州。','补书前文以冯延巳、宋齐丘为缓解处分者，记载依存问题保留，不推确证全部请托经过。')
add('xu_han_request_execution_rejected','徐铉、韩熙载请求处死陈觉、冯延鲁以重军威，李璟未采纳',82,'知制诰会稽',None,[('徐铉','以知制诰身份请求公开处死败军者'),('韩熙载','以史馆修撰身份与徐铉同上疏'),('唐主','拒绝两人处死陈觉、冯延鲁的请求'),('陈觉','被徐铉、韩熙载要求处死'),('冯延鲁','被徐铉、韩熙载要求处死')],when='947年四月流放诏令后，具体日未载',place='南唐朝廷',note='上疏称齐丘、延巳陈请致赦，是两位上疏者的解释；显戮为请求，结尾不从表示未采纳，不是执行死刑。')
claim('person',people['徐铉'],'description','《宋史》记徐铉字鼎臣，扬州广陵人。',82,'徐鉉，字鼎臣，揚州廣陵人。','与主书本段会稽籍贯写法不同，分别保留；字、官职及同名人物上下文支持身份，未自动改主书原字。',source=xu,relation='conflicts')
add('feng_yansi_removed_chancellor','冯延巳被罢宰相，改任太弟少保',83,'中书侍郎','罢为太弟少保，',[('冯延己','从中书侍郎、同平章事被罢，改任太弟少保')],when=t,place='南唐朝廷',note='太弟少保为正式官名，动作写罢相改任；原文延己沿已有冯延巳主体。')
sup('feng_yansi_removed_chancellor',83,nt,'亦罷延巳為少傅','《新五代史》记冯延巳改任少傅，与主书太弟少保有官名差异。','少傅与太弟少保不自动视为完全相同官名，保留异说。',relation='conflicts')
add('wei_cen_demoted','魏岑被贬为太子洗马',83,'贬魏岑',None,[('魏岑','被贬太子洗马')],when=t,place='南唐朝廷',note='太子洗马为官名，不作现代字面职业解释。')
sup('wei_cen_demoted',83,nt,'岑為太子洗馬。','《新五代史》也记魏岑改任太子洗马。','保留同一次处分。')
add('han_warns_against_song_party','韩熙载多次指出宋齐丘及其党羽将酿成祸乱',84,'韩熙载','必为祸乱。',[('韩熙载','多次警告宋齐丘集团可能酿祸'),('宋齐丘','受到韩熙载对其党羽的警告批评')],when='947年条下，多次言论具体日期未载',place='南唐朝廷',note='必为祸乱是韩熙载预判，不提前建立后续叛乱事实或具体党羽关系。')
add('song_accuses_han_then_demotes','宋齐丘奏称韩熙载嗜酒放纵，韩熙载被贬和州司士参军',84,'齐丘奏',None,[('宋齐丘','以嗜酒放纵指控韩熙载'),('韩熙载','被指控后遭贬和州司士参军')],when=t,place='南唐朝廷至和州',note='嗜酒猖狂是宋齐丘指控，不作医学诊断或独立人格定论。')
sup('song_accuses_han_then_demotes',84,nt,'韓熙載上書切諫，請誅覺等，齊丘惡之，貶熙載和州司馬。','《新五代史》把韩熙载被贬与请求诛陈觉等相连，职衔作和州司马。','主书司士参军与新史司马差异保留；两书处分动机与叙事位置不同，不强排唯一顺序。',relation='conflicts')
add('shi_fengjun_surrenders_fengzhou','石奉頵举凤州归附后蜀',85,'乙亥，',None,[('石奉頵','以凤州防御使身份举州降蜀')],when='947年四月乙亥',place='凤州',note='晋之宗属支持宗族身份，未指明亲属连接，不建为石敬瑭儿子或兄弟；归附与前批孙汉韶攻城分开。')
reviews={76:'方太武定与洋州职衔异写保留；郑王为被迫；朱乙出家未知年；攻城败退、谮告、师朗受害、暂留守、杀朱、伊阙迎击与被诱杀逐项分录。旧史夹引通鉴不作独立补证。',77:'护送刘晞回洛阳与因怀疑杀潘环分开，牟谟同人，怀疑不当确证。',78:'武行友戊辰抵达与前批派遣启程分记。',79:'庚午为奏报日，千余为战果报告；耿崔南退与马追获胜分清，奚王沿既有待考主体。',80:'辛未正式授河阳节度与前批占城推都部署分开。',81:'三失为耶律德光自述归因，不是完整历史因果；劫掠词义按语境。',82:'壬申赦议斩、江弹劾批评、被贬、押送、宋待罪、诏流放、徐韩请斩及不从逐项分录；指控观点不压成独立事实，徐籍贯异说保留。',83:'延己沿延巳主体；主书太弟少保与新史少傅差异保留；太子洗马保官名。',84:'韩的警告与宋指控及实际贬谪分清，和州司士参军、司马异写和动机差异保留。',85:'乙亥归附，石奉頵宗属不推具体亲属连接。'}
assert not (P/'publication.json').exists()
for n in range(76,86):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(76,86)],next_paragraph=Q[86]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原81—90行连续十段，累计85/92，947年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(76,86)],source_issues_review='方太与南唐诸官异衔、徐铉籍贯、韩被贬动机差异分别保留；师朗同名区别；议斩未当执行；奚王先前身份疑问不消除。',plain_language_review='首次逐项核对全部人物事件标题说明、角色、关系、日期地点、出处和事实说明；明示主语、怀疑指控言论和实际动作，出家追叙未知年，引用字形保持底本。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
