"""Curate consecutive Tongjian volume 260, year 895 paragraphs 52–56."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p052-p056', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_13_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('yang_sends_tian_an_hangzhou','杨行密遣田頵安仁义攻杭州镇戍援董昌',52,'895年十月条；确日未载','杭州镇戍',
      '杨行密派宁国节度使田頵、润州团练使安仁义攻杭州镇戍，以救董昌。',[('杨行密','遣将者'),('田頵','奉遣宁国节度使'),('安仁义','奉遣润州团练使'),('董昌','援救对象')],quote='杨行密遣宁国节度使田頵、润州团练使安仁义攻杭州镇戍以救董昌',note='攻杭州镇戍不作杭州城已陷；本段未载兵数。')
event('dong_xushu_weiyue_jiaxing_siege','董昌遣徐淑会魏约围嘉兴',52,'895年十月条；确日未载','嘉兴',
      '董昌派湖州将徐淑会同淮南将魏约围嘉兴。',[('董昌','遣将者'),('徐淑','湖州围城将'),('魏约','淮南围城将')],quote='昌使湖州将徐淑会淮南将魏约共围嘉兴。',note='两将军属不同保留，围城不作已克；徐淑不写成徐温。')
event('qian_sends_gu_quanwu_jiaxing','钱镠遣顾全武救嘉兴破二寨',52,'895年十月围嘉兴条；确日未载','嘉兴、乌墩、光福',
      '钱镠派武勇都指挥使顾全武救嘉兴，顾全武攻破乌墩、光福二寨。',[('钱镠','遣救者'),('顾全武','救援破寨指挥使')],quote='钱镠遣武勇都指挥使顾全武救嘉兴，破乌墩、光福二寨。',note='未由破二寨认整场围城此时已经解除，二寨不是两个州。')
claim('person',people['顾全武'],'biography','顾全武是馀姚人。',52,quote='全武，馀姚人也。',note='馀姚保史载字，未作出生地坐标或现代行政区转换。')
event('ke_hou_breaks_suzhou_water_fence','柯厚攻破苏州水栅',52,'895年十月条；确日未载','苏州水栅',
      '淮南将柯厚攻破苏州水栅。',[('柯厚','淮南破水栅将')],quote='淮南将柯厚破苏州水栅。',note='水栅失守不自动等于整座苏州城失陷，未作台濛亲攻结果。')
event('wang_chucun_dies_895','义武节度使王处存去世',53,'895年十月条；确日未载',None,
      '义武节度使王处存去世。',[('王处存','去世节度使')],quote='义武节度使王处存薨',note='死因和地点未载；复用王处存身份。')
event('army_elects_wang_gao_yiwu','义武军推王郜为留后',53,'895年十月王处存去世后条；确日未载','义武',
      '军中推王处存之子、节度副使王郜为留后。',[('王郜','被军推留后副使')],quote='军中推其子节度副使郜为留后。',note='军中推为不是朝廷正式授节度使，姓从父取，未补即位礼或母亲。')
relation('王处存','王郜','父亲',53,'王处存是王郜的父亲。',quote='义武节度使王处存薨，军中推其子节度副使郜为留后。')
event('sun_wo_becomes_chancellor_895','京兆尹孙偓授兵部侍郎同平章事',54,'895年十月条；确日未载','朝廷',
      '朝廷以京兆尹、武邑人孙偓为兵部侍郎、同平章事。',[('孙偓','受相职者')],quote='以京兆尹武邑孙亻屋为兵部侍郎、同平章事。',note='底本孙亻屋为偓的拆字转录，以孙偓作检索名、拆字作别名；同源文件后段有孙偓字形，当前未提前录后段事件。')
for row in B['people']:
    if row['key']==people['孙偓']:row['aliases']=['孙亻屋']
claim('person',people['孙偓'],'biography','孙偓是武邑人，本段称京兆尹。',54,quote='京兆尹武邑孙亻屋',note='籍贯职衔据本句；不补籍贯的现代坐标。')
event('keyong_attacks_xingyu_longquan','王行瑜五千守龙泉，李克用攻之',54,'895年十月条；确日未载','龙泉寨',
      '王行瑜用五千精甲守龙泉寨，李克用进攻。',[('王行瑜','守寨者'),('李克用','攻寨者')],quote='王行瑜以精甲五千守龙泉寨，李克用攻之。',note='五千为史载守军数，非李克用兵数；攻不作立即克寨。')
event('maozhen_five_thousand_aid_longquan','李茂贞五千援龙泉，营镇西',54,'895年十月攻龙泉条；确日未载','龙泉镇西',
      '李茂贞以五千兵救援龙泉寨，营于镇西。',[('李茂贞','援寨者')],quote='李茂贞以兵五千救之，营于镇西。',note='该次五千不与此前龙泉万人或咸阳三万人相加推总兵力。')
event('han_zhi_drives_fengxiang_aid','李罕之击退凤翔援兵',54,'895年十月至十一月攻龙泉过程中；确日未另载','龙泉寨附近',
      '李罕之攻击凤翔兵，令其败走。',[('李罕之','败凤翔兵者')],quote='李罕之击凤翔兵，走之',note='未载追击至凤翔或斩茂贞；附近为上文龙泉战区，不补坐标。')
event('longquan_falls_xingyu_flees_bin','丁巳攻克龙泉，王行瑜走邠州请降',54,'895年十一月丁巳克寨；请降日未另载','龙泉寨、邠州',
      '李克用军攻克龙泉寨，王行瑜逃入邠州，遣使向李克用请降。',[('李克用','克寨军帅与受请降者'),('王行瑜','走邠州请降者')],quote='十一月，丁巳，拨龙泉寨。行瑜走入邠州，遣使请降于克用。',note='拨疑拔保原字；请降不作已经受降或安全入朝。')
event('zhu_qiong_surrenders_qizhou','朱琼举齐州降朱温',55,'895年十一月条；确日未载','齐州',
      '齐州刺史朱琼以全州降朱温。',[('朱琼','举州降刺史'),('朱温','受降者')],note='硃字归朱，不补刺史实际交接清册或全城居民意愿。')
person('朱瑾',55,'朱琼从父弟')
relation('朱琼','朱瑾','堂兄',55,'朱琼是朱瑾的从父兄，按父系堂兄关系录。',quote='琼，瑾之从父兄也。')
event('chen_ru_quzhou_dies','衢州刺史陈儒去世',56,'895年十一月条；确日未载','衢州',
      '衢州刺史陈儒去世。',[('陈儒（衢州刺史）','去世刺史')],quote='衢州刺史陈儒卒',note='与884年攻舒州的同名陈儒暂按职位消歧，无任职连接不合并，也不认定必为两人；衢州为官属地，非确定卒地。')
event('chen_ji_succeeds_quzhou','陈岌接替兄陈儒',56,'895年十一月陈儒卒后条；确日未载','衢州',
      '陈儒之弟陈岌接替其职。',[('陈岌','接替兄职者')],quote='衢州刺史陈儒卒，弟岌代之。',note='岌从兄姓作陈岌，代之为接职，不补朝廷任命日。')
relation('陈儒（衢州刺史）','陈岌','兄长',56,'衢州刺史陈儒是陈岌的兄长。',quote='衢州刺史陈儒卒，弟岌代之。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-895-longquan-falls';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==600)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L600'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·收龙泉寨',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第600页，乾宁二年十一月丁巳段。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=600的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
quote='十一月丁巳，\n收龙泉寨。时行瑜以精甲五千守之，\n李茂贞出兵来援，为李罕之所败，邠\n贼遂弃龙泉寨而去。行瑜复入邠州';assert quote in raw.decode()
ck=f'claim_zztj_260_0895_13_{len(B["claims"])+1:04d}';ek='event_zztj_260_0895_longquan_falls_xingyu_flees_bin'
B['claims'].append(dict(key=ck,subject_table='event',subject_key=ek,field_path='description',claim_text='《旧五代史》同记十一月丁巳收龙泉寨，行瑜精甲五千守、茂贞来援被李罕之击败、行瑜退入邠州。',source_key=sk,citation='卷26·武皇纪下·乾宁二年十一月丁巳·原PDF第600页',note='原文：'+quote+'；核对说明：同记龙泉败退，该书此段未载茂贞援军五千，不借守军五千填援军人数。',status='draft'))
reviews={
 52:'遣田安攻镇戍、徐魏围嘉兴、钱遣顾救破二寨、柯破水栅分录；破栅不作苏州全城已陷，顾籍贯单记。',
 53:'王处存卒、军推王郜留后分录，父亲方向有明文，军推非朝廷正式授节度。',
 54:'孙拆字归偓、官籍贯有句；龙泉守五千与援五千不同，攻、击退、丁巳克走请降有先后；请求未作受降。',
 55:'朱琼降齐州、从父兄朱瑾为堂兄关系，不能当亲兄。',
 56:'衢州陈儒按职位消歧，卒与弟陈岌接职分录，兄长方向有句，未补卒地或朝廷任命。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(52,57):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(52,57)],next_paragraph=Q[57]['id'],coverage='第52—56段连续整理；本年未完成。',supplements=[dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[54]['id'],subject_key=ek,relation='corroborates')],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
