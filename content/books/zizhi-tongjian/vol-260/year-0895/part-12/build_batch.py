"""Curate consecutive Tongjian volume 260, year 895 paragraphs 49–51."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p049-p051', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_12_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('emperor_gives_chen_to_keyong','唐昭宗赐魏国夫人陈氏给李克用',49,'895年十月戊子',None,
      '唐昭宗将魏国夫人陈氏赐给李克用；史书称其才色冠后宫。',[('唐昭宗','赐陈氏者'),('陈氏（魏国夫人）','被赐魏国夫人'),('李克用','受赐者')],quote='魏国夫人陈氏，才色冠后宫；戊子，上以赐李克用。',note='陈氏按所载称号消歧，不补名、生卒或籍贯；才色为史家评价，赐予不自动推正妻婚姻关系。')
event('keyong_orders_urgent_liyuan_attack','李克用命李罕之李存信急攻梨园',49,'895年十月戊子后条；确日未另载','梨园',
      '李克用命李罕之、李存信等加紧进攻梨园。',[('李克用','命攻者'),('李罕之','奉命急攻者'),('李存信','奉命急攻者')],quote='克用令李罕之、李存信等急攻梨园',note='此段李存信明文与前段李存贞异记分别保，不以此改写前段领军者。')
event('liyuan_abandoned_ambush_three_forts','梨园守军粮尽弃城，李罕之等邀击克三寨',49,'895年十月急攻梨园后条；确日未载','梨园等三寨',
      '城内粮尽，守军弃城逃走，李罕之等截击，杀万余人，攻克梨园等三寨。',[('李罕之','邀击克寨者')],quote='城中食尽，弃城走。罕之等邀击之，所杀万馀人，克梨园等三寨',note='万余为史载杀人数，非补书擒二百人数；三寨另外两寨未具名不补。')
event('capture_xingyu_son_yuanfu_liyuan','梨园战后获王行瑜子知进与李元福',49,'895年十月克梨园条；确日未另载','梨园等三寨',
      '李克用军俘王行瑜之子知进及大将李元福等人。',[('王知进','被俘王行瑜之子'),('李元福','被俘大将')],quote='获王行瑜子知进及大将李元福等',note='俘者按前文李克用军，不确指独由李罕之亲擒；未载处决不补。')
person('王行瑜',49,'被俘知进之父')
relation('王行瑜','王知进','父亲',49,'王行瑜是知进的父亲；按父姓以王知进为检索名。',quote='获王行瑜子知进')
event('keyong_camps_liyuan','李克用进驻梨园',49,'895年十月克三寨后条；确日未另载','梨园',
      '李克用进军驻梨园。',[('李克用','进屯者')],quote='克用进屯梨园。')
event('wang_brothers_burn_ningzhou_flee','王行约王行实烧宁州逃走',49,'895年十月庚寅','宁州',
      '王行约、王行实烧宁州后逃走。',[('王行约','烧宁州遁者'),('王行实','烧宁州遁者')],quote='庚寅，王行约、王行实烧宁州遁去。',note='未载逃往何处；不补全城建筑尽毁、平民死亡数。')
event('keyong_petitions_su_wenjian_jingnan','李克用奏请苏文建为静难，催赴镇兼理宁州',49,'895年十月王氏兄弟遁后条；确日未载','静难、宁州',
      '李克用奏请以匡国节度使苏文建为静难节度使，催其赴镇，暂以宁州治理并招抚降人。',[('李克用','奏请催赴者'),('苏文建','被请任静难与催赴者')],quote='克用奏请以匡国节度使苏文建为静难节度使，趣令赴镇，且理宁州，招抚降人。',note='奏请非朝廷明确批准，催赴与已到任区分；且理宁州保暂理含义，不补永久移镇。')
event('emperor_moves_back_danei','唐昭宗迁居大内',50,'895年十月条；确日未载','大内',
      '唐昭宗迁居大内。',[('唐昭宗','迁居者')],note='与还京后寓尚书省分开，不补具体宫殿名。')
event('zhu_wen_ge_congzhou_yanzhou_siege','朱温遣葛从周击兖州并以大军继，癸卯围城',51,'895年十月癸卯围城；派兵日未另载','兗州',
      '朱温派都将葛从周攻兖州，自己率大军随后，癸卯围兖州。',[('朱温','遣将率军继者'),('葛从周','都将攻城者')],note='围城非已经攻克；未具名守将不加参与者，未补兵数。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-895-liyuan-captives-ningzhou';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==600)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L600'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·梨园俘获与宁州',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第600页，乾宁二年十月段。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=600的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
supplements=[]
def extra(code,text,quote,note,kind='corroborates'):
    assert quote in raw.decode();ck=f'claim_zztj_260_0895_12_{len(B["claims"])+1:04d}';key='event_zztj_260_0895_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation='卷26·武皇纪下·乾宁二年十月段·原PDF第600页',note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[49]['id'],subject_key=key,relation=kind))
extra('capture_xingyu_son_yuanfu_liyuan','《旧五代史》补俘知进并母丘氏、李元福等二百人送阙庭。','生擒行\n瑜之子知进，并母丘氏、大将李元福\n等二百人，送赴阙庭。','二百为该书俘者合数，非斩杀数；母丘氏身份关系先保引文，未由短句推完整配偶家谱。','adds')
extra('wang_brothers_burn_ningzhou_flee','《旧五代史》同记庚寅王行约王行实烧劫宁州逃走。','庚寅，王行\n约、王行实烧劫宁州遁走','独立出处保该书烧劫措辞。')
extra('keyong_petitions_su_wenjian_jingnan','《旧五代史》记李克用表苏文建为邠州节度使，且以宁州为治所。','武皇表苏文建为邠州节度\n使，且于宁州为治所。','主书静难与该书邠州职地称谓各保，不认新的第二次任命；表为不作已获诏准。','adds')
reviews={
 49:'赐陈氏、命急攻、粮尽弃城截击克三寨、俘知进元福、进屯、庚寅烧宁遁、奏苏任镇分别录。赐不推妻，父亲关系方向王行瑜→知进，未载出生年不补。旧史俘二百母丘氏与送阙、邠州宁州补证独存。',
 50:'迁居大内不同于前批还京居尚书省，不补宫殿名。',
 51:'遣葛攻兖、自以军继、癸卯围城为过程，不作已克，不补守将。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(49,52):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(49,52)],next_paragraph=Q[52]['id'],coverage='第49—51段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
