"""Curate consecutive Tongjian volume 258, year 890 paragraphs 17–20."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 44))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0890-p017-p020', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias = {'赫连鐸':'赫连铎','硃崇节':'朱崇节','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0890_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·大顺元年（890）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('zhang_yang_rivalry_background','张浚与杨复恭旧隙的追叙',17,'此前；具体年未载','',
      '《通鉴》追叙张浚原依杨复恭进身，杨复恭中废后改附田令孜，后与复用的杨复恭交恶；昭宗知两人有隙而亲倚张浚。',
      [('张浚','进身及改附者'),('杨复恭','与张浚交恶者'),('田令孜','被依附者'),('唐昭宗','亲倚张浚者')],year=None,note='初与及复用为跨时追叙，不给890确年；不把阶段依附关系扩成永久主君。')
event('li_criticizes_zhang','李克用评张浚，张浚闻而衔',17,'讨黄巢及张浚作相前后；具体年日未载','河中',
      '《通鉴》追叙李克用讨黄巢屯河中时，张浚为都统判官；李克用后闻其为相，向诏使批评其虚谈无实用、会交乱天下，张浚听闻而记恨。',
      [('李克用','评论者'),('张浚','受评论及记恨者')],year=None,note='人物品评和未来祸乱说法为李克用言论；谢安裴度只是张浚自比对象，不作为事件参与者。')
event('capital_recruits_troops','张浚主张强兵，昭宗募兵京师',17,'昭宗与张浚论治乱时；具体年日未载','京师',
      '昭宗与张浚论治乱，张浚主张强兵以服天下，昭宗遂在京师广募兵，《通鉴》记至十万人。',
      [('唐昭宗','募兵者'),('张浚','强兵建议者')],year=None,note='段内跨时追叙，募兵具体年未载；至十万为书载募兵规模，不独立核实人数。')
event('court_debates_hedong','朝廷议讨河东，杜让能刘崇望反对',18,'890年五月诏令前','',
      '昭宗命三省、御史台四品以上议讨李克用，书载六七成反对，杜让能、刘崇望亦反对。张浚主张借两河藩镇之势速讨，孔纬赞同，杨复恭认为不宜再启兵端；昭宗顾念李克用兴复之功，最终从张浚孔纬议。',
      [('唐昭宗','召议及最后同意者'),('杜让能','反对者'),('刘崇望','反对者'),('张浚','主张讨伐者'),('孔纬','支持者'),('杨复恭','反对启兵者'),('李克用','被议讨者')],note='六七成为书载比例；旬月可平、馈运一二年不匮为主战者论说，不作结果预言或财政核实。')
event('li_keyong_stripped_890','朝廷削夺李克用官爵属籍',18,'890年五月','',
      '朝廷诏削夺李克用官爵、属籍。',[('李克用','被削夺者')],note='属籍依原文保存，不扩写为人物血缘身份变化。')
event('zhang_sun_han_command','张浚孙揆韩建获授河东行营职',18,'890年五月','河东行营',
      '朝廷以张浚为河东行营都招讨制置宜慰使，孙揆副之，韩建为都虞候兼供军粮料使。',
      [('张浚','统帅受任者'),('孙揆','副使受任者'),('韩建','都虞候及粮料使受任者')],note='底本官衔“宜慰”疑转录异字，保留原称不擅改；职任不等于已出师。')
event('hedong_direction_commands','朱全忠王镕李匡威赫连铎获授分面招讨职',18,'890年五月','河东南面、东面、北面',
      '朝廷以朱全忠为南面招讨使、王镕为东面招讨使、李匡威为北面招讨使、赫连铎为北面副使。',
      [('朱温','以朱全忠名义南面招讨使受任者'),('王镕','东面招讨使受任者'),('李匡威','北面招讨使受任者'),('赫连铎','北面副使受任者')],note='招讨分面是作战职分，不作为已占疆域或终身联盟。')
event('niu_hui_declines','牛徽拒任河东行营判官',18,'890年五月条；具体日未载','',
      '张浚奏请给事中牛徽为行营判官。牛徽认为国家经丧乱后不宜挑强寇、离诸侯心，以衰疾坚辞。',
      [('张浚','奏请者'),('牛徽','拒任者')],note='牛徽预言颠沛为当事人言论；本段“僧孺之孙”保留省称，未新建未核全名的祖孙关系。')
claim('person',people['牛徽'],'biography','《通鉴》附记牛徽为“僧孺之孙”。',18,quote='徽，僧孺之孙也。',note='保留史书省称，未据本段猜定额外关系。')
event('lu_anti_meng_background','安居受等召河东兵取潞州的追叙',19,'此前；具体年未载','潞州',
      '《通鉴》追叙潞人反叛孟氏，牙将安居受等召河东军取得潞州。',
      [('安居受','召河东兵者')],year=None,note='初为追叙，孟氏未细列姓名，不据族称猜定参与人。')
event('meng_qian_lu_favor','孟迁受李克用宠任，引潞将怨惧',19,'孟迁以三州归李克用后；具体日未载','潞州',
      '孟迁以邢、洺、磁归李克用后，李克用宠任其为军城都虞候，其群从获补右职，安居受等怨惧。书中又述潞人怀念李克修简俭，对李克恭不满，军心离散。',
      [('孟迁','受宠任者'),('李克用','宠任者'),('安居受','怨惧者'),('李克恭','被怨将帅'),('李克修','被怀念的前任')],note='怨惧、军心与人物评价按书载叙述；群从未具名，不推具体亲等。')
event('houyuan_troops_transferred','李克用调昭义后院将赴晋阳',19,'890年五月庚子前','潞州、晋阳',
      '李克用计划向河朔用兵，令李克恭选后院将中的骁勇者五百人赴晋阳；李克恭遣李元审、冯霸部送，潞人惜此精兵。',
      [('李克用','调兵命令者'),('李克恭','选送者'),('李元审','部送将领'),('冯霸','部送小校')],note='五百为书载人数，图河朔为计划，不记为已出征河朔。')
event('feng_ba_mutiny','冯霸铜鞮劫众叛，李元审受伤',19,'890年五月庚子前','铜鞮、沁水、潞州',
      '冯霸至铜鞮劫众叛变，沿山向南至沁水，书载众至三千；李元审进击，受冯霸所伤，返回潞州。',
      [('冯霸','叛众统领'),('李元审','出击受伤返回者')],note='劫众不推全军自愿；三千为书载规模，未绘具体行军路径。')
event('li_kegong_killed','安居受作乱焚杀李克恭李元审',19,'890年五月庚子','潞州',
      '李克恭赴李元审所住处探视，安居受率党作乱，攻击并纵火，李克恭、李元审皆死。',
      [('李克恭','被焚杀者'),('李元审','被焚杀者'),('安居受','作乱纵火者')])
event('an_jushou_liuhou','安居受被推留后归附朱全忠',19,'890年五月庚子作乱后','潞州',
      '众人推安居受为留后，归附朱全忠；安居受召冯霸，冯霸不来。',
      [('安居受','被推留后及召冯霸者'),('朱温','以朱全忠名义受归附者'),('冯霸','不应召者')],note='众推留后不作朝廷任命。')
event('an_jushou_death','安居受出走被杀，冯霸自为留后',19,'890年五月庚子条后；具体日未载','潞州及出走途中',
      '安居受害怕而出逃，为野人所杀；冯霸率军入潞州，自为留后。',
      [('安居受','出逃被杀者'),('冯霸','入城自称留后者')],note='野人未具名，不新建人物；原文未给具体杀人地点。')
event('zhu_chongjie_enters_lu','朱全忠遣朱崇节权知潞州留后',20,'890年五月后条；李克恭死后','潞州',
      '朝廷讨李克用时闻李克恭死，朝臣皆贺。朱全忠遣河阳留后朱崇节率兵入潞州，权知留后。',
      [('朱温','以朱全忠名义遣军任用者'),('朱崇节','入潞州权知留后者')],note='皆贺为书中叙述，不补个别未具名朝臣身份；权知保留代理性质。')
event('kang_li_besiege_lu','康君立李存孝围潞州',20,'890年五月后条；朱崇节入潞州后','潞州',
      '李克用遣康君立、李存孝率兵围攻潞州。',
      [('李克用','遣军者'),('康君立','围城将领'),('李存孝','围城将领')],note='此段仅记围攻，不预记潞州得失。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={17:'初与黄巢战事为追叙；比较谢安裴度不建参与；政论与募兵分录。',18:'议讨、削官、统帅分面任命、牛徽拒任分录；宜慰疑转录官衔保留；诸人理由归当事人，不作确定结果。',19:'先前潞州归附追叙、孟迁宠任及军心、调兵、铜鞮叛变、庚子焚杀、安居受与冯霸变局分录；群从不猜具体亲属。',20:'朱崇节入潞与康君立李存孝围城分录；权知不作正式诏命。'}
for n in range(17,21):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17,21):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=890,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(17,21)],next_paragraph='zztj-v258-y0890-p021',coverage='卷258大顺元年第17—20段连续录入；长段含多阶段事件，未跳段，本年未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
