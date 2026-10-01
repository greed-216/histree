"""Curate consecutive Tongjian volume 261, year 898 paragraphs 37–47."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 48))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0898-p037-p047', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-898-yearend'
fixed_commit='3f35337'
source_specs=[]
for d in sorted((P/'sources/library').iterdir()):
 r=json.loads((d/'paragraph.json').read_text());source_specs.append((d.name,r['book']+'·'+r['section_title'],{'资治通鉴':'司马光等','旧五代史':'薛居正等','新五代史':'欧阳修','新唐书':'欧阳修、宋祁等','旧唐书':'刘昫等'}[r['book']]))
reused_source_keys=set()
manifest=[]
for sk,title,author in source_specs:
 d=P/'sources/library'/sk;r=json.loads((d/'paragraph.json').read_text());filename='library/'+sk+'/source.txt';url='https://github.com/greed-216/histree/blob/'+fixed_commit+'/'+str((d/'source.txt').relative_to(ROOT))
 B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='选定TXT逐字导出；电子本，纸本及异文待核。',url=url,note=r['citation']))
 manifest.append(dict(key=sk,file=filename,sha256=hashlib.sha256((d/'source.txt').read_bytes()).hexdigest(),url=url,paragraph_id=r['id'],upstream_locator=r['locator'],transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
primary_keys=['tongjian-261-898-yearend','tongjian-261-898-guangzhou']
primary_texts={sk:(P/'sources/library'/sk/'source.txt').read_text() for sk in primary_keys}
for n in range(37,48):assert Q[n]['text'] in ''.join(primary_texts.values())
def primary(n,q):return next(sk for sk in primary_keys if q in primary_texts[sk])
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'王熔':'王镕','国弘信':'罗弘信','硃友裕':'朱友裕','赫连鐸':'赫连铎','硃崇节':'朱崇节','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, set(reused_source_keys)
alias.update({'李彦徽':'李彦徽（湖州）','延王戒丕':'李戒丕','王宗播':'许存','杜弘':'杜洪','嵩从周':'葛从周','硃瑾':'朱瑾','硃宣':'朱瑄','李继徽':'杨崇本','硃朴':'朱朴','韩健':'韩建','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_261_0898_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=primary(n,q), citation=f'卷261·光化元年（898）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷261光化元年条所见人物：{name}。',biography=None,status='draft')
    if name=='李抱真（唐潞州节度使）':row['era']='唐'
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=898,note=None,quote=None):
    key='event_zztj_261_0898_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_261_0898_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def e(code,title,n,q,actors=(),when=None,place=None,note=None,description=None,year=898):
    return event(code,title,n,when or '898年本段条；确日未载',place,description or title+'。',actors,quote=q,note=note,year=year)
e('zongdi_full_jiedushi','王宗涤正式授东川节度使',37,Q[37]['text'],[('王宗涤','正式受授者')],when='898年十月丁巳',place='东川',note='承王宗涤留后与别镇申请，但授节不等于分五州别镇申请已获准。')
e('zhang_quanyi_shizhong','张全义加兼侍中',38,Q[38]['text'],[('张全义','受加者')],when='898年十月条；确日未载',place='佑国军',note='无单列干支，不强设与前丁巳同日。')
e('wang_gong_bian_raids_hezhong','王珙引汴军寇河中，王珂向李克用求救',39,'王珙引汴兵寇河中，王珂告急于李克用。',[('王珙','引汴军者'),('王珂','告急者'),('李克用','受告急者')],when='898年十月条；确日未载',place='河中',note='与897年猗氏解围分清，不补汴军未具名统帅。')
e('li_sizhao_rescues_hubi','李嗣昭救河中，于胡壁败汴军',39,'克用遣李嗣昭救之，败汴兵于胡壁，汴人走。',[('李克用','遣援者'),('李嗣昭','救援击败者')],when='898年十月条；确日未载',place='胡壁',note='旧五补三千援兵与胡壁堡，不猜现代坐标。')
e('wang_zhu_summoned','朝廷征召前常州刺史王柷',39,'前常州刺史王柷，性刚介，有时望。诏征之，时人以为且入相。',[('王柷','被征召者')],when='898年十月条；确日未载',note='且入相为时人预期，不记正式已任宰相；不猜诏发日或亲属。')
e('wang_zhu_declines_gong_ritual','王柷过陕，拒王珙子侄礼',39,'过陕，王珙延奉甚至，请叙子侄之礼拜之，柷固辞不受。',[('王柷','拒礼者'),('王珙','请礼者')],when='898年王柷被征途中；确日未载',place='陕',note='请叙子侄礼不是实际血亲，不建立叔侄关系。')
e('wang_gong_kills_wang_zhu','王珙使人杀王柷，害家属掠资伪报覆舟',39,'珙怒，使送者杀之，并其家人悉投诸河，掠其资装，以覆舟闻。朝廷不敢诘。',[('王珙','命杀并伪报者'),('王柷','被杀者')],when='898年王柷拒礼后；确日未载',place='陕及河',note='家人原文未名，河未具名不推黄河；覆舟为伪报，不作意外死亡。朝廷不敢诘为史书记述。')
claim('person',people['王柷'],'death_year','898年条记王柷被王珙遣人杀害。',39,quote='珙怒，使送者杀之')
e('cao_gui_suzhou_commissioner','钱镠以曹圭为苏州制置使',40,'闰月，钱镠以其将曹圭为苏州制置使',[('钱镠','任命者'),('曹圭','受任者')],when='898年闰十月；确日未载',place='苏州',note='闰月承十月、后为十一月，记闰十月；钱所署职不当朝廷正式授官。')
e('wang_qiu_attacks_wuzhou','钱镠遣王球攻婺州',40,'遣王球攻婺州。',[('钱镠','遣军者'),('王球','攻军将领')],when='898年闰十月；确日未载',place='婺州',note='仅遣攻，本段未载攻克或刺史死亡。')
e('prince_zhen_ya','皇子祯封雅王',41,'十一月，甲寅，立皇子祯为雅王',[('唐昭宗','封王者'),('李祯','被封雅王')],when='898年十一月甲寅',note='主书祯，旧唐书诸子传禛，同雅王同光化元年十一月封的对应保异文；不与宣宗子雅王泾混同。')
e('prince_xiang_qiong','皇子祥封琼王',41,'祥为琼王。',[('唐昭宗','封王者'),('李祥','被封琼王')],when='898年十一月甲寅')
e('luo_shaowei_full_jiedushi','罗绍威由魏博留后正式授节度使',42,Q[42]['text'],[('罗绍威','正式受授者')],when='898年十一月条；确日未载',place='魏博军',note='与军推、朝廷知留后分阶段，本句未单列甲寅，不强填同日。')
e('chen_ji_requests_yang_surrender','衢州陈岌向杨行密请降',43,'衢州刺史陈岌请降于杨行密',[('陈岌','请降者'),('杨行密','请降对象')],when='898年十一月条；确日未载',place='衢州',note='请降不等于杨军已控制衢州。')
e('gu_quanwu_sent_against_chen','钱镠遣顾全武讨陈岌',43,'钱镠使顾全武讨之。',[('钱镠','遣讨者'),('顾全武','受遣讨者'),('陈岌','被讨对象')],when='898年十一月条；确日未载',place='衢州',note='本段未给取城结果，留后续。')
e('zhang_cunjing_attacks_cui_hong','朱全忠因崔洪交通淮南遣张存敬攻之',44,'硃全忠以奉国节度使崔洪与杨行密交通，遣其将张存敬攻之。',[('朱温','遣攻者'),('崔洪','受攻奉国节度使'),('杨行密','史载交通对象'),('张存敬','受遣攻者')],when='898年十一月条；确日未载',place='奉国军',note='交通为联系，不扩展永久盟友；杨行密未被写为此次亲自参战。')
e('cui_offers_xian_troops','崔洪请以崔贤为质并遣二千军从征',44,'洪惧，请以弟都指挥使贤为质，且言：“将士顽悍，不受节制，请遣二千人诣麾下从征伐。”',[('崔洪','提出者'),('崔贤','拟送质都指挥使'),('朱温','受请对象')],when='898年十一月张存敬攻后；确日未载',note='此处是请以弟为质及遣军方案，实际二千赴汴与崔贤之死待899年；不写已送齐二千。')
e('zhu_accepts_cui_recalls_zhang','朱全忠许崔洪请求，召张存敬还',44,'全忠许之，召存敬还。',[('朱温','准请召回者'),('崔洪','请求获许者'),('张存敬','被召回者')],when='898年十一月条；确日未载')
claim('person',people['张存敬'],'description','张存敬为曹州人。',44,quote='存敬，曹州人也。',note='曹州为籍贯，不作此次战场。')
e('xue_zhiqin_dies','昭义节度使薛志勤去世',45,Q[45]['text'],[('薛志勤','去世者')],when='898年十二月；确日未载',place='昭义军')
claim('person',people['薛志勤'],'death_year','898年十二月条记薛志勤去世。',45)
e('hanzhi_requests_binning_refused','李罕之在平王行瑜时求邠宁，李克用未许',46,Q[46]['text'].split('罕之不悦而退',1)[0],[('李罕之','求镇者'),('李克用','受求而未许者'),('王行瑜','此前被讨者')],when='追叙李克用平王行瑜时（895年）；确日未载',year=895,place='邠宁',description='李罕之在李克用平王行瑜时求邠宁；李克用以已奏苏文建赴镇、不可反复为由未许。',note='原文为追叙，王行瑜被平已见895年卷260；不作898年第二次讨王。主书引语有重复及功赏所为也的疑似转录问题，原字保留。')
claim('event','event_zztj_261_0898_hanzhi_requests_binning_refused','description','李克用称已奏苏文建赴镇，不可改反复。',46,quote='昨破贼之日，吾首奏趣苏文建赴镇。今才达天听，遽复二三',note='作为拒绝理由的史载说辞，不新增一次未具名日期的任命。')
person('苏文建',46,'李克用拒改镇时提及已奏赴镇')
e('hanzhi_gai_request_small_command','李罕之托盖寓求小镇休兵，李克用未应',46,'罕之不悦而退，私于盖寓曰：“罕之自河阳失守，依托大庇，岁月已深。比来衰老，倦于军旅，若蒙吾王与太傅哀愍，赐一小镇，使数年之间休兵养疾，然后归老闾阎，幸免。”寓为之言，克用不应。',[('李罕之','托求者'),('盖寓','代言者'),('李克用','未应者')],when='追叙平王行瑜后至薛志勤卒前；确年未载',year=None,note='岁月已深、衰老、养疾为本人陈词；此事跨段追叙，不能强定898年或诊断疾病。')
claim('person',people['李克用'],'description','李克用在盖寓再论李罕之求镇时，以鹰饥用饱飞比喻说明其顾虑。',46,quote='吾于罕之岂爱一镇，但罕之，鹰也，饥则为用，饱则背飞。',note='李克用史载说辞，非客观人格诊断；不把比喻造成人物关系标签。')
e('hanzhi_seizes_luzhou','李罕之擅引泽州兵夜入潞州',46,'及志勤薨，旬日无帅，罕之擅引泽州兵夜入潞州，据之',[('李罕之','擅入据城者')],when='898年十二月薛志勤卒后旬日；确日未载',place='泽州、潞州',note='旬日为相对时长，不自换十日公历；擅据不等于李克用正式任命。')
e('li_keyong_rebukes_hanzhi','李罕之报据潞州，李克用遣人责之',46,'以状白克用，曰：“薛铁山死，州民无主，虑不逞者为变，故罕之专命镇抚，取王裁旨。”克用怒，遣人让之。',[('李罕之','报状者'),('李克用','责让者')],when='898年十二月李罕之据潞后；确日未载',place='潞州',note='虑民变为李罕之辩解，不认定城内实际发生叛乱；薛铁山指前薛志勤。')
e('hanzhi_hao_surrender_captives','李罕之遣子李颢降汴，拘马溉傅瑶等送汴州',46,'罕之遂遣其子颢请降于硃全忠，执河东将马溉等及沁州刺史傅瑶送汴州。',[('李罕之','遣降拘送者'),('李颢','受遣请降者'),('朱温','请降对象'),('马溉','被拘送将领'),('傅瑶','被拘送沁州刺史')],when='898年十二月受责后；确日未载',place='潞州、沁州、汴州',note='沁州为傅瑶职地，不确定各被捕具体地点；请降不作本段朝廷授节。旧书伊铎何万友仅补证，不把未核身份塞入主书等。')
e('li_sizhao_takes_ze_families','李嗣昭奉命讨李罕之，先取泽州送其家属晋阳',46,'克用遣李嗣昭将兵讨之，嗣昭先取泽州，收罕之家属送晋阳。',[('李克用','遣讨者'),('李嗣昭','取泽拘送者'),('李罕之','被讨对象')],when='898年十二月请降汴后；确日未载',place='泽州、晋阳',note='先取泽州不等于同时夺回潞州；家属未具名不猜配偶子女。')
e('yang_qian_prisoner_exchange','杨行密遣成及等归两浙换魏约等，钱镠许之',46,'杨行密遣成及等归两浙以易魏约等，钱镠许之。',[('杨行密','遣归提议者'),('钱镠','允换者'),('成及','拟归两浙者'),('魏约','拟交换者')],when='898年十二月条；确日未载',place='两浙',note='同段切到另一地区，非李罕之事件后果；只写提议与允换，不补交换地点或匿名同囚姓名。')
e('zeng_wang_attack_guangzhou','曾兖攻广州，王璙以战舰应之',47,'韶州刺史曾兗举兵攻广州，州将王璙帅战舰应之。',[('曾兖','举兵者'),('王璙','战舰响应者')],when='898年岁末条；确月日未载',place='韶州、广州',note='兗兖繁简归同名，不与曾衮强合；州将原文未明所指州，保州将身份。王璙不因字形推为钱镠子钱元璙。')
e('liu_yin_defeats_zeng_wang','清海行军司马刘隐破攻广州军',47,'清海行军司马刘隐一战破之。',[('刘隐','击破者'),('曾兖','攻军败方'),('王璙','响应攻军败方')],when='898年岁末广州受攻后；确月日未载',place='广州',note='清海行军司马不提前作清海节度使或南汉皇帝；一战不填兵数死伤。')
e('liu_yin_slays_liu_tong','刘潼据浈浛，刘隐讨斩之',47,'韶州将刘潼复据浈、浛，隐讨斩之。',[('刘潼','据地被斩者'),('刘隐','讨斩者')],when='898年岁末条；确月日未载',place='浈、浛',note='浈浛保史载简称，不猜县界坐标；刘潼不因同姓合刘隐亲属。')
claim('person',people['刘潼'],'death_year','898年岁末条记刘潼被刘隐讨斩。',47,quote='韶州将刘潼复据浈、浛，隐讨斩之。')
def relation(a,b,kind,n,q,note):
 ak,bk=people[a],people[b];rk='relationship_'+ak+'_'+bk+'_'+kind
 B['person_relationships'].append(dict(key=rk,person_a_key=ak,person_b_key=bk,relation_type=kind,description=a+'是'+b+'的'+kind+'。',status='draft'))
 claim('person_relationship',rk,'description',a+'是'+b+'的'+kind+'。',n,quote=q,note=note)
 return rk
relation('李杰','李祯','父亲',41,'十一月，甲寅，立皇子祯为雅王','皇子依当朝昭宗主体，A父亲B；未推婚生或母亲。')
relation('李杰','李祥','父亲',41,Q[41]['text'],'皇子祯祥并列，A昭宗是B父亲，不推母亲。')
cr=relation('崔洪','崔贤','兄长',44,'洪惧，请以弟都指挥使贤为质','主书贤为洪弟，A洪是B兄长；新唐书兄贤异说随独立引用保留，不另造反向重复关系。')
relation('李罕之','李颢','父亲',46,'罕之遂遣其子颢请降于硃全忠','其子明示，A罕之是B颢父亲，关系未始于本年。')
claim('person',people['李祯'],'name','主书雅王名字作祯，按当朝李氏皇子记录为李祯。',41,quote='立皇子祯为雅王',note='与旧唐书同封的雅王禛用字异文并列，不静改主体名。')
supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
 record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0898_04_{len(B["claims"])+1:04d}'
 B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
 supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('jiuwudaishi-026-898-hubi','event','event_zztj_261_0898_li_sizhao_rescues_hubi','description','《旧五代史》记十月李嗣昭率三千救河中屯胡壁堡，击退万余汴军。','是月，河中王珂來告急，言王珙引汴軍來寇，武皇遣李嗣昭將兵三千以援之，屯於胡壁堡。汴軍萬餘人來拒戰，嗣昭擊退之。',39,'是月承上十月，兵数为旧书所载，不充作独立统计测量；不同897猗氏战。')
extra('jiutangshu-175-898-princes','person',people['李祯'],'name','《旧唐书》雅王名字作禛，主书作祯。','雅王禛、瓊王祥，並光化元年十一月九日封。',41,'同光化元年十一月同雅琼王对应，保名字用字异文，主书主体仍李祯；未查纸本，不静改字。','conflicts')
extra('jiutangshu-175-898-princes','event','event_zztj_261_0898_prince_zhen_ya','time_original','《旧唐书》记雅王禛与琼王祥于光化元年十一月九日封。','雅王禛、瓊王祥，並光化元年十一月九日封。',41,'与主书十一月甲寅并列，不未经历法校核强换公历。')
extra('jiutangshu-175-898-princes','event','event_zztj_261_0898_prince_xiang_qiong','time_original','《旧唐书》记琼王祥与雅王禛同日封。','雅王禛、瓊王祥，並光化元年十一月九日封。',41,'原文同日为十一月九日，主书甲寅保原，两名皇子不混同。','corroborates')
extra('xintangshu-186-cui-xian','person_relationship',cr,'description','《新唐书》称崔贤是崔洪的兄，主书称弟。','遣兄賢入質，全忠還之，質洪子於汴。',44,'主体同洪贤与送质背景，长幼兄/弟相反，保主书关系方向并列异说，不强定谁误。送回贤及质洪子为此书延展，未合成主书当时已发生。','conflicts')
extra('jiuwudaishi-015-hanzhi-request','event','event_zztj_261_0898_hanzhi_gai_request_small_command','description','《旧五代史》亦记李罕之托盖寓求小镇休兵，李克用未答。','寓為言之，克用不對。每藩鎮缺帥，議所不及，罕之私心鬱鬱，蓋寓懼其他圖，亟為論之。',46,'此前乾宁二年从讨与功赏后叙，未给求小镇另日，不全部认作898年；郁郁为史书叙述。','corroborates')
extra('jiuwudaishi-015-898-hanzhi-luzhou','event','event_zztj_261_0898_hanzhi_seizes_luzhou','description','《旧五代史》记光化元年十二月李罕之乘薛志勤丧，自泽入潞并自称留后。','光化元年十二月，晉之潞帥薛志勤卒，罕之乘其喪，自澤州率眾徑入潞州，自稱留後',46,'补自称留后，不当河东批准；薛志勤原字依快照，主书薛铁山所指一致。')
extra('jiuwudaishi-015-898-hanzhi-luzhou','event','event_zztj_261_0898_hanzhi_hao_surrender_captives','description','《旧五代史》另列被拘送将领伊铎、何万友，并记李颢拘送求援。','罕之執其守將馬溉、伊鐸、何萬友，沁州刺史傅瑤等，遣其子顥拘送於太祖以求援焉。',46,'此书其守将不据字面反推马溉为罕之亲兵；李昭嗣倒置异名保原，不改主书李嗣昭。后明年六月卒不提前录本年。')
extra('xinwudaishi-065-liu-yin-family','person',people['刘隐'],'description','《新五代史》记刘隐父刘谦、祖刘安仁，祖为上蔡人后徙闽商贾南海而家焉。','劉隱，其祖安仁，上蔡人也，後徙閩中，商賈南海，因家焉。父謙，為廣州牙將。',47,'祖上蔡籍与徙居不直接等于刘隐本人的出生地点或出生年；这里只补人物背景，不提前建后世封王。')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(37,48):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='十一段连续校核；授节与留后分期，子侄礼不造血亲。皇子祯禛、崔贤兄弟长幼异文并列。李罕之求镇追叙与十二月擅据潞、拘将降汴、嗣昭取泽分录，重复疑讹引语原字保留。交换俘虏、广州战另录，未读未来段不推进。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=898,primary_source_key=source,primary_source_keys=primary_keys,paragraphs=[Q[n]['id'] for n in range(37,48)],next_paragraph='zztj-v261-y0899-p001',coverage='光化元年末11段，接光化二年；本年是否完成以全47段发布审计为准。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
