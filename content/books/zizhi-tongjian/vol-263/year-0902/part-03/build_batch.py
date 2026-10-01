"""Curate Tongjian 263, year 902, consecutive paragraphs 17–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 60))
primary = 'tongjian-263-902-april'
old_five = 'jiuwudaishi-002-902-campaign'
new_tang = 'xintangshu-190-feng-hongduo'

B = {'format_version': 1, 'batch_key': 'zztj-v263-y0902-p017-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-02/sources/library' / primary, '352a55e', '司马光等'),
    (old_five, P.parent / 'part-01/sources/library' / old_five, '2a58915', '薛居正等'),
    (new_tang, P / 'sources/library' / new_tang, 'e75f760', '欧阳修、宋祁等'),
]
source_dirs = {sk: d for sk, d, _, _ in source_specs}
manifest = []
for sk, d, commit, author in source_specs:
    record = json.loads((d / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((d / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=sk, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=sk, file=os.path.relpath(d / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((d / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary,)}
for n in range(17, 25):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/263.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅', '李存审': '符存审', '李继昭':'符道昭', '刘夫人':'刘夫人（李克用妻）', '曹氏':'曹氏（李存勖母）', '李继诲':'周承诲', '李彦弼':'董彦弼', '吉谏':'王宗黯', '李继徽':'杨崇本'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_263_0902_03_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷263·天复二年（902）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical, aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷263天复二年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=902):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_263_0902_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '902年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '902年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_263_0902_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_263_0902_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 17: the Fengxiang defeat and an explicit alternate name.
event('kang_defeats_fu_mogu', '康怀贞于莫谷击败凤翔将李继昭',17,
      '汴将康怀贞击凤翔将李继昭于莫谷，大破之。',
      [('康怀贞','汴军进攻者'),('李继昭','凤翔军被败者')],
      when='902年四月后、五月前；确日未载',place='莫谷',
      note='李继昭本姓苻、名道昭见同段后句；与孙德昭获赐名李继昭者不同。旧五作康怀英、虢县，不直接合并。')
claim('person',people['符道昭'],'description',
      '本段凤翔将李继昭为蔡州人，本姓苻，名道昭；旧五代史作符道昭。',17,
      '继昭，蔡州人也，本姓苻，名道昭。',
      '既有人库符道昭对应同一将领；苻/符字形分别保留，勿并入孙德昭。')

# 18–19: Wenzhou succession and movements toward Fengxiang.
event('zhu_bao_dies', '温州刺史朱褒五月庚戌去世',18,
      '五月，庚戌，温州刺史硃褒卒，',
      [('朱褒','去世者')],when='902年五月庚戌',place='温州')
event('zhu_ao_claims_wenzhou', '朱敖于兄朱褒死后自称温州刺史',18,
      '兄敖自称刺史。',
      [('朱敖','自称刺史者'),('朱褒','其弟')],when='902年五月庚戌后',place='温州',
      note='自称与朝廷正式授任不同。')
rel='relationship_person_朱敖_person_朱褒_兄长'
B['person_relationships'].append(dict(key=rel,person_a_key=people['朱敖'],person_b_key=people['朱褒'],
    relation_type='兄长',description='《资治通鉴》记朱敖为朱褒之兄。',status='draft'))
claim('person_relationship',rel,'description','朱敖是朱褒的兄长。',18,
      '温州刺史硃褒卒，兄敖自称刺史。','原文以“兄敖”明示长幼；硃字按稳定人名规范作朱。')
event('fengxiang_residents_move_inside', '凤翔城外居民闻朱全忠将至而迁入城内',19,
      '凤翔人闻硃全忠且来，皆惧，癸丑，城外居民皆迁入城。',
      [('朱温','将至者')],when='902年五月癸丑',place='凤翔',
      note='“闻”是凤翔人的消息与反应，不据此认定朱全忠在癸丑已抵城下。')
event('zhu_reaches_east_wei_bridge', '朱全忠率军出河中至东渭桥因霖雨驻十日',19,
      '己未，全忠将精兵五万发河中，至东渭桥，遇霖雨，留旬日。',
      [('朱温','行军者')],when='902年五月己未后十日左右',place='河中、东渭桥',
      note='五万是主书所记兵数；十日为“旬日”约数，未换算确切离营日。')

# 20–23: ministerial mourning and appointments; do not normalize OCR noise.
event('wei_yifan_mourning', '韦贻范五月庚午遭母丧',20,
      '庚午，工部侍郎、同平章事韦贻范遭母丧，',
      [('韦贻范','居丧者')],when='902年五月庚午')
event('yao_ji_declines_nomination', '宦官荐姚洎为相，姚洎移疾未任',20,
      '宦官荐翰林学士姚洎为相。洎谋于韩偓，偓曰：“若图永久之利，则莫若未就为善；倘出上意，固无不可。且汴军旦夕合围，孤城难保，家族在东，可不虑乎！”洎乃移疾，上亦自不许。',
      [('姚洎','被荐而移疾者'),('韩偓','劝说者'),('李杰','未准任者')],
      when='902年五月庚午后',note='姚洎被荐并不等于实际入相；“移疾”与皇帝不许分别记录。')
event('qian_liu_yue_prince', '钱镠由彭城王进爵越王',21,
      '镇海、镇东节度使彭城王钱镠进爵越王。',
      [('钱镠','进爵者')],when='902年五月条；确日未载')
event('su_jian_chancellor', '苏检六月丙子任工部侍郎同平章事',22,
      '六月，丙子，以中书舍入苏检为工部侍郎、同平章事。',
      [('苏检','受任者')],when='902年六月丙子',
      note='底本“中书舍入”疑为电子转录讹字；不据此确定其前职，保留原字待校。')
event('recommendations_for_su_jian', '韦贻范荐苏检姚洎，李茂贞与宦官促用苏检',22,
      '时韦贻范在草土，荐检及姚洎于李茂贞。上既不用洎，茂贞及宦官恐上自用人，协力荐检，遂用之。',
      [('韦贻范','荐举者'),('苏检','最终受用者'),('姚洎','同被荐而未用者'),('李茂贞','协力荐苏检者')],
      when='902年六月丙子前后',note='恐皇帝自用人是主书对李茂贞与宦官动机的记述，不追加未具名宦官个人。')
event('zhu_camps_guoxian', '朱全忠六月丁丑军于虢县',23,
      '丁丑，硃全忠军于虢县。',
      [('朱温','驻军者')],when='902年六月丁丑',place='虢县')

# 24: naval preparations, deceptive route and battle.
event('tian_jun_builds_ships', '田頵图冯弘铎并募工造战舰',24,
      '宁国节度使田頵欲图之，募弘鐸工人造战舰，工人曰：“冯公远求坚木，故其船堪久用，今此无之。”頵曰：“第为之，吾止须一用耳。”',
      [('田頵','募工造舰者'),('冯弘铎','被谋者')],when='902年六月条前后；确日未载',
      note='田頵的“一用”是其言辞，不推出已建成舰数。')
event('feng_hongduo_preempts_tian', '冯晖颜建劝冯弘铎先攻田頵，冯弘铎南上',24,
      '弘鐸将冯晖、颜建说弘鐸先击頵，弘鐸从之，帅众南上，声言攻洪州，实袭宣州也。',
      [('冯晖','劝攻者'),('颜建','劝攻者'),('冯弘铎','率军者'),('田頵','受袭目标')],
      when='902年六月辛巳前',place='洪州、宣州',
      note='攻洪州为对外声言，真实目标按主书为宣州。')
event('yang_xingmi_fails_to_stop_feng', '杨行密遣人阻冯弘铎出兵未果',24,
      '杨行密使人止之，不从。',
      [('杨行密','遣使劝止者'),('冯弘铎','不从者')],when='902年六月辛巳前')
event('tian_defeats_feng_geshan', '田頵辛巳于葛山大破冯弘铎舟师',24,
      '辛巳，頵帅舟师逆击于葛山，大破之。',
      [('田頵','水战获胜者'),('冯弘铎','败军主将')],when='902年六月辛巳',place='葛山',
      note='主书作葛山，《新唐书》卷190作曷山；未核地理前不合并地名或赋坐标。')

extra(old_five,'event','event_zztj_263_0902_kang_defeats_fu_mogu','description',
      '《旧五代史》卷二记康怀英于虢县败符道昭，与主书康怀贞、莫谷存在人名和地名差异。',
      '四月，岐人遣符道昭領大軍屯於虢縣，康懷英帥驍騎敗之',17,'conflicts',
      '符道昭可据本段李继昭本姓苻名道昭对应；康怀贞/康怀英、莫谷/虢县分别保留。')
extra(new_tang,'event','event_zztj_263_0902_tian_jun_builds_ships','description',
      '《新唐书》卷一百九十亦记田頵募工造舰且称只求一用。',
      '時行密大將田頵在宣州，陰圖弘鐸，募工治艦',24,'corroborates',
      '同书后文作“我為舟於一用”，印证计划与意图，不增造船数量。')
extra(new_tang,'event','event_zztj_263_0902_tian_defeats_feng_geshan','description',
      '《新唐书》记田頵逆击于曷山、冯弘铎败；《通鉴》作葛山。',
      '頵逆擊於曷山，弘鐸大敗',24,'conflicts',
      '两书战地字形异，未据电子本裁定同一地名。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17,25):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷263天复二年第17—24段：莫谷败战及同名消歧、温州朱褒朱敖、凤翔迁民与东渭桥、姚洎未相、钱镠进爵、苏检任相、虢县驻军、冯弘铎田頵舟战。旧五康怀英/主书康怀贞及新唐曷山/主书葛山并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=263,year=902,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],
    coverage='卷263天复二年共59个非空段落中的第17—24段连续处理；本年尚未完成。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
