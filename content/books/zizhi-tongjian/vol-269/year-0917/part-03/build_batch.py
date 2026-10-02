"""Curate consecutive Tongjian vol. 269, 917 paragraphs 7–9."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 10))
main = 'tongjian-269-917-northern-frontier'
old28 = 'jiuwudaishi-028-newzhou'
specs = [
    (main,ROOT / 'content/books/zizhi-tongjian/vol-269/year-0917/part-02/sources/library' / main,'00253a75','司马光等'),
    (old28,ROOT / 'content/books/zizhi-tongjian/vol-269/year-0917/part-01/sources/library' / old28,'f5788d38','薛居正等'),
    ('jiuwudaishi-028-yuzhou-relief',P / 'sources/library/jiuwudaishi-028-yuzhou-relief','50b6b16a','薛居正等'),
    ('liaoshi-001-yuzhou-siege',P / 'sources/library/liaoshi-001-yuzhou-siege','50b6b16a','脱脱等'),
    ('xinwudaishi-061-xu-wen-move',P / 'sources/library/xinwudaishi-061-xu-wen-move','50b6b16a','欧阳修'),
    ('xinwudaishi-069-gao-tribute',P / 'sources/library/xinwudaishi-069-gao-tribute','50b6b16a','欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0917-p007-p009',
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
lines = (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()
for n in range(7, 10):
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
    for key in (main,):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明三年（917）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0917_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'晋王':'李存勖','契丹主':'阿保机','三郎':'徐知训','徐知诰':'李昪','李存审':'符存审'}.get(name, name)
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
    key = 'event_zztj_269_0917_' + code
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
        edge = 'participation_zztj_269_0917_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p007: siege, request for relief, decision and April departure.
event('khitan_siege_yuzhou','契丹乘新州之胜围幽州',7,
      '契丹乘胜进围幽州，声言有众百万，氈车毳幕弥温山泽。',
      [],when='917年三月至四月间；围城确日未载',place='幽州',
      note='百万为契丹声称之数，不作实际兵力；氈字保留底本字形。')
claim('event','event_zztj_269_0917_khitan_siege_yuzhou','description','《旧五代史》也记契丹乘胜攻幽州，并述同时有五十万与百万两种传闻。',7,
      '契丹乘勝寇幽州。是時言契丹者，或云五十萬，或云百萬',
      '人数为当时传闻，不能视作确数。',old28,'corroborates')
claim('event','event_zztj_269_0917_khitan_siege_yuzhou','time_original','《辽史》太祖纪系围幽州于神册二年四月。',7,
      '夏四月壬午，圍幽州，不克。','与主书段落衔接的三月至四月时间并列保留。','liaoshi-001-yuzhou-siege','adds')
event('lu_wenjin_siege_methods','卢文进教契丹作地道与土山围攻幽州',7,
      '卢文进教之攻城，为地道，昼夜四面俱进，城中穴地然膏以邀之。又为土山以临城，城中熔铜以洒之，日杀千计，而攻之不止。',
      [('卢文进','教授契丹攻城法者')],place='幽州',
      note='“日杀千计”为主书记述，未另核算杀伤；城中抵御方法亦按原文。')
event('zhou_dewei_requests_yuzhou_relief','周德威遣密使向晋王求援',7,
      '周德威遣间使诣晋王告急，王方与梁相持河上，欲分兵则兵少，欲勿救恐失之，忧形于色，谋于诸将，独李嗣源、李存审、阎宝劝王救之。',
      [('周德威','遣密使告幽州危急者'),('李存勖','收到求援并与诸将商议的晋王'),('李嗣源','主张救援的晋将'),('李存审','主张救援的晋将'),('阎宝','主张救援的晋将')],place='幽州、晋军河上营',
      note='李存审、阎宝主张等待契丹粮尽后追击，李嗣源主张立即赴援；同赞成救援但方案不同。')
claim('event','event_zztj_269_0917_zhou_dewei_requests_yuzhou_relief','description',
      '李存审、阎宝认为契丹辎重不足，宜待其粮尽再击；李嗣源请先行赴援。',7,
      '存审、宝以为虏无辎重，势不能久，俟其野无所掠，食尽自还，然后踵而击之。李嗣源曰：“周德威社稷之臣，今幽州朝夕不保，恐变生于中，何暇待虏之衰！臣请身为前锋以赴之。”',
      '分别记录主张，不把未执行的迟援方案写成战役。')
event('jin_orders_april_yuzhou_relief','晋王四月命李嗣源先赴涞水、阎宝继进',7,
      '夏，四月，晋王命嗣源将兵先进，军于涞水，阎宝以镇、定之兵继之。',
      [('李存勖','下令救援幽州的晋王'),('李嗣源','先率军至涞水者'),('阎宝','率镇定军继进者')],
      when='917年夏四月；确日未载',place='涞水',
      note='“军于涞水”是本段进度，不提前记为解幽州之围。')
claim('event','event_zztj_269_0917_jin_orders_april_yuzhou_relief','description',
      '《旧五代史》亦记四月李嗣源赴援驻涞水，阎宝进兵。',7,
      '夏四月，命李嗣源率師赴援，次於淶水；又遣閻寶率師夜過祁溝',
      '旧书补阎宝夜过祁沟及俘擒，未纳入主书事件结果。','jiuwudaishi-028-yuzhou-relief','corroborates')

# p008: Jianghuai administrative changes; no conflation of Xu father and son.
event('xu_wen_moves_zhenhai_seat','徐温采陈彦谦议，移镇海治所至升州',8,
      '五月，徐温行部至升州，爱其繁富。润州司马陈彦谦劝温徙镇海军治所于升州，温从之',
      [('徐温','决定移镇海军治所的掌权者'),('陈彦谦','建议迁治的润州司马')],
      when='917年五月；确日未载',place='升州',
      note='主书将繁富城市建设归徐知诰；建议者为陈彦谦，不将其当徐温之子。')
claim('event','event_zztj_269_0917_xu_wen_moves_zhenhai_seat','description',
      '《新五代史》吴世家亦记天祐十四年徐温迁治金陵。',8,
      '十四年，徐溫徙治金陵。','金陵是升州治所的称法；仅作同一迁治的书证，不另建事件。','xinwudaishi-061-xu-wen-move','corroborates')
event('xu_zhigao_transferred_runzhou','徐知诰由升州转任润州团练使',8,
      '温从之，徙知诰为润州团练使。知诰求宣州，温不许，知诰不乐。',
      [('徐温','调整徐知诰职位并拒绝宣州请求者'),('徐知诰','转任润州团练使者')],
      when='917年五月后；确日未载',place='润州',
      note='润州任命与请求宣州是两项不同动作；这里仅记录转任及请求被拒。')
event('song_qiqiu_advises_xu_zhigao','宋齐丘密劝徐知诰就润州官',8,
      '宋齐丘密言于知诰曰：“三郎骄纵，败在朝夕。润州去广陵隔一水耳，此天授也。”知诰悦，即之官。三郎，谓温长子知训也。',
      [('宋齐丘','密劝徐知诰就任润州者'),('徐知诰','接受宋齐丘建议者'),('徐知训','宋齐丘言及的徐温长子')],
      when='917年五月后；确日未载',place='润州',
      note='“三郎”由主书明释为徐知训；评论败亡是当时预测，不写成917年已发生。')
event('chen_yanqian_zhenhai_judge','徐温任陈彦谦为镇海节度判官',8,
      '温以陈彦谦为镇海节度判官。温但举大纲，细务悉委彦谦，江、淮称治。彦谦，常州人也。',
      [('徐温','任陈彦谦判官并委以细务者'),('陈彦谦','出任镇海节度判官者')],
      when='917年五月后；确日未载',place='升州',
      note='常州籍贯另见人物事实；“江、淮称治”是主书评价。')
claim('person',people['陈彦谦'],'description','《通鉴》称陈彦谦为常州人。',8,
      '彦谦，常州人也。','籍贯据本段，不推断生地或现代坐标。')

# p009: Gao Jichang and Gao Jixing are the same established person.
event('gao_jichang_restores_liang_tribute','高季昌与孔勍修好，恢复向后梁贡献',9,
      '高季昌与孔勍修好，复通贡献。',
      [('高季昌','与孔勍修好并恢复贡献的荆南节度使'),('孔勍','与高季昌修好的梁将')],
      when='917年五月后；本段未载具体月日',place='荆南',
      note='简短条目仅记修好与恢复贡献，不推断具体谈判条款。')
claim('event','event_zztj_269_0917_gao_jichang_restores_liang_tribute','description',
      '《新五代史》高季兴传称此前绝贡数年，贞明三年复修贡。',9,
      '乃絕貢賦累年。梁末帝優容之，封季興渤海王，賜以衮冕劍佩。貞明三年，始復脩貢。',
      '高季兴为高季昌异名，复用同一主体；旧书“累年”不可量化为确切年数。','xinwudaishi-069-gao-tribute','corroborates')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(7, 10):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷269贞明三年第7—9段；契丹围幽州及晋援、徐温迁镇海治所、高季昌复贡。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=917,
    primary_source_key=main,primary_source_keys=[main],paragraphs=[Q[n]['id'] for n in range(7,10)],
    next_paragraph='卷270贞明三年第1段（待建账本）',
    coverage='卷269贞明三年第7—9段；契丹围幽州与晋军救援、吴镇海迁治及荆南复贡。',
    supplements=supplements,reviewed_questions=[
      {'paragraph_id':Q[7]['id'],'note':'契丹声称百万、旧书又记五十万传闻，均不作实兵数；晋救援方案和实际进兵分开。'},
      {'paragraph_id':Q[8]['id'],'note':'徐温、徐知诰、徐知训及陈彦谦分别复用或新建；宋齐丘之预测不提前写成事件。'},
      {'paragraph_id':Q[9]['id'],'note':'新五代史用“高季兴”，本站复用高季昌及别名；“始复修贡”与主书互证。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
