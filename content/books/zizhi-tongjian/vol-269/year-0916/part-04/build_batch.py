"""Curate consecutive Tongjian vol. 269, 916 paragraphs 18–22."""
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
spring = 'tongjian-269-916-spring'
main = 'tongjian-269-916-autumn'
new63 = 'xinwudaishi-063-shu-invasion'
old28a = 'jiuwudaishi-028-xingzhou'
old28b = 'jiuwudaishi-028-cangzhou'
old52 = 'jiuwudaishi-052-li-siben'
new25 = 'xinwudaishi-025-fu-cunshen'
new14 = 'xinwudaishi-014-cao'
old35 = 'jiuwudaishi-035-li-siyuan-916'
specs = [(spring, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-02/sources/library' / spring, 'b1a2623e', '司马光等')]
for key, author in [(main,'司马光等'),(new63,'欧阳修'),(old28a,'薛居正等'),(old28b,'薛居正等'),(old52,'薛居正等'),(new25,'欧阳修'),(new14,'欧阳修'),(old35,'薛居正等')]:
    path_key = 'jiuwudaishi-035-li-siyuan' if key == old35 else key
    specs.append((key, P / 'sources/library' / path_key, '5e858107', author))
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0916-p018-p022',
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
for n in range(18, 23):
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
    for key in ([spring] if n == 18 else [main]):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source in (spring, main):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明二年（916）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0916_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (spring, main):
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'蜀主':'王建','晋王':'李存勖','李存审':'符存审','王宗播':'许存','契丹王阿保机':'阿保机','曹夫人':'曹氏（李存勖母）'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases=['曹夫人','曹氏'] if name == '曹氏（李存勖母）' else [],
                   era='五代十国', birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明二年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '原文称谓与既有姓名合并；原文摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0916_' + code
    row = dict(key=key, title=title, start_year=916, end_year=916,
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

# p018: the two armies and their commands are distinct; troop counts are reported numbers.
event('shu_northeast_campaign_against_qi','前蜀东北路十万军由凤州伐岐',18,
      '蜀主以王宗绾为东北面都招讨，集王宗翰、嘉王宗寿为第一、第二招讨，将兵十万出凤州',
      [('王建','下令伐岐的前蜀君主'),('王宗绾','东北面都招讨'),('王宗翰','第一招讨'),('王宗寿','第二招讨')],
      when='916年丙午；未换算公历日',place='凤州',note='十万为主书所载兵数；本段只记出兵，不提前写战果。')
event('shu_northwest_campaign_against_qi','前蜀西北路十二万军由秦州伐岐',18,
      '以王宗播为西北面都招讨，武信军节度使刘知俊、天雄节度使王宗俦、匡国军使唐文裔为第一、第二、第三招讨，将兵十二万出秦州，以伐岐。',
      [('王宗播','西北面都招讨'),('刘知俊','第一招讨、武信军节度使'),('王宗俦','第二招讨、天雄节度使'),('唐文裔','第三招讨、匡国军使')],
      when='916年丙午；未换算公历日',place='秦州',note='十二万为主书所载西北路兵数；不与东北路十万合并。')
claim('event','event_zztj_269_0916_shu_northeast_campaign_against_qi','description',
      '《新五代史》记王宗绾等率十二万出大散关攻岐，与《通鉴》两路分载及兵数不同。',18,
      '通正元年，遣王宗綰等率兵十二萬出大散關攻岐，取隴州。',
      '新书记通正元年、总兵十二万和后续取陇州；不将其数字硬配通鉴东北路，也不提前记战果。',new63,'conflicts')

# p019: separate advance, withdrawal, surrender, and appointments.
event('zhang_yun_abandons_xiangzhou','晋王攻邢州时，张筠弃相州而走',19,
      '晋王自将攻邢州，昭德节度使张筠弃相州走。',
      [('李存勖','自率军攻邢州的晋王'),('张筠','弃相州的昭德节度使')],place='邢州、相州')
event('li_siyuan_xiangzhou_prefect','晋以李嗣源为相州刺史',19,
      '晋人复以相州隶天雄军，以李嗣源为刺史。',
      [('李嗣源','被任为相州刺史')],place='相州')
claim('event','event_zztj_269_0916_li_siyuan_xiangzhou_prefect','description',
      '《旧五代史》庄宗纪称袁建丰任相州刺史，与《通鉴》不同。',19,
      '以袁建豐為相州刺史，依舊隸魏州。',
      '旧书卷二十八作袁建丰；不据该异说另建相州同一任命事件。',old28a,'conflicts')
claim('event','event_zztj_269_0916_li_siyuan_xiangzhou_prefect','description',
      '《旧五代史》明宗纪亦称李嗣源任相州刺史。',19,
      '四月，相州張筠遁走，乃以帝為相州刺史。',
      '旧书内部卷三十五与卷二十八记载不同；月份亦异，先并列保留。',old35,'corroborates')
event('yan_bao_surrenders_xingzhou','阎宝受张温劝谕，举邢州降晋',19,
      '晋王遣人告阎宝以相州已拔，又遣张温帅援兵至城下谕之，宝举城降。',
      [('李存勖','派人告知并遣张温劝谕的晋王'),('张温','率援兵至城下劝谕者'),('阎宝','举城降晋的邢州守将')],place='邢州',
      note='相州已拔是劝降时告知的信息；阎宝投降发生于本段，不倒填前段拒守时。')
event('yan_bao_jin_appointment','晋王任阎宝为东南面招讨使并遥领天平',19,
      '晋王以宝为东南面招讨使，领天平节度使、同平章事',
      [('李存勖','授阎宝官职的晋王'),('阎宝','受东南面招讨使等职')])
claim('event','event_zztj_269_0916_yan_bao_jin_appointment','description',
      '《旧五代史》卷二十八作阎宝为西南面招讨使。',19,
      '以閻寶為西南面招討使，遙領天平軍節度使。',
      '方位与通鉴东南面不同，保留异文待纸本核对。',old28a,'conflicts')
event('fu_cunshen_anguo_xingzhou','晋王以符存审为安国节度使镇邢州',19,
      '以李存审为安国节度使，镇邢州。',
      [('李存审','以李存审名受安国节度使、镇邢州')],place='邢州')
claim('event','event_zztj_269_0916_fu_cunshen_anguo_xingzhou','description',
      '《新五代史》符存审传同记阎宝降后授安国节度使。',19,
      '閻寶以邢州降，乃以存審為安國軍節度使。',
      '新书原字“存審”；此人本站规范名符存审，李存审为其别名。',new25,'corroborates')

# p020: campaign, capture, envoy and resistance; claimed army size remains quoted.
event('aba oji_takes_yuzhou'.replace(' ',''),'阿保机率诸部攻陷晋蔚州',20,
      '契丹王阿保机帅诸部兵三十万，号百万，自麟、胜攻晋蔚州，陷之',
      [('阿保机','率契丹诸部攻蔚州的契丹王')],place='麟州、胜州、蔚州',
      note='三十万、号百万为主书所载及所号，不当作核定兵力。')
event('li_siben_captured_yuzhou','蔚州失陷，李嗣本被契丹俘虏',20,
      '陷之，虏振武节度使李嗣本。',
      [('李嗣本','蔚州失陷后被俘的振武节度使')],place='蔚州')
claim('event','event_zztj_269_0916_li_siben_captured_yuzhou','description',
      '《旧五代史》李嗣本传记其据城数日、城陷后举族入契丹。',20,
      '其眾三十萬攻振武，嗣本嬰城拒戰者累日。契丹為火車地道，晝夜急攻，城中兵少，禦備罄竭，城陷，嗣本舉族入契丹。',
      '旧书传记补足守城过程；“举族”不推为精确人数。',old52,'adds')
event('li_cunzhang_kills_khitan_envoy','李存璋斩契丹索货使者',20,
      '遣使以木书求货于大同防御使李存璋，存璋斩其使。',
      [('李存璋','斩杀索货使者的大同防御使')],place='大同')
event('li_cunzhang_defends_yunzhou','契丹进攻云州，李存璋尽力抵御',20,
      '契丹进攻云州，存璋悉力拒之。',
      [('李存璋','抵御契丹进攻云州者')],place='云州',
      note='此段只记抵御，不提前记契丹撤退。')

# p021: one dated journey, retrospective visit frequency is descriptive only.
event('li_cunxu_returns_jinyang_autumn','晋王李存勖九月还晋阳省曹夫人',21,
      '九月，晋王还晋阳。王性仁孝，故虽经营河北，而数还晋阳省曹夫人，岁再三焉。',
      [('李存勖','回晋阳省曹夫人的晋王'),('曹夫人','受晋王探视的曹夫人')],
      when='916年九月；确日未载',place='晋阳',
      note='“岁再三”是习惯性回顾，不另造该年三次定日探视。')
claim('person',people['曹氏（李存勖母）'],'description',
      '《新五代史》称曹氏为李存勖生母，受封晋国夫人。',21,
      '曹氏封晉國夫人，後生子，是謂莊宗',
      '庄宗即李存勖；据独立人名与亲属记载确认曹夫人的身份，原文繁体保留。',new14,'adds')
rel='relationship_person_曹氏（李存勖母）_person_li_cunxu_母亲'
B['person_relationships'].append(dict(key=rel,person_a_key=people['曹氏（李存勖母）'],
    person_b_key=people['李存勖'],relation_type='母亲',description='曹氏是李存勖之母；母子关系见本段。',status='draft'))
reused.add(rel)
claim('person_relationship',rel,'description','曹氏是李存勖的母亲。',21,
      '曹氏封晉國夫人，後生子，是謂莊宗',
      '《新五代史》明示曹氏生庄宗；庄宗为李存勖。',new14,'adds')

# p022: Cangzhou withdrawal, surrender, reassignment, and personal staff appointment.
event('dai_siyuan_abandons_cangzhou','戴思远弃沧州奔东都',22,
      '晋人以兵逼沧州，顺化节度使戴思远弃城奔东都。',
      [('戴思远','弃沧州奔东都的顺化节度使')],place='沧州、东都')
event('mao_zhang_surrenders_cangzhou','毛璋据沧州降晋，李嗣源奉命镇抚',22,
      '沧州将毛璋据城降晋，晋王命李嗣源将兵镇抚之，嗣源遣璋诣晋阳。',
      [('毛璋','据沧州降晋并被遣赴晋阳的守将'),('李存勖','命李嗣源镇抚沧州的晋王'),('李嗣源','率兵镇抚沧州并遣毛璋赴晋阳者')],place='沧州、晋阳')
claim('event','event_zztj_269_0916_mao_zhang_surrenders_cangzhou','description',
      '《旧五代史》称毛璋为“旧将”，李嗣源招抚后毛璋降。',22,
      '舊將毛璋入據其城。李嗣源帥師招撫，璋以城降。',
      '主书写毛璋据城降后李嗣源镇抚，旧书叙序不同；不推断具体降约时间。',old28b,'conflicts')
event('fu_cunshen_henghai_cangzhou','晋王徙符存审镇沧州为横海节度使',22,
      '晋王徙李存审为横海节度使，镇沧州',
      [('李存审','以李存审名受横海节度使、镇沧州')],place='沧州')
claim('event','event_zztj_269_0916_fu_cunshen_henghai_cangzhou','description',
      '《新五代史》符存审传同记毛璋降后徙存审横海。',22,
      '毛璋以滄州降，徙存審橫海',
      '新书原字“存審”；本站复用符存审。',new25,'corroborates')
event('li_siyuan_anguo_xingzhou','晋王徙李嗣源为安国节度使',22,
      '以嗣源为安国节度使。',
      [('李嗣源','受安国节度使')],place='邢州',
      note='前句沧州任命后接李嗣源任安国；旧书作邢州节度。')
event('an_chonghui_appointed_staff','李嗣源任安重诲为中门使',22,
      '嗣源以安重诲为中门使，委以心腹，重诲亦为嗣源尽力。重诲，应州胡人也。',
      [('李嗣源','任安重诲为中门使并委以心腹'),('安重诲','受中门使任命的应州胡人')],
      place=None,
      note='应州为安重诲籍称，不当作任命发生地点；主书未记任命地点。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(18, 23):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明二年第18—22段连续处理；两路伐岐、相邢降晋、契丹攻蔚、晋阳省母、沧州降晋；繁简同人合并，异文并列。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=916,
    primary_source_key=main,primary_source_keys=[spring,main],
    paragraphs=[Q[n]['id'] for n in range(18,23)],next_paragraph=Q[23]['id'],
    coverage='卷269贞明二年第18—22段；前蜀两路伐岐、晋取相邢、契丹攻蔚云、晋王还晋阳、沧州降晋。',
    supplements=supplements,reviewed_questions=[
      {'paragraph_id':Q[18]['id'],'note':'新五代史卷六十三称王宗绾等十二万出大散关，通鉴分记东北十万及西北十二万；暂不等同。王宗播系已有人物许存的赐名，复用其主体。'},
      {'paragraph_id':Q[19]['id'],'note':'旧五代史卷二十八作袁建丰任相州刺史、西南面招讨使；卷三十五又作李嗣源任相州刺史；与通鉴异文并存。'},
      {'paragraph_id':Q[20]['id'],'note':'三十万、号百万仅为史书所载兵数及宣传称数，不作为核实统计。阿保机/耶律阿保机重复实体已按修订合并。'},
      {'paragraph_id':Q[21]['id'],'note':'曹夫人由新五代史卷十四明确指向李存勖生母曹氏；“岁再三”不拆为多个日期事件。'},
      {'paragraph_id':Q[22]['id'],'note':'毛璋降城与李嗣源镇抚的先后在通鉴、旧五代史略异；只按主书建时序。应州是安重诲籍称。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
