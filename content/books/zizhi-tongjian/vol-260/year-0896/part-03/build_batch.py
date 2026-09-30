"""Curate consecutive Tongjian volume 260, year 896 paragraphs 8–10."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 49))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0896-p008-p010', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-260-896'
B['sources'] = [dict(key=source,title='资治通鉴·卷260',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/260.txt',note='卷260乾宁三年条；书、卷、年、段落及行号见批次账本。')]
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
    B['claims'].append(dict(key=f'claim_zztj_260_0896_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁三年（896）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷260乾宁三年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=896,note=None,quote=None):
    key='event_zztj_260_0896_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_260_0896_'+code+'_'+pk
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

event('li_sixiao_requests_retirement_recommends_brother','李思孝请退休，荐弟李思敬代职',8,'896年三月条；确日未载','保大、朝廷',
      '保大节度使李思孝上表请求退休，推荐弟弟李思敬接替。',[('李思孝','请退荐弟者'),('李思敬','被推荐弟弟')],quote='保大节度使李思孝表请致仁，荐弟思敬自代',note='底本致仁疑致仕，摘录保字；请退与诏准分开，李思敬不补本姓拓跋或具体年龄。')
relation('李思孝','李思敬','兄长',8,'李思孝是李思敬的兄长。',quote='保大节度使李思孝表请致仁，荐弟思敬自代')
event('li_sixiao_taishi_retired_sijing_liuhou','李思孝授太师致仕，李思敬为保大留后',8,'896年三月诏准退休条；确日未载','保大、朝廷',
      '朝廷诏李思孝为太师退休，以李思敬为保大留后。',[('李思孝','受太师致仕者'),('李思敬','受留后者')],quote='诏以思孝为太师，致仕，思敬为保大留后。',note='诏准明确，留后未作正式节度使，太师不作李思孝继续统兵。')
event('pang_shigu_defeats_yun_majia','朱温遣庞师古伐郓，马颊败郓兵进城下',9,'896年三月条；确日未载','马颊、郓州城下',
      '朱温派庞师古率兵讨郓州，在马颊击败郓军，进抵城下。',[('朱温','遣讨者'),('庞师古','攻郓胜军将')],note='进城下非已入城，郓军未具名不补指挥者或兵数。')
event('gu_quanwu_attacks_yuyao_huang_aid','顾全武攻馀姚，黄晟遣兵助',10,'896年三月己酉','馀姚',
      '顾全武等攻馀姚，明州刺史黄晟派兵助攻。',[('顾全武','攻城者'),('黄晟','遣兵助者')],quote='己酉，顾全武等攻馀姚，明州刺史黄晟遣兵助之',note='等未名者不补成许再思固定参与，黄派兵未作本人亲赴。')
event('gu_captures_dong_xu_zhang','董昌遣徐章救馀姚，顾全武擒之',10,'896年三月己酉攻馀姚条；确日未另载','馀姚',
      '董昌派徐章救馀姚，顾全武将其击败俘获。',[('董昌','遣援者'),('徐章','被擒援将'),('顾全武','击擒者')],quote='董昌遣其将徐章救馀姚，全武击擒之。',note='俘援将不作已经克全馀姚城，也不作徐章已杀。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-niucunjie-896-majia';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==503)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L503'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·牛存节传·庞师古屯马颊',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第503页，乾宁三年夏段；卷次待核，以传名和固定页定位。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=503的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
quote='三年夏，太祖东讨郓州，存节领\n军次故乐亭，扼其要路，都指挥使庞\n师古屯马颊';assert quote in raw.decode()
ck=f'claim_zztj_260_0896_03_{len(B["claims"])+1:04d}';ek='event_zztj_260_0896_pang_shigu_defeats_yun_majia'
B['claims'].append(dict(key=ck,subject_table='event',subject_key=ek,field_path='description',claim_text='《旧五代史》牛存节传乾宁三年夏东讨郓州段，记庞师古屯马颊。',source_key=sk,citation='牛存节传·乾宁三年夏段·原PDF第503页',note='原文：'+quote+'；核对说明：补相同战区驻军记载；该书夏与主书三月各保，不能确认正是同次马颊战，不以此改主书月份，也未提前录年底攻城。',status='draft'))
reviews={
 8:'李请致仁疑致仕保字、荐弟与诏太师致仕留后分录，兄长方向有句，不补本姓。',
 9:'朱遣庞伐郓马颊败军至城下，非已克；旧夏驻马颊为相关战区补证不认同次确证。',
 10:'顾等攻馀姚黄遣助、董徐援被擒分录，未作城已陷，等未名不补许，徐未作已杀。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(8,11):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=896,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(8,11)],next_paragraph=Q[11]['id'],coverage='第8—10段连续整理；本年未完成。',supplements=[dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[9]['id'],subject_key=ek,relation='adds')],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
