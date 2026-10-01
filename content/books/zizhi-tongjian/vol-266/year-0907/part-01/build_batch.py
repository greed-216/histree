"""Curate Tongjian 266, year 907, consecutive paragraphs 1–7."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 62))
primary = 'tongjian-266-907-spring'
new_yangwo = 'xinwudaishi-061-yangwo'
B = {'format_version': 1, 'batch_key': 'zztj-v266-y0907-p001-p007',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P / 'sources/library' / primary, '56c8b850', '司马光等'),
    (new_yangwo, P / 'sources/library' / new_yangwo, '56c8b850', '欧阳修等'),
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
primary_texts = {primary: (source_dirs[primary] / 'source.txt').read_text()}
for n in range(1, 8):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/266.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '硃思勍':'朱思勍', '梁王':'朱温', '渥':'杨渥',
           '师周':'吕师周', '章':'綦章', '颢':'张颢', '温':'徐温',
           '王景仁':'王茂章'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/year-0907/content-batch.json').read_text())['events']}

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_266_0907_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷266·开平元年（907）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷266开平元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=907, time_quote=None, reuse_key=None):
    assert quote in Q[n]['text'], (n, quote)
    key = reuse_key or ('event_zztj_266_0907_' + code)
    if reuse_key:
        assert not actors, 'Published event edges are preserved by stable key'
        row = dict(legacy_events[reuse_key], status='draft')
        B['events'].append(row)
        reused.add(key)
        desc = row['description']
    else:
        desc = title + '。'
        B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                                time_original=when or '907年本段条；确日未载', dynasty='唐', description=desc,
                                phases=[], location_name=place, location_modern_name=None, location_lat=None,
                                location_lng=None, location_precision='unknown',
                                location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '907年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_266_0907_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_266_0907_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# The first line connects directly to the published 907 archive.
event('beizhou_rest', '梁王在贝州休兵', 1,
      '春，正月，辛巳，梁王休兵于贝州。',
      when='907年正月辛巳',place='贝州',
      note='旧档案已有同一事件，复用 event_0907_beizhou；正文从此段按《通鉴》卷年连续推进。',
      reuse_key='event_0907_beizhou')

event('yang_wo_executes_zhou_yin', '杨渥责周隐并处死之', 2,
      '谓节度判官周隐曰：“君卖人国家，何面复相见！”遂杀之。',
      [('杨渥','斥责并处死周隐者'),('周隐','被处死的节度判官')],
      when='907年正月条；确日未载',place='淮南',
      note='“卖人国家”为杨渥指责用语，不作为已核准的周隐罪行。')
event('lu_shizhou_defects_to_hunan', '吕师周惧杨渥而奔湖南', 3,
      '师周惧，谋于綦章曰：“马公宽厚，吾欲逃死焉，可乎？”章曰：“兹事君自图之，吾舌可断，不敢泄！”师周遂奔湖南',
      [('吕师周','出奔湖南者'),('綦章','获商议并承诺不泄者')],
      when='907年正月条；确日未载',place='上高、湖南',
      note='“马公宽厚”是吕师周对湖南掌权者的判断；不以言辞证明实际待遇。')
event('qi_zhang_releases_lu_family', '綦章放吕师周家属离去', 3,
      '章纵其孥，使逸去。',
      [('綦章','放行家属者'),('吕师周','家属获放行者')],
      when='吕师周出奔湖南后；确日未载',
      note='原文“孥”指其家属，不推定具体姓名和人数。')

# The legacy coup event covers the outcome; these two precursors remain distinct.
event('zhang_xu_remonstrate_yang_wo', '张颢徐温劝谏杨渥而遭怒斥', 4,
      '左、右牙指挥使张颢、徐温泣谏，渥怒曰：“汝谓我不才，何不杀我自为之！”二人惧。',
      [('张颢','劝谏者'),('徐温','劝谏者'),('杨渥','受谏后发怒者')],
      when='907年兵谏前；确日未载',place='淮南',
      note='原文未写具体劝谏事项；不推成此时已经发动兵谏。')
event('zhang_xu_execute_three_yang_guards', '张颢徐温借江西戍守事处死杨渥三名亲兵将领', 4,
      Q[4]['text'][Q[4]['text'].index('渥之镇宣州也'):Q[4]['text'].index('渥闻三将死')],
      [('张颢','命处死三将者'),('徐温','命处死三将者'),('陈祐','赴洪州执行者'),
       ('秦裴','陈祐告知后召三将者'),('硃思勍','被诬谋叛并斩杀者'),
       ('范思从','被诬谋叛并斩杀者'),('陈璠','被诬谋叛并斩杀者')],
      when='907年兵谏前；确日未载',place='洪州',
      note='本句称“诬以谋叛”，不将三将谋叛当成事实；六日是陈祐路程时长。')
event('huainan_coup', '张颢徐温以兵谏控制淮南军政', 4,
      '丙戍，渥晨视事，颢、温帅牙兵二百，露刃直入庭中',
      when='907年正月后条丙戍；底本字样待历日核校',place='淮南',
      note='底本作“丙戍”，不静默改成“丙戌”；旧档案同一兵谏事件复用稳定key。',
      reuse_key='event_0907_huainan_coup')

event('zhu_succession_persuasion', '罗绍威劝朱温受禅，薛贻矩传达禅位意向', 5,
      '罗绍威恐王袭之，入见王曰：“今四方称兵为王患者，皆以翼戴唐室为名，王不如早灭唐以绝人望。”',
      when='907年正月丁亥后；确日未载',place='魏州、大梁',
      note='本段后续记薛贻矩使梁及唐帝拟二月禅位，旧档案已合记，复用稳定key；“恐王袭之”为主书写罗绍威心态。',
      reuse_key='event_0907_persuade')
event('kang_huaizhen_guards_jinzhou', '康怀贞率京兆同华之兵屯晋州', 6,
      '王命保平节度使康怀贞悉发京兆，同华之兵屯晋州以备之。',
      when='907年正月后条；确日未载',place='晋州',
      note='“以备之”对应上句河东军欲窥泽州；旧档案已有同一防备事件。',
      reuse_key='event_0907_jinzhou_defense')
event('abdication_petitions', '唐廷及各镇向梁王劝进', 7,
      '二月，唐大臣共奏请昭宣帝逊位。壬子，诏宰相帅百官笺诣元帅府劝进，王遣使却之。',
      when='907年二月壬子及前后',
      note='本段仅记录奏请、诏令与梁王遣使辞让，不能写成二月已经完成禅位；旧档案劝进事件复用。',
      reuse_key='event_0907_abdication_petitions')

extra(new_yangwo,'event','event_zztj_266_0907_yang_wo_executes_zhou_yin','description',
      '《新五代史》卷六十一同记杨渥斥周隐“卖吾国”并杀之。',
      '渥見溫使，乃行。行密卒，渥嗣立，召周隱罵曰：「汝，欲賣吾國者，復何面目見楊氏乎？」遂殺之',
      2,'corroborates','本书将此事系于杨渥继位后，不据卷六十一摘录推定907年具体日。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,8):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷266开平元年第1—7段连续处理；旧907事件复用，新发现的前因分录；异体字与疑字原样保留。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=266,year=907,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(1,8)],next_paragraph=Q[8]['id'],
    coverage='卷266开平元年第1—7段连续处理；贝州休兵、淮南政变前因、梁唐禅代交涉及晋州防备。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
