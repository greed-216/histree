"""Curate consecutive Tongjian volume 257, year 887 paragraphs 41–48."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 60))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0887-p041-p048', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_257_0887_06_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·光启三年（887）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('zhu_zhen_takes_puzhou','朱珍取濮州，朱裕奔郓',41,'光启三年十月丁未','濮州、郓州',
      '朱珍攻取濮州，刺史朱裕奔郓；朱珍继续进攻郓州。',
      [('朱珍','攻取者'),('朱裕','出奔刺史')])
event('zhu_xuan_ambushes_bian','朱瑄设伏击退汴军',41,'濮州失守后；具体日未载','郓州',
      '朱瑄使朱裕诈称可为内应，诱朱珍夜进郓州；朱瑄开门纳汴军后关门袭杀，汴军退去。',
      [('朱瑄','设伏者'),('朱裕','传诈书者'),('朱珍','率军入伏者')],
      note='“死者数千人”为原文战报，不作为核定伤亡。')
event('zhu_xuan_retakes_cao','朱瑄复取曹州任郭词刺史',41,'击退汴军后；具体日未载','曹州',
      '朱瑄乘胜复取曹州，任其部属郭词为刺史。',
      [('朱瑄','复取及任命者'),('郭词','受任者')])
event('prince_sheng_title','皇子升封益王',42,'光启三年十月甲寅','',
      '朝廷立皇子升为益王。',
      [('李升','益王受封者')],
      note='原文只称“皇子升”，展示暂作李升；是否已有同名人物及确切名讳待核。')
event('du_leng_takes_chang','杜稜等攻取常州',43,'光启三年十月；具体日未载','常州、海陵',
      '杜稜等攻取常州，丁从实逃往海陵。',
      [('杜稜','攻城方将领'),('丁从实','出奔者')],
      note='“等”不据此断言此前所列全部将领均直接参战。')
event('qian_honors_zhou_bao','钱镠迎周宝至杭州',43,'光启三年十月；具体日未载','杭州',
      '钱镠奉周宝返回杭州，以部将礼节出城迎接，并将其交属高鞬。',
      [('钱镠','迎接者'),('周宝','受迎者'),('高鞬','受托者')],
      note='“属高鞬”仅按交付托属记录，未扩写其实际拘管方式。')
event('guangling_siege_famine','广陵长期围城饥荒',43,'杨行密围广陵近半年至光启三年十月','广陵',
      '杨行密围广陵近半年，秦彦、毕师铎多次出战不利；城中食物耗尽，民众大量饿死，宣州军又掠人贩卖和杀害。',
      [('杨行密','围城方'),('秦彦','城中主将'),('毕师铎','城中主将')],
      note='价格与死者“太半”均为本书记载；屠掠记为宣州军行为，不据此指称每名将领亲自实施。')
event('zhang_shenwei_opens_gate','张审威潜登广陵开门',43,'光启三年十月己巳夜至次晨','广陵西壕、城门',
      '杨行密久攻广陵不下，曾想撤军。张审威率兵伏于西壕，趁守军换班登城开门，守军溃散。',
      [('杨行密','围城军统领'),('张审威','潜登开门者')],
      note='张审威原为吕用之部将，不因此推定吕用之仍在现场指挥。')
event('qin_bi_flee','秦彦毕师铎逃往东塘',43,'广陵城门被打开后；具体日未载','广陵开化门、东塘',
      '秦彦、毕师铎向王奉仙问计后，从开化门出逃至东塘。',
      [('秦彦','出逃者'),('毕师铎','出逃者'),('王奉仙','建议逃离者')],
      note='王奉仙的“走为上策”是建议；原文还记二人此前倚重其卜决，不据此推定谶言真实有效。')
event('yang_enters_guangling','杨行密入广陵自称淮南留后',43,'秦彦毕师铎出逃后；具体日未载','广陵',
      '杨行密率军入广陵，自称淮南留后。',
      [('杨行密','入城及自称留后者')],
      note='“自称”不改写为朝廷正式任命；“万五千人”是原文兵数。')
event('liang_zan_executed','杨行密斩梁缵，韩问自尽',43,'杨行密入广陵后；具体日未载','广陵戟门',
      '杨行密以梁缵转为秦彦、毕师铎所用为由将其斩杀；韩问闻讯投井而死。',
      [('杨行密','下令处斩者'),('梁缵','被斩者'),('韩问','自尽者')],
      note='“不尽节于高氏”是杨行密处斩梁缵的理由，不作为独立核定评价。')
event('gao_yu_reburial_and_relief','高愈摄副使改殡高骈，杨行密赈广陵',43,'杨行密入广陵后；具体日未载','广陵',
      '杨行密任高骈从孙高愈摄副使，令其改殡高骈及亲族；又从西寨运米赈济城中幸存者。',
      [('杨行密','任命及赈济者'),('高愈','摄副使及改殡者'),('高骈','被改殡者')],
      note='“城中遗民才数百家”是原文概数。')
event('qin_zongheng_enters_yangzhou','秦宗权遣秦宗衡争扬州',44,'光启三年十一月辛未','广陵城西',
      '秦宗权遣弟秦宗衡率军渡淮，孙儒为副，张佶、刘建锋、马殷及秦彦晖随军；辛未抵广陵城西，取得杨行密尚未入城的辎重。',
      [('秦宗权','遣军者'),('秦宗衡','率军者'),('孙儒','副将'),('张佶','随军者'),('刘建锋','随军者'),('马殷','随军者'),('秦彦晖','随军者'),('杨行密','辎重被夺者')],
      note='“宗权族弟彦晖”暂按同姓称秦彦晖；“万人”为原文军数，不作实点。')
event('qin_yan_joins_zongheng','秦彦毕师铎转投秦宗衡',44,'光启三年十一月辛未后','东塘、广陵城西',
      '秦彦、毕师铎逃至东塘，张雄不予收留；二人拟渡江往宣州，接秦宗衡邀请后折返与其合军。',
      [('秦彦','转投者'),('毕师铎','转投者'),('张雄','拒收者'),('秦宗衡','邀请者')])
event('sun_ru_kills_zongheng','孙儒杀秦宗衡',44,'光启三年十一月甲戌','广陵城西',
      '秦宗权召秦宗衡返蔡拒朱全忠，孙儒托病不行；秦宗衡屡催，孙儒于席间杀秦宗衡，并将首级送给朱全忠。',
      [('秦宗权','召回者'),('秦宗衡','被杀者'),('孙儒','杀人者'),('朱温','以朱全忠名义受首级者')],
      note='“孙儒知宗权势不能久”是本书对其心理的叙述，不作可独立核实的预测。')
event('an_renyi_joins_yang','安仁义降杨行密并领骑兵',44,'秦宗衡被杀后；具体日未载','广陵',
      '秦宗衡部将安仁义归降杨行密，杨行密将骑兵委其统领，位在田頵之上。',
      [('安仁义','归降及领骑者'),('杨行密','受降及委任者'),('田頵','原将领位次参照')])
event('sun_ru_moves_gaoyou','孙儒与秦彦毕师铎袭高邮',44,'光启三年十一月后；具体日未载','高邮',
      '孙儒分兵掠邻州，军众增加；因广陵城下缺粮，与秦彦、毕师铎合军袭高邮。',
      [('孙儒','率军者'),('秦彦','参战者'),('毕师铎','参战者')],
      note='“数万”为原文概数。')
event('zhu_zhen_li_tangbin_dispute','朱珍与李唐宾争执后获朱全忠宽宥',45,'光启三年十一月丙子夜前后','大梁、濮州',
      '朱全忠因朱珍未经请命迎妻而愤怒，曾拟召回朱珍、让李唐宾代领其军；敬翔劝止。朱珍、李唐宾互疑，先后离军赴大梁；朱全忠未治罪，遣二人回濮州。',
      [('朱温','以朱全忠名义拟召与宽宥者'),('朱珍','被召而生疑者'),('李唐宾','拟代领军及奔大梁者'),('敬翔','劝止者')],
      note='本段后称“汉宾”与前文李唐宾不一致，疑底本异字；暂按前文李唐宾，不另创“汉宾”。')
event('jing_xiang_adviser','朱全忠常咨敬翔军政',46,'光启三年十一月前后；具体日未载','宣武',
      '《通鉴》称敬翔能推知朱全忠意图，朱全忠常就军机、民政询问他。',
      [('敬翔','军政顾问'),('朱温','以朱全忠名义咨询者')],
      note='段落为长期关系总述，不据此推定单一任命日期。')
event('gaoyou_sun_ru_sacks','孙儒攻陷高邮，张神剑返扬州',47,'光启三年辛巳至丙戌；月份未重标','高邮、扬州',
      '高邮镇遏使张神剑先率少数部众逃归扬州；丙戌孙儒攻陷高邮，原文称“屠高邮”。',
      [('张神剑','逃归者'),('孙儒','攻陷及屠城者')],
      note='张神剑辛巳出逃、孙儒丙戌屠城，日期相隔五日；不按屠城一词自拟死亡人数。')
event('yang_kills_gaoyou_survivors','杨行密坑杀高邮残兵及张神剑',47,'光启三年戊子至次日；月份未重标','广陵',
      '高邮残兵突围到广陵，杨行密疑其生变，分配诸将后一夜全部坑杀；次日又杀张神剑。',
      [('杨行密','下令杀害者'),('张神剑','次日被杀者')],
      note='“七百人”为原文数量；不能把高邮残兵被坑杀与孙儒屠高邮合为一事。')
event('gao_ba_evacuates_hailing','高霸率海陵军民迁广陵',47,'光启三年壬寅至戊戌；月份未重标','海陵、广陵',
      '杨行密忧孙儒进取海陵，命高霸率军民撤回广陵，并以族诛相胁；大批居民弃产迁徙。戊戌高霸与其弟暀、余绕山、丁从实抵广陵，杨行密出城迎接。',
      [('杨行密','下令与迎接者'),('高霸','率众迁徙者'),('高暀','高霸之弟及同行者'),('余绕山','同行将领'),('丁从实','同行者')],
      note='原文末另有乱码“往”，不据此创第二人；“数万户”为原文概数。')
event('qin_zongquan_takes_zheng','秦宗权攻陷郑州',48,'光启三年己亥；月份未重标','郑州',
      '秦宗权攻陷郑州。',
      [('秦宗权','攻城者')])

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(41,49):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {41:'先失濮州、设伏郓州、复取曹州分录；伤亡数字照书载。',42:'“皇子升”暂展示为李升，确切名讳待核。',43:'围城饥荒、开门、逃亡、入城、处置和赈济分别记录；自称留后不等于朝廷任命。',44:'“宗权族弟彦晖”暂称秦彦晖；军数为概数。',45:'底本同段“李唐宾”“汉宾”不一，后者不另创人物。',47:'底本末“往”有乱码，不据此创人物；坑杀残兵与高邮屠城分录；月份未重标。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,49):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=887,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(41,49)],next_paragraph='zztj-v257-y0887-p049',coverage='卷257光启三年条第41—48段；本年续录。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
