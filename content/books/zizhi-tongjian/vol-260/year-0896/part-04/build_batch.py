"""Curate consecutive Tongjian volume 260, year 896 paragraphs 11–13."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 49))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0896-p011-p013', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0896_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁三年（896）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('zhu_wen_splits_river_huazhou','河涨将毁滑州，朱温决分二河为害更甚',11,'896年夏四月辛酉','滑州',
      '河水上涨将毁滑州城，朱温命决分为两河，夹滑城向东，灾害更重。',[('朱温','命决河者')],note='将毁非城已全毁，不补伤亡人数、河道坐标或现代水利效果。')
event('keyong_huanshui_attacks_wei','李克用攻洹水杀魏兵万余，进攻魏州',12,'896年四月条；确日未载','洹水、魏州',
      '李克用攻击罗弘信，攻洹水，杀魏兵万余，继而进攻魏州。',[('李克用','攻魏者'),('罗弘信','被攻者')],note='万余为史载战果，进攻非魏州已克，不补守将和准确死亡名单。')
person('刘建锋',13,'武安节度使，史述得志后嗜酒不亲政')
claim('person',people['刘建锋'],'biography','史书称刘建锋得志后嗜酒、不亲政事。',13,quote='武安节度使刘建锋既得志，嗜酒，不亲政事。',note='性情与习惯为背景，不定每次饮酒、失政均在896四月。')
event('liu_jianfeng_affair_chen_wife','刘建锋与陈赡妻私通',13,'卷260乾宁三年条背景；起始未载',None,
      '史书记长直兵陈赡妻美，刘建锋与她私通。',[('刘建锋','史载私通者'),('陈赡','其妻被私通的军士')],year=None,quote='长直兵陈赡妻美，建锋私之。',note='妻未名，不补姓氏、个人UUID或具体婚姻始年；美为史家描述，私通起始不强定896。')
event('chen_shan_kills_liu_jianfeng','陈赡以铁挝击杀刘建锋',13,'896年四月条；确日未载','武安',
      '陈赡袖藏铁挝，将刘建锋击杀。',[('陈赡','击杀者'),('刘建锋','被杀者')],quote='赡袖铁挝击杀建锋',note='武安为事属军镇，不补具体府院或金属兵器现代形制。')
event('generals_kill_chen_choose_zhang','诸将杀陈赡，迎张佶为留后',13,'896年四月刘建锋被杀后条；确日未载','武安',
      '诸将杀陈赡，迎行军司马张佶为留后。',[('陈赡','被诸将杀者'),('张佶','被迎留后行军司马')],quote='诸将杀赡，迎行军司马张佶为留后。',note='诸将未名不补马殷或李琼亲杀；迎为非朝廷已诏任正式节度。')
event('zhang_ji_horse_injures_thigh','张佶将入府，马踶啮伤左髀',13,'896年四月迎留后以后；确日未载',None,
      '张佶将入府时，马忽然踢咬，伤其左大腿。',[('张佶','受马伤者')],quote='佶将入府，马忽踶啮，伤左髀。',note='保左髀伤，不作死亡或现代诊断；踶啮是踢咬，不把马写作名为忽踶啮。')
event('zhang_ji_recommends_summons_ma','张佶荐马殷为主，以牒召之',13,'896年四月张受伤以后；确日未载','武安、邵州',
      '马殷尚未攻下邵州。张佶向诸将称马殷勇有谋、宽厚乐善胜于自己，是应立之主，发牒召马殷。',[('张佶','荐主发牒者'),('马殷','被召攻邵将')],quote='时马殷攻邵州未下，佶谢诸将曰：“马公勇而有谋，宽厚乐善，吾所不及，真乃主也。”乃以牒召之。',note='赞语归张，发牒与马已到分开，未把此段未下邵州写成已经攻克。')
event('yao_yanzhang_persuades_ma','姚彦章劝犹豫的马殷赴长沙',13,'896年四月张召马以后；确日未载','邵州',
      '马殷犹豫未行，听直军将、汝南人姚彦章称他与刘建锋张佶一体，刘遇祸张受伤，天命人望应归他。',[('姚彦章','劝赴者'),('马殷','被劝者')],quote='殷犹豫未行，听直军将汝南姚彦章说殷曰：“公与刘龙骧、张司马，一体人也，今龙骧遇祸，司马伤髀，天命人望，舍公尚谁属哉！”',note='刘龙骧按本段刘建锋称号，一体不造血缘；天命人望为姚游说，不作超自然确证。')
claim('person',people['姚彦章'],'biography','姚彦章是汝南人，主书称听直军将。',13,quote='听直军将汝南姚彦章',note='籍贯职衔按原文，未把听直改成未经校核的他职。')
event('ma_goes_changsha_li_qiong_stays','马殷令李琼留攻邵州，赴长沙',13,'896年四月姚劝以后；确日未载','邵州、长沙',
      '马殷令亲从都指挥使李琼留攻邵州，自己直接去长沙。',[('马殷','留将赴长沙者'),('李琼','奉留攻邵指挥使')],quote='殷乃使亲从都指挥使李琼留攻邵州，径诣长沙。',note='李琼非朱琼，留攻非已攻克；未提前录入马殷到后受位仪式。')

from urllib.parse import quote as urlquote
supplements=[]
def addsource(sk,book,path,page,title):
    raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==page)
    url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+f'#L{page}'
    (P/'sources'/(sk+'.txt')).write_bytes(raw)
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author='欧阳修' if book=='新五代史' else '薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note=f'原PDF第{page}页，相关纪年及校核见各条引用。'))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation=f'提取JSONL pdf_page={page}的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
    return raw.decode()
def extra(sk,book,page,raw,code,n,text,q,note,kind='corroborates'):
    assert q in raw;ck=f'claim_zztj_260_0896_04_{len(B["claims"])+1:04d}';key='event_zztj_260_0896_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation=('梁书·太祖纪·乾宁三年四月辛酉' if book=='旧五代史' else '卷66·楚世家·湖南交接段')+f'·原PDF第{page}页',note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book=book,primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
sk='jiuwudaishi-taizu-896-hua-river';book='旧五代史';raw=addsource(sk,book,'resources/derived/twenty-four-histories/18旧五代史.jsonl',27,'旧五代史·梁书太祖纪·滑城决河')
extra(sk,book,27,raw,'zhu_wen_splits_river_huazhou',11,'《旧五代史》同记四月辛酉河涨将坏滑城，命分二河夹城向东，灾害甚。','四月辛酉，河东泛涨，将坏滑\n城。帝令决堤岸以分其势为二河，夹\n滑城而东，为害滋甚。','该书河东泛涨与主书河涨各保，不把河东字样自动指李克用军；未换算现代河段。')
sk='xinwudaishi-066-896-jianfeng-chen';book='新五代史';raw=addsource(sk,book,'resources/derived/twenty-four-histories/19新五代史.jsonl',1427,'新五代史·卷66·楚世家·刘建锋陈赡')
extra(sk,book,1427,raw,'chen_shan_kills_liu_jianfeng',13,'《新五代史》同记刘建锋与陈赡妻私通，被陈赡铁器击杀；字作建峰、铁楇。','军卒陈赡妻有色，建峰\n私之，赡怒，以铁楇击杀建峰。','刘建峰与主书刘建锋、楇与挝保异字，不另建人物或推不同凶器。')
sk='xinwudaishi-066-896-zhang-ma-summons';raw=addsource(sk,book,'resources/derived/twenty-four-histories/19新五代史.jsonl',1428,'新五代史·卷66·楚世家·张佶推马殷')
extra(sk,book,1428,raw,'generals_kill_chen_choose_zhang',13,'《新五代史》先叙推张佶为帅及马伤、张荐主，再记诸将杀陈赡并遣姚迎马；主书先杀陈迎张。','诸将乃共杀赡，磔其尸，遣\n姚彦章迎殷于邵州。','与主书次序及张牒召、姚劝说的叙法并列；补书磔尸为附记，不用它改主书先后。','conflicts')
extra(sk,book,1428,raw,'zhang_ji_horse_injures_thigh',13,'《新五代史》同记张佶入府马踢咬伤髀，未说左侧。','佶将入府，乘\n马辄踶啮，伤佶髀。','主书左髀与补书髀详略区别，不增补其他伤情。')
reviews={
 11:'河涨将坏城、命分二河反更害保过程，无死亡数不补，旧书河东泛涨字保。',
 12:'洹水杀魏万余进魏州，非已克州，兵数史载不算精确。',
 13:'刘嗜酒背景、私陈妻起年未定、陈杀刘、诸杀陈迎张、马伤、张荐召、姚劝及马留李赴长沙分录，匿名妻不补姓，张赞姚天命归言辞，补书杀陈次序异记独存。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,14):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=896,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(11,14)],next_paragraph=Q[14]['id'],coverage='第11—13段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
