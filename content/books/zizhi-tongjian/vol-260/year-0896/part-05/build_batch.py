"""Curate consecutive Tongjian volume 260, year 896 paragraphs 14–16."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 49))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0896-p014-p016', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0896_05_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁三年（896）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

def relation(a,b,t,n,description,quote=None):
    ka,kb=people[a],people[b]
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==ka and r['person_b_key']==kb and r['relation_type']==t]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);key=row['key'];reused.add(key)
    else:
        key=f'relationship_{ka}_{kb}_{t}';row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key

event('huangtiandang_zhenhai_defeat','淮南镇海战皇天荡，镇海不利',14,'896年四月条；确日未载','皇天荡',
      '淮南兵与镇海兵在皇天荡交战，镇海军不利。',[],quote='淮南兵与镇海兵战于皇天荡，镇海兵不利',note='两军未载领将姓名，不补杨钱亲自指挥；不利不推确定损失数。')
event('yang_xingmi_besieges_suzhou_896','杨行密继而围苏州',14,'896年四月皇天荡战后条；确日未載','苏州',
      '杨行密继而围苏州。',[('杨行密','围城者')],quote='杨行密遂围苏州。',note='围不作已克苏州，未提前录后续苏州陷落。')
event('qian_zhong_du_request_zhu_aid','钱镠钟传杜洪向朱温求援',14,'896年四月条；确日未载',None,
      '钱镠、钟传、杜洪惧杨行密强大，均向朱温请求援助。',[('钱镠','求援者'),('钟传','求援者'),('杜洪','求援者'),('朱温','受请者')],quote='钱镠、钟传、杜洪畏杨行密之强，皆求援于硃全忠',note='共同求援不作已经缔结统一永久联盟，不补书信全文。')
event('zhu_sends_yougong_ten_thousand_huai','朱温遣朱友恭万人渡淮，许便宜行事',14,'896年四月求援以后；确日未载','淮',
      '朱温派许州刺史朱友恭率一万兵渡淮，准其自行处置军务。',[('朱温','遣兵授权者'),('朱友恭','受遣刺史')],quote='全忠遣许州刺史硃友恭将兵万人渡淮，听以便宜从事。',note='便宜为临机军务授权，不推永久独立政权，派军不作已经解苏州围。')
event('dong_chang_punishes_true_reports','董昌杀报钱军强者，赏报疲乏者',15,'卷260乾宁三年条背景；多次侦报起讫未载',None,
      '董昌派人窥察钱镠军。有人报告军势强盛便被怒斩，报告兵疲食尽则获奖。',[('董昌','差遣并惩赏者')],year=None,quote='董昌使人觇钱镠兵，有言其强盛者辄怒，斩之；言兵疲食尽，则赏之。',note='侦报者未名，不补姓名和被杀人数，惯行未全定896。')
event('yuan_bin_surrenders_yuyao','袁邠以馀姚降钱镠',15,'896年四月戊寅','馀姚',
      '袁邠以馀姚向钱镠投降。',[('袁邠','降者'),('钱镠','受降者')],quote='戊寅，袁邠以馀姚降于镠',note='主书记主动以地降，吴越备史记执袁邠等，并列保记载差别。')
event('gu_xu_reach_yue_city','顾全武许再思进抵越州城下',15,'896年四月袁邠降后条；确日未另载','越州城下',
      '顾全武、许再思进军到越州城下。',[('顾全武','进抵将'),('许再思','进抵将')],quote='顾全武、许再思进兵至越州城下。',note='至城下未作已入城或董已死。')
event('dong_chang_defeated_yue_siege','董昌五月出战败，顾全武等围越州',15,'896年五月；确日未載','越州',
      '董昌出战失败，退守城内，顾全武等包围他。',[('董昌','出战败退守者'),('顾全武','围城者')],quote='五月，昌出战而败，婴城自守，全武等围之。',note='围者等未名不单据上句补全部参与名单，婴城为据守，不是幼儿城名。')
event('dong_chang_abandons_emperor_title','董昌惧，去帝号复称节度使',15,'896年五月败战被围以后；确日未另载','越州',
      '董昌开始惧怕，取消帝号，又称节度使。',[('董昌','去帝号者')],quote='昌始惧，去帝号，复称节度使。',note='复称不作重新获得一次朝廷授节度，也不作已经出城投降。')
event('zhang_ji_yields_liuhou_to_ma','马殷抵长沙，张佶让留后并拜贺',16,'896年五月条；到长沙及让位确日未载','长沙',
      '马殷到长沙，张佶坐肩舆入府受其拜谒，随后让马殷升堂并让留后位，自己下堂率将吏拜贺。',[('马殷','受留后者'),('张佶','让位者')],quote='马殷至长沙，张佶肩舆入府，坐受殷拜谒，已，乃命殷升听事，以留后让之，即趋下，帅将吏拜贺',note='受留后非此时已称楚王或获朝廷正式任节度，听事是堂，不是听取某事之动词。')
event('zhang_ji_resumes_sima_attacks_shao','张佶复行军司马，代马殷攻邵州',16,'896年五月让位后条；确日未载','邵州',
      '张佶又任行军司马，替马殷率军攻邵州。',[('张佶','复司马代将攻者'),('马殷','被代攻者')],quote='复为行军司马，代殷将兵攻邵州。',note='代将攻不作已攻克或马殷被废，职位与临时任务分清。')

from urllib.parse import quote as urlquote
supplements=[]
def addsource(sk,title,path,page=None):
    raw=(ROOT/path).read_bytes()
    if page is not None:raw=next(json.loads(l)['text'].encode() for l in raw.decode().splitlines() if json.loads(l)['pdf_page']==page)
    url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+(f'#L{page}' if page is not None else '')
    (P/'sources'/(sk+'.txt')).write_bytes(raw)
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author='欧阳修' if page else '范坰、林禹',edition='仓库电子底本；原字换行保留，未核纸本。',url=url,note='定位及与主书差异见逐条引用。'))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation=f'提取JSONL pdf_page={page}的text字段，不改字。' if page else 'none'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
    return raw.decode()
def extra(sk,book,citation,raw,code,n,text,q,note,kind='corroborates'):
    assert q in raw;ck=f'claim_zztj_260_0896_05_{len(B["claims"])+1:04d}';key='event_zztj_260_0896_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation=citation,note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book=book,primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
sk='wuyuebeishi-001-896-yue-siege';raw=addsource(sk,'吴越备史·卷1·乾宁三年越州围攻','resources/originals/kanripo/KR2i0019/KR2i0019_001.txt')
extra(sk,'吴越备史','卷1·乾宁三年四月·KR2i0019_SBCK_001-20a末',raw,'yuan_bin_surrenders_yuyao',15,'《吴越备史》四月记执袁邠及偏将潘荐等二千余人，主书作袁邠以馀姚降。','夏四月我師執¶\n袁邠及徧将潘薦等凡二千餘人','主动降与被执、俘数详略并列，不凭此推主书降州一定虚构或二事必为同一细节。','conflicts')
extra(sk,'吴越备史','卷1·乾宁三年五月辛巳·KR2i0019_SBCK_001-20b',raw,'dong_chang_abandons_emperor_title',15,'《吴越备史》记五月辛巳董昌五云门战败退，始惧去帝号。','五月辛巳董昌親閲戦于五雲門仍懸玉帛以誘我師頋¶\n全武許再思等奮擊之其黨大敗昌愕視而退至是始懼¶\n自去其帝號','五月辛巳、五云门为该书补充，未覆盖主书未具日和城名；该句未明复称节度使，不额外补其官。','adds')
sk='xinwudaishi-066-896-ma-zhang-transfer';raw=addsource(sk,'新五代史·卷66·楚世家·张佶让位马殷','resources/derived/twenty-four-histories/19新五代史.jsonl',1428)
extra(sk,'新五代史','卷66·楚世家·乾宁三年交接段·原PDF第1428页',raw,'zhang_ji_yields_liuhou_to_ma',16,'《新五代史》同记马殷至、张佶肩舆入府受谒后率将吏拜让，时乾宁三年。','殷至，佶乘肩舆\n入府，殷拜谒于廷中，佶召殷上，乃\n率将吏下，北面再拜，以位与之，时\n乾宁三年也。','896年交接有补书明载，北面拜为补书细节，不作同时称王。')
reviews={
 14:'皇天荡两军未名将不补、杨围苏、钱钟杜请援及朱遣万人朱友恭渡淮分录，未作苏已克或援已成功。',
 15:'董侦报惩赏习惯年未定、戊寅袁降、顾许到城、五月董出败守围与去帝复节度分录；吴越执袁异记独存，五月辛巳为补书具日。',
 16:'马至长沙张肩舆受拜让留后率下拜、复司马代攻分录，非已称楚王或马被废。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(14,17):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=896,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(14,17)],next_paragraph=Q[17]['id'],coverage='第14—16段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
