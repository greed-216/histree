"""Curate consecutive Tongjian volume 261, year 899 paragraphs 21–29."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 30))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0899-p021-p029', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-899-late'
fixed_commit='42abb19'
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
primary_keys=['tongjian-261-899-late']
primary_texts={sk:(P/'sources/library'/sk/'source.txt').read_text() for sk in primary_keys}
for n in range(21,30):assert Q[n]['text'] in ''.join(primary_texts.values())
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
alias.update({'李存审':'符存审','硃简':'朱友谦','朱简':'朱友谦'})
alias.update({'李璠':'李璠（陕州）','王檀':'王檀（婺州）','陈汉宾':'陈海宾'})
people, used, reused = {}, {}, set(reused_source_keys)
alias.update({'李彦徽':'李彦徽（湖州）','延王戒丕':'李戒丕','王宗播':'许存','杜弘':'杜洪','嵩从周':'葛从周','硃瑾':'朱瑾','硃宣':'朱瑄','李继徽':'杨崇本','硃朴':'朱朴','韩健':'韩建','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_261_0899_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=primary(n,q), citation=f'卷261·光化二年（899）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷261光化二年条所见人物：{name}。',biography=None,status='draft')
    if name=='李抱真（唐潞州节度使）':row['era']='唐'
    B['people'].append(row);people[name]=row['key']
    nq={'陈章':'叔琮有骁将陈章，号“陈夜叉”，为前锋','氏叔琮':'叔琮有骁将陈章','李克用':'克用闻之，以戒德威','周德威':'克用闻之，以戒德威'} if n==9 else {}
    if n==22:nq={'朱温':'硃全忠召葛从周于潞州，使贺德伦守之。','葛从周':'硃全忠召葛从周于潞州，使贺德伦守之。','贺德伦':'硃全忠召葛从周于潞州，使贺德伦守之。','李嗣昭':'八月，丙寅，李嗣昭引兵至潞州城下，分兵攻泽州。','李孝璋':'以李孝璋为泽州刺史。','符存审':'河东将李存审伏兵邀击之，杀获甚众。'}
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote=nq.get(name))
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=899,note=None,quote=None):
    key='event_zztj_261_0899_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_261_0899_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def e(code,title,n,q,actors=(),when=None,place=None,note=None,description=None,year=899):
    return event(code,title,n,when or '899年本段条；确日未载',place,description or title+'。',actors,quote=q,note=note,year=year)
e('ma_sends_li_tang_dao','马殷遣李唐攻道州',21,'马殷遣其将李唐攻道州',[('马殷','遣攻者'),('李唐','受遣攻军者')],when='899年七月条；确日未载',place='道州',note='承七月条，不能无来源推确日。')
e('cai_ambushes_li_tang','蔡结聚军山隘伏击败李唐',21,'蔡结聚群蛮，伏兵于隘以击之，大破唐兵。',[('蔡结','设伏击败者'),('李唐','败方将领')],when='899年七月条；确日未载',place='道州山隘',note='群蛮为原史称呼，未指明现代民族；唐兵指李唐所部，不另指一支唐廷派军。')
e('li_tang_burns_forest_takes_dao','李唐因风烧林取道州，擒斩蔡结',21,'唐曰：“蛮所恃者，山林耳。若战平地，安能败我！”乃命因风燔林，火烛天地，群蛮惊遁，遂拔道州，擒结，斩之。',[('李唐','烧林攻取者'),('蔡结','被擒斩者')],when='899年七月山隘败后；确日未载',place='道州',note='先败后胜次序明确，不给烧林编坐标面积或气候数据；擒后斩不写战中自杀。')
claim('person',people['蔡结'],'death_year','蔡结899年七月条被李唐军擒斩。',21,quote='遂拔道州，擒结，斩之。')
e('zhu_recalls_ge_he_guards_lu','朱全忠召葛从周，留贺德伦守潞',22,'硃全忠召葛从周于潞州，使贺德伦守之。',[('朱温','召换守方'),('葛从周','被召回者'),('贺德伦','受命守城者')],when='899年八月围潞前；确日未载',place='潞州',note='前六月葛代丁，当前又换贺；不将几个阶段并成同次任命。')
e('sizhao_arrives_lu_attacks_ze','李嗣昭至潞州城下，分兵攻泽州',22,'八月，丙寅，李嗣昭引兵至潞州城下，分兵攻泽州。',[('李嗣昭','围攻分兵者')],when='899年八月丙寅',place='潞州、泽州',note='到城下与分攻并载，不写本日已取两城。')
e('bian_ze_flees_tianjing_taken','汴守将弃泽州，河东军进取天井关',22,'弃泽州走，河东兵进拔天井关。',when='899年八月己巳',place='泽州、天井关',note='日期由同句开己巳核；原将名刘后私用字缺字，未造不可读人物。旧五作刘屺保补书姓名，不静改底本。')
e('li_xiaozhang_ze_appointed','李孝璋任泽州刺史',22,'以李孝璋为泽州刺史。',[('李孝璋','主书记名受任者')],when='899年八月取泽后条；确日未另载',place='泽州',note='主书孝璋，旧五同役存璋；已有李存璋主体，二名是否同人待核，暂不设互相别名或替换旧UUID。')
next(r for r in B['people'] if r['key']==people['李孝璋'])['description']='本版《资治通鉴》卷261光化二年条记为泽州刺史李孝璋；与《旧五代史》同役所记李存璋是否同人待核。'
e('sizhao_cuts_lu_supply','李嗣昭围潞捕刍牧、刈附城禾黍',22,'贺德伦闭城不出，李嗣昭日以铁骑环其城，捕刍牧者，附城三十里禾黍皆刈之。',[('贺德伦','闭城守者'),('李嗣昭','围城断给者')],when='899年八月丙寅至乙酉围城中；各次确日未载',place='潞州城及周边',note='三十里为史载范围，未换成地理半径坐标；刍牧者未具名不造名单。')
e('he_flees_lu_cunshen_ambushes','贺德伦弃潞州遁壶关，李存审伏击',22,'乙酉，德伦等弃城宵遁，趣壶关，河东将李存审伏兵邀击之，杀获甚众。',[('贺德伦','弃城退者'),('李存审','伏击者')],when='899年八月乙酉',place='潞州、壶关',note='李存审复用符存审别名主体；等未名者不猜全名。杀获甚众不造具体数字。旧五另列张归厚保补书，不强写主书已有。')
e('ge_aid_lu_arrives_returns','葛从周援至，闻贺军已败而还',22,'葛从周以援兵至，闻德伦等已败，乃还。',[('葛从周','闻败还援军者')],when='899年八月贺军败后；确日未载',place='潞州附近',note='不把未及救援写成葛同被伏击，不补援军确抵城位置。')
e('li_maozhen_joint_feng_zhangyi','李茂贞兼领凤翔彰义节度',23,Q[23]['text'],[('李茂贞','受任者')],when='899年九月癸卯',place='凤翔、彰义',note='兼节度不凭此推出实际统一控制所有属县。')
e('li_petitions_meng_zhaoyi','李克用表孟迁为昭义留后',24,Q[24]['text'],[('李克用','表请者'),('孟迁','被表请者')],when='899年九月条；确日未载',place='昭义军',note='表留后为报请，不静改为朝廷正式授节；孟原汾州官地不作此次战场。')
e('wang_shifan_requests_yang_rebels','王师范因沂密内叛向杨行密乞援',25,'淄青节度使王师范以沂、密内叛，乞师于杨行密。',[('王师范','乞援者'),('杨行密','受求援者')],when='899年十月遣援前；确月日未载',place='沂州、密州、淄青',note='叛军首领未名不创造地方刺史姓名；请求时段在遣援前，不全强填十月。')
e('yang_tai_wang_take_mi','杨行密遣台濛王绾援，取密州归王师范',25,'冬，十月，行密遣海州刺史台濛、副使王绾将兵助之，拔密州，归于师范。',[('杨行密','遣援者'),('台濛','援军将领'),('王绾','副使援军将领'),('王师范','接收密州者')],when='899年十月；确日未载',place='密州',note='助取归属于史载军事行动，不据此造永久同盟；台濛复用苏州弃城者主体。')
e('wang_warns_yi_prepares_ambush','王绾据侦察劝勿攻沂，伏兵林中待军',25,'将攻沂州，先使觇之，曰：“城中皆偃旗息鼓。”绾曰：“此必有备，而救兵近，不可击也。”诸将曰：“密已下矣，沂何能为！”绾不能止，乃伏兵林中以待之。',[('王绾','劝阻设伏者')],when='899年十月取密后攻沂前；确日未载',place='沂州城外',note='有备救兵近为王判断，后援至另载，先不作已实测消息。使觇与诸将均未名不补台濛发言。')
e('yi_attack_fails_aid_arrives','淮军攻沂不克，敌援至而退',25,'诸将攻沂州不克，救兵至，引退。',when='899年十月条；确日未載',place='沂州',note='攻军将未逐名，不自动补台濛为亲战主帅；敌援将未名，不填朱全忠或葛从周。')
e('wang_ambush_defeats_yi_pursuers','沂州兵追退军，王绾发伏击败之',25,'州兵乘之，绾发伏击败之。',[('王绾','伏击者')],when='899年十月淮军退后；确日未载',place='沂州外',note='击败追兵不等于攻占沂城；不补精确追兵人数。')
e('zhu_jian_kills_li_fan_self_deputy','朱简杀李璠，自称陕州留后附朱全忠',26,'十一月，陕州都将硃简杀李璠，自称留后，附硃全忠',[('朱简','杀将自立附汴者'),('李璠','被杀留后'),('朱温','归附对象')],when='899年十一月；确日未载',place='陕州',note='朱简复用朱友谦主体；李璠复用本年分立陕州主体，不合892战死宣武副使。自称不当朝廷正式授节；旧五友谦传作逃归汴异说并列。')
claim('person',people['李璠（陕州）'],'death_year','主书899年十一月记陕州李璠被朱简杀。',26,quote='十一月，陕州都将硃简杀李璠',note='旧五友谦传却称攻璠后逃归汴，存死亡与逃生异说，不虚构后复活。')
e('zhu_jian_requests_youqian_name','朱简请更名友谦、预朱全忠子侄',26,'仍请更名友谦，预于子侄。',[('朱简','更名入子侄请求者'),('朱温','受请对象')],when='899年十一月附汴后；确日未载',note='请字为请求，不据此建立已正式认养父子或血亲；旧五后文获名编籍未明确同日，不提前硬定此刻完成。')
claim('person',people['朱友谦'],'aliases','朱友谦在本段旧名为朱简，请改名友谦。',26,quote=Q[26]['text'],note='复用已存在主体与UUID，不创建朱简第二人；未直接更写已发布人档。')
e('zhao_kuangning_zhongshu','赵匡凝加兼中书令',27,Q[27]['text'],[('赵匡凝','受加者')],when='899年十一月条；确日未载',place='忠义军')
e('li_qiong_takes_chen_slays_chen','马殷遣李琼攻郴州，执斩陈彦谦',28,'马殷遣其将李琼攻郴州，执陈彦谦，斩之',[('马殷','遣攻者'),('李琼','攻取擒斩者'),('陈彦谦','被执斩者')],when='899年十一月条；确日未载',place='郴州',note='承本月条，不补公历日；与898七州各据形势接续。')
e('li_qiong_lian_lu_suicide','李琼进攻连州，鲁景仁自杀',28,'进攻连州，鲁景仁自杀，湖南皆平。',[('李琼','进攻者'),('鲁景仁','自杀者')],when='899年郴州取后；确日未另载',place='连州',note='湖南皆平是主书本轮总括，不推出所有边县与桂管等未读地区已取；自杀不改成被擒斩。')
claim('person',people['陈彦谦'],'death_year','899年十一月条记陈彦谦被李琼军执斩。',28,quote='执陈彦谦，斩之')
claim('person',people['鲁景仁'],'death_year','899年李琼进攻连州时鲁景仁自杀。',28,quote='进攻连州，鲁景仁自杀')
e('luo_shaowei_pingzhang','罗绍威加同平章事',29,Q[29]['text'],[('罗绍威','受加者')],when='899年十二月；确日未載',place='魏博军')
supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
 record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0899_03_{len(B["claims"])+1:04d}'
 B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
 supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('xintangshu-010-899-dao','event','event_zztj_261_0899_li_tang_burns_forest_takes_dao','time_original','《新唐书》七月条记马殷陷道州，蔡结死。','馬殷陷道州，刺史蔡結死之。',21,'该段七月壬辰另记海州，蔡句不单列干支，不能强作蔡同壬辰死。马总帅与李唐执行层次不同。','corroborates')
extra('jiuwudaishi-026-899-lu-recovered','event','event_zztj_261_0899_he_flees_lu_cunshen_ambushes','description','《旧五代史》武皇纪记八月贺德伦等弃城，潞州平。','是月，德倫等棄城而遁，潞州平。',22,'是月承八月；补弃城后主书本轮潞州收复，不把书中后九月报孟提前。','corroborates')
extra('jiuwudaishi-052-899-lu-details','event','event_zztj_261_0899_bian_ze_flees_tianjing_taken','description','《旧五代史》李嗣昭传汴泽州刺史名字作刘屺，记弃城。','汴將澤州刺史劉屺棄城而遁',22,'主书名字第二字私用缺字，保原快照；刘屺是补书可读名字，不据单版本猜恢复主书字形或合其他刘姓将。')
extra('jiuwudaishi-052-899-lu-details','event','event_zztj_261_0899_li_xiaozhang_ze_appointed','description','《旧五代史》同役记泽州刺史李存璋，主書作李孝璋。','汴將澤州刺史劉屺棄城而遁，乃以李存璋為刺史。',22,'孝/存用字及身份待核，已有人库李存璋；主书新键不设别名，留候选身份问题，未静改底本。','conflicts')
extra('jiuwudaishi-052-899-lu-details','event','event_zztj_261_0899_he_flees_lu_cunshen_ambushes','description','《旧五代史》李嗣昭传另列张归厚与贺德伦八月弃潞。','八月，德倫、張歸厚棄城遁去，我復取潞州。',22,'此书具名张归厚补主书等，不直接写入主书未名参与人。')
extra('jiuwudaishi-026-899-lu-recovered','event','event_zztj_261_0899_li_petitions_meng_zhaoyi','description','《旧五代史》九月称李克用表孟迁为潞州节度使，主书昭义留后。','九月，武皇表汾州刺史孟遷為潞州節度使。',24,'同报请但留后/节度使不同，潞州与昭义为城镇层次，不强改主书正式授节。','conflicts')
extra('jiuwudaishi-002-899-zhu-jian','event','event_zztj_261_0899_zhu_jian_kills_li_fan_self_deputy','description','《旧五代史》梁纪亦记十一月朱简杀留后李璠、自称留后送款。','十一月，陝州都將硃簡殺留後李璠，自稱留後，送款於帝。',26,'同杀璠叙法，史书相依不算独立确证；与同书友谦传逃璠异说并列。','corroborates')
extra('jiuwudaishi-063-youqian-names','event','event_zztj_261_0899_zhu_jian_kills_li_fan_self_deputy','description','《旧五代史》朱友谦传称朱简攻李璠，璠逃归汴；主书与梁纪称杀。','簡復攻璠，璠冒刃獲免，逃歸於汴。',26,'杀与逃不能直接合并，保本书内异说；不补后来第二次被杀作为凑合解释。','conflicts')
extra('jiuwudaishi-063-youqian-names','person',people['朱友谦'],'description','《旧五代史》朱友谦字德光、许州人，本名简，祖岩父琮为陈许小校。','朱友謙，字德光，許州人，本名簡。祖岩，父琮，世為陳、許小校。',26,'简与友谦同主体印证，家世及籍贯补书保原，不据许州籍推出出生地点。')
extra('jiuwudaishi-063-youqian-names','event','event_zztj_261_0899_zhu_jian_requests_youqian_name','description','《旧五代史》后述获名友谦、编属籍、待遇同子。','梁祖深賞其心，乃名之為友謙，編入屬籍，待遇同於己子。',26,'前文昭宗迁洛后又陈情，具体改名编籍时间与主书899请预子侄未强合。待遇同子不确认本年已建立养父关系。')
extra('xinwudaishi-066-ma-six-states','event','event_zztj_261_0899_li_qiong_lian_lu_suicide','description','《新五代史》总述马殷遣秦彦晖李琼等攻连邵郴衡道永六州皆下。','殷遣其將秦彥暉、李瓊等攻連、邵、郴、衡、道、永六州，皆下之。',28,'在马氏立业传中跨年总述，不把六州全设899十一月李琼亲攻；后桂管战尚未读，不提前录。')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(21,30):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='年末九段连续校核；道州先败后取斩，泽潞分攻与换守、贺弃城伏击、葛援迟还分录。原刘缺字保快照，不猜姓名；李孝璋与李存璋候选身份待核。沂军败退与王伏胜不误作取城；朱简复用友谦，杀璠与旧传逃归汴异说并列，请入子侄不造已认养。郴斩陈、连鲁自杀及湖南平总括有别。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=899,primary_source_key=source,primary_source_keys=primary_keys,paragraphs=[Q[n]['id'] for n in range(21,30)],next_paragraph='zztj-v262-y0900-p001',coverage='光化二年末9段，卷261末；本年完成须全29段发布验证后确认。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
