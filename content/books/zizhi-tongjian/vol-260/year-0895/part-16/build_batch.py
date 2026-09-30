"""Curate consecutive Tongjian volume 260, year 895 paragraphs 65–68."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p065-p068', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_16_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('keyong_camps_yunyang_december','李克用驻军云阳',65,'895年十二月乙酉','云阳',
      '李克用驻军云阳。',[('李克用','驻军者')],note='军于为驻军，不补营址或新战果。')
event('wang_jian_accuses_gu_requests_attack','王建奏控顾彦晖，求出兵讨东川',66,'895年十二月戊子前条；确日未载','朝廷、东川、峡路',
      '王建上奏称顾彦晖未发兵赴难而掠夺辎重，并遣泸州刺史马敬儒阻断峡路，请出兵讨之。',[('王建','奏控请讨者'),('顾彦晖','奏中被指者'),('马敬儒','奏中被称断峡路者')],quote='王建奏：“东川节度使顾彦晖不发兵赴难，而掠夺辎重，遣泸州刺史马敬儒断峡路，请兴兵讨之。”',note='控辞归王建奏报，未认朝廷已批准或作独立核验的罪事实。')
event('wang_zongdi_wins_qiulin_895','华洪楸林大破东川兵',66,'895年十二月戊子','楸林；底本末句揪林寒',
      '华洪在楸林大败东川兵，俘斩数万；底本接记“拔揪林寒”。',[('王宗涤','以华洪名作战者')],quote='戊子，华洪大破东川兵于楸林，俘斩数万，拔揪林寒。',note='华洪沿用王宗涤别名；俘斩数万是合称不拆为各数万；末句揪林寒疑楸林寨等转录讹字，未核前保底本并注明，不默改寨名。')
event('keyong_promoted_jin_prince','李克用进爵晋王',67,'895年十二月乙未','朝廷',
      '朝廷晋封李克用为晋王。',[('李克用','进封者')],quote='乙未，进李克用爵晋王',note='进封晋王不作建国称帝或后唐开始。')
event('han_zhi_jian_shizhong_895','李罕之加兼侍中',67,'895年十二月乙未','朝廷',
      '朝廷加李罕之兼侍中。',[('李罕之','加衔者')],quote='加李罕之兼侍中')
event('gai_yu_rongguan_observer','盖寓领容管观察使',67,'895年十二月乙未','容管',
      '朝廷以河东大将盖寓领容管观察使。',[('盖寓','领容管观察使者')],quote='以河东大将盖寓领容管观察使',note='领职不作已离河东赴任容管，职衔与实际掌地须分。')
event('keyong_staff_descendants_promoted','李克用其余将佐子孙进官爵',67,'895年十二月乙未条','朝廷',
      '李克用其余将佐、子孙也进官爵。',[('李克用','所属将佐子孙受赏之帅')],quote='自馀克用将佐、子孙并进官爵。',note='未具名受赏者与具体官爵，不补人物、人数或逐人官职。')
claim('person',people['李克用'],'biography','本段背景称李克用性严急，左右小过常获死，无人敢违忤。',67,quote='克用性严急，左右小有过辄死，无敢违忤',note='史家概述性情和惯行，不定每次杀罚均发生895，也不为未具名死者造事件。')
claim('person',people['盖寓'],'biography','史述盖寓敏慧、揣李克用意并婉辞进益，遇怒将吏时佯助其怒、引近事谏诤，受李克用爱信。',67,quote='惟盖寓敏慧，能揣其意，婉辞裨益，无不从者。克用或以非罪怒将吏，寓必阳助之怒，克用常释之；有所谏诤，必征近事为喻；由是克用爱信之',note='长期行事背景，确年未载，评价与事例归史书，不推正式共有节度权。')
claim('person',people['盖寓'],'biography','史书形容盖寓权势与李克用相侔，境内依附；朝廷及邻道使者馈赠先至李克用，再至盖寓家。',67,quote='境内无不依附，权与克用侔。朝廷及邻道遣使至河东，其赏赐赂遗，先入克用，次及寓家。',note='史述权势与馈赠习惯，不认盖寓已取代节度使、无不为可核人数或本年确定单次受贿额。')
event('zhu_wen_sows_gai_keyong_distrust','朱温屡间李克用盖寓，李克用待寓更厚',67,'卷260乾宁二年条背景；数次离间起讫未载',None,
      '朱温多次派人离间李克用与盖寓，并扬言盖寓已取代李克用，李克用却对盖寓更优厚。',[('朱温','离间扬言者'),('李克用','仍厚待者'),('盖寓','被离间而获厚待者')],year=None,quote='硃全忠数遣数人间之，及扬言云盖寓已代克用，而克用待之益厚。',note='数遣为多次未定年，已代为朱温扬言非实际换帅；不将背景全定895。')
event('wang_jian_attacks_dongchuan_zongbi_captured','王建攻东川，王宗弼被擒',68,'895年十二月丙申','东川',
      '王建进攻东川，别将王宗弼被东川军俘获。',[('王建','攻东川者'),('王宗弼','被擒别将')],quote='丙申，王建攻东川，别将王宗弼为东川兵所擒',note='俘获者为东川兵，不指顾彦晖亲手擒，未推宗弼已叛王建。')
event('gu_yanhui_adopts_zongbi','顾彦晖将被俘王宗弼收为子',68,'895年十二月丙申被俘后条；确日未另载','东川',
      '顾彦晖将王宗弼收养为子。',[('顾彦晖','收养者'),('王宗弼','被收为子者')],quote='顾彦晖畜以为子',note='与王建早先养子关系并存，保同一宗弼主体，不认其生父为顾。')
relation('顾彦晖','王宗弼','养父',68,'顾彦晖将被俘的王宗弼收为子，是其养父。',quote='别将王宗弼为东川兵所擒，顾彦晖畜以为子')
event('li_yanzhao_surrenders_wang_jian','通州李彦昭率二千兵降王建',68,'895年十二月戊戌','通州',
      '通州刺史李彦昭率所部二千人降王建。',[('李彦昭','率部降者'),('王建','受降者')],quote='戊戌，通州刺史李彦昭将所部兵二千降于建。',note='二千是本段史载部兵，不推整个通州居民及城池已全部交割，未补母族或养亲。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-895-jin-prince-yunyang';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==601)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L601'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·云阳与晋王封爵',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第601页，乾宁二年十二月乙未段。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=601的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
supplements=[]
def extra(code,n,text,quote,note,kind='corroborates'):
    assert quote in raw.decode();ck=f'claim_zztj_260_0895_16_{len(B["claims"])+1:04d}';key='event_zztj_260_0895_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation='卷26·武皇纪下·乾宁二年十二月段·原PDF第601页',note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('keyong_camps_yunyang_december',65,'《旧五代史》同记十二月驻云阳，补其等待朝廷决定是否讨凤翔。','十二月，武皇营于云阳，候讨凤\n翔进止。','补意图，不作朝廷已准或云阳驻军已讨凤翔。','adds')
extra('keyong_promoted_jin_prince',67,'《旧五代史》同记乙未进封晋王，补赐忠贞平难功臣、加实封二百户。','乙未，天子赐武皇为忠贞平\n难功臣，进封晋王，加实封二百户。','封户为书载授封数，不推领有对应完整新地域或实际税入。','adds')
reviews={
 65:'十二月乙酉驻云阳，旧史补等待请讨未作已经开战。',
 66:'王建奏控顾马断路归奏辞，请讨非已准；华洪复用宗涤，楸林及末揪林寒疑文保字，俘斩合数不拆。',
 67:'乙未进晋王加李侍中盖领容管及未名将子孙赏分录；严急与盖惯行传闻背景不全定895，多次离间事件年未定。',
 68:'丙申攻擒、顾收子、戊戌李二千降分录，顾养父方向明确，既有王建养亲不删除。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(65,69):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(65,69)],next_paragraph=Q[69]['id'],coverage='第65—68段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
