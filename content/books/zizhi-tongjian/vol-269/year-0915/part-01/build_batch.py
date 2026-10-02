"""Curate consecutive Tongjian vol. 269, 915 paragraphs 1–4."""
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
main = 'tongjian-269-914-year-end'
old_xu = 'jiuwudaishi-008-xuzhou'
old_retire = 'jiuwudaishi-008-retirement'
old_wei = 'jiuwudaishi-008-wei-division'
new_wei = 'xinwudaishi-042-wei-division'
specs = [
    (main, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0914/part-03/sources/library' / main, 'cc69bae0', '司马光等'),
    (old_xu, P / 'sources/library' / old_xu, 'd374d4f5', '薛居正等'),
    (old_retire, P / 'sources/library' / old_retire, 'd374d4f5', '薛居正等'),
    (old_wei, P / 'sources/library' / old_wei, 'd374d4f5', '薛居正等'),
    (new_wei, P / 'sources/library' / new_wei, 'd374d4f5', '欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0915-p001-p004',
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
for n in range(1, 5):
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
    ck = f'claim_zztj_269_0915_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明元年条所见人物：{name}。', biography=None, status='draft')
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

# p001: an explicitly dated audience, followed by background and an undated execution.
event('shu_receives_captives', '王建在得贤门受蛮俘并大赦', 1,
      '春，正月，己亥，蜀主御得贤门受蛮俘，大赦。',
      [('王建','在得贤门受俘并颁大赦的蜀主')],
      when='915年正月己亥', place='得贤门',
      note='“蛮俘”是底本用语；本句未列俘虏姓名及人数。')
event('jinbao_three_killed', '王建以漏泄军谋处死金堡三王并毁金堡', 1,
      '于是，蜀主数以漏泄军谋，斩于成都市，毁金堡。',
      [('王建','下令处死金堡三王并毁金堡的蜀主'),
       ('刘昌嗣','前文列金堡三王之一'),('郝玄鉴','前文列金堡三王之一'),('杨师泰','前文列金堡三王之一')],
      when='贞明元年正月条追叙；处死确年未载', place='成都市、金堡', year=None,
      note='“初”引入旧事，“于是”承前事；未据编排强定处死在915年。三人内附、受爵和暗通南诏是背景，亦不强定年份。')
claim('event','event_zztj_269_0915_jinbao_three_killed','description',
      '《通鉴》称刘昌嗣、郝玄鉴、杨师泰号金堡三王，曾暗通南诏。',1,
      '初，黎、雅蛮酋刘昌嗣、郝玄鉴、杨师泰，虽内属于唐，受爵赏，号金堡三王，而潜通南诏，为之诇导。',
      '这是三人背景及被杀前因，不将内附、受爵、通南诏定在915年。')
# p002: the city fell, then the rebel and his kin died in the fire.
event('xu_prefecture_captured', '牛存节等攻下彭城', 2,
      '二月，牛存节等拔彭城，', [('牛存节','率梁军攻下彭城者')],
      when='915年二月', place='彭城',
      note='“等”不具名；旧五代史卷八明确并记刘鄩参战，单列补证。')
event('wang_yin_family_fire', '王殷举族自焚', 2,
      '王殷举族自焚。', [('王殷','彭城失守后举族自焚者')],
      when='915年二月', place='彭城',
      note='只按原文录自焚，不推定族内成员姓名或人数。')
claim('event','event_zztj_269_0915_xu_prefecture_captured','description',
      '《旧五代史》卷八并记刘鄩与牛存节攻下徐州。',2,
      '牛存節、劉鄩拔徐州', '旧书给出另一参战将领；彭城为徐州治所，地名层级不同。',old_xu,'adds')
claim('event','event_zztj_269_0915_wang_yin_family_fire','description',
      '《旧五代史》卷八记王殷举族自焚，另称其尸首被取而献。',2,
      '逆賊將殷舉族自燔而死，於火中得其屍，梟首以獻。',
      '“逆贼”为梁朝纪传措辞，不作本站判断；尸首细节仅作旧书补证。',old_xu,'adds')
# p003: separate dated resignation.
event('zhao_guangfeng_retires', '赵光逢以太子太保致仕', 3,
      '三月，丁卯，以右仆射兼门下侍郎、同平章事赵光逢为太子太保，致仕。',
      [('赵光逢','原任右仆射、同平章事，改太子太保并致仕者')],
      when='915年三月丁卯',
      note='“致仕”为退职，不推定同日离京。')
claim('event','event_zztj_269_0915_zhao_guangfeng_retires','description',
      '《旧五代史》卷八同记赵光逢丁卯以太子太保致仕。',3,
      '丁卯，以右僕射兼門下侍郎、同平章事、監修國史、判度支趙光逢為太子太保致仕。',
      '旧书还列监修国史、判度支官衔；与主书日期相合。',old_retire,'corroborates')
# p004: death, retrospective military establishment, ensuing split, and coercive deployment.
event('yang_shihou_dies', '杨师厚卒', 4,
      '天雄节度使兼中书令鄴王杨师厚卒。', [('杨师厚','卒于魏博的天雄节度使、鄴王')],
      when='915年三月条；确日未载', place='魏博',
      note='旧五代史卷八作魏博节度使杨师厚薨并辍朝三日。')
claim('event','event_zztj_269_0915_yang_shihou_dies','description',
      '《旧五代史》卷八记杨师厚薨、梁廷辍视朝三日。',4,
      '魏博節度使楊師厚薨，輟視朝三日。',
      '辍朝三日仅见旧书该段，按梁廷丧礼记载补充。',old_retire,'adds')
event('yang_shihou_yinqiang', '杨师厚此前设置银枪效节都', 4,
      '师厚晚年矜功恃众，擅割财赋，选军中骁勇，置银枪效节都数千人，给赐优厚，欲以复故时牙兵之盛。',
      [('杨师厚','生前设置银枪效节都并厚给将士者')],
      when='杨师厚晚年；建置确年未载', place='魏博', year=None,
      note='“数千人”为通鉴记数，确年待考；新五代史卷四十二概记二千，数量异说并列。')
claim('event','event_zztj_269_0915_yang_shihou_yinqiang','description',
      '《新五代史》卷四十二称杨师厚复置牙兵二千。',4,
      '復置牙兵二千', '主书记银枪效节都“数千人”，新书记“二千”，不合并为精确规模。',new_wei,'conflicts')
event('wei_split_proposed', '赵岩、邵赞劝朱友贞分魏博六州为两镇', 4,
      '租庸使赵岩、判官邵赞言于帝曰：',
      [('赵岩','倡议分魏博为两镇的租庸使'),('邵赞','共同进言的租庸判官'),('朱友贞','接受分镇建议的梁帝')],
      when='915年杨师厚卒后；确日未载', place='梁朝廷',
      note='引文后半明示分六州为两镇，赵岩与邵赞两人同议。')
claim('event','event_zztj_269_0915_wei_split_proposed','description',
      '《旧五代史》卷八作赵岩、邵讚共同献议分割相、魏两镇。',4,
      '租庸使趙岩、租庸判官邵讚獻議於帝',
      '邵讚繁体字形规范到邵赞；旧书对发议者与主书相合。',old_wei,'corroborates')
claim('event','event_zztj_269_0915_wei_split_proposed','description',
      '《新五代史》卷四十二也记赵岩、邵贊议分相魏。',4,
      '巖與租庸判官邵贊議曰', '两书措辞相近，不视作完全独立确证。',new_wei,'corroborates')
event('wei_bowei_split', '朱友贞分魏博为天雄、昭德两镇并命贺德伦与张筠赴镇', 4,
      '帝以为然，以平卢节度使贺德伦为天雄节度使；置昭德军于相州，割澶、卫二州隶焉，以宣徽使张筠为昭德节度使，仍分魏州将士府库之半于相州。',
      [('朱友贞','同意分镇并下令的梁帝'),('贺德伦','新任天雄节度使'),('张筠','新任昭德节度使')],
      when='915年杨师厚卒后；确日未载', place='魏州、相州、澶州、卫州',
      note='相、澶、卫三州划入昭德，魏博贝仍属天雄；部分兵士、府库迁分，不推定立即顺利执行。')
claim('event','event_zztj_269_0915_wei_bowei_split','description',
      '《旧五代史》卷八诏令载相州建昭德军，澶、卫隶属，以张筠为节度使。',4,
      '其相州宜建節度為昭德軍。以澶、衛兩州為屬郡，以張筠為相州節度使。',
      '诏文支持行政划分；未据后文魏军叛变回推本时结果。',old_wei,'corroborates')
claim('event','event_zztj_269_0915_wei_bowei_split','description',
      '《新五代史》卷四十二亦记昭德军分相、澶、卫三州。',4,
      '乃分相、澶、衛為昭德軍。', '与旧书及主书大体相合。',new_wei,'corroborates')
event('liu_xun_crosses_yellow_river', '梁遣刘鄩率军自白马渡河威慑魏州', 4,
      '遣开封尹刘鄩将兵六万自白马济河，以讨镇、定为名，实张形势以胁之。',
      [('朱友贞','命刘鄩领军的梁帝'),('刘鄩','率军自白马渡河并威慑魏州的将领')],
      when='915年分镇决定后；确日未载', place='白马、魏州',
      note='“以讨镇、定为名”是公开名义，主书记实际威慑魏州；六万为主书记数。')
claim('event','event_zztj_269_0915_liu_xun_crosses_yellow_river','description',
      '《旧五代史》卷八称刘鄩率兵六万屯河朔。',4,
      '遣劉鄩率兵六萬屯河朔。', '支持兵力与方向，不提供主书白马渡河的路线细节。',old_wei,'corroborates')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 5):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明元年第1—4段连续处理；金堡三王处死与银枪效节都为追叙，确年不强定；魏博分镇按决策与部署拆录。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=915,
    primary_source_key=main, primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(1, 5)], next_paragraph=Q[5]['id'],
    coverage='卷269贞明元年正月至三月第1—4段；受俘大赦、金堡三王旧事、彭城之役、赵光逢致仕及杨师厚死后的魏博分镇。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[1]['id'],'note':'金堡三王处死由“初”领起，确年不明；与915年受俘大赦分录。'},
      {'paragraph_id':Q[4]['id'],'note':'银枪效节都主书记数千人，新五代史卷42记二千；两者不能合为精确数。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
