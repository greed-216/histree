"""Curate consecutive Tongjian volume 256, year 885 paragraphs 21–30."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 31))
B = {'format_version': 1, 'batch_key': 'zztj-v256-y0885-p021-p030', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-256-884'
prior = json.loads((ROOT / 'content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json').read_text())
B['sources'] = [next(s for s in prior['sources'] if s['key'] == source)]
raw = (ROOT / 'resources/derived/tongjian/256.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/256.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','郭禹':'成汭'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_256_0885_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷256·光启元年（885）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=['郭禹'] if name=='成汭' else [],era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷256光启元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=885,note=None,quote=None):
    key='event_zztj_256_0885_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_256_0885_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('wang_chongrong_petitions','王重荣拒赴兖州，上表指责田令孜',21,'光启元年七月后条；具体日未载','河中、兖州',
      '王重荣不肯赴泰宁镇，多次上表指责田令孜离间君臣、列举其十罪；田令孜联络朱玫、李昌符与之抗衡。',
      [('王重荣','拒赴新镇及上表者'),('田令孜','被王重荣指责者'),('朱玫','田令孜联络者'),('李昌符','田令孜联络者')],
      note='“十罪”是王重荣表章中的指控；兖州为泰宁新任地，并非已经到任。')
event('wang_chucun_jinzhou','王处存赴河中受阻，返义武',21,'光启元年八月','晋州、易定',
      '王处存上表以卢龙、成德军新退为由请留守易定；朝廷催赴河中。八月他率军到晋州，刺史冀君武闭城不纳，遂返回。',
      [('王处存','奉诏赴镇而受阻者'),('冀君武','闭城者')],
      note='王处存上表关于王重荣“无罪”是其主张；实际行军到晋州后未赴河中任。')
event('ma_shuang_rebellion','马爽举兵请诛奚忠信，兵溃后被杀',22,'光启元年八月后条；具体日未载','邢州南、魏州',
      '马爽与奚忠信不和，在邢州南起兵并胁孟方立诛奚忠信；马爽兵溃逃魏州，奚忠信使人贿乐彦祯杀之。',
      [('马爽','举兵及被杀者'),('奚忠信','被要求诛杀及贿杀者'),('孟方立','被胁请诛奚忠信者'),('乐彦祯','受贿杀马爽者')])
event('chenzhou_resistance','赵犨守陈州，秦宗权未能攻下',23,'光启元年条；攻守确日未载','陈州',
      '《通鉴》称秦宗权攻陷邻道多州，陈州刺史赵犨持续抗拒，秦宗权未能使其屈服。',
      [('秦宗权','攻陈州者'),('赵犨','守陈州者')],
      note='攻邻道二十余州为本段总述，不能把每一州陷落均定在885年。')
event('zhao_chou_caizhou','赵犨获任蔡州节度使',23,'陈州防御期间；具体日未载','蔡州、陈州',
      '朝廷任赵犨为蔡州节度使。',[('赵犨','受任者')])
event('zhao_zhu_marriage','赵犨与朱全忠结婚姻',23,'获朱全忠援助后；具体日未载',None,
      '赵犨感念朱全忠援助，与其结成婚姻关系，朱全忠调发时赵犨及时响应。',
      [('赵犨','结亲及响应者'),('朱温','以朱全忠名义结亲及调发者')],
      note='原文只称“与全忠结婚”，未载婚配双方姓名或辈分；不补具体婚姻对象。')
rel='relationship_'+people['赵犨']+'_'+people['朱温']+'_姻亲'
B['person_relationships'].append(dict(key=rel,person_a_key=people['赵犨'],person_b_key=people['朱温'],relation_type='姻亲',description='《通鉴》卷256称赵犨与朱全忠“结婚”；具体婚配成员未载。',status='draft'))
claim('person_relationship',rel,'description','赵犨与朱全忠结婚姻，具体婚配成员未载。',23,'犨德硃全忠之援，与全忠结婚')
event('wang_xu_mother_order','王绪欲诛王潮之母，因将士求情而放过',24,'王绪行至漳州时；具体日未载','漳州',
      '王绪因道路艰险粮少，禁止军中携带老弱；王潮兄弟仍扶母董氏同行。王绪欲斩董氏，王潮兄弟求先死，将士也求情，董氏得免。',
      [('王绪','下令及拟处死者'),('王潮','护母请死者'),('董氏（王潮母）','被拟处死者')],
      note='本段只具名王潮，另两位兄弟不据后世资料在此冒名。')
rel='relationship_'+people['董氏（王潮母）']+'_'+people['王潮']+'_母子'
B['person_relationships'].append(dict(key=rel,person_a_key=people['董氏（王潮母）'],person_b_key=people['王潮'],relation_type='母子',description='《通鉴》卷256称董氏为王潮兄弟之母。',status='draft'))
claim('person_relationship',rel,'description','董氏为王潮之母。',24,'王潮兄弟扶其母董氏崎岖从军')
event('wang_xu_purge','王绪疑忌部将，刘行全亦死',24,'行军至南安前；具体日未载',None,
      '《通鉴》记王绪因望气者言军中有王者气，遂杀勇略或体貌出众的将卒；刘行全亦死，军中惶惧。',
      [('王绪','疑忌并杀部下者'),('刘行全','死于此期间者')],
      note='原文未逐字说明刘行全死法，保留“亦死”，不加具体刑杀经过。')
event('wang_chao_seizes_command','王潮在南安擒王绪，被推为军将',24,'行军至南安时；具体日未载','南安',
      '王潮说服前锋将，设伏于竹林中擒获王绪；军中相推让，最终奉王潮为将军。',
      [('王潮','谋划擒王绪及被推者'),('王绪','被擒者')],
      note='前锋将未记姓名，不建立具名实体；本段仅记王绪被擒，未记其死亡。')
event('wang_chao_quanzhou','王潮率军围泉州',24,'南安夺军权后；具体日未载','沙县、泉州',
      '王潮原拟率兵回光州，至沙县时张延鲁等泉州人请求留下对付泉州刺史廖彦若，王潮遂领兵围泉州。',
      [('王潮','率兵围城者'),('张延鲁','请求留军者'),('廖彦若','时任泉州刺史')],
      note='张延鲁等指廖彦若贪暴是请兵者之言，不据此独立断定其全部政绩。')
event('chen_jingxuan_september','陈敬瑄获任三川及峡内军政职',25,'光启元年九月戊申','三川及峡内诸州',
      '朝廷任陈敬瑄为三川及峡内诸州指挥、制置等使。',[('陈敬瑄','受任者')])
event('chen_ru_killed','张瑰杀赵匡和陈儒',26,'光启元年九月后条；具体日未载','荆南',
      '蔡州军围荆南，赵匡谋带前节度使陈儒出城，张瑰发现后杀赵匡和陈儒。',
      [('张瑰','杀人者'),('赵匡','被杀者'),('陈儒','被杀者')])
event('bajiao_battle','秦宗权在八角击败朱全忠',27,'光启元年十月癸丑','八角',
      '秦宗权在八角击败朱全忠。',[('秦宗权','获胜者'),('朱温','以朱全忠名义战败者')])
event('wang_requests_li','王重荣请李克用援助',28,'八角战后、十一月前；具体日未载','河中',
      '王重荣向李克用求援，劝其先消除朝廷近侧对手，再与朱全忠作战。李克用上表称朱玫、李昌符与朱全忠共同威胁自己，并说明将来出兵打算；朝廷多次遣使劝解。',
      [('王重荣','求援及劝说者'),('李克用','受求援及上表者'),('朱玫','李克用奏表指控对象'),('李昌符','李克用奏表指控对象'),('朱温','以朱全忠名义受指控者')],
      note='李克用关于共同谋害和“十五万”兵数是其表章说法，不直接作为已证兵力与密谋事实。')
event('zhu_mei_false_flag','朱玫派人扰乱京师并嫁祸李克用',28,'王重荣求援后；具体日未载','长安',
      '《通鉴》记朱玫遣人潜入京城，焚烧储物或刺杀近侍，声称为李克用所为，导致京城恐慌。',
      [('朱玫','遣人行事者'),('李克用','被嫁祸者')],
      note='“声云克用所为”是嫁祸说辞，与叙述中的遣人者分层。')
event('shayuan_standoff','田令孜遣朱玫等屯沙苑讨王重荣',28,'光启元年十一月前后','沙苑、河中',
      '田令孜遣朱玫、李昌符率本军及神策诸军屯沙苑讨王重荣。王重荣发兵抵御并再次请李克用援助，李克用率军赶来。',
      [('田令孜','遣军者'),('朱玫','沙苑军统领'),('李昌符','沙苑军统领'),('王重荣','抵抗者'),('李克用','赴援者')],
      note='原文对各军“三万人”是书载数字，不合计或推为全部实到兵力。')
event('tongzhou_battle','王重荣部攻同州，郭璋战死',28,'光启元年十一月','同州',
      '王重荣遣兵攻同州，刺史郭璋出战失败身死。',
      [('王重荣','遣兵者'),('郭璋','战败身死者')])
event('shayuan_battle','李克用、王重荣在沙苑击败朱玫、李昌符',28,'光启元年十二月癸酉','沙苑',
      '李克用与王重荣军在沙苑交战，朱玫、李昌符战败退回本镇；溃军沿途焚掠。此前双方相持一个多月，朝廷和解诏令未被李克用接受。',
      [('李克用','参战获胜者'),('王重荣','参战获胜者'),('朱玫','战败者'),('李昌符','战败者')],
      note='“月馀”仅说明相持时长，不据此反推精确开始日。')
event('emperor_flees_fengxiang','田令孜奉僖宗出长安奔凤翔',28,'光启元年十二月乙亥夜','长安、凤翔',
      '李克用军进逼京城；田令孜奉皇帝夜出开远门，前往凤翔。',
      [('李克用','军队进逼者'),('田令孜','奉驾出走者')])
event('changan_burned_again','长安在兵乱中再次遭焚掠',29,'光启元年十二月车驾出奔前后','长安',
      '《通鉴》追述黄巢退后长安已多次被焚掠，王徽多年补葺；至此次兵乱，宫室及城中建筑再次被乱兵焚掠。',
      [('王徽','此前修缮者')],
      note='“初”后的黄巢退兵、诸道兵旧掠为背景；本事件只记本次再次焚掠。')
event('hezhong_huguo','河中军获赐号护国',30,'光启元年是岁；具体月日未载','河中',
      '朝廷赐河中军号“护国”。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(21,31):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {21:'王重荣、王处存奏表为各自主张；调任令与实际到任分开。',23:'秦宗权侵多州为范围不明总述；赵犨与朱全忠结婚姻，不补婚配双方。',24:'王潮两位兄弟和前锋将未具名，不补名；王绪只记被擒。',28:'表章主张、京师嫁祸、沙苑战事及车驾出奔分录；兵数不推为实到。',29:'“初”段旧事为背景，本次焚掠另记。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(21,31):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=256,year=885,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(21,31)],next_paragraph='zztj-v256-y0886-p001',coverage='卷256光启元年条最后十段；全卷885年30段至此覆盖。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
