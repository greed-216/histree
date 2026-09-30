"""Curate consecutive Tongjian volume 258, year 891 paragraphs 25–34."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 41))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0891-p025-p034', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-258-891'
B['sources'] = [dict(key=source,title='资治通鉴·卷258',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/4d35696319726b523bd624f2370cb2cf7faa6b43/resources/derived/tongjian/258.txt',note='卷258大顺二年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/258.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/258.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
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
alias['郑渥']='王宗渥'

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0891_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·大顺二年（891）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷258大顺二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=891,note=None,quote=None):
    key='event_zztj_258_0891_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_258_0891_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def relation(a,b,t,n,description):
    key=f'relationship_{people[a]}_{people[b]}_{t}'
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['key']==key]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);reused.add(key)
    else:row=dict(key=key,person_a_key=people[a],person_b_key=people[b],relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n)
    return key

event('wang_chongying_zhongshu','王重盈加兼中书令',25,'891年九月条；具体日未载','护国',
      '朝廷加护国节度使王重盈兼中书令。',[('王重盈','加官者')])
event('gu_yanlang_dies_succession','顾彦朗去世，军推顾彦晖知留后',26,'891年九月条；具体日未载','东川',
      '东川节度使顾彦朗去世，军中推其弟顾彦晖知留后。',[('顾彦朗','去世节度使'),('顾彦晖','军推知留后者')],note='军中推知留后不提前写朝廷正式任命。')
relation('顾彦朗','顾彦晖','兄长',26,'《通鉴》称顾彦晖为顾彦朗之弟；顾彦朗是顾彦晖的兄长。')
event('zhang_yun_surrender','宿州张筠投降丁会',27,'891年十月壬午','宿州',
      '宿州刺史张筠投降丁会。',[('张筠','投降刺史'),('丁会','受降将领')],note='与前批八月仅攻克外城分开记录。')
event('wang_xichuan_formal','王建获朝廷任西川节度使',28,'891年十月癸未','永平、西川',
      '朝廷以永平节度使王建为西川节度使。',[('王建','朝廷正式受任者')],note='与八月入成都自称留后以及四月交印分别记录。')
event('yongping_abolished','朝廷废永平军',28,'891年十月甲申','永平',
      '朝廷废永平军。',note='这是节镇建制调整，不写成军队人数归零或全体解散。')
event('wang_governance_assessment','通鉴评王建得西川后的政事与忌杀',28,'得西川后；各行为确年日未载','西川',
      '《通鉴》述王建得西川后留心政事、容纳直言、好施乐士、用人尽才且谦恭俭素，又称多忌好杀，功名诸将多因事被诛。',[('王建','史书评价对象')],year=None,note='政事和性格为概括书评，不抽象造一场未具名诸将处死事件，不将全部评价固定891年。')
event('yang_fugong_accused','杨复恭与杨守信被告谋反',29,'891年十月乙酉前','京师、玉山营',
      '杨复恭住所近玉山营，假子杨守信任玉山军使、屡来探望。有人告杨复恭与守信谋反。',[('杨复恭','被告者'),('杨守信','来省与被告者')],note='或告是指控，不以此判定谋反已独立证实；告者未具名。')
relation('杨复恭','杨守信','假父',29,'《通鉴》此段称杨守信为杨复恭假子；杨复恭是杨守信的假父。')
event('li_shunjie_assault_yang','李顺节李守节攻杨复恭宅未克',29,'891年十月乙酉','安喜门、杨复恭宅',
      '皇帝御安喜门陈兵自卫，命李顺节与李守节率兵攻杨复恭宅。张绾率家众拒战，杨守信引兵助，李顺节等未能攻克。',
      [('李杰','以唐昭宗身份下命督战者'),('杨守立','以李顺节名义攻宅者'),('李守节','攻宅将领'),('杨复恭','被攻者'),('张绾','家众拒战者'),('杨守信','引军助守者')],note='底本安喜门照存，另一电子版本作安喜楼；李守节与李顺节（杨守立）不是同人，不据名字合并。')
event('liu_chongwang_redirects_guards','刘崇望止禁兵掠市，引其东击',29,'891年十月丙戌','含光门、街东',
      '禁兵守含光门待开欲掠两市，刘崇望劝其应到皇帝督战处杀敌立功、勿贪小利，士卒遵从而东；杨守信军望兵遂溃。',
      [('刘崇望','止掠引兵者'),('杨守信','军溃方')],note='想掠两市不写为实际已掠；史书称贼是劝军话语，不额外构造道德结论。')
event('yang_fugong_flees_zhang_killed','杨复恭杨守信奔兴元，权安追斩张绾',29,'891年十月丙戌后条','通化门、兴元',
      '杨守信与杨复恭携族由通化门出逃向兴元，永安都头权安追击，擒张绾并斩之。',
      [('杨守信','出逃者'),('杨复恭','出逃者'),('权安','追擒处斩者'),('张绾','被擒斩者')],note='通化门只是出城经过点，不单写为张绾被斩精确地点；张绾非王建将李绾。')
event('yang_family_resists','杨守亮等兴元举兵拒朝廷',29,'891年十月条；杨复恭至兴元后','兴元、绵州',
      '杨复恭至兴元后，杨守亮、杨守忠、杨守贞及绵州刺史杨守厚同举兵拒朝廷，以讨李顺节为名。',
      [('杨复恭','奔到兴元者'),('杨守亮','举兵者'),('杨守忠','举兵者'),('杨守贞','举兵者'),('杨守厚','举兵者'),('杨守立','以李顺节名义被声称讨伐对象')],note='讨李顺节为举兵名义，不推已发生与其交战；复用主底本杨守忠，前批已列武定记名守思异文。')
relation('杨复恭','杨守厚','假父',29,'《通鉴》明言杨守厚亦为杨复恭假子；杨复恭是杨守厚的假父。')
event('li_defeats_zhen_longwei','李克用龙尾岗破镇兵取临城',30,'891年十月条；具体日未载','龙尾岗、临城、元氏、柏乡',
      '李克用攻击王镕，在龙尾岗大败镇兵，书载斩获万计，攻取临城，再攻元氏、柏乡。',[('李克用','进攻者'),('王镕','镇兵所属主将')],note='斩获万计包括杀获，不全计阵亡；元氏柏乡仅攻不写已取。')
event('li_kuangwei_relief_zhen','李匡威引幽兵救镇，李克用掠还邢州',30,'891年十月条；龙尾岗战后','幽州、邢州',
      '李匡威引幽州兵援救王镕，李克用大掠而还，驻邢州。',[('李匡威','援救者'),('王镕','被援对象'),('李克用','掠还驻军者')],note='援救关系限定本次行动，不转长期同盟；幽州为援军来源，不写战斗在幽州。')
event('guo_zhu_kills_governor','郭铢杀曹州郭词降朱全忠',31,'891年十一月','曹州',
      '曹州都将郭铢杀刺史郭词，投降朱全忠。',[('郭铢','杀刺史及投降者'),('郭词','被杀刺史'),('朱温','以朱全忠名义受降对象')],note='郭铢与郭词不同人，不因同姓推亲属。')
event('zhu_jin_attacks_shan','朱瑾率万余人攻单州',32,'891年十一月条；具体日未载','单州',
      '泰宁节度使朱瑾率万余人攻击单州。',[('朱瑾','进攻者')],note='万余为书载军数，仅攻不记攻克。')
event('liu_zhijun_surrenders','刘知俊率二千人降朱全忠并获任',33,'891年十一月乙丑','徐州、汴',
      '时溥将刘知俊率二千人降朱全忠，《通鉴》称此后时溥军不振；朱全忠以刘知俊为左右开道指挥使。',
      [('刘知俊','率部投降及受任者'),('时溥','失将方'),('朱温','以朱全忠名义受降任将者')],note='徐为军属来源，不据此断投降仪式精确地点；军不振是书中概括，不生成未载的逐场败战。')
claim('person',people['刘知俊'],'biography','刘知俊为沛人，原为时溥麾下徐州骁将。',33,quote='知俊，沛人，徐之骁将也。',note='只据本年所见身份，后续投奔不提前抽录。')
event('liu_honge_surrenders','刘弘鄂因恶孙儒举寿州降朱全忠',34,'891年十一月辛未','寿州',
      '寿州将刘弘鄂厌恶孙儒残暴，举州投降朱全忠。',[('刘弘鄂','举州投降者'),('孙儒','被背离主将'),('朱温','以朱全忠名义受降对象')],note='恶残暴为书载动机，不添加未载个人恩怨。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={25:'加兼中书令不推职任变动。',26:'顾彦朗薨，弟顾彦晖军推知留后，兄长关系依证复用。',27:'十月壬午刺史降，区别前批只克外城。',28:'癸未正式授西川，甲申废永平分事；概括书评确年空。',29:'指控、乙酉攻宅未克、丙戌止掠引军、出逃追斩、兴元举兵分录；李守节与杨守立不同；假父关系依原文。',30:'龙尾岗破军临城取，元氏柏乡只攻；幽兵援镇及掠还邢州分录。',31:'郭铢杀郭词归汴，不推同姓亲属。',32:'朱瑾万余攻单州未载结果。',33:'刘知俊二千归汴及受任，籍贯独引，数量非死亡。',34:'刘弘鄂举寿州降朱全忠，不补未载恩怨。'}
for n in range(25,35):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,35):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=891,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(25,35)],next_paragraph='zztj-v258-y0891-p035',coverage='卷258大顺二年第25—34段连续录入；本年40段尚未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
