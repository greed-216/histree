"""Curate consecutive Tongjian volume 256, year 886 paragraphs 41–48."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 57))
B = {'format_version': 1, 'batch_key': 'zztj-v256-y0886-p041-p048', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-256-884'
prior = json.loads((ROOT / 'content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json').read_text())
B['sources'] = [next(s for s in prior['sources'] if s['key'] == source)]
raw = (ROOT / 'resources/derived/tongjian/256.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/256.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_256_0886_05_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷256·光启二年（886）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷256光启二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=886,note=None,quote=None):
    key='event_zztj_256_0886_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_256_0886_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('zhang_xiong_suzhou','张雄、冯弘铎据苏州，自号天成军',41,'光启二年十月后条；具体日未载','苏州',
      '张雄、冯弘铎因得罪时溥，率众渡江袭取苏州；张雄自称刺史，部众渐多，自号天成军。',
      [('张雄','袭取苏州及自称刺史者'),('冯弘铎','同领兵者'),('时溥','此前节度使')],
      note='“五万”“千余战舰”均为本书后续壮大时的记数，不等于初渡江时已有规模。')
event('zhuge_shuang_death','诸葛爽去世，诸将立诸葛仲方为留后',42,'光启二年十月后条；具体日未载','河阳',
      '河阳节度使诸葛爽去世，刘经、张全义拥立其子诸葛仲方为留后。',
      [('诸葛爽','去世者'),('刘经','拥立者'),('张全义','拥立者'),('诸葛仲方','被立留后者')])
rel='relationship_'+people['诸葛爽']+'_'+people['诸葛仲方']+'_父子'
B['person_relationships'].append(dict(key=rel,person_a_key=people['诸葛爽'],person_b_key=people['诸葛仲方'],relation_type='父子',description='《通鉴》卷256称诸葛仲方为诸葛爽之子。',status='draft'))
claim('person_relationship',rel,'description','诸葛仲方为诸葛爽之子。',42,'立爽子仲方为留后')
event('li_kexiu_xingzhou_fail','李克修攻邢州不克而还',43,'光启二年十月后条；具体日未载','邢州',
      '李克修进攻邢州，未攻下而返回。',[('李克修','领兵攻城者')])
event('qian_liu_yuezhou','钱镠攻下越州，刘汉宏奔台州',44,'光启二年十一月丙戌','越州、台州',
      '钱镠攻下越州，刘汉宏逃往台州。',[('钱镠','攻取越州者'),('刘汉宏','逃往台州者')])
event('zhang_xiao_mutiny','张骁举兵攻义成州城，安师儒杀夏侯晏、杜标',45,'光启二年十一月条；具体日未载','义成治所',
      '安师儒把政事交给夏侯晏、杜标，军中不满；小校张骁聚众攻城，安师儒斩二人以平息军中怨气。',
      [('安师儒','杀二人及安抚军中者'),('夏侯晏','被杀者'),('杜标','被杀者'),('张骁','举兵者')])
event('zhu_yu_kills_zhang','朱瑄遣朱裕诱杀张骁',45,'张骁举兵后；具体日未载','滑州方向',
      '朱瑄意图取得滑州，遣朱裕诱杀张骁。',[('朱瑄','遣兵者'),('朱裕','诱杀者'),('张骁','被杀者')])
event('zhu_zhen_huazhou','朱全忠部攻下滑州并俘安师儒',45,'光启二年十一月条；具体日未载','滑州',
      '朱全忠先遣朱珍、李唐宾袭滑州，部队趁大雪一夜抵城，登城攻下，俘安师儒。朱全忠以胡真知义成留后。',
      [('朱温','以朱全忠名义遣兵及任将者'),('朱珍','攻城者'),('李唐宾','攻城者'),('安师儒','被俘者'),('胡真','知义成留后者')],
      note='原文记“百梯并升”，只按其叙事保留，不推定真实梯数及兵力。')
event('tian_lingzi_chengdu','田令孜到成都，请求寻医获准',46,'光启二年十一月条；具体日未载','成都',
      '田令孜抵成都，请求寻医，获准。',[('田令孜','请求者')],
      note='原文“请寻医，许之”未具名批准者，也未记具体病情。')
event('fengzhou_taken','诸军拔凤州，满存任防御使',47,'光启二年十二月戊寅','凤州',
      '诸军攻下凤州，朝廷任满存为凤州防御使。',[('满存','受任者')])
event('yang_fugong_bounty','杨复恭传檄悬赏朱玫首级',48,'光启二年十二月戊寅之后','关中',
      '杨复恭向关中传檄，称取得朱玫首级者可授静难节度使。',
      [('杨复恭','传檄者'),('朱玫','悬赏对象')],
      note='这是一项悬赏承诺，不先记为已兑现任命。')
event('wang_xingyu_kills_zhu_mei','王行瑜返京擒杀朱玫',48,'光启二年十二月甲寅','长安',
      '王行瑜多次战败后担心朱玫责罚，率军自凤州返京，于朱玫视事时将其擒斩，并杀其党。',
      [('王行瑜','擒杀者'),('朱玫','被杀者')],
      note='杀其党“数百人”为本书所载数；不把檄文悬赏直接写成王行瑜唯一动机。')
event('changan_plunder','朱玫被杀后长安诸军大乱焚掠',48,'光启二年十二月甲寅之后','长安',
      '朱玫被杀后诸军大乱，焚掠京城；《通鉴》记士民因失衣而冻死。',
      note='死伤情形按本段史家叙述，不换算具体人数。')
event('li_yun_flees_hezhong','裴澈、郑昌图奉襄王煴奔河中',48,'光启二年十二月甲寅之后','长安、河中',
      '裴澈、郑昌图率百官奉襄王煴逃往河中。',
      [('裴澈','奉煴出奔者'),('郑昌图','奉煴出奔者'),('李煴','出奔者')],
      note='原文“二百余人”是随行百官概数，不等于最终生还数。')
event('wang_chongrong_kills_yun','王重荣诱捕并杀襄王煴',48,'襄王煴抵河中后；具体日未载','河中',
      '王重荣佯作迎奉，捕获并杀襄王煴，囚裴澈、郑昌图；《通鉴》记随行百官死者近半。',
      [('王重荣','诱捕及杀人者'),('李煴','被杀者'),('裴澈','被囚者'),('郑昌图','被囚者')],
      note='“百官死者殆半”是史家约数，不推成具体死亡人数。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(41,49):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {41:'五万及千余战舰为逐渐发展规模，非袭苏州当日规模。',42:'诸葛仲方为诸葛爽之子，父子关系有原文支持。',45:'军中内乱、朱瑄诱杀张骁、朱全忠攻滑州分录。',48:'檄文悬赏、王行瑜杀朱玫、京城焚掠、襄王煴出奔及王重荣杀煴分录。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,49):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=256,year=886,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(41,49)],next_paragraph='zztj-v256-y0886-p049',coverage='卷256光启二年条第41至48段；本年尚未完成。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
