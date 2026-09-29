"""Curate consecutive Tongjian volume 257, year 888 paragraphs 9–16."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 50))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0888-p009-p016', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-257-888'
B['sources'] = [dict(key=source,title='资治通鉴·卷257',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/f3d1c3c15ff4df6cf15204307c37f81ca1275a8a/resources/derived/tongjian/257.txt',note='卷257文德元年起；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/257.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/257.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_257_0888_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·文德元年（888）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷257文德元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=888,note=None,quote=None):
    key='event_zztj_257_0888_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_257_0888_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('lei_ye_sent_and_killed','朱全忠遣雷邺至魏籴粮，雷邺被杀',9,'乐彦祯被逐前后；具体日未载','魏州',
      '朱全忠拟讨蔡州，先遣雷邺携银赴魏州买粮；魏博牙兵逐乐彦祯后，在馆舍杀雷邺。',
      [('朱温','以朱全忠名义遣使者'),('雷鄴','被杀使者'),('乐彦祯','被逐魏博旧帅')],
      note='“先是”追叙遣使，不能都记为888年同日；“银万两”为原文数。')
event('le_congxun_seeks_zhu','乐从训败后向朱全忠求援',9,'乐从训退内黄后；具体日未载','内黄、宣武',
      '乐从训遭魏州军击败后向朱全忠求援。',
      [('乐从训','求援者'),('朱温','以朱全忠名义受求援者')])
event('li_zhang_old_alliance','李罕之张全义昔日结盟',10,'此前；具体年日未载','河阳、河南',
      '《通鉴》追叙李罕之与张全义曾刻臂为盟，起初相处友善。',
      [('李罕之','昔日盟约一方'),('张全义','昔日盟约一方')],year=None,
      note='段首“初”为回叙，盟约具体年份未载；不把两人标为888年仍稳定结盟。')
event('li_hanzhi_extorts_zhang','李罕之屡索张全义粮帛',10,'昔日结盟后至888年前后；具体日期未载','河阳、河南',
      '李罕之屡向张全义索粮帛，不足时拘河南官吏至河阳杖责；张全义尽力供给，河南将佐不满。',
      [('李罕之','索取及责罚者'),('张全义','供给者')],year=None,
      note='此为一段多年关系的总述，未给具体起止年；“贪暴”等属史家评价，不作为可量化事实。')
event('li_hanzhi_jin_jiang','李罕之攻绛州晋州',10,'888年二月至三月前后；具体日未载','绛州、晋州',
      '李罕之率军攻绛州，刺史王友遇投降；继而进攻晋州。',
      [('李罕之','进攻者'),('王友遇','绛州降者')],
      note='“至是”承本年叙事，但本段未标干支日；其部掠夺与食人是原文所记，不扩写规模。')
event('zhang_quanyi_seizes_heyang','张全义趁李罕之攻晋州取河阳',10,'李罕之攻晋州时；具体日未载','河阳、泽州',
      '王重盈秘密与张全义谋划，张全义趁李罕之出兵晋州夜袭河阳，黎明进入三城并俘其家属；李罕之逃泽州，向李克用求援。',
      [('王重盈','密议者'),('张全义','夜袭及取城者'),('李罕之','逃亡求援者'),('李克用','受求援者')],
      note='张全义“兼领河阳节度使”据原文为战后掌控，不推为朝廷即时正式任命。')
event('solar_eclipse','三月戊戌日食',11,'888年三月戊戌朔','',
      '《通鉴》记三月朔日发生日全食。',
      note='原文“日有食之，既”表示食既；不自行给出观测地点或现代天文参数。')
event('xizong_ill_again','唐僖宗病重',12,'888年三月己亥至壬寅','长安',
      '唐僖宗己亥病复作，壬寅病危。',
      [('唐僖宗','病重者')],
      note='本段称“上”，据上下文为唐僖宗；不推定病名。')
event('li_jie_heir','寿王李杰立为皇太弟监军国',12,'888年三月壬寅','长安',
      '群臣曾寄望吉王保；杨复恭请立寿王杰。朝廷下诏立寿王杰为皇太弟、监军国事，刘季述遣兵迎入少阳院。',
      [('李保','曾受群臣期待的吉王'),('杨复恭','请立寿王者'),('李杰','皇太弟受立者'),('刘季述','奉迎者')],
      note='“群臣属望”是原文对继位期待的描述，不推成吉王保曾受正式册立。')
event('xizong_dies','唐僖宗崩于灵符殿',12,'888年三月癸卯','长安灵符殿',
      '唐僖宗在灵符殿去世；遗制令皇太弟李杰改名李敏，以韦昭度摄冢宰。',
      [('唐僖宗','去世者'),('李杰','依遗制改名李敏者'),('韦昭度','摄冢宰者')],
      note='皇太弟“杰更名敏”明确载于本段；李杰、李敏是同一人。')
row=next(x for x in B['people'] if x['key']==people['李杰'])
for name in ['李敏','唐昭宗']:
    if name not in row['aliases']:row['aliases'].append(name)
claim('person',row['key'],'aliases','寿王杰在僖宗遗制中更名敏，即后文昭宗。',12,
      note='李杰、李敏及后文昭宗共用一个人物键；帝号由紧接的下一段印证。')
event('zhaozong_enthroned','唐昭宗即位',13,'唐僖宗崩后；具体日未载','长安',
      '寿王李杰即位为唐昭宗。《通鉴》记其即位初尊礼大臣，试图振兴朝廷。',
      [('李杰','即位者')],
      note='“体貌明粹”等是史书评述，不拆作可核定人物事实；具体即位日未另载。')
event('zhu_sends_two_armies','朱全忠分兵攻蔡救乐从训',14,'888年三月前后；具体日未载','宋州、滑州、蔡州方向、魏博方向',
      '朱全忠在宋州拟讨秦宗权，乐从训求援后移屯滑州，遣李唐宾等攻蔡州，又遣朱珍等救乐从训。',
      [('朱温','以朱全忠名义分兵者'),('乐从训','求援者'),('李唐宾','攻蔡州一路将领'),('朱珍','救乐从训一路将领'),('秦宗权','拟讨目标')],
      note='兵数“三万”为原文概数；两路兵分别指向蔡州与魏博，不合并成同一战斗。')
event('zhu_zhen_defeats_wei','朱珍军入魏博取三镇',14,'分兵救乐从训后；具体日未载','白马、黎阳、临河、李固、内黄',
      '朱珍等军渡白马，取黎阳、临河、李固三镇，至内黄击败魏博军，俘周儒等将领。',
      [('朱珍','进兵一路将领'),('周儒','被俘魏军将领'),('乐从训','受援者')],
      note='“败魏军万余人”“获十人”为原文战争数字，不据此核定总伤亡。')
event('li_keyong_helps_hanzhi','李克用遣康君立等助李罕之攻河阳',15,'888年三月至四月前后；具体日未载','河阳',
      '李克用任康君立为南面招讨使，令其督李存孝、薛阿檀、史俨、安全俊、安休休率骑兵援李罕之，攻河阳。',
      [('李克用','遣军及任命者'),('康君立','统军者'),('李存孝','参战将领'),('薛阿檀','参战将领'),('史俨','参战将领'),('安全俊','参战将领'),('安休休','参战将领'),('李罕之','受援者')],
      note='“骑七千”为原文兵额，不作实点统计。')
event('zhang_quanyi_seeks_zhu','张全义守河阳向朱全忠求援',15,'李克用援军攻河阳时；具体日未载','河阳',
      '张全义守河阳，城中粮尽，向朱全忠求援，以妻子为质。',
      [('张全义','守城及求援者'),('朱温','以朱全忠名义受求援者')],
      note='妻子未具名，不创建独立人物。')
event('wang_jian_attacks_peng','王建攻彭州后劫掠西川',16,'888年四月庚午前；具体日未载','彭州、西川',
      '王建攻彭州，陈敬瑄率军救援后王建退去；《通鉴》又记王建军大掠西川，十二州受害。',
      [('王建','攻城及劫掠方统领'),('陈敬瑄','救援者')],
      note='“十二州”照史书叙述，不据此逐州建未具名事件。')
event('empress_wang_posthumous','朝廷追尊昭宗母王氏',16,'888年四月庚午','长安',
      '朝廷追尊新帝之母王氏为恭宪皇后。',
      [('李杰','受追尊皇后之子')],
      note='“上母王氏”指新帝之母；本段仅记姓氏和追尊号，不另创未消歧人物。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(9,17):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {9:'“先是”遣雷邺为追叙；牙兵杀人与乐从训求援有先后。',10:'“初”盟约及索粮多年总述不硬置888年；夜袭河阳独立录。',11:'只录原文日食，不推现代地点和历日换算。',12:'吉王保仅受期待，寿王杰正式受立并更名敏；僖宗病重与崩逝分录。',13:'昭宗与李杰、李敏同人；即位日未另记。',14:'朱全忠分攻蔡与救魏两路，数字仅书载。',16:'王建袭扰与朝廷追尊皇后是不同事件；王氏未消歧不创具名人物。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,17):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=888,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph='zztj-v257-y0888-p017',coverage='卷257文德元年条第9—16段；本年续录。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
