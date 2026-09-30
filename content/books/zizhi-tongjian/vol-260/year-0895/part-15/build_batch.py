"""Curate consecutive Tongjian volume 260, year 895 paragraphs 61–64."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p061-p064', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_15_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('keyong_returns_wei_north','李克用回师渭北',61,'895年十一月平王行瑜以后；确日未载','渭北',
      '李克用回军渭北。',[('李克用','旋军者')],note='渭北不是已回太原，不补起讫里程和具体驻营地点。')
event('su_wenjian_chancellor_title','苏文建加同平章事',62,'895年十一月条；确日未载','朝廷',
      '静难节度使苏文建加同平章事。',[('苏文建','加衔者')],note='此段已称静难节度使，明确记加衔，与此前奏请授镇分开，不补实际到任日。')
event('jiang_xun_requests_shaozhou_refused','蒋勋求邵州刺史，刘建锋不许',63,'895年十一月条；确日未载','邵州',
      '蒋勋请求任邵州刺史，刘建锋不允许。',[('蒋勋','求职者'),('刘建锋','拒绝者')],quote='蒋勋求为邵州刺史，刘建锋不许',note='请求未获准，不作蒋勋此时已任邵州刺史。')
event('jiang_deng_raid_xiangtan_hold_shaozhou','蒋勋邓继崇起兵，连飞山梅山众寇湘潭据邵州',63,'895年十一月蒋求职被拒后条；确日未载','飞山、梅山、湘潭、邵州',
      '蒋勋与邓继崇起兵，联结飞山、梅山的地方武装，侵扰湘潭，占据邵州。',[('蒋勋','起兵者'),('邓继崇','共起兵者')],quote='勋乃与邓继崇起兵，连飞山、梅山蛮寇湘潭，据邵州',note='底本蛮保引文，描述用地方武装，不由历史泛称确定现代族属；同兵不造结义亲族关系。')
event('shen_dechang_garrisons_dingsheng','蒋勋令申德昌屯定胜扼潭人',63,'895年十一月据邵州以后；确日未载','定胜镇',
      '蒋勋派其将申德昌驻定胜镇，以扼制潭州方面。',[('蒋勋','派将者'),('申德昌','屯定胜将')],quote='使其将申德昌屯定胜镇以扼潭人。',note='潭人保为潭州方面，不作所有居民被囚或潭州已克，未推永久统属边。')
event('three_prefects_join_wang_jian_895','李继雍费存陈璠率部奔王建',64,'895年十二月甲申','阆州、蓬州、渠州',
      '阆州防御使李继雍、蓬州刺史费存、渠州刺史陈璠各率所属兵投奔王建。',[('李继雍','率部奔王建阆州防御使'),('费存','率部奔王建蓬州刺史'),('陈璠','率部奔王建渠州刺史'),('王建','受投奔者')],note='三州为官职属地，未载集结目的地；率兵奔不自动认各州城及全部居民一同交割。李继雍与前段利州被斩李继颙字异不合并。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-895-return-wei-north';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==601)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L601'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·平行瑜还渭北',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第601页，乾宁二年平行瑜后段。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=601的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
quote='武皇既平行瑜，还军渭北。';assert quote in raw.decode()
ck=f'claim_zztj_260_0895_15_{len(B["claims"])+1:04d}';ek='event_zztj_260_0895_keyong_returns_wei_north'
B['claims'].append(dict(key=ck,subject_table='event',subject_key=ek,field_path='description',claim_text='《旧五代史》同记李克用平行瑜后还军渭北。',source_key=sk,citation='卷26·武皇纪下·乾宁二年平行瑜后段·原PDF第601页',note='原文：'+quote+'；核对说明：同记军回渭北，不把下段十二月云阳等待请讨或班师提前录成本次已回太原。',status='draft'))
reviews={
 61:'旋军渭北非已回太原，旧史补证同。',
 62:'苏文建称静难节度加相衔，与此前奏请授镇分开，实际赴任日不补。',
 63:'求邵州被拒、与邓起兵连地方众侵湘潭据邵州、申将屯定胜分录，蛮仅引史字不认现代族群。',
 64:'甲申三官各率部奔王建，不推三州整体交割，李继雍不合并继颙。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(61,65):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(61,65)],next_paragraph=Q[65]['id'],coverage='第61—64段连续整理；本年未完成。',supplements=[dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[61]['id'],subject_key=ek,relation='corroborates')],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
