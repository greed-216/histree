"""Curate consecutive Tongjian volume 258, year 889 paragraphs 1–8."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 25))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0889-p001-p008', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-258-889'
B['sources'] = [dict(key=source,title='资治通鉴·卷258',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/4d35696319726b523bd624f2370cb2cf7faa6b43/resources/derived/tongjian/258.txt',note='卷258龙纪元年起；书、卷、年、段落及行号见批次账本。')]
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
alias = {'唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄'}
people, used, reused = {}, {}, set()

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0889_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·龙纪元年（889）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷258龙纪元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=889,note=None,quote=None):
    key='event_zztj_258_0889_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_258_0889_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('new_era_amnesty','昭宗大赦改元龙纪',1,'889年正月癸巳朔','',
      '昭宗在正月朔日赦天下，改元龙纪。',[('唐昭宗','赦令及改元者')],
      note='原文年首为龙纪元年，主体承卷首昭宗；与既有李杰实体复用，不按后来的改名另建人物。')
event('liu_chongwang_chancellor','刘崇望拜相',2,'889年正月；具体日未载','',
      '朝廷以翰林学士承旨、兵部侍郎刘崇望同平章事。',[('刘崇望','同平章事受任者')])
event('pang_captures_suqian','庞师古拔宿迁并驻吕梁',3,'889年正月；具体日未载','宿迁、吕梁',
      '汴将庞师古攻取宿迁，驻军吕梁。',[('庞师古','攻城及驻军将领')])
event('shi_pu_defeat_lvliang','时溥迎战庞师古败退彭城',3,'889年正月；具体日未载','吕梁、彭城',
      '时溥迎战庞师古，大败后退守彭城。',[('时溥','败退者'),('庞师古','对战将领')])
event('guo_fan_kills_shen','郭璠杀申丛送秦宗权至汴',4,'889年正月壬子','汴',
      '蔡将郭璠杀申丛，将秦宗权送到汴，向朱全忠声称申丛谋再立秦宗权。',
      [('郭璠','杀申丛并送俘者'),('申丛','被杀者'),('秦宗权','被押送者'),('朱温','以朱全忠名义接收者')],
      note='“丛谋复立宗权”是郭璠告朱全忠的说法，不能作为已独立证实的谋反事实。')
event('guo_fan_huaixi','朱全忠以郭璠为淮西留后',4,'889年正月壬子条','淮西',
      '朱全忠以郭璠为淮西留后。',[('朱温','以朱全忠名义任用者'),('郭璠','淮西留后受任者')],
      note='原文是朱全忠任用，不写成朝廷正式诏命。')
event('wang_defeats_shan','王建败山行章于新繁',5,'889年正月条；原文戊申','新繁',
      '王建在新繁大败山行章，《通鉴》记杀获近万人，山行章仅以身免。',
      [('王建','胜方统领'),('山行章','败退将领')],note='杀获人数为书载数量，不当作核实后的统计；与前段壬子干支次序不顺，维基文库卷258亦同文，保留段序与干支，不换算日期或据此调整事件先后。')
event('yang_shan_reposition','杨晟山行章转屯与王建相持',5,'889年正月条；新繁戊申战后','三交、濛阳',
      '杨晟惧而移屯三交，山行章屯濛阳，与王建相持。',
      [('杨晟','移屯三交者'),('山行章','屯濛阳者'),('王建','相持对手')])
event('qin_zongquan_executed','秦宗权送京师处斩',6,'889年二月；具体日未载','京师、独柳',
      '朱全忠将秦宗权送到京师，秦宗权被斩于独柳，京兆尹孙揆监刑。秦宗权在槛车中自辩只是输忠不效，观者皆笑。',
      [('朱温','以朱全忠名义送俘者'),('秦宗权','被处决及自辩者'),('孙揆','京兆尹监刑者')],
      note='自辩只作为秦宗权言论记录，不采用为编者对其政治身份的判断。')
claim('person',people['孙揆'],'description','本段末附记孙揆为“逖之族孙”。',6,quote='揆，逖之族孙也。',note='本段省称“逖”；不据省称新增另一人物或推断具体亲等。')
event('zhu_dongping_prince','朱全忠加中书令进爵东平郡王',7,'889年三月；具体日未载','',
      '朝廷加朱全忠兼中书令，进爵东平郡王；《通鉴》述其克蔡州后军势益盛。',
      [('朱温','以朱全忠名义加官进爵者')])
event('zhao_deyin_chuwen_promoted','赵德諲赵犨加官及忠武移治陈州',7,'889年三月；具体日未载','陈州',
      '朝廷加奉国节度使赵德諲中书令，加蔡州节度使赵犨同平章事并充忠武节度使，以陈州为治所。',
      [('赵德諲','加中书令者'),('赵犨','加同平章事并任忠武节度使者')])
event('zhao_chang_succeeds','赵犨病请退，赵昶继领忠武',7,'889年三月条；具体日未载','陈州',
      '赵犨患病，将军府事务交给弟赵昶，上表请求退休，朝廷诏以赵昶代为忠武节度使。',
      [('赵犨','病而交事请退者'),('赵昶','继任忠武节度使者')])
rk='relationship_person_赵犨_person_赵昶_兄长'
B['person_relationships'].append(dict(key=rk,person_a_key=people['赵犨'],person_b_key=people['赵昶'],relation_type='兄长',description='《通鉴》889年条称赵昶为赵犨之弟；方向为赵犨是赵昶的兄长。',status='draft'))
claim('person_relationship',rk,'description','赵犨是赵昶的兄长。',7,quote='会犨有疾，悉以军府事授其弟昶，表乞骸骨，诏以昶代为忠武节度使。')
event('zhao_chou_death','赵犨退任后去世',7,'889年三月条后未几；具体日未载','',
      '赵犨退任后不久去世。',[('赵犨','去世者')],note='“未几”保留相对顺序，不补写卒日；事件按本年条记录，不改复用人物旧档。')
event('qian_qiu_captures_suzhou','钱銶拔苏州，徐约逃海死亡',7,'889年三月丙申','苏州、海上',
      '钱銶攻取苏州，徐约逃入海中而死。',[('钱銶','攻城将领'),('徐约','败逃死亡者')],
      note='“亡入海而死”未明确溺死或具体海域，不补写死因。')
event('shen_can_suzhou','钱镠以沈粲权知苏州',7,'889年三月丙申条；苏州攻取后','苏州',
      '钱镠以海昌都将沈粲权知苏州。',[('钱镠','任用者'),('沈粲','权知苏州受任者')],note='“权知”保留代理性质，不写成正式刺史任命。')
event('shanguo_baoyi','陕虢军获赐保义军号',8,'889年四月','陕虢',
      '朝廷赐陕虢军号保义。',note='军号变更不创建未具名的任命人物。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={1:'年号与主体承年首卷首；昭宗复用李杰。',3:'宿迁攻取、吕梁交战及彭城退守分录。',4:'郭璠指控申丛谋复立为当事人说法；淮西留后为朱全忠任用。',5:'新繁战斗与转屯相持分录；近万杀获为书载。前段壬子与本段戊申干支次序不顺，维基文库卷258同文，未核纸本，保留段序不换算日期。',6:'自辩不作编者判断；末附省称逖的族孙信息，未扩建不明亲等。',7:'加官、病退继任、去世、苏州攻取及代理任用分别录入；赵犨→兄长→赵昶。'}
for n in range(1,9):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
    if n in reviews:ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=889,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph='zztj-v258-y0889-p009',coverage='卷258龙纪元年第1—8段连续录入；本年共24段尚未完结。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
