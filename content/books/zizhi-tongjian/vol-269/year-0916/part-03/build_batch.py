"""Curate consecutive Tongjian vol. 269, 916 paragraphs 11–17."""
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
main = 'tongjian-269-916-spring'
old08 = 'jiuwudaishi-008-li-ba-revolt'
old64 = 'jiuwudaishi-064-du-yanqiu'
new46 = 'xinwudaishi-046-du-yanqiu'
new44 = 'xinwudaishi-044-zhang-wen'
old68 = 'jiuwudaishi-068-dou-mengzheng'
specs = [
    (main, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-02/sources/library' / main, 'b1a2623e', '司马光等'),
    (old08, P / 'sources/library' / old08, '3c8ce057', '薛居正等'),
    (old64, P / 'sources/library' / old64, '3c8ce057', '薛居正等'),
    (new46, P / 'sources/library' / new46, '3c8ce057', '欧阳修'),
    (new44, P / 'sources/library' / new44, '3c8ce057', '欧阳修'),
    (old68, P / 'sources/library' / old68, '3c8ce057', '薛居正等'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0916-p011-p017',
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
for n in range(11, 18):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line'] - 1]
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

def choose_source(quote):
    for key in (main,):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明二年（916）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0916_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'全昱':'朱全昱','友谅':'朱友谅','硃瑾':'朱瑾','李存审':'符存审','晋王':'李存勖','吴王':'杨隆演','蜀主':'王建','帝':'朱友贞'}.get(name,name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
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
          '追叙确年不明。' if year is None else '按主书段落次序；干支未换算公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_269_0916_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p011: the command to garrison Yangliu, rebellion, suppression, and appointment.
event('li_ba_sent_to_yangliu','后梁命李霸率捉生军千人戍杨刘',11,
      '帝遣捉生都指挥使李霸帅所部千人戍杨刘，癸卯，出宋门',
      [('朱友贞','遣李霸率部戍杨刘的后梁皇帝'),('李霸','受命率千人赴杨刘的捉生都指挥使')],
      when='916年夏四月癸卯；未换算公历日',place='汴州宋门、杨刘',
      note='戍杨刘为朝廷派遣，李霸当晚回城作乱另记。')
event('li_ba_mutiny','李霸当夜率部由水门入汴州纵火攻建国门',11,
      '李霸帅所部千人戍杨刘，癸卯，出宋门，其夕，复自水门入，大噪。纵火剽掠，攻建国门，帝登楼拒战。',
      [('李霸','率部返城发动兵变者'),('朱友贞','登楼拒战的后梁皇帝')],
      when='916年夏四月癸卯夜；未换算公历日',place='汴州水门、建国门',
      note='李霸是承上句主语；“攻建国门”未说已攻克。')
claim('event','event_zztj_269_0916_li_ba_mutiny','description',
      '《旧五代史》卷八也记李霸四月癸卯夜自水门返城作乱。',11,
      '癸卯夜，捉生都將李霸作亂，龍驤都將杜晏球討平之。',
      '旧书本纪与主书时序相合；本句将发乱和讨平合叙。',old08,'corroborates')
event('du_yanqiu_repels_mutineers','杜晏球率龙骧骑兵出击，使李霸乱军溃散',11,
      '龙骧四军都指挥使杜晏球以五百骑屯球场，贼以油沃幕，长木揭之，欲焚楼，势甚危。晏球于门隙窥之，见贼无甲胄，乃出骑击之，决力死战，俄而贼溃走。',
      [('杜晏球','率五百骑出击乱军的龙骧都指挥使')],
      when='916年夏四月癸卯夜；未换算公历日',place='汴州球场、建国门',
      note='李霸为上文明确的乱首；五百骑、油幕依主书。')
claim('event','event_zztj_269_0916_du_yanqiu_repels_mutineers','description',
      '《旧五代史》杜晏球传也记五百骑及油幕攻门。',11,
      '晏球聞亂，先得龍驤馬五百屯於鞠場，俄而亂兵以竿豎麻布沃油焚建國縷',
      '旧书作鞠场、建国縷，疑为同事异字；保留原字，纸本待核。',old64,'corroborates')
claim('event','event_zztj_269_0916_du_yanqiu_repels_mutineers','description',
      '《新五代史》杜晏球传亦记其不待命出五百骑击乱兵。',11,
      '晏球聞亂，不俟命，率龍驤五百騎擊之，賊勢稍却。',
      '新书新增“不俟命”细节，不据此断言其违令。',new46,'adds')
event('li_ba_mutineers_punished','杜晏球讨平李霸乱军，营中遭族诛',11,
      '既而晏球讨乱者，阖营皆族之，以功除单州刺史。',
      [('杜晏球','讨平乱者后受单州刺史任命者')],
      when='916年夏四月兵变平定后；确日未载',place='汴州',
      note='“阖营皆族之”是主书原叙，不据此推算实际处决人数；单州为主书官名。')
claim('event','event_zztj_269_0916_li_ba_mutineers_punished','description',
      '《新五代史》杜晏球传正文作澶州刺史，注记古本作单州。',11,
      '以功拜澶〈古本作單。〉州刺史。',
      '官名主书、旧书作单州，新书正文作澶州而自注古本单州；异文保留待纸本核。',new46,'conflicts')
# p012: travel itinerary and explicit kinship.
event('qian_liu_sends_pi_guangye_tribute','钱镠遣皮光业经七道赴后梁入贡',12,
      '五月，吴越王镠遣浙西安抚判官皮光业自建、汀、虔、郴、潭、岳、荆南道入贡。',
      [('钱镠','遣使入贡的吴越王'),('皮光业','从建汀虔郴潭岳荆南道赴梁的浙西安抚判官')],
      when='916年五月；确日未载',place='建、汀、虔、郴、潭、岳、荆南道',
      note='地名照史载顺序列出；不据此推算现代坐标或路线长度。')
parent=person('皮日休',12,'皮光业之父','光业，日休之子也。')
child=people['皮光业']
rel='relationship_person_皮日休_person_皮光业_父亲'
B['person_relationships'].append(dict(key=rel,person_a_key=parent,person_b_key=child,
    relation_type='父亲',description='皮日休是皮光业的父亲。',status='draft'))
claim('person_relationship',rel,'description','皮日休是皮光业的父亲。',12,
      '光业，日休之子也。','“日休”承上皮光业之姓；父子关系由主书明示。')
# p013: the siege is ongoing; Zhang Wen's surrender is not Yan Bao's capitulation.
event('jin_besieges_xingzhou','晋军攻邢州，阎宝拒守',13,
      '六月，晋人攻邢州，保义节度使阎宝拒守。',
      [('阎宝','拒守邢州的保义节度使')],
      when='916年六月；确日未载',place='邢州',
      note='本段仅写阎宝拒守，不提前记邢州后来降晋。')
event('zhang_wen_defects_to_jin','后梁援邢将张温率五百人降晋',13,
      '帝遣捉生都指挥使张温将兵五百救之，温以其众降晋。',
      [('朱友贞','遣张温率兵救邢州的后梁皇帝'),('张温','率所部降晋的捉生都指挥使')],
      when='916年六月邢州受攻期间；确日未载',place='赴邢州途中',
      note='五百为主书所载援兵数；不据本段推断张温投降原因。')
claim('event','event_zztj_269_0916_zhang_wen_defects_to_jin','description',
      '《新五代史》阎宝传记张温在内黄遇晋军后降，并由晋军使其招阎宝。',13,
      '溫至內黃，遇晉軍，乃降晉。晉遣溫將所降梁軍至城下招寶',
      '内黄与招降是新书补充；该段年题牵涉不同纪年，不能据此改定通鉴六月。',new44,'adds')
# p014: travel fact only.
event('jin_king_arrives_weizhou','晋王李存勖七月初一到魏州',14,
      '秋，七月，甲寅朔，晋王至魏州。',
      [('李存勖','抵达魏州的晋王')],
      when='916年秋七月甲寅朔；未换算公历日',place='魏州',
      note='只据本段记到达，不推定此行为另一次攻城。')
# p015: appointment and remonstrance are separated.
event('qian_liu_named_generalissimo','后梁加钱镠诸道兵马元帅',15,
      '上嘉吴越王镠贡献之勤，壬戌，加镠诸道兵马元帅。',
      [('朱友贞','因入贡而加钱镠官号的后梁皇帝'),('钱镠','获加诸道兵马元帅的吴越王')],
      when='916年七月壬戌；未换算公历日',place='后梁朝廷',
      note='“贡献之勤”为主书说明的加号理由，不将入贡次数自行量化。')
event('dou_mengzheng_protests_title','窦梦征反对过授钱镠名器，因而贬蓬莱尉',15,
      '朝议多言镠之入贡，利于市易，不宜过以名器假之。翰林学士窦梦征执麻以泣，坐贬蓬莱尉。',
      [('窦梦征','执麻以泣并因此被贬蓬莱尉的翰林学士')],
      when='916年七月钱镠加号时；确日未载',place='后梁朝廷、蓬莱',
      note='“朝议多言”不具名，不给窦梦征之外人物创建反对参与边。')
claim('event','event_zztj_269_0916_dou_mengzheng_protests_title','description',
      '《旧五代史》窦梦征传也记其反对钱镠元帅之命而被外贬。',15,
      '夢徵以鏐無功於中原，兵柄不宜虛授，其言切直。梁末帝以觸時忌，左授外任。',
      '旧书不在此句给具体所贬县名；主书蓬莱尉保留。',old68,'corroborates')
claim('person',people['窦梦征'],'description','《旧五代史》称窦梦征同州人，与《资治通鉴》棣州人不同。',15,
      '竇夢徵，同州人。','籍贯异文并列，未强改规范人物生地。',old68,'conflicts')
# p016: mutiny and suppression in Runzhou.
event('zhou_jiao_mutiny_runzhou','润州牙将周郊作乱，入府杀秦师权等',16,
      '甲子，吴润州牙将周郊作乱，入府，杀大将秦师权等',
      [('周郊','作乱入府的润州牙将'),('秦师权','被杀的吴国大将')],
      when='916年七月甲子；未换算公历日',place='润州',
      note='“等”表示另有遇害者，原文未具名，不据此新增人物。')
event('chen_you_suppresses_zhou_jiao','陈祐等讨斩润州叛将周郊',16,
      '甲子，吴润州牙将周郊作乱，入府，杀大将秦师权等，大将陈祐等讨斩之。',
      [('陈祐','率众讨斩乱者的吴国大将'),('周郊','被讨斩的叛将')],
      when='916年七月甲子兵变后；确日未载',place='润州',
      note='“之”承上周郊；并未给其他参与者姓名。')
# p017: court appointment.
event('zhao_guangfeng_chancellor','后梁起用致仕赵光逢为司空、门下侍郎、同平章事',17,
      '八月，丁酉，以太子太保致仕赵光逢为司空兼门下侍郎、同平章事。',
      [('赵光逢','被起用并授司空等官职的原致仕太子太保')],
      when='916年八月丁酉；未换算公历日',place='后梁朝廷',
      note='官职按原文列出；不另推其具体施政。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11, 18):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明二年第11—17段连续处理；李霸兵变分录，皮光业父子明示，张温降晋未提前写阎宝投降，官名与籍贯异文保留。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=916,
    primary_source_key=main, primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(11, 18)], next_paragraph=Q[18]['id'],
    coverage='卷269贞明二年第11—17段；李霸兵变、吴越入贡、邢州战事与梁吴两地任官及兵变。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[11]['id'],'note':'杜晏球平李霸乱后所授州名，通鉴与旧五代史作单州，新五代史正文作澶州、并注古本单州；异文待纸本核。'},
      {'paragraph_id':Q[12]['id'],'note':'皮日休为皮光业之父系主书明示；入贡经过地名按原文，不添现代坐标。新唐书卷五十九载皮日休唐咸通间任官，已将人物时代校为晚唐并补独立出处；见content/revisions/2026-10-02-pi-rishiu-era/publication.json。'},
      {'paragraph_id':Q[13]['id'],'note':'本段张温降晋时阎宝仍拒守；新五代史所记后来招阎宝为补充，不提前录为六月本段结果。'},
      {'paragraph_id':Q[15]['id'],'note':'窦梦征籍贯通鉴作棣州，旧五代史卷六十八作同州；只作冲突声明，不改人物主字段。'},
      {'paragraph_id':Q[16]['id'],'note':'周郊作乱及陈祐讨斩分录；其他被害者、参与者未具名。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
