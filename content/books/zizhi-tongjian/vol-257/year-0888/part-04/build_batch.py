"""Curate consecutive Tongjian volume 257, year 888 paragraphs 25–32."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 50))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0888-p025-p032', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_257_0888_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·文德元年（888）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('zhu_besieges_cai','朱全忠败秦宗权围蔡州',25,'888年五月至六月前；具体日未载','蔡州',
      '朱全忠大举攻秦宗权，于蔡州南击败其军、攻取北关门；秦宗权守中州，朱全忠分兵列二十八寨包围。',
      [('朱温','以朱全忠名义进攻及围城者'),('秦宗权','守城者')],
      note='“既得洛、孟”是本段行动背景，不据此另造同日夺取事件；寨数照原文。')
event('li_maozhen_jianjiao','李茂贞加检校侍中',26,'888年五月至六月前；具体日未载','凤翔',
      '朝廷加凤翔节度使李茂贞检校侍中。',
      [('李茂贞','受任者')])
event('wang_jian_sichuan_stalemate','王建陈敬瑄相攻，王建议借朝命',27,'888年五月至六月前；具体日未载','成都、西川',
      '陈敬瑄与王建交战，西川贡赋中断。王建一度想罢兵，周庠、綦毋谏反对；王建决定请朝廷派大臣主持西川事务。',
      [('陈敬瑄','交战一方'),('王建','交战及请朝命一方'),('周庠','劝谏者'),('綦毋谏','劝谏者')],
      note='周庠关于邛州可据数年的说法和王建关于军心的判断均是谋议，不当作未来结果。')
event('wang_jian_gu_petitions','王建与顾彦朗分别上表朝廷',27,'888年五月至六月前；具体日未载','西川、东川、朝廷',
      '王建使周庠起草奏表，请求讨陈敬瑄并求邛州；顾彦朗也上表请求赦免王建、调陈敬瑄他镇。',
      [('王建','奏请者'),('周庠','起草奏表者'),('陈敬瑄','奏表所涉者'),('顾彦朗','另行奏请者')],
      note='奏表请求与朝廷准许分开，不能把求邛州记为已经获授。')
event('shouwang_tian_earlier','寿王李杰昔随僖宗入蜀时受田令孜鞭责',28,'黄巢之乱时；具体年日未载','赴蜀山道',
      '《通鉴》追叙寿王李杰昔随唐僖宗入蜀，行路困顿时向田令孜求马未得，反受其鞭责。',
      [('李杰','当时的寿王'),('唐僖宗','西幸皇帝'),('田令孜','鞭责者')],year=None,
      note='段首“初”是较早背景，不归为888年事件；“心衔之”是史书对寿王情绪的叙述。')
event('zhaozong_sends_supervisor','昭宗遣人监西川军遭田令孜拒绝',28,'昭宗即位后至888年六月前','西川',
      '昭宗即位后遣人监督西川军，田令孜不奉诏。',
      [('李杰','以唐昭宗名义遣人者'),('田令孜','不奉诏者')],
      note='监督者未具名，不创建人物；“上言愤籓镇跋扈”疑底本文字，相关动机不扩写。')
event('wei_zhaodu_sichuan','朝廷命韦昭度镇西川并征陈敬瑄',28,'888年六月','西川',
      '朝廷命韦昭度兼中书令、充西川节度使和招抚制置等使，征陈敬瑄为龙武统军。',
      [('李杰','以唐昭宗名义下诏者'),('韦昭度','西川受任者'),('陈敬瑄','被征召者')],
      note='任命和征召只说明朝廷决定，不推为韦昭度已到镇或陈敬瑄已遵命。')
event('wang_jian_recruits_local','王建令王宗瑶招地方武装',29,'888年六月前后；具体日未载','新都、绵竹、安仁',
      '王建屯新都时，绵竹何义阳、安仁费师懃等地方武装自保；王建遣王宗瑶劝说，各部归附并提供粮资，王建军势恢复。',
      [('王建','遣说者及受援者'),('王宗瑶','劝说者'),('何义阳','归附地方统领'),('费师懃','归附地方统领')],
      note='原文“安仁费师懃”把安仁按地名处理；兵数“或万人，少者千人”为书载概数。')
event('youguo_army_created','朝廷置佑国军，任张全义节度使',30,'888年六月前后；具体日未载','河南府',
      '朝廷在河南府设置佑国军，以张全义为节度使。',
      [('张全义','受任者')])
event('li_hanzhi_attacks_heyang','李罕之引河东兵攻河阳被丁会击退',31,'888年七月','河阳',
      '李罕之率河东军攻河阳，丁会击退其军。',
      [('李罕之','进攻者'),('丁会','防守及击退者')])
event('fengzhou_manzun','凤州升节度府，满存受任',32,'888年七月；具体日未载','凤州、兴州、利州',
      '朝廷将凤州升为节度府，划兴、利二州隶属，任凤州防御使满存为节度使、同平章事。',
      [('满存','受任者')])

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(25,33):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {25:'洛、孟既得为行动背景；蔡州战与围城记为本段事件。',27:'周庠与王建的设想属谋议，王建及顾彦朗的奏请不作已获批准。',28:'“初”寿王赴蜀往事不记888年；六月任命不推为已经交接镇务。',29:'安仁作为费师懃所在地处理；地方兵数为书载。',30:'置军与节度使任命同段。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,33):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=888,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph='zztj-v257-y0888-p033',coverage='卷257文德元年条第25—32段；本年续录。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
