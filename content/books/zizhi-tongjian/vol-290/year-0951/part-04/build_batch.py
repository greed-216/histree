# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 951 paragraphs 23–30."""
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
COMMIT='dd3926f483152113be60d810cbf48dffff7b9b14'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-111-jinzhou','jiuwudaishi-111-xizhou','xinwudaishi-011-first-year-951']:
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
main_sources = ['tongjian-290-951-february-diplomacy']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0951-p023-p030',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-290-951-february-diplomacy': '卷290·广顺元年·二三月外交与楚国册封', 'xinwudaishi-066-chu-investiture': '卷66·楚世家·南唐册封马希萼', 'songshi-261-chen-yingzhou': '卷261·陈思让传·湖南赴援与郢州停军', 'songshi-261-chen-recall-cizhou': '卷261·陈思让传·召还与磁州驻防'}
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
for n in range(23, 31):
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
    labels={'tongjian-290-951-february-diplomacy': '卷290·广顺元年·二三月外交与楚国册封', 'xinwudaishi-066-chu-investiture': '卷66·楚世家·南唐册封马希萼', 'songshi-261-chen-yingzhou': '卷261·陈思让传·湖南赴援与郢州停军', 'songshi-261-chen-recall-cizhou': '卷261·陈思让传·召还与磁州驻防'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺元年（951年二三月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0951_04_{len(B["claims"])+1:04d}'
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










ALIASES.update({'帝':'郭威','楚王':'马希萼','唐主':'李璟','北汉主':'刘崇（刘知远弟）','契丹主':'耶律阮','硃宪':'朱宪（后周使者）','鱼崇谅':'鱼崇远','孙忌':'孙晟'})
NEW_ALIASES={'刘光辅':['劉光輔'],'袅骨支':['䮍骨支'],'田敏':[],'李巩言':[]}
NEW_DESCRIPTIONS={'刘光辅':'马希萼的掌书记。951年二月奉命向南唐进贡。生卒年未载。','袅骨支':'契丹使臣。951年二月与后周使者朱宪一同来后周，祝贺郭威即位。《新五代史》字形写作䮍骨支；《旧五代史》同日贺即位使者写郭济，是否同人待核。生卒年未载。','田敏':'后周尚书左丞。951年二月奉命出使契丹。《旧五代史》也记录他充契丹国信使。生卒年尚未录入。','李巩言':'北汉通事舍人。951年奉刘崇派遣出使契丹，请求援兵。生卒年未载。'}
jin='jiuwudaishi-111-jinzhou';xi='jiuwudaishi-111-xizhou';nw='xinwudaishi-011-first-year-951';chu='xinwudaishi-066-chu-investiture';ying='songshi-261-chen-yingzhou';recall='songshi-261-chen-recall-cizhou'
add('chu_liu_guangfu_tribute','马希萼派刘光辅向南唐进贡',23,'甲辰，',None,[('楚王','派掌书记向南唐进贡'),('刘光辅','以掌书记身份出使进贡')],when='951年二月甲辰',place='楚国至南唐',note='本段记录进贡出使，没有提前录入刘光辅后来秘密建议南唐取湖南的谈话。')
add('guo_smashes_han_treasures','郭威把后汉宫中数十件宝玉器物砸碎',24,'帝悉出','宜以为鉴！”',[('帝','砸碎后汉宫中宝玉器物，并以刘承祐为戒')],when='951年二月甲辰进贡条后，具体砸器日未另载',place='后周宫廷庭院',note='郭威关于刘承祐与宠臣嬉戏的说法是其讲话内容，未独立证明每天活动；不据该叙述给死去的刘承祐建立951年参与。')
sup('guo_smashes_han_treasures',24,jin,'內出寶玉器及金銀結縷、寶裝床幾、飲食之具數十，碎之於殿庭。','《旧五代史》还列出金银装饰、宝装床几和饮食用具等被砸物件。','《旧五代史》将此事列于丙午条下；《资治通鉴》未另列日期，保留其叙述位置，不自行换算公历。',relation='adds')
add('guo_bans_palace_luxuries','郭威禁止珍华悦目的物品再进入宫中',24,'仍戒左右，',None,[('帝','命身边侍从以后不得把珍华物品送入宫')],when='951年二月砸碎宝玉器物后，具体日未载',place='后周宫廷',note='禁令针对进入宫廷的珍华物品，不推为全社会禁止珠宝交易。')
sup('guo_bans_palace_luxuries',24,jin,'仍詔所司，凡珍華悅目之物，不得入宮。','《旧五代史》也记禁止珍华物品入宫的诏令。','禁令与砸器行动分别登记，避免把长期规定当成另一次砸器。')
add('khitan_congratulates_guo','耶律阮派袅骨支与朱宪一同来后周，祝贺郭威即位',25,'丁未，',None,[('契丹主','派使臣向郭威贺即位'),('袅骨支','作为契丹使臣来后周贺即位'),('硃宪','从契丹返回，与来使同行'),('帝','接受契丹使者对即位的祝贺')],when='951年二月丁未',place='契丹至后周朝廷',note='朱宪复用此前后周出使档案；袅骨支与《旧五代史》郭济是否同人尚未核定，不加郭济别名。')
sup('khitan_congratulates_guo',25,nw,'丁未，契丹兀欲遣使䮍骨支來。','《新五代史》也记丁未契丹使者来朝，姓名字形为䮍骨支。','同一日期、派遣者和来使场景支持对应袅骨支；原文字形保留。')
sup('khitan_congratulates_guo',25,jin,'丁未，左千牛將軍朱憲使契丹回。契丹主烏裕遣使郭濟獻良馬一駟，賀登極。','《旧五代史》记同日朱宪归来，契丹派郭济献良马一驷、贺即位。','该使者姓名不同，是否同一使团中的不同人或同人异名未定；不把两个人名直接合并。良马一驷是此书记载的贡物。',relation='conflicts')
add('former_officials_live_outside','郭威准许前资官自行在外州居住',26,'戊申，','各听自便居外州。',[('帝','准许前资官在外州自便居住')],when='951年二月戊申',place='后周各州府',note='前资官指此前任过官、目前未任职的官员，不译成所有现任官员；自便外居不等于所有人已经迁居。')
sup('former_officials_live_outside',26,jin,'應諸道州府，有前資朝官居住，如未赴京，不得發遣。','《旧五代史》进一步规定，住在地方而尚未赴京的前资朝官，不得被地方强行发遣入京。','这段诏书具体解释政策对象与做法，不泛化为现任官员可随意离职。',relation='adds')
sup('former_officials_live_outside',26,jin,'年月未滿，一聽外居。如非時詔征，不在此限。','《旧五代史》还允许任职期满候选官在规定期限内外居，但临时奉诏征召者不在此限。','诏书前文“得替求官，自有月限”说明这是候选官求官期限；保留非时征召例外。',relation='adds')
add('chen_stays_yingzhou','陈思让尚未到湖南，长沙已失守，于是留驻郢州',26,'陈思让未至湖南，','思让留屯郢州，',[('陈思让','赴援途中得知长沙失守，留驻郢州'),('楚王','已攻克长沙，使赴援失去原目标')],year=None,when='950年长沙失守至951年二月召还以前的追述，具体停军日未载',place='郢州',note='马希萼克长沙是此前已录的950年史事，这里只记录赴援军队未能到达和停驻，不另建一次攻克事件。')
sup('chen_stays_yingzhou',26,ying,'乃分兵令思讓往郢州赴援，兵未渡而希廣敗。思讓留於郢。','《宋史》也记陈思让往郢州赴援，未渡时马希广已败，陈思让留在郢州。','相邻原文马希灊字形及合兵淮南表述有疑，未据这些字句另建姓名、联军或路线；此处只引用停军与援救未成的明确记载。')
add('guo_recalls_chen','郭威下敕召回留驻郢州的陈思让',26,'敕召令还。',None,[('帝','召陈思让及部队返回'),('陈思让','被朝廷下令从郢州返回')],when='951年二月戊申外居敕之后条下，具体召还日未另载',place='郢州至后周朝廷',note='召令是命令，不推定同日已经返回京师。')
sup('guo_recalls_chen',26,recall,'周祖即位，遣供奉官邢思進召思讓及所部兵還。','《宋史》补记郭威派供奉官邢思进召陈思让和所部兵返回。','该传只以郭威即位标记阶段，未给召还的具体月日。',relation='adds')
add('tian_min_khitan_mission','郭威派尚书左丞田敏出使契丹',27,'丁巳，','使契丹。',[('帝','派田敏出使契丹'),('田敏','以尚书左丞身份出使')],when='951年二月丁巳',place='后周至契丹',note='出使行为与北汉另派李巩言求援区分，不把田敏当成北汉使者。')
sup('tian_min_khitan_mission',27,xi,'丁已，以尚書左丞田敏充契丹國信使。','《旧五代史》也记田敏任契丹国信使，底本纪日写丁已。','《资治通鉴》《新五代史》写丁巳；已巳字形差异保留，不悄悄改写引文。')
sup('tian_min_khitan_mission',27,nw,'丁巳，尚書左丞田敏使于契丹。','《新五代史》也记二月丁巳田敏出使契丹。','纪日、职务和目的地与《资治通鉴》相符。',field='time_original')
add('li_gongyan_requests_troops','刘崇派李巩言出使契丹，请求援兵',27,'北汉主遣',None,[('北汉主','派通事舍人出使请求援兵'),('李巩言','奉命向契丹请求援兵')],when='951年二月丁巳田敏出使条后，具体北汉使者出发日未另载',place='北汉至契丹',note='两方出使在同段记载，不强定李巩言也在丁巳出发；求援不等于已经得到援兵。')
add('murong_zhongshuling','郭威加授慕容彦超中书令',28,'诏加泰宁节度使慕容彦超','中书令，',[('帝','加授慕容彦超中书令'),('慕容彦超','以泰宁节度使身份加官')],when='951年二月末至三月壬戌答诏以前，具体加官日未另载',place='后周朝廷与泰宁军',note='加官位于三月朔答诏前，不能把整段所有动作都套成壬戌同日。')
add('yu_congyuan_yanzhou','郭威派鱼崇谅到兖州向慕容彦超传达旨意',28,'遣翰林学士鱼崇谅','崇谅，即崇远也。',[('帝','派翰林学士去兖州传达旨意'),('鱼崇谅','奉命到兖州传旨，原名鱼崇远'),('慕容彦超','成为传旨对象')],when='951年三月壬戌答诏以前，具体派遣日未载',place='兖州',note='原文明示鱼崇谅就是鱼崇远，复用既有主体；不与其他史书中同名崇谅人物凭字面合并。')
claim('person',people['鱼崇远'],'name','鱼崇谅即鱼崇远。',28,'崇谅，即崇远也。','《资治通鉴》直接说明同人，保存改名后的称法，保留既有稳定key。')
add('murong_thanks_guo','慕容彦超上表向郭威谢恩',28,'彦超上表谢。',None,[('慕容彦超','上表谢恩')],when='951年加官传旨后、三月壬戌答诏以前',place='兖州至后周朝廷',note='谢表与郭威回诏是前后两项动作，不能合为一次使者行动。')
add('guo_reassures_murong','郭威答复慕容彦超，赞许其为后汉尽职并表示暂不调镇',28,'三月，壬戌朔，',None,[('帝','以诏书赞许慕容彦超侍奉旧君，并表示不拟调换其任所'),('慕容彦超','收到安抚答诏，被要求安民尽职')],when='951年三月壬戌朔',place='后周朝廷与泰宁军',note='诏书赞许是郭威的政治评价，不视为本站独立证实慕容彦超全部忠诚动机；前朝失德等是诏书措辞，未改成中立史实。',description='郭威在回诏中赞许慕容彦超此前应后汉召命，并称忠于旧君不应成为疑惧理由。他要求慕容彦超尽力安民、侍奉后周，并表示尚不考虑调换其任所。')
add('li_jing_invests_ma_xie','李璟册封马希萼为楚王，授天策上将军等职',29,'唐以楚王希萼','楚王，',[('唐主','册封马希萼并授军镇和中书令等职'),('楚王','获天策上将军、四军节度使兼中书令、楚王封号')],when='951年三月壬戌答诏后条下，具体册封日未另载',place='南唐与楚国',description='李璟授马希萼天策上将军、武安、武平、静江、宁远节度使兼中书令，并册封为楚王。',note='多个节度使头衔是册授内容，不推定马希萼当时实际控制各军全部地域。')
sup('li_jing_invests_ma_xie',29,chu,'希萼遂臣於李景，景冊封希萼楚王，','《新五代史》也记马希萼向李璟称臣，并获册封楚王。','相邻句把汉隐帝死亡放在乾祐三年的明年，与950年死亡纪年不一致，未用它改变《资治通鉴》的951年册封记录。此处与篇末马氏被迁后再次封楚王分开。')
add('sun_yao_investiture_envoys','李璟任命孙忌、姚凤为册礼使',29,'以右仆射孙忌',None,[('唐主','任命两名册礼使'),('孙忌','以右仆射身份任册礼使'),('姚凤','以客省使身份任册礼使')],when='951年三月马希萼册封条下，具体任命及到达日未载',place='南唐至楚国',note='孙忌沿既有孙晟及孙凤别名主体；姚凤复用945年南唐将领档案，未因官职改变另建人。册礼使任命不等于已到楚国完成礼仪。')
add('chen_garrisons_cizhou','郭威派陈思让率兵驻磁州，控制黄泽路',30,'丙寅，',None,[('帝','派陈思让驻兵磁州控制黄泽路'),('陈思让','以前淄州刺史身份领兵驻防')],when='951年三月丙寅',place='磁州、黄泽路',note='驻军行动与后来磁州刺史、团练使任命分开，不提前录入传记中的后续升迁。')
sup('chen_garrisons_cizhou',30,recall,'遣思讓率兵詣磁州，控扼澤、潞。','《宋史》也记郭威派陈思让率兵去磁州，控制泽州、潞州方向。','《资治通鉴》写黄泽路，《宋史》写泽、潞，作为各书对驻防目的的说明保留，不推定新行政边界。')
reviews={23:'甲辰承二月，入贡与后续密议分开。',24:'砸器行动、郭威讲话与禁入规定区分。旧本纪列丙午，主书未另纪日；刘承祐嬉戏为郭威提及的传闻，不建立951年活动。',25:'朱宪复用后周使者；袅骨支与䮍骨支同日同使团对应，旧郭济名字和马贡并列待核，不强合。',26:'前资官外居不是在职官自由离任，旧诏求官月限及非时征召例外保留。陈在郢的停军起点跨950至951不强定年，召还与返京完成分开，宋传印证。',27:'田敏后周出使与李巩言北汉求援分开；李出发日未定，不套丁巳。旧丁已原字保留，新丁巳印证。',28:'加官、遣鱼、谢表、三月壬戌答诏分录；鱼改名明确沿稳定主体，诏评价不改成已证实动机。',29:'天策与四军等册授不是实际疆域确证；孙忌复用孙晟，姚凤沿已有南唐将。新楚世家相邻汉隐死年有问题，不据其改变主书册封时间，也未提前录下文楚政变。',30:'三月丙寅驻磁州，黄泽路和宋传控泽潞方向分别保留，不提前宋传未几升官。'}
assert not (P/'publication.json').exists()
for n in range(23,31):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=951,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(23,31)],next_paragraph=Q[31]['id'],next_volume=290,next_year=951,supplements=supplements,excluded_non_body=[],coverage='卷290原28—35行连续八段；本年后续正文仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(23,31)],source_issues_review='已检查上下文、官职、姓名和时间。旧郭济与主新袅骨支来使异说、旧丁已字形、新楚世家汉隐崩的相邻纪年问题均保留；宋陈传马希灊及淮南字句未据以建立新身份。朱宪限定后周使者，鱼崇谅与孙忌按明确同人说明复用。原文不改字，纸本未核。',plain_language_review='本次逐条检查所有新增展示文案与事实说明；动作、传闻、诏书评价、命令、实际执行及追述年月分清。原文引用保持底本字形，繁简转换仅用于展示；不安排固定的第二轮文案重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
