"""Curate consecutive Tongjian volume 270, year 919, paragraphs 13–15."""
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
    ('tongjian-270-919-lanshan', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0919/part-02/sources/library/tongjian-270-919-lanshan', '9e9d8b9a', '司马光等'),
    ('xinwudaishi-061-caoyun-wuxi', P / 'sources/library/xinwudaishi-061-caoyun-wuxi', '7397fed5', '欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0919-p013-p015',
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
for n in range(13, 16):
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
    ck = f'claim_zztj_270_0919_04_{len(B["claims"])+1:04d}'
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
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪'}.get(name, name)
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

event('qian_chuanguan_attacks_changzhou','钱镠遣钱传瓘率军攻吴常州，徐温分兵抵御',13,
      '秋，七月，吴越王镠遣钱传瓘将兵三万攻吴常州，徐温帅诸将拒之，右雄武统军陈璋以水军下海门出其后。',
      [('吴越王镠','遣钱传瓘攻常州者'),('钱传瓘','率吴越军攻常州者'),('徐温','率吴将抵御者'),('陈璋','率水军出海门迂后者')],
      when='919年七月；确日未载',place='常州、海门',
      note='三万为原书军数；陈璋水军出敌后作为同段吴军部署，不推测具体行军日次。')
event('wuxi_battle_xu_wen_ill','无锡交战时徐温病热，陈彦谦迁军旗稳住中军',13,
      '壬申，战于无锡。会温病热，不能治军，吴越攻中军，飞矢雨集，镇海节度判官陈彦谦迁中军旗鼓于左，取貌类温者，擐甲胄，号令军事，温得少息。',
      [('徐温','病热暂不能指挥的吴军统帅'),('陈彦谦','迁旗鼓并设貌似徐温者号令者'),('钱传瓘','率吴越军与吴交战者')],
      when='919年七月壬申',place='无锡',
      note='人物陈彦谦的具体处置主书明载；病情仅述当时，未推定长期失能。')
event('wu_fire_defeats_wuyue_wuxi','吴军乘风纵火大败吴越兵，钱传瓘遁走',13,
      '俄顷，疾稍间，出拒之。时久旱草枯，吴人乘风纵火，吴越兵乱，遂大败，杀其将何逢、吴建，斩首万级。传瓘遁去，追至山南，复败之。',
      [('徐温','病稍间后率吴军出拒者'),('钱传瓘','兵败遁走的吴越将领'),
       ('何逢','被杀的吴越将领'),('吴建','被杀的吴越将领')],
      when='919年七月壬申战后；追击确日未载',place='无锡、山南',
      note='记录吴军乘风纵火与追击；“斩首万级”为主书说法，不当现代核定人数。')
claim('event','event_zztj_270_0919_wu_fire_defeats_wuyue_wuxi','description',
      '《新五代史》徐温传也记吴军无锡败越兵，但与曹筠归吴事同系在“十年”至“十二年”之间。',13,
      '秋，越人攻毗陵，溫戰于無錫，筠感溫前言，臨戰奔歸，遂敗越兵。十二年，封溫齊國公',
      '新书上下文“十年”对应天祐十年，主书在919年条；可能有不同无锡交战或纪年抵牾，不据同地同人武断合并，待核纸本。',
      'xinwudaishi-061-caoyun-wuxi','conflicts')
event('chen_zhang_wins_xiangwan','陈璋于香弯击败吴越军',13,
      '陈璋败吴越于香弯。',
      [('陈璋','在香弯败吴越兵者')],
      when='919年七月无锡之战后本段；确日未载',place='香弯',
      note='香弯沿用原载地名；不据现代音近地名给坐标。')
event('xu_wen_recaptures_then_reappoints_chen_shao','徐温悬赏生擒陈绍，崔彦章获之后仍用陈绍典兵',13,
      '温募生获叛将陈绍者赏钱百万，指挥使崔彦章获之。绍勇而多谋，温复使之典兵。',
      [('徐温','悬赏并重新任用陈绍者'),('陈绍','被获后复典兵者'),('崔彦章','生擒陈绍的指挥使')],
      when='919年七月本段；确日未载',place='吴',
      note='“叛将”与“复使典兵”均为主书措辞，未见陈绍叛归时间、悬赏兑现与否。')

event('cao_yun_prior_defection_xu_wen_mercy','曹筠此前奔吴越，徐温赦其家属并传话',14,
      '初，锦衣之役，吴马军指挥曹筠叛奔吴越，徐温赦其妻子，厚遇之，遣间使告之曰：“使汝不得志而去，吾之过也，汝无以妻子为念。”',
      [('曹筠','早先奔吴越的吴马军指挥'),('徐温','赦免曹筠家属并遣使致意者')],
      when='锦衣之役；具体年未据本段确定',year=None,place='吴、吴越',
      note='本段以“初”追述，不当919年发生；新五代史系“十年”临安之战附近，另作补书异文。')
event('cao_yun_returns_to_wu','曹筠在此役后复归吴，徐温不治罪并还其田宅官职',14,
      '及是役，筠复奔吴。温自数昔日不用筠言者三，而不问筠去来之罪，归其田宅，复其军职，筠内愧而卒。',
      [('曹筠','复归吴、复职后内愧而卒者'),('徐温','赦曹筠出入罪并归田宅复职者')],
      when='919年本段所承无锡之役后；卒日未载',place='吴',
      note='归吴属本段承接事件；“而卒”无确日，不把死亡定在无锡交战当日。')
claim('event','event_zztj_270_0919_cao_yun_returns_to_wu','description',
      '《新五代史》亦述曹筠受徐温前言感动、无锡战时归吴，但系于天祐十年附近。',14,
      '溫戰于無錫，筠感溫前言，臨戰奔歸，遂敗越兵。',
      '两书皆记曹筠归吴，纪年和其归来相对战斗的先后用语不同，保留异文待核。',
      'xinwudaishi-061-caoyun-wuxi','conflicts')

event('li_bian_proposes_suzhou_raid','李昪请以两千步卒伪装吴越军袭苏州，徐温未采',15,
      '知诰请帅步卒二千，易吴越旗帜铠仗，蹑败卒而东，袭取苏州。温曰：“尔策固善；然吾且求息兵，未暇如汝言也。”',
      [('知诰','提出伪装吴越军袭苏州者'),('徐温','肯定计策但暂拒实行者')],
      when='919年无锡战后；确日未载',place='苏州、吴',
      note='李昪当时称徐知诰，沿用既有稳定主体；提议未施行，不写苏州被攻取。')
event('xu_wen_declines_further_war','徐温拒诸将乘胜灭吴越之议，引军还',15,
      '温叹曰：“天下离乱久矣，民困已甚，钱公亦未易可轻；若连兵不解，方为诸君之忧。今战胜以惧之，戢兵以怀之，使两地之民各安其业，君臣高枕，岂不乐哉！多杀何为！”遂引还。',
      [('徐温','以息兵为由拒继续进兵并率军还者')],
      when='919年无锡战后；确日未载',place='吴越边境、吴',
      note='诸将另有尽步骑灭吴越的建议，徐温原话拒之；只记决策，不推断长期和议已经达成。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(13, 16):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明五年第13—15段；无锡战事、曹筠复归、李昪袭苏州之议与徐温息兵。新五代史同事纪年有异。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=919,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(13, 16)], next_paragraph=Q[16]['id'],
    coverage='卷270贞明五年第13—15段；吴、吴越无锡战事及曹筠归吴、徐温战后决策。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[13]['id'],'note':'新五代史卷61徐温传亦记无锡败越兵，但叙于“十年”与“十二年”之间；不能确定与通鉴919年是否同一战，保留纪年歧异。'},
      {'paragraph_id':Q[14]['id'],'note':'“初，锦衣之役”是追叙，未定919年；本段曹筠复归吴承上无锡战事，新五代史则系于更早纪年，待核。'},
      {'paragraph_id':Q[15]['id'],'note':'李昪时称知诰，提出袭苏州计策未施行；徐温实际引还，不能据此写吴取苏州。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
