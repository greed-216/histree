"""Curate consecutive Tongjian volume 258, year 891 paragraphs 17–24."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 41))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0891-p017-p024', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-258-891'
B['sources'] = [dict(key=source,title='资治通鉴·卷258',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/4d35696319726b523bd624f2370cb2cf7faa6b43/resources/derived/tongjian/258.txt',note='卷258大顺二年条；书、卷、年、段落及行号见批次账本。')]
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
alias['郑渥']='王宗渥'
alias['李简']='李简（杨行密将）'

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0891_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·大顺二年（891）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['王瓌'] if name=='王瑰' else ['张打胸'] if name=='张勍' else ['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷258大顺二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=891,note=None,quote=None):
    key='event_zztj_258_0891_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_258_0891_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

supplements=[]
SUP={}
for sk,title,author,file,book in [
 ('shiguochunqiu-039-891-names','十国春秋·卷39·姓名摘录','吴任臣','shiguochunqiu/039-name-excerpts.txt','十国春秋'),
 ('jiutangshu-184-891-wang-gui','旧唐书·卷184·杨复恭传摘录','刘昫等','jiutangshu/184-wang-gui-excerpt.txt','旧唐书'),
 ('tongjian-258-891-husansheng-variants','资治通鉴（胡三省音注）·卷258·姓名异文摘录','司马光等，胡三省注','tongjian/258-husansheng-891-variants.txt','资治通鉴')]:
    url='https://github.com/greed-216/histree/blob/db866478918e5e21427833c05c03d135d51cfe38/resources/derived/'+file
    data=(ROOT/'resources/derived'/file).read_bytes();local=sk+'.txt';(P/'sources'/local).write_bytes(data)
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='维基文库电子文本逐字摘录，保留字形与括注；未核纸本，不是整卷快照。',url=url,note='原网页与摘录方式见仓库 resources/derived/891-name-excerpts-manifest.json。'))
    SUP[sk]=(data.decode(),book)
    mf=json.loads((P/'sources/manifest.json').read_text());meta=next(x for x in json.loads((ROOT/'resources/derived/891-name-excerpts-manifest.json').read_text()) if x['file']=='resources/derived/'+file)
    mf.append(dict(key=sk,file=local,sha256=hashlib.sha256(data).hexdigest(),url=url,upstream=meta['upstream'],transformation=meta['transformation']))
    (P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def supplement(table,key,field,value,n,sk,quote,citation,note,relation='adds'):
    assert quote in SUP[sk][0]
    ck=f'claim_zztj_258_0891_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=value,source_key=sk,citation=citation,note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,primary_paragraph_id=Q[n]['id'],subject_key=key,source_book=SUP[sk][1],relation=relation))
def relation(a,b,t,n,description,reuse=False):
    ka,kb=people[a],people[b];key=f'relationship_{ka}_{kb}_{t}'
    if reuse:
        rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['key']==key]
        assert rows and all(r==rows[0] for r in rows);row=dict(rows[0]);reused.add(key)
    else:row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row)
    return key

event('zhu_yang_joint_plan','朱全忠约杨行密共攻孙儒',17,'891年七月后条；具体日未载','',
      '朱全忠遣使与杨行密约共攻孙儒。孙儒欲先灭杨行密、后敌朱全忠，向藩镇移牒指责二人，声称平宣汴后将入朝除君侧之恶。',
      [('朱温','以朱全忠名义约攻者'),('杨行密','约攻对象'),('孙儒','谋分次攻击及移牒者')],note='约攻是本次军议；孙儒计划与移牒声称不当作已执行，不记终身同盟。')
event('sun_ru_destroys_yangzhou','孙儒焚扬州，驱民渡江杀老弱',17,'891年七月后条；具体日未载','扬州、江',
      '孙儒焚尽扬州庐舍，驱丁壮与妇女渡江，并杀老弱以充食。',[('孙儒','焚城驱民及杀食者')],note='为书载惨状，不补未载伤亡人数或现代界定。')
event('zhang_li_relieve_yangzhou','张训李德诚入扬州灭火发谷赈饥',17,'891年七月后条；孙儒焚扬州后','扬州',
      '杨行密将张训、李德诚潜入扬州，灭余火，获得谷数十万斛以赈饥民。',[('张训','潜入灭火赈饥将领'),('李德诚','潜入灭火赈饥将领'),('杨行密','两将所从主将')],note='数十万斛为书载，不換算现代重量。')
event('zhang_jian_grain','张谏借谷给军，张训奉命馈还',17,'891年七月后条；具体日未载','泗州、扬州',
      '泗州刺史张谏借数万斛谷给军，张训奉杨行密之命馈给张谏，张谏由此感德杨行密。',
      [('张谏','借谷及受馈者'),('张训','奉命馈谷者'),('杨行密','命馈者')],note='贷与馈依书载表述，不推定长期从属或另造未载还粮数额。')
event('li_cunxiao_urges_zhen','李存孝劝李克用攻镇州',18,'891年七月后条；八月南巡前','镇州',
      '邢洺节度使李存孝劝李克用攻镇州，李克用采纳。',[('李存孝','劝攻者'),('李克用','采纳者')],note='谋议不写成已经攻克镇州；本段以邢洺节度使称李存孝，可与此前表请任职区别。')
event('li_southern_tour','李克用八月巡泽潞涉怀孟',18,'891年八月','泽潞、怀孟',
      '李克用南巡泽潞，进入怀孟境内。',[('李克用','南巡者')],note='涉境不直接写作攻陷怀孟。')
event('ding_hui_su_outer','丁会攻克宿州外城',19,'891年八月条；具体日未载','宿州',
      '朱全忠遣丁会攻宿州，克其外城。',[('朱温','以朱全忠名义遣将者'),('丁会','攻外城者')],note='只克外城，不写已全取宿州。')
event('li_jian_rescues_yang','李简广德力战救出杨行密',20,'891年八月乙未','苏州、广德',
      '孙儒由苏州出屯广德，杨行密率军抵抗而营寨被围。上蔡李简率百余人力战破围，救出杨行密。',
      [('孙儒','出屯围寨者'),('杨行密','抵抗被围者'),('李简','破围救出主将者')],note='百余人为书载；原文破寨拔出不写攻占孙儒全军营寨。李简为杨行密将、上蔡人，采用消歧名称；与本年王建部下同名李简另建人物，不因同名合并。')
claim('person',people['李简（杨行密将）'],'biography','李简为上蔡人。',20,quote='行密将上蔡李简',note='上蔡为籍贯，不标为战斗地点。')
event('chengdu_supply_cut','王建占新都断陈敬瑄彭州粮道',21,'891年八月条；成都受降前','成都、新都、彭州',
      '王建加紧攻陈敬瑄，陈出战多败、所辖州县多被取。威戎节度使杨晟时常送粮，王建以兵据新都，使彭州道路断绝；陈敬瑄慰勉士卒无人回应。',
      [('王建','围攻断道者'),('陈敬瑄','受围者'),('杨晟','馈食者')],note='巡内州县率被取不作每一县均已攻陷，缺确日不補。')
event('tian_surrenders_seal','田令孜携西川印节授王建',21,'891年八月辛丑夜','成都城、王建营',
      '田令孜登城与王建对话，王建称未忘父子恩但奉朝廷命讨不受代者。当夜田令孜携西川印节至王建营授之，王建谢并请恢复父子关系如初。',
      [('田令孜','携印交授者'),('王建','接印及请复父子者')],note='父子为既有假父子关系，不作亲生；携印不等于朝廷任命已下。')
rk=relation('田令孜','王建','假父',21,'',reuse=True)
claim('person_relationship',rk,'description','本段王建称父子之恩，请与田令孜复为父子如初。',21,quote='建泣谢，请复为父子如初。',note='复用884年假父关系key及原描述，只补891年独立引文，不新建重复关系。')
event('wang_loot_promise','王建围城前许将士取财轮任节度使',21,'先是；成都受降前，确年日未载','成都城外',
      '《通鉴》追述王建曾许将士得成都后恣取金帛子女，并轮日任节度使。',[('王建','许诺者')],year=None,note='先是为追叙，确年留空；许诺不写成轮任已实际实行。')
event('zhang_qing_polices_chengdu','陈敬瑄开城，张勍先入禁止焚掠',21,'891年八月壬寅及其后','成都',
      '陈敬瑄开城迎王建，王建任张勍为马步斩斫使使先入，告诫将士不得焚掠坊市。张勍捕百余犯令士卒，捶胸杀之，众遂不敢犯，时人称张打胸。',
      [('陈敬瑄','开城者'),('王建','任将禁掠者'),('张勍','先入执法将领')],note='底本不富忠疑为不富贵，快照保留，叙述仅用明确禁掠旨意；百余为书载，处刑不能美化作无人伤亡。')
claim('person',people['张勍'],'aliases','张勍被时人称张打胸。',21,quote='故时人谓勍为“张打胸”。',note='绰号作别名，不另建人物。')
event('wang_enters_chengdu','王建入成都自称西川留后',21,'891年八月癸卯','成都',
      '王建进入成都，自称西川留后。',[('王建','自称留后者')],note='自称区别于后续朝廷正式授职，不提前写西川节度使诏授。')
event('han_wu_assassinated','韩武引轮任许诺抗议，被王建刺杀',21,'891年八月癸卯后条；具体日未载','成都使厅',
      '小校韩武屡在使厅上马，牙司阻止，韩武以王建曾许轮任节度使反驳，王建暗遣人刺杀韩武。',[('韩武','抗议被杀者'),('王建','密遣刺杀者')],note='牙司与刺客未具名不建人物；数为屡次，不补具体次数。')
event('tian_controls_chen_background','田令孜取得陈敬瑄军政的追叙',22,'初；陈敬瑄拒朝命时，确年日未载','西川',
      '《通鉴》追述陈敬瑄拒朝命时，田令孜建议代掌军务、每日咨呈，陈敬瑄同意，此后军政不由己。',[('陈敬瑄','交军政者'),('田令孜','代掌军政者')],year=None,note='底本田信孜疑转录，按同段人物及胡注本田令孜复用；初为追叙，不强定891年。')
event('chen_tao_yazhou','王建表陈陶为雅州刺史，陈敬瑄随行',22,'891年成都平后；具体日未载','雅州',
      '王建上表请陈敬瑄之子陈陶为雅州刺史，使陈敬瑄随陈陶赴任。',[('王建','表请与安排者'),('陈陶','被表请刺史者'),('陈敬瑄','随子赴任者')],note='陶按父姓补陈；上表不另推朝廷诏授。')
rk=relation('陈敬瑄','陈陶','父亲',22,'《通鉴》称陈陶为陈敬瑄之子；陈敬瑄是陈陶的父亲。')
claim('person_relationship',rk,'description','陈敬瑄是陈陶的父亲。',22,quote='建表敬瑄子陶为雅州刺史',note='沿父姓补全陈陶，父亲方向由陈敬瑄指陈陶。')
event('chen_returns_xinjin','陈敬瑄次年罢归，寓居新津',22,'明年；892年，具体日未载','新津',
      '《通鉴》在成都平后段预叙次年陈敬瑄罢归、寓居新津，王建以一县租赋赡养。',[('陈敬瑄','罢归寓居者'),('王建','租赋赡养者')],year=892,note='明年依当前891年段承接记892年；这是本段预叙，不将892年账本标为已处理。')
event('wang_renames_generals','王建分军就食诸州，改文武坚谢从本姓名',23,'891年八月癸丑','西川诸州',
      '王建分遣士卒到诸州就食，将文武坚、谢从本分别更名。底本记王完阮、王宗本；胡注本与《十国春秋》文武坚传记前者为王宗阮。陈敬瑄将佐中有才干者，王建礼待任用。',
      [('王建','遣军改名任用者'),('文武坚','改姓名者，异本为王宗阮'),('谢从本','改名王宗本者')],note='王完阮与王宗阮存在底本字差，以独立出处并列；沿用文武坚、谢从本稳定key，不重建改名人物。')
claim('person',people['文武坚'],'aliases','底本记文武坚更姓名为王完阮；其他电子版本记王宗阮。',23,quote='更文武坚姓名曰王完阮',note='原文字差保留，不单靠底本把王完阮当作无疑的正常别名。')
claim('person',people['谢从本'],'aliases','谢从本更姓名为王宗本。',23,quote='谢从本曰王宗本。',note='省承更姓名；复用谢从本key，公开别名另以证据合并，不改旧批次。')
sk='shiguochunqiu-039-891-names'
supplement('person',people['文武坚'],'aliases','《十国春秋》称王宗阮本为文武坚，并记成都平后更姓名。',23,sk,'王宗阮，本僰道土豪文武堅也。','卷39·王宗阮传·姓名摘录第5行','与底本王完阮字形有异；仅用于对应当前改名段，不提前录其后履历。','conflicts')
supplement('person',people['谢从本'],'aliases','《十国春秋》称王宗本本姓谢名从本。',23,sk,'王宗本，本姓謝，名從本','卷39·王宗本传·姓名摘录第3行','与通鉴改名相印证；清代汇编史书，不当作独立同时代见证。','corroborates')
rk=relation('王建','谢从本','养父',23,'《十国春秋》记成都平后王建养谢从本为子并改名王宗本；王建是谢从本的养父。')
supplement('person_relationship',rk,'description','成都平后，王建养谢从本为子，改姓名为王宗本。',23,sk,'及敬瑄平，養以爲子，改姓名曰王宗本。','卷39·王宗本传·姓名摘录第3行','高祖为前蜀王建，通鉴主段仅记改名；补证养子身份，关系方向为王建养父→谢从本。')
sk='tongjian-258-891-husansheng-variants'
supplement('person',people['文武坚'],'aliases','胡注本记文武坚更姓名为王宗阮。',23,sk,'更文武堅姓名曰王宗阮','卷258·大顺二年·改名段·摘录第5行','底本王完阮与本电子版本王宗阮并列，不改原始快照。','conflicts')
supplement('event','event_zztj_258_0891_tian_controls_chen_background','description','胡注本在军政转交追叙中记田令孜。',22,sk,'田令孜欲盜其軍政','卷258·大顺二年·军政追叙·摘录第3行','底本田信孜为疑字，按本版本与上下文归田令孜；不另建田信孜人物。','conflicts')
event('yang_fugong_guards_background','杨复恭专掌禁兵，假子牧守拒贡',24,'九月致仕前的背景；确年日未载','京师、龙剑、武定',
      '《通鉴》述杨复恭总宿卫兵、专制朝政，诸假子任节度使刺史，另养宦官子六百人任监军。龙剑节度使杨守贞、武定节度使杨守忠不输贡赋并上表讥薄朝廷；胡注本相同位置记守思。',
      [('杨复恭','掌禁兵及养子牧守者'),('杨守贞','龙剑节度使拒贡者'),('杨守忠','底本记武定节度使拒贡者')],year=None,note='六百为书载；九月前背景不强定养子、拒贡确年。武定守忠与胡注本守思为记名差异，不把守思加入别名或另断同人。')
for name in ['杨守贞','杨守忠']:
 rk=relation('杨复恭',name,'假父',24,f'《通鉴》本电子底本记{name}为杨复恭假子；杨复恭是假父。'+('武定节度使名另本作守思，身份记名尚待校核。' if name=='杨守忠' else ''))
 claim('person_relationship',rk,'description',f'本电子底本记杨复恭是{name}的假父。',24,quote='假子龙剑节度使守贞、武定节度使守忠',note='据本段省承杨氏；武定名异文守思需并列，不以养子推亲生。')
supplement('event','event_zztj_258_0891_yang_fugong_guards_background','description','胡注本武定节度使记名守思，底本作守忠。',24,sk,'假子龍劍節度使守貞、武定節度使守思不輸貢賦，上表訕薄朝廷。','卷258·大顺二年·假子拒贡段·摘录第7行','只记录对应位置名字异文；未核纸本，不断定谁为真，也不自动合并杨守忠与守思。','conflicts')
event('wang_gui_appointment','皇舅王瑰求节度，与杨复恭争执后外任',24,'九月杨复恭致仕前；确年日未载','禁中、黔南',
      '皇舅瑰求节度使，皇帝询杨复恭而被否，瑰怒斥之。其出入禁中任事，杨复恭厌恶，上奏任其黔南节度使；《旧唐书》此人记王瑰，胡注本记王瓌。',
      [('王瑰','求职争执及外任者'),('杨复恭','否议及奏外任者'),('李杰','以唐昭宗身份询问者')],year=None,note='底本省姓，以旧唐书与胡注本补王氏；黔南节度辖区不明，不标现代坐标。')
rk=relation('王瑰','李杰','舅父',24,'《通鉴》称瑰为皇帝舅，《旧唐书》记国舅王瑰；王瑰是唐昭宗李杰的舅父。')
claim('person_relationship',rk,'description','王瑰是唐昭宗李杰的舅父。',24,quote='上舅瑰求节度使',note='上为当时唐昭宗，复用李杰key；姓王另有旧唐书补证。')
event('wang_gui_drowned','王瑰吉柏津覆舟死亡，两书记述不同',24,'九月杨复恭致仕前；确年日未载','吉柏津',
      '《通鉴》记杨复恭令杨守亮将皇舅瑰覆于江中，宗族宾客皆死，按船毁上报，皇帝深恨；《旧唐书》只记覆舟而没及舆论归咎杨复恭，责任说法并列保留。',
      [('杨复恭','通鉴记密令者'),('杨守亮','通鉴记执行者'),('王瑰','覆舟死者'),('李杰','以唐昭宗身份怀恨者')],year=None,note='两书责任断言强度有别，不以旧唐书物议证明独立确认谋杀；未载确年不定891。')
supplement('person',people['王瑰'],'name','《旧唐书》杨复恭传记国舅王瑰。',24,'jiutangshu-184-891-wang-gui','國舅王瑰，頗居中任事','卷184·杨复恭传·王瑰段·摘录第3行','补主底本省称瑰之姓；与李克用部下判官同名者不得混同。')
supplement('person',people['王瑰'],'aliases','胡注本相同皇舅事记王瓌。',24,sk,'上舅王瓌求節度使','卷258·大顺二年·皇舅段·摘录第9行','王瑰与王瓌为相同皇舅求职及覆舟条的记名字形，用作异体检索。')
supplement('event','event_zztj_258_0891_wang_gui_drowned','description','《旧唐书》记王瑰覆舟没，物议归咎杨复恭。',24,'jiutangshu-184-891-wang-gui','至吉柏江，覆舟而沒，物議歸咎於復恭，上每切齒道復恭。','卷184·杨复恭传·王瑰段·摘录第3行','旧唐书是舆论归责，通鉴是明载密令，保留差别；吉柏江与津名不画成精确地理同点。','conflicts')
event('yang_shouli_accuses_fugong','李顺节告杨复恭阴事，复恭拒赴凤翔',24,'九月乙卯致仕前；具体日未载','京师、凤翔',
      '李顺节与杨复恭争权，将复恭隐事尽告皇帝；朝廷出复恭为凤翔监军，复恭愠怒不肯前往，称病求致仕。',
      [('杨守立','以李顺节名义告事争权者'),('杨复恭','拒赴任求致仕者'),('李杰','以唐昭宗身份外任复恭者')],note='复用李顺节为杨守立的既证别名；告事不判每项指控属实；明确未赴任。')
event('yang_fugong_retires_kills_envoy','杨复恭致仕后遣张绾杀使者',24,'891年九月乙卯及其后','京师',
      '朝廷以杨复恭为上将军致仕，赐几杖。使者送诏后返，杨复恭暗遣腹心张绾刺杀使者。',[('杨复恭','致仕及遣刺者'),('张绾','被遣刺杀者')],note='使者未具名不建人物；返程刺杀无独立干支，不将所有动作强定乙卯。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={17:'约攻和孙儒计划分明；焚城驱民杀食、两将灭火赈饥、张谏借粮馈粮逐事分录。',18:'劝攻与八月南巡分录，涉境不作已攻陷。',19:'仅宿州外城克，未先记内城降。',20:'百余为书载，李简救杨行密不补其他战果。',21:'受降三个干支依序，先是许诺确年未定；不富忠疑转录；张勍绰号独引；假父复用原关系。',22:'初为追叙；田信孜另本田令孜；陈陶随父姓；明年罢归明标892不推进892账本。',23:'王完阮异本王宗阮，谢从本王宗本同人key；旧名补别名；十国春秋仅补本段身份，不提前选其后来事件。',24:'杨复恭掌权背景年份留空；武定名守忠/守思并列；王瑰补姓，王瓌异体；覆舟责任叙述差别留存；九月致仕与刺使分辨日期。'}
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
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=891,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph='zztj-v258-y0891-p025',coverage='卷258大顺二年第17—24段连续录入；本年40段尚未完。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
