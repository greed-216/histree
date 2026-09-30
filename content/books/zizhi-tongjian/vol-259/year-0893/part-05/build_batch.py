"""Curate consecutive Tongjian volume 259, year 893 paragraphs 30–38."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 39))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0893-p030-p038', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-893'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259景福二年条；书、卷、年、段落及行号见批次账本。')]
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
alias.update({'王超':'王超（邠岐判官）','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0893_05_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·景福二年（893）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259景福二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=893,note=None,quote=None):
    key='event_zztj_259_0893_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0893_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def relation(a,b,t,n,description,quote=None):
    ka,kb=people[a],people[b]
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==ka and r['person_b_key']==kb and r['relation_type']==t]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);key=row['key'];reused.add(key)
    else:
        key=f'relationship_{ka}_{kb}_{t}';row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key

event('li_sizhou_escorts_xu','李嗣周三万禁军送徐彦若，屯兴平',30,'893年九月乙亥','兴平、凤翔',
      '李嗣周率三万禁军送徐彦若赴凤翔节度使之任，军队驻兴平。李茂贞、王行瑜合近六万军屯盩厔拒之。',[('李嗣周','以覃王嗣周名领禁军者'),('徐彦若','被护送赴任者'),('李茂贞','合兵拒军者'),('王行瑜','合兵拒军者')],note='三万近六万为书载，徐未抵凤翔，不記到任；盩厔保留旧地名，不核现代坐标。')
event('imperial_army_flees_xingping','李茂贞王行瑜逼兴平，禁军溃、进三桥',30,'893年九月壬午','兴平、三桥、京师',
      '《通鉴》述禁军皆新募市井少年、邠岐军为久战边兵。壬午李茂贞等逼兴平，禁军望风溃逃，邠岐军乘胜攻三桥，京师震动，士民逃散，市人守阙请诛最先议战者。',[('李茂贞','进逼乘胜者'),('王行瑜','同军进逼者'),('李嗣周','禁军所属主帅')],note='望风逃溃不补已进行正面大战或具体伤亡；首议用兵者为市人指向，非本项目对罪责判断。')
event('cui_blames_du_li_requests_killing','崔昭纬密书归责杜让能，李茂贞表请诛',30,'893年九月；甲申李陈临皋表请','京师、临皋驿',
      '崔昭纬嫉害杜让能，密信李茂贞称用兵不是皇帝意思而全由杜。甲申李茂贞陈兵临皋驿，上表列杜让能罪，请杀之。',[('崔昭纬','密书归责者'),('杜让能','被归罪者'),('李茂贞','陈兵表请诛者')],note='崔信说辞与第25段皇帝决战记载并存，不转为杜独自主战的事实。')
event('du_demoted_wuzhou_three_exile_orders','杜让能请自任罪，贬梧州并命流三宦官',30,'893年九月甲申','京师；梧州、儋州、崖州、欢州（所命贬流地）',
      '杜让能请求以自己解难，昭宗流泪诀别，贬其为梧州刺史，制词称其弃善谋而构藩镇衅。又命西门君遂流儋州、李周潼流崖州、段诩流欢州。',[('杜让能','请解难被贬者'),('李杰','以唐昭宗身份下令者'),('西门君遂','被命流者'),('李周潼','被命流者'),('段诩','被命流者')],note='诏辞为罪责说法，不当独立确证；流是命令，未记已抵流所，翌日处死亦不推从海南返京。')
event('three_eunuchs_executed_du_redemoted','昭宗安福门斩三人，再贬杜让能雷州',30,'893年九月乙酉','京师、安福门；雷州（所命贬地）',
      '昭宗到安福门，斩西门君遂、李周潼、段诩，再贬杜让能为雷州司户。派使向李茂贞称惑帝举兵的是这三人，不是杜之罪。',[('李杰','以唐昭宗身份处死贬官遣使者'),('西门君遂','被斩者'),('李周潼','被斩者'),('段诩','被斩者'),('杜让能','再被贬者'),('李茂贞','所遣使告知对象')],note='三人惑帝为遣使说辞，区别第25段主战记载；杜未此时死亡，也未记已经抵雷州。')
event('luo_liu_guard_lieutenants','骆全瓘刘景宣授左右军中尉',30,'乙酉条后；893年九月，具体日未载','京师',
      '朝廷任内侍骆全瓘、刘景宣为左右军中尉。',[('骆全瓘','受任者'),('刘景宣','受任者')],note='左右与人名顺序沿原文，不补任命时具体军情。')
event('wei_cui_chancellors','韦昭度、崔胤授同平章事',31,'893年九月壬辰','京师',
      '朝廷以东都留守韦昭度为司徒、门下侍郎、同平章事，以御史中丞崔胤为户部侍郎、同平章事。',[('韦昭度','受任者'),('崔胤','受任者')],note='东都为韦原职所辖，未推当天任命礼在东都。')
person('崔慎由',31,'崔胤之父')
person('崔安潜',31,'崔胤季父，批评其败家')
relation('崔慎由','崔胤','父亲',31,'《通鉴》称崔胤为慎由之子；崔慎由是崔胤的父亲。',quote='胤，慎由之子也')
relation('崔安潜','崔胤','季父',31,'《通鉴》称安潜为崔胤季父；崔安潜是崔胤的季父，保留具体叔辈称谓。',quote='季父安潜谓所亲曰')
claim('person',people['崔胤'],'biography','《通鉴》评崔胤外宽弘内巧险，与崔昭纬深结而得相；其小字缁郎。',31,note='性情及入相原因归于史书，小字据原文；不推终身同盟或具体首次结交时间。')
next(p for p in B['people'] if p['key']==people['崔胤'])['aliases']=['缁郎']
claim('person',people['崔胤'],'aliases','缁郎是崔胤小字。',31,quote='缁郎，胤小字也。',note='小字不是另一人物。')
event('cui_anqian_criticizes_cui_yin','崔安潜忧崔胤将毁门户',31,'崔胤授相条所附；言说具体年日未载','',
      '崔安潜对亲近者说，父兄刻苦建立家门，终将被缁郎崔胤败坏。',[('崔安潜','言说者'),('崔胤','被批评者')],year=None,note='为长辈忧虑预言，不把家门已毁当发生事实。')
event('li_maozhen_insists_du_death','李茂贞不解兵，崔昭纬挤杜让能',32,'九月贬杜后至冬十月之前条','临皋、京师',
      '李茂贞不撤兵，要求杀杜让能才回镇，崔昭纬继续协助排挤杜。',[('李茂贞','勒兵请诛者'),('崔昭纬','协助挤杜者'),('杜让能','受迫被请诛者')],note='请诛与实际赐死分开，不推李已返凤翔。')
event('du_rangneng_honghui_ordered_suicide','杜让能杜弘徽获赐自尽',32,'893年冬十月；具体日未载','',
      '朝廷赐杜让能及其弟户部侍郎杜弘徽自尽。',[('杜让能','获赐自尽者'),('杜弘徽','获赐自尽者'),('李杰','以唐昭宗身份朝廷发令者')],note='不补具体死亡地点、方式或同日时刻；自尽命令依原文。')
relation('杜让能','杜弘徽','兄长',32,'原文称弘徽为杜让能之弟；杜让能是杜弘徽的兄长。',quote='赐让能及其弟户部侍郎弘徽自尽')
event('court_proclamation_against_du','朝廷诏称杜让能枉法卖官聚敛',32,'赐自尽后条；具体日未载','',
      '朝廷再诏告中外，称杜让能举枉错直、爱憎徇一时、卖官鬻狱、聚敛巨万。',[('杜让能','诏中被指控者'),('李杰','以唐昭宗身份朝廷宣诏者')],note='诏书罪名按指控记录，不当项目已核实的贪腐事实；巨万不换现代金额。')
event('cui_chan_wang_chao_pressure_court','邠岐判官崔鋋王超助二镇干预朝廷总述',32,'自是；后续各次确年日未载','邠、岐、朝廷',
      '《通鉴》述此后朝廷动息都禀邠岐，南北司往往依附两镇求恩。两镇判官崔鋋、王超受不满者诉告，教李茂贞、王行瑜上章干预，朝廷稍不从便言辞不逊。',[('崔鋋','二镇判官助干预者'),('王超（邠岐判官）','二镇判官助干预者'),('李茂贞','据诉上章者'),('王行瑜','据诉上章者')],year=None,note='长期现象总述，不造893一条具名诉案；王超按所属暂辨，崔鋋与神策都头李鋋不同。')
next(p for p in B['people'] if p['key']==people['王超（邠岐判官）'])['aliases']=['王超']
event('li_maozhen_restored_fengxiang','李茂贞复授凤翔兼山南，徐彦若御史大夫',32,'893年冬十月条；具体日未载','凤翔、山南西道、兴元等十五州',
      '朝廷再以李茂贞为凤翔节度使兼山南西道节度使、守中书令；书述他由此尽有凤翔、兴元、洋、陇秦等十五州之地。徐彦若任御史大夫。',[('李茂贞','复兼凤翔山南者'),('徐彦若','改授御史大夫者')],note='十五州总数依书，不补全未列州名、国界或坐标；兼镇本次获授，区别年首请求未获。')
event('wang_chao_fujian_observer','王潮授福建观察使',33,'893年十月戊戌','福建、泉州',
      '朝廷以泉州刺史王潮为福建观察使。',[('王潮','受任者')],note='区别五月入福州自称留后，不写此前已正式授节度。')
event('ni_zhang_flees_li_shenfu_shuzhou','倪章弃舒州，杨行密以李神福为刺史',34,'893年十月条；具体日未载','舒州',
      '舒州刺史倪章弃城逃走，杨行密以李神福为舒州刺史。',[('倪章','弃城者'),('杨行密','任命者'),('李神福','受任者')],note='不补倪目的地、死亡或李确切到任日。')
event('wang_xingyu_requests_shangshu_denied','王行瑜求尚书令，韦昭度密谏',35,'893年十一月之前条；具体日未载','朝廷、邠宁',
      '王行瑜求任尚书令，韦昭度密奏称太宗以此职执政后登大位，此后不授人臣，仅郭子仪以大功受授仍终身避让，王行瑜不可轻议。',[('王行瑜','求职者'),('韦昭度','密谏者')],note='前朝事为韦奏论据，不建893太宗郭子仪事件；未记给王授尚书令。')
event('wang_xingyu_taishi_shangfu','王行瑜授太师、号尚父、赐铁券',35,'893年十一月','邠宁、朝廷',
      '朝廷授王行瑜太师，赐号尚父并赐铁券。',[('王行瑜','受授者')],note='尚父为尊号，不创建皇帝生父养父关系；铁券具体条款未载。')
event('zhu_requests_salt_iron_bian_refused','朱全忠请徙盐铁汴州，朝廷诏谕',36,'893年十二月','汴州、朝廷',
      '朱全忠请求把盐铁事务移至汴州方便供军。崔昭纬担忧朱新破徐郓而兵力倍增，若再掌盐铁便难控制，朝廷遂诏开谕。',[('朱温','以朱全忠名义请移者'),('崔昭纬','顾虑者')],note='新破徐郓是崔判断说辞，郓未据此新增893攻陷事件；不可复制为难控制旧义，不作现代复制语义；未记移盐铁已实行。')
event('ge_attacks_qizhou_zhu_relief','葛从周攻齐州，朱瑄朱瑾救朱威',37,'893年十二月条；具体日未载','齐州',
      '汴将葛从周攻齐州刺史朱威，朱瑄、朱瑾率兵来救。',[('葛从周','攻军将领'),('朱威','被攻刺史'),('朱瑄','率援者'),('朱瑾','率援者')],note='朱威按硃威字形展开；本段无胜败，不提前写城破。')
# Paragraph 38 explicitly summarizes a previously archived episode.
person('周岳',38,'此前据潭州、后被邓雷击斩者');person('闵勖',38,'此前死亡被邓处讷思报仇者')
old=json.loads((ROOT/'content/books/zizhi-tongjian/vol-256/year-0886/part-03/content-batch.json').read_text())
old_event=next(e for e in old['events'] if e['key']=='event_zztj_256_0886_tanzhou_battle')
B['events'].append(dict(old_event,status='draft'));reused.add(old_event['key']);used.setdefault(38,[]).append(old_event['key'])
claim('event',old_event['key'],'description','本段追述周岳杀闵勖并据潭州，接续886年潭州战事。',38,quote='初，武安节度使周岳杀闵勖，据潭州',note='本段结果归周岳概述；886详细条记黄皓杀闵后又被周岳杀。两段各自引用，不将周岳改为亲手行杀或重复建893闵死亡。')
event('deng_chunu_vows_revenge','邓处讷闻闵勖死，誓报仇练兵',38,'初；此前闻闵死后，训练八年；具体起讫未载','邵州',
      '邵州刺史邓处讷听说闵勖被杀而哭，向来吊将领说同受闵恩、欲以一州力报仇，众赞同，于是训练士卒，书载八年。',[('邓处讷','誓报仇练兵者'),('闵勖','所思旧主'),('周岳','所欲报仇对象')],year=None,note='八年为训练时长，不自行反算开始年或现代精确八整年；诸将未名不造人。')
event('deng_lei_takes_tanzhou_zhou_dies','邓处讷联雷满克潭斩周岳，自称留后',38,'893年条段末；练兵八年之后，具体日未载','潭州、朗州',
      '邓处讷联结朗州刺史雷满共攻潭州，攻克并杀周岳，邓自称留后。',[('邓处讷','联军攻克及自称者'),('雷满','朗州联军主将'),('周岳','被斩者')],note='段内初的往事与最后本年攻克分开；自称不作正式朝廷授任，朗州为雷职地非另一次战场。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={30:'送任拒军、壬午溃进、崔归责与甲申请诛、杜贬及命流、乙酉斩与再贬遣使、两中尉授分阶段；流地非已抵达，言罪为说辞。',31:'韦崔授相、父季父关系、小字及史评、安潜忧虑分层；缁郎非另人，预言非已败家。',32:'李不解请死、杜弘徽赐自尽、诏罪指控、后续两镇判官干预、李兼授徐御史分开；崔鋋非李鋋，王超按所属暂辨。',33:'王福建观察使正式授任区别五月自称。',34:'倪弃城未载目的地；杨任李未补到任日。',35:'王求尚书令与韦谏、十一月太师尚父铁券分开；尚父尊号非父子。',36:'迁盐铁为请求；徐郓为崔判断不造893郓陷，不可复制旧义。',37:'齐攻与援，无胜败不补。',38:'周岳闵勖886旧事复用原事件并存两段归责；誓报仇八年练兵年空，本年克潭斩岳自称留后。'}
for n in range(30,39):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(30,39):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=893,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(30,39)],next_paragraph='zztj-v259-y0894-p001',coverage='卷259景福二年第30—38段连续录入；本年段尾，完成须核五批审计。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
