"""Curate Tongjian 264, year 903, consecutive paragraphs 29–32."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 55))
primary = 'tongjian-264-903-august'
new_five = 'xinwudaishi-063-wang-jian'

B = {'format_version': 1, 'batch_key': 'zztj-v264-y0903-p029-p032',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P / 'sources/library' / primary, 'e36b962', '司马光等'),
    (new_five, P / 'sources/library' / new_five, 'e36b962', '欧阳修等'),
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
for n in range(29, 33):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范','李存审':'符存审','王宗本':'谢从本'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0903_05_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷264·天复三年（903）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷264天复三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=903):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_264_0903_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '903年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '903年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_264_0903_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_264_0903_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 29. The Shan'nan West Circuit appointment.
event('wang_zonghe_jiedushi','王宗贺由山南西道留后升节度使',29,
      '丁卯，以山南西道留后王宗贺为节度使。',
      [('王宗贺','受任节度使者')],when='903年七月丁卯',place='山南西道',
      note='原文只载授官，不补推实际就镇日期。')

# 30. Muzhou rebellion, Qian Liu's suspicion, then an August Qingzhou order.
event('chen_xun_lanxi','睦州刺史陈询叛钱镠并攻兰溪',30,
      '睦州刺史陈询叛钱镠，举兵攻兰溪',
      [('陈询','叛乱并进攻者'),('钱镠','被叛离者')],
      when='903年七月至八月前；确日未载',place='睦州、兰溪',
      note='本段未记兰溪陷落。')
event('qian_sends_fang','钱镠遣方永珍迎击陈询',30,
      '镠遣指挥使方永珍击之。',
      [('钱镠','遣将者'),('方永珍','受遣迎击者'),('陈询','被击者')],
      when='903年七月至八月前；确日未载',place='兰溪',
      note='仅记出击，不推断胜负。')
event('qian_suspects_du','钱镠因杜建徽与陈询连姻而疑之，得书后释疑',30,
      '武安都指挥使杜建徽与询连姻，镠疑之，建徽不言。会询亲吏来奔，得建徽与询书，皆劝戒之辞，镠乃悦。',
      [('杜建徽','被怀疑且有劝戒书者'),('钱镠','怀疑后释疑者'),('陈询','与杜建徽往来者')],
      when='903年七月至八月前；确日未载',
      note='书信内容是劝戒陈询，不能把连姻直接认作共谋。')
event('du_jiansi_accuses_du','杜建思诬告杜建徽蓄兵谋乱，钱镠搜检后更信任建徽',30,
      '建徽从兄建思谮建徽私蓄兵仗，谋作乱。镠使人索之，建徽方食，使者直入卧内，建徽不顾，镠以是益亲重之。',
      [('杜建思','进谗者'),('杜建徽','被诬告与受搜者'),('钱镠','命搜及增信者')],
      when='903年七月至八月前；确日未载',
      note='“从兄”保留原称，不简化为亲兄长；蓄兵谋乱属于建思指控，非核实事实。')
event('zhu_leaves_qingzhou','朱全忠留杨师厚攻青州后返大梁',30,
      '八月，戊辰朔，硃全忠留齐州刺史杨师厚攻青州，身归大梁。',
      [('朱温','留下将领并归大梁者'),('杨师厚','留攻青州者')],
      when='903年八月戊辰朔',place='青州、大梁',
      note='本句与上文睦州线分开；留攻不等于青州当日陷落。')

# 31. Wang Jian's new rank and title.
event('wang_jian_shu_king','王建加守司徒，进爵蜀王',31,
      '庚辰，加西川节度使西平王王建守司徒，进爵蜀王。',
      [('王建','受加官进爵者')],when='903年八月庚辰',place='西川',
      note='保持唐廷封爵语境；不写成王建此时自立皇帝。')

# 32. Wang Zongben's proposal and the actual dispatch.
event('wang_zongben_proposes_jingnan','王宗本请王建出兵取荆南，王建采纳',32,
      '前渝州刺史王宗本言于王建，请出兵取荆南。建从之',
      [('王宗本','建言者'),('王建','采纳者')],
      when='903年八月；确日未载',place='西川',
      note='请兵与王建采纳已载；是否取荆南须看后续。')
event('wang_zongben_marches_gorge','王建任王宗本开道都指挥使，王宗本率兵下峡',32,
      '以宗本为开道都指挥使，将兵下峡。',
      [('王建','任命者'),('王宗本','受任并领军者')],
      when='903年八月；确日未载',place='峡江',
      note='原文仅记“下峡”，不补写已攻取具体州。')

rel='relationship_person_杜建徽_person_陈询_姻亲'
B['person_relationships'].append(dict(key=rel,person_a_key=people['杜建徽'],
    person_b_key=people['陈询'],relation_type='姻亲',
    description='杜建徽与陈询有姻亲关系。',status='draft'))
claim('person_relationship',rel,'description','杜建徽与陈询有姻亲关系。',30,
      '杜建徽与询连姻','原文只说连姻，未说明具体婚配对象，不推定夫妻关系或共谋。')
claim('person',people['杜建思'],'description','杜建思是杜建徽的从兄。',30,
      '建徽从兄建思谮建徽','保留“从兄”原称；不以兄长关系误表亲兄弟。')

extra(new_five,'event','event_zztj_264_0903_wang_jian_shu_king','description',
      '《新五代史》卷63亦记天复三年八月唐封王建为蜀王。',
      '三年八月，唐封建蜀王',31,'corroborates',
      '月与封爵相合；该传未细记本段庚辰日及守司徒。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(29,33):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天复三年第29—32段连续处理；连姻与从兄保留原义，谗言未当作事实；八月青州与睦州叙事分开。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=903,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(29,33)],next_paragraph=Q[33]['id'],
    coverage='卷264天复三年共54个非空段落中的第29—32段连续处理；下一段开启田頵叛乱叙事。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
