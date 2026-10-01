"""Curate consecutive Tongjian volume 261, year 897 paragraphs 49–50."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 51))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0897-p049-p050', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-897-final'
fixed_commit='fbebc6a'
source_specs=[(source,'资治通鉴·卷261·乾宁四年第49—50段','司马光等'),('xintangshu-059-zhang-daogu','新唐书·卷59·张道古兵论','欧阳修、宋祁等')]
reused_source_keys=set()
manifest=[]
for sk,title,author in source_specs:
 d=P/'sources/library'/sk;r=json.loads((d/'paragraph.json').read_text());filename='library/'+sk+'/source.txt';url='https://github.com/greed-216/histree/blob/'+fixed_commit+'/'+str((d/'source.txt').relative_to(ROOT))
 B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='选定TXT逐字导出；电子本，纸本及异文待核。',url=url,note=r['citation']))
 manifest.append(dict(key=sk,file=filename,sha256=hashlib.sha256((d/'source.txt').read_bytes()).hexdigest(),url=url,paragraph_id=r['id'],upstream_locator=r['locator'],transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for n in range(49,51):assert Q[n]['text'] in (P/'sources/library'/source/'source.txt').read_text()
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'王熔':'王镕','国弘信':'罗弘信','硃友裕':'朱友裕','赫连鐸':'赫连铎','硃崇节':'朱崇节','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, set(reused_source_keys)
alias.update({'李彦徽':'李彦徽（湖州）','延王戒丕':'李戒丕','王宗播':'许存','杜弘':'杜洪','嵩从周':'葛从周','硃瑾':'朱瑾','硃宣':'朱瑄','李继徽':'杨崇本','硃朴':'朱朴','韩健':'韩建','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_261_0897_06_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷261·乾宁四年（897）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷261乾宁四年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=897,note=None,quote=None):
    key='event_zztj_261_0897_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_261_0897_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def e(code,title,n,q,actors=(),when=None,place=None,note=None,description=None,year=897):
    return event(code,title,n,when or '897年本段条；确日未载',place,description or title+'。',actors,quote=q,note=note,year=year)
chiefs=[('刘王（黎雅部落首领）','刘王'),('郝王（黎雅部落首领）','郝王'),('杨王（黎雅部落首领）','杨王')]
for name,short in chiefs:person(name,49,f'黎雅间部落首领，主书仅载{short}称号，未载完整姓名')
e('liya_chiefs_two_sides_spy','黎雅三王受西川缯帛及南诏赂而双方侦察',49,'黎、雅间有浅蛮曰刘王、郝王、杨王，各有部落，西川岁赐缯帛三千匹，使觇南诏，亦受南诏赂诇成都虚实。',[(x[0],'接受两方财物侦察者') for x in chiefs],when='段内先前惯常安排；确起止年未载',place='黎州、雅州、成都',year=None,note='三千匹为西川岁赐总述，不分别赋每人三千；浅蛮为史载称呼，不作现代族群认定。')
e('liya_chiefs_collude_generals','黎雅三王与西川大将相表里，教部落纷扰邀姑息',49,'而三王阴与大将相表里，节度使或失大将心，则教诸蛮纷扰。先是节度使多文臣，不欲生事，故大将常籍此以邀姑息，而南诏亦凭之屡为边患。',[(x[0],'与大将相表里者') for x in chiefs],when='段内先前惯常政军背景；确起止年未载',place='西川、黎雅',year=None,note='不猜匿名历任节度与大将姓名，不据三人同行造结盟人物关系；南诏屡边患不造若干缺细节战役。')
e('wang_stops_stipend_kills_shan','王建镇西川后绝旧赐，斩山行章',49,'及王建镇西川，绝其旧赐，斩都押牙山行章以惩之。',[('王建','绝赐斩将者'),('山行章','被斩都押牙')],when='王建镇西川后追叙；确年未载',place='西川',year=None,note='王建任镇不等于本段发生年；复用此前陈敬瑄将、后降王建的山行章，不把死亡定897。')
claim('person',people['山行章'],'description','主书追述山行章为都押牙，在王建镇西川后被斩。',49,quote='及王建镇西川，绝其旧赐，斩都押牙山行章以惩之。',note='确年不明，不补death_year；并非此前888或889交战当时已死。')
claim('person',people['王建'],'description','主书总述王建采取惩处后，邛崃之南不置鄣候、不戍一卒，蛮亦不敢侵盗。',49,quote='邛崃之南，不置鄣候，不戍一卒，蛮亦不敢侵盗。',note='为主书边防效果概括，不推永久无守军或永不侵盗。')
e('zongbo_attacks_nanzhao_chiefs_leak','王建遣王宗播击南诏，三王漏泄军事',49,'其后遣王宗播击南诏，三王漏泄军事',[('王建','遣军者'),('王宗播','领军者')]+[(x[0],'漏泄军事者') for x in chiefs],when='前述安排其后；确年未载，可能跨本年',place='南诏',year=None,note='其后不能定897；王宗播沿已有许存主体。不补胜败、兵数与战场。')
e('wang_executes_liya_chiefs','王建召而斩泄密的黎雅三王',49,'其后遣王宗播击南诏，三王漏泄军事，召而斩之。',[('王建','召斩者')]+[(x[0],'被召斩者') for x in chiefs],when='其后三王泄军事后；确年未载',year=None,note='召斩主语承王建，不补处刑地点日；三王以称号加地域消歧，不猜正式姓名或终身盟约。')
e('zhang_daogu_petition_five_dangers','张道古上疏称国家五危二乱，批评昭宗驭臣',50,'右拾遗张道古上疏，称：“国家有五危、二乱。昔汉文帝即位未几，明习国家事。今陛下登极已十年，而曾不知为君驭臣之道。太宗内安中原，外开四夷，海表之国，莫不入臣。今先朝封域，日蹙几尽。臣虽微贱，窃伤陛下朝廷社稷始为奸臣弄，终为贼臣所有也。”',[('张道古','上疏者'),('唐昭宗','被进谏者')],when='897年年末条；确月日未载',note='五危二乱与奸贼臣等是奏中批评，不拆成已证实五项危机，也不由登极十年推精确即位日。')
e('emperor_demotes_zhang_daogu','昭宗怒，贬张道古施州司户',50,'上怒，贬道古施州司户。',[('唐昭宗','贬谏官者'),('张道古','被贬者')],when='897年上疏后；确月日未载',place='施州',note='贬职不补已抵施州。')
e('emperor_edict_zhang_to_remonstrators','昭宗下诏罪状张道古，宣示谏官',50,'仍下诏罪状道古，宣示谏官。',[('唐昭宗','下诏者'),('张道古','被诏列罪状者')],when='897年贬张后；确月日未载',note='诏列罪状为朝廷处分说法，不将罪名认定为现代已核违法。')
claim('person',people['张道古'],'description','张道古为青州人。',50,quote='道古，青州人也。',note='青州为籍贯，与被贬任地施州分清。')
sk='xintangshu-059-zhang-daogu';record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());q=(P/'sources/library'/sk/'source.txt').read_text().strip();ck=f'claim_zztj_261_0897_06_{len(B["claims"])+1:04d}'
B['claims'].append(dict(key=ck,subject_table='person',subject_key=people['张道古'],field_path='description',claim_text='《新唐书》艺文志著录张道古《兵论》一卷，小注字子美、景福进士第。',source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：正文著录与小注信息分清，仅补人物书目、字和科举记载，不将景福登第定为897；不是对本次上疏细节的独立印证。电子本纸本异文待核。',status='draft'))
supplements=[dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[50]['id'],subject_key=people['张道古'],relation='adds')]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(49,51):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='年末两段连续校核；黎雅三王仅用称号消歧，岁赐、勾连为背景，王建斩山、宗播征南诏及三王被斩确年未载，不强塞897。张道古疏词与贬官、罪状诏分录，书目著录作补证。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=897,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(49,51)],next_paragraph='zztj-v261-y0898-p001',coverage='乾宁四年最后两段，第49—50段；全年是否完成须另核其余批次与下一年年界。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
