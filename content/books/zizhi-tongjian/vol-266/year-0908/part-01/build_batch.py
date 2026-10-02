"""Curate Tongjian 266, year 908, consecutive paragraphs 1–10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 41))
primary = 'tongjian-266-907-yearend'
succession = 'tongjian-266-908-succession'
old_keyong = 'jiuwudaishi-026-keyong-death'
new_keyong = 'xinwudaishi-004-keyong-death'
old_tang = 'jiutangshu-020b-aidi-death'
old_jiyin = 'jiuwudaishi-004-jiyin-death'
old_shi = 'jiuwudaishi-055-shi-jingrong'
new_shu = 'xinwudaishi-063-shu-wucheng'
B = {'format_version': 1, 'batch_key': 'zztj-v266-y0908-p001-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parents[1] / 'year-0907/part-06/sources/library' / primary, '3fdb705c', '司马光等'),
    (succession, P / 'sources/library' / succession, 'e7278afb', '司马光等'),
    (old_keyong, P / 'sources/library' / old_keyong, 'e7278afb', '薛居正等'),
    (new_keyong, P / 'sources/library' / new_keyong, 'e7278afb', '欧阳修等'),
    (old_tang, P / 'sources/library' / old_tang, 'e7278afb', '刘昫等'),
    (old_jiyin, P / 'sources/library' / old_jiyin, 'e7278afb', '薛居正等'),
    (old_shi, P / 'sources/library' / old_shi, 'e7278afb', '薛居正等'),
    (new_shu, P / 'sources/library' / new_shu, 'e7278afb', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, succession)}
for n in range(1, 11):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/266.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '蜀主':'王建', '吴越王镠':'钱镠', '晋王克用':'李克用', '晋王存勖':'李存勖', '济阴王':'唐昭宣帝', '唐哀皇帝':'唐昭宣帝', '存勗':'李存勖', '克寧':'李克宁'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/later-liang-907-923/content-batch.json').read_text())['events']}
legacy_relations = {}
for archive in ('content/late-tang-zhu-wen-early/content-batch.json',
                'content/year-0907/content-batch.json',
                'content/later-liang-907-923/content-batch.json',
                'content/books/zizhi-tongjian/vol-263/year-0902/part-02/content-batch.json'):
    for row in json.loads((ROOT / archive).read_text())['person_relationships']:
        if row['key'] in legacy_relations:
            assert legacy_relations[row['key']] == row
        legacy_relations[row['key']] = row

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_266_0908_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷266·开平二年（908）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical,
                   aliases=[], era='五代十国', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷266开平二年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=908, time_quote=None, reuse_key=None):
    assert quote in Q[n]['text'], (n, quote)
    key = reuse_key or ('event_zztj_266_0908_' + code)
    if reuse_key:
        assert not actors, 'Published event edges are preserved by stable key'
        if key not in {row['key'] for row in B['events']}:
            row = dict(legacy_events[reuse_key], status='draft')
            B['events'].append(row)
        reused.add(key)
        desc = title + '。'
    else:
        desc = title + '。'
        B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                                time_original=when or '908年本段条；确日未载', dynasty='五代十国', description=desc,
                                phases=[], location_name=place, location_modern_name=None, location_lat=None,
                                location_lng=None, location_precision='unknown',
                                location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '908年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_266_0908_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def relation(key, n, quote, note):
    assert quote in Q[n]['text']
    row = legacy_relations[key]
    if key not in {item['key'] for item in B['person_relationships']}:
        B['person_relationships'].append(dict(row, status='draft'))
        reused.add(key)
    claim('person_relationship',key,'description',row['description'],n,quote,note)

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_266_0908_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 1-3: Shu court decisions at the start of Wucheng.
event('xingyi_monk','王建听张格劝谏，停止因僧人自残而大规模施饭',1,
      '春，正月，癸酉朔，蜀主登兴义楼。有僧抉一目以献，蜀主命饭僧万人以报之。翰林学士张格曰：“小人无故自残，赦其罪已幸矣，不宜复崇奖以败风俗。”蜀主乃止。',
      [('王建','先命施饭、后停止的蜀主'),('张格','劝止过度奖赏自残的翰林学士')],
      when='908年正月癸酉朔',place='兴义楼',
      note='僧人未具名；蜀主“乃止”指停止所拟施饭，不写成已实施万人施饭。')
event('weizhuang_pm','前蜀任韦庄为门下侍郎、同平章事',2,
      '丁丑，蜀以韦庄为门下侍郎、同平章事。',
      [('韦庄','受任门下侍郎、同平章事')],when='908年正月丁丑',
      note='承接907年韦庄判中书门下事，但此处为新授官。')
event('shu_wucheng_era','王建祀南郊，次日大赦改元武成',3,
      '辛巳，蜀主祀南郊；壬午，大赦，改元武成。',
      [('王建','祀南郊并颁赦改元的蜀主')],when='908年正月辛巳祀南郊、壬午赦改元',
      note='祀南郊与改元相隔一日，不合并为同日。')
extra(new_shu,'event','event_zztj_266_0908_shu_wucheng_era','description',
      '《新五代史》卷六十三亦记前蜀武成元年正月祀南郊、大赦改元。',
      '武成元年正月，祀天南郊，大赦，改元',3,'corroborates',
      '新史未细分辛巳与壬午，主书日次分别保留。')

# 4: Li Keyong's death, designated succession, actual accession, and city command.
event('keyong_designates_heir','李克用病重，嘱李克宁等辅立李存勖',4,
      '晋王命其弟内外蕃汉都知兵马使、振武节度使克宁、监军张承业、大将李存璋、吴珙、掌书记卢质立其子晋州刺史存勖为嗣',
      [('李克用','临终指定继承人'),('李存勖','被指定为嗣子'),('李克宁','受托辅立李存勖'),('张承业','受托辅立李存勖'),('李存璋','受托辅立李存勖'),('吴珙','受托辅立李存勖'),('卢质','受托辅立李存勖')],
      when='908年正月辛卯前；确日未载',place='晋阳',
      note='临终指定继承与辛卯死亡、后续袭位分录；“其弟”“其子”明示身份。')
relation('relationship_keyong_cunxu',4,'立其子晋州刺史存勖为嗣','李克用为李存勖父亲，复用已有方向。')
relation('relationship_person_li_keyong_person_李克宁_兄长',4,
         '晋王命其弟内外蕃汉都知兵马使、振武节度使克宁','“其弟”明示李克用为李克宁兄长。')
event('keyong_death','晋王李克用病逝',4,
      '辛卯，晋王谓存勖曰：“嗣昭厄于重围，吾不及见矣。俟葬毕，汝与德威辈速竭力救之！”又谓克宁等曰：“以亚子累汝！”亚子，存勖小名也。言终而卒。',
      when='908年正月辛卯',place='晋阳',
      note='“亚子”为李存勖小名；李克用临终嘱救李嗣昭，不能写为他本人随后援救。')
extra(new_keyong,'event','event_zztj_266_0908_keyong_death','description',
      '《新五代史》卷四记李克用正月辛卯卒、年五十三。',
      '五年正月辛卯，克用卒，年五十三。',4,'corroborates',
      '“五年”沿用天祐纪年；不把“年五十三”推算为无争议出生年份。')
extra(old_keyong,'event','event_zztj_266_0908_keyong_death','description',
      '《旧五代史》卷二十六亦记李克用辛卯卒于晋阳。',
      '辛卯，崩於晉陽，年五十三。',4,'corroborates',
      '旧书本段作“正月戊子朔”，与主书“癸酉朔”有历日不合；仅辛卯死亡干支与地点相互印证，朔日待校。')
event('cunxu_succeeds_jin','李存勖袭河东节度使、晋王',4,
      '张承业入谓存勖曰：“大孝在不坠基业，多哭何为！”因扶存勖出，袭位为河东节度使、晋王。李克宁首帅诸将拜贺',
      [('李存勖','袭位为河东节度使、晋王'),('张承业','扶李存勖出受诸将拜贺'),('李克宁','率诸将拜贺')],
      when='908年正月辛卯后；确日未载',place='晋阳',
      note='李存勖先以位让李克宁，后在张承业劝说下袭位；不能把“让位”写作实际禅让。')
extra(new_keyong,'event','event_zztj_266_0908_cunxu_succeeds_jin','description',
      '《新五代史》卷四简记李克用卒后子李存勖立。',
      '子存勗立',4,'corroborates',
      '“存勗”是底本字形，与站内李存勖复用同一主体；具体袭位过程据主书。')
event('cunzhan_jin_city','李存璋任河东军城使并整肃侵扰市肆者',4,
      '以李存璋为河东军城使、马步都虞候。先王之时，多宠借胡人及军士，侵扰市肆，存璋既领职，执其尤暴横者戮之，旬月间城中肃然。',
      [('李存璋','受任河东军城使并整肃军纪')],
      when='908年李存勖袭位后；整肃历旬月',place='晋阳',
      note='“先王之时”是追叙旧弊；李存璋任后整肃有持续时间。')

# 5-7: Wu-Yue relief, Shu office removal, and Zhang Ge's appointment.
event('wuyue_ganlu_relief','钱镠遣兵攻甘露镇以援信州',5,
      '吴越王镠遣兵攻淮南甘露镇，以救信州。',
      [('钱镠','遣兵攻甘露镇援信州')],when='908年正月条；确日未载',place='甘露镇、信州',
      note='承接907年卷266第61段信州求援；没有记甘露镇攻城结果。')
event('wang_zongji_removed','前蜀罢王宗佶政事、任太师',6,
      '二月，甲辰，以宗佶为太师，罢政事。',
      [('王宗佶','被任太师并罢去政事'),('王建','作出任免的蜀主')],
      when='908年二月甲辰',
      note='本段前面专权与唐道袭不和是任免前情，不擅定发生于同日。')
claim('event','event_zztj_266_0908_wang_zongji_removed','description',
      '主书记王宗佶自恃功劳而专权，与唐道袭失和。',6,
      '蜀中书令王宗佶，于诸假子为最长，且恃其功，专权骄恣。唐道袭已为枢密使，宗佶犹以名呼之；道袭心衔之而事之逾谨。',
      '对品行的评语是史书叙述；不把所有前情定在二月甲辰。')
extra(new_shu,'event','event_zztj_266_0908_wang_zongji_removed','description',
      '《新五代史》卷六十三把王宗佶任太师系于武成元年正月，与《通鉴》二月甲辰不合。',
      '武成元年正月，祀天南郊，大赦，改元，以王宗佶為太師。',6,'conflicts',
      '两书月份并列保留；新史也记唐袭与王宗佶不和，但含后续被杀事件，不倒填此段。')
event('zhang_ge_pm','前蜀任张格为中书侍郎、同平章事',7,
      '蜀以户部侍郎张格为中书侍郎、同平章事。',
      [('张格','受任中书侍郎、同平章事')],when='908年二月甲辰后；确日未载',
      note='主书后句关于张格迎合排挤的评述不作为具体可日期化的任官事实。')

# 8-9: Succession unrest, plot, disclosure, and executions.
event('cunning_succession_pressure','李存颢劝李克宁争位，李克宁起初拒绝',8,
      '假子李存颢阴说克宁曰：“兄终弟及，自古有之。以叔拜侄，于理安乎！天与不取，后悔无及！”克宁曰：“吾家世以慈孝闻天下，先王之业苟有所归，吾复何求！汝勿妄言，我且斩汝！”',
      [('李存颢','劝李克宁夺取继承权'),('李克宁','起初拒绝李存颢劝说')],
      when='908年李存勖继位后、二月壬戍前；确日未载',place='晋阳',
      note='起初明确拒绝；后续受到妻孟氏等影响，与第9段形成过程，不写为此时已定策。')
event('cunning_pressure_and_kill','李克宁受近人催逼并擅杀都虞候李存质',8,
      '克宁妻孟氏，素刚悍，诸假子各遣其妻入说孟氏，孟氏以为然，且虑语泄及祸，数以迫克宁。克宁性怯，朝夕惑于众言，心不能无动；又与张承业、李存璋相失，数诮让之；又因事擅杀都虞候李存质；又求领大同节度使，以蔚、朔、应州为巡属。晋王皆听之。',
      [('李克宁','受催逼并擅杀李存质'),('李存质','被李克宁擅杀的都虞候')],
      when='908年李存勖继位后；确日未载',place='晋阳',
      note='句内多事无确日；妻孟氏催逼与擅杀李存质分述，不将其写为已完成政变。')
event('cunning_plot','李克宁、李存颢等谋害李存勖并归附梁',9,
      '李存颢等为克宁谋，因晋王过其第，杀承业、存璋，奉克宁为节度使，举河东九州附于梁，执晋王及太夫人曹氏送大梁。',
      [('李克宁','密谋接受河东军府'),('李存颢','为李克宁筹谋'),('李存勖','密谋中拟被扣送大梁的晋王'),('曹氏（李存勖母）','密谋中拟被扣送大梁的太夫人')],
      when='908年二月壬戍前；确日未载',place='晋阳',
      note='这是密谋方案，诸“杀”“附”“执送”未实际发生；原文底本作壬戍，日字待校。')
relkey='relationship_person_曹氏（李存勖母）_person_li_cunxu_母亲'
B['person_relationships'].append(dict(key=relkey,person_a_key=person('曹氏（李存勖母）',9,'李存勖之母','太夫人曹氏'),
                                      person_b_key=person('李存勖',9,'曹氏之子','晋王及太夫人曹氏'),
                                      relation_type='母亲',description='曹氏是李存勖之母；母子关系见本段。',status='draft'))
claim('person_relationship',relkey,'description','曹氏是李存勖之母。',9,
      '太夫人曹氏','“母子”见后文太夫人自述，曹氏与晋王李存勖在本段同指。')
event('cunning_plot_exposed','史敬镕向曹太夫人告发李克宁密谋',9,
      '克宁欲知府中阴事，召敬镕，密以谋告之。敬镕阴许之，入告太夫人，太夫人大骇，召张承业',
      [('史敬镕','听取密谋后向太夫人告发'),('李克宁','向史敬镕透露密谋'),('曹氏（李存勖母）','获知密谋并召张承业')],
      when='908年二月壬戍前；确日未载',place='晋阳',
      note='史敬镕佯许后告发；前句交代其与李克用旧属关系，不另定为908年任职。')
extra(old_shi,'event','event_zztj_266_0908_cunning_plot_exposed','description',
      '《旧五代史》卷五十五记史敬镕获知李克宁密谋后告发。',
      '克寧密引敬鎔，以邪謀諭之。既而敬鎔白，貞簡太后惶駭',9,'corroborates',
      '旧书为史敬镕列传，人物与行动可对应；关于其他人执行细节仍据主书。')
event('cunning_plot_suppressed','李存勖设伏拘捕并处死李克宁、李存颢',9,
      '壬戍，置酒会诸将于府舍，伏甲执克宁、存颢于座。晋王流涕数之曰：“儿郎勖以军府让叔父，叔父不取。今事已定，奈何复为此谋，忍以吾母子遗仇雠乎！”克宁曰：“此皆谗人交构，夫复何言！”是日，杀克宁及存颢。',
      [('李存勖','设伏拘捕李克宁、李存颢的晋王'),('李克宁','被拘捕处死'),('李存颢','被拘捕处死')],
      when='908年二月壬戍（底本文字；干支待校）',place='晋阳',
      note='底本“壬戍”疑为“壬戌”，逐字保留；此前密谋未实现，处死发生在本句。')
extra(old_shi,'event','event_zztj_266_0908_cunning_plot_suppressed','description',
      '《旧五代史》卷五十五也记李克宁等密谋败露后伏诛。',
      '克寧等伏誅',9,'corroborates',
      '仅印证败露及处死；旧书未在所引段落详述设伏日期和方式。')

# 10: The former Tang emperor's murder, with the historical titles kept on one person.
event('aidi_murdered','后梁鸩杀济阴王，追谥唐哀皇帝',10,
      '癸亥，鸩杀济阴王于曹州，追谥曰唐哀皇帝。',
      [('唐昭宣帝','退位后封济阴王、于曹州遭鸩杀')],
      when='908年二月癸亥',place='曹州',
      note='“济阴王”“唐哀皇帝”与已发布唐昭宣帝为同一人；主书此句没有点名具体执行者。')
extra(old_jiyin,'event','event_zztj_266_0908_aidi_murdered','description',
      '《旧五代史》卷四记后梁二月弑济阴王。',
      '是月弑濟陰王。',10,'corroborates',
      '只核对月份和遇害事实，旧书此句未载癸亥干支。')
extra(old_tang,'event','event_zztj_266_0908_aidi_murdered','description',
      '《旧唐书》卷二十下记唐哀帝天祐五年二月二十一日在曹州为朱全忠所害。',
      '天祐五年二月二十一日，帝為全忠所害，時年十七，仍諡曰哀皇帝',10,'adds',
      '旧唐书给月内日及朱全忠责任；是否与主书癸亥恰合待历日校核，不强行换算。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,11):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷266开平二年第1—10段连续处理；李克用死亡、李存勖继位、李克宁密谋与济阴王遇害分录，旧新史异文并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=266,year=908,
    primary_source_key=primary,primary_source_keys=[primary,succession],
    paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph=Q[11]['id'],
    coverage='卷266开平二年第1—10段连续处理；前蜀政事、晋王继位与内变、济阴王遇害。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
