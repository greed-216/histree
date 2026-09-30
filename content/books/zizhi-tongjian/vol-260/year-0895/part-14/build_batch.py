"""Curate consecutive Tongjian volume 260, year 895 paragraphs 57–60."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p057-p060', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_14_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('keyong_besieges_bin_xingyu_denies','李克用逼邠州，王行瑜哭称无罪请归朝',57,'895年十一月丁卯前条；确日未载','邠州',
      '李克用率军逼近邠州。王行瑜登城哭称自己无罪，将胁迫天子归于李茂贞、李继鹏，请李克用移兵凤翔，自愿束身归朝。',[('李克用','逼城者'),('王行瑜','登城自辩请归朝者')],quote='李克用引兵逼邠州，王行瑜登城，号哭谓克用曰：“行瑜无罪，迫胁乘舆，皆李茂贞及李继鹏所为。请移兵问凤翔，行瑜愿束身归朝。”',note='无罪与归责是行瑜自辩，不由此免责或建立已经归朝结果。')
event('keyong_refuses_decide_xingyu_surrender','李克用答不能自行决断王行瑜归朝',57,'895年十一月邠州对答；确日未载','邠州',
      '李克用答称奉诏讨三贼臣，王行瑜在其中，束身归朝之请非自己能专断。',[('李克用','答辩者'),('王行瑜','受答者')],quote='克用曰：“王尚父何恭之甚！仆受诏讨三贼臣，公预其一，束身归朝，非仆所得专也。”',note='答语归说话人，未据此写朝廷已赦或明确下令处斩。')
event('xingyu_family_abandons_bin','王行瑜挈族弃邠州逃走',57,'895年十一月丁卯','邠州',
      '王行瑜带家族弃城逃走。',[('王行瑜','挈族弃城者')],quote='丁卯，行瑜挈族弃城走。',note='主书未載家属人数，不由补书五百扩大为确定实数。')
event('keyong_enters_bin_seals_treasury','李克用入邠州封库安抚，命高爽权巡抚',57,'895年十一月丁卯弃城后条；确日未另载','邠州',
      '李克用入邠州，封府库、安抚居民，命指挥使高爽暂巡抚军城。',[('李克用','入城封库抚民者'),('高爽','权巡抚军城指挥使')],quote='克用入邠州，封府库，抚居人，命指挥使高爽权巡抚军城',note='权为临时任务，不作高爽正式节度使；封库不推库内财物数。')
event('keyong_urges_su_wenjian_arrival','李克用奏催苏文建赴镇',57,'895年十一月入邠州后条；确日未载','朝廷、邠州',
      '李克用上奏催苏文建赴镇。',[('李克用','奏催者'),('苏文建','被催赴镇者')],quote='奏趣苏文建赴镇。',note='与上批请授职分开，催赴不作已经到任。')
event('xingyu_killed_qingzhou_frontier','王行瑜逃至庆州境被部下斩首',57,'895年十一月逃邠州以后；确日未载','庆州境',
      '王行瑜逃到庆州境内，被部下斩杀并传首。',[('王行瑜','被部下斩杀者')],quote='行瑜走至庆州境，部下斩行瑜，传首。',note='主书部下未名，不将李克用或高爽作直接斩杀者，不补具体村镇。')
event('zhu_xuan_sends_caozhou_relief','朱瑄遣贺瑰柳存何怀宝袭曹州解兖围',58,'895年十一月丁卯以前；确日未載','曹州',
      '朱瑄派其将贺瑰、柳存及河东将何怀宝领一万余人袭曹州，以解兖州围。',[('朱瑄','遣援者'),('贺瑰','朱瑄将领袭者'),('柳存','朱瑄将领袭者'),('何怀宝','河东将袭者')],quote='硃瑄遣其将贺瑰、柳存及河东将何怀宝将兵万馀人袭曹州，以解兗州之围。',note='三将军属区别，一万余为合载数非各将各万人；解围为目的，未作成功。')
claim('person',people['贺瑰'],'biography','贺瑰是濮阳人。',58,quote='瑰，濮阳人也。',note='保籍贯，不补生卒或现代坐标。')
event('zhu_wen_night_pursuit_juyesouth','朱温从中都夜追，巨野南败援军',58,'895年十一月丁卯，夜追至明','中都、巨野南',
      '朱温从中都领兵夜追，天亮到巨野南追及援军，杀伤甚众，擒贺瑰、柳存、何怀宝及三千余士卒。',[('朱温','夜追胜者'),('贺瑰','被擒将'),('柳存','被擒将'),('何怀宝','被擒将')],quote='丁卯，全忠自中都引兵夜追之，比明，至巨野南，及之，屠杀殆尽，生擒瑰存、怀宝，俘士卒三千馀人',note='殆尽为史书记述，不算确定死者总数；三千余为俘士卒非阵亡数，三将另列。')
event('zhu_wen_orders_kill_juyesouth_captives','朱温因风沙言杀人未足，下令尽杀俘虏',58,'895年十一月丁卯晡后','巨野南战区',
      '当日下午大风沙尘晦冥，朱温说杀人未足，下令将所得俘虏全部杀死。',[('朱温','发杀俘命令者')],quote='是日晡后，大风沙尘晦冥，全忠曰：“此杀人未足耳！”下令所得之俘尽杀之。',note='风沙与他说话均按史载，不将天气解释为确证天谴；三名将领后条仍被带往兖城，命令不写成三将此时均已死。')
event('zhu_wen_displays_prisoners_yanzhou','朱温缚贺瑰等徇兖州城下劝朱瑾降',58,'895年十一月庚午','兗州城下',
      '朱温将贺瑰等捆缚在兖州城下示众，对朱瑾称其兄已败、劝早降。',[('朱温','示俘劝降者'),('贺瑰','被缚示众者'),('柳存','被缚示众者'),('何怀宝','被缚示众者'),('朱瑾','被劝降者')],quote='庚午，缚瑰等徇于兗州城下，谓硃瑾曰：“卿兄已败，何不早降！”',note='瑰等据前文三将，示众非处死；兄已败为朱温劝降说辞，未在这里新造血亲边。')
event('zongkan_takes_lizhou_kills_jiyong','王宗侃攻克利州，执李继颙斩之',59,'895年十一月丁丑','利州',
      '雅州刺史王宗侃攻克利州，抓获刺史李继颙并将其斩杀。',[('王宗侃','攻克执斩者'),('李继颙','被执斩刺史')],note='拨疑拔保原字，雅州为王宗侃官职属地，利州为攻克地点；未凭继字建养父或合并其他李继人物。')
event('zhu_jin_feigned_surrender_yanshou','朱瑾诈降，延寿门与朱温议交符印',60,'895年十一月辛巳前条；确日未载','延寿门',
      '朱瑾假派使者请降，朱温到延寿门下与其谈话。朱瑾称欲送符印，请朱琼来领。',[('朱瑾','诈降设诱者'),('朱温','亲赴谈者'),('朱琼','被指定接印者')],quote='硃瑾伪遣使请降于硃全忠，全忠自就延寿门下与瑾语。瑾曰：“欲送符印，愿使兄琼来领之。”',note='伪降不是实降，欲交印是诱辞，不作实际交割；朱琼为前批从父兄非另建亲兄。')
event('dong_huaijin_ambushes_zhu_qiong','朱温遣朱琼，董怀进伏桥下擒之',60,'895年十一月辛巳','兗州桥上、桥下',
      '朱温派朱琼前往，朱瑾立马桥上，伏勇士董怀进在桥下。朱琼到，董怀进突起，将其擒入城。',[('朱温','遣朱琼者'),('朱琼','被伏擒者'),('朱瑾','设伏者'),('董怀进','伏擒执行者')],quote='辛巳，全忠使琼往，瑾立马桥上，伏骁果董怀进于桥下，琼至，怀进突出，擒之以入',note='桥未载名不补，骁果为勇士描述不造正式军号。')
event('zhu_qiong_head_thrown_outside','朱琼被斩，首级掷城外',60,'895年十一月辛巳被擒后须臾','兗州城外',
      '朱琼被擒后不久，首级被掷到城外。',[('朱琼','被杀者'),('朱瑾','城内设伏方主将')],quote='须臾，掷首城外。',note='由上文琼被擒承首级，不确指董怀进亲斩，主书未明执行者。')
event('zhu_wen_withdraws_after_qiong_death','朱温撤军',60,'895年十一月朱琼被杀后条；确日未载','兗州',
      '朱温于是率军返回。',[('朱温','引兵还者')],quote='全忠乃引兵还',note='本段未明返到何处，不补返汴确日。')
event('zhu_pin_qizhou_defense_commander','朱温以朱琼弟朱玭为齐州防御使',60,'895年十一月引兵还条；确日未载','齐州',
      '朱温以朱琼的弟弟朱玭为齐州防御使。',[('朱温','授职者'),('朱玭','受防御使者')],quote='以琼弟玭为齐州防御使',note='按朱温主语任用，不替换成朝廷明确诏任。')
relation('朱琼','朱玭','兄长',60,'朱琼是朱玭的兄长。',quote='以琼弟玭为齐州防御使')
event('zhu_wen_kills_liucun_huai_bao','朱温杀柳存何怀宝',60,'895年十一月引兵还条；确日未载',None,
      '朱温杀柳存、何怀宝。',[('朱温','杀俘者'),('柳存','被杀者'),('何怀宝','被杀者')],quote='杀柳存、何怀宝',note='时间在本段处置条，不能前移至丁卯杀俘命令；未载地点不补。')
event('zhu_wen_releases_employs_he_gui','朱温闻贺瑰名，释而用之',60,'895年十一月处置俘将条；确日未载',None,
      '朱温听闻贺瑰名声，释放并任用他。',[('朱温','释而用者'),('贺瑰','被释放任用者')],quote='闻贺瑰名，释而用之。',note='未载具体新官职，不补；与同批柳何被杀区分。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-895-xingyu-death';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==601)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L601'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·邠州与行瑜之死',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第601页，乾宁二年十一月末段。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=601的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
supplements=[]
def extra(code,text,quote,note,kind='corroborates'):
    assert quote in raw.decode();ck=f'claim_zztj_260_0895_14_{len(B["claims"])+1:04d}';key='event_zztj_260_0895_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation='卷26·武皇纪下·乾宁二年十一月末段·原PDF第601页',note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[57]['id'],subject_key=key,relation=kind))
extra('keyong_enters_bin_seals_treasury','《旧五代史》同记李克用收城封库，并迅速奏捷。','武皇收其城，封府库，遽以捷\n闻。','主书另载抚民高爽权巡抚，该书此句未载，不据未载否定。')
extra('xingyu_killed_qingzhou_frontier','《旧五代史》记庆州奏王行瑜带家属五百到州界，被部下所杀，传首阙下。','既而庆州奏，王行瑜将家属五百\n人到州界，为部下所杀，传首阙下。','五百为该书庆州奏载数；主书未载数并列保留，部下未名不补。','adds')
reviews={
 57:'逼城对答均归说话人；丁卯挈族逃、克用入封抚高权、奏催苏赴、庆境部下杀分录，不以自辩免责，不指李克用亲杀。',
 58:'遣袭目的、夜追巨野南胜擒、晡后杀俘命令、庚午缚将示众分录；三将仍在后条，不能将命令解释为本日三将都死。贺籍贯单记。',
 59:'王宗侃利州执斩李继颙，官属雅州非战地，未推养亲。',
 60:'诈降谈印、辛巳伏擒、掷朱琼首、温撤军、任弟玭、杀柳何、释用贺分录；朱琼兄长指玭有句，直接斩者未名不指董，未补贺新官。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(57,61):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(57,61)],next_paragraph=Q[61]['id'],coverage='第57—60段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
