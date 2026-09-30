"""Curate consecutive Tongjian volume 260, year 895 paragraphs 45–48."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p045-p048', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_11_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('wang_jian_zongyao_aid_emperor','王建遣王宗瑶赴难，军至绵州',45,'895年九月甲戌驻军；派遣日未另载','绵州',
      '王建派简州刺史王宗瑶等率兵赴难，甲戌驻军绵州。',[('王建','遣兵者'),('王宗瑶','领兵赴难简州刺史')],note='赴难按前文皇帝避乱语境，不写已与行在合军；绵州是本段明确驻军处。')
event('dong_chang_requests_yang_aid','董昌向杨行密求援',46,'895年九月条；确日未载',None,
      '董昌向杨行密求救。',[('董昌','求救者'),('杨行密','被求救者')],quote='董昌求救于杨行密',note='求援不推结义或长期同盟关系。')
event('yang_sends_tai_meng_suzhou','杨行密遣台濛攻苏州救董昌',46,'895年九月董昌求救以后；确日未载','苏州',
      '杨行密派泗州防御使台濛进攻苏州，以救董昌。',[('杨行密','派将者'),('台濛','奉遣攻苏州泗州防御使'),('董昌','援救对象')],quote='行密遣泗州防御使台濛攻苏州以救之',note='派攻不作已攻克苏州，职衔保本段称谓。')
event('yang_petitions_restore_dong_titles','杨行密上表为董昌请复官爵',46,'895年九月遣台濛攻苏州条；确日未载','朝廷',
      '杨行密上表称董昌已引咎、愿恢复职贡，请求恢复董昌官爵。',[('杨行密','上表请复者'),('董昌','被表称引咎愿修职贡者')],quote='且表昌引咎，愿修职贡，请复官爵。',note='引咎愿修为奏表所称，未验证董昌实际贡奉；请复不作朝廷已批准。')
event('yang_letter_qian_stop_dong_campaign','杨行密致钱镠书，主张停止攻董昌',46,'895年九月上表条；确日未载',None,
      '杨行密写信给钱镠，称董昌因狂疾自立、已惧兵谏并押送同恶者，主张不应再讨。',[('杨行密','写信劝止者'),('钱镠','收信者'),('董昌','信中被称者')],quote='又遗钱镠书，称：“昌狂疾自立，已畏兵谏，执送同恶。不当复伐之。”',note='狂疾及押送为杨行密信中辩护语，不作为现代医学诊断或另经验证的事实；未说钱镠已接受。')
event('cunzhen_liyuan_north_victory','李存贞梨园北败邠宁军',47,'895年冬十月丙戌','梨园北',
      '河东将李存贞在梨园北击败邠宁军，杀千余人；自此梨园守军闭壁不敢出。',[('李存贞','主书所记胜军将')],note='杀千余是主书记数，不等同补书斩首千余；旧五代史领军者作李存信，保异说，未合并二人。')
event('cui_zhaowei_demoted_wuzhou','崔昭纬贬梧州司马',48,'895年十月条；确日未载','梧州',
      '右仆射崔昭纬被贬为梧州司马。',[('崔昭纬','被贬者')],note='贬官与前批罢相分开，未补已经抵梧州或被赐死。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-895-liyuan-north-victory';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==599)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L599'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·梨园北胜军异记',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第599页，乾宁二年十月丙戌段。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=599的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
quote='十月丙戌，李存信于梨园寨北遇\n贼军，斩首千余级，自是贼闭壁不\n出。';assert quote in raw.decode()
ck=f'claim_zztj_260_0895_11_{len(B["claims"])+1:04d}';ek='event_zztj_260_0895_cunzhen_liyuan_north_victory'
B['claims'].append(dict(key=ck,subject_table='event',subject_key=ek,field_path='description',claim_text='《旧五代史》同日梨园寨北之战记领军者李存信、斩首千余级，主书作李存贞、杀千余人。',source_key=sk,citation='卷26·武皇纪下·乾宁二年十月丙戌·原PDF第599页',note='原文：'+quote+'；核对说明：同日同地战事并列书证，姓名与战果措辞差别保留，不能凭此将李存贞合并李存信，未另造第二场确定战事。',status='draft'))
reviews={
 45:'王建遣简州王宗瑶赴难与甲戌绵州驻军保过程，未作已抵行在。',
 46:'董求救、杨遣台濛攻苏州、杨表请复与致钱信分录，奏表信中称说明确归杨，不作批准或对狂疾的现代诊断。',
 47:'十月丙戌梨园北，主书李存贞与旧史李存信、杀人/斩首各保不同；不合并姓名或另造两场战事。',
 48:'崔昭纬贬梧州司马，非前罢相重复，不补到任或死。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(45,49):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(45,49)],next_paragraph=Q[49]['id'],coverage='第45—48段连续整理；本年未完成。',supplements=[dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[47]['id'],subject_key=ek,relation='conflicts')],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
