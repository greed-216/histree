"""Curate consecutive Tongjian volume 258, year 891 paragraphs 1–8."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 41))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0891-p001-p008', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
people, used, reused = {}, {}, set()

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0891_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·大顺二年（891）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷258大顺二年条所见人物：{name}。',biography=None,status='draft')
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

event('zhu_defeats_wei_neihuang','朱全忠内黄击罗弘信至永定桥',1,'891年正月丙辰','内黄、永定桥',
      '罗弘信驻军内黄，朱全忠进击，《通鉴》记五战皆捷，推进至永定桥，斩首万余。',
      [('罗弘信','驻军败方'),('朱温','以朱全忠名义进击者')],note='五战与斩首万余均为书载，不独立核实。')
event('luo_zhu_peace','罗弘信求和，朱全忠止掠还俘',1,'891年正月丙辰战后','魏博、河上',
      '罗弘信遣使以厚币求和，朱全忠令停止焚掠、归还俘虏，回军河上；《通鉴》称魏博自此服于汴。',
      [('罗弘信','求和者'),('朱温','以朱全忠名义止掠还俘者')],note='服于汴为这一阶段书载政治关系，不建立终身同盟。')
event('kong_zhang_outposts','孔纬张浚罢相转外任',2,'891年正月庚申','荆南、鄂岳',
      '朝廷以孔纬为荆南节度使，以张浚为鄂岳观察使。',[('孔纬','荆南节度使受任者'),('张浚','鄂岳观察使受任者')],note='职任不等于已到地方视事。')
event('cui_xu_chancellors','崔昭纬徐彦若拜相',2,'891年正月庚申条','',
      '朝廷以翰林学士承旨、兵部侍郎崔昭纬同平章事，以御史中丞徐彦若为户部侍郎、同平章事。',
      [('崔昭纬','同平章事受任者'),('徐彦若','户部侍郎同平章事受任者')])
pk=person('崔慎由',2,'原文省称慎由，崔昭纬为其从子')
rk='relationship_person_崔昭纬_person_崔慎由_从子'
B['person_relationships'].append(dict(key=rk,person_a_key=people['崔昭纬'],person_b_key=pk,relation_type='从子',description='《通鉴》称崔昭纬为崔慎由从子；崔昭纬是崔慎由的从子，不推叔伯排行。',status='draft'))
claim('person_relationship',rk,'description','崔昭纬是崔慎由的从子。',2,quote='昭纬，慎由从子',note='慎由为崔氏省称补姓；保留从子术语，不擅改为具体叔父伯父。')
pk=person('徐商',2,'原文省称商，徐彦若之父')
rk='relationship_person_徐商_person_徐彦若_父亲'
B['person_relationships'].append(dict(key=rk,person_a_key=pk,person_b_key=people['徐彦若'],relation_type='父亲',description='《通鉴》称徐彦若为商之子；徐商是徐彦若的父亲。',status='draft'))
claim('person_relationship',rk,'description','徐商是徐彦若的父亲。',2,quote='彦若，商之子也。',note='商按徐氏省称补姓；对照旧唐书卷179徐彦若传父商记载，未核纸本。')
event('yang_robs_kong','杨复恭使人劫孔纬长乐坡',2,'891年正月庚申条后','长乐坡',
      '杨复恭遣人劫孔纬，斩其旌节，夺尽资装，孔纬仅自脱免。',[('杨复恭','遣人劫掠者'),('孔纬','被劫者')],note='未具名劫者不建人物，孔纬脱免不记遇害。')
event('li_petitions_against_zhang','李克用再上表指责张浚',2,'891年正月条；具体日未载','',
      '李克用遣使再上表，指责张浚求一时之功、与朱温连结，称自己无官爵、不敢归藩方，欲寄寓河中待命。',
      [('李克用','上表者'),('张浚','被指责者'),('朱温','奏表所指连结对象')],note='指责与寄寓计划为奏表言论，不据此断言已到河中或建立永久同盟。')
event('kong_zhang_relegated_li_restored','孔纬张浚再贬，李克用复官爵',2,'891年正月条；再奏后','均州、连州、晋阳',
      '朝廷再贬孔纬为均州刺史、张浚为连州刺史，恢复李克用全部官爵，令其归晋阳。',
      [('孔纬','再贬者'),('张浚','再贬者'),('李克用','恢复官爵者')],note='令归是诏命，不补抵达晋阳的确日。')
event('sun_ru_moves_south','孙儒尽举淮蔡军渡江南攻',2,'891年正月癸酉条','江、润州以南',
      '孙儒尽举淮、蔡军渡江，自润州转战向南，田頵、安仁义屡败退，杨行密所属城戍相继奔溃。',
      [('孙儒','渡江南攻者'),('田頵','败退将领'),('安仁义','败退将领'),('杨行密','城戍所属主将')],note='尽举及望风奔溃为书载叙述，不补未载具体人数与每城失陷日期。')
event('tai_meng_checks_li_congli','台濛传呼疑兵退李从立',2,'891年正月癸酉条后','宣州东溪、溪西',
      '李从立突然到宣州东溪，杨行密守备未固，夜遣合肥台濛驻溪西。台濛令士卒往返传呼，李从立以为大军续至，撤离。',
      [('李从立','被疑兵退去者'),('杨行密','遣防守者'),('台濛','传呼疑兵将领')],note='五百为书载军数；以为援军到是李从立判断，不记为真有大军续到。')
event('li_shenfu_night_raid','李神福溧水佯退夜袭孙儒军',2,'891年正月条；具体日未载','溧水',
      '孙儒前军至溧水，杨行密遣李神福抵抗；李神福佯退示怯，敌军不设防，夜率精兵袭击，书载俘斩千人。',
      [('孙儒','前军所属主将'),('杨行密','遣将者'),('李神福','佯退夜袭将领')],note='俘斩为合计，不能改作全部阵亡；千人为书载。')
event('li_keyong_hanzhi_restored','李克用加守中书令，李罕之复官爵',3,'891年二月','',
      '朝廷加李克用守中书令，恢复李罕之官爵。',[('李克用','加官者'),('李罕之','复官爵者')])
event('zhang_xiuzhou_demoted','张浚再贬绣州司户',3,'891年二月','绣州',
      '朝廷再次贬张浚为绣州司户。',[('张浚','再贬者')],note='贬职不等于已到绣州。')
event('sichuan_siege_background','韦昭度讨西川三年未克，朝议息兵',4,'讨西川以来三年；逐事确年未载','西川',
      '《通鉴》述韦昭度统诸道军讨陈敬瑄，三年未能攻克，馈运不继，朝议欲停战。',
      [('韦昭度','围讨统帅'),('陈敬瑄','被围讨者')],year=None,note='十余万为书载兵数，三年为背景时长，不反推精确出兵日期。')
event('chen_restored_wang_gu_ordered_home','陈敬瑄复官爵，顾彦朗王建奉令归镇',4,'891年三月乙亥','西川及原镇',
      '朝廷恢复陈敬瑄官爵，命顾彦朗、王建各率军归镇。',[('陈敬瑄','恢复官爵者'),('顾彦朗','被令归镇者'),('王建','被令归镇者')],note='命归不记已经执行。')
event('lu_hong_turns_against_wang','卢弘受命攻棣州却回攻王师范',5,'891年三月后条；具体日未载','棣州、平卢',
      '王师范遣都指挥使卢弘攻棣州张蟾，卢弘却率军返回攻王师范；王师范以重赂迎接，表示愿让位保全性命，卢弘因其年少而不防备。',
      [('王师范','遣将及佯让者'),('卢弘','转攻及受骗者'),('张蟾','原讨伐对象')],note='底本弘击攻、师池疑转录，按同段主语王师范复用，不另建师池人物；让位为诱敌言辞，不写已让位。')
event('liu_xun_kills_lu_hong','王师范设宴，刘鄩杀卢弘',5,'891年三月后条；卢弘入城后','平卢城中',
      '王师范密令安丘小校刘鄩杀卢弘，卢弘入城后，王师范伏甲设宴，刘鄩在座上杀卢弘及其党数人。',
      [('王师范','设伏者'),('刘鄩','宴中杀将者'),('卢弘','被杀者')],note='党人未具名，不建人物；具体城名未直书，不猜现代坐标。')
event('wang_takes_dizhou','王师范攻棣州斩张蟾，崔安潜归京',5,'891年三月后条；卢弘死后','棣州、京师',
      '王师范慰谕赏赐士卒，亲率攻棣州，拘执张蟾并斩之；崔安潜逃归京师。',
      [('王师范','统军攻杀者'),('张蟾','被执斩者'),('崔安潜','逃归者')])
event('wang_pinglu_confirmed','王师范获平卢节度使，刘鄩获副职',5,'891年三月后条；平卢争位结束后','平卢',
      '王师范任刘鄩为马步副都指挥使，朝廷诏以王师范为平卢节度使。',
      [('王师范','任副将及获朝廷授职者'),('刘鄩','副都指挥使受任者')],note='本次朝廷诏授与889年军中推留后分为不同事件。')
event('wang_respects_county_magistrates','王师范拜本县令的书载逸事',5,'本县令到任时；具体年日未载','本县',
      '《通鉴》述王师范每逢本县令到官，备仪卫谒见，自称百姓王师范拜于庭；僚佐劝谏时解释为敬桑梓、教子孙不忘本。',
      [('王师范','敬县令及解释者')],year=None,note='和谨好学为书中评价，县令与子孙无姓名，不建额外人物；不强定891年。')
event('zhang_kong_asylum_hua','张浚孔纬依韩建，朱全忠代诉获自便',6,'891年三月后条；具体日未载','蓝田、华州、商州',
      '张浚至蓝田后逃依华州韩建，与孔纬密向朱全忠求救。朱全忠为二人上表申冤，朝廷允其自便；孔纬至商州而返，亦寓华州。',
      [('张浚','逃依求救者'),('韩建','收依对象'),('孔纬','求救及寓居者'),('朱温','以朱全忠名义代诉者')],note='代诉内容为奏请，不推朝廷已经恢复两人原官。')
event('an_zhijian_replaced','安知建通汴，李克用表李存孝代任',7,'891年三月后条；具体日未载','邢洺、青州',
      '邢洺节度使安知建秘密联系朱全忠，李克用上表请李存孝代之，安知建害怕逃至青州，朝廷任其为神武统军。',
      [('安知建','通汴逃走及受任者'),('朱温','以朱全忠名义秘密联系对象'),('李克用','表请换帅者'),('李存孝','被表请代任者')],note='安知建与已死的安金俊不是同名，不合并；表请李存孝不单写成朝廷已授。')
event('zhu_xuan_kills_an','朱瑄伏杀赴京安知建，传首晋阳',7,'891年三月后条；神武统军任命后','郓州、河上、晋阳',
      '安知建率部欲赴京师，途经郓州；朱瑄与李克用正友好，在河上伏杀安知建，将首级送晋阳。',
      [('安知建','赴京被杀者'),('朱瑄','伏杀者'),('李克用','传首晋阳所指对象')],note='三千为书载部众，方睦为阶段关系，不建终身同盟。')
event('comet_santai','彗星见三台东入太微',8,'891年四月','三台、太微',
      '《通鉴》记彗星出现于三台，向东进入太微，长十丈余。',note='天象及长度按史书记录，不把星区作为地理落点，不换算现代物理量或推吉凶因果。')
event('amnesty_891_04','朝廷四月甲申赦天下',8,'891年四月甲申','',
      '朝廷赦天下。',note='与同段天象并列记载，不建立彗星导致赦令的因果边。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={1:'军数杀获为书载，服汴为阶段关系。',2:'庚申外任与拜相、劫孔、李克用再奏及复官、孙儒南攻与台濛李神福战斗分录；从子方向由崔昭纬指崔慎由；徐商父亲方向。',3:'加官复爵与张浚再贬分录，不推已到贬所。',4:'三年为背景时长未反算；三月乙亥复爵和命归不推已执行。',5:'弘击攻师池疑转录按王师范同段归人；反攻、宴杀、攻棣、正式授职与县令礼遇逸事分录。',6:'代诉获自便不写成恢复原官。',7:'安知建与安金俊区分；秘密联系和表请不推终身盟友。',8:'天象为书载，不标地图，不推赦令因果。'}
for n in range(1,9):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=891,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph='zztj-v258-y0891-p009',coverage='卷258大顺二年第1—8段连续录入；本年40段尚未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
