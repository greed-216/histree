"""Curate consecutive Tongjian volume 261, year 898 paragraphs 25–36."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 48))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0898-p025-p036', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-898-autumn'
fixed_commit='ee8ea7b'
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
primary_keys=['tongjian-261-898-autumn','tongjian-261-898-kunshan','tongjian-261-898-october']
primary_texts={sk:(P/'sources/library'/sk/'source.txt').read_text() for sk in primary_keys}
for n in range(25,37):assert Q[n]['text'] in ''.join(primary_texts.values())
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
    q = quote or ('甲申，'+Q[n]['text'].split('甲申，',1)[1] if n==31 else Q[n]['text'])
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_261_0898_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=primary(n,q), citation=f'卷261·光化元年（898）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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
e('huazhou_xingde_renamed','华州改兴德府',25,Q[25]['text'],[('唐昭宗','朝廷改府者')],when='898年八月庚戌',place='华州、兴德府',note='行政称名变化，不表示新建另一座城或另推府界。')
e('kang_takes_deng_guo_captured','康怀贞袭取邓州，擒国湘',26,'戊午，汴将康怀贞袭邓州，克之，擒刺史国湘。',[('康怀贞','袭取者'),('国湘','被擒刺史')],when='898年八月戊午',place='邓州',note='承前邓城战之后新取邓州；擒不等于被杀，不补国湘亲属或生卒。')
e('zhao_requests_zhu_submission','赵匡凝请服朱全忠获许',26,'赵匡凝惧，遣使请服于硃全忠，全忠许之。',[('赵匡凝','请服者'),('朱温','许服者')],when='898年八月邓州陷后；确日未载',note='请服明载，不补匿名使者姓名或全套盟约条款。')
e('emperor_leaves_hua_returns_changan','昭宗离华州回长安',27,'己未，车驾发华州。壬戌，至长安。',[('唐昭宗','返京者')],when='898年八月己未发、壬戌至',place='华州、长安')
e('guanghua_amnesty_era','昭宗赦天下改元光化',27,'甲子，赦天下，改元。',[('唐昭宗','赦改元者')],when='898年八月甲子',place='长安',note='改元名光化由本年年题确定；前各条光化元年为编年追称，不意味着年初已改元。')
e('zhang_youfu_peace_mission','昭宗遣张有孚宣慰河东汴州，诏书令李朱和解',28,'上欲籓镇相与辑睦，以太子宾客张有孚为河东、汴州宣慰使，赐李克用、硃全忠诏，又令宰相与之书，使之和解。',[('唐昭宗','倡和遣使者'),('张有孚','宣慰使'),('李克用','受诏和解对象'),('朱温','受诏和解对象')],when='898年八月返京后；确日未载',note='宰相未具名不猜完整参与人；令和解不等于和解已成。')
e('li_wang_letter_zhu_refuses','李克用托王镕通意，朱全忠不从',28,'克用欲奉诏，而耻于先自屈，乃致书王镕，使通于全忠。全忠不从。',[('李克用','致书者'),('王镕','受托通意者'),('朱温','不从者')],when='898年八月宣慰诏后；确日未载',note='耻先屈为主书记述，不作精神诊断；不把次年两人修好提前写此时成功。')
for code,title,name,q in [('han_taifu_xingde','韩建守太傅兴德尹','韩建','九月，乙亥，加韩建守太傅、兴德尹'),('wang_rong_zhongshu','王镕兼中书令','王镕','加王镕兼中书令'),('luo_hongxin_shizhong','罗弘信守侍中','罗弘信','罗弘信守侍中。')]:
 e(code,title,29,q,[(name,'受加者')],when='898年九月乙亥')
e('zongdi_requests_split_five_states','王宗涤请分五州别镇，王建上表',30,Q[30]['text'],[('王宗涤','请求者'),('王建','转表者')],when='898年九月己丑',place='遂州、合州、泸州、渝州、昌州',note='五千里和数月为王宗涤陈词，未核现代距离；请别镇未见本段批准，不提前造新镇成立。')
e('suzhou_food_exhausted','顾全武围苏州，城内与援军食尽',31,'顾全武攻苏州，城中及援兵食皆尽。',[('顾全武','围攻者')],when='898年九月甲申取城前；确日未载',place='苏州')
e('tai_meng_flees_suzhou_taken','台濛弃苏州，顾全武取城',31,'甲申，淮南所署苏州刺史台濛弃城走，援兵亦遁。全武克苏州',[('台濛','弃城者'),('顾全武','取城者')],when='898年九月甲申',place='苏州',note='淮南所署职与朝廷正式授官分清，不补匿名援军各将。')
e('gu_defeats_zhou_wangting','顾全武追败周本于望亭',31,'追败周本等于望亭。',[('顾全武','追击者'),('周本','被击败者')],when='898年九月苏州取后；确日未另载',place='望亭')
e('gu_attacks_kunshan_qin_resists','顾全武万余军攻昆山，秦裴屡战拒之',31,'独秦裴守昆山不下，全武帅万馀人攻之。裴屡出战，使病者被甲执矛，壮者彀弓弩，全武每为之却。',[('顾全武','攻城者'),('秦裴','坚守者')],when='898年九月苏州失后持续围攻；确起止日未载',place='昆山',note='万余为顾攻军，不是秦守军；病壮部署按原载，不补疾病诊断。')
e('qin_sends_buddhist_text','秦裴以佛经回顾全武招降函',31,'全武檄裴令降。全武尝为僧，裴封函纳款，全武喜，召诸将发函，乃佛经一卷，全武大惭，曰：“裴不忧死，何暇戏予！”',[('顾全武','招降发函者'),('秦裴','函中寄经者')],when='898年昆山围中；确日未载',place='昆山',note='纳款表面函语，实佛经讥戏，不作这一步已正式投降；尝僧是既往经历，不记当年出家。')
e('kunshan_flood_qin_surrenders','顾全武灌昆山，城坏粮尽秦裴降',31,'益兵攻城，引水灌之，城坏，食尽，裴乃降。',[('顾全武','增兵灌城者'),('秦裴','力屈投降者')],when='898年昆山围后；确月日未另载',place='昆山',note='发生在取苏后的延续围城，不全部强定甲申日。')
e('qian_qin_banquet_plea_mercy','钱镠宴秦裴降军，顾全武劝宥获准',31,'钱镠设千人馔以待之，及出，羸兵不满百人。镠怒曰：“单弱如此，何敢久为旅拒！”对曰：“裴义不负杨公，今力屈而降耳，非心降也。”镠善其言。顾全武亦劝镠宥之，镠从之。',[('钱镠','设宴准宥者'),('秦裴','陈降意者'),('顾全武','劝宥者')],when='898年秦裴降后；确月日未载',note='千人馔是备宴容量，非当时实有一千守兵；不满百为出降人数，不算三千兵到此精确死伤。非心降为秦自陈。')
claim('person',people['顾全武'],'description','主书评顾全武劝宥秦裴，时人称其长者。',31,quote='顾全武亦劝镠宥之，镠从之。时人称全武长者。',note='长者为当时评价，非现代实证人格诊断。')
e('luo_hongxin_dies_army_chooses_son','罗弘信去世，军推罗绍威知留后',32,Q[32]['text'],[('罗弘信','去世节度使'),('罗绍威','军中推立者')],when='898年九月条；确日未载',place='魏博军',note='军中推立与第36段朝廷任命分别录，十一月正式授节待后段。')
claim('person',people['罗弘信'],'death_year','898年九月条记罗弘信去世。',32,quote='魏博节度使罗弘信薨')
rk='relationship_person_罗弘信_person_罗绍威_父亲'
B['person_relationships'].append(dict(key=rk,person_a_key=people['罗弘信'],person_b_key=people['罗绍威'],relation_type='父亲',description='罗弘信是罗绍威的父亲。',status='draft'))
claim('person_relationship',rk,'description','罗弘信是罗绍威的父亲。',32,quote='军中推其子节度副使绍威知留后。',note='其子承前罗弘信；A是B父亲，不给关系添当年始立日期。')
e('zhu_yougong_accusation_wu_killed','朱友恭过安州，因通淮指控攻杀武瑜',33,Q[33]['text'],[('朱友恭','攻杀者'),('武瑜','被指控并杀的刺史')],when='898年十月己亥',place='安州',note='或告潜通淮南谋取汴军是匿名指控，不认定已证实谋反；朱友恭复用李彦威主体。')
claim('person',people['武瑜'],'death_year','898年十月己亥安州刺史武瑜被朱友恭攻杀。',33,quote='冬，十月，己亥，友恭攻而杀之。')
e('li_sizhao_dewei_campaign_xing','李克用遣李嗣昭周德威二万兵出青山复三州',34,'李克用遣其将李嗣昭、周德威将步骑二万出青山，将复山东三州。',[('李克用','遣军者'),('李嗣昭','率军者'),('周德威','率军者')],when='898年十月邢州战前条；确日未载',place='青山、邢洺磁三州',note='山东指太行山以东三州，非现代山东省；将复为目的，不写已收三州。补书九月三万另保异记。')
e('ge_defeats_li_at_xing','河东攻邢州被葛从周破',34,'壬寅，进攻邢州，葛从周出战，大破之。',[('李嗣昭','败方主将'),('周德威','同领军者'),('葛从周','击破者')],when='898年十月壬寅',place='邢州')
e('ge_pursues_qingshan_infantry_breaks','葛从周追河东至青山，步兵溃',34,'嗣昭等引兵退入青山，从周追之，将扼其归路。步兵自溃，嗣昭不能制。',[('李嗣昭','退军者'),('周德威','同领退军者'),('葛从周','追击者')],when='898年十月邢州败后；确日未另载',place='青山',note='将扼为意图，不推归路全被封；步兵自溃不记所有骑兵同溃。')
e('li_siyuan_sizhao_counterattack','李嗣源高地列阵奋击，李嗣昭继进退葛军',34,'会横冲都将李嗣源以所部兵至，谓嗣昭曰：“吾辈亦去，则势不可支矣，我试为公击之。”嗣昭曰：“善，我请从公后。”嗣源乃解鞍厉镞，乘高布阵，左右指画，邢队莫之测。嗣源直前奋击，嗣昭继之，从周乃退。',[('李嗣源','到援列阵反击者'),('李嗣昭','继进者'),('葛从周','退兵者')],when='898年十月青山退军中；确日未另载',place='青山',note='李嗣源复用已有后唐明宗主体；葛退不等于三州已收复。旧明宗纪相似战于前乾宁三年之后明年，年序差异需核。')
claim('person',people['周德威'],'description','周德威为马邑人。',34,quote='德威，马邑人也。',note='马邑为籍贯，不当战场。')
e('shenzhi_full_jiedushi','王审知正式授节度使',35,Q[35]['text'],[('王审知','正式受授者')],when='898年十月癸卯',place='威武军',note='承三月留后，不提前称闽王。')
e('luo_shaowei_court_deputy','朝廷以罗绍威知魏博留后',36,Q[36]['text'],[('罗绍威','获朝廷任命者')],when='898年十月条；确日未载',place='魏博军',note='与九月军中推立分录；本句未单列癸卯，不能强填同日。')
supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
 record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0898_03_{len(B["claims"])+1:04d}'
 B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
 supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('jiutangshu-020-898-return','event','event_zztj_261_0898_emperor_leaves_hua_returns_changan','time_original','《旧唐书》记八月己未车驾自华还京师，主书同日发华、壬戌至长安。','八月戊戌朔。己未，車駕自華還京師。',27,'本纪统述还京不强作当己未日已抵长安；保主书起程到达分别。','corroborates')
extra('jiutangshu-020-898-return','event','event_zztj_261_0898_guanghua_amnesty_era','description','《旧唐书》记甲子御端门大赦，改元光化。','甲子，御端門，大赦，改元光化。',27,'同日改元，端门为补细节，未反推年初已称光化。','adds')
extra('jiuwudaishi-026-898-peace-xing','event','event_zztj_261_0898_li_wang_letter_zhu_refuses','description','《旧五代史》记还宫后诏李朱通好，李不欲先下，托王镕导意；次年方记互通书币。','武皇不欲先下汴帥，乃致書於鎮州王鎔，令導其意。明年，汴帥遣使奉書幣來修好，武皇亦報之。',28,'次年修好只补叙事时序，不建当前批次当年和解成功；王鎔与镕字形保原。','adds')
extra('xintangshu-010-898-suzhou','event','event_zztj_261_0898_tai_meng_flees_suzhou_taken','time_original','《新唐书》九月甲申记钱镠陷苏州，与主书顾军取城同日。','甲申，錢鏐陷蘇州。',31,'钱为统帅、顾为执行将领不同叙事层级，非另造第二次夺城。','corroborates')
extra('xinwudaishi-039-898-luo-succession','event','event_zztj_261_0898_luo_hongxin_dies_army_chooses_son','description','《新五代史》罗绍威传亦记弘信死、绍威立。','弘信死，紹威立。',32,'这里只印证继承，未单列年日，不替主书补月日或朝廷正式授节时刻。','corroborates')
extra('jiuwudaishi-026-898-peace-xing','event','event_zztj_261_0898_li_sizhao_dewei_campaign_xing','time_original','《旧五代史》记九月遣周德威李嗣昭三万出青山口，主书十月条遣二万。','九月，武皇遣周德威、李嗣昭率兵三萬出青山口，以迫邢、洺。',34,'可能出发与交战分月，但兵数二万/三万仍保异记，不强凑总数或另造一支确定后援。','conflicts')
extra('jiuwudaishi-026-898-peace-xing','event','event_zztj_261_0898_ge_defeats_li_at_xing','description','《旧五代史》记十月遇葛从周于张公桥、河东败。','十月，遇汴將葛從周於張公橋，既戰，我軍大敗。',34,'补战场表述，主书进攻邢州与青山退兵保持；张公桥不猜现代坐标。','adds')
extra('jiuwudaishi-035-898-siyuan','event','event_zztj_261_0898_li_siyuan_sizhao_counterattack','description','《旧五代史》明宗纪有近似救援叙述，记李嗣源解鞍砺镞、凭高列阵。','帝率其屬，解鞍礪鏃，憑高列陣，左右指畫，梁人莫之測',34,'帝为明宗李嗣源；此段开明年，前p001077乾宁三年已回查，按字面是897，与主书898差年，是否同战待考。这里只保相似叙述，不把伤箭等未核细节直接改入主书事件。','conflicts')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(25,37):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='十二段连续校核；返京起程到达和改元分录，别镇申请不当批准。苏州取城与昆山围降持续时段分清，备宴千人不算降兵。魏军推立与朝廷授留后分录；武瑜通淮是指控。邢青山兵数与旧明宗纪年序差异保独立引用，未强填现代地理。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=898,primary_source_key=source,primary_source_keys=primary_keys,paragraphs=[Q[n]['id'] for n in range(25,37)],next_paragraph=Q[37]['id'],coverage='光化元年47段中的第25—36段连续整理，本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
