"""Curate consecutive Tongjian volume 259, year 892 paragraphs 25–30."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 47))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0892-p025-p030', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-892'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259景福元年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/259.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/259.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'王熔':'王镕','国弘信':'罗弘信','硃友裕':'朱友裕','赫连鐸':'赫连铎','硃崇节':'朱崇节','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, {source}
alias.update({'郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0892_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·景福元年（892）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259景福元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=892,note=None,quote=None):
    key='event_zztj_259_0892_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0892_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

# Consecutive paragraphs: return to Yangzhou, civilian harm, and recruitment policy.
event('yang_returns_yangzhou','杨行密六月启程、七月至广陵',25,'892年六月丁酉启程；七月丙辰至广陵','扬州、广陵',
      '杨行密六月丁酉率众归扬州，七月丙辰到广陵。',[('杨行密','率众返回者')],note='扬州与广陵为本段同一目的地表述，启程与抵达跨月，不记为两次到达。')
event('yang_petitions_tian_an','杨行密表田頵守宣州、安仁义守润州',25,'892年七月丙辰至广陵后条','宣州、润州',
      '杨行密表请田頵守宣州、安仁义守润州。',[('杨行密','上表者'),('田頵','被表守宣州者'),('安仁义','被表守润州者')],note='上表与第32段八月朝廷授职分别录入，不把两者合为同日任命。')
event('yangzhou_war_devastation','扬州富庶与江淮兵火后的对照',26,'先是富庶；历次兵火后；确年未载','扬州、江淮',
      '《通鉴》追述扬州曾富庶甲天下，时人称扬一、益二；经历秦、毕、孙、杨兵火后，书中形容江淮东西千里扫地尽矣。',year=None,note='概括多年战乱，不绑定892单次战事；扫地尽矣为史书形容，不转为人口归零或现代面积统计。益为富庶比较对象，不作战场地点。')
event('pengzhou_civilian_raids','王建围彭州时诸寨俘掠居民',27,'围彭州久不下期间；具体日未载','彭州、山谷',
      '王建围彭州久不下，居民逃入山谷。各寨每天外出俘掠，称淘虏；都将先挑选俘获中较好者，其余由士卒分取，成为常例。',[('王建','围军主将')],note='记录围军侵害居民；原文未说王建亲自参与每次俘掠，不补具体都将姓名。')
event('wang_xiancheng_remonstrates','王先成劝王宗侃停止俘掠、招安百姓',28,'围彭州累月期间；具体日未载','彭州、北寨',
      '新津军士王先成本为书生，因世乱为兵。他向王宗侃陈述围军劫财、驱畜、将妇女老弱分作奴婢，致亲属流离、山民饥困；指出久无招安将使民心转向杨晟，又以假设敌军乘寨空袭击说明每日淘虏的军防风险。王宗侃受触动，问如何应对。',
      [('王先成','陈说民害与军防风险者'),('王宗侃','听议求策者'),('杨晟','议论所指被围者')],note='伏兵千人、弩手砲手各百、役卒五百均是王先成假设方案，未发生，不建实际袭寨事件。陈田及彭州旧属为讲话追叙，非892新增战事。')
claim('person',people['王先成'],'biography','王先成，新津人，本为书生，因世乱成为军士。',28,quote='有军士王先成者，新津人，本书生也，世乱，为兵',note='仅记录明示籍贯与身份经历，不推生卒、具体入伍年。')
policy=event('seven_policies_submitted_adopted','王先成草招安七策，王建悉数实行',29,'围彭州期间；七策呈报并获采纳','彭州、招安寨',
      '王先成经王宗侃命令草拟七条招安措施呈王建：招安山民；禁止淘虏并划樵牧范围；置招安寨派兵巡卫；委王宗侃统一招安；索还俘获居民使家属团聚；置九陇行县以王丕摄令、由居民招亲；使百姓返田卖沤麻以得资粮。王建大喜，立即按所申全部实行。',
      [('王先成','草拟七策者'),('王宗侃','命草呈报及拟总领招安者'),('王建','采纳实施者')],note='末句即行之悉如所申支持实际采纳实行；七项具体细节见阶段，区别第30段效果。')
steps=[
 ('招安山民','招安逃入山中的百姓。'),
 ('禁止淘虏、限定樵牧','禁止各寨军士及子弟擅自外出淘虏，在诸寨旁七里内标界，准许樵牧，越界者斩。'),
 ('设寨巡卫','置招安寨容数千百姓，选谨慎干练将校为招安将，带三十人昼夜持兵巡卫。'),
 ('统一招安','招安须委一人总领，避免各寨自行派军士使百姓惊疑；请将招安事务专交王宗侃。'),
 ('归还俘民、团聚亲属','命四寨及府中诸营索出俘获男女老幼，让父子兄弟夫妇相认相从，登记人数护送招安寨；府营先送回者量给资粮，私匿者斩。'),
 ('设行县、居民招亲','在招安寨置九陇行县，以前南郑令王丕摄县令，设曹局抚理；选居民壮子弟给帖入山招亲，使其知侵掠已禁、被俘者获安堵。'),
 ('卖麻资粮、恢复生业','彭州宜麻，百姓逃山前多有沤藏之麻；令县令晓谕各归田里，取麻出售以得资粮，逐渐复业。')]
B['events'][-1]['phases']=[dict(title=t,description=d) for t,d in steps]
for i,(t,d) in enumerate(steps):
    claim('event',policy,f'phases.{i}.description',d,29,note=f'按七策第{i+1}条及末句悉如所申记录；七里、三十人、数千均书载，不作现代测量。')
event('wang_pi_jiulong_magistrate','九陇行县设立，王丕摄县令',29,'七策获王建采纳时；具体日未载','彭州、九陇行县',
      '招安七策要求在招安寨设九陇行县，以前南郑令王丕摄县令，设曹局抚理百姓；王建悉按所申实行。',[('王丕','摄县令者'),('王先成','草拟此策者'),('王建','批准实行者')],note='摄为代理，前南郑令是既往职务；未补王丕实际到任日。')
event('pengzhou_recovery_after_notice','招安榜帖后山民出寨、卖麻复业',30,'明日榜帖至；三日山民出；月馀寨空','彭州、招安寨、村落',
      '招安榜帖次日到，军中不敢犯禁。三日山民竞赴招安寨，容纳不足便扩建，渐成市井并出售麻。居民见村落无抄暴之患，陆续辞县令返回旧业；月余招安寨皆空。',year=None,note='相对日期沿用原文，未获具体施策日，不换算公历或强定各阶段年界；寨空表示居民复业离寨，非死亡或逃亡。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={25:'六月启程七月到；表请与八月授职分开。',26:'先是及多年兵火总述年空；扫地为书载形容。',27:'如实录围军俘掠，未把每次行为直接归王建本人。',28:'劝说及身份有据；袭寨兵数为假设，不作发生。',29:'七策逐项保留并依悉如所申判实施；行县代理职独立索引。',30:'榜到次日三日月余为相对时间；寨空因居民复业，年份空。'}
for n in range(25,31):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,31):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=892,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(25,31)],next_paragraph='zztj-v259-y0892-p031',coverage='卷259景福元年第25—30段连续录入；本年46段尚未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})

def relation(a,b,t,n,description,quote=None):
    ka,kb=people[a],people[b]
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==ka and r['person_b_key']==kb and r['relation_type']==t]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);key=row['key'];reused.add(key)
    else:
        key=f'relationship_{ka}_{kb}_{t}';row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key
