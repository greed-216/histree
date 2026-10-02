"""Curate consecutive Tongjian vol. 269, 915 paragraphs 12–14."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 34))
main = 'tongjian-269-915-wei'
old_28 = 'jiuwudaishi-028-he-delun'
old_21 = 'jiuwudaishi-021-he-delun'
old_71 = 'jiuwudaishi-071-sikong-ting'
old_69 = 'jiuwudaishi-069-wang-zhengyan'
new_26 = 'xinwudaishi-026-kong-qian'
specs = [
    (main, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0915/part-03/sources/library' / main, '5b089ca3', '司马光等'),
    (old_28, P / 'sources/library' / old_28, '70b0b93e', '薛居正等'),
    (old_21, P / 'sources/library' / old_21, '70b0b93e', '薛居正等'),
    (old_71, P / 'sources/library' / old_71, '70b0b93e', '薛居正等'),
    (old_69, P / 'sources/library' / old_69, '70b0b93e', '薛居正等'),
    (new_26, P / 'sources/library' / new_26, '70b0b93e', '欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0915-p012-p014',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_dirs = {key: path for key, path, _, _ in specs}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
for n in range(12, 15):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in (source_dirs[main] / 'source.txt').read_text(), n
registry = {}
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    for row in json.loads(path.read_text())['people']:
        old = registry.get(row['name'])
        if old:
            assert old['key'] == row['key'], (row['name'], path)
        registry[row['name']] = row
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=main, relation='adds'):
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明元年（915）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0915_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'李存审': '符存审'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明元年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '姓名按既有主体规范；原文和摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=915):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0915_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '915年本段条；确日未载', dynasty='五代十国',
               description=title + '。', phases=[], location_name=place,
               location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown',
               location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',
               status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote,
          note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', row['time_original'], n, quote,
          '段内追叙，确年待考。' if year is None else '按主书段落次序；未把干支换算成公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_269_0915_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key



# p012: transfer of the Wei seal, then separate reassignment and retention.
event('jin_wang_takes_wei_seal', '贺德伦请晋王入魏州并上印节，李存勖兼领天雄军', 12,
      Q[12]['text'].split('德伦帅将吏拜贺')[0],
      [('贺德伦','率将吏请晋王入城并上印节的前天雄节度使'),('李存勖','入魏州、先辞后接受天雄军印节的晋王')],
      when='915年六月庚寅朔', place='魏州府城',
      note='晋王起初推辞，后文“王乃受之”才确认接领；不把初辞当作最终拒绝。')
claim('event','event_zztj_269_0915_jin_wang_takes_wei_seal','description',
      '《旧五代史》卷二十八记六月庚寅晋王入魏州，贺德伦献符印。',12,
      '六月庚寅朔，帝入魏州，賀德倫上符印，請帝兼領魏州，帝從之。',
      '与主书接领相合；旧书以晋王方纪述，符印与印节为同一仪式的用语。',old_28,'corroborates')
event('he_delun_datong_detained', '李存勖改授贺德伦大同节度使，张承业留其于晋阳', 12,
      '王承制以德伦为大同节度使，遣之官。德伦至晋阳，张承业留之。',
      [('李存勖','承制改授贺德伦大同节度使的晋王'),('贺德伦','获改授大同而行至晋阳被留下者'),('张承业','于晋阳留住贺德伦的晋方监军')],
      when='915年六月庚寅朔后；确日未载', place='晋阳',
      note='原文“留之”只说明贺德伦未即赴大同，不提前写入后文死亡。')
claim('event','event_zztj_269_0915_he_delun_datong_detained','description',
      '《旧五代史》卷二十一记贺德伦授云州节度使，张承业留其于河东。',12,
      '尋授雲州節度使，行次河東，監軍張承業留之不遣。',
      '云州为大同军治所的表述待地名校核；旧书同样记其未赴任，不将后续被杀提前。',old_21,'adds')
# p013: suppressing disorder, delegating administration, then Sikong Ting's fall.
event('jin_weizhou_discipline', '李存勖下令严禁魏州军暴掠，李存进执行刑罚', 13,
      '时银枪效节都在魏城犹骄横，晋王下令：“自今有朋党流言及暴掠百姓者，杀无赦！”以沁州刺史李存进为天雄都巡按使。有讹言摇众及强取人一钱已上者，存进皆枭首磔尸于市。旬日，城中肃然，无敢喧哗者。',
      [('李存勖','在魏城颁禁军纪命令的晋王'),('李存进','受任天雄都巡按使并执法者')],
      when='915年六月后；确日未载', place='魏城',
      note='“强取人一钱已上”属原书记法，不能据此推出后世量刑制度；“旬日”是严治见效时长。')
claim('person', people['李存进'], 'aliases',
      '李存进本姓孙、名重进。', 13,
      '存进本姓孙，名重进，振武人也。',
      '本站复用既有李存进稳定主体；孙重进作为原姓名称，不另建人物。')
event('sikong_ting_manages_wei', '李存勖将天雄军府事务委司空颋办理', 13,
      '晋王多出征讨，天雄军府事皆委判官司空颋决之。',
      [('李存勖','将天雄军府务委交司空颋的晋王'),('司空颋','受托办理天雄军府事务的判官')],
      when='915年六月后；为持续任事，确日未载', place='魏州',
      note='“多出征讨”为概括背景，委任不能按一个确日定位。')
claim('event','event_zztj_269_0915_sikong_ting_manages_wei','description',
      '《旧五代史》卷七十一记庄宗仍以司空颋为判官，后来使其权军府事。',13,
      '莊宗仍以頲為判官，後以頲權軍府事。',
      '旧书“后”未给确日；与主书委府务方向相合，不倒推到入魏当日。',old_71,'corroborates')
event('zhang_yu_reports_sikong_letter', '张裕扣押司空颋召河南侄子的使者并报告晋王', 13,
      '颋有从子在河南，颋密使人召之。都虞候张裕执其使者以白王，',
      [('司空颋','密遣使者召河南从子的判官'),('张裕','扣押使者并向晋王报告的都虞候'),('李存勖','接到张裕报告的晋王')],
      when='915年司空颋管魏府务后；确日未载', place='魏州、河南',
      note='主书记召从子，不等于已证实通梁；旧书卷七十一作“侄在梁”、称使家奴。')
claim('event','event_zztj_269_0915_zhang_yu_reports_sikong_letter','description',
      '《旧五代史》卷七十一作司空颋召在梁之侄，家奴被张裕擒。',13,
      '頲有侄在梁，遣家奴以書召之，都虞候張裕擒其家奴',
      '主书作“从子在河南”，旧书作“侄在梁”；亲属称谓与所在政权并列，不直接断定通敌。',old_71,'adds')
event('sikong_ting_executed_wang_replaces', '李存勖族诛司空颋，以王正言代判官', 13,
      '王责颋曰：“自吾得魏博，庶事悉以委公，公何得见欺如是！独不可先相示邪？”揖令归第。是日，族诛于军门，以判官王正言代之。',
      [('李存勖','责问并下令处死司空颋、改用王正言的晋王'),('司空颋','被族诛的原判官'),('王正言','接任判官者')],
      when='915年张裕报告当日；确日未载', place='魏州军门',
      note='“族诛”据通鉴原字，不推定遇害亲属姓名或具体人数。')
claim('event','event_zztj_269_0915_sikong_ting_executed_wang_replaces','description',
      '《旧五代史》卷六十九记司空颋被诛后王正言继任节度判官。',13,
      '頲誅，代為節度判官。',
      '传记确认继任，未重复主书的族诛细节。',old_69,'corroborates')
claim('event','event_zztj_269_0915_sikong_ting_executed_wang_replaces','description',
      '《旧五代史》卷七十一将司空颋被杀归于“以谓通于梁”。',13,
      '以謂通於梁，遂見殺。',
      '旧书明确是怀疑/指称，不据此断定其确实通敌；旧书本段另转引《通鉴》族诛句，不作独立证据。',old_71,'adds')
# p014: appointment in 915; the decade of tax collection is retrospective.
event('kong_qian_appointed_zhidu', '李存勖任魏州孔目吏孔谦为支度务使', 14,
      '魏州孔目吏孔谦，勤敏多计数，善治簿书，晋王以为支度务使。',
      [('孔谦','从魏州孔目吏受任支度务使者'),('李存勖','任命孔谦的晋王')],
      when='915年取得魏博后；确日未载', place='魏州',
      note='后文“殆将十年”评其多年供军，与此任命不能混作同一时点。')
claim('event','event_zztj_269_0915_kong_qian_appointed_zhidu','description',
      '《新五代史》卷二十六记孔谦原为魏州孔目官，晋得魏博后任度支使。',14,
      '魏博入于晉，莊宗以為度支使。',
      '新书作度支使，主书作支度务使；是否同一职务的省称待核，不直接改写官名。',new_26,'corroborates')
claim('person',people['孔谦'],'biography',
      '《通鉴》追述孔谦为晋军长期供应军需，同时急征重敛，使魏博六州百姓困苦。',14,
      '魏州新乱之后，府库空竭，民间疲弊，而聚三镇之兵，战于河上，殆将十年，供亿军须，未尝有阙，谦之力也。然急征重敛，使六州愁苦，归怨于王，亦其所为也。',
      '这是跨多年回顾，不把十年军需、重税全部定在915年。')
claim('person',people['孔谦'],'biography',
      '《新五代史》卷二十六也评孔谦供给晋梁对峙军费有功，而民不胜其苦。',14,
      '謙調發供饋，未嘗闕乏，所以成莊宗之業者，謙之力為多，然民亦不勝其苦也。',
      '新书也是事后评述，与主书相近；不视为独立证明某一年度税额。',new_26,'corroborates')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(12, 15):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明元年第12—14段连续处理；贺德伦移镇、魏城整肃、司空颋被诛与孔谦任事分录，孔谦多年财政评价不强定为915年。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=915,
    primary_source_key=main, primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(12, 15)], next_paragraph=Q[15]['id'],
    coverage='卷269贞明元年六月及魏州新政第12—14段；贺德伦上印节、魏城纪律、司空颋被诛与孔谦财政任命。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[13]['id'],'note':'李存进本姓孙名重进，同人稳定key已复用，线上别名待补；司空颋召侄被疑通梁，未证明实际通敌。'},
      {'paragraph_id':Q[14]['id'],'note':'孔谦长期供军与重税为编年段内追述，未当作915年单一事件；新书官名作度支使。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
