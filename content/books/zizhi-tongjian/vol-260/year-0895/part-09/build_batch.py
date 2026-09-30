"""Curate consecutive Tongjian volume 260, year 895 paragraphs 37–40."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p037-p040', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_09_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

alias.update({'李溪':'李磎','李谿':'李磎','李存审':'符存审','延王戒丕':'李戒丕','丹王允':'李允'})
event('southern_mountain_warlord_alarm','南山扈从士民屡惊邠岐兵至',37,'895年七月帝在南山旬余期间','南山',
      '唐昭宗在南山十余日，随驾避乱士民每天相互惊呼邠岐军到了。',[('唐昭宗','南山避乱者')],quote='上在南山旬馀，士民从车驾避乱者日相惊曰：“邠、岐兵至矣！”',note='士民相惊是惊报，不独认邠岐兵每天真到；旬余不反算精确起止日。')
event('jiepi_urges_keyong_advance','延王李戒丕诣河中催李克用进兵',37,'895年七月南山避乱期间；确日未载','河中',
      '唐昭宗派延王李戒丕到河中催李克用进兵。',[('唐昭宗','遣催者'),('李戒丕','奉遣催兵延王'),('李克用','被催者')],quote='上遣延王戒丕诣河中，趣李克用令进兵。',note='派遣与已进兵另录，未补王行程路线。')
event('keyong_leaves_hezhong','李克用从河中发兵',37,'895年七月壬午','河中',
      '李克用从河中出发。',[('李克用','发兵者')],quote='壬午，克用发河中。',note='与前段已记移营渭桥时序并列保留，不默改原书段序或整军行程。')
event('zhang_chengye_envoy_monitor','张承业奉使李克用军，留监其军',37,'895年八月奉使；留监与屡奉使起讫未另载','李克用军',
      '唐昭宗派供奉官张承业去李克用军。史书说明张承业屡奉使，因而留下监其军。',[('唐昭宗','遣供奉官者'),('张承业','奉使并留监军者'),('李克用','受使且被留监之军帅')],quote='八月，上遣供奉官张承业诣克用军。承业，同州人，屡奉使于克用，因留监其军。',note='本年八月明确这次奉使，屡奉使和因留监为背景说明，不定全部使事或永久留监始日。')
claim('person',people['张承业'],'biography','张承业是同州人，曾多次奉使李克用。',37,quote='承业，同州人，屡奉使于克用',note='保籍贯与多次使事，不推生卒年。')
event('keyong_weiqiao_cunzhen_vanguard','李克用进军渭桥，李存贞为前锋',37,'895年八月己丑','渭桥',
      '李克用进军渭桥，派李存贞为前锋。',[('李克用','进军命前锋者'),('李存贞','前锋将')],quote='己丑，克用进军渭桥，遣其将李存贞为前锋',note='按主书记李存贞，未因同姓存字与李存节、李存审合并；未建无明句的养亲。')
event('keyong_takes_yongshou','李克用军攻克永寿',37,'895年八月辛卯','永寿',
      '李克用军攻克永寿。',[('李克用','所率军攻克者')],quote='辛卯，拨永寿',note='拨疑拔，保底本引用，未据连上前锋句认定李存贞独立攻城或补守将。')
event('shi_yan_three_thousand_shimen','史俨率三千骑赴石门侍卫',37,'895年八月辛卯条；确日未另载','石门',
      '李克用派史俨领三千骑到石门侍卫车驾。',[('李克用','遣侍卫骑者'),('史俨','领骑侍卫者'),('唐昭宗','侍卫对象')],quote='又遣史俨将三千骑诣石门侍卫。',note='三千为本项遣骑数，不与随后驻三桥军数混同。')
event('cunxin_cunshen_sixiao_attack_liyuan','李存信李存审会李思孝攻黎园寨擒王令陶',37,'895年八月癸已；底本日字如此','黎园寨、行在',
      '李克用派李存信、李存审会同保大节度使李思孝攻王行瑜黎园寨，俘王令陶等将，献于行在。',[('李克用','遣将攻寨者'),('李存信','领军攻者'),('符存审','以李存审名攻寨者'),('李思孝','保大节度使会攻者'),('王行瑜','寨所属之帅'),('王令陶','被擒将')],quote='癸已，遣李存信、李存审会保大节度使李思孝攻王行瑜黎园寨，擒其将王令陶等，献于行在。',note='癸已疑巳保字；黎园与补书梨园异字存，不作全寨此时已克，擒将不作已杀。')
for row in B['people']:
    if row['key']==people['李思孝']:row['aliases']=['拓跋思孝']
claim('person',people['李思孝'],'aliases','李思孝本姓拓跋。',37,quote='思孝本姓拓跋',note='本姓改姓线索明示，保拓跋思孝检索名；不补赐姓日。')
person('拓跋思恭',37,'李思孝之兄，原文短称思恭')
relation('拓跋思恭','李思孝','兄长',37,'拓跋思恭是李思孝的兄长；原文称思孝本姓拓跋、思恭之弟。',quote='思孝本姓拓跋，思恭之弟也。')
event('maozhen_kills_jipeng','李茂贞斩李继鹏，传首行在',37,'895年八月攻黎园后条；确日未载','行在',
      '李茂贞惧，斩李继鹏，将首级送至行在。',[('李茂贞','斩假子传首者'),('李继鹏','被斩者')],quote='李茂贞惧，斩李继鹏，传首行在',note='不由此删除前段养亲关系，保持同一继鹏阎珪主体；未载斩首地点。')
event('maozhen_seeks_pardon_peace','李茂贞表请罪，并遣使求和李克用',37,'895年八月斩李继鹏后条；确日未另载',None,
      '李茂贞上表请罪，又派使者向李克用求和。',[('李茂贞','请罪求和者'),('李克用','被求和者'),('唐昭宗','受请罪表者')],quote='上表请罪，且遣使求和于克用。',note='请罪不作已赦，求和不作已经达成和约。')
event('emperor_orders_focus_xingyu','唐昭宗遣二王谕暂赦茂贞，集中讨行瑜',37,'895年八月李茂贞请罪以后；确日未载','李克用军、行在',
      '唐昭宗派延王李戒丕、丹王李允告李克用，暂赦李茂贞，集中兵力讨王行瑜，待平定后再议。',[('唐昭宗','遣王传令者'),('李戒丕','传谕延王'),('李允','传谕丹王'),('李克用','受谕者'),('李茂贞','被令暂赦者'),('王行瑜','被集中请讨者')],quote='上复遣延王戒丕、丹王允谕克用，令且赦茂贞，并力讨行瑜，俟其殄平，当更与卿议之。',note='且赦是暂时策略，不写茂贞永久免罪；俟殄平未来条件不作行瑜此时已灭。')
event('two_princes_call_keyong_brother','奉诏二王拜李克用为兄',37,'895年八月遣谕条；确日未另载',None,
      '唐昭宗命延王、丹王拜李克用为兄。',[('唐昭宗','命认兄者'),('李戒丕','奉命认兄延王'),('李允','奉命认兄丹王'),('李克用','奉命被认兄者')],quote='且命二王拜克用为兄。',note='奉诏认兄是政治礼遇，不作血缘兄弟。')
relation('李克用','李戒丕','义兄',37,'李克用为延王李戒丕奉诏所认之兄，不是血缘兄长。',quote='且命二王拜克用为兄。')
relation('李克用','李允','义兄',37,'李克用为丹王李允奉诏所认之兄，不是血缘兄长。',quote='且命二王拜克用为兄。')
event('cui_yin_restored_chancellor','崔胤复为中书侍郎同平章事',38,'895年八月条；具体日未载','朝廷',
      '朝廷以前河中节度使崔胤为中书侍郎、同平章事。',[('崔胤','再任相者')],note='前河中头衔按本段，未补先前已实际到镇；本次与三月授护国分开。')
event('xingyu_stripped_titles','朝廷削夺王行瑜官爵',39,'895年八月戊戌','朝廷',
      '朝廷剥夺王行瑜官爵。',[('王行瑜','被削官爵者')],quote='戊戌，削夺王行瑜官爵。')
event('keyong_bin_campaign_commander','李克用授邠宁四面行营都招讨使',39,'895年八月癸卯','邠宁、朝廷',
      '朝廷以李克用为邠宁四面行营都招讨使。',[('李克用','受总招讨使者')],quote='癸卯，以李克用为邠宁四面行营都招讨使',note='主书称职范围邠宁四面，不扩大成永久全国军权。')
event('three_direction_campaign_commanders','李思孝李思谏张鐇分授三面招讨使',39,'895年八月癸卯','邠宁、朝廷',
      '保大节度使李思孝授北面招讨使，定难节度使李思谏授东面招讨使，彰义节度使张鐇授西面招讨使。',[('李思孝','受北面招讨使'),('李思谏','受东面招讨使'),('张鐇','受西面招讨使')],quote='保大节度使李思孝为北面招讨使，定难节度使李思谏为东面招讨使，彰义节度使张鐇为西面招讨使。',note='同段授三任逐名角色，不据同姓思字推思谏与思孝长幼或父子。')
event('cunxu_eleven_visits_emperor','十一岁的李存勖诣行在，皇帝称将为栋梁',39,'895年八月招讨任命后条；确日未载','行在',
      '李克用派十一岁的儿子李存勖到行在。皇帝奇其状貌，抚其身，称将为国家栋梁、将来应尽忠唐室。',[('李克用','遣子者'),('李存勖','十一岁入见之子'),('唐昭宗','抚赞者')],quote='克用遣其子存勖诣行在，年十一，上奇其状貌，抚之曰：“儿方为国之栋梁，它日宜尽忠于吾家。”',note='年龄保史载，不反算确定出生年；将为栋梁是帝赞与期许，不写此时已掌国政。')
relation('李克用','李存勖','父亲',39,'李克用是李存勖之父。',quote='克用遣其子存勖诣行在')
claim('person',people['李存勖'],'biography','895年入见行在时，史书称李存勖年十一。',39,quote='克用遣其子存勖诣行在，年十一',note='不由古代年龄反算确切生日，沿既有稳定人物UUID。')
event('emperor_accepts_capital_return','李克用表请皇帝还京，皇帝许',39,'895年八月还京以前；确日未载',None,
      '李克用上表请皇帝回京，皇帝准许。',[('李克用','表请还京者'),('唐昭宗','准还京者')],quote='克用表请上还京；上许之。')
event('three_thousand_cavalry_sanqiao','命李克用遣三千骑驻三桥备御',39,'895年八月还京以前；确日未载','三桥',
      '朝廷命李克用派三千骑驻三桥防备。',[('李克用','受令遣骑者')],quote='令克用遣骑三千驻三桥为备御。',note='命遣与已驻日期区分；与前段史俨石门三千骑不是自动同一队。')
event('emperor_returns_capital_895','唐昭宗车驾还京',39,'895年八月辛亥','京师',
      '唐昭宗回到京师。',[('唐昭宗','还京者')],quote='辛亥，车驾还京师。')
event('cui_zhaowei_removed_chancellor','崔昭纬罢相为右仆射',39,'895年八月壬子','朝廷',
      '司空兼门下侍郎、同平章事崔昭纬罢相，为右仆射。',[('崔昭纬','罢相者')],quote='壬子，司空兼门下侍郎、同平章事崔昭纬罢为右仆射。',note='不补本段未载罪因或直接写已赐死。')
event('wang_ke_rengong_formal_governors','王珂刘仁恭分别授本镇节度使',40,'895年八月条；确日未载','护国、卢龙',
      '朝廷以护国留后王珂、卢龙留后刘仁恭各为本镇节度使。',[('王珂','护国留后正式授节度使者'),('刘仁恭','卢龙留后正式授节度使者')],note='与先前军请、李表或三帅改镇请求分开；以主书明确各授节度使为本次正式任命依据。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-895-princes-capital-return';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==598)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L598'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·二王兄事与还京',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第598页，乾宁二年八月段。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=598的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
supplements=[]
def extra(code,n,text,quote,note,kind='corroborates'):
    assert quote in raw.decode();ck=f'claim_zztj_260_0895_09_{len(B["claims"])+1:04d}';key='event_zztj_260_0895_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation='卷26·唐书二·武皇纪下·乾宁二年八月段·原PDF第598页',note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('two_princes_call_keyong_brother',37,'《旧五代史》同记皇帝命延王、丹王以兄礼事李克用。','命二王兄事武\n皇。','政治礼遇非血缘，无须另建反向弟弟关系。')
extra('emperor_orders_focus_xingyu',37,'《旧五代史》载延王传密旨，姑息茂贞，待枭斩行瑜后再与李克用商议。','且欲姑息茂\n贞，令与卿修好，俟枭斩行瑜，更与\n卿商量。','言辞出密旨，仍为条件策略，不认为茂贞此时已被讨平。')
extra('three_thousand_cavalry_sanqiao',39,'《旧五代史》记李存节领二千骑京西北防备，主书记命李克用遣三千骑驻三桥。','令\n李存节领二千骑于京西北，以防邠贼\n奔突。','领军姓名、兵数与地点详略不同，保为并列书证；不凭存字将李存节合并李存贞或认为两队肯定相同。','conflicts')
extra('emperor_returns_capital_895',39,'《旧五代史》同记辛亥天子还宫。','辛亥，天子还宫','主书还京与补书还宫相应，不补具体宫门路线。')
reviews={
 37:'南山惊报、遣王催与壬午发、八月张使留监背景、己丑前锋渭桥辛卯克永寿遣史三千石门、癸已会攻黎园擒将、斩李请罪求和、帝暂赦专讨及二王奉命认兄分录。前段移渭桥与发河中时序不默改；思孝拓跋旧姓、思恭兄长有句，亲兄与政治义兄区分；未知赐姓日不补。',
 38:'崔胤复相非前护国已赴镇。',
 39:'戊戌削王癸卯总招讨及三方、十一子入见、父关系复用原key、请还与备御命令、辛亥还京壬子崔罢分录。年龄不反算生年，帝赞为期许；旧史二千京西北与主书三千三桥独存。',
 40:'护国卢龙两留后正式授本镇节度使，区别先前奏请，未补确日。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(37,41):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(37,41)],next_paragraph=Q[41]['id'],coverage='第37—40段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
