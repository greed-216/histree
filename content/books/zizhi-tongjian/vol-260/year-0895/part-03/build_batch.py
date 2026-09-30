"""Curate consecutive Tongjian volume 260, year 895 paragraphs 7–10."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p007-p010', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-260-895'
B['sources'] = [dict(key=source,title='资治通鉴·卷260',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/260.txt',note='卷260乾宁二年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/260.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/260.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
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
alias.update({'嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_260_0895_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷260乾宁二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=895,note=None,quote=None):
    key='event_zztj_260_0895_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_260_0895_'+code+'_'+pk
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

alias.update({'李溪':'李磎','李谿':'李磎','李存审':'符存审','刘廉':'刘谦'})
event('wang_gong_yao_attack_ke','王珙王瑶举兵攻王珂',7,'895年二月条；确日未载',None,
      '王重盈之子保义节度使王珙、晋州刺史王瑶举兵攻击王珂。',[('王珙','保义节度使出兵者'),('王瑶','晋州刺史出兵者'),('王珂','被攻者')],quote='王重盈之子保义节度使珙、晋州刺史瑶举兵击王珂')
person('王重盈',7,'王珙、王瑶之父')
relation('王重盈','王珙','父亲',7,'王重盈是王珙之父。',quote='王重盈之子保义节度使珙、晋州刺史瑶')
relation('王重盈','王瑶','父亲',7,'王重盈是王瑶之父。',quote='王重盈之子保义节度使珙、晋州刺史瑶')
event('wang_gong_yao_dispute_ke_identity','王珙王瑶上表并致朱全忠书，争王珂继嗣',7,'895年王氏争继立时；确日未载',None,
      '王珙、王瑶上表声称王珂非王氏子，又致书朱全忠称王珂原为家中苍头、不应为嗣。',[('王珙','争嗣上表致书者'),('王瑶','争嗣上表致书者'),('王珂','被指称无继嗣资格者'),('朱温','以朱全忠名收书者')],quote='表言珂非王氏子。与硃全忠书，言“珂本吾家苍头，不应为嗣。”',note='这是争嗣双方一方的说法，不当已证王珂非王氏；前段生父与养父关系仍保留。')
event('wang_ke_petitions_keyong_aid','王珂上表自陈，求援李克用',7,'895年争继立时；确日未载',None,
      '王珂上表申述，并向李克用求援。',[('王珂','上表自陈与求援者'),('李克用','被求援者')],quote='珂上表自陈，且求援于李克用。',note='未给表全文，不补具体反驳；求援不作李已出援兵。')
event('emperor_sends_wang_mediation','唐昭宗遣中使谕解王氏争端',7,'895年王珂自陈求援后；确日未载',None,
      '唐昭宗派中使劝解王氏争端。',[('唐昭宗','派中使谕解者')],quote='上遣中使谕解之。',note='中使未具名；谕解不表示成功和解。')
event('li_xi_reappointed_chancellor','李磎再授户部侍郎同平章事',8,'895年二月乙未','朝廷',
      '唐昭宗重李磎文学，再任其为户部侍郎、同平章事；《通鉴》本段作李溪。',[('唐昭宗','重文学而授相者'),('李磎','以李溪名再任相者')],note='复承894年罢相；李溪、李谿、李磎为同人书载字形，沿用已有主体，不新建三人。')
event('zhu_wen_shanfu_reinforcement','朱全忠军单父，声援朱友恭',9,'895年二月己酉','单父',
      '朱全忠驻军单父，为朱友恭提供声援。',[('朱温','以朱全忠名驻军声援者'),('朱友恭','受声援者')],note='军于单父仅明确朱全忠驻军，不推出朱友恭移驻单父或单父发生会战。')
event('keyong_recommends_rengong_garrison','李克用表刘仁恭为卢龙留后，留兵戍守',10,'895年二月条；返晋阳以前，确日未载','卢龙、幽州',
      '李克用上表推刘仁恭为卢龙留后，并留下军队戍守。',[('李克用','上表与留戍兵者'),('刘仁恭','所表卢龙留后者')],quote='李克用表刘仁恭为卢龙留后，留兵戍之',note='表不写为唐廷此日已正式授节度使；留兵人数未载。')
event('keyong_returns_jinyang_895','李克用还晋阳',10,'895年二月壬子','晋阳',
      '李克用返回晋阳。',[('李克用','返晋阳者')],quote='壬子，还晋阳。')

sk='jiuwudaishi-058-895-li-xi-glyph'
path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==1391)
from urllib.parse import quote as urlquote
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L1391'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷58·李琪传·李谿字形',source_type='primary',author='薛居正等',edition='仓库PDF派生文本；未核纸本。',url=url,note='李琪传回述昭宗朝文学人物，第1391页；只补李谿姓名字形，不用于断本年再任相。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=1391的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
ck=f'claim_zztj_260_0895_03_{len(B["claims"])+1:04d}'
quote='昭宗时，李谿父子以文学知名。'
assert quote in raw.decode()
B['claims'].append(dict(key=ck,subject_table='person',subject_key=people['李磎'],field_path='aliases',claim_text='《旧五代史》李琪传作李谿，补李磎主体的姓名字形引用。',source_key=sk,citation='卷58·唐书三十四·列传十·李琪传·原PDF第1391页',note='原文：'+quote+'；核对说明：与已归档北梦琐言李磎及通鉴李溪同一昭宗朝文学宰相名对应；只补字形书证，不把李琪十八岁事定为895，不称正式改名。',status='draft'))

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={
 7:'举兵与争嗣上表、朱书、自陈求援、中使劝解分别录；苍头非王氏子为争嗣指控非事实；重盈父关系有原句，求援非已出兵，谕解非已和解。',
 8:'复授相承894罢；李溪归李磎稳定主体，旧史李谿字形补独立人物别名出处，不将李琪早年事定895。',
 9:'朱全忠军单父声援友恭，不推两人同驻或会战。',
 10:'表仁恭与留戍兵、壬子归晋阳分录；留兵无数，表留后非朝廷已授节度。',
}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(7,11):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(7,11)],next_paragraph=Q[11]['id'],coverage='第7—10段连续整理；本年未完成。',supplements=[dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[8]['id'],subject_key=people['李磎'],relation='adds')],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
