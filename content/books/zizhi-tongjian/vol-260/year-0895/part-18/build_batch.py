"""Curate consecutive Tongjian volume 260, year 895 paragraphs 70–74."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p070-p074', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_18_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('ge_congzhou_retained_yanzhou_895','朱温离兖州，留葛从周守寨',70,'895年朱温离兖州时；确月日未载','兗州',
      '朱温离开兖州时，留葛从周领兵驻守，朱瑾闭城不再出战。',[('朱温','留将者'),('葛从周','领兵留守者'),('朱瑾','闭城者')],quote='硃全忠之去兗州也，留葛从周将兵守之，硃瑾闭城不复出',note='之去追接此前撤军，不认朱温本日又撤第二次；守之是城外营守，不作兖州城已属朱温。')
event('ge_congzhou_feigned_relief_ambush','葛从周诈称邀援，夜潜回寨设伏',70,'895年末条；确月日未载','兗州故寨',
      '葛从周将还，扬言天平、河东援兵到、自己去西北截击，夜半偷偷返回旧寨。',[('葛从周','诈言设伏者')],quote='从周将还，乃扬言“天平、河东救兵至，引兵西北邀之，”夜半，潜归故寨。',note='援兵到为诱敌扬言，不作已核到达；旧寨不补准确坐标。')
event('ge_congzhou_defeats_zhu_jin_captures_sun','朱瑾出攻旧寨，葛从周击败擒孙汉筠',70,'895年末条；设伏夜后，确日未载','兗州故寨',
      '朱瑾以为葛从周精兵全出，出军攻寨；葛从周突击，杀千余人，擒都将孙汉筠后返回。',[('朱瑾','误判出攻者'),('葛从周','突击胜者'),('孙汉筠','被擒朱瑾都将')],quote='瑾以从周精兵悉出，果出兵攻寨。从周突出奋击，杀千馀人，擒其都将孙汉筠而还。',note='千余为史载战果，不补孙被杀或以后降职。')
event('qian_liu_jian_shizhong_895','钱镠加兼侍中',71,'895年末条；确月日未载','朝廷',
      '镇海节度使钱镠加兼侍中。',[('钱镠','加衔者')],note='加侍中非新任镇海；未载当日朝觐不补。')
event('zhang_fan_dies_895','彰义节度使张鐇去世',72,'895年末条；确月日未载',None,
      '彰义节度使张鐇去世。',[('张鐇','去世节度使')],quote='彰义节度使张鐇薨',note='地点死因未载不补。')
event('zhang_lian_acting_liuhou','张琏权知彰义留后',72,'895年末张鐇去世后条；确月日未载','彰义',
      '朝廷以张鐇之子张琏暂任留后。',[('张琏','权知留后者')],quote='以其子琏权知留后。',note='权知留后为临时职务，不作正式节度使，姓从父取。')
relation('张鐇','张琏','父亲',72,'张鐇是张琏的父亲。',quote='彰义节度使张鐇薨，以其子琏权知留后。')
event('zhu_brothers_request_hedong_relief','朱瑄朱瑾屡受攻，民财困而告急河东',73,'895年末告急条；屡攻起讫未另载','兗州、郓州、河东',
      '朱瑄、朱瑾多次受朱温攻击，百姓失去耕种机会、财力困乏，二人向河东告急。',[('朱瑄','告急者'),('朱瑾','告急者'),('朱温','屡攻之帅')],quote='硃瑄、硃瑾屡为硃全忠所攻，民失耕稼，财力俱弊。告急于河东',note='屡攻为累积背景，不另算本年固定次数或所有受害人数。')
event('keyong_sends_shi_li_via_wei_895','李克用遣史俨李承嗣数千骑借道魏援二朱',73,'895年末告急以后；确月日未载','魏、兗州、郓州',
      '李克用派大将史俨、李承嗣率数千骑借道魏以救二朱。',[('李克用','遣援者'),('史俨','率骑援将'),('李承嗣','率骑援将')],quote='李克用遣大将史俨、李承嗣将数千骑假道于魏以救之。',note='数千为合载兵数，借道意图与是否已经获得许可分清；未提前录896年借道许可及后续阻断。')
event('jia_sheng_fears_jiang_xuanhui','家晟与蒋玄晖有隙而惧祸',74,'895年末条背景；嫌隙起始未载',None,
      '安州防御使家晟与朱温亲吏蒋玄晖有嫌隙，担心遭祸。',[('家晟','有隙惧祸者'),('蒋玄晖','与家晟有隙朱温亲吏')],quote='安州防御使家晟与硃全忠亲吏蒋玄晖有隙，恐及祸',year=None,note='旧怨起始未定年，惧祸为其顾虑，不作蒋玄晖已经实施杀害。')
event('jia_liu_chen_seize_guizhou','家晟刘士政陈可璠三千兵袭桂州杀周元静',74,'895年末条；系列行动确月日未载','桂州',
      '家晟与指挥使刘士政、兵马监押陈可璠率三千兵袭桂州，杀经略使周元静，家晟取代其职。',[('家晟','袭州代职者'),('刘士政','同袭指挥使'),('陈可璠','同袭兵马监押'),('周元静','被杀经略使')],quote='与指挥使刘士政、兵马监押陈可璠将兵三千袭桂州，杀经略使周元静而代之。',note='三千合载，未定每人分兵数；与二将同行不作血亲或结义，代职不是朝廷已诏任家晟。')
event('chen_kefan_kills_jia_sheng','家晟醉侮陈可璠，被其手刃',74,'895年末条；袭桂州后，确日未载','桂州',
      '家晟醉后侮辱陈可璠，陈可璠亲手杀死家晟。',[('家晟','被杀者'),('陈可璠','手刃者')],quote='晟醉侮可璠，可璠手刃之',note='保叙事先后，不补家晟确日或酒宴地点。')
event('liu_shizheng_chosen_chen_deputy','陈可璠推刘士政知军府，自为副使',74,'895年末条；家晟被杀后，确日未载','桂州',
      '陈可璠推刘士政掌军府，自己为副使。',[('陈可璠','推主自为副使者'),('刘士政','被推知军府者')],quote='推士政知军府事，可璠自为副使。',note='推知军府与朝廷正式诏任分开，副使具体全衔未载不补。')
event('liu_shizheng_guiguan_imperial_appointment','朝廷诏刘士政为桂管经略使',74,'895年末条；推知军府后，确日未载','桂管、朝廷',
      '朝廷随即诏刘士政为桂管经略使。',[('刘士政','正式受经略使者')],quote='诏即以士政为桂管经略使。',note='诏任依据明确，不推该年全部政变环节同日发生。')
claim('person',people['蒋玄晖'],'biography','蒋玄晖是吴人。',74,quote='玄晖，吴人也。',note='吴为史载籍贯范围，不补具体县或现代坐标。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-taizu-895-ge-congzhou-yanzhou';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==27)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L27'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·梁书太祖纪·葛从周兖州胜军',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第27页，乾宁二年十二月段；卷次待核，以固定文件页定位。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=27的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
quote='十二月，葛\n从周领兵复伐兗。既至，与朱瑾战于\n垒下，杀千余众，擒其将孙汉筠已下\n二十人，遂旋师。';assert quote in raw.decode()
ck=f'claim_zztj_260_0895_18_{len(B["claims"])+1:04d}';ek='event_zztj_260_0895_ge_congzhou_defeats_zhu_jin_captures_sun'
B['claims'].append(dict(key=ck,subject_table='event',subject_key=ek,field_path='description',claim_text='《旧五代史》记十二月葛从周兖州垒下胜朱瑾，殺千余、擒孙汉筠以下二十人后旋师；主书详诈言设伏。',source_key=sk,citation='梁书·太祖纪·乾宁二年十二月段·原PDF第27页',note='原文：'+quote+'；核对说明：月份及俘二十为补书详载，主书仅孙汉筠未列其余；复伐与主书留守设伏叙法并列，不据此另造第二场确定战事。',status='draft'))
reviews={
 70:'此前朱温去与葛留守、诈言援至夜返、朱出被伏擒孙分录，之去不是第二次撤，守非占城，旧史复伐和十二月并列。',
 71:'钱镠加兼侍中，不作新任镇海。',
 72:'张鐇卒与子琏权知留后分录，父亲方向明，权知非正式节度。',
 73:'民耕财困为屡攻背景，告急与遣史李数千借魏救分录，不提前套896借道答应或被隔。',
 74:'家蒋旧怨未定年；三千袭杀代家、醉侮手刃、推刘自副、诏刘正任分录，吴籍贯单记。系列月日未载不强同日。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(70,75):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(70,75)],next_paragraph='zztj-v260-y0896-p001',coverage='第70—74段连续整理；发布核验后审核全年覆盖。',supplements=[dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[70]['id'],subject_key=ek,relation='adds')],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
