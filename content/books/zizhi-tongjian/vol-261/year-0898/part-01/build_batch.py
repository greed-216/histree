"""Curate consecutive Tongjian volume 261, year 898 paragraphs 1–12."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 48))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0898-p001-p012', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-898-spring'
fixed_commit='329c302'
source_specs=[]
titles={
 'tongjian-261-898-spring':'资治通鉴·卷261·光化元年第1—11段',
 'tongjian-261-898-suzhou-relief':'资治通鉴·卷261·光化元年第12段',
 'jiuwudaishi-026-898-palace-workers':'旧五代史·卷26·修宫丁匠与和好',
 'jiuwudaishi-018-li-zhen-genealogy':'旧五代史·卷18·李振身世与天平任职',
 'jiutangshu-020-898-wei-zhen':'旧唐书·卷20上·韦震求兼郓州',
 'xintangshu-010-898-mao-pardon':'新唐书·卷10·赦李茂贞',
 'jiuwudaishi-015-feng-jinzhu':'旧五代史·卷15·冯行袭与金州军额',
 'jiuwudaishi-133-qian-hangzhou':'旧五代史·卷133·钱镠迁军额于杭州',
}
for d in sorted((P/'sources/library').iterdir()):
 r=json.loads((d/'paragraph.json').read_text());source_specs.append((d.name,titles[d.name],{'资治通鉴':'司马光等','旧五代史':'薛居正等','新唐书':'欧阳修、宋祁等','旧唐书':'刘昫等'}[r['book']]))
reused_source_keys=set()
manifest=[]
for sk,title,author in source_specs:
 d=P/'sources/library'/sk;r=json.loads((d/'paragraph.json').read_text());filename='library/'+sk+'/source.txt';url='https://github.com/greed-216/histree/blob/'+fixed_commit+'/'+str((d/'source.txt').relative_to(ROOT))
 B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='选定TXT逐字导出；电子本，纸本及异文待核。',url=url,note=r['citation']))
 manifest.append(dict(key=sk,file=filename,sha256=hashlib.sha256((d/'source.txt').read_bytes()).hexdigest(),url=url,paragraph_id=r['id'],upstream_locator=r['locator'],transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def primary(n):return 'tongjian-261-898-suzhou-relief' if n==12 else 'tongjian-261-898-spring'
for n in range(1,13):assert Q[n]['text'] in (P/'sources/library'/primary(n)/'source.txt').read_text()
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
    B['claims'].append(dict(key=f'claim_zztj_261_0898_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=primary(n), citation=f'卷261·光化元年（898）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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
e('four_regions_request_zhu_command_denied','两浙、江西、武昌、淄青请朱全忠都统讨杨，诏不许',1,Q[1]['text'],[('朱温','被荐都统人选'),('杨行密','拟讨对象')],when='898年正月；确日未载',note='四道遣使原文未具使者或当时各道主姓名，不用地名替推具体使者；未实际获授都统。')
e('wang_shifan_added_pingzhang','王师范加同平章事',2,Q[2]['text'],[('王师范','受加者')],when='898年正月；确日未载',place='平卢军')
e('liu_chongwang_dongchuan_appointed','刘崇望同平章事任东川节度使',3,'以兵部尚书刘崇望同平章事，充东川节度使。',[('刘崇望','受任者')],when='898年正月；确日未载',place='东川',note='朝廷任命不等于已经接管王建所署留后之辖地；后续召还留待后段。')
e('feng_zhaoxin_appointed','冯行袭由昭信防御使任节度使',3,'以昭信防御使冯行袭为昭信节度使。',[('冯行袭','受任者')],when='898年正月；确日未载',place='昭信军',note='主书昭信保原军号；补书戎昭军号另附同人事实，不静改。')
e('emperor_self_blame_restores_mao','昭宗罪己息兵诏，恢复李茂贞姓名官爵',4,'上下诏罪己息兵，复李茂贞姓名官爵',[('唐昭宗','下诏者'),('李茂贞','受恢复者')],when='898年正月；确日未载',note='承897被削夺宋文通复名处分；二月正式复凤翔任命另录，不强合一次。')
e('fengxiang_campaigns_stopped','朝廷罢诸道讨凤翔军',4,'应诸道讨凤翔兵皆罢之。',[('唐昭宗','罢兵者')],when='898年正月；确日未载',place='凤翔',note='罢讨军非全部军队解散，不猜各军撤回路线。')
e('wang_ke_marriage_jinyang','王珂亲迎于晋阳',5,'壬辰，河中节度使王珂亲迎于晋阳',[('王珂','亲迎者')],when='898年正月壬辰',place='晋阳',note='亲迎为婚礼行为，本句未具新妇姓名，不新建无名配偶或擅定婚姻缔结起日。')
e('li_sizhao_guards_hezhong','李克用遣李嗣昭守河中',5,'李克用遣其将李嗣昭守河中。',[('李克用','遣将者'),('李嗣昭','受遣守者')],when='898年正月壬辰条；确日未另载',place='河中',note='守为任务，不补同时战役。')
e('mao_han_letters_li_workers','李茂贞韩建致书李克用求和及丁匠，李许之',6,Q[6]['text'],[('李茂贞','致书求和者'),('韩建','致书求匠者'),('李克用','许之者')],when='898年正月；确日未载',note='同奖王室为书中请求，不直接写成永久政治盟约；许助匠不补实际到工人数。')
e('gu_requests_mao_aid_background','顾彦晖求李茂贞救东川，李出兵救之',7,'初，王建攻东川，顾彦晖求救于李茂贞，茂贞命将出兵救之，不暇东逼乘舆',[('王建','攻东川者'),('顾彦晖','求援者'),('李茂贞','遣援者')],when='段内初王建攻东川时追叙；确年未载',year=None,place='东川',note='顾已在897死亡，此为前事；匿名受遣将不猜名字，不把出兵定898。未见既有相同求援事件，既有893赐节与求和不等同本次救兵。')
claim('person',people['李茂贞'],'description','主书追叙李茂贞救东川期间，不暇向东逼乘舆，诈称改过，与韩建共翼戴天子。',7,quote='不暇东逼乘舆，诈称改过，与韩建共翼戴天子。',note='诈称为主书评价，不变成真实认错或永久效忠。')
person('朱温',7,'曾营洛阳宫并累表迎车驾的背景人物')
claim('person',people['朱温'],'description','主书追叙朱全忠营洛阳宫，累表迎车驾；李茂贞韩建闻而惧。',7,quote='及闻硃全忠营洛阳宫，累表迎车驾，茂贞、韩建惧',note='营宫及累表为背景，确年未载；未建当年帝已至洛阳事件。')
e('mao_han_request_palace_return','李茂贞韩建请修宫阙奉帝归长安',7,'及闻硃全忠营洛阳宫，累表迎车驾，茂贞、韩建惧，请修复宫阙，奉上归长安。',[('李茂贞','请修迎还者'),('韩建','请修迎还者')],when='前述营洛阳迎驾消息后；确年未载',year=None,place='长安',note='请迎还非已实际还长安；可能跨前后年，不全定898。')
e('han_palace_restoration_commission','韩建受命修宫阙，诸道助钱工材',7,'诏以韩建为修宫阙使。诸道皆助钱及工材。',[('韩建','受命主持者')],when='请修宫后；工程起年未载',year=None,place='长安宫阙',note='诸道未逐一具名，不补任意藩镇具体贡献数额。')
e('cai_jingsi_supervises_palace','韩建使蔡敬思督修宫役',7,'建使都将蔡敬思督其役。',[('韩建','遣督工者'),('蔡敬思','都将督役者')],when='宫阙工程中；确年未载',year=None,place='长安宫阙',note='都将为军职，督工非现代工程资质，不并蔡敬思与蔡儔、蔡结。')
e('han_visits_restored_palace','宫阙既成，韩建二月往视',7,'既成，二月，建自往视之。',[('韩建','巡视者')],when='898年二月；确日未载',place='长安宫阙',note='明确二月为此时年标；前工程起始与此完工时分清。')
e('qian_requests_zhenhai_hangzhou','钱镠请迁镇海军于杭州获准',8,Q[8]['text'],[('钱镠','请迁获准者')],when='898年二月条；确日未载',place='杭州',note='迁军额治所，不把整片辖区随之易主；旧五代史相关迁额记法放在董昌僭号前，关系与日期待考。')
e('mao_fengxiang_reappointed','李茂贞复任凤翔节度使',9,Q[9]['text'],[('李茂贞','复任者')],when='898年二月条；确日未载',place='凤翔',note='与正月恢复姓名官爵分别记录，不作被裁又复任的额外猜测。')
e('shenzhi_weiwu_deputy_confirmed','王审知获授威武留后',10,Q[10]['text'],[('王审知','受授者')],when='898年三月己丑',place='威武军',note='承897自称福建留后后朝廷任命，不当当日正式节度使或封闽王。')
e('wei_zhen_petitions_tianping','朱全忠遣韦震入奏求兼天平，韦力争',11,'硃全忠遣副使万年韦震入奏事，求兼镇天平，朝廷未之许，震力争之。',[('朱温','遣使求兼者'),('韦震','入奏争请者')],when='898年三月条；确日未载',note='万年为韦籍贯语境，不写入奏去万年；旧唐书纪于正月，日期保独立。')
claim('person',people['韦震'],'description','韦震为万年人，主书称朱全忠副使。',11,quote='硃全忠遣副使万年韦震入奏事',note='副使与旧唐书判官官称各保，不据此猜完整履历或改姓。')
e('zhu_three_commands_granted','朱全忠获授宣武宣义天平三镇',11,'朝廷不得已，以全忠为宣武、宣义、天平三镇节度使。',[('朱温','兼领三镇者')],when='898年三月条争请后；确日未载',place='宣武军、宣义军、天平军',note='不得已为主书记述，不拟写未载朝廷会议或诏全文。')
e('wei_zhen_tianping_deputy','朱全忠以韦震为天平留后',11,'全忠以震为天平留后',[('朱温','署任者'),('韦震','受署留后者')],when='898年三月条三镇任命后；确日未载',place='天平军',note='朱署留后与朝廷授三镇分清。')
e('li_zhen_tianping_vice','李振任天平节度副使',11,'以前台州刺史李振为天平节度副使。',[('朱温','任副使者'),('李振','受任副使者')],when='898年三月条；确日未载',place='天平军',note='复用907档案同人；前台州刺史不表示已到台州任官，旧书记未能之任。')
person('李抱真（唐潞州节度使）',11,'李振曾祖，补书明确唐潞州节度使，不并李匡威判官')
rk='relationship_person_李抱真（唐潞州节度使）_person_李振_曾祖父'
B['person_relationships'].append(dict(key=rk,person_a_key=people['李抱真（唐潞州节度使）'],person_b_key=people['李振'],relation_type='曾祖父',description='李抱真（唐潞州节度使）是李振的曾祖父。',status='draft'))
claim('person_relationship',rk,'description','李抱真（唐潞州节度使）是李振的曾祖父。',11,quote='振，抱真之曾孙也。',note='A是B曾祖父；年代身份经旧五代史李振传明确，不认同名李匡威判官，也不补两代中间人姓名。')
e('zhou_ben_relief_suzhou_defeated','周本救苏州，被顾全武击破',12,'淮南将周本救苏州，两浙将顾全武击破之。',[('周本','救援败方'),('顾全武','击破者')],when='898年三月条；确日未载',place='苏州',note='此段击救援军不写苏州城已克；围城和秦裴后日投降按后续段落继续。')
e('qin_pei_takes_kunshan','秦裴率三千兵取昆山并驻守',12,'淮南将秦裴以兵三千人拔昆山而戍之。',[('秦裴','取城驻守者')],when='898年三月条；确日未载',place='昆山',note='三千为此段出兵数，后续守兵数不预先覆盖；不并秦彦、秦彦晖或秦宗权。')
supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
 record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0898_01_{len(B["claims"])+1:04d}'
 B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
 supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('jiuwudaishi-026-898-palace-workers','event','event_zztj_261_0898_mao_han_letters_li_workers','description','《旧五代史》亦记光化元年正月李茂贞韩建求李克用和好并助丁匠修秦宫，李许之。','光化元年春正月，鳳翔李茂貞、華州韓建皆致書於武皇，乞修和好，同獎王室，兼乞助丁匠修繕秦宮，武皇許之。',6,'同月同事，武皇依本书武皇纪李克用身份；不由同奖建立永久盟友关系。','corroborates')
extra('jiuwudaishi-018-li-zhen-genealogy','person',people['李振'],'description','《旧五代史》记李振字兴绪，唐潞州节度使李抱真曾孙，祖父父亲均至郡守。','李振，字興緒，唐潞州節度使抱真之曾孫也。祖、父，皆至郡守。',11,'跨年身世，复用既有主体；未具名祖父父亲不造姓名，曾祖不是晚唐李匡威判官。','adds')
extra('jiuwudaishi-018-li-zhen-genealogy','person_relationship',rk,'description','《旧五代史》明确李振为唐潞州节度使抱真的曾孙。','李振，字興緒，唐潞州節度使抱真之曾孫也。',11,'同人消歧与方向校核，A是B曾祖父。','corroborates')
extra('jiuwudaishi-018-li-zhen-genealogy','event','event_zztj_261_0898_li_zhen_tianping_vice','description','《旧五代史》记朱全忠兼领郓州后，署李振天平军节度副使。','太祖兼領鄆州，署天平軍節度副使。',11,'与本次任副使对应，太祖按书为朱温；郓州为天平镇治所表述，不另造二次任职。','corroborates')
extra('jiuwudaishi-018-li-zhen-genealogy','person',people['李振'],'description','《旧五代史》记李振曾改台州刺史，因浙东盗据而未能之任，西归过汴以策略干朱全忠。','振仕唐，自金吾將軍改台州刺史。會盜據浙東，不克之任，因西歸過汴，以策略幹太祖，太祖奇之，辟為從事。',11,'补台州任命与未到任，不把此前履历定898；未另造已有任用事件。','adds')
extra('jiutangshu-020-898-wei-zhen','event','event_zztj_261_0898_wei_zhen_petitions_tianping','time_original','《旧唐书》在光化元年正月记朱全忠遣判官韦震求兼郓州；主书记三月条求兼天平。','朱全忠遣判官韋震奏事，求兼領鄆州。',11,'本片年首光化元年春正月明确；两书所记是否初请与再请不同阶段待核，不静改主书三月条，副使判官称谓并列。','conflicts')
extra('xintangshu-010-898-mao-pardon','event','event_zztj_261_0898_emperor_self_blame_restores_mao','time_original','《新唐书》二月记赦李茂贞；主书正月复姓名官爵，二月复凤翔任。','二月，赦李茂貞。',4,'前段p002821光化元年正月已回查；赦与恢复官爵可能不同环节，只保补书二月，不推相同诏命确定同日。','adds')
extra('jiuwudaishi-015-feng-jinzhu','person',people['冯行袭'],'description','《旧五代史》记金州升节镇以戎昭军为额，冯行袭任节度使；主书本段称昭信。','詔升金州為節鎮，以戎昭軍為額，即以行襲為節度使。',3,'此传纪年未明，军额异记或不同时期待核，不改主书昭信，不造确定本年改军号链。','adds')
extra('jiuwudaishi-133-qian-hangzhou','event','event_zztj_261_0898_qian_requests_zhenhai_hangzhou','description','《旧五代史》在董昌僭号前叙钱镠授镇海军节度，并移润州军额于杭州为治所；主书记898年请徙镇海。','朝廷以镠為鎮海軍節度，仍移潤州軍額於杭州為治所',8,'两书叙述先后不同，是否先定治所而后再请迁额待核，保各书原位置，不凭此静改898或造两次确定迁移。','conflicts')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(1,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='十二段连续校核；任命与辖区实控分清。初东川救援及修宫起始跨年追叙不定898，既成二月明确；三月威武授留后接上年自称。韦震求天平月序、迁镇海先后和昭信戎昭记法独立引用；李振曾祖经正史消歧，不并李匡威判官。苏州救援败与城后陷分清。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=898,primary_source_key=primary(1),primary_source_keys=[primary(1),primary(12)],paragraphs=[Q[n]['id'] for n in range(1,13)],next_paragraph=Q[13]['id'],coverage='光化元年47段中的第1—12段连续整理，未完成全年。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
