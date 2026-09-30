"""Curate consecutive Tongjian volume 260, year 895 paragraphs 19–24."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p019-p024', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_05_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

alias.update({'李溪':'李磎','李谿':'李磎','硃延寿':'朱延寿','李存审':'符存审','刘廉':'刘谦'})
event('lu_xisheng_removed','陆希声罢相为太子少师',19,'895年四月条；具体日未载','朝廷',
      '户部侍郎、同平章事陆希声罢相，为太子少师。',[('陆希声','罢相改少师者')],note='承正月任相，不补罢相罪因、诏日。')
event('yang_shouzhou_siege_stalls','杨行密围寿州不克，准备撤还',20,'895年四月庚寅以前；确日未载','寿州',
      '杨行密围寿州未克，准备撤回。',[('杨行密','围城未克将还者')],quote='杨行密围寿州，不克，将还',note='将还是准备，不作已经离城；承本年丁亥围寿，未计算围城天数。')
event('zhu_yanshou_takes_shouzhou','朱延寿再攻寿州，一鼓克城执江从勖',20,'895年四月庚寅','寿州',
      '朱延寿请求再试攻寿州，一鼓攻克，俘刺史江从勖。',[('朱延寿','请再攻并克城者'),('江从勖','被执寿州刺史')],quote='庚寅，其将硃延寿请试往更攻，一鼓拨之，执剌史江从勖。',note='拨疑拔、剌史疑刺史保字；一鼓非已知攻城小时数，执不作已杀。')
event('zhu_yanshou_acting_shouzhou','杨行密命朱延寿权知寿州团练使',20,'895年攻克寿州以后；确日未另载','寿州',
      '杨行密以朱延寿暂管寿州团练使事务。',[('杨行密','命权知者'),('朱延寿','权知寿州团练使者')],quote='行密以延寿权知寿州团练使。',note='权知按原文保留，不换成正式节度使。')
event('bian_army_attacks_shouzhou','汴兵数万攻寿州，城中兵少惧',20,'朱延寿权知寿州未几；确年待考','寿州',
      '汴军数万攻击寿州，城中兵少，吏民恐惧。',[('朱延寿','权知守城者')],year=None,quote='未几，汴兵数万攻寿州，州中兵少，吏民忷惧。',note='未几未另载确年，不强定895；汴兵没有具名将帅，不自动补朱温亲征，数万为书载概数。')
event('li_hou_ten_flags_fail','李厚领十旗击汴兵失利',20,'汴兵攻寿州时；确年待考','寿州',
      '朱延寿规定军中每旗二十五骑，命黑云队长李厚领十旗击汴兵，未胜。',[('朱延寿','制旗编并命出击者'),('李厚','黑云队长领十旗者')],year=None,quote='延寿制，军中每旗二十五骑。命黑云队长李厚将十旗击汴兵，不胜',note='保存每旗及旗数，不据编制推城中总兵数或实际无缺员；不胜不作全军覆灭。')
event('li_hou_chai_seek_reinforcement','朱延寿欲斩李厚，柴再用助请增兵',20,'李厚首战不胜以后；确年待考','寿州',
      '朱延寿欲斩李厚。李厚称众寡不敌，愿加兵再战，败则死；都押牙柴再用也替他求情，朱延寿增给五旗。',[('朱延寿','欲斩而增兵者'),('李厚','请益兵再战者'),('柴再用','都押牙代请者')],year=None,quote='延寿将斩之，厚称众寡不敌，愿益兵更往，不胜则死。都押牙汝阳柴再用亦为之请，乃益以五旗。',note='将斩为未执行处分；众寡不敌为李厚自辩，增五旗不是重开五旗之外新军种。')
event('shouzhou_defenders_defeat_bian','李厚再战、柴再用助，朱延寿乘胜败汴兵',20,'增五旗以后；确年待考','寿州',
      '李厚殊死再战，柴再用相助，朱延寿尽众乘势进击，汴军败走。',[('李厚','殊死战者'),('柴再用','助战者'),('朱延寿','悉众乘胜者')],year=None,quote='厚殊死战，再用助之，延寿悉众乘之，汴兵败走。',note='汴军败走不作全灭、主将死亡或已知撤退路线。')
claim('person',people['李厚'],'biography','李厚是蔡州人，时为黑云队长。',20,quote='厚，蔡州人也。',note='籍贯见此句，队长见同段命黑云队长李厚；不补生卒或现代籍贯。')
claim('person',people['柴再用'],'biography','柴再用是汝阳人，时为都押牙。',20,quote='都押牙汝阳柴再用亦为之请',note='保存籍贯、官职，不因都押牙推其上司以外未载任职经历。')
event('yang_raids_lianshui','杨行密另遣兵袭取涟水',20,'寿州战事后本段另记；确年待考','涟水',
      '杨行密另派兵袭击涟水，攻下该地。',[('杨行密','遣兵袭取者')],year=None,quote='行密又遣兵袭涟水，拨之。',note='确年未另载，连未几后述段保待考；不擅补领兵将或坐标，拨疑拔保底本。')
event('qian_petitions_dong_campaign','钱镠表董昌僭逆不可赦，请本道兵讨',21,'895年四月朝廷释董昌以后；确日未载','朝廷、浙西',
      '钱镠上表认为董昌僭逆不可赦，请以本道军队讨伐。',[('钱镠','表请讨伐者'),('董昌','被表请讨者')],note='不可赦为钱奏判断；请以本道兵讨不是新诏已经批准、也非已经再次进军。')
event('wei_zhaodu_retires','韦昭度以太保致仕',22,'895年四月条；确日未载','朝廷',
      '太傅、门下侍郎、同平章事韦昭度以太保致仕。',[('韦昭度','以太保致仕者')],note='致仕非死亡，未据前段两帅请求补罪因。')
event('liu_jianfeng_wuan_commission','刘建锋授武安节度使',23,'895年四月戊戌','武安',
      '朝廷以刘建锋为武安节度使。',[('刘建锋','受武安节度使者')],quote='戊戌，以刘建锋为武安节度使。',note='与894年入潭州阶段分开；不推本日抵任。')
event('ma_yin_commands_liu_army','刘建锋以马殷为内外马步军都指挥使',23,'895年刘建锋受武安节度使条；确日未另载','武安',
      '刘建锋任命马殷为内外马步军都指挥使。',[('刘建锋','命都指挥使者'),('马殷','受都指挥使者')],quote='建锋以马殷为内外马步军都指挥使。',note='沿任命事实，不另推终身统属或提前赋楚王称号。')
event('yang_envoy_qian_pardon_dong','杨行密遣使劝钱镠释董昌',24,'895年四月条；确日未载',None,
      '杨行密遣使到钱镠处，声称董昌已改过、应释放其责。',[('杨行密','遣使倡释者'),('钱镠','受使劝者'),('董昌','被称改过者')],quote='杨行密遣使诣钱镠，言董昌已改过，宜释之',note='董已改过为杨使者传言，不写董已撤销帝位；使者姓名未载。')
event('yang_envoy_dong_resume_tribute','杨行密另遣使促董昌朝贡',24,'895年四月条；确日未载',None,
      '杨行密又派使者到董昌处，催促其向朝廷朝贡。',[('杨行密','遣使促朝贡者'),('董昌','被促朝贡者')],quote='亦遣诣昌，使趣朝贡。',note='趣作催促，不写已经贡物、贡额或董接受劝告。')

reviews={
 19:'陆罢为太子少师，未推罪因。',
 20:'围寿未克将还与庚寅朱再攻执江、杨命权知分开；未几后汴攻、李十旗不胜、将斩求益五旗、柴助朱乘众击败与另袭涟水各录。未几无另载年保未知；旗编数不推总兵，处分未执行，人物籍贯有明句。',
 21:'钱不可赦为奏中判断，请以本道兵讨非已获新诏或已再出军。',
 22:'韦以太保致仕不作卒，不将两帅此前奏语认罢相罪因。',
 23:'刘授武安与马授内外马步军指挥分别，不作已赴镇或提前楚王。',
 24:'杨使说董已改过为外交说辞，另使催朝贡非已朝贡；未具名使者不补人。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text())
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(19,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(19,25)],next_paragraph=Q[25]['id'],coverage='第19—24段连续整理；本年未完成。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
