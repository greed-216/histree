"""Curate consecutive Tongjian volume 259, year 894 paragraphs 1–8."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 34))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0894-p001-p008', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-894'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259乾宁元年条；书、卷、年、段落及行号见批次账本。')]
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
people, used, reused = {}, {}, set()
alias.update({'嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0894_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·乾宁元年（894）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259乾宁元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=894,note=None,quote=None):
    key='event_zztj_259_0894_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0894_'+code+'_'+pk
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

event('amnesty_era_qianning','昭宗赦天下，改元乾宁',1,'894年春正月乙丑朔','',
      '朝廷在正月初一赦天下，改元乾宁。',[('李杰','以唐昭宗身份在位的皇帝')],note='改元名称据该年标题乾宁元年；朔为月首，干支不换算公历日，不假定赦免范围的具体条款。')
event('li_maozhen_armed_court_visit','李茂贞入朝，陈兵自卫后归镇',1,'894年正月条；数日归镇','朝廷、凤翔',
      '李茂贞入朝，广陈兵力自卫，数日后返回所镇。',[('李茂贞','入朝陈兵后归镇者')],note='数日归镇为相对时长；不把入朝与返镇都定为乙丑，也不补陈兵数量。凤翔系既有职任背景，原段只称归镇。')
event('li_kuangchou_lulong_official','李匡筹正式受任卢龙节度使',2,'894年正月条；具体日未载','卢龙',
      '朝廷任李匡筹为卢龙节度使。',[('李匡筹','正式受任者')],note='与893年据军府自称留后分别记录，不回改自称为朝廷任命。')
event('zhu_wen_yushan_campaign','朱全忠亲军进击朱瑄，屯鱼山',3,'894年二月','鱼山',
      '朱全忠亲自领军攻朱瑄，在鱼山驻军。',[('朱温','以朱全忠名领军者'),('朱瑄','所击对象')])
event('zhu_xuan_jin_yushan_defeat','朱瑄朱瑾合击鱼山，兗郓军大败',3,'894年二月','鱼山',
      '朱瑄与朱瑾合兵攻朱全忠，兗郓军大败，书载死者一万余人。',[('朱瑄','合兵进攻而败者'),('朱瑾','合兵进攻而败者'),('朱温','以朱全忠名应战者')],note='万余是史书记数，未分两镇死者数量；主书未叙火攻，另书补记不改写本段原文。')
event('zheng_qi_chancellor','郑綮被授礼部侍郎同平章事',4,'894年二月条；具体日未载','朝廷',
      '朝廷以右散骑常侍郑綮为礼部侍郎、同平章事；昭宗认为其诗有所寓意，在班簿上亲自批注命为宰相。',[('郑綮','被任宰相者'),('李杰','以唐昭宗身份批注任命者')],note='有所蕴为昭宗的理解，不断言讥嘲诗证明其行政能力；授官与后来视事分阶段。')
claim('person',people['郑綮'],'biography','《通鉴》记郑綮喜诙谐，常作歇后诗讥嘲时事。',4,quote='綮好诙谐，多为歇后诗，讥嘲时事',note='人物特点为史书概述，不指定作品写于894年；歇后郑五是其自称，不另建郑五人物。')
event('zheng_qi_surprised_declines_then_serves','郑綮闻任惊讶，多次辞让后视事',4,'闻任以后；累让不获，乃视事','',
      '堂吏告知任命时，郑綮以诙谐言语表示难信及忧人取笑；贺客来时又感叹歇后郑五竟作宰相。多次辞让未获准，才就任处理政事。',[('郑綮','惊讶辞让后视事者')],note='其言时事可知矣为自述感叹，不作本项目的治乱判决；底本史曰疑吏曰，照存且不因此新增史某人物。视事确日未载。')
event('deng_chune_wuan_official','邓处讷受任武安节度使',5,'894年二月条；具体日未载','武安、邵州',
      '朝廷任邵州刺史邓处讷为武安节度使。',[('邓处讷','正式受任者')],note='与893年取潭州后自称留后区分，邵州是原官职地，未推当日人在邵州。')
event('zhang_jun_dies_recommends_brother','张钧去世，曾表请兄张鐇为留后',6,'894年二月条；卒及表的确日未载','彰义',
      '彰义节度使张钧去世，原文同记其上表请兄张鐇为留后。',[('张钧','去世节度使、表请者'),('张鐇','其兄、表请留后对象')],note='表其兄不拆为表弟亲属词，也不作去世后本人上表；表请不等朝廷已正式任命，年末正式任命另段。')
relation('张鐇','张钧','兄长',6,'张鐇是张钧的兄长，原文称其兄鐇。',quote='彰义节度使张钧薨，表其兄鐇为留后。')
event('wu_tao_huangzhou_surrenders','吴讨举黄州降杨行密',7,'894年三月','黄州',
      '黄州刺史吴讨带所辖州归降杨行密。',[('吴讨','举州归降刺史'),('杨行密','接受归降一方')],note='举州为辖州归降，不推全城人员逐一迁徙或杀害。')
event('li_cunxiao_requests_meeting','邢州粮尽，李存孝登城请见李克用',8,'894年三月甲申','邢州',
      '邢州城内粮尽，李存孝登城向李克用请求见面，称自己受王恩、因谗言才背离父子关系而附仇敌。',[('李存孝','登城请求并作辩解者'),('李克用','受请求者')],quote='邢州城中食尽，甲申，李存孝登城谓李克用曰：“儿蒙王恩得富贵，苟非困于谗慝，安肯舍父子而从仇雠乎！愿一见王，死不恨！”',note='承上三月；谗慝是存孝的辩解，不独立确认其叛离全部由别人逼成；既有养子关系复用人物身份，不因对话父子新建生父关系。')
event('liu_brings_cunxiao_to_keyong','刘夫人引李存孝出城见李克用',8,'894年三月甲申条后；具体时刻未载','邢州城外',
      '李克用派刘夫人探视李存孝；刘夫人带存孝出城见李克用。存孝叩首认罪，称李存信逼使自己失策；李克用反问他寄朱全忠、王镕的信中尽毁自己，难道也是存信教的。',[('李克用','遣夫人并质问者'),('刘氏（李克用妻）','以刘夫人称入城引见者'),('李存孝','谢罪辩解者'),('李存信','存孝辩解所指者'),('朱温','以朱全忠名被提及的收信人'),('王镕','被提及的收信人')],quote='克用使刘夫人视之。夫人引存孝出见克用，存孝泥首谢罪曰：“儿粗立微劳，存信逼儿，失图至此！”克用叱之曰：“汝遗硃全忠、王镕书，毁我万端，亦存信教汝乎！”',note='存孝与克用各自话语分开呈现，不裁定唯一责任；收信人在话语中提及，不表示现场在城外。刘夫人沿用884年已见的李克用妻刘氏，另书刘太妃称号不另建人。')
event('li_cunxiao_imprisoned_taken_jinyang','李存孝被囚，押回晋阳',8,'见李克用后；押回确日未载','邢州、晋阳',
      '李克用拘囚李存孝，将他押回晋阳。',[('李克用','拘囚押回者'),('李存孝','被拘押者')],quote='囚之，归于晋阳，车裂于牙门。',note='归于晋阳指押归，未把到达晋阳也记作邢州请见的甲申日。')
event('li_cunxiao_executed','李存孝在晋阳牙门被车裂',8,'894年；押回晋阳后，确日未载','晋阳、牙门',
      '李存孝押回晋阳后，在牙门被车裂。',[('李存孝','被处死者'),('李克用','李存孝所属军主')],quote='囚之，归于晋阳，车裂于牙门。',note='死亡日不能直接用甲申；牙门是主书地点，旧书于市另列，不以现代地点猜解。')
claim('person',people['李存孝'],'biography','《通鉴》称李存孝在李克用军中骁勇无比，常率骑兵为先锋，披重甲、持弓槊铁楇突阵，另随二马，在阵中换马。',8,quote='存孝骁勇，克用军中皆莫及；常将骑兵为先锋，所向无敌，身被重铠，腰弓髀槊，独舞铁楇陷陈，万人辟易。每以二马自随，马稍乏，就阵中易之，出入如飞。',note='传记式总述不作为894年某次新战役；所向无敌、万人辟易为史书赞述，不生成逐战人数。')
event('keyong_hopes_generals_plead','李克用惜李存孝之才，欲待诸将求情而无言',8,'李存孝临刑时；确日未载','晋阳',
      '《通鉴》叙李克用珍惜李存孝的才能，意欲在临刑时等诸将求情，再因而赦免；诸将嫉其才能，无人出言。',[('李克用','史书所叙希望诸将求情者'),('李存孝','临刑者')],quote='克用惜其才，意临刑诸将必为之请，因而释之。既而诸将疾其能，竟无一人言者。',note='惜才、预期及诸将嫉妒归于史书叙述；未发生释之，不把预期赦免记为实际释放，也不把每个具名武将都自动列为拒求情者。')
event('keyong_mourns_cunxiao','李克用因李存孝死十日不视事，未谴李存信',8,'李存孝死后；不视事旬日','晋阳',
      '李存孝死后，李克用十日不处理政事，私下恨诸将，却未责罚李存信。',[('李克用','不视事及未谴者'),('李存信','未受责罚者'),('李存孝','死亡引发此叙的将领')],quote='既死，克用为之不视事者旬日，私恨诸将，而于李存信竟无所谴。',note='旬日是书载时长，不反算起止公历日期；未谴不等史书证明存信无过。')
claim('person',person('薛阿檀',8,'与存孝勇力相侔的将领'),'biography','《通鉴》称薛阿檀之勇与李存孝相当，受诸将嫉妒、常不得志，私与存孝通信。',8,quote='又有薛阿檀者，其勇与存孝相侔，诸将疾之，常不得志，密与存孝通',note='长期处境与通信为总述，未反算始年或据同通断言同谋具体叛乱方案。')
event('xue_atan_suicide','李存孝被诛后，薛阿檀因恐泄事自杀',8,'894年；李存孝被诛以后','',
      '薛阿檀私下与李存孝通信，李存孝被诛后，怕事情泄露，遂自杀。',[('薛阿檀','恐泄事而自杀者'),('李存孝','已被诛的通信对象')],quote='又有薛阿檀者，其勇与存孝相侔，诸将疾之，常不得志，密与存孝通；存孝诛，恐事泄，遂自杀。',note='事的具体内容未明，未将密通写成已证实军事同谋；地点与确日未载。')
claim('person',people['李克用'],'biography','《通鉴》在李存孝死后评论：李克用兵势逐渐弱，而朱全忠独盛。',8,quote='自是克用兵势浸弱，而硃全忠独盛矣。',note='趋势性史评不生成894年具体兵力数或独立战役，也不推全由一次处刑导致。')
event('ma_shisu_xingming_recommendation','李克用表请马师素为邢洺节度使',8,'894年三月条末；具体日未载','邢洺',
      '李克用上表请任马师素为邢洺节度使。',[('李克用','上表者'),('马师素','表请任命对象')],quote='克用表马师素为邢洺节度使。',note='表为推荐请求，不推朝廷已经批准或马已到任。')

# Independent excerpts retain PDF text and line breaks from the committed JSONL.
from urllib.parse import quote as urlquote
supplements=[]
for sk,title,page in [('jiuwudaishi-001-894-yushan-start','旧五代史·卷1·梁太祖纪·鱼山战起',24),('jiuwudaishi-001-894-yushan-fire','旧五代史·卷1·梁太祖纪·鱼山火攻',25),('jiuwudaishi-053-894-cunxiao-meeting','旧五代史·卷53·李存孝传·出城前',1274),('jiuwudaishi-053-894-cunxiao-execution','旧五代史·卷53·李存孝传·出城与车裂',1275)]:
    path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
    raw=next(json.loads(x)['text'].encode() for x in (ROOT/path).read_text().splitlines() if json.loads(x)['pdf_page']==page)
    url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+f'#L{page}'
    (P/'sources'/(sk+'.txt')).write_bytes(raw)
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；逐字及换行保留，未核纸本。',url=url,note=f'原PDF第{page}页，只补当前主线段落。'))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation=f'提取JSONL pdf_page={page}的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(table,key,field,text,n,sk,quote,citation,note,kind):
    assert quote in (P/'sources'/(sk+'.txt')).read_text()
    ck=f'claim_zztj_259_0894_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=citation,note=f'原文：{quote}；核对说明：{note}',status='draft'))
    supplements.append(dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('event','event_zztj_259_0894_zhu_wen_yushan_campaign','description','《旧五代史》记乾宁元年二月梁太祖由郓州东路向北驻鱼山。',3,'jiuwudaishi-001-894-yushan-start','乾宁元年二月，帝亲领大军由郓\n州东路北次于鱼山。','卷1·梁书·太祖纪一·原PDF第24页','补进军方向，帝为后称梁太祖；894年朱温尚未称帝，不把书中帝称变成当年皇帝职任。','adds')
extra('event','event_zztj_259_0894_zhu_xuan_jin_yushan_defeat','description','《旧五代史》另记西北风骤起后朱温令纵火，乘烟焰攻击朱瑄朱瑾军，杀万余人；余众入清河，并在鱼山下筑京观。',3,'jiuwudaishi-001-894-yushan-fire','俄而西北风骤发，时\n两军皆在草莽中，帝因令纵火。既而\n烟焰亘天，乘势以攻贼阵，瑄、瑾大\n败。杀万余人，余众拥入清河，因筑\n京观于鱼山之下，驻军数日而还。','卷1·梁书·太祖纪一·原PDF第25页','承第24页二月鱼山段，独立补火攻、清河与京观；原书贼阵为史书立场，不使用为中立身份标签。','adds')
extra('event','event_zztj_259_0894_li_cunxiao_requests_meeting','time_original','《旧五代史》同记乾宁元年三月李存孝在邢州登城认罪求见李克用。',8,'jiuwudaishi-053-894-cunxiao-meeting','乾宁元年三月，存孝登城首罪，','卷53·唐书·列传第五·李存孝传·原PDF第1274页','印证月与请见次序；旧书此处未给甲申，不凭无日记载校定通鉴干支。','corroborates')
extra('event','event_zztj_259_0894_liu_brings_cunxiao_to_keyong','description','《旧五代史》称李克用遣刘太妃入城慰劳，太妃引李存孝出见；与《通鉴》刘夫人称号不同。',8,'jiuwudaishi-053-894-cunxiao-meeting','武皇愍之，遣\n刘太妃入城慰劳。太妃引来谒见，','卷53·唐书·列传第五·李存孝传·原PDF第1274页','刘太妃为后称，不能推894年已经受封太妃；相同叙事位置的刘氏沿用已有人物，不建第二刘氏。','adds')
extra('event','event_zztj_259_0894_li_cunxiao_executed','description','《旧五代史》记李存孝被押回太原后车裂于市；《通鉴》记晋阳牙门，地点用语并列。',8,'jiuwudaishi-053-894-cunxiao-execution','絷归\n太原，车裂于市。','卷53·唐书·列传第五·李存孝传·原PDF第1275页','太原与晋阳为各书用语；市与牙门具体位置未核，不能直接断为相同刑场或改写主书地点。','conflicts')
extra('event','event_zztj_259_0894_keyong_mourns_cunxiao','description','《旧五代史》亦记李存孝死后李克用十日不视事，久怨诸将。',8,'jiuwudaishi-053-894-cunxiao-execution','存孝死，武皇\n不视事旬日，私憾诸将久之。','卷53·唐书·列传第五·李存孝传·原PDF第1275页','书称武皇为追尊，不补894年帝号；此摘录不提李存信未谴，只印证旬日不视事及怨诸将。','corroborates')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={1:'正月朔改元赦与入朝陈兵数日返分录；不把返镇也定朔日。',2:'正式授任区别893自称。',3:'亲军进驻与合击败分录；旧五代史卷1两页补风火、清河与京观，帝称为后称。',4:'授相、惊讶辞让视事分开；讥嘲诗人物总述，史曰疑吏曰照存；言论不作项目治乱判决。',5:'武安正式授与893自称留后区别。',6:'卒与表请兄任记相对次序不以死人奏表；兄长方向张鐇→张钧；正式任节度在后段。',7:'举黄州降，不推人口迁移。',8:'粮尽甲申请见、刘引见辩解质问、囚押归、车裂、惜才欲待请、死后十日与不谴、薛自杀、马任表请分录；武勇与兵势为总述；死亡不强定甲申；旧史卷53印证三月、称刘太妃与市处刑分别存引。'}
for n in range(1,9):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=894,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph='zztj-v259-y0894-p009',coverage='卷259乾宁元年第1—8段连续录入；本年33段尚未完。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
