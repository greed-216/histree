"""Curate consecutive Tongjian volume 270, year 919, paragraphs 9–12."""
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
    ('jiuwudaishi-009-desheng-relief', P / 'sources/library/jiuwudaishi-009-desheng-relief', 'bc9c710b', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0919-p009-p012',
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
for n in range(9, 13):
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
    ck = f'claim_zztj_270_0919_03_{len(B["claims"])+1:04d}'
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
            '徐知诰':'李昪','徐知誥':'李昪'}.get(name, name)
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

event('he_gui_besieges_desheng_south','贺瑰围攻德胜南城并以艨艟阻晋援军',9,
      '贺瑰攻德胜南城，百道俱进，以竹笮联艨艟十馀艘，蒙以牛革，设睥睨、战格如城状，横于河流，以断晋之救兵，使不得渡。',
      [('贺瑰','率梁军围攻并阻断河渡者')],
      when='919年四月前后本段；主书确日未载',place='德胜南城',
      note='艨艟与竹笮设施按原文记录；本段另有两处私用字待校，事件标题不使用疑字。')
claim('event','event_zztj_270_0919_he_gui_besieges_desheng_south','description',
      '《旧五代史》卷九记四月贺瑰攻德胜南城，以艨艟横河阻晋援军。',9,
      '是月，賀瑰攻德勝南城，以艨艟戰艦橫於河，以扼津濟之路。',
      '旧书记四月，与主书本段未标确日的叙事相接；补书未记李建及等具体破障经过。',
      'jiuwudaishi-009-desheng-relief','corroborates')
event('li_cunxu_sends_ma_polong','晋王驰援德胜并遣马破龙入城探报',9,
      '晋王自引兵驰往救之，陈于北岸，不能进；遣善游者马破龙入南城，见守将氏延赏，延赏言矢石将尽，陷在顷刻。',
      [('晋王','率兵驰援并遣人探城者'),('马破龙','泅入德胜南城者'),('氏延赏','守城并告急者')],
      when='919年德胜南城围攻期间；确日未载',place='德胜南城、北岸',
      note='晋军初被截河不得渡；氏延赏报告矢石将尽，不把预期失守写作实际失守。')
event('li_jianji_breaks_liang_river_barrier','李建及率三百敢死士斧断竹笮、火攻梁艨艟',9,
      '乃选效节敢死士得三百人，被铠操斧，帅之乘舟而进。',
      [('李建及','领三百敢死士破梁河障者')],
      when='919年德胜南城围攻期间；确日未载',place='德胜河渡',
      note='主书电子底本两处作私用字，另处明写“艨艟”；疑字只保留在来源快照中待核，事件名称用明见字。')
claim('event','event_zztj_270_0919_li_jianji_breaks_liang_river_barrier','description',
      '李建及率士入舰间断竹笮，并放火船破河障。',9,
      '建及使操斧者入艨艟间，斧其竹笮，又以木罂载薪，沃油然火，于上流纵之，随以巨舰实甲士，鼓噪攻之。',
      '破障细节主书明确；不把疑字人工改写进出处摘录。')
event('jin_relief_desheng_liang_retires','晋军渡河解德胜南城围，贺瑰退屯行台村',9,
      '艨艟既断，随流而下，梁兵焚溺者殆半，晋兵乃得渡。瑰解围走，晋兵追之，至濮州而还。瑰退屯行台村。',
      [('李建及','破障使晋援军得渡者'),('贺瑰','解围退屯行台村者')],
      when='919年德胜南城围攻期间；确日未载',place='德胜、濮州、行台村',
      note='“殆半”为主书估计，未作精确伤亡数；追击至濮州后还。')
claim('event','event_zztj_270_0919_jin_relief_desheng_liang_retires','description',
      '《旧五代史》卷九记晋人断梁艨艟，渡河救援南城，贺瑰退军。',9,
      '晉人斷其艨艟，濟軍以援南城，瑰等退軍。',
      '与主书救援结果相合；旧书省略具体执行者。',
      'jiuwudaishi-009-desheng-relief','corroborates')

event('shu_ruler_forbids_unapproved_leave','蜀主禁止天策府诸将擅离屯戍',10,
      '蜀主命天策府诸将无得擅离屯戍。',
      [('蜀主','下令禁止擅离屯戍者')],place='蜀',
      note='禁令和后续违令获赦分录，不能据此说禁令从未生效。')
event('shu_ruler_pardons_three_officers','王承谔等三将违令，蜀主赦免',10,
      '五月，丁卯朔，左散旗军使王承谔、承勋、承会违命，蜀主皆原之。自是禁令不行。',
      [('王承谔','违令后被赦的左散旗军使'),('王承勋','违令后被赦者'),('王承会','违令后被赦者'),('蜀主','赦免三将者')],
      when='919年五月丁卯朔',place='蜀',
      note='“承勋”“承会”承上姓王；主书评述此后禁令不行，未逐次列事。')

event('chu_attacks_jingnan_gao_requests_wu','楚军攻荆南，高季昌向吴求援',11,
      '楚人攻荆南，高季昌求救于吴，',
      [('高季昌','荆南守臣、向吴求援者')],place='荆南',
      note='只记楚军进攻与求援，不推定楚军已攻下荆南。')
event('wu_dispatches_liu_xin_li_jian','吴遣刘信与李简分率步水军援荆南',11,
      '吴命镇南节度使刘信等帅洪、吉、抚、信步兵自浏阳趣潭州，武昌节度使李简等帅水军攻复州。',
      [('刘信','率洪吉抚信步兵趋潭州者'),('李简','率水军进攻复州者')],
      place='浏阳、潭州、复州',note='两路兵分录角色；不据同一命令推断同日到达。')
event('chu_retires_wu_takes_fuzhou','楚兵撤围荆南，吴军入复州执鲍唐',11,
      '信等至潭州东境，楚兵释荆南引归。简等入复州，执其知州鲍唐。',
      [('刘信','抵潭州东境促楚兵引归的吴将'),('李简','率军入复州者'),('鲍唐','被吴军执获的复州知州')],
      place='潭州东境、荆南、复州',note='楚兵撤围与吴军取复州分作同段先后结果；不追加未载的战斗细节。')

event('wu_defeats_wuyue_at_shashan','吴六月在沙山击败吴越兵',12,
      '六月，吴人败吴越兵于沙山。',[],when='919年六月；确日未载',place='沙山',
      note='短条只载胜负和地点；未明主将、兵力和战术，不补猜人物。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9, 13):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明五年第9—12段；德胜南城攻防、蜀主赦违令将、楚攻荆南与沙山交战。私用字保留原文，另有同段正确字形。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=919,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(9, 13)], next_paragraph=Q[13]['id'],
    coverage='卷270贞明五年第9—12段；德胜南城攻防、蜀禁令、楚吴荆南战事及沙山交兵。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[9]['id'],'note':'通鉴电子底本两见私用字，同段另有“艨艟”；仅来源快照保留疑字，语义按同段艨艟理解，纸本待核。旧五代史卷9概记四月贺瑰围城、晋人断舰救城。'},
      {'paragraph_id':Q[10]['id'],'note':'承勋、承会依句式承王姓，暂以王承勋、王承会识别；人物其他事迹待补。'},
      {'paragraph_id':Q[12]['id'],'note':'沙山短条无主将和日次，不从邻段反推人物或军数。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
