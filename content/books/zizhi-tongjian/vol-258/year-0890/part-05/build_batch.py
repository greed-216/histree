"""Curate consecutive Tongjian volume 258, year 890 paragraphs 29–36."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 44))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0890-p029-p036', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-258-890'
B['sources'] = [dict(key=source,title='资治通鉴·卷258',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/4d35696319726b523bd624f2370cb2cf7faa6b43/resources/derived/tongjian/258.txt',note='卷258大顺元年起；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/258.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/258.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
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

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0890_05_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·大顺元年（890）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷258大顺元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=890,note=None,quote=None):
    key='event_zztj_258_0890_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_258_0890_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('qian_orders_du_harmed','杜孺休到官，钱镠密使沈粲害之',29,'890年八月条；具体日未载','苏州',
      '苏州刺史杜孺休到任，钱镠秘密命沈粲加害杜孺休。',
      [('杜孺休','到官被加害对象'),('钱镠','秘密命害者'),('沈粲','奉密命者')],note='仅按“密使害之”保存史载行动，不补具体杀害方式、执行日期或现场。')
event('li_you_takes_suzhou','李友拔苏州，沈粲归杭州后奔孙儒',29,'890年八月条；具体日未载','苏州、杭州',
      '杨行密将李友攻取苏州，沈粲返回杭州。钱镠欲归罪沈粲而杀之，沈粲逃投孙儒。',
      [('杨行密','李友所属主将'),('李友','攻城将领'),('沈粲','返回及逃投者'),('钱镠','拟归罪杀人者'),('孙儒','沈粲逃投对象')],note='欲杀不记为已杀沈粲。')
event('wang_withdraws_hanzhou','王建退屯汉州',30,'890年八月条；具体日未载','汉州',
      '王建撤退驻军汉州。',[('王建','退屯者')],note='原文未说明退兵原因，不自动归因于败战。')
event('chen_forced_tax','陈敬瑄设征督院逼富民供军',31,'890年八月条；具体日未载','',
      '陈敬瑄搜括富民财产供军，置征督院，以桎梏棰楚逼民自报财产，对匿财虚报者急征；《通鉴》评有财者不聊生。',
      [('陈敬瑄','设院征财者')],note='负担与不聊生为书载叙述；未明确院址，不补具体地点及税额。')
event('li_cunxiao_relief_ze','李存孝奉李克用命援李罕之',32,'890年八月后条；具体日未载','泽州方向',
      '李罕之向李克用告急，李克用遣李存孝率骑兵救援。',
      [('李罕之','告急者'),('李克用','遣援者'),('李存孝','援军统领')],note='五千为书载军数；泽州方向承前后同一围攻，不补具体援军路线。')
event('zhu_heyang_camp','朱全忠驻军河阳',33,'890年九月壬寅','河阳',
      '朱全忠驻军河阳。',[('朱温','以朱全忠名义驻军者')])
event('ze_taunts_background','围泽州两军相讥的前事',33,'汴军初围泽州至李存孝到援时；具体日未载','泽州',
      '汴军初围泽州时讥李罕之倚河东，称沙陀将无处藏身。李存孝来援后率精骑绕汴寨，以寻穴者自称，挑战汴军。',
      [('李罕之','被讥对象'),('李存孝','率骑挑战者')],year=None,note='段内回叙不强定九月壬寅；军中夸言不作张浚已围太原或战争结果的独立证据，五百为书载。')
event('deng_jiqun_captured','李存孝生擒邓季筠',33,'890年九月条；李存孝到援后','泽州',
      '邓季筠率兵出战，被李存孝生擒。',[('邓季筠','出战被俘者'),('李存孝','俘获者')],note='被俘不据本段补死亡。')
event('malao_battle','李存孝李罕之败汴军于马牢山',33,'890年九月条；擒邓季筠当夕后','马牢山、怀州',
      '李谠、李重胤当夕率众逃走，李存孝、李罕之追击，在马牢山大败汴军，追至怀州而还。',
      [('李谠','退逃将领'),('李重胤','退逃将领'),('李存孝','追击将领'),('李罕之','追击将领')],note='书载斩获万计，不独立核实；当夕相对时间不换算确日。')
event('ge_zhu_abandon_lu','葛从周朱崇节弃潞州',33,'890年九月条；马牢山战后','潞州',
      '李存孝再率兵攻潞州，葛从周、朱崇节弃城返回。',
      [('李存孝','进攻者'),('葛从周','弃城者'),('朱崇节','弃城者')],note='返回目的地未载，不补朱全忠军中或大梁。')
event('zhu_executes_li_generals','朱全忠责败斩李谠李重胤',33,'890年九月戊申','',
      '朱全忠庭责诸将败退之罪，斩李谠、李重胤后返回。',
      [('朱温','以朱全忠名义责斩者'),('李谠','被斩将领'),('李重胤','被斩将领')],note='底本“桡”按败退语境整理，不猜确切刑场与返回地。')
event('kang_cunxiao_appointments','康君立领昭义，李存孝任汾州刺史',34,'890年九月条；潞州战后','昭义、汾州',
      '李克用以康君立为昭义留后，以李存孝为汾州刺史。《通鉴》记李存孝自认擒孙揆功大应镇昭义，因而愤恚，数日不食并纵意刑杀，始有叛李克用之志。',
      [('李克用','任用者'),('康君立','昭义留后受任者'),('李存孝','汾州刺史受任及不满者')],note='叛志是书载意向，不提前记为实际叛乱；此处未说朝廷授职。')
event('li_kuangwei_takes_wei','李匡威攻蔚州俘邢善益',34,'890年九月条；具体日未载','蔚州',
      '李匡威攻蔚州，俘获刺史邢善益。',[('李匡威','攻城俘获者'),('邢善益','被俘刺史')])
event('helian_attacks_zhelu','赫连铎攻遮虏平杀刘胡子',34,'890年九月条；具体日未载','遮虏平',
      '赫连铎率吐蕃、黠戛斯部众进攻遮虏平，杀其军使刘胡子。',
      [('赫连铎','进攻者'),('刘胡子','被杀军使')],note='数万为书载数，不把两个部族统称写作具体个人。')
event('li_siyuan_relief_victory','李存信初败，李嗣源为副后破敌',34,'890年九月条；遮虏平被攻后','遮虏平方向',
      '李克用先遣李存信出击，未能获胜；再命李嗣源为李存信副手，遂击败敌军。',
      [('李克用','遣将增副者'),('李存信','先战不胜及再战将领'),('李嗣源','受命为副及胜方将领')],note='不胜不增写为全军溃败；方向承同段战事，不猜具体战场点。')
event('li_defeats_kuangwei_helian','李克用继进败李匡威赫连铎',34,'890年九月条；李嗣源击破之后','',
      '李克用以大军随后，李匡威、赫连铎败走，李克用军俘获李匡威之子、武州刺史李仁宗及赫连铎之婿，书载俘斩万计。',
      [('李克用','统军胜方'),('李匡威','败走一方'),('赫连铎','败走一方'),('李仁宗','武州刺史被俘者')],note='原文省称仁宗，依明确李匡威之子补姓李，非帝王庙号；赫连铎婿未具名不新建人物；人数为书载。')
rk='relationship_person_李匡威_person_李仁宗_父亲'
B['person_relationships'].append(dict(key=rk,person_a_key=people['李匡威'],person_b_key=people['李仁宗'],relation_type='父亲',description='《通鉴》称武州刺史仁宗为李匡威之子；李匡威是李仁宗的父亲。',status='draft'))
claim('person_relationship',rk,'description','李匡威是李仁宗的父亲。',34,quote='获匡威之子武州刺史仁宗及鐸之婿')
event('li_siyuan_generals_remark','李嗣源讥诸将夸口勇略',35,'诸将相会时；具体年日未载','',
      '《通鉴》记诸将相会各夸勇略，李嗣源默然，后称诸将以口击贼、自己以手击贼，诸将惭而止；书中评李嗣源谨重廉俭。',
      [('李嗣源','言语评论者')],year=None,note='性行评价与会面逸事未载具体时间，不强定890年九月。')
event('zhang_xingzhou_changzhou','杨行密任张行周常州制置使',36,'890年九月条；闰月前','常州',
      '杨行密以其将张行周为常州制置使。',[('杨行密','任用者'),('张行周','制置使受任者')])
event('liu_takes_changzhou_890','刘建锋取常州杀张行周并围苏州',36,'890年闰月；承九月条','常州、苏州',
      '孙儒遣刘建锋攻取常州，杀张行周，随后围苏州。',
      [('孙儒','遣军者'),('刘建锋','攻城杀将及围城将领'),('张行周','被杀制置使')],note='闰月承九月条保存，不换算公历；围苏州不提前记攻取。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={29:'杜孺休到官受密害与李友取苏州、沈粲归杭后逃奔分录；钱镠欲杀沈粲不记成已杀。',31:'富民财征督院和不聊生为书载叙述，不猜院址税额。',33:'九月驻河阳、旧围军夸言、擒邓季筠、马牢追击、弃潞及戊申斩将分录；夸言不作战况独立证据。',34:'任命与李存孝不满、北方攻势、救援及大军胜利分录；叛志不提前写实际叛乱；仁宗按李匡威子同姓补李。',35:'会面逸事未记时间，给未定年；性行评价明示书载。',36:'常州任命与闰月攻杀围苏分录，围不作已得。'}
for n in range(29,37):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
    if n in reviews:ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(29,37):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=890,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(29,37)],next_paragraph='zztj-v258-y0890-p037',coverage='卷258大顺元年第29—36段连续录入；本年未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
