"""Curate consecutive Tongjian volume 257, year 888 paragraphs 33–40."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 50))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0888-p033-p040', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_257_0888_05_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·文德元年（888）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('luo_hongxin_weibo_jiedushi','罗弘信正式授魏博节度使',33,'888年七月后、八月前；具体日未载','魏博',
      '朝廷任原权知魏博留后的罗弘信为魏博节度使。',
      [('罗弘信','受任者')],
      note='与前段“权知留后”区分为正式授节度使。')
event('zhu_takes_cai_south','朱全忠取蔡州南城',34,'888年八月戊辰','蔡州南城',
      '朱全忠攻取蔡州南城。',
      [('朱温','以朱全忠名义攻取者'),('秦宗权','蔡州守方主将')],
      note='取南城不等于全蔡州或秦宗权已降。')
event('yuan_xi_plans_xuanzhou','袁袭建议杨行密取宣州',35,'888年八月；具体日未载','庐州、宣州方向',
      '杨行密惧孙儒进逼，原想轻兵袭洪州；袁袭认为江西钟传强而宣州赵锽新据、易图，建议联孙端、张雄攻宣州，杨行密采纳。',
      [('杨行密','筹谋及采纳者'),('袁袭','进言者'),('孙儒','逼迫方'),('钟传','被评估的江西主将'),('赵锽','拟攻宣州守将'),('孙端','建议联合者'),('张雄','建议联合者')],
      note='钟传难图、赵锽失众等均为袁袭当时判断，不当作已核定军力民心事实。')
event('yang_crosses_yangtze','杨行密留蔡俦守庐州并渡江',35,'888年八月；具体日未载','庐州、糁潭、江南',
      '杨行密令蔡俦守庐州，亲率诸将从糁潭渡江。',
      [('杨行密','率军渡江者'),('蔡俦','留守庐州者')],
      note='“糁潭”照电子底本史载地名，未核现代坐标与异文。')
event('sun_zhang_lose_to_zhao','孙端张雄为赵锽所败',36,'888年八月；具体日未载','宣州方向',
      '孙端、张雄两军先为赵锽击败。',
      [('孙端','败方将领'),('张雄','败方将领'),('赵锽','胜方主将')])
event('yang_defeats_su_qi','杨行密于曷山败苏塘漆朗',36,'孙端张雄败后；具体日未载','曷山、宣州',
      '赵锽部将苏塘、漆朗屯曷山。袁袭建议杨行密坚壁诱其松懈，杨行密采纳并击败二将，随后围宣州。',
      [('赵锽','守方主将'),('苏塘','败方将领'),('漆朗','败方将领'),('袁袭','献策者'),('杨行密','进攻与围城者')],
      note='“曷山”照底本，不推定现代地名；兵数“二万”为书载，诱敌策略按原文归属袁袭。')
event('tao_ya_defeats_zhao_qianzhi','陶雅败赵乾之于九华',36,'杨行密围宣州时；具体日未载','九华、池州',
      '赵锽之兄赵乾之自池州率军救宣州，杨行密遣陶雅在九华击败其军；赵乾之奔江西，陶雅受任池州制置使。',
      [('赵锽','被援救守将'),('赵乾之','援军将领及败走者'),('杨行密','遣将者'),('陶雅','胜方及受任者')],
      note='原文称“锽兄乾之”，据此暂称赵乾之；任命不推为池州已无抵抗。')
event('zhu_lifts_cai_siege','朱全忠自蔡州撤军',37,'888年九月','蔡州',
      '朱全忠因粮运不继，并认为秦宗权已残破而引军撤离蔡州。',
      [('朱温','以朱全忠名义撤军者'),('秦宗权','被围目标')],
      note='“不足忧”为朱全忠判断，不当作蔡州威胁已经消失。')
event('zhu_zhen_escorts_liu','朱全忠遣朱珍护刘瓚赴楚州',37,'888年九月丙申','楚州方向',
      '朱全忠遣朱珍领兵护送楚州刺史刘瓚赴任。',
      [('朱温','以朱全忠名义遣将者'),('朱珍','护送将领'),('刘瓚','赴任刺史')],
      note='兵数“五千”为书载；本段只记遣行，不推为已到楚州。')
event('qian_qiu_attacks_suzhou','钱镠遣钱銶攻徐约于苏州',38,'888年九月；具体日未载','苏州',
      '钱镠遣从弟钱銶率军攻苏州徐约。',
      [('钱镠','遣军者'),('钱銶','率军从弟'),('徐约','苏州守方')],
      note='原文明示“从弟”，不推定钱銶的具体父系支属或攻城结果。')
event('zhu_zhen_beats_xu_troops','朱珍刘瓚击徐军取沛滕',39,'888年十月','沛县、滕县',
      '徐州军阻朱珍、刘瓚前进，朱珍等击退之并取沛、滕二县。',
      [('朱珍','进攻方将领'),('刘瓚','同行赴任者')],
      note='“斩获万计”为原文战报，不据此核定死伤或俘虏数；“徐兵”未在本段具名统领。')
event('li_kexiu_captures_xi','李克修败奚忠信于辽州',40,'888年十月；具体日未载','辽州、晋阳',
      '孟方立遣奚忠信率军袭辽州，李克修迎击大败其军，俘奚忠信送晋阳。',
      [('孟方立','遣军者'),('奚忠信','被俘将领'),('李克修','迎击者')],
      note='“三万”为原文兵数，不作实点。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(33,41):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {33:'罗弘信由权知留后转授节度使，官职变化独立记。',34:'蔡州南城陷不等于整个蔡州陷落。',35:'袁袭对江西与宣州形势为当时谋议；糁潭地名照底本。',36:'孙端张雄先败，杨行密后败苏塘漆朗，陶雅再败赵乾之，依序分录。',37:'朱全忠认为秦宗权不足忧是其判断；刘瓚尚在赴任途中。',39:'徐兵未具名统领，战报数字不核为确数。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(33,41):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=888,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(33,41)],next_paragraph='zztj-v257-y0888-p041',coverage='卷257文德元年条第33—40段；本年续录。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
