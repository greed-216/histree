"""Curate consecutive Tongjian volume 270, year 919, paragraphs 16–18."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 24))
specs = [
    ('tongjian-270-919-late', P / 'sources/library/tongjian-270-919-late', 'c239fe89', '司马光等'),
    ('jiuwudaishi-126-fengdao-counsel', P / 'sources/library/jiuwudaishi-126-fengdao-counsel', 'c239fe89', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0919-p016-p018',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
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
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/270.txt').read_text().splitlines()
for n in range(16, 19):
    assert Q[n]['text'] == lines[Q[n]['source_line'] - 1]
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

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷270·贞明五年（919）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_270_0919_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'蜀主':'王宗衍','晋王':'李存勖','汉主岩':'刘岩',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨隆演',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷270贞明五年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='919年本段条；确日未载', note='', year=919, place='吴'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_270_0919_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。')
    claim('event', key, 'time_original', when, n, quote,
          '按主书本段纪时；追叙或他书记载另作说明，不自行换算公历日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_270_0919_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('qian_liu_grieves_he_feng','钱镠见何逢坐骑悲恸，史书称将士归心',16,
      '吴越王镠见何逢马，悲不自胜，故将士心附之。',
      [('吴越王镠','见何逢马而悲恸的吴越王'),('何逢','前战身亡、遗马为钱镠所见者')],
      when='919年何逢战死后本段；确日未载',place='吴越',
      note='何逢已在上段无锡战事被杀；“将士心附”是主书评述，不推出每名将士的行为。')
event('qian_liu_punishes_zheng_father','钱镠不为宠姬郑氏父亲违法求情开脱',16,
      '宠姬郑氏父犯法当死，左右为之请，镠曰：“岂可以一妇人乱我法。”出其女而斩之。',
      [('吴越王镠','拒绝求情并处死郑氏之父者'),('郑氏','父亲犯法后被遣出的钱镠宠姬')],
      when='钱镠在位期间追叙；发生年未载',year=None,place='吴越',
      note='郑氏父亲未具名，不新建虚构姓名；此为回顾事例，未定919年。')
event('qian_liu_vigilance_habits','钱镠在军中长期保持警醒，以警枕、粉盘等自督',16,
      '镠自少在军中，夜未尝寐，倦极则就圆木小枕，或枕大铃，寐熟辄欹而寤，名曰：“警枕”。置粉盘于卧内，有所记则书盘中，比老不倦。',
      [('吴越王镠','使用警枕、粉盘的军中主帅')],
      when='钱镠早年至晚年习惯；起止年未载',year=None,place='吴越',
      note='主书以“自少”“比老”概述长期习惯，不能定为919年单次事件。')
event('qian_liu_rewards_gate_guard','钱镠微行遭北门吏拒开关，次日厚赏守吏',16,
      '尝微行，夜叩北城门，吏不肯启关，曰：“虽大王来亦不可启。”乃自他门入。明日，召北门吏，厚赐之。',
      [('吴越王镠','微行并赏守门吏者')],
      when='钱镠在位期间追叙；发生年未载',year=None,place='吴越北城门',
      note='北门吏未具名；“明日”仅相对于夜叩城门，不换算公历日期。')

event('yang_longyan_enfeoffs_brothers_and_son','吴王杨隆演封四弟与一子为郡公',17,
      '丙戌，吴王立其弟濛为庐江郡公，溥为丹杨郡公，浔为新安郡公，澈为鄱阳郡公，子继明为庐陵郡公。',
      [('吴王','册立四弟与一子者'),('濛','被封庐江郡公的吴王之弟'),
       ('溥','被封丹杨郡公的吴王之弟'),('浔','被封新安郡公的吴王之弟'),
       ('澈','被封鄱阳郡公的吴王之弟'),('继明','被封庐陵郡公的吴王之子')],
      when='919年丙戌；本段未重标月份',place='吴',
      note='“其弟”统摄四人，“子继明”是吴王之子；保留丹杨原载字，不擅改地名。')
elder=person('杨隆演',17,'四弟之兄、杨继明之父','吴王立其弟濛为庐江郡公，溥为丹杨郡公，浔为新安郡公，澈为鄱阳郡公，子继明为庐陵郡公。')
for younger,title in [('杨濛','庐江郡公'),('杨溥','丹杨郡公'),('杨浔','新安郡公'),('杨澈','鄱阳郡公')]:
    rk='relationship_zztj_270_0919_yang_longyan_elder_of_'+younger
    B['person_relationships'].append(dict(key=rk,person_a_key=elder,person_b_key=people[younger],
        relation_type='兄长',description=f'杨隆演是{younger}的兄长。',status='draft'))
    claim('person_relationship',rk,'description',f'杨隆演是{younger}的兄长。',17,
          '吴王立其弟濛为庐江郡公，溥为丹杨郡公，浔为新安郡公，澈为鄱阳郡公，子继明为庐陵郡公。',
          f'本句“其弟”指吴王四弟，包括受封{title}的{younger}；仅定杨隆演相对其弟为兄，不排序四弟长幼。')
rk='relationship_zztj_270_0919_yang_longyan_father_of_yang_jiming'
B['person_relationships'].append(dict(key=rk,person_a_key=elder,person_b_key=people['杨继明'],
    relation_type='父亲',description='杨隆演是杨继明的父亲。',status='draft'))
claim('person_relationship',rk,'description','杨隆演是杨继明的父亲。',17,
      '吴王立其弟濛为庐江郡公，溥为丹杨郡公，浔为新安郡公，澈为鄱阳郡公，子继明为庐陵郡公。',
      '句中“子继明”明指吴王之子；端点方向为父亲指向儿子。')

event('li_cunxu_returns_jinyang_appoints_fengdao','晋王归晋阳，以冯道为掌书记',18,
      '晋王归晋阳，以巡官冯道为掌书记。',
      [('晋王','归晋阳并任命冯道者'),('冯道','由巡官任掌书记者')],
      when='919年本段；确日未载',place='晋阳',
      note='旧五代史冯道传另言张承业荐霸府从事、俄署太原掌书记，未给同一确日。')
claim('event','event_zztj_270_0919_li_cunxu_returns_jinyang_appoints_fengdao','description',
      '《旧五代史》冯道传称张承业荐其为霸府从事，旋署太原掌书记。',18,
      '承業尋薦為霸府從事，俄署太原掌書記',
      '补书提供荐举经过；“俄”不等于主书919年确日。',
      'jiuwudaishi-126-fengdao-counsel','adds')
event('fengdao_advises_li_cunxu_after_guo_request','郭崇韬请减诸将陪食，晋王发怒，冯道劝止',18,
      '中门使郭崇韬以诸将陪食者众，请省其数。王怒曰：“孤为效死者设食，亦不得专，可令军中别择河北帅，孤自归太原。”即召冯道令草词以示众。',
      [('郭崇韬','请减陪食诸将人数者'),('晋王','因请求发怒并命冯道草词者'),('冯道','受命草词而劝止者')],
      when='919年本段；确日未载',place='晋',
      note='请求减陪食人数与晋王激愤发言分明，不能写成郭崇韬主张更换晋王。')
claim('event','event_zztj_270_0919_fengdao_advises_li_cunxu_after_guo_request','description',
      '冯道劝晋王不因郭崇韬减陪食之请宣示君臣失和，晋王遂止。',18,
      '道执笔逡巡不为，曰：“大王方平河南，定天下，崇韬所请未至大过；大王不从可矣，何必以此惊动远近，使敌国闻之，谓大王君臣不和，非所以隆威望也。”会崇韬入谢，王乃止。',
      '主书因果限于本段对话与“王乃止”，不把冯道劝止扩成长期政策。')
claim('event','event_zztj_270_0919_fengdao_advises_li_cunxu_after_guo_request','description',
      '《旧五代史》卷一百二十六亦记郭崇韬请减陪食、冯道进言，郭崇韬入谢。',18,
      '道執筆久之，莊宗正色促焉，道徐起對曰：「道所掌筆硯，敢不供職。今大王屢集大功，方平南寇，崇韜所諫，未至過當，阻拒之則可，不可以向來之言，喧動群議，敵人若知，謂大王君臣之不和矣。幸熟而思之，則天下幸甚也。」俄而崇韜入謝，因道為之解焉',
      '补书有夹河对垒的背景，主书置于晋王归晋阳后；事件核心相合，地点编排差异保留待核。',
      'jiuwudaishi-126-fengdao-counsel','corroborates')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(16, 19):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明五年第16—18段；钱镠轶事多为追叙，吴王封弟子，冯道劝止陪食争议。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=919,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(16, 19)], next_paragraph=Q[19]['id'],
    coverage='卷270贞明五年第16—18段；钱镠行事回顾、吴王封四弟与一子及冯道劝晋王。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[16]['id'],'note':'何逢马可承上战事；郑氏父案、警枕和北门赏吏均为叙事性追忆，发生年未载，事件年置空。'},
      {'paragraph_id':Q[17]['id'],'note':'“其弟”只确定四人皆杨隆演弟，未明示四弟彼此长幼；继明为吴王之子，父亲方向明确。'},
      {'paragraph_id':Q[18]['id'],'note':'旧五代史卷126有冯道进言同类叙事，置于夹河对垒；主书置于晋王归晋阳后，地点与具体日次待核。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
