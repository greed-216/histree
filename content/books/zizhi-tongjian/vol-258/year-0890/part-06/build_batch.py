"""Curate consecutive Tongjian volume 258, year 890 paragraphs 37–43."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 44))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0890-p037-p043', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-258-890'
B['sources'] = [dict(key=source,title='资治通鉴·卷258',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/4d35696319726b523bd624f2370cb2cf7faa6b43/resources/derived/tongjian/258.txt',note='卷258大顺元年起；书、卷、年、段落及行号见批次账本。')]
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

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0890_06_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·大顺元年（890）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷258大顺元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=890,note=None,quote=None):
    key='event_zztj_258_0890_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_258_0890_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('mao_xiang_qiong_siege','邛州粮尽，毛湘请任可知持首归王建',37,'890年闰月壬戌','邛州',
      '王建急攻邛州，毛湘粮尽而救兵不到，向任可知表示不忍负田令孜、吏民无罪，愿其持己首归王建，随后沐浴待死。',
      [('王建','攻城者'),('毛湘','请以首归降者'),('任可知','受嘱将领'),('田令孜','毛湘不忍辜负对象')],note='田令孜本段为原亲吏关系及言语对象，不写其在城中；请求与临死准备分清，不补动机为现代判断。')
event('ren_kills_mao_surrenders','任可知斩毛湘及二子降王建',37,'890年闰月壬戌条','邛州',
      '任可知斩毛湘及其二子后投降王建，《通鉴》记士民皆泣。',
      [('任可知','斩人投降者'),('毛湘','被斩者'),('王建','受降者')],note='二子未具名，不新建人物；士民皆泣为书载叙述。')
event('wang_enters_qiong','王建持永平旌节入邛州，张琳知留后',37,'890年闰月甲戌','邛州',
      '王建持永平旌节进入邛州，以节度判官张琳知留后，修整城隍，抚安夷獠，经营蜀、雅。',
      [('王建','入州修治者'),('张琳','知留后受任者')],note='经营不推定蜀雅当日均已完全实控；知留后保留代理任用性质。')
event('wang_returns_chengdu_890','王建回兵成都，李行周以蜀州降',37,'890年十月癸未朔','成都、蜀州',
      '王建率兵返回成都，蜀州将李行周驱逐徐公鉥，举城投降王建。',
      [('王建','回兵及受降者'),('李行周','逐刺史降城者'),('徐公鉥','被逐刺史')],note='李行周与前段常州张行周姓名不同，不合并人物。')
event('zhu_denied_passage_wei','朱全忠赴滑州，魏镇拒粮马借道',38,'890年十月乙酉','河阳、滑州、魏、镇',
      '朱全忠自河阳赴滑州视事，向魏请求粮马与借道讨河东，罗弘信不许；再向镇请求，镇人亦不许。',
      [('朱温','以朱全忠名义请求者'),('罗弘信','拒绝者')],note='镇人未直接具名，不把拒绝归作王镕亲自决定的独立事实。')
event('zhu_crosses_liyang','朱全忠自黎阳渡河攻魏',38,'890年十月乙酉条后','黎阳、魏',
      '借道请求被拒后，朱全忠自黎阳渡河进攻魏。',[('朱温','以朱全忠名义渡河进攻者')],note='未给精确渡口，不据此绘行军线。')
event('wang_xingyu_zhang_quanyi_promoted','王行瑜加侍中，张全义加同平章事',39,'890年十月后条；具体日未载','',
      '朝廷加邠宁节度使王行瑜侍中，加佑国节度使张全义同平章事。',
      [('王行瑜','加侍中者'),('张全义','加同平章事者')])
event('hedong_defense_hongdong_zhaocheng','官军出阴地关，河东军驻洪洞赵城',40,'890年十一月条前；具体日未载','阴地关、汾州、洪洞、赵城',
      '官军出阴地关，游兵至汾州；李克用遣薛志勤、李承嗣驻洪洞，李存孝驻赵城。',
      [('李克用','部署者'),('薛志勤','洪洞驻军将领'),('李承嗣','洪洞驻军将领'),('李存孝','赵城驻军将领')],note='三千骑、五千兵为书载规模，段内未给各项确日。')
event('han_jian_raid_defeated','韩建夜袭李存孝营受伏，官军溃退',40,'890年十一月条前；具体日未载','赵城、晋州西门',
      '韩建率壮士夜袭李存孝营，李存孝预知设伏，韩建兵不利；静难、凤翔军不战而走，禁军溃散，河东军追抵晋州西门。',
      [('韩建','夜袭失利者'),('李存孝','设伏胜方将领')],note='三百为书载人数；禁军自溃为书载叙述，不推各个将领已死。')
event('zhang_defeated_defends_jin','张浚出战再败，与韩建闭守晋州',40,'890年十一月条前；具体日未载','晋州',
      '张浚出战再败，官军死者书载近三千。诸镇军先渡河西归，张浚所余禁军、宣武军与韩建闭城防守，此后不敢再出。',
      [('张浚','战败守城者'),('韩建','共同守城者')],note='近三千死者、合万人守军均书载数字，不独立核实。')
event('zhang_xinggong_abandons_jiang','李存孝攻绛州，张行恭弃城',40,'890年十一月','绛州',
      '李存孝率军攻绛州，刺史张行恭弃城逃走。',[('李存孝','攻城者'),('张行恭','弃城刺史')])
event('li_cunxiao_withdraws_zhang_flees','李存孝退军，张浚韩建逃离晋州',40,'890年十一月；攻晋州三日后','晋州、含口',
      '李存孝攻晋州三日后，与部众议称俘宰相无益、天子禁兵不宜加害，遂后退驻军；张浚、韩建自含口逃去。',
      [('李存孝','议后撤军者'),('张浚','逃离者'),('韩建','逃离者')],note='退五十里为书载距离，不换算精确路线；议论为李存孝言论。')
event('li_takes_jin_jiang','李存孝取晋绛并掠慈隰',40,'890年十一月；张浚韩建逃后','晋州、绛州、慈州、隰州',
      '李存孝取得晋、绛二州，并大掠慈、隰境内。',[('李存孝','取州及侵掠将领')],note='保留大掠，不改写为单纯接管。')
event('li_keyong_petition_background','李克用遣韩归范归朝诉冤的前事',40,'张浚战败以前；具体年日未载','朝廷',
      '李克用此前遣韩归范归朝附表申冤，列举三代四朝功劳，批评朝廷赏他镇而罚河东，并称已集兵五十万，欲与张浚决战或入朝自诉。',
      [('李克用','上表者'),('韩归范','归朝送表者'),('张浚','奏表所指交战对象')],year=None,note='先是标前事；功绩、五十万及赴朝计划均为奏表说法，不作独立核实或已执行事实。韩彭伊吕为比喻不建参与人。')
event('zhang_han_retreat_heyang','张浚韩建越王屋至河阳渡河',40,'890年十一月条后；具体日未载','王屋、河阳',
      '李克用奏表抵朝时张浚已败，朝廷震恐；张浚、韩建越王屋至河阳，拆民屋作筏渡河，书载师徒失亡殆尽。',
      [('张浚','败退渡河者'),('韩建','败退渡河者')],note='失亡殆尽保留书载用语，不等同于全军阵亡，不补总死亡数。')
event('hedong_campaign_assessment','通鉴评河东之役协同失利',40,'河东之役回顾；非独立确日事件','',
      '《通鉴》总述朝廷原倚朱全忠及河朔三镇，但朱全忠正战徐郓，虽遣将攻泽州而本人未至；镇魏不出兵粮，孙揆被擒、幽云败军及杨复恭居中阻挠，官军遂溃。',
      [('朱温','以朱全忠名义被评援军方'),('杨复恭','书载居中阻挠者'),('张浚','战役失利统帅'),('孙揆','此前被擒的副使')],year=None,note='是役也为书中综合解释，不创建独立因果边。底本末列鄄疑异字，不据疑字建精确援军来源地图。')
event('sun_ru_takes_suzhou','孙儒取苏州杀李友',41,'890年十二月己丑','苏州',
      '孙儒攻取苏州，杀李友。',[('孙儒','攻城杀将者'),('李友','被杀者')])
event('an_renyi_leaves_runzhou','安仁义等焚润州庐舍夜撤',41,'890年十二月己丑条；闻苏州失后','润州',
      '安仁义等闻苏州失陷，焚烧润州庐舍，夜间撤离。',[('安仁义','焚舍撤军者')],note='底本“润庐舍”依同段后句润州守将语境整理，未猜焚毁规模。')
event('shen_gui_garrison','沈粲归传道受孙儒命分守苏润',41,'890年十二月己丑条后','苏州、润州',
      '孙儒命沈粲守苏州，另遣其将归传道守润州。',
      [('孙儒','任守者'),('沈粲','苏州守将'),('归传道','润州守将')])
event('ding_ge_take_liyang_linhe','丁会葛从周渡河取黎阳临河',42,'890年十二月辛丑','黎阳、临河',
      '汴将丁会、葛从周进击魏军，渡河取得黎阳、临河。',[('丁会','进击取地将领'),('葛从周','进击取地将领')])
event('pang_huo_take_qimen_wei','庞师古霍存下淇门卫县，朱全忠继进',42,'890年十二月辛丑条','淇门、卫县',
      '庞师古、霍存攻下淇门、卫县，朱全忠随后率大军推进。',
      [('庞师古','攻取将领'),('霍存','攻取将领'),('朱温','以朱全忠名义率后续大军者')])
event('shengzhou_established','上元置升州，张雄任刺史',43,'890年；原文是岁','上元县、升州',
      '朝廷在上元县置升州，以张雄为刺史。',[('张雄','升州刺史受任者')],note='是岁只有年，不补月份和设州具体边界。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={37:'闰月毛湘末事、任可知斩降、甲戌入邛与十月癸未回兵、李行周逐刺史分录；二子未具名不建人物。',38:'赴滑州请求与拒绝、黎阳渡河进攻分录；镇人不猜指定决策人。',40:'韩建夜袭失利、张浚守城、十一月取绛晋、退避逃遁、先是上表、败退渡河及书中总评分录。五十万仅奏表声称，失亡不解为全部阵亡；末列鄄疑字保留。',41:'己丑苏州被取杀李友、安仁义焚润撤走、沈粲归传道分守分别录入。',42:'两组攻取地点与后续大军分录，未绘精确行军线。',43:'本年置升州不补月日疆界。'}
for n in range(37,44):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
    if n in reviews:ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(37,44):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=890,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(37,44)],next_paragraph='zztj-v258-y0891-p001',coverage='卷258大顺元年第37—43段连续录入；本年结束，后接891年。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
