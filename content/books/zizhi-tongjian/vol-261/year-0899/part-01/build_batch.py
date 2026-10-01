"""Curate consecutive Tongjian volume 261, year 899 paragraphs 1–8."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 30))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0899-p001-p008', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-899-spring'
fixed_commit='e050824'
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
primary_keys=['tongjian-261-899-spring']
primary_texts={sk:(P/'sources/library'/sk/'source.txt').read_text() for sk in primary_keys}
for n in range(1,9):assert Q[n]['text'] in ''.join(primary_texts.values())
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
    B['claims'].append(dict(key=f'claim_zztj_261_0899_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=primary(n,q), citation=f'卷261·光化二年（899）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷261光化二年条所见人物：{name}。',biography=None,status='draft')
    if name=='李抱真（唐潞州节度使）':row['era']='唐'
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
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
e('cui_yin_dismissed_premier','崔胤罢相守本官',1,'春，正月，丁未，中书侍郎兼吏部尚书、同平章事崔胤罢守本官。',[('崔胤','被罢相者')],when='899年正月丁未',note='罢同平章事，守本官不写被逐出朝或已罢所有官职。')
e('lu_yi_premier_restored','陆扆任同平章事',1,'以兵部尚书陆扆同平章事。',[('陆扆','受任者')],when='899年正月丁未',note='旧唐本纪有兵部侍郎异记，不静改主书兵部尚书。')
for code,title,name,q in [
 ('hanzhi_zhaoyi_petition','朱全忠表李罕之为昭义节度使','李罕之','硃全忠表李罕之为昭义节度使'),
 ('ding_hui_heyang_petition','朱全忠表丁会为河阳节度使','丁会','又表权知河阳留后丁会'),
 ('wang_jingrao_wuning_petition','朱全忠表王敬荛为武宁节度使','王敬荛','武宁留后王敬荛'),
 ('zhang_ke_zhangyi_petition','朱全忠表张珂为彰义节度使','张珂','彰义留后张珂并为节度使。')]:
 e(code,title,2,Q[2]['text'],[('朱温','表请者'),(name,'被表请节度者')],when='899年正月条；确日未载',note='朱表为申请，本段未独载朝廷制授，不与受授完成混写。王敬荛不并王敬武王敬仁，张珂不并河中王珂。')
e('yang_zhu_jin_attack_xuzhou','杨行密朱瑾率数万兵攻徐州屯吕梁',3,'杨行密与硃瑾将兵数万攻徐州，军于吕梁',[('杨行密','攻军统帅'),('朱瑾','同将攻军者')],when='899年正月条；确日未载',place='徐州、吕梁',note='吕梁为徐州附近史载地名，不当现代山西吕梁；数万为史书记数。')
e('zhu_sends_zhang_guihou_xu','朱全忠遣张归厚救徐州',3,'硃全忠遣骑将张归厚救之。',[('朱温','遣援者'),('张归厚','骑将援军者')],when='899年正月条；确日未载',place='徐州')
e('liu_ren_gong_mobilizes_12_states','刘仁恭发幽沧等十二州十万军欲兼河朔',4,'刘仁恭发幽、沧等十二州兵十万，欲兼河朔。',[('刘仁恭','发军者')],when='899年正月条；确日未载',place='幽州、沧州、河朔',note='十二州只具幽沧，其他州不猜；欲兼为目标，兵数为主书记载。')
e('liu_ren_gong_takes_slaughters_bei','刘仁恭军陷贝州，屠城投尸清水',4,'攻贝州，拔之，城中万馀户，尽屠之，投尸清水。',[('刘仁恭','领军攻取者')],when='899年刘军进攻魏州前；主书正月条，确日未载',place='贝州、清水',note='万余户为户数，不换算人口或认作精确万人；旧唐在二月条保月序异记。')
e('liu_advances_wei_north','刘仁恭攻魏州营城北',4,'由是诸城各坚守不下。仁恭进攻魏州，营于城北。',[('刘仁恭','进攻者')],when='899年贝州陷后；确日未载',place='魏州',note='其他诸城坚守并非全部先已被攻克。')
e('luo_shaowei_requests_zhu_help','罗绍威向朱全忠求救',4,'魏博节度使罗绍威求救于硃全忠。',[('罗绍威','求救者'),('朱温','受求援者')],when='899年刘军攻魏时；确日未载',place='魏博军')
e('cui_xian_return_cai_muster','朱全忠遣崔贤还蔡州发二千兵赴汴',5,'硃全忠遣崔贤还蔡州，发其兵二千诣大梁。',[('朱温','遣还发军者'),('崔贤','受遣回蔡募军者')],when='899年正月末至二月前条；确日未载',place='蔡州、大梁',note='发兵为命令，不记二千已全到汴；与898提质遣兵方案接续。旧唐三千并列。')
e('cui_jingsi_kills_xian_takes_hong','蔡军崔景思等杀崔贤，劫崔洪驱兵民奔淮南',5,'二月，蔡将崔景思等杀贤，劫崔洪，悉驱兵民度淮奔杨行密。',[('崔景思','杀贤劫洪者'),('崔贤','被杀者'),('崔洪','被劫裹挟者'),('杨行密','奔赴对象')],when='899年二月；确日未载',place='蔡州、淮南',note='主书劫崔洪与新唐洪惧驱民的自主性异记并列；不把杨写亲自参加蔡军杀人。')
claim('person',people['崔贤'],'death_year','899年二月崔贤为崔景思等所杀。',5,quote='二月，蔡将崔景思等杀贤')
e('cai_people_scatter_guangling','蔡州奔淮兵民沿途遁归，至广陵不足二千',5,'兵民稍稍遁归，至广陵者不满二千人。',[('崔洪','被裹挟奔淮主体')],when='899年二月驱兵民奔淮后；确日未载',place='广陵',note='不足二千为最终至广陵的兵民，不等于只二千蔡兵原定出戍；未具名兵民不新建人物。')
e('zhu_youyu_guards_cai','朱全忠命朱友裕守蔡州',5,'全忠命许州刺史硃友裕守蔡州。',[('朱温','命守者'),('朱友裕','受命守蔡者')],when='899年二月蔡军出奔后；确日未载',place='蔡州',note='守蔡不等于本句正式任蔡州刺史。')
e('zhu_personal_xu_aid_yang_withdraws','朱全忠亲自救徐州，杨行密退军',5,'硃全忠自将救徐州，杨行密闻之，引兵去。',[('朱温','亲将援军者'),('杨行密','闻援退军者')],when='899年二月；确日未载',place='徐州',note='朱行军至辉州，不能写其本人已到徐州城下。旧五统述正月征退，与主书二月亲救保月序异记。')
e('bian_pursues_xiapi_zhu_returns','汴军追淮兵于下邳，朱全忠至辉州还军',5,'汴人追及之于下邳，杀千馀人。全忠行至辉州，闻淮南兵已退，乃还。',[('朱温','至辉州还军者'),('杨行密','所部被追方')],when='899年二月杨军退后；确日未载',place='下邳、辉州',note='追击汴将未名，不强填张归厚；朱本人在辉州，非下邳杀敌者。千余为史载数。')
e('li_si_an_zhang_aid_neihuang','朱全忠遣李思安张存敬救魏屯内黄',6,'三月，硃全忠遣其将李思安、张存敬将兵救魏博，屯于内黄。',[('朱温','遣援者'),('李思安','援军将领'),('张存敬','援军将领')],when='899年三月；确日未载',place='内黄、魏博',note='旧五梁纪另列朱友伦为此书参与叙述，不强添入主书具名将领。')
e('zhu_main_force_huazhou','朱全忠中军驻滑州',6,'癸卯，全忠以中军军于滑州。',[('朱温','中军统帅')],when='899年三月癸卯',place='滑州')
e('liu_shouwen_shan_attack_li','刘仁恭遣刘守文单可及五万军攻李思安',6,'刘仁恭谓其子守文曰：“汝勇十倍于思安，当先虏鼠辈，后擒绍威耳！”乃遣守文及其妹婿单可及将精兵五万击思安于内黄。',[('刘仁恭','遣攻者'),('刘守文','率军者'),('单可及','同率军者'),('李思安','受攻对象')],when='899年三月；确日未另载',place='内黄',note='勇十倍为仁恭言辞不当能力测量；其妹婿指代有歧义，未造婚配另一端人物。五万为主书记数，不强定癸卯。')
e('li_yuan_ambush_shouwen','李思安袁象先设伏，内黄夹击败刘守文',6,'丁未，思安使其将袁象先伏兵于清水之右，思安逆战于繁阳，阳不胜而却，守文逐之。及内黄之北，思安勒兵还战，伏兵发，夹击之。幽州兵大败，斩可及，杀获三万人，守文仅以身免。',[('李思安','诱敌还击者'),('袁象先','伏兵者'),('刘守文','追击中伏败者'),('单可及','战中被斩者')],when='899年三月丁未',place='繁阳、清水之右、内黄北',note='杀获三万为杀与获合计，不全写斩首；单被斩与旧五被擒异说并列。阳为佯退义，不是地名。')
claim('person',people['单可及'],'death_year','主书899年三月丁未战记单可及被斩。',6,quote='幽州兵大败，斩可及，杀获三万人，守文仅以身免。',note='旧五梁纪作擒单无敌，保异说，不推确切被俘后处刑程序。')
claim('person',people['单可及'],'aliases','单可及号单无敌。',6,quote='可及，幽州骁将，号“单无敌”',note='绰号与夸饰不作实际永无败绩事实。')
claim('person',people['李思安'],'description','李思安为陈留人。',6,quote='思安，陈留人也。',note='籍贯不作内黄战现场。')
e('ge_enters_wei_from_xing','葛从周自邢州率八百精骑入魏州',7,'时葛从周自邢州将精骑八百已入魏州。',[('葛从周','入城援军者')],when='899年三月戊申战前；确日未载',place='邢州、魏州',note='八百为此前入城精骑；旧五五百为后出战骑，阶段不同不强冲突。')
e('ge_he_sally_defeat_liu','葛从周贺德伦闭城门出战，败刘军擒薛王二将',7,'戊申，仁恭攻上水关、馆陶门。从周与宣义牙将贺德伦出战，顾门者曰：“前有大敌，不可返顾。”命阖其扉。从周等殊死战，仁恭复大败，擒其将薛突厥、王郐郎。',[('刘仁恭','攻城败方'),('葛从周','出战者'),('贺德伦','出战宣义牙将'),('薛突厥','被擒将领'),('王郐郎','被擒将领')],when='899年三月戊申',place='魏州、上水关、馆陶门',note='阖门为己方将命门者，不写城已陷；薛突厥是姓名式称谓，未知姓源，不拆作族群。王郐郎与旧五王郃郎保文字异记。')
e('bian_wei_break_eight_camps','汴魏合军破八寨，刘仁恭父子烧营退',7,'明日，汴、魏乘胜合兵击仁恭，破其八寨，仁恭父子烧营而遁。',[('刘仁恭','烧营遁者'),('刘守文','随父退军者')],when='899年三月戊申翌日；干支未另载',place='魏州城外',note='明日承戊申，不自算公历；主书未名该步领军将，不将前一战将领自动补作统领八寨战。八寨非八座城。')
e('bian_wei_pursues_linqing_canal','汴魏军追刘军至临清，拥入永济渠杀溺',7,'汴、魏之人长驱追之，至临清，拥其众入永济渠，杀溺不可胜纪。',[('刘仁恭','所部被追方'),('刘守文','所部被追方')],when='899年三月刘军遁后；确日未另载',place='临清、永济渠',note='不可胜纪不造精确人数；魏至沧五百里为后叙范围，不换现代地图距离。')
e('zhen_troops_intercept_liu','镇州军在东境邀击败退刘军',7,'镇人亦出兵邀击于东境，自魏至沧五百里间，僵尸相枕。',[('刘仁恭','退军受邀击方')],when='899年三月刘军退中；确日未载',place='镇州东境、魏州至沧州',note='镇人指镇州军，统帅未名不新增王镕本人参战；僵尸相枕为史载描述，不补死亡统计。')
claim('person',people['贺德伦'],'description','贺德伦为河西胡人。',7,quote='德伦，河西胡人也',note='籍贯及史载称呼保留，不指定现代民族。')
e('luo_requests_hedong_help','罗绍威向河东修好并求救',7,'刘仁恭之攻魏州也，罗绍威遣使修好于河东，且求救。',[('罗绍威','修好求援者'),('李克用','河东受求援方')],when='899年三月刘仁恭攻魏时追叙；确日未载',place='魏州、河东',note='段内回叙攻魏时，不能把请求时间放在刘已退后；修好不造永久同盟。')
e('li_sizhao_sent_wei_aid','李克用遣李嗣昭救魏',7,'壬午，李克用遣李嗣昭将兵救之。',[('李克用','遣援者'),('李嗣昭','受遣者'),('罗绍威','援助对象')],when='899年三月壬午',place='河东、魏博',note='救魏为命令，不写李军已与幽州交战。')
e('luo_breaks_hedong_li_returns','罗绍威因幽州已败再绝河东，李嗣昭还军',7,'会仁恭已为汴兵所败，绍威复与河东绝，嗣昭引还。',[('罗绍威','再绝河东者'),('李嗣昭','引还者'),('李克用','河东方')],when='899年三月遣李嗣昭援魏后；确日未载',note='破仁恭为汴魏战，不把李嗣昭写为共同击败刘军；此处未交锋即还。')
e('ge_tumen_takes_chengtian','葛从周从土门攻河东，取承天军',8,'葛从周乘破幽州之势，自土门攻河东，拔承天军。',[('葛从周','进攻者')],when='899年三月魏战后；确日未载',place='土门、承天军',note='承天军是史载军城，不拆成一支被全歼的军队。')
e('shi_maling_liao_yuci','氏叔琮自马岭取辽州乐平，进至榆次',8,'别将氏叔琮自马岭入，拔辽州乐平，进军榆次。',[('氏叔琮','进攻者')],when='899年三月魏战后；确日未载',place='马岭、辽州乐平、榆次',note='与葛土门军为不同进军线路；乐平保史载地名，不指现代江西乐平。')
e('li_sends_dewei_against_shi','李克用遣周德威迎击氏叔琮',8,'李克用遣内牙军副周德威击之。',[('李克用','遣击者'),('周德威','受遣内牙军副'),('氏叔琮','被击对象')],when='899年三月汴军进榆次后；确日未载',place='河东',note='迎击命令与下一段挑战破敌分清，当前不提前写已擒陈章。')
# Reuse the published directed father relationship instead of creating an inverse edge.
rk='relationship_person_刘仁恭_person_刘守文_父亲';reused.add(rk)
B['person_relationships'].append(dict(key=rk,person_a_key=people['刘仁恭'],person_b_key=people['刘守文'],relation_type='父亲',description='刘仁恭是刘守文的父亲。',status='draft'))
claim('person_relationship',rk,'description','刘仁恭是刘守文的父亲。',6,quote='刘仁恭谓其子守文曰',note='复用898年已发布父亲方向及UUID，不新增反向子关系。')
supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
 record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0899_01_{len(B["claims"])+1:04d}'
 B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
 supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('jiutangshu-020-899-lu','event','event_zztj_261_0899_lu_yi_premier_restored','description','《旧唐书》正月丁未记陆扆为兵部侍郎同平章事，主书为兵部尚书同平章事。','二年春正月乙未朔。丁未，以兵部尚書陸扆為兵部侍郎、同平章事。',1,'同相职日期，兵部尚书/侍郎文字相异，保两书记法，不静改主书。','conflicts')
extra('jiutangshu-020-899-cai-wei','event','event_zztj_261_0899_cui_xian_return_cai_muster','description','《旧唐书》记崔贤还蔡征三千兵，主书记二千。','汴人遣賢還蔡，徵兵三千出征。',5,'征兵数二千/三千并列，与最后至广陵人数不同统计阶段，不强凑。','conflicts')
extra('xintangshu-186-cui-flight','event','event_zztj_261_0899_cui_jingsi_kills_xian_takes_hong','description','《新唐书》记崔景思杀贤后，崔洪惧而驱民奔行密，主书记劫洪。','將行，大將崔景思不悅，殺賢，洪懼，驅民趨申州，遂奔行密',5,'自主驱民与劫洪叙法不同，保独立引文，不补本人是否自愿、途中每城控制权。','conflicts')
extra('xintangshu-186-cui-flight','event','event_zztj_261_0899_cai_people_scatter_guangling','description','《新唐书》另记武昌杜洪欲邀崔洪而未及，蔡士多亡去，随从才二千。','武昌杜洪邀之，弗及，蔡士多亡去，從者才二千人。',5,'才二千与主书不满二千留不同精度；未到场事件仅补书叙述，不推杜洪已交战。')
extra('jiutangshu-020-899-cai-wei','event','event_zztj_261_0899_liu_ren_gong_takes_slaughters_bei','time_original','《旧唐书》在二月条记刘仁恭陷贝州屠城，主书置正月条出兵攻贝。','是月陷貝州，人無少長皆屠之，投屍清水，為之不流。',4,'是月承该段二月；出发与攻克可跨月，但此时未核定，主书月序与书证分列。','conflicts')
extra('jiuwudaishi-002-899-wei','event','event_zztj_261_0899_zhu_personal_xu_aid_yang_withdraws','time_original','《旧五代史》梁纪正月统述朱全忠亲征、杨退，主书二月条记亲救与退兵。','二年正月，淮南楊行密舉全吳之眾，精甲五萬，以伐徐州，帝領大軍禦之。行密聞帝親征，乃收軍而退。',5,'攻徐始于正月与后来亲救分阶段可能，未强定各书为互斥第二次战役；保两月序。','conflicts')
extra('jiuwudaishi-002-899-wei','event','event_zztj_261_0899_li_si_an_zhang_aid_neihuang','description','《旧五代史》梁纪救魏军另列朱友伦与张存敬李思安屯内黄。','帝遣硃友倫、張存敬、李思安等先屯于內黃，帝遂親征。',6,'朱友伦仅该书列名，主书未具名，不用朱友裕替换；跨书参与扩展留此出处。')
extra('jiuwudaishi-002-899-wei','event','event_zztj_261_0899_li_yuan_ambush_shouwen','description','《旧五代史》梁纪内黄战记杀二万余、获马二千余、擒单无敌等七十余；主书杀获三万并斩单可及。','三月，與燕軍戰于內黃北，燕軍大敗，殺二萬餘眾，奪馬二千餘匹，擒都將單無敵已下七十餘人。',6,'杀二万余与杀获三万统计口径不同，擒/斩单的过程亦异记；不虚构先擒再斩以消冲突。片内通鉴注文非独立正文确证。','conflicts')
extra('jiuwudaishi-016-899-ge','event','event_zztj_261_0899_ge_he_sally_defeat_liu','description','《旧五代史》葛从周传补魏州出战五百骑并闭门。','從周與賀德倫率五百騎出戰，謂門者曰：「前有敵，不可返顧！」命闔其門。',7,'五百是出战兵数，主书八百是此前入魏精骑，不当同一时点必然互斥。')
extra('jiuwudaishi-016-899-ge','person',people['王郐郎'],'description','《旧五代史》同战被擒将名作王郃郎，主书作王郐郎。','擒都將薛突厥、王郃郎等。',7,'同战同薛突厥并列，保郐/郃异字，不静改名，不与后文另一年同名擒将提前合并人生轨迹。','conflicts')
extra('xinwudaishi-044-he-delun','person',people['贺德伦'],'description','《新五代史》记贺德伦河西人，少为滑州牙将，随朱全忠征伐。','賀德倫，河西人也。少為滑州牙將。梁太祖兼領宣義，德倫從太祖征伐',7,'补早年任牙将与从军背景，不把累迁平卢节度的后事提前899。')
extra('jiuwudaishi-026-899-hedong','event','event_zztj_261_0899_ge_tumen_takes_chengtian','time_original','《旧五代史》武皇纪三月记葛从周氏叔琮入河东陷承天辽州、进榆次。','三月，汴將葛從周、氏叔琮自土門陷承天軍，又陷遼州，進軍榆次。',8,'主书分别土门与马岭两路，旧书统述不能推氏也全从土门；三月印证当前月序。','corroborates')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='八段连续校核；表请不当制授。徐州退兵、蔡军出奔、内黄设伏、魏州破寨追击与两路河东进军分录。万余户不换人口，杀获不全当斩首，八百入魏与五百出战分清。补书月序、军数、单可及擒斩及崔洪劫与驱民异记并列。未造妹婿另一端或匿名将领。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=899,primary_source_key=source,primary_source_keys=primary_keys,paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],coverage='光化二年29段中的第1—8段连续处理，本年尚未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
