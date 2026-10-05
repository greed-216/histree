# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 287, year 947 paragraphs 65–75."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,76))
COMMIT='9b62c7b788a5cf8c34fb22fab6b06d364892b228'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-100-december-return','xinwudaishi-067-qian-zong-succession','songshi-254-hou-yi-shu']:
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
main_sources = ['tongjian-287-947-year-end-wuyue']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0947-p065-p075',
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
lines = (ROOT / 'resources/derived/tongjian/287.txt').read_text().splitlines()
for n in range(65, 76):
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
        citation = f'卷287·天福十二年（947年十二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0947_09_{len(B["claims"])+1:04d}'
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
    key = 'event_zztj_287_0947_' + code
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
        edge = 'participation_zztj_287_0947_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_287_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','承训':'刘承训','李孺赟':'李仁达','孺赟':'李仁达','修让':'鲍修让','弘倧':'钱弘倧','弘亻宗':'钱弘倧','弘佐':'钱弘佐','忠献王':'钱弘佐','弘亻叔':'钱弘俶','进思':'胡进思','承训（吴越）':'何承训','昭券':'水丘昭券','德昭':'元德昭','光弦':'鹿光铉','唐主':'李璟'})
NEW_ALIASES={'吴程':['吳程'],'何承训':['何承訓'],'鹿光铉':['鹿光鉉','鹿光弦']}
NEW_DESCRIPTIONS={'吴程':'山阴人，吴越丞相。947年十二月鲍修让将李仁达首级送到钱塘后，钱弘倧任吴程主持威武节度事务。生卒年未载。','何承训':'吴越内牙指挥使。947年与钱弘倧商议驱逐胡进思，后来担忧事泄，反向胡进思告知谋议。与后汉皇子刘承训、霍彦威之子霍承训分别建档。生卒年尚未录入。','鹿光铉':'钱弘倧的舅父，任进侍。947年年末胡进思发动废立后将其杀害。《资治通鉴》同段姓名写作光铉、光弦，沿同一人保留异字。出生年未载。'}
NEW_DEATH_YEARS={'鹿光铉':947}
dec='jiuwudaishi-100-december-return';qian='xinwudaishi-067-qian-zong-succession';origin='songshi-480-qian-chu-origin';hou='songshi-254-hou-yi-shu';t='947年十二月，具体日未载';u='947年十二月庚戌晦'
add('liu_chengxun_dies','刘承训去世，史书记其孝友忠厚、善于从政',65,'辛卯，',None,[('承训','以皇子、开封尹身份去世')],when='947年十二月辛卯',place='后汉',note='孝友忠厚与人皆惜之为史家评价，不作为逐人反应统计；死亡地点此句未明确，不猜皇宫。')
sup('liu_chengxun_dies',65,dec,'甲午，以皇子開封尹承訓薨。廢朝三日，追封魏王。','《旧五代史》记刘承训去世在十二月甲午，并停朝三日、追封魏王。','与通鉴辛卯死亡及乙未追立分条不同，分别保留纪日，不自行换算对齐。',relation='conflicts')
add('liu_returns_daliang','刘知远从邺都回到大梁',66,'癸巳，',None,[('帝','回到大梁')],when='947年十二月癸巳',place='大梁',note='与上一批丙戌发邺都的启程日区别。')
sup('liu_returns_daliang',66,dec,'癸巳，至自鄴都。','《旧五代史》同记癸巳刘知远从邺都返回。','依本纪京师语境与通鉴大梁明确到京地点，不将到达当启程。')
add('li_ren_da_plans_kill_bao','李仁达与鲍修让失和，谋杀鲍并计划再归南唐',67,'威武节度使','复以福州降唐。',[('李孺赟','与鲍修让不协，谋杀并再归南唐'),('修让','成为谋杀对象')],when='947年十二月癸巳至乙未之间，具体日未载',place='福州',note='复以福州降唐在谋袭杀之后作为计划方向整理，随后遭攻杀，未有证据证明已完成移交南唐。李孺赟沿已有李仁达更名主体。')
add('bao_kills_li_clan','鲍修让察觉谋杀，攻入府第杀李仁达并灭其族',67,'修让觉之，',None,[('修让','发兵攻府第，杀李仁达及其族'),('李孺赟','被杀害并遭夷族')],when='947年十二月鲍修让发现谋议当日，干支未载',place='福州府第',note='是日指这次反击当日，不能直接写成前句癸巳到京日；夷族具体名单与人数未载，不造全部姓名。')
add('liu_chengxun_posthumous_wei','刘承训被追封为魏王',68,'乙未，',None,[('承训','死后被追封魏王')],when='947年十二月乙未',place='后汉朝廷',note='追立为死后封爵，不写成生前任魏王或继位。')
sup('liu_chengxun_posthumous_wei',68,dec,'甲午，以皇子開封尹承訓薨。廢朝三日，追封魏王。','《旧五代史》在甲午去世条接记追封魏王。','通鉴明确乙未追立，该书未另列追封干支；只补死后封爵，不把甲午直接当独立追封纪日确证。',relation='adds')
add('hou_zhao_petition_shu','侯益请降后蜀，与赵匡赞共同请求出兵关中',69,'侯益请降',None,[('侯益','请降并令使者带兵籍粮帐西还，与赵匡赞联名上表'),('吴崇恽','携兵籍、粮帐回后蜀'),('赵匡赞','与侯益共同请求后蜀出兵')],when=t,place='凤翔、长安至后蜀',note='同上表明确联名请求，不等于对整个关中已经实际归蜀；持兵籍粮帐不推具体兵数或粮量。')
sup('hou_zhao_petition_shu',69,hou,'益遂與其子歸蜀，昶令重建率川兵數萬出大散關以應之。','《宋史》侯益传也记侯益与子归款后蜀，孟昶令何重建率川兵经大散关接应。','该传随后记侯益改变立场与奔朝，不能将归蜀字样直接解作本人已移居成都；通鉴是请降与送兵粮帐，过程和字面分别保留。',relation='adds')
add('bao_sends_li_head','鲍修让将李仁达首级送到钱塘',70,'己酉，','至钱塘，',[('修让','将李仁达首级送达钱塘'),('李孺赟','首级被送到钱塘')],when='947年十二月己酉',place='福州至钱塘',note='己酉为首级传到钱塘日，不当李仁达遇害日。')
add('wu_cheng_fuzhou_regency','钱弘倧任吴程主持威武节度事务',70,'吴越王弘倧',None,[('弘倧','任吴程知威武节度事'),('吴程','以山阴籍丞相身份主持威武节度事务')],when='947年十二月己酉',place='吴越朝廷、福州威武军',note='知节度事是主持事务，未载当日已从钱塘到福州，不虚构赴任行程。')
add('qian_zong_kills_three_officials','钱弘倧继位后处死杭、越三名违法官吏',71,'吴越王弘倧，',None,[('弘倧','不满先王放任诸将，继位后杀杭越违法官吏三人'),('弘佐','其任内容养诸将受到新王不满')],when='947年钱弘倧继位后，具体日未载',place='杭州、越州',note='及袭位为继位后追叙，不直接置十二月。性刚严、容养及愤为史家评价和心态叙述，三名官吏未具名。')
add('hu_intervenes_rejects_transfer','胡进思干预政务，不接受钱弘倧授其一州的安排',72,'内牙统军使','进思不可。',[('进思','以内牙统军使身份干政，拒绝授一州安排'),('弘倧','不满干政，想让胡进思掌一州')],when='947年钱弘倧继位后、废立之前，具体日未载',place='吴越',note='欲授一州但被拒，未载州名，不虚构已任某州刺史或节度使。')
add('qian_rebukes_hu_hu_mourns','钱弘倧多次当面驳斥胡进思，胡回家祭钱弘佐痛哭',72,'进思有所谋议，','被发恸哭。',[('弘倧','多次当面驳斥胡进思建议'),('进思','回家设钱弘佐牌位，披发痛哭')],when='947年继位后、废立前，具体各次日未载',place='吴越朝廷、胡进思家',note='设位是祭先王，不将其推成复活先王或一次正式国葬；哭的具体动机不超原文补写。')
add('qian_investigates_beef_case','钱弘倧据牛肉重量质疑杀牛案供述，下令查办官吏',72,'民有杀牛者，','命按其罪。',[('弘倧','询问牛肉重量，认为案吏虚妄并命查办'),('进思','回答大牛肉量不过三百斤')],when='947年钱弘倧在位期间，具体日未载',place='吴越',note='案中报近千斤与胡所言三百斤是记载的说法，不当现代实测。按其罪指钱认为虚妄的官吏，未载最终量刑。')
add('hu_interprets_butcher_question','胡进思透露曾从事屠宰，认为钱弘倧借此羞辱他',72,'进思拜贺其明。','益恨怒。',[('进思','说自己从军前做过此业，认为询问是在羞辱自己'),('弘倧','问胡进思为何清楚牛肉重量')],when='947年杀牛案询问之际，具体日未载',place='吴越',note='胡认为王知其旧业而故辱是胡的理解，不认定钱弘倧确有此意。弘亻宗异字沿钱弘倧。')
add('qian_blames_hu_li_rebellion','钱弘倧因李仁达再叛责备胡进思，胡更加不安',72,'进思建议','进思愈不自安。',[('进思','此前建议遣李仁达归福州，此后受责而不安'),('弘倧','因李仁达叛乱责备胡进思'),('李孺赟','其叛乱成为责备背景')],when='947年十二月福州变局后、吴越废立前，具体日未载',place='吴越',note='此前建议归福州已在第33段有对应事件，此处主要录后来的责备与反应，不重新建立归福州批准事件。')
add('qian_he_plot_remove_hu','钱弘倧与何承训商议驱逐胡进思',72,'弘倧与内牙指挥使','谋逐进思，',[('弘倧','与何承训商议驱逐胡进思'),('何承训','以内牙指挥使身份参与谋议'),('进思','成为拟驱逐对象')],when='947年十二月废立之前，具体日未载',place='吴越',note='谋逐不是已逐，何承训与刘承训为不同人；本句没有杀胡计划，不把驱逐扩大成已谋杀。')
add('shuiqiu_advises_tolerate_hu','水丘昭券认为胡进思党羽强，劝钱弘倧容忍',72,'又谋于内都监使','弘倧犹豫未决。',[('弘倧','再询问水丘昭券，听后犹豫'),('昭券','以内都监使身份劝容忍胡进思'),('进思','其党盛成为劝忍理由')],when='947年十二月废立之前，具体日未载',place='吴越',note='党盛难制为水丘的判断；犹豫未决不写成已执行驱逐。')
add('he_chengxun_informs_hu','何承训担忧事情泄露，反向胡进思告知驱逐谋议',72,'承训恐事泄，',None,[('何承训','担忧事泄，将谋议告诉胡进思'),('进思','得知针对自己的谋议')],when='947年十二月废立之前，具体日未载',place='吴越',note='承训按本段前文是何承训，不能沿后汉皇子刘承训；此处未载钱弘倧知其反告。')
add('hu_armed_confrontation','胡进思率百名亲兵闯天策堂，质问钱弘倧',73,'庚戌晦，','王何故图之？”',[('弘倧','夜宴将吏，被胡进思带兵质问'),('进思','疑王谋害自己，与党谋作乱，率兵入堂质问')],when=u,place='吴越天策堂',note='百人为史载兵数；疑其图己是胡的猜疑与质问，不将夜宴定为已经实施暗杀。')
add('hu_confines_qian_zong','钱弘倧退入义和院，胡进思锁门将其拘禁',73,'弘倧叱之','进思锁其门，',[('弘倧','叱胡不退，惊愕后退入义和院'),('进思','锁院门拘禁钱弘倧')],when=u,place='天策堂至义和院',note='这是实际拘禁，左右愤怒未载各人姓名，不虚构每名持兵者。')
add('hu_forges_succession_order','胡进思假称钱弘倧患风疾，宣布传位钱弘俶',73,'矫称王命，','传位于同参相府事弘亻叔。”',[('进思','假称王命，宣告风疾与传位'),('弘倧','名义被冒用'),('弘亻叔','成为假传王命中的继位者')],when=u,place='吴越',note='风疾与自愿传位都是胡假称内容，不写钱弘倧实际患病或真下传位令。弘亻叔按本站钱弘俶主体。')
add('hu_invites_qian_chu_yuan','胡进思率诸将迎钱弘俶，并召元德昭',73,'进思因帅诸将','且召丞相元德昭。',[('进思','率将迎新君并召丞相'),('弘亻叔','在私第受迎立'),('德昭','作为丞相被召来')],when=u,place='钱弘俶私第、吴越宫府')
add('yuan_waits_to_see_new_ruler','元德昭等见新君才行礼，胡进思急忙揭帘',73,'德昭至，','德昭乃拜。',[('德昭','站在帘外等见新君才拜'),('进思','急忙揭帘让元德昭见新君')],when=u,place='吴越宫府',note='不拜是暂等见新君，不推元德昭已经拒认继位或与胡结盟。')
add('hu_confers_qian_chu_offices','胡进思冒称钱弘倧命，授钱弘俶两镇节度使兼侍中',73,'进思称弘倧之命，','镇海、镇东节度使兼侍中。',[('进思','冒称旧王命，以承制名义授官'),('弘亻叔','获授镇海、镇东节度使兼侍中')],when=u,place='吴越',note='标明权力来自假称旧王命的政变安排，不能写成钱弘倧真实自愿授任或后汉朝廷此日正式册命。')
add('qian_chu_conditions_on_brother_safety','钱弘俶要求保全兄长，胡进思答应后他开始理事',73,'弘亻叔曰：',None,[('弘亻叔','以保全兄长为接位条件，获答应后理事'),('进思','承诺保全钱弘倧'),('弘倧','安全成为弟弟承命条件')],when=u,place='吴越',note='承诺与后续是否守诺后文再录，不据此证明胡进思永不谋杀。')
relationship('弘倧','弘亻叔','兄长',73,span(73,'弘亻叔曰：',None),'能全吾兄明确钱弘倧是钱弘俶的兄长，方向固定；检查并复用既有关系。')
sup('qian_chu_conditions_on_brother_safety',73,origin,'佐卒，弟倧嗣，為其大將胡進思所廢，遂迎立俶，事具《五代史》。','《宋史》钱俶传也记钱弘倧被胡进思废黜后迎立钱俶。','该传承认废立顺序，未提供庚戌纪日，且明言事具五代史，不能当全部细节的独立确证。')
sup('hu_confines_qian_zong',73,qian,'是夕擁衞兵廢倧，囚於義和院，迎俶立之，遷倧于東府。','《新五代史》也记岁除当夜胡进思带兵废钱弘倧、囚义和院、迎钱俶。','迁东府是该书后续概述，主书此刻只记义和院；下一年迁故王与后续谋害待连续原文再录。',relation='adds')
sup('hu_armed_confrontation',73,qian,'歲除，畫工獻鍾馗擊鬼圖，倧以詩題圖上，進思見之大悟，知倧將殺己。','《新五代史》补记岁除钟馗图题诗，胡进思见后认为钱弘倧将杀自己。','将杀己是书中对胡认知的叙述，通鉴叙夜宴疑图己；不能据题诗确认实际暗杀计划。',relation='adds')
add('hu_kills_shuiqiu_lu','胡进思杀水丘昭券及钱弘倧舅父鹿光铉',74,'进思杀','弘倧之舅也。',[('进思','杀害水丘昭券与鹿光铉'),('昭券','被杀害'),('鹿光铉','以进侍身份被杀，是钱弘倧的舅父')],when='947年十二月庚戌废立后，具体杀害日未另载',place='吴越',note='同段光铉光弦是同一进侍舅父，别名保留异字；未载杀害地点，不猜具体院落。')
relationship('鹿光铉','弘倧','舅父',74,span(74,'进思杀','弘倧之舅也。'),'舅为母亲兄弟，方向表示鹿光铉是钱弘倧的舅父；母亲姓名此处未载，不猜连接具体吴氏。')
add('hu_wife_condemns_shuiqiu_killing','胡进思的妻子责问为何杀害水丘昭券',74,'进思之妻曰：',None,[('进思','因杀水丘昭券受到妻子责问'),('昭券','被胡妻评价为君子、不应受害')],when='947年十二月废立及杀人后，具体日未載',place='吴越',note='评价为胡妻言论，未具妻姓名，不建立无证人物或误把她等同其他史书中的同姓女性。')
add('wang_yanzheng_anhua_poyang','李璟任王延政为安化节度使、鄱阳王，镇饶州',75,'是岁，',None,[('唐主','授王延政地方军职与王爵'),('王延政','以羽林大将军身份获任安化节度使、鄱阳王，镇饶州')],when='947年，是岁概述，具体月日未载',place='饶州',note='是岁不能强定十二月；此是任职王爵，不把前闽主重新受封说成复国。')
reviews={65:'辛卯死亡与旧史甲午不同，孝友忠厚等评价归史家，死亡地点未定。',66:'癸巳到京与丙戌启行区别，旧史相合。',67:'李孺赟沿李仁达，谋袭杀及再降唐意图与鲍发兵杀夷族的实际行动分清；是日不套前癸巳，具体族人未名。',68:'乙未追封与旧甲午条附封保留，不写成生前封王。',69:'侯赵联名请蜀出兵、送兵粮帐与完成移居归蜀区别，宋侯传归蜀及后续改意保留。',70:'己酉首级到钱塘不当杀李日，吴程知威武事务不当已到福州。',71:'继位后杀三吏为回叙，不硬定十二月，未名吏不建人。',72:'想授一州未执行、驳议祭先王、杀牛案供述与问答、胡自觉受辱、因李叛受责、驱逐谋议与水丘劝忍、何反告逐项分录；历史斤未换现代重量，查吏未造量刑，何承训不误作刘承训。',73:'庚戌晦夜宴疑杀与实际带兵拘禁、假风疾传位、迎俶召元、元见新君才拜、假称王命授职、保兄承诺后理事分录；宋俶传补身份顺序，新史题图疑杀不能当已证暗杀。',74:'鹿光铉光弦同段异字为同人，舅父方向明确不造母名；杀水丘与胡妻责问分录，不造胡妻名。',75:'是岁王延政任安化与鄱阳王镇饶州不强定十二月，前闽主非复国。'}
assert not (P/'publication.json').exists()
for n in range(65,76):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(65,76)],next_paragraph='zztj-v287-y0948-p001',next_volume=287,next_year=948,supplements=supplements,excluded_non_body=[],coverage='卷287原70—80行连续十一段，本卷947年75/75；跨卷286及287累计167/167，须公开读回与年度审计通过后标完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(65,76)],source_issues_review='刘承训死亡辛卯与旧甲午、追封乙未与旧附条异说；李孺赟更名沿李仁达，钱弘俶弘亻叔、鹿光铉光弦异字保留。原快照夹948开头，本批仅947正文原70—80行。',plain_language_review='首次全字段白话、身份时间及引用自查；明确主语，假称命令与真实行动、谋议与执行、当事人认知与史家评价分清。未明月日不补，逐字摘录保持底本原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
