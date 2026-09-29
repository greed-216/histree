"""Curate consecutive Tongjian volume 257, year 887 paragraphs 33–40."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 60))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0887-p033-p040', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_257_0887_05_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·光启三年（887）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('li_maozhen_fengxiang','李茂贞授凤翔节度使',33,'光启三年丙子；原文未重标月份','凤翔',
      '朝廷任李茂贞同平章事，充凤翔节度使。',
      [('李茂贞','受任者')],
      note='上文“八月壬寅朔”至此“丙子”相隔逾一月，但下文才标“九月”；月日存在文本历日疑点，仅保留本段干支。')
event('wei_zhaodu_promoted','韦昭度加守太保兼侍中',34,'光启三年；具体月日未载','',
      '朝廷任韦昭度守太保、兼侍中。',
      [('韦昭度','受任者')],
      note='本段没有另记干支日，不沿用上一段丙子。')
event('zhu_quarrels_with_xuan','朱全忠与朱瑄交恶',35,'光启三年壬子前；具体月日未载','宣武、兖郓',
      '《通鉴》称朱全忠欲兼兖、郓，因朱瑄兄弟此前援己，遂以招诱宣武军士之说责备朱瑄；朱瑄回书不逊，两方生隙。',
      [('朱温','以朱全忠名义责备者'),('朱瑄','被责备及复书者')],
      note='底本“诬瑄”指此控诉为朱全忠所诬，不把招诱军士录成朱瑄已实施的事实。')
event('zhu_takes_caozhou','朱珍葛从周袭曹州杀丘弘礼',35,'光启三年壬子；原文未重标月份','曹州',
      '朱全忠遣朱珍、葛从周袭曹州，壬子攻下，刺史丘弘礼被杀。',
      [('朱温','以朱全忠名义遣将者'),('朱珍','袭城将领'),('葛从周','袭城将领'),('丘弘礼','被杀刺史')])
event('liu_bridge_battle','朱全忠军与兖郓兵战于刘桥',35,'曹州被攻后；具体月日未载','濮州、刘桥',
      '朱全忠军攻濮州，与兖、郓兵在刘桥交战；朱瑄、朱瑾逃脱。',
      [('朱温','以朱全忠名义进攻者'),('朱瑄','兖郓一方将领'),('朱瑾','兖郓一方将领')],
      note='“杀数万人”为原文战争数字，不据以核定死亡。')
event('qin_grants_zhang_titles','秦彦授张雄及部将告身',36,'光启三年丁卯前；具体月日未载','广陵、东塘',
      '秦彦希望借张雄军力，给张雄仆射告身，并给冯弘铎等部将尚书告身；张雄军与广陵民众以粮货交易，渐富而不愿作战，其后又帮助杨行密。',
      [('秦彦','授告身者'),('张雄','受告身及变更支持方者'),('冯弘铎','受告身部将'),('杨行密','后来受张雄援助者')],
      note='授告身、交易和“未几”复助杨行密先后发生，具体日期未载；不把张雄阵营归属当作始终不变。')
event('yang_defeats_bi_west','杨行密于广陵城西败毕师铎郑汉章',36,'光启三年丁卯；原文未重标月份','广陵城西',
      '秦彦令毕师铎、郑汉章率军出城列阵。杨行密设粮帛诱敌并伏兵夹击，广陵军败，毕师铎、郑汉章逃脱。此后秦彦不再议出师。',
      [('秦彦','遣军者'),('毕师铎','出战及逃脱者'),('郑汉章','出战及逃脱者'),('杨行密','设伏击败者')],
      note='原文“万二千”“俘斩殆尽”属战报，不做精确统计；伏击策略记为史书叙述。')
event('li_tao_advocates_battle','李涛主张杨行密出战',36,'光启三年丁卯；原文未重标月份','广陵城西',
      '李宗礼建议杨行密守寨，李涛反对退军并请为前锋；杨行密随后部署诱敌。',
      [('李宗礼','建议坚壁者'),('李涛','主张出战者'),('杨行密','听取建议者')],
      note='原文未明说杨行密正式任李涛为前锋，不把请战记为已获任命。')
event('zhang_jun_chancellor','张浚授兵部侍郎同平章事',37,'光启三年九月；具体日未载','',
      '朝廷任张浚为兵部侍郎、同平章事。',
      [('张浚','受任者')])
event('gao_pian_starved','高骈道院遭断供',38,'光启三年九月甲戌前','广陵道院',
      '高骈被拘于道院，秦彦供给极少，随侍人员陷入严重饥饿。',
      [('高骈','被拘及受困者'),('秦彦','负责供给者')],
      note='原文记燃木像、煮皮带及“有相啖者”，此处概括为严重饥饿；不推定具名食人者。')
event('qin_orders_gao_killed','秦彦命刘匡时杀高骈及家人',38,'光启三年九月甲戌','广陵道院',
      '秦彦因疑高骈厌胜及内应，又听王奉仙所谓“大人死”可解灾之言，命刘匡时杀高骈及其子弟甥侄，并合葬一坑。',
      [('秦彦','下令者'),('王奉仙','进言者'),('刘匡时','奉命行杀者'),('高骈','被杀者')],
      note='厌胜与灾异都是秦彦等人的怀疑、谶言，不作为真实因果；家人未具名不创人物。')
event('yang_mourns_gao','杨行密为高骈举哀',38,'光启三年九月乙亥起三日','广陵城外',
      '杨行密闻高骈被杀，率士卒穿丧服向广陵城哭悼三日。',
      [('杨行密','举哀者'),('高骈','被哀悼者')])
event('zhu_han_killed','朱瑄弟罕援濮州被擒斩',39,'光启三年九月辛卯','范、濮州方向',
      '朱珍攻濮州，朱瑄遣其弟罕率军来援；朱全忠在范迎击，罕被擒斩。',
      [('朱珍','攻濮州者'),('朱瑄','遣援军者'),('朱罕','被擒斩者'),('朱温','以朱全忠名义迎击者')],
      note='原文“瑄遣其弟罕”，按同姓及兄弟关系暂称朱罕，具体身世待补证；“万人”为原文兵数。')
event('zheng_hanzhang_raids_camps','郑汉章破张神剑高霸寨',40,'光启三年十月；具体日未载','广陵外、高邮、海陵',
      '秦彦遣郑汉章攻张神剑、高霸营寨并破之；张神剑奔高邮，高霸奔海陵。',
      [('秦彦','遣军者'),('郑汉章','进攻者'),('张神剑','营寨被破及奔高邮者'),('高霸','营寨被破及奔海陵者')],
      note='原文“五千”为书载兵额，不作实点统计。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(33,41):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {33:'上文八月壬寅朔至丙子跨逾一月，而下文才标九月；历日疑点待据异本核。',34:'未列月日，不承接上一段丙子。',35:'“诬瑄”不能录成朱瑄确曾招诱军士；刘桥伤亡仅为书载；壬子月份待核。',36:'张雄先受秦彦告身、后助杨行密，不能给静态阵营标签；丁卯月份待核；战报数字不核为确数。',38:'厌胜及灾异是秦彦疑惧和王奉仙谶言，不作事实因果。',39:'原文“瑄遣其弟罕”，朱罕身份按亲属称谓暂记并待补证。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(33,41):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=887,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(33,41)],next_paragraph='zztj-v257-y0887-p041',coverage='卷257光启三年条第33—40段；本年续录。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
