"""Curate consecutive Tongjian volume 257, year 887 paragraphs 9–16."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 60))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0887-p009-p016', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-257-887'
B['sources'] = [dict(key=source,title='资治通鉴·卷257',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/5911e959ccc6b7efae3e673a6f8bcb612a9748a0/resources/derived/tongjian/257.txt',note='卷257光启三年起；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/257.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/257.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_257_0887_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·光启三年（887）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷257光启三年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=887,note=None,quote=None):
    key='event_zztj_257_0887_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_257_0887_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('gao_sends_shi_e','高骈遣石锷劝毕师铎',9,'光启三年四月；具体日未载','扬子、广陵',
      '高骈遣石锷带毕师铎幼子、其母书信及高骈的解释到扬子劝说。毕师铎送子返，要求先杀“吕、张”，愿以妻子为质；高骈收毕师铎母、妻、子置于使院。',
      [('高骈','遣使及收置家眷者'),('石锷','劝说使者'),('毕师铎','受劝并提出条件者')],
      note='原文仅称“吕、张”，此处不擅自展开张氏身份；“恐用之屠其家”是高骈的忧虑。')
event('qin_chou_aid','秦彦遣秦稠助毕师铎',10,'光启三年四月辛酉','扬子',
      '秦彦遣秦稠率兵至扬子援助毕师铎。',
      [('秦彦','遣援军者'),('秦稠','领兵者'),('毕师铎','受援者')],
      note='“三千”照原文，不据此核定实际兵额。')
event('guangling_assault','宣州军连日攻广陵',10,'光启三年四月壬戌至甲子','广陵',
      '宣州军壬戌攻南门未克，癸亥攻罗城东南隅几次险些破城；甲子罗城西南隅有守者焚守具响应毕师铎，毕师铎毁城入兵。',
      [('毕师铎','攻城方主将'),('秦稠','宣州援军将领')],
      note='三日战况依原文顺序合记；守者未具名，不创人物。')
event('lv_flees_guangling','吕用之战后三桥北逃离广陵',10,'光启三年四月甲子','广陵三桥北、参佐门',
      '吕用之率军在三桥北与毕师铎军战；高杰从子城出兵拟擒吕用之交给毕师铎，吕用之遂开参佐门北走。',
      [('吕用之','作战并逃走者'),('毕师铎','对战方'),('高杰','拟擒吕用之者')],
      note='“师铎垂败”是原文战况判断，不推论胜负数字。')
event('liang_zan_holds_inner_city','高骈命梁缵守子城',10,'光启三年四月甲子','广陵子城',
      '吕用之北走后，高骈召梁缵率昭义军百余人守子城。',
      [('高骈','命令者'),('梁缵','守子城者')])
event('bi_plunder_and_appointed','毕师铎入城掠夺并获高骈任命',10,'光启三年四月乙丑','广陵延和阁',
      '毕师铎纵兵大掠。高骈撤除戒备与其相见，署毕师铎为节度副使、行军司马，加左仆射；郑汉章等人也获得迁官。',
      [('毕师铎','纵兵与受任者'),('高骈','授官者'),('郑汉章','迁官者')],
      note='授官是在兵入城之后；“不得已”依原文，不解释为自愿和解。')
event('shen_ji_advises_escape','申及劝高骈夜逃而未获采纳',11,'毕师铎入城后；具体日未载','广陵',
      '申及建议高骈夜出城门、调诸镇兵再取府城；高骈犹豫未从。申及惧言泄而藏匿，张雄抵东塘时前往投奔。',
      [('申及','献策及出奔者'),('高骈','未采纳者'),('张雄','申及投奔者')],
      note='此处张雄据本年上卷苏州张雄承接；不与高邮张神剑合并。夜逃与再取府城是建议，不是已发生行动。')
event('bi_secures_gates','毕师铎守广陵诸门并诛吕用之亲党',12,'光启三年四月丙寅','广陵',
      '毕师铎分兵守城门，搜捕并杀吕用之亲党，自己入居使院。秦稠以宣州军守使宅及仓库。',
      [('毕师铎','守门及搜捕者'),('吕用之','亲党被搜捕者'),('秦稠','守使宅仓库者')],
      note='被杀者未具名，不据“悉诛之”估计人数。')
event('gao_resigns_bi_administers','高骈请解任，毕师铎兼判府事',12,'光启三年四月丙寅','广陵',
      '高骈以公文请求解除所任，由毕师铎兼判府事。毕师铎遣孙约赴宣城催秦彦过江。',
      [('高骈','请解任者'),('毕师铎','兼判府事及遣使者'),('孙约','催请使者'),('秦彦','被催过江者')],
      note='原文只记催请，不将秦彦已过江当作本段事实。')
event('bi_rejects_advice','毕师铎拒绝停止迎秦彦的劝告',12,'光启三年四月丙寅后','广陵',
      '一名未具名者劝毕师铎继续奉高骈、总兵权并阻秦彦过江；毕师铎不接受，次日告知郑汉章。郑汉章赞其为智士，搜寻而不得。',
      [('毕师铎','受劝而拒绝者'),('高骈','建议继续奉戴者'),('秦彦','建议阻止过江者'),('郑汉章','闻议并寻人者')],
      note='整段谋议是匿名者的建议与预测；不把其中关于秦彦、庐寿等未来结果录成事实。')
event('gao_confined_south','高骈被迁居南第并受监禁',13,'光启三年四月戊辰','广陵南第',
      '高骈迁家至南第，毕师铎以甲士百人名义上护卫，实际将其拘禁。',
      [('高骈','被拘禁者'),('毕师铎','拘禁者')])
event('xuanzhou_burns_towers','宣州军焚进奉楼',13,'光启三年四月戊辰','广陵进奉楼',
      '宣州军因所求未得，焚进奉楼，楼中财物被焚。',
      note='本段未明示下令焚楼的具名将领，不将此事归责秦稠。')
event('bi_takes_office','毕师铎府厅视事并迁高骈东第',13,'光启三年四月己巳','广陵府厅、东第',
      '毕师铎在府厅视事，保留不掌兵权官吏原职，又将高骈迁至东第。',
      [('毕师铎','视事及迁置者'),('高骈','被迁置者')])
event('tang_hong_policing','毕师铎任唐宏禁广陵军掠',13,'光启三年四月己巳','广陵',
      '广陵陷落后诸军昼夜劫掠，高骈所积财物亦被抢走；毕师铎至此任唐宏为静街使，命其禁止劫掠。',
      [('毕师铎','任命者'),('唐宏','受命禁掠者'),('高骈','财物被掠者')],
      note='原文记任命禁止，未证明劫掠已完全止息。')
event('zhuge_yin_killed','诸葛殷被杖杀',14,'光启三年四月庚午','广陵',
      '诸葛殷被捕后杖杀，遗体又遭怨家与众人毁辱。',
      [('诸葛殷','被杀者')],note='原文未明示下令杖杀者，不归责具体人。')
event('zheng_qi_killed','郑杞转投毕师铎后被高霸杀害',14,'吕用之败后至光启三年四月庚午前后','海陵',
      '吕用之败后郑杞先投毕师铎，获署知海陵监事；其后暗记高霸得失并报告毕师铎，高霸取得书信后酷刑杀郑杞。',
      [('郑杞','被杀者'),('毕师铎','任命及受报告者'),('高霸','杀郑杞者'),('吕用之','郑杞原所附者')],
      note='转投、任命、报告与死亡为段内追叙，具体各日未载。')
event('zhu_attacks_lu_tang','朱全忠袭击卢瑭万胜营',15,'光启三年四月；具体日未载','万胜、汴水',
      '卢瑭屯万胜截汴州运路；朱全忠乘雾袭击其营，卢瑭军败。',
      [('卢瑭','被袭蔡军将领'),('朱温','以朱全忠名义袭营者')],
      note='“掩杀殆尽”是原文战报，不作精确伤亡统计。')
event('zhu_attacks_zhang_zhi','朱全忠再攻张晊赤冈营',15,'袭卢瑭营后；具体日未载','赤冈、大梁',
      '蔡兵移往张晊驻守的赤冈，朱全忠再攻；蔡军惊惧，朱全忠随后返大梁休兵。',
      [('朱温','以朱全忠名义进攻者'),('张晊','被攻蔡军将领')],
      note='“杀二万余人”照史书所记的战争叙述，不推为核定伤亡。')
event('gao_bribes_guard','高骈以金贿守者',16,'光启三年四月辛未','广陵',
      '高骈暗中给看守者黄金，毕师铎获知。',
      [('高骈','给金者'),('毕师铎','获知者')],
      note='原文未说明高骈具体意图和看守者姓名。')
event('gao_family_confined','毕师铎幽禁高骈家人',16,'光启三年四月壬午','广陵道院',
      '毕师铎再次迎高骈入道院，并将高氏子弟、甥侄十余人一同幽禁。',
      [('毕师铎','拘禁者'),('高骈','被拘禁者')],
      note='壬午照原文干支记录，不自行换算或改写为壬申。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(9,17):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {9:'吕、张只按原文称谓；不推定张氏全名。',11:'张雄按上卷苏州张雄接续；暂不与高邮张神剑合并。',12:'匿名劝说中的形势预测不当作既成事实。',13:'禁掠任命不推为已经止掠。',14:'被杖杀的诸葛殷未见具名下令者。',15:'战争人数与杀伤数字不推为确证。',16:'辛未、壬午均照电子底本文字保留。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,17):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=887,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph='zztj-v257-y0887-p017',coverage='卷257光启三年条第9—16段；本年续录。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
