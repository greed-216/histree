"""Curate consecutive Tongjian volume 257, year 887 paragraphs 17–24."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 60))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0887-p017-p024', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_257_0887_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·光启三年（887）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('zhang_xiong_east_pond','张雄屯东塘并遣赵晖据上元',17,'光启三年五月前后；具体日未载','东塘、上元',
      '前苏州刺史张雄率众溯江屯东塘，遣赵晖据上元。',
      [('张雄','率军与遣将者'),('赵晖','据上元者')],
      note='原文明确“前苏州刺史张雄”，与前段申及所归张雄相互印证；仍不与张神剑合并。')
event('lv_forges_gao_order','吕用之伪造高骈牒召杨行密',18,'毕师铎攻广陵时；具体日未载','广陵、庐州',
      '吕用之伪造高骈公文，署杨行密为行军司马，要求杨行密率兵入援。',
      [('吕用之','伪造公文者'),('高骈','被冒用名义者'),('杨行密','被召兵者')],
      note='任命出自伪牒，不能作为高骈真实任命记录。')
event('yuan_xi_advises_yang','袁袭劝杨行密赴淮南',18,'毕师铎攻广陵时；具体日未载','庐州',
      '庐江人袁袭劝杨行密趁淮南各方冲突率兵前往；杨行密采纳。',
      [('袁袭','进言者'),('杨行密','采纳者')],
      note='袁袭关于淮南归属的判断是劝说辞，不作既成事实。')
event('yang_reaches_tianchang','杨行密合兵抵天长',18,'光启三年五月','庐州、和州、天长',
      '杨行密发庐州兵，又向和州刺史孙端借兵，合军抵天长。',
      [('杨行密','率军者'),('孙端','出借兵力者')],
      note='“数千人”为原文概数。')
event('lv_attacks_hankou','吕用之攻淮口未克后归杨行密',18,'光启三年五月前后','淮口、天长',
      '郑汉章随毕师铎时留妻守淮口；吕用之攻十日未克，郑汉章率兵救援。吕用之闻杨行密抵天长，率众归附。',
      [('郑汉章','率兵救援者'),('吕用之','攻淮口后归附者'),('杨行密','受归附者')],
      note='郑汉章妻未具名，不创独立人物。')
event('zhu_defeats_zhang_again','朱全忠再次击败张晊',19,'光启三年五月丙子','汴州方向',
      '朱全忠出兵击败张晊；秦宗权闻讯从郑州率精兵前来会合。',
      [('朱温','以朱全忠名义出击者'),('张晊','被击败者'),('秦宗权','率兵来会者')])
event('zhang_shenjian_joins_yang','张神剑率众归杨行密',20,'光启三年五月；具体日未载','高邮、天长方向',
      '张神剑向毕师铎索取财货未获立即答应，遂率众归杨行密，并运高邮粮供其军。',
      [('张神剑','率众归附并运粮者'),('毕师铎','被索货者'),('杨行密','受归附者')],
      note='高邮张神剑名雄，但与前苏州刺史张雄的身份关系未证。')
event('gao_ba_liu_jin_join_yang','高霸等率众归杨行密',20,'光启三年五月；具体日未载','海陵、曲溪、盱胎',
      '高霸、刘金、贾令威各率众归杨行密，杨行密军势扩大。',
      [('高霸','率众归附者'),('刘金','率众归附者'),('贾令威','率众归附者'),('杨行密','受归附者')],
      note='“万七千人”照史书所记，不推为实测兵额；“盱胎”照电子底本原字。')
event('zhu_requests_allies','朱全忠向兖郓及义成求援',21,'光启三年五月辛巳前','兖州、郓州、汴州',
      '朱全忠向兖、郓求援，朱瑄、朱瑾率兵来援，义成军也加入。',
      [('朱温','以朱全忠名义求援者'),('朱瑄','率兵援助者'),('朱瑾','率兵援助者')])
event('bianxiao_battle','朱全忠等在边孝村败秦宗权',21,'光启三年五月辛巳','边孝村、阳武桥',
      '朱全忠率四镇兵攻秦宗权于边孝村，秦宗权败而夜遁；朱全忠追至阳武桥后返。',
      [('朱温','以朱全忠名义率军者'),('秦宗权','败退者'),('朱瑄','援军统领'),('朱瑾','援军统领')],
      note='“斩首二万余级”是原文战争数字，不据此核定实际死亡。')
event('zhu_honors_zhu_xuan','朱全忠兄事朱瑄',21,'边孝村之战后','汴州方向',
      '朱全忠感念朱瑄援军，以兄长之礼对待朱瑄。',
      [('朱温','以朱全忠名义致礼者'),('朱瑄','受礼者')])
event('cai_positions_abandoned','蔡军弃东都等驻地',21,'秦宗权边孝村败后','东都、河阳、许、汝、怀、郑、陕、虢',
      '蔡军在东都、河阳等地的驻军闻秦宗权败而撤离；秦宗权离郑州、孙儒离河阳时杀掠焚毁当地。',
      [('秦宗权','郑州撤离及杀掠者'),('孙儒','河阳撤离及杀掠者')],
      note='各地事件叙述简略，不据此推定每地撤离的日期和范围。')
event('xu_zheng_appointments','许郑两州分别任命主事者',21,'秦宗权边孝村败后','许州、郑州',
      '朝廷任杨守宗知许州事，朱全忠任孙从益知郑州事。',
      [('杨守宗','朝廷所任许州主事者'),('朱温','以朱全忠名义任命者'),('孙从益','郑州受任者')])
event('qian_sends_against_xue','钱镠遣将讨薛朗',22,'光启三年五月；具体日未载','东安、浙江、静江',
      '钱镠遣杜稜、阮结、成及率兵讨薛朗。',
      [('钱镠','遣将者'),('杜稜','领兵者'),('阮结','领兵者'),('成及','领兵者'),('薛朗','讨伐对象')])
event('zhao_hui_blocks_qin','赵晖于上元截击秦彦军',23,'光启三年五月甲午','上元、长江',
      '秦彦率宣歙军乘竹筏沿江而下，赵晖在上元截击，秦彦军损失惨重。',
      [('秦彦','率军者'),('赵晖','截击者')],
      note='“三万余”“杀溺殆半”照原文，不作精确军额与伤亡统计。')
event('qin_enters_guangling','秦彦入广陵并自署权知淮南节度事',23,'光启三年五月丙申','广陵',
      '秦彦入广陵，自称权知淮南节度事，任毕师铎为行军司马、赵锽为宣歙观察使。',
      [('秦彦','入城及自署者'),('毕师铎','受任者'),('赵锽','受任者')],
      note='“自称”体现任命来源，不推为朝廷正式任命。')
event('yang_besieges_guangling','杨行密围广陵设八寨',23,'光启三年五月戊戌','广陵',
      '杨行密率军抵广陵城下，设八寨围守；秦彦闭城自守。',
      [('杨行密','围城者'),('秦彦','守城者')])
event('li_changfu_fighting','李昌符与杨守立争道引发交战',24,'光启三年六月戊申至己酉','行宫',
      '李昌符与杨守立部下因争道相殴，皇帝遣使劝止未果；己酉李昌符拥兵焚行宫。',
      [('李昌符','凤翔军统领及拥兵者'),('杨守立','天威军统领')],
      note='争道与焚行宫分属两日，原文未记确切现代地点。')
event('li_changfu_defeated','李昌符攻大安门败走陇州',24,'光启三年六月庚戌','大安门、陇州',
      '李昌符攻大安门，与杨守立军在通衢交战，败后率部逃往陇州；杜让能步入宫中侍驾，韦昭度将家属留在军中以激励士卒。',
      [('李昌符','进攻及败走者'),('杨守立','击败李昌符者'),('杜让能','入宫侍驾者'),('韦昭度','激励军士者')],
      note='“质其家”按史书叙事保留为留家属于军中，不增写具体胁迫细节。')
event('li_maozhen_campaign','朝廷命李茂贞讨李昌符',24,'光启三年六月壬子','陇州方向',
      '朝廷任李茂贞为陇州招讨使，命其讨李昌符。',
      [('李茂贞','受命讨伐者'),('李昌符','讨伐对象')],
      note='任命不推为讨伐已完成。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(17,25):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {17:'前苏州刺史张雄身份明确，仍不与高邮张神剑合并。',18:'伪牒不能录成高骈真实任命；袁袭谋议不是既成事实。',20:'张神剑与苏州张雄不合并；兵额是原文战报。',21:'战报杀伤数字不推为确数；秦宗权败后各地撤军无逐地日期。',23:'秦彦自署不等同朝廷任命。',24:'六月起新月段，争道、焚宫、败走和任命依日拆分。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17,25):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=887,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph='zztj-v257-y0887-p025',coverage='卷257光启三年条第17—24段；本年续录。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
