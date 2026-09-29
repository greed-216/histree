"""Curate consecutive Tongjian volume 256, year 886 paragraphs 11–20."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 57))
B = {'format_version': 1, 'batch_key': 'zztj-v256-y0886-p011-p020', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_256_0886_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷256·光启二年（886）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷256光启二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=886,note=None,quote=None):
    key='event_zztj_256_0886_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_256_0886_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('fengxiang_memorial','凤翔百官请诛田令孜及韦昭度',11,'光启二年三月癸未','凤翔',
      '萧遘等凤翔百官上表列田令孜及其党韦昭度的罪状，请求诛杀二人。',
      [('萧遘','上表者'),('田令孜','被指控者'),('韦昭度','被指控者')],
      note='罪状属于萧遘等人的上表内容；本事件只确定上表及其请求。')
event('wei_zhaodu_background','韦昭度此前经僧澈结识宦官而为相',11,'“初”追叙；确年待考',None,
      '《通鉴》追叙韦昭度经供奉僧澈结交宦官而获相位；其师知玄不赞同僧澈的行为。',
      [('韦昭度','受相位者'),('僧澈','引见者'),('知玄','不赞同者')],year=None,
      note='本段“初”所叙旧事，不能定为886年；知玄态度按史书转述，不扩写动机。')
event('court_xingyuan','车驾抵达兴元',12,'光启二年三月丙申','西县、兴元',
      '山南西道监军严遵美在西县迎接皇帝，丙申车驾抵达兴元。',[('严遵美','迎驾者')])
event('kong_du_chancellors','孔纬、杜让能获任同平章事',13,'光启二年三月戊戌',None,
      '朝廷以孔纬、杜让能并为兵部侍郎、同平章事。',
      [('孔纬','受任者'),('杜让能','受任者')])
event('li_chan_fengzhou','李鋋等在凤州击败邠军',14,'光启二年三月条；具体日未载','凤州',
      '保銮都将李鋋等在凤州击败邠军。',[('李鋋','领兵者')])
event('wang_chongrong_grain','朝廷命王重荣调粮，王重荣拒奉诏',15,'光启二年三月条；具体日未载','河中',
      '朝廷加王重荣应接粮料使，令从本道调谷十五万斛供国用；王重荣上表称田令孜未被诛，拒绝奉诏。',
      [('王重荣','受命、上表及拒诏者'),('田令孜','王重荣所称拒诏理由')],
      note='十五万斛为诏令拟调额，并非已交纳量；田令孜未诛是王重荣表章所言理由。')
event('lu_wo_hanzhong','卢渥任山南西道留后',16,'光启二年三月条；具体日未载','山南西道',
      '朝廷任尚书左丞卢渥为户部尚书，并充山南西道留后。',[('卢渥','受任者')])
event('yan_zunmei_privy','严遵美任内枢密使',16,'光启二年三月条；具体日未载',None,
      '朝廷任严遵美为内枢密使。',[('严遵美','受任者')])
event('roads_sanquan_heishui','王建守三泉，晋晖、张造屯黑水修栈道',16,'光启二年三月条；具体日未载','三泉、黑水',
      '朝廷派王建率部守三泉、晋晖与张造率四都兵屯黑水，修栈道以通往来；王建遥领壁州刺史。',
      [('王建','守三泉并遥领壁州者'),('晋晖','屯黑水者'),('张造','屯黑水者')],
      note='“遥领”不是实际赴壁州治理；原文“自此始”为史家概括。')
event('zheng_junli_hanzhou','郑君立攻陷汉州后战败身死',17,'光启二年三月后条；具体日未载','汉州、成都方向',
      '郑君立自遂州起兵，攻陷汉州、进向成都；陈敬瑄派李顺之迎战，郑君立战败身死。',
      [('郑君立','起兵、攻城及战死者'),('陈敬瑄','派将迎战者'),('李顺之','迎战者')])
event('gao_renhou_killed','陈敬瑄派维、茂羌军杀高仁厚',17,'郑君立之乱后；具体日未载','东川方向',
      '陈敬瑄猜疑东川节度使高仁厚，发维、茂羌军攻之，高仁厚被杀。',
      [('陈敬瑄','发兵者'),('高仁厚','被杀者')],
      note='本段先记猜疑，再记发兵杀高仁厚；未载确切杀害地点。')
event('zhu_mei_succession_plan','朱玫劝萧遘改立李氏宗室，萧遘拒绝',18,'光启二年春；具体日未载',None,
      '朱玫与萧遘谈及皇帝受田令孜控制，提出改立李氏宗室。萧遘认为罪在田令孜，不愿参与废立；朱玫随后公开声称要拥立一名李氏王。',
      [('朱玫','倡议改立者'),('萧遘','拒绝者'),('田令孜','双方谈论对象')],
      note='双方话语中关于战死比例、皇帝过失与田令孜的评价是当事人主张，不单独当作核实事实。')
event('li_yun_regency','朱玫迫凤翔百官奉襄王煴监国',19,'光启二年夏四月壬子','凤翔、石鼻驿',
      '朱玫迫凤翔百官奉襄王煴权监军国事，令其承制封拜，并在石鼻驿使百官盟誓。',
      [('朱玫','胁迫百官者'),('李煴','被奉监国者')],
      note='“权监军国事”按原文保留，尚非把李煴称为正式登基皇帝。')
event('li_yun_investiture','襄王煴受册，朱玫率百官奉之还京',19,'光启二年夏四月乙卯','凤翔、京师方向',
      '萧遘辞撰册文，郑昌图代撰。乙卯襄王煴受册；朱玫自兼左右神策十军使，率百官奉煴返回京师。',
      [('李煴','受册者'),('朱玫','率百官者'),('萧遘','辞撰册文者'),('郑昌图','代撰册文者')])
event('zheng_changtu_finance','郑昌图获任同平章事并掌三司',19,'光启二年夏四月乙卯后','京师',
      '朱玫一方任郑昌图同平章事、判度支盐铁户部，使其掌三司事务。河中百官崔安潜等上笺祝贺襄王煴受册。',
      [('郑昌图','受任并掌三司者'),('崔安潜','上笺者')],
      note='任命出自朱玫拥立的襄王煴政权安排，与僖宗行在任命区分。')
event('tian_leaves_court','田令孜荐杨复恭继任，自往依陈敬瑄',20,'光启二年夏四月后条；具体日未载','西川',
      '田令孜荐杨复恭任左神策中尉、观军容使，自除西川监军使，离开行在去依附陈敬瑄。',
      [('田令孜','荐人并赴西川者'),('杨复恭','受荐者'),('陈敬瑄','被投靠者')])
event('yang_fugong_assignments','杨复恭出任王建等四人为外州刺史',20,'田令孜离开后；具体日未载','利州、集州、万州、忠州',
      '杨复恭排斥田令孜党人，任王建为利州刺史、晋晖为集州刺史、张造为万州刺史、李师泰为忠州刺史。',
      [('杨复恭','安排任命者'),('王建','受任利州者'),('晋晖','受任集州者'),('张造','受任万州者'),('李师泰','受任忠州者')],
      note='原文“出”表外放，不据此断定四人已赴任。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(11,21):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {11:'癸未上表与“初”所述韦昭度旧事分录。',15:'十五万斛为诏调数，非交纳实数。',16:'王建遥领壁州不等于赴任。',17:'郑君立与郑君雄非一人；高仁厚死亡地点未载。',18:'朱玫、萧遘对话按各自主张整理，不把言辞中的数字当核实战损。',19:'权监国与乙卯受册及郑昌图任命分录；与僖宗行在政权区分。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,21):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=256,year=886,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(11,21)],next_paragraph='zztj-v256-y0886-p021',coverage='卷256光启二年条第11至20段；本年尚未完成。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
