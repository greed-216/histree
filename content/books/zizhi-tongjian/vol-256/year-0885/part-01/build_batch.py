"""Curate consecutive Tongjian volume 256, year 885 paragraphs 1–10."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 31))
B = {'format_version': 1, 'batch_key': 'zztj-v256-y0885-p001-p010', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','郭禹':'成汭'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_256_0885_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷256·光启元年（885）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=['郭禹'] if name=='成汭' else [],era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷256光启元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=885,note=None,quote=None):
    key='event_zztj_256_0885_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_256_0885_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('qin_amnesty','朝廷下诏招抚秦宗权',1,'光启元年正月戊午',None,'朝廷下诏招抚秦宗权。',[('秦宗权','诏书招抚对象')],note='“之”的所指据紧接前一年末段“上将还长安、畏宗权为患”与此年后续秦宗权条定位；并非本段直接具名。')
event('court_departure','僖宗车驾离开成都',2,'光启元年正月己卯','成都、汉州','皇帝车驾离成都，陈敬瑄送至汉州后返回。',[('陈敬瑄','送驾者')])
event('shentu_old','申屠琮先前率兵赴长安讨黄巢',3,'郑绍业镇荆南时；确年待考','荆南、长安','郑绍业镇荆南期间曾遣申屠琮率兵五千至长安攻击黄巢。',[('郑绍业','遣将者'),('申屠琮','率兵者'),('黄巢','被攻者')],year=None,note='“郑绍业之镇荆南也”引出旧事，不能定为885年。')
event('zhongyong_breakup','程君之率忠勇军逃往朗州，申屠琮追击',3,'申屠琮回荆南后；确年待考','荆南、朗州','忠勇军行为暴横。陈儒请申屠琮处理；程君之闻讯率众奔朗州，申屠琮追击，杀百余人，余众溃散。',[('朱敬玫','忠勇军招募者'),('陈儒','请申屠琮处理者'),('申屠琮','追击者'),('程君之','率众逃走者')],year=None,note='段内有旧事串叙，行动具体发生年未给；杀伤数照原文。')
event('lei_man_raids','雷满屡攻荆南，陈儒纳赂退敌',4,'光启元年前后屡次；确年待考','荆南','雷满多次攻掠荆南，陈儒用重赂使其退去。',[('雷满','攻掠者'),('陈儒','纳赂者')],year=None,note='“屡”表反复，不能定为单次885年事件。')
event('zhang_han_rebellion','张瑰、韩师德叛高骈并据复、岳州',4,'光启元年条；具体月日未载','复州、岳州','张瑰与韩师德叛离高骈，占据复州、岳州并自称刺史；陈儒请二人摄荆南军职，拟用以击雷满。',[('张瑰','叛离及受邀者'),('韩师德','叛离及受邀者'),('高骈','被叛离者'),('陈儒','邀二将者')])
event('zhang_imprisons_chen','张瑰逐陈儒并将其囚禁',4,'张瑰、韩师德受邀后；具体日未载','荆南','韩师德引兵入峡劫掠，张瑰返回荆南逐陈儒并取代之；陈儒欲奔行在，被张瑰挟回囚禁。',[('张瑰','逐陈儒并囚禁者'),('韩师德','入峡劫掠者'),('陈儒','被逐及被囚者')])
event('zhu_jingmei_old','朱敬玫先前杀将夺财，朝廷遣杨玄晦代之',5,'“先是”追叙；确年待考','荆南','《通鉴》追叙朱敬玫先前多次杀将及富商夺财，朝廷遣杨玄晦接替其职位。',[('朱敬玫','被替代者'),('杨玄晦','接替者')],year=None,note='“先是”所述确年待考；不把多次旧事统一定在885年。')
event('zhu_jingmei_killed','张瑰杀朱敬玫夺其财物',5,'杨玄晦代朱敬玫后；具体日未载','荆南','朱敬玫留居荆南，张瑰遣兵夜攻并杀之，夺其财物。',[('张瑰','遣兵杀人者'),('朱敬玫','被杀者')])
event('cheng_rui_guizhou','成汭以郭禹之名据归州',5,'光启元年庚申；月份依本段未明','归州','郭禹原名成汭，因先前杀人改名；张瑰欲杀他，郭禹率众出走，庚申袭据归州，自称刺史。',[('成汭','以郭禹名袭据归州者'),('张瑰','欲杀郭禹者')],note='原文明确郭禹即成汭，人物只建一个实体；本段“庚申”未单列月份，不套用前段正月。')
claim('person',people['成汭'],'aliases','成汭曾更名郭禹。',5,'禹，青州人成汭也，因杀人亡命，更其姓名。')
event('lu_guangchou_qianzhou','卢光稠陷虔州并用谭全播为谋主',6,'光启元年条；具体月日未载','虔州','卢光稠攻陷虔州并自称刺史，以同乡谭全播为谋主。',[('卢光稠','攻陷虔州者'),('谭全播','谋主')])
event('wang_xu_flees','王绪惧秦宗权，率光寿兵渡江',7,'光启元年正月条；具体日未载','光州、寿州、江南','秦宗权向光州刺史王绪索租赋，王绪无法缴纳；秦宗权发兵。王绪遂率光、寿兵渡江，驱使吏民随行，以刘行全为前锋，转掠江、洪、虔州。',[('秦宗权','索赋及发兵者'),('王绪','率众渡江者'),('刘行全','前锋')])
event('wang_xu_ting_zhang','王绪部攻陷汀、漳而未守住',7,'光启元年正月（“是月”）','汀州、漳州','王绪部当月攻陷汀、漳二州，但未能据守。',[('王绪','率军者'),('刘行全','王绪部前锋')],note='“是月”依前段正月定位；原文只明言王绪部陷二州，刘行全参与本段军队但未直言由其攻城。')
event('jiao_yi','朱全忠于焦夷败秦宗权',8,'光启元年正月后条；具体日未载','焦夷','秦宗权侵颍、亳；朱全忠在焦夷击败其军。',[('秦宗权','侵颍亳者'),('朱温','以朱全忠名义击败秦军者')])
event('court_fengxiang','僖宗车驾抵凤翔',9,'光启元年二月丙申','凤翔','皇帝车驾抵达凤翔。')
event('court_changan','僖宗车驾返回长安',9,'光启元年三月丁卯','长安','皇帝车驾返回京师长安；《通鉴》记城内荒废。')
event('era_guangqi','朝廷赦天下、改元光启',9,'光启元年三月己巳','长安','朝廷赦天下并改元光启。')
event('qin_proclaims','秦宗权称帝并置百官',10,'光启元年三月条；具体日未载',None,'秦宗权称帝，设百官。',[('秦宗权','称帝者')])
event('shi_pu_command','时溥受命统兵讨秦宗权',10,'秦宗权称帝后；具体日未载','蔡州方向','朝廷任时溥为蔡州四面行营兵马都统，令其讨伐秦宗权。',[('时溥','受命者'),('秦宗权','讨伐对象')])

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(1,11):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {1:'“之”承接884年末秦宗权条。',3:'郑绍业旧事及忠勇军冲突确年待考。',4:'雷满屡攻不强定885年单次事件。',5:'郭禹即成汭；“先是”旧事不强定885年。',7:'“是月”依本年正月条定位。',9:'二月抵凤翔、三月抵京师及改元分录。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,11):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=256,year=885,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph='zztj-v256-y0885-p011',coverage='卷256光启元年条前十段；本年尚未完成。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
