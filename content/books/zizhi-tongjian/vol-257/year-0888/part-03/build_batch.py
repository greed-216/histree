"""Curate consecutive Tongjian volume 257, year 888 paragraphs 17–24."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 50))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0888-p017-p024', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_257_0888_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·文德元年（888）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('sun_ru_takes_yangzhou','孙儒攻取扬州，杨行密出奔',17,'888年四月壬午','扬州',
      '孙儒袭取扬州，杨行密离城；孙儒自称淮南节度使。',
      [('孙儒','攻取及自称节度使者'),('杨行密','出奔者')],
      note='“自称”不记为朝廷正式任命。')
event('yuan_xi_turns_yang_luzhou','袁袭劝杨行密归庐州',17,'杨行密出扬州后；具体日未载','扬州、庐州方向',
      '杨行密原想奔海陵，袁袭劝其归庐州另谋进取，杨行密采纳。',
      [('杨行密','改定去向者'),('袁袭','进言者')],
      note='此段记采纳计划，未明抵庐州的具体日期。')
event('zhu_aids_heyang','朱全忠遣丁会等援河阳',18,'888年四月；具体日未载','河阳',
      '朱全忠遣丁会、葛从周、牛存节率军援河阳。',
      [('朱温','以朱全忠名义遣援者'),('丁会','援军将领'),('葛从周','援军将领'),('牛存节','援军将领')],
      note='“数万”为原文概数。')
event('heyang_wen_battle','河阳援军击败李存孝等',18,'朱全忠援军抵河阳后；具体日未载','河阳、温、太行路',
      '李存孝率骑兵在温迎战，李罕之率步兵攻城，河东军战败；安休休奔蔡州。汴军拟断太行路，康君立等引兵还。',
      [('李存孝','迎战方骑军统领'),('李罕之','攻城方步军统领'),('安休休','战后出奔者'),('康君立','引兵撤退者'),('朱温','以朱全忠名义援军统领')],
      note='李罕之与李存孝为本次河东一方，不与之前张全义的旧盟关系混用。')
event('zhu_heyang_appointments','朱全忠奏丁会河阳留后、张全义河南尹',18,'河阳战后；具体日未载','河阳、河南',
      '朱全忠奏请丁会为河阳留后，复任张全义为河南尹。',
      [('朱温','以朱全忠名义上表者'),('丁会','被举荐者'),('张全义','被复任者')],
      note='原文“表”说明奏请，不擅认朝廷即时批准。')
event('zhang_quanyi_supplies_zhu','张全义为朱全忠供军粮器',18,'河阳获救后；具体年日未载','河南、宣武方向',
      '张全义感念朱全忠援助，之后朱全忠出战时由张全义供给粮食、器仗。',
      [('张全义','长期供给者'),('朱温','以朱全忠名义受供给者')],year=None,
      note='“全忠每出战”是此后持续关系总述，不将所有供给行为限定在888年。')
event('li_hanzhi_zezhou','李罕之返泽州，遣子侍李克用',19,'河阳兵败后；具体日未载','泽州',
      '李罕之任泽州刺史、领河阳节度使，留其子颀侍李克用，自己返泽州。',
      [('李罕之','返泽州者'),('李颀','奉父命侍李克用者'),('李克用','接纳李颀者')],
      note='原文“子颀”明示父子；“领河阳节度使”与实控河阳分开看待。')
event('li_hanzhi_raids_region','李罕之据泽州劫掠周边',19,'李罕之返泽州后至此后多年；确年未载','怀、孟、晋、绛一带',
      '《通鉴》概述李罕之据泽州后长期掠夺，周边官府与耕作受严重破坏。',
      [('李罕之','掠夺方统领')],year=None,
      note='原文“殆将十年”为跨年总述，不把十年破坏全归888年当年。')
event('li_hanzhi_moyun','李罕之攻取摩云山',19,'李罕之据泽州后；具体年日未载','摩云山',
      '李罕之攻取河中、绛州间民众聚保的摩云山，因而被时人称为“李摩云”。',
      [('李罕之','攻山者')],year=None,
      note='本段置于长期劫掠总述之后，不给无据的888年确年。')
event('le_congxun_killed','乐从训被程公信击杀',20,'888年四月癸巳前','洹水、魏州',
      '乐从训移军洹水，罗弘信遣程公信进击，乐从训被斩，其与父乐彦祯的首级都被悬于军门。',
      [('乐从训','被杀者'),('罗弘信','遣将者'),('程公信','进击者'),('乐彦祯','首级被悬者')],
      note='原文明确程公信斩乐从训；乐彦祯何日何人所杀未记，不将其死亡直接归责程公信。')
event('luo_makes_peace_zhu','罗弘信与朱全忠修好',20,'888年四月癸巳','魏博、汴军方向',
      '罗弘信派使者厚礼犒朱全忠军并请求修好，朱全忠召军返；朝廷诏罗弘信权知魏博留后。',
      [('罗弘信','请和及受任者'),('朱温','以朱全忠名义召军者')],
      note='诏命与修好均见原文，礼物数额未载。')
event('guo_yu_takes_jingnan','郭禹逐王建肇据荆南',21,'888年四月前后；具体日未载','荆南、黔州',
      '归州刺史郭禹进攻荆南，逐王建肇出逃黔州；朝廷诏郭禹为荆南留后。',
      [('郭禹','攻取及受任者'),('王建肇','出奔者')],
      note='郭禹后复名成汭，与既有人物成汭共用键；战后荆南仅十七家是原文极端概数。')
event('guo_yu_jingnan_recovery','郭禹抚集荆南，晚年人口恢复',21,'郭禹治荆南期间至晚年；确年未载','荆南',
      '《通鉴》记郭禹治理荆南、招抚流民、通商劝农，至晚年户数恢复。',
      [('郭禹','治理者')],year=None,
      note='“晚年殆及万户”明确为多年后总述，不记成888年人口；户数仅书载。')
event('han_jian_huazhou_policy','韩建于华州招民劝农',21,'韩建治华州数年间；确年未载','华州',
      '《通鉴》比较记述韩建在华州招抚流民、劝课农桑，数年间民富军赡，时人称北韩南郭。',
      [('韩建','华州治理者'),('郭禹','称谓所对比的荆南治理者')],year=None,
      note='“数年之间”为跨年总述；“北韩南郭”为时人称谓，不是二人的正式官号。')
event('guo_yu_takes_kuizhou','郭禹与许存夺夔州',21,'郭禹治荆南期间；具体年日未载','夔州',
      '秦宗权别将常厚据夔州，郭禹与其将许存攻取。',
      [('常厚','原据夔州者'),('郭禹','攻取者'),('许存','随军将领')],year=None,
      note='本段先后叙事无确年，不套用888年。')
event('guo_yu_renamed_cheng_rui','郭禹后授荆南节度使并复名成汭',21,'郭禹据荆南久之；具体年未载','荆南',
      '朝廷后来授郭禹荆南节度使、王建肇武泰节度使；郭禹奏请恢复姓名为成汭。',
      [('郭禹','受任及复名者'),('王建肇','受任者')],year=None,
      note='“久之”明示晚于888年当年叙事；郭禹与成汭同一人。')
event('li_keyong_shizhong','李克用加兼侍中',22,'888年四月；具体日未载','',
      '朝廷加李克用兼侍中。',
      [('李克用','受任者')],
      note='本段未标月日，四月仅承上文月序；不补具体干支。')
event('zhu_quanzhong_shizhong','朱全忠加兼侍中',23,'888年五月己亥','',
      '朝廷加朱全忠兼侍中。',
      [('朱温','以朱全忠名义受任者')])
event('zhao_deyin_surrenders','赵德諲举山南东道降朱全忠',24,'888年五月壬寅','山南东道',
      '赵德諲失荆南后判断秦宗权将败，率山南东道归降，托附朱全忠。',
      [('赵德諲','归降者'),('秦宗权','其所离开阵营主将'),('朱温','以朱全忠名义受归附者')],
      note='秦宗权将败是赵德諲的判断，不当作此日已败事实。')
event('zhao_deyin_chungyi','朝廷授赵德諲忠义军节度使',24,'赵德諲归降后；具体日未载','山南东道',
      '朱全忠奏赵德諲为副，朝廷改山南东道为忠义军，授赵德諲节度使、蔡州四面行营副都统。',
      [('朱温','以朱全忠名义上表者'),('赵德諲','受任者')])

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(17,25):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {17:'孙儒自称节度使不等于朝廷任命；杨行密采纳归庐建议未记到达日。',18:'河阳援军、温地作战、上表任命与此后长期供粮分录。',19:'“殆将十年”及摩云山事未给确年，不硬归888年；领河阳职与实控分开。',20:'乐从训死于程公信进击，乐彦祯死日与执行者未载。',21:'郭禹即成汭；晚年万户、韩建数年治华及“久之”授官均为跨年总述。',22:'未明月日，四月只承上文月序。',24:'赵德諲对秦宗权将败的判断不是已发生事实。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17,25):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=888,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph='zztj-v257-y0888-p025',coverage='卷257文德元年条第17—24段；本年续录。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
