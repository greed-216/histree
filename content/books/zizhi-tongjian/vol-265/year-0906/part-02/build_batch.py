"""Curate Tongjian 265, year 906, consecutive paragraphs 9–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 43))
primary_early = 'tongjian-265-905-yearend'
primary_spring = 'tongjian-265-906-spring'
old_wei = 'jiuwudaishi-002-wei-guards'
old_spring = 'jiuwudaishi-002-906-spring'
old_fu = 'jiuwudaishi-021-fu-daozhao'
old_li = 'jiuwudaishi-026-li-sizhao'
new_tang = 'xintangshu-010-906-april'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0906-p009-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_early, P.parent.parent / 'year-0905/part-09/sources/library' / primary_early, '49e7efb9', '司马光等'),
    (primary_spring, P / 'sources/library' / primary_spring, '04b02541', '司马光等'),
    (old_wei, P.parent / 'part-01/sources/library' / old_wei, '26e932a5', '薛居正等'),
    (old_spring, P / 'sources/library' / old_spring, '04b02541', '薛居正等'),
    (old_fu, P / 'sources/library' / old_fu, '04b02541', '薛居正等'),
    (old_li, P / 'sources/library' / old_li, '04b02541', '薛居正等'),
    (new_tang, P / 'sources/library' / new_tang, '04b02541', '欧阳修等'),
]
source_dirs = {sk: d for sk, d, _, _ in source_specs}
manifest = []
for sk, d, commit, author in source_specs:
    record = json.loads((d / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((d / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=sk, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=sk, file=os.path.relpath(d / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((d / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_early, primary_spring)}
for n in range(9, 17):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '绍威':'罗绍威', '知新':'陈知新', '嗣昭':'李嗣昭', '延规':'钟延规', '匡时':'钟匡时', '仁遇':'史仁遇', '重霸':'李重霸', '璋':'陈璋', '王钊':'王钊（镇州大将）'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0906_02_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐三年（906）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical,
                   aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷265天祐三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=906, time_quote=None):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0906_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '906年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '906年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0906_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0906_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 9–11: Separate dispatch, capture, appointment, refusal and eclipse.
event('yang_sends_chen_zhixin', '杨渥遣陈知新攻湖南', 9,
      '杨渥遣先锋指挥使陈知新攻湖南。', [('杨渥','派兵者'),('陈知新','受命者')],
      when='906年三月乙丑前；确日未载',place='湖南',note='遣军日未载，不倒填攻岳州的乙丑。')
event('chen_takes_yuezhou', '陈知新乙丑取岳州逐许德勋', 9,
      '三月，乙丑，知新拔岳州，逐刺史许德勋', [('陈知新','攻取者'),('许德勋','被逐者')],
      when='906年三月乙丑',place='岳州')
event('yang_appoints_chen_yuezhou', '杨渥以陈知新为岳州刺史', 9,
      '渥以知新为岳州刺史。', [('杨渥','授任者'),('陈知新','受任者')],
      when='取岳州后；确日未载',place='岳州',note='原文在攻取后记授任，不强定同日。')
event('zhu_refuses_three_offices', '唐廷授朱全忠三司都制置使，朱辞不受', 10,
      '戊寅，以硃全忠为盐铁、度支、户部三司都制置使。三司之名始于此。全忠辞不受。',
      [('朱温','受诏而辞不受者')],when='906年三月戊寅',
      note='诏命与受领分开；三司之名始于此是主书制度判断，不推定机构已经建立。')
event('eclipse_fourth_month', '四月癸未朔日食', 11,
      '夏，四月，癸未朔，日有食之。',when='906年四月癸未朔',
      note='古历记录照录，不自行换算公历日或观测地点。')

# 12: Shi's uprising, the field-army mutiny and its suppression are distinct.
event('shi_renyu_rebels_gaotang', '史仁遇聚兵据高唐自称留后', 12,
      '会天雄牙将史仁遇作乱，聚众数万据高唐，自称留后，天雄巡内州县多应之。',
      [('史仁遇','据高唐自称留后者')],when='906年魏博牙军被杀后；确日未载',place='高唐',
      note='数万是本段集众规模，不与前批被杀牙军人数相加。')
event('wei_army_mutinies_liting', '魏军行营兵在历亭响应史仁遇', 12,
      '全忠移军入城，遣使召行营兵还攻高唐，至历亭，魏兵在行营者作乱，与仁遇相应。',
      [('朱温','调行营兵者'),('史仁遇','被响应者')],when='史仁遇据高唐后；确日未载',place='历亭',
      note='历亭行营兵与高唐史仁遇分别行动。')
event('li_fu_suppress_gaotang', '李周彝与苻道昭破叛军并克高唐', 12,
      '元帅府左司马李周彝、右司马苻道昭击之，所杀殆半，进攻高唐，克之，城中兵民无少长皆死。擒史仁遇，锯杀之。',
      [('李周彝','出兵者'),('苻道昭','同击者'),('史仁遇','被擒并锯杀者')],
      when='906年四月条；确日未载',place='历亭、高唐',
      note='历亭叛军所杀殆半与高唐城中兵民尽死是不同地点，不合计为一个数字。')

# 13–14: Prior request and concurrent fronts retain their separate order.
event('shi_requests_relief', '史仁遇先向河东与沧州求援', 13,
      '先是，仁遇求救于河东及沧州', [('史仁遇','求援者')],
      when='高唐失陷前追叙；确日未载',year=None,
      note='“先是”为追叙，不能排在高唐已陷后。')
event('li_sizhao_attacks_xingzhou', '李克用遣李嗣昭攻邢州救史仁遇', 13,
      '李克用遣其将李嗣昭将三千骑攻邢州以救之。时邢州兵才二百，团练使牛存节守之，嗣昭攻七日不克。',
      [('李克用','遣兵者'),('李嗣昭','率骑兵攻邢州者'),('牛存节','守邢州者')],
      when='高唐攻防期间；确日未载',place='邢州',
      note='三千骑、二百守兵、七日不克均依主书；不记邢州陷落。')
event('zhang_yun_defeats_li_sizhao', '张筠援邢州于马岭击败李嗣昭', 13,
      '全忠遣右长直都将张筠将数千骑助存节守城，筠伏兵于马岭，击嗣昭，败之，嗣昭遁去。',
      [('朱温','派援军者'),('张筠','设伏击败者'),('牛存节','受援守将'),('李嗣昭','败走者')],
      when='李嗣昭围邢州后；确日未载',place='马岭',
      note='旧五代史李嗣昭传作青山口，地名异说并列。')
event('liu_shouwen_attacks_bei_ji', '刘守文遣军攻贝冀并取蓚县', 14,
      '义昌节度使刘守文遣兵万人攻贝州，又攻冀州，拔蓚县，进攻阜城。',
      [('刘守文','遣兵者')],when='906年四月条；确日未载',place='贝州、冀州、蓚县、阜城',
      note='蓚县已取，阜城仍在进攻；万人为原文兵数。')
event('wang_zhao_attacks_li_zhongba', '王钊在宗城攻李重霸', 14,
      '时镇州大将王钊攻魏州叛将李重霸于宗城。',
      [('王钊','进攻者'),('李重霸','据宗城被攻者')],when='刘守文攻冀州时；确日未载',place='宗城',
      note='此王钊为镇州大将，与894年改名王宗谨的蜀将王钊不同；不归作刘守文部下。')
event('li_zhongba_killed', '朱全忠遣援冀州，李重霸弃城被胡规追斩', 14,
      '全忠遣归救冀州，沧州兵去。丙午，重霸弃城走，汴将胡规追斩之。',
      [('朱温','遣援军者'),('李重霸','弃城被斩者'),('胡规','追斩者')],
      when='906年四月丙午李重霸出逃；遣援确日未载',place='冀州、宗城',
      note='救冀、沧州兵退、丙午追斩按原次序；不全套为同日。')

# 15: Adoption and inheritance have explicit, separate parentage.
event('zhong_yangui_made_jiangzhou_prefect', '钟传以养子钟延规为江州刺史', 15,
      '镇南节度使钟传以养子延规为江州刺史。',
      [('钟传','授职的养父'),('钟延规','受职的养子')],
      when='906年钟传去世前；确日未载',place='江州',
      note='养子关系另录；不把授官定为钟传卒日。')
event('zhong_chuan_dies_kuangshi_liuhou', '钟传去世，军中立钟匡时为留后', 15,
      '传薨，军中立其子匡时为留后。',
      [('钟传','去世者'),('钟匡时','被军中立为留后者')],
      when='906年四月条；确日未载',place='镇南军',
      note='新唐书作匡时“自称留后”，行为主体异说并列。')
event('zhong_yangui_submits_huainan', '钟延规未得继立而遣使降淮南', 15,
      '延规恨不得立，遣使降淮南。', [('钟延规','遣使归降者')],
      when='钟匡时被立后；确日未载',place='江州、淮南',
      note='未得继立与遣使有先后，不直接写淮南已控制江州。')
zhong=people['钟传']
yangui=people['钟延规']
rel='relationship_person_钟传_person_钟延规_养父'
B['person_relationships'].append(dict(key=rel,person_a_key=zhong,person_b_key=yangui,
    relation_type='养父',description='钟传是钟延规的养父；收养起年未载。',status='draft'))
claim('person_relationship',rel,'description','钟传是钟延规的养父。',15,
      '镇南节度使钟传以养子延规为江州刺史。','“养子”明示钟传→钟延规的养父关系。')
old_rel='relationship_person_钟传_person_钟匡时_父亲'
prior=json.loads((ROOT/'content/books/zizhi-tongjian/vol-262/year-0901/part-07/content-batch.json').read_text())
old=next(r for r in prior['person_relationships'] if r['key']==old_rel)
assert old['person_a_key']==zhong and old['person_b_key']==people['钟匡时'] and old['relation_type']=='父亲'
B['person_relationships'].append(dict(old,status='draft'))
reused.add(old_rel)
claim('person_relationship',old_rel,'description','钟传是钟匡时的父亲。',15,
      '传薨，军中立其子匡时为留后。','“其子”承钟传，复用已有父亲关系。')

event('zhu_patrols_mingzhou_north', '朱全忠丁巳赴洺州巡北边后返魏', 16,
      '五月，丁巳，硃全忠如洺州，遂巡北边，视戎备，还，入于魏。',
      [('朱温','巡边后返魏者')],when='906年五月丁巳赴洺州；归魏确日未载',place='洺州、北边、魏',
      note='丁巳仅明确赴洺州，巡边与归魏不强定同日。')

extra(old_spring,'event','event_zztj_265_0906_zhu_refuses_three_offices','time_original',
      '《旧五代史》卷二作三月甲寅命总判三司，主书作戊寅都制置使。',
      '三月甲寅，天子命帝總判鹽鐵、度支、戶部等三司事',10,'conflicts',
      '干支与职名均不同，保留两书说法。')
extra(new_tang,'event','event_zztj_265_0906_eclipse_fourth_month','time_original',
      '《新唐书》卷十同记四月癸未朔日食。',
      '四月癸未朔，日有食之',11,'corroborates','电子底本独立出处，未给观测地点。')
extra(old_wei,'event','event_zztj_265_0906_shi_renyu_rebels_gaotang','description',
      '《旧五代史》卷二记魏军余众拥史仁遇保高唐。',
      '餘眾乃擁大將史仁遇保于高唐',12,'corroborates',
      '旧书未在本句记其自称留后，依主书记录该称号。')
extra(old_spring,'event','event_zztj_265_0906_li_fu_suppress_gaotang','description',
      '《旧五代史》卷二记四月癸未攻下高唐、杀军民并擒史仁遇。',
      '四月癸未，攻下高唐，軍民無少長皆殺之，生擒逆首史仁遇以獻',12,'adds',
      '主书未给攻克日，旧书给癸未；执行手法主书另记锯杀。')
extra(old_fu,'event','event_zztj_265_0906_li_fu_suppress_gaotang','description',
      '《旧五代史》苻道昭传亦记其参与镇压。',
      '道昭佐周彝與彥卿已下大破之',12,'adds',
      '同书不同传记不当作独立证人；该传另述左行迁，不与史仁遇强并。')
extra(old_li,'event','event_zztj_265_0906_zhang_yun_defeats_li_sizhao','description',
      '《旧五代史》李嗣昭传记在青山口遇牛存节、张筠不利而还。',
      '遇汴將牛存節、張筠於青山口，嗣昭不利而還',13,'conflicts',
      '主书作马岭；两地是否同一处未证实。')
extra(new_tang,'event','event_zztj_265_0906_zhong_chuan_dies_kuangshi_liuhou','description',
      '《新唐书》卷十记钟传四月卒，其子匡时自称留后。',
      '鎮南軍節度使鍾傳卒，其子匡時自稱留後',15,'conflicts',
      '主书作“军中立其子匡时”，行为主体不同。')
extra(old_spring,'event','event_zztj_265_0906_zhu_patrols_mingzhou_north','description',
      '《旧五代史》卷二记五月朱全忠至洺州后返魏。',
      '五月，帝略地於洺州，既而復入于魏',16,'corroborates',
      '旧书未给丁巳日，日序仍据主书。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,17):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷265天祐三年第9—16段连续处理；追叙与实事分开，其他书的干支、地名、继任异说并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=265,year=906,
    primary_source_key=primary_early,primary_source_keys=[primary_early,primary_spring],
    paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],
    coverage='卷265天祐三年第9—16段连续处理；岳州、三司、日食、魏博余军、邢州、冀州、钟传继任和巡边。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
