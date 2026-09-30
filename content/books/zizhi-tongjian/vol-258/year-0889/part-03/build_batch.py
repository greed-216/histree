"""Curate consecutive Tongjian volume 258, year 889 paragraphs 17–24."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 25))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0889-p017-p024', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-258-889'
B['sources'] = [dict(key=source,title='资治通鉴·卷258',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/4d35696319726b523bd624f2370cb2cf7faa6b43/resources/derived/tongjian/258.txt',note='卷258龙纪元年起；书、卷、年、段落及行号见批次账本。')]
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
alias = {'李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0889_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·龙纪元年（889）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷258龙纪元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=889,note=None,quote=None):
    key='event_zztj_258_0889_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_258_0889_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('zhaozong_name_ye','昭宗改名晔',17,'889年十一月','',
      '昭宗改名晔；本次改名仍归既有李杰人物。',[('唐昭宗','改名者')],note='姓名变化不另建人物，原先李敏、李杰及唐昭宗沿用同一key。')
claim('person',people['李杰'],'aliases','昭宗于889年十一月改名晔，李晔为同一人物的后用名。',17)
event('eunuch_ritual_clothes','昭宗允宦官服剑佩参与祭祀',18,'889年十一月；圆丘祭祀前','',
      '昭宗命有司制法服，孔纬与谏官、礼官反对；昭宗手札承认所论得当，但主张从权，宦官遂服剑佩侍祠。',
      [('唐昭宗','准许法服者'),('孔纬','反对者')],note='底本“衤癸衫”疑转录残字，保留快照，不猜定具体衣制名称；本事件只记明示的本次制法服与争议。')
event('round_mound_amnesty','昭宗祀圆丘并大赦',18,'889年十一月己酉','圆丘',
      '昭宗祭祀圆丘，赦天下。',[('唐昭宗','祭祀及赦令者')])
event('zhaozong_eunuch_background','昭宗即位前后与杨复恭权力矛盾',18,'在藩邸及即位后；具体年日未逐事确定','',
      '《通鉴》追叙昭宗在藩邸时厌恶宦官，即位后对杨复恭恃援立之功的行为不平，政事多与宰相谋议；孔纬、张浚劝其仿大中故事抑制宦官权力。',
      [('唐昭宗','与宰相谋议者'),('杨复恭','被批评对象'),('孔纬','抑宦权建议者'),('张浚','抑宦权建议者')],year=None,note='跨藩邸与即位后的追叙，不一律落在889年；对其行为的评价以书载叙述呈现。')
event('kong_wei_rebukes_yang','孔纬当廷批评杨复恭蓄假子',18,'昭宗即位后他日；具体年日未载','太极殿',
      '孔纬当昭宗面批评杨复恭乘肩舆至前殿、蓄壮士为假子并令掌禁兵或方镇，称其有将反之迹；杨复恭辩称为收士心卫国家，昭宗追问为何不使假子姓李。',
      [('孔纬','当廷批评者'),('杨复恭','辩解者'),('唐昭宗','追问者')],year=None,note='谋反是孔纬的指控、卫国家是杨复恭的辩解；不把指控记成已发生的叛乱。')
event('yang_shouli_renamed','昭宗赐杨守立姓名李顺节',18,'昭宗即位后；具体年日未载','',
      '昭宗担忧杨守立作乱，要求杨复恭使其入侍；杨复恭引见杨守立，昭宗赐姓名李顺节，并使掌六军管钥。',
      [('唐昭宗','赐名及授职者'),('杨复恭','引见者'),('李顺节','原名杨守立的赐名受任者')],year=None,note='杨守立、胡弘立、李顺节依本段明确同一人；既有887年天威军统领实体复用。段内跨时追叙未明记赐名日，不强定889年。')
claim('person',people['杨守立'],'aliases','杨守立本姓胡、名弘立，后获赐姓名李顺节。',18,quote='复恭假子天威军使杨守立，本姓胡，名弘立，勇冠六军，人皆畏之。上欲讨复恭，恐守立作乱，谓复恭：“朕欲得卿胡子在左右。”复恭见守立于上，上赐姓名李顺节')
rk='relationship_person_杨复恭_person_杨守立_假父'
B['person_relationships'].append(dict(key=rk,person_a_key=people['杨复恭'],person_b_key=people['杨守立'],relation_type='假父',description='《通鉴》称杨守立为杨复恭假子；杨复恭是杨守立的假父，收为假子的具体年未载。',status='draft'))
claim('person_relationship',rk,'description','杨复恭是杨守立的假父。',18,quote='复恭假子天威军使杨守立，本姓胡，名弘立')
event('li_shunjie_promoted','李顺节升天武都头领镇海节度使',18,'赐名后不期年，俄；具体年日未载','',
      '李顺节获赐名后未满一年升至天武都头，领镇海节度使，随后加同平章事。',
      [('李顺节','擢升加官者')],year=None,note='“不期年”“俄”只提供相对时间，可能跨年；领镇海节度使不等于其赴任并实控镇海。')
event('kong_wei_rejects_li_audience','孔纬拒集百僚见李顺节',18,'李顺节加官谢日及他日；具体年日未载','中书',
      '李顺节加官谢日，台吏申请其班见百僚，孔纬判不集。李顺节后到中书流露不悦并提起此事，孔纬以宰相师长百僚回应，李顺节不敢再言。',
      [('孔纬','拒集百僚及回应者'),('李顺节','申请班见及不悦者')],year=None,note='这段接加官后的谢日、他日，未定确年，不录为889年确日事件。')
event('zhu_salt_iron_refused','孔纬阻朱全忠兼领盐铁',19,'889年十一月后条；具体日未载','',
      '朱全忠请求兼领盐铁，孔纬坚持反对，并向进奏吏表示朱全忠若要此职须兴兵；朱全忠遂止。',
      [('朱温','以朱全忠名义求职及停止者'),('孔纬','反对者')],note='孔纬“非兴兵不可”是强硬表态，不推定双方实际因此开战。')
event('tian_jun_captures_changzhou','田頵地道入常州擒杜稜',20,'889年十一月后条；具体日未载','常州',
      '田頵攻常州，通过地道于夜间入城，军兵出于制置使杜稜寝室，俘获杜稜，并以兵驻守常州。',
      [('田頵','攻城及驻军将领'),('杜稜','被俘制置使')],note='书载驻兵三万，不当作独立核实的兵数；杜稜被俘不推定遇害。')
event('pang_attacks_sun_ru','庞师古自颍上进击孙儒',21,'889年十一月后条；具体日未载','颍上、淮南',
      '朱全忠遣庞师古率兵自颍上趋淮南，进击孙儒。',
      [('朱温','以朱全忠名义遣军者'),('庞师古','进击将领'),('孙儒','被攻方主将')],note='本段未记交战结果，不预录后续胜败。')
event('wang_guangdu_victory','王建败山行章宋行能于广都',22,'889年十二月甲子','广都、成都、眉州',
      '王建在广都击败山行章及西川骑将宋行能。宋行能返回成都，山行章退守眉州。',
      [('王建','胜方统领'),('山行章','败退将领'),('宋行能','败返成都将领')],note='底本“夺还成都”保留；仅整理为返回成都，不猜定“夺”字异文。')
event('shan_surrenders_wang','山行章向王建请降',22,'889年十二月壬申','眉州',
      '山行章向王建请求投降。',[('山行章','请降者'),('王建','受请降者')],note='“请降”不补写已交城或随后官职安排。')
event('sun_ru_crosses_yangtze','孙儒自广陵渡江',23,'889年十二月戊寅','广陵、江',
      '孙儒自广陵引兵渡江。',[('孙儒','渡江统领')],note='江只依原文保存，不据此绘精确渡江点。')
event('sun_ru_takes_changzhou','孙儒逐田頵取常州，刘建锋守城',23,'889年十二月壬午','常州',
      '孙儒驱逐田頵，攻取常州，以刘建锋守之，随后返回广陵。',
      [('孙儒','攻城及任守者'),('田頵','被逐者'),('刘建锋','守城将领')])
event('liu_jianfeng_takes_runzhou','刘建锋逐成及取润州',23,'889年十二月条；孙儒还广陵后','润州',
      '孙儒返回广陵后，刘建锋又驱逐成及，攻取润州。',
      [('刘建锋','攻城将领'),('成及','被逐者')])
event('liu_jurong_alchemy_background','刘巨容襄阳得炼金方的追叙',24,'刘巨容任山南东道节度使时；具体年未载','襄阳',
      '《通鉴》追叙刘巨容在襄阳时，申屠生传授所谓烧药为黄金的方法；田令孜之弟途经襄阳，刘巨容向其展示金。',
      [('刘巨容','受方及示金者'),('申屠生','传方者')],year=None,note='炼金说法作为史书所叙记录，不判定科学真实性；田令孜之弟未具名，不凭既知亲属猜定身份。')
event('liu_jurong_refuses_recipe','田令孜求刘巨容炼金方被拒',24,'刘巨容寓居成都后；具体年未载','成都',
      '刘巨容寓居成都后，田令孜向其索取炼金方法，刘巨容不予，田令孜记恨。',
      [('田令孜','求方者'),('刘巨容','拒予者')],year=None,note='拒方与记恨为史书叙述；寓居时年未载，不一律定889年。')
event('tian_kills_liu_jurong','田令孜杀刘巨容并灭其族',24,'889年；原文是岁','',
      '《通鉴》记田令孜在本年杀刘巨容并灭其族。',[('田令孜','杀人者'),('刘巨容','被杀者')],note='“是岁”明确本年；杀人地点未单独明载，不借寓居成都推精确刑杀地点。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={17:'昭宗改名晔，复用李杰；需将李晔作为同一人的检索别名补入。',18:'法服、圆丘祭祀与段内权力争议、赐名加官分别拆录；追叙及不期年、俄、他日不给889确年；杨守立胡弘立李顺节复用一人；假父按既定方向。衤癸衫残字保留。',20:'杜稜被俘不推死；三万为书载。',22:'夺还保留底本，不猜定异字；请降不补交城。',23:'渡江、取常州及再取润州分录。',24:'襄阳炼金和寓成都拒方为追叙，杀刘巨容按是岁归889；未具名田令孜弟不猜人。'}
for n in range(17,25):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
    if n in reviews:ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17,25):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=889,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph='zztj-v258-y0890-p001',coverage='卷258龙纪元年第17—24段连续录入，本年终结；后接大顺元年。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
