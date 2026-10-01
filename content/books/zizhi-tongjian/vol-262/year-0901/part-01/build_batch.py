"""Curate Tongjian 262, year 901, consecutive paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 56))
primary_prev = 'tongjian-262-900-yearend'
primary = 'tongjian-262-901-spring'
old_tang = 'jiutangshu-020-901-restoration'
new_sun = 'xinwudaishi-046-901-sun'
B = {'format_version': 1, 'batch_key': 'zztj-v262-y0901-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_prev, P.parent.parent / 'year-0900/part-04/sources/library' / primary_prev, '7db9c9d', '司马光等'),
    (primary, P / 'sources/library' / primary, '7b68833', '司马光等'),
    (old_tang, P / 'sources/library' / old_tang, '7b68833', '刘昫等'),
    (new_sun, P / 'sources/library' / new_sun, '7b68833', '欧阳修'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_prev, primary)}
for n in range(1, 9):
    assert Q[n]['text'] in ''.join(primary_texts.values()), (n, Q[n]['text'][:30])

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '上': '李杰', '何后': '何氏（唐昭宗皇后）',
           '太子': '李祐', '裕': '李祐', '李继昭': '孙德昭',
           '李继诲': '周承诲', '李彦弼': '董彦弼'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and Q[n]['text'] in data)

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_262_0901_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷262·天复元年（901）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical, aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷262天复元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=901):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_262_0901_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '901年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '901年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role)
        edge = 'participation_zztj_262_0901_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_262_0901_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

event('sun_kills_wang_zhongxian', '孙德昭安福门擒斩王仲先', 1,
      '春，正月，乙酉朔，王仲先入朝，至安福门，孙德昭擒斩之，',
      [('孙德昭', '擒斩王仲先者'), ('王仲先', '被擒斩者')],
      when='901年春正月乙酉朔', place='安福门',
      note='主书明确孙斩王仲先；旧唐本纪正月甲申朔记昭宗反正，日次异，旧唐十二月另记孙等杀王；新五孙传作孙斩刘季述，不静改主书。')
claim('person', people['王仲先'], 'death_year', '王仲先于901年正月乙酉朔被孙德昭擒斩。', 1,
      '王仲先入朝，至安福门，孙德昭擒斩之', '主书乙酉朔；与旧唐十二月记事月日异。')
event('queen_demands_head_emperor_freed', '何皇后验王仲先首，昭宗与后出少阳院', 1,
      '何后不信，曰：“果尔，以其首来！”德昭献其首，上乃与后毁扉而出。',
      [('何氏（唐昭宗皇后）', '求验首并出院者'), ('孙德昭', '献首者'), ('李杰', '出院昭宗')],
      when='901年正月乙酉朔', place='少阳院',
      note='何后为既有昭宗皇后；验首后出院，勿写听到呼喊即出。')
event('cui_welcomes_emperor_changle', '崔胤迎昭宗登长乐门楼率百官称贺', 1,
      '崔胤迎上御长乐门楼，帅百官称贺。',
      [('崔胤', '迎驾率百官者'), ('李杰', '复位受贺昭宗')],
      when='901年正月乙酉朔', place='长乐门楼',
      note='昭宗出少阳院后受贺；旧唐作甲申朔，保干支异记。')
event('zhou_captures_liu_wangyanfan', '周承诲擒刘季述王彦范，二人被乱梃击死', 1,
      '周承诲擒刘季述、王彦范继至，方诘责，已为乱梃所毙。',
      [('周承诲', '擒二人者'), ('刘季述', '被擒后击死者'), ('王彦范', '被擒后击死者')],
      when='901年正月乙酉朔昭宗出院后', place='长乐门楼附近',
      note='主书称周擒、乱梃击死，未指周本人亲手击毙；旧唐称孙执刘，新五称孙斩刘，保各书叙法。')
for name in ('刘季述', '王彦范'):
    claim('person', people[name], 'death_year', f'{name}于901年复位之日被乱梃击死。', 1,
          '周承诲擒刘季述、王彦范继至，方诘责，已为乱梃所毙。',
          '复位当日承乙酉朔；具体行刑者未具名。')
event('xue_qiwo_well_death', '薛齐偓投井而死，尸出复斩', 1,
      '薛齐偓赴井死，出而斩之。', [('薛齐偓', '投井死后被斩者')],
      when='901年正月乙酉朔', note='先赴井死再出斩，不写被斩才死亡。')
claim('person', people['薛齐偓'], 'death_year', '薛齐偓于901年复位之日投井身亡。', 1,
      '薛齐偓赴井死，出而斩之。', '先死后斩，死亡与毁尸次序分明。')
event('coup_families_and_party_purged', '四名废立者家族被灭，党羽二十余人被诛', 1,
      '灭四人之族，并诛其党二十馀人。',
      when='901年正月复位后；确日未另载',
      note='四人承刘季述、王仲先、王彦范、薛齐偓；家族及党羽未逐名，不造人物和精确受害人数。')
event('crown_prince_deposed_renamed_yu', '昭宗还太子东宫，黜德王复名裕', 1,
      '上曰：“裕幼弱，为凶竖所立，非其罪也。”命还东宫，黜为德王，复名裕。',
      [('李杰', '降太子封德王者'), ('李祐', '被降德王并复名裕者')],
      when='901年正月复位后；确日未另载', place='东宫',
      note='李祐为891德王、897更名裕、900更名缜的同一稳定主体；复名裕不新建人物。旧唐书作“改名祐”，异记并列。')
claim('person', people['李祐'], 'aliases', '901年昭宗复位后太子被黜德王，史书记复名裕。', 1,
      '命还东宫，黜为德王，复名裕。', '复用同一主体；旧唐书作改名祐，保异文。')
event('sun_dezhao_awarded_renamed', '孙德昭丙戌授同平章事静海节度使并赐名李继昭', 1,
      '丙戌，以孙德昭同平章事，充静海节度使，赐姓名李继昭。',
      [('孙德昭', '受任及赐姓名者')], when='901年正月丙戌', place='静海军',
      note='孙德昭此次赐名李继昭，与897年凤翔将既有李继昭同名不可合并；本批后文“李继昭”均指孙德昭。')
claim('person', people['孙德昭'], 'aliases', '孙德昭于901年正月丙戌获赐姓名李继昭。', 1,
      '以孙德昭同平章事，充静海节度使，赐姓名李继昭。',
      '只留事实引用，不改已发布凤翔将李继昭的稳定键或混加别名。')
extra(old_tang, 'event', 'event_zztj_262_0901_cui_welcomes_emperor_changle', 'time_original',
      '《旧唐书》本纪作天复元年正月甲申朔昭宗反正登长乐门，主书作乙酉朔。',
      '天復元年春正月甲申朔，昭宗反正，登長樂門樓，受朝賀。', 1, 'conflicts',
      '正月朔干支甲申/乙酉异记；未据转历或后人校改消解。')
extra(old_tang, 'event', 'event_zztj_262_0901_crown_prince_deposed_renamed_yu', 'description',
      '《旧唐书》本纪记太子裕降德王“改名祐”，主书作复名裕。',
      '制皇太子裕降為德王，改名祐。', 1, 'conflicts',
      '同降封而改名字面冲突；稳定主体沿891李祐，不强选唯一终名。')
extra(new_sun, 'event', 'event_zztj_262_0901_sun_kills_wang_zhongxian', 'description',
      '《新五代史》孙德昭传作正月朔孙德昭伏兵斩刘季述，主书作孙斩王仲先、周擒刘季述。',
      '天復元年正月朔，未旦，季述將朝，德昭伏甲士道旁，邀其輿斬之', 1, 'conflicts',
      '同复位事的被斩者与主攻人叙法不同；不造第二次处死刘季述。')

event('cui_yin_situ_declined', '崔胤丁亥进位司徒固辞，昭宗仍厚待', 2, Q[2]['text'],
      [('崔胤', '进位而固辞者'), ('李杰', '厚待崔胤者')], when='901年正月丁亥',
      note='固辞是崔的回应；不写其已实际受司徒职。旧唐本纪此日也与主书有差。')
event('zhu_sends_cheng_yan_executed', '朱全忠折程岩足并械送京师', 3,
      '硃全忠闻刘季述等诛，折程岩足，械送京师，',
      [('朱温', '折足械送者'), ('程岩', '被折足械送者')],
      when='901年正月己丑', place='大梁至京师',
      note='此句只述折足械送；斩首由后句“并……皆斩于都市”支持，不写朱本人在京师亲自行刑。')
event('envoys_cheng_executed_li_valued', '程岩刘希度李奉本等在都市被斩，朱全忠益重李振', 3,
      '折程岩足，械送京师，并刘希度、李奉本等皆斩于都市，由是益重李振。',
      [('程岩', '被斩者'), ('刘希度', '被斩者'), ('李奉本', '被斩者'), ('朱温', '益重李振者'), ('李振', '受倚重者')],
      when='901年正月己丑条；具体行刑日未单列', place='京师都市',
      note='程岩承前句“械送京师”；希度奉本900年被囚、901年始死，勿倒填900。')
for name in ('程岩', '刘希度', '李奉本'):
    claim('person', people[name], 'death_year', f'{name}于901年被斩于京师都市。', 3,
          '折程岩足，械送京师，并刘希度、李奉本等皆斩于都市',
          '程岩承前句，三人同条被斩；确日未单独指明。')
extra(old_tang, 'event', 'event_zztj_262_0901_zhu_sends_cheng_yan_executed', 'description',
      '《旧唐书》本纪己丑亦记朱全忠折程岩足并槛送京师戮于市。',
      '己丑，朱全忠械程岩，折足檻送京師，戮之於市。', 3, 'corroborates',
      '同程岩处置，未补刘希度李奉本个人日期。')

event('zhou_chenghui_awarded_renamed', '周承诲任岭南西道节度并赐名李继诲', 4,
      '庚寅，以周承诲为岭南西道节度使，赐姓名李继诲，',
      [('周承诲', '受任并赐名者')], when='901年正月庚寅', place='岭南西道',
      note='复用周承诲主体，赐名李继诲不另建人；新五孙传作孙承诲，保异名。')
claim('person', people['周承诲'], 'aliases', '周承诲于901年赐姓名李继诲。', 4,
      '以周承诲为岭南西道节度使，赐姓名李继诲',
      '本批后文李继诲指同人；新五孙传作孙承诲待校。')
event('dong_yanbi_awarded_li_surname', '董彦弼任宁远节度并赐李姓', 4,
      '董彦弼为宁远节度，赐姓李，并同平章事；',
      [('董彦弼', '受任赐姓者')], when='901年正月庚寅', place='宁远军',
      note='主书本句仅赐姓李，下段李彦弼沿同人；新五孙传作董从实，保书证异名。')
claim('person', people['董彦弼'], 'aliases', '董彦弼于901年获赐李姓，后文称李彦弼。', 4,
      '董彦弼为宁远节度，赐姓李', '后段“李彦弼”承同一受赐姓者，不新建人物。')
event('three_premiers_lodge_rewarded', '李继昭李继诲李彦弼留宿卫十日并受厚赏', 4,
      '与李继昭俱留宿卫，十日乃出还家，赏赐倾府库，时人谓之“三使相”。',
      [('孙德昭', '赐名李继昭的三使相之一'), ('周承诲', '赐名李继诲的三使相之一'), ('董彦弼', '赐李姓的三使相之一')],
      when='901年正月庚寅后十日；确日未换算', place='京师',
      note='三使相为时人称谓，赐官不等于已赴岭南宁远实际镇守；凤翔将旧李继昭不参与此事。')
extra(new_sun, 'event', 'event_zztj_262_0901_three_premiers_lodge_rewarded', 'description',
      '《新五代史》孙德昭传称与孙承诲董从实等皆拜节度同平章，留京师号三使相。',
      '與承誨等皆拜節度使、同中書門下平章事，圖形凌煙閣，俱留京師，號「三使相」',
      4, 'adds', '承诲、董从实姓名在该传前文，主书周承诲董彦弼；不直接设别名。')
event('zhu_east_ping_king', '朱全忠进爵东平王', 5, Q[5]['text'],
      [('朱温', '进爵东平王者')], when='901年正月癸巳',
      note='东平王为爵位，不写已受禅称梁帝。')
event('court_restricts_eunuch_audiences', '朝廷恢复宰相奏事后枢密使始得升殿旧制', 6,
      '自今并依大中旧制，俟宰臣奏事毕，方得升殿承受公事。',
      [('李杰', '颁敕者')], when='901年正月丙午',
      note='敕限制枢密使殿上承受次序，不写宦官兵权已全被文臣夺取。')
event('li_shiqian_xu_yansun_executed', '李师虔徐彦孙赐自尽', 6,
      '赐两军副使李师虔、徐彦孙自尽，皆刘季述之党也。',
      [('李师虔', '被赐自尽者'), ('徐彦孙', '被赐自尽者')],
      when='901年正月丙午', note='旧唐本纪另一名作徐彦回，与主书徐彦孙异；不将两名直接并为同人别名。')
for name in ('李师虔', '徐彦孙'):
    claim('person', people[name], 'death_year', f'{name}于901年正月丙午被赐自尽。', 6,
          '赐两军副使李师虔、徐彦孙自尽', '确日承丙午；旧唐徐彦回异名另见补证。')
extra(old_tang, 'event', 'event_zztj_262_0901_li_shiqian_xu_yansun_executed', 'description',
      '《旧唐书》本纪同诏列李师虔与徐彦回，主书记徐彦孙。',
      '殺神策軍使李師虔、徐彥回。', 6, 'conflicts',
      '彦孙/彦回用字及官称不同，待纸本核，不静改既有徐彦孙新键。')
event('li_maozhen_visits_promoted', '李茂贞来朝并加尚书令侍中进爵歧王', 7, Q[7]['text'],
      [('李茂贞', '来朝受加爵者')], when='901年正月条；确日未载', place='京师',
      note='来朝与加官进爵同段；歧王保底本用字，不推此前爵号撤销。')

event('cui_lu_request_army_command', '崔胤陆扆请求分主左右军', 8,
      '崔胤、陆扆上言：“祸乱之兴，皆由中官典兵。乞令胤主左军，扆主右军，则诸侯不敢侵陵，王室尊矣。”',
      [('崔胤', '请主左军者'), ('陆扆', '请主右军者')],
      when='901年刘季述王仲先死后；确日未载',
      note='此为崔陆上言建议和判断，不写文臣已接掌两军。')
event('emperor_hesitates_maozhen_objects', '昭宗犹豫两日，李茂贞反对崔胤夺军权', 8,
      '上犹豫两日未决。李茂贞闻之，怒曰：“崔胤夺军权未得，已欲翦灭诸侯！”',
      [('李杰', '犹豫未决者'), ('李茂贞', '反对者'), ('崔胤', '被李茂贞指责者')],
      when='901年崔陆上奏后两日；确日未载',
      note='翦灭诸侯为李茂贞指控，不作崔胤已计划灭诸侯的事实。')
event('three_generals_reject_southern_command', '李继昭李继诲李彦弼反对两军归南司', 8,
      '上召李继昭、李继诲、李彦弼谋之，皆曰：“臣等累世在军中，未闻书生为军主；若属南司，必多所变更，不若归之北司为便。”',
      [('李杰', '召议者'), ('孙德昭', '受召反对者，赐名李继昭'),
       ('周承诲', '受召反对者，赐名李继诲'), ('董彦弼', '受召反对者，赐姓李')],
      when='901年昭宗犹豫期间；确日未载',
      note='三名系刚受赐姓者：李继昭=孙德昭，不与897年凤翔将同名者混合；“书生为军主”是将领意见。')
event('emperor_refuses_cui_lu', '昭宗以将士不愿为由拒崔胤陆扆分主两军', 8,
      '上乃谓胤、扆曰：“将士意不欲属文臣，卿曹勿坚求。”',
      [('李杰', '拒请者'), ('崔胤', '被拒者'), ('陆扆', '被拒者')],
      when='901年三将表态后；确日未载',
      note='拒绝崔陆此次请求，不等于朝廷永不调整军权。')
event('han_zhang_appointed_eunuch_command', '韩全诲张彦弘分任左右军中尉', 8,
      '于是以枢密使韩全诲、凤翔监军使张彦弘为左、右中尉。',
      [('韩全诲', '任左军中尉者'), ('张彦弘', '任右军中尉者')],
      when='901年崔陆请求被拒后；确日未载',
      note='按“韩、张为左、右”顺序对应；不与张彦弘后文异写静改。')
event('yan_zunmei_refuses_two_armies', '严遵美拒受两军中尉观军容处置使', 8,
      '又征前枢密使致仕严遵美为两军中尉、观军容处置使。遵美曰：“一军犹不可为，况两军乎！”固辞不起。',
      [('严遵美', '被征召而固辞者')],
      when='901年韩张任命后；确日未载',
      note='征召与固辞分别清楚，严未实际上任。')
event('yuan_zhou_privy_appointed', '袁易简周敬容任枢密使', 8,
      '以袁易简、周敬容为枢密使。',
      [('袁易简', '受任枢密使者'), ('周敬容', '受任枢密使者')],
      when='901年严遵美辞后；确日未载')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 9):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='八段连续校核：昭宗复位、刘季述党处置、太子降封复名、孙德昭周承诲董彦弼受任赐名、朱全忠进爵、枢密殿上程序和军权归属分录。孙赐名李继昭不并897凤翔将；旧唐朔日、太子改名及徐彦孙异文与新五复位将领叙法并列。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused | {primary_prev}), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=262, year=901,
    primary_source_key=primary_prev, primary_source_keys=[primary_prev, primary],
    paragraphs=[Q[n]['id'] for n in range(1, 9)], next_paragraph=Q[9]['id'],
    coverage='天复元年55段中的第1—8段连续处理；本年尚未完成。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
