"""Curate Tongjian 264, year 904, consecutive paragraphs 9–11."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 12))
primary = 'tongjian-264-904-early'
new_luo = 'xinwudaishi-039-luoshaowei-title'
B = {'format_version': 1, 'batch_key': 'zztj-v264-y0904-p009-p011',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-01/sources/library' / primary, 'da18066', '司马光等'),
    (new_luo, P / 'sources/library' / new_luo, '8fc26015', '欧阳修等'),
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
for n in range(9, 12):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','邪律阿保机':'耶律阿保机','硃友谅':'朱友谅','李继徽':'杨崇本','独孤捐':'独孤损','钱传撩':'钱传璙','侯矩':'王宗矩','张濬':'张浚','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范','李存审':'符存审','王宗本':'谢从本','硃延寿':'朱延寿','王坛':'王檀','坛':'王檀','硃氏（杨行密夫人）':'朱氏（杨行密夫人）','郭行頵':'郭行悰','侯矩':'王宗矩','硃友伦':'朱友伦','硃全忠':'朱温','邪律阿保机':'耶律阿保机','硃友谅':'朱友谅','李继徽':'杨崇本','独孤捐':'独孤损','钱传撩':'钱传璙','侯矩':'王宗矩','张濬':'张浚'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0904_03_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷264·天祐元年（904）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷264天祐元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=904):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_264_0904_' + code
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
        edge = 'participation_zztj_264_0904_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_264_0904_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 9: court reorganization and appointments after the move to Luoyang.
event('abolish_inner_offices','唐廷戊申裁停内诸司，仅留宣徽等九使',9,
      '戊申，敕内诸司惟留宣徽等九使外，馀皆停废，仍不以内夫人充使。',
      [('李杰','诏令名义者')],when='904年闰四月戊申',place='洛阳',
      note='原文未逐列九使；不据此创建九个机构，也不推定内夫人此前具体职务。')
event('appoint_palace_officers','唐廷任蒋玄晖、王殷、张廷范与韦震掌宫廷及京畿职务',9,
      '以蒋玄晖为宣徽南院使兼枢密使，王殷为宣徽北院使兼皇城使，张廷范为金吾将军、充街使，以韦震为河南尹兼六军诸卫副使',
      [('蒋玄晖','宣徽南院使兼枢密使'),('王殷','宣徽北院使兼皇城使'),
       ('张廷范','金吾将军兼街使'),('韦震','河南尹兼六军诸卫副使')],
      when='904年闰四月戊申',place='洛阳',
      note='四人的任职分别登记；仅据《通鉴》“以”字，不外推任命程序。')
event('appoint_dragon_guards','唐廷征朱友恭与氏叔琮典宿卫',9,
      '又征武宁留后硃友恭为左龙武统军，保大节度使氏叔琮为右龙武统军，典宿卫，皆全忠之腹心也。',
      [('朱友恭','左龙武统军、典宿卫'),('氏叔琮','右龙武统军、典宿卫'),('朱温','二人所依附者')],
      when='904年闰四月戊申',place='洛阳',
      note='“腹心”为《通鉴》对二人的归属判断；复用朱友恭既有实体及硃友恭异体别名。')
event('appoint_zhang_quanyi','张全义癸丑任天平节度使',9,
      '癸丑，以张全义为天平节度使。',
      [('张全义','获任天平节度使者')],when='904年闰四月癸丑',
      note='仅记录任命，不以此前或此后任职替换。')
event('appoint_zhu_four_commands','唐廷乙卯以朱全忠兼四镇节度使',9,
      '乙卯，以全忠为护国、宣武，宣义、忠武四镇节度使',
      [('朱温','受护国、宣武、宣义、忠武四镇节度使者')],when='904年闰四月乙卯',
      note='源TXT此行末缺句号，下一行另起钱镠条；四镇据此句列举，不跨行连读为第五镇。')

# 10: Qian Liu's request and the title actually granted.
event('qian_requests_wuyue_title','钱镠请求封吴越王，唐廷起初未允',10,
      '镇海、镇东节度使越王钱镠求封吴越王，朝廷不许。',
      [('钱镠','请求吴越王爵者')],when='904年闰四月条；确日未载',
      note='请求未允，不能写成904年已受吴越王爵；“越王”是本段起首现有爵号。')
event('zhu_pleads_qian_wu_title','朱全忠为钱镠请封，唐廷改封钱镠吴王',10,
      '硃全忠为之言于执政，乃更封吴王。',
      [('朱温','为钱镠言于执政者'),('钱镠','获改封吴王者')],
      when='904年闰四月条；确日未载',
      note='“吴王”是此次改封结果；与后梁时期“吴越王”分清。')

# 11: Wei-Bo army rename and Luo Shaowei title.
event('rename_weibo_tianxiong','唐廷将魏博军更名天雄军',11,
      '更命魏博曰天雄军。',when='904年闰四月条；确日未载',place='魏博',
      note='仅录军号更改，不据军号推断辖境变化。')
event('luo_promoted_ye_king','罗绍威癸亥由长沙郡王进爵鄴王',11,
      '癸亥，进天雄节度使长沙郡王罗绍威爵鄴王。',
      [('罗绍威','天雄节度使、获进鄴王爵者')],when='904年闰四月癸亥',
      note='原文用“鄴”，主体姓名用简体“罗”；爵号保留史载字形。')
extra(new_luo,'event','event_zztj_264_0904_luo_promoted_ye_king','description',
      '《新五代史》卷三十九记罗绍威于昭宗东迁后营太庙、进封鄴王。',
      '昭宗東遷洛陽，詔諸鎮繕理京師，紹威營太廟成，加拜守侍中，進封鄴王。',
      11,'corroborates','确认进封鄴王的叙事；此段不载《通鉴》的癸亥干支，不能用来独立核验具体日。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,12):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天祐元年第9—11段连续处理；官职、封爵与军号分录；简繁字形归并主体，源文保原字。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=904,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(9,12)],next_paragraph=None,
    coverage='卷264天祐元年第9—11段连续处理，至本卷年末；904年仍续见卷265。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
