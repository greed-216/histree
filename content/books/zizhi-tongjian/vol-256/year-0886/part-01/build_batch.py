"""Curate consecutive Tongjian volume 256, year 886 paragraphs 1–10."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 57))
B = {'format_version': 1, 'batch_key': 'zztj-v256-y0886-p001-p010', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','郭禹':'成汭'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_256_0886_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷256·光启二年（886）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷256光启二年条所见人物：{name}。',biography=None,status='draft')
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

event('zhang_yu_changzhou','张郁作乱并攻陷常州',1,'光启二年春正月','常州',
      '镇海牙将张郁作乱，攻陷常州。',[('张郁','作乱并攻城者')])
event('li_wang_memorial','李克用、王重荣上表请僖宗还宫并诛田令孜',2,'光启二年正月条；具体日未载','河中、行在',
      '李克用回军河中，与王重荣共同上表，请皇帝回宫，并列田令孜罪状、请求诛杀。',
      [('李克用','上表者'),('王重荣','上表者'),('田令孜','被指控者')],
      note='罪状是李克用、王重荣表章中的主张；本条只记录上表行为。')
event('yang_fugong_privy','杨复恭复任枢密使',2,'光启二年正月条；具体日未载',None,
      '朝廷再次任飞龙使杨复恭为枢密使。',[('杨复恭','受任者')])
event('tian_abducts_emperor','田令孜劫持僖宗出奔宝鸡',3,'光启二年正月戊子夜','凤翔、宝鸡',
      '田令孜请求皇帝往兴元，皇帝不从；当夜田令孜领兵入宫，迫使车驾往宝鸡，朝臣多不知情。',
      [('田令孜','领兵胁驾者')],note='原文“上不从”“劫上幸宝鸡”支持胁迫；出发地未在本段明记，地点仅保留宝鸡和凤翔行在背景。')
event('du_kong_follow','杜让能、孔纬等追及车驾',3,'戊子夜后至翌日','宝鸡',
      '杜让能得知车驾离去，独自追上皇帝于宝鸡；次日孔纬等随后抵达。',
      [('杜让能','追驾者'),('孔纬','次日追驾者')])
event('kong_wei_court','孔纬任御史大夫并奉命召百官',3,'光启二年正月庚寅','宝鸡',
      '朝廷任孔纬为御史大夫，命其返召百官，皇帝留宝鸡等待。',[('孔纬','受任及召集者')])
event('zhu_li_realignment','朱玫、李昌符转而与李克用、王重荣合',3,'田令孜胁驾之后；具体日未载',None,
      '《通鉴》称朱玫、李昌符因不满田令孜且顾忌李克用、王重荣势强，转与二人合。',
      [('朱玫','转而联合者'),('李昌符','转而联合者'),('李克用','被联合者'),('王重荣','被联合者')],
      note='本段记当时政治合纵，关系具有时段性；不录为永久结盟。')
event('zhu_mei_fengxiang','朱玫奉召领兵至凤翔',4,'光启二年正月癸巳','凤翔',
      '萧遘通过李松年召朱玫迎车驾；癸巳朱玫率步骑五千抵凤翔。',
      [('萧遘','遣召者'),('李松年','传递者'),('朱玫','率军到凤翔者')],
      note='五千为本书所载兵数，不据此推算全部兵力。')
event('kong_wei_summons_officials','孔纬催百官赴行在',4,'光启二年正月癸巳后；具体日未载','凤翔',
      '孔纬敦促百官前往皇帝行在；萧遘、裴澈以田令孜随驾为由称病未往。孔纬后来请求李昌符派骑兵护送，李昌符允之。',
      [('孔纬','催百官及请护卫者'),('萧遘','称病未往者'),('裴澈','称病未往者'),('李昌符','派骑护送者')])
event('panshi_attack','瑄宁、凤翔兵在潘氏追击车驾',5,'光启二年正月后条；具体日未载','潘氏',
      '原文作“瑄宁、凤翔兵”追逼车驾，于潘氏击败神策指挥使杨晟；“瑄宁”地军名待校。',
      [('杨晟','在潘氏战败者')],
      note='仓库底本和维基文库均作“瑄宁”；疑有讹字，暂不改作邠宁或据此确定军镇。')
event('yang_sheng_ganyi','朝廷置感义军，命杨晟守散关',5,'潘氏战后；具体日未载','兴州、凤州、散关',
      '田令孜奉皇帝离宝鸡，留禁军守石鼻；朝廷于兴、凤二州置感义军，任杨晟为节度使、守散关。',
      [('田令孜','奉驾出宝鸡者'),('杨晟','任感义节度使及守关者')])
event('wang_jian_escort','王建、晋晖护送车驾越大散岭',6,'光启二年正月后条；具体日未载','大散岭、散关',
      '朝廷以王建、晋晖为清道斩斫使。王建领兵在前，携传国宝随驾；李昌符焚阁道，王建扶皇帝越过。',
      [('王建','前驱护驾者'),('晋晖','清道斩斫使'),('李昌符','焚阁道者')])
event('zhu_mei_sanguan','朱玫围宝鸡并攻散关未克',6,'车驾入散关时；具体日未载','宝鸡、散关',
      '朱玫围宝鸡，石鼻守军溃散后进攻散关，未能攻下。',[('朱玫','攻关者')])
event('li_yun_captured','嗣襄王煴滞留，被朱玫所得',6,'车驾过散关时；具体日未载','遵涂驿、凤翔',
      '嗣襄王煴因病未能随驾，被朱玫得到并带回凤翔。',
      [('李煴','因病滞留并被带走者'),('朱玫','带回凤翔者')],
      note='原文称“嗣襄王煴”；据王号和所指建立李煴实体，底本与其他电子文本有煴/熅字形差异，暂不据此另造一人。')
claim('person',people['李煴'],'aliases','李煴在本卷称嗣襄王煴。',6,'嗣襄王煴，肃宗之玄孙也')
event('li_keyong_taiyuan','李克用返回太原',7,'光启二年正月庚戌','太原',
      '李克用返回太原。',[('李克用','返太原者')])
event('february_petition','王重荣、朱政、李昌符再请诛田令孜',8,'光启二年二月',None,
      '王重荣、朱政、李昌符再次上表请求诛杀田令孜。',
      [('王重荣','上表者'),('朱政','上表者'),('李昌符','上表者'),('田令孜','被指控者')],
      note='底本和维基文库均作“朱政”，身份未定；暂不擅自与朱玫合并。')
event('zheng_congdang_office','郑从谠任守太傅兼侍中',9,'光启二年二月条；具体日未载',None,
      '前东都留守郑从谠获任守太傅兼侍中。',[('郑从谠','受任者')])
event('shi_junshe_blocks','石君涉受朱玫、李昌符命阻车驾',10,'光启二年二月后至三月前','山南西道',
      '朱玫、李昌符命石君涉设置栅障、焚烧驿舍阻断险要，车驾绕道艰行，邠军在后追逼。',
      [('朱玫','遣令者'),('李昌符','遣令者'),('石君涉','设障者')])
event('shi_junshe_flees','石君涉弃镇归朱玫',10,'光启二年三月壬午','山南西道',
      '石君涉弃镇，逃归朱玫。',[('石君涉','弃镇者'),('朱玫','收留者')])

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(1,11):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {3:'戊子劫驾、次日追驾、庚寅任命和朱玫等改合分录；“罪状”是表章内容。',5:'“瑄宁”疑讹，原样保留，不擅改作某军名。',6:'嗣襄王煴本段尚未被册立；仅录因病滞留并被带走。',8:'原文“硃政”身份未定，未擅与朱玫合并。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,11):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=256,year=886,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph='zztj-v256-y0886-p011',coverage='卷256光启二年条前十段；本年尚未完成。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
