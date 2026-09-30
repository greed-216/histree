"""Curate consecutive Tongjian volume 259, year 892 paragraphs 1–8."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 47))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0892-p001-p008', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-892'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259景福元年条；书、卷、年、段落及行号见批次账本。')]
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
people, used, reused = {}, {}, set()
alias.update({'郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0892_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·景福元年（892）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259景福元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=892,note=None,quote=None):
    key='event_zztj_259_0892_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0892_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('amnesty_change_era','朝廷赦天下改元景福',1,'892年春正月丙寅','',
      '朝廷赦天下，改元景福。',note='元年年首与卷259标题承接确定892年，不换算干支日。')
event('five_commanders_seek_campaign','李茂贞等五帅请讨诸杨，朝廷令和解',2,'892年正月条；具体日未载','凤翔、静难、镇国、同州、秦州、山南',
      '李茂贞、王行瑜、韩建、王行约、李茂庄五节度使上言杨守亮容匿杨复恭，请出军讨之，并求授李茂贞山南西道招讨使。朝议恐李茂贞得山南难制，下诏和解，五帅不听。',
      [('李茂贞','联奏请讨及求任者'),('王行瑜','联奏者'),('韩建','联奏者'),('王行约','联奏者'),('李茂庄','联奏者'),('杨守亮','被奏指容匿者'),('杨复恭','被奏指叛臣者')],note='叛臣为奏表称谓；底本诏讨使疑招讨使，按同年下文招讨复用职称，快照不改；下令和解不记已执行。')
event('li_sixun_defeats_yaoshan','李嗣勋尧山击败幽镇联军',3,'892年正月条；具体日未载','尧山',
      '王镕、李匡威合兵十余万攻尧山，李克用遣李嗣勋迎击，大破幽州镇州军，书载斩获三万。',
      [('王镕','攻尧山一方'),('李匡威','攻尧山一方'),('李克用','遣将者'),('李嗣勋','获胜将领')],note='十余万为军数，三万为斩获书载，不全部改作死亡；李嗣勋与李嗣昭等名字相近者不合并。')
event('yang_tactics_against_sun','刘威李神福劝坚壁，戴友规劝遣民归淮',4,'892年正月条；具体日未载','铜官、淮南',
      '杨行密称孙儒兵十倍、自己多次不利，询是否退保铜官。刘威、李神福劝据险坚壁清野、抄粮饷；戴友规劝护送淮南士民归乡复业，使敌军思归。杨行密欣然采纳。',
      [('杨行密','问策采纳者'),('刘威','献坚壁清野策者'),('李神福','献坚壁清野策者'),('戴友规','献护民归乡策者'),('孙儒','被谋对付对象')],note='十倍为杨行密言论，不确证兵力统计；采用战术不补具体执行日，也不提前记孙儒被擒。')
claim('person',people['戴友规'],'biography','戴友规为庐州人。',4,quote='友规，庐州人也。',note='籍贯不作当时军议发生地点。')
event('yang_sheng_allies_against_wang','杨晟约杨守亮等攻王建',5,'892年二月丁丑前','威戎、山南、西川',
      '杨晟与杨守亮等约定攻击王建。',[('杨晟','约攻者'),('杨守亮','约攻对象'),('王建','被谋攻击对象')],note='本次约攻不作永久同盟。')
event('lu_yao_defeated_killed','杨晟掠新繁汉州，李简击斩吕尧',5,'892年二月丁丑及其后','新繁、汉州、梓州',
      '杨晟出军掠新繁汉州，遣吕尧率二千人会杨守厚攻梓州。王建遣行营都指挥使李简迎击吕尧，斩之。',
      [('杨晟','出掠遣将者'),('吕尧','率军被斩者'),('杨守厚','会攻对象'),('王建','遣迎击者'),('李简','以王建将身份击斩者')],note='李简复用王建将的消歧key；二千为部兵书载，不记全部战死；击斩地点未直书，不将所列多地标为确点。')
event('zhu_youyu_doumen','朱全忠击朱瑄，遣朱友裕军斗门',6,'892年二月戊寅','斗门',
      '朱全忠出兵击朱瑄，遣其子朱友裕领兵先行，驻斗门。',[('朱温','以朱全忠名义出兵遣子者'),('朱瑄','被攻目标'),('朱友裕','前行驻军者')],note='本段首次明言友裕为朱全忠之子，关系另录；出击不推已胜。')
rk=f'relationship_{people["朱温"]}_{people["朱友裕"]}_父亲'
rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==people['朱温'] and r['person_b_key']==people['朱友裕'] and r['relation_type']=='父亲']
if rows:
    assert all(r==rows[0] for r in rows);row=dict(rows[0]);rk=row['key'];reused.add(rk)
else:row=dict(key=rk,person_a_key=people['朱温'],person_b_key=people['朱友裕'],relation_type='父亲',description='《通鉴》称朱友裕为朱全忠之子；朱温（朱全忠）是朱友裕的父亲。',status='draft')
B['person_relationships'].append(row)
claim('person_relationship',rk,'description','朱温（朱全忠）是朱友裕的父亲。',6,quote='硃全忠出兵击硃瑄，遣其子友裕将兵前行',note='父亲角色由朱温指朱友裕；查全站既有关系后复用，反向阅读不另建儿子边。')
event('li_maozhen_unauthorized_attack','李茂贞王行瑜擅击兴元并凌朝廷',7,'892年二月条；具体日未载','兴元',
      '李茂贞与王行瑜未经诏命举兵攻兴元，李茂贞不断表求招讨使，又给杜让能、西门君遂写信凌蔑朝廷。',
      [('李茂贞','擅攻求任者'),('王行瑜','擅攻者'),('杜让能','受书者'),('西门君遂','受书者')],note='陵蔑为书中措辞；未列书信全文，不补具体辱词。')
event('niu_hui_debates_campaign','牛徽请授招讨以约束，朝廷任李茂贞',7,'892年二月条；延英议后','延英、山南西道',
      '皇帝召宰相谏官议李茂贞，众不敢言。牛徽称其不应不待诏命，又称军过山南伤民甚多，建议授招讨以国法约束。皇帝采纳，任李茂贞山南西道招讨使。',
      [('李杰','以唐昭宗身份召议采纳者'),('牛徽','献议者'),('李茂贞','受任者')],note='前朝护卫功、疾恶与杀伤系牛徽议论，未独立统计；具名宰相不必都自动挂本场参与边；未知宦官不补名。')
event('zhu_xuan_seizes_doumen','朱瑄袭斗门，朱友裕弃营逃',8,'892年二月甲申','卫南、斗门',
      '朱全忠至卫南时，朱瑄率步骑万人袭斗门，朱友裕弃营逃走，朱瑄占其营。',[('朱温','以朱全忠名义至卫南者'),('朱瑄','袭营占营者'),('朱友裕','弃营者')],note='万人是书载来袭军数；友裕逃不记战死。')
event('zhu_enters_doumen_ambush','朱全忠不知斗门失营，引军遭袭退瓠河',8,'892年二月乙酉','斗门、瓠河',
      '朱全忠不知斗门已为朱瑄占据，引军趋营，到者被郓州军杀，遂退驻瓠河。',[('朱温','以朱全忠名义不知失营退军者'),('朱瑄','占营一方主将')],note='至者皆杀为史书叙述，不扩大为朱全忠全军覆没，后文尚有力战突围。')
event('zhu_defeated_huhe','朱瑄瓠河大破朱全忠，张归厚后战救免',8,'892年二月丁亥','瓠河',
      '朱瑄进攻朱全忠并大败之，朱全忠逃走，张归厚在后力战，使朱全忠仅免；副使李璠等皆死。',[('朱瑄','获胜方'),('朱温','以朱全忠名义败走者'),('张归厚','殿后力战者'),('李璠','阵亡副使')],note='李璠沿用先奔大梁、后宣武行军司马的既有人物；张归厚为后战救免，不补救援具体招式与伤亡。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={1:'正月丙寅改元赦，不换算公历。',2:'五帅联奏与和解未执行；诏讨疑招讨，据下段统一职称不改原文。',3:'十余万兵与斩获三万书载区分，李嗣勋不与李嗣昭合并。',4:'战策与兵力十倍言论区分，戴友规籍贯独引，不提前记执行结果。',5:'约攻、丁丑掠境出吕尧与击斩分录，李简复用王建将消歧key。',6:'二月戊寅出攻前行驻斗门，朱友裕父亲关系依证查复用。',7:'擅攻兴元与求任信函、延英议后牛徽献议正式授职分开。',8:'甲申斗门失营、乙酉误趋营退瓠河、丁亥大败殿后与李璠阵亡依次分录。'}
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
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=892,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph='zztj-v259-y0892-p009',coverage='卷259景福元年第1—8段连续录入；本年46段尚未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
