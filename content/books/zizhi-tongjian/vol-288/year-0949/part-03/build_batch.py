# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 949 paragraphs 17–22."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,38))
COMMIT='2d42e21ad1bb401f000e13eff449c033474939df'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-288-949-june-july','songshi-263-926-zhangzhao-name']:
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
main_sources = ['tongjian-288-949-june-july']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0949-p017-p022',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-107-hou-zan':'卷107·后赞传·飞龙使','jiuwudaishi-107-guo-yunming':'卷107·郭允明传','jiuwudaishi-125-wang-shouen-luoyang':'卷125·王守恩传·洛阳聚敛与被替换','jiuwudaishi-125-wang-shouen-note':'卷125·王守恩传·《五代史补》注引洛阳易留守','jiuwudaishi-102-july-949':'卷102·隐帝本纪·乾祐二年七月'}
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
lines = (ROOT / 'resources/derived/tongjian/288.txt').read_text().splitlines()
for n in range(17, 23):
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
    labels={'jiuwudaishi-107-hou-zan':'卷107·后赞传·飞龙使','jiuwudaishi-107-guo-yunming':'卷107·郭允明传','jiuwudaishi-125-wang-shouen-luoyang':'卷125·王守恩传·洛阳聚敛与被替换','jiuwudaishi-125-wang-shouen-note':'卷125·王守恩传·《五代史补》注引洛阳易留守','jiuwudaishi-102-july-949':'卷102·隐帝本纪·乾祐二年七月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷288·乾祐二年（949年七月至八月及概述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0949_03_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=949, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='949年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_288_0949_' + code
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
        edge = 'participation_zztj_288_0949_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_288_0949_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘承祐','太后':'李氏（刘知远妻）','唐主':'李璟','张昭':'张昭（五代宋初）','硃元':'舒元','朱元':'舒元','李平':'杨讷','吴越王':'钱弘俶','弘亿':'钱弘亿'})
NEW_ALIASES={'后匡赞':['后赞','後贊','後匡贊'],'郭允明':['窦十','竇十'],'钟谟':['鍾謨'],'李德明':[],'范冲敏':['范沖敏']}
NEW_DESCRIPTIONS={
'后匡赞':'瑕丘人，后汉飞龙使。949年条下与郭允明一起见于刘承祐近臣的记载。《旧五代史》写后赞，官职及朝廷人物背景相合，本批保留这个异名。生卒年尚未录入。',
'郭允明':'太原、河东人，小名窦十。曾在刘知远身边服役，后来担任翰林茶酒使兼鞍辔库使。949年为刘承祐近臣，《通鉴》和《旧五代史》都记其受宠。生卒年尚未录入。',
'钟谟':'会稽人，南唐吏部郎中。949年条下与李德明一起参与国政，史书称两人以辩才聪慧受到李璟宠信。与后文同名外交官的进一步经历按年代续录，生卒年尚未录入。',
'李德明':'南唐尚书员外郎。949年条下与钟谟一起参与国政，史书记两人受李璟宠信，但不是魏岑的同党。生卒年尚未录入。',
'范冲敏':'南唐户部员外郎。949年劝王建封上书批评执政者、请求任用正直之人，随后被李璟处死。生年与此前经历未载。'}
NEW_DEATH_YEARS={'范冲敏':949}
hou='jiuwudaishi-107-hou-zan';yun='jiuwudaishi-107-guo-yunming';zhang='songshi-263-926-zhangzhao-name';wang='jiuwudaishi-125-wang-shouen-luoyang';wn='jiuwudaishi-125-wang-shouen-note';july='jiuwudaishi-102-july-949'
add('liu_chengyou_close_courtiers','史书记刘承祐亲近后匡赞、郭允明，与他们猜谜说粗俗话',17,'飞龙使瑕丘后匡赞、','为廋辞、丑语，',[('刘承祐','亲近后匡赞、郭允明，与他们猜谜说粗俗话'),('后匡赞','以飞龙使身份受到刘承祐宠信'),('郭允明','以茶酒使身份受到刘承祐宠信')],year=None,when='刘承祐在位期间的概述，949年七月条下记载，具体起止未载',place='后汉宫廷',note='谄媚得幸是史书评价，廋辞解释为谜语；三叛既平为概括语，不能据此把凤翔战事结束时间定在七月。')
claim('person',people['刘承祐'],'description','《资治通鉴》认为刘承祐此后日益骄纵，与身边近臣亲昵。',17,'三叛既平，帝浸骄纵，与左右狎昵。','这是史家对一段时期的概括评价，不构造某一天发生的性格变化。')
claim('person',people['后匡赞'],'aliases','《旧五代史》将飞龙使后匡赞写作后赞。',17,'後贊，爲飛龍使。','按同一朝廷、官职及近臣人物背景识别；旧史底本後贊原字保留，不解释为方向词。',source=hou)
claim('person',people['郭允明'],'aliases','郭允明的小名是窦十。',17,'郭允明者，小名竇十，河東人也。','按郭允明传开头明示小名，不与窦姓人物合并。',source=yun)
claim('person',people['郭允明'],'description','《旧五代史》记郭允明累迁至翰林茶酒使兼鞍辔库使，刘承祐即位后尤受亲近。',17,'累遷至翰林茶酒使兼鞍轡庫使。隱帝嗣位，尤見親狎，','补充官职与受宠背景，后文乾祐末行为不提前录在949年。',source=yun)
add('li_dowager_warns_son','李太后多次告诫刘承祐，刘承祐不放在心上',17,'太后屡戒之，','帝不以为意。',[('太后','多次告诫刘承祐'),('刘承祐','没有重视太后的告诫')],year=None,when='刘承祐与近臣亲昵期间的概述，具体年月未载',place='后汉宫廷',note='太后为刘知远妻李氏，复用后汉主体，不与后晋李太后合并；未补写告诫原话。')
add('zhang_zhao_advises_confucian_learning','张昭建议刘承祐亲近儒臣、学习经典，未被采纳',17,'癸亥，','不听。',[('张昭','以太常卿身份建议亲近儒臣、学习经典'),('刘承祐','没有采纳张昭的建议')],when='949年七月癸亥',place='后汉朝廷',note='癸亥承接上段七月壬戌；上言是建议，不写成刘承祐已讲习经典。')
claim('person',people['张昭（五代宋初）'],'aliases','张昭本名张昭远，为避后汉高祖刘知远的名讳改称张昭。',17,'昭，即昭远，避高祖讳改之。','高祖指后汉刘知远，避免误指后晋或其他高祖。')
claim('person',people['张昭（五代宋初）'],'aliases','《宋史》也记张昭本名昭远，避汉祖名讳而只称昭。',17,'張昭，字潛夫，本名昭遠，避漢祖諱，止稱昭。','独立出处核对姓名与避讳对象，沿用已发布的宋史固定快照。',source=zhang,relation='corroborates')
add('guo_congyi_honor_chancellor','后汉加郭从义同平章事',18,'戊辰，','郭从义同平章事，',[('郭从义','以永兴节度使身份获加同平章事')],when='949年七月戊辰',place='后汉朝廷、永兴',note='加衔不自行解释为进入中书实际主持政务；本句未载迁华州，补证另记。')
sup('guo_congyi_honor_chancellor',18,july,'戊辰，永興軍節度使兼兵馬都部署郭從義加同平章事，徙華州節度使。','《旧五代史》同记郭从义加同平章事，并记他迁任华州节度使。','主书本句只记加衔，迁任华州作为补充，未写成赵思绾实际已经到华州。',relation='adds')
add('hu_yanke_moves_huguo','扈彦珂由镇国节度使改任护国节度使',18,'徙镇国节度使','为护国节度使，',[('扈彦珂','由镇国节度使改任护国节度使')],when='949年七月戊辰',place='镇国军、护国军')
add('liu_ci_appointed_zhenguo','刘词获任镇国节度使',18,'以河中行营',None,[('刘词','由河中行营马步都虞候获任镇国节度使')],when='949年七月戊辰',place='河中行营、镇国军')
add('li_jing_reappoints_wei_cen','李璟重新任用魏岑',19,'唐主复进用魏岑。','唐主复进用魏岑。',[('李璟','重新任用魏岑'),('魏岑','重新受到李璟任用')],when='949年七月条下，具体日未载',place='南唐朝廷',note='进用没有列具体新官职，不擅自补任宰相。')
add('zhong_li_participate_government','钟谟与李德明受李璟宠信，开始参与国政',19,'吏部郎中会稽钟谟、','参预国政。',[('钟谟','以吏部郎中身份受到宠信、参与国政'),('李德明','以尚书员外郎身份受到宠信、参与国政'),('李璟','宠信钟谟与李德明，让他们参与国政')],when='949年七月条下，具体日未载',place='南唐朝廷',note='始以辩慧得幸为史书记载的受宠原因；未载三人正式会议日期。')
claim('person',people['钟谟'],'description','《资治通鉴》评价钟谟与李德明倚仗恩宠、轻率急躁，并记他们虽不是魏岑的同党，仍为国人厌恶。',19,'二人皆恃恩轻躁，虽不与岑为党，而国人皆恶之。','二人承接钟谟、李德明；史家概括国人态度，不当作有统计依据的全民意见，不建立与魏岑的同党关系。')
claim('person',people['李德明'],'description','《资治通鉴》评价李德明与钟谟倚仗恩宠、轻率急躁，并明说他们不是魏岑的同党。',19,'二人皆恃恩轻躁，虽不与岑为党，而国人皆恶之。','评价与党属明文分开，不根据共同受宠推定盟友或从属关系。')
add('fan_guides_wang_petition','范冲敏让王建封上书，批评执政者并请求任用正直之人',19,'户部员外郎范冲敏，','请进用正人。',[('范冲敏','让王建封上书批评执政者、请求任用正直之人'),('王建封','以天威都虞候身份上书批评执政者')],when='949年七月条下，具体日未载',place='南唐朝廷',note='历诋为史书对批评的用语，正人是上书诉求；未列被批评者完整名单，不直接列宋齐丘等人。')
add('li_jing_exiles_wang_jianfeng','李璟认为王建封不应干预国政，将他流放池州',19,'唐主谓建封','流建封于池州，',[('李璟','认为掌兵的王建封不应干预国政，命其流放'),('王建封','被下令流放池州')],when='949年七月条下，具体日未载',place='南唐朝廷至池州',note='武臣不应干预国政是李璟的意见，不作为本站普遍制度结论；被流放不等于已到池州。')
add('wang_jianfeng_killed_before_arrival','王建封在到达池州以前被杀',19,'唐主谓建封','未至，杀之，',[('王建封','在流放途中、到达池州前被杀'),('李璟','在流放王建封后将他杀死')],when='949年七月条下，具体日未载',place='前往池州途中，具体地点未载',note='杀之承接李璟，未载具体行刑者，不补行刑方式。')
claim('person',people['王建封'],'death_year','王建封于949年被流放池州，未到目的地就被杀。',19,span(19,'唐主谓建封','未至，杀之，'),'沿用南唐将领王建封主体，补充死亡事实，不覆盖旧批档案字段。')
add('fan_chongmin_executed','范冲敏被处死',19,'唐主谓建封','冲敏弃市。',[('范冲敏','在王建封上书后被处死'),('李璟','在处置王建封后又将范冲敏处死')],when='949年七月条下，具体日未载',place='南唐，具体行刑地点未载',note='弃市表示处死，未据此指定某城或具体行刑方式。')
add('li_jing_promotes_shu_yuan','李璟得知河中城破，任命舒元为驾部员外郎',19,'唐主闻河中破，','以硃元为驾部员外郎，',[('李璟','得知河中城破后任命舒元'),('硃元','获任驾部员外郎')],when='949年七月河中城破消息传到南唐之后，具体日未载',place='南唐朝廷',note='硃元沿用既有舒元主体；传到南唐的日期未知，不强定为河中壬戌城破当天。')
add('li_jing_promotes_yang_ne','李璟任命杨讷为尚书员外郎',19,'唐主闻河中破，',None,[('李璟','任命文理院待诏杨讷为尚书员外郎'),('李平','由文理院待诏获任尚书员外郎')],when='949年七月河中城破消息传到南唐之后，具体日未载',place='南唐朝廷',note='李平沿用此前已核的杨讷别名；不因改名另建人物。')
add('qian_hongyi_administers_mingzhou','钱弘俶命钱弘亿管理明州',20,'吴越王',None,[('钱弘俶','命丞相钱弘亿管理明州'),('钱弘亿','以丞相身份受命管理明州')],when='949年七月条下，具体日未载',place='吴越、明州',note='判明州解释为管理明州，不自行改写成节度使；没有明说是惩罚或谋叛告发的必然结果。')
add('wang_shouen_extorts_funeral_tax','王守恩要求丧车缴钱后才能出洛阳城',21,'西京留守、','不得出城，',[('王守恩','任西京留守时要求丧车缴钱后才能出城')],year=None,when='王守恩任西京留守期间、949年八月被替换以前，具体起止未载',place='洛阳',note='性贪鄙为史家评价；此处具体收费办法未注明何日开始，不强定为949年七月。')
add('wang_shouen_taxes_poor_allows_theft','王守恩向清理厕所者和乞丐收钱，纵容部下夺人财物',21,'下至抒厕、','盗人财。',[('王守恩','向贫困者收取钱物，并纵容部下盗取财物')],year=None,when='王守恩任西京留守期间、949年八月被替换以前，具体起止未载',place='洛阳',note='抒厕按清理厕所理解；课率是摊派钱物，未载具体税率与总收入。')
sup('wang_shouen_taxes_poor_allows_theft',21,wang,'守恩性貪鄙，委任群小，以掊斂為務，雖病廢殘癃者，亦不免其稅率，人甚苦之。','《旧五代史》还记王守恩委任小人聚敛，病残者也无法免除摊派，百姓深受其苦。','同一任内聚敛概述，不把病残者与主书的清厕者当作同一群体，不补税率数字。',relation='adds')
add('wang_shouen_gains_silver_wedding','王守恩与伶人参加富家婚礼，得到数铤银',21,'有富室娶妇，',None,[('王守恩','带数名伶人参加富家婚礼，得到银数铤后返回')],year=None,when='王守恩任西京留守期间、949年八月被替换以前，具体婚礼日期未载',place='洛阳',note='原文未列婚家姓名、银重量或授受方式，不擅写抢劫或换算价值。')
sup('wang_shouen_gains_silver_wedding',21,wang,'洛都嘗有豪士，為二姓之會，守恩乃與伶人數輩夜造，自為賀客，因獲白金數笏而退。','《旧五代史》也记王守恩与伶人夜访婚礼，以贺客身份获得银后离开。','二姓之会为婚礼，白金在此为银；笏与铤的记载不同，不折算重量。')
add('guo_passes_luoyang_refuses_wang','郭威返回途中经过洛阳，因王守恩乘轿出迎而拒见',22,'八月，','辞以浴，不见，',[('郭威','从河中返回，认为王守恩乘轿出迎怠慢自己，借口沐浴拒见'),('王守恩','乘轿迎接郭威，被郭威拒见')],when='949年八月甲申',place='洛阳',note='乘肩舆是出迎方式，怠慢为郭威判断，不当作已证明的王守恩动机。')
sup('guo_passes_luoyang_refuses_wang',22,wn,'時王守恩為留守，以使相自專，乘檐子迎高祖於郊外，高祖遙見大怒，且疾驅入於公館。','《旧五代史》附引《五代史补》也记王守恩乘轿出迎，郭威见后大怒。','高祖为后周郭威；附引属于另书引文，不能当作旧史正文独立确证。')
add('guo_orders_bai_replace_wang','郭威用枢密使文书命白文珂接替王守恩',22,'即以头子命','文珂不敢违。',[('郭威','以枢密使文书命白文珂接任西京留守'),('白文珂','不敢违命，接替王守恩'),('王守恩','被郭威命令撤换')],when='949年八月甲申',place='洛阳',note='头子指枢密使文书，此时郭威尚未称帝；与后汉朝廷随后的正式任命分开。')
sup('guo_orders_bai_replace_wang',22,wang,'太祖回自河中，駐軍於洛陽，詔以白文珂代之，守恩甚懼。','《旧五代史》正文将白文珂接替王守恩写作诏令。','《通鉴》细记郭威以头子先行撤换、朝廷后来任命；诏与枢密文书的叙述差别并列，不据太祖称谓认为郭威当时已经称帝。',relation='conflicts')
add('wang_family_forced_from_office','王守恩得知白文珂已就任，回去发现家属被逐出府署',22,'守恩犹坐客次，','在通衢矣。',[('王守恩','听到白文珂已就任后赶回，发现家属被逐出府署'),('白文珂','已在府署处理留守事务')],when='949年八月甲申',place='洛阳留守府署及街道',note='数百家属为史书人数概述，未据此补造逐人的身份；家属在街道不等于都已死亡或被流放。')
sup('wang_family_forced_from_office',22,wn,'留恩大驚，奔馬而歸，但見家屬數百口皆被逐於通衢中，百姓莫不聚觀。','《旧五代史》附引《五代史补》也记王守恩赶回后见数百家属被逐到街上。','留恩为选定底本原字，按传主和前后文对应王守恩；原字保留，不另建留恩人物。')
add('han_formally_appoints_bai_luoyang','后汉朝廷未追问撤换过程，任命白文珂为西京留守',22,'朝廷不之问，',None,[('刘承祐','在位朝廷未追问撤换过程，任命白文珂'),('白文珂','获加兼侍中，并正式任西京留守')],when='949年八月甲申条下，具体朝廷下令日未载',place='后汉朝廷、洛阳',note='未追问是史书记载的朝廷反应，不补刘承祐亲口认可的话；与郭威前一命令分开。')
sup('han_formally_appoints_bai_luoyang',22,july,'甲申，以陜州節度使、充河中一行兵馬都部署白文珂為西京留守，加兼侍中；','《旧五代史》本纪记甲申任白文珂西京留守、加兼侍中。','该条列在七月段落内，主书记八月甲申；保留编月差异，不静默将两书月份改成一致。',relation='conflicts',field='time_original')
reviews={17:'帝与太后明确为后汉刘承祐、李氏；史家评价与具体建议分开。三叛既平不用于推定凤翔七月已经平定；张昭避刘知远讳据宋史核名，后赞与郭允明别名、职务据旧史核对。',18:'加衔与迁任区分，扈彦珂与刘词分别记职务；旧史另记郭从义迁华州，保留补证。',19:'钟谟、李德明参与国政与史家评价分开，不与魏岑建同党关系。范冲敏教王建封上书、流放未到而被杀、范被处死分开。朱元复用舒元、李平复用杨讷，听到河中城破不定为城破当日。',20:'判明州解释为管理明州，未直接指为惩罚，也不补新官职。',21:'西京留守任内概述用未知年，不把一切收费行为限定七月；清厕、乞丐与旧史病残摊派并列，婚礼得银未擅定重量和强取方式。',22:'郭威尚为枢密使，头子文书与朝廷正式任命分开。怠慢为郭威判断，家属被逐不写死亡；旧史正文诏字、本纪甲申编月与主书详略差别保留，注引不冒充独立确证。'}
assert not (P/'publication.json').exists()
for n in range(17,23):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=949,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,23)],next_paragraph=Q[23]['id'],next_volume=288,next_year=949,supplements=supplements,excluded_non_body=[],coverage='卷288原95—100行连续六段，949年累计首22/37正文，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,23)],source_issues_review='三叛既平概括与后文凤翔时序有出入，不推定提前结束。旧史本纪甲申在七月段内、主书八月甲申，保留编月差异；旧传正文诏令与主书头子先行撤换详略并列。旧史注引留恩原字保留按传主解释；纸本异文待核。南唐本段逐项查过新史南唐世家及宋史南唐列传，所检索钟谟、李德明条多属后年外交，不提前拉入949年作为确证。',plain_language_review='首次逐条核对标题、人物介绍、正文、参与角色、时间地点解释与事实说明。明确姓名主语，区分史家评价、说话者判断、建议与实际处置；概述年月未知用null，不补官职、税率、银重或死亡名单。原文字形保留，复用主体不改旧档案，不另作固定发布后文案重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
