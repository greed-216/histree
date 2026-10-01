"""Curate Tongjian 265, year 904, consecutive paragraphs 1–5."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 22))
primary = 'tongjian-265-904-early'
old_may = 'jiutangshu-020-may'
old_june = 'jiutangshu-020-june'
old_july = 'jiutangshu-020-july'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0904-p001-p005',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P / 'sources/library' / primary, '2377218f', '司马光等'),
    (old_may, P / 'sources/library' / old_may, '2377218f', '刘昫等'),
    (old_june, P / 'sources/library' / old_june, '2377218f', '刘昫等'),
    (old_july, P / 'sources/library' / old_july, '2377218f', '刘昫等'),
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
for n in range(1, 6):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '硃友裕':'朱友裕', '李继徽':'杨崇本', '王宗阮':'文武坚'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0904_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐元年（904）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical, aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷265天祐元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=904):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0904_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '904年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '904年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0904_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0904_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 1: May appointment.
event('appoint_zhang_hanyu','张汉瑜加同平章事',1,
      '五月，丙寅，加河阳节度使张汉瑜同平章事。',
      [('张汉瑜','河阳节度使、获加同平章事者')],when='904年五月丙寅',
      note='“加”是官衔变化；不推定新受河阳节度使之职。')

# 2: emperor's banquet, Zhu's refusal, and travel to Bian.
event('emperor_banquet_zhu','昭宗在崇勋殿宴朱全忠与百官',2,
      '帝宴硃全忠及百官于崇勋殿，既罢，复召全忠宴于内殿。',
      [('李杰','设宴者'),('朱温','受宴及再召者')],when='904年五月丙寅后；确日未载',place='洛阳崇勋殿',
      note='《旧唐书》将宴百僚系五月丙寅，此段未重复干支，故以本段次序记载。')
event('zhu_refuses_inner_banquet','朱全忠疑昭宗内殿再宴而未入，敬翔亦被遣退',2,
      '全忠疑，不入。帝曰：“全忠不欲来，可令敬翔来。”全忠擿翔使去，曰：“翔亦醉矣。”',
      [('朱温','疑而未入、使敬翔离开者'),('李杰','提出召敬翔者'),('敬翔','被召而离开者')],
      when='904年五月宴后；确日未载',place='洛阳内殿',
      note='“疑”为朱全忠自身猜疑；不据此断言昭宗设伏。')
event('zhu_returns_daliang','朱全忠辛未东还，乙亥至大梁',2,
      '辛未，全忠东还，乙亥，至大梁。',
      [('朱温','自洛阳东还、至大梁者')],when='904年五月辛未至乙亥',place='洛阳、大梁',
      note='《旧唐书》五月条另作己巳辞赴大梁，出发日有异，不能强合。')

# 3: Zhao's failed offensive and the river barrier.
event('zhao_naval_attack_kuizhou','赵匡凝遣水军上峡攻王建夔州，王宗阮等击败之',3,
      '忠义节度使赵匡凝遣水军上峡攻王建夔州，知渝州王宗阮等击败之。',
      [('赵匡凝','遣水军进攻者'),('王建','夔州被攻方'),('王宗阮','击败来军者')],
      when='904年五月后；确日未载',place='夔州、渝州',
      note='“等”未列其余将领；王宗阮依既有改名记录复用文武坚，不另建主体。')
event('zhang_wu_locks_gorge','万州刺史张武以铁絙与栅阻江，称鏁峡',3,
      '万州刺史张武作铁絙绝江中流，立栅于两端，谓之“鏁峡”。',
      [('张武','造铁絙与立栅者')],when='904年五月后；确日未载',place='峡江、万州',
      note='“鏁峡”留原书字形；未能从此句确定精确地理坐标。')

# 4: anti-Zhu proclamations and western campaign.
event('li_wang_yang_proclaim_against_zhu','李茂贞、王建与杨崇本六月传檄合兵讨朱全忠',4,
      '六月，李茂贞、王建、李继徽传檄合兵以讨硃全忠。',
      [('李茂贞','传檄合兵者'),('王建','传檄合兵者'),('杨崇本','以李继徽名传檄合兵者'),('朱温','被讨者')],
      when='904年六月；确日未载',
      note='李继徽即杨崇本旧名，复用同一人；“传檄合兵”不推成三军已经会师。')
event('zhu_orders_youyu_xun','朱全忠令朱友裕统军迎击，刘鄩弃鄜州屯同州',4,
      '全忠以镇国节度使硃友裕为行营都统，将步骑数万击之；命保大节度使刘鄩弃鄜州，引兵屯同州。',
      [('朱温','下令者'),('朱友裕','行营都统、率军者'),('刘鄩','弃鄜州屯同州者')],
      when='904年六月；确日未载',place='鄜州、同州',
      note='“数万”为史书约数；未把“击之”写成已有胜负。')
event('zhu_goes_west','朱全忠癸丑自大梁西讨，七月经洛阳至河中',4,
      '癸丑，全忠引兵自大梁西讨茂贞等。秋，七月，甲子，过东都入见。壬申，至河中。',
      [('朱温','自大梁西征并经洛阳至河中者'),('李茂贞','被讨一方')],
      when='904年六月癸丑至七月壬申',place='大梁、东都、河中',
      note='五月与七月干支按各月分记；《旧唐书》记七月癸亥朔、甲子自汴至洛。')

# 5: Shu deliberation, marriage, supplies, and Feng Juan's remonstrance.
event('feng_juan_advises_wang','冯涓劝王建与李茂贞修好以保凤翔屏障',5,
      '建以问节度判官冯涓，涓曰：“兵者凶器，残民耗财，不可穷也。今梁、晋虎争，势不两立，若并而为一，举兵向蜀，虽诸葛亮复生，不能敌矣。凤翔，蜀之籓蔽，不若与之和亲，结为婚姻，无事则务农训兵，保固疆场，有事则觇其机事，观衅而动，可以万全。”',
      [('王建','询问者'),('冯涓','建议与李茂贞和亲者')],
      when='904年七月条；确日未载',place='西川',
      note='梁晋将合是冯涓的假设推演，不录成已发生的联盟。')
event('wang_li_make_peace','王建采纳冯涓意见，与李茂贞修好',5,
      '乃与茂贞修好。',
      [('王建','修好者'),('李茂贞','修好者')],when='904年七月条；确日未载',
      note='本段明言修好；不延展为永久同盟。')
event('li_jichong_marriage','李茂贞遣赵锽为侄李继崇求婚，王建以女妻之',5,
      '丙子，茂贞遣判官赵锽如西川，为其侄天雄节度使继崇求婚，建以女妻之。',
      [('李茂贞','遣判官为侄求婚者'),('赵锽','赴西川求婚者'),('李继崇','被求婚者'),
       ('王建','嫁女者'),('王氏（李继崇妻）','王建之女、嫁李继崇者')],
      when='904年七月丙子',place='西川',
      note='继崇为茂贞之侄由“其侄”承前，未明侄的父系支属；王建之女本名未载。')
event('li_requests_supplies','李茂贞多次向王建索货与甲兵，王建应允',5,
      '茂贞数求货及甲兵于建，建皆与之。',
      [('李茂贞','索取者'),('王建','给予者')],when='修好后多次；确年未载',year=None,
      note='“数求”表示多次，未载各次年月，不强定全部发生在904年。')
event('feng_juan_remonstrates_tax','冯涓借王建生日献颂劝减赋敛，王建谢而税稍损',5,
      '王建赋敛重，人莫敢言。冯涓因建生日献颂，先美功德，后言生民之苦。建愧谢曰：“如君忠谏，功业何忧！”赐之金帛。自是赋敛稍损。',
      [('王建','受谏并减轻赋敛者'),('冯涓','献颂谏税者')],
      when='王建生日及其后；确年未载',year=None,
      note='本段未给生日年份；重赋是此前状态，减税是此后概括，均不强定具体日。')

def relation(code, a, b, kind, description, n, quote, note):
    pa=person(a,n,kind,quote); pb=person(b,n,kind,quote)
    key='relationship_zztj_265_0904_'+code
    B['person_relationships'].append(dict(key=key,person_a_key=pa,person_b_key=pb,
        relation_type=kind,description=description,status='draft'))
    claim('person_relationship',key,'description',description,n,quote,note)
    return key

relation('wang_daughter','王氏（李继崇妻）','王建','女儿','王氏（李继崇妻）是王建的女儿。',5,
         '建以女妻之','“女”直指王建之女；本名未载。')
relation('wang_jichong_wife','王氏（李继崇妻）','李继崇','妻子','王氏（李继崇妻）是李继崇的妻子。',5,
         '建以女妻之','原文明载婚配，不推定后续婚姻持续时间。')

extra(old_may,'event','event_zztj_265_0904_appoint_zhang_hanyu','time_original',
      '《旧唐书》记五月乙丑朔、丙寅制张汉瑜同平章事。',
      '五月乙丑朔。丙寅，制河陽節度使張漢瑜同平章事。',1,'corroborates',
      '职官与干支均合主书；原书繁体摘录保持原字。')
extra(old_may,'event','event_zztj_265_0904_zhu_refuses_inner_banquet','description',
      '《旧唐书》详记昭宗欲召敬翔、朱全忠令敬翔私退。',
      '全忠既不欲來，即令敬翔來，朕與之言。',2,'corroborates',
      '此书另给昭宗宴席谈话细节；未将谈话外推为设伏。')
extra(old_may,'event','event_zztj_265_0904_zhu_returns_daliang','time_original',
      '《旧唐书》作五月己巳朱全忠辞赴大梁，与《通鉴》辛未东还异日。',
      '己巳，全忠辭赴大梁',2,'conflicts',
      '日分不同；两书各自保留，不强合出发日。')
extra(old_june,'event','event_zztj_265_0904_zhu_orders_youyu_xun','description',
      '《旧唐书》六月条记朱全忠遣朱友裕屯百仁村。',
      '全忠遣朱友裕屯軍於百仁村',4,'adds',
      '补充屯军地点；不能据此推定与《通鉴》“行营都统”同日任命。')
extra(old_july,'event','event_zztj_265_0904_zhu_goes_west','description',
      '《旧唐书》记七月癸亥朔朱全忠率师讨邠凤，甲子自汴至洛阳。',
      '七月癸亥朔，全忠率師討邠、鳳。甲子，自汴至洛陽',4,'corroborates',
      '印证七月经洛阳；六月癸丑自大梁西讨仍据主书。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,6):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷265天祐元年第1—5段连续处理；出发日异说及追叙言论分辨，繁简体仅用于实体归并。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=265,year=904,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(1,6)],next_paragraph=Q[6]['id'],
    coverage='卷265天祐元年共21段中的第1—5段连续处理；五月任职、昭宗与朱全忠宴饮、峡江战事、六月讨朱及西川结亲。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
