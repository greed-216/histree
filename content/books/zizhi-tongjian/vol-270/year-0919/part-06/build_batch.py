"""Curate consecutive Tongjian volume 270, year 919, paragraphs 19–23."""
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
    ('tongjian-270-919-late', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0919/part-05/sources/library/tongjian-270-919-late', 'c239fe89', '司马光等'),
    ('jiuwudaishi-009-hegui-wangzan', P / 'sources/library/jiuwudaishi-009-hegui-wangzan', 'fba288fb', '薛居正等'),
    ('jiuwudaishi-009-liuyan-decree', P / 'sources/library/jiuwudaishi-009-liuyan-decree', 'fba288fb', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0919-p019-p023',
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
for n in range(19, 24):
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
    ck = f'claim_zztj_270_0919_06_{len(B["claims"])+1:04d}'
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
            '郑氏':'钱镠宠姬郑氏','王瓚':'王瓒'}.get(name, name)
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

event('gongyi_claims_daefeng_kingship','躬乂在天祐初聚众据开州称王、号大封国',19,
      '天祐初，高丽石窟寺眇僧躬乂，聚众据开州称王，号大封国，',
      [('躬乂','聚众据开州自立大封国王者')],
      when='天祐初；具体年未载',year=None,place='开州',
      note='本段以“初”追叙；人名躬乂保留通鉴电子底本字形，未仅凭音近并入他名。')
event('gongyi_envoy_jin_liqi_to_wu','躬乂遣佐良尉金立奇入贡吴',19,
      '至是，遣佐良尉金立奇入贡于吴。',
      [('躬乂','遣使入贡吴者'),('金立奇','奉遣入贡吴的佐良尉')],
      when='919年本段；确日未载',place='高丽、吴',
      note='“至是”连接本年，区别前文“唐灭高丽”“天祐初”背景；佐良尉为原书官称。')

event('he_gui_dies_august','宣义节度使贺瑰八月乙未朔卒',20,
      '八月，乙未朔，宣义节度使贺瑰卒。',
      [('贺瑰','卒于本段的梁将')],when='919年八月乙未朔',place='梁',
      note='旧五代史卷九同日记滑州节度使贺瑰卒；职衔称法并存，纸本待核。')
claim('event','event_zztj_270_0919_he_gui_dies_august','description',
      '《旧五代史》卷九也记八月乙未朔贺瑰去世，并补梁廷辍朝三日、赠侍中。',20,
      '八月乙未朔，滑州節度使賀瑰卒，輟視朝三日，詔贈侍中。',
      '滑州节度与主书宣义节度有职衔表述差异，补书所载赠官不改主书事实。',
      'jiuwudaishi-009-hegui-wangzan','adds')
event('wang_zan_replaces_he_gui','梁以开封尹王瓒为北面行营招讨使',20,
      '以开封尹王瓚为北面行营招讨使。',
      [('王瓚','新任北面行营招讨使的开封尹')],
      when='919年八月本段；确日未载',place='梁',
      note='瓚规范显示为王瓒，原书字形仍在引文；任命接贺瑰卒事，但不擅断具体日次。')
claim('event','event_zztj_270_0919_wang_zan_replaces_he_gui','description',
      '《旧五代史》卷九亦载梁廷命王瓚为北面行营招讨使。',20,
      '是月，命開封尹王瓚為北面行營招討使。',
      '补书有“是月”，同指八月；繁简仅用于王瓚/王瓒主体匹配。',
      'jiuwudaishi-009-hegui-wangzan','corroborates')
event('wang_zan_campaign_yangcun','王瓒渡河进军澶魏、退据杨村夹河筑垒',20,
      '瓚将兵五万，自黎阳渡河掩击澶、魏，至顿丘，遇晋兵而旋，瓚为治严，令行禁止，据晋人上游十八里杨村，夹河筑垒，运洛阳竹木造浮梁，自滑州馈运相继。',
      [('王瓚','统率梁军渡河、据杨村并造浮梁者')],
      when='919年八月后本段；确日未载',place='黎阳、顿丘、杨村、滑州',
      note='“遇晋兵而旋”未称大败；五万、十八里均照原书，不核作现代精确数量。')
claim('event','event_zztj_270_0919_wang_zan_campaign_yangcun','description',
      '《旧五代史》卷九另记王瓚与王彦章等率军渡黎阳、营杨村并造浮梁。',20,
      '瓚乃與許州留後王彥章等率大軍自黎陽濟，營於楊村，造浮梁以通津路。',
      '补书附王彦章随军；主书本段未明，暂作为附见，不把其写入主书参与。',
      'jiuwudaishi-009-hegui-wangzan','adds')
event('li_cunjin_builds_desheng_pontoon','李存进以苇笮系巨舰，于德胜逾月造浮梁',20,
      '晋蕃汉马步副总管、振武节度使李存进亦造浮梁于德胜，或曰：“浮梁须竹笮、铁牛、石囷，我皆无之，何以能成！”存进不听，以苇笮维巨舰，系于土山巨木，逾月而成，人服其智。',
      [('李存进','以苇笮造德胜浮梁的晋将')],
      when='919年八月后本段；历时逾月，确日未载',place='德胜',
      note='“逾月而成”是持续施工，未换算完工日；“人服其智”为史书评价。')

event('wu_returns_wuyue_captives','徐温奉吴王书归还无锡之俘，钱镠遣使请和',21,
      '吴徐温遣使以吴王书归无锡之俘于吴越；吴越王镠亦遣使请和于吴。',
      [('徐温','派使归俘的吴臣'),('钱镠','遣使向吴请和的吴越王'),('吴王','书信名义所出之吴王')],
      when='919年无锡战后本段；确日未载',place='吴、吴越',
      note='双方动作均为原文明示；未记正式条约签署日与遣使姓名。')
event('wu_rest_after_war','吴与吴越议和后，史书追述吴地长期休兵',21,
      '自是吴国休兵息民，三十馀州民乐业者二十馀年。',[],
      when='自919年本段以后约二十余年；非919年单年结果',year=None,place='吴',
      note='长期效果为史书回望，不把二十余年压缩为919年事实；三十馀州为原载概数。')
event('wu_urges_qian_liu_to_assume_kingship','吴王与徐温屡致书劝钱镠自王，钱镠不从',21,
      '吴王及徐温屡遗吴越王镠书，劝镠自王其国；镠不从。',
      [('吴王','多次致书劝钱镠自王者'),('徐温','多次致书劝钱镠自王者'),('钱镠','拒绝吴方劝说者')],
      when='919年后屡次；具体年月未载',year=None,place='吴、吴越',
      note='“屡”指多次，跨时未明，不造单次919年日期。')

event('liang_strips_liu_yan_offices','梁廷九月丙寅削刘岩官爵并命钱镠讨之',22,
      '九月，丙寅，诏削刘岩官爵，命吴越王镠讨之。',
      [('刘岩','被削官爵的对象'),('钱镠','受命攻讨刘岩的吴越王')],
      when='919年九月丙寅',place='梁、广州、吴越',
      note='诏命和实际攻讨分开，不能因下诏便认定钱镠出兵。')
claim('event','event_zztj_270_0919_liang_strips_liu_yan_offices','description',
      '《旧五代史》卷九亦载九月丙寅削刘岩官爵、诏钱鏐攻讨，并说梁廷理由为刘岩将谋僭号。',22,
      '九月丙寅，製削奪廣州節度使、南平王劉岩在身官爵，以其將謀僭號故也。仍詔天下兵馬元帥錢鏐指揮攻討。',
      '旧书保留繁体鏐及“将谋僭号”廷议说法；不把廷议动机改写为独立定论。',
      'jiuwudaishi-009-liuyan-decree','adds')
event('qian_liu_does_not_attack_liu_yan','钱镠虽受梁命，最终未攻刘岩',22,
      '镠虽受命，竟不行。',
      [('钱镠','受命后未实际出兵者')],
      when='919年九月诏命后；未行的观察期限未载',place='吴越、广州',
      note='“竟不行”为主书对诏命执行情况的结论，不能补造两军交战。')

event('yang_meng_objects_xu_wen_domination','吴庐江公杨濛感叹国家为他人所有，徐温闻而恶之',23,
      '吴庐江公濛有材气，常叹曰：“我国家而为它人所有，可乎！”徐温闻而恶之。',
      [('濛','表达对国家权柄旁落不满的吴庐江公'),('徐温','听闻杨濛言论而厌恶者')],
      when='919年本段概述；言论次数和确日未载',place='吴',
      note='“它人”未在引语直接点名，虽徐温闻而恶之，也不把言论扩大为杨濛已发动政变。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(19, 24):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明五年第19—23段；躬乂事按追叙与当年入贡分录，梁晋造浮梁、吴越议和、削刘岩官爵和杨濛言论。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=919,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(19, 24)], next_paragraph='zztj-v271-y0919-p001',
    coverage='卷270贞明五年第19—23段；高丽使吴、贺瑰卒与梁晋浮梁、吴越议和、刘岩削爵及杨濛言论。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[19]['id'],'note':'“初，唐灭高丽”及“天祐初”均是前事背景，不录作919年发生；躬乂名字按通鉴底本保留，异名待核。'},
      {'paragraph_id':Q[20]['id'],'note':'旧五代史称贺瑰为滑州节度使，主书称宣义节度使；旧书又附王彦章同军，分别保留，不扩作主书正文。王瓚显示规范作王瓒。'},
      {'paragraph_id':Q[21]['id'],'note':'二十馀年休兵和“屡遗书”为跨年总结，事件年空置；919年只给归俘与请和定年。'},
      {'paragraph_id':Q[23]['id'],'note':'杨濛的言论及徐温反应限于主书所载，不推定已实施夺权行动。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
