"""Curate consecutive Tongjian volume 260, year 896 paragraphs 18–20."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 49))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0896-p018-p020', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-260-896'
B['sources'] = [dict(key=source,title='资治通鉴·卷260',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/260.txt',note='卷260乾宁三年条；书、卷、年、段落及行号见批次账本。')]
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
people, used, reused = {}, {}, {source}
alias.update({'硃延寿':'朱延寿','贾公鐸':'贾公铎','刘存':'刘存（光州刺史）','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_260_0896_07_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁三年（896）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷260乾宁三年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=896,note=None,quote=None):
    key='event_zztj_260_0896_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_260_0896_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('zhu_yanshou_besieges_qizhou','朱延寿突至蕲州围城',18,'896年五月条；确日未载','蕲州',
      '淮南将朱延寿突然到达蕲州，包围城池。',[('朱延寿','围城将')],quote='淮南将硃延寿奄至蕲州，围其城。')
event('jia_gongduo_hunts_blocked_outside','贾公铎出猎不得还，伏兵林中',18,'896年蕲州被围时；确日未载','蕲州城外林中',
      '贾公铎当时在外打猎，不能回城，将兵伏于林中。',[('贾公铎','出猎并伏兵者')],quote='大将贾公鐸方猎，不得还，伏兵林中',note='大将所指贾公铎，不因公铎名相近合并后蜀张公铎；林中位置未配坐标。')
event('jia_sends_sheepskin_braves_into_city','贾公铎遣二勇士衣羊皮潜入城，约开门举火',18,'896年蕲州围攻时夜间；确日未载','蕲州',
      '贾公铎命两名勇士穿羊皮，夜入朱延寿掠来的羊群，潜入城中约定夜半开门举火响应，再穿羊皮返回复命。',[('贾公铎','遣勇士定信号者')],quote='命勇士二人衣羊皮夜入延寿所掠羊群，潜入城，约夜半开门举火为应，复衣皮返命。',note='二勇士未名，不编姓名或人物档案；约夜半是约定，不转换钟点或公历日。')
event('jia_breaks_siege_into_qizhou','贾公铎按火号力战，突围入城',18,'896年围攻条；按约之夜','蕲州城南',
      '贾公铎按约率兵至城南，见门中举火，力战突破包围进入城内。',[('贾公铎','率兵突围入城者')],quote='公鐸如期引兵至城南，门中火举，力战，突围而入。',note='突围而入不能反写成出城逃亡，未载双方伤亡数。')
event('zhu_requests_oath_gifts_marriage_persuasion','朱延寿请遣贾公铎故旧持誓书金帛劝降，许以婚',18,'896年贾公铎突围入城以后；确日未载',None,
      '朱延寿惊于贾公铎突围而入，认为城难速取，向杨行密请求选军中与贾公铎有旧者，持誓书金帛劝说，并许以婚姻。',[('朱延寿','提出劝降办法者'),('杨行密','受请求者')],quote='延寿惊曰：“吾常恐其溃围而出，反溃围而入，如此，城安可猝拔！”乃白行密，求军中与公鐸有旧者持誓书金帛往说之，许以婚。',note='许以婚仅为劝降条件，未载婚配对象或婚姻实现，不建夫妻关系；难猝拔是朱判断。')
event('chai_zaiyong_volunteers_persuades_jia','柴再用请行，临城向贾公铎陈利害',18,'896年朱延寿请劝降后；确日未载','蕲州城前',
      '寿州团练副使柴再用主动请求前往，临城与贾公铎交谈，陈说利害。',[('柴再用','请行劝说者'),('贾公铎','受劝说者')],quote='寿州团练副使柴再用请行，临城与语，为陈利害。',note='承前受话者公铎；柴官主书是副使，十国春秋贾传作团练使，保差别不覆盖。')
event('jia_feng_request_surrender','贾公铎冯敬章数日后请降',18,'896年柴再用劝说后数日；确日未载','蕲州',
      '数日后，贾公铎和刺史冯敬章请求投降。',[('贾公铎','请降者'),('冯敬章','请降刺史')],quote='数日，公鐸及刺史冯敬章请降。',note='数日不补确日；请降未发挥为有完整盟誓或终身联盟。')
event('feng_jia_receive_posts','冯敬章为左都押牙，贾公铎为右监门卫将军',18,'896年蕲州请降后；确日未载',None,
      '冯敬章被任为左都押牙，贾公铎被任为右监门卫将军。',[('冯敬章','受左都押牙者'),('贾公铎','受右监门卫将军者')],quote='以敬章为左都押牙，公鐸为右监门卫将军。',note='主书本句省任命者，补书明记太祖杨行密；不只凭省主语句额外建任命者参与。')
event('zhu_captures_guang_kills_liu_cun','朱延寿进拔光州，杀刺史刘存',18,'896年蕲州请降及任职以后；确日未载','光州',
      '朱延寿继续攻取光州，杀刺史刘存。',[('朱延寿','攻取并杀者'),('刘存','被杀光州刺史')],quote='延寿进拔光州，杀刺吏刘存。',note='刺吏保底本文字；与907年淮南将刘存活动及卒年不同，使用刘存（光州刺史）消歧，未因同名合并。')
event('emperor_sends_envoy_reconcile_chuans','唐昭宗遣中使赴梓州和解两川',19,'896年五月丙戌','梓州',
      '唐昭宗派中使前往梓州，调解两川。',[('唐昭宗','遣中使者')],quote='丙戌，上遣中使诣梓州和解两川',note='中使未名，不补具名宦官；遣和解不表示战争已经结束。')
event('wang_jian_returns_chengdu_war_continues','王建奉诏回成都，两川仍连兵未解',19,'896年五月丙戌和解条；奉诏还确日未另载','成都',
      '王建虽奉诏回成都，两川仍继续交战，战事未解。',[('王建','奉诏还者')],quote='王建虽奉诏还成都，然犹连兵未解。',note='还成都与连兵未解均明载，不从还推完全停战，不新增战役地点。')
event('cui_zhaowei_again_requests_zhu_rescue','崔昭纬再次向朱温求救',20,'896年五月戊子赐死前条；确日未载',None,
      '崔昭纬再次向朱温请求救助。',[('崔昭纬','求救者'),('朱温','受请求者')],quote='崔昭纬复求救于硃全忠。',note='求救不作朱已派兵或救助成功，复未补此前次数。')
event('emperor_orders_cui_death','唐昭宗遣中使赐崔昭纬死',20,'896年五月戊子',None,
      '唐昭宗遣中使赐崔昭纬死。',[('唐昭宗','发命者'),('崔昭纬','被赐死者')],quote='戊子，遣中使赐昭纬死',note='省主语承帝叙事；命令与实际追斩分录。')
event('envoy_pursues_executes_cui_jingnan','中使行至荆南追及崔昭纬，斩之',20,'896年五月戊子遣使以后；追及确日未另载','荆南',
      '中使到荆南，追上崔昭纬并将他斩杀。主书记中外均以为快。',[('崔昭纬','被追及斩杀者')],quote='行至荆南，追及，斩之，中外咸以为快。',note='中外咸以为快作为主书评价，不视为对所有人心理的独立确证；执行日期未因戊子遣使定为同日。')

from urllib.parse import quote as urlquote
sk='shiguochunqiu-006-896-jia-qizhou';path='resources/originals/kanripo/KR2i0021/KR2i0021_006.txt'
raw=(ROOT/path).read_bytes();url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='十国春秋·卷6·贾公铎传',source_type='primary',author='吴任臣',edition='四库全书电子文本；保原字换行，未核纸本。',url=url,note='贾公铎传位于第7b—8a叶；补证与主书对应见引用。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='none'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
supplements=[]
def extra(table,key,field,text,q,citation,note,kind='adds'):
    assert q in raw.decode();ck=f'claim_zztj_260_0896_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=citation,note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='十国春秋',primary_paragraph_id=Q[18]['id'],subject_key=key,relation=kind))
extra('person',people['贾公铎'],'description','《十国春秋》记贾公铎为上蔡人，夹注称《九国志》作贾铎。',
      '賈公鐸(九國志/作賈鐸)上蔡人也','卷6·吴六列传·贾公铎传·KR2i0021_WYG_006-7b',
      '只作该书籍贯及转述姓名异文；未直接查九国志，不计另一个独立来源，未直接把贾铎登记确定别名。')
extra('event','event_zztj_260_0896_feng_jia_receive_posts','description','《十国春秋》贾公铎传明记太祖杨行密任冯敬章左都押牙、贾公铎右监门卫将军。',
      '公鐸及敬章請降太祖以敬章為左都¶\n押牙公鐸為右監門衛將軍','卷6·吴六列传·贾公铎传·KR2i0021_WYG_006-8a',
      '相同任职有补书明确主语，太祖是本书吴太祖杨行密；叙事与通鉴高度一致，不能视为独立确证。','corroborates')
extra('event','event_zztj_260_0896_chai_zaiyong_volunteers_persuades_jia','description','《十国春秋》贾传称柴再用为寿州团练使，主书称团练副使。',
      '壽州團練使柴再用請行臨陳¶\n與語為陳利害','卷6·吴六列传·贾公铎传·KR2i0021_WYG_006-8a',
      '同一事件官称使与副使不同，并列保留；同卷柴传又记授寿州团练副使，未据贾传改已有职位。','conflicts')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
reviews={18:'蕲州围攻、羊皮潜入信号、贾突围入、朱请故旧誓金婚劝、柴劝、请降授职、光州攻杀连续分录。婚仅许诺；光州刘存另行消歧，不合907淮南将。十国春秋籍贯、任命者与官称异记独立引用。',19:'遣中使和解与王建还成都而连兵未解分录，不作已停战。',20:'崔求救、帝戊子赐死与中使荆南追斩分录，不把遣使与执行强定同日，中外评价归于主书。'}
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(18,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=896,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(18,21)],next_paragraph=Q[21]['id'],coverage='第18—20段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
