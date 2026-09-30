"""Curate consecutive Tongjian volume 259, year 893 paragraphs 22–29."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 39))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0893-p022-p029', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-893'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259景福二年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/259.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/259.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'王熔':'王镕','国弘信':'罗弘信','硃友裕':'朱友裕','赫连鐸':'赫连铎','硃崇节':'朱崇节','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, {source}
alias.update({'嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0893_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·景福二年（893）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259景福二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=893,note=None,quote=None):
    key='event_zztj_259_0893_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0893_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def relation(a,b,t,n,description,quote=None):
    ka,kb=people[a],people[b]
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==ka and r['person_b_key']==kb and r['relation_type']==t]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);key=row['key'];reused.add(key)
    else:
        key=f'relationship_{ka}_{kb}_{t}';row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key

event('li_maozhuang_chancellor','李茂庄加同平章事',22,'893年七月条；具体日未载','天雄',
      '天雄节度使李茂庄加同平章事。',[('李茂庄','受加官者')],note='天雄为本段职任称，不推此前秦州天雄与魏博天雄为同一镇；外镇加官不等入京任相。')
event('qian_builds_hangzhou_wall','钱镠发民夫军士筑杭州罗城',23,'893年七月条；具体起讫未载','杭州',
      '钱镠征发民夫二十万及十三都军士修筑杭州外城，书载周长七十里。',[('钱镠','征发营建者')],note='二十万、十三都、七十里均书载；未给军士人数，不将十三都转为十三万人；不换算现代周长或坐标。')
event('zhang_xiong_dies_feng_succeeds','张雄卒，冯弘铎接升州刺史',24,'893年七月条；具体日未载','升州',
      '升州刺史张雄去世，冯弘铎继任刺史。',[('张雄','去世刺史'),('冯弘铎','以冯弘鐸字形继任者')],note='代之不推受诏日期或死因。')
event('li_maozhen_insolent_memorial','李茂贞上表及书杜让能，言辞激怒昭宗',25,'893年七月至八月出兵谋议前；具体日未载','京师、凤翔',
      '李茂贞上表、写信给杜让能，言语不逊。昭宗想讨他，李又上表讥朝廷不能保护元舅、不能诛杨复恭，称朝廷只观强弱不计是非、随强弱施恩刑，并以军情易变、百姓受祸及乘舆将逃往何处等语相逼。',[('李茂贞','上表写信者'),('杜让能','收书宰相'),('李杰','以唐昭宗身份受表及欲讨者'),('杨复恭','表中所指未诛者')],note='不能庇与不计是非均李表主张，不当项目的事实判断；元舅未具名不本段造人，前史另有身份证据。')
event('emperor_du_campaign_debate','昭宗决讨李茂贞，杜让能谏不宜并承命',25,'893年；讨伐谋议期间，具体日未载','京师、中书',
      '昭宗决定讨李茂贞，命杜让能专掌调兵食。杜劝茂贞近国门、不宜构怨败后无及，建议群臣共力；昭宗说不愿坐视王室衰弱，用兵委诸王、成败不责杜，并以元辅之位要求其任事。杜说明非避事，忧时势不能及日后遭罪，仍奉诏愿以死继之。',[('李杰','以唐昭宗身份决讨委任者'),('杜让能','谏争后奉命者'),('李茂贞','所讨对象')],note='原文国步末夷疑未夷，保留；宪宗晁错七国为论辩比拟，不建893参与人物。承诺不责与后来诛杜分别记，不调和矛盾。')
event('du_month_planning_cui_leaks','杜让能留中书月余调度，崔昭纬泄二镇',25,'留中书月馀不归；具体起止未载','京师、中书、邠岐',
      '昭宗命杜让能留中书筹划调度，一个多月不回家。崔昭纬暗结邠岐，充耳目，杜朝发言二镇夕知。',[('李杰','以唐昭宗身份命留者'),('杜让能','调度者'),('崔昭纬','向二镇泄情者')],note='朝言夕知为史载描述，未定每条传讯内容；月余不反算开始日。')
event('market_protest_attacks_chancellors','李茂贞党纠市人，诉君遂并袭二相',25,'前述筹兵期间；具体日未载','京师',
      '李茂贞命其党聚集市人，拦西门君遂马称岐帅无罪、不宜讨；君遂说属宰相事。市人又拦崔昭纬、郑延昌轿，二相说主上专委杜让能、自己不知。市人投瓦石，二相藏民宅才免，丢堂印与朝服。',[('李茂贞','命党纠集者'),('西门君遂','被拦且答者'),('崔昭纬','被拦遭袭者'),('郑延昌','被拦遭袭者'),('杜让能','二相说辞所指受委者')],note='数百千人原底本表述含混，不改为精确某人数；二相自称不预不能消除崔此前泄情记载，岐帅无罪为诉者说辞。')
event('emperor_punishes_protest_leaders','昭宗诛市人首领，京师仍有逃民',25,'投瓦袭相之后；具体日未载','京师、山谷',
      '昭宗命捕杀带头闹事者，讨伐意愿更坚定。部分京师居民逃藏山谷，严刑不能禁。',[('李杰','以唐昭宗身份下令者')],note='唱帅者未名，不造人；严刑不能禁为书述，不补人数。')
event('li_sizhou_li_hui_campaign_offices','李嗣周京西招讨使，李鐬为副',25,'893年八月','京西',
      '朝廷以嗣覃王李嗣周为京西招讨使，神策大将军李鐬为副。',[('李嗣周','嗣覃王、被授招讨使者'),('李鐬','神策大将军、招讨副使')],note='底本嗣覃王嗣周据李氏宗室称谓展开姓名；李钅岁是金旁与岁部件分写，合字记李鐬并保留原字形，不另建两人；不补宗室世系。')
for name,aliases in [('李嗣周',['嗣覃王嗣周','覃王嗣周']),('李鐬',['李钅岁'])]:
    next(p for p in B['people'] if p['key']==people[name])['aliases']=aliases
    claim('person',people[name],'aliases',f'{name}在底本此段记作{aliases[0]}。',25,quote='八月，以嗣覃王嗣周为京西招讨使，神策大将军李钅岁副之。',note='称号展开与拆字合并均保留底本形式；未据二字猜另一个姓名。')
event('tian_attacks_shezhou','田頵二万攻歙，裴枢守城久不下',26,'893年八月丙辰开始；久不下','歙州、宣州',
      '杨行密派田頵率宣州二万军攻歙州，歙州刺史裴枢守城，久未攻下。',[('杨行密','遣军者'),('田頵','攻城者'),('裴枢','守城者')],note='二万书载；不把久不下写成当日即败退或已攻克。')
event('tao_ya_shezhou_accepted','歙人请陶雅，杨任刺史、送裴枢还朝',26,'久攻后；具体日未载','歙州、池州、朝廷',
      '《通鉴》评诸将多贪暴、池州团练使陶雅宽厚得民，歙人说若得陶为刺史便听命。杨行密任陶雅为歙州刺史，歙人接纳；陶以礼见裴枢，送其回朝。',[('杨行密','任陶者'),('陶雅','被任接纳并礼送裴者'),('裴枢','被送还朝者')],note='宽厚及贪暴为史书品评，不泛化所有武将；久攻后未换算日期，送归未补朝廷后任。')
claim('person',people['裴枢'],'biography','《通鉴》称裴枢为遵庆之曾孙。',26,quote='枢，遵庆之曾孙也。',note='保留书载曾孙信息，未据本段片名另建祖人或推具体中间世系。')
event('pang_attacks_yanzhou','庞师古移兵攻兗，屡破朱瑾',27,'893年八月条；各次日未载','兗州',
      '朱全忠命庞师古移军攻兗州，同朱瑾交战，多次击败朱瑾。',[('朱温','以朱全忠名义命移兵者'),('庞师古','攻战者'),('朱瑾','被击败者')],note='屡破为多次概述，不造未具名逐战日期或军数。')
event('qian_zhenhai_appointment','钱镠授镇海节度使',28,'893年九月丁卯','镇海',
      '朝廷任钱镠为镇海节度使。',[('钱镠','受任者')],note='区别此前武胜防御与苏杭观察使，不把三次任职合一日。')
event('li_cunxiao_night_raid_sun_capture','李存孝夜袭李存信营，擒孙考老',29,'893年九月条；具体日未载','邢州战区、李存信营',
      '李存孝夜袭李存信营，俘获奉诚军使孙考老。',[('李存孝','夜袭捕获者'),('李存信','被袭营主'),('孙考老','被俘军使')],note='营地未在本段精确定位，未补孙死亡。')
event('li_keyong_sieges_xing_fortification','李克用亲围邢，李存孝突击阻筑堑',29,'夜袭之后；具体日未载','邢州',
      '李克用亲率军围邢州，掘沟筑垒环城；李存孝时出突击，使沟垒不能筑成。',[('李克用','亲围筑堑者'),('李存孝','突击阻筑者')],note='区别二月围及七月合军的阶段；未下结论此时城已陷。')
event('yuan_fengtao_misleads_li_cunxiao','袁奉韬密劝李存孝停攻，十日沟垒成',29,'筑堑被阻后；停击旬日成','邢州',
      '河东牙将袁奉韬秘密遣人告诉李存孝，李克用只是等堑成便回晋阳，其他将非其敌、浅堑不足阻之。李存孝相信，停止出击；十日沟垒完成，无处越逃，李存孝陷入困境。',[('袁奉韬','遣人说诱者'),('李存孝','听信停击者'),('李克用','说辞所指主将')],note='待堑成归晋阳为袁说辞，未记李克用真已离围；无处越为书述，不补已投降或处死。')
event('deng_jijun_returns_zhu','邓季筠从围邢逃返，朱使领亲军',29,'邢州围城时；具体日未载','邢州、汴',
      '汴将邓季筠跟随李克用攻邢州，轻骑逃回朱全忠处。朱大喜，使他统领亲军。',[('邓季筠','从围后逃返受用者'),('李克用','所从攻邢主将'),('朱温','以朱全忠名义任用者')],note='从克用攻说明此次临时同行，不推永久投晋；轻骑逃不补护从人数。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={22:'外镇加官；天雄职称不误合魏博天雄。',23:'20万民夫13都军士70里为书载，军士总数及现代周长未知。',24:'张卒冯代，不补死因与诏日。',25:'表书言论、君杜争论、月余调度与泄情、纠市袭相、捕首逃民、八月授招讨分录；说辞与书述区分，拆字李鐬保留底本别名。',26:'丙辰二万攻久不下与改陶得纳礼送分阶段；裴枢曾孙只加人物依据。',27:'屡战概述不造逐次日期。',28:'钱镇海授与前两次职区分。',29:'夜袭俘孙、亲围筑堑被阻、袁说诱及旬日成、邓逃返亲军分开；袁归晋阳说非真实离围。'}
for n in range(22,30):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(22,30):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=893,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(22,30)],next_paragraph='zztj-v259-y0893-p030',coverage='卷259景福二年第22—29段连续录入；本年38段尚未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
