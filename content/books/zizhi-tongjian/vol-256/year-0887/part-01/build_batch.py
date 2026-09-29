"""Curate consecutive Tongjian volume 256, year 887 paragraphs 1–11."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 12))
B = {'format_version': 1, 'batch_key': 'zztj-v256-y0887-p001-p011', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-256-884'
prior = json.loads((ROOT / 'content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json').read_text())
B['sources'] = [next(s for s in prior['sources'] if s['key'] == source)]
raw = (ROOT / 'resources/derived/tongjian/256.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/256.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_256_0887_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷256·光启三年（887）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷256光启三年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=887,note=None,quote=None):
    key='event_zztj_256_0887_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_256_0887_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('january_offices','王行瑜等五将获任节度使',1,'光启三年春正月','静难、武定、金商、东川、山南西道',
      '朝廷任王行瑜为静难军节度使、李茂贞领武定节度使、杨守宗为金商节度使、顾彦朗为东川节度使、杨守亮为山南西道节度使。',
      [('王行瑜','受任静难者'),('李茂贞','领武定者'),('杨守宗','受任金商者'),('顾彦朗','受任东川者'),('杨守亮','受任山南西道者')],
      note='本段为一组朝廷任命；“领武定”与实际到镇治理不同。')
event('dong_qian_offices','董昌、钱镠获正式任命',2,'光启三年正月辛巳','浙东、杭州',
      '朝廷任董昌为浙东观察使，钱镠为杭州刺史。',
      [('董昌','受任浙东观察使者'),('钱镠','受任杭州刺史者')])
event('zhu_zhen_recruits','朱全忠遣朱珍募兵',3,'光启三年二月','淄州、东道',
      '秦宗权计划集中力量攻汴州；朱全忠因兵力不足，任朱珍为淄州刺史，遣其到东道募兵，约定初夏返回。',
      [('秦宗权','拟攻汴州者'),('朱温','以朱全忠名义遣朱珍者'),('朱珍','募兵者')],
      note='“兵力十倍”是秦宗权自认为的比较，不作为核实兵数；攻汴州为计划，非已发生。')
event('tian_lingzi_exiled','田令孜被削官长流端州，实际未行',4,'光启三年二月戊辰','端州、西川',
      '朝廷削田令孜官爵，下令长流端州；田令孜依附陈敬瑄，流放令最终未执行。',
      [('田令孜','被贬而未赴端州者'),('陈敬瑄','庇护者')],
      note='必须区分诏令与执行结果；本段明记“竟不行”。')
event('li_guochang_death','代北节度使李国昌去世',5,'光启三年二月后条；具体日未载','代北',
      '代北节度使李国昌去世。',[('李国昌','去世者')])
event('three_chancellors_executed','萧遘、郑昌图、裴澈在岐山被斩',6,'光启三年三月癸未','岐山',
      '朝廷下诏将曾受襄王煴方面官职的萧遘、郑昌图、裴澈示众处斩，三人均死于岐山。',
      [('萧遘','被处决者'),('郑昌图','被处决者'),('裴澈','被处决者')],
      note='原文称“伪宰相”是僖宗朝廷的政治定性；萧遘此前拒撰册文及称病归去，仍照本段记录实际结局。')
event('du_rangneng_amnesty','杜让能力争，部分受襄王官职朝士免死',6,'光启三年三月癸未后','行在',
      '法司拟严惩众多曾受襄王煴官职的朝士，杜让能力争，史书记载多数获免。',
      [('杜让能','力争减免者')],
      note='“什七八”为书载概数，不推为精确获免人数。')
event('court_fengxiang','僖宗车驾至凤翔，李昌符请求暂驻',7,'光启三年三月壬辰','凤翔',
      '皇帝车驾抵凤翔；李昌符以宫室未完为由，请皇帝驻于其府舍，获准。',
      [('李昌符','请驻者')],
      note='李昌符担忧还京后恩赏转疏是本段所述动机；不据此推定朝廷实际处分。')
event('zheng_congdang_transfer','郑从谠罢太傅兼侍中，任太子太保',8,'光启三年三月条；具体日未载',None,
      '郑从谠由太傅兼侍中改任太子太保。',[('郑从谠','改任者')])
event('zhou_bao_houlou','周宝先前募后楼兵，镇海军生怨',9,'镇海军变前；确年待考','镇海',
      '周宝募待遇较高的亲军后楼兵，普通镇海军不满；其后楼兵渐骄横，筑城劳役亦使民众困苦。',
      [('周宝','募兵及筑城者')],year=None,
      note='这一段为兵变背景，未记募兵起年；不把所有积怨归到887年。')
event('liu_hao_revolt','刘浩率镇海军兵变，周宝逃常州',9,'光启三年三月癸巳前夜及当日','镇海、常州',
      '薛朗将周宝威胁镇海军的话转告刘浩，刘浩当夜率党攻府舍；周宝逃常州依丁从实，刘浩杀多名僚佐。',
      [('薛朗','转告者'),('刘浩','兵变领袖'),('周宝','逃走者'),('丁从实','收留者')],
      note='兵变起夜与癸巳推留后相连；不据此换算公历日。')
event('xue_lang_liuhou','刘浩军推薛朗为镇海留后',9,'光启三年三月癸巳','镇海',
      '刘浩军迎薛朗入府，推其为留后。',[('刘浩','迎入者'),('薛朗','被推留后者')])
event('gao_pian_reacts','高骈闻周宝败，送齑粉相讥',9,'镇海兵变后；具体日未载','扬州、常州',
      '高骈听闻周宝败走后接受祝贺，并遣人送齑粉；周宝愤怒，回称高骈有吕用之，后事未定。',
      [('高骈','遣物者'),('周宝','回话者'),('吕用之','周宝话中所指者')],
      note='周宝话是预言式反讥，不作为吕用之日后行动已发生的证据。')
event('yangzhou_famine','扬州连年饥荒，城中多人饿死',9,'连岁；具体年界待考','扬州',
      '《通鉴》记扬州连年饥荒，城中饿死者众，坊巷萧条。',year=None,
      note='“连岁”“日数千人”为史家概括性记数，不据此推算人口和确切年份。')
event('yang_shouliang_calls_wang','杨守亮屡召王建，王建不往',10,'光启三年三月后条；具体日未载','利州、山南西道',
      '杨守亮忌王建勇武，屡次召其前往；王建畏惧而不赴。',
      [('杨守亮','召见者'),('王建','拒赴者')])
event('wang_jian_langzhou','王建袭阆州、逐杨茂实',10,'光启三年三月后条；具体日未载','阆州、嘉陵江',
      '周庠建议王建以杨茂实不修职贡为由进兵；王建招兵沿嘉陵江袭阆州，逐杨茂实，占据该州并自称防御使。',
      [('周庠','建言者'),('王建','攻城及自称防御使者'),('杨茂实','被逐者')],
      note='周庠对唐朝前途及王建功业的判断是其劝说内容；“八千”为本书所载兵数。')
event('wang_jian_advisers','张虔裕、綦毋谏劝王建奉表及养士爱民',10,'王建据阆州之后；具体日未载','阆州',
      '张虔裕建议王建奉表朝廷，綦毋谏建议养士爱民、观望形势；王建均采纳。',
      [('张虔裕','建言奉表者'),('綦毋谏','建言养士者'),('王建','采纳者')],
      note='原文只记王建听从建议，不据此认定已完成奉表行为。')
event('wang_gu_old','王建与顾彦朗先前同在神策军',10,'“初”追叙；确年待考',None,
      '《通鉴》追叙王建与顾彦朗曾同在神策军、共同讨贼。',
      [('王建','此前神策军成员'),('顾彦朗','此前神策军成员')],year=None,
      note='“初”所述旧事起年不明，不强定887年。')
event('gu_yanlang_appeases_wang','顾彦朗馈王建军粮，王建未犯东川',10,'王建据阆州后；具体日未载','东川、阆州',
      '顾彦朗担心王建侵入东川，数次馈送军粮；王建因此未侵犯东川。',
      [('顾彦朗','馈粮者'),('王建','受馈及未进攻者')],
      note='此处因果关系仅限本段所述期间，不推为终身盟好。')
event('zhou_bao_xu_yue','周宝先前诱徐约进攻苏州',11,'“初”追叙；确年待考','苏州方向',
      '《通鉴》卷256末段追叙周宝听闻徐约兵精，诱使他进攻苏州；结果续见下卷。',
      [('周宝','诱使者'),('徐约','被诱出兵者')],year=None,
      note='本段以“初”起并在卷末中断，不能仅据此断定进攻日期或结果。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(1,12):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {3:'秦宗权“兵力十倍”为其自评，攻汴州为计划。',4:'田令孜流放有令未行。',6:'“伪宰相”为朝廷政治定性；诏斩与杜让能力争分别记录。',9:'后楼兵、筑城和连岁饥荒为背景，癸巳兵变另记。',10:'“初”之旧事与王建袭阆州分开；建言不等于已奉表。',11:'卷末“初”引出下卷续事，起年与结果未定。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,12):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=256,year=887,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,12)],next_paragraph='zztj-v257-y0887-p001',coverage='卷256光启三年条11段；该年续于卷257。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
