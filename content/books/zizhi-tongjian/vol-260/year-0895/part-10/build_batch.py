"""Curate consecutive Tongjian volume 260, year 895 paragraphs 41–44."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p041-p044', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_10_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('emperor_resides_shangshu_after_return','宫室焚毁，唐昭宗寓尚书省',41,'895年八月还京以后；确日未载','尚书省',
      '宫室焚毁，尚未修葺完成，唐昭宗寄居尚书省。百官往往缺袍笏、仆从和马。',[('唐昭宗','寓居者')],quote='时宫室焚毁，未暇完葺，上寓居尚书省，百官往往无袍笏仆马。',note='时述还京后状态，不将所有焚毁事件新定本日；往往不作每位百官均无物。')
event('keyong_campaign_du_tong','李克用授行营都统',41,'895年八月还京后条；确日未载','朝廷',
      '朝廷以李克用为行营都统。',[('李克用','受行营都统者')],quote='以李克用为行营都统。',note='与此前都招讨使分录；主书此处未列守太师中书令，不从补书静默补齐授官。')
event('kong_wei_dies_895','宰相孔纬去世',42,'895年九月癸亥',None,
      '司空兼门下侍郎、同平章事孔纬去世。',[('孔纬','去世者')],note='本段确载去世，保纪年干支，不补地点死因。')
event('zhu_wen_defeats_zhu_xuan_liangshan','朱温亲征朱瑄，梁山败瑄',43,'895年九月辛未','梁山、郓',
      '朱温亲率军攻朱瑄，两军在梁山交战，朱瑄败走回郓。',[('朱温','亲征胜者'),('朱瑄','败走还郓者')],note='硃全忠复用朱温，硃瑄复用朱瑄；郓不作已陷，未载兵数不补。')
event('keyong_intensifies_liyuan_siege','李克用急攻梨园，王行瑜求救李茂贞',44,'895年九月条；确日未载','梨园',
      '李克用加紧进攻梨园，王行瑜向李茂贞求救。',[('李克用','急攻者'),('王行瑜','求救者'),('李茂贞','被求救者')],quote='李克用急攻梨园，王行瑜求救于李茂贞',note='梨园与前段黎园底本异字各保；求救不等于援军已解围。')
event('maozhen_longquan_xianyang_reinforcement','李茂贞遣万人屯龙泉，自将三万屯咸阳旁',44,'895年九月王行瑜求救以后；确日未载','龙泉镇、咸阳之旁',
      '李茂贞派兵一万人驻龙泉镇，自己率三万人驻咸阳附近。',[('李茂贞','遣兵兼自将者')],quote='茂贞遣兵万人屯龙泉镇，自将兵三万屯咸阳之旁。',note='兵数分别从史书保留，不合计推独立总兵力或认已夺咸阳。')
event('keyong_requests_strip_maozhen_again','李克用请求令茂贞归镇削爵，欲分兵讨之',44,'895年九月茂贞援行瑜条；确日未载',None,
      '李克用请求朝廷诏令李茂贞归镇，并削其官爵，打算分兵讨伐。',[('李克用','请求并计划讨者'),('李茂贞','被请削讨者')],quote='克用请诏茂贞归镇，仍削夺其官爵，欲分兵讨之。',note='请求和欲讨均未作批准或已出兵。')
event('emperor_refuses_maozhen_punishment_orders_return','皇帝拒再削讨茂贞，只命归镇和解',44,'895年九月李克用请讨以后；确日未载','朝廷',
      '唐昭宗以李茂贞已自诛李继鹏、此前已赦为由，不许再次削爵讨伐，只诏其归镇，并令李克用与之和解。',[('唐昭宗','裁决遣诏者'),('李茂贞','受归镇诏者'),('李克用','被令和解者')],quote='上以茂贞自诛继鹏，前已赦宥，不可复削夺诛讨，但诏归镇，仍令克用与之和解。',note='帝拒绝与下诏是已发生裁决，茂贞已归镇或两军已和解尚无本段明文。')
event('han_zhi_bin_campaign_deputy','李罕之检校侍中，授邠宁四面副都统',44,'895年九月条；确日未载','邠宁、朝廷',
      '朝廷以昭义节度使李罕之检校侍中，充邠宁四面行营副都统。',[('李罕之','受检校侍中副都统者')],quote='以昭义节度使李罕之检校侍中，充邠宁四面行营副都统。',note='昭义是原段称职，不补此次始授昭义。')
event('shi_yan_yunyang_captures_linghui','史俨云阳败邠宁兵，擒王令诲献之',44,'895年九月条；确日未载','云阳',
      '史俨在云阳击败邠宁军，擒云阳镇使王令诲等人献上。',[('史俨','败军擒将者'),('王令诲','被擒云阳镇使')],quote='史俨败邠宁兵于云阳，擒云阳镇使王令诲等，献之。',note='王令诲与上段王令陶姓名不同，不因同姓令字合并；献之未明送到哪座城，不补受献人或杀害结果。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-895-maozhen-return-hanzhi';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==599)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L599'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·请削茂贞与罕之副都统',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第599页，乾宁二年九月前后段。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=599的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
supplements=[]
def extra(code,text,quote,note,kind='corroborates'):
    assert quote in raw.decode();ck=f'claim_zztj_260_0895_10_{len(B["claims"])+1:04d}';key='event_zztj_260_0895_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation='卷26·唐书二·武皇纪下·乾宁二年九月前后段·原PDF第599页',note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[44]['id'],subject_key=key,relation=kind))
extra('keyong_requests_strip_maozhen_again','《旧五代史》同记李克用请茂贞罢兵、削其官爵。','武皇奉请诏茂贞罢兵，兼请削\n夺茂贞官爵。','请求未作朝廷已经准许。')
extra('emperor_refuses_maozhen_punishment_orders_return','《旧五代史》载诏称茂贞已遣归镇，并戒李克用不得犯其疆；主书此处仅命归镇和解。','诏曰：“茂贞勒兵，盖\n备非常，寻已发遣归镇。”','保为诏书所称，未用此证实茂贞军实际已归镇。','adds')
extra('emperor_refuses_maozhen_punishment_orders_return','《旧五代史》所引诏说李茂贞已诛李继鹏、李继晸，并戒李克用勿犯土疆；主书本段仅提继鹏。','茂贞已诛李继鹏、李继晸，卿可切\n戒兵甲，无犯土疆。','李继晸为补书诏辞新增姓名，身份尚未核；不自动并入李继鹏或其他李继字人物，也不由此另造确定杀人时间。','adds')
extra('han_zhi_bin_campaign_deputy','《旧五代史》补记李克用表请以李罕之为副都统。','又表李罕之为\n副都统。','补表请经过，正式任命用主书依据；未载表请日不补。','adds')
reviews={
 41:'还京宫室未葺、寓尚书省百官往往乏用，与李克用授行营都统分录；状态未推每官皆无袍笏。',
 42:'孔纬九月癸亥去世保原纪年，无地点死因不补。',
 43:'朱温亲征梁山败朱瑄、瑄还郓，稳定主体复用，未作郓城失陷。',
 44:'急攻求援、茂两路屯兵、李请削爵欲分讨、帝拒削只诏归镇和解、李罕之副都统、史俨云阳败擒分录。请求命令与完成结果有别；王令诲不合并令陶。旧史诏辞补继晸身份待考。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,45):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(41,45)],next_paragraph=Q[45]['id'],coverage='第41—44段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
