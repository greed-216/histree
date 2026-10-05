# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 285, year 945 paragraphs 17–24."""
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
COMMIT='e66af1aafd18c0050199cc2962fef4065cc04d3a'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-285-946-july-august','jiuwudaishi-084-946-august','jiuwudaishi-084-946-zhao-correspondence','jiuwudaishi-099-bai-chengfu-death','xinwudaishi-062-chen-jue-fuzhou','xinwudaishi-065-hongya-death']:
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
main_sources = ['tongjian-285-946-july-august','tongjian-285-946-august-october']
B = {'format_version': 1, 'batch_key': 'zztj-v285-y0946-p017-p024',
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
for n in range(17, 25):
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
        citation = f'卷285·后晋开运三年（946年八月至九月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_285_0946_03_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'石重贵','唐主':'李璟','汉主':'刘弘熙','刘晟':'刘弘熙','李弘义':'李仁达','弘义':'李仁达','弘达':'李仁达','李弘达':'李仁达','李宏达':'李仁达','李达':'李仁达','李彦韬':'李彦韬（后晋宣徽使）','杨匡鄴':'杨匡邺'})
NEW_ALIASES={'顾忠':['顧忠'],'杨崇保':['楊崇保'],'杨匡邺':['杨匡鄴','楊匡鄴'],'邓伸':['鄧伸'],'马捷':['馬捷'],'丁彦贞':['丁彥貞']}
NEW_DESCRIPTIONS={'顾忠':'南唐侍卫官。946年八月条下记陈觉伪造诏令，派他召李仁达入朝。原TXT段首误写陈诲，已结合本段上下文、《新五代史》和另一《通鉴》版本校读为陈觉。顾忠生卒、籍贯未载。','杨崇保':'福州楼船指挥使。946年陈觉、冯延鲁攻福州时，李仁达派他领州兵抵抗；八月丁丑在候官被陈觉、冯延鲁击败。生卒年未载。','杨匡邺':'南唐左神威指挥使。946年八月戊寅，陈觉、冯延鲁乘胜进攻福州西关，遭李仁达出击大败，杨匡邺被俘。后续命运及生卒年未载。','邓伸':'南汉特进，陈道庠的朋友。刘思潮等死后，他送陈道庠《汉纪》，以韩信、彭越的遭遇提醒其危险。刘晟闻知后，邓伸与陈道庠均被杀并夷族；《资治通鉴》列在946年九月，《新五代史》补记下狱、斩于市。出生年未载。','马捷':'福州排阵使。946年九月辛丑，他引南唐兵从马牧山攻入福州，抵善化门桥。底本官职写排陈使，展示采用排阵使；生卒年未载。','丁彦贞':'福州都指挥使。946年九月辛丑，马捷引南唐军攻入后，他率一百人于善化门桥抵抗；李仁达随后退保善化门。生卒年未载。'}
NEW_DEATH_YEARS={'邓伸':946}
aug='946年八月条下，具体日未载';sep='946年九月条下，具体日未载'
oa='jiuwudaishi-084-946-august';oz='jiuwudaishi-084-946-zhao-correspondence';oh='jiuwudaishi-099-bai-chengfu-death';cj='xinwudaishi-062-chen-jue-fuzhou';hy='xinwudaishi-065-hongya-death';sw='songshi-254-yao-lingzhou';co='tongjian-285-946-chen-jue-collation'
# 17.
add('murong_illegal_grain_levy','慕容彦超违法征敛，取官麦五百斛制酒曲并摊派给百姓',17,'濮州','部民。',[('慕容彦超','擅取官麦制曲，摊派给百姓')],when='946年八月受处分以前，违法行为具体日未载',place='濮州',note='造麹为制作酒曲，赋与部民为摊派；不猜价格和每户数量。')
sup('murong_illegal_grain_levy',17,oa,'棣州刺史慕容彥超削奪在身官爵，房州安置，坐前任濮州擅出省倉麥及私賣官面，準法處死，','《旧五代史》记慕容彦超此时为棣州刺史，因前任濮州时擅取省仓麦、私卖官面而应处死。','主书以濮州刺史起述，旧书说前任濮州而现棣州，职务时序与罪事细节分别保留，不认两人。',relation='adds')
add('yantao_exposes_murong','李彦韬因与慕容彦超有嫌隙，揭发他违法征敛',17,'李彦韬素','应死。',[('李彦韬','与慕容彦超有嫌隙，揭发其事'),('慕容彦超','被揭发并面临死罪')],when=aug,place='后晋',note='嫌隙与实有征敛记载分开；此段未说全部罪事为捏造，不套白承福诬告案。')
add('yantao_urges_execution','李彦韬催冯玉处死慕容彦超',17,'彦韬趣','杀之，',[('李彦韬','催冯玉执行死罪'),('冯玉','受催促杀慕容彦超'),('慕容彦超','受到要求执行死罪的压力')],when=aug,place='后晋朝廷',note='催杀是要求，后来免死，不录成已被杀。')
add('liu_saves_murong','刘知远上表为慕容彦超求救',17,'刘知远','论救。',[('刘知远','上表救慕容彦超'),('慕容彦超','得到刘知远上表求救')],when=aug,place='太原至后晋朝廷')
sup('liu_saves_murong',17,oa,'太原節度使劉知遠上表救之，故貸其死。','《旧五代史》同记刘知远上表救慕容彦超，因此免其死。','只补救援与免死，不凭这一句补亲属身份。')
add('li_song_argues_leniency','李崧称诸藩都有类似违法，若都严处会使人人不安',17,'李崧曰：','不自安。”',[('李崧','提出不宜严处慕容彦超的理由')],when=aug,place='后晋朝廷',note='全体藩侯都有此罪是李崧讲话，未当作现代逐镇调查结论。')
add('murong_exiled_fangzhou','慕容彦超获免死，削官爵、流放房州',17,'甲戌，',None,[('慕容彦超','获免死，削去官爵并流放房州')],when='946年八月甲戌',place='房州',note='三项处分同诏记录，不另造三次不同日期；房州具体住所未载。')
sup('murong_exiled_fangzhou',17,oa,'甲戌，以大理少卿劇可久為大理卿。棣州刺史慕容彥超削奪在身官爵，房州安置，','《旧五代史》同在甲戌条记慕容彦超削官爵、房州安置。','甲戌是同条日期，前面剧可久官命只留作上下文，不把他当此案参与人。')
# 18: correction demonstrated by exported same-book variant and independent annals.
add('chen_forges_fuzhou_summons','陈觉返至剑州，因无功而伪造诏令，派顾忠召李仁达入朝',18,'唐陈诲','入朝，',[('陈觉','返至剑州后伪造召入朝诏令'),('顾忠','作为侍卫官被派传召'),('弘义','受到伪造诏令召入朝')],when=aug,place='福州至剑州',note='TXT段首陈诲与本段后文另具剑州刺史陈诲不合；同书固定修订写唐陈觉自福州还，新史也写陈觉返而矫命。整理主体为陈觉，快照陈诲原字不改。')
sup('chen_forges_fuzhou_summons',18,co,'唐陳覺自福州還，至劍州，恥無功，矯詔使侍衛官顧忠召弘義入朝，','同书另一电子版本明确写陈觉从福州回到剑州，伪诏派顾忠召李仁达入朝。','只作同书人名校读，不算独立史料确证；固定修订2554328原字与定位保留。',relation='conflicts')
sup('chen_forges_fuzhou_summons',18,cj,'覺慚，還至建州，矯命發汀、建、信、撫州兵攻仁達。','《新五代史》同以陈觉为返程伪造命令发兵的主体，但写返至建州。','主书剑州、该书建州地点不同，均保留，未为统一地名改原文；此补证与同书校读共同识别陈觉。',relation='conflicts')
add('chen_claims_fuzhou_control','陈觉自称暂掌福州军府事务',18,'自称','军府事，',[('陈觉','未经真实诏令，自称权福州军府事')],when=aug,place='剑州、福州',note='自称是其主张，不把这项福州军权当作李璟正式授任。')
add('chen_mobilizes_feng','陈觉擅调汀建抚信四州兵和戍卒，命冯延鲁领兵赴福州',18,'擅发','迎弘义。',[('陈觉','擅发四州兵和戍卒'),('冯延鲁','以建州监军使身份奉陈觉之命领兵赴福州')],when=aug,place='汀州、建州、抚州、信州至福州',note='迎弘义为武力召入朝任务，不能淡化为友好迎接。')
add('feng_warns_li','冯延鲁先写信给李仁达，告知顺从或拒绝的利害',18,'延鲁先','祸福。',[('冯延鲁','向李仁达写信晓以祸福'),('弘义','收到冯延鲁书信')],when=aug,place='南唐军至福州',note='原文未列全部信文，不虚拟最后通牒具体条件。')
add('li_requests_battle','李仁达回信要求交战，并派杨崇保率福州兵抵抗',18,'弘义复书','拒之。',[('弘义','回信请战并派杨崇保迎拒'),('杨崇保','以楼船指挥使身份率福州兵抵抗')],when=aug,place='福州及近郊')
add('chen_hui_naval_command','陈觉任剑州刺史陈诲为缘江战棹指挥使',18,'觉以剑州','指挥使，',[('陈觉','安排陈诲掌缘江战棹军'),('陈诲','以剑州刺史身份任缘江战棹指挥使')],when=aug,place='剑州至福州战区',note='这里陈诲为明确具职姓名，与段首校读出的陈觉是两人；该任命由陈觉作出，不冒作李璟亲诏。')
sup('chen_hui_naval_command',18,co,'覺以劍州刺史陳誨為緣江戰棹指揮使，','同书校读本也明确陈觉以剑州刺史陈诲为缘江战棹指挥使。','同一句分别出现觉和陈诲，证两主体不可混为一人；校读不算独立确证。')
add('chen_predicts_capture','陈觉上表称福州孤危，马上可以攻克',18,'表：','可克。”',[('陈觉','上表声称福州即将被攻克')],when=aug,place='福州战区至南唐朝廷',note='战况乐观判断为陈觉奏报，不提前写已克全城。')
add('li_angry_unauthorized_command','李璟因陈觉擅自发号施令而发怒',18,'唐主以觉','甚怒，',[('唐主','因陈觉擅自发令而生气'),('陈觉','因专命引起李璟愤怒')],when=aug,place='南唐朝廷')
add('ministers_urge_reinforcement','南唐群臣称军队已到福州城下不能中止，建议发兵援助',18,'群臣多言：','助之。”',[],when=aug,place='南唐朝廷',note='群臣未名，不将推荐具体归给宋齐丘或其他已知人；这是建议，后文增援为另事。')
add('chen_feng_defeat_yang','陈觉、冯延鲁在候官击败杨崇保',18,'丁丑，','候官，',[('陈觉','与冯延鲁击败杨崇保'),('冯延鲁','与陈觉击败福州军'),('杨崇保','在候官战败')],when='946年八月丁丑',place='候官',note='候官底本字形保留，是否应侯官仍待纸本核，不自动改地名或补现代坐标。')
add('li_defeats_tang_west_gate','南唐军攻福州西关，被李仁达出击大败，杨匡邺被俘',18,'戊寅，','杨匡鄴。',[('陈觉','与冯延鲁乘胜攻福州西关而败'),('冯延鲁','参与西关进攻而败'),('弘义','出击大败南唐军'),('杨匡鄴','以左神威指挥使身份被俘')],when='946年八月戊寅',place='福州西关',note='俘虏不等于当场被杀；杨姓名鄴展示规范邺，摘录不改。')
add('wang_chongwen_southeast_command','李璟任王崇文为东南面都招讨使',18,'唐主以永安','都招讨使，',[('唐主','任王崇文掌东南招讨'),('王崇文','由永安节度使任东南面都招讨使')],when=aug,place='南唐至福州战区')
add('wei_east_supervisor','魏岑以漳泉安抚使、谏议大夫身份任东面监军使',18,'以漳泉','监军使，',[('魏岑','受任东面监军使')],when=aug,place='漳泉及福州战区')
add('feng_south_supervisor','冯延鲁任南面监军使',18,'延鲁为','监军使，',[('冯延鲁','受任南面监军使')],when=aug,place='福州战区')
add('tang_takes_outer_city','南唐各军会攻福州，攻下外郭，李仁达坚守第二重城',18,'会兵',None,[('王崇文','率招讨军会攻福州'),('魏岑','作为监军参与福州攻城'),('冯延鲁','作为监军参与福州攻城'),('弘义','退守并坚守第二重城')],when=aug,place='福州',note='只克外郭，第二城未下，不写南唐此时已彻底吞并福州。')
# 19: short rations, negotiations, tactical plan, actual signal and entry.
add('feng_runs_out_of_food','冯晖率兵穿过旱海，到辉德时粮食已尽',19,'冯晖引兵','已尽。',[('冯晖','率兵过旱海，至辉德粮尽')],when='946年赴灵州途中，八月条下，具体日未载',place='旱海、辉德',note='糗粮指行军食物，不虚补粮车数量与行军人数。')
sup('feng_runs_out_of_food',19,sw,'朔方距威州七百里，無水草，號旱海，師須賫糧以行，至耀德食盡，比明，行四十里。','《宋史》也记过旱海需携粮而至耀德粮尽，并记朔方距威州七百里。','主书辉德与宋史耀德字形有别，保留地点异文待核，不擅改同一地名或换里为公里。',relation='conflicts')
add('tuoba_blocks_springs','拓跋彦超率数万人分三阵，占据要路水泉，冯晖军大惧',19,'拓跋彦超','大惧。',[('拓跋彦超','率众数万三阵占要路水泉，阻冯晖'),('冯晖','部队被堵在缺粮缺水地，军中恐惧')],when='946年赴灵州途中，具体日未载',place='辉德及要路水泉',note='数万为史载概数，三陈展示三阵，不借此补三个具名统领。')
sup('tuoba_blocks_springs',19,sw,'彥超等眾數萬，布為三陣，扼要路，據水泉，以待暉軍，軍中大懼。','《宋史》同记拓跋彦超等数万分三阵，占据要路水泉等待冯晖军。','两书兵力为概数，战区布置一致，不额外补具体地形坐标。')
add('feng_seeks_peace_with_gifts','冯晖送财求和，拓跋彦超虽答应，却直到中午仍未撤兵',19,'晖以赂','兵未解。',[('冯晖','以财物求和，多次派使往返'),('拓跋彦超','口头许和但仍列兵不退')],when='946年该役当日早晨至中午，具体日期未载',place='灵州道路',note='答应和议不等于已经解围，数四为多次概述，不列确切往返次数。')
sup('feng_seeks_peace_with_gifts',19,sw,'暉遣人賂以金帛，求和解，彥超許之。使者往復數四，至日中，列陣如故。','《宋史》补明送的是金帛，并同记使者多次往返、中午仍列阵。','金帛类型明确、数量未明，不造贿款金额。',relation='adds')
add('yao_proposes_west_attack','药元福判断许和是在拖延，提出先攻西山精兵、举黄旗合击',19,'药元福曰：','必矣。”',[('药元福','分析敌军意图并提出骑兵先击、黄旗合势战术'),('冯晖','听取药元福战术建议')],when='946年该役中午，日期未载',place='战场西山及冯晖军阵',note='敌意与精兵判断为药元福讲话，建议未直接写成已胜。')
add('yao_attacks_then_signals','药元福率骑兵短兵接战，敌稍退后举黄旗',19,'乃帅骑','黄旗，',[('药元福','率骑兵前进力战，见敌稍退后举黄旗'),('拓跋彦超','部众稍退')],when='946年该役当日，具体日期未载',place='西山战区')
add('feng_joins_and_wins','冯晖见黄旗率兵合击，拓跋彦超大败',19,'晖引兵','大败。',[('冯晖','率兵响应黄旗合击'),('药元福','先击后举旗引主军合击'),('拓跋彦超','在合击中大败')],when='946年该役当日，具体日期未载',place='赴灵州道路')
sup('feng_joins_and_wins',19,sw,'元福即舉黃旗以招暉，暉軍繼進，彥超大敗，橫屍蔽野。','《宋史》同记药元福举黄旗、冯晖军跟进，拓跋彦超大败。','战后横尸为该书所述，未计未载死亡人数。')
add('feng_enters_lingzhou','冯晖于战胜次日进入灵州',19,'明日，',None,[('冯晖','战胜次日进入灵州')],when='946年击败拓跋彦超的次日，具体日期未载',place='灵州')
sup('feng_enters_lingzhou',19,sw,'是夕，入清邊軍。明日，至靈州。','《宋史》补记战胜当晚入清边军，次日至灵州。','主书只列明日入灵州，独立补晚间经清边军的路线，不换成未经核实现代道路。',relation='adds')
event('feng_yao_receive_rewards','《宋史》记冯晖、药元福战后获衣带绢帛银器赏赐',19,'元福還郡，詔賜暉、元福衣帶繒帛銀器。',[('冯晖','获战后衣带绢帛银器赏赐'),('药元福','回郡后获赏')],source=sw,when='946年灵州道路战事以后，赏赐具体日未载',place='后晋朝廷至冯晖、药元福所在',note='只录该传本役后奖赏，不提前后汉平凤翔等后来经历。')
# 20–21.
add('khitan_invades_hedong','契丹三万兵进入河东侵扰',20,'九月，','河东。',[],when=sep,place='河东',note='三万为史载兵力，不自行补未名主帅。')
add('liu_wins_yangwu','刘知远在杨武谷击败契丹，史书记斩首七千',20,'壬辰，',None,[('刘知远','在杨武谷击败契丹')],when='946年九月壬辰',place='杨武谷',note='主书给战日壬辰；斩首七千为史书记数，不现代统计独立确证。')
sup('liu_wins_yangwu',20,oz,'癸卯，太原奏，破契丹於楊武谷，殺七千餘人。','《旧五代史》九月癸卯记太原奏报杨武谷破契丹、杀七千余人。','癸卯为奏报日期，壬辰为主书战日，两者不能都作为发生日互相覆盖；数字主七千、旧七千余分别保留。',relation='adds',field='time_original')
sup('liu_wins_yangwu',20,oh,'九月，契丹犯塞，帝親率牙兵至朔州南陽武谷，大破之。','《旧五代史》汉高祖纪九月记刘知远亲率牙兵至朔州南阳武谷大破契丹。','该纪帝为刘知远，阳武与主杨武字形分别保留；是否同一谷地待纸本核，未换地名或坐标。',relation='adds')
add('chen_fears_after_liu_deaths','刘思潮等被杀后，陈道庠感到不安',21,'汉刘思潮','不自安。',[('陈道庠','因刘思潮等被杀感到不安')],when='945年刘思潮等被杀后、946年陈道庠被杀前，具体日未载',year=None,place='南汉',note='承前945已录诛思潮，本句只录陈不安，不重复前一诛杀。')
add('deng_gives_han_chronicle','邓伸送陈道庠《汉纪》，借韩信彭越遭遇提醒他危险',21,'特进邓伸','读之！”',[('邓伸','以特进身份赠书并提醒危险'),('陈道庠','收到书，询问缘故后受到提醒')],when='946年九月条下陈道庠遇害前，赠书具体日未载',place='南汉',note='书中韩信彭越是历史例子，不新增本年杀韩信彭越事件；憨獠为引文贬语，展示不沿用。')
sup('deng_gives_han_chronicle',21,hy,'其友鄧伸以荀悅漢紀遺之，道庠莫能曉，伸罵曰：「憝獠！韓信誅而彭越醢，皆在此書矣！」道庠悟，益懼。','《新五代史》补记邓伸是陈道庠朋友，所赠为荀悦《汉纪》；陈道庠理解后更害怕。','该书连叙在三年杀刘思潮之后，未单给陈道庠赠书与遇害年月，不把段首三年机械套全部后续情节。',relation='adds')
add('han_kills_chen_and_deng','刘晟得知赠书劝戒后，杀陈道庠、邓伸并夷族',21,'汉主闻之，',None,[('汉主','得知劝戒后杀陈道庠与邓伸并夷族'),('陈道庠','与族众被杀'),('邓伸','与族众被杀')],when=sep,place='南汉',note='汉主复用更名刘晟的刘弘熙；未名族人不逐人虚造，族杀不等于只杀二人。')
sup('han_kills_chen_and_deng',21,hy,'晟聞之大怒，以道庠、伸下獄，皆斬之於市，夷其族。','《新五代史》补记刘晟愤怒，将陈道庠、邓伸下狱，在市中斩杀并夷族。','补拘禁与处刑方式，具体哪座市场未载，不凭都城确定刑场；该传未在此单独标年。',relation='adds')
for name in ['陈道庠','邓伸']:
 claim('person',people[name],'death_year',name+'于《资治通鉴》946年九月条下记为被刘晟杀死并夷族。',21,'汉主闻之，族道庠及伸。','主书纪年据当前九月条，补书处刑细节独立引用，未改变旧人物介绍与档案。')
relationship('陈道庠','邓伸','朋友',21,'其友鄧伸以荀悅漢紀遺之，','《新五代史》明确记其友邓伸，才建朋友关系；为对称关系，不以同场出现推友。',source=hy)
# 22–24: aliases remain shared subjects.
add('li_claims_min_and_changes_name','李仁达自称威武留后、权知闽国事，改名弘达并向后晋请命',22,'李弘义','于晋。',[('弘义','自称留后、权知闽国事，改名弘达并向后晋请命')],when=sep,place='福州至后晋朝廷',note='自称与正式任命分别录；弘义、弘达归同一李仁达主体，不另建人物。')
claim('person',people['李仁达'],'aliases','《资治通鉴》记李仁达此时以李弘义之名活动，改名弘达；同一人物后文又改名达。',22,'李弘义自称威武留后，权知闽国事，更名弘达，奉表请命于晋。','前批已由李仁达改名弘义的同事书证识别，本段继续记弘义到弘达，检索别名带姓李，不造重复人。')
add('jin_appoints_li_min','后晋任李仁达为威武节度使、同平章事，知闽国事',22,'甲午，',None,[('弘义','获后晋授威武节度使、同平章事，知闽国事')],when='946年九月甲午',place='福州',note='此处任命弘义沿用前名并不另人；同平章事不据此推他已到后晋中枢实际执政。')
sup('jin_appoints_li_min',22,oz,'甲午，以權知威武軍節度使李宏達為檢校太尉、同平章事，充福建節度使，知閩國事。','《旧五代史》同日记李宏达任检校太尉、同平章事、福建节度使，知闽国事。','宏达弘达为底本字形异说，福建与威武军镇称谓分别保留，不创造新任同名人。',relation='adds')
claim('person',people['李仁达'],'aliases','《旧五代史》把李仁达此时的弘达之名写作李宏达。',22,'李宏達為檢校太尉、同平章事，充福建節度使，知閩國事。','同日、职地和前后福州叙事对应，保留宏弘字形，别名用于检索不代替纸本校核。',source=oz,relation='adds')
add('zhang_reports_dingzhou_victory','张彦泽奏报在定州北击败契丹',23,'张彦泽','定州北，',[('张彦泽','奏报定州北胜契丹')],when=sep,place='定州北',note='本句无确战日，后书己亥奏报不得硬套战斗日。')
sup('zhang_reports_dingzhou_victory',23,oz,'己亥，張彥澤奏，破蕃賊於定州界，斬首二十餘級，追襲百餘里，生擒蕃將四人，摘得金耳環二副進呈。','《旧五代史》记九月己亥张彦泽奏报定州界破敌，斩二十余、追百余里、生擒将四人。','这是定州一场奏报；主书定州北加泰州两胜合记二千，不把二千直接与该书二十余认成同范围统计。',relation='adds')
add('zhang_reports_taizhou_victory','张彦泽又奏报在泰州击败契丹，两次胜仗合记斩首二千',23,'又败之',None,[('张彦泽','又奏报泰州胜仗，原文两胜共记斩首二千')],when=sep,place='泰州',note='二千承整句两胜，不拆给每场各二千；奏报不代表独立战损核验。')
add('ma_brings_tang_into_fuzhou','马捷引南唐兵从马牧山破寨进入福州，抵善化门桥',24,'辛丑，','门桥，',[('马捷','以福州排陈使身份引南唐兵入城')],when='946年九月辛丑',place='马牧山至福州善化门桥',note='主动引敌进入是明确动作，不猜许诺的官职与报酬；官名陈阵异字展示排阵。')
add('ding_resists_at_bridge','丁彦贞率一百人在善化门桥抵抗南唐兵',24,'都指挥使','拒之。',[('丁彦贞','以都指挥使身份率百人抵抗')],when='946年九月辛丑',place='福州善化门桥',note='百人为史载兵数，没有本句死亡结局，不录成全员战死。')
add('li_defends_shanhua_gate','李仁达退保善化门，南唐军占据两重外城',24,'弘达退','所据。',[('弘达','退保善化门')],when='946年九月辛丑',place='福州善化门及两重外城',note='外城再重为两重，不与第二城都破等同，南唐此时仍未完全取福州。')
add('li_changes_name_da','李仁达再次改名为达',24,'弘达更名','名达，',[('弘达','从弘达改名达')],when='946年九月辛丑福州受攻之后，具体改名日未载',place='福州',note='原文只写达，检索带姓写李达，规范主体仍李仁达；不凭这一句推改名动机。')
claim('person',people['李仁达'],'aliases','《资治通鉴》记弘达又改名达，带姓检索写作李达。',24,'弘达更名达，','沿同一李仁达主体，保留正文达的原字，不把更名达解释为另一新人物。')
add('li_requests_wuyue_help','李仁达遣使向吴越称臣，请求出兵救援',24,'遣使',None,[('弘达','向吴越奉表称臣并请求援军')],when='946年九月辛丑福州受攻之后，具体送使日未载',place='福州至吴越',note='使者未名，吴越救援决定在后段，当前只录请求。')
reviews={17:'濮州为罪事旧任，旧本纪现棣州分别；擅官麦酒曲摊派不猜价格。彦韬揭发、催杀、刘上救、李理由与甲戌免死流放分开，非白案诬全罪。',18:'段首陈诲据同书固定修订陈觉及新史主体校读，快照不改；另剑刺陈诲是真独立人。剑州建州地点异说。伪诏、自称、擅发兵和正式增援分开；丁丑候官胜、戊寅西关败俘不是同日或全福州陷。监军任命与外郭攻下第二城坚守分别。',19:'辉德宋耀德地名字异待核。饥渴三阵、金帛和议拖延、药判断战术、短兵举旗与冯合击、次日入灵分先后，数万概数。宋补夕清边军和战后赏，不提前后汉生涯；旧土桥吐蕃之战不强合同本役。',20:'壬辰为主战日，旧癸卯为太原奏报日；主七千旧七千余不同数字保留，阳武杨武谷异字未改坐标。',21:'前945思潮死只背景，不重新造诛杀；赠荀悦汉纪与韩彭历史例非本年事件。刘晟主更名刘弘熙主体，新传连段前后三年不机械定陈死亡945。市斩下狱夷族补，邓朋友据新明友才建，死年据主946。',22:'李仁达→弘义→弘达同主体，自称官命和正式甲午任分开；旧宏達异字留别名待核，福建威武称谓保留。',23:'定州和泰州两报，主2000合计不逐场；旧定州报20余和捕将4属另一统计范围，己亥是奏日。',24:'马引唐军、丁百人拒、李退保、两重外城占、改达与请吴越分开；未名使不造人，救军未提前。'}
assert not (P/'publication.json').exists()
for n in range(17,25):
 assert ledger[n-1]['status']=='pending' or (ledger[n-1]['status']=='reviewed' and ledger[n-1]['batch_key']==B['batch_key'])
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=285,year=946,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],next_volume=285,next_year=946,supplements=supplements,excluded_non_body=[],coverage='卷285原47—54行连续八段，发布后946年累计24/56，余32段。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,25)],source_contexts=[dict(source_key=main_sources[0],note='只录第17—18段，前文已录不重复。'),dict(source_key=main_sources[1],note='只录第19—24段；马希范元帅、河决及瀛莫诱降和十月部署留后批。'),dict(source_key=co,note='固定修订同书人名校读，原段陈诲与版本陈觉并列，不算独立书证。'),dict(source_key=hy,note='补陈邓下狱、市斩、夷族及朋友和荀悦汉纪，前945刘思潮等死亡不重复。'),dict(source_key=sw,note='只补赴灵州道路战役与战后赏，后汉平凤翔经历不提前。')],source_issues_review='陈觉陈诲段首底本疑误校读，剑州建州、辉德耀德、杨武阳武地字差保留。定州20余与两胜总2000不同范围不强比；刘知远战日与奏日分别；宏弘姓名异字保留。',plain_language_review='首次逐项阅读展示字段与事实说明，简体白话、明确主体；建议判断、伪诏自称、奏报、正式任命、实际胜败与城防层次分开；原文引用不改字，人名校读有独立定位。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
