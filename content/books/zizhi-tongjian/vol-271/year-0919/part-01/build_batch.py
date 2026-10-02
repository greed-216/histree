"""Curate consecutive Tongjian volume 271, year 919, paragraphs 1–4."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 9))
specs = [
    ('tongjian-271-919-autumn-winter', P / 'sources/library/tongjian-271-919-autumn-winter', 'd78219e5', '司马光等'),
    ('jiuwudaishi-009-yanzhou-fall', P / 'sources/library/jiuwudaishi-009-yanzhou-fall', 'd78219e5', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0919-p001-p004',
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
lines = (ROOT / 'resources/derived/tongjian/271.txt').read_text().splitlines()
for n in range(1, 5):
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
        citation = f'卷271·贞明五年（919）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0919_01_{len(B["claims"])+1:04d}'
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
            '郑氏':'钱镠宠姬郑氏','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271贞明五年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='919年本段条；确日未载', note='', year=919, place='吴'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0919_' + code
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
        edge = 'participation_zztj_271_0919_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('yang_meng_sent_to_chuzhou','吴将庐江公杨濛外放为楚州团练使',1,
      '冬，十月，出濛为楚州团练使。',
      [('濛','出任楚州团练使的吴庐江公')],
      when='919年十月；确日未载',place='楚州',
      note='承上卷杨濛议论及徐温恶之；“出”只说明外任，不擅认正式罪名或囚禁。')

event('li_cunxu_enlarges_desheng_north','晋王至魏州，征数万徒扩德胜北城并与梁军频战',2,
      '晋王如魏州，发徒数万，广德胜北城，日与梁人争，大小百馀战，互有胜负。',
      [('晋王','发徒扩德胜北城并率军与梁争者')],
      when='919年冬十月后本段；确日未载',place='魏州、德胜北城',
      note='“百馀战”与“互有胜负”是持续交战概括，不造百余单独战斗记录。')
event('liu_zhiyuan_rescues_shi_jingtang','刘知远在河壖战中让马救石敬瑭，两人得免',2,
      '左射军使石敬塘与梁人战于河壖，梁人击敬瑭，断其马甲，横冲兵马使刘知远以所乘马授之，自乘断甲者徐行为殿；梁人疑有伏，不敢追，俱得免，敬瑭以是亲爱之。',
      [('石敬塘','在河壖战中获刘知远让马而脱险者'),('刘知远','让马给石敬瑭、自乘受损之马断后者')],
      when='919年冬十月后本段；确日未载',place='河壖',
      note='本句先作“石敬塘”、后作“敬瑭”，同段同事按石敬瑭一人；电子底本异字保留，待纸本核。')
claim('person','person_石敬瑭','description','石敬瑭和刘知远先世皆沙陀；石敬瑭是李嗣源女婿。',2,
      '敬瑭、知远，其先皆沙陀人。敬瑭，李嗣源之婿也。',
      '先世与姻亲是主书说明，未据此推生年或未名配偶。')
father_in_law=person('李嗣源',2,'石敬瑭之岳父','敬瑭，李嗣源之婿也。')
son_in_law=person('石敬瑭',2,'李嗣源之婿','敬瑭，李嗣源之婿也。')
rk='relationship_zztj_271_0919_li_siyuan_father_in_law_of_shi_jingtang'
B['person_relationships'].append(dict(key=rk,person_a_key=father_in_law,person_b_key=son_in_law,
    relation_type='岳父',description='李嗣源是石敬瑭的岳父。',status='draft'))
claim('person_relationship',rk,'description','李嗣源是石敬瑭的岳父。',2,
      '敬瑭，李嗣源之婿也。','“婿”明示女婿身份，反向写岳父，未名之妻不另建主体。')

event('liu_xun_besieges_zhang_wanjin','刘鄩经年围兗州，张万进军情困窘',3,
      '刘鄩围张万进于兗州经年，城中危窘，晋王方与梁人战河上，力不能救。',
      [('刘鄩','经年围攻兗州的梁将'),('张万进','兗州被围的守将'),('晋王','当时因河上战事未能援救者')],
      when='919年本段概述经年围城；始年未载',year=None,place='兗州、河上',
      note='围城跨年，起始年不明；晋王当时无力救援不等于拒绝全部请求。')
event('liu_churang_begs_jin_relief','刘处让代表张万进乞晋援，截耳明志',3,
      '万进遣亲将刘处让乞师于晋，晋王未之许，处让于军门截耳曰：“苟不得请，生不如死！”',
      [('张万进','遣刘处让求援者'),('刘处让','乞师并截耳求援者'),('晋王','初未许援请求者')],
      when='919年兗州陷前；确日未载',place='兗州、晋军门',
      note='刘处让为新主体，后来的任官分录；“未之许”是起初未允。')
event('liu_xun_takes_yanzhou_zhang_family_killed','刘鄩破兗州、张万进被族，晋王止出兵',3,
      '晋王义之，将为出兵，会鄩已屠兗州，族万进，乃止。',
      [('晋王','称义刘处让并拟出兵但闻城破而止者'),('刘鄩','攻破兗州的梁将'),('张万进','城破后被族的兗州守将')],
      when='919年冬十月本段；确日未载',place='兗州',
      note='“将为出兵”未实际出兵；“族万进”记录主书措辞，旧书另明擒张守进、夷其族。')
claim('event','event_zztj_271_0919_liu_xun_takes_yanzhou_zhang_family_killed','description',
      '《旧五代史》卷九记十月刘鄩攻下兗州、擒张守进并夷其族。',3,
      '是月，劉鄩攻下兗州，擒張守進，夷其族。',
      '张守进是张万进受梁赐名后的旧书称法；主书“族万进”与补书“擒后夷族”的细节分别保存。',
      'jiuwudaishi-009-yanzhou-fall','adds')
event('liu_churang_appointed_guard_general','晋王以刘处让为行台左骁卫将军',3,
      '以处让为行台左骁卫将军。处让，沧州人也。',
      [('刘处让','被任行台左骁卫将军者')],
      when='919年兗州陷后本段；确日未载',place='晋',
      note='沧州籍贯仅据主书记载；不将任命提前到兗州陷前。')

event('zhang_chong_raids_anzhou','吴武宁节度使张崇十一月寇安州',4,
      '十一月，吴武宁节度使张崇寇安州。',
      [('张崇','率吴军进攻安州的武宁节度使')],
      when='919年十一月；确日未载',place='安州',
      note='“寇”只证明进攻，不据此说吴军已占安州。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 5):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷271贞明五年第1—4段；杨濛出楚州、德胜战斗及石敬瑭刘知远、兗州陷落与安州进攻。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=271, year=919,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(1, 5)], next_paragraph=Q[5]['id'],
    coverage='卷271贞明五年第1—4段；杨濛外任、晋梁争德胜、兗州陷落与吴攻安州。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[2]['id'],'note':'主书同段先作石敬塘、后作敬瑭，按石敬瑭同人复用；异字保留快照。李嗣源为其岳父有“婿”明证。'},
      {'paragraph_id':Q[3]['id'],'note':'兗州围城跨年，始年未核；旧书称张守进（张万进赐名）并记擒后夷族，不把晋王拟出兵写成已出兵。'},
      {'paragraph_id':Q[4]['id'],'note':'吴军“寇安州”未说明攻克，事件只录进攻。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
