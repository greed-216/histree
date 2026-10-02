"""Curate consecutive Tongjian vol. 269, 916 paragraphs 34–36."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 39))
main = 'tongjian-269-916-yearend'
old106 = 'jiuwudaishi-106-zhang-guan'
specs = [
    (main, P / 'sources/library' / main, 'ff79148c', '司马光等'),
    (old106, P / 'sources/library' / old106, 'c7068f6b', '薛居正等'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0916-p034-p036',
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
for n in range(34, 37):
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
    for key in ([main]):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明二年（916）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0916_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'蜀主':'王建','晋王':'李存勖','李存审':'符存审','王宗播':'许存','契丹王阿保机':'阿保机','晋王':'李存勖'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases=[],
                   era='五代十国', birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明二年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '原文称谓与既有姓名合并；原文摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=916):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0916_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '916年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_269_0916_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p034: the five nephews are not all named; the executed nephew is also unnamed.
event('zhang_chengye_nephews_join_jin','张承业五侄自同州来依，晋王因承业而擢用',34,
      '河东监军张承业既贵用事，其侄瓘等五人自同州往依之，晋王以承业故，皆擢用之。',
      [('张承业','受五名侄辈投依的河东监军'),('张瓘','自同州往依张承业的五名侄辈之一'),('李存勖','因张承业而擢用其五侄的晋王')],
      place='同州、河东',note='只具名瓘，不为其余四人补名；“既贵用事”是背景，未给始年。')
guan = person('张瓘',34,'张承业之侄','其侄瓘等五人自同州往依之')
chengye = person('张承业',34,'张瓘的伯叔辈亲属','其侄瓘等五人自同州往依之')
rel = 'relationship_person_张瓘_person_张承业_侄子'
B['person_relationships'].append(dict(key=rel,person_a_key=guan,person_b_key=chengye,
    relation_type='侄子',description='张瓘是张承业的侄子。',status='draft'))
claim('person_relationship',rel,'description','张瓘是张承业的侄子。',34,
      '其侄瓘等五人自同州往依之','“其”承张承业；张瓘为具名侄辈，不推断承业与其父的具体排行。')
claim('person',guan,'description','《旧五代史》张瓘传亦称其为张承业犹子，同州车渡村人。',34,
      '張瓘，同州車渡村人，故太原監軍使承業之猶子也。',
      '“犹子”与主书“侄”相应；原字瓘保留。',old106,'corroborates')
event('zhang_chengye_executes_nephew','张承业处斩杀贩牛人的侄子，晋王施救不及',34,
      '承业治家甚严，有侄为盗，杀贩牛者，承业立斩之，王亟使救之，已不及。',
      [('张承业','将杀人侄子立即处斩者'),('李存勖','急遣人施救而未及的晋王')],
      place=None,note='被处斩的侄子未具名，不能误认作张瓘；被害贩牛者也未具名。')
claim('event','event_zztj_269_0916_zhang_chengye_executes_nephew','description',
      '《旧五代史》张瓘传也记承业处斩一侄，但作被害者为河西卖羊客。',34,
      '一侄為磁州副使，以其殺河西賣羊客，承業立捕斬之。',
      '主书“贩牛者”与旧书“卖羊客”不同；不确定是否底本或传闻差异，待纸本核。',old106,'conflicts')
event('zhang_guan_linzhou_prefect','晋王任张瓘为麟州刺史',34,
      '王以瓘为麟州刺史',
      [('李存勖','任张瓘为麟州刺史的晋王'),('张瓘','受任麟州刺史者')],place='麟州')
claim('event','event_zztj_269_0916_zhang_guan_linzhou_prefect','description',
      '《旧五代史》张瓘传记天祐十三年补麟州刺史。',34,
      '瓘天祐十三年補麟州刺史。',
      '晋仍用唐天祐年号，时间与本段916年对应；仅保留史载纪年。',old106,'corroborates')
event('zhang_chengye_warns_guan','张承业告诫张瓘改过守法',34,
      '承业谓瓘曰：“汝本车度一民，与刘开道为贼，惯为不法，今若不悛，死无日矣！”',
      [('张承业','训诫张瓘改过的河东监军'),('张瓘','受张承业训诫者')],place=None,
      note='主书“车度一民”字形待核；刘开道可能为刘知俊绰号，未把其作为此次在场参与者。')
claim('event','event_zztj_269_0916_zhang_chengye_warns_guan','description',
      '《旧五代史》张瓘传作“车渡村百姓刘开道下贼”，与主书地名用字不同。',34,
      '汝車渡村百姓劉開道下賊，慣作非為，今須改行',
      '旧书提供车渡村背景，主书车度一民疑字；并列保留待纸本核。',old106,'adds')

# p035: a marriage visit establishes interstate goodwill, but spouse is unnamed.
event('qian_chuanxiang_fujian_marriage','钱传珦赴闽迎娶，闽与吴越自此通好',35,
      '吴越牙内先锋都指挥使钱传珦逆妇于闽，自是闽与吴越通好。',
      [('钱传珦','赴闽迎娶的吴越牙内先锋都指挥使')],place='闽、吴越',
      note='“逆妇”照主书理解为迎娶；妇人未具名，不新建人物或臆定王室身份。')

# p036: monetary practice, no unrecorded mint locations or rates.
event('min_lead_coins_circulate','闽铸铅钱，与铜钱并行',36,
      '闽铸铅钱，与铜钱并行。',[],place='闽',
      note='仅记铅钱铸造与和铜钱并行；不推定币值、铸地或流通全域。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(34, 37):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷269贞明二年第34—36段连续处理；张承业家事、钱传珦闽婚与闽铅钱。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=916,
    primary_source_key=main,primary_source_keys=[main],paragraphs=[Q[n]['id'] for n in range(34,37)],
    next_paragraph=Q[37]['id'],coverage='卷269贞明二年第34—36段；张承业侄辈、吴越闽婚与闽铅钱。',
    supplements=supplements,reviewed_questions=[
      {'paragraph_id':Q[34]['id'],'note':'处斩的侄子匿名，不等于张瓘；被害者通鉴作贩牛人、旧五代史作河西卖羊客。车度/车渡异文并列。'},
      {'paragraph_id':Q[35]['id'],'note':'钱传珦所迎娶妇人未具名，不推定其姓名或政治身份。'},
      {'paragraph_id':Q[36]['id'],'note':'铅钱与铜钱并行未给币值和铸地，不添加现代货币解释。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
