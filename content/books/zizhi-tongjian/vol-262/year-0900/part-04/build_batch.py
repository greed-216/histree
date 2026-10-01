"""Curate Tongjian 262, year 900, consecutive paragraphs 25–32."""
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
primary_late = 'tongjian-262-900-late'
primary_coup = 'tongjian-262-900-coup-cont'
primary_yearend = 'tongjian-262-900-yearend'
old_tang_coup = 'jiutangshu-020-900-coup'
old_liang_coup = 'jiuwudaishi-002-900-coup'
new_li_yu = 'xinwudaishi-054-li-yu'
B = {'format_version': 1, 'batch_key': 'zztj-v262-y0900-p025-p032',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_late, P.parent / 'part-03/sources/library' / primary_late, '6baba6f', '司马光等'),
    (old_tang_coup, P.parent / 'part-03/sources/library' / old_tang_coup, '6baba6f', '刘昫等'),
    (primary_coup, P / 'sources/library' / primary_coup, '7db9c9d', '司马光等'),
    (primary_yearend, P / 'sources/library' / primary_yearend, '7db9c9d', '司马光等'),
    (old_liang_coup, P / 'sources/library' / old_liang_coup, '7db9c9d', '薛居正等'),
    (new_li_yu, P / 'sources/library' / new_li_yu, '7db9c9d', '欧阳修'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_late, primary_coup, primary_yearend)}
assert Q[25]['text'][:120] in primary_texts[primary_late]
assert Q[25]['text'][-120:] in primary_texts[primary_coup]
for n in range(26, 33):
    assert Q[n]['text'] in primary_texts[primary_yearend], (n, Q[n]['text'][:30])

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '上': '李杰', '皇后': '何氏（唐昭宗皇后）',
           '太子': '李祐', '希度': '刘希度', '薛王知柔': '李知柔',
           '睦王倚': '李倚', '弟询': '陈询'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data)

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_262_0900_04_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷262·光化三年（900）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote):
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
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote,
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
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_262_0900_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_262_0900_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# The coup paragraph spans two original TXT export blocks. Each citation uses a
# single verbatim excerpt within one block, while the ledger preserves the line.
event('emperor_hunts_and_kills_attendants', '昭宗十一月猎苑饮酒后杀黄门侍女数人', 25,
      '十一月，上猎苑中，因置酒，夜，醉归，手杀黄门、侍女数人。',
      [('李杰', '酒后杀内侍者')], when='900年十一月；确日未载', place='猎苑、宫中',
      note='主书称数人，不造姓名和确数；与后次日宦官破门分开。')
event('liu_jishu_breaks_palace_gate', '刘季述向崔胤称宫中有变并率千禁兵破门', 25,
      '季述诣中书白崔胤曰：“宫中必有变，我内臣也，得以便宜从事，请入视之。”乃帅禁兵千人破门而入，访问，具得其状。',
      [('刘季述', '率禁兵破门者'), ('崔胤', '被告知宰相')],
      when='900年十一月昭宗猎苑归后次日；确日未载', place='宫门',
      note='千人为主书记数；季述“请入视之”是其自称理由，不当朝廷正式授权废立。')
event('liu_forces_ministers_sign', '刘季述庚寅陈兵迫崔胤百官署太子监国状', 25,
      '庚寅，季述召百官，陈兵殿庭，作胤等连名状，请太子监国，以示之，使署名。胤及百官不得已皆署之。',
      [('刘季述', '迫令署状者'), ('崔胤', '被迫署状宰相'), ('李祐', '拟监国太子')],
      when='900年十一月庚寅', place='殿庭',
      note='百官署名是在陈兵压力下，不能当自愿拥立或既已即位。')
event('eunuchs_enter_qiqiaolou', '刘季述王仲先与程岩等率兵入乞巧楼胁昭宗', 25,
      '上在乞巧楼，季述、仲先伏将士千人于门外，与宣武进奏官程岩等十馀人入请对。季述、仲先甫登殿，将士大呼，突入宣化门，至思政殿前，逢宫人，辄杀之。上见兵入，惊堕床下，起，将走，季述、仲先掖之令坐。',
      [('刘季述', '率兵胁迫者'), ('王仲先', '同率兵者'), ('程岩', '宣武进奏官同入者'), ('李杰', '被胁迫昭宗')],
      when='900年十一月庚寅', place='乞巧楼、宣化门、思政殿',
      note='门外千人、入见十余人分别是两个范围；宫人被杀者无名。')
event('queen_gives_seal_transfer', '何皇后交传国宝，昭宗与后移少阳院', 25,
      '后曰：“宅家趣依军容语！”即取传国宝以授季述，宦官扶上与后同辇，嫔御侍从者才十馀人，适少阳院。',
      [('何氏（唐昭宗皇后）', '被迫交传国宝并同辇者'), ('李杰', '被迁昭宗'), ('刘季述', '受传国宝者')],
      when='900年十一月庚寅', place='少阳院',
      note='旧唐书明称何皇后，复用既有同一人；交宝发生武力胁迫中，不作自愿禅让。')
event('liu_confines_emperor', '刘季述锁少阳院并遣李师虔围禁昭宗', 25,
      '乃手锁其门，熔铁锢之，遣左军副使李师虔将兵围之，上动静辄白季述，穴墙以通饮食，凡兵器针刀皆不得入，上求钱帛俱不得，求纸笔亦不与。',
      [('刘季述', '锁门幽禁及命围者'), ('李师虔', '率兵围少阳院者'), ('李杰', '被幽禁者')],
      when='900年十一月庚寅后；确日未另载', place='少阳院',
      note='幽禁与后续太子即位分录；主书称穴墙通饮食，不断言完全断粮。')
event('prince_regency_false_edict', '刘季述等矫诏迎太子李祐监国', 25,
      '季述等矫诏令太子监国，迎太子入宫。',
      [('刘季述', '矫诏者'), ('李祐', '被迎监国太子')],
      when='900年十一月庚寅后；确日未另载', place='宫中',
      note='主书明称矫诏，监国阶段先于辛卯嗣位诏及甲午即位。')
event('prince_renamed_zhen_edict', '辛卯矫诏令太子嗣位更名缜，昭宗后为太上皇后', 25,
      '辛卯，矫诏令太子嗣位，更名缜。以上为太上皇，皇后为太上皇后。',
      [('李祐', '被矫诏更名缜者'), ('李杰', '被尊太上皇者'), ('何氏（唐昭宗皇后）', '被尊太上皇后者')],
      when='900年十一月辛卯',
      note='李祐即897更名裕之太子；“缜”为900短暂改名，稳定key不新建李缜。')
claim('person', people['李祐'], 'aliases', '太子裕于900年十一月辛卯被矫诏更名缜。', 25,
      '辛卯，矫诏令太子嗣位，更名缜。', '复用李祐稳定主体；其897已改名裕，不新造缜主体。')
event('prince_enthroned_jiawu', '甲午太子即位，少阳院改问安宫', 25,
      '甲午，太子即皇帝位，更名少阳院曰问安宫。',
      [('李祐', '被宦官拥立即位者'), ('李杰', '被幽禁于更名院者')],
      when='900年十一月甲午', place='问安宫',
      note='甲午实际即位，不能与庚寅监国、辛卯嗣位矫诏合为同一天。')
event('liu_kills_mu_prince_and_favorites', '刘季述等杀睦王李倚并榜杀昭宗近幸', 25,
      '杀睦王倚，凡宫人、左右、方士、僧、道为上所宠信者，皆榜杀之。',
      [('刘季述', '宦官废立主事方'), ('李倚', '被杀睦王')],
      when='900年十一月甲午后；确日未载',
      note='榜杀受害者多未具名，不造姓名；主书未逐一指认行刑人，刘为主事方而非必亲手杀。')
claim('person', people['李倚'], 'death_year', '睦王李倚于900年废立后被杀。', 25,
      '杀睦王倚', '唐宗室姓李；原文未述具体日期和行刑方式。')
event('hu_xiulin_protests_survives', '胡秀林谏止刘季述继续滥杀', 25,
      '将杀司天监胡秀林，秀林曰：“军容幽囚君父，更欲多杀无辜乎！”季述惮其言正而止。',
      [('胡秀林', '司天监抗言者'), ('刘季述', '因言止杀者')],
      when='900年废立后；确日未载',
      note='此处胡秀林未被杀，勿据“将杀”录死亡年。')
event('cui_demoted_roles_writes_zhu', '崔胤被解度支盐铁职并密书朱全忠求返正', 25,
      '季述等欲杀崔胤，而惮硃全忠，但解其度支监督铁转运使而已。崔胤密致书全忠，使兴兵图返正。',
      [('崔胤', '被解使职并密求朱援者'), ('刘季述', '欲杀崔但未行者'), ('朱温', '收密书求援对象')],
      when='900年废立后；确日未载',
      note='“欲杀”非既杀，崔仍在朝；“返正”为请求，尚未成功。')
extra(old_tang_coup, 'event', 'event_zztj_262_0900_prince_enthroned_jiawu', 'description',
      '《旧唐书》本纪记甲午太子登帝位，昭宗与何皇后被移东宫，皆系刘季述废立。',
      '甲午，宣上皇制，太子登皇帝位', 25, 'corroborates',
      '此摘录支持甲午即位；昭宗何皇后移东宫另见同段前文，不能以此单句扩写移宫细节。')

event('zhang_jun_urges_zhang_quanyi', '张浚见张全义劝匡复并致书诸镇', 26, Q[26]['text'],
      [('张浚', '劝匡复及致书者'), ('张全义', '受劝者')],
      when='900年十一月废立后；确日未载', place='长水、洛阳',
      note='张全义是否响应本段未载，不写起兵成功；诸镇受信者不逐个造人。')
event('li_yu_memorial_han_jian', '李愚上书韩建劝举兵反正', 27,
      '进士无棣李愚客游华州，上韩建书',
      [('李愚', '进士上书者'), ('韩建', '受书者')],
      when='900年昭宗被幽后；确日未载', place='华州',
      note='无棣为史载籍贯，不据此定出生坐标；上书内容为李愚主张。')
event('han_jian_declines_li_leaves', '韩建厚待李愚而未采反正之议，李愚辞去', 27,
      '建虽不能用，厚待之，愚坚辞而去。',
      [('韩建', '未采其议者'), ('李愚', '辞去者')],
      when='900年李愚上书后；确日未载', place='华州',
      note='韩厚待不等于发兵；李愚书中对韩的褒赞属游说之辞。')
extra(new_li_yu, 'event', 'event_zztj_262_0900_li_yu_memorial_han_jian', 'description',
      '《新五代史》李愚传亦记刘季述幽昭宗时李愚以书说韩建图兴复。',
      '劉季述幽昭宗於東內，愚以書說韓建，使圖興復，其言甚壯。建不能用，乃去之洛陽。',
      27, 'corroborates', '人物经历同；传文后去洛阳为补叙，主书只称辞去。')

event('zhu_returns_dingzhou_daliang', '朱全忠闻乱丁未自定州南还，十二月戊辰至大梁', 28,
      '硃全忠在定州行营，闻乱，丁未，南还。十二月，戊辰，至大梁。',
      [('朱温', '闻政变后南还者')],
      when='900年十一月丁未返程，十二月戊辰抵大梁', place='定州、大梁',
      note='丁未为南还，戊辰为至大梁，两时点分明；未写丁未已到汴。')
event('liu_jishu_sends_liu_xidu_offer', '刘季述遣养子刘希度见朱全忠许输唐社稷', 28,
      '季述遣养子希度诣全忠，许以唐社稷输之；',
      [('刘季述', '遣养子者'), ('刘希度', '受遣传言者'), ('朱温', '受许诺者')],
      when='900年朱至大梁后；确日未载', place='大梁',
      note='“许输唐社稷”为刘季述使者承诺，不代表朱已实际受让政权；希度按刘养子姓及旧五代史复核。')
event('li_fengben_delivers_edict', '刘季述遣李奉本持太上皇诰示朱全忠', 28,
      '又遣供奉官李奉本以太上皇诰示全忠。',
      [('刘季述', '遣供奉官者'), ('李奉本', '持诰者'), ('朱温', '受示者')],
      when='900年朱至大梁后；确日未载', place='大梁',
      note='诰为当时废立政权所用文书，不据此认定昭宗自愿禅让。')
event('li_zhen_advises_zhu_restore', '李振劝朱全忠讨刘季述以扶唐室', 28,
      '天平节度副使李振独曰：“王室有难，此霸者之资也。今公为唐桓、文，安危所属。季述一宦竖耳，乃敢囚废天子，公不能讨，何以复令诸侯！且幼主位定，则天下之权尽归宦官矣，是以太阿之柄授人也。”全忠大悟，',
      [('李振', '劝讨刘季述者'), ('朱温', '受劝者')],
      when='900年十二月朱回大梁后；确日未载', place='大梁',
      note='“霸者之资”“权尽归宦官”为李振论说，不当站点的客观政治评判。')
event('zhu_detains_envoys_sends_li_zhen', '朱全忠囚刘希度李奉本，遣李振入京探事', 28,
      '即囚希度、奉本，遣振如京师诇事。',
      [('朱温', '囚使并遣探者'), ('刘希度', '被囚者'), ('李奉本', '被囚者'), ('李振', '入京探事者')],
      when='900年十二月李振劝后；确日未载', place='大梁、京师',
      note='囚禁不等于此时杀；二人在901后续处置待下年段落。')
event('zhu_sends_jiang_summons_cheng', '朱全忠遣蒋玄晖与崔胤谋返正并召程岩赴大梁', 28,
      '即还，又遣亲吏蒋玄晖如京师，与崔胤谋之；又召程岩赴大梁。',
      [('朱温', '遣蒋及召程者'), ('蒋玄晖', '赴京谋议者'), ('崔胤', '京中谋议者'), ('程岩', '被召赴大梁者')],
      when='900年李振自京还后；确日未载', place='京师、大梁',
      note='程岩赴大梁是被召，不在900年写其901被诛后事。')
extra(old_liang_coup, 'event', 'event_zztj_262_0900_liu_jishu_sends_liu_xidu_offer', 'description',
      '《旧五代史》梁纪亦记刘季述遣养子希度向朱全忠表示愿输唐神器。',
      '仍遣其養子希度來言，願以唐之神器輸於帝。',
      28, 'corroborates', '梁纪以梁太祖称帝为追称，不能当900年朱已称帝。')
extra(old_liang_coup, 'event', 'event_zztj_262_0900_li_zhen_advises_zhu_restore', 'description',
      '《旧五代史》梁纪亦记李振从长安归后劝朱全忠讨宦官，朱遣振复使。',
      '會李振自長安使回，因言於帝曰：「夫豎刁、伊戾之亂，所以資霸者之事也。今閹豎幽辱天子，王不能討，無以令諸侯。」帝悟，因請振復使于長安',
      28, 'corroborates', '李振劝说同一政策线，旧书归京后复使次序与主书细节并列。')

event('li_zhirou_dies', '清海节度使薛王李知柔薨', 29, Q[29]['text'],
      [('李知柔', '去世清海节度使')], when='900年末条；确日未载', place='清海军',
      note='复用薛王知柔既有李知柔主体；不推死于广州具体地点。')
claim('person', people['李知柔'], 'death_year', '李知柔于900年去世。', 29,
      '清海节度使薛王知柔薨。', '确年承本年条；薨为史书用语。')
event('yang_xingmi_shizhong', '杨行密加兼侍中', 30, Q[30]['text'],
      [('杨行密', '受加兼侍中者')], when='900年是岁；确月日未载',
      note='是岁仅支持全年，不强填十二月。')
event('chen_sheng_dies', '睦州刺史陈晟卒', 31, '睦州刺史陈晟卒，',
      [('陈晟', '去世睦州刺史')], when='900年是岁条；确月日未载', place='睦州')
claim('person', people['陈晟'], 'death_year', '陈晟于900年去世。', 31,
      '睦州刺史陈晟卒', '确年承是岁条；不补死因。')
event('chen_xun_claims_muzhou', '陈晟弟陈询自称睦州刺史', 31, '弟询自称刺史。',
      [('陈询', '陈晟弟，自称刺史')], when='900年陈晟卒后；确月日未载', place='睦州',
      note='自称不等于朝廷正式授命；弟询承陈晟。')
kin_chen = 'relationship_person_陈询_person_陈晟_弟弟'
B['person_relationships'].append(dict(key=kin_chen, person_a_key=people['陈询'], person_b_key=people['陈晟'],
    relation_type='弟弟', description='陈询是陈晟的弟弟。', status='draft'))
claim('person_relationship', kin_chen, 'description', '陈询是陈晟的弟弟。', 31,
      '睦州刺史陈晟卒，弟询自称刺史。', '“弟询”承陈晟，方向为陈询—弟弟→陈晟。')

event('wang_zhongxian_audits_army', '王仲先钩校两军钱谷并急征隐没积欠', 32,
      '王仲先性苛察，素知左、右军多积弊，及为中尉，钩校军中钱谷，得隐没为奸者，痛捶之，急征所负，将士颇不安。',
      [('王仲先', '钩校与征负者')],
      when='900年太子即位累旬后；确日未载', place='左、右军',
      note='“性苛察”为主书评语；具体隐没将士未名，不一概判有罪。')
event('cui_sends_shi_to_sun', '崔胤遣判官石戬接近孙德昭', 32,
      '有盐州雄毅军使孙德昭为左神策指挥使，自刘季述等废立，常愤惋不平。崔胤闻之，遣判官石戬与之游。',
      [('孙德昭', '左神策指挥使、不平者'), ('崔胤', '遣判官接触者'), ('石戬', '接触孙德昭者')],
      when='900年废立后、除夜前；确日未载', place='京师',
      note='孙不平先于行动；遣游为接触，未到公开举兵阶段。')
event('shi_persuades_sun', '石戬密劝孙德昭诛刘季述王仲先迎昭宗复位', 32,
      '戬知其诚，乃密以胤意说之曰：“自上皇幽闭，中外大臣至于行间士卒，孰不切齿！今反者独季述、仲先耳，公诚能诛此二人，迎上皇复位，则富贵穷一时，忠义流千古；苟狐疑不决，则功落他人之手矣！”',
      [('石戬', '传崔胤意劝说者'), ('孙德昭', '受说者'), ('崔胤', '密谋主使方')],
      when='900年除夜前；确日未载', place='京师',
      note='“今反者独季述仲先”“富贵”等属游说辞；此处仅策划，未录杀人既成事实。')
event('sun_agrees_cui_belt_letter', '孙德昭允从崔胤命，崔胤割衣带手书授之', 32,
      '德昭谢曰：“德昭小校，国家大事，安敢专之！苟相公有命，不敢爱死！”戬以白胤。胤割衣带，手书以授之。',
      [('孙德昭', '表示愿受命者'), ('石戬', '传话者'), ('崔胤', '授手书者')],
      when='900年除夜前；确日未载', place='京师',
      note='割衣带手书为信物/书信动作，不附会具体未载全文。')
event('sun_recruits_dong_zhou_newyear_eve', '孙德昭联董彦弼周承诲谋除夜伏兵安福门', 32,
      '德昭复结右军清远都将董彦弼、周承诲，谋以除夜伏兵安福门外以俟之。',
      [('孙德昭', '联络及筹划者'), ('董彦弼', '右军清远都将参与筹划者'), ('周承诲', '右军清远都将参与筹划者')],
      when='900年除夜前筹划，拟除夜伏兵；实际行动待901年条', place='安福门',
      note='此段只写计划；主书下一年正月乙酉才叙实际擒斩王仲先，不提前记成功。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25, 33):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='八段连续校核：十一月废立从破门、胁署、移宫、幽禁到监国、改名、甲午即位分期；张浚李愚劝复、朱全忠十二月决策、年终死亡任职与孙德昭除夜筹划各据原文。第32段仅谋伏，901年实际复位不提前。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused | {primary_late}), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=262, year=900,
    primary_source_key=primary_late, primary_source_keys=[primary_late, primary_coup, primary_yearend],
    paragraphs=[Q[n]['id'] for n in range(25, 33)], next_paragraph='zztj-v262-y0901-p001',
    coverage='光化三年32段中的第25—32段连续处理；卷262第38—39行转入天复元年（901）。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
