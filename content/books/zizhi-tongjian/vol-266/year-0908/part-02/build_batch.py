"""Curate Tongjian 266, year 908, consecutive paragraphs 11–24."""
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
primary = 'tongjian-266-908-succession'
prelude = 'tongjian-266-908-luzhou-prelude'
battle = 'tongjian-266-908-luzhou-battle'
after = 'tongjian-266-908-luzhou-aftermath'
old_battle = 'jiuwudaishi-027-luzhou-battle'
new_battle = 'xinwudaishi-022-luzhou-battle'
old_sizhao = 'jiuwudaishi-052-lisizhao'
old_dewei = 'jiuwudaishi-056-zhou-dewei'
new_shu = 'xinwudaishi-063-shu-wucheng'
B = {'format_version': 1, 'batch_key': 'zztj-v266-y0908-p011-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-01/sources/library' / primary, 'e7278afb', '司马光等'),
    (prelude, P / 'sources/library' / prelude, 'f6893bfc', '司马光等'),
    (battle, P / 'sources/library' / battle, 'f6893bfc', '司马光等'),
    (after, P / 'sources/library' / after, 'f6893bfc', '司马光等'),
    (old_battle, P / 'sources/library' / old_battle, 'f6893bfc', '薛居正等'),
    (new_battle, P / 'sources/library' / new_battle, 'f6893bfc', '欧阳修等'),
    (old_sizhao, P / 'sources/library' / old_sizhao, 'f6893bfc', '薛居正等'),
    (old_dewei, P / 'sources/library' / old_dewei, 'f6893bfc', '薛居正等'),
    (new_shu, P.parent / 'part-01/sources/library' / new_shu, 'e7278afb', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, prelude, battle, after)}
for n in range(11, 25):
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
    B['claims'].append(dict(key=f'claim_zztj_266_0908_02_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_266_0908_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 11-16: Shu takes Guizhou while the Liang siege of Luzhou deteriorates.
event('shu_guizhou','前蜀兵入归州并执刺史张瑭',11,
      '甲子，蜀兵入归州，执刺史张瑭。',
      [('张瑭','被前蜀军所执的归州刺史')],when='908年二月甲子',place='归州',
      note='只记进入归州与执张瑭，不据此推定后续归属或处置。')
event('han_jian_palace','后梁任韩建侍中兼建昌宫使',11,
      '辛未，以韩建为侍中，兼建昌宫使。',
      [('韩建','受任侍中、兼建昌宫使')],when='908年二月辛未',
      note='与本段甲子蜀兵入归州是相隔数日的另一政权事件。')
event('liang_zezhou_command','朱温赴泽州接应潞州围军并任刘知俊招讨使',12,
      '三月，壬申朔，帝发大梁；丁丑，次泽州。辛巳，刘知俊至。壬午，以知俊为潞州行营招讨使。',
      [('朱温','从大梁至泽州接应围军的后梁皇帝'),('刘知俊','受任潞州行营招讨使')],
      when='908年三月壬申朔启程、丁丑至泽州、壬午任刘知俊',place='泽州',
      note='行军到达、刘知俊到达与授职日分开；“帝疑晋王克用诈死”是其怀疑，不是死亡事实有疑。')
claim('event','event_zztj_266_0908_liang_zezhou_command','description',
      '李思安久攻潞州不下，梁军疲弊逃亡，朱温因此考虑撤军接应。',12,
      '李思安等攻潞州，久不下，士卒疲弊，多逃亡。晋兵犹屯余吾寨',
      '主书为梁军处境；不将所有逃亡人数外推为确数。')
event('zhang_wenwei_death','后梁宰相张文蔚去世',13,
      '癸巳，门下侍郎、同平章事张文蔚卒。',
      [('张文蔚','于后梁宰相任内去世')],when='908年三月癸巳',
      note='按前文三月条次归月，不自行换算公历日。')
event('lisi_an_dismissed','朱温削李思安官爵并勒归本贯',14,
      '甲午，削思安官爵，勒归本贯充役。',
      [('李思安','久攻潞州无功而被削官')],when='908年三月甲午',
      note='主书所述兵员损失是处分的背景；“士卒以万计”为史书概数。')
event('yang_minzhen_executed','后梁处死监押杨敏贞',14,
      '斩监押杨敏贞。',
      [('杨敏贞','被后梁处斩的监押')],when='908年三月甲午条',
      note='同段接于李思安处分，未另明载行刑日；保留条次。')
event('lisizhao_defends_luzhou','李嗣昭困守潞州，拒绝后梁劝降',15,
      '晋李嗣昭固守逾年，城中资用将竭，嗣昭登城宴诸将作乐。流矢中嗣昭足，嗣昭密拔之，座中皆不觉。帝数遣使赐嗣昭诏，谕降之。嗣昭焚诏书，斩使者。',
      [('李嗣昭','困守潞州并拒降')],
      when='908年三月条；围守已逾年',place='潞州',
      note='宴会中箭及焚书斩使为同段所述守城事，确日未载。')
extra(old_sizhao,'event','event_zztj_266_0908_lisizhao_defends_luzhou','description',
      '《旧五代史》卷五十二亦记李嗣昭中箭不显露、焚诏斩使。',
      '賊矢中足，嗣昭密拔之，坐客不之覺，酣飲如故，以安眾心。五年五月，莊宗敗汴軍，破夾城。',15,'corroborates',
      '所引传记同时概述五月解围；本段事件只确认围中守城，解围另据第21段。')
event('liang_luzhou_delay','朱温采纳诸将意见，暂留潞州围军',16,
      '诸将以为李克用死，余吾兵且退，上党孤城无援，请更留旬月以俟之。帝从之，命增运刍粮以馈其军。',
      [('朱温','决定暂缓撤出潞州围军')],
      when='908年三月至四月；确日未载',place='泽州、潞州',
      note='诸将认为晋军将退是判断，不是晋军已撤的既成事实。')
event('liu_zhijun_luzhou_action','刘知俊出击晋军后奉命休兵转驻晋州',16,
      '刘知俊将精兵万馀人击晋军，斩获甚众，表请自留攻上党，车驾宜还京师。帝以关中空虚，虑岐人侵同华，命知俊休兵长子旬日，退屯晋州，俟五月归镇。',
      [('刘知俊','出击晋军并请求留攻上党'),('朱温','命刘知俊转驻晋州')],
      when='908年三月至四月；俟五月归镇',place='上党、长子、晋州',
      note='“万馀人”“斩获甚众”为史书记述，不作精确数；五月归镇是预期安排而非本段已完成。')

# 17-20: Wang Zongji's death, Zhou Dewei's return, Jin relief preparations, and Huainan attacks.
event('wang_zongji_killed','王建命卫士扑杀王宗佶',17,
      '已亥，宗佶入见，辞色悖慢。蜀主谕之，宗佶不退，蜀主不堪其忿，命卫士扑杀之。',
      [('王建','命卫士扑杀王宗佶的蜀主'),('王宗佶','被扑杀的前蜀太师')],
      when='908年三月至四月间已亥；原文日字待校',place='蜀',
      note='底本作“已亥”，疑为“己亥”；原文照录。王宗佶密养死士及请求掌六军是前情。')
claim('event','event_zztj_266_0908_wang_zongji_killed','description',
      '王宗佶上表请求设置元帅府并独掌六军，王建因此生疑。',17,
      '臣请开元帅府，铸六军印，征戍征发，臣悉专行。',
      '这是王宗佶的请求，未被批准，不写成已设元帅府。')
event('wang_zongji_followers','王建贬郑骞、李钢并在途中赐死',17,
      '贬其党御史中丞郑骞为维州司户，卫尉少卿李钢为汶川尉，皆赐死于路。',
      [('王建','处分王宗佶党人的蜀主'),('郑骞','被贬后在途中赐死'),('李钢','被贬后在途中赐死')],
      when='908年王宗佶被杀后；确日未载',
      note='两人先受贬官再于路上赐死；不与王宗佶扑杀视为同一地点同一时刻。')
extra(new_shu,'event','event_zztj_266_0908_wang_zongji_killed','description',
      '《新五代史》卷六十三亦记王建令卫士扑杀王宗佶，并赐郑骞死。',
      '建叱衞士撲殺之，并賜騫死。',17,'corroborates',
      '新史本段只明载郑骞赐死，李钢处分仍据《通鉴》；月份排列与前批中王宗佶罢政异文分开。')
event('zhou_dewei_returns','周德威独身入晋阳哭李克用并拜见李存勖',18,
      '夏，四月，辛丑朔，德威至晋阳，留兵城外，独徒步而入，伏先王柩，哭极哀。退，谒嗣王，礼甚恭。众心由是释然。',
      [('周德威','率军回晋阳并向新晋王表示恭顺'),('李存勖','接受周德威拜见的新晋王')],
      when='908年四月辛丑朔',place='晋阳',
      note='“国人皆疑之”为疑虑，不当作周德威真有叛心。')
extra(old_dewei,'event','event_zztj_266_0908_zhou_dewei_returns','description',
      '《旧五代史》卷五十六记周德威单骑入谒、伏灵柩痛哭，众疑遂释。',
      '單騎入謁，伏靈柩哭，哀不自勝，由是群情釋然。',18,'corroborates',
      '旧书记单骑，主书记徒步；只印证其孤身入谒及哭柩，不将交通方式强行统一。')
event('liang_court_apr908','后梁罢杨涉相位，任于兢、张策同平章事',19,
      '癸卯，门下侍郎、同平章事杨涉罢为右仆射；以吏部侍郎于兢为中书侍郎，翰林学士承旨张策为刑部侍郎，并同平章事。',
      [('杨涉','罢相改任右仆射'),('于兢','受任中书侍郎、同平章事'),('张策','受任刑部侍郎、同平章事')],
      when='908年四月癸卯',
      note='授官与同段后续军事行动分开。')
event('jin_prepares_luzhou_relief','李存勖筹划急援潞州并向岐、契丹求援',19,
      '张承业亦劝之行。乃遣承业及判官王缄乞师于凤翔，又遣使赂契丹王阿保机求骑兵。岐王衰老，兵弱财竭，竟不能应。',
      [('李存勖','筹备潞州救援的晋王'),('张承业','劝说并赴凤翔乞援'),('王缄','随张承业赴凤翔乞援')],
      when='908年四月丙午后、甲子前',place='晋阳、凤翔',
      note='向契丹求骑兵是请求，岐王未能响应；不据此建已实现的军事同盟。')
claim('event','event_zztj_266_0908_jin_prepares_luzhou_relief','description',
      '李存勖任丁会为都招讨使，甲子率周德威等自晋阳出发。',19,
      '晋王大阅士卒，以前昭义节度使丁会为都招讨使。甲子，帅周德威等发晋阳。',
      '甲子是出发日；夹寨之战在下一段五月，不能提前。')
event('huainan_shishou','淮南兵进犯石首，在瀺港被襄州兵击败',20,
      '淮南遣兵寇石首，襄州兵败之于瀺港。',
      when='908年四月条；确日未载',place='石首、瀺港',
      note='主书未载此役具体淮南将领。')
event('huainan_jingnan','淮南李厚率水军趋荆南，在马头被高季昌击败',20,
      '又遣其将李厚将水军万五千趣荆南，高季昌逆战，败之于马头。',
      [('李厚','率淮南水军趋荆南'),('高季昌','在马头迎击并击败来军')],
      when='908年四月条；确日未载',place='马头、荆南',
      note='“万五千”为主书所记军数，不作现代精确统计。')
# 21: Break the long paragraph at the decisive battle and the later Zezhou defense.
event('luzhou_relief','李存勖突袭夹寨，潞州解围',21,
      '五月，辛未朔，晋王伏兵三垂冈下，诘旦大雾，进兵直抵夹寨。',
      when='908年五月辛未朔伏兵、诘旦突击',place='三垂冈、潞州夹寨',
      note='“诘旦”指次晨，沿用已发布潞州解围事件但另加明确日次引用；不把伏兵与突击强作同日。',
      reuse_key='event_luzhou_relief')
claim('event','event_luzhou_relief','description',
      '周德威攻夹寨西北隅，李嗣源攻东北隅；梁军溃退。',21,
      '晋王命周德威、李嗣源分兵为二道，德威攻西北隅，嗣源攻东北隅，填堑烧寨，鼓噪而入。梁兵大溃，南走',
      '这是主书记的两路进攻；《旧五代史》另列李存璋、李存审等，均在附证中标注。')
claim('event','event_luzhou_relief','description',
      '《通鉴》记符道昭马倒后为晋军所杀。',21,
      '招讨使符道昭马倒，为晋人所杀。',
      '《旧五代史》卷二十七作“获其将符道昭”，二书其结局异说并列。')
claim('event','event_luzhou_relief','description',
      '李嗣昭先疑城外劝其开门者为诈，见李存勖后开城，潞州围解。',21,
      '嗣昭见王白服，大恸几绝，城中皆哭，遂开门。',
      '开门发生在夹寨已破之后；不将此前不信理解为拒绝李存勖。')
claim('event','event_luzhou_relief','description',
      '李克用临终曾托李存勖化解周德威与李嗣昭旧隙，周德威得知后力战。',21,
      '晋王存勖以告德威，德威感泣，由是战夹寨甚力；既与嗣昭相见，遂欢好如初。',
      '这段是夹寨之战后的追叙，旧隙起始年份未载，不定为908年新仇。')
extra(old_battle,'event','event_luzhou_relief','description',
      '《旧五代史》卷二十七也记三垂冈伏兵、夹城被破，并增记李存璋、李存审参战。',
      '李嗣源壞夾城東北隅，率先掩擊，梁軍大恐，南向而奔',21,'corroborates',
      '旧书记“李存审”等参战，主书未逐一列出；只作为补充，不自动覆盖主书两路描述。')
extra(old_battle,'event','event_luzhou_relief','description',
      '《旧五代史》记晋军“获”符道昭，《通鉴》记其马倒被杀。',
      '獲其將副招討使符道昭洎大將三百人',21,'conflicts',
      '符道昭结局/“获”字语义待更多版本校核；两书原文并列。')
extra(new_battle,'event','event_luzhou_relief','description',
      '《新五代史》卷二十二也记三垂冈伏兵趁雾破夹城。',
      '會天大昏霧，伏兵三垂岡，直趨夾城，攻破之。',21,'corroborates',
      '本段梁将作康怀英，主书称康怀贞；是否同一人尚待人物身份校核，不因字形相近直接合并。')
event('zezhou_defense','牛存节赴泽州拒晋军，刘知俊来援后晋军撤至高平',21,
      '牛存节自西都将兵应接夹寨溃兵，至天井关',
      [('牛存节','主动赴泽州组织防御'),('刘知俊','从晋州率兵救泽州')],
      when='908年潞州解围后；泽州防御历十三日',place='泽州、天井关、高平',
      note='夹寨失败后另起的泽州攻防；牛存节守十三日，刘知俊来援后晋军退保高平。')
claim('event','event_zztj_266_0908_zezhou_defense','description',
      '牛存节至泽州稳定局面，抵御晋军地道攻城十三日。',21,
      '晋兵寻至，缘城穿地道攻之，存节昼夜拒战，凡旬有三日。',
      '“十三日”为围攻时长；不擅自推算起止公历日期。')
claim('event','event_zztj_266_0908_zezhou_defense','description',
      '刘知俊自晋州来援，周德威焚攻具并退保高平。',21,
      '刘知俊自晋州引兵救之，德威焚攻具，退保高平。',
      '只记本段结局，不将泽州说成被晋军攻取。')

# 22-24: Jin administration and long recovery of Luzhou.
event('cunxu_governance','李存勖回晋阳后整吏治、减租赋并整训军队',22,
      '晋王归晋阳，休兵行赏。以周德威为振武节度使、同平章事。命州县举贤才，黜贪残，宽租赋，抚孤穷，伸冤滥，禁奸盗',
      [('李存勖','回晋阳并发布整治政令的晋王'),('周德威','受任振武节度使、同平章事')],
      when='908年潞州解围后；确日未载',place='晋阳、河东',
      note='主书后句“故能兼山东，取河南”是后见评述，不倒填为908年已完成疆域扩张。')
claim('event','event_zztj_266_0908_cunxu_governance','description',
      '李存勖定骑兵与分道行军纪律，违令者严惩。',22,
      '令骑兵不见敌无得乘马。部分已定，无得相逾越，及留绝以避险；分道并进，期会无得差晷刻。犯者必斩。',
      '军令为本段所记；其后“兼山东取河南”不能作为本年结果。')
event('cunxu_commissions','李存勖开始承制除授官吏',23,
      '至是，晋王存勖始承制除吏。',
      [('李存勖','开始承制除授官吏的晋王')],when='908年潞州解围后条；确日未载',
      note='前句李克用不愿行墨制为追叙；“至是”才是李存勖新做法。')
event('cunxu_honors_zhang','李存勖厚礼张承业并拜见其母',23,
      '晋王德张承业，以兄事之，每至其第，升堂拜母，赐遗甚厚。',
      [('李存勖','厚礼张承业的晋王'),('张承业','受李存勖敬重的监军')],
      when='908年李存勖继位后；历时未载',
      note='“以兄事之”比喻敬重，不建血缘兄弟关系；拜母为其礼敬行为。')
event('luzhou_recovery','李嗣昭在潞州解围后劝农、宽租缓刑，城邑渐复',24,
      '李嗣昭劝课农桑，宽租缓刑，数年之间，军城完复。',
      [('李嗣昭','推动潞州解围后恢复的守将')],
      when='908年解围后起、数年间；结束年未载',place='潞州',
      note='“数年之间”明确跨年，后续恢复不全定在908年。')
for row in B['events']:
    if row['key']=='event_zztj_266_0908_luzhou_recovery':
        row['end_year']=None
        break
extra(old_sizhao,'event','event_zztj_266_0908_luzhou_recovery','description',
      '《旧五代史》卷五十二也记李嗣昭宽租劝农，潞州一二年间恢复。',
      '嗣昭緩法寬租，勸農務穡，一二年間，軍城',24,'adds',
      '旧书作“一二年间”，主书作“数年之间”；时间跨度并列，不选其一为精确年限。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,25):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷266开平二年第11—24段连续处理；潞州前后战事、前蜀宫廷事件与跨年恢复分开，旧新史异说并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=266,year=908,
    primary_source_key=primary,primary_source_keys=[primary,prelude,battle,after],
    paragraphs=[Q[n]['id'] for n in range(11,25)],next_paragraph=Q[25]['id'],
    coverage='卷266开平二年第11—24段连续处理；潞州围城、夹寨解围、泽州防守、前蜀宫廷及潞州恢复。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
