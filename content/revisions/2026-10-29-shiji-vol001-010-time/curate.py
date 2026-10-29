# coding: utf-8
"""Explicit editorial decisions; calendar arithmetic only after reviewed epoch selection."""
import json,gzip,re
from pathlib import Path
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent
PARAS={p['id']:p for p in map(json.loads,gzip.open(R/'resources/derived/history-library/shiji/paragraphs.jsonl.gz','rt'))}
P=lambda n: f'shiji-174f8dfa444c-p{n:06d}'
# Each epoch is checked in the selected TXT, not supplied from model memory.
EPOCHS={}
def epoch(name,year,n,needle):
 p=PARAS[P(n)];assert p['text'].split('\t')[0].strip()==str(-year) and needle in p['text'];EPOCHS[name]=dict(year=year,paragraph_id=p['id'],quote=p['text'],label=needle)
for row in [('共和',-841,1049,'共和元年'),('宣王',-827,1063,'宣王元年'),('幽王',-781,1109,'幽王元年'),('平王',-770,1120,'平王元年'),('桓王',-719,1171,'桓王元年'),('庄王',-696,1194,'莊王元年'),('釐王',-681,1209,'釐王元年'),('惠王',-676,1214,'惠王元年'),('襄王',-651,1239,'襄王元年'),('顷王',-618,1272,'頃王元年'),('匡王',-612,1278,'匡王元年'),('定王瑜',-606,1284,'定王元年'),('简王',-585,1305,'簡王元年'),('灵王',-571,1319,'靈王元年'),('景王',-544,1346,'景王元年'),('敬王',-519,1371,'敬王元年'),('元王',-476,1431,'元王元年'),('定王介',-468,1439,'定王元年'),('考王',-440,1467,'考王元年'),('威烈王',-425,1482,'威烈王元年'),('烈王',-375,1532,'烈王元年'),('显王',-368,1539,'顯王元年'),('赧王',-314,1593,'周赧王元年'),('秦庄公',-821,1069,'秦莊公其元年'),('秦襄公',-777,1113,'秦襄公元年'),('秦文公',-765,1125,'秦文公元年'),('秦宁公',-715,1175,'秦寧公元年'),('秦出子',-703,1187,'秦出子元年'),('秦武公',-697,1193,'秦武公元年'),('秦德公',-677,1213,'秦德公元年'),('秦穆公',-659,1231,'秦穆公任好元年'),('秦康公',-620,1270,'秦康公罃元年'),('秦桓公',-603,1287,'秦桓公元年'),('秦景公',-576,1314,'秦景公元年'),('秦哀公',-536,1354,'秦哀公元年'),('秦厉共公',-476,1431,'厲共公元年'),('秦怀公',-428,1479,'秦懷公元年'),('秦灵公',-424,1483,'秦靈公元年'),('秦简公',-414,1493,'秦簡公元年'),('秦献公',-384,1523,'秦獻公元年'),('秦王政',-246,1661,'始皇帝元年'),('秦二世',-209,1698,'二世元年'),('汉高祖',-206,1810,'高祖元年'),('汉惠帝',-194,1822,'孝惠元年'),('汉文帝',-179,1837,'孝文元年')]:epoch(*row)
def yr(king,n):
 a=EPOCHS[king];ordinal=a['year'] if a['year']<0 else a['year']-1;o=ordinal+n-1;return o if o<0 else o+1
INV=json.loads((R/'content/books/shiji/runs/2026-10-29-vol-001-010/time-review/inventory.json').read_text())
ITEMS={e['key']:dict(e,volume=v['volume']) for v in INV['volumes'] for e in v['new_event_details']}
DEC={}
def key(v,slug):return f'event_shiji_v{v:03}_'+slug
for k,x in ITEMS.items():
 era=x['dynasty'] or '时代待考'
 DEC[k]=dict(decision='era',precision='era',era=era,earliest=None,latest=None,legacy=False,anchors=[],reason='原文支持所列时代与叙事先后；未有已核绝对纪年锚点，不由世系、年龄或段落标题倒算。原有时长和追叙保留。',phases=[])
def setd(k,decision,lo=None,hi=None,reason='',anchors=(),legacy=False,precision=None,phases=()):
 x=ITEMS[k];DEC[k]=dict(decision=decision,precision=precision or {'exact':'year','range':'range','multiple':'range','conflicting':'range','relative':'relative'}[decision],era=x['dynasty'],earliest=lo,latest=hi,legacy=legacy,anchors=list(anchors),reason=reason,phases=list(phases))
def exact(v,slug,king,n,extra=()):
 y=yr(king,n);setd(key(v,slug),'exact',y,y,f'本纪明示{king}{n}年；核对选定电子年表的元年后按在位年换算为公元前{-y}年。现代公元列是对照资料；原月日和干支不换算公历日。',anchors=[EPOCHS[king]['paragraph_id'],*[P(i) for i in extra]],legacy=True)
def range_(v,slug,lo,hi,note,anchors=()):setd(key(v,slug),'range',lo,hi,note,anchors=[P(n) for n in anchors])
def phase(parent,king,specs):
 vals=[]
 for n,title in specs:
  y=yr(king,n);vals.append(dict(year=y,title=title,king=king,regnal=n,anchor=EPOCHS[king]['paragraph_id']))
 setd(parent,'multiple',min(p['year'] for p in vals),max(p['year'] for p in vals),'原记录含不同年份的独立行动；保留原总述，另建按年阶段事件。此处范围表示材料覆盖的时点，不表示连续持续。',anchors=[EPOCHS[king]['paragraph_id']],phases=vals)
# 周本纪：明确单年行动，纪年锚点均在同书年表逐一核对。
for slug,king,n in [('lu_wugong','宣王',12),('earthquake','幽王',2),('lu_yin','平王',49),('huan_succeeds','平王',51),('huan_wounded','桓王',13),('heijian','庄王',4),('qi_hegemon','釐王',3),('tui_revolt','惠王',2),('hui_returns','惠王',4),('qi_awarded','惠王',10),('di_invade','襄王',16),('jin_restores','襄王',17),('heyang','襄王',20),('jinwen_death','襄王',24),('qinmu_death','襄王',31),('ding_asks_vessels','定王瑜',1),('chu_zheng','定王瑜',10),('chu_death','定王瑜',16),('jin_li_dao','简王',13),('cui_zhu','灵王',24),('tian_chang','敬王',39),('chen_destroyed','敬王',41),('confucius_death','敬王',41),('zhi_partition','定王介',16),('ai_si_kao','定王介',28),('tan_prophecy','烈王',2),('qin_king','显王',44),('sudai_chu','赧王',8),('suli_baiqi','赧王',34),('mafan_city','赧王',42),('zhouju','赧王',45),('qin_sanjin','赧王',58)]:exact(4,slug,king,n)
for slug,king,n in [('周幽王','宣王',46),('周庄王','桓王',23),('周釐王','庄王',15),('周惠王','釐王',5),('周襄王','惠王',25),('周匡王','顷王',6),('周定王（瑜）','匡王',6),('周简王','定王瑜',21),('周灵王','简王',14),('周景王','灵王',27),('周定王（介）','元王',8),('周威烈王','考王',15)]:exact(4,'succession_'+slug,king,n)
setd(key(4,'gonghe'),'range',-841,-828,'共和为十四年的实际行政时期；年表共和元年与十四年分别对应前841、前828年，属于真实持续过程，起止年可用于年度列表。',anchors=[P(1049),P(1062)],legacy=True)
setd(key(4,'you_death'),'exact',-771,-771,'本纪叙幽王被杀与宜臼被立；核年表幽王十一年同条记犬戎杀王，公元前771年。平王次年改元，不以平王元年覆盖幽王遇害年。',anchors=[P(1119)],legacy=True)
setd(key(4,'ping_east'),'exact',-770,-770,'本纪仅记平王东迁，年表平王元年同条明确东徙雒邑，对应前770年。',anchors=[P(1120)],legacy=True)
range_(4,'depose_shen',-779,-771,'段首幽王三年先记宠爱褒姒，后叙生子及最终废立，不把全部经历压在三年；只约束为三年起至幽王末年前。',[1109,1119])
range_(4,'beacon',-781,-771,'烽火故事未单载年份；只约束为本书记载的幽王时期，保留传世叙事性质。',[1109,1119])
range_(4,'census',-789,-782,'料民在千亩败绩后叙述，未明说同年；按宣王三十九年至四十六年末约束，不认定为持续七年。',[1063])
range_(4,'guan_ritual',-648,-643,'管仲平戎在襄王三年叔带作乱之后、齐桓公卒之前叙述，未明同年；仅保留这段先后界限。',[1239])
range_(4,'dai_second',-635,-635,'本段承襄王十六年来攻，接十七年复位；出奔是否跨年未独立载明，不为单一确年。',[1239])
# Correct conservative envelope for the flight before the next year's restoration.
DEC[key(4,'dai_second')].update(earliest=-636,latest=-635)
setd(key(4,'jing_succession'),'conflicting',-525,-520,'本纪记景王二十年崩；年表王位段及子朝争位在二十五年附近。两处系年不能合成唯一确年，保留待考范围，不改作某一年。',anchors=[P(1346),P(1370)])
setd(key(4,'succession_周顷王'),'conflicting',-620,-619,'本纪以襄王三十二年记崩；与年表襄王末年、顷王元年衔接有一年的疑点，保留两个候选年，未强定。',anchors=[P(1239),P(1271),P(1272)])
setd(key(4,'succession_周元王'),'conflicting',-478,-477,'本纪记敬王四十二年崩，与年表敬王末年及元王元年的衔接有差异；先保留本纪折算与表末年两说。',anchors=[P(1371),P(1431)])
for slug in ['li_exile','jing_saved']:setd(key(4,slug),'relative',None,-841,'厉王出奔及召公保护太子的故事在共和行政前；不以本纪三十四年加三年倒推厉王绝对元年。仅保留不晚于共和开始的界限及原叙事。',anchors=[P(1049)])
setd(key(4,'han_zhou_heir'),'relative',None,None,'原文仅汉兴九十余载后及天子巡河南；汉兴起算点和巡行年未独立核定，不按90倒算。')
phase(key(4,'zheng_audience'),'桓王',[(3,'桓王不礼遇来朝的郑庄公'),(5,'郑国与鲁国交换许田')])
phase(key(4,'dai_first'),'襄王',[(3,'王子带联戎翟谋伐襄王后奔齐'),(12,'王子带从齐国返回周')])
phase(key(4,'zheng_envoys'),'襄王',[(13,'郑国囚禁周王派来的使者'),(15,'襄王借翟兵攻打郑国')])
phase(key(4,'jing_returns'),'敬王',[(1,'晋人助敬王入周未果，敬王居泽'),(4,'晋率诸侯迎敬王入周'),(16,'子朝余党作乱，敬王逃往晋国'),(17,'晋定公迎敬王返回周')])
phase(key(4,'qin_awards'),'显王',[(5,'周显王向秦献公致贺'),(9,'周显王向秦孝公赐祭胙'),(33,'周显王向秦惠王致贺'),(35,'周显王向秦惠王赐祭胙')])
# 千亩前事无年，战事明示宣王三十九年；只为后者新建年度阶段。
setd(key(4,'qianmu'),'multiple',-827,-782,'不修籍田与千亩战败是不同动作；前事仅知宣王时期，后事明确三十九年。总述保留，战争另列年度事件。',anchors=[P(1063)],phases=[dict(year=yr('宣王',39),title='周宣王在千亩败于姜戎',king='宣王',regnal=39,anchor=EPOCHS['宣王']['paragraph_id'])])
# 秦本纪
for slug,king,n in [('chuuzi','秦宁公',12),('kill_chuzi','秦出子',6),('wugong_death','秦武公',20),('han_battle','秦穆公',15),('liangrui','秦穆公',20),('chonger','秦穆公',24),('siege_zheng','秦穆公',30),('wangguan','秦穆公',36),('rong_hegemony','秦穆公',37),('mu_death','秦穆公',39),('linghu','秦康公',1),('huaigong','秦怀公',4),('jian_reform','秦简公',6)]:exact(5,slug,king,n)
range_(5,'qinzhong',-822,-778,'秦仲死于在位二十三年，庄公兄弟奉命复战在后，原文未注明同年；保留复合叙事，秦仲战死另列前822年的阶段。',[1049,1069])
DEC[key(5,'qinzhong')]['decision']='multiple';DEC[key(5,'qinzhong')]['phases']=[dict(year=-822,title='秦仲在讨伐西戎时战死',king='秦仲',regnal=23,anchor=P(1068))];DEC[key(5,'qinzhong')]['anchors'].append(P(1068))
range_(5,'shifu',-821,-778,'世父出战让位记在庄公生前，末句庄公四十四年是其去世纪年，不能反套世父行动。仅约束为庄公时期。',[1069,1112])
range_(5,'mugong_appoint',-655,-651,'五年虞亡后百里傒辗转入秦，随后举荐蹇叔；九年送晋惠公时已任事。未明赎回与聘任同年，保留前655至前651年范围。',[1231])
range_(5,'jin_hui',-651,-648,'迎立夷吾与背约在九年事后、十二年前的叙事内，不能当作单日或全部同一年。',[1231])
range_(5,'send_grain',-648,-645,'赈晋夹在十二年与十五年韩地之战前，原段未独立纪年；先按上下文约束，不借常识指定某一年。',[1231])
range_(5,'attack_zheng',-628,-627,'决策在三十三年春出师之前，出师及灭滑明确在三十三年；保留准备与执行层次，执行另列年度阶段。',[1231])
DEC[key(5,'attack_zheng')]['decision']='multiple';DEC[key(5,'attack_zheng')]['phases']=[dict(year=-627,title='秦军袭郑受弦高犒军后改灭滑',king='秦穆公',regnal=33,anchor=P(1263))]
setd(key(5,'xiao_defeat'),'exact',-627,-627,'本纪承三十三年袭郑返程及晋文公丧未葬，年表同年秦晋两栏均记殽败，核为前627年。',anchors=[P(1263)],legacy=True)
range_(5,'pengya',-626,-624,'彭衙条未单载年，前承三十四年、后至三十六年；年表另载三十五年败于汪，不未经地名辨析就强并，保留范围待考。',[1264,1265,1266])
range_(5,'youyu',-659,-623,'由余离戎入秦在穆公朝、三十七年征戎之前；过程包含终年未归等时长，不套相邻三十四年。仅给本朝上界和征戎前下界。',[1231])
range_(5,'houzizhen',-541,-537,'出奔在景公三十六年，返秦在景公四十年卒后；保留跨阶段范围，出奔和返归分别列出。',[1314])
phase(key(5,'wen_yi'),'秦文公',[(4,'秦文公在汧渭之会营建城邑'),(10,'秦文公设鄜畤祭祀'),(13,'秦国开始设置史官记录政事')])
# 本记录的二十年另记三族刑制，不是向周献地；避免错误把该年用于归还岐东。
setd(key(5,'wen_rong'),'exact',yr('秦文公',16),yr('秦文公',16),'击戎、得岐西与献岐东均承文公十六年；二十年是另记三族刑制，不属于本事件。纠正原时间文字混入二十年。',anchors=[EPOCHS['秦文公']['paragraph_id']],legacy=True)
phase(key(5,'wugong'),'秦武公',[(3,'秦武公诛杀三父等人'),(10,'秦武公讨邽冀戎并设置县'),(11,'秦武公设置杜县和郑县')])
phase(key(5,'degong'),'秦德公',[(1,'秦德公迁居雍城大郑宫'),(2,'秦德公开始举行伏祭')])
phase(key(5,'huan_jin'),'秦桓公',[(24,'秦桓公与晋厉公夹河结盟后背约'),(26,'晋率诸侯攻秦并追至泾水')])
phase(key(5,'ligong'),'秦厉共公',[(16,'秦厉共公出兵攻取大荔王城'),(21,'秦国初设频阳县'),(33,'秦厉共公攻义渠并俘其王')])
phase(key(5,'xian_abolish'),'秦献公',[(1,'秦献公停止以人殉葬'),(2,'秦献公营建栎阳')])
setd(key(5,'xiang_save_zhou'),'multiple',-771,-770,'秦襄公七年救周与平王东迁不是同一时点；年表前771年幽王遇害、前770年平王元年东迁，分别列阶段。',anchors=[P(1119),P(1120)],phases=[dict(year=-771,title='秦襄公出兵救周幽王',king='秦襄公',regnal=7,anchor=P(1119)),dict(year=-770,title='秦襄公护送平王东迁并受封',king='秦襄公',regnal=8,anchor=P(1120))])
setd(key(5,'ling_jian'),'relative',None,None,'本纪十三年筑城后记灵公卒，年表简公元年与这段纪年衔接有疑点；不把段首十三年直接当卒年，留同书系年待考。',anchors=[P(1483),P(1493)])
range_(5,'rescue_chu',-506,-501,'求援叙在秦哀公三十一年吴入楚之后；出兵未独立载年，不假定所有过程发生同年，暂约束为此事至哀公末年。',[1354])
# 秦始皇、楚汉和汉初。背景与主行动的时间分开。
for slug,king,n in [('chengjiao','秦王政',8),('dongjunstone','秦王政',36),('shootfish','秦王政',37),('erafang','秦二世',1)]:exact(6,slug,king,n)
range_(6,'lanchi',-217,-216,'原文始皇三十一年十二月；秦历十月岁首，年表对照前216年不能直接当成公历十二月。尚未历算，保留可能跨前217/216年的界限。',[1661])
range_(6,'changpingchu',-224,-223,'立昌平君及其败亡分属秦王政二十三至二十四年，属于连续反秦战事，保留前224至223年过程。',[1661])
DEC[key(6,'changpingchu')]['legacy']=True
setd(key(6,'weiliaostrategy'),'relative',None,None,'尉缭故事置于十年逐客令段，但有个人评价及后续任用，不能把整段都压为十年；保留叙事位置待核。',[1661] if False else ())
exact(7,'waihuang_pardon','汉高祖',4,extra=[689])
exact(8,'father_banquet','汉高祖',9,extra=[777])
exact(9,'zhangbiqiang_plan','汉惠帝',7)
range_(10,'bozhao_welcome',-180,-179,'本纪文帝元年十月壬子；汉初十月岁首，元年的年表对照前179年不能直接当公历十月。保留跨年前180/179界限，干支不换算。',[1837])
exact(10,'tiger_tallies','汉文帝',2,extra=[854])

range_(4,'nan_capital',-314,-256,'本段明说赧王时期迁都，未载具体年；仅约束为赧王在位范围，不能把段首或元年当迁都年。',[1593,1651])
setd(key(5,'houzizhen'),'relative',-541,None,'出奔明确在秦景公三十六年；回归在景公去世、哀公继立以后叙述，不能把景公四十年反套为回归年。出奔另列前541年阶段，返归保留相对先后。',anchors=[P(1314)],phases=[dict(year=-541,title='后子鍼因惧被诛而逃往晋国',king='秦景公',regnal=36,anchor=P(1314))])
for k,d in DEC.items():
 if d['decision']=='era':
  d['reason']+=' 本条原时间说明为：'+ITEMS[k]['time_original']+'。'
# Separate contemporary dynasty background from a named participant; phase actors are reviewed below.

# The bounded revision includes all 247 decisions, even where no absolute year is supported.
assert set(DEC)==set(ITEMS)
for k,d in DEC.items():
 assert d['reason'] and d['precision'];assert d['earliest'] is None or d['latest'] is None or d['earliest']<=d['latest'],k
 for pid in d['anchors']:assert pid in PARAS,(k,pid)
(D/'curation.json').write_text(json.dumps(dict(format_version=1,source_version='174f8dfa444c',epochs=EPOCHS,events=[dict(key=k,**d) for k,d in DEC.items()]),ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(Counter(d['decision'] for d in DEC.values()),'phases',sum(len(d['phases']) for d in DEC.values()))
