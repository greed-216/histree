"""Curate consecutive Tongjian volume 257, year 888 paragraphs 1–8."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 50))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0888-p001-p008', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎'}
people, used, reused = {}, {}, set()

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_257_0888_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·文德元年（888）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('sun_ru_kills_qin_bi_zheng','孙儒杀秦彦毕师铎郑汉章',1,'888年正月甲寅','广陵',
      '孙儒因唐宏诬告秦彦等暗召汴军而杀秦彦、毕师铎、郑汉章，任唐宏为马军使。',
      [('孙儒','下令杀人及任命者'),('唐宏','诬告及受任者'),('秦彦','被杀者'),('毕师铎','被杀者'),('郑汉章','被杀者')],
      note='“潜召汴军”是唐宏的诬告，不能当作秦彦等已实施的事实；本段还追叙其部众先被孙儒渐夺。')
event('zhang_shouyi_killed','杨行密杀张守一',2,'888年正月；具体日未载','广陵',
      '张守一此前与吕用之一同归杨行密，此后为诸将炼仙丹，并欲干预军府政务；杨行密怒而将其杀死。',
      [('张守一','被杀者'),('杨行密','处置者'),('吕用之','此前共同归附者')],
      note='“此前同归”是追叙，不推为吕用之此时仍在世。')
event('zhu_captures_shi_fan','朱全忠遣军擒石璠',3,'888年正月；癸亥前','陈州、亳州方向',
      '石璠率蔡军侵陈、亳，朱全忠遣朱珍、葛从周率骑军迎击并俘石璠。',
      [('石璠','进犯及被俘者'),('朱温','以朱全忠名义遣将者'),('朱珍','迎击者'),('葛从周','迎击者')],
      note='两军兵额均为书载概数。')
event('zhu_cai_campaign_commander','朝廷任朱全忠蔡州四面行营都统',3,'888年正月癸亥','蔡州方向',
      '朝廷任朱全忠为蔡州四面行营都统，代替时溥，诸镇军归其节度。',
      [('朱温','以朱全忠名义受任者'),('时溥','被替代者')])
event('zhang_tingfan_reports_yang','张廷范赴广陵后密报朱全忠',4,'888年正月甲子前','广陵',
      '张廷范到广陵受杨行密礼遇；杨行密听说李璠将来任留后后不悦。张廷范密报朱全忠，建议亲率大军赴镇。',
      [('张廷范','赴广陵及密报者'),('杨行密','接待及不悦者'),('李璠','拟任留后者'),('朱温','以朱全忠名义受密报者')],
      note='张廷范与前段传朝命的“张延范”职责、行程连续，暂复用人物键，原文字形差异保留待核。')
claim('person',people['张延范'],'aliases','传命使姓名前作张延范，此段作张廷范。',4,
      note='据相邻两段同一赴淮南行程暂合并；若异本证明不同人，可拆分。')
event('zhu_abandons_huainan_trip','朱全忠停止赴淮南',4,'888年正月甲子','宋州',
      '朱全忠行至宋州，张廷范从广陵返称杨行密难图；甲子李璠也报告徐军阻道，朱全忠遂停止赴镇。',
      [('朱温','以朱全忠名义停止进军者'),('张廷范','返报者'),('李璠','报告者'),('杨行密','报告中所涉淮南主事者')],
      note='未发生朱全忠接管淮南；张廷范所言、李璠所言均按原文归属发言者。')
event('qian_executes_xue_lang','钱镠杀薛朗祭周宝',5,'888年正月丙寅','杭州',
      '钱镠斩薛朗，以其心祭周宝。',
      [('钱镠','下令处置者'),('薛朗','被杀者'),('周宝','受祭者')])
event('ruan_jie_runzhou','钱镠任阮结润州制置使',5,'888年正月丙寅','润州',
      '钱镠任阮结为润州制置使。',
      [('钱镠','任命者'),('阮结','受任者')])
event('zhu_petitions_yang_huainan','朱全忠奏杨行密为淮南留后',6,'888年二月；具体日未载','淮南',
      '朱全忠向朝廷奏请任杨行密为淮南留后。',
      [('朱温','以朱全忠名义上奏者'),('杨行密','被举荐者')],
      note='原文“奏以”，只记奏请，不推定任命已完成。')
event('emperor_ill_and_returns','僖宗病中自凤翔返长安',7,'888年二月乙亥至己丑','凤翔、长安',
      '皇帝乙亥身体不适，壬午离凤翔，己丑抵长安。',
      note='本段称“上”，据卷年帝系为唐僖宗；不从这段推定病名。')
event('emperor_amnesty_era','僖宗赦天下并改元',7,'888年二月庚寅','长安',
      '皇帝赦天下并改元，任韦昭度兼中书令。',
      [('韦昭度','兼中书令受任者')],
      note='“改元”照原文，具体新年号由卷首“文德元年”标示；不自行换算公历日。')
event('le_yanzhen_forced_labor','乐彦祯征民筑魏博罗城',8,'888年前；具体年日未载','魏博',
      '《通鉴》追叙乐彦祯令六州民众筑罗城，百姓苦于劳役；其子乐从训聚私兵，牙兵因而疑惧。',
      [('乐彦祯','征发民众者'),('乐从训','聚私兵者')],year=None,
      note='段首为人物与局势背景，筑城和聚兵起始年份未载，不强置888年。')
event('le_yanzhen_steps_down','乐彦祯避位居寺，魏军推留后',8,'乐从训私兵引发猜疑后；具体年日未载','魏州龙兴寺',
      '乐彦祯因牙兵猜疑而请避位，至龙兴寺为僧；军中推都将代理留后。',
      [('乐彦祯','避位者')],
      note='代理留后姓名在底本作“赵文弁”，字形未核，不据此建立具名人物；原文未给明确干支。')
event('wei_troops_choose_luo','魏博军杀代理留后改推罗弘信',8,'乐彦祯避位后；具体日未载','魏州',
      '乐从训率军逼魏州，代理留后未出战，被军众杀害；牙兵另推罗弘信代理留后。',
      [('乐从训','率军逼城者'),('罗弘信','受推留后者')],
      note='被杀者姓名底本乱码，不创建确定人名；“白须翁”传言为拥立时的说辞，不作为神异事实。')
event('luo_defeats_le_congxun','罗弘信败乐从训并围内黄',8,'罗弘信受推后；具体日未载','魏州、内黄',
      '罗弘信率军击败乐从训；乐从训退守内黄，魏军围城。',
      [('罗弘信','击败及围城者'),('乐从训','退守者')])

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(1,9):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {1:'唐宏诬告不是秦彦等已召汴军的事实。',2:'吕用之此前已死，“同归”是追叙。',4:'张廷范与前段张延范暂合并，字形差异待异本校核；朱全忠最终未赴镇。',5:'薛朗887年被擒、888年才被杀，分年处理。',6:'“奏以”只记奏请。',7:'二月皇帝病、返长安、赦及改元分录；病名未载。',8:'筑城聚兵为未定年追叙；代理留后姓名乱码不建人；传言不作神异事实。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=888,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph='zztj-v257-y0888-p009',coverage='卷257文德元年条第1—8段；本年续录。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
