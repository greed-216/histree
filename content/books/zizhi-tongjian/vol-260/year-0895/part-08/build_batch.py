"""Curate consecutive Tongjian volume 260, year 895 paragraphs 33–36."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p033-p036', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-260-895'
B['sources'] = [dict(key=source,title='资治通鉴·卷260',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/260.txt',note='卷260乾宁二年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/260.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/260.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
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
alias.update({'嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_260_0895_08_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷260乾宁二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=895,note=None,quote=None):
    key='event_zztj_260_0895_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_260_0895_'+code+'_'+pk
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

alias.update({'李溪':'李磎','李谿':'李磎','薛王知柔':'李知柔','知柔':'李知柔','王瑰':'王瑰（河东判官）'})
event('rumored_warlords_fetch_emperor','传闻邠岐二帅将迎驾，唐昭宗惧受迫',33,'895年七月辛酉出京以前；确日未另载','京师',
      '有人传言王行瑜、李茂贞将亲来迎驾，唐昭宗担心受迫。',[('唐昭宗','闻传言而惧者'),('王行瑜','传言中的迎驾者'),('李茂贞','传言中的迎驾者')],quote='或传王行瑜、李茂贞欲自来迎车驾，上惧为所迫',note='或传保传闻，不写二帅此时已到京；帝担忧受迫不作已被劫。')
event('emperor_qixia_to_shacheng','唐昭宗以两都兵自卫，出启夏门宿莎城',33,'895年七月辛酉','启夏门、南山、莎城镇',
      '唐昭宗以李筠、李居实两都兵自卫，出启夏门向南山，宿莎城镇。',[('唐昭宗','出京避乱者'),('李筠','所属都兵护驾者'),('李居实','所属都兵护驾者')],quote='辛酉，以筠、居实两都兵自卫，出启夏门，趣南山，宿莎城镇。',note='两都为军队单位，不补兵数；方向与宿地保史名，未配坐标。')
event('followers_heat_deaths_robbed','扈从士民至谷口多暍死，夜遭盗掠',33,'895年七月辛酉出京途中及当夜','谷口、南山',
      '士民数十万追随车驾，至谷口时史书称暍死者三分之一，当夜又遭盗贼抢掠，哭声震山谷。',[('唐昭宗','士民所从车驾之主')],quote='士民追从车驾者数十万人，比至谷口，暍死者三之一，夜，复为盗所掠，哭声震山谷。',note='数十万与三之一为史书记载的概数和比例，不相乘推定确切死亡人数；未具体列士民或盗人姓名。')
event('li_zhirou_first_arrives_court_admin','薛王知柔先至，权知中书事及置顿使',33,'895年七月出京避乱时；确日未另载','行在',
      '百官多未及扈从，户部尚书、判度支及盐铁转运使薛王李知柔先至，皇帝命其暂管中书事并任置顿使。',[('李知柔','先至受权中书置顿者'),('唐昭宗','命暂管者')],quote='时百官多扈从不及，户部尚书、判度支及盐铁转运使薛王知柔独先至，上命权知中书事及置顿使。',note='权知中书事不作已经正式宰相；薛王知柔按唐宗室姓名归李知柔，未反算其封王日。')
for row in B['people']:
    if row['key']==people['李知柔']:row['aliases']=['薛王知柔']
event('keyong_enters_tongzhou','李克用入同州',34,'895年七月壬戌','同州',
      '李克用进入同州。',[('李克用','入同州者')],quote='壬戌，李克用入同州。')
event('three_chancellors_reach_shacheng','崔昭纬徐彦若王抟至莎城',34,'895年七月壬戌条；确日未另载','莎城',
      '崔昭纬、徐彦若、王抟到莎城。',[('崔昭纬','至莎城者'),('徐彦若','至莎城者'),('王抟','至莎城者')],quote='崔昭纬、徐彦若、王抟至莎城。')
event('emperor_moves_shimen','唐昭宗徙幸石门镇',34,'895年七月甲子','石门镇',
      '唐昭宗移驻石门镇。',[('唐昭宗','徙幸石门者')],quote='甲子，上徙幸石门镇')
event('zhirou_guangyu_guard_capital','李知柔刘光裕奉命还京制置宫禁守卫',34,'895年七月甲子徙石门条','京城、宫禁',
      '唐昭宗命薛王李知柔与知枢密院刘光裕回京城，安排宫禁守卫。',[('唐昭宗','命还京制卫者'),('李知柔','奉命还京者'),('刘光裕','知枢密院奉命者')],quote='命薛王知柔与知枢密院刘光裕还京城，制置守卫宫禁。',note='命还京是派遣，实际到京日未另载；不得与前段避乱一起判为都在石门留驻。')
event('wang_gui_court_inquiry','李克用遣判官王瑰奉表问起居',34,'895年七月丙寅','行在',
      '李克用派节度判官王瑰奉表询问皇帝起居。',[('李克用','遣问者'),('王瑰（河东判官）','奉表判官'),('唐昭宗','受问起居者')],quote='丙寅，李克用遣节度判官王瑰奉表问起居。',note='按河东判官职位消歧，不仅凭同名与891年已录国舅王瑰合并；此段未给表全文。')
event('xi_tingyu_edict_cavalry_xinping','郗廷昱赍诏，令李克用王珂各万骑赴新平',34,'895年七月丁卯','李克用军、新平',
      '唐昭宗派内侍郗廷昱带诏到李克用军，命李克用、王珂各发万骑赴新平。',[('唐昭宗','发诏者'),('郗廷昱','赍诏内侍'),('李克用','受令发骑者'),('王珂','受令发骑者')],quote='丁卯，上遣内侍郗廷昱赍诏诣李克用军，令与王珂各发万骑同赴新平。',note='各万骑为诏定军数，不作两万人已经齐抵新平。')
event('zhang_fan_blocks_fengxiang','诏张鐇以泾原兵控扼凤翔',34,'895年七月丁卯条；确日未另载','泾原、凤翔',
      '唐昭宗诏彰义节度使张鐇以泾原兵控制凤翔方向。',[('唐昭宗','发诏者'),('张鐇','受令彰义节度使')],quote='又诏彰义节度使张鐇以泾原兵控扼凤翔。',note='控扼非已经攻克凤翔；延续894年张鐇任彰义主体，未补兵数。')
event('keyong_attacks_huazhou','李克用遣兵攻华州，韩建质问',35,'895年七月石门发诏后条；确日未载','华州',
      '李克用派兵攻华州，韩建登城称对李公未失礼，质问受攻之由。',[('李克用','遣兵攻者'),('韩建','登城质问者')],quote='李克用遣兵攻华州；韩建登城呼曰：“仆于李公未尝失礼，何为见攻？”',note='未尝失礼为韩自辩，不据此否定此前三帅行为。')
event('keyong_rebukes_han_forcing_emperor','李克用答韩建逼逐天子为无礼',35,'895年七月攻华州时；确日未載','华州',
      '李克用使人答韩建，责其身为臣而逼逐天子，不当以有礼自居。',[('李克用','遣答责者'),('韩建','受责者')],quote='克用使谓之曰：“公为人臣，逼逐天子，公为有礼，孰为无礼者乎！”',note='回复为李言辞，不补使者姓名。')
event('xi_reports_warlords_near_shimen','郗廷昱至，报邠岐军欲迎驾',35,'895年七月李军攻华州时；确日未载','华州、盩厔、兴平',
      '郗廷昱到李克用处，报告李茂贞领三万兵到盩厔，王行瑜领兵到兴平，皆欲迎驾。',[('郗廷昱','传军情者'),('李克用','受军情者'),('李茂贞','所报盩厔领军者'),('王行瑜','所报兴平领军者')],quote='会郗廷昱至，言李茂贞将兵三万至盩厔，王行瑜将兵至兴平，皆欲迎车驾',note='保存郗报告语气；三万仅李军，王军未给数，迎驾意图不作已到行在。')
event('keyong_lifts_hua_moves_weiqiao','李克用解华州围，移营渭桥',35,'895年七月受郗报告后；确日未载','华州、渭桥',
      '李克用解除华州之围，将军队移营渭桥。',[('李克用','解围移军者')],quote='克用乃释华州之围，移兵营渭桥。',note='解围不是攻陷华州或韩建已投降；与下段进军渭桥时序另留书证。')
event('li_zhirou_qinghai_commission','李知柔授清海节度使同平章事，暂留京职',36,'895年七月条；确日未载','清海、京兆、朝廷',
      '朝廷任薛王李知柔为清海节度使、同平章事，仍暂管京兆尹、判度支、盐铁转运使，待皇帝返京后赴镇。',[('李知柔','受清海节度使并暂留京职者')],note='俟反正日赴镇是任命中的未来条件，不记李已到广州；反正保当时回京恢复秩序语意，不改成现代政权倒戈。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-895-shimen-huazhou';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==597)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L597'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·石门与华州',source_type='primary',author='薛居正等',edition='仓库PDF派生文本；原字换行保留，未核纸本。',url=url,note='原PDF第597页，乾宁二年七月段。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=597的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
supplements=[]
def extra(code,n,text,quote,note,kind='corroborates'):
    assert quote in raw.decode();ck=f'claim_zztj_260_0895_08_{len(B["claims"])+1:04d}';key='event_zztj_260_0895_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation='卷26·唐书二·武皇纪下·乾宁二年七月段·原PDF第597页',note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('wang_gui_court_inquiry',34,'《旧五代史》同记李克用遣判官王瑰奉表奔问皇帝。','遣判\n官王瑰奉表奔问','与主书节度判官、奉表问起居同动作链，补同人职位引用，不等于与国舅同名者已证合一。')
extra('keyong_lifts_hua_moves_weiqiao',35,'《旧五代史》记闻邠岐二军欲往石门迎驾后，李克用解华州围、进营渭桥。','欲往石门迎驾，\n乃解华州之围，进营渭桥。','补明确所欲目的地石门；不写二军已成功到达石门。')
reviews={
 33:'或传迎驾为传闻；辛酉两都自卫出启夏宿莎、士民追从暍死夜盗、知柔先至权中书置顿分录。概数与三之一不反算死数，两都非人数。',
 34:'壬戌入同与三相至莎、甲子徙石门及命李刘还京守宫、丙寅王瑰问、丁卯郗诏各万骑赴新平与张鐇控凤分录。王瑰按判官消歧不盲合国舅；命令军数非已抵。',
 35:'攻华与韩自辩、李责、郗报两军、解围移渭桥各录，韩礼貌自陈不作实断；李茂三万不分给王，解围非克城。',
 36:'清海同平章与京兆度支转运留职为同次条件授官；待反正赴镇非已到广州。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(33,37):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(33,37)],next_paragraph=Q[37]['id'],coverage='第33—36段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
