# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 955 paragraphs 25–31."""
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
COMMIT='7d5d8eead8288f56c81433a236a49d52b585665f'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-292-955-qinfeng-first-order','jiuwudaishi-115-zhangmei-eight-month']:
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
main_sources = ['tongjian-292-955-qinfeng-first-order','tongjian-292-955-autumn-qinfeng']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0955-p025-p031',
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
for n in range(25, 32):
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
        citation = f'卷292·显德二年（955年八月至十月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0955_04_{len(B["claims"])+1:04d}'
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










ALIASES.update({'上':'柴荣','帝':'柴荣','蜀主':'孟昶','王景':'王景（后晋耀州团练使）','王溥':'王溥（后周宋初）','李进':'李进（后蜀先锋将）','王峦':'王峦（后蜀染院使）'})
NEW_ALIASES={'李进（后蜀先锋将）':[],'张建雄':['張建雄'],'王峦（后蜀染院使）':[],'赵玭':['趙玭']}
NEW_DESCRIPTIONS={
'李进（后蜀先锋将）':'后蜀先锋都指挥使。955年秦凤战事中，李廷珪派他据守马岭寨。与此前南汉交州将李进、洋州将李进唐缺少同人证据，分别保存。生卒年未载。',
'张建雄':'后周将领。955年秦凤战事中，王景派他率二千人到黄花，配合截断后蜀军退路的部队击败蜀军。《宋史》向拱传称他为排阵使。生卒年未载。',
'王峦（后蜀染院使）':'后蜀染院使。955年率军由唐仓出兵，在黄花交战失利。《通鉴》记他被俘，《旧五代史》本纪也记俘获，而该书引《九国志》记他战死。与此前后晋殿直王峦暂无同人证据，不作合并，死亡年份不据异说写死。',
'赵玭':'澶州人，后蜀秦州观察判官。955年秦凤战事中带秦州归降后周。柴荣拟任其为节度使，范质反对，最后任郢州刺史。《宋史》本传补充其闭城门拒纳败军、召官属商议归降的经过。生卒年未载。'
}
aug='jiuwudaishi-115-zhangmei-eight-month';cop='jiuwudaishi-115-copper-and-prisoners';old='jiuwudaishi-115-huanghua-report';sbat='songshi-255-huanghua-battle';zi='songshi-274-zhaopin-identity';zs='songshi-274-zhaopin-surrender'
add('jingfan_leaves_finance','景范停止兼管三司事务',25,'八月，','罢判三司，',[('景范','以宰相身份停止兼判三司')],when='955年八月丁未',place='后周朝廷',note='罢判三司不等于同时罢相，守丧离开政事是随后另一阶段。')
sup('jingfan_leaves_finance',25,aug,'丁未，中書侍郎、平章事、判三司景範罷判三司，','《旧五代史》同记八月丁未景范停止判三司。','原书名字景範沿同一主体，罢财务兼职不译为被开除全部官职。')
add('jingfan_mourning','景范随后因父亲去世而停止政务',25,'寻以',None,[('景范','因父丧停止政务')],when='955年八月罢判三司之后不久，具体日未载',place='后周朝廷',note='寻只表相隔不久，不把父丧和罢政事都强定丁未；父亲姓名未载。')
add('wangjing_captures_threehundred','王景等击败后蜀军，俘获将卒三百人',26,'王景等','获将卒三百。',[('王景','率军击败后蜀军并俘获三百将卒')],when='955年八月段所记，具体交战日未载',place='秦凤战场',note='这是此前一场交战的俘虏，不与闰月黄花战役俘虏相加，也不从送到京城纪日推交战日。')
sup('wangjing_captures_threehundred',26,cop,'辛卯，西南面招討使王景，部送所獲西川軍校姜暉已下三百人至闕。','《旧五代史》另记九月辛卯王景将姜晖以下三百名被俘后蜀军校送到京城。','这是押送抵京的纪日，与主书八月条交战捕获的时点分别保存；同为三百人不能单凭人数认定所有名单完全相同。',relation='adds')
add('yishenzheng_campaign_visit','孟昶派伊审征到行营慰劳并督战',26,'己未，',None,[('蜀主','派伊审征到行营'),('伊审征','以通奏使、知枢密院、武泰节度使身份慰劳督战')],when='955年八月己未',place='后蜀行营',note='慰扶与督战是同一次派遣的任务，不把受命日当成到达日。')
add('copper_mints_order','柴荣因钱币短缺，下令设监采铜铸钱',27,'帝以县官','始立监采铜铸钱，',[('帝','因钱币减少命设监采铜铸钱')],when='955年九月丙寅朔',place='后周辖区',description='《通鉴》记官府久未铸钱，民间又熔钱制作器皿和佛像，钱币愈少。柴荣因此下令设监采铜铸钱。这里县官指官府，不是某名县令；诏令不等于所有铸钱机构当日已经建成。')
sup('copper_mints_order',27,cop,'九月丙寅朔，詔禁天下銅器，始議立監鑄錢。','《旧五代史》同日记禁止铜器并开始商议设监铸钱。','旧史记始议、主书记敕始立，两书行动表述分别保留，均不推定当日已经完成生产。')
add('copper_collection_rules','柴荣要求五十日内交纳部分铜器与佛像，并给付价款',27,'自非县官法物、','给其直；',[('帝','规定交铜期限、例外和给价')],when='955年九月丙寅朔诏令，交纳期限五十日',place='后周辖区',description='除官府法物、军器，以及寺观钟、磬、钹、铎等获准保留的物件外，民间铜器和铜佛像须在五十日内交给官府，官府给付价款。没有把所有宗教用品都列为征收对象，也未记录每户实际成交金额。',note='磐疑磬及鐸等底本原字保留；期限沿原书，不换算为现代截止日。')
add('copper_concealment_penalties','柴荣规定逾期藏匿应交铜器的处罚',27,'过期隐匿','论刑有差。',[('帝','规定隐匿不交铜器的刑罚')],when='955年九月丙寅朔诏令，五十日期满后适用',place='后周辖区',description='应交铜器逾期被隐匿不交，藏匿五斤以上者处死，不满五斤者按数量分别处罚。这里是诏令规定，史书本段没有列出已被处死的具体案件。',note='五斤是史载单位，不换算现代重量；不等于持有所有铜器五斤即可定罪，须保留应交、逾期、隐匿三个条件。')
add('chairong_explains_buddha_images','柴荣向侍臣解释征收铜佛像的理由',27,'上谓侍臣曰：',None,[('上','用佛教利人、行善观念解释征收铜像')],when='955年九月征铜铸钱政策时，讲话具体日未单列',place='后周朝廷',description='柴荣告诉侍臣，不必因毁损佛像而疑虑：佛以善道教化，行善才是奉佛，铜像本身并不是佛；若自己的身体能帮助百姓，也不应吝惜。这是柴荣解释政策时的讲话，不作本站对佛教教义的裁定。')
commentary_before=len(B['claims'])
claim('person',people['柴荣'],'evaluation','司马光赞许柴荣以百姓利益为重、不让他认为无益之物妨碍有益之事，称其仁而明。',28,Q[28]['text'],'臣光曰是司马光的史论，沿原段引用保存为人物评价，不生成955年当日发生的评论事件。')
commentary_keys=[c['key'] for c in B['claims'][commentary_before:]]

add('shu_blocks_qinfeng_supply','李廷珪派兵据马岭、白涧等地，试图截断周军粮道',29,'蜀李廷珪','绝周粮道。',[('李廷珪','安排多路兵力据寨设营、截断周军粮道'),('李进','以先锋都指挥使身份据马岭寨')],when='955年闰月黄花战役以前，具体布兵日未载',place='马岭寨、斜谷、白涧、凤州北唐仓镇及黄花谷',note='军事目的与截粮实际效果分开，不给未载的奇兵将领姓名。')
add('wangjing_huanghua_deployment','王景派张建雄赴黄花，并派另一支部队截断蜀军退路',29,'闰月，','扼蜀归路。',[('王景','部署两路兵力'),('张建雄','率二千兵赴黄花')],when='955年闰月，具体出兵日未载',place='黄花至唐仓',description='王景派张建雄率二千兵到黄花，又派一千兵赴唐仓扼守蜀军归路。第二路将领未具名，二千人与一千人是两支部队，不是俘虏数。')
sup('wangjing_huanghua_deployment',29,sbat,'拱與王景偵知之，命排陣使張建雄領兵二千直抵黃花谷，又遣別將領勁卒千人出敵後，截其歸路。','《宋史》向拱传记向拱与王景侦知蜀军行动后，命排阵使张建雄率二千兵赴黄花，并派千兵截断退路。','该传向拱对应此役主书向训，沿既有主体；官号与共同部署情况作为补充，不据此改变主书姓名。',relation='adds')
add('huanghua_tangcang_victory','张建雄等在黄花、唐仓接连击败王峦所部',29,'蜀染院使王峦','虏峦及其将士三千人。',[('王峦','率后蜀兵出唐仓，在黄花战败后又在唐仓被击败'),('张建雄','率周军与王峦交战')],when='955年闰月，具体交战日未载',place='黄花及唐仓',description='后蜀染院使王峦率兵由唐仓出发，在黄花被张建雄击败，退回唐仓又遇周军而败。《通鉴》记王峦及其将士三千人被俘；《旧五代史》《宋史》记一千五百余人，旧史引《九国志》还记王峦战死，数量和生死差异均保留。',note='后蜀王峦与旧后晋殿直王峦无同人证据，新增限定名主体；不以俘虏统计异说推定确切死伤总数。')
sup('huanghua_tangcang_victory',29,old,'閏月壬子，西南面招討使王景奏，大破西川賊軍於黃花谷，擒偽命都監王巒、孫韜等一千五百餘人。','《旧五代史》记闰月壬子王景奏报黄花谷获胜，俘王峦、孙韬等一千五百余人。','壬子是奏报日，不直接当作交战日；俘虏数与主书三千人有差别，不能相加。',relation='conflicts')
sup('huanghua_tangcang_victory',29,sbat,'擒其監軍王巒、孫韜等千五百餘。','《宋史》向拱传记俘获王峦、孙韬等一千五百余人。','传记未给战日；与旧史人数相近不等于已独立核定精确人数，主书异数继续保留。',relation='conflicts')
sup('huanghua_tangcang_victory',29,old,'又遣染院使王巒領兵出唐倉，與周師遇，蜀師敗走，王巒死之。','《旧五代史》所引《九国志·李廷珪传》另说王峦在败退中战死。','此为旧史注引另一书，来源依赖单独说明，不认作与旧史本纪相同结论，不据此直接填写人物死亡年份。',relation='conflicts')
add('shu_retreats_qingni','李廷珪、高彦俦等因军队溃败退守青泥岭',29,'马岭、白涧兵皆溃，','退保青泥岭。',[('李廷珪','在多处部队溃败后退守青泥岭'),('高彦俦','与诸将退守青泥岭')],when='955年闰月黄花战役之后',place='马岭、白涧至青泥岭')
add('hanjixun_abandons_qinzhou','韩继勋放弃秦州，逃回成都',29,'蜀雄武节度使','奔还成都、',[('韩继勋','以雄武节度使兼侍中身份放弃秦州，逃回成都')],when='955年闰月蜀军失利之后',place='秦州至成都',note='底本成都后的顿号保留引用，不影响动作分界；不从弃城推定韩继勋此时已经被处死。')
add('zhaopin_surrenders_qinzhou','赵玭率秦州归降后周',29,'观察判宫赵玭','斜谷援兵亦溃。',[('赵玭','以观察判官身份带秦州归降')],when='955年闰月蜀军败退之后，主书未单列归降日',place='秦州',note='判宫疑判官，原引用保留宫字，显示职官据宋传及旧本纪上下文为观察判官。')
sup('zhaopin_surrenders_qinzhou',29,old,'癸丑，秦州偽命觀察判官趙比以本城降，','《旧五代史》记闰月癸丑秦州观察判官赵比带城归降。','赵比与主书赵玭为同一秦州降城叙事的姓名异字，仍保留底本并暂不添加赵比别名；旧史癸丑与主书壬子庆功前叙归降的次序并列，未强改日期。',relation='adds')
sup('zhaopin_surrenders_qinzhou',29,zs,'玭閉門不納，召官屬諭之曰：','《宋史》补充赵玭关城门拒纳败退兵马，并召集官属商议。','前文高彦俦未至闻败溃归的叙次与主书分别保留；后文历史概括及伤亡说法是赵玭对官属的说辞，不当实测统计。',relation='adds')
sup('zhaopin_surrenders_qinzhou',29,zs,'眾皆俯伏聽命。玭遂以城歸朝。','《宋史》记官属听从，赵玭随后带城归降。','归朝是该书从后周承继王朝立场的用语，展示明确写归降后周。')
claim('person',people['赵玭'],'origin','赵玭为澶州人。',29,'玭，澶州人也。','籍贯只按原书，现代位置及坐标未核。')
claim('person',people['赵玭'],'origin','《宋史》也记赵玭为澶州人，家富有财。',29,'趙玭，澶州人。家富於財。','只取有明确支持的身份与籍贯；该传后文孟知祥署官与晋末入蜀时序可疑，不据此新增确年任命。',source=zi,relation='corroborates')
add('chengjie_surrender','成州、阶州归降，后蜀人心震恐',29,'成、阶二州皆降，','蜀人振恐。',[],when='955年闰月秦州归降前后，具体日未载',place='成州、阶州及后蜀',note='没有具名降将，不虚构人物；凤州最后攻克在后段，不能在此提前写四州全平。')
add('zhaopin_appointment_discussion','柴荣拟任赵玭为节度使，范质反对后改任郢州刺史',29,'帝欲以玭','郢州刺史。',[('帝','拟授节度使，最终授郢州刺史'),('范质','反对授赵玭节度使'),('赵玭','归降后获任郢州刺史')],when='955年闰月秦州归降之后，具体任命日未载',place='后周朝廷及郢州',note='拟授和实际授任分清，不为赵玭添加实际未获的节度使任职。')
sup('zhaopin_appointment_discussion',29,zs,'世宗欲命以藩鎮，宰相范質不可，乃授郢州刺史，','《宋史》也记柴荣拟授藩镇、范质反对，最后授郢州刺史。','后文历汝密泽三州是后续履历，不直接记为此次同时授任。')
add('chairong_praises_wangpu','柴荣在群臣庆功时称赞王溥选将有功',29,'壬子，',None,[('帝','向王溥举酒称赞'),('王溥','因推荐统帅获称赞')],when='955年闰月壬子',place='后周朝廷',note='边功为当时进展，凤州最终攻克还在后段；王溥非王朴，沿后周宋初主体。')
add('chairong_wansui_banquet','柴荣在万岁殿与将相用餐，表示愿冒险为百姓除害',30,Q[30]['text'],None,[('上','与将相用餐并谈为民除害的责任')],when='955年闰月甲子',place='万岁殿',description='柴荣与将相在万岁殿用餐，谈到这两日大寒，自己在宫中享用珍膳而未亲耕，感到惭愧，因此希望亲冒矢石为百姓除害。这是柴荣当时的责任表态，不是本段已发生的亲征行动。')
add('litinggui_apologizes','李廷珪上表请罪',31,'乙丑，','上表待罪。',[('李廷珪','因战事失利上表请罪')],when='955年闰月乙丑',place='后蜀',note='主书未明说此时已被处罚，后文明确释之。')
add('yishenzheng_apologizes','伊审征回到成都请罪，孟昶宽免他和李廷珪',31,'冬，十月，','皆释之。',[('伊审征','到成都请罪并获宽免'),('李廷珪','此前上表请罪后获宽免'),('蜀主','宽免请罪者')],when='955年十月壬申伊审征到成都；宽免具体日未另载',place='成都',note='皆释之承接两名请罪者，不解释为牢中所有囚犯均获释放。')
add('shu_peace_letter_rejected','孟昶以大蜀皇帝名义向柴荣请和，柴荣不予回复',31,'蜀主致书','不答。',[('蜀主','致书请和，自称大蜀皇帝'),('帝','因称号对等而愤怒，不回复')],when='955年十月请罪记载之后，具体送信日未载',place='后蜀至后周朝廷',description='孟昶致书柴荣请求和解，自称大蜀皇帝。柴荣因孟昶仍以对等皇帝称号行礼而生气，没有答复。请和、称号争执与未答复分别说明，不能记作已经签订和约。')
add('shu_defensive_buildup','孟昶在剑门、白帝集结兵粮，准备防守',31,'蜀主愈恐，','为守御之备，',[('蜀主','在剑门和白帝聚集兵粮备守')],when='955年十月请和未获答复以后，具体日未载',place='剑门、白帝',note='防御准备不等于后周此时已经进攻或占领剑门白帝。')
add('shu_iron_coinage','孟昶因募兵开支不足开始铸铁钱，并专管境内铁器',31,'募兵既多，',None,[('蜀主','在开支不足时铸铁钱并对铁器实行榷管')],when='955年十月段所记备守之后，具体日未载',place='后蜀境内',description='孟昶募兵增多而费用不足，开始铸造铁钱，并对境内铁器实行榷管。《通鉴》记百姓因此深受困扰。榷为官府专管，不自行推定具体收购价格、铸币兑换比例或民户损失金额。')

reviews={25:'罢判三司与随后父丧罢政事分开，丁未只确定前者；旧史同日印证。',26:'八月获三百与九月辛卯送俘抵京分开，不能由人数自行认定名单完全相同；伊审征慰劳督战为派遣任务。',27:'县官指官府；设监命令、铜器征收例外期限给价、逾期隐匿处罚和柴荣解释讲话均完整处理。五斤不换算，刑罚不造已执行个案。',28:'司马光史论归柴荣人物评价，只有引用无955年事件，不虚构评论日期。',29:'部署、黄花唐仓战、撤退、弃城降城、任官与庆功分层。王峦同名暂分，俘三千与一千五百余及死俘异说保留；旧纪壬子奏报和癸丑归降与主书记序分别保存。宋传赵玭前史孟知祥时序疑问不导入任官确年。凤州仍未最终攻克。',30:'万岁殿讲话作为责任表态，不当本段已亲征。',31:'李廷珪与伊审征请罪跨闰月十月，宽免承接两人；请和未答不是和约。剑门白帝备守与铁钱铁器榷管分开，不虚构兑换价格。'}
assert not (P/'publication.json').exists()
for n in range(25,32):
 row=ledger[n-1];row.update(event_keys=used.get(n,[]),batch_key=B['batch_key'],status='reviewed',review=reviews[n])
 if n==28:row.update(kind='historian_commentary',fact_claim_keys=commentary_keys)
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=955,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(25,32)],next_paragraph=Q[32]['id'],next_volume=292,next_year=955,supplements=supplements,excluded_non_body=[],coverage='原57—63行连续七段，含六段史事及一段司马光史论；下一段南唐与淮南部署待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(25,32)],source_issues_review='黄花俘虏数、王峦生死、秦州降城与庆功时序并列；王峦同名暂分，赵比异字不自动追加别名，判宫等疑字保留。宋赵玭传孟知祥任官时序可疑，不据疑叙入确年。纸本待核。',plain_language_review='首次逐条核对标题、人物说明、参与角色、事件正文、时间与事实解释为现代白话。诏令条件、讲话观点、史家评论、愿望与实际行动分开；原文保留。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
