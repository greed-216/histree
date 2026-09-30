"""Curate consecutive Tongjian volume 258, year 889 paragraphs 9–16."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 25))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0889-p009-p016', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-258-889'
B['sources'] = [dict(key=source,title='资治通鉴·卷258',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/4d35696319726b523bd624f2370cb2cf7faa6b43/resources/derived/tongjian/258.txt',note='卷258龙纪元年起；书、卷、年、段落及行号见批次账本。')]
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
alias = {'唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0889_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·龙纪元年（889）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷258龙纪元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=889,note=None,quote=None):
    key='event_zztj_258_0889_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_258_0889_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('ruan_jie_dies','阮结卒，成及代润州制置使',9,'889年五月甲辰','润州',
      '润州制置使阮结去世，钱镠以静江都将成及代之。',[('阮结','去世者'),('钱镠','任用者'),('成及','代任制置使者')])
event('li_takes_ci_ming','李罕之李存孝拔磁洺二州',10,'889年六月；发兵具体日未载','磁州、洺州',
      '李克用大发兵，遣李罕之、李存孝攻孟方立，六月攻取磁、洺二州。',
      [('李克用','遣军者'),('李罕之','攻城将领'),('李存孝','攻城将领'),('孟方立','被攻方主将')])
event('liulipo_battle','孟方立援军败于琉璃陂',10,'889年六月条；具体日未载','琉璃陂',
      '孟方立遣马溉、袁奉韬率军抵抗，在琉璃陂大败，两将被擒；李克用乘胜进攻邢州。',
      [('孟方立','遣援军者'),('马溉','败被擒将领'),('袁奉韬','败被擒将领'),('李克用','乘胜进攻者')],note='原文记兵数数万，未独立核实；不推定两被擒将领的死亡。')
event('meng_fangli_suicide','孟方立饮药死，孟迁被奉留后',10,'889年六月条；邢州被攻后','邢州',
      '《通鉴》记孟方立因诸将不为所用，惭惧饮药而死；其弟、摄洺州刺史孟迁被众人奉为留后，向朱全忠求援。',
      [('孟方立','饮药去世者'),('孟迁','被奉留后及求援者'),('朱温','以朱全忠名义受求援者')],note='猜忌、惭惧及得士心为书中叙述；“众奉”不写成朝廷诏命。')
rk='relationship_person_孟方立_person_孟迁_兄长'
B['person_relationships'].append(dict(key=rk,person_a_key=people['孟方立'],person_b_key=people['孟迁'],relation_type='兄长',description='《通鉴》称孟迁为孟方立之弟；孟方立是孟迁的兄长。',status='draft'))
claim('person_relationship',rk,'description','孟方立是孟迁的兄长。',10,quote='弟摄洺州刺史迁，素得士心，众奉之为留后，求援于硃全忠。')
event('wang_qianyu_aids_xing','王虔裕间道援邢州',10,'889年六月条；孟迁求援后','魏博、邢州',
      '朱全忠向魏博借道遭罗弘信拒绝，改遣王虔裕率精兵数百，间道进入邢州共同守城。',
      [('朱温','以朱全忠名义遣援者'),('罗弘信','拒借道者'),('王虔裕','间道入援将领'),('孟迁','邢州守方留后')],note='“间道”不推具体路线；数百为书载人数。')
event('zhou_jinsi_expels_zhao','宣州饥困，周进思逐赵锽',11,'889年六月后条；具体日未载','宣州',
      '杨行密围宣州，城中粮食耗尽，《通鉴》记人相啖；周进思据城逐赵锽，赵锽欲奔广陵，被田頵追擒。',
      [('杨行密','围城者'),('周进思','逐赵锽者'),('赵锽','被逐及被擒者'),('田頵','追擒将领')])
event('yang_enters_xuanzhou','宣州执周进思降，徐温赈饥',11,'889年六月后条；逐赵锽后未几','宣州',
      '城中拘执周进思投降，杨行密入宣州。诸将争取金帛，徐温独据米囷，煮粥赈济饥民。',
      [('周进思','被执者'),('杨行密','受降入城者'),('徐温','煮粥赈饥者')])
claim('person',people['徐温'],'biography','《通鉴》称徐温为朐山人。',11,quote='温，朐山人也。')
event('zhou_ben_retained','杨行密释周本并任裨将',11,'889年六月后条；宣州战事中具体日未载','宣州',
      '赵锽部将周本被杨行密俘获后释放，并被任为裨将；《通鉴》称周本为宿松人，勇冠军中。',
      [('周本','被俘获释放及任用者'),('杨行密','释放任用者'),('赵锽','周本原所属主将')],note='勇冠军中为书中评价，不据释放推成永久政治效忠。')
event('li_decheng_marriage','杨行密以宗女妻李德诚',11,'889年六月后条；赵锽败后','',
      '赵锽兵败后，李德诚仍随从不去；杨行密以宗女嫁给李德诚。《通鉴》称李德诚为西华人。',
      [('李德诚','随从赵锽及受婚者'),('赵锽','被随从者'),('杨行密','宗女婚配安排者')],note='宗女未具名，且未说明与杨行密的具体亲等，不新建妻子、父女或叔侄关系。')
event('yang_xuanshe_observer','杨行密受任宣歙观察使',11,'889年六月后条；具体日未载','宣歙',
      '杨行密上表朝廷，朝廷诏以其为宣歙观察使。',[('杨行密','上表及受任者')],note='观察使不提前改记为后来的节度使。')
event('zhao_huang_killed','杨行密从袁袭议杀赵锽',11,'889年六月后条；宣州战后','',
      '朱全忠因与赵锽有旧，遣使索要赵锽；杨行密咨询袁袭，采纳其斩首以送朱全忠的建议。',
      [('朱温','以朱全忠名义索要赵锽者'),('赵锽','被杀者'),('杨行密','采纳杀人建议者'),('袁袭','建议斩首者')],note='“有旧”不足以细化为同盟；记录袁袭建议及杨行密从之，不补具体处斩地点。')
event('yuan_xi_death','袁袭卒，杨行密哀悼',11,'宣州战后未几；具体年日待核','',
      '袁袭不久去世，杨行密哭悼，称失去股肱，并将其短寿与屡劝杀人联系。',
      [('袁袭','去世者'),('杨行密','哭悼及评论者')],year=None,note='“未几”无确年；杨行密评论为当事人言论，不作为死亡原因。')
event('cai_chou_surrenders_lu','蔡俦以庐州降孙儒',12,'889年六月后条；具体日未载','庐州',
      '孙儒遣兵攻庐州，蔡俦以州降孙儒。',[('孙儒','遣军受降者'),('蔡俦','以州投降者')])
event('zhu_zhen_captures_xiao','朱珍据萧县与时溥相拒',13,'889年七月前；具体日未载','萧县',
      '朱珍攻取萧县并据守，与时溥相拒，朱全忠欲亲自前往。',
      [('朱珍','攻取据守者'),('时溥','相拒对手'),('朱温','以朱全忠名义拟亲临者')],note='底本本句“时浦”，后文作时溥，按同一战局复用时溥，保留底本异字。')
event('zhu_zhen_kills_li_tangbin','朱珍杀李唐宾并报谋叛',13,'889年七月前；具体日未载','萧县军中',
      '朱珍命诸军修葺马厩，李唐宾部将严郊怠慢，军吏责备；李唐宾向朱珍申诉，朱珍怒其无礼而杀之，向朱全忠报告称李唐宾谋叛。',
      [('朱珍','专杀及报告者'),('李唐宾','被杀者'),('严郊','怠慢修厩者'),('朱温','以朱全忠名义接报者')],note='谋叛为朱珍的报告，不作独立证实的事实；未具名军吏不创实体。')
event('jing_xiang_calms_army','敬翔缓报并谋慰抚军中',13,'889年七月前；李唐宾被杀后','',
      '敬翔担忧朱全忠仓促处置，留报信者到夜间才禀报，又建议假意拘收李唐宾妻子入狱并遣骑慰抚军中；朱全忠采纳，军中始安。',
      [('敬翔','延报及画策者'),('朱温','以朱全忠名义采纳者'),('李唐宾','其家属被拘对象')],note='妻子在古文中指妻与子女，原文无姓名，不创家属人物；“诈收”保留计策性质。')
event('zhu_zhen_executed','朱全忠诛朱珍，霍存等求情',13,'889年七月；赴萧县途中','赴萧县途中',
      '朱全忠赴萧县，未到时拘执迎接的朱珍，以专杀罪责诛之；霍存等数十名将领叩头求情，朱全忠发怒掷床，诸将退下。',
      [('朱温','以朱全忠名义诛杀者'),('朱珍','被诛者'),('霍存','求情将领')],note='“未至”只支持尚未到萧县，不能据此定位近郊或具体地点。')
event('pang_replaces_zhu_zhen','庞师古代朱珍为都指挥使',13,'889年七月丁未','萧县',
      '朱全忠抵达萧县，以庞师古代朱珍为都指挥使。',[('朱温','以朱全忠名义任用者'),('庞师古','都指挥使受任者')])
event('zhu_rain_withdrawal','朱全忠攻时溥遇雨退兵',13,'889年八月丙子','时溥军壁',
      '朱全忠进攻时溥营壁，遇大雨后撤军。',[('朱温','以朱全忠名义进攻撤军者'),('时溥','被攻军营主将')])
event('wang_jingwu_dies','王敬武卒，王师范被推平卢留后',14,'889年十月','平卢',
      '平卢节度使王敬武去世，军中推其子、时年十六的王师范为留后，棣州刺史张蟾不从。',
      [('王敬武','去世者'),('王师范','被军中推立者'),('张蟾','拒从者')],note='十六为史载年龄，不据此反算精确出生年；军中推举不当作朝廷任命。')
rk='relationship_person_王敬武_person_王师范_父亲'
B['person_relationships'].append(dict(key=rk,person_a_key=people['王敬武'],person_b_key=people['王师范'],relation_type='父亲',description='《通鉴》889年条称王师范为王敬武之子；王敬武是王师范的父亲。',status='draft'))
claim('person_relationship',rk,'description','王敬武是王师范的父亲。',14,quote='平卢节度使王敬武薨。子师范，年十六，军中推为留后')
event('cui_anqian_pinglu','崔安潜受任平卢，张蟾迎讨王师范',14,'889年十月；具体日未载','平卢、棣州',
      '朝廷命太子少师崔安潜兼侍中、充平卢节度使；张蟾迎其至州，共讨王师范。',
      [('崔安潜','平卢节度使受任及讨伐者'),('张蟾','迎任及共讨者'),('王师范','被讨者')],note='“至州”依张蟾为棣州刺史的上下文，不写成已入青州或已实控平卢。')
event('du_ruxiu_suzhou','杜孺休任苏州刺史，钱镠留沈粲制置',15,'889年十月后条；具体日未载','苏州',
      '朝廷以给事中杜孺休为苏州刺史，钱镠不悦，以知州事沈粲为制置指挥使。',
      [('杜孺休','苏州刺史受任者'),('钱镠','另任沈粲者'),('沈粲','制置指挥使受任者')],note='不悦是书载反应，不推定拒接诏命或刺史未到任。')
event('tian_jun_attacks_changzhou','杨行密遣田頵攻常州',16,'889年十月后条；具体日未载','常州',
      '杨行密遣马步都虞候田頵等进攻常州。',[('杨行密','遣军者'),('田頵','进攻将领')],note='本段只记进攻，攻城结果在后续段落另录。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={10:'磁洺攻取、琉璃陂战斗、孟方立死及孟迁推举、借道拒绝和援邢州分录；兄长关系按明文。',11:'宣州攻守、赈饥、任用、婚配、赵锽处死及袁袭去世分录；宗女无姓名亲等不推；袁袭卒用未定年。',13:'时浦按上下文复用时溥；李唐宾谋叛为朱珍报告；妻子指家属；朱珍诛杀与庞师古接任及八月退兵分别记录。',14:'十六为史载年龄不反算出生年；军中推留后与朝廷命节度使区分。'}
for n in range(9,17):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
    if n in reviews:ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,17):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=889,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph='zztj-v258-y0889-p017',coverage='卷258龙纪元年第9—16段连续录入；本年共24段尚未完结。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
