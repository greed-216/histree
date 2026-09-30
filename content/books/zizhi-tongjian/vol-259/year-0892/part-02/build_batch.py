"""Curate consecutive Tongjian volume 259, year 892 paragraphs 9–16."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 47))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0892-p009-p016', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-892'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259景福元年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/259.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/259.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
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
alias.update({'郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0892_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·景福元年（892）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259景福元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=892,note=None,quote=None):
    key='event_zztj_259_0892_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0892_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def relation(a,b,t,n,description,quote=None):
    ka,kb=people[a],people[b]
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==ka and r['person_b_key']==kb and r['relation_type']==t]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);key=row['key'];reused.add(key)
    else:
        key=f'relationship_{ka}_{kb}_{t}';row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key

event('zhu_requests_heyang_change','朱全忠奏贬赵克裕，以张全义兼河阳',9,'892年二月条；具体日未载','河阳、佑国',
      '朱全忠奏请贬河阳节度使赵克裕，以佑国节度使张全义兼河阳节度使。',[('朱温','以朱全忠名义奏请者'),('赵克裕','被奏贬者'),('张全义','兼领所指者')],note='奏贬依原文，不把奏请单写朝廷诏令已下；受任不等于到任。')
event('sun_ru_sieges_xuanzhou','孙儒围宣州',10,'892年二月条；具体日未载','宣州',
      '孙儒围攻宣州。',[('孙儒','围攻者')],note='对应本年记事，区别891年底逼宣州，不补未载的具体开围日期。')
event('changzhou_transfer_background','刘建锋随孙儒出征，陈可言据常州的追叙',10,'初；确年日未载','常州、甘露镇',
      '《通鉴》追述刘建锋原为孙儒守常州，后来率兵从孙儒攻杨行密，甘露镇使陈可言率千人占常州。',
      [('刘建锋','原守及率兵出征者'),('孙儒','主将'),('杨行密','被击对象'),('陈可言','率部据城者')],year=None,note='初为追叙，确年空；一千为书载兵数。')
event('zhang_xun_takes_changzhou','张训袭常州手刃陈可言',10,'段内初之后；确年日未定','常州',
      '张训突然率军至常州城下，陈可言仓促出迎，张训亲手杀之，取得常州。',[('张训','袭城杀将者'),('陈可言','出迎被杀者')],year=None,note='同一初起的段内追叙，年界未明，暂不强定892年；手刃为书载动作。')
event('yang_other_general_takes_run','杨行密别将取得润州',10,'段内初之后；确年日未定','润州',
      '杨行密另一将领取得润州。',[('杨行密','别将所属主将')],year=None,note='别将未具名，不推成张训或安仁义；与初追叙相接，具体年日待考。')
event('xu_region_war_famine_background','朱全忠连年攻时溥，三州战水灾饥死',11,'连年；起始与逐次确年日未载','涂州、泗州、濠州',
      '《通鉴》述朱全忠连年攻时溥，三州居民不得耕获，外镇援军无功，又遇水灾，书载人死十之六七。',
      [('朱温','以朱全忠名义连年进攻者'),('时溥','被攻方')],year=None,note='底本涂及衮兗并列有转录疑点，不改快照、不据字差多建州名；死亡比例为史载而非现代统计，连年不反算首战日期。')
event('shi_pu_peace_move_condition','时溥求和，朱全忠要求移镇',11,'892年二月条；具体日未载','徐州',
      '时溥困迫向朱全忠求和，朱全忠要求其移镇才可，时溥答应；朱全忠奏请将时溥移它镇，命大臣镇徐州。',[('时溥','求和并许移镇者'),('朱温','以朱全忠名义设条件奏请者')],note='答应移镇不写实际已离徐州。')
event('liu_chongwang_ganhua_shi_refuses','刘崇望受任感化，时溥拒诏使其折返',11,'892年二月条；移镇议后','徐州、华阴',
      '朝廷任刘崇望同平章事、感化节度使，任时溥为太子太师。时溥怕朱全忠欺骗杀他，据城不奉诏，刘崇望到华阴后返回。',[('刘崇望','受任及到华阴折返者'),('时溥','拒诏者'),('朱温','以朱全忠名义被疑者')],note='惧被诈是时溥担心，不确认真实杀计划；刘崇望未抵徐州，不记到任。')
event('zhao_deyin_dies_kuangning_succeeds','赵德諲去世，赵匡凝继任',12,'892年二月条；具体日未载','忠义',
      '忠义节度使赵德諲去世，其子赵匡凝继任。',[('赵德諲','去世节度使'),('赵匡凝','继任者')],note='子匡凝按父姓补赵，不补朝廷任命日或具体葬地。')
relation('赵德諲','赵匡凝','父亲',12,'《通鉴》称赵匡凝为赵德諲之子；赵德諲是赵匡凝的父亲。',quote='忠义节度使赵德諲薨，子匡凝代之。')
event('wang_fujian_attack','王潮遣王彦复王审知攻福州',13,'892年二月条；具体日未载','福州、平湖洞、滨海',
      '范晖骄侈失众心，王潮以从弟王彦复为都统、弟王审知为都监，率军攻福州。居民请输米饷军，平湖洞及滨海蛮夷用兵船相助。',[('范晖','被攻留后'),('王潮','遣军者'),('王彦复','都统将领'),('王审知','都监将领')],note='骄侈失众心为书评，居民与部落未具名不造人物；未载攻克结果，不提前记福州已经取。')
relation('王彦复','王潮','从弟',13,'《通鉴》称王彦复为王潮从弟；王彦复是王潮的从弟，不推具体叔伯。',quote='王潮以从弟彦复为都统')
relation('王潮','王审知','兄长',13,'《通鉴》称王审知为王潮之弟；王潮是王审知的兄长。',quote='王潮以从弟彦复为都统，弟审知为都监')
event('wang_generals_siege_peng','王宗裕等五万人攻彭州围杨晟',14,'892年二月辛丑','彭州',
      '王建遣族子嘉州刺史王宗裕、雅州刺史王宗侃、华洪、茂州刺史王宗瑶率五万人攻彭州，杨晟迎战败，诸将围之。',[('王建','遣军者'),('王宗裕','领军族子'),('王宗侃','出征将领'),('王宗涤','以华洪旧名出征将领'),('王宗瑶','出征将领'),('杨晟','迎战被围者')],note='五万为书载；嘉雅茂为诸将职任而非战斗全发生地。')
relation('王宗裕','王建','族子',14,'《通鉴》称王宗裕为王建族子；王宗裕是王建的族子，不推直系亲子或具体侄辈。',quote='王建遣族子嘉州刺史宗裕')
event('hua_hong_deters_fu_zhao','华洪更鼓疑兵退符昭救成都',14,'892年二月辛丑后条','成都、三学山',
      '杨守亮遣符昭救杨晟，符昭直向成都营三学山。王建急召华洪返，华洪后军未集，以数百人夜近敌营数里，多击更鼓，符昭误以蜀军大至，连夜逃走。',[('杨守亮','遣援者'),('符昭','进兵及被疑兵退去者'),('杨晟','被援对象'),('王建','召回者'),('王宗涤','以华洪旧名用更鼓疑兵者')],note='数百为书载先到人马，误以大军到不能写真有大军到；三学山仅原文名未核坐标。')
event('zheng_yanchang_chancellor','郑延昌三月拜相',15,'892年三月','',
      '朝廷以户部尚书郑延昌为中书侍郎、同平章事。',[('郑延昌','拜相者')])
person('郑从谠',15,'原文记其与郑延昌为从兄弟')
relation('郑延昌','郑从谠','从兄弟',15,'《通鉴》称郑延昌与郑从谠为从兄弟；长幼不明，保留对称从兄弟关系。',quote='延昌，从谠之从兄弟也。')
event('yang_three_surrender_wang','杨子实子迁子钊率二万人降王建',16,'892年三月壬子','渠州、西川',
      '杨守亮假子杨子实、杨子迁、杨子钊从渠州引兵救杨晟，得知杨守亮必败，率众二万投降王建。',[('杨子实','率众降将'),('杨子迁','率众降将'),('杨子钊','率众降将'),('杨守亮','三将所从假父'),('杨晟','原被援对象'),('王建','受降者')],note='二万为三将合计率众，不为每人各记二万；知必败是三将判断；名称子迁子钊按同句杨氏展开。')
for name in ['杨子实','杨子迁','杨子钊']:
 relation('杨守亮',name,'假父',16,f'《通鉴》明言杨子实、子迁、子钊皆杨守亮假子；杨守亮是{name}的假父。',quote='杨子实、子迁、子钊，皆守亮之假子也')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={9:'奏贬与兼领按奏请，不补朝廷任命日。',10:'围宣与初起常州守将变动、杀将取常、别将取润分录；初后年界不明暂空。',11:'连年战灾背景、求和移镇条件、授职拒诏与刘崇望华阴返分录；涂衮兗疑字、什六七书载。',12:'赵德諲薨子匡凝代，父亲方向依证。',13:'王彦复从弟方向及王潮王审知兄长关系，兵船饷粮未具名者不造人。',14:'辛丑彭州围杨晟与符昭成都被疑兵退分录；王宗裕族子不推直系；华洪复用王宗涤。',15:'郑延昌拜相与从兄弟无长幼明示，不强转哥哥弟弟。',16:'三杨假子与率众二万合计降王建，假父关系分别依证。'}
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
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=892,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph='zztj-v259-y0892-p017',coverage='卷259景福元年第9—16段连续录入；本年46段尚未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
