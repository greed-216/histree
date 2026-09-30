"""Curate consecutive Tongjian volume 259, year 892 paragraphs 17–24."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 47))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0892-p017-p024', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias['吉谏']='王宗黯'
alias.update({'郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0892_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·景福元年（892）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

def relation(a,b,t,n,description,quote=None):
    ka,kb=people[a],people[b]
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==ka and r['person_b_key']==kb and r['relation_type']==t]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);key=row['key'];reused.add(key)
    else:
        key=f'relationship_{ka}_{kb}_{t}';row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key

supplements=[]
event('li_wang_take_tianchang','李克用王处存合攻镇州拔天长镇',17,'892年三月癸丑','天长镇',
      '李克用与王处存合兵攻王镕，攻取天长镇。',[('李克用','合攻者'),('王处存','合攻者'),('王镕','被攻方')],note='天长镇不等同淮南天长县，同名地点不标未经核实坐标。')
event('wang_rong_wins_xinshi','王镕新市大败河东定州军',17,'892年三月戊午','新市',
      '王镕与李克用王处存联军在新市交战，大败对手，书载杀获三万余。',[('王镕','获胜方'),('李克用','败军主将'),('王处存','合兵一方')],note='杀获包括杀与俘，不能全部作阵亡；不补未载的两军分项损失。')
event('li_retreat_luancheng_mediation','李克用退屯栾城，朝廷诏和四镇',17,'892年三月辛酉及其后','栾城、河东、镇州、定州、幽州',
      '李克用退屯栾城，朝廷下诏和解河东、镇、定、幽四镇。',[('李克用','退屯者')],note='诏和不等于四镇已签和约；四镇是调停对象，不把所有领帅自动挂为同一现场参与者。')
event('yang_sheng_requests_diversion','杨晟求诸杨攻东川解彭州围',18,'892年三月条；具体日未载','彭州、东川',
      '杨晟给杨守贞、杨守忠、杨守厚写信，要求攻击东川以解彭州围，杨守贞等同意。',[('杨晟','书信求援者'),('杨守贞','应求者'),('杨守忠','应求者'),('杨守厚','应求者')],note='约援限定本次行动，不构造永久联盟。')
event('dou_xingshi_plot_execution','窦行实内应败露，被顾彦晖斩',18,'892年三月条；杨守厚至涪城时','梓州、涪城',
      '神策督将窦行实戍梓州，被杨守厚暗诱为内应。杨守厚至涪城时事泄，顾彦晖斩窦行实，杨守厚逃去。',[('窦行实','内应被斩者'),('杨守厚','诱应及退走者'),('顾彦晖','斩内应者')],note='梓州为窦戍守地点、涪城为杨到达地点，不把两地合成一个坐标。')
event('ji_jian_breaks_shouhou','吉谏袭败杨守厚',18,'892年三月条；内应事泄后','绵州、剑州一带',
      '杨守贞杨守忠军到后无归处，在绵、剑间停留。王建遣吉谏袭杨守厚并击败之。',[('杨守贞','盘桓军将'),('杨守忠','盘桓军将'),('王建','遣袭者'),('王宗黯','以吉谏旧名袭敌者'),('杨守厚','败方')],note='吉谏后名王宗黯由十国春秋对应景福元年条补证，不另建同人；攻击准确地点未载，绵剑只表军所在范围。')
event('li_jian_zhongyang_win','李简钟阳邀击杨守忠',18,'892年三月癸亥','钟阳',
      '西川将李简在钟阳邀击杨守忠，书载斩获三千余。',[('李简','王建麾下获胜将领'),('杨守忠','败方')],note='复用李简（王建将）key；斩获不全作战死；钟阳未核现代定位。')
event('li_jian_tongmao_win','李简铜鉾破杨守厚，降众万五千',18,'892年夏四月','铜鉾',
      '李简再次在铜鉾击败杨守厚，书载斩获三千余、降一万五千人；杨守忠与杨守厚皆逃走。',[('李简','王建麾下获胜将领'),('杨守厚','败退者'),('杨守忠','逃走者')],note='斩获、投降为不同数目，不相加成死亡；铜鉾保留史载字形，坐标空。')
event('qian_wusheng_hangzhou','杭州置武胜军，钱镠任防御使',19,'892年四月乙酉','杭州',
      '朝廷在杭州设置武胜军，任钱镠为防御使。',[('钱镠','防御使受任者')],note='防御使不能写成此时已授镇海节度使。')
event('jia_desheng_killed','贾德晟怨李顺节死，西门君遂奏杀',20,'892年四月条；具体日未载','京师',
      '天威军使贾德晟因李顺节之死心怀怨愤，西门君遂厌恶，上奏后杀之。',[('贾德晟','怨愤被杀者'),('西门君遂','奏杀者'),('杨守立','以李顺节名义此前死者')],note='李顺节死发生891年，不把其死重复记892年；仅作贾德晟怨因所指。')
event('jia_cavalry_flees_feng','贾德晟部骑千余奔凤翔',20,'892年四月条；贾德晟被杀后','凤翔',
      '贾德晟部下千余骑奔凤翔，李茂贞势力因此增强。',[('贾德晟','此前部众所属者'),('李茂贞','受兵增强者')],note='千余骑为部众书载，贾已死非本人逃往凤翔；不补受任职位。')
event('li_kuangwei_invades_li_returns','李匡威侵云代，李克用引军还',21,'892年四月壬寅','云州、代州',
      '李匡威出兵侵云、代，壬寅李克用开始率军返回。',[('李匡威','进兵侵境者'),('李克用','引军返者')],note='未补李克用军最终抵达地或抵达确日，不由相邻记载生成正式因果边。')
event('zhang_li_take_chuzhou','张训李德诚寿河败徐兵取楚州',22,'892年四月条；具体日未载','寿河、楚州',
      '时溥遣兵南侵至楚州，张训李德诚在寿河击败之，取得楚州，拘执刺史刘瓚。',[('时溥','遣南侵军主将'),('张训','获胜取城将领'),('李德诚','获胜取城将领'),('刘瓚','被执刺史')],note='刘瓚被执不写被杀；寿河未核坐标，取楚州与战地点区别。')
event('wang_xingyu_zhongshu','王行瑜加兼中书令',23,'892年五月','邠宁',
      '朝廷加邠宁节度使王行瑜兼中书令。',[('王行瑜','加官者')])
event('sun_guangde_supply_cut','杨行密破孙儒广德营，张训断粮道',24,'892年六月戊寅战前；具体日未载','广德、安吉',
      '杨行密屡败孙儒军，攻破广德营；张训驻安吉，切断孙儒粮道。',[('杨行密','击破营寨者'),('孙儒','被击一方'),('张训','屯军断粮者')],note='屡败只概括本段，不补每次确日和未载地点。')
event('sun_epidemic_plunder','孙儒军粮尽染疫，遣刘建锋马殷掠县',24,'892年六月戊寅战前；具体日未载','宣州一带诸县',
      '孙儒粮尽，士卒大疫，遣刘建锋与马殷分兵掠诸县。',[('孙儒','粮尽遣将者'),('刘建锋','分兵掠县者'),('马殷','分兵掠县者')],note='大疫为史载，不用现代病名诊断士卒；诸县无名，不造具体名单。')
event('yang_june_defeats_sun','杨行密趁孙儒疾疟出击，雨中大败敌军',24,'892年六月戊寅','宣州战场',
      '杨行密听说孙儒患疟，纵兵进攻，恰逢大雨天暗，孙儒军大败。',[('杨行密','进攻获胜者'),('孙儒','书载闻疾疟败军主将')],note='闻疾疟为书载消息，未独立医学确诊；会大雨与战果并记，不补唯一败因。')
event('tian_captures_kills_sun','安仁义破五十余寨，田頵擒斩孙儒',24,'892年六月戊寅条；战败后','宣州战场、京师',
      '安仁义攻破孙儒五十余寨，田頵在阵中擒孙儒并斩之，将首级送京师；孙儒部众多降杨行密。',[('安仁义','破寨者'),('田頵','擒斩者'),('孙儒','被擒斩者'),('杨行密','部众归降对象')],note='擒儒于陈的陈为阵义，不定位到陈州；京师为传首目的地而非斩杀点；五十余寨为书载。')
event('liu_ma_southward','刘建锋马殷收七千余众南走洪州',24,'892年六月孙儒死后','洪州',
      '刘建锋马殷收余众七千，南走洪州，推刘建锋为帅、马殷为先锋指挥使，张佶为谋主。',[('刘建锋','被推主帅'),('马殷','先锋指挥使'),('张佶','谋主')],note='七千为所收余众书载，主帅由军中推举，不写朝廷任命。')
event('liu_ma_grows_jiangxi','刘建锋军到江西时增至十余万的后续',24,'比至江西；具体年月未载','江西',
      '《通鉴》续述刘建锋马殷所领军到江西时增至十余万。',[('刘建锋','主帅'),('马殷','先锋')],year=None,note='比至的经过时长不明，后续确年留空；不把十余万与七千当作同日同一统计。')
# Independent source excerpts mapped to the exact current paragraphs.
for sk,title,author,path,commit,book,page in [
 ('shiguochunqiu-039-892-ji-jian','十国春秋·卷39·王宗黯姓名摘录','吴任臣','resources/derived/shiguochunqiu/039-ji-jian-892-excerpt.txt','bde215d79e86c885c3b0dced8268505057567ed9','十国春秋',None),
 ('xinwudaishi-061-892-sun-ru','新五代史·卷61·吴世家·孙儒败亡段','欧阳修','resources/derived/twenty-four-histories/19新五代史.jsonl','17a0b9a305d40d6371bbdd66d1827c8f2f7321fa','新五代史',1274)]:
    from urllib.parse import quote as urlquote
    raw=(ROOT/path).read_bytes()
    if page:raw=next(json.loads(x)['text'].encode() for x in raw.decode().splitlines() if json.loads(x)['pdf_page']==page)
    local=sk+'.txt';(P/'sources'/local).write_bytes(raw)
    url='https://github.com/greed-216/histree/blob/'+commit+'/'+urlquote(path,safe='/')+('#L1274' if page else '')
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='电子文本摘录；原文与换行保留，未核纸本。',url=url,note='只补当前连续段落对应身份与战事；不提前录后续履历。'))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=local,sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='从JSONL提取pdf_page=1274的text字段，不改字。' if page else '已归档电子网页首句摘录，不是整卷。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(table,key,field,value,n,sk,quote,citation,note,book,kind):
    assert quote in (P/'sources'/(sk+'.txt')).read_text()
    ck=f'claim_zztj_259_0892_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=value,source_key=sk,citation=citation,note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,primary_paragraph_id=Q[n]['id'],subject_key=key,source_book=book,relation=kind))
extra('person',people['王宗黯'],'aliases','《十国春秋》记王宗黯本姓吉名谏，景福元年破杨守厚后获赐姓名。',18,'shiguochunqiu-039-892-ji-jian','王宗黯，本姓吉，名諫，隸高祖帳下爲牙將，景福元年破楊守厚有功，賜姓名曰王宗黯。','卷39·王宗黯传首句·姓名摘录第3行','对应主段吉谏袭杨守厚；同人共用key，吉谏为旧名。清代汇编不作为独立同时代见证。','十国春秋','adds')
extra('event','event_zztj_259_0892_tian_captures_kills_sun','description','《新五代史》记孙儒兵饥大疫，杨行密尽兵击之，孙儒败被擒。',24,'xinwudaishi-061-892-sun-ru','久\n之，儒兵饥，又大疫，行密悉兵击\n之，儒败，被擒','卷61·吴世家第一·原PDF第1274页','印证本段败亡过程，换行逐字保留；本段未据此补新五代史临死对话或超出主段的以后事件。','新五代史','corroborates')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={17:'癸丑拔天长、戊午新市败军、辛酉栾城退与诏和分录，杀获三万非纯死亡。',18:'求援、内应斩窦、吉谏袭败、癸亥钟阳战、四月铜鉾战跨月分录；吉谏王宗黯同人补证。',19:'四月乙酉杭州置武胜、授防御使不提前升节度。',20:'贾德晟奏杀与部骑千余奔凤翔分录，李顺节死仍891，不重复892死亡。',21:'侵云代与壬寅李克用还未補抵达终点。',22:'寿河战楚州取刘瓚执，不记已死。',23:'五月王行瑜加官。',24:'广德断粮、疫病掠县、六月雨战、破寨擒斩传首、余众南洪与增长后续分录；陈为阵非陈州；新五代史败被擒独引。'}
for n in range(17,25):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17,25):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=892,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph='zztj-v259-y0892-p025',coverage='卷259景福元年第17—24段连续录入；本年46段尚未完。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
