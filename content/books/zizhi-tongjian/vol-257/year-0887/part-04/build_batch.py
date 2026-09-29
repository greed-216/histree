"""Curate consecutive Tongjian volume 257, year 887 paragraphs 25–32."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 60))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0887-p025-p032', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-257-887'
B['sources'] = [dict(key=source,title='资治通鉴·卷257',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/5911e959ccc6b7efae3e673a6f8bcb612a9748a0/resources/derived/tongjian/257.txt',note='卷257光启三年起；书、卷、年、段落及行号见批次账本。')]
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
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_257_0887_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·光启三年（887）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷257光启三年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=887,note=None,quote=None):
    key='event_zztj_257_0887_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_257_0887_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('wang_chongrong_killed','常行儒杀王重荣',25,'光启三年六月甲寅','河中',
      '河中牙将常行儒举兵攻府舍，王重荣逃出，次日被常行儒寻获杀害。史书称王重荣执法严厉、常行儒曾受罚。',
      [('常行儒','起事并杀王重荣者'),('王重荣','被杀节度使')],
      note='甲寅为起事日，王重荣被杀在“明旦”；不把两步强并为同日。关于起事动机依本书叙述。')
event('wang_chongying_appointed','朝廷任王重盈为护国节度使',25,'王重荣遇害后；具体日未载','河中、陕虢',
      '朝廷任陕虢节度使王重盈为护国节度使，并命其子王珙权知陕虢留后。',
      [('王重盈','护国节度使受任者'),('王珙','陕虢留后受任者')],
      note='原文“重盈子珙”明示父子关系；暂只记于角色与引用。')
event('chang_xingru_executed','王重盈至河中处死常行儒',25,'王重盈抵河中后；具体日未载','河中',
      '王重盈到河中后拘捕常行儒并将其杀死。',
      [('王重盈','处置者'),('常行儒','被杀者')],
      note='抵河中与处置的具体日期均未载，不套用甲寅。')
event('bi_qin_attack_yang','毕师铎秦稠出城攻杨行密败',26,'光启三年六月戊午','广陵城西',
      '秦彦遣毕师铎、秦稠率军出城西击杨行密；秦稠战死，出击军损失惨重。',
      [('秦彦','遣军者'),('毕师铎','率军者'),('秦稠','战死者'),('杨行密','受攻击者')],
      note='“八千”“死者什七八”均为原文战报，不作精确统计。')
event('guangling_famine','广陵围城乏食',26,'光启三年六月戊午前后','广陵',
      '广陵城内粮食匮乏，樵采路断；原文接记“宣州军始食之”。',
      [('秦彦','城中宣州军主将')],
      note='“之”所指在电子底本段落中需进一步核对，先保留原文措辞，不明确改写为具体食用对象；不归责秦彦个人下令。')
event('xie_yin_expels_song','谢殷逐宋兖',27,'光启三年六月壬戌','亳州',
      '亳州将领谢殷驱逐刺史宋兖。',
      [('谢殷','驱逐者'),('宋兗','被逐者')],
      note='底本作“宋兗”，人物展示字形统一为“宋兖”，原文保留。')
event('li_zhang_reoccupy','李罕之与张全义据河阳东都',28,'孙儒离河阳后；具体日未载','泽州、河阳、东都',
      '孙儒离开河阳后，李罕之召张全义合余众，分别据河阳和东都，并向河东求援。',
      [('孙儒','撤离河阳者'),('李罕之','据河阳及求援者'),('张全义','据东都及求援者')])
event('li_keyong_aids_henan','李克用遣安金俊援河南',28,'李罕之张全义求援后；具体日未载','泽州、河阳、东都',
      '李克用任安金俊为泽州刺史，派骑兵援助李罕之、张全义，并上表请任李罕之为河阳节度使、张全义为河南尹。',
      [('李克用','遣援军及上表者'),('安金俊','率骑兵者'),('李罕之','被表举者'),('张全义','被表举者')],
      note='“表”是奏请，原文未记朝廷批准日期，不改写为已获正式任命。')
event('luoyang_wartime_ruin','东都战乱后人口凋敝',28,'黄巢之乱后至张全义初到东都；具体年未载','东都',
      '《通鉴》追叙东都经黄巢之乱及后续战乱，张全义初到时城郭残破，居民极少。',
      [('张全义','初到东都者')],year=None,
      note='“初”引入此前背景，不把黄巢之乱或东都破坏硬记为887年；户数照原文概述。')
event('zhang_quanyi_repopulation','张全义设屯将招抚流散',28,'张全义初治东都时；具体年日未载','东都及属县',
      '张全义选十八人任屯将，往属县旧聚落招徕流散人口、劝农，并组织民众防御盗寇。',
      [('张全义','推行招抚者')],year=None,
      note='段内接“数年之后”，初治东都的具体措施可追叙至887年前后，但本段未逐项给出确年，保留未定。')
event('zhang_quanyi_recovery','张全义治下东都逐年恢复',28,'张全义初治东都数年之后；具体年未载','东都及属县',
      '史书记张全义治理数年后东都坊曲、县户逐渐恢复，耕作扩大，并据户口恢复奏置令佐。',
      [('张全义','治理及奏置者')],year=None,
      note='明确“数年之后”，不能将恢复成果录为887年当年事件；兵额与户数仅为书载。')
event('zhang_quanyi_farming_policy','张全义奖农并督责荒田',28,'张全义治东都期间；具体年未载','东都及属县',
      '《通鉴》叙张全义察田桑、奖赏丰收农户，对荒田加以督责，并鼓励邻里相助。',
      [('张全义','施政者')],year=None,
      note='本段为多年施政总述，既有奖励也有杖责，保留两面；不视为单日法令。')
event('du_leng_defeats_li','杜稜等败薛朗将李君暀',29,'光启三年六月；具体日未载','阳羡',
      '杜稜等人在阳羡击败薛朗部将李君暀。',
      [('杜稜','进攻方将领'),('薛朗','被击部将上级'),('李君暀','被击败者')],
      note='承前段钱镠遣杜稜等讨薛朗；“等”不据此擅列所有将领直接参战。')
event('wu_miao_joins_yang','吴苗率众降杨行密',30,'光启三年七月癸未','广陵',
      '淮南将吴苗率众越城投降杨行密。',
      [('吴苗','率众投降者'),('杨行密','受降者')],
      note='“八千人”为原文数字，不推为实点人数。')
event('li_changfu_killed','李昌符于陇州被杀',31,'光启三年八月壬寅朔','陇州',
      '李茂贞上奏陇州刺史薛知筹献城，李昌符被斩，族属遭诛。',
      [('李茂贞','上奏者'),('薛知筹','献城者'),('李昌符','被斩者')],
      note='“灭其族”照原文，不补写人数及具体执行者。')
event('xie_yin_killed','朱全忠遣霍存杀谢殷',32,'光启三年八月；具体日未载','亳州',
      '朱全忠经过亳州时遣霍存袭击谢殷，谢殷被斩。',
      [('朱温','以朱全忠名义遣将者'),('霍存','袭击者'),('谢殷','被杀者')])

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(25,33):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {25:'甲寅起事，明旦王重荣被杀；后续王重盈到河中、处死常行儒日期未载。',26:'“宣州军始食之”代词所指待核，保留原词；战损为书载。',28:'“初”与“数年之后”分别处理为未定年追叙，不置于887年。',29:'“等”不推定此前所有将领均直接参战。',31:'“灭其族”不补人数或执行者。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,33):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=887,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph='zztj-v257-y0887-p033',coverage='卷257光启三年条第25—32段；本年续录。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
