"""Curate Tongjian 265, year 906, consecutive paragraphs 17–24."""
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
primary = 'tongjian-265-906-spring'
old_spring = 'jiuwudaishi-002-906-spring'
old_tang = 'jiutangshu-020-906-rongzhao'
new_qinpei = 'xinwudaishi-061-qinpei-jiangxi'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0906-p017-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-02/sources/library' / primary, '04b02541', '司马光等'),
    (old_spring, P.parent / 'part-02/sources/library' / old_spring, '04b02541', '薛居正等'),
    (old_tang, P / 'sources/library' / old_tang, 'd7ae356f', '刘昫等'),
    (new_qinpei, P / 'sources/library' / new_qinpei, 'd7ae356f', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary,)}
for n in range(17, 25):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '绍威':'罗绍威', '渥':'杨渥', '裴':'秦裴', '匡时':'钟匡时', '璋':'陈璋', '镠':'钱镠', '本':'周本', '侃':'李侃'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0906_03_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_265_0906_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 17–20: Separate court restructuring from subsequent appointments and expedition.
event('rongzhao_abolished', '唐廷丙子废戎昭军，均房改隶忠义军', 17,
      '丙子，废戎昭军，并均、房隶忠义军。',
      when='906年五月丙子',place='均州、房州',
      note='旧唐书奏敕称均房还山南东道；第19段又将忠义军复名山南东道，保留各时点称谓。')
event('feng_xingxi_made_kuangguo', '冯行袭改任匡国节度使', 17,
      '以武定节度使冯行袭为匡国节度使。',
      [('冯行袭','由武定军转任匡国军者')],when='906年五月丙子',
      note='军额废改与冯行袭转任同段，分别记录；不据此绘制边界。')
event('yang_wo_sends_qin_pei', '杨渥令秦裴率兵攻江西钟匡时', 18,
      '杨渥以升州刺史秦裴为西南行营都招讨使，将兵击钟匡时于江西。',
      [('杨渥','任命并遣兵者'),('秦裴','任西南行营都招讨使并领兵者'),('钟匡时','被攻对象')],
      when='906年五月后条；确日未载',place='江西',
      note='这里只记任命与出兵；洪州战况见第22段，攻克见后续段落。')
event('zhongyi_restored_shannan_east', '唐廷甲申复称忠义军为山南东道', 19,
      '六月，甲申，复以忠义军为山南东道。',
      when='906年六月甲申',place='忠义军',
      note='是军额改称；不自行推定军镇辖境或与第17段同日。')
event('zhu_petitions_han_wang_transfer', '朱全忠请调韩建往淄青、王重师往佑国', 20,
      '硃全忠以长安邻于邠、岐，数有战争，奏徙佑国节度使韩建于淄青，以淄青节度使长社王重师为佑国节度使。',
      [('朱温','奏请调任者'),('韩建','被奏调往淄青者'),('王重师','被奏调往佑国者')],
      when='906年六月条；确日未载',place='长安、淄青、佑国军',
      note='“奏徙”是朱全忠请求调任；本段未记朝廷批准或两人实际赴任。')

# 21: Campaign closure and its supply burden should not be combined as one casualty count.
event('zhu_clears_wei_rebel_holds', '朱全忠七月克相州并平魏境余乱', 21,
      '秋，七月，硃全忠克相州。时魏之乱兵散据贝、博、澶、相、卫州及魏之诸县，全忠分命诸将攻讨，至是悉平之，引兵南还。',
      [('朱温','分遣诸将平乱并南还者')],when='906年七月',place='相州及魏境',
      note='前期逐州战斗发生在七月以前，主书只定相州克复及至此悉平，不倒填各地同日陷落。')
event('luo_shao_wei_supplies_zhu', '罗绍威在朱全忠驻魏半年间承担巨额军需', 21,
      '全忠留魏半岁，罗绍威供亿，所杀牛羊豕近七十万，资粮称是，所赂遗又近百万，比去，蓄积为之一空。',
      [('罗绍威','承担供给者'),('朱温','在魏驻军者')],
      when='朱全忠留魏约半年；截至906年七月南还',place='魏州',
      note='近七十万为牛羊豕数量，近百万为赂遗数；两者单位不同，不合并为损失人数。')
event('zhu_returns_daliang_july', '朱全忠壬申抵大梁', 21,
      '壬申，全忠至大梁。', [('朱温','抵大梁者')],
      when='906年七月壬申',place='大梁',
      note='与905年淮南行军后归大梁为不同时间的事件，使用独立key。')

# 22: Qin Pei's tactical account is a quoted explanation, not independently established intent.
event('qin_pei_camps_liaozhou', '秦裴到洪州后驻蓼州', 22,
      '秦裴至洪州，军于蓼州。诸将请阻水立寨，裴不从。',
      [('秦裴','驻蓼州并不纳诸将建议者')],when='906年七月后条；确日未载',place='洪州、蓼州',
      note='诸将建议阻水立寨未获采纳，不写成已建寨。')
event('qin_pei_captures_liu_chu', '秦裴破钟匡时军寨并擒刘楚', 22,
      '钟匡时果遣其将刘楚据之。诸将以咎裴，裴曰：“匡时骁将独楚一人耳，若帅众守城，不可猝拔，吾故以要害诱致之耳。”未几，裴破寨，执楚',
      [('钟匡时','遣刘楚者'),('刘楚','据寨被擒者'),('秦裴','破寨擒将者')],
      when='秦裴驻蓼州后；确日未载',place='蓼州',
      note='秦裴所谓诱敌目的属于其引语；破寨擒刘楚是主书记载的结果。')
event('qin_pei_besieges_hongzhou_tang_bao_submits', '秦裴围洪州，饶州刺史唐宝请降', 22,
      '遂围洪州，饶州刺史唐宝请降。',
      [('秦裴','围洪州者'),('唐宝','请降者')],when='擒刘楚后；确日未载',place='洪州、饶州',
      note='请降不等于此时洪州已被攻克；第22段仍在围城阶段。')

# 23: Hostage and the Cangzhou campaign are unrelated acts in one paragraph.
event('li_maozhen_sends_li_kan_hostage', '李茂贞乙酉遣子李侃入西川为质', 23,
      '八月，乙酉，李茂贞遣其子侃为质于西川，王建以侃知彭州。',
      [('李茂贞','遣子为质者'),('李侃','赴西川为质并知彭州者'),('王建','任李侃知彭州者')],
      when='906年八月乙酉',place='西川、彭州',
      note='为质与知彭州均依原文；不推断李侃是否立即到任。')
rel='relationship_person_李茂贞_person_李侃_父亲'
B['person_relationships'].append(dict(key=rel,person_a_key=people['李茂贞'],person_b_key=people['李侃'],
    relation_type='父亲',description='李茂贞是李侃的父亲。',status='draft'))
claim('person_relationship',rel,'description','李茂贞是李侃的父亲。',23,
      '李茂贞遣其子侃为质于西川','“其子”承李茂贞；父亲方向为李茂贞→李侃。')
event('zhu_marches_to_cangzhou_august', '朱全忠甲辰由大梁发兵欲取沧州', 23,
      '硃全忠以幽、沧相首尾为魏患，欲先取沧州，甲辰，引兵发大梁。',
      [('朱温','发兵者')],when='906年八月甲辰',place='大梁至沧州',
      note='欲取沧州是行动意图，本段仅记出发，未记已攻克。')

# 24: Relief, retreat and rear-guard ambush are in sequence.
event('chen_zhang_asks_huainan_relief', '陈璋在衢州遭围后求援淮南', 24,
      '两浙兵围衢州，衢州刺史陈璋告急于淮南。',
      [('陈璋','衢州求援者')],when='906年八月条；确日未载',place='衢州',
      note='只记求援及围城，不推定两浙军将领。')
event('yang_sends_zhou_ben_for_chen', '杨渥遣周本迎陈璋', 24,
      '杨渥遣左厢马步都虞候周本将兵迎璋。',
      [('杨渥','遣援者'),('周本','领兵迎陈璋者'),('陈璋','被迎者')],
      when='陈璋求援后；确日未载',place='衢州',
      note='任务是迎陈璋，后文周本未采吕师造追击之议。')
event('chen_leaves_quzhou_liangzhe_takes_city', '陈璋随周本退走，两浙军取衢州', 24,
      '本至衢州，浙人解围，陈于城下。璋帅众归于本，两浙兵取衢州。',
      [('周本','到衢州接应者'),('陈璋','率众归周本者')],
      when='周本到衢州后；确日未载',place='衢州',
      note='浙军解围后列阵，随后取城；不写成在周本到城之前已取。')
event('zhou_ben_ambushes_pursuers', '周本撤军设伏击败两浙追兵', 24,
      '遂引兵还。本为之殿，浙人蹑之，本中道设伏，大破之。',
      [('周本','断后设伏者')],when='陈璋离衢州后；确日未载',place='衢州归途',
      note='吕师造先建议主动攻击、周本不纳；此处为撤军中对追兵设伏。')

extra(old_tang,'event','event_zztj_265_0906_rongzhao_abolished','time_original',
      '《旧唐书》卷二十下作五月丙申废戎昭军、均房还山南东道；主书作丙子、隶忠义军。',
      '丙申，敕：「天祐二年九月二十日于金州置戎昭軍',17,'conflicts',
      '干支丙申／丙子不同；忠义军第19段复称山南东道，名称与时间顺序并列待核。')
extra(new_qinpei,'event','event_zztj_265_0906_yang_wo_sends_qin_pei','description',
      '《新五代史》卷六十一亦记杨渥遣秦裴攻钟匡时。',
      '渥遣秦裴率兵攻之',18,'corroborates',
      '该书另载九月克洪州，是后续结果，不提前记为第18段已克。')
extra(old_spring,'event','event_zztj_265_0906_zhu_clears_wei_rebel_holds','time_original',
      '《旧五代史》卷二称七月己未收相州、魏境悉平。',
      '七月己未，自魏班師。是日，收復相州，自是魏境悉平',21,'adds',
      '主书只称七月克相州，旧书给己未日；依各书叙述保留。')
extra(old_spring,'event','event_zztj_265_0906_zhu_returns_daliang_july','time_original',
      '《旧五代史》卷二同记壬申归魏至大梁。',
      '壬申，帝歸自魏',21,'corroborates',
      '“帝”为旧书追称朱全忠，主书记壬申至大梁。')
extra(new_qinpei,'event','event_zztj_265_0906_qin_pei_besieges_hongzhou_tang_bao_submits','description',
      '《新五代史》卷六十一记秦裴九月克洪州；本段《通鉴》仍记围城。',
      '九月，克洪州，執匡時及司馬陳象以歸',22,'adds',
      '补充书给出后来攻克时间，不能倒填第22段的围城与唐宝请降为已完成攻克。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17,25):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷265天祐三年第17—24段连续处理；军额、围城与后续攻克、撤军和伏击分录，异日另记。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=265,year=906,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],
    coverage='卷265天祐三年第17—24段连续处理；军额调整、秦裴江西行动、魏境平乱、李侃入蜀、沧州出兵与衢州救援。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
