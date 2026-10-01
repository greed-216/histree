"""Curate consecutive Tongjian volume 261, year 897 paragraphs 4–12."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 51))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0897-p004-p012', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-897-p004-p012'
fixed_commit='3cf1551'
reused_source_keys={'jiutangshu-020a-897-army-prince','jiuwudaishi-001-897-yunzhou'}
old_sources={r['key']:r for r in json.loads((YEAR/'part-01/content-batch.json').read_text())['sources']}
source_specs=[(source,'资治通鉴·卷261·乾宁四年第4—12段','司马光等'),('xinwudaishi-042-897-zhu-jin','新五代史·卷42·朱瑾奔淮南','欧阳修'),('xinwudaishi-013-zhang-wife','新五代史·卷13·朱温妻张氏','欧阳修'),('xinwudaishi-040-yang-chongben','新五代史·卷40·杨崇本姓名与收养','欧阳修'),('jiuwudaishi-052-li-sizhao','旧五代史·卷52·李嗣昭身世','薛居正等'),('jiutangshu-020a-897-ma-xu','旧唐书·卷20上·马道殷许岩士后事','刘昫等'),('jiutangshu-020a-897-army-prince','',''),('jiuwudaishi-001-897-yunzhou','','')]
manifest=[]
for sk,title,author in source_specs:
    if sk==source:
        records=[json.loads((P/'sources/library'/part/'paragraph.json').read_text()) for part in ['tongjian-opening-a','tongjian-opening-b']];filename='tongjian-261-897-p004-p012.txt';citation='《资治通鉴》卷261乾宁四年；原TXT连续段落 '+ '、'.join(r['id'] for r in records)
    else:
        records=[json.loads((P/'sources/library'/sk/'paragraph.json').read_text())];filename='library/'+sk+'/source.txt';citation=records[0]['citation']
    snapshot=P/'sources'/filename;url='https://github.com/greed-216/histree/blob/'+fixed_commit+'/'+str(snapshot.relative_to(ROOT))
    if sk in reused_source_keys:
        row=dict(old_sources[sk]);url=row['url']
    else:row=dict(key=sk,title=title,source_type='primary',author=author,edition='选定TXT逐字导出；电子本，纸本及异文待核。',url=url,note=citation)
    B['sources'].append(row)
    manifest.append(dict(key=sk,file=filename,sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),url=url,paragraph_ids=[r['id'] for r in records],upstream_locators=[r['locator'] for r in records],transformation='主书相邻两份导出TXT按原字节拼接；补书保逐字导出，复用书证保既有主体及固定出处。'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for n in range(4,13):assert Q[n]['text'] in (P/'sources/tongjian-261-897-p004-p012.txt').read_text()
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
alias.update({'王宗播':'许存','杜弘':'杜洪','嵩从周':'葛从周','硃瑾':'朱瑾','硃宣':'朱瑄','李继徽':'杨崇本','硃朴':'朱朴','韩健':'韩建','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_261_0897_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷261·乾宁四年（897）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷261乾宁四年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=897,note=None,quote=None):
    key='event_zztj_261_0897_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_261_0897_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def e(code,title,n,q,actors=(),when=None,place=None,note=None,description=None,year=897):
    return event(code,title,n,when or '897年本段条；确日未载',place,description or title+'。',actors,quote=q,note=note,year=year)
e('zhu_enters_yun_pang_retainer','朱温入郓州，以庞师古为天平留后',4,'硃全忠入郓州，以庞师古为天平留后。',[('朱温','入城署任者'),('庞师古','受留后者')],when='897年正月郓州陷后；确日未载',place='郓州',note='旧五代史初署朱友裕与主书先庞师古、三月再表友裕不同，独立附异记。')
e('zhu_jin_leaves_kang_plunders_food','朱瑾留康怀贞守兖，与史俨李承嗣掠徐境给食',4,'硃瑾留大将康怀贞守兗州。与河东将史俨、李承嗣掠徐州之境给军食。',[('朱瑾','留将外掠者'),('康怀贞','留守者'),('史俨','同掠者'),('李承嗣','同掠者')],when='897年正月兖州陷前；确日未载',place='兖州、徐州之境',note='河东二将与朱瑾同掠，不据此改其出身；康怀贞复用旧人物，补书康怀英保异字。')
e('zhu_sends_ge_surprise_yan','朱温遣葛从周袭兖州',4,'全忠闻之，遣嵩从周将兵袭兗州。',[('朱温','遣袭者'),('葛从周','领袭者')],when='897年正月末至二月兖州陷前；确日未载',place='兖州',note='嵩从周疑字按上下文与两唐书葛从周复用，不新建嵩姓人物。')
e('kang_surrenders_yan','康怀贞因郓州失守、汴兵至而降',4,'怀贞闻郓州已失守，汴兵奄至，遂降。',[('康怀贞','降者')],when='897年兖州陷前；确日未载',place='兖州')
e('ge_enters_yan_captures_family','葛从周入兖州，获朱瑾妻子',4,'二月，戊申，从周入兗州，获瑾妻子。',[('葛从周','入城者'),('朱瑾妻（兖州被俘者）','被俘妻')],when='897年二月戊申',place='兖州',note='妻子不据此补子女姓名；女子原名未详，以本次被俘身份消歧，不将姓氏猜为朱。')
e('zhu_jin_denied_yizhou','朱瑾返无归、趋沂州，尹处宾拒纳',4,'硃瑾还，无所归，帅其众趋沂州，刺史尹处宾不纳',[('朱瑾','求入者'),('尹处宾','拒纳者')],when='897年二月兖州陷后；确日未载',place='沂州',note='复用异书处賓字形对应同地同职，不推其他籍贯或死期。')
e('zhu_jin_haizhou_cross_huai','朱瑾保海州受逼，与河东二将拥州民渡淮',4,'走保海州，为汴兵所逼，与史俨、李承嗣拥州民度淮，奔杨行密。',[('朱瑾','渡淮投奔者'),('史俨','同渡者'),('李承嗣','同渡者')],when='897年二月拒入沂州以后；确日未载',place='海州、淮水',note='拥州民度淮按原文，不补自愿迁徙或确切人口；奔向杨不等于已有中央节度诏。')
e('yang_welcomes_jin_gaoyou','杨行密于高邮迎朱瑾',4,'行密逆之于高邮',[('杨行密','迎者'),('朱瑾','受迎者')],when='897年二月朱瑾渡淮后；确日未载',place='高邮')
e('yang_petitions_jin_wuning','杨行密表朱瑾领武宁节度使',4,'表瑾领武宁节度使。',[('杨行密','上表者'),('朱瑾','被表者')],when='897年二月迎接朱瑾后；确日未载',note='表领为表荐，未推实际进驻徐州或中央批准日。')
e('zhu_takes_jin_wife_returns','朱温纳朱瑾妻并引兵还',4,'全忠纳瑾之妻，引兵还',[('朱温','纳妻还军者'),('朱瑾妻（兖州被俘者）','被纳者')],when='897年二月兖州陷后；确日未载',note='保纳原义，不写正式结婚仪式，不建朱温与被俘女子的丈夫关系。')
e('zhang_greets_zhu_fengqiu','张夫人迎朱温于封丘，得知朱瑾妻事',4,'张夫人逆于封丘，全忠以得瑾妻告之。',[('张夫人','迎问者'),('朱温','告之者')],when='897年二月朱温还军时；确日未载',place='封丘')
e('zhang_meets_jin_wife_warns','张夫人与朱瑾妻互拜，泣言同姓相攻及失守之忧',4,'夫人请见之，瑾妻拜，夫人答拜，且泣曰：“兗、郓与司空同姓，约为兄弟，以小故恨望，起兵相攻，使吾姒辱于此。他日汴州失守，吾亦如吾姒之今日乎！”',[('张夫人','答拜泣言者'),('朱瑾妻（兖州被俘者）','拜见者')],when='897年二月封丘迎军后；确日未载',place='封丘',note='约兄弟与未来失守是张氏说辞，不建确定结义关系，也不把预测记为897汴州已陷。')
e('zhu_sends_jin_wife_nunnery','朱温送朱瑾妻入佛寺为尼',4,'全忠乃送瑾妻于佛寺为尼',[('朱温','送寺者'),('朱瑾妻（兖州被俘者）','被送为尼者')],when='897年二月张氏泣言后；确日未载',place='佛寺',note='未给寺名，不擅定寺址坐标。')
e('zhu_xuan_executed_bian_bridge','朱瑄被斩于汴桥',4,'斩硃宣于汴桥。',[('朱温','斩者'),('朱瑄','被斩者')],when='897年本段二月条叙述；确日待核',place='汴桥',note='硃宣为底本部件私用字形，复用朱瑄；补书有正月陷郓与寻斩，未强定公历日。')
claim('person',people['朱瑄'],'death_year','朱瑄在乾宁四年（897）郓州陷后被斩于汴桥。',4,quote='斩硃宣于汴桥。',note='主书排列在二月段，确日与补书不同叙述待核；人物复用不覆盖旧行。')
e('fourteen_prefectures_zhu_summary','兖郓失陷后十四州归朱温势力的综述',4,'于是郓、齐、曹、棣、兗、沂、密、徐、宿、陈、许、郑、滑、濮皆入于全忠。',[('朱温','势力归属者')],when='897年兖郓陷后主书综述；各州取得时间未逐列',place='郓、齐、曹、棣、兖、沂、密、徐、宿、陈、许、郑、滑、濮',note='这是汇总范围，不把十四州均建为二月同日新克城事件。')
e('wang_shifan_submits_keeps_zhiqing','王师范保淄青而服朱温',4,'惟王师范保淄青一道，亦服于全忠。',[('王师范','保道服者'),('朱温','受服者')],when='897年兖郓陷后综述；确日未载',place='淄青',note='保淄青仍为其所据，不作淄青已被朱温直接占城。')
e('li_cunxin_withdraws_wei','李存信闻兖郓皆陷，自魏州还军',4,'李存信在魏州，闻兗、郓皆陷，引兵还。',[('李存信','闻讯还军者')],when='897年二月兖郓陷后；确日未载',place='魏州')
e('huainan_strengthens_cavalry_summary','河东兖郓兵投淮南使军声大振',4,'淮南旧善水战，不知骑射，及得河东、兗、郓兵，军声大振。',when='897年本段投淮之后；确日未载',place='淮南',note='主书军队能力与声势评价，不据此造精确骑兵兵力或把所有淮南兵都定义不会骑射。')
e('li_keyong_requests_two_generals','李克用遣间道使向杨行密请求史俨李承嗣',4,'史俨、李承嗣皆河东骁将，李克用深惜之，遣使间道诣杨行密请之。',[('李克用','遣使请求者'),('杨行密','被请求者'),('史俨','所请求将'),('李承嗣','所请求将')],when='897年二将投淮后；确日未载',note='请将与已经返河东区分，不新建无名使者。')
e('yang_agrees_sends_goodwill','杨行密许归将并遣使向李克用修好',4,'行密许之，亦遣使诣克用修好。',[('杨行密','许并遣使者'),('李克用','受修好者')],when='897年河东请求之后；确日未载',note='许之未记二将实际到达河东，不建立永久联盟或君臣关系。')
e('wang_sends_huahong_zongyou_dongchuan','王建遣华洪王宗祐五万兵攻东川',5,'戊午，王建遣邛州刺史华洪、彭州刺史王宗祐将兵五万攻东川',[('王建','遣军者'),('华洪','领兵者'),('王宗祐','领兵者')],when='897年二月戊午',place='东川',note='华洪复用王宗涤旧主体；五万为书载兵数，不作现代核定。')
e('zongjin_vanguard_defeats_jihui','王宗谨任凤翔西面先锋，败李继徽等于玄武',5,'以戎州刺史王宗谨为凤翔西面行营先锋使，败凤翔李继徽等于玄武。',[('王建','授先锋者'),('王宗谨','任先锋胜者'),('李继徽','败者')],when='897年二月戊午条；确日未另载',place='玄武',note='任使与败军在同句，未推被杀或被俘；李继徽复用杨崇本，勿并湖州彦徽。')
claim('person',people['杨崇本'],'aliases','李继徽本姓杨名崇本，为李茂贞假子。',5,quote='继徽本姓杨，名崇本，茂贞之假子也。',note='沿用已有杨崇本稳定主体，收养发生年未载，不写897新收养。')
e('general_amnesty_february','朝廷赦天下',6,'己未，赦天下。',[('唐昭宗','赦令者')],when='897年二月己未',note='赦令范围未列，不补具体罪名豁免条款。')
e('emperor_worships_temporary_temple','昭宗飨行庙',7,'上飨行庙。',[('唐昭宗','祭飨者')],when='897年二月己未条；确日未另载',place='行庙',note='行庙不推固定长安太庙地点；飨不当普通宴会。')
e('zongkan_eight_thousand_yuzhou','王宗侃任开峡都指挥使，八千趋渝',8,'庚申，王建以决云都知兵马使王宗侃为应援开峡都指挥使，将兵八千趋渝州',[('王建','遣任者'),('王宗侃','领趋渝者')],when='897年二月庚申',place='渝州')
e('zongruan_seven_thousand_luzhou','王宗阮任开江防送进奉使，七千趋泸州',8,'决胜都知兵马使王宗阮为开江防送进奉使，将兵七千趋沪州。',[('王建','遣任者'),('王宗阮','领趋泸者')],when='897年二月庚申',place='泸州',note='沪州底本疑字按下文泸州对应，原摘录保沪；王宗阮复用文武坚。')
e('zongkan_takes_yu_mou_surrenders','王宗侃取渝州，牟崇厚降',8,'辛未，宗侃取渝州，降刺史牟崇厚',[('王宗侃','取州者'),('牟崇厚','降刺史')],when='897年二月辛未',place='渝州')
e('zongruan_takes_lu_kills_ma','王宗阮拔泸州，斩马敬儒，峡路通',8,'癸酉，宗阮拔泸州，斩刺史马敬儒，峡路始通。',[('王宗阮','拔州者'),('马敬儒','被斩刺史')],when='897年二月癸酉',place='泸州',note='峡路始通为本段概述，不自行画定运输线路。')
e('li_jizhao_relief_zongbo_captures','李继昭救梓留将剑门，王宗播击擒偏将',8,'凤翔将李继昭救梓州，留偏将守剑门，西川将王宗播击擒之。',[('李继昭','救梓留将者'),('王宗播','击擒者')],when='897年二月癸酉后条；确日未载',place='梓州、剑门',note='擒之承守剑门偏将，不写王宗播擒李继昭；偏将无名不建猜定人物。')
e('sun_wo_chancellorship_removed','孙偓罢相守本官',8,'乙亥，门下侍郎、同平章事孙亻屋罢守本官',[('孙偓','罢相者')],when='897年二月乙亥',note='孙亻屋复用孙偓，罢守本官不写被杀。')
e('zhu_pu_removed_secretary','朱朴罢相为秘书监',8,'中书侍郎、同平章事硃朴罢为秘书监。朴既秉政，所言皆不效，外议沸腾。',[('朱朴','罢相者')],when='897年二月乙亥',note='所言不效外议沸腾是主书记评，不补承诺的具体政策全部失败数据。')
e('ma_xu_favored_skills_background','马道殷以天文、许岩士以医得昭宗宠幸',8,'太子詹事马道殷以天文，将作监许岩士以医得幸于上',[('马道殷','以天文得幸者'),('许岩士','以医得幸者'),('唐昭宗','宠幸者')],when='897年本段罢相缘由追叙；得幸起年未载',year=None,note='官职技能及得幸作为追叙，不将开始得幸年直接定897。')
e('han_false_accusation_kills_ma_xu','韩建诬罪杀马道殷许岩士，又称孙朱与之交通',8,'韩建诬二人以罪而杀之，且言亻屋、朴与二人交通，故罢相。',[('韩建','诬杀者'),('马道殷','被杀者'),('许岩士','被杀者')],when='897年二月罢孙偓朱朴相的缘由；确日待核',note='交通为韩建指控，不建孙朱与二人真实阴谋或犯罪关系；旧唐书八月后寻杀异记另附。')
e('yang_commander_campaign_du_hong','杨行密受江南诸道都统诏讨杜洪',9,'诏以杨行密为江南诸道行营都统，以讨武昌节度使杜洪。',[('杨行密','受都统者'),('杜弘','被讨对象')],when='897年二月乙亥后条；确日未载',place='江南、武昌',note='杜洪沿用旧主体杜弘字形，诏讨不作当日已克武昌。')
e('zhang_ji_takes_shao_captures_jiang','张佶克邵州擒蒋勋',10,'张佶克邵州，擒蒋勋。',[('张佶','克州者'),('蒋勋','被擒者')],when='897年二月条；确日未载',place='邵州',note='被擒不写已杀。')
e('ge_taining_retainer','朱温表葛从周为泰宁留后',11,'三月，丙子，硃全忠表曹州刺史葛从周为泰宁留后',[('朱温','表任者'),('葛从周','被表者')],when='897年三月丙子',place='泰宁军')
e('zhu_youyu_tianping_retainer','朱温表朱友裕为天平留后',11,'硃友裕为天平留后',[('朱温','表任者'),('朱友裕','被表者')],when='897年三月丙子',place='天平军',note='承前朱温表，勿与先前主书庞师古留后混一任命。')
e('pang_wuning_retainer','朱温表庞师古为武宁留后',11,'庞师古为武宁留后。',[('朱温','表任者'),('庞师古','被表者')],when='897年三月丙子',place='武宁军',note='与杨表朱瑾领武宁不同阵营任命并存，不据军额同名合并人物。')
e('wang_gong_attacks_ke','王珙攻王珂，双方求援河东宣武',12,'保义节度使王珙攻护国节度使王珂，珂求援于李克用，珙求援于硃全忠。',[('王珙','攻求援者'),('王珂','守求援者'),('李克用','被求援者'),('朱温','被求援者')],when='897年三月条；确日未载',place='河中',note='请求援军不等同永久结盟；已有兄弟异议不据本段新建亲属关系。')
e('zhang_yang_defeat_hedong_yishi','张存敬杨师厚败河中兵于猗氏南',12,'宣武将张存敬、杨师厚败河中兵于猗氏南。',[('张存敬','胜将'),('杨师厚','胜将')],when='897年三月条；确日未载',place='猗氏南')
e('li_sizhao_yishi_zhangdian_relief','李嗣昭败陕兵于猗氏及张店，解河中围',12,'河东将李嗣昭败陕兵于猗氏，又败之于张店，遂解河中之围。',[('李嗣昭','援胜者')],when='897年三月条；确日未载',place='猗氏、张店、河中',note='两战不同地点保留，未据此定所有宣武将都被擒。')
claim('person',people['杨师厚'],'description','杨师厚为斤沟人。',12,quote='师厚，斤沟人',note='底本斤沟保原字，未换现代地名或坐标。')
person('李克柔',12,'李克用之弟、李嗣昭养父');claim('person',people['李嗣昭'],'description','李嗣昭是李克用弟李克柔的假子。',12,quote='嗣昭，克用弟克柔之假子也。',note='假子按收养，起年未载，不写本年新收养。')
e('ganyi_renamed_zhaowu','感义军更名昭武，治利州',12,'更名感义军曰昭武，治利州',when='897年三月条；确日未载',place='利州')
e('su_wenjian_zhaowu_governor','苏文建任昭武节度使',12,'以前静难节度使苏文建为节度使。',[('苏文建','受任者')],when='897年三月条；确日未载',place='昭武军、利州',note='前静难指旧职，节度使承昭武新军额。')
# Directed relationships reuse already published rows and stable keys.
relation_registry={}
for f in (ROOT/'content').rglob('content-batch.json'):
 if f.resolve()==(P/'content-batch.json').resolve():continue
 for r in json.loads(f.read_text())['person_relationships']:relation_registry[(r['person_a_key'],r['person_b_key'],r['relation_type'])]=r
for a,b,t,n,q,desc in [('朱瑾妻（兖州被俘者）','朱瑾','妻子',4,'从周入兗州，获瑾妻子。','兖州被俘女子是朱瑾之妻，姓名未详。'),('李茂贞','杨崇本','养父',5,'继徽本姓杨，名崇本，茂贞之假子也。','李茂贞是杨崇本的养父。'),('李克用','李克柔','兄长',12,'嗣昭，克用弟克柔之假子也。','李克用是李克柔的兄长。'),('李克柔','李嗣昭','养父',12,'嗣昭，克用弟克柔之假子也。','李克柔是李嗣昭的养父。')]:
 ka=person(a,n,t);kb=person(b,n,'关系另一端');old=relation_registry.get((ka,kb,t))
 if old:r=dict(old,status='draft');reused.add(r['key'])
 else:r=dict(key=f'relationship_{ka}_{kb}_{t}',person_a_key=ka,person_b_key=kb,relation_type=t,description=desc,status='draft')
 B['person_relationships'].append(r);claim('person_relationship',r['key'],'description',desc,n,quote=q,note='A是B的该关系；收养或婚姻起年未载，不按本年追填。')
supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
    record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0897_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('jiuwudaishi-001-897-yunzhou','event','event_zztj_261_0897_zhu_enters_yun_pang_retainer','description','《旧五代史》太祖纪记郓州平后己亥朱温入城，以朱友裕为郓州兵马留后。','己亥，帝入于鄆，以朱友裕為鄆州兵馬留後。',4,'主书先庞师古、三月再表朱友裕；太祖纪此处先朱友裕，并列任命差异，编校案语不建新事实。','conflicts')
extra('jiuwudaishi-001-897-yunzhou','event','event_zztj_261_0897_zhu_xuan_executed_bian_bridge','description','《旧五代史》郓州战事记朱瑄被擒后寻斩于汴桥下。','尋斬汴橋下。鄆州平。',4,'太祖纪正月段未给寻斩确日，保独立叙事位置，不静改主书本段二月排列或算日期。','adds')
extra('jiutangshu-020a-897-army-prince','event','event_zztj_261_0897_ge_enters_yan_captures_family','time_original','《旧唐书》亦记二月戊申葛从周攻陷兖州，朱瑾奔杨、康怀贞降。','戊申，汴將葛從周攻兗州，陷之，節度使朱瑾奔楊行密，其將康懷貞降從周',4,'本段开头二月丙午朔，戊申与主书对应；本句不记被俘家属名单，不据此补子名。','corroborates')
extra('jiutangshu-020a-897-army-prince','person',people['康怀贞'],'description','《旧唐书》记朱瑾将康怀贞在兖州陷时降葛从周。','其將康懷貞降從周',4,'同州同主同降事对应；两五代史康怀英字形另保，不新建重复将领。','corroborates')
extra('xinwudaishi-042-897-zhu-jin','person',people['康怀贞'],'description','《新五代史》朱瑾传在相应兖州降事称康怀英。','瑾將康懷英等以城降梁。',4,'主书康怀贞与补书康怀英暂按同事件对应挂异文，不覆盖稳定人物名称或正式别名。','adds')
extra('xinwudaishi-042-897-zhu-jin','person',people['尹处宾'],'description','《新五代史》记沂州刺史尹处宾拒纳朱瑾。','沂州刺史尹處賓不納。',4,'同地同职及拒入对应，繁简字保各自出处。','corroborates')
extra('xinwudaishi-042-897-zhu-jin','event','event_zztj_261_0897_yang_petitions_jin_wuning','description','《新五代史》补杨行密闻朱瑾来喜，赠玉带，表领武宁并以为行军副使。','楊行密聞瑾來，大喜，解其玉帶贈之，表瑾領武寧軍節度使，以為行軍副使。',4,'未给月日，独立补迎接和职任内容，不写朱瑾实际据有徐州，后清口战不倒填本段。','adds')
extra('xinwudaishi-013-zhang-wife','person',people['张氏（朱温妻）'],'description','《新五代史》记朱温妻张氏为单州砀山渠亭里富家子。','太祖元貞皇后張氏，單州碭山縣渠亭里富家子也。',4,'沿用现有人物，元贞皇后为后世传名不写897已有皇后身份，不添现代坐标。','adds')
extra('xinwudaishi-040-yang-chongben','person',people['杨崇本'],'aliases','《新五代史》记杨崇本少事李茂贞，收养后冒李姓名继徽。','楊崇本，幼事李茂貞，養以為子，冒姓李，名曰繼徽',5,'收养和改名起年未载，复用旧主体，不把后投梁复姓的日期拉到897。','corroborates')
extra('xinwudaishi-040-yang-chongben','person_relationship','relationship_person_李茂贞_person_杨崇本_养父','description','《新五代史》记李茂贞养杨崇本为子。','幼事李茂貞，養以為子',5,'方向为茂贞是崇本养父，保旧关系UUID，不新建重复养父边。','corroborates')
extra('jiutangshu-020a-897-ma-xu','event','event_zztj_261_0897_han_false_accusation_kills_ma_xu','time_original','《旧唐书》在八月杀诸王后记寻杀马道殷、许岩士并贬朱朴；主书在二月罢相缘由记诬杀。','尋殺太子詹事馬道殷、將作監許岩士，貶平章事朱樸，皆上所寵昵者。',8,'所选段首八月甲辰朔，寻为后续未具日；保月份和叙事次序异记，不强断两书同日、不重复造杀人事件。','conflicts')
extra('jiuwudaishi-052-li-sizhao','person',people['李嗣昭'],'description','《旧五代史》记李嗣昭字益光、小字进通，为李克柔假子。','李嗣昭，字益光，武皇母弟代州刺史克柔之假子也。小字進通，不知族姓所出。',12,'本传旧说不知族姓与夹注韩氏是不同层次，本批不直接把括注做正式姓氏改写，出生年未载。','adds')
extra('jiuwudaishi-052-li-sizhao','person',people['李克柔'],'description','《旧五代史》记李克柔为武皇母弟、代州刺史。','武皇母弟代州刺史克柔之假子也。',12,'补兄弟与职任说明，未具任代州年月，不写897刚授职。','adds')
extra('jiuwudaishi-052-li-sizhao','person_relationship','relationship_person_李克柔_person_李嗣昭_养父','description','《旧五代史》李嗣昭传亦记李嗣昭为李克柔假子。','李嗣昭，字益光，武皇母弟代州刺史克柔之假子也。',12,'假子按收养，起年未载；该传乾宁初猗氏和四年胡壁援战不强并主书两战。','corroborates')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(4,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='九段连续校核；兖郓陷、投淮、东川两路、诬杀罢相、三月留后和河中援战分录。配偶匿名及养父方向明确，复用人关系；孙朱罢相与马许被杀月份异记独立补证。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=897,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(4,13)],next_paragraph=Q[13]['id'],coverage='本年50段中的第4—12段连续整理，本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
