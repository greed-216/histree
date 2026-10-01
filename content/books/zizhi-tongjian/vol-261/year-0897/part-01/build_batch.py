"""Curate consecutive Tongjian volume 261, year 897 paragraphs 1–3."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 51))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0897-p001-p003', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-897-opening'
fixed_commit='06969d7'
source_specs=[(source,'资治通鉴·卷261·乾宁四年开头','司马光等'),('xintangshu-224b-897-han-jian','新唐书·卷224下·韩建削卫兵','欧阳修、宋祁等'),('jiutangshu-020a-897-army-prince','旧唐书·卷20上·诸王罢兵与太子','刘昫等'),('jiuwudaishi-001-897-yunzhou','旧五代史·卷1·郓州战事','薛居正等'),('jiuwudaishi-013-zhu-xuan','旧五代史·卷13·朱瑄传','薛居正等')]
manifest=[]
for sk,title,author in source_specs:
    d=P/'sources/library'/sk; record=json.loads((d/'paragraph.json').read_text()); audit=json.loads((d/'manifest.json').read_text()); filename='library/'+sk+'/source.txt'
    url='https://github.com/greed-216/histree/blob/'+fixed_commit+'/'+str((P/'sources'/filename).relative_to(ROOT))
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='选定TXT逐字导出；EPUB电子本，纸本及异文待核。',url=url,note=record['citation']))
    manifest.append(dict(key=sk,file=filename,sha256=audit['sha256'],url=url,paragraph_id=record['id'],upstream=record['locator']['source_file'],upstream_locator=record['locator'],transformation='按导出定位逐字截取TXT，保原换行空格。'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for n in range(1,4):assert Q[n]['text'] in (P/'sources/library'/source/'source.txt').read_text()
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'王熔':'王镕','国弘信':'罗弘信','硃友裕':'朱友裕','赫连鐸':'赫连铎','硃崇节':'朱崇节','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, set()
alias.update({'硃朴':'朱朴','韩健':'韩建','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_261_0897_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷261·乾宁四年（897）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

def e(code,title,n,q,actors=(),when=None,place=None,note=None,description=None):
    return event(code,title,n,when or '897年本段条；确日未载',place,description or title+'。',actors,quote=q,note=note)
e('han_accuses_eight_princes','韩建使张行思告八王谋杀劫驾',1,'韩建奏：“防城将张行思等告睦、济、韶、通、彭、韩、仪、陈八王谋杀臣，劫车驾幸河中。”建恶诸王典兵，故使行思等告之。',[('韩建','指使奏告者'),('张行思','被使告变者')],when='897年正月甲申',note='告变由韩建指使，谋杀劫驾为指控，不建八王确实谋反或已迁河中事件。八王原名未载，不按封号猜实名。')
e('emperor_summons_han_refuses','昭宗召韩建谕之，韩建称疾不入',1,'上大惊，召建谕之，建称疾不入。',[('唐昭宗','召谕者'),('韩建','称疾拒入者')],when='897年正月甲申告变后',note='称疾是借口式原记，不补真实疾病诊断。')
e('princes_visit_han_refuses_meeting','八王奉令诣韩建自陈，韩建拒见',1,'令诸王诣建自陈，建表称：“诸王忽诣臣理所，不测事端。臣详酌事体，不应与诸王相见。”',[('唐昭宗','令自陈者'),('韩建','表拒见者')],when='897年正月甲申告变后',note='诸王来访不写已与韩建会面；不补未载个人行迹。')
e('han_requests_princes_disarm','韩建请诸王归十六宅、不典兵预政',1,'又称：“诸王当自避嫌疑，不可轻为举措。陛下若以友爱含容，请依旧制，令归十六宅，妙选师傅，教以诗书，不令典兵预政。”且曰：“乞散彼乌合之兵，用光麟趾之化。”',[('韩建','请罢兵权者')],when='897年正月甲申奏告后',note='乌合为韩奏评价，不认作兵员客观素质判断。')
e('han_surrounds_palace','韩建精兵围行宫并连上奏疏',1,'建虑上不从，仍引麾下精兵围行宫，表疏连上。',[('韩建','围宫胁奏者')],when='897年正月甲申',place='行宫',note='虑帝不从是主书归因，未补围宫兵数。')
e('edict_princes_soldiers_dispersed','诏解诸王军士归田，王归十六宅，甲兵归韩建',1,'上不得已，是夕，诏诸王所领军士并纵归田里，诸王勒归十六宅，其甲兵并委韩建收掌。',[('唐昭宗','受迫下诏者'),('韩建','收掌甲兵者')],when='897年正月甲申夕',place='十六宅',note='军士归田和甲兵收掌分清；未记各王封爵被除。')
e('han_requests_four_armies_dissolution','韩建奏请罢殿后四军',1,'建又奏：“陛下选贤任能，足清祸乱，何必别置殿后四军。纵有厚薄之恩，乖无偏无党之道。且所聚皆坊市无赖奸猾之徒，平居犹思祸变，临难必不为用，而使之张弓挟刃，密迩皇舆，臣窃寒心，乞皆罢。”',[('韩建','请罢军者')],when='897年正月甲申条；诸王解兵后',note='无赖奸猾和临难无用是韩奏说法，非本批确认的全军特征。')
e('four_armies_twenty_thousand_disband','殿后四军二万余人悉散',1,'遣诏亦从之。于是殿后四军二万馀人悉散，天子之亲军尽矣。',[('唐昭宗','从奏者')],when='897年正月甲申条；韩奏后',note='二万余保记数，不造现代精确人数；新唐书三十控鹤排马官附独立补证，不静改主书尽矣。')
e('li_yun_executed_dayun','韩建奏斩捧日都头李筠于大云桥',1,'捧日都头李筠，石门扈从功第一，建复奏斩于大云桥。',[('韩建','奏斩者'),('李筠','被斩者')],when='897年正月甲申条；罢亲军后',place='大云桥',note='主书捧日官称与补书定州行营将分记；石门功第一为主书记述，不推其他功臣名单。')
claim('person',people['李筠'],'death_year','李筠在乾宁四年（897）正月条被奏斩于大云桥。',1,quote='捧日都头李筠，石门扈从功第一，建复奏斩于大云桥。',note='年月按主书本段；旧唐书二月条异记保留，不覆盖旧人物实体字段。')
e('han_requests_princes_recalled','韩建请召还四方奉命诸王，诏从',1,'今诸王衔命四方者，乞皆召还。',[('韩建','请召者'),('唐昭宗','从奏者')],when='897年正月甲申条；确日未另载',note='原段诏悉从之对应；引玄宗代宗朱玫为奏辞比喻，不把前代人建本次参与边。')
e('han_requests_ban_fangshi','韩建奏禁方士入宫，诏从',1,'又奏：“诸方士出入禁庭，眩惑圣听，宜皆禁止，无得入宫。”诏悉从之。',[('韩建','请禁者'),('唐昭宗','从奏者')],when='897年正月甲申条；确日未另载',note='眩惑圣听为韩奏评价；禁令不等于已处死或逐出所有方士。')
e('han_petitions_dewang_heir','韩建幽诸王后奏请立德王为太子',1,'建既幽诸王于别第，知上意不悦，乃奏请立德王为太子，欲以解之。',[('韩建','幽王奏立者'),('李祐','拟立者')],when='897年正月甲申后、丁亥前',note='别第幽禁及欲解帝不悦按主书归述，不静合十六宅为同一建筑。')
e('li_you_crown_prince_renamed_yu','德王李祐立皇太子、更名裕',1,'丁亥，诏立德王祐为皇太子，仍更名裕。',[('李祐','受立改名者'),('唐昭宗','诏立者')],when='897年正月丁亥',note='复用既有德王祐稳定主体，改名事实附引用，旧实体不重建；旧唐书二月己未记册命，书证并列。')
claim('person',people['李祐'],'aliases','德王祐在本段立为皇太子，更名裕。',1,quote='丁亥，诏立德王祐为皇太子，仍更名裕。')
e('pang_ge_assault_yun_moat','庞师古葛从周攻郓，朱瑄引水深壕自固',2,'庞师古、葛从周并兵攻郓州，硃瑄兵少食尽，不复出战，但引水为深壕以自固。',[('庞师古','攻城者'),('葛从周','合攻者'),('朱瑄','守深壕者')],when='897年正月；辛卯前',place='郓州')
e('pang_camps_build_bridge_drains','庞师古营水西南造浮梁并潜决濠水',2,'辛卯，师古等营于水西南，命为俘梁。登已，潜决濠水。',[('庞师古','营造者')],when='897年正月辛卯；潜决濠水确日待考',place='郓州水西南',note='底本俘梁、登已疑字保留，俘梁按下文浮梁释读；登已不当确定干支，不静改为既而等词。')
e('pang_night_cross_bridge','浮梁成，庞师古夜率中军先渡',2,'丙申，浮梁成，师古夜以中军先济。',[('庞师古','先济者')],when='897年正月丙申夜',place='郓州壕水',note='主书丙申与旧五代史乙未夜并列，不擅算公历日。')
e('zhu_xuan_flees_zhongdu','朱瑄弃郓州奔中都',2,'瑄闻之，弃城奔中都',[('朱瑄','弃城者')],when='897年正月浮梁渡军后',place='郓州、中都')
e('ge_pursues_zhu_captured_family','葛从周追朱瑄，野人执朱瑄及妻子献军',2,'葛从周逐之，野人执瑄及妻子以献。',[('葛从周','追者'),('朱瑄','被执者')],when='897年正月弃城后',place='中都',note='野人未具实名，不建推定人物；妻子按家属表述，妻名和后续斩首留补书独立引用，未提前占下段主线。')
e('sun_wo_removed_campaign_posts','罢孙偓凤翔行营节度等使',3,'己亥，罢孙亻屋凤翔四面行营节度等使',[('孙偓','罢军职者')],when='897年正月己亥',note='孙亻屋底本部件字形，复用孙偓，不推被罢全部朝职。')
e('li_sijian_ningsai_governor','李思谏任宁塞节度使',3,'以副都统李思谏为宁塞节度使。',[('李思谏','受节度使者')],when='897年正月己亥',place='宁塞军',note='保持新军额，未擅改回静难或定难。')
e('du_leng_relief_wuzhou','钱镠遣杜稜救婺州',3,'钱镠使行军司马杜稜救婺州。',[('钱镠','遣援者'),('杜稜','救援者')],when='897年正月己亥条；确日未另载',place='婺州')
e('an_renyi_muzhou_fails_returns','安仁义移攻睦州不克而还',3,'安仁义移兵攻睦州，不克而还。',[('安仁义','移攻还军者')],when='897年正月救婺后；确日未载',place='睦州',note='不克不是已占；未添未载伤亡。')
supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
    record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0897_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('xintangshu-224b-897-han-jian','event','event_zztj_261_0897_four_armies_twenty_thousand_disband','description','《新唐书》记散卫兵后留三十控鹤排马官隶飞龙坊。','詔留三十人為控鶴排馬官，隸飛龍坊。',1,'卷224下追叙未具本句月日，保三十人职属，未将其称完整保留亲军或静改主书尽矣。','adds')
extra('xintangshu-224b-897-han-jian','person',people['李筠'],'description','《新唐书》韩建传称李筠为定州行营将，韩以兵围宫请诛。','建初懼帝不聽，以兵環宮，請誅定州行營將李筠。帝懼，斬筠，兵乃解。',1,'职称与主书捧日都头分录，不因不同职称拆为异人，纸本待核。','adds')
extra('jiutangshu-020a-897-army-prince','event','event_zztj_261_0897_han_accuses_eight_princes','time_original','《旧唐书》二月甲寅记华州防城将花重武告八王，主书为正月甲申张行思等。','甲寅，華州防城將花重武告睦王已下八王欲謀殺韓建，移車駕幸河中。',1,'卷20上本段首二月丙午朔；月份、干支与告者均异记。不把花重武合并张行思或把八王指控当事实。','conflicts')
extra('jiutangshu-020a-897-army-prince','event','event_zztj_261_0897_li_yun_executed_dayun','time_original','《旧唐书》在二月甲寅条记杀捧日都头李筠于大云桥下，主书置正月条。','是日，囚八王於別第，殿后侍衛四軍二萬餘人皆放散，殺捧日都頭李筠於大雲橋下',1,'该书是日承二月甲寅，不覆盖主书；桥与桥下作为原地名范围保留。','conflicts')
extra('jiutangshu-020a-897-army-prince','event','event_zztj_261_0897_li_you_crown_prince_renamed_yu','time_original','《旧唐书》二月条己未制德王裕宜册皇太子，主书正月丁亥诏立并改名。','己未，制德王裕宜冊為皇太子。',1,'册命与诏立可能有阶段差异，未强认不同月份必为同一仪式，也未另建重复人物。','conflicts')
extra('jiuwudaishi-001-897-yunzhou','event','event_zztj_261_0897_pang_night_cross_bridge','time_original','《旧五代史》太祖纪作乙未夜庞师古率中军先济，主书为丙申夜。','乙未夜，師古以中軍先濟，聲振于鄆',2,'卷1四年正月上下文；同事件日期异记保留，电子正文夹编校案语，未将案语当原始事件。','conflicts')
extra('jiuwudaishi-001-897-yunzhou','event','event_zztj_261_0897_ge_pursues_zhu_captured_family','description','《旧五代史》记葛从周追至中都北，擒朱瑄并妻男。','葛從周逐之至中都北，擒瑄并其妻男以獻',2,'追者及被俘相应，中都北为补书更细地点，不替主书改捕者野人；捕者差别保留。','adds')
extra('jiuwudaishi-013-zhu-xuan','person',people['朱瑄'],'description','《旧五代史》朱瑄传记其宋州下邑人。','朱瑄，宋州下邑人也。',2,'籍贯补同一主体，不把传中早年经历定897，不添现代坐标或生年。','adds')
extra('jiuwudaishi-013-zhu-xuan','event','event_zztj_261_0897_ge_pursues_zhu_captured_family','description','《旧五代史》朱瑄传记其匿于中都北民家，被擒时妻为荣氏。','遁至中都北，匿於民家，為其所箠，並妻榮氏擒之來獻',2,'同次被擒事件补妻名和民家地点；被斩后事待下一连续段主线处理，不据本段妻子二字补全子女名单。','adds')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(1,4):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='正月三段顺序校核；谋反为韩指使之告，兵散与三十留官、两唐书月份姓名及旧五代渡日异记独立附出处。追叙不定当年，祐更名裕复用主体。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=897,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,4)],next_paragraph=Q[4]['id'],coverage='本年50段中的第1—3段连续整理，本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
