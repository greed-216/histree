"""Curate consecutive Tongjian volume 257, year 887 paragraphs 1–8."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 60))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0887-p001-p008', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
people, used, reused = {}, {}, set()

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_257_0887_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·光启三年（887）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('xu_yue_suzhou','徐约逐张雄，张雄率部逃海',1,'光启三年夏四月甲辰朔','苏州、海上',
      '徐约逐苏州刺史张雄；张雄率部逃入海中。',
      [('徐约','驱逐者'),('张雄','被逐者')],
      note='承接上卷末周宝诱徐约攻苏州的追叙；本段明确记四月甲辰朔之结果。')
event('gao_sends_bi','高骈遣毕师铎屯高邮',2,'光启三年四月乙巳前；具体日未载','高邮',
      '高骈听闻秦宗权将攻淮南，遣毕师铎率兵屯高邮。',
      [('高骈','遣军者'),('秦宗权','被传将攻淮南者'),('毕师鐸','领军者')],
      note='秦宗权将攻为当时传闻或预期，不写成已攻淮南。')
event('bi_lv_conflict','毕师铎与吕用之关系恶化',2,'毕师铎赴高邮前；具体年日未载','广陵、高邮方向',
      '毕师铎因吕用之掌权并探访其妾而愤惧；赴高邮前，吕用之反而厚待，毕师铎更加疑虑。',
      [('毕师鐸','与吕用之生隙者'),('吕用之','与毕师铎生隙者')],
      note='妻妾未具名；文中关于暗害的担心是毕师铎的主观疑惧，不当作吕用之已下杀令。')
event('bi_zheng_conspire','毕师铎联郑汉章举兵',2,'光启三年四月乙巳前夜','高邮',
      '毕师铎疑吕用之将害己，与郑汉章会合；郑汉章发镇兵及居民跟随。张神剑被毕师铎问及密报，称并无文书，后与之共同起事。',
      [('毕师鐸','谋举兵者'),('郑汉章','率兵加入者'),('张神剑','高邮镇遏使；参与谋议者'),('吕用之','被讨伐目标')],
      note='“用之将害己”是毕师铎的疑惧及传言；“四十三郎”未记本名，不创具名人物。')
claim('person',people['张神剑（高邮）'],'aliases','高邮镇遏使张神剑名雄。',2,'神剑名雄，人以其善用剑，故谓之“神剑”。',
      note='与卷256苏州刺史张雄是否同人，本段不能证明；目前用“张神剑（高邮）”作消歧标签，暂不合并。')
event('bi_appointed_campaign','毕师铎被推行营使，发檄后出高邮',2,'光启三年四月乙巳至戊申','高邮、淮南',
      '乙巳众人推毕师铎为行营使，发文告称要诛吕用之、张守一、诸葛殷；郑汉章为副使、张神剑为都指挥使。戊申毕师铎、郑汉章率军离高邮。',
      [('毕师鐸','被推主将及出兵者'),('郑汉章','副使及出兵者'),('张神剑','都指挥使'),('吕用之','文告讨伐对象'),('张守一','文告讨伐对象'),('诸葛殷','文告讨伐对象')],
      note='文告中的罪名与目标是毕师铎阵营宣称，不能当作三人已被处决或罪名核实。')
event('lv_hides_report','吕用之隐瞒毕师铎起事军情',3,'光启三年四月庚戌','广陵',
      '侦骑把毕师铎军情报告高骈，吕用之将报告隐瞒。',
      [('高骈','受报告者'),('吕用之','隐瞒者')])
event('zhu_zhen_returns','朱珍募兵归大梁并袭青州得马',4,'光启三年四月辛亥','淄青、青州、大梁',
      '朱珍赴淄青募兵，又袭青州取马；辛亥率部回大梁。朱全忠得知后喜。',
      [('朱珍','募兵及袭青州者'),('朱温','以朱全忠名义接纳者')],
      note='“万余人”“千匹”照书载，不推为精确实到数。')
event('zhu_qinxian_camp','朱全忠突击秦贤营寨',4,'光启三年四月辛亥后','汴州、板桥',
      '秦贤、张晊率蔡州军攻汴州周边；朱全忠趁秦贤未防备率军突击，连取四寨。',
      [('秦贤','营寨被攻者'),('张晊','蔡军另一部统领'),('朱温','以朱全忠名义突击者')],
      note='“斩万余级”是本书战争叙事数字，不据此核定总伤亡。')
event('guo_yan_recruits','朱全忠遣郭言赴河阳等地募兵',4,'秦贤营寨被攻后；具体日未载','河阳、陕、虢',
      '朱全忠遣郭言往河阳、陕、虢募兵，郭言带兵返回。',
      [('朱温','以朱全忠名义遣将者'),('郭言','募兵者')],
      note='“万余人”照原文，不推为实际战斗员额。')
event('bi_guangling_assault','毕师铎兵至广陵城下，吕用之出战后闭城',5,'光启三年四月壬子','广陵',
      '毕师铎军到广陵城下；吕用之率兵出城作战使对方暂退，随后断桥闭门守城。',
      [('毕师鐸','攻城方'),('吕用之','出战及守城者')])
event('gao_questions_lv','高骈知毕师铎之变，质问吕用之',5,'光启三年四月壬子','广陵延和阁',
      '高骈听闻毕师铎起事后质问吕用之；吕用之淡化军情，高骈表示已察觉其妄言。',
      [('高骈','质问者'),('吕用之','答辩者')],
      note='吕用之所称毕师铎军“思归”是其答辩，并非对军情的核实。')
event('bi_requests_qin_yan','毕师铎向宣州秦彦求援',5,'光启三年四月癸丑','广陵、宣州',
      '毕师铎遣孙约与其子赴宣州请求秦彦援军，许诺攻下广陵后迎秦彦为帅。',
      [('毕师鐸','求援者'),('孙约','出使者'),('秦彦','受请求者')],
      note='底本“观使察秦彦”疑有转录讹字；仅按明示姓名秦彦及求援行为整理，不扩写完整官衔。')
event('gao_peace_letter','高骈命吕用之遣人持札劝毕师铎',6,'光启三年四月癸丑后','广陵',
      '高骈向吕用之问清事由，表示先遣可信将领持手札劝毕师铎，若不从再另行处置。',
      [('高骈','提出劝解者'),('吕用之','奉命安排者'),('毕师鐸','劝解对象')])
event('xu_kan_killed','毕师铎杀吕用之所遣许戡',6,'光启三年四月甲寅','广陵城外',
      '吕用之派许戡带高骈手札、誓状与酒食慰劳毕师铎；毕师铎拒绝接谈，将许戡杀害。',
      [('吕用之','遣使者'),('许戡','被杀使者'),('毕师鐸','下令杀使者')])
event('bi_letter_burned','毕师铎射书入城，吕用之焚毁',6,'光启三年四月乙卯','广陵',
      '毕师铎将书信射入城内，吕用之未开读即焚毁。',
      [('毕师鐸','送书者'),('吕用之','焚书者')],
      note='信件内容未载，不能补写。')
event('gao_lv_break','吕用之带甲士见高骈，高吕决裂',7,'光启三年四月丁巳','广陵延和阁',
      '吕用之带兵进入高骈所在的延和阁下，高骈惊而责其无故带兵，命逐出。吕用之离开子城，自此两人决裂。',
      [('吕用之','带兵入见者'),('高骈','责令退出者')])
event('gao_jie_command','高骈任其从子高杰掌都牢城',7,'光启三年四月戊午','广陵',
      '高骈与从子高杰密议军务，任高杰为都牢城使并给亲信兵。',
      [('高骈','任命者'),('高杰','受任者')])
rel='relationship_'+people['高骈']+'_'+people['高杰']+'_从子'
B['person_relationships'].append(dict(key=rel,person_a_key=people['高骈'],person_b_key=people['高杰'],relation_type='从子',description='《通鉴》卷257称高杰为高骈从子。',status='draft'))
claim('person_relationship',rel,'description','高杰为高骈从子。',7,'骈召其从子前左金吾卫将军杰密议军事')
event('lv_forces_civilians','吕用之强迫广陵民众登城守卫',8,'光启三年四月戊午前后','广陵',
      '吕用之命人搜捕城中壮丁，连朝士书生也被迫登城守卫，常日不得休息；家人难以找到他们。',
      [('吕用之','下令者')],
      note='原文未记具体人数与持续天数，故不补写。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(1,9):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {1:'承上卷徐约攻苏州续事，四月甲辰朔有结果。',2:'张神剑名雄，与苏州刺史张雄是否同人未证，暂消歧；“要C061”原样保留不释义。',4:'募兵与突击秦贤营分录，战报数字照书载。',5:'吕用之淡化军情是其答辩；“观使察秦彦”疑讹。',6:'许戡被杀与来书被焚分录，书信内容不补。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=887,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph='zztj-v257-y0887-p009',coverage='卷257光启三年条前八段；本年续录。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
