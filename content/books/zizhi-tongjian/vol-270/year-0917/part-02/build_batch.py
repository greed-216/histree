"""Curate consecutive Tongjian vol. 270, 917 paragraphs 5–7."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 21))
main1 = 'tongjian-270-917-start'
main2 = 'tongjian-270-917-autumn'
old28 = 'jiuwudaishi-028-yuzhou-august-relief'
old23 = 'jiuwudaishi-023-liu-xun-917'
old09 = 'jiuwudaishi-009-qian-liu'
liao01 = 'liaoshi-001-yuzhou-relief'
specs = [
    (main1,ROOT / 'content/books/zizhi-tongjian/vol-270/year-0917/part-01/sources/library' / main1,'8cdf5b01','司马光等'),
    (main2,P / 'sources/library' / main2,'d1b943a5','司马光等'),
    (old28,ROOT / 'content/books/zizhi-tongjian/vol-270/year-0917/part-01/sources/library/jiuwudaishi-028-yuzhou-relief','8cdf5b01','薛居正等'),
    (old23,P / 'sources/library/jiuwudaishi-023-liu-xun','d1b943a5','薛居正等'),
    (old09,P / 'sources/library' / old09,'d1b943a5','薛居正等'),
    (liao01,P / 'sources/library' / liao01,'d1b943a5','脱脱等'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0917-p005-p007',
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
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/270.txt').read_text().splitlines()
for n in range(5, 8):
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
    for key in (main1, main2):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source in (main1, main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷270·贞明三年（917）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_270_0917_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1, main2):
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'晋王':'李存勖','李存审':'符存审','吴越王镠':'钱镠','嗣源':'李嗣源','从珂':'李从珂'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases=[],
                   era='五代十国', birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明三年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '原文称谓与既有姓名合并；原文摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=917):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_270_0917_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '917年本段条；确日未载', dynasty='五代十国',
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
          '只保留原纪年，不换算公历日；叙述性回顾不推成逐次日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_270_0917_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p005: the relief of Youzhou; the final Lu Wenjin sentences are retrospective.
event('yuzhou_siege_nearly_two_hundred_days','幽州被契丹围困近二百日',5,
      '契丹围幽州且二百日，城中危困。',[],when='917年八月前；围城约二百日',place='幽州',
      note='“且二百日”为主书概数，不反推围城起讫精确日。')
event('jin_relief_army_gathers_yizhou','李嗣源、阎宝、符存审会七万步骑于易州',5,
      '李嗣源、阎宝、李存审步骑七万会于易州',
      [('李嗣源','赴援将领'),('阎宝','赴援将领'),('李存审','赴援将领')],
      when='917年八月前后；确日未载',place='易州',
      note='七万为主书所载总兵数，尚未解围；李存审复用符存审。')
claim('event','event_zztj_270_0917_jin_relief_army_gathers_yizhou','description',
      '《旧五代史》同记李存审与李嗣源会易州、步骑七万。',5,
      '帝遣李存審領軍與嗣源會於易州，步騎凡七萬',
      '数字为史书所记，不代表现代核算。',old28,'corroborates')
event('jin_relief_chooses_mountain_route','李嗣源主张晋军循山路潜趋幽州',5,
      '嗣源曰：“虏无辎重，吾行必载粮食自随，若平原相遇，虏抄吾粮，吾不战自溃矣。不若自山中潜行趣幽州，与城中合势，若中道遇虏，则据险拒之。”',
      [('李嗣源','提出避开平原、循山路增援者')],
      when='917年出易州前；确日未载',place='易州至幽州山路',
      note='将领的战术判断按原话记录，不据此推定敌军实际辎重。')
event('jin_relief_crosses_dafangling','晋军甲午出易州、庚子越大房岭',5,
      '甲午，自易州北行，庚子，逾大房岭，循涧而东。',
      [('李嗣源','前锋将领'),('李存审','援军将领'),('阎宝','援军将领')],
      when='917年八月甲午至庚子；确公历日期未换算',place='易州、大房岭',
      note='按原文日序；不据地名设置现代坐标。')
event('li_siyuan_congke_break_khitan_blockade','李嗣源与养子李从珂力战，冲开契丹山口阻截',5,
      '嗣源与养子从珂将三千骑为前锋，距幽州六十里，与契丹遇。契丹惊却，晋兵翼而随之。契丹行山上，晋兵行涧下，每至谷口，契丹辄邀之，嗣源父子力战，乃得进。',
      [('李嗣源','三千骑前锋主将'),('李从珂','李嗣源养子、前锋将领')],
      when='917年八月庚子后；确日未载',place='幽州西南山路',
      note='六十里为原文距离；养父子关系既有同一主体，未重复新建。')
claim('event','event_zztj_270_0917_li_siyuan_congke_break_khitan_blockade','description',
      '李嗣源率百余骑先冲敌阵，晋后军跟进使契丹兵退。',5,
      '嗣源以百馀骑先进，免胄扬鞭，胡语谓契丹曰：“汝无故犯我疆场，晋王命我将百万众直抵西楼，灭汝种族！”因跃马奋楇，三入其陈，斩契丹酋长一人。后军齐进，契丹兵却，晋兵始得出。',
      '“百万众”是李嗣源战场喊话，不作晋军真实兵数。')
event('fu_cunshen_wooden_barrier_tactic','符存审命步兵持木枝成鹿角寨抵御契丹骑兵',5,
      '李存审命步兵伐木为鹿角，人持一枝，止则成寨。契丹骑环寨而过，寨中发万弩射之，流矢蔽日，契丹人马死伤塞路。',
      [('李存审','布置鹿角寨及弩兵抵骑者')],
      when='917年八月幽州山路交战期间',place='幽州近郊',
      note='“万弩”“死伤塞路”按主书叙事；未换算具体装备与伤亡。')
event('jin_defeats_khitan_before_yuzhou','符存审设烟尘诱敌，晋军击败幽州城外契丹军',5,
      '将至幽州，契丹列陈待之。存审命步兵陈于其后，戒勿动，先令羸兵曳柴然草而进，烟尘蔽天，契丹莫测其多少。因鼓噪合战，存审乃趣后陈起乘之，契丹大败',
      [('李存审','布置烟尘与后阵攻击者')],
      when='917年八月辛丑之前；确日未载',place='幽州城外',
      note='战果据主书；“俘斩万计”属史书估述，不作为精确统计。')
event('jin_enters_yuzhou_relief','李嗣源等辛丑入幽州，周德威迎见',5,
      '辛丑，嗣源等入幽州，周德威见之，握手流涕。',
      [('李嗣源','率援军入幽州者'),('周德威','幽州守将、迎见援军者'),('李存审','援军将领'),('阎宝','援军将领')],
      when='917年八月辛丑',place='幽州',
      note='三将按前文援军组织归并；此处主句以嗣源等概称。')
claim('event','event_zztj_270_0917_jin_enters_yuzhou_relief','description',
      '《旧五代史》亦记辛丑晋军入幽州，周德威与诸将相见。',5,
      '辛丑，大軍入幽州，德威見諸將，握手流涕。',
      '同文内容可能源流相关，作独立引文而非证明两书完全独立。',old28,'corroborates')
claim('event','event_zztj_270_0917_jin_enters_yuzhou_relief','description',
      '《辽史》太祖纪称八月李存勖遣李嗣源等救幽州，契丹留守将因兵少退去。',5,
      '秋八月，李存勗遣李嗣源等救幽州，曷魯等以兵少而還。',
      '辽史把退军归于曷鲁等兵少，与主书大军战败细节不完全同说；并列。',liao01,'conflicts')
event('lu_wenjin_later_khitan_raids','卢文进后居平州，屡导契丹骑兵侵晋北边',5,
      '契丹以卢文进为幽州留后，其后又以为卢龙节度使，文进常居平州，帅奚骑岁入北边，杀掠吏民。',
      [('卢文进','契丹任用、后居平州侵北边者')],
      when='幽州解围后追叙；起止年份未载',place='平州及北边',year=None,
      note='“其后”“常”“岁”是跨年追叙，不全归为917年。')
claim('event','event_zztj_270_0917_lu_wenjin_later_khitan_raids','description',
      '主书称卢文进引汉卒为向导，使卢龙所属诸州受害。',5,
      '契丹每入寇，则文进帅汉卒为乡导，卢龙巡属诸州为之残弊。',
      '反复性记述不拆成逐年未具名的战事。')

# p006 and p007: Liang court consequences and Wuyue title.
event('liu_xun_demoted_bozhou','后梁因河朔失守罢刘鄩同平章事，贬亳州团练使',6,
      '刘鄩自滑州入朝，朝议以河朔失守责之。九月，落鄩平章事，左迁亳州团练使。',
      [('刘鄩','被朝议责河朔失守并贬任者')],
      when='917年九月；确日未载',place='滑州、亳州',
      note='“责之”是朝议归咎，不直接断定所有河朔失守皆由刘鄩一人造成。')
claim('event','event_zztj_270_0917_liu_xun_demoted_bozhou','description',
      '《旧五代史》刘鄩传亦记九月落平章事、授亳州团练使，并称刘鄩上表避位。',6,
      '其年，河朔失守，朝廷歸咎於鄩，鄩亦不自安，上表避位。九月，落平章事，授亳州團練使。',
      '补旧书“上表避位”细节，不把朝廷归咎直接写成已证实的军事责任。',old23,'corroborates')
event('qian_liu_generalissimo','后梁加钱镠天下兵马元帅',7,
      '冬，十月，己亥，加吴越王镠天下兵马元帅。',
      [('吴越王镠','受加天下兵马元帅的吴越王')],
      when='917年冬十月己亥',place='吴越',
      note='官号与具体日期据主书；不推断其此时实际统辖天下诸军。')
claim('event','event_zztj_270_0917_qian_liu_generalissimo','description',
      '《旧五代史》末帝纪同日详记钱镠加天下兵马元帅。',7,
      '己亥，以啟聖匡運同德功臣、諸道兵馬元帥、淮南鎮海鎮東等軍節度使、充淮南宣潤等四面行營都統、開府儀同三司、尚書令、吳越王錢鏐為天下兵馬元帥。',
      '旧书保留其原有官衔串列；不据此推定实际辖境。',old09,'corroborates')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(5,8):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷270贞明三年第5—7段；晋援幽州与卢文进追叙、刘鄩降职、钱镠加号。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=270,year=917,
    primary_source_key=main1,primary_source_keys=[main1,main2],paragraphs=[Q[n]['id'] for n in range(5,8)],next_paragraph=Q[8]['id'],
    coverage='卷270贞明三年第5—7段；晋军解幽州之围、后梁与吴越官职。',supplements=supplements,
    reviewed_questions=[
      {'paragraph_id':Q[5]['id'],'note':'围城二百日与各军兵数按史书概数；卢文进“其后”“岁”是追叙不定年，辽史对退兵原因另有说法。'},
      {'paragraph_id':Q[6]['id'],'note':'刘鄩被朝廷归咎不等于全部败责已核实；旧五代史补上表避位。'},
      {'paragraph_id':Q[7]['id'],'note':'天下兵马元帅是授予钱镠的官号，不外推实辖天下。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
