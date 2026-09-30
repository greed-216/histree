"""Curate consecutive Tongjian volume 259, year 894 paragraphs 9–16."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 34))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0894-p009-p016', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-894'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259乾宁元年条；书、卷、年、段落及行号见批次账本。')]
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
alias.update({'嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0894_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·乾宁元年（894）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259乾宁元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=894,note=None,quote=None):
    key='event_zztj_259_0894_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0894_'+code+'_'+pk
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

alias.update({'赵章':'王宗勉','王茂权':'王宗训','王钊':'王宗谨','李绾':'王宗绾'})
event('zhang_conghui_shouzhou_mission','朱全忠遣张从晦慰抚寿州',9,'894年三月条后、五月条前；具体日未载','寿州',
      '朱全忠派军将张从晦到寿州慰抚。张从晦凌侮刺史江彦温，又同诸将夜饮。',[('朱温','以朱全忠名遣使者'),('张从晦','奉遣慰抚、凌侮夜饮者'),('江彦温','被凌侮的寿州刺史')],note='三月至五月之间的段落位置不强定具体月份；凌侮为书述，不补所说言语。')
event('jiang_yanwen_kills_generals_suicide','江彦温疑谋己，杀夜饮诸将后自杀',9,'张从晦夜饮的次日；894年，确日未载','寿州',
      '江彦温怀疑夜饮诸将谋害自己，次日杀掉在席诸将，写信向朱全忠谢罪后自杀。',[('江彦温','因疑杀诸将、写信并自杀者'),('朱温','以朱全忠名收谢书一方')],note='疑其谋己只证江的怀疑，不证真有暗杀阴谋；原文不具列被杀将名，张从晦后由朱腰斩，不能列作此次已被杀者。')
event('jiang_congxu_acting_shouzhou','寿州军推江从顼知军州事',9,'江彦温自杀后；具体日未载','寿州',
      '寿州军中推江彦温之子江从顼暂管军州事务。',[('江从顼','被推知军州事者'),('江彦温','其已自杀父亲')],quote='军中推其子从顼知军州事',note='知军州事是暂摄，未记正式诏任刺史；承父姓展开江从顼，未与别处同名拼合。')
relation('江彦温','江从顼','父亲',9,'江彦温是江从顼的父亲，原文称其子从顼。',quote='彦温疑其谋己，明日，尽杀在席诸将，以书谢全忠而自杀。军中推其子从顼知军州事')
event('zhu_executes_zhang_conghui','朱全忠为寿州事腰斩张从晦',9,'江彦温自杀与军推其子后；具体日未载','',
      '寿州内变后，朱全忠将张从晦腰斩。',[('朱温','以朱全忠名处刑者'),('张从晦','被腰斩者')],quote='全忠为之腰斩从晦。',note='为之承此段寿州事，未推具体处刑地点、公开罪名或已独立查明的幕后谋划。')
event('qian_chancellor_title','钱镠加同平章事',10,'894年五月','镇海',
      '镇海节度使钱镠加同平章事。',[('钱镠','受加官者')],note='外镇加官，不等于当日入京处理宰相政务。')
event('liu_ma_arrive_liling_deng_guard','刘建锋马殷至澧陵，邓处讷派三千守关',11,'894年五月条；具体日未载','澧陵、龙回关',
      '刘建锋、马殷带兵到澧陵；邓处讷派邵州指挥使蒋勋、邓继崇率步骑三千守龙回关。',[('刘建锋','引兵来者'),('马殷','引兵来者'),('邓处讷','遣守关者'),('蒋勋','领兵守关指挥使'),('邓继崇','领兵守关指挥使')],note='三千为两将步骑总数，不各记三千；底本澧陵与新史醴陵异字独立记录，不自动做现代地名坐标。')
event('ma_envoy_persuades_jiang','马殷遣使劝蒋勋归降，守兵弃甲散去',11,'马殷先至关下后；具体日未载','龙回关',
      '马殷先到关下遣使联系蒋勋，蒋勋等以牛酒犒军。马殷使者称刘骧智勇、将十万精兵，又引术士预言并许归降富贵还乡。蒋勋等接受，说东军许他们返回；士卒欢呼，弃旗甲兵器散去。',[('马殷','遣使劝说者'),('蒋勋','接受劝说并告部众者'),('邓继崇','勋等所含的同守关将领'),('刘建锋','使者所称刘骧的领军对象')],note='十万与精锐无敌是游说辞，非已核当前兵数；翼轸星宿预言为当事人引用，不作天命证实。刘骧按同段指刘建锋，未改既有人物姓名或别名库；邓继崇在勋等范围，未造其单独讲话。')
event('liu_disguises_front_tanzhou','刘建锋前锋冒邵州兵入潭，擒斩邓处讷',11,'龙回关守兵散去后；具体日未载','潭州',
      '刘建锋让前锋穿守兵铠甲、举其旗奔潭州，潭人误当邵州兵返回，没有防备。刘军径入府，擒住正在宴饮的邓处讷并斩杀。',[('刘建锋','命伪装进城者'),('邓处讷','被擒斩的武安节度使')],note='不把未具名的开门守卒造人物，捕杀与自称留后分开；原文建锋入径入府疑重复入字，保存快照。')
event('liu_tanzhou_acting_self_proclaimed','刘建锋在潭州自称留后',11,'894年五月戊辰','潭州',
      '刘建锋取得潭州后自称留后。',[('刘建锋','自称留后者')],quote='戊辰，建锋潭州，自称留后。',note='底本建锋潭州中疑脱入或据字；结合前句取得府城只记自称，不无据补原字；不作朝廷正式诏授。')
event('wang_pengzhou_famine_zhao_surrenders','彭州被围至相食，赵章出降',12,'894年五月条；具体日未载','彭州',
      '王建攻彭州，城中发生相食；彭州内外都指挥使赵章出城归降。',[('王建','围攻者'),('王宗勉','以赵章名出降者')],quote='王建攻彭州，城中人相食，彭州内外都指挥使赵章出降。',note='相食为围城饥荒记载，不补人数、具名受害者或推刑事身份。赵章后改王宗勉同段明载，保持同一人物。')
event('wang_xiancheng_longwei_proposal','王先成请筑龙尾道接女墙',12,'彭州攻城时；具体日未载','彭州',
      '王先成建议筑龙尾道，连接城墙女墙。',[('王先成','建议者'),('王建','攻城军主')],quote='王先成请筑龙尾道，属于女墙。',note='请筑为方案建议，未独立记尺寸、材料或建成时刻；不在现代地图虚构道路。')
event('pengzhou_falls_yang_sheng_killed','西川兵登彭州，王茂权斩杨晟',12,'894年五月丙子','彭州',
      '西川军登上城墙，杨晟仍率众力战，刀子都虞候王茂权将其斩杀。',[('王建','西川军主'),('杨晟','率众力战后被杀者'),('王宗训','以王茂权名斩杨晟者')],quote='丙子，西川兵登城，杨晟犹帅众力战，刀子都虞候王茂权斩之。',note='杨晟被王茂权斩，不误归王建亲手杀；王茂权改宗训在段末同记，未因改名推收养。')
event('an_shijian_refuses_service_killed','安师建被俘拒为王建将，遭杀后礼葬',12,'彭州攻克后；具体日未载','彭州',
      '彭州马步使安师建被俘，王建想用他为将；安师建说已誓与杨晟同生死，求速死。王建反复劝解，他不接受，于是被杀，获礼葬祭奠。',[('安师建','被俘拒任求死后被杀者'),('王建','欲任再劝后杀并礼葬者'),('杨晟','安所称杨司徒的已故军主')],note='求死与被杀区别，未写安自杀；未把忠义话语推成法定亲属或养父子关系，也未补死亡具体方式。')
event('wang_changes_four_names','王建更赵章等四将姓名',12,'彭州攻克后；具体日未载','',
      '王建将赵章改名王宗勉、王茂权改名宗训、王钊改名宗谨、李绾改姓名王宗绾。',[('王建','更姓名者'),('王宗勉','原名赵章的改名者'),('王宗训','原名王茂权的改名者'),('王宗谨','原名王钊的改名者'),('王宗绾','原名李绾的改姓改名者')],quote='更赵章姓名曰王宗勉，王茂权名曰宗训，又更王钊名曰宗谨，李绾姓曰王宗勉，王茂权名曰宗训，又更王钊名曰宗谨，李绾姓名曰王宗绾。',note='底本中间有重复转录与错接李绾姓曰王宗勉；前后完整姓名句可辨四人，只各录一次，保留原文并注明。更姓名不自动等于正式收养。')
for name,old,quote in [('王宗勉','赵章','更赵章姓名曰王宗勉'),('王宗训','王茂权','王茂权名曰宗训'),('王宗谨','王钊','又更王钊名曰宗谨'),('王宗绾','李绾','李绾姓名曰王宗绾')]:
    next(r for r in B['people'] if r['key']==people[name])['aliases']=[old]
    claim('person',people[name],'aliases',f'{name}在本段更名前为{old}。',12,quote=quote,note='据完整更姓名句合为同一稳定人物；底本重复不另建同名人物，不补父子关系。')
event('zheng_yanchang_removed_chancellor','郑延昌罢相为右仆射',13,'894年五月辛卯','朝廷',
      '中书侍郎、同平章事郑延昌罢去宰相职，任右仆射。',[('郑延昌','罢相转官者')],note='罢为不补外流、获罪细节或当日被诛。')
event('zhu_brothers_request_hedong_help','朱瑄朱瑾向河东求援',14,'894年五月条；具体日未载','兗、郓、河东',
      '朱瑄、朱瑾向河东请求援兵。',[('朱瑄','求救者'),('朱瑾','求救者'),('李克用','河东军主、随后遣援者')],quote='硃瑄、硃瑾求救于河东',note='本次求援不独立推永久同盟或替所有今后战争建立因果。')
event('an_brothers_500_ride_to_yun_yan','李克用遣安氏三将率五百骑经魏渡河援兗郓',14,'894年五月条；具体日未载','魏、河道、兗郓',
      '李克用派骑将安福顺与其弟安福庆、安福迁率精骑五百，借道魏地渡河响应朱瑄朱瑾求援。',[('李克用','遣援者'),('安福顺','领精骑将领'),('安福庆','安福顺弟、同领援骑者'),('安福迁','安福顺弟、同领援骑者'),('朱瑄','求援受援者'),('朱瑾','求援受援者')],note='五百为共同兵数，非每人五百；假道魏不推魏正式加入联盟，未按现代河道画行军路线。')
relation('安福顺','安福庆','兄长',14,'安福顺是安福庆的兄长。',quote='李克用遣骑将安福顺及弟福庆、福迁')
relation('安福顺','安福迁','兄长',14,'安福顺是安福迁的兄长。',quote='李克用遣骑将安福顺及弟福庆、福迁')
event('du_hong_attacks_huangzhou_zhu_relief','杜洪攻黄州，杨行密遣朱延寿等救援',15,'894年五月条；具体日未载','黄州',
      '武昌节度使杜洪攻黄州，杨行密派行营都指挥使朱延寿等救援。',[('杜洪','攻黄州者'),('杨行密','遣救者'),('朱延寿','行营都指挥使、援救者')],note='救之只支持遣援，不补战果、杜撤军或黄州已陷。')
event('zhang_yanfan_wuning_official','张廷范正式受任武宁节度使',16,'894年六月甲午','武宁、宋州',
      '朝廷应朱全忠的请求，以宋州刺史张廷范为武宁节度使。',[('张延范','以张廷范名正式受任者'),('朱温','以朱全忠名奏请者')],note='已归档异名证据支持复用张延范；区别893年知感化留后暂摄。武宁为所任军名，宋州为原职，不把任命当行旅同日到达。')

from urllib.parse import quote as urlquote
supplements=[]
sk='xinwudaishi-066-894-tanzhou';path='resources/derived/twenty-four-histories/19新五代史.jsonl';page=1427
raw=next(json.loads(x)['text'].encode() for x in (ROOT/path).read_text().splitlines() if json.loads(x)['pdf_page']==page)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+f'#L{page}'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='新五代史·卷66·楚世家·取潭州段',source_type='primary',author='欧阳修',edition='仓库PDF派生电子文本；逐字及换行保留，未核纸本。',url=url,note='原PDF第1427页；只补乾宁元年龙回关与取潭州，同页后事尚未推进。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=1427的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(key,field,text,quote,note,kind):
    assert quote in raw.decode()
    ck=f'claim_zztj_259_0894_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path=field,claim_text=text,source_key=sk,citation='卷66·楚世家第六·乾宁元年段·原PDF第1427页',note=f'原文：{quote}；核对说明：{note}',status='draft'))
    supplements.append(dict(claim_key=ck,source_book='新五代史',primary_paragraph_id=Q[11]['id'],subject_key=key,relation=kind))
extra('event_zztj_259_0894_liu_ma_arrive_liling_deng_guard','location_name','《新五代史》乾宁元年入湖南段作醴陵，主书底本作澧陵。','乾宁元年，入湖\n南，次醴陵。','地名异字并存，不据现代地图默改主书；新书刘建峰与主书刘建锋用字不同，依相同姓名与行动链对应同一既有人物。','conflicts')
extra('event_zztj_259_0894_liu_disguises_front_tanzhou','description','《新五代史》亦记刘建峰令先锋穿蒋勋铠甲举旗入潭州；进一步称到东门，守者以为戍兵返回而开门，遂杀邓处讷。','建峰取勋铠甲被先锋兵，张其\n旗帜，直趋潭州，至东门，东门守者\n以为关兵戍还，开门内之，遂杀处\n讷，建峰自称留后。','补东门与开门细节，刘建峰复用刘建锋而非新人物；同页下文僖宗授官与894年年代不合，暂不采用该授官句，更不提前录陈赡后事。','adds')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={9:'慰抚凌侮夜饮、疑而杀诸将自杀、军推其子、朱腰斩分录；疑非确证阴谋，从晦不列被杀诸将；江父亲→从顼有其子原句。',10:'镇海加官非入京实任。',11:'三千守关、使说十万为言辞、弃兵散、冒甲夺潭杀邓、自称留后分录；戊辰句疑脱字留原文，新史醴澧、建峰锋异字及东门补细节；新史僖宗授官句年代疑点暂不采用。',12:'饥荒赵降、请筑、丙子登城斩杨、安拒任被杀礼葬、四更姓名分录；段尾重复照存但只录四人改名，不据姓名更改推养父子。',13:'辛卯罢相右仆射，不补流罪。',14:'求援与三将五百借魏渡河分阶段；兄長安福顺→福庆福迁有弟字，不推福庆福迁彼此长幼或永久联盟。',15:'攻与遣救未给胜负。',16:'六月甲午武宁正式授与893感化知留后区别；张廷范复用已归档张延范。'}
for n in range(9,17):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,17):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=894,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph='zztj-v259-y0894-p017',coverage='卷259乾宁元年第9—16段连续录入；本年33段尚未完。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
