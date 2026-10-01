"""Curate Tongjian 264, year 903, consecutive paragraphs 9–16."""
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
primary = 'tongjian-264-903-spring'
old_five = 'jiuwudaishi-012-zhu-youning'
new_five = 'xinwudaishi-061-yang-xingmi'

B = {'format_version': 1, 'batch_key': 'zztj-v264-y0903-p009-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P / 'sources/library' / primary, '71feb52', '司马光等'),
    (old_five, P / 'sources/library' / old_five, '71feb52', '薛居正等'),
    (new_five, P / 'sources/library' / new_five, '71feb52', '欧阳修等'),
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
for n in range(9, 17):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0903_02_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_264_0903_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 9. Appointment proposed by Zhu Quanzhong.
event('pei_shu_chancellor','裴枢任门下侍郎同平章事',9,
      '以清海节度使裴枢为门下侍郎、同平章事，硃全忠荐之矣。',
      [('裴枢','受任者'),('朱温','推荐者')],when='903年二月末至三月前；确日未载',
      note='“荐之”是朱全忠的举荐，不另推定朝廷其他决策人。')

# 10. Reported speech and political readings remain attributed.
event('li_keyong_comments_cui','李克用闻使者报告后批评崔胤',10,
      '李克用使者还晋阳，言崔胤之横，克用曰：“胤为人臣，外倚贼势，内胁其君，既执朝政，又握兵权。权重则怨多，势侔则衅生，破家亡国，在眼中矣。”',
      [('李克用','发言者'),('崔胤','被评论者')],when='903年二月末至三月前；确日未载',place='晋阳',
      note='“外倚贼势”“破家亡国”是李克用的评判与预言，不当作已发生结果。')
event('zhu_requests_li_favor','朱全忠临行请朝廷厚待李克用',10,
      '硃全忠将行，奏：“克用于臣，本无大嫌，乞厚加宠泽，遣大臣抚慰；俾知臣意。”',
      [('朱温','进奏者'),('李克用','进奏所涉者')],when='903年二月朱全忠离京前；确日未载',
      note='原文仅记请求，没有记朝廷落实宠泽与遣使。')
event('li_keyong_reads_zhu_intent','李克用闻朱全忠奏请后推测其欲攻淄青',10,
      '进奏吏以白克用，克用笑曰：“贼欲有事淄青，畏吾掎其后耳！”',
      [('李克用','判断者'),('朱温','被揣测者')],when='903年二月末至三月前；确日未载',
      note='“欲有事淄青”是李克用的判断，不能据此定为朱全忠已下达军令。')

# 11. Distinct battles and the dated arrival.
event('zhu_reaches_daliang','朱全忠戊午至大梁',11,
      '三月，戊午，硃全忠至大梁。',[('朱温','抵达者')],when='903年三月戊午',place='大梁')
event('wang_shilu_qizhou','王师鲁围齐州，朱友宁击退',11,
      '王师范弟师鲁围齐州，硃友宁引兵击走之。',
      [('王师鲁','围齐州者'),('朱友宁','击退围军者')],
      when='903年三月戊午后；确日未载',place='齐州',
      note='王师范未被记为亲临围城；“弟师鲁”另建兄长关系。')
event('zhu_blocks_yanzhou_aid','朱友宁截取王师范增援刘鄩军，葛从周围兖州',11,
      '师范遣兵益刘鄩军，友宁击取之。由是兗州援绝，葛从周引兵围之。',
      [('王师范','遣援军者'),('刘鄩','被增援者'),('朱友宁','截取援军者'),('葛从周','围兖州者')],
      when='903年三月；确日未载',place='兖州',
      note='“援绝”由主书明确归因于友宁截军；未推断刘鄩当段已败。')
event('zhu_youning_qingzhou','朱友宁进攻青州，朱全忠戊辰率诸军继进',11,
      '友宁进攻青州；戊辰，全忠引四镇及魏博兵十万继之。',
      [('朱友宁','进攻青州者'),('朱温','率军继进者')],when='903年三月；朱全忠继进为戊辰',place='青州',
      note='十万为主书所记兵数，未把进攻写成攻克。')

# 12. Li Shenfu's ruse at Ezhou; the outcome is limited to the burning.
event('li_shenfu_sieges_ezhou','李神福围鄂州并拟焚城中积荻',12,
      '淮南将李神福围鄂州，望城中积荻，谓监军尹建峰曰：“今夕为公焚之。”',
      [('李神福','围城并提出火攻者'),('尹建峰','听言的监军')],
      when='903年三月；确日未载',place='鄂州',
      note='“今夕为公焚之”为李神福预告；此句尚非焚烧已成。')
event('li_shenfu_fire_ruse','秦皋于滠口举火诱杜洪焚荻',12,
      '神福遣部将秦皋乘轻舟至滠口，举火炬于树杪。洪以为救兵至，果焚获以应之。',
      [('李神福','遣秦皋者'),('秦皋','举火者'),('杜洪','误认援军而焚荻者')],
      when='903年三月某夜；确日未载',place='滠口、鄂州',
      note='“获”疑为底本讹字，前文作“荻”；原文照录，按上下文注明为城中积荻，不改底本。')

# 13-14. Date and local seizure.
event('zhu_marshal_office','朱全忠判元帅府事',13,
      '夏，四月，己卯，以硃全忠判元帅府事。',
      [('朱温','受任者')],when='903年四月己卯')
event('ding_zhang_killed','知温州事丁章被木工李彦杀',14,
      '知温州事丁章为木工李彦所杀',
      [('丁章','被杀者'),('李彦','行凶者')],when='903年四月；确日未载',place='温州')
event('zhang_hui_wenzhou','张惠据温州',14,
      '其将张惠据温州。',[('张惠','据城者')],
      when='903年四月；确日未载',place='温州',
      note='“其将”回指丁章；未据此断定张惠参与丁章被杀。')

# 15. Aid to Wang Shifan and the unsuccessful diversion toward Suzhou.
event('yang_sends_wang_maozhang','杨行密遣王茂章率步骑七千援王师范',15,
      '王师范求救于淮南，乙未，杨行密遣其将王茂章以步骑七千救之',
      [('王师范','求援者'),('杨行密','遣援者'),('王茂章','率援军者')],
      when='903年四月乙未',place='淮南、青州',
      note='此段记遣军，王茂章后续胜败留待下文。')
event('yang_attacks_suzhou','杨行密另遣数万兵攻宿州，康怀英驰援后淮南军退',15,
      '又遣别将将兵数万攻宿州。全忠遣其将康怀英救宿州，淮南兵遁去。',
      [('杨行密','另遣兵者'),('朱温','遣康怀英者'),('康怀英','救宿州者')],
      when='903年四月乙未后；确日未载',place='宿州',
      note='“数万”为原书记述；淮南军遁去，不写成宿州陷落。')

# 16. Proposed brotherhood was rejected, so no relationship edge is created.
event('yang_asks_ma_alliance','杨行密遣使请马殷绝朱全忠并约为兄弟',16,
      '杨行密遣使诣马殷，言硃全忠跋扈，请殷绝之，约为兄弟。',
      [('杨行密','遣使提议者'),('马殷','被提议者'),('朱温','绝交提议所涉者')],
      when='903年四月；确日未载',
      note='“跋扈”是使者陈述；约为兄弟是提议，不录成既成结义关系。')
event('ma_declines_yang_proposal','马殷从许德勋议，未绝朱全忠',16,
      '许德勋曰：“全忠虽无道，然挟天子以令诸侯，明公素奉王室，不可轻绝也。”殷从之。',
      [('许德勋','进言者'),('马殷','采纳进言者'),('朱温','议论所涉者')],
      when='903年四月；确日未载',
      note='许德勋对朱全忠的评价归于其发言；“殷从之”只说明不轻绝。')

person('王师范',11,'王师鲁兄','王师范弟师鲁围齐州')
rel='relationship_person_王师范_person_王师鲁_兄长'
B['person_relationships'].append(dict(key=rel,person_a_key=people['王师范'],
    person_b_key=people['王师鲁'],relation_type='兄长',
    description='王师范是王师鲁的兄长。',status='draft'))
claim('person_relationship',rel,'description','王师范是王师鲁的兄长。',11,
      '王师范弟师鲁围齐州','“弟师鲁”明示王师范较长；未据此推王师范亲临围城。')

extra(old_five,'event','event_zztj_264_0903_wang_shilu_qizhou','description',
      '《旧五代史》朱友宁传亦记王师范遣弟围齐州，朱友宁救之。',
      '師範遣其弟將兵圍齊州。友寧引兵救之',11,'corroborates',
      '旧五代史另记夺马与斩首数，未合并进通鉴的主事件描述。')
extra(new_five,'event','event_zztj_264_0903_yang_sends_wang_maozhang','description',
      '《新五代史》杨行密世家亦记王师范求救、王茂章奉遣。',
      '王師範來求救，遣王茂章救之',15,'corroborates',
      '同段所记后续大败梁兵、朱友宁战死属未处理下文，不提前录入。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,17):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天复三年第9—16段连续处理；发言、提议与战果分清，原文繁简及疑讹字保留。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=903,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],
    coverage='卷264天复三年共54个非空段落中的第9—16段连续处理；同年后续仍待录入。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
