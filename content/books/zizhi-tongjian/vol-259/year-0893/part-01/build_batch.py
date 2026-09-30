"""Curate consecutive Tongjian volume 259, year 893 paragraphs 1–7."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 39))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0893-p001-p007', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-893'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259景福二年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/259.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/259.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
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
alias.update({'郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0893_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·景福二年（893）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259景福二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=893,note=None,quote=None):
    key='event_zztj_259_0893_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0893_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('shi_pu_suzhou_guo_dies','时溥攻宿州，郭言战死',1,'893年春正月；具体日未载','宿州',
      '时溥遣军攻宿州，宿州刺史郭言战死。',[('时溥','遣兵者'),('郭言','战死刺史')],note='原段不具名领军将，不补首战日。')
claim('person',people['郭言'],'death_year','郭言于景福二年正月条所记宿州战事中战死。',1,quote='春，正月，时溥遣兵攻宿州，刺史郭言战死。',note='死亡事实加引用，不覆盖旧发布人物字段或补出生年。')
event('gu_yanhui_dongchuan_appointment','顾彦晖授东川节度使',2,'893年正月条；具体日未载','东川',
      '顾彦晖与王建有隙，李茂贞想安抚使其依从自己，要求恢复赐节；朝廷诏授顾彦晖东川节度使。',[('顾彦晖','授节度者'),('王建','与顾有隙者'),('李茂贞','请赐节者')],note='底本秦恢复疑奏恢复，不悄改原文；诏授明确，未補到任日，抚之使从为李茂贞意图。')
event('li_jimi_relief_petition','李茂贞奏遣李继密救梓州',2,'893年正月条；具体日未载','梓州、兴元',
      '李茂贞又奏请派知兴元府事李继密援救梓州。',[('李茂贞','奏遣者'),('李继密','被奏遣救援者')],note='奏遣与实际抵达分清，兴元为官职所辖不是本次战场。')
event('wang_defeats_allied_armies_lizhou','王建军在利州击败东川凤翔兵',2,'未几；前述奏遣后不久','利州',
      '不久，王建遣军在利州击败东川与凤翔军队。',[('王建','遣军主将'),('顾彦晖','东川军所属节度使'),('李茂贞','凤翔军所属节度使')],note='未几沿用相对时间，未补亲自临阵的主将；没有推定李继密本人参战或阵亡。')
event('gu_yanhui_requests_peace_break','顾彦晖求和，承诺与李茂贞断绝',2,'利州兵败后；具体日未载','东川',
      '顾彦晖向王建求和，请与李茂贞断绝关系，王建同意。',[('顾彦晖','求和及请断绝者'),('李茂贞','所请断绝对象'),('王建','许和者')],note='请求与获许依原文，不扩为永久阵营身份。')
event('li_maozhen_xingyuan_reassignment','李茂贞请镇兴元，授山南西道兼武定',3,'893年正月条；具体日未载','兴元、山南西道、武定',
      '李茂贞自请移镇兴元，朝廷任其为山南西道兼武定节度使。',[('李茂贞','请移镇并被授职者')],note='授职与其后拒诏分开，未写实际交出凤翔。')
event('xu_yanruo_fengxiang_guolang_wuding','徐彦若授凤翔，果阆划隶武定',3,'893年正月条；具体日未载','凤翔、果州、阆州、武定',
      '朝廷任徐彦若同平章事、凤翔节度使，并划果州、阆州属武定军。',[('徐彦若','被授凤翔节度使者')],note='任命及行政划隶为诏令，不推实际驻军控制或徐已到任。')
event('li_maozhen_refuses_reassignment','李茂贞欲兼凤翔，不奉移镇诏',3,'前述任命后；具体日未载','凤翔',
      '李茂贞想兼有凤翔，不遵奉朝廷移镇诏令。',[('李茂贞','拒诏者')],note='欲兼得是书载意图，不作诏令已经许兼。')
event('wang_jian_chancellor_honor','王建加同平章事',4,'893年二月甲戌','西川',
      '西川节度使王建加同平章事。',[('王建','受加官者')],note='外镇加同平章事不等于实际入京任相。')
event('li_keyong_kills_wang_canghai','李克用围邢，斩来信求解的王藏海',5,'893年二月条；具体日未载','邢州',
      '李克用率军围邢州，王镕派牙将王藏海带信请解围。李克用发怒，杀王藏海，并进兵攻王镕。',[('李克用','围邢斩来使进攻者'),('王镕','遣使者'),('王藏海','带信被斩牙将')],note='王藏海为王镕牙将，与同名者无证不并；书信未全文，不补内容。')
event('li_keyong_pingshan_tianchang','李克用平山败镇兵，围天长旬日不下',5,'893年二月辛巳攻天长；旬日不下','平山、天长镇',
      '李克用在平山击败镇州军，辛巳进攻天长镇，十日未攻下。',[('李克用','进攻者'),('王镕','镇军所属主将')],note='镇州天长镇不混同淮南天长；十日未下不记城已破。')
event('li_keyong_chiriling_victory','王镕援天长，李克用叱日岭迎破',5,'围天长旬日后条；具体日未载','叱日岭、天长镇',
      '王镕出兵三万救天长，李克用在叱日岭下迎战，大破援军，书载斩首万余级，其余军溃逃。',[('王镕','派援军者'),('李克用','迎战胜方')],note='兵数与斩首数为书载，叱日岭仅底本名称未核现代地点。')
event('hedong_army_eats_corpses','河东军缺粮，脯尸为食',5,'叱日岭战后条；具体日未载','',
      '《通鉴》记河东军没有粮食，将死者尸体制成脯食用。',[('李克用','河东军主将')],note='脯其尸而啖之按原文记录；不推具体执行兵士或现代诊断。')
event('huo_cun_guards_caozhou','时溥求朱瑾援，霍存骑兵驻曹备之',6,'893年二月条；具体日未载','徐州、曹州',
      '时溥向朱瑾求援，朱全忠派霍存率三千骑兵驻曹州防备援军。',[('时溥','求援者'),('朱瑾','求援所向者'),('朱温','以朱全忠名义遣军者'),('霍存','驻曹州将领')],note='三千为书载，求救不记已获援结果。')
event('huo_youyu_stone_buddha_victory','霍存朱友裕石佛山下破徐兗兵',6,'朱瑾率兵救徐之后；具体日未载','石佛山、徐州、兗州',
      '朱瑾率二万兵救徐州，霍存前往，与朱友裕合击徐州、兗州军于石佛山下，大破之，朱瑾逃回兗州。',[('朱瑾','率援军败返者'),('霍存','合击者'),('朱友裕','合击者')],note='与第9段佛山寨攻拔阶段分开；二万为书载援兵数，未推合计阵亡。')
event('huo_cun_dies_xu_sortie','徐兵再出，霍存战死',6,'893年二月辛卯','徐州',
      '徐州军再次出战，霍存战死。',[('霍存','战死将领'),('时溥','徐军所属主将')],note='不把前次胜利与此次死亡合为同一战。')
claim('person',people['霍存'],'death_year','霍存于景福二年二月辛卯条所记徐兵出战时战死。',6,quote='辛卯，徐兵复出，存战死。',note='本段存即前文霍存；不补葬地、生年。')
event('li_cunxiao_relief_king','李克用下井陉，李存孝救王镕入镇议事',7,'893年二月条；具体日未载','井陉、镇州',
      '李克用攻下井陉。李存孝率兵救王镕，进入镇州同王镕商议。',[('李克用','攻取井陉者'),('李存孝','率援入镇议事者'),('王镕','受援议事者')],note='下井陉为本段进军，不推李存孝本人同李克用在该处已交战。')
event('zhu_keyong_letters_ye_claim','王镕求朱援，朱全忠与李克用书信交锋',7,'王镕求援后；具体日未载','邺下（朱函声称）、常山（李函约战）',
      '王镕向朱全忠求援，朱正与时溥交战不能援，只写信向李克用声称邺下有十万精兵尚未进军。李克用回信说若确实驻邺下则盼降临，若要决胜负愿在常山之尾角逐。',[('王镕','求援者'),('朱温','以朱全忠名义称兵写信者'),('李克用','复书者'),('时溥','朱军当时交战对象')],note='十万是朱函声称，不记录实际军队已驻邺；常山约战不写已交战。')
event('li_kuangwei_yuanshi_relief','李匡威元氏救王镕、李克用还邢',7,'893年二月甲午','元氏、邢州',
      '李匡威率兵援王镕，在元氏击败河东军，李克用退回邢州。',[('李匡威','援军胜方'),('王镕','被援者'),('李克用','败退者')],note='李克用退还邢州，不写已归晋阳。')
event('wang_rewards_li_kuangwei','王镕藁城犒李匡威，以金帛酬援',7,'元氏获援后；具体日未载','藁城',
      '王镕在藁城犒劳李匡威，运送金帛二十万酬谢。',[('王镕','犒谢者'),('李匡威','受犒者')],note='二十万原书未明确单位，不改为二十万斤黄金或现代币值。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={1:'宿州郭言战死，人物死亡另有字段证据；未名领军不补。',2:'授顾节度、奏遣继密、利州胜及求和断结分录；秦恢复疑奏保留。',3:'移镇授职、徐授凤翔果阆划隶、茂贞拒诏分录，不推诏均执行。',4:'外镇加同平章，不记实际入朝任相。',5:'斩来使进攻、平山天长旬日、叱日岭破援、脯尸缺粮分别记录；军数斩首书载。',6:'曹州防援、石佛山胜、辛卯霍存战死分开。',7:'井陉取及存孝救镕、朱李书信、元氏援胜、藁城犒谢分录；十万为声称，金帛单位不补。'}
for n in range(1,8):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,8):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=893,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,8)],next_paragraph='zztj-v259-y0893-p008',coverage='卷259景福二年第1—7段连续录入；本年38段尚未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})

def relation(a,b,t,n,description,quote=None):
    ka,kb=people[a],people[b]
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==ka and r['person_b_key']==kb and r['relation_type']==t]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);key=row['key'];reused.add(key)
    else:
        key=f'relationship_{ka}_{kb}_{t}';row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key
