"""Curate consecutive Tongjian vol. 269, 915 paragraphs 19–21."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 34))
main = 'tongjian-269-915-august'
old_08 = 'jiuwudaishi-008-august'
old_28 = 'jiuwudaishi-028-august'
old_22 = 'jiuwudaishi-022-wang-tan'
old_08_lx = 'jiuwudaishi-008-liu-xun-memorial'
specs = [
    (main, P / 'sources/library' / main, '5f494c20', '司马光等'),
    (old_08, P / 'sources/library' / old_08, '5f494c20', '薛居正等'),
    (old_28, P / 'sources/library' / old_28, '5f494c20', '薛居正等'),
    (old_22, P / 'sources/library' / old_22, '5f494c20', '薛居正等'),
    (old_08_lx, P / 'sources/library' / old_08_lx, '5f494c20', '薛居正等'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0915-p019-p021',
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
for n in range(19, 22):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in (source_dirs[main] / 'source.txt').read_text(), n
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

def claim(table, key, field, value, n, quote, note, source=main, relation='adds'):
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明元年（915）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0915_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'李存审': '符存审', '李绍荣': '元行钦', '李绍奇': '夏鲁奇'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明元年条所见人物：{name}。', biography=None, status='draft')
    if name == '杨延直':
        row['aliases'] = ['楊延直']
    if name == '夏鲁奇':
        row['aliases'] = ['李绍奇']
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '姓名按既有主体规范；原文和摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=915):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0915_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '915年本段条；确日未载', dynasty='五代十国',
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
          '段内追叙，确年待考。' if year is None else '按主书段落次序；未把干支换算成公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_269_0915_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key




# p019: Liang's attacks and recovery of Chanzhou.
event('yin_hao_attacks_xi_ci', '尹皓攻隰州、慈州，均未攻克', 19,
      '绛州刺史尹皓攻晋之隰州，八月，又攻慈州，皆不克。',
      [('尹皓','率军攻晋隰州与慈州而未克的绛州刺史')],
      when='915年，慈州之攻在八月；隰州之攻确日未载', place='隰州、慈州',
      note='隰州之攻在八月前的主书叙事中；不把两次进攻记为同一天。')
event('liang_recaptures_chanzhou', '王檀、贺瑰夺回澶州，俘李岩送往东都', 19,
      '王檀与昭义留后贺瑰攻澶州，拔之，执李岩，送东都。',
      [('王檀','与贺瑰攻取澶州的梁将'),('贺瑰','参与攻取澶州的昭义留后'),('李岩','被梁军俘获并送往东都的晋方澶州刺史')],
      when='915年八月条', place='澶州、东都',
      note='与本年第15段晋军夜取澶州是先后两次易手；旧书王檀传另称擒王开关，主书此段未载。')
claim('event','event_zztj_269_0915_liang_recaptures_chanzhou','description',
      '《旧五代史》卷八记八月贺瑰收复澶州。',19,
      '八月，賀瑰收復澶州。',
      '旧书只点贺瑰；不据此排除主书所记王檀。',old_08,'corroborates')
claim('event','event_zztj_269_0915_liang_recaptures_chanzhou','description',
      '《旧五代史》卷二十二王檀传也记王檀攻澶州、擒李岩，另载王开关。',19,
      '檀攻澶州魏縣，下之，擒賊將李岩、王開關以獻。',
      '“澶州魏县”地名表述与主书“澶州”并列保留；不据传记段落给王开关补主书参与边。',old_22,'adds')
event('yang_yanzhi_chanzhou_governor', '朱友贞任杨延直为澶州刺史，率万人助刘鄩', 19,
      '帝以杨师厚故将杨延直为澶州刺史，使将兵万人助刘鄩，且招诱魏人。',
      [('朱友贞','任命杨延直的后梁皇帝'),('杨延直','杨师厚旧将，获任澶州刺史并领兵助刘鄩'),('刘鄩','被杨延直奉命援助的梁将')],
      when='915年澶州收复后；确日未载', place='澶州、魏州',
      note='杨师厚是其旧主，不因此建立亲属关系；“万人”为主书记数。')
claim('person',people['杨延直'],'aliases','杨延直与旧书繁体“楊延直”为同一人。',19,
      '時帝遣偏將楊延直領軍萬餘人屯澶州以應鄩',
      '旧书卷八在次年三月叙事中回顾杨延直屯澶州；仅用其姓名字形校对身份，不以此断任命发生于三月。',old_08_lx,'corroborates')
# p020: the Beizhou siege.
event('li_cunshen_besieges_beizhou', '符存审率五千兵围贝州并征八县民夫开堑', 20,
      '晋王遣李存审将兵五千击贝州。张源德有卒三千，每夕分出剽掠，州民苦之，请堑其城以安耕耘。存审乃发八县丁夫堑而围之。',
      [('李存勖','命符存审攻贝州的晋王'),('符存审','以李存审之名率军围贝州的晋将'),('张源德','据守贝州、麾下士卒夜间出掠的刺史')],
      when='915年八月条；确日未载', place='贝州及周边八县',
      note='主书五千为晋军兵数、三千为张源德兵数；征八县丁夫不等于八县各出固定人数。')
claim('event','event_zztj_269_0915_li_cunshen_besieges_beizhou','description',
      '《旧五代史》卷二十八记李存审领五千兵攻贝州，因堑围城。',20,
      '帝遣李存審率兵五千攻貝州，因塹而圍之。',
      '旧书与主书的兵数、围法相合；旧书本段随后十月投毒记载不提前录为八月事。',old_28,'corroborates')
# p021: shortages, imperial correspondence, the officers' debate, and a failed attack.
event('liu_xun_supply_shortage', '刘鄩在莘县久驻缺粮，晋军攻断甬道', 21,
      '刘鄩在莘久，馈运不给，晋人数抵其寨下挑战，鄩不出。晋人乃攻绝其甬道，以千馀斧斩寨木，梁人惊忧而出，因俘获而还。',
      [('刘鄩','在莘县久驻并遭遇军粮短缺的梁将')],
      when='915年莘县对峙期间；确日未载', place='莘县、梁军营寨',
      note='主书未具名指挥攻断甬道的晋将；“千余斧”是器具数，不推为确切士兵数。')
event('liang_emperor_rebukes_liu_xun', '朱友贞责刘鄩迟不决战，刘鄩以缺粮和敌强答复', 21,
      '帝以诏书让鄩老师费粮，失亡多，不速战。鄩奏称：“臣比欲以奇兵捣其腹心，还取镇、定，期以旬时再清河朔。无何天未厌乱，淫雨积旬，粮竭士病。又欲据临清断其馈饷，而周杨五奄至，驰突如神。臣今退保莘县，享士训兵以俟进取。观其兵数甚多，便习骑射，诚为勍敌，未易轻也。苟有隙可乘，臣岂敢偷安养寇！”',
      [('朱友贞','下诏责刘鄩迟不作战的后梁皇帝'),('刘鄩','上奏解释雨阻、缺粮和晋军强盛的梁将')],
      when='915年莘县对峙期间；确日未载', place='莘县、后梁朝廷',
      note='“周杨五”是主书电子本原字，疑似讹文待核；刘鄩奏辞作为其陈述，不等同独立证实每项军情。')
claim('event','event_zztj_269_0915_liang_emperor_rebukes_liu_xun','description',
      '《旧五代史》卷八在次年三月条以“先是”追述刘鄩驻莘时受责，记其称需每人十斛粮。',21,
      '先是，鄩駐於莘，帝以河朔危急，師老於外，餉饋不充，遣使賜鄩詔，微有責讓。鄩奏以寇勢方盛，未可輕動。帝又問鄩決勝之策，鄩奏曰：「但人給糧十斛，盡則破敵。」',
      '旧书卷八把这段作为三月决战前的追述，不把三月误赋予此处问答；十斛为刘鄩请求。',old_08_lx,'corroborates')
event('liu_xun_refuses_rash_battle', '刘鄩反对仓促决战，借河水告诫诸将', 21,
      '鄩集诸将问曰：“主上深居禁中，不知军旅，徒与少年新进辈谋之。夫兵在临机制变，不可预度。今敌尚强，与战必不利，奈何？”诸将皆曰：胜负须一决，旷日何待！”鄩默然，不悦。退谓所亲曰：“主暗臣谀，将骄卒惰，吾未知死所矣！”他日，复集诸将于军门，人置河水一器于前，令饮之，众莫之测。鄩谕之曰：“一器犹难，滔滔之河，可胜尽乎！”众失色。',
      [('刘鄩','认为敌军尚强、劝诸将避免仓促决战的梁将')],
      when='915年梁帝催战后；确日未载', place='刘鄩军营',
      note='底本“诸将皆曰”后的引号缺配对，逐字保留；诸将未具名，不新建人物。')
event('liu_xun_attack_zhen_ding_camps', '刘鄩攻镇定军营遭符存审、李建及反击，大败退寨', 21,
      '后数日，鄩将万馀人薄镇、定营，镇、定人惊扰。晋李存审以骑兵二千横击之，李建及以银枪千人助之，鄩大败，奔还。晋人逐之，及寨下，俘斩千计。',
      [('刘鄩','率万余人攻镇定营后败退的梁将'),('符存审','以李存审之名率二千骑横击刘鄩的晋将'),('李建及','率银枪兵千人助击的晋将')],
      when='915年梁帝催战数日后；确日未载', place='镇定军营、刘鄩军寨',
      note='“俘斩千计”为俘虏和斩杀合述，不拆成各一千人；旧五代史卷八另叙镇定军惊扰与俘斩甚众，但处于次年三月回顾中，未作同一战的独立确证。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(19, 22):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明元年第19—21段连续处理；梁晋澶州易手、贝州围城和刘鄩莘县军情分录；旧书次年条追述不强行定为次年。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=915,
    primary_source_key=main, primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(19, 22)], next_paragraph=Q[22]['id'],
    coverage='卷269贞明元年八月第19—21段；梁收澶州、晋围贝州、刘鄩莘县军情。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[19]['id'],'note':'旧五代史王檀传作“澶州魏县”并增王开关，地名和额外俘将待核；未据此扩写主书。'},
      {'paragraph_id':Q[20]['id'],'note':'旧五代史卷二十八同记五千兵围贝州；其后十月投毒另属下文，不提前记入本段。'},
      {'paragraph_id':Q[21]['id'],'note':'旧五代史卷八在次年三月以“先是”追述莘县驻军受责，不改主书编年；通鉴电子本“周杨五”及引号疑有讹脱，原字保留待纸本核。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
