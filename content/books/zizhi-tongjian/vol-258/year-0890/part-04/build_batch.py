"""Curate consecutive Tongjian volume 258, year 890 paragraphs 21–28."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 44))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0890-p021-p028', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_258_0890_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·大顺元年（890）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('zhang_leaves_capital','张浚出师，昭宗安喜楼饯行',21,'890年五月壬子','京师、安喜楼',
      '张浚率诸军及邠、宁、鄜、夏部众出京师，昭宗在安喜楼饯行。张浚私言先除外忧再除内患，杨复恭偷听得知。',
      [('张浚','出师及私言者'),('唐昭宗','饯行者'),('杨复恭','窃听者')],note='五十二都、合五万为史载编制与规模，不独立核实。除内患为张浚意图，不记为已发生内廷清洗。')
event('yang_zhang_farewell_dispute','张浚杨复恭长乐坂饯席交锋',21,'890年五月壬子条；出师时','长乐坂',
      '两军中尉在长乐坂饯张浚，杨复恭劝酒，张浚以醉辞；两人言语相讥，杨复恭更加忌恨张浚。',
      [('张浚','辞酒回应者'),('杨复恭','劝酒讥言者')],note='底本长乐坂依原文保留；对情绪与意图的叙述不推成战争结果。')
event('li_hanzhi_stripped','朝廷削夺李罕之官爵',21,'890年五月癸丑','',
      '朝廷削夺李罕之官爵。',[('李罕之','被削夺者')])
event('sun_kui_zhaoyi','孙揆任昭义节度使兼招讨副使',21,'890年六月','昭义',
      '朝廷以孙揆为昭义节度使，充招讨副使。',[('孙揆','节度使及副使受任者')],note='授职不等于已抵潞州或已实控昭义。')
event('li_jichang_slain','李继昌援成都被王建击斩',22,'890年六月丁巳至己未','成都方向',
      '茂州刺史李继昌率众救成都，王建在己未击败并斩杀李继昌。',
      [('李继昌','援救被斩者'),('王建','击斩者')],note='具体交战地点未载，不把成都方向写成已入成都。')
event('xie_congben_surrenders','谢从本杀张承简举雅州降王建',22,'890年六月辛酉','雅州',
      '资简都制置应援使谢从本杀雅州刺史张承简，举城投降王建。',
      [('谢从本','杀刺史降城者'),('张承简','被杀刺史'),('王建','受降者')])
event('sun_ru_seeks_peace','孙儒求好，朱全忠表请授淮南节度使',23,'890年六月条；具体日未载','',
      '孙儒向朱全忠求好，朱全忠上表请其为淮南节度使。',
      [('孙儒','求好及被表请者'),('朱温','以朱全忠名义表请者')],note='求好与表请分别依原文，不推成朝廷已诏授或永久同盟。')
event('zhu_kills_sun_envoy','朱全忠杀孙儒使者再度交恶',23,'求好后未几；具体年日未载','',
      '朱全忠不久杀孙儒使者，两人再为仇敌。',[('朱温','以朱全忠名义杀使者者'),('孙儒','使者被杀一方')],year=None,note='未几只记相对时间，未据此强定确年；使者未具名，不创人物。')
event('lu_yanwei_background','卢彦威光启末逐杨全玫自称留后',24,'光启末；具体年未载','德州、义昌',
      '德州刺史卢彦威在光启末驱逐义昌节度使杨全玫，自称留后并求旌节，朝廷未准。',
      [('卢彦威','逐帅自称及求节者'),('杨全玫','被逐者')],year=None,note='光启末不擅定某年，自称留后不记为朝廷授节。')
event('lu_yanwei_yichang','王镕罗弘信代请，卢彦威获义昌节度使',24,'890年六月条；张浚用兵时','义昌',
      '王镕、罗弘信趁张浚用兵，为卢彦威请求旌节，朝廷遂以卢彦威为义昌节度使。',
      [('王熔','按王镕同人代请者'),('国弘信','按罗弘信同人代请者'),('卢彦威','节度使受任者')],note='底本王熔、国弘信与维基文库卷258王鎔、羅弘信对读，按既有同人复用，保留原字；不是另建王熔或国弘信。')
event('zhang_meets_armies_jin','张浚会诸镇军于晋州',25,'890年六月后条；具体日未载','晋州',
      '张浚在晋州会合宣武、镇国、静难、凤翔、保大、定难诸军。',[('张浚','会军统帅')],note='军镇名为会军单位，不给未具名将帅补角色。')
event('yicheng_renamed_xuanyi','义成军改名宣义',26,'890年六月条；具体日未载','义成军',
      '朝廷将义成军更名为宣义。',note='军号更改不等于迁治或新得领土。')
event('zhu_dual_commands','朱全忠任宣武宣义节度使',26,'890年六月辛未','宣武、宣义',
      '朝廷以朱全忠为宣武、宣义节度使。',[('朱温','以朱全忠名义两镇节度使受任者')])
event('hu_zhen_xuanyi','朱全忠辞宣义请胡真，朝廷从之',26,'890年六月辛未条后','宣义',
      '朱全忠因正有事徐、杨，认为征兵遣戍范围辽阔，辞宣义，请以胡真为节度使，朝廷同意。胡真任内，赋出入仍受朱全忠控制。',
      [('朱温','以朱全忠名义辞任表请及控赋者'),('胡真','宣义节度使受任者')],note='赋出入控制依书载叙述，不推胡真所有军政行为均为朱全忠授意。')
event('zhu_dual_commands_later','胡真入统军后朱全忠复兼两镇',26,'胡真入为统军后；具体年日未载','宣武、宣义、淮南',
      '胡真入为统军后，朱全忠最终兼任宣武、宣义两镇节度使，不再领淮南。',
      [('胡真','入为统军者'),('朱温','以朱全忠名义复兼两镇者')],year=None,note='及、竟标记后事，未明记确年，不将这一任命并入六月辛未授职。')
event('government_yindiguan','官军抵阴地关',27,'890年七月','阴地关',
      '讨河东官军抵达阴地关。',note='本句官军未单指某将，不把张浚列为已亲抵此关的直接证据。')
event('ge_congzhou_enters_lu','葛从周夜入潞州援守军',27,'890年七月','壶关、潞州',
      '朱全忠遣葛从周率骑兵，潜自壶关夜抵潞州，冲破围军进入城内。',
      [('朱温','以朱全忠名义遣援者'),('葛从周','夜入援将领')],note='千骑为书载规模，潜行只保存史载地点，不绘精确路径。')
event('zhu_attacks_ze_supports_lu','李谠等攻泽州，张全义朱友裕应援',27,'890年七月','泽州、泽州北',
      '朱全忠遣李谠、李重胤、邓季筠攻泽州李罕之，又遣张全义、朱友裕驻军泽州北，应援葛从周。《通鉴》称邓季筠为下邑人。',
      [('朱温','以朱全忠名义遣军者'),('李谠','进攻将领'),('李重胤','进攻将领'),('邓季筠','进攻将领'),('李罕之','被攻者'),('张全义','应援将领'),('朱友裕','应援将领'),('葛从周','被应援将领')])
event('sun_kui_sent_lu','张浚分兵令孙揆赴潞州',27,'890年七月后条；八月发晋州前','潞州方向',
      '朱全忠上奏请孙揆赴镇，张浚亦担忧昭义为汴军所据，分兵令孙揆率往潞州。',
      [('朱温','以朱全忠名义奏请者'),('张浚','分兵遣赴者'),('孙揆','受遣赴镇者')],note='二千为书载人数；张浚担忧为书中解释，不把担忧写成汴军已永久取得昭义。')
event('sun_kui_captured','李存孝伏长子擒孙揆韩归范',27,'890年八月乙丑','晋州、长子西谷、刁黄岭',
      '孙揆自晋州出发，李存孝在长子西谷设伏，俘获孙揆、赐旌节中使韩归范及牙兵，追杀余众至刁黄岭。',
      [('孙揆','赴镇被俘者'),('李存孝','伏击俘获者'),('韩归范','赐节中使被俘者')],note='三百骑、牙兵五百余为书载数，尽杀余众为书中叙述；不补孙揆当日死亡。')
event('sun_kui_paraded','李存孝徇孙揆韩归范于潞州城下',27,'孙揆被俘后；具体日未载','潞州城下',
      '李存孝械系孙揆、韩归范，在潞州城下展示，讥令葛从周速归使孙揆赴任，随后送交李克用。',
      [('李存孝','示俘送俘者'),('孙揆','被示俘者'),('韩归范','被示俘者'),('葛从周','被讥言对象'),('李克用','接收俘虏者')],year=None,note='底本两处纟斥残字保留，不猜具体绑束方式；讥言不是实际赴任诏令。')
event('sun_kui_refuses_dies','孙揆拒李克用任用而遇害',27,'被俘后既而；具体年日未载','',
      '李克用囚孙揆后，试图诱其任河东副使，孙揆拒绝。李克用命用锯处死孙揆，书载其至死骂不绝声。',
      [('李克用','诱任及命杀者'),('孙揆','拒任遇害者')],year=None,note='既而不补确日与杀人地点；拒任及临死言语按书载保留，不将其写成当日赴镇死亡。')
event('sun_ru_attacks_runzhou_890','孙儒进攻润州',28,'890年八月丙寅','润州',
      '孙儒进攻润州。',[('孙儒','进攻者')],note='本段只记攻，不预记已攻取。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={21:'五月出师、饯席言语、李罕之削爵与六月孙揆授职分录。',22:'丁巳援兵、己未斩李继昌、辛酉谢从本杀张承简降雅州按日顺序。',23:'求好表请不等于授职，未几杀使另用未定年。',24:'光启末追叙不给确年；王熔国弘信对读王鎔羅弘信归已有同人，底本不改。',26:'更军号、辛未两镇任命、辞宣义任胡真及后事分录；及胡真入统军未定年。',27:'七月救潞与泽州攻势、分兵赴镇、八月伏击与巡俘、既而拒诱遇害分录；纟斥残字不猜绑束法。',28:'攻润州不记已得。'}
for n in range(21,29):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
    if n in reviews:ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(21,29):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=890,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(21,29)],next_paragraph='zztj-v258-y0890-p029',coverage='卷258大顺元年第21—28段连续录入；本年未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
