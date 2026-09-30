"""Curate consecutive Tongjian volume 258, year 891 paragraphs 9–16."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 41))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0891-p009-p016', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_258_0891_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·大顺二年（891）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('chengdu_famine','成都围城粮尽，贩米仍难济饥',9,'891年四月后条；围城期间','成都',
      '成都粮食短缺，弃儿满路，居民偷从行营贩米入城。韦昭度与陈敬瑄均准其救饥，贩米渐多但数量极少，米价高昂，饿死者众。',
      [('韦昭度','允贩米救饥者'),('陈敬瑄','允贩米救饥者')],note='米筒尺寸、价格和饥民惨状按书载，不换算现代物价；为本次围城背景，不定首次饥荒日。')
event('chengdu_cruelty_xu_geng','陈敬瑄诛欲降者，徐耕受逼杀俘',9,'891年四月后条；围城期间','成都',
      '军民强弱相欺，酷刑不能止；陈敬瑄捕杀谋出降者族党。内外都指挥使、眉州刺史徐耕仁恕，书载保全数千人；田令孜以不刑一人质疑其有异志，徐耕惧而夜杀俘囚于市。',
      [('陈敬瑄','捕杀族党者'),('徐耕','先宽恕后受逼杀俘者'),('田令孜','质疑逼迫者')],note='徐耕成都人为籍贯，不推当时眉州现地驻守；全活数千为书载，未具名俘囚不建人物。')
event('wang_rejects_withdrawal','王建拒罢兵，周庠劝独攻成都',10,'891年四月条；见罢兵制书后','成都行营',
      '王建见罢兵制书不愿撤围，询周庠；周庠劝请韦昭度还朝、独攻成都。王建上表请继续讨陈敬瑄田令孜，又说韦昭度宜返朝谋关东大事，由自己负责平定成都。',
      [('王建','拒撤围及说服者'),('周庠','献策者'),('韦昭度','被劝还朝者'),('陈敬瑄','奏表请讨对象'),('田令孜','奏表请讨对象')],note='奏表罪不可赦为王建立场；韦昭度犹豫与未能还朝不写为已同意。')
event('luo_bao_killed','王建令唐友通等杀食骆保以胁韦昭度',10,'891年四月庚子','行府门',
      '王建暗令东川将唐友通等擒韦昭度亲吏骆保于行府门，脔食之，称其盗军粮，以此恐吓韦昭度。',
      [('王建','密令者'),('唐友通','参与擒杀将领'),('骆保','被擒杀亲吏'),('韦昭度','受胁者')],note='称其盗军粮是杀者所持理由，不核定骆保确有盗粮；保留书载脔食，不为同伴补名。')
event('wei_hands_command_to_wang','韦昭度授王建印节，东还京师',10,'891年四月庚子及其后','成都行营、新都、京师',
      '韦昭度惊惧称病，将印节授王建，牒其知三使留后兼行营招讨使，当日东还；王建送至新都跪拜告别。韦昭度到京师后被任东都留守。',
      [('韦昭度','交印东还及受任者'),('王建','接印留后及送别者')],note='韦昭度到京师及任留守无独立干支，不把诸事都定庚子；牒知三使留后不改为朝廷正式授西川节度使。')
event('wang_blocks_jianmen','王建守剑门拒东军并急攻成都',10,'891年四月庚子后；韦昭度出剑门后','剑门、成都',
      '韦昭度刚出剑门，王建即派兵守之，不再容东军进入；又急攻成都，环城烽堑亘五十里。',[('王建','守关及围攻者')],note='五十里为书载围城规模，不换算疆域坐标。')
event('wang_yao_spy','王鹞诈亡入成都扰乱守方',10,'891年四月后条；急围成都时','成都',
      '狗屠王鹞请诈作得罪王建而逃入成都。入见陈敬瑄田令孜时称王建军疲粮尽将退，出而卖茶时暗向吏民称王建英武、兵强，致守方懈备而众心惧。',
      [('王鹞','诈亡间谍'),('王建','遣间者'),('陈敬瑄','受诈守方'),('田令孜','受诈守方')],note='两种相反说辞均是王鹞策略，不作为王建粮尽或将遁的事实。')
event('zheng_wo_spy_rename','郑渥诈降侦成都后改名王宗渥',10,'891年四月后条；围成都时','成都',
      '王建遣京兆郑渥诈降侦察。陈敬瑄任其为将、令登城，郑渥又用计得归，王建因而知城中虚实，任其亲从都指挥使，改姓名为王宗渥。',
      [('王建','遣间任职改名者'),('王宗渥','以郑渥旧名诈降侦察者'),('陈敬瑄','接纳诈降任将者')],note='郑渥与王宗渥为同一人，共用key；改姓名不自动推作养子关系。')
claim('person',people['王宗渥'],'aliases','郑渥后改姓名为王宗渥。',10,quote='以渥为亲从都指挥使，更姓名曰王宗渥。',note='同段先称京兆郑渥，后明载改姓名；郑渥作为旧名别名，不建第二个人物。')
event('zhou_yue_lingnan','周岳由武安改任岭南西道',11,'891年四月后条；具体日未载','武安、岭南西道',
      '朝廷以武安节度使周岳为岭南西道节度使。',[('周岳','改授节度使者')],note='任职不等于已出发或抵任。')
event('li_keyong_sieges_yun','李克用败赫连铎于河上，围云州',12,'891年四月后条；具体日未载','河上、云州',
      '李克用大举进击赫连铎，在河上击败其军，进围云州。',[('李克用','进击围城者'),('赫连铎','败军被围者')],note='河上原文未指具体河段，不标坐标。')
event('liu_zhu_huangchi_defeat','刘威朱延寿黄池击孙儒大败',13,'891年四月后条；五月大水前','黄池',
      '杨行密遣刘威、朱延寿率兵三万在黄池攻击孙儒，刘威等大败。',
      [('杨行密','遣军者'),('刘威','败军将领'),('朱延寿','败军将领'),('孙儒','获胜方')],note='三万为书载兵数，不改为阵亡或伤亡数。')
claim('person',people['朱延寿'],'biography','朱延寿为舒城人。',13,quote='延寿，舒城人也。',note='籍贯不等同本次战斗发生地。')
event('sun_ru_flood_retreat','黄池洪水淹营，孙儒还扬州',13,'891年五月','黄池、扬州',
      '孙儒驻军黄池，五月洪水使诸营被淹，遂回扬州。',[('孙儒','因水还军者')],note='诸营皆没不等于全军溺死，不补人数或具体日。')
event('kang_an_garrisons','孙儒遣康暀据和州、安景思据滁州',13,'891年五月条；还扬州时','和州、滁州',
      '孙儒使康暀据和州，安景思据滁州。',[('孙儒','派将者'),('康暀','据和州将领'),('安景思','据滁州将领')])
event('li_you_de_prince','皇子李祐封德王',14,'891年五月丙午','',
      '朝廷立皇子祐为德王。',[('李祐','德王受封者')],note='祐按唐皇室姓氏记李祐；不在这一条追填后来的改名、废立或生卒。')
event('li_shenfu_he_chu','李神福攻和滁，康暀降安景思走',15,'891年五月后条；具体日未载','和州、滁州',
      '杨行密遣李神福攻和州、滁州，康暀投降，安景思逃走。',
      [('杨行密','遣将者'),('李神福','攻城将领'),('康暀','投降者'),('安景思','逃走者')],note='安景思逃走不记死亡；两州行动同段合记，不补攻城确日。')
event('helian_abandons_yun','赫连铎云州食尽，奔吐谷浑后归幽州',16,'891年秋七月及其后','云州、吐谷浑部、幽州',
      '李克用急攻云州，赫连铎粮尽，逃往吐谷浑部，随后归幽州。',[('李克用','急攻者'),('赫连铎','粮尽出走者')],note='既而归幽州无独立日期，不强定同日；吐谷浑部不作一个精确地理坐标。')
event('shi_shanyou_datong','李克用表石善友为大同防御使',16,'891年七月条；云州守方出走后','大同',
      '李克用上表请以大将石善友为大同防御使。',[('李克用','表请者'),('石善友','被表请任职者')],note='表为不单推朝廷已批准；石善友不与石君和或石敬瑭混同。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={9:'饥荒贩米、酷刑和徐耕先宽后杀分录，尺寸价格数目为书载。',10:'拒撤兵、庚子杀骆保、韦昭度交印东还、封剑门围城及两间谍分录；郑渥王宗渥同人、旧名独立引用；诈言不当事实。',11:'改授周岳不推抵任。',12:'河上败军进围云州，不补河段坐标。',13:'黄池战败、五月洪水还军、两州留将分录，朱延寿籍贯另引。',14:'五月丙午封德王，祐补唐皇室姓氏，不追填未来改名。',15:'攻和滁与降逃依原文，未载确日。',16:'七月急攻食尽奔部归幽州和表石善友分录，表请不当已授。'}
for n in range(9,17):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,17):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=891,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph='zztj-v258-y0891-p017',coverage='卷258大顺二年第9—16段连续录入；本年40段尚未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
