"""Curate Tongjian 269, year 914, consecutive paragraphs 5-10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 17))
main = 'tongjian-269-914-spring'
old_kang = 'jiuwudaishi-023-kang-huaiying'
old_kang_office = 'jiuwudaishi-008-kang-office'
old_han = 'jiuwudaishi-008-han-zhu'
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0914-p005-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main, P.parent / 'part-01/sources/library' / main, '98ce861b', '司马光等'),
    (old_kang, P / 'sources/library' / old_kang, 'b3715083', '薛居正等'),
    (old_kang_office, P / 'sources/library' / old_kang_office, 'b3715083', '薛居正等'),
    (old_han, P / 'sources/library' / old_han, 'b3715083', '薛居正等'),
]
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
primary_texts = {key:(source_dirs[key]/'source.txt').read_text() for key in (main,)}
for n in range(5,11):
    row=Q[n]
    assert row['text']==(ROOT/'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line']-1]
    assert any(row['text'] in text for text in primary_texts.values()),n

registry = {}
existing_relation_keys = set()
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    archived = json.loads(path.read_text())
    existing_relation_keys.update(row['key'] for row in archived['person_relationships'])
    for row in archived['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (path, row['name'])
        registry[row['name']] = row
aliases = {'吴越王镠':'钱镠','楚王殷':'马殷','蜀主':'王建',
           '王景仁':'王茂章','张宗奭':'张全义','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','元膺':'王宗懿','硃友谦':'朱友谦','王镠':'钱镠','吴越王镠':'钱镠','张宗奭':'张全义','李存审':'符存审','韩珪':'韩勍','丁昭浦':'丁昭溥','徐知浩':'李昪','徐知诰':'李昪','王德明':'张文礼','段凝':'段明远','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
aliases.update({'元膺':'王宗懿','蜀主':'王建','帝':'朱友贞','硃友谦':'朱友谦',
                '鄴王':'杨师厚','晋王':'李存勖','守光':'刘守光',
                '行珪':'高行珪','行周':'高行周','嗣源':'李嗣源',
                '存矩':'李存矩','传瓘':'钱传瓘','传璙':'钱传璙',
                '吴越王镠':'钱镠','从珂':'李从珂','魏氏':'魏氏（李从珂母）'})
aliases.update({'刘光浚':'刘光濬','光浚':'刘光濬','李存审':'符存审',
                '王德明':'张文礼','赵王':'王镕','传瓘':'钱传瓘',
                '师厚':'杨师厚','守奇':'刘守奇','万进':'张万进'})
aliases.update({'元膺':'王宗懿','太子':'王宗懿','蜀主':'王建',
                '道袭':'唐道袭','宗翰':'王宗翰','宗侃':'王宗侃',
                '宗贺':'王宗贺','宗黯':'王宗黯','赵王镕':'王镕',
                '晋王':'李存勖','高季兴':'高季昌'})
aliases.update({'吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘',
                '传璙':'钱传璙','传瑛':'钱传瑛','蜀主':'王建',
                '宗衍':'王宗衍','宗辂':'王宗辂','宗杰':'王宗杰',
                '宗侃':'王宗侃','晋王':'李存勖','守光':'刘守光',
                '朱温':'朱温','王景仁':'王茂章'})
aliases.update({'硃瑾':'朱瑾','硃景浮':'朱景浮','王景仁':'王茂章',
                '景仁':'王茂章','守光':'刘守光','晋王':'李存勖',
                '越王镕':'王镕','赵王镕':'王镕','仁恭':'刘仁恭'})
aliases.update({'镕':'王镕','晋王':'李存勖','守光':'刘守光',
                '仁恭':'刘仁恭','小喜':'李小喜','蜀主':'王建',
                '太子':'王宗衍','宗寿':'王宗寿','季昌':'高季昌',
                '成先':'王成先','张武':'张武'})
aliases.update({'康怀英':'康怀贞','怀英':'康怀贞','怀贞':'康怀贞',
                '帝':'朱友贞','蜀主':'王建','马鄴':'马邺',
                '崇景':'刘崇景','威':'刘威','洙':'韩洙'})
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main,) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main,):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·乾化四年（914）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_269_0914_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main,):
        book = json.loads((source_dirs[source] / 'paragraph.json').read_text())['book']
        supplements.append(dict(claim_key=ck, source_book=book, primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=supplement_relation))
    return ck

def person(name, n, role, quote):
    name = aliases.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269乾化四年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=914):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0914_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '914年本段条；确日未载', dynasty='五代十国',
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
          '段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_269_0914_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key,
                                       role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key

def relation(a, b, kind, n, quote, note):
    ak, bk = people[a], people[b]
    key = f'relationship_{ak}_{bk}_{kind}'
    if key in existing_relation_keys:
        reused.add(key)
    B['person_relationships'].append(dict(key=key, person_a_key=ak, person_b_key=bk,
                                          relation_type=kind, description=f'{a}是{b}的{kind}。', status='draft'))
    claim('person_relationship', key, 'description', f'{a}是{b}的{kind}。', n, quote, note)

event('kang_huaiying_yongping', '后梁徙康怀贞为永平节度使、镇长安', 5,
      '帝以岐人数为寇，二月，甲戌，徙感化节度使康怀英为永平节度使，镇长安。',
      [('朱友贞','因岐军屡犯而调整西部军镇的梁帝'),('康怀贞','以康怀英之名由感化节度使改镇永平、长安')],
      when='914年二月甲戌',place='长安',
      note='原文此时作康怀英，但本段明示其即康怀贞，复用旧主体UUID；“数为寇”未给具体战次数。')
claim('event','event_zztj_269_0914_kang_huaiying_yongping','description',
      '《旧五代史》卷八亦记二月甲戌任康怀英永平军节度使。',5,
      '二月甲戌，以感化軍節度使、華商等州觀察使、檢校太傅、同平章事、太原郡開國公康懷英為大安尹，充永平軍節度使，大安金棣等州觀察處置使。',
      '旧书补大安尹等衔；主书“镇长安”与旧书官号不强行互换。',old_kang_office,'adds')
event('kang_huaizhen_renamed', '康怀贞避后梁帝名改名康怀英', 5,
      '怀英即怀贞也，避帝名改焉。',
      [('康怀贞','原名康怀贞，避梁帝名而改康怀英')],
      when='朱友贞即位后、914年二月甲戌前后；改名确日未载',place='后梁',year=None,
      note='主书明言同一人，改名原因是避帝名；不将名字变化直接定在本段甲戌。')
claim('person',people['康怀贞'],'aliases','康怀贞又名康怀英；避后梁末帝名改称怀英。',5,
      '怀英即怀贞也，避帝名改焉。',
      '两种名字归入康怀贞稳定主体；原书不同年代的署名保持原字。')
claim('person',people['康怀贞'],'aliases','《旧五代史》卷二十三亦明确记康怀英本名怀贞。',5,
      '康懷英，兗州人也。本名懷貞，避末帝御名，故改之。',
      '旧书传记与通鉴本段一致；避讳关系在两书明示，非仅凭字形相似推断。',old_kang,'corroborates')
event('shu_moves_zhenjiang', '前蜀迁镇江军治于夔州', 6,
      '夏，四月，丙子，蜀主徙镇江军治夔州。',
      [('王建','迁镇江军治于夔州的前蜀皇帝')],
      when='914年四月丙子',place='夔州',
      note='迁的是镇江军军治，不推为全境迁移。')
event('yu_jing_demoted', '于兢因挟私迁补军校罢相并贬莱州司马', 7,
      '丁丑，司空兼门下侍郎、同平章事于兢坐挟私迁补军校，罢为工部侍郎，再贬莱州司马。',
      [('于兢','因挟私迁补军校受罢相及再贬的后梁官员')],
      when='914年四月丁丑及其后',place='后梁、莱州',
      note='“坐挟私迁补”是主书所记处罚理由；“再贬”先后顺序保留，未给第二次贬日。')
event('liu_chongjing_defects_chu', '袁州刺史刘崇景叛吴附楚', 7,
      '吴袁州刺史刘崇景叛，附于楚。崇景，威之子也。',
      [('刘崇景','由吴袁州刺史叛附楚的刘威之子'),('刘威','刘崇景之父')],
      when='914年四月；确日未载',place='袁州',
      note='“附于楚”不等于楚已占稳袁州；下一段战果需另录。')
relation('刘威','刘崇景','父亲',7,'崇景，威之子也。',
         '原文明示刘崇景为刘威之子；关系方向刘威是刘崇景的父亲。')
event('chu_relieves_yuanzhou', '楚将许贞率万人援刘崇景，吴遣柴再用、米志诚讨之', 7,
      '楚将许贞将万人援之，吴都指挥使柴再用、米志诚帅诸将讨之。',
      [('许贞','率楚军万人援刘崇景'),('柴再用','率吴军讨刘崇景与楚援军的都指挥使'),('米志诚','同柴再用率吴军讨叛军')],
      when='914年四月；确日未载',place='袁州',
      note='“万人”是楚许贞援军口径；本段只记出兵，万胜冈战果见第10段。')
event('chu_huangzhou_raid', '王环趁南风夜袭黄州，擒吴刺史马邺并掠归', 8,
      '楚岳州刺史许德勋将水军巡边。夜分，南风暴起，都指挥使王环乘风趣黄州，以绳梯登城，径趣州署，执吴刺史马鄴，大掠而还。',
      [('许德勋','率楚水军巡边的岳州刺史'),('王环','乘风夜袭黄州并擒马邺的楚都指挥使'),('马邺','以底本“马鄴”字形被俘的吴黄州刺史')],
      when='914年四月后、五月前；确日未载',place='黄州',
      note='“马鄴”规范写马邺，原文仍保留；风势是行动条件，不推为战果唯一原因。')
event('chu_fleet_passes_ezhou', '许德勋备鄂州邀击，王环主张径过，鄂军未逼', 8,
      '德勋曰：“鄂州将邀我，宜备之。”环曰：“我军入黄州，鄂人不知，奄过其城，彼自救不暇，安敢邀我！”乃展旗鸣鼓而行，鄂人不敢逼。',
      [('许德勋','建议防备鄂州军邀击的楚将'),('王环','主张展旗鸣鼓通过鄂州的楚将')],
      when='914年四月后、五月前；确日未载',place='鄂州',
      note='两人战术判断是引语；结果只记鄂军未逼，并非楚军攻克鄂州。')
event('han_xun_dies_son_interim', '朔方节度使韩逊卒，军中推其子韩洙为留后', 9,
      '五月，朔方节度使兼中书令颍川王韩逊卒，军中推其子洙为留后。',
      [('韩逊','五月去世的朔方节度使'),('韩洙','被军中推为留后的韩逊之子')],
      when='914年五月；确日未载',place='朔方',
      note='军中推举为留后，与随后朝廷正式节度使任命是两阶段。')
relation('韩逊','韩洙','父亲',9,'军中推其子洙为留后。',
         '原文明示韩洙为韩逊之子；关系方向韩逊是韩洙父亲。')
event('han_zhu_jiedushi', '梁朝诏授韩洙朔方节度使', 9,
      '癸丑，诏以洙为节度使。',
      [('韩洙','由留后获朝廷诏授节度使')],
      when='914年五月癸丑',place='朔方')
claim('event','event_zztj_269_0914_han_zhu_jiedushi','description',
      '《旧五代史》卷八记五月癸丑韩洙起复授朔方军节度使。',9,
      '五月癸丑，朔方軍留後、檢校司徒韓洙起復，授朔方軍節度使，檢校太保。',
      '旧书补起复及检校衔；主书只记诏授节度使。',old_han,'adds')
event('wanshenggang_wu_victory', '柴再用等万胜冈大破刘崇景、许贞，二人弃袁州逃离', 10,
      '吴柴再用等与刘崇景、许贞战于万胜冈，大破之，崇景、贞弃袁州遁去。',
      [('柴再用','率吴军于万胜冈击败叛楚联军'),('刘崇景','战败后弃袁州逃走'),('许贞','战败后随刘崇景弃袁州逃走')],
      when='914年五月；确日未载',place='万胜冈、袁州',
      note='“大破”未给具体杀伤；“等”未具名者不另建。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(5,11):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷269乾化四年二月至五月第5—10段连续处理；康怀贞＝康怀英以通鉴及旧五代史明文合一主体，其他人地繁简保持来源原字。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=914,
    primary_source_key=main,primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(5,11)],next_paragraph='zztj-v269-y0914-p011',
    coverage='卷269乾化四年二月至五月第5—10段，康怀贞改名、蜀迁镇江军、袁州及黄州战事、韩洙承朔方。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[5]['id'],'note':'通鉴明言“康怀英即怀贞也”，旧五代史卷23明言“本名怀贞，避末帝御名”，证明同一主体；早期双实体线上合并另留修正审计。'},
      {'paragraph_id':Q[8]['id'],'note':'吴刺史底本作“马鄴”，站内规范作马邺；原文保留。'},
      {'paragraph_id':Q[9]['id'],'note':'韩逊五月卒、军中推韩洙为留后；癸丑诏授节度使分为两事。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
