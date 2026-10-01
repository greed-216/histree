"""Curate consecutive Tongjian volume 261, year 898 paragraphs 13–24."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 48))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0898-p013-p024', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-898-summer'
fixed_commit='f7f4d26'
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
def primary(n):return source
for n in range(13,25):assert Q[n]['text'] in (P/'sources/library'/primary(n)/'source.txt').read_text()
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
    B['claims'].append(dict(key=f'claim_zztj_261_0898_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=primary(n), citation=f'卷261·光化元年（898）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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
e('ma_yin_wuan_deputy','马殷知武安留后',13,'以潭州刺史、判湖南军府事马殷知武安留后。',[('马殷','受任留后者')],when='898年三月条；确日未载',place='武安军',note='知留后不改正式节度使；后句所得潭邵不等于已实控七州。')
for name,place in [('杨师远','衡州'),('唐世旻','永州'),('蔡结','道州'),('陈彦谦','郴州'),('鲁景仁','连州')]:
 person(name,13,f'据{place}的地方首领，主书称贼帅')
 claim('person',people[name],'description',f'本段湖南七州形势记{name}据{place}。',13,quote=Q[13]['text'],note='此为当时控制状态，未载始据年月；不补正式刺史授官或占城战役，史称贼帅与现代描述分清。')
claim('person',people['马殷'],'description','本段湖南管内七州，马殷所得只有潭、邵二州。',13,quote='殷所得惟潭、邵而已。',note='行政七州与实际据两州分清，不把其余五州先算已收复。')
e('liu_lu_contest_salt','刘仁恭与卢彦威争盐利',14,'与卢龙节度使刘仁恭争盐利',[('卢彦威','争盐利者'),('刘仁恭','争盐利者')],when='898年袭沧州前；确起年未载',year=None,place='卢龙、义昌邻境',note='原文未载争利起时和具体盐场，不画确定边界或以残虐评价替代证据。')
e('liu_shouwen_attacks_cang','刘仁恭遣刘守文袭沧州',14,'仁恭遣其子守文将兵袭沧州',[('刘仁恭','遣子者'),('刘守文','领兵袭州者')],when='898年三月条；确日未载',place='沧州')
e('lu_flees_wei_refused_bian','卢彦威弃沧州奔魏，罗弘信拒而转奔汴',14,'彦威弃城，挈家奔魏州。罗弘信不纳，乃奔汴州。',[('卢彦威','弃城出奔者'),('罗弘信','拒纳者')],when='898年三月条沧州被袭后；确日未载',place='沧州、魏州、汴州',note='匿名家人不猜姓名；旧书魏送汴与主书拒纳异叙并列。')
e('liu_takes_three_prefectures_shouwen_deputy','刘仁恭取沧景德，以刘守文义昌留后',14,'仁恭遂取沧、景、德三州，以守文为义昌留后。',[('刘仁恭','取州署任者'),('刘守文','受署留后者')],when='898年三月条；确日未载',place='沧州、景州、德州',note='父署留后不等于朝廷已授节。')
e('liu_requests_shouwen_insignia_denied','刘仁恭为守文请节未许，向中使争长安本色',14,'仁恭兵势益盛，自谓得天助，有并吞河朔之志，为守文请旌节，朝廷未许。会中使至范阳，仁恭语之曰：“旌节吾自有之，但欲得长安本色耳，何为累章见拒，为吾言之！”其悖慢如此。',[('刘仁恭','请节争说者'),('刘守文','未获节人选')],when='898年三月取州署留后后；确日未载',place='范阳',note='自谓天助和并吞志为原书人物心理记述，不写天助客观事实；匿名中使不猜人名。')
rk='relationship_person_刘仁恭_person_刘守文_父亲'
B['person_relationships'].append(dict(key=rk,person_a_key=people['刘仁恭'],person_b_key=people['刘守文'],relation_type='父亲',description='刘仁恭是刘守文的父亲。',status='draft'))
claim('person_relationship',rk,'description','刘仁恭是刘守文的父亲。',14,quote='仁恭遣其子守文将兵袭沧州',note='A是B父亲；未载出生年或关系起时，父子与政治支持分开。')
e('zhu_liu_reconcile_attack_li','朱全忠与刘仁恭修好，合魏博兵击李克用',15,'硃全忠与刘仁恭修好，会魏博兵击李克用。',[('朱温','修好会兵者'),('刘仁恭','修好者'),('李克用','被击对象')],when='898年四月巨鹿战前；确日未载',note='魏博兵未具将领姓名，不给罗弘信强加亲自出战；修好不补终身盟约或猜所有军同时到场。')
e('zhu_julu_victory_qingshan','朱全忠至巨鹿败河东军，北至青山口',15,'夏，四月，丁未，全忠至巨鹿城下，败河东兵万馀人，遂北至青山口。',[('朱温','至城击败者')],when='898年四月丁未；北进确日未另载',place='巨鹿、青山口',note='主書敗萬餘不等於全部斬首萬餘；旧书记败于青山口，战场位置异述保引，不静改主书句法。')
e('wang_ke_added_shizhong','王珂兼侍中',16,Q[16]['text'],[('王珂','受加者')],when='898年四月条；确日未载',place='护国军')
e('ge_mingzhou_attack_capture','葛从周分兵攻洺州并取城斩邢善益',17,Q[17]['text'],[('朱温','遣攻者'),('葛从周','攻取者'),('邢善益','被斩刺史')],when='898年四月丁卯遣攻、戊辰取城',place='洺州',note='遣攻与取城各保日，不合为一个日；丁卯、戊辰保原干支不换公历。')
claim('person',people['邢善益'],'death_year','898年四月戊辰洺州陷，刺史邢善益被斩。',17,quote='戊辰，拔之，斩刺史邢善益。')
e('may_amnesty','五月己巳朔赦天下',18,Q[18]['text'],[('唐昭宗','赦令发布者')],when='898年五月己巳朔',note='按朝廷赦令语境，不补具体豁免对象名单。')
e('ge_xingzhou_ma_flees','葛从周攻邢州，马师素弃城',19,'葛从周攻邢州，刺史马师素弃城走。',[('葛从周','攻城者'),('马师素','弃城者')],when='898年五月条；主书未另记此事确日',place='邢州',note='承五月己巳朔条，补书明记己巳另引，不倒填主书未列日。')
e('yuan_fengtao_suicide','磁州袁奉滔自刭',19,'辛未，磁州刺史袁奉滔自刭。',[('袁奉滔','自刭刺史')],when='898年五月辛未',place='磁州')
claim('person',people['袁奉滔'],'death_year','898年五月辛未磁州刺史袁奉滔自刭。',19,quote='辛未，磁州刺史袁奉滔自刭。')
e('ge_zhaoyi_deputy_three_prefectures','葛从周任昭义留后守邢洺磁，朱全忠还',19,'全忠以从周为昭义留后，守邢、洺、磁三州而还。',[('朱温','署留后还师者'),('葛从周','受署守三州者')],when='898年五月三州既取后；确日未载',place='邢州、洺州、磁州',note='昭义在此为邢洺磁一镇，不误作同时已取潞州昭义；而还主语全忠保主书语境。')
e('li_jimi_shannan_west','李继密任山南西道节度使',20,Q[20]['text'],[('李继密','受任者')],when='898年五月条；确日未载',place='山南西道',note='沿已有同名人物，不并李继瑭、李继溥。')
e('liu_chongwang_recalled_zongdi_confirmed','刘崇望召还兵部，王宗涤仍留后',21,'朝廷闻王建已用王宗涤为东川留后，乃召刘崇望还，为兵部尚书，仍以宗涤为留后。',[('王建','已署留后者'),('王宗涤','获仍留后者'),('刘崇望','召还任尚书者')],when='898年五月条；确日未载',place='东川',note='承正月任刘，王建先署王宗涤是已录897任命，不新建重复同次署任；召还不猜到京日期。')
e('yao_requests_five_states_recommends_li','姚彦章劝马殷取五州并荐李琼',21,'湖南将姚彦章言于马殷，请取衡、永、道、连、郴五州，仍荐李琼为将。',[('姚彦章','建策荐将者'),('马殷','受策者'),('李琼','被荐将领')],when='898年五月湖南进军前条；确日未载',place='衡州、永州、道州、连州、郴州',note='请取五州不等于已取五州，后段本批只明记衡永。')
e('ma_lingbei_roving_commanders','马殷署李琼秦彦晖游奕使，张图英李唐副之',21,'殷以琼及秦彦晖为岭北七州游奕使，张图英、李唐副之',[('马殷','任将者'),('李琼','游奕使'),('秦彦晖','游奕使'),('张图英','副将'),('李唐','副将')],when='898年五月条进军前；确日未载',place='岭北七州',note='游奕使军职不改每州刺史；张图英不并张佶，李唐为人名不当朝代，秦彦晖不并秦裴秦彦。')
e('lingbei_takes_heng_kills_yang','岭北军攻衡州斩杨师远',21,'将兵攻衡州，斩杨师远',[('李琼','领军者'),('秦彦晖','领军者'),('张图英','副将'),('李唐','副将'),('杨师远','被斩据州者')],when='898年五月条湖南进军；确日未载',place='衡州',note='领军及副将承前句身份，不写馬殷親至。')
claim('person',people['杨师远'],'death_year','898年湖南军攻衡州，杨师远被斩。',21,quote='将兵攻衡州，斩杨师远')
e('lingbei_sieges_yong_tang_dies_fleeing','岭北军围永州月余，唐世旻逃而死',21,'引兵趣永州，围之月馀，唐世旻走死。',[('李琼','领军者'),('秦彦晖','领军者'),('张图英','副将'),('李唐','副将'),('唐世旻','出逃死亡者')],when='898年衡州既取后围月余；确月日未载',place='永州',note='月余不推出具体始终日；走死不改为被斩或擒后处决。')
claim('person',people['唐世旻'],'death_year','898年永州被围月余后唐世旻走死。',21,quote='围之月馀，唐世旻走死。')
e('li_tang_yongzhou_appointed','李唐任永州刺史',21,'殷以李唐为永州刺史。',[('马殷','署任者'),('李唐','受任者')],when='898年永州既取后；确日未载',place='永州')
e('zhao_xu_zhongwu_appointed','赵珝由濠州任忠武节度使',22,'六月，以濠州刺史赵珝为忠武节度使。',[('赵珝','受任者')],when='898年六月；确日未载',place='忠武军')
person('赵犨',22,'赵珝之兄，身份记述非本年活动')
rk2='relationship_person_赵犨_person_赵珝_兄长'
B['person_relationships'].append(dict(key=rk2,person_a_key=people['赵犨'],person_b_key=people['赵珝'],relation_type='兄长',description='赵犨是赵珝的兄长。',status='draft'))
claim('person_relationship',rk2,'description','赵犨是赵珝的兄长。',22,quote='珝，犨之弟也。',note='A是B兄长；不据弟的任职推兄赵犨仍在世或同行授官。')
e('lei_man_added_pingzhang','雷满加同平章事',23,'秋，七月，加武贞节度使雷满同平章事',[('雷满','受加者')],when='898年七月；确日未载',place='武贞军')
e('zhong_chuan_added_shizhong','钟传加兼侍中',23,'加镇南节度使钟传兼侍中。',[('钟传','受加者')],when='898年七月；确日未载',place='镇南军')
e('zhao_kuangning_secret_yang','赵匡凝闻清口败，暗附杨行密',24,'忠义节度使赵匡凝闻硃全忠有清口之败，阴附于杨行密。',[('赵匡凝','暗附者'),('杨行密','受附对象')],when='897年清口战后至898年七月征讨前；起年未载',year=None,note='追述政策转向，不全定898；暗附未载具体盟约或官属任命，不推长期对称盟友关系。')
e('shi_shucong_sent_against_zhao','朱全忠遣氏叔琮讨赵匡凝',24,'全忠遣宿州刺史尉氏氏叔琮将兵伐之',[('朱温','遣将者'),('氏叔琮','领兵者'),('赵匡凝','被讨对象')],when='898年七月；确日未载',note='尉氏为氏叔琮籍贯，不是另一个氏姓或军到尉氏；不并叔琮叔宗。')
claim('person',people['氏叔琮'],'description','氏叔琮为尉氏人，本段称宿州刺史。',24,quote='宿州刺史尉氏氏叔琮')
e('shi_takes_tangzhou','氏叔琮军拔唐州',24,'丙申，拔唐州',[('氏叔琮','领军取州者')],when='898年七月丙申',place='唐州')
e('shi_captures_suizhou_zhao','氏叔琮军擒随州刺史赵匡璘',24,'擒随州刺史赵匡璘',[('氏叔琮','领军擒将者'),('赵匡璘','被擒刺史')],when='898年七月丙申条；确日未另载',note='刺史任地随州不当明确在随州城被擒；旧书临阵就擒无具体战地，地点及坐标空。赵匡璘与赵匡凝的亲属未载，不因同字推兄弟。')
e('shi_defeats_xiang_dengcheng','氏叔琮军在邓城败襄州兵',24,'败襄州兵于邓城。',[('氏叔琮','领军击败者')],when='898年七月丙申条；确日未另载',place='邓城',note='邓城战不改为邓州城当日已取；后康怀贞袭邓州待后段。')

supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
 record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0898_02_{len(B["claims"])+1:04d}'
 B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
 supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('jiuwudaishi-133-ma-yin-background','person',people['马殷'],'description','《旧五代史》记马殷字霸图，许州鄢陵人，早年为木工。','馬殷，字霸圖，許州鄢陵人也。少為木工',13,'补身世，未把早年职业定898；本传久之授节遂有七州为跨年总述，不提前替主书潭邵二州。','adds')
extra('xintangshu-010-898-cangzhou','event','event_zztj_261_0898_liu_shouwen_attacks_cang','time_original','《新唐书》记三月刘仁恭之子守文陷沧州，卢彦威奔汴。','三月，幽州盧龍軍節度使劉仁恭之子守文陷滄州，義昌軍節度使盧彥威奔于汴州。',14,'本纪光化元年上下文与主书三月对应，未补确日。','corroborates')
extra('jiuwudaishi-135-898-cangzhou','event','event_zztj_261_0898_liu_takes_three_prefectures_shouwen_deputy','description','《旧五代史》亦记光化元年三月袭州后得沧景德三郡，署守文留后。','光化元年三月，令其長子襲淪州，盧彥威委城而遁，遂兼有滄、景、德三郡，以守文為留後',14,'原淪州字形保快照，后文滄與同事定位支持归到本事件，但不静改底本。','corroborates')
extra('jiuwudaishi-135-898-cangzhou','event','event_zztj_261_0898_liu_requests_shouwen_insignia_denied','description','《旧五代史》亦记请节未给，中使至范阳，刘争长安本色。','請節鉞於朝。昭宗怒其擅興，不時與之。會中使至范陽，仁恭私之曰：「旄節吾自有，但要長安本色耳，何以累章見阻？為吾言之。」',14,'补书增昭宗怒与不时给，刘言为请求不是已获节事实；引长安本色原词不猜材质。','adds')
extra('jiuwudaishi-002-898-campaigns','person',people['卢彦威'],'description','《旧五代史》梁纪此处称沧州节度卢廷彦；主书与其他两史称卢彦威。','四月，滄州節度使盧廷彥為燕軍所攻，棄城奔于魏，魏人送於汴。',14,'同州同役的姓名异记，保既有卢彦威主体并说明，不强设正式别名或新建卢廷彦。','conflicts')
extra('jiuwudaishi-002-898-campaigns','event','event_zztj_261_0898_lu_flees_wei_refused_bian','time_original','《旧五代史》梁纪记四月卢廷彦弃城奔魏、魏送汴；主书三月条记卢彦威被拒而奔汴。','四月，滄州節度使盧廷彥為燕軍所攻，棄城奔于魏，魏人送於汴。',14,'月份与魏送/拒纳过程异叙，可能阶段不同但未证；保独立记法不覆盖主书。','conflicts')
extra('jiuwudaishi-002-898-campaigns','event','event_zztj_261_0898_zhu_julu_victory_qingshan','description','《旧五代史》记朱至钜鹿屯城下、于青山口败晋军万余并俘马千余。','是月，帝以大軍至钜鹿，屯於城下，敗晉軍萬餘眾于青山口，俘馬千餘匹。',15,'主书句法败军后遂北至青山口，补书明确败于青山口；地点先后并列，不猜两个确定独立战役。钜鹿/巨鹿按字形对应，不改底本。','adds')
extra('jiuwudaishi-002-898-campaigns','event','event_zztj_261_0898_ge_mingzhou_attack_capture','description','《旧五代史》同丁卯遣葛攻洺州，斩邢善益并擒将五十余。','丁卯，遣從周分兵攻洺州，斬刺史邢善益，擒將五十餘人。',17,'补书统叙未另列戊辰，主书遣与取日分别保；五十余擒将为补数，不加匿名个人。','corroborates')
extra('jiuwudaishi-002-898-campaigns','event','event_zztj_261_0898_ge_xingzhou_ma_flees','time_original','《旧五代史》记五月己巳马师素弃邢州；主书本段未另标其日。','五月己巳，邢州刺史馬師素棄城遁去。',19,'本书记具体日，主书相邻赦条也是己巳朔但不将未标日者强填为己巳。','adds')
extra('jiuwudaishi-002-898-campaigns','event','event_zztj_261_0898_yuan_fengtao_suicide','time_original','《旧五代史》亦记辛未磁州袁奉滔自剄死。','辛未，磁州刺史袁奉滔自剄而死。',19,'同月同日同人，刭剄字形各保。','corroborates')
extra('xinwudaishi-042-zhao-brothers','person_relationship',rk2,'description','《新五代史》赵犨传记其弟昶、珝为将，印证赵珝为赵犨之弟。','以其弟昶、珝為將。',22,'早年亲属身份，不将该任将事件定898；不并珝与另一弟昶。','corroborates')
extra('jiuwudaishi-017-898-zhao-capture','event','event_zztj_261_0898_shi_shucong_sent_against_zhao','description','《旧五代史》赵匡凝传记清口败后密附淮，朱遣氏叔琮伐。','光化初，匡凝以太祖有清口之敗，密附於淮夷，太祖遣氏叔琮率師伐之。',24,'光化初总述不补确月日；淮夷为史载称呼，整理用杨行密方面，未造正式君臣。','corroborates')
extra('jiuwudaishi-017-898-zhao-capture','event','event_zztj_261_0898_shi_captures_suizhou_zhao','description','《旧五代史》赵传同称随州刺史赵匡璘临阵被擒。','隨州刺史趙匡璘臨陣就擒。',24,'与主书同名，临阵非随州城定位；不补处决、生卒或匡凝亲属。','corroborates')
extra('jiuwudaishi-002-898-campaigns','person',people['赵匡璘'],'description','《旧五代史》梁纪作随州赵匡琳临阵被擒；主书与赵传作匡璘。','隨州刺史趙匡琳臨陣就擒。',24,'同州同役书内异名，保持主书匡璘主体，未核前不强写琳为正式别名。','conflicts')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(13,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='十二段连续校核；湖南七州行政范围与潭邵实控分清，衡永进军及署官循叙事。沧州月序姓名异記与魏拒/送汴独立引用，父亲兄长方向明示。邢洺磁昭义留后不混潞州；杨被斩、唐走死、袁自刭分别保。赵附淮追述起年空，邓城战不当邓州陷。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=898,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(13,25)],next_paragraph=Q[25]['id'],coverage='光化元年47段中的第13—24段连续整理，本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
