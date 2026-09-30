"""Curate consecutive Tongjian volume 260, year 896 paragraph 17."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 49))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0896-p017-p017', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias.update({'嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_260_0896_06_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁三年（896）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

# All actions remain in the order of the continuous primary paragraph.
event('lu_ying_delivers_suzhou_cheng_captured','陆郢以苏州城应杨行密，成及被俘',17,'896年五月癸未','苏州',
      '苏州常熟镇使陆郢以州城响应杨行密，刺史成及被俘。',[('陆郢','以城响应者'),('杨行密','受响应者'),('成及','被俘刺史')],
      quote='癸未，苏州常熟镇使陆郢以州城应杨行密，虏刺史成及。',note='州城指苏州，不将常熟镇误作州城；响应及俘获的具体执行者不另补。')
event('yang_values_cheng_books_appoints_sima','杨行密见成及所蓄图书药物，署行军司马',17,'896年五月苏州陷后条；确日未另载',None,
      '杨行密查看成及家中所蓄，只有图书和药物，认为他贤，带回并署为行军司马。',[('杨行密','察看并署职者'),('成及','受署者')],
      quote='行密阅及家所蓄，惟图书、药物，贤之，归，署行军司马。',note='归的目的地未明，不据后文馆府舍配现代扬州坐标；署职不推成及已自愿归附。')
event('cheng_ji_speaks_family_attempts_self_stabbing','成及哭诉家属在钱镠处，欲自刺',17,'896年五月受署后条；确日未另载',None,
      '成及拜而哭泣，称家中百口在钱镠处，愿以自己一身换家属免死，随后拔佩刀欲自刺。',[('成及','陈词并欲自刺者')],
      quote='及拜且泣曰：“及百口在钱公所。失苏州不能死，敢求富贵！愿以一身易百口之死！”引佩刀欲自刺。',note='百口为成及陈词中的称数，不建一百个无名人物；不推钱镠已杀家属、实际交换成立或自杀成功。')
event('yang_stops_cheng_houses_at_office','杨行密执成及手，止其自刺并馆于府舍',17,'896年五月成及欲自刺时；确日未另载',None,
      '杨行密立即握住成及的手，阻止其自刺，并安排他住在府舍。',[('杨行密','阻止并安置者'),('成及','获阻止安置者')],
      quote='行密遽执其手，止之，馆于府舍。',note='只记制止和安置，未载伤势不补受伤或死而复生，也未因此建立永久亲属关系。')
event('yang_visits_cheng_unarmoured_shares_meals','杨行密常单衣访成及并共饮食',17,'卷260乾宁三年条所述往来背景；起讫未载',None,
      '成及室内也有兵器，杨行密仍常穿单衣前往，与他一同饮食，书中记其无所疑。',[('杨行密','常往共饮膳者'),('成及','受访共饮膳者')],year=None,
      quote='其室中亦有兵仗，行密每单衣诣之，与之共饮膳，无所疑。',note='每为反复往来，未全部强定为五月癸未；单衣不发挥成完全无侍卫，书中评价无所疑不推一生信任。')
event('qian_recalls_gu_to_defend_xiling','钱镠闻苏州陷，召顾全武趋西陵防杨行密',17,'896年五月苏州陷后；确日未另载','西陵',
      '钱镠听闻苏州陷落，急召顾全武，令其赴西陵防备杨行密。',[('钱镠','下令召还者'),('顾全武','被召将')],
      quote='钱镠闻苏州陷，急召顾全武，使趋西陵备行密',note='这是钱镠下令，不作顾已离开越州并抵西陵；后文建议改变策略，未另建抵达事件。')
event('gu_proposes_yue_first_qian_accepts','顾全武请先取越州后复苏州，钱镠从之',17,'896年五月钱镠召还以后；确日未另载',None,
      '顾全武认为越州是敌方根本，请先取越州再恢复苏州，钱镠听从。',[('顾全武','提出先越后苏者'),('钱镠','采纳者')],
      quote='全武曰：“越州贼之根本，奈何垂克而弃之！请先取越州，后复苏州。”镠从之。',note='先取后复为策略请求并获采纳，不提前记越州已克或苏州已恢复；贼之根本属于顾的判断。')

supplements=[]
sk='wuyuebeishi-001-896-yue-siege'
prior=json.loads((YEAR/'part-05/content-batch.json').read_text())
B['sources'].append(next(dict(r) for r in prior['sources'] if r['key']==sk));reused.add(sk)
raw=(ROOT/'resources/originals/kanripo/KR2i0019/KR2i0019_001.txt').read_bytes()
(P/'sources'/(sk+'.txt')).write_bytes(raw)
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(next(dict(r) for r in json.loads((YEAR/'part-05/sources/manifest.json').read_text()) if r['key']==sk));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def supplement(code,text,q,note,kind):
    assert q in raw.decode()
    key='event_zztj_260_0896_'+code;ck=f'claim_zztj_260_0896_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation='卷1·乾宁三年五月癸未·KR2i0019_SBCK_001-21a',note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='吴越备史',primary_paragraph_id=Q[17]['id'],subject_key=key,relation=kind))
supplement('lu_ying_delivers_suzhou_cheng_captured','《吴越备史》同记五月癸未苏州陷、成及被执，并称台蒙等为陷城者。',
           '是月癸未越城将¶\n抜而䑓蒙等陷我姑蘇刺史成及𬒳執',
           '补书以台蒙等陷城，主书以陆郢应为叙事重点，不由此造第二次陷城；台蒙字形保原，不新增相似姓名人物。','adds')
supplement('gu_proposes_yue_first_qian_accepts','《吴越备史》同记钱镠拟分兵西陵，顾全武主张先拔越州再复苏州，钱镠从之。',
           '王乃召全武議将¶\n分兵西陵以備北㓂全武上言曰賊之根本繫于甌越豈¶\n以失一姑蘇而遂逭天討碩先抜越城然後復茂苑未遲¶\n王從之',
           '碩先保留底本疑字不静默改愿先；该书记召议分兵与主书使趋的措辞差别保留，结论均为从先越后苏。','corroborates')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text());ledger[16].update(event_keys=used[17],batch_key=B['batch_key'],review='陆郢以城应、成及被俘、杨阅藏署司马、成陈词欲自刺、杨制止安置、常单衣饮膳、钱召顾和先越后苏分录；反复往来未强定896，吴越补书同日陷城与议策独立引用。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=896,primary_source_key=source,paragraphs=[Q[17]['id']],next_paragraph=Q[18]['id'],coverage='第17段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
