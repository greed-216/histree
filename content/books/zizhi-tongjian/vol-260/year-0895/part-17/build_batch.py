"""Curate consecutive Tongjian volume 260, year 895 paragraph 69."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p069-p069', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
people, used, reused = {}, {}, {source}
alias.update({'嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_260_0895_17_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

def e(code,title,when,place,desc,actors,quote,note):
    return event(code,title,69,when,place,desc,actors,quote=quote,note=note)
e('li_xiji_thanks_requests_fengxiang','李克用遣李袭吉谢恩，密请乘胜取凤翔','895年十二月晋王封爵以后；确日未载','朝廷、渭北',
  '李克用派掌书记李袭吉入朝谢恩，并密请乘胜攻取凤翔，称军在渭北等待决定。',[('李克用','遣使请讨者'),('李袭吉','掌书记传密言者'),('唐昭宗','受请者')],
  '李克用遣掌书记李袭吉入谢恩，密言于上曰：“比年以来，关辅不宁，乘此胜势，遂取凤翔，一劳永逸，时不可失。臣屯军渭北，专俟进止。”','密言为李克用请求，俟进止非已获批准，一劳永逸为其主张。')
e('emperor_consults_fengxiang_fears_shatuo','皇帝询贵近，有人忧灭茂贞后沙陀过盛','895年十二月李袭吉使后条；确日未载','朝廷',
  '唐昭宗询问亲近者，有人称李茂贞若灭，沙陀势力将太盛、朝廷会危险。',[('唐昭宗','咨询者')],
  '上谋于贵近，或曰：“茂贞复灭，则沙陀大盛，朝廷危矣！”','或曰未名不造谏者；朝廷危为该人预测，不认已发生危亡。')
e('emperor_orders_keyong_rest_armies','昭宗诏褒李克用，令休兵息民','895年十二月议讨后条；确日未载','朝廷',
  '唐昭宗诏褒李克用忠诚，称王行瑜罪最重，茂贞韩建知罪并继续贡奉，应暂休兵。李克用奉诏停止请讨后的进攻计划。',[('唐昭宗','赐诏者'),('李克用','奉诏止者')],
  '上乃赐克用诏，褒其忠款，而言：“不臣之状，行瑜为甚。自朕出幸以来，茂贞、韩建自知其罪，不忘国恩，职贡相继，且当休兵息民。”克用奉诏而止。','茂韩知罪贡奉为诏书所称，未独立核验；止不是此次已攻下凤翔。')
e('keyong_private_warning_maozhen','李克用私谓诏使朝廷疑己，茂贞不去关中难安','895年十二月奉诏后条；确日未载',None,
  '李克用私下对诏使说朝廷似疑自己有异心，李茂贞不除，关中不会安宁。',[('李克用','私言者')],
  '既而私于诏使曰：“观朝廷之意，似疑克用有异心也。然不去茂贞，关中无安宁之日。”','疑己是李克用推测，关中难安为警告，不自动认皇帝真实内心。')
e('emperor_exempts_keyong_audience','朝廷免李克用入朝，将佐劝其入见','895年十二月奉诏后条；确日未载',None,
  '朝廷诏免李克用入朝，将佐有人认为已近京师应入见，李克用犹豫未决。',[('唐昭宗','免朝诏者'),('李克用','犹豫者')],
  '又诏免克用入朝，将佐或言：“今密迩阙庭，岂可不入见天子，！”克用犹豫未决','或言将佐未名，未认李克用此时已朝见；底本异常标点保留。')
e('gai_yu_advises_avoid_alarm_capital','盖寓劝李克用勿率兵渡渭惊京城','895年十二月入朝争议时；确日未载','渭北、京师',
  '盖寓劝李克用，天子未安、人心尚危，率兵渡渭恐再惊京城；人臣尽忠在勤王而非入觐，应慎重考虑。李克用笑称盖寓尚不愿自己入朝，何况天下人。',[('盖寓','谏者'),('李克用','受谏答者')],
  '盖寓言于克用曰：“向者王行瑜辈纵兵狂悖，致銮舆播越，百姓奔散。今天子还未安席，人心尚危，大王若引兵渡渭，窃恐复惊骇都邑。人臣尽忠，在于勤王，不在入觐，愿熟图之！”克用笑曰：“盖寓尚不欲吾入朝，况天下之人乎！”','恐惊为建议中的预测，未作已率军渡渭或京城再次奔乱。')
e('keyong_memorial_declines_audience','李克用上表不敢径入朝，忧军扰居民','895年十二月辛亥以前；确日未载','朝廷、渭北',
  '李克用表称统率大军，不敢直接入朝，又恐部落士卒侵扰渭北居民。',[('李克用','上表者')],
  '乃表称：“臣总帅大军，不敢径入朝觐，且惧部落士卒侵扰渭北居人。”','惧侵扰是表述顾虑，不补已发生单次劫掠。')
e('keyong_returns_east_capital_calms','李克用辛亥率军东归，奏表至京上下始安','895年十二月辛亥','京师、东归途中',
  '李克用率军东归，奏表到京师，朝廷上下才安定。',[('李克用','引兵东归者')],
  '辛亥，引兵东归。表至京师，上下始安。','东归未载此日已达太原；上下始安为史书记述，不推全体民众具体感受。')
e('emperor_rewards_hedong_thirty_wan','朝廷赐河东士卒三十万缗','895年十二月李克用东归条；确日未载','朝廷、河东',
  '朝廷诏赐河东士卒钱三十万缗。',[('唐昭宗','诏赐者')],
  '诏赐河东士卒钱三十万缗。','保诏赐金额，不等于已逐人发到或现代币值。')
e('maozhen_hexizhou_hu_jingzhang','李克用去后茂贞占河西州县，任胡敬璋','895年十二月李克用去后总述；起讫未另载','河西州县',
  '李克用离去后，史书称李茂贞仍骄横，河西多州县被其占据，他以胡敬璋为河西节度使。',[('李茂贞','据州任将者'),('胡敬璋','被任河西节度使者')],
  '克用既去，李茂贞骄横如故，河西州县多为茂贞所据，以其将胡敬璋为河西节度使。','河西按关中语境保史名，不直接等同现代河西走廊；未具名州县不补疆域，多为总述不造每州确定占领日。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-895-request-fengxiang-withdrawal';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==601)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L601'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·请讨不允与班师',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第601页，乾宁二年十二月末段。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=601的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
quote='武皇复上表请讨李茂贞，天子不允。';assert quote in raw.decode()
ck=f'claim_zztj_260_0895_17_{len(B["claims"])+1:04d}';ek='event_zztj_260_0895_emperor_orders_keyong_rest_armies'
B['claims'].append(dict(key=ck,subject_table='event',subject_key=ek,field_path='description',claim_text='《旧五代史》同记李克用再表请讨李茂贞，皇帝不允。',source_key=sk,citation='卷26·武皇纪下·乾宁二年十二月末段·原PDF第601页',note='原文：'+quote+'；核对说明：独立出处印证请讨未准，不作已经讨平。',status='draft'))
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger[68].update(event_keys=used[69],batch_key=B['batch_key'],review='第69段遣使密请、贵近疑盛、诏休奉止、私语疑己、免朝将劝、盖谏李答、上表不入、辛亥东归安京、诏赐钱、茂据河西任胡分录。诏说与私言预测归属明确，东归非已抵太原，河西不套现代走廊。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[69]['id']],next_paragraph=Q[70]['id'],coverage='第69段连续整理；本年未完成。',supplements=[dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[69]['id'],subject_key=ek,relation='corroborates')],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
