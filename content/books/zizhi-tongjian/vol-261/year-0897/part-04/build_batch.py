"""Curate consecutive Tongjian volume 261, year 897 paragraphs 25–36."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 51))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0897-p025-p036', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-897-autumn'
fixed_commit='51ef137'
source_specs=[(source,'资治通鉴·卷261·乾宁四年第25—36段','司马光等'),('jiuwudaishi-026-897-mugua','旧五代史·卷26·木瓜涧战','薛居正等'),('jiuwudaishi-135-897-liu-rengong','旧五代史·卷135·刘仁恭拒兵与木瓜涧','薛居正等'),('xintangshu-082-897-princes','新唐书·卷82·十一王石堤谷之难','欧阳修、宋祁等'),('xintangshu-010-897-huzhou','新唐书·卷10·湖州归钱镠','欧阳修、宋祁等')]
reused_source_keys=set()
manifest=[]
for sk,title,author in source_specs:
 d=P/'sources/library'/sk;r=json.loads((d/'paragraph.json').read_text());filename='library/'+sk+'/source.txt';url='https://github.com/greed-216/histree/blob/'+fixed_commit+'/'+str((d/'source.txt').relative_to(ROOT))
 B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='选定TXT逐字导出；电子本，纸本及异文待核。',url=url,note=r['citation']))
 manifest.append(dict(key=sk,file=filename,sha256=hashlib.sha256((d/'source.txt').read_bytes()).hexdigest(),url=url,paragraph_id=r['id'],upstream_locator=r['locator'],transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for n in range(25,37):assert Q[n]['text'] in (P/'sources/library'/source/'source.txt').read_text()
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
    B['claims'].append(dict(key=f'claim_zztj_261_0897_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷261·乾宁四年（897）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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
e('cheng_rui_added_shizhong','成汭加兼侍中',25,'秋，七月，加荆南节度使成汭兼侍中。',[('成汭','受加官者')],when='897年七月；确日未载',place='荆南')
e('han_letter_mao_lifts_prince_siege','韩建书李茂贞，解奉天围，覃王归华州',26,'韩建移书李茂贞，茂贞解奉天之围，覃王归华州。',[('韩建','移书者'),('李茂贞','解围者'),('覃王嗣周','归华州者')],when='897年七月；确日未载',place='奉天、华州',note='解围与王归明记，不补王已接管凤翔。')
e('yang_chongben_jingnan_appointed','李继徽从天雄任静难节度',27,'以天雄节度使李继徽为静难节度使。',[('李继徽','受静难者')],when='897年七月；确日未载',place='静难军',note='复用杨崇本，与湖州彦徽分清。')
e('qian_returns_hang_sends_gu_suzhou','钱镠还杭州遣顾全武取苏州',28,'庚戌，钱镠还杭州，遣顾全武取苏州。',[('钱镠','还镇遣将者'),('顾全武','受遣者')],when='897年七月庚戌',place='杭州、苏州',note='取是遣军任务，不说当日苏州全境已陷。')
e('gu_takes_songjiang','顾全武军拔松江',28,'乙未，拔松江。',[('顾全武','拔地者')],when='897年七月乙未',place='松江')
e('gu_takes_wuxi','顾全武军拔无锡',28,'戊戌，拔无锡。',[('顾全武','拔地者')],when='897年七月戊戌',place='无锡')
e('gu_takes_changshu_huating','顾全武军拔常熟华亭',28,'辛丑，拔常熟、华亭。',[('顾全武','拔地者')],when='897年七月辛丑',place='常熟、华亭')
person('刘仁恭',29,'幽州节度使，受河东征兵');person('李克用',29,'先取幽州留戍典政、征兵者')
claim('person',people['刘仁恭'],'description','主书追叙刘仁恭受表幽州节度、河东留兵及腹心将十人典机要，军用外租赋输晋阳。',29,quote='初，李克用取幽州，表刘仁恭为节度使，留戍兵及腹心将十人典其机要，租赋供军之外，悉输晋阳。',note='既往任命沿用前面实体，本段增述制度，不再新建同次授节事件或把背景置897。')
e('li_keyong_requests_you_troops_and_letters','李克用征刘仁恭兵，并致王镕王郜书共定关中',29,'及上幸华州，克用征兵于仁恭，又遣成德节度使王镕、义武节度使王郜书，欲与之共定关中，奉天子还长安。',[('李克用','征兵致书者'),('刘仁恭','受征兵者'),('王镕','受书者'),('王郜','受书者')],when='车驾幸华州后至897亲征以前追叙；确起年未载',year=None,note='共同平关中迎还为目的，不当已实现；追叙跨年不全定897。')
e('liu_refuses_troops_khitan_pretext','刘仁恭以契丹入寇辞，催兵数月不出',29,'仁恭辞以契丹入寇，须兵扞御，请俟虏退，然后承命。克用屡趣之，使者相继，数月，兵不出。',[('刘仁恭','辞兵者'),('李克用','催兵者')],when='前述征兵至数月不出；确起年未载',year=None,note='契丹入寇为仁恭理由，不据此建独立已核契丹入侵事件。')
e('liu_insults_detains_envoy_garrison_escape','刘仁恭辱李书囚使，欲杀戍将而戍将逃免',29,'克用移书责之，仁恭抵书于地，慢骂，囚其使者，欲杀河东戍将，戍将遁逃获免。',[('李克用','责书者'),('刘仁恭','辱书囚使欲杀者')],when='897年八月李亲征前；确日未载',note='欲杀不等于戍将已死；无名使者戍将不猜实名。')
e('li_keyong_august_attacks_liu','李克用八月亲征刘仁恭',29,'克用大怒，八月，自将击仁恭。',[('李克用','亲征者'),('刘仁恭','被征对象')],when='897年八月；确日未载',place='幽州')
e('emperor_considers_fengtian_stopped','昭宗欲赴奉天亲讨茂贞，宰相谏止',30,'上欲幸奉天亲讨李茂贞，令宰相议之。宰相切谏，乃止。',[('唐昭宗','欲亲讨止者'),('李茂贞','拟讨对象')],when='897年八月条；确日未载',place='奉天',note='宰相本句未具姓名，不补某相参与；未实际赴奉天。')
e('jiepi_returns_han_accuses_princes','李戒丕还晋阳，韩建奏指延覃阴计',31,'延王戒丕还自晋阳，韩建奏：“自陛下即位以来，与近辅交恶，皆因诸王典兵，凶徒乐祸，致銮舆不安。比者臣奏罢兵权，实虑不测之变。今闻延王、覃王尚苞阴计，愿陛下圣断不疑，制于未乱，则社稷之福。”',[('延王戒丕','返使者'),('韩建','奏指者')],when='897年八月条；确日未载',note='阴计是韩指控，不建确实谋反；新唐书另有丹王同行背景，不猜丹王完整姓名。')
e('emperor_no_reply_han_liu_forge_siege','帝数日不报，韩建刘季述矫制围十六宅',31,'上曰：“何至于是！”数日不报。建乃与知枢密刘季述矫制发兵围十六宅。',[('唐昭宗','未批指控者'),('韩建','矫制围宅者'),('刘季述','同矫制者')],when='897年八月韩奏后数日',place='十六宅',note='矫制非真实皇帝批准诏，不建真实诏杀或刘季述受帝命关系。')
e('eleven_princes_killed_shidigu','韩建拥十一王至石堤谷尽杀，奏称谋反',31,'诸王被发，或缘垣，或登屋，或升木，呼曰：“宅家救儿！”建拥通、沂、睦、济、韶、彭、韩、陈、覃、延、丹十一王至石堤谷，尽杀之，以谋反闻。',[('韩建','拥杀者'),('李滋','被杀通王'),('覃王嗣周','被杀覃王'),('延王戒丕','被杀延王')],when='897年八月围宅后；确日未载',place='石堤谷',note='十一王按封号照录；三具名主体按已有封号出处复用，不猜其余实名或视所有人皆昭宗亲子。谋反为事后上奏指控。')
for name in ['李滋','李嗣周','李戒丕']:claim('person',people[name],'death_year','本段列该王在乾宁四年（897）石堤谷之难被杀。',31,quote='建拥通、沂、睦、济、韶、彭、韩、陈、覃、延、丹十一王至石堤谷，尽杀之，以谋反闻。',note='封号按既有同人记录对应，不补确日及未载生年，旧人物行不覆盖。')
e('sun_wo_demoted_nanzhou','孙偓贬南州司马',32,'贬礼部尚书孙亻屋为南州司马。',[('孙偓','被贬者')],when='897年八月条；确日未载',place='南州',note='部件字复用孙偓，未写已抵任。')
e('zhu_pu_demoted_kui_chen','朱朴先夔州司马再郴州司户',32,'秘书监硃朴先贬夔州司马，再贬郴州司户。',[('朱朴','连贬者')],when='897年八月条所记连续贬职；各次确日未载',place='夔州、郴州',note='保先再顺序，不把两任合为同地同时。')
e('he_ying_demoted_huzhou','何迎因朱朴相时骤迁后贬湖州司马',32,'朴之为相，何迎骤迁至右谏议大夫，至是亦贬湖州司马。',[('何迎','被贬者')],when='897年八月至是条；前迁为追叙',place='湖州',note='前迁跟朱朴任相起，未把首次迁官定897。')
e('zhou_bei_flees_zhong_chuan','钟传欲讨周琲，周率众奔广陵',33,'钟传欲讨吉州刺史襄阳周琲，琲帅其众奔广陵。',[('钟传','欲讨者'),('周琲','领众奔者')],when='897年八月条；确日未载',place='吉州、广陵',note='欲讨不作已交战，襄阳为周籍贯，不当逃往襄阳。')
claim('person',people['周琲'],'description','周琲为襄阳人，本段为吉州刺史。',33,quote='吉州刺史襄阳周琲')
e('wang_besieges_zi_september','王建顾彦晖五十余战后九月围梓',34,'王建与顾彦晖五十馀战，九月，癸酉朔，围梓州。',[('王建','围攻者'),('顾彦晖','守方')],when='897年九月癸酉朔；五十余战为此前总述',place='梓州',note='不把五十余战全部发生在朔日或逐造五十场缺细节事件。')
e('zhou_dequan_advises_recruit_outlaws','周德权劝招东川贼帅授官威服',34,'蜀州刺史周德权言于建曰：“公与彦晖争东川三年，士卒疲于矢石，百姓困于输輓。东川群盗多据州县，彦晖懦而无谋，欲为偷安之计，皆啗以厚利，恃其救援，故坚守不下。今若遣人谕贼帅以祸福，来者赏之以官，不服者威之以兵，则彼之所恃，反为我用矣。”',[('周德权','建策者'),('王建','听策者')],when='897年九月围梓条；确日未载',place='东川',note='顾懦和三年负担为周陈词，不作独立人品结论，未推出确切起战日期或招降者全名。')
e('wang_accepts_policy_gu_isolated','王建从周德权策，顾彦晖更孤',34,'建从之，彦晖势益孤。',[('王建','采纳者'),('顾彦晖','势孤者')],when='897年九月周建策后；确日未载',note='采纳不等于所有贼帅均已归降，孤为主书记述。')
claim('person',people['周德权'],'description','周德权为许州人。',34,quote='德权，许州人也。')
e('li_keyong_arrives_ansai_attacks','李克用至安塞军并进攻',35,'丁丑，李克用至安塞军，辛巳，攻之。',[('李克用','进攻者')],when='897年九月丁丑到、辛巳攻',place='安塞军')
e('shan_cavalry_li_drunk_orders_attack','单可及骑军至，李克用醉中命击',35,'幽州将单可及引骑兵至，克用方饮酒，前锋曰：“贼至矣。”克用醉，曰：“仁恭何在？”对曰：“但见可及辈。”克用瞋目曰：“可及辈何足为敌！”亟命击之。',[('单可及','引骑至者'),('李克用','醉中命战者')],when='897年九月辛巳',place='安塞军',note='醉按主书记，不推酒量或诊断；前锋无名不猜实名。')
e('yang_shikan_ambush_mugua','杨师侃伏木瓜涧，河东大败失亡过半',35,'是日大雾，不辨人物，幽州将杨师侃伏兵于木瓜涧，河东兵大败，失亡太半。',[('杨师侃','伏兵者'),('李克用','败军主帅')],when='897年九月辛巳',place='木瓜涧',note='太半保比例词，不算精确阵亡数；失亡不全当死亡。杨师侃不并王宗侃或杨师厚。')
e('storm_youzhou_releases_pursuit','风雨震电，幽州军解去',35,'会大风雨震电，幽州兵解去。',when='897年九月辛巳战后',place='木瓜涧',note='解去不补河东反败为胜。')
e('li_sober_blames_cunxin','李克用醒知败，责李存信等未力谏',35,'克用醒而后知败，责大将李存信等曰：“吾以醉废事，汝曹何不力争！”',[('李克用','责将者'),('李存信','受责者')],when='897年九月木瓜败后；确日未另载',note='责词不据此定李存信叛变或已受刑。')
e('yanhui_wants_yang_people_refuse_flees','湖州李彦徽欲附杨，众不从而奔广陵',36,'湖州刺史李彦徽欲以州附于杨行密，其众不从。彦徽奔广陵',[('李彦徽','欲附逃者')],when='897年九月条；确日未载',place='湖州、广陵',note='复用李师悦子湖州彦徽，与新唐书继徽异名待考；未实现附杨，不建湖州归淮南事实。')
e('shen_you_huzhou_submits_qian','沈攸以湖州归钱镠',36,'都指挥使沈攸以州归钱镠。',[('沈攸','归州者'),('钱镠','受归者')],when='897年九月彦徽出奔后；确日未载',place='湖州',note='以州归是政治归属行为，主书未记此处攻城细节。')
supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
    record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0897_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('jiuwudaishi-026-897-mugua','event','event_zztj_261_0897_li_keyong_august_attacks_liu','time_original','《旧五代史》记七月征兵幽州、刘囚使，八月大举伐刘。','七月，武皇復征兵於幽州，劉仁恭辭旨不遜，武皇以書讓之；仁恭捧書謾罵，抵之於地，仍囚武皇之行人。八月，大舉以伐仁恭。',29,'卷26四年上下文，八月亲征对应；七月复征不据此把主书从幸华州追叙全部只定该月。','corroborates')
extra('jiuwudaishi-135-897-liu-rengong','person',people['刘仁恭'],'description','《旧五代史》记刘仁恭受幽州节度后，河东留腹心燕留德等十余人分典军政。','即以仁恭為幽州節度使，留腹心燕留德等十餘人分典軍政',29,'与主书追叙留兵背景并列；十余人与十人原数词各保，不改旧任命年或另建相同授节事件。','adds')
extra('xintangshu-082-897-princes','event','event_zztj_261_0897_emperor_no_reply_han_liu_forge_siege','description','《新唐书》记帝未允诛王，三日后韩建刘季述矫诏攻十六宅。','後三日，與劉季述矯詔以兵攻十六宅。',31,'与主书数日不报、矫制对应，三日作该书细节，不静改主书数日为确定三日。','adds')
extra('xintangshu-082-897-princes','event','event_zztj_261_0897_eleven_princes_killed_shidigu','description','《新唐书》记韩建将十一王并其属至石堤谷杀，后以谋反奏。','建乃將十一王並其屬至石堤谷殺之，徐以謀反聞，天下冤之。',31,'十一王及眷属范围保补书；天下冤之为该书评价，不据此列全体人的心理，也不坐实谋反。','corroborates')
extra('xintangshu-082-897-princes','event','event_zztj_261_0897_eleven_princes_killed_shidigu','description','《新唐书》注明济韶彭韩沂陈延覃丹九王系胄失载。','濟、韶、彭、韓、沂、陳、延、覃、丹九王，史逸其系胄雲。',31,'不凭该句话否认主书已具延覃部分名号，但不给剩余封号猜父母实名，尤不认所有为昭宗亲子。','adds')
extra('jiuwudaishi-026-897-mugua','event','event_zztj_261_0897_yang_shikan_ambush_mugua','description','《旧五代史》记醉中与单可及兵战，步兵退而大败于木瓜涧。','時步兵望賊而退，為燕軍所乘，大敗於木瓜澗。',35,'同战役记步兵退，主书杨师侃伏兵另保；不据补书未名杨否认或改杨身份，传中先燕披靡不写最后河东获胜。','adds')
extra('jiuwudaishi-135-897-liu-rengong','event','event_zztj_261_0897_li_keyong_arrives_ansai_attacks','time_original','《旧五代史》刘仁恭传记九月五日次安塞、九日渡木瓜涧。','九月五日，次安塞軍。九日，渡木瓜澗，大為燕軍所敗，死傷大半。',35,'主书本段前癸酉朔，丁丑与辛巳在干支顺序为五日九日；仅比较本月序数，不换算公历，不把该传死伤大半当主书失亡精确死亡人数。','corroborates')
extra('xintangshu-010-897-huzhou','person',people['李彦徽（湖州）'],'description','《新唐书》九月湖州条称忠国军节度李继徽奔淮南，主书湖州刺史李彦徽奔广陵。','九月，錢鏐陷湖州，忠國軍節度使李繼徽奔于淮南。',36,'复用前面父亲李师悦、同地接职的湖州主体保异名官称，不把正式别名强写继徽、不并邠宁杨崇本。','conflicts')
extra('xintangshu-010-897-huzhou','event','event_zztj_261_0897_shen_you_huzhou_submits_qian','description','《新唐书》记九月钱镠陷湖州，主书记沈攸以州归钱镠。','九月，錢鏐陷湖州',36,'同归属变化附不同叙事，攻陷与归州可能不同阶段；未核细节前不造第二场确定攻城或覆盖沈攸行为。','adds')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(25,37):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='十二段连续校核；授静难与湖州异名分清，八月亲征前追叙不全定本年。十一王指控与矫诏杀分录，不猜封号系胄；木瓜战干支和补书月日序数比较，湖州归属异记保独立引用。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=897,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(25,37)],next_paragraph=Q[37]['id'],coverage='本年50段中的第25—36段连续整理，本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
