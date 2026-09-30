"""Curate consecutive Tongjian volume 258, year 890 paragraphs 9–16."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 44))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0890-p009-p016', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias = {'赫连鐸':'赫连铎','硃友裕':'朱友裕','硃实':'朱实','石和':'石君和','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0890_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·大顺元年（890）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else ['石和'] if name=='石君和' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷258大顺元年条所见人物：{name}。',biography=None,status='draft')
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

event('ma_jingyan_takes_runzhou','马敬言乘虚据润州',9,'890年二月后条；具体日未载','润州',
      '杨行密遣马敬言率兵乘虚袭据润州。',[('杨行密','遣军者'),('马敬言','袭据将领')],note='五千为书载军数，不独立确认为实点。')
event('li_you_qingcheng','李友屯青城拟攻常州',9,'890年二月后条；具体日未载','青城、常州',
      '李友率兵屯青城，准备攻常州。《通鉴》称李友为合肥人。',[('李友','驻军及拟攻者')],note='“将攻”只记录计划，不记为已经攻取；二万为书载数。')
event('wujin_battle','安仁义刘威田頵败刘锋于武进',9,'890年二月后条；具体日未载','武进、润州',
      '安仁义、刘威、田頵在武进击败刘锋；马敬言、安仁义、刘威屯润州。《通鉴》称刘威为慎县人。',
      [('安仁义','胜方将领及驻军者'),('刘威','胜方将领及驻军者'),('田頵','胜方将领'),('刘锋','败方将领'),('马敬言','驻军者')])
event('li_keyong_attacks_yun','李克用攻云州东城，李匡威来援',10,'890年二月丙子条前后；具体日未逐项记载','云州',
      '李克用率兵攻云州防御使赫连铎，攻取东城；赫连铎向李匡威求救，李匡威率兵来援。',
      [('李克用','攻城者'),('赫连铎','守方求援者'),('李匡威','率援军者')],note='底本赫连鐸复用赫连铎；三万为书载援军数，不推定全云州被攻占。')
event('an_jinjun_death_shen_defects','安金俊中流矢死，申信降赫连铎',10,'890年二月丙子','云州战场',
      '邢洺团练使安金俊中流矢死亡，河东万胜军使申信叛降赫连铎；幽州军抵达后，李克用撤军。',
      [('安金俊','中箭去世者'),('申信','叛降者'),('赫连铎','受降者'),('李克用','撤军者')],note='云州战场按上下文概略保留，未核具体阵地；不据叛降推定申信此后终身所属。')
event('shi_aids_shi_pu','李克用遣石和援时溥',11,'890年二月后条；具体日未载','徐州方向',
      '时溥向河东求救，李克用遣其将石和率五百骑前往援助。',
      [('时溥','求援者'),('李克用','遣援者'),('石和','本段以石和名义赴援者')],note='石和与后段石君和依同一援徐脉络及旧五代史对应记载暂归同人；别名依据作为独立补证，五百为书载数。')
event('li_kexiu_beaten','李克用因供具责打李克修',12,'890年三月前；具体日未载','潞州',
      '李克用巡视潞州，因供具不厚而怒，辱骂并笞打昭义节度使李克修。',
      [('李克用','巡视及责打者'),('李克修','被责打者')],note='原文供具不厚不展开为具体贡赋或贪污指控。')
event('li_kexiu_death_kegong','李克修卒，李克用表李克恭留后',12,'890年三月','潞州、昭义',
      '《通鉴》记李克修惭愤成疾，三月去世；李克用上表请其弟、决胜军使李克恭为昭义留后。',
      [('李克修','病卒者'),('李克用','表请者'),('李克恭','被表请为留后者')],note='惭愤成疾为书载解释，不作现代医学死因；表请不写成诏命已下。')
rk='relationship_person_li_keyong_person_李克恭_兄长'
B['person_relationships'].append(dict(key=rk,person_a_key=people['李克用'],person_b_key=people['李克恭'],relation_type='兄长',description='《通鉴》称李克恭为李克用之弟；李克用是李克恭的兄长。',status='draft'))
claim('person_relationship',rk,'description','李克用是李克恭的兄长。',12,quote='克用表其弟决胜军使克恭为昭义留后。')
event('yang_ningguo','宣歙赐宁国军号，杨行密任节度使',13,'890年三月后条；具体日未载','宣歙',
      '朝廷赐宣歙军号宁国，以杨行密为节度使。',[('杨行密','节度使受任者')],note='与889年观察使任命分为两次，不提前改写旧任命。')
event('zhang_yun_suzhou_revolt','张筠逐张绍光附时溥，朱全忠来讨',14,'890年四月','宿州',
      '宿州将张筠驱逐刺史张绍光，归附时溥，朱全忠率诸军讨伐。',
      [('张筠','逐刺史及归附者'),('张绍光','被逐刺史'),('时溥','受归附者'),('朱温','以朱全忠名义率军讨伐者')])
event('zhu_youyu_captures_shi','朱友裕击时溥军擒石君和',14,'890年四月；具体日未载','砀山',
      '时溥遣兵侵掠砀山，朱全忠遣牙内都指挥使朱友裕出击，《通鉴》记杀三千余人，俘获石君和。',
      [('时溥','遣兵侵掠者'),('朱温','以朱全忠名义遣军者'),('朱友裕','出击将领'),('石君和','被俘将领')],note='三千余为书载杀获数；本段只记石君和被俘，死亡与日干支若用他书需另引。')
rk='relationship_person_zhu_wen_person_朱友裕_父亲'
B['person_relationships'].append(dict(key=rk,person_a_key=people['朱温'],person_b_key=people['朱友裕'],relation_type='父亲',description='《通鉴》称朱友裕为朱全忠之子；朱温是朱友裕的父亲。',status='draft'))
claim('person_relationship',rk,'description','朱温是朱友裕的父亲。',14,quote='友裕，全忠之子也。')
event('ren_conghai_defeated','任从海援邛州败后欲降，被陈敬瑄杀',15,'890年四月乙丑','邛州、蜀州',
      '陈敬瑄遣蜀州刺史任从海率兵救邛州，任从海战败后欲以蜀州降王建，被陈敬瑄杀死；陈敬瑄以徐公鉥代为蜀州刺史。',
      [('陈敬瑄','遣援、处死及任用者'),('任从海','战败欲降被杀者'),('王建','拟受降者'),('徐公鉥','蜀州刺史代任者')],note='欲降不记成已经投降；原文二万为书载兵数，不定位任从海刑杀地点。')
event('zhu_shi_surrenders_jia','朱实以嘉州降王建',15,'890年四月丙寅','嘉州',
      '嘉州刺史朱实举州投降王建。',[('朱实','以州投降者'),('王建','受降者')])
event('wen_wujian_surrenders_rong','文武坚执谢承恩降王建',15,'890年四月丙子','戎州、僰道',
      '僰道土豪文武坚拘执戎州刺史谢承恩，投降王建。',
      [('文武坚','执刺史投降者'),('谢承恩','被执刺史'),('王建','受降者')])
event('petition_against_li_keyong','赫连铎李匡威朱全忠奏请讨李克用',16,'890年四月后条；具体日未载','',
      '赫连铎、李匡威上表请求讨李克用。朱全忠亦上言称李克用终为国患，请率汴、滑、孟三军与河北三镇共讨，并请求朝廷命大臣为统帅。',
      [('赫连铎','表请讨伐者'),('李匡威','表请讨伐者'),('朱温','以朱全忠名义奏请者'),('李克用','被奏请讨伐对象')],note='国患为朱全忠奏言，方案为奏请，不提前记录为出兵、朝廷诏命或已成联盟。')

# Independent evidence identifying the differently named relief commander.
extra='jiuwudaishi-890-shi-junhe'
from urllib.parse import quote as urlquote
extraurl='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/twenty-four-histories/'+urlquote('18旧五代史.jsonl')
pages=[r for r in map(json.loads,(ROOT/'resources/derived/twenty-four-histories/18旧五代史.jsonl').read_text().splitlines()) if r['pdf_page']==583]
extra_text=pages[0]['text'];(P/'sources'/f'{extra}.txt').write_text(extra_text)
B['sources'].append(dict(key=extra,title='旧五代史·唐武皇纪·大顺元年条',source_type='primary',author='薛居正等',edition='仓库PDF提取文本第583页；未核纸本。',url=extraurl,note='对应援助时溥的将领姓名；与通鉴石和记载对读。'))
manifest=json.loads((P/'sources/manifest.json').read_text());manifest.append(dict(key=extra,file=f'{extra}.txt',sha256=hashlib.sha256(extra_text.encode()).hexdigest(),url=extraurl,upstream='resources/derived/twenty-four-histories/18旧五代史.jsonl#pdf_page=583',transformation='Decode JSONL page 583 text exactly; retain PDF extraction line breaks.'));(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
ck='claim_zztj_258_0890_02_shi_alias_supplement'
quote='时徐州时溥为汴军所攻，遣使来\n求援，武皇命石君和由兗、郓以赴\n之。';assert quote in extra_text
B['claims'].append(dict(key=ck,subject_table='person',subject_key=people['石君和'],field_path='aliases',claim_text='通鉴援徐将石和与后段石君和暂归同人：旧五代史同一援徐记载明确称石君和。',source_key=extra,citation='唐武皇纪·大顺元年援徐条·PDF第583页',note=f'原文：{quote}；核对说明：结合通鉴本年援徐与砀山被俘脉络暂归同人；保存石和别名，尚未核纸本姓名异文。',status='draft'))
ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={9:'袭据润州、李友拟攻、武进交战分录；拟攻不记攻取。',10:'云州只克东城；安金俊战死、申信叛降和撤军分录；旧五代史云州攻战系三月，与通鉴本段月序有异，未补确日。',11:'石和与石君和依旧五代史同一援徐记载暂归同人，保留别名与独立补证。',12:'责打与三月病卒、表请李克恭分录；表请不作诏授。',14:'朱温为朱友裕父亲；擒石君和不依本段推死。',15:'欲降不记已降；三处州县归降分录。',16:'奏请、国患说法不写成诏命、已成联盟或实际出兵。'}
for n in range(9,17):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
    if n in reviews:ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,17):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=890,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph='zztj-v258-y0890-p017',coverage='卷258大顺元年第9—16段连续录入；本年未完。',supplements=[dict(claim_key=ck,source_book='jiuwudaishi',primary_paragraph_id=Q[11]['id'],subject_key=people['石君和'],relation='adds')],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
