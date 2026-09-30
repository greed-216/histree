"""Curate consecutive Tongjian volume 260, year 896 paragraphs 1–3."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 49))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0896-p001-p003', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
people, used, reused = {}, {}, set()
alias.update({'嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_260_0896_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁三年（896）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('zongkui_longzhou_kills_tian','王宗夔攻克龙州杀田昉',1,'896年春正月；确日未载','龙州',
      '西川将王宗夔攻克龙州，杀刺史田昉。',[('王宗夔','攻州杀刺史者'),('田昉','被杀刺史')],quote='春，正月，西川将王宗夔攻拔龙州，杀刺史田昉。',note='王宗夔按原名，不凭宗字推养子关系，未补兵数。')
event('ma_yin_dingsheng_defeats_jiang','刘建锋遣马殷讨蒋勋，攻破定胜寨',1,'896年正月丁已；底本日字如此','定胜寨',
      '刘建锋派都指挥使马殷率兵讨蒋勋，攻破定胜寨。',[('刘建锋','遣将者'),('马殷','都指挥使攻寨者'),('蒋勋','被讨者')],quote='丁已，刘建锋遣都指挥使马殷将兵讨蒋勋，攻定胜寨，破之。',note='已疑巳保底本，马殷复用全站人物；破寨不作蒋已死或整个邵州收复。')
event('an_renyi_fleet_huzhou','安仁义舟师至湖州欲渡江援董昌',2,'896年正月辛未','湖州',
      '安仁义率舟师到湖州，想渡江援董昌。',[('安仁义','舟师将'),('董昌','意图援救对象')],quote='辛未，安仁义以舟师至湖州，欲渡江应董昌',note='欲渡未作已经渡江或董援成功。')
event('qian_gu_xu_guard_xiling','钱镠遣顾全武许再思守西陵阻渡',2,'896年正月辛未条','西陵',
      '钱镠派武勇都指挥使顾全武、都知兵马使许再思守西陵，安仁义不能渡江。',[('钱镠','遣守者'),('顾全武','守西陵武勇指挥使'),('许再思','守西陵都知兵马使'),('安仁义','受阻未渡者')],quote='钱镠遣武勇都指挥使顾全武、都知兵马使许再思守西陵，仁义不能度。',note='不能度为本次结果，未补船数或另造已发生水战。')
event('dong_sends_tang_yuan_defend','董昌遣汤臼守石城袁邠守馀姚',2,'896年正月条；确日未另载','石城、馀姚',
      '董昌派将汤臼守石城、袁邠守馀姚。',[('董昌','遣守者'),('汤臼','石城守将'),('袁邠','馀姚守将')],quote='昌遣其将汤臼守石城，袁邠守馀姚。',note='汤臼按底本文字建检索名，未核其他字形前不改；派守不是两城已经战败。')
event('cunxin_ten_thousand_shenxian','李克用遣李存信万骑借魏援兖郓，军莘县',3,'896年闰月；确日未载','魏、莘县',
      '李克用派蕃汉都指挥使李存信领万骑借道魏救兖郓，驻军莘县。',[('李克用','遣援者'),('李存信','万骑都指挥使')],quote='闰月，克用遣蕃、汉都指挥使李存信将万骑假道于魏以救兗、郓，军于莘县。',note='主书万骑与旧史步骑三万并列，闰月按正月后二月前理解闰正月但保原名，不换算公历。')
event('zhu_wen_warns_luo_about_keyong','朱温遣人警告罗弘信李克用欲吞河朔',3,'896年闰月莘县驻军后条；确日未载',None,
      '朱温派人告诉罗弘信，李克用有吞河朔之志，返军时魏道将可忧。',[('朱温','遣游说者'),('罗弘信','受游说者')],quote='硃全忠使人谓罗弘信曰：“克用志吞河朔，师还之日，贵道可忧。”',note='侵魏意图是朱温游说说辞，未作李克用已公开发此计划；使者未名不补。')
event('cunxin_army_violates_wei_people','李存信军纪律不严，侵暴魏民',3,'896年闰月条；确日未载','魏',
      '李存信约束军众不严，部兵侵扰魏民。',[('李存信','未严束众之帅')],quote='存信戢众不严，侵暴魏人。',note='未载受害人数、具体村镇或罪种，未把未知士卒逐名补入。')
event('luo_night_attacks_cunxin_three_wan','罗弘信三万兵夜袭，李存信败保洺州',3,'896年闰月条；夜袭确日未载','莘县、洺州',
      '罗弘信怒，发三万兵夜袭李存信军。李军溃退保洺州，损失士卒十分之二三，并弃大量军需兵械。',[('罗弘信','夜袭者'),('李存信','败退者')],quote='弘信怒，发兵三万夜袭之。存信军溃退。保洺州，丧士卒什二三，委弃资粮兵械万楼',note='什二三保比例不乘万骑换确定伤亡人数，丧不全部等于死；万楼疑转录讹字保摘录，不推准确物资件数。')
event('shi_li_relief_cut_off_896','史俨李承嗣军被隔不能返回',3,'896年闰月魏袭以后；确日未载',None,
      '史俨、李承嗣军被隔断，无法返回。',[('史俨','被隔将'),('李承嗣','被隔将')],quote='史俨、李承嗣之军隔绝不得还。',note='位置未载不补，也不作已经全军覆没或投降。')
event('luo_breaks_hedong_aligns_bian','罗弘信与河东断交，转向汴',3,'896年闰月夜袭以后；关系持续起讫未另载','魏、河东、汴',
      '罗弘信自此与河东断绝关系，专心依向汴。',[('罗弘信','断交转向者')],quote='弘信自是与河东绝，专志于汴。',note='关系转向保事件，不由此推血缘或永久盟约文书。')
event('zhu_wen_courts_luo_gifts','朱温北向拜受罗弘信赠遗，以六兄相称',3,'896年闰月条背景；每有赠遗起讫未载',None,
      '朱温图兖郓又担心罗弘信在后，每遇罗赠遗，对使者向北拜受，称罗为年长一倍的六兄。罗相信他的礼遇，朱温得专意东方。',[('朱温','礼遇游说者'),('罗弘信','受礼遇者')],year=None,quote='金忠方图兗、郓，畏弘信议其后，弘信每有赠遗，全忠必对使者北向拜授之，曰：“六兄于予，倍年以长，固非诸邻之比。”弘信信之，全忠以是得专意东方。',note='金忠疑全忠、拜授疑拜受，保底本文字；每有为习惯背景，不定所有赠受在896，不由六兄造亲兄或确定结义边，倍年不推具体年龄。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-896-weibo-cunxin';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==602)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L602'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·魏博李存信军',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第602页，乾宁三年正月段承上。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=602的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
supplements=[]
def extra(code,text,quote,note,kind='corroborates'):
    assert quote in raw.decode();ck=f'claim_zztj_260_0896_01_{len(B["claims"])+1:04d}';key='event_zztj_260_0896_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation='卷26·武皇纪下·乾宁三年正月段承上·原PDF第602页',note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[3]['id'],subject_key=key,relation=kind))
extra('cunxin_ten_thousand_shenxian','《旧五代史》记李存信步骑三万与李承嗣史俨会军拒汴，主书此段作万骑。','乃令都指\n挥使李存信将步骑三万与李承嗣、史\n俨会军，以拒汴人。','兵种与数目并列异记，不合算四万或用一书改另一书。','conflicts')
extra('cunxin_army_violates_wei_people','《旧五代史》记存信御军无法，侵魏刍牧者。','存信御兵无法，稍侵魏之刍\n牧者','补受扰者叙法，未给具体人数或地名。','adds')
extra('luo_night_attacks_cunxin_three_wan','《旧五代史》同记罗弘信三万兵攻李存信，存信退保洺州。','宏信乃与汴帅通，出师三万攻\n存信军。存信揭营而退，保于洺州。','罗宏信与主书罗弘信按既有同一人物处理；该句未载夜，不补匿名姓名。')
reviews={
 1:'正月宗夔龙州杀田与丁已马讨破定胜分录，日字疑巳保原，未推蒋死。',
 2:'辛未安舟至欲渡、钱遣顾许阻渡、董汤袁守分录，欲渡与已渡区别，汤按臼保字。',
 3:'闰月李援军、朱游说、李侵魏、罗三万夜袭退损、史李隔军、罗断河东、朱每赠礼遇分录；兵数异记独存，不乘比例推死人。六兄非血亲，疑字未默改，习惯年未定。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,4):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=896,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,4)],next_paragraph=Q[4]['id'],coverage='第1—3段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
