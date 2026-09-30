"""Curate consecutive Tongjian volume 259, year 893 paragraphs 14–21."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 39))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0893-p014-p021', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
people, used, reused = {}, {}, {source}
alias.update({'李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0893_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·景福二年（893）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

def relation(a,b,t,n,description,quote=None):
    ka,kb=people[a],people[b]
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==ka and r['person_b_key']==kb and r['relation_type']==t]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);key=row['key'];reused.add(key)
    else:
        key=f'relationship_{ka}_{kb}_{t}';row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key

event('li_kuangwei_prepares_seizure','李匡威助王镕整军，暗谋夺镇',14,'893年；李匡威在镇州期间，具体月日未载','镇州、真定',
      '李匡威为王镕修城堑、整甲兵、训士卒，以其年少且自己喜真定风土，暗谋夺取镇州。李抱真从京师回来，为他策划，以私下恩惠笼络将士；镇人爱王氏，不随李匡威。',[('李匡威','整军并谋夺者'),('王镕','镇主及夺位对象'),('李抱真（李匡威判官）','回来策划者')],note='视之如子为态度，不建养子关系；意图与人心描述归于书述，不单列现代心理结论。')
event('li_kuangwei_kidnaps_wang','李匡威伏兵劫王镕，胁同入府',14,'893年；匡威忌日，具体月日未载','镇州、匡威住宅、军府',
      '李匡威忌日，王镕来吊，匡威素服内穿甲，伏兵劫王镕。王镕抱他劝共回府、以位相让；匡威未接受其说法，但与王镕并马，陈兵入府。大风雷雨中，匡威进东偏门，镇州亲军闭门。',[('李匡威','设伏劫持者'),('王镕','被劫并劝说者')],note='让位是被劫时说辞，不记实际完成交位；忌日原文未说是谁的忌日，不推具体亡亲。')
event('mo_junhe_saves_wang_li_killed','墨君和救王镕，镇人杀李匡威及族党',14,'劫持入府时；893年，具体日未载','镇州、东偏门',
      '屠者墨君和从缺墙跃出，拳击李匡威甲士，将王镕从马上挟救，背上屋顶。镇人取得王镕后进攻并杀李匡威，连同其族党。王镕被挟后颈痛头偏数日。',[('墨君和','屠者救人者'),('王镕','获救者'),('李匡威','被杀者')],note='天气为同段环境，不造唯一失败原因；颈痛为书载后果，不补现代病名；族党未具名不捏造人物。')
claim('person',people['王镕'],'biography','《通鉴》记李匡威劫持时王镕年十七、体疏瘦。',14,quote='镕时年十七，体疏瘦',note='史载年龄不反算出生年或虚实岁。')
event('li_kuangchou_requests_revenge_denied','李匡筹奏请讨王镕报兄仇，朝廷不许',14,'李匡威被杀后；具体日未载','',
      '李匡筹上奏称王镕杀其兄，请举兵报仇，朝廷不准。',[('李匡筹','请复兄仇者'),('王镕','请求讨伐对象'),('李匡威','被杀兄长')],note='请求不记已获批准，实际出兵见后第19段。')
event('liu_rengong_wei_garrison_revolt','刘仁恭蔚州戍兵思归，奉帅攻幽失利',15,'893年；李匡筹立后，具体日未载','蔚州、幽州、居庸关',
      '幽州将刘仁恭领兵戍蔚州，超过轮代期，士卒想归乡。李匡筹自立时，戍卒拥刘仁恭为帅，回攻幽州，在居庸关被军府兵击败。',[('刘仁恭','受拥带兵被败者'),('李匡筹','幽州军府主将')],note='过期未代不推具体轮换制度天数；奉为帅不写朝廷授任。')
event('liu_rengong_flees_hedong','刘仁恭奔河东，李克用厚待',15,'居庸关败后；具体日未载','河东',
      '刘仁恭逃奔河东，李克用厚待他。',[('刘仁恭','奔河东者'),('李克用','接纳厚待者')],note='具体官职本段未载，未提前写894年后授幽州。')
event('yang_tian_meet_hefei_siege','李神福围庐州，杨行密田頵会军',16,'893年四月甲午','庐州、宣州',
      '李神福围庐州，甲午杨行密亲自率军赴庐州，田頵从宣州带兵会合。',[('李神福','围城者'),('杨行密','亲赴者'),('田頵','引兵来会者')],note='宣州为田出发地，未把会军写成庐州已克。')
event('zhang_hao_service_background','张颢先事秦孙、孙败归杨后转助蔡俦',16,'初及后；具体各阶段年日未载','庐州、蔡（籍贯）',
      '《通鉴》追述蔡人张颢以骁勇事秦宗权，后从孙儒，孙儒败后归杨行密，受厚待被派戍庐州；蔡俦反叛时，张颢又为蔡所用。',[('张颢','更从多主者'),('秦宗权','前所属主将'),('孙儒','随后所属主将'),('杨行密','孙败后接纳并遣戍者'),('蔡俦','其反叛时所助者')],year=None,note='跨年生平追叙，不把事秦孙和孙败记同在893；蔡为籍贯称谓，不作全段战场。')
event('zhang_hao_surrenders_reassigned','张颢越城降，杨行密拒袁稹请杀改置亲军',16,'庐州围急时；具体日未载','庐州',
      '围急，张颢越城来降。杨行密将他隶银枪都使袁稹，袁稹认为他反复，请求杀他；杨行密怕袁稹不能容，便把张颢放到亲军。',[('张颢','越城降及改置亲军者'),('杨行密','受降并改隶者'),('袁稹','银枪都使请杀者')],note='反复为袁稹评价；请杀未被实行，不记张颢此时死亡。')
claim('person',people['袁稹'],'biography','袁稹，陈州人，本段任银枪都使。',16,note='职任与籍贯均见同段，不推生卒。')
event('dong_chang_sends_fuzhou_relief','范晖求董昌援，温台婺五千来救',17,'893年福州久攻期间；具体日未载','福州、温州、台州、婺州',
      '王彦复、王审知攻福州久不下。范晖向威胜节度使董昌求援，董昌与陈岩有婚姻关系，发温台婺三州兵五千救范晖。',[('王彦复','围城将领'),('王审知','围城将领'),('范晖','求援者'),('董昌','遣援者')],note='五千为三州总发兵数，不为每州五千；婚姻关系具体双方未载，不改成董昌是陈岩丈夫。')
person('陈岩',17,'董昌姻亲及福州前主')
relation('董昌','陈岩','姻亲',17,'《通鉴》称董昌与陈岩婚姻，未具婚配双方，保留对称姻亲关系。',quote='昌与陈岩婚姻')
event('wang_chao_refuses_withdrawal','王潮拒福州撤兵，命二将继续攻',17,'援兵将至、士卒死伤多时','福州',
      '王彦复、王审知因城坚、援军将到及伤亡多，向王潮请求撤军改日再攻，王潮拒绝；二将又请王潮亲临，王潮回称兵尽添兵、将尽添将、兵将俱尽才自来。二将惧，亲冒矢石急攻。',[('王彦复','请退后急攻者'),('王审知','请退后急攻者'),('王潮','拒退督攻者')],note='兵将俱尽为督战说辞，不当士兵将领均已死亡；王潮未此时亲临。')
event('fan_hui_flees_fuzhou_taken','范晖弃城援军返，王彦复等入福州',17,'893年五月；庚子入城','福州',
      '五月城中粮尽，范晖知不能守，夜把印交监军后弃城逃走，援军也回去；庚子王彦复等进入福州。',[('范晖','弃城者'),('王彦复','入城领军者'),('王审知','同段围攻将领')],note='粮尽为书述，监军未名不造人；王潮之后入福州另录。')
event('fan_hui_killed_coastal','范晖抵沿海都被将士杀',17,'893年五月辛丑','沿海都',
      '范晖逃到沿海都，被将士杀死。',[('范晖','被杀者')],note='沿海都为史载名未核今地；将士未名不推杀者是王氏哪将。')
event('wang_chao_fuzhou_family_reconciliation','王潮入福州自称留后，葬陈岩、结婚抚其家',17,'王彦复入福州及范晖死后条；具体日未载','福州',
      '王潮进入福州，自称留后，穿素服安葬陈岩，将女儿嫁给陈岩之子陈延晦，厚待陈岩家属。',[('王潮','自称留后及抚陈氏者'),('陈岩','被安葬前主'),('陈延晦','受婚者')],note='陈岩死亡在前已录，本段仅葬，不重复893死亡；女儿未名不造人；自称不当正式授任。')
relation('陈岩','陈延晦','父亲',17,'陈延晦为陈岩之子；陈岩是陈延晦的父亲。',quote='葬陈岩，以女妻其子延晦')
relation('王潮','陈延晦','岳父',17,'王潮以女妻陈延晦；王潮是陈延晦的岳父，未补其女姓名。',quote='潮入福州，自称留后，素服葬陈岩，以女妻其子延晦')
event('ting_jian_surrender_bandits','汀建归降，岭海二十余盗群降溃',17,'王潮入福州后条；具体日未载','汀州、建州、岭海',
      '汀州、建州归降，岭海间群盗二十余股均投降或溃散。',[('王潮','前述入福州接续所指主将')],note='降溃保留两种结果，不把全部写成受降；未具名盗首不造人。')
event('qian_suhang_observer','钱镠授苏杭观察使',18,'893年闰月','苏州、杭州',
      '朝廷以武胜防御使钱镠为苏杭观察使。',[('钱镠','受任者')],note='闰月依原文序列为闰五月，保留原记，不换公历日；与九月镇海节度授任分开。')
event('three_guard_commanders_assigned','曹诚李鋋孙惟晟被授黔中镇海荆南',18,'893年闰月','黔中、镇海、荆南',
      '朝廷任扈跸都头曹诚为黔中节度使，耀德都头李鋋为镇海节度使，宣威都头孙惟晟为荆南节度使，并同平章事。',[('曹诚','被授黔中者'),('李鋋','被授镇海者'),('孙惟晟','被授荆南者')],note='诏授不作三人已经实际掌控各镇；并同平章事据同段，不推入京任相。')
event('chen_pei_lingnan_appointment','陈珮被授岭南东道节度使',18,'893年六月','岭南东道',
      '朝廷任捧日都头陈珮为岭南东道节度使，同平章事。',[('陈珮','被授者')],note='授任不补赴任抵达日或实控范围。')
event('emperor_releases_guard_commanders','昭宗为解兵柄，令四都头赴镇',18,'前述加恩授镇时；893年，具体日未载','京师及所授各镇',
      '《通鉴》述李茂贞跋扈，皇帝认为武臣难制，想用诸王代替；给上述四都头加恩，解除兵柄，命其赴镇。',[('李杰','以唐昭宗身份下令者'),('李茂贞','书述难制外镇'),('曹诚','解兵柄赴镇所指者'),('李鋋','解兵柄赴镇所指者'),('孙惟晟','解兵柄赴镇所指者'),('陈珮','解兵柄赴镇所指者')],note='占攵城等四人底本疑转录，以紧前四都头为语境解释，不造占攵城人物；诸王未名，不将四都头直接写成皇子。')
event('li_kuangchou_attacks_wang','李匡筹攻乐寿武强报兄耻',19,'893年六月条；具体日未载','乐寿、武强',
      '李匡筹出兵攻王镕所属乐寿、武强，报李匡威被杀之耻。',[('李匡筹','出兵者'),('王镕','被攻城邑主将'),('李匡威','复仇所指兄长')],note='第14段请复冤未准，此段实出兵，区别朝廷授权。')
event('wang_relief_xing_defeated','王镕救邢州，李克用平山败之进镇',20,'893年秋七月；壬申进镇','邢州、平山、镇州',
      '王镕派兵救邢州，被李克用在平山击败；壬申李克用进攻镇州。',[('王镕','遣援者'),('李克用','破援进击者')],note='与二月平山、尧山各次战役分开。')
event('wang_li_agree_siege_supplies','王镕请助围邢，李克用许并军任县',20,'七月壬申进镇之后；具体日未载','栾城、任县、琉璃陂、邢州',
      '王镕害怕，请以兵粮二十万助攻邢州，李克用答应。李克用在栾城整军，书载合镕兵三万进驻任县，李存信驻琉璃陂。',[('王镕','请助兵粮者'),('李克用','许助整军者'),('李存信','驻琉璃陂者')],note='兵粮二十万未明单位，不作二十万士兵；合镕兵三万沿原记，不擅分两军各自人数；合作限定本次，不推永久盟友。')
event('yang_takes_hefei_kills_cai','杨行密克庐州，斩蔡俦',21,'893年七月丁亥','庐州',
      '杨行密攻克庐州，杀蔡俦。',[('杨行密','攻克斩敌者'),('蔡俦','被斩者')],note='与四月围及张颢投降分阶段。')
event('yang_refuses_grave_revenge','杨行密拒发蔡俦父母墓报复',21,'庐州克后；具体日未载','庐州',
      '左右请求挖蔡俦父母墓报复，杨行密说蔡俦正因此得罪，自己何必效仿，拒绝该请求。',[('杨行密','拒绝发墓者'),('蔡俦','所拟发墓父母的后人')],note='请求未实行，不录为蔡氏墓已发；父母未名不造人。')

from urllib.parse import quote as urlquote
supplements=[]
for sk,title,author,path,page in [
 ('jiuwudaishi-893-wangrong-hostage','旧五代史·王镕传·李匡威劫持段','薛居正等','resources/derived/twenty-four-histories/18旧五代史.jsonl',1288),
 ('xinwudaishi-039-893-mojunhe','新五代史·卷39·王镕传·墨君和救援段','欧阳修','resources/derived/twenty-four-histories/19新五代史.jsonl',687)]:
    raw=next(json.loads(x)['text'].encode() for x in (ROOT/path).read_text().splitlines() if json.loads(x)['pdf_page']==page)
    url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+f'#L{page}'
    (P/'sources'/(sk+'.txt')).write_bytes(raw)
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='PDF派生电子文本，逐字换行保留，未核纸本。',url=url,note=f'原PDF第{page}页；只补当前主段。'))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation=f'提取JSONL pdf_page={page}的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(table,key,field,text,sk,quote,citation,note,book,kind):
    assert quote in (P/'sources'/(sk+'.txt')).read_text()
    ck=f'claim_zztj_259_0893_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=citation,note=f'原文：{quote}；核对说明：{note}',status='draft'))
    supplements.append(dict(claim_key=ck,source_book=book,primary_paragraph_id=Q[14]['id'],subject_key=key,relation=kind))
extra('event','event_zztj_259_0893_li_kuangwei_kidnaps_wang','time_original','《旧五代史》将王镕被劫记在景福二年五月。','jiuwudaishi-893-wangrong-hostage','五月，镕\n谒匡威于其馆，匡威阴遣部下伏甲劫\n镕','王镕传·原PDF第1288页','主书本段未明月日，旧书五月作为补充，不强覆盖主书时间。','旧五代史','adds')
extra('person',people['王镕'],'biography','《旧五代史》亦记王镕被劫时年十七、疏瘦。','jiuwudaishi-893-wangrong-hostage','镕本疏瘦，时年始十\n七','王镕传·原PDF第1288页','印证年龄体态；不反算出生年。','旧五代史','corroborates')
extra('event','event_zztj_259_0893_mo_junhe_saves_wang_li_killed','description','《新五代史》亦记屠者墨君和跃出缺墙，从马上救王镕。','xinwudaishi-039-893-mojunhe','屠者墨君和望见镕，识之，从\n缺垣中跃出，挟镕于马，负之而走','卷39·杂传第二十七·王镕传·原PDF第687页','救援主体与行动印证；新史正抱名与主书李抱真不同，未据本页自动追加别名。','新五代史','corroborates')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={14:'整军谋夺、伏劫胁入、墨救及李死、弟请复冤不许分开；父礼非收养；年龄不推生年，旧史五月补记，新史救援印证。',15:'蔚戍奉帅攻幽居庸败与逃河东分开，未推已受幽州任。',16:'围军会合、张颢跨年从秦孙背景及助蔡、越城降袁请杀后置亲军分录；袁陈籍贯。',17:'求援五千、拒退督战、五月弃城庚子入、辛丑范死、王入自称葬陈婚女抚家、汀建及盗群降溃分录；姻亲岳父父亲有据，陈死不重复。',18:'钱苏杭、三都头闰授及陈六月授、解兵柄赴镇分录；占攵城疑字不造人，诸王非四将身份。',19:'实攻乐寿武强与请准不许分开。',20:'平山败援壬申进镇与兵粮协定整军驻扎分开；二十万单位未知，不定二十万兵。',21:'克斩蔡与拒发墓分别记；未实行不作发墓事实。'}
for n in range(14,22):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(14,22):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=893,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(14,22)],next_paragraph='zztj-v259-y0893-p022',coverage='卷259景福二年第14—21段连续录入；本年38段尚未完。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
