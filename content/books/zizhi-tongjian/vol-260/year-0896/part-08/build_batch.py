"""Curate consecutive Tongjian volume 260, year 896 paragraph 21."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 49))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0896-p021-p021', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias.update({'王宗播':'许存','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_260_0896_08_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁三年（896）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('cheng_xu_take_river_counties','成汭许存溯江，取滨江州县',21,'896年五月条；确日未载','滨江州县',
      '荆南节度使成汭与其将许存溯江略地，取滨江州县。',[('成汭','率部略地者'),('许存','略地将')],quote='荆南节度使成汭与其将许存溯江略地，尽取滨江州县。',note='滨江是主书概括范围，不补未列州县或明确疆域边界。')
event('wang_jianzhao_retreats_fengdu','王建肇弃黔州，收余众保丰都',21,'896年成汭许存略地条；确日未载','黔州、丰都',
      '武泰节度使王建肇放弃黔州，收集余众，退保丰都。',[('王建肇','弃黔退保者')],quote='武泰节度使王建肇弃黔州，收馀众保丰都。')
event('xu_captures_yu_fu_variant','许存引兵西取谕、涪二州',21,'896年溯江略地后条；确日未载','谕、涪二州（底本）',
      '许存又率兵向西，攻取底本所记“谕、涪二州”；“谕”与补书“渝”存在字形差异。',[('许存','引兵西取者')],quote='存又引兵西取谕、涪二州',note='不静默改底本谕为渝；十国春秋卷35明确作渝涪，独立补证，不配现代坐标。')
event('cheng_appoints_zhao_xu_qian_wan','成汭任赵武黔中留后、许存万州刺史',21,'896年取二州以后；确日未载','黔中、万州',
      '成汭任其将赵武为黔中留后，许存为万州刺史。',[('成汭','任职者'),('赵武','受黔中留后者'),('许存','受万州刺史者')],quote='汭以其将赵武为黔中留后，存为万州刺史。',note='赵武新建同名主体，不以相近名补别名；黔中留后不改写正式节度使。')
event('cheng_receives_spy_report_on_xu','成汭使人探察许存，获不治州事蹴鞠报告',21,'896年许存任万州刺史后条；确日未载',None,
      '成汭得知许存不得志，派人探察，获报告称许存不处理州务，每天出外蹴鞠。',[('成汭','遣探并受报告者'),('许存','受探察者')],quote='汭知存不得志，使人诇之，曰：“存不治州事，日出蹴鞠。”',note='不治州事和蹴鞠归于探察报告，不单凭此定许存实际怠职；侦者未名不造人物。')
event('cheng_suspects_xu_escape','成汭认为许存蹴鞠是在准备逃跑',21,'896年接探察报告后；确日未载',None,
      '成汭认为许存将要逃走，蹴鞠是在先练足力。',[('成汭','提出猜测者')],quote='汭曰：“存将逃，先匀足力也。”',note='存将逃及匀足力均为成汭推测，不当作许存已经明确公布的计划或现代体能解释。')
event('cheng_attacks_xu_flees_maoba','成汭遣兵袭许存，许存弃城逃屯茅坝',21,'896年探察及猜测后条；确日未载','茅坝',
      '成汭派兵袭击许存，许存弃城逃走，其部众逐渐归来，屯驻茅坝。',[('成汭','遣袭者'),('许存','逃走并屯驻者')],quote='遣兵袭之，存弃城走；其众稍稍归之，屯于茅坝。',note='其众归之是部众归附许存，不误作许存归成汭；弃城承万州但未补确切逃路线。')
event('zhao_attacks_fengdu_wang_xu_surrender','赵武攻丰都，王建肇许存降王建',21,'896年茅坝屯驻以后条；数攻及请降确日未载','丰都',
      '赵武多次攻丰都，王建肇无法继续守城，与许存都投降王建。',[('赵武','攻丰都者'),('王建肇','不能守而降者'),('许存','归降者'),('王建','受降者')],quote='赵武数攻丰都，王建肇不能守，与存皆降于王建',note='两人归同一主君不推彼此盟誓；数攻为本段连续战事概括，不补攻城次数。')
event('wang_intends_kill_xu_gao_objects','王建忌许存欲杀，高烛谏阻',21,'896年许存归降后条；确日未载',None,
      '王建忌许存勇略，想杀他；掌书记高烛以许存穷困来归、王建应招揽英雄为由劝阻。',[('王建','欲杀并受谏者'),('许存','被拟杀者'),('高烛','谏阻者')],quote='建忌存勇略，欲杀之，掌书记高烛曰：“公方总揽英雄以图霸业，彼穷来归我，奈向杀之！”',note='欲杀未作已经杀害，奈向保底本不静默改何；图霸业为高烛劝说语。')
event('wang_sends_xu_shu_orders_surveillance','王建遣许存戍蜀州，密命王宗绾察之',21,'896年高烛劝阻后条；确日未载','蜀州',
      '王建令许存守蜀州，又秘密令知蜀州王宗绾观察他。',[('王建','遣戍并密令者'),('许存','被遣戍观察者'),('王宗绾','受命观察者')],quote='建使戍蜀州，阴使知蜀州王宗绾察之。',note='不误读许存已任蜀州刺史；知蜀州是王宗绾，许存为戍守。')
event('wang_zongwan_reports_xu_spared_renamed','王宗绾密言许存良将才，王建舍之改名王宗播',21,'896年蜀州观察后条；确日未载',None,
      '王宗绾密报许存忠勇廉厚、有良将才能，王建放弃杀他，改其姓名为王宗播。王宗绾始终未使他知自己曾助其免死。',[('王宗绾','密报者'),('王建','舍杀改名者'),('许存','免死改名者')],quote='宗绾密言存忠勇廉厚，有良将才，建乃舍之，更其姓名臼王宗播，而宗绾竟不使宗播知其免己也。',note='臼保原文字形；上下文与十国春秋均明示改姓名为王宗播，复用许存key，不新增王宗播人物；评价是宗绾密报。')
claim('person',people['许存'],'aliases','许存被王建改名王宗播；同一人物，保原key及UUID并补王宗播检索别名。',21,
      quote='建乃舍之，更其姓名臼王宗播',note='臼疑为曰，摘录原字不改。补书卷39明记本姓许名存及更其姓名曰王宗播，身份交叉支持；发布后另行受保护合并别名。')
event('liu_xiuye_counsels_zongbo_caution','柳修业常劝王宗播慎静免祸',21,'卷260乾宁三年条内往事及常行概述；起讫未载',None,
      '柳修业多次劝王宗播谨慎安静，以免招祸。',[('柳修业','劝慎静者'),('许存','受劝者')],year=None,
      quote='宗播元从也目官柳修业，每劝宗播慎静以免祸。',note='元从也目官疑有转录讹字，未据此确定完整职位。补书作孔目官栁脩業另列出处。每未全定896。')
event('zongbo_leads_hard_fights_declines_boasting','王宗播后来先身战强敌，有功称病不自伐',21,'其后概述；战事和终身起讫未载',None,
      '主书概述王宗播后来为王建将，遇其他将领畏惧的强敌常亲自争先，有功就称病而不自夸，得以功名终。',[('许存','后事所述将领'),('王建','所事主君')],year=None,
      quote='其后宗播为建将，遇强敌诸将所惮者，以身先之。及有功，辄称病，不自伐，由是得以功名终。',note='其后辄和功名终是跨时总结，未全部置896，不补具体战役、死亡年或医学病因。')

from urllib.parse import quote as urlquote
supplements=[]
def addsource(sk,volume):
    path=f'resources/originals/kanripo/KR2i0021/KR2i0021_{volume:03}.txt';raw=(ROOT/path).read_bytes();url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')
    (P/'sources'/(sk+'.txt')).write_bytes(raw)
    B['sources'].append(dict(key=sk,title=f'十国春秋·卷{volume}·许存王宗播相关段',source_type='primary',author='吴任臣',edition='四库全书电子文本；原字换行保留，未核纸本。',url=url,note='具体卷叶与书间时间及字形差异见引用。'))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='none'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n');return raw.decode()
def extra(sk,raw,table,key,field,text,q,citation,note,kind='adds'):
    assert q in raw;ck=f'claim_zztj_260_0896_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=citation,note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='十国春秋',primary_paragraph_id=Q[21]['id'],subject_key=key,relation=kind))
sk='shiguochunqiu-035-896-xu-yu-fu';raw=addsource(sk,35)
extra(sk,raw,'event','event_zztj_260_0896_xu_captures_yu_fu_variant','description','《十国春秋》卷35乾宁三年条记许存引兵拔渝、涪二州，主底本作谕、涪。',
      '存復引兵拔¶\n渝涪二州','卷35·前蜀高祖纪上·乾宁三年·KR2i0021_WYG_035-15a',
      '地名字形异记独立保留，不直接改主书谕为渝。','conflicts')
sk='shiguochunqiu-039-zongbo-identity';raw=addsource(sk,39)
extra(sk,raw,'person',people['许存'],'aliases','《十国春秋》明记王宗播本姓许名存，王建更其姓名为王宗播，支持同人检索别名。',
      '王宗播本姓許名存故荆南節度使成汭將也','卷39·前蜀五列传·王宗播传·KR2i0021_WYG_039-9a',
      '姓名身份补证不复制人物；同书改名原文亦明确。','corroborates')
extra(sk,raw,'event','event_zztj_260_0896_wang_zongwan_reports_xu_spared_renamed','description','《十国春秋》记王宗绾密言后，王建信之而更许存姓名为王宗播，与诸子齿。',
      '宗綰¶\n密言存忠勇謙謹有良將才髙祖信之乃更其姓名曰¶\n王宗播與諸子齒','卷39·前蜀五列传·王宗播传·KR2i0021_WYG_039-9a',
      '与诸子齿为补书内容；本批未据此增加主书未明言的养父边，忠勇是所报评价。','adds')
extra(sk,raw,'event','event_zztj_260_0896_wang_zongwan_reports_xu_spared_renamed','description','《十国春秋》王宗播传将降王建背景系于乾德中，主书在896年条连记，存在时间异记。',
      '存不得¶\n志乾徳中降于髙祖','卷39·前蜀五列传·王宗播传·KR2i0021_WYG_039-9a',
      '乾德字面与卷35乾宁三年归降及主线不同，疑底本讹字或书内异记，未换算乾德年或覆盖主书896。','conflicts')
extra(sk,raw,'person',people['柳修业'],'description','《十国春秋》王宗播传称栁脩業为孔目官，并记其劝宗播慎静免祸。',
      '孔¶\n<pb:KR2i0021_WYG_039-9b>¶\n目官栁脩業謂宗播曰','卷39·前蜀五列传·王宗播传·KR2i0021_WYG_039-9a末—9b',
      '补书明确孔目官，主底本元从也目官待校；栁脩業与柳修业按同一叙事对应，不另造异体人物。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text());ledger[20].update(event_keys=used[21],batch_key=B['batch_key'],review='溯江略地、弃黔保丰、取二州、任赵许、探察推测袭击逃屯、降王建、拟杀谏阻、戍察密报免杀改名逐项分录。王宗播同许存，谕渝及臼也目等原字保留；柳每劝和其后功名终年份未定。十国春秋身份、官称与乾德时间异记独附。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=896,primary_source_key=source,paragraphs=[Q[21]['id']],next_paragraph=Q[22]['id'],coverage='第21段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
