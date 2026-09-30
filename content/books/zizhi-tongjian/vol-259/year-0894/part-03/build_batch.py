"""Curate consecutive Tongjian volume 259, year 894 paragraphs 17–24."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 34))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0894-p017-p024', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-894'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259乾宁元年条；书、卷、年、段落及行号见批次账本。')]
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
    B['claims'].append(dict(key=f'claim_zztj_259_0894_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·乾宁元年（894）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259乾宁元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=894,note=None,quote=None):
    key='event_zztj_259_0894_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0894_'+code+'_'+pk
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

alias.update({'李溪':'李磎','李谿':'李磎','薛志诚':'薛志勤'})
event('feng_jingzhang_intercepts_zhu_attack_fails','冯敬章邀击淮南军，朱延寿攻蕲未克',17,'894年六月条；具体日未载','蕲州',
      '蕲州刺史冯敬章截击淮南军；朱延寿攻蕲州，没有攻下。',[('冯敬章','邀击的蕲州刺史'),('朱延寿','攻蕲未克的淮南将领')],note='邀击与攻城未克照书分别陈述，不推冯全歼淮南军或朱已死。')
event('li_xi_chancellor_proclamation','朝廷宣制授李溪同平章事',18,'894年六月戊午','朝廷',
      '朝廷宣制，以翰林学士承旨、礼部尚书李溪为同平章事。',[('李磎','底本作李溪的授相对象'),('李杰','以唐昭宗身份任命者')],note='依据北梦琐言同一哭麻事件对应李磎，李溪李谿为电子本异字；授制与正式视事区别，后被阻未作已长期执政。')
next(r for r in B['people'] if r['key']==people['李磎'])['aliases']=['李溪','李谿']
claim('person',people['李磎'],'aliases','主书底本在本段记李溪，另一电子转录作李谿；北梦琐言哭麻篇作李磎。',18,quote='以翰林学士承旨、礼部尚书李溪同平章事',note='主书底本为李溪；另名书证另设独立引用，按同一任相受阻及刘崇鲁哭麻行动链对应，不凭同音任意合人。')
event('liu_chonglu_cries_proclamation_accuses_li','刘崇鲁掠麻恸哭，向昭宗指控李溪',18,'894年六月戊午；方宣制时','朝廷',
      '宣制时，水部郎中知制诰刘崇鲁出班取制书恸哭。昭宗问原因，刘指称李溪奸邪、依附杨复恭西门君遂得翰林职，没有宰相才能，恐危社稷。',[('刘崇鲁','掠麻哭并对问指控者'),('李杰','以唐昭宗身份召问者'),('李磎','底本李溪、被指控者'),('杨复恭','指控中所称受依附者'),('西门君遂','指控中所称受依附者')],note='刘言为指控，未作为确证李奸邪或任官靠结交；西门已死，话语中的既往人物不作894年现场参与。')
event('li_xi_blocked_to_junior_tutor','李溪任相受阻，改太子少傅',18,'宣制被阻后；确日未载','朝廷',
      '李溪任相最终受阻，改为太子少傅。',[('李磎','底本李溪、改官者')],quote='溪竟罢为太子少傅。',note='不补在任天数；太子少傅为所授官名，未据此猜所教太子姓名。')
claim('person',people['李磎'],'biography','《通鉴》称李溪是鄜之孙，又记昭宗向他学习作文。',18,quote='溪，鄜之孙也。上师溪为文',note='仅保留书载祖名片段，不另造未核全名祖父；学文是关系背景，未定始年，未泛成所有政务的师生指挥。')
event('cui_fears_li_power_has_liu_block','崔昭纬恐李溪分权，使刘崇鲁阻相',18,'李溪拟任相时；背景具体日未载','朝廷',
      '《通鉴》叙崔昭纬怕李溪任相分去权力，因此使刘崇鲁阻止。',[('崔昭纬','史书所叙授意阻相者'),('刘崇鲁','所使阻相者'),('李磎','底本李溪、拟任相者')],quote='崔昭纬恐溪为相，分己权，故使崇鲁沮之。',note='动机与授意归于史书解释，不把它写成刘本人承认；发生背景限此任相争端，不补密谋地点。')
event('li_xi_ten_memorials_counterclaims','李溪十表自讼，反驳并指控刘氏',18,'任相受阻后；十表具体日期未载','朝廷',
      '李溪十次上表为自己辩解，斥刘崇鲁父符受赃事觉自杀，并指崇望与杨复恭深交、崇鲁曾拜田令孜和为朱玫作劝进表；他援礼制批评刘在殿上恸哭，请求治罪。',[('李磎','底本李溪、上表自讼者'),('刘崇鲁','反指控及治罪请求对象'),('刘崇望','奏表中所称崇望'),('杨复恭','奏表中被提及者'),('田令孜','奏表中被提及者'),('朱玫','奏表中被提及者')],note='受赃、自杀、深交、庭拜与劝进等为李奏的控词，不仅因有人指称就建立事件或结交关系；父符只保留片名不造未核全名。底本弟崇望与两唐书崇望弟崇鲁的长幼写法相抵，暂不建方向关系。')
event('liu_chonglu_office_stopped','诏停刘崇鲁现任官职',18,'李溪上表后；确日未载','朝廷',
      '朝廷下诏停止刘崇鲁的现任官职。',[('刘崇鲁','被停见任者'),('李杰','以唐昭宗身份在位皇帝')],quote='诏停崇鲁见任。',note='见任即现任，不补流放、处死或具体后官。')
event('li_xi_continues_severe_petitions','李溪仍上表求诛窜，言辞激烈',18,'停刘崇鲁见任后；确日未载','',
      '停刘崇鲁官以后，李溪继续上表，要求处死或流窜刘氏，奏表数千言，书叙其诟骂无所不至。',[('李磎','底本李溪、继续上表者'),('刘崇鲁','求治罪对象')],quote='溪犹上表不已，乞行诛窜，表数千言，诟詈无所不至。',note='乞行是请求，未获记允不得录刘被诛或流窜；言辞评价归于书述，不作研究者心理诊断。')
event('keyong_tuyuhun_helian_dead_bai_captured','李克用破吐谷浑，杀赫连铎擒白义诚',19,'894年六月条；具体日未载','',
      '李克用大败吐谷浑，杀赫连铎，俘白义诚。',[('李克用','击败杀擒者'),('赫连铎','被杀者'),('白义诚','被擒者')],note='原文未载战地、杀法与白后来结局；不将部族名猜为地名或替白补官职。')
event('li_maozhen_takes_langzhou','李茂贞遣军攻取阆州',20,'894年秋七月','阆州',
      '李茂贞派军进攻阆州，将其攻下。',[('李茂贞','遣攻者')],quote='秋，七月，李茂贞遣兵攻阆州，拨之',note='拨之按攻取语义整理而不改底本拨字；不猜具体统军者。')
event('yang_family_breaks_langzhou_siege','杨复恭杨守亮杨守信率族党突围',20,'894年七月阆州被攻时','阆州',
      '杨复恭、杨守亮、杨守信带族党冲出包围逃走。',[('杨复恭','突围逃走者'),('杨守亮','突围逃走者'),('杨守信','突围逃走者')],quote='杨复恭、杨守亮、杨守信帅其族党犯围走。',note='此段未记已到河东，之后欲奔及途中被获另段；族党未名不批量虚构家族成员。')
event('zheng_qi_retires','郑綮累表避位，太子少保致仕',21,'894年七月条；具体日未载','朝廷',
      '礼部侍郎、同平章事郑綮自觉不合众望，多次上表辞位，朝廷诏以太子少保致仕。',[('郑綮','请辞获致仕者')],note='自以为其个人判断，不断言所有朝臣反对；累表不反算首次请辞日。')
event('xu_yanruo_chancellor','徐彦若复为中书侍郎兼吏部尚书同平章事',21,'894年七月条；具体日未载','朝廷',
      '御史大夫徐彦若被任为中书侍郎兼吏部尚书、同平章事。',[('徐彦若','授相兼官者')],note='既有经历中曾任宰相，因此复用主体不另建；不把中书与吏部职分为不同人物。')
event('yang_shouhou_dies','绵州刺史杨守厚卒',22,'894年七月条；具体日未载','绵州',
      '绵州刺史杨守厚去世。',[('杨守厚','去世刺史')],quote='绵州刺史杨守厚卒',note='只记书载去世，不补死因、年龄或确日。')
event('chang_zairong_surrenders_mianzhou','常再荣举绵州降王建',22,'杨守厚卒后；具体日未载','绵州',
      '杨守厚部将常再荣带城归降王建。',[('常再荣','举城归降者'),('王建','接受归降一方')],note='举城不等城破屠戮，未推常得何新官或全部人口离城。')
event('yang_family_captured_qianyuan','杨氏欲奔河东，至乾元被华州兵获',23,'阆州突围后、894年八月献俘前','商山、乾元',
      '杨复恭、杨守亮、杨守信打算从商山逃往河东，至乾元遇华州军，被俘。',[('杨复恭','欲奔河东后被俘者'),('杨守亮','欲奔河东后被俘者'),('杨守信','欲奔河东后被俘者')],quote='杨复恭、守亮、守信将自商山奔河东，至乾元，遇华州兵，获之。',note='将自是拟逃路线，不记三人实际已到河东；乾元不猜今名或经纬度。')
event('han_presents_yang_execution_duliu','韩建献杨复恭等，三人斩于独柳',23,'894年八月','阙下、独柳',
      '韩建将杨复恭、杨守亮、杨守信献到朝廷，三人被斩于独柳。',[('韩建','献俘者'),('杨复恭','被献被斩者'),('杨守亮','被献被斩者'),('杨守信','被献被斩者')],quote='杨复恭、守亮、守信将自商山奔河东，至乾元，遇华州兵，获之。八月，韩建献于阙下，斩于独柳。',note='八月未给具体日；献阙下与独柳处刑为前后两地点，不猜现代刑场。')
event('li_maozhen_submits_yang_old_letter','李茂贞献杨复恭给守亮的旧书',23,'894年八月条；呈献确日未载','朝廷',
      '李茂贞献杨复恭曾写给杨守亮的书信。信中诉说自己致仕遭遇，令大侄积粟训兵勿贡献，并称自己扶立寿王却被废斥，骂皇帝为负心门生天子。',[('李茂贞','献旧书者'),('杨复恭','旧信作者'),('杨守亮','旧信受信者'),('李杰','以寿王与天子称被旧信指责者')],note='写信早于献书，年月不详；本事件只为献书，不在894年让已处死者新写信。立寿王与致仕经过均旧信自诉，承天门隋家旧业亦信中说法，不作产权事实；大侄称呼不另增生亲叔侄。')
event('kang_visits_keyong_jinyang','康君立到晋阳谒李克用',23,'894年八月条；己未宴前','晋阳',
      '昭义节度使康君立到晋阳拜见李克用。',[('康君立','来谒节度使'),('李克用','受谒者')],quote='昭义节度使康君立诣晋阳谒李克用。',note='本段位置在八月，旧史列传作九月来太原，异说另引，不据来谒推隐秘阴谋。')
event('keyong_slashes_kang_imprisons','李克用宴饮念存孝，斫康君立并囚',23,'894年八月己未','晋阳、马步司',
      '李克用同诸将饮酒博戏，谈到李存孝流泪。素与李存信友善的康君立说了一句忤意的话，李克用拔剑砍他，将其囚于马步司。',[('李克用','饮博、哭及斫囚者'),('康君立','言忤后被斫囚者'),('李存孝','已死、被谈论者'),('李存信','康平素相善对象')],quote='己未，克用会诸将饮博，酒酣，克用语及李存孝，流涕不已。君立素与李存信善，一言忤旨。克用拨剑斫之，囚于马步司。',note='拨剑疑拔剑保留底本；康所言具体内容未载，不编造台词或将伤后立即死亡写成主书事实。存孝不作现场活人，存信仅关系背景未定出席。')
event('kang_already_dead_when_removed','九月朔出康君立，已死',23,'894年九月庚申朔；实际死亡在此之前','马步司',
      '九月庚申初一将康君立从囚所移出时，康已死亡。',[('康君立','移出时已死者'),('李克用','此前斫囚他的军主')],quote='九月，庚申朔，出之，君立已死。',note='记录已死被发现的时间，不把庚申朔认作精确死亡日；主书未说鸩死，旧新五代史赐鸩另列。')
event('xue_zhiqin_zhaoyi_recommendation','李克用表云州刺史为昭义留后',23,'894年九月条；具体日未载','云州、昭义',
      '李克用表请云州刺史薛志诚为昭义留后；结合旧史同任接替康君立段，暂对应既有薛志勤。',[('李克用','表请者'),('薛志勤','底本作薛志诚的表请对象，姓名异文待核')],quote='克用表云州刺史薛志诚为昭义留后。',note='主书字形原样保留；旧五代史薛志勤从云州大同任接替康君立及后续通鉴昭义薛志勤相应，暂用同主体附异文，不新建重复人，不把志诚登记为已确证改名。表请仍非诏准。')
event('four_princes_enfeoffed','昭宗封祤禊禋祎四皇子为王',24,'894年冬十月丁酉','朝廷',
      '朝廷封皇子李祤为棣王、李禊为虔王、李禋为沂王、李祎为遂王。',[('李杰','以唐昭宗身份的皇子之父'),('李祤','受封棣王的皇子'),('李禊','受封虔王的皇子'),('李禋','受封沂王的皇子'),('李祎','受封遂王的皇子')],note='皇子依皇室姓展开李姓；祤与裕不同字，不因近形合成同人。未记排行、生母、年龄或始生年。')
for son,quote in [('李祤','封皇子祤为棣王'),('李禊','封皇子祤为棣王，禊为虔王'),('李禋','封皇子祤为棣王，禊为虔王，禋为沂王'),('李祎','封皇子祤为棣王，禊为虔王，禋为沂王，祎为遂王')]:
    relation('李杰',son,'父亲',24,f'唐昭宗李杰是{son}的父亲，本段称皇子。',quote=quote)

from urllib.parse import quote as urlquote
supplements=[]
specs=[('jiuwudaishi-055-894-kang-visit','旧五代史·卷55·康君立传·来谒', '旧五代史','薛居正等','resources/derived/twenty-four-histories/18旧五代史.jsonl',1310),('jiuwudaishi-055-894-kang-poison','旧五代史·卷55·康君立传·赐鸩','旧五代史','薛居正等','resources/derived/twenty-four-histories/18旧五代史.jsonl',1311),('jiuwudaishi-055-894-xue-succession','旧五代史·卷55·薛志勤传·昭义接任','旧五代史','薛居正等','resources/derived/twenty-four-histories/18旧五代史.jsonl',1312),('xinwudaishi-036-894-kang-poison','新五代史·卷36·康君立段','新五代史','欧阳修','resources/derived/twenty-four-histories/19新五代史.jsonl',653),('beimeng-suoyan-894-li-xi','北梦琐言·哭麻刘舍人事','北梦琐言','孙光宪','resources/originals/supplements/beimeng-suoyan/pg25173.txt',None)]
for sk,title,book,author,path,page in specs:
    raw=(ROOT/path).read_bytes() if page is None else next(json.loads(x)['text'].encode() for x in (ROOT/path).read_text().splitlines() if json.loads(x)['pdf_page']==page)
    url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+(f'#L{page}' if page else '#L273')
    (P/'sources'/(sk+'.txt')).write_bytes(raw)
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition=('Project Gutenberg电子转录，保留原始CRLF；本文未标分卷，未核纸本。' if page is None else '仓库PDF派生电子文本；逐字及换行保留，未核纸本。'),url=url,note=('哭麻刘舍人事，原文件第273行；不伪造该电子本未标卷号。' if page is None else f'原PDF第{page}页；仅补当前连续主线。')))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='none' if page is None else f'提取JSONL pdf_page={page}的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(table,key,field,text,n,sk,quote,citation,note,book,kind):
    assert quote in (P/'sources'/(sk+'.txt')).read_text()
    ck=f'claim_zztj_259_0894_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=citation,note=f'原文：{quote}；核对说明：{note}',status='draft'))
    supplements.append(dict(claim_key=ck,source_book=book,primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('person',people['李磎'],'aliases','《北梦琐言》哭麻刘舍人事称李相磎，同记刘崇鲁在宣制之日抱麻哭及李上表反驳，支持主书李溪与李磎为同一人。',18,'beimeng-suoyan-894-li-xi','唐李相磎，高才奧學，冠絕群彥，為朋黨所排。洎登嚴廊，似涉由徑，雖然，亦才授也。制下之日，劉舍人崇魯抱麻而哭之。李相斥其祖禰，條上其事，具表論之。','哭麻刘舍人事·原文件第273行','摘录赞语是孙光宪书中品评，与刘指控分层，不作本项目断言；该电子本未分卷，只给可回溯篇名行号。','北梦琐言','corroborates')
extra('event','event_zztj_259_0894_li_xi_ten_memorials_counterclaims','description','《北梦琐言》补记李磎作鸚鵡杯賦攻击刘氏先德受贿饮鸩，朝士对其奏表议论。',18,'beimeng-suoyan-894-li-xi','又以彭城先德受賄飲鴆，乃作《鸚鵡杯賦》，醜詞訐切，人為寒心。','哭麻刘舍人事·原文件第273行','受贿饮鸩属此篇所叙与赋的攻击内容，仍不脱离言论背景独立定罪；赋作具体日期未载，不误作戊午当天。','北梦琐言','adds')
extra('event','event_zztj_259_0894_kang_visits_keyong_jinyang','time_original','《旧五代史》康君立传记九月康至太原、宴博；《通鉴》相应宴为八月己未，时序不同。',23,'jiuwudaishi-055-894-kang-visit','九月，君立至太原，武皇会诸\n将酒博，因语及存孝事，流涕不已。','卷55·唐书·列传第七·康君立传·原PDF第1310页','旧史与主书记月并列，不能把二者各造一次同样宴会或改主书干支。','旧五代史','conflicts')
extra('event','event_zztj_259_0894_kang_already_dead_when_removed','description','《旧五代史》记康君立以一言忤意，李克用赐鸩致死；主书为斫囚后移出时已死。',23,'jiuwudaishi-055-894-kang-poison','时君立以一言忤旨，武皇赐鸩而殂，\n时年四十八。','卷55·唐书·列传第七·康君立传·原PDF第1311页','死法不同并列，不把主书暗改成鸩死；四十八为旧书卒龄，不机械反算出生年。','旧五代史','conflicts')
extra('event','event_zztj_259_0894_kang_already_dead_when_removed','description','《新五代史》同记康君立在谈李存孝时表示不以为然，李克用怒而鸩杀之。',23,'xinwudaishi-036-894-kang-poison','存\n孝已死，太祖与诸将博，语及存孝，\n流涕不已，君立以为不然，太祖怒，\n鸩杀君立。','卷36·义儿传第二十四·康君立段·原PDF第653页','新书补君立以为不然及鸩杀，但仍与主书斫囚描述并列；新旧史可能依赖，不作两份独立目击证词。','新五代史','conflicts')
extra('event','event_zztj_259_0894_xue_zhiqin_zhaoyi_recommendation','description','《旧五代史》薛志勤传称其先平王晖云州之叛，任大同军防御使，乾宁初代康君立为昭义节度使；主书作云州刺史薛志诚表为留后。',23,'jiuwudaishi-055-894-xue-succession','王晖据云州叛，讨平之，以志勤\n为大同军防御使、检校司空。乾宁\n初，代康君立为昭义节度使。','卷55·唐书·列传第七·薛志勤传·原PDF第1312页','官职与接任过程对应支持沿用薛志勤主体，但姓名志诚志勤异文仍留待校勘；表留后与旧史节度使任职阶段不同，未用旧史倒推诏任日期。','旧五代史','adds')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={17:'邀击与攻蕲未克，不补全歼或退军日期。',18:'授制、哭麻指控、改少傅、崔使沮、十表反控、停刘见任、续求诛窜分录；李溪对北梦琐言李磎，片名鄜符不造全名祖父；弟崇望长幼与两唐书相抵暂不建兄长；控词不作定罪。',19:'大破吐谷浑杀赫连擒白，不猜地点或俘后结局。',20:'七月阆攻拔与杨三人突围分开，不先记已到河东。',21:'郑自评累请致仕与徐授相分录；不推全朝反对。',22:'杨守厚卒与常再荣举绵降分录，未推死因与新官。',23:'欲逃路线乾元获、八月献斩、呈旧信、康来谒、己未宴斫囚、九月朔出已死、表薛留后分开；旧书九月来与赐鸩、新书鸩杀并列；薛志诚暂对既有薛志勤附接任书证，不确证改名；旧信自诉非产权或真实罪据。',24:'四子十月丁酉封王同事件、父亲→皇子关系有据；祤裕不误合，不猜长幼生母年龄。'}
for n in range(17,25):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17,25):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=894,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph='zztj-v259-y0894-p025',coverage='卷259乾宁元年第17—24段连续录入；本年33段尚未完。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
