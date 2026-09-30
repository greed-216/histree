"""Curate consecutive Tongjian volume 260, year 895 paragraphs 1–5."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p001-p005', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-260-895'
B['sources'] = [dict(key=source,title='资治通鉴·卷260',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/260.txt',note='卷260乾宁二年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/260.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/260.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
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
alias.update({'嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_260_0895_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷260乾宁二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=895,note=None,quote=None):
    key='event_zztj_260_0895_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_260_0895_'+code+'_'+pk
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

alias.update({'李溪':'李磎','李谿':'李磎','薛志诚':'薛志勤','李存审':'符存审','刘廉':'刘谦'})
event('keyong_welcomed_youzhou','幽州军民迎李克用入府舍',1,'895年春正月辛酉','幽州、府舍',
      '幽州军民数万以麾盖、歌鼓迎李克用进入府舍。',[('李克用','受迎入府者')],note='承894年末进幽州受降，迎入府舍是本年后续，不重建894年攻城；数万为书载概数。')
event('cunshen_rengong_settle_youzhou_dependencies','李克用命李存审刘仁恭略定巡属',1,'895年正月辛酉条；具体起讫未载','幽州巡属',
      '李克用命李存审、刘仁恭带兵平定幽州所辖地区。',[('李克用','命将出兵者'),('符存审','以李存审名奉命领兵者'),('刘仁恭','奉命领兵者')],note='巡属照原文理解所辖地区，不编具体郡县、行军路径或同日全部完成；符李存审按上批赐名书证复用。')
event('zhu_yougong_sieges_yanzhou','朱全忠遣朱友恭围兗州',2,'895年正月癸未','兗州',
      '朱全忠派朱友恭包围兗州。',[('朱温','以朱全忠名遣围者'),('朱友恭','奉遣围城者')],note='主书癸未与旧史癸亥另存，不自行换算公历或默改干支。')
event('gaowu_relief_defeated_an_captured','朱瑄援兗粮兵遭高梧伏击，安氏两将被俘',2,'895年正月条；围兗以后，确日未载','高梧、兗州',
      '朱瑄从郓州率兵带粮救兗，朱友恭设伏，在高梧击败援军，夺其全部军粮，俘河东将安福顺、安福庆。',[('朱瑄','带粮援兵者'),('朱友恭','设伏败援夺粮者'),('安福顺','被俘河东将'),('安福庆','被俘河东将')],note='癸未明确系遣围，援战确日未另载，不强合为同日；俘获非处死，旧书高吴字形并列，未配现代地点。')
event('lu_xisheng_chancellor','陆希声授户部侍郎同平章事',3,'895年正月己已；底本日字如此','朝廷',
      '朝廷以给事中陆希声为户部侍郎、同平章事。',[('陆希声','授官任相者')],note='己已疑己巳，原字保留，未校历或改动快照。')
claim('person',people['陆希声'],'biography','《通鉴》称陆希声为元方五世孙。',3,quote='希声，元方五世孙也。',note='祖名片段与代数按原书保留，不补中间四代、不建直接父子关系或未核全名祖人。')
event('wang_chongying_dies','护国节度使王重盈卒',4,'895年正月壬申','护国',
      '护国节度使王重盈去世。',[('王重盈','去世节度使')],quote='壬申，护国节度使王重盈薨',note='只记卒，不推死因、年龄或因与王珂争继立而被害。')
event('army_requests_wang_ke_acting','军中请王珂知留后事',4,'895年正月壬申条；重盈卒后','护国、河中',
      '王重盈死后，军中请求以王重荣之养子、行军司马王珂暂管留后事务。',[('王珂','军中所请暂摄者'),('王重荣','王珂已故养父')],note='军中请是请求，不作朝廷已诏准；重荣子与段后收养说明合读，不误成生父。')
person('王重简',4,'王重盈兄、王珂生父')
relation('王重简','王珂','父亲',4,'王重简是王珂的生父，原文称珂为重盈兄重简之子。',quote='珂，重盈兄重简之子也')
relation('王重荣','王珂','养父',4,'王重荣是王珂的养父，原文称重荣养以为子。',quote='重荣养以为子。')
relation('王重简','王重盈','兄长',4,'王重简是王重盈的兄长。',quote='珂，重盈兄重简之子也')
event('yang_petitions_coalition_against_zhu','杨行密表朱全忠罪恶，请会四方兵讨之',5,'895年正月条；具体日未载','朝廷、易定、兗郓、河东',
      '杨行密上表指述朱全忠罪恶，请求会合易定、兗、郓、河东军讨伐。',[('杨行密','上表请会兵者'),('朱温','以朱全忠名被表指控与拟讨者')],note='罪恶为杨奏的指控，原段未展开罪条，不能据此新增具体罪行；请会不是已成联盟或已出联合军。易定等未具名主将，本批不凭辖区自动补参与人。')

from urllib.parse import quote as urlquote
supplements=[]
for sk,title,author,path,page in [
 ('jiuwudaishi-001-895-yanzhou','旧五代史·卷1·围兗高吴段','薛居正等','resources/derived/twenty-four-histories/18旧五代史.jsonl',25),
 ('xinwudaishi-042-895-wangke-family','新五代史·卷42·王珂传·父与养父','欧阳修','resources/derived/twenty-four-histories/19新五代史.jsonl',778)]:
    raw=next(json.loads(x)['text'].encode() for x in (ROOT/path).read_text().splitlines() if json.loads(x)['pdf_page']==page)
    url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+f'#L{page}'
    (P/'sources'/(sk+'.txt')).write_bytes(raw)
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='仓库PDF派生电子文本；逐字与换行保留，未核纸本。',url=url,note=f'原PDF第{page}页，只补当前连续主线。'))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation=f'提取JSONL pdf_page={page}的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(table,key,field,text,n,sk,quote,citation,note,book,kind):
    assert quote in (P/'sources'/(sk+'.txt')).read_text()
    ck=f'claim_zztj_260_0895_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=citation,note=f'原文：{quote}；核对说明：{note}',status='draft'))
    supplements.append(dict(claim_key=ck,source_book=book,primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('event','event_zztj_260_0895_zhu_yougong_sieges_yanzhou','time_original','《旧五代史》乾宁二年正月记癸亥遣朱友恭围兗，与主書癸未记日不同。',2,'jiuwudaishi-001-895-yanzhou','二年正月癸亥，遣朱友恭帅师复\n伐兗，遂堑而围之。','卷1·太祖纪一·乾宁二年正月段·原PDF第25页','二年承前页乾宁元年后段；记日差别并列，不默改主书记日。','旧五代史','conflicts')
extra('event','event_zztj_260_0895_gaowu_relief_defeated_an_captured','location_name','《旧五代史》记同一伏援夺粮地点为高吴，主书作高梧。',2,'jiuwudaishi-001-895-yanzhou','未几，朱瑄自郓\n率步骑援粮欲入于兗，友恭设伏以败\n之，尽夺其饷于高吴，因擒蕃将安福\n顺、安福庆。','卷1·太祖纪一·原PDF第25页','援兵、粮与安氏两将相应，保留地点异字，不猜现代地名；未几不作围城当日。','旧五代史','conflicts')
extra('person_relationship',f"relationship_{people['王重简']}_{people['王珂']}_父亲",'description','《新五代史》同记王珂为王重简之子，王重荣因无子立为后。',4,'xinwudaishi-042-895-wangke-family','重荣无子，以其兄重简子珂\n为后。','卷42·杂传第三十·王珂传·原PDF第778页','印证生父与收养结构；各书后称不把王重荣录作895年活人，也未用无子推其他未载婚姻。','新五代史','corroborates')
extra('person_relationship',f"relationship_{people['王重荣']}_{people['王珂']}_养父",'description','《新五代史》记王重荣无子，以其兄重简子王珂为后；印证收养。',4,'xinwudaishi-042-895-wangke-family','重荣无子，以其兄重简子珂\n为后。','卷42·杂传第三十·王珂传·原PDF第778页','主书明确养以为子，补书为后相应；不反算收养日或另造母亲。','新五代史','corroborates')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={
 1:'正月辛酉迎府与命二将略巡属分录；承894进幽后事，数万为概数，略属不编县与路线。',
 2:'癸未遣围与朱瑄援、友恭伏败夺粮擒安分阶段；旧史癸亥和高吴另引，不默改；被俘不作死。',
 3:'己已疑己巳保底本；陆授相，五世孙仅保代数，不编中间世系。',
 4:'重盈卒与军请王珂暂摄分录；王重简生父、王重荣养父、重简兄长→重盈有句，新史父与养父补证，军请非诏准。',
 5:'杨表罪恶与会兵皆奏请，不写已联军或补奏中未载罪条、辖区未具名主将。',
}
for n in range(1,6):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,6):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,6)],next_paragraph='zztj-v260-y0895-p006',coverage='卷260乾宁二年第1—5段连续录入；本年74段尚未完。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
