"""Curate Tongjian 262, year 900, consecutive paragraphs 17–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 33))
primary_autumn = 'tongjian-262-900-autumn'
primary_late = 'tongjian-262-900-late'
old_liang = 'jiuwudaishi-002-900-dezhou'
old_tang_september = 'jiutangshu-020-900-xu'
new_ma = 'xinwudaishi-066-900-ma'
new_wang = 'xinwudaishi-039-900-wang'
B = {'format_version': 1, 'batch_key': 'zztj-v262-y0900-p017-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (old_liang, P.parent / 'part-01/sources/library' / old_liang, 'bb575ad', '薛居正等'),
    (primary_autumn, P.parent / 'part-02/sources/library' / primary_autumn, '9c06dec', '司马光等'),
    (old_tang_september, P.parent / 'part-02/sources/library' / old_tang_september, '9c06dec', '刘昫等'),
    (primary_late, P / 'sources/library' / primary_late, '6baba6f', '司马光等'),
    (new_ma, P / 'sources/library' / new_ma, '6baba6f', '欧阳修'),
    (new_wang, P / 'sources/library' / new_wang, '6baba6f', '欧阳修'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_autumn, primary_late)}
for n in range(17, 25):
    assert Q[n]['text'] in ''.join(primary_texts.values()), (n, Q[n]['text'][:30])

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '硃友谦': '朱友谦', '镕': '王镕', '上': '李杰'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and Q[n]['text'] in data)

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_262_0900_03_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷262·光化三年（900）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷262光化三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=900):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_262_0900_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '900年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '900年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role)
        edge = 'participation_zztj_262_0900_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_262_0900_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# September court appointments and the Jingjiang elevation.
event('cui_yuan_removed', '崔远罢相守本官', 17,
      '丙午，中书侍郎兼吏部尚书、同平章事崔远罢守本官，',
      [('崔远', '罢相者')], when='900年九月丙午',
      note='守本官不等于褫夺全部职官。')
event('pei_zhi_premier', '裴贽任中书侍郎同平章事', 17,
      '以刑部尚书裴贽为中书侍郎、同平章事。',
      [('裴贽', '受任宰相者')], when='900年九月丙午')
person('裴坦', 17, '裴贽叔父，史书以“坦之弟子”指称')
kin_pei = 'relationship_person_裴贽_person_裴坦_侄子'
B['person_relationships'].append(dict(key=kin_pei, person_a_key=people['裴贽'],
    person_b_key=people['裴坦'], relation_type='侄子', description='裴贽是裴坦弟弟之子。', status='draft'))
claim('person_relationship', kin_pei, 'description', '裴贽是裴坦弟弟之子。', 17,
      '贽，坦之弟子也。', '“弟子”依句法作弟之子；父亲未具名，不补父亲人物。')
event('jingjiang_elevated', '桂管升为静江军', 17, '升桂管为静江军，',
      when='900年九月丙午条', place='桂管',
      note='升军为建制变化，与刘士政个人任官分录。')
event('liu_shizheng_jingjiang', '刘士政由桂管经略使任静江节度使', 17,
      '以经略使刘士政为节度使。', [('刘士政', '受任静江节度使者')],
      when='900年九月丙午条', place='静江军',
      note='官职按主书；新五代史马殷传在后来桂管战叙称刘为桂管留后，保职名异说。')
extra(old_tang_september, 'event', 'event_zztj_262_0900_cui_yuan_removed', 'description',
      '《旧唐书》制词丙午记崔远罢知政事、守本官。',
      '丙午，制光祿大夫、中書侍郎、兼吏部尚書、同平章事、充集賢殿大學士、判戶部事、博陵郡開國公、食邑二千戶崔遠罷知政事，守本官。',
      17, 'corroborates', '与主书同日同任免，制词具原官衔。')
extra(old_tang_september, 'event', 'event_zztj_262_0900_pei_zhi_premier', 'description',
      '《旧唐书》同段制裴贽中书侍郎、兼刑部尚书、同平章事。',
      '以正議大夫、守刑部尚書、上柱國、河東縣開國男、食邑三百戶、賜紫金魚袋裴贄為中書侍郎，兼刑部尚書、同平章事',
      17, 'corroborates', '书证具兼官；与主书同次任相，不另算一任。')

# Zhenzhou: campaign, negotiation, hostage, marriage and renewed northern offensive.
event('zhu_attacks_zhenzhou', '朱全忠因王镕通河东进攻镇州', 18,
      '硃全忠以王镕与李克用交通，移兵伐之，下临城，逾滹沱，攻镇州南门，焚其关城。',
      [('朱温', '进攻镇州者'), ('王镕', '受攻成德节度使'), ('李克用', '主书所述与王镕交通者')],
      when='900年九月后、十月前条；确日未载', place='临城、滹沱、镇州',
      note='交通为朱举兵理由，不据此写正式永久盟约；临城被下、镇州南门被攻焚关城有别，不写镇州已陷。')
event('wang_rong_sends_zhou_shi', '王镕遣周式向朱全忠请和', 18,
      '全忠自至元氏，镕惧，遣判官周式诣全忠请和。',
      [('王镕', '遣使求和者'), ('周式', '成德判官请和使'), ('朱温', '受使者')],
      when='900年朱军至元氏后；确日未载', place='元氏',
      note='请和为请求，是否达成看后续纳质撤军。')
event('zhou_shi_persuades_zhu', '周式论说朱全忠，朱允其议', 18,
      '全忠笑揽式袂，延之帐中，曰：“与公戏耳！”',
      [('周式', '说服朱军议和者'), ('朱温', '接纳周式入帐者')],
      when='900年周式请和时；确日未载', place='朱全忠军帐',
      note='“与公戏耳”为朱的自述，不据此断定先前威胁只是戏言。')
event('liu_han_enters_zhenzhou', '朱全忠遣刘捍入镇州见王镕', 18,
      '乃遣客将开封刘捍入见镕，',
      [('朱温', '遣客将者'), ('刘捍', '入见王镕者'), ('王镕', '受见者')],
      when='900年周式议和后；确日未载', place='镇州')
event('wang_rong_hostage_tribute', '王镕送王昭祚等为质并以文缯二十万犒军', 18,
      '镕以其子节度副使昭祚及大将子弟为质，以文缯二十万犒军。',
      [('王镕', '纳质及犒军者'), ('王昭祚', '王镕子、节度副使人质')],
      when='900年镇州请和后；确日未载', place='镇州',
      note='二十万是主书文缯数，不换算银两；旧唐十五万匹并列。未名大将子弟不造人物。')
kin_father = 'relationship_person_王镕_person_王昭祚_父亲'
B['person_relationships'].append(dict(key=kin_father, person_a_key=people['王镕'],
    person_b_key=people['王昭祚'], relation_type='父亲', description='王镕是王昭祚的父亲。', status='draft'))
claim('person_relationship', kin_father, 'description', '王镕是王昭祚的父亲。', 18,
      '镕以其子节度副使昭祚及大将子弟为质', '其子承王镕；方向为王镕—父亲→王昭祚。')
event('zhu_withdraws_marriage', '朱全忠撤兵并以女嫁王昭祚', 18,
      '全忠引还，以女妻昭祚。',
      [('朱温', '撤军并嫁女者'), ('王昭祚', '朱全忠女婿')],
      when='900年镇州纳质后；确日未载', place='镇州方向',
      note='朱女未具名，不新造姓名或女子生平；婚姻由此句明载。')
kin_affinity = 'relationship_person_王昭祚_person_朱温_女婿'
B['person_relationships'].append(dict(key=kin_affinity, person_a_key=people['王昭祚'],
    person_b_key=people['朱温'], relation_type='女婿', description='王昭祚是朱全忠的女婿。', status='draft'))
claim('person_relationship', kin_affinity, 'description', '王昭祚是朱全忠的女婿。', 18,
      '全忠引还，以女妻昭祚。', '朱全忠以女嫁王昭祚；仅建明示姻亲方向，不杜撰其女姓名。')
extra(old_tang_september, 'event', 'event_zztj_262_0900_wang_rong_hostage_tribute', 'description',
      '《旧唐书》本纪记王镕送王昭祚等为质、犒军絹十五万匹；主书记文缯二十万。',
      '王鎔懼，遣判官周式、副大使王昭祚、主事梁公儒子弟為質於汴，出犒師絹十五萬匹求盟，許之。',
      18, 'conflicts', '同次请盟的人质和犒军，但数量十五万/二十万异记；旧唐将王昭祚列副大使，不静改主书副使。')
event('zhang_ze_proposes_north', '张泽劝王镕请朱全忠兼服幽沧易定', 18,
      '成德判官张泽言于王镕曰：“河东，勍敌也，今虽有硃氏之援，譬如火发于家，安能俟远水乎！彼幽、沧易定。犹附河东，不若说硃公乘胜兼服之，使河北诸镇合而为一，则可以制河东矣。”',
      [('张泽', '提出建议者'), ('王镕', '听议者')],
      when='900年镇州和解后；确日未载', place='镇州',
      note='此为张泽政策建议，不当幽沧易定已被朱兼并的事实。')
event('wang_rong_sends_zhou_again', '王镕再次遣周式说朱全忠北攻', 18,
      '镕复遣周式往说全忠。全忠喜，',
      [('王镕', '再次遣说者'), ('周式', '再次往说者'), ('朱温', '受说者')],
      when='900年镇州和解后；确日未载',
      note='“复遣”与首次请和分开；朱喜不等于各镇统一。')
event('zhu_sends_zhang_against_liu', '朱全忠遣张存敬会魏博兵击刘仁恭', 18,
      '遣张存敬会魏博兵击刘仁恭，',
      [('朱温', '遣攻者'), ('张存敬', '率军会魏博者'), ('刘仁恭', '被攻对象')],
      when='900年秋王镕再遣周式后；确日未载', place='魏博、幽沧方向')
event('zhang_takes_ying', '张存敬军拔瀛州', 18, '甲寅，拔瀛州；',
      [('张存敬', '攻军将领')], when='900年秋甲寅', place='瀛州',
      note='承张存敬奉命出兵；旧五梁纪置十一月，主书甲寅在十月前，月序待核。')
event('zhang_takes_jing_capture_renba', '张存敬军拔景州执刘仁霸', 18,
      '冬，十月，丙辰，拔景州，执刺史刘仁霸；',
      [('张存敬', '攻军将领'), ('刘仁霸', '被执景州刺史')],
      when='900年冬十月丙辰', place='景州', note='被执不记已被杀。')
event('zhang_takes_mo', '张存敬军拔莫州', 18, '辛酉，拔莫州。',
      [('张存敬', '攻军将领')], when='900年冬十月辛酉', place='莫州')

# Guilin campaign: request, reconnaissance, seizure, rout, surrender, appointments.
event('liu_shizheng_sends_chen_to_quanyi', '刘士政遣陈可璠屯全义岭御马殷', 19,
      '静江节度使刘士政闻马殷悉平岭北，大惧，遣副使陈可璠屯全义岭以备之。',
      [('刘士政', '遣防者'), ('陈可璠', '屯全义岭副使'), ('马殷', '被防备湖南方')],
      when='900年十月后条；确日未载', place='全义岭',
      note='闻岭北已平为刘的获知和警惕，不由此推本段所有岭北作战日期。')
event('ma_peace_envoy_rejected', '马殷遣使修好刘士政，陈可璠拒之', 19,
      '殷遣使修好于士政，可璠拒之。',
      [('马殷', '遣使修好者'), ('刘士政', '被求好者'), ('陈可璠', '拒绝使者')],
      when='900年全义岭设防后；确日未载', place='全义岭',
      note='使者未名，不新造；拒使与开战分开。')
event('ma_sends_qin_li_7000', '马殷遣秦彦晖李琼七千军击刘士政', 19,
      '殷遣其将秦彦晖、李琼等将兵七千击士政。',
      [('马殷', '遣军者'), ('秦彦晖', '受遣将领'), ('李琼', '受遣将领'), ('刘士政', '受攻方')],
      when='900年陈可璠拒使后；确日未载', place='桂管方向',
      note='七千为主书记数；不写全部七千参与夜袭秦城。')
event('liu_posts_wang_jianwu_qincheng', '刘士政遣王建武屯秦城', 19,
      '士政又遣指挥使王建武屯秦城。',
      [('刘士政', '遣防者'), ('王建武', '屯秦城指挥使')],
      when='900年湖南军至全义后；确日未载', place='秦城')
event('chen_seizes_cattle_villagers_guide', '陈可璠掠牛，县民怨而为湖南军指小径', 19,
      '可璠掠县民耕牛以犒军，县民怨之，请为湖南乡异，曰：“此西南有小径，距秦城才五十里，仅通单骑。”',
      [('陈可璠', '掠耕牛者')],
      when='900年秦城设防后；确日未载', place='全义岭、秦城',
      note='县民未具名，不造人物；“乡异”疑底本讹字，原字保留，只依下文其报告小径。五十里为史载距离，不换地图坐标。')
event('li_qiong_night_raid_qincheng', '秦彦晖遣李琼夜袭秦城擒王建武', 19,
      '彦晖遣李琼将骑六十、步兵三百袭秦城，中宵，逾垣而入，擒王建武，',
      [('秦彦晖', '遣袭者'), ('李琼', '率夜袭军者'), ('王建武', '秦城被擒者')],
      when='900年秦城设防后某夜；确日未载', place='秦城',
      note='六十骑三百步兵为夜袭分遣兵，不等于前述七千总兵；王被擒时未写已处死。')
event('li_displays_wang_head', '湖南军至陈可璠壁下斩王建武示首', 19,
      '斩其首，投壁中，桂人震恐。',
      [('李琼', '夜袭军率领者'), ('王建武', '被斩者')],
      when='900年秦城夜袭次晨；确日未载', place='陈可璠壁下',
      note='“其”承被擒王建武，主书先示活人后斩；底本“纟斥之以练”转录疑讹，不依据该字推刑罚细节。')
claim('person', people['王建武'], 'death_year', '王建武于900年秦城夜袭后被斩首。', 19,
      '斩其首，投壁中', '“其”指前句被擒王建武；不补公历月日。')
event('li_captures_chen_kills_surrendered', '李琼击擒陈可璠，降其将士二千后皆杀', 19,
      '琼因勒兵击之，擒可璠，降其将士二千，皆杀之。',
      [('李琼', '击擒陈可璠者'), ('陈可璠', '被擒者')],
      when='900年秦城袭击后；确日未载', place='全义岭',
      note='“皆杀之”指降军二千，陈本人最终处置本句未独载，不能写被处死；新五作悉坑而保书证说法。')
event('li_sieges_guizhou', '李琼趋桂州，沿途堡垒溃散并围城', 19,
      '引兵趣桂州，自秦城以南二十馀壁皆望风奔溃，遂围桂州。',
      [('李琼', '进军围桂州者')],
      when='900年全义岭战后；确日未载', place='秦城至桂州',
      note='二十余壁为史载堡垒数，不逐一造地名；望风溃散与李琼亲自攻克不同。')
event('liu_surrenders_five_prefectures', '刘士政出降，桂宜岩柳象五州归湖南', 19,
      '数日，士政出降，桂、宜、岩、柳、象五州皆降于湖南。',
      [('刘士政', '出城投降者')],
      when='900年桂州被围数日后；确日未载', place='桂州、宜州、岩州、柳州、象州',
      note='数日仅相对围城，不换算日历；新五代史称虏，主书称出降，身份处境异叙并列。')
event('ma_appoints_li_qiong_guizhou', '马殷以李琼为桂州刺史，后表静江节度使', 19,
      '马殷以李琼为桂州刺史，未几，表为静江节度使。',
      [('马殷', '任及上表者'), ('李琼', '受桂州刺史并被表静江者')],
      when='900年桂州降后，未几表任；确日未载', place='桂州、静江军',
      note='前者马殷用人，后者仅为上表；不写朝廷已正式授静江节度。')
extra(new_ma, 'event', 'event_zztj_262_0900_li_captures_chen_kills_surrendered', 'description',
      '《新五代史》马楚世家记擒陈可璠等及兵二千余，悉坑之；主书记降二千皆杀。',
      '擒可璠等及其兵二千餘人，悉坑之', 19, 'adds',
      '人数二千/二千余和处死方式“坑”属书证异记；不凭此倒推陈本人确死。')
extra(new_ma, 'event', 'event_zztj_262_0900_liu_surrenders_five_prefectures', 'description',
      '《新五代史》马楚世家记围桂管后“虏士政”，主书作刘士政出降。',
      '遂圍桂管，虜士政，盡取其屬州。', 19, 'conflicts',
      '虏与出降叙法不同，暂不补其被俘具体过程；新五未逐列本段五州。')

event('zhang_takes_twenty_cities', '张存敬攻刘仁恭连下二十城', 20,
      '张存敬攻刘仁恭，下二十城，',
      [('张存敬', '攻城者'), ('刘仁恭', '被攻方')],
      when='900年十月后条；确日未载', place='幽沧地区',
      note='二十城为主书记数，不当逐城名称可考或全是州城。')
event('zhang_diverts_due_mud', '张存敬因道路泥泞弃趋幽州而西攻易定', 20,
      '将自瓦桥趣幽州，道泞不能进，乃引兵西攻易定，',
      [('张存敬', '改向西攻者')],
      when='900年下二十城后；确日未载', place='瓦桥、易定方向',
      note='原拟趋幽州未成，不录已攻幽州城。')
event('zhang_takes_qi_yang_yue_killed', '张存敬军拔祁州，杀刺史杨约', 20,
      '辛巳，拔祁州，杀刺史杨约。',
      [('张存敬', '攻军统帅'), ('杨约', '被杀祁州刺史')],
      when='900年辛巳，确月主书未另载', place='祁州')
claim('person', people['杨约'], 'death_year', '杨约于900年祁州陷时被杀。', 20,
      '辛巳，拔祁州，杀刺史杨约。', '年与干支承主书；不补具体刑杀程序。')
extra(old_liang, 'event', 'event_zztj_262_0900_zhang_takes_twenty_cities', 'time_original',
      '《旧五代史》梁纪将张存敬北攻瀛莫等置十一月，主书前列甲寅及冬十月景莫。',
      '十一月，以張存敬為上將，自甘陵發軍，北侵幽、薊，連拔瀛、莫二郡',
      20, 'conflicts', '不同月序与攻城范围可能统叙，未强定两次北伐；主书20城数未由该句证实。')
extra(old_tang_september, 'event', 'event_zztj_262_0900_zhang_diverts_due_mud', 'description',
      '《旧唐书》本纪记张存敬下郡邑二十后因雨泥不能至幽州，遂西陷祁州。',
      '下郡邑二十，阻雨泥濘，不及幽州。遂西行陷祁州',
      20, 'corroborates', '二十郡邑与主书二十城语词略异；雨泞改道同。')

event('zhu_youqian_baoyi', '朱友谦由保义留后任节度使', 21, Q[21]['text'],
      [('朱友谦', '受任保义节度使者')], when='900年癸未；确月主书未另载', place='保义军',
      note='复用899年朱简改名朱友谦同一主体；保义留后转节度。')

# Dingzhou: debate, battle, flight, succession, negotiation, reprisals and relief.
event('wang_gao_sends_chuzhi', '王郜遣王处直率军拒张存敬', 22,
      '义武节度使王郜遣后院都知兵马使王处直将兵数万拒之。',
      [('王郜', '遣拒者'), ('王处直', '率义武军者'), ('张存敬', '受拒汴军将')],
      when='900年张存敬攻定州时；确日未载', place='定州',
      note='“数万”为主书记数，未精确。')
event('chuzhi_proposes_defense_liangwen_opposes', '王处直请依城栅待敌师老，梁汶主张迎战', 22,
      '处直请依城为栅，俟其师老而击之。孔目官梁汶曰：“昔幽、镇兵三十万攻我，于时我军不满五千，一战败之。今存敬兵不过三万，我军十倍于昔，奈何示怯，欲依城自固乎！”',
      [('王处直', '请依城防守者'), ('梁汶', '反对守城的孔目官')],
      when='900年定州迎战前；确日未载', place='定州',
      note='兵数三十万、三万及十倍均为梁汶说辞，不当客观清点。')
event('chuzhi_sandriver_defeat', '王处直依王郜命沙河逆战大败', 22,
      '郜乃遣处直逆战于沙河，易定兵大败，死者过半，馀众拥处直奔还。',
      [('王郜', '决命迎战者'), ('王处直', '率军败归者'), ('张存敬', '汴军对手')],
      when='900年定州战；确日未载', place='沙河',
      note='死者过半为主书战后概数；不把此前梁汶自称兵数反推精确死亡人数。')
event('wang_gao_flees_chuzhi_later', '王郜甲申奔晋阳，军推王处直为留后', 22,
      '甲申，王郜弃城奔晋阳，军中推处直为留后。',
      [('王郜', '弃城奔晋阳者'), ('王处直', '军中推举留后')],
      when='900年甲申；确月主书未另载', place='定州、晋阳',
      note='军推留后与朝廷节度使正式授命分开；晋阳是王郜目的地。')
event('zhang_sieges_ding_zhu_arrives', '张存敬围定州，朱全忠丙申至城下', 22,
      '存敬进围定州，丙申，硃全忠至城下，',
      [('张存敬', '围城者'), ('朱温', '至定州城下者')],
      when='900年甲申后、丙申朱至；确月未另载', place='定州',
      note='张围城与朱到城下先后有别。')
event('chuzhi_negotiates_zhu', '王处直与朱全忠城上交涉并获许改图', 22,
      '对曰：“吾兄与晋王同时立勋，封疆密迩，且婚姻也，修好往来，乃常理耳，请从兹改图。”全忠许之。',
      [('王处直', '城上答辩及请改图者'), ('朱温', '准其改图者'), ('李克用', '王处直提及的晋王')],
      when='900年丙申朱到定州城下后；确日未另载', place='定州',
      note='婚姻仅为王处直陈述其兄与晋王两家关联；未具婚配双方，不建直接配偶关系。')
event('liangwen_clan_killed_tribute', '王处直归罪梁汶并族之，以缯帛十万犒朱军', 22,
      '乃归罪于梁汶而族之，以谢全忠，以缯帛十万犒师。',
      [('王处直', '族梁汶并犒军者'), ('梁汶', '被族杀者'), ('朱温', '受谢犒者')],
      when='900年定州议和后；确日未载', place='定州',
      note='族之含梁汶亲族惩罚，不造无名家属；十万为主书记数，旧唐作二十万。')
claim('person', people['梁汶'], 'death_year', '梁汶于900年定州议和后被族杀。', 22,
      '乃归罪于梁汶而族之', '族杀由主书明载；不补其他族人姓名。')
event('zhu_withdraws_petitions_chuzhi', '朱全忠撤军并为王处直表求节钺', 22,
      '全忠乃还，仍为处直表求节钺。',
      [('朱温', '撤军及表请者'), ('王处直', '被表请授节者')],
      when='900年定州犒军后；确日未载', place='定州',
      note='表求节钺是申请，不写此句朝廷已制授；王处直此前仅军推留后。')
person('王处存', 22, '王处直同母兄长')
kin_brother = 'relationship_person_王处直_person_王处存_弟弟'
B['person_relationships'].append(dict(key=kin_brother, person_a_key=people['王处直'],
    person_b_key=people['王处存'], relation_type='弟弟', description='王处直是王处存的同母弟弟。', status='draft'))
claim('person_relationship', kin_brother, 'description', '王处直是王处存的同母弟弟。', 22,
      '处直，处存之母弟也。', '母弟明示同母与长幼；方向为王处直—弟弟→王处存。')
event('liu_shouguang_aids_ding', '刘仁恭遣刘守光援定州，军易水', 22,
      '刘仁恭遣其子守光将兵救定州，军于易水之上。',
      [('刘仁恭', '遣援者'), ('刘守光', '率援军营易水者')],
      when='900年王处直与朱议和后条；确日未载', place='易水',
      note='旧资料已有父亲方向稳定关系，不另造反向儿子边；营易水不等于已进入定州。')
event('zhang_ambushes_shouguang', '朱全忠遣张存敬袭刘守光易水军', 22,
      '全忠遣张存敬袭之，杀六万馀人。',
      [('朱温', '遣袭者'), ('张存敬', '袭击者'), ('刘守光', '受袭方')],
      when='900年刘守光军易水后；确日未载', place='易水',
      note='六万余为主书记数，非经独立清点；旧五张传作斩首五万级，异记并列。')
extra(old_tang_september, 'event', 'event_zztj_262_0900_liangwen_clan_killed_tribute', 'description',
      '《旧唐书》记王处直斩梁汶后出缣二十万乞盟，主书记族梁汶、缯帛十万。',
      '王處直斬孔目官梁汶，出縑二十萬乞盟', 22, 'conflicts',
      '十万/二十万、族/斩叙法不同，不静改主书数额；或指不同支付阶段，未有证据不强合。')
extra(new_wang, 'event', 'event_zztj_262_0900_chuzhi_sandriver_defeat', 'description',
      '《新五代史》王处直传记光化三年沙河战败，乱兵逐王郜、推王处直留后。',
      '光化三年，梁兵攻定州，郜遣處直率兵拒之，戰于沙河，為梁兵所敗。兵返入城逐郜，郜出奔晉，亂兵推處直為留後。',
      22, 'corroborates', '与主书战败及推留后同役；新书“逐郜”是补叙，主书仅称郜弃城奔。')

# Prior relief attempt narrated after the Dingzhou battle.
event('wang_gao_requests_hedong', '王郜事先向河东告急', 23,
      '先是王郜告急于河东，', [('王郜', '向河东告急者'), ('李克用', '受告急方')],
      when='先是；定州陷危之前，确日未载', place='河东',
      note='“先是”为倒叙，不排成王郜弃城后才求援。')
event('li_sizhao_takes_huaizhou', '李克用遣李嗣昭三万步骑出太行取怀州', 23,
      '李克用遣李嗣昭将步骑三万下太行，攻怀州，拔之，',
      [('李克用', '遣援者'), ('李嗣昭', '率军取怀州者')],
      when='900年王郜事先告急后；确日未载', place='太行、怀州',
      note='三万为步骑合计主书记数；怀州取后再进河阳。')
event('li_sizhao_attacks_heyang', '李嗣昭进攻河阳坏羊马城', 23,
      '进攻河阳。河阳留后侯言不意其至，狼狈失据，嗣昭坏其羊马城。',
      [('李嗣昭', '进攻坏外城者'), ('侯言', '河阳留后守方')],
      when='900年怀州拔后；确日未载', place='河阳',
      note='坏羊马城是毁外围设施，不写攻陷河阳主城；“狼狈失据”为主书描述。')
event('yan_bao_relief_hedong_withdraws', '阎宝援河阳壕外力战，河东军退', 23,
      '会佑国军将阎宝引兵救之，力战于壕外，河东兵乃退。',
      [('阎宝', '援河阳者'), ('侯言', '受援守将'), ('李嗣昭', '所部退兵统帅')],
      when='900年河阳被攻后；确日未载', place='河阳壕外',
      note='阎宝救援与李嗣昭取怀州不同战场，不写阎直接收复怀州。')
claim('person', people['阎宝'], 'description', '《资治通鉴》记阎宝为郓州人。', 23,
      '宝，郓州人也。', '郓州是史载籍贯称谓，不强换现代出生地坐标。')

# Palace coup planning before the following November action paragraph.
event('eunuchs_fear_after_dao_bi', '道弼景务修死后宦官益惧', 24,
      '及宋道弼、景务修死，宦官益惧。',
      [('景务修', '此前被赐死枢密使')],
      when='900年道弼景务修死后追叙；确日未载',
      note='本段“宋道弼”与本卷第9段“硃道弼”冲突；这里只记宦官恐惧，宋名不自动并入朱或新造同一主体。')
event('liu_jishu_group_plans_deposition', '刘季述王仲先王彦范薛齐偓密谋废昭宗立太子', 24,
      '于是左军中尉刘季述、右宫中尉王仲先、枢密使王彦范、薛齐偓等阴相与谋曰：“主上轻佻多变诈，难奉事；专听任南司，吾辈终罹其祸。不若奉太子立之，尊主上为太上皇，引岐、华兵为援，控制诸籓，谁能害我哉！”',
      [('刘季述', '参与密谋的左军中尉'), ('王仲先', '参与密谋的右宫中尉'),
       ('王彦范', '参与密谋的枢密使'), ('薛齐偓', '参与密谋的枢密使'), ('李杰', '密谋废黜对象')],
      when='900年十一月政变前；确日未载',
      note='“主上轻佻多变诈”是谋者言辞；本段仅密谋，废立实施见后续段，不提前写太子已即位。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17, 25):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='八段连续校核：九月朝廷任免、镇州和议与北攻、桂州战役、易定战线、河东援河阳及宦官废立密谋逐事分录。王镕父子、朱王姻亲、王处直母弟等关系有向；宋/硃道弼本卷异文保留。第24段仅密谋，第25段实施未提前处理。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused | {primary_autumn, old_liang, old_tang_september}), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=262, year=900,
    primary_source_key=primary_autumn, primary_source_keys=[primary_autumn, primary_late],
    paragraphs=[Q[n]['id'] for n in range(17, 25)], next_paragraph=Q[25]['id'],
    coverage='光化三年32段中的第17—24段连续处理；本年累计24/32段，尚未完成。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
