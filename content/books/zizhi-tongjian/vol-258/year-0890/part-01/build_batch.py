"""Curate consecutive Tongjian volume 258, year 890 paragraphs 1–8."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 44))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0890-p001-p008', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias = {'杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, set()

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0890_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·大顺元年（890）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('zhaozong_title_dashun','群臣上昭宗尊号，改元大顺',1,'890年正月戊子朔','',
      '群臣上尊号圣文睿德光武弘孝皇帝，朝廷改元大顺。',[('唐昭宗','受尊号及改元者')],note='尊号与改元依年首；不把尊号作为新人物名称。')
event('meng_qian_surrenders','孟迁执王虔裕及汴兵降李克用',2,'890年正月；具体日未载','邢州',
      '李克用急攻邢州，孟迁粮尽力竭，拘执王虔裕及汴兵投降。',
      [('李克用','攻城受降者'),('孟迁','拘援兵投降者'),('王虔裕','被拘将领')],note='王虔裕被拘未见本段遇害，不提前补卒年。')
event('an_jinjun_xingming','安金俊受任邢洺团练使',2,'890年正月；孟迁降后','邢州、洺州',
      '李克用以安金俊为邢洺团练使。',[('李克用','任用者'),('安金俊','团练使受任者')])
event('wang_attacks_qiong','王建攻邛州，陈敬瑄遣杨儒助守',3,'890年正月壬寅','邛州',
      '王建进攻邛州，陈敬瑄遣大将杨儒率军帮助刺史毛湘守城，毛湘出战屡败。',
      [('王建','攻城者'),('陈敬瑄','遣援军者'),('杨儒','原名杨儒的助守将领'),('毛湘','出战败方刺史')],note='杨儒在本段后改名王宗儒，复用同一主体；书载援军三千，未独立核实。')
claim('person',people['王宗儒'],'biography','《通鉴》称杨儒为彭城人。',3,quote='陈敬瑄遣其大将彭城杨儒将兵三千')
event('yang_ru_surrenders_adopted','杨儒降王建，被养为子赐名王宗儒',3,'890年正月壬寅条；邛州战中','邛州',
      '杨儒见王建军势盛，称唐祚将尽、王建治众严而不残，率部投降；王建收养其为子，改姓名为王宗儒。',
      [('王宗儒','原杨儒投降及受收养者'),('王建','受降及收养赐名者')],note='唐祚尽、可庇民为杨儒评价，不当作编者判断；收养与改名不复制人物。')
rk='relationship_person_王建_person_王宗儒_养父'
B['person_relationships'].append(dict(key=rk,person_a_key=people['王建'],person_b_key=people['王宗儒'],relation_type='养父',description='890年邛州战事中，王建收降将杨儒为养子并赐名王宗儒；王建是王宗儒的养父。',status='draft'))
claim('person_relationship',rk,'description','王建是王宗儒的养父。',3,quote='遂帅所部出降。建养以为子，更其姓名曰王宗儒。')
claim('person',people['王宗儒'],'aliases','王宗儒原名杨儒，由王建收养后改姓名。',3,quote='遂帅所部出降。建养以为子，更其姓名曰王宗儒。')
event('zhang_lin_qiongnan','王建留张琳招安邛南，回兵成都',3,'890年正月乙巳','邛南、成都',
      '王建留永平节度判官张琳为邛南招安使，率兵返回成都。《通鉴》称张琳为许州人。',
      [('王建','任用及回兵者'),('张琳','招安使受任者')])
event('chen_fortifies_chengdu','陈敬瑄布寨征丁修守成都',3,'890年正月条；具体日未载','犀浦、郫、导江、成都',
      '陈敬瑄分兵在犀浦、郫、导江等县布寨，征城中民户一丁，白日开壕采竹木运砖石，夜间登城巡警，昼夜无休。',
      [('陈敬瑄','布寨征役者')],note='原文每户一丁，不扩为总人数；描述书载民役负担，不绘精确城防范围。')
event('wei_wang_camps','韦昭度王建分别驻营唐桥东阊门外',4,'890年正月；具体日未载','唐桥、东阊门外',
      '韦昭度驻营唐桥，王建驻营东阊门外；《通鉴》称王建事韦昭度甚谨。',
      [('韦昭度','唐桥驻营者'),('王建','东阊门外驻营者')],note='谨慎事奉为书载评价，不推为永久统属。')
event('du_youqian_surrenders_jian','杜有迁执员虔嵩降王建并知简州',4,'890年正月辛亥','简州',
      '简州将杜有迁拘执刺史员虔嵩，投降王建；王建以杜有迁知州事。',
      [('杜有迁','执刺史投降及知州者'),('员虔嵩','被执刺史'),('王建','受降及任用者')])
event('pang_takes_tianchang','庞师古渡淮声称救杨行密，取天长',5,'890年正月；具体日未载','淮、天长',
      '庞师古等汴军渡淮，声称救援杨行密，攻取天长；其军号称十万。',
      [('庞师古','渡淮攻城将领'),('杨行密','汴军声称救援对象')],note='十万为号称，救援为声言，不据此建立同盟或实数兵额。')
event('pang_takes_gaoyou','庞师古攻取高邮',5,'890年正月壬子','高邮',
      '庞师古等汴军攻取高邮。',[('庞师古','攻城将领')])
event('hou_yuanchuo_surrenders_zi','侯元绰执杨戡降王建并知资州',6,'890年二月己未','资州',
      '资州将侯元绰拘执刺史杨戡，投降王建；王建以侯元绰知州事。',
      [('侯元绰','执刺史投降及知州者'),('杨戡','被执刺史'),('王建','受降及任用者')])
event('zhu_guarding_zhongshu','朱全忠加守中书令',7,'890年二月乙丑','',
      '朝廷加朱全忠守中书令。',[('朱温','以朱全忠名义加官者')],note='保留“守”官衔用语，不与前年的兼中书令重复为同一事件。')
event('pang_lingting_defeat','庞师古败于孙儒退还',8,'890年二月己巳','陵亭、淮南',
      '庞师古率兵深入淮南，在陵亭与孙儒交战，兵败后返回。',
      [('庞师古','战败退还者'),('孙儒','对战将领')],note='不补原文未载的伤亡数字与返回目的地。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={2:'孟迁降及安金俊任用分录；王虔裕被执未推死。',3:'杨儒与王宗儒一人；收养赐名明示，养父由王建指向王宗儒；评价归杨儒；张琳任用回兵、陈敬瑄征役分别录入。',5:'十万为号称、救杨行密为声言，不创同盟。',7:'守中书令保留职衔，不与889年加官事件合并。'}
for n in range(1,9):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
    if n in reviews:ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=890,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph='zztj-v258-y0890-p009',coverage='卷258大顺元年第1—8段连续录入；本年共43段未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
