# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 952 paragraphs 1–10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,47))
COMMIT='14cbc2e919886dae0472b77f2330611d8b32c8d7'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-112-january-953-yeji']:
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
main_sources = ['tongjian-291-953-january-intercalary']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0953-p001-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-953-january-intercalary':'卷291·广顺三年正月至闰正月','jiuwudaishi-112-intercalary-953':'卷112·太祖本纪三·广顺三年闰月','songshi-278-maquanyi-early':'卷278·列传第三十七·马全义早年','songshi-278-maquanyi-zhou':'卷278·列传第三十七·马全义事周'}
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
for n in range(1, 11):
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
    labels={'tongjian-291-953-january-intercalary':'卷291·广顺三年正月至闰正月','jiuwudaishi-112-intercalary-953':'卷112·太祖本纪三·广顺三年闰月','songshi-278-maquanyi-early':'卷278·列传第三十七·马全义早年','songshi-278-maquanyi-zhou':'卷278·列传第三十七·马全义事周'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·广顺三年（953年正月至闰正月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0953_01_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=953, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='953年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0953_' + code
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
        edge = 'participation_zztj_291_0953_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0953_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','荣':'柴荣','梁太祖':'朱温','折从阮':'折从远','张仿':'张亻放（楚军指挥使）','朱元琇':'朱全琇','绍基':'高绍基','李彬':'李彬（延州观察判官）'})
NEW_ALIASES={'李万全':['李萬全'],'杨弘裕':['楊弘裕'],'马全乂':['馬全乂','马全义','馬全義'],'高绍基':['高紹基'],'李彬（延州观察判官）':['李彬（延州觀察判官）']}
NEW_DESCRIPTIONS={'李万全':'野鸡族首领之一。953年正月折从阮奏报其已接受后周诏书并立誓。具体族属不作现代归类，生卒年未载。','杨弘裕':'后周定和都指挥使。953年契丹围义丰军时夜袭敌营，获胜使契丹撤走。生卒年未载。','马全乂':'原为李守贞麾下骑士，后事柴荣。953年随柴荣入朝，郭威召见并任命为殿前指挥使，称赞其忠于所事。《宋史》作马全义，记同一河中经历、任职和召见言论，复用同人异名；后续生卒另待录。','高绍基':'雄武节度使高允权之子、牙内指挥使。953年父死后图谋继任，隐瞒父丧，杀死劝谏的观察判官李彬并诬报谋反；朝廷派张仁谦巡检后才公开父丧。生卒年未载。','李彬（延州观察判官）':'雄武军观察判官。953年劝谏高绍基隐瞒父丧谋求继任，被高绍基杀死，并被诬报为谋反者。生年未载，不与其他同名人物混同。'}
NEW_DEATH_YEARS={'李彬（延州观察判官）':953}
oldjan='jiuwudaishi-112-january-953-yeji';oldinter='jiuwudaishi-112-intercalary-953';songearly='songshi-278-maquanyi-early';songzhou='songshi-278-maquanyi-zhou'
add('liuyan_wuping_commission','郭威任刘言为武平节度使，统理武安、静江军事，加同平章事',1,'春，正月，丙辰，','同平章事；',[('帝','授刘言武平节度使等职'),('刘言','由武平留后正式获任节度使并统理相关军事')],when='953年正月丙辰',place='后周朝廷、朗州')
add('wang_wuan_commission','郭威任王逵为武安节度使',1,'以王逵为','武安节度使，',[('帝','任命王逵为武安节度使'),('王逵','获任武安节度使')],when='953年正月丙辰',place='潭州')
add('he_jingzhen_jingjiang_commission','郭威任命何敬真为静江节度使',1,'何敬真为','静江节度使，',[('帝','任命何敬真为静江节度使'),('何敬真','获任静江节度使')],when='953年正月丙辰',place='静江军')
add('zhou_xingfeng_wuan_sima','郭威任命周行逢为武安行军司马',1,'周行逢为',None,[('帝','任命周行逢为武安行军司马'),('周行逢','获任武安行军司马')],when='953年正月丙辰',place='武安军')
sup('liuyan_wuping_commission',1,oldjan,'丙辰，以武平軍節度使留後、檢校太尉劉言為檢校太師、同平章事，行朗州大都督，充武平軍節度兼三司水陸轉運等使，制置武安、靜江等軍事，進封彭城郡公；','《旧五代史》同日补载刘言兼水陆转运等使、行朗州大都督、进封彭城郡公等职衔。','正式授职承接此前留后身份，不能把各项加官当作多次独立上任。',relation='adds')
sup('he_jingzhen_jingjiang_commission',1,oldjan,'以武安軍行軍司馬兼衙內步軍都指揮使、檢校太傅何敬貞為檢校太尉，行桂州刺史，充靜江軍節度使；','《旧五代史》同日作何敬贞，补载此前武安行军司马等职及领桂州刺史。','主书何敬真、旧纪何敬贞按同日同职同军府对应保留异文；未将同名何敬洙混入。',relation='adds')
# Additional appointments from the independent chronicle share the same dated decree.
for code,title,quote,actors in [
 ('zhang_fang_wuping_deputy','张仿领眉州刺史，任武平军节度副使','以張仿領眉州刺史，充武平軍節度副使；',[('张仿','领眉州刺史并任武平军节度副使')]),
 ('zhu_quanxiu_jingjiang_deputy','朱全琇领黄州刺史，任静江军节度副使','以朱元琇領黃州刺史，充靜江軍節度副使；',[('朱元琇','据旧纪领黄州刺史并任静江军节度副使')])]:
 E[code]=event(code,title,1,quote,actors,when='953年正月丙辰，《旧五代史》同次任命',place='后周朝廷、湖南军府',source=oldjan,note='独立旧纪的补充任职，领刺史为兼领职衔，不能认定本人搬赴该州；朱元琇与随后闰月同军府朱全琇写法连续对应，保留异文。')
sup('zhou_xingfeng_wuan_sima',1,oldjan,'以周行逢領集州刺史，充武安軍節度行軍司馬。','《旧五代史》另载周行逢兼领集州刺史。','领职不等于赴集州实际驻守，主线仍为武安行军司马。',relation='adds')
claim('person',people['朱全琇'],'aliases','《旧五代史》正月任命名单写朱元琇，后续同一军府出兵名单写朱全琇，保留全、元异文。',1,'以朱元琇領黃州刺史，充靜江軍節度副使；','结合王进逵、何敬贞同一湖南军府任命及后续出兵名单识别，仍保留已有朱全琇主体。',source=oldjan)
claim('person',people['朱全琇'],'aliases','《旧五代史》闰月奏报又作朱全琇，与正月朱元琇写法不同。',1,'遣朗州行軍司馬何敬貞與指揮使朱全琇、陳順等，率水陸軍五萬進擊。','此处只引用后续军府名单用于姓名校核，不提前建立本段尚未叙到的出兵事件；两写法逐字保留。',source=oldinter)
claim('person',people['何敬真'],'aliases','《旧五代史》同日授任静江节度使记作何敬贞，与《通鉴》何敬真对应，保留异文。',1,'以武安軍行軍司馬兼衙內步軍都指揮使、檢校太傅何敬貞為檢校太尉，行桂州刺史，充靜江軍節度使；','同日授同军职且此前武安行军司马履历对应，不只凭相似姓名合并。',source=oldjan)
add('guo_offers_yeji_terms','郭威令折从阮对愿改过的野鸡族授官赐金帛，否则进兵',2,'诏折从阮：','不则进兵讨之。”',[('帝','规定招抚与进兵的条件'),('折从阮','受命按改过与否分别招抚或进兵')],when='953年正月，壬戌奏报以前',place='静难军、庆州',note='这是附条件的命令，不把全部首领写成已经受官受赏。')
add('zhe_reports_yeji_division','折从阮奏报李万全等已受诏立誓，其余部众仍不服，正在讨伐',2,'壬戌，从阮奏：',None,[('折从阮','报告首领归附与仍不服者的情况'),('李万全','据奏报接受诏书并立誓')],when='953年正月壬戌奏报',place='静难军、庆州',note='方讨之为奏报正在推进的讨伐，未给已经完成歼灭的战果；受诏与受官不同。')
add('older_border_tuntian','此前屯田多设在边境，由驻军耕种',3,'前世屯田皆在边地，','使戍兵佃之。',[],year=None,when='此前屯田制度的历史概述，未给具体朝代起止',place='边境地区',note='前世不是953年新建屯田，皆是原书记述的概括，不推为历代所有屯田无一例外。')
add('late_tang_central_yingtian','唐末中原驻军，在各地设置营田耕种荒地',3,'唐末，中原宿兵，','以耕旷土。',[],year=None,when='唐末战争时期的制度概述，具体设立年未载',place='中原')
add('yingtian_rich_households','营田后来招募富户纳课承佃，由户部另设官署管理，不属州县',3,'其后又募高赀户','不隶州县，',[],year=None,when='唐末设营田以后至后周改革以前，具体制度变更年未载',place='中原营田',note='高赀户为财力较丰之家，输课佃之为承担课税租佃，不擅自解释为土地私有制。')
add('yingtian_oversight_abuses','一些营田户人口多却不服役，或藏匿奸盗，州县无法追究',3,'或丁多无役，','州县不能诘。',[],year=None,when='后周改革以前营田制度弊端的概述，具体案例年未载',place='中原营田',note='或表示部分情况，不能写成所有营田户皆为逃犯。')
add('zhu_distributes_captured_cattle','朱温进攻淮南时掠夺大量牛，分给东南各州农民，要求逐年纳租',3,'梁太祖击淮南，','使岁输租。',[('梁太祖','将淮南战争中掠得的牛分给农民并征租')],year=None,when='朱温进攻淮南时的回述，具体战役年本段未载',place='淮南、东南诸州',note='千万计为原书对规模的表述，具体数量待核；展示用大量牛，不把它当精确牲畜统计。')
add('cattle_rent_persists','多年后所租的牛已死，租课仍未取消，百姓深受其苦',3,'自是历数十年，','民甚苦之。',[],year=None,when='掠牛分配后数十年至953年改革以前的制度延续',place='东南诸州',note='数十年描述延续，不是本年新增税种，也不能一律换算为固定年数。')
add('zhang_li_seek_yingtian_reform','张凝请求撤销营田务，李谷也提出同样建议',3,'帝素知其弊，','李谷亦以为言。',[('张凝','以阖门使、知青州身份请求撤销营田务'),('李谷','同样建议撤销营田务'),('帝','此前已知道营田弊端')],when='953年正月乙丑改革以前，具体建言日未载',place='青州、后周朝廷')
add('guo_abolishes_yingtian_offices','郭威撤销户部营田务，将营田户划归州县，并把田屋、牛与农具赐给现佃者',3,'乙丑，敕：','悉除租牛课。”',[('帝','废营田务、归户州县、赐田产并取消租牛课')],when='953年正月乙丑',place='后周',note='永业为永久保有的田产安排，不能扩大解释为取消全部田税或任何租赁关系。')
sup('guo_abolishes_yingtian_offices',3,oldjan,'乙丑，詔：「諸道州府系屬戶部營田及租稅課利等，除京兆府莊宅務、贍國軍榷鹽務、兩京行從莊外，其餘並割屬州縣，','《旧五代史》同日敕文还载京兆府庄宅务、赡国军榷盐务、两京行从庄起初属于例外。','主书悉罢的概述与旧书先有例外、随后按例处理的展开分别保留，不将所有机构都写成同日无条件划归。',relation='adds')
sup('guo_abolishes_yingtian_offices',3,oldjan,'未幾，京兆府莊宅務及榷鹽務亦歸州縣，依例處分。','《旧五代史》续记不久后京兆庄宅务及榷盐务也划归州县。','未几是相对时间，不能将后续调整强定为乙丑当天。',relation='adds')
add('yingtian_reform_registration_effect','营田改革当年户部增加三万余户，佃户开始修屋植树，史书称收益增长数倍',3,'是岁，户部增三万馀户。','获地利数倍。',[],when='953年改革当年的效果概述，具体统计日未载',place='后周',note='户部增户包含改隶登记，不等于当年出生三万户；数倍为史书概述，不给精确现代经济指标。')
add('guo_rejects_selling_yingtian','有人建议出售肥沃营田筹钱，郭威以利民亦利国为由拒绝',3,'或言：',None,[('帝','回应售田筹款建议，主张让利于民')],when='953年营田改革期间的议论，具体日期未载',place='后周朝廷',note='肥铙疑为肥饶之讹，展示按上下文为肥沃田地，原字不改；数十万缗为建议者预计，不是已收到的卖田款。')
add('ye_renlu_corruption_sentence','郭威赐死旧部叶仁鲁，史书记其涉赃绢一万五千匹、钱千缗',4,'莱州刺史叶仁鲁，','庚午，赐死。',[('叶仁鲁','因涉赃被赐死'),('帝','依法赐死旧部叶仁鲁')],when='953年正月庚午',place='后周、莱州',note='金额为史书所列涉赃，不编具体单笔受贿者；旧纪称前莱州刺史，保留职衔阶段差异。')
sup('ye_renlu_corruption_sentence',4,oldjan,'前萊州刺史葉仁魯賜死，坐為民所訟故也。','《旧五代史》同日也记前莱州刺史叶仁鲁因被百姓控告而赐死。','该书未列主书赃额，前刺史与主书刺史称谓并列，不另造同名人物。',relation='adds')
add('guo_promises_ye_mother_support','郭威派中使给叶仁鲁酒食，说明其触犯国法，并承诺照顾其母',4,'帝遣中使赐以酒食曰：',None,[('帝','派使赐酒食并承诺照顾叶仁鲁之母'),('叶仁鲁','听到诏意后感动哭泣')],when='953年正月庚午赐死时',place='后周',note='母亲未具名，不据承诺认定后续全部赡养手续已经完成。')
add('wang_jun_inspects_river','郭威忧虑河决，准许王峻亲自巡视',5,'帝以河决为忧，','许之。',[('帝','准许王峻察看河决'),('王峻','请求亲自巡视黄河决口')],when='953年正月，闰月以前',place='黄河决口地区')
sup('wang_jun_inspects_river',5,oldjan,'辛未，詔樞密使王峻巡視河堤。峻請行，故從之。','《旧五代史》明确记正月辛未批准王峻巡视河堤。','主书未给此行明确日，以旧纪作独立日期补证；河堤巡视与治理工程完成不同。',relation='adds',field='time_original')
add('wang_jun_blocks_rong_visits','柴荣多次请求入朝，王峻因忌惮其才能而屡次阻止',5,'镇宁节度使荣','每沮止之。',[('荣','以镇宁节度使身份多次请求入朝'),('王峻','据史书所记忌惮柴荣而多次阻止')],year=None,when='953年闰正月入朝以前一段时期，具体起始未载',place='澶州、后周朝廷',note='忌其英烈为史书对王峻动机的解释，未补本人未载言辞。')
add('guo_allows_rong_court','闰正月王峻巡视河堤时，郭威准许柴荣再次请求入朝',5,'闰月，荣复求入朝，',None,[('荣','再次请求入朝'),('帝','在王峻巡视河堤时准许入朝')],when='953年闰正月，丙申入朝以前',place='澶州、后周朝廷')
add('yang_hongyu_repels_khitan','契丹围义丰军，杨弘裕夜袭敌营大获，契丹撤去',6,'契丹寇定州，','契丹遁去。',[('杨弘裕','以定和都指挥使身份夜袭契丹营寨获胜')],when='953年闰正月条下，具体夜袭日未载',place='定州、义丰军')
sup('yang_hongyu_repels_khitan',6,oldinter,'辛卯，定州奏，契丹攻義豐軍，出勁兵夜斫蕃營，斬首六十級，契丹遁去。','《旧五代史》闰月辛卯记定州奏报夜袭契丹军、斩首六十级并迫其退去。','辛卯为奏报，不能认定夜袭就是当晚；旧纪未具名杨弘裕，人物来自主书。',relation='adds')
add('zhenzhou_repels_khitan','契丹又进犯镇州，当地军队击退来敌',6,'又寇镇州，',None,[],when='953年闰正月条下，具体交战日未载',place='镇州')
sup('zhenzhou_repels_khitan',6,oldinter,'甲午，鎮州奏，契丹寇境，遣兵追襲，至無極而還。','《旧五代史》闰月甲午记镇州奏报追击契丹至无极而还。','补追击范围及奏报日，未将甲午硬定为全部交战步骤的发生日。',relation='adds')
add('rong_enters_court','柴荣以镇宁节度使身份入朝',7,'丙申，','镇宁节度使荣入朝。',[('荣','以镇宁节度使身份入朝')],when='953年闰正月丙申',place='澶州至后周朝廷')
sup('rong_enters_court',7,oldinter,'丙申，皇子澶州節度使榮來朝。','《旧五代史》同日记皇子、澶州节度使荣来朝。','同一柴荣身份，皇子为郭威养子背景称谓，不将其误录成郭威血亲新人物。')
add('ma_quanyi_joins_rong','马全乂此前在河中效力李守贞，后追随柴荣入朝',7,'故李守贞骑士马全乂','从荣入朝，',[('马全乂','以李守贞旧骑士身份随柴荣入朝'),('荣','带马全乂入朝')],when='953年闰正月丙申',place='澶州至后周朝廷',note='故为原属李守贞而非马全乂已死；此前骑士关系作背景，不编李守贞仍在本日活动。')
sup('ma_quanyi_joins_rong',7,songearly,'漢乾祐中，李守貞鎮河中，召置帳下。及守貞叛，周祖討之，全義毎率敢死士，夜出攻周祖壘，多所殺傷。','《宋史》马全义传补记其在乾祐中入李守贞帐下，河中战事时多次夜袭郭威营垒。','这些是此前河中经历，不归入953年当日交战；同一效力经历与后续召见印证同人。',relation='adds')
add('guo_commissions_ma_quanyi','郭威召见马全乂，任命为殿前指挥使，并称赞其忠于旧主',7,'帝召见，','汝辈宜效之。”',[('帝','召见任命马全乂并称赞其忠于所事'),('马全乂','获任殿前指挥使，被郭威称赞')],when='953年闰正月柴荣入朝时',place='后周朝廷')
sup('guo_commissions_ma_quanyi',7,songzhou,'從世宗入朝，周祖召見，補殿前指揮使，謂左右曰：「此人忠於所事，昔在河中，屢挫吾軍，汝等宜效之。」','《宋史》记马全义随柴荣入朝，同样获任殿前指挥使，并保存郭威对其忠诚的赞语。','同次任职和相同赞语支持马全义与马全乂同人，未把后续世宗即位后的任职提前。')
claim('person',people['马全乂'],'aliases','《通鉴》的马全乂与《宋史》马全义据河中旧经历、随柴荣入朝、同次任职及赞语对应为同人。',7,'從世宗入朝，周祖召見，補殿前指揮使，', '保存全乂、全义两种写法，不与马全节混同。',source=songzhou)
add('wang_jun_returns_daliang','王峻听说柴荣已入朝，立即从河堤返回，戊戌到大梁',7,'王峻闻荣入朝，',None,[('王峻','得知柴荣入朝后赶回大梁')],when='953年闰正月戊戌抵达大梁；此前从河堤启程',place='黄河堤至大梁',note='戊戌为到达日，不擅自认定其收到消息和出发也在同日。')
add('gao_yunquan_dies','雄武节度使高允权去世',8,'雄武节度使高允权卒，','雄武节度使高允权卒，',[('高允权','以雄武节度使身份去世')],when='953年闰正月，高绍基隐瞒父丧以前，实际死亡日未载',place='延州')
sup('gao_yunquan_dies',8,oldinter,'丁未，延州節度使高允權卒。','《旧五代史》闰月丁未才记高允权去世。','主书先记死亡后隐丧，旧纪较晚登记可能是公开父丧后的奏报，不认定实际死亡一定是丁未。',relation='adds',field='time_original')
add('gao_shaoji_hides_death','高绍基谋求继任，谎称父亲患病，上表自称暂掌军府',8,'其子牙内指挥使绍基','表己知军府事。',[('绍基','隐瞒父丧，假称父亲患病并谋求继任')],when='953年闰正月高允权死亡以后、辛丑以前',place='延州',note='主书已明说谋袭诈称，不能把自称暂掌等同朝廷正式任命。')
sup('gao_shaoji_hides_death',8,oldinter,'延州衙內指揮使高紹基奏言：「父允權患腳膝，令臣權知軍州事。」','《旧五代史》保留高绍基声称父亲患脚膝病、让自己暂掌军州的奏报。','该句是高绍基所称，结合主书记诈称，不能写成高允权确已发出亲署授权。',relation='adds')
add('gao_kills_li_bin','李彬极力劝谏高绍基，高绍基愤怒将他杀死',8,'观察判官李彬','斩之，',[('李彬','以观察判官身份劝谏，被高绍基杀死'),('绍基','因劝谏发怒，杀死李彬')],when='953年闰正月，辛丑上报以前',place='延州')
add('gao_accuses_li_bin_rebellion','高绍基向朝廷诬报李彬谋反',8,'辛丑，',None,[('绍基','将被杀的李彬诬报为谋反者')],when='953年闰正月辛丑',place='延州至后周朝廷',note='结合前句劝谏后被斩的因果记载为虚报，未将李彬确实谋反当作史实。')
relationship('高允权','高绍基','父亲',8,'其子牙内指挥使绍基谋袭父位，诈称允权疾病，表己知军府事。','原文明示其子绍基，方向为高允权是高绍基的父亲。')
add('wang_jun_pinglu_commission','王峻坚持要求兼领藩镇，郭威不得已让他兼平卢节度使',9,'王峻固求领籓镇，',None,[('王峻','坚持要求领藩镇，获兼平卢节度使'),('帝','在王峻坚持要求下授其兼职')],when='953年闰正月壬寅',place='后周朝廷、平卢军',note='兼任不是立即离开枢密使等原职，帝不得已为史书描述。')
sup('wang_jun_pinglu_commission',9,oldinter,'壬寅，以樞密使、尚書左僕射、同平章事、監修國史王峻兼青州節度使，餘如故。','《旧五代史》同日记王峻兼青州节度使，其余职务照旧。','青州为平卢治所，余如故印证兼任而非罢去中央原职。')
add('gao_shaoji_repeated_border_reports','高绍基反复奏报边地遭侵扰，希望因此获准继任',10,'高绍基屡奏','冀得承袭，',[('绍基','反复奏报边境受侵扰，以谋求获准继任')],when='953年闰正月高允权父丧公开以前',place='延州',note='冀得是希望获得任命，不能写成继任已获批准；杂虏为史书概称，未按现代民族细分。')
add('zhang_renqian_inspects_yanzhou','郭威派张仁谦赴延州巡检，高绍基无法继续隐瞒，才公开父丧',10,'帝遣六宅使张仁谦',None,[('帝','派六宅使张仁谦巡检延州'),('张仁谦','赴延州巡检'),('绍基','巡检后无法隐瞒，公开父丧')],when='953年闰正月，高绍基多次奏报以后',place='后周朝廷至延州',note='主书始发父丧不说明高允权此时才死亡，公开与实际死亡分开。')

reviews={1:'主书四项正式授职与旧纪张仿、朱元琇补任分开；领刺史不写迁往该州，何敬真贞和朱全元姓名异文有同日军府与后续同人记载。',2:'诏书招抚条件、李万全等立誓及仍不服者讨伐为奏报层次，未补已全部受赏或灭族。',3:'此前制度与953改革分开；朱温掠牛未知战役年，牛死租留为制度延续。户部增户为改隶登记可能，未写出生户；原肥铙字保留，展示肥沃。旧书先有例外与后续归县分别补证。',4:'叶仁鲁赃额、赐死与郭威赐酒食承诺分开，前刺史与刺史称谓保留，母亲未具名不造实体。',5:'河决巡视、王峻阻柴荣入朝、闰月获准分开；旧书辛未日期作为巡视补证。',6:'义丰军夜袭与镇州驱敌分开；旧纪辛卯甲午为奏报日，六十级和追至无极仅作补充。',7:'柴荣入朝、马全乂随行获任及王峻戊戌返回分录；全乂全义按同经历同职同赞语对应，故为旧骑士，不误读已死。',8:'父死、隐丧谋继、杀李彬及诬报谋反分录；旧纪丁未登记与主书死亡时点不强等同，父子方向明确。',9:'求兼藩镇与壬寅获任同一事件，旧纪青州与平卢治所对应，原中央职保留。',10:'反复奏报是谋继，巡检促公开父丧不当实际死亡发生日，未凭同名合并李彬。'}
assert not (P/'publication.json').exists()
for n in range(1,11):
 assert ledger[n-1]['status'] in ('pending','reviewed');ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=953,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph=Q[11]['id'],next_volume=291,next_year=953,supplements=supplements,excluded_non_body=[],coverage='卷291原33—42行连续十段；953年共46正文，后续尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,11)],source_issues_review='全乂与全义、敬真与敬贞、全琇与元琇按职务行动连续校核，原字保留。肥铙疑字只在展示释义，死亡与奏报区别清楚。纸本异文未核。',plain_language_review='首次逐条核对全部展示字段，人物姓名、动作、角色与关系方向明确；制度回述、建议条件、任命执行、计划与奏报分别说明。引文保持底本原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
