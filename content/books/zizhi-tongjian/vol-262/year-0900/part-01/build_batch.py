"""Curate Tongjian 262, year 900, consecutive paragraphs 1–8."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 33))
primary = 'tongjian-262-900-spring'
supplement = 'jiuwudaishi-002-900-dezhou'
fixed_commit = 'bb575ad'
B = {'format_version': 1, 'batch_key': 'zztj-v262-y0900-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for sk, author in ((primary, '司马光等'), (supplement, '薛居正等')):
    d = P / 'sources/library' / sk
    record = json.loads((d / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + fixed_commit + '/' + str((d / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=sk, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=sk, file='library/' + sk + '/source.txt',
                         sha256=hashlib.sha256((d / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
source_text = (P / 'sources/library' / primary / 'source.txt').read_text()
for n in range(1, 9):
    assert Q[n]['text'] in source_text

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '李钅岁': '李鐬'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_262_0900_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary, citation=f'卷262·光化三年（900）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical, aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷262光化三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, Q[n]['text'],
          '只据本段确认其参与身份；异体字和既有人物键回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_262_0900_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=900, end_year=900,
                            time_original=when or '900年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '900年本段条；确日未载', n, quote,
          note or '沿主书段落次序；干支日未换算公历日。')
    for name, role in actors:
        pk = person(name, n, role)
        edge = 'participation_zztj_262_0900_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定盟约或亲缘。')
    return key

event('kang_ru_attacks_muzhou', '康儒攻睦州', 1, '宣州将康儒攻睦州', [('康儒', '宣州进攻将领')],
      when='900年春正月', place='睦州')
event('qian_liu_sends_qiu_resist', '钱镠遣从弟钱銶拒康儒', 1, '钱镠使其从弟銶拒之。',
      [('钱镠', '遣拒者'), ('钱銶', '受遣拒敌者')], when='900年春正月', place='睦州',
      note='从弟为原文亲属称谓；拒之表示遣去抵御，不写已取胜。')
kinship = 'relationship_person_钱镠_person_钱銶_从兄'
B['person_relationships'].append(dict(key=kinship, person_a_key=people['钱镠'], person_b_key=people['钱銶'],
    relation_type='从兄', description='钱镠是钱銶的从兄。', status='draft'))
claim('person_relationship', kinship, 'description', '钱镠是钱銶的从兄。', 1,
      '钱镠使其从弟銶拒之。', '“其从弟”以钱镠为参照，方向为钱镠—从兄→钱銶；只据史载称谓，不补父辈谱系。')
event('wang_jian_chancellor', '王建兼中书令', 2, Q[2]['text'], [('王建', '加兼中书令者')],
      when='900年二月庚申', note='底本“西川李度使”疑为传录讹字，原字保留；只据清楚的“王建兼中书令”录职。')
event('wang_shenzhi_tongpingzhangshi', '王审知加同平章事', 3, Q[3]['text'], [('王审知', '加同平章事者')],
      when='900年二月壬申')
event('cui_yin_tongpingzhangshi_qinghai', '崔胤复同平章事并充清海节度使', 4, Q[4]['text'],
      [('崔胤', '同平章事及清海节度使受任者')], when='900年二月壬午',
      note='此处为任官记载，不写崔胤已到广州；下段出镇复召须后续连续段处理。')
event('li_keyong_repairs_jinyang', '李克用大发军民修晋阳城堑', 5, '李克用大发军民治晋阳城堑',
      [('李克用', '发军民修城堑者')], place='晋阳', note='治为修城壕，不推定城防已完成。')
event('liu_yanye_advises_li', '刘延业谏李克用修晋阳城堑', 5,
      '押牙刘延业谏曰：“大王声振华、夷，宜扬兵以严四境，不宜近治城堑，损威望而启寇心。”',
      [('刘延业', '进谏押牙'), ('李克用', '受谏者')], place='晋阳',
      note='进谏理由是刘延业所言，不当客观判断邻敌已生攻心。')
event('li_rewards_liu_yanye', '李克用谢刘延业并赐金帛', 5, '克用谢之，赏以金帛。',
      [('李克用', '谢而赏者'), ('刘延业', '受赏者')], place='晋阳')
event('li_chengqing_tongpingzhangshi', '李承庆加同平章事', 6, Q[6]['text'],
      [('李承庆', '加同平章事者')], when='900年夏四月',
      note='仍按本段定难军节度使称谓，不据此推领土边界。')
event('zhu_sends_ge_against_liu', '朱全忠遣葛从周统四镇军攻刘仁恭', 7,
      '硃全忠遣葛从周帅兗、郓、滑、魏四镇兵十万击刘仁恭',
      [('朱温', '遣攻者'), ('葛从周', '统四镇攻军者'), ('刘仁恭', '被攻对象')],
      when='900年四月后、五月庚寅前；确日未载', place='兗、郓、滑、魏至沧州方向',
      note='十万为主书记数；出兵日未明，旧五代史作四月；四镇不当四座新取城。')
dezhou = event('ge_takes_dezhou_fukilled', '葛从周军拔德州并斩傅公和', 7,
      '五月，庚寅，拔德州，斩刺史傅公和。', [('葛从周', '攻军将领'), ('傅公和', '被斩德州刺史')],
      when='900年五月庚寅', place='德州', note='主书称斩傅；旧五代史补城上枭首，不写傅死于此前战斗。')
claim('person', people['傅公和'], 'death_year', '傅公和于900年五月庚寅德州陷后被斩。', 7,
      '五月，庚寅，拔德州，斩刺史傅公和。', '确年及干支日来自主书，不推生年。')
event('ge_sieges_shouwen_cangzhou', '葛从周军围刘守文于沧州', 7, '己亥，围刘守文于沧州。',
      [('葛从周', '围城军将领'), ('刘守文', '被围者')], when='900年五月己亥', place='沧州',
      note='旧五代史作进攻浮阳；地名并列保留，不增造另一次围城。')
event('liu_requests_hedong_aid', '刘仁恭向河东求援', 7,
      '仁恭复遣使卑辞厚礼求救于河东', [('刘仁恭', '遣使求援者'), ('李克用', '河东受求援方')],
      when='900年五月沧州被围后；确日未载', place='河东', note='使者未名，不新造人名。')
event('li_sends_dewei_huangze', '李克用遣周德威五千骑出黄泽攻邢洺以救沧州', 7,
      '李克用遣周德威将五千骑出黄泽，攻邢、洺以救之。',
      [('李克用', '遣援者'), ('周德威', '率五千骑者'), ('刘仁恭', '受援方')],
      when='900年五月沧州被围后；确日未载', place='黄泽、邢州、洺州',
      note='攻邢洺是牵制救援，不写五千骑直接抵沧州或已经赢得攻城战。')
event('yongzhou_revolt_expels_li', '邕州军乱逐节度使李鐬', 8, '邕州军乱，逐节度使李钅岁。',
      [('李鐬', '被逐节度使')], when='900年五月后、六月癸亥前条；确日未载', place='邕州',
      note='底本“李钅岁”为拆字转录，复用既有人物李鐬；主书未名叛将，不造具名人物。')
event('li_hui_borrows_troops_quells', '李鐬借邻道兵讨平邕州军乱', 8, '钅岁借兵邻道讨平之。',
      [('李鐬', '借兵讨平者')], when='900年邕州军乱后、六月癸亥前条；确日未载', place='邕州、邻道',
      note='邻道未名，不指认具体藩镇或将领。')
event('wang_zongdi_tongpingzhangshi', '王宗涤加同平章事', 8, '六月，癸亥，加东川节度使王宗涤同平章事。',
      [('王宗涤', '加同平章事者')], when='900年六月癸亥',
      note='王宗涤复用华洪改名后的既有人物，不误为王建本人。')

record = json.loads((P / 'sources/library' / supplement / 'paragraph.json').read_text())
def extra(key, field, text, quote, n, relation, note):
    assert quote in (P / 'sources/library' / supplement / 'source.txt').read_text()
    ck = f'claim_zztj_262_0900_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table='event', subject_key=key, field_path=field,
                            claim_text=text, source_key=supplement, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))
extra('event_zztj_262_0900_zhu_sends_ge_against_liu', 'time_original',
      '《旧五代史》梁纪在三年四月记葛从周率兗郓滑魏四镇兵伐沧州。',
      '三年四月，遣葛從周以兗、鄆、滑、魏之師伐滄州。', 7, 'corroborates',
      '三年承梁纪光化三年900；补出兵四月，不将主书未载干支日补成确日。')
extra(dezhou, 'description', '《旧五代史》梁纪记五月庚寅德州拔后，傅公和被枭首城上。',
      '五月庚寅，攻德州，拔之，梟刺史傅公和於城上。', 7, 'adds',
      '与主书拔德斩傅同役，枭首为该书补充，不把传记写成第二次处死。')
extra('event_zztj_262_0900_ge_sieges_shouwen_cangzhou', 'description',
      '《旧五代史》梁纪在五月己亥记葛从周军进攻浮阳；主书称围刘守文于沧州。',
      '己亥，進攻浮陽。', 7, 'adds',
      '同月同日同战事，浮阳与沧州地名并列，尚未由独立地理证据校定等同范围。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 9):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='前八段连续校核；任官、修城进谏、德州与沧州战事、邕州军乱拆分。疑讹“西川李度使”与拆字“李钅岁”原文保留；旧五代史同役补证，不将待考地名或兵数强行合并。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=262, year=900,
    primary_source_key=primary, primary_source_keys=[primary], paragraphs=[Q[n]['id'] for n in range(1, 9)],
    next_paragraph=Q[9]['id'], coverage='光化三年32段中的第1—8段连续处理，本年尚未完成。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
