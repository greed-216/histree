"""Curate consecutive Tongjian volume 261, year 899 paragraphs 9–20."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 30))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0899-p009-p020', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-899-dewei'
fixed_commit='8eccde0'
source_specs=[]
for d in sorted((P/'sources/library').iterdir()):
 r=json.loads((d/'paragraph.json').read_text());source_specs.append((d.name,r['book']+'·'+r['section_title'],{'资治通鉴':'司马光等','旧五代史':'薛居正等','新五代史':'欧阳修','新唐书':'欧阳修、宋祁等','旧唐书':'刘昫等'}[r['book']]))
reused_source_keys=set()
manifest=[]
for sk,title,author in source_specs:
 d=P/'sources/library'/sk;r=json.loads((d/'paragraph.json').read_text());filename='library/'+sk+'/source.txt';url='https://github.com/greed-216/histree/blob/'+fixed_commit+'/'+str((d/'source.txt').relative_to(ROOT))
 B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='选定TXT逐字导出；电子本，纸本及异文待核。',url=url,note=r['citation']))
 manifest.append(dict(key=sk,file=filename,sha256=hashlib.sha256((d/'source.txt').read_bytes()).hexdigest(),url=url,paragraph_id=r['id'],upstream_locator=r['locator'],transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
primary_keys=['tongjian-261-899-dewei','tongjian-261-899-summer']
primary_texts={sk:(P/'sources/library'/sk/'source.txt').read_text() for sk in primary_keys}
for n in range(9,21):assert Q[n]['text'] in ''.join(primary_texts.values())
def primary(n,q):return next(sk for sk in primary_keys if q in primary_texts[sk])
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'王熔':'王镕','国弘信':'罗弘信','硃友裕':'朱友裕','赫连鐸':'赫连铎','硃崇节':'朱崇节','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
alias.update({'李璠':'李璠（陕州）','王檀':'王檀（婺州）','陈汉宾':'陈海宾'})
people, used, reused = {}, {}, set(reused_source_keys)
alias.update({'李彦徽':'李彦徽（湖州）','延王戒丕':'李戒丕','王宗播':'许存','杜弘':'杜洪','嵩从周':'葛从周','硃瑾':'朱瑾','硃宣':'朱瑄','李继徽':'杨崇本','硃朴':'朱朴','韩健':'韩建','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_261_0899_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=primary(n,q), citation=f'卷261·光化二年（899）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷261光化二年条所见人物：{name}。',biography=None,status='draft')
    if name=='李抱真（唐潞州节度使）':row['era']='唐'
    B['people'].append(row);people[name]=row['key']
    nq={'陈章':'叔琮有骁将陈章，号“陈夜叉”，为前锋','氏叔琮':'叔琮有骁将陈章','李克用':'克用闻之，以戒德威','周德威':'克用闻之，以戒德威'} if n==9 else {}
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote=nq.get(name))
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=899,note=None,quote=None):
    key='event_zztj_261_0899_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_261_0899_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def e(code,title,n,q,actors=(),when=None,place=None,note=None,description=None,year=899):
    return event(code,title,n,when or '899年本段条；确日未载',place,description or title+'。',actors,quote=q,note=note,year=year)
e('chen_zhang_requests_reward','陈章请擒周德威求一州赏',9,'叔琮有骁将陈章，号“陈夜叉”，为前锋，请于叔琮曰：“河东所恃者周杨五，请擒之，求一州为赏。”',[('陈章','前锋请赏者'),('氏叔琮','受请主将')],when='899年三月河东战中；确日未载',place='河东',note='请为将来目标，不写已经擒周或已受一州；陈夜叉为绰号，周杨五与旧书周陽五字形分记，不静改底本。')
claim('person',people['陈章'],'aliases','陈章号陈夜叉。',9,quote='陈章，号“陈夜叉”',note='绰号不作超自然身世。')
e('li_warns_dewei_chen','李克用闻陈章求擒周德威而戒备之',9,'克用闻之，以戒德威',[('李克用','警戒告知者'),('周德威','受告知者')],when='899年三月河东战中；确日未载',note='后接周答有乱码，保原快照；只录可读的警戒行为，不猜乱码缺句。')
e('dewei_captures_chen_zhang','周德威微服挑战，诱陈章追而生擒',9,'德威微服往挑战，谓其属曰：“汝见陈夜叉即走。”章果逐之，德威奋铁楇击之坠马，生擒以献。',[('周德威','诱敌擒获者'),('陈章','追击被擒者')],when='899年三月河东交战中；确日未载',place='河东',note='生擒不记被斩，不补后处刑；铁楇保字，不改武器种类。上一句乱码未作为事实内容。旧五周传有可读完整平行叙述。')
e('dewei_defeats_shi_three_thousand','周德威军大破氏叔琮，斩首三千',9,'叔琮，大破之，斩首三千级。',[('周德威','击破者'),('氏叔琮','败方主将')],when='899年三月擒陈章后条；确日未载',place='河东',note='前接因系二字疑讹，原快照保留，不把系读成已俘氏；大破与斩数清楚，旧五武皇纪另具洞涡驿地。')
e('dewei_pursues_shihui','氏叔琮弃营，周德威追出石会关再斩千余',9,'叔琮弃营走，德威追之，出石会关，又斩千余级。',[('氏叔琮','弃营退者'),('周德威','追击者')],when='899年三月氏军败后；确日未载',place='石会关',note='又斩千余为追击阶段，不与此前三千硬凑精确全役损失；末句后周亦引还指代及字形未核，不新造后周朝代部队。')
claim('event','event_zztj_261_0899_dewei_pursues_shihui','description','主书末句另记引还，原文作后周，具体主体与文字待核。',9,quote='后周亦引还。',note='疑为前文从周的讹写，未核纸本不能静改或强认其人为另建事件。')
e('ding_hui_takes_ze','朱全忠遣丁会攻取泽州',10,Q[10]['text'],[('朱温','遣攻者'),('丁会','攻取者')],when='899年三月丁巳',place='泽州',note='丁巳承三月条，取泽与此前李嗣昭取泽为时序变化，不重复同一次夺城。')
e('wang_tan_requests_tian_help','婺州王檀被两浙围而向田頵求救',11,'婺州刺史王檀为两浙所围，求救于宣歙观察使田頵。',[('王檀','被围求援刺史'),('田頵','受求援者')],when='899年四月遣援前；确月日未载',place='婺州',note='王檀标婺州以消歧，未与梁将同名者并为一人；两浙围军将未具名，不补钱镠亲至。')
e('tian_sends_kang_wu','田頵遣康儒救婺州',11,'夏，四月，頵遣行营都指挥使康儒救之。',[('田頵','遣援者'),('康儒','受遣行营都指挥使'),('王檀','援救对象')],when='899年四月；确日未载',place='婺州')
e('wuxin_created_sui_five','遂州置武信军，遂合等五州属之',12,Q[12]['text'],when='899年五月甲午',place='遂州、合州等五州',note='接898王宗涤分镇申请，当前置军有明载；本句只名遂合，另外三州不无出处补进。未名实施者，不强添王建个人。')
e('li_junqing_sieges_lu','李克用遣李君庆攻李罕之，围潞州',13,'李克用遣蕃、汉马步都指挥使李君庆将兵攻李罕之，己亥，围潞州。',[('李克用','遣攻者'),('李君庆','受遣围军统帅'),('李罕之','受攻对象')],when='899年五月己亥围城；出兵日未另载',place='潞州',note='出兵与围起日分清，不写已经夺城。')
e('zhu_heyang_sends_zhang','朱全忠屯河阳遣张存敬援潞',13,'硃全忠出屯河阳，辛丑，遣其将张存敬救之',[('朱温','屯军遣援者'),('张存敬','受遣援军者')],when='899年五月辛丑遣援；屯河阳日未载',place='河阳、潞州')
e('ding_hui_second_aid_lu','朱全忠遣丁会继援潞州',13,'壬寅，又遣丁会将兵继之。',[('朱温','续遣者'),('丁会','继援将领')],when='899年五月壬寅',place='潞州')
e('bian_defeats_junqing_siege_ends','汴援军破河东兵，李君庆解潞围',13,'大破河东兵，君庆解围去。',[('李君庆','败退解围者')],when='899年五月继援后；确日未载',place='潞州',note='承张丁援军，具体战日与总指挥未单载，不将前壬寅直接作全部战日。')
e('li_executes_junqing_two_deputies','李克用诛李君庆、伊审、李弘袭',13,'克用诛君庆及其裨将伊审、李弘袭',[('李克用','诛杀者'),('李君庆','被诛主将'),('伊审','被诛裨将'),('李弘袭','被诛裨将')],when='899年五月潞州败退后；确日未载',note='三个具名者分别记录，未补族诛或临阵被敌军杀。')
for name in ['李君庆','伊审','李弘袭']:
 claim('person',people[name],'death_year',name+'在899年五月潞州败退后被李克用诛。',13,quote='克用诛君庆及其裨将伊审、李弘袭',note='确日未載，不当己亥战死。')
e('sizhao_replaces_junqing_lu','李嗣昭代任蕃汉马步都指挥使攻潞',13,'以李嗣昭为蕃、汉马步都指挥使，代之攻潞州。',[('李克用','代任遣攻方'),('李嗣昭','代任受遣者')],when='899年五月诛李君庆后；确日未载',place='潞州',note='代攻是再遣任务，不提前写已收潞。')
e('kang_longqiu_captures_qiu_wu','康儒龙丘败两浙、擒王球取婺州',14,Q[14]['text'],[('康儒','击败攻取者'),('王球','被擒将领')],when='899年五月庚戌',place='龙丘、婺州',note='与898王球受遣攻婺接续；擒不等于被斩。龙丘保史载名不猜坐标。')
e('hanzhi_severely_ill','李罕之疾亟',15,'六月，乙丑，李罕之疾亟。',[('李罕之','病重者')],when='899年六月乙丑',note='只记病重，不诊断病名或病因。')
e('zhu_hanzhi_heyang_ding_zhaoyi','朱全忠表李罕之为河阳、以丁会为昭义节度',15,'丁卯，全忠表罕之为河阳节度使，以丁会为昭义节度使。',[('朱温','安排调任表请者'),('李罕之','被表请河阳者'),('丁会','被置昭义者')],when='899年六月丁卯',place='河阳、昭义',note='朱表不等同本句独载朝廷制授，旧五本传补病篤换代，不提前写罕已去世。')
e('zhang_guiba_guards_xing','朱全忠以张归霸守邢州',15,'未几，又以其将张归霸守邢州',[('朱温','命守方'),('张归霸','受命守者')],when='899年六月调任后未几；确日未载',place='邢州',note='守邢不等于本句已朝廷授节。')
e('ge_replaces_ding_lu','朱全忠遣葛从周代丁会守潞州',15,'遣葛从周代会守潞州。',[('朱温','遣代守方'),('葛从周','代守者'),('丁会','被替换守军主将')],when='899年六月调任后未几；确日未载',place='潞州')
e('zongji_wuxin_appointed','王宗佶任武信节度使',16,'以西川大将王宗佶为武信节度使。',[('王宗佶','受任者')],when='899年六月条；确日未载',place='武信军',note='王宗佶复用907主体；本姓甘不推本名甘佶或王建血亲。')
claim('person',people['王宗佶'],'description','王宗佶本姓甘，为洪州人。',16,quote='宗佶，本姓甘，洪州人也。',note='籍贯不写出生地点，本姓不是完整原名。')
e('hanzhi_dies_huai','李罕之于怀州去世',17,Q[17]['text'],[('李罕之','去世者')],when='899年六月丁丑',place='怀州',note='承本月先病重、改镇，不写死于潞州；旧五本传补传舍及年五十八，不自动推生年。')
claim('person',people['李罕之'],'death_year','李罕之899年六月丁丑在怀州去世。',17)
e('wang_gong_killed_mutiny','保义王珙军乱被麾下所杀',18,'保义节度使王珙，性猜忍，虽妻子亲近，常不自保。至是军乱，为麾下所杀',[('王珙','军乱被杀者')],when='899年六月条；确日未载',place='保义军',note='猜忍为史书评价，不作现代人格诊断；本段杀者未具名，旧五称李璠保独立出处。')
claim('person',people['王珙'],'death_year','899年六月条记王珙在军乱中被麾下杀。',18,quote='至是军乱，为麾下所杀')
e('li_fan_shan_selected','军推李璠为保义留后',18,'推都将李璠为留后。',[('李璠','被推都将')],when='899年六月王珙被杀后；确日未载',place='保义军、陕州',note='李璠（陕州）不同已录892年战死宣武副使李璠，新建消歧主体；军推不作朝廷正式授节。')
e('chen_haibin_requests_yang','海州戍将陈海宾向杨行密请降',19,'秋，七月，硃全忠海州戍将陈海宾请降于杨行密。',[('陈海宾','海州请降戍将'),('杨行密','请降对象')],when='899年七月；确日未載',place='海州',note='同段后作汉宾，按指代同一人，保海/汉异名；请降与淮军实际据城分录。')
e('zhang_wang_take_haizhou','张训王绾率二千军入据海州',19,'淮海游奕使张训以汉宾心未可知，与涟水防遏使庐江王绾将兵二千直趣海州，遂据其城。',[('张训','领兵入据者'),('王绾','领兵入据者'),('陈海宾','所守城被据者')],when='899年七月请降后；确日未載',place='海州',note='汉宾心未可知是张训判断，不记已证谋反；王绾庐江是籍贯，涟水是官地。二千为主书记数。')
claim('person',people['王绾'],'description','王绾为庐江人，任涟水防遏使。',19,quote='涟水防遏使庐江王绾',note='籍贯、官地与海州行动地分清。')
claim('person',people['陈海宾'],'aliases','本段陈海宾后称汉宾，保陈汉宾异名。',19,quote=Q[19]['text'],note='同段指代与同海州戍将补书支持，不并其他同姓将。')
next(r for r in B['people'] if r['key']==people['陈海宾'])['aliases']=['陈汉宾']
e('cheng_rui_zhongshu','成汭加兼中书令',20,Q[20]['text'],[('成汭','受加者')],when='899年七月条；确日未載',place='荆南军',note='本句未单列壬辰，不从他书海州事干支挪来。')
supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
 record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0899_02_{len(B["claims"])+1:04d}'
 B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
 supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('jiuwudaishi-056-899-chen-zhang','event','event_zztj_261_0899_dewei_captures_chen_zhang','description','《旧五代史》周德威传亦记微服挑战、部下伪退，铁楇击陈章落马生获。','德威微服挑戰，部下偽退，陳章縱馬追之，德威背揮鐵楇擊墮馬，生獲以獻',9,'平行可读叙述印证擒陈，不用于凭想象填主书乱码。','corroborates')
extra('jiuwudaishi-056-899-chen-zhang','person',people['陈章'],'description','《旧五代史》记陈章曾乘骢马、着朱甲以自异。','陳章嘗乘驄馬朱甲以自異。',9,'骢马朱甲为此书外观补充，求赏未成，未新建封郡事件。')
extra('jiuwudaishi-026-899-zhao','event','event_zztj_261_0899_dewei_defeats_shi_three_thousand','location_name','《旧五代史》武皇纪记周德威败氏军于洞涡驿。','武皇令周德威擊之，敗汴軍於洞渦驛',9,'补本役地名，主书未具洞涡，不静改主书底本或猜现代坐标。')
extra('jiuwudaishi-026-899-zhao','event','event_zztj_261_0899_dewei_pursues_shihui','description','《旧五代史》亦记氏叔琮弃营、周德威追出石会关杀千余。','叔琮棄營而遁，德威追擊，出石會關，殺千餘人。',9,'同追击次序，斩千余/杀千余保原文，不推总损失。','corroborates')
extra('jiuwudaishi-026-899-zhao','event','event_zztj_261_0899_li_junqing_sieges_lu','description','《旧五代史》五月记李君庆将兵收泽潞，为汴军败退。','五月，武皇令都指揮使李君慶將兵收澤、潞，為汴軍所敗而還。',13,'收泽潞为任务，非已经两地皆下；本批主书围潞败退相承。','corroborates')
extra('jiuwudaishi-026-899-zhao','event','event_zztj_261_0899_sizhao_replaces_junqing_lu','description','《旧五代史》亦记李嗣昭代都指挥使进攻潞州。','以李嗣昭為都指揮使，進攻潞州。',13,'同代任遣攻，不把后八月收复提前。','corroborates')
extra('jiuwudaishi-015-899-hanzhi-death','event','event_zztj_261_0899_hanzhi_dies_huai','description','《旧五代史》记李罕之六月改河阳、行至怀州传舍卒，年五十八。','明年六月，病篤，太祖令丁會代之，移罕之為河陽節度使；行至懷州，卒於傳舍，時年五十八。',17,'明年承光化元年即899；补死处传舍和享年，不确定生年、疾病诊断或实际已赴河阳。')
extra('jiuwudaishi-063-899-li-fan','event','event_zztj_261_0899_wang_gong_killed_mutiny','description','《旧五代史》朱友谦传具体称光化二年六月李璠杀王珙。','二年六月，璠殺珙，歸附汴人，梁祖表璠為陝州節度使。',18,'本传前光化元年接二年，属899；补具名杀者只留该出处，军推留后不作主书已朝廷正式授节。')
extra('jiuwudaishi-063-899-li-fan','person',people['李璠（陕州）'],'description','《旧五代史》记陕州李璠为王珙牙将、受倚爱，也因小忤遭箠击而衔怨。','牙將李璠者，珙深所倚愛，小有違忤，暴加箠擊，璠陰銜之。',18,'此人为陕州牙将，已录892死宣武副使不能复活并入；本书后被朱简攻逃归汴先保时序，不提前899本批死亡。')
extra('xintangshu-010-899-chen-hanbin','event','event_zztj_261_0899_chen_haibin_requests_yang','time_original','《新唐书》记七月壬辰海州陈汉宾附杨行密，主书未列干支。','七月壬辰，海州戍將陳漢賓以其州叛附于楊行密。',19,'主书请降与随后淮军据城，书证统述归附；保独立确日，不静加主书所有行动同日。')
extra('xintangshu-010-899-chen-hanbin','person',people['陈海宾'],'aliases','《新唐书》同海州戍将名字作陈汉宾。','海州戍將陳漢賓',19,'同地同归附背景，与主书同段汉宾互指；保异名，不悄悄改主书陈海宾。','corroborates')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(9,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='十二段连续校核；陈章求赏与生擒、石会关追击分录。乱码原存，只引可读段，末后周指代待考。武信置军与授王宗佶分期。围潞与援军、诛主副、嗣昭代攻、罕病改镇死怀分录。陕州李璠与892死宣武副使消歧；陈海宾汉宾同段异名，未造未名将领或年代后果。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=899,primary_source_key=source,primary_source_keys=primary_keys,paragraphs=[Q[n]['id'] for n in range(9,21)],next_paragraph=Q[21]['id'],coverage='光化二年29段中的第9—20段连续处理，本年尚未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
