"""Curate Tongjian 263, year 902, consecutive paragraphs 49–59."""
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
primary = 'tongjian-263-902-winter'
primary_late = 'tongjian-263-902-yearend'
old_five = 'jiuwudaishi-002-902-fengxiang'
new_tang = 'xinwudaishi-041-luguangchou-battle'
new_five_xu = 'xinwudaishi-067-902-xu-wan'

B = {'format_version': 1, 'batch_key': 'zztj-v263-y0902-p049-p059',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-06/sources/library' / primary, 'd7ab9ff', '司马光等'),
    (primary_late, P / 'sources/library' / primary_late, '6cba60d', '司马光等'),
    (old_five, P.parent / 'part-04/sources/library' / old_five, '648c8e6', '薛居正等'),
    (new_tang, P / 'sources/library' / new_tang, '6cba60d', '欧阳修等'),
    (new_five_xu, P.parent / 'part-04/sources/library' / new_five_xu, '648c8e6', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, primary_late)}
for n in range(49, 60):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/263.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅', '李存审': '符存审', '李继昭':'符道昭', '王万弘':'李继密', '王宗播':'许存', '刘夫人':'刘夫人（李克用妻）', '曹氏':'曹氏（李存勖母）', '李继诲':'周承诲', '李彦弼':'董彦弼', '吉谏':'王宗黯', '李继徽':'杨崇本', '杜建微':'杜建徽', '傅璙':'钱传璙', '传璙':'钱传璙', '彦询':'彦询（李茂贞假子）', '周彝':'李茂勋', '传瓘':'钱传瓘', '传球':'钱传球', '延昌':'卢延昌', '陟':'刘陟', '进忠':'邓进忠', '进思':'邓进思', '继昭':'符道昭', '传镠':'钱传瓘', '硃郁':'朱郁', '硃敖':'朱敖'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_263_0902_07_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_263_0902_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 49: the raid on Fu and Fang and the winter famine around Fengxiang.
event('zhu_orders_fu_fang_raid', '朱全忠乘李茂勋离镇遣孔勍李晖袭鄜坊',49,
      '硃全忠遣其将孔勍、李晖将兵乘虚袭鄜、坊。',
      [('朱温','遣将者'),('孔勍','领兵者'),('李晖','领兵者')],place='鄜州、坊州',
      note='乘虚是主书对时机的判断；实际攻克分别后录。')
event('bian_takes_fangzhou', '汴军壬子攻取坊州',49,'壬子，拔坊州。',
      [('孔勍','汴军领兵者'),('李晖','汴军领兵者')],when='902年十一月壬子',place='坊州',
      note='本段前句只合称两将领兵，未细分谁单独取坊州。')
event('bian_takes_fuzhou', '汴军甲寅乘雪入鄜州并俘李继璙',49,
      '甲寅，大雪，汴军冒之夕进，五鼓，抵庸阝州城下。鄜人不为备，汴军入城，城中兵尚八千人，格斗至午，鄜人始败，擒留守李继璙。',
      [('孔勍','汴军领兵者'),('李晖','汴军领兵者'),('李继璙','被俘留守')],
      when='902年十一月甲寅',place='鄜州',
      note='底本有“庸阝州”疑损字；由同句“鄜人”及旧五代史“鄜州平”识别为鄜州，摘录保留损字。八千为城中兵数。')
event('li_hui_acts_fuzhou', '汴军安抚鄜州并命李晖权知军府',49,
      '就抚存李茂勋及将士之家，按堵无扰，命李晖权知军府事。茂勋闻之，引兵遁去。',
      [('李晖','权知军府者'),('李茂勋','闻讯退走者')],place='鄜州',
      note='史载安抚对象及退兵；不推断全部家属实际安全。')
event('fengxiang_winter_famine', '凤翔围城冬季大雪断粮并出现严重饥馑',49,
      '是冬，大雪，城中食尽，冻馁死者不可胜计',
      [('李茂贞','守城方'),('李杰','困城皇帝')],when='902年冬',place='凤翔',
      note='“不可胜计”是史载定性，不换算人数；同段疑字C061处不作具体伤害方式。')
event('emperor_sells_clothes', '昭宗出售御衣与小皇子衣以充用',49,
      '上鬻御衣及小皇子衣于市以充用，削渍松梯以饲御马。',
      [('李杰','变卖御衣者')],when='902年冬',place='凤翔',
      note='照录主书记述的困窘，不推定具体售价。')

event('wei_yifan_dies', '韦贻范丙子去世',50,'丙子，户部侍郎、同平章事韦贻范薨。',
      [('韦贻范','去世者')],when='902年冬丙子；月待核',
      note='前段有“是冬”总述；此处未重标月份，干支照录，不推定十一月。')
event('zhu_cuts_forage', '朱全忠癸亥命人除城外草以困凤翔',51,
      '癸亥，硃全忠遣人薙城外草以困城中。',
      [('朱温','下令者')],when='902年冬癸亥；月待核',place='凤翔城外')
event('maozhen_guards_palace_gate', '李茂贞甲子增兵守宫门',51,
      '甲子，李茂贞增兵守宫门，诸宦官自度不免，互相尤怨。',
      [('李茂贞','增守者')],when='902年冬甲子；月待核',place='凤翔宫门',
      note='宦官互相尤怨是主书叙述；未逐一落实到个人。')

event('su_jian_proposes_han_wo', '苏检向李茂贞等建议韩偓入相而被拒',52,
      '苏检数为韩偓经营入相，言于茂贞及中尉、枢密，且遣亲吏告偓，偓怒曰',
      [('苏检','推荐者'),('韩偓','拒绝者'),('李茂贞','受建议者')],place='凤翔',
      note='韩偓怒拒见原文；推荐不记为实际入相。')
event('tian_jun_pressures_hangzhou', '田頵攻杭州并备舟拟自西陵渡江',52,
      '田頵急攻杭州，仍具舟将自西陵渡江。',
      [('田頵','攻城及备渡者')],place='杭州、西陵',
      note='“将”是计划，不记作已渡江。')
event('qian_defeats_tian_crossing', '钱镠遣盛造朱郁击退田頵渡江军',52,
      '钱镠遣其将盛造、硃郁拒破之。',
      [('钱镠','遣将者'),('盛造','拒敌将领'),('硃郁','拒敌将领')],place='西陵',
      note='援引上句西陵渡江语境；底本“硃”规范人物名朱郁。')

event('li_maoxun_surrenders_renamed', '李茂勋十二月请降朱全忠并改名周彝',53,
      '十二月，李茂勋遣使请降于硃全忠，更名周彝。',
      [('李茂勋','请降及改名者'),('朱温','受降者')],when='902年十二月',place='鄜州、凤翔',
      note='同人改名，不另建周彝；第47段旧五代史已以周彝记其率兵。')
event('maozhen_isolated_fengxiang', '李茂贞失山南关中州镇而守凤翔',53,
      '于是茂贞山南州镇皆入王建，关中州镇皆入全忠，坐守孤城。',
      [('李茂贞','失外镇者'),('王建','得山南州镇者'),('朱温','得关中州镇者')],place='凤翔',
      note='“皆入”是主书概括，不据此生成逐州归属或疆域边界。')
event('maozhen_zhu_exchange_letters', '李茂贞致书朱全忠提议诛宦官迎驾，朱回书',53,
      '乃密谋诛宦官以自赎，遗全忠书曰：“祸乱之兴，皆由全诲。仆迎驾至此，以备他盗。公既志匡社稷，请公迎扈还宫，仆以弊甲雕兵，从公陈力。”全忠复书曰：“仆举兵至此，正以乘舆播迁；公能协力，固所愿也。”',
      [('李茂贞','致书者'),('朱温','回书者'),('韩全诲','被指责者')],when='902年十二月',place='凤翔',
      note='书信中的祸因与动机属当事人说法；诛宦官此时仍是密谋。')

# 54–55: Tian Jun's withdrawal, hostages, and unrest south of the Yangtze.
event('yang_recalls_tian_jun', '杨行密以更换宣州主帅相促召田頵还镇',54,
      '杨行密使人召田頵曰：“不还，吾且使人代镇宣州。”',
      [('杨行密','召还者'),('田頵','被召者')],when='902年十二月',place='宣州、杭州',
      note='威胁改任为引语；未记为实际换帅。')
event('tian_jun_demands_payment_hostage', '田頵庚辰索犒军钱二十万缗并要求钱氏子为质',54,
      '庚辰，頵将还，征犒军钱二十万缗于钱镠，且求镠子为质，将妻以女。',
      [('田頵','索款索质者'),('钱镠','受索者')],when='902年十二月庚辰',place='杭州',
      note='“征”是田頵要求，未据此断言钱款足额交付；将妻以女为约定。')
event('qian_chuanqiu_refuses_hostage', '钱传球拒绝前往田頵营为质',54,
      '镠欲遣幼子传球，传球不可。镠怒，将杀之。',
      [('钱镠','欲遣其子者'),('传球','拒绝者')],when='902年十二月庚辰前后',place='杭州',
      note='“将杀之”是意图，未记为已经杀害。')
event('qian_chuanguan_volunteers_hostage', '钱传瓘请代弟赴田頵营并缒城而出',54,
      '次子传瓘请行，吴夫人泣曰：“奈何置儿虎口！”传镠曰：“纾国家之难，安敢爱身！”再拜而出，镠泣送之。传瓘从数人缒北门而下。',
      [('传瓘','自请赴质者'),('钱镠','父及送行者'),('吴夫人','忧子者')],
      when='902年十二月庚辰前后',place='杭州北门',
      note='“传镠曰”疑为转录讹字，按前后文理解为传瓘说话但逐字保留；吴夫人是否其生母未据此断定。')
event('tian_xu_xu_withdraw_xuanzhou', '田頵与徐绾许再思同归宣州',54,
      '頵与徐绾、许再思同归宣州。',
      [('田頵','回宣州者'),('徐绾','随归者'),('许再思','随归者')],when='902年十二月庚辰后',place='宣州',
      note='杭州之围解除与回宣州相连，但本句未明示各军具体撤退时刻。')
event('qian_removes_chuanqiu_seal', '钱镠夺钱传球内牙兵印',54,
      '镠夺传球内牙兵印。',
      [('钱镠','夺印者'),('传球','被夺印者')],when='902年十二月',place='杭州')

event('zhang_hong_flees_quzhou', '张洪率三百步兵奔衢州并获陈璋收纳',55,
      '越州客军指挥使张洪以徐绾之党自疑，帅步兵三百奔衢州，刺史陈璋纳之。',
      [('张洪','率兵投奔者'),('陈璋','收纳者'),('徐绾','被视同党者')],place='衢州',
      note='“自疑”为张洪的自我判断，不据此断定其确为徐绾党羽。')
event('ding_zhang_seizes_wenzhou', '丁章逐朱敖据温州，朱敖奔福州',55,
      '温州将丁章逐刺史硃敖，敖奔福州。章据温州',
      [('丁章','驱逐并据州者'),('硃敖','被逐刺史')],place='温州、福州',
      note='硃敖规范写朱敖；不推定其到福州后职务。')
event('chen_zhang_allows_tian_envoy', '陈璋允许田頵使者往返衢州，钱镠不满',55,
      '田頵遣使招之，道出衢州。陈璋听其往还，钱镠由是恨璋。',
      [('田頵','遣使者'),('陈璋','允许往返者'),('钱镠','不满者'),('丁章','被招者')],place='衢州',
      note='钱镠之“恨”据主书，不外推后续惩处。')

# 56–57: court deliberation and Fu Daozhao's defection.
event('emperor_meets_fengxiang_leaders', '昭宗丁酉召李茂贞等商议与朱全忠和解',56,
      '丁酉，上召李茂贞、苏检、李继诲、李彦弼、李继岌、李继远、李继忠食，议与硃全忠和',
      [('李杰','召议者'),('李茂贞','被召议者'),('苏检','被召议者'),('李继诲','被召议者'),('李彦弼','被召议者'),('李继岌','被召议者'),('李继远','被召议者'),('李继忠','被召议者')],
      when='902年十二月丁酉',place='凤翔',
      note='只记议和与皇帝催促，正式和解仍见后续。')
event('fengxiang_troops_confront_han_quanhui', '凤翔兵责骂韩全诲，李茂贞与昭宗调解',57,
      '凤翔兵十馀人遮韩全诲于左银台门，喧骂曰：“阖境涂炭，阖城馁死，正为军容辈数人耳！”全诲叩头诉于茂贞，茂贞曰：“卒辈何知！”命酌酒两杯，对饮而罢。又诉于上，上亦谕解之。',
      [('韩全诲','受责者'),('李茂贞','调解者'),('李杰','调解者')],place='凤翔左银台门',
      note='士兵将灾祸归咎韩全诲等，是其责骂内容，不作为客观单一因果。')
event('fu_daozhao_defects', '李继昭斥韩全诲后投朱全忠并复姓名苻道昭',57,
      '李继昭谓全诲曰：“昔杨军容破杨守亮一族，今军容亦破继昭一族邪！”慢骂之，遂出降于全忠，复姓苻，名道昭。',
      [('李继昭','投降及复名者'),('韩全诲','被斥者'),('朱温','受降者')],place='凤翔',
      note='李继昭与苻道昭为同一人，沿用既有稳定key；不据引语推定杨守亮族具体命运。')

# 58–59: the Lingnan campaign and Yuezhou succession.
event('lu_guangchou_takes_shaozhou', '卢光稠攻取韶州并使子卢延昌守城',58,
      '是岁，虔州刺史卢光稠攻岭南，陷韶州，使其子延昌守之，进围潮州。',
      [('卢光稠','攻取及任子守城者'),('延昌','守韶州者')],when='902年是岁；确月未载',place='韶州、潮州',
      note='同句记继续围潮州，未断定取潮州。')
event('liu_yin_reliefs_chaozhou', '刘隐击退卢光稠围潮州军后转攻韶州',58,
      '清海留后刘隐发兵击走之，乘胜进攻韶州。',
      [('刘隐','领兵反攻者'),('卢光稠','被击退方')],when='902年是岁；确月未载',place='潮州、韶州')
event('liu_yin_fails_shaozhou', '刘隐围韶州遇江涨断饷，谭全播设伏使其败还',58,
      '会江涨，馈运不继，光稠自虔州引兵救之。其将谭全播伏精兵万人于山谷，以羸弱挑战，大破隐于城南，隐奔还。',
      [('刘隐','围城后败还者'),('卢光稠','领援者'),('谭全播','设伏者')],
      when='902年是岁；确月未载',place='韶州城南',
      note='前句“隐下从”疑转录问题，只据明确的围城、江涨、伏击、败还记录。新五代史把对手写刘巖并叙不同攻城脉络，另列异说。')
event('tan_quanbo_yields_merit', '谭全播将战功让诸将，卢光稠益重之',58,
      '全播悉以功让诸将，光稠益贤之。',
      [('谭全播','让功者'),('卢光稠','赏识者')],when='902年是岁；确月未载',place='韶州')
event('deng_jinsi_dies_jinzhong_succeeds', '岳州刺史邓进思去世，弟邓进忠自称刺史',59,
      '岳州刺史邓进思卒，弟进忠自称刺史。',
      [('邓进思','去世者'),('进忠','自称刺史的弟弟')],when='902年是岁；确月未载',place='岳州',
      note='“自称”不等于朝廷任命；姓名邓进忠由同句“弟”承接，待其他书证核。')

# Explicit kinship, with A being B's named relation. Reuse the 907 stable relation.
qian_chuanguan_rel = next(r for r in json.loads((ROOT/'content/year-0907/content-batch.json').read_text())['person_relationships']
                         if r['key']=='relationship_person_钱镠_person_钱传瓘_父亲')
B['person_relationships'].append(dict(qian_chuanguan_rel, status='draft'))
claim('person_relationship',qian_chuanguan_rel['key'],'description','钱镠是钱传瓘的父亲。',54,
      '次子传瓘请行','“次子”承上文钱镠诸子；复用907年既有关系key和端点。')
for rel,a,b,kind,n,quote,desc in [
    ('relationship_person_钱镠_person_钱传球_父亲','钱镠','钱传球','父亲',54,'镠欲遣幼子传球','钱镠是钱传球的父亲。'),
    ('relationship_person_卢光稠_person_卢延昌_父亲','卢光稠','卢延昌','父亲',58,'使其子延昌守之','卢光稠是卢延昌的父亲。'),
    ('relationship_person_邓进思_person_邓进忠_兄长','邓进思','邓进忠','兄长',59,'邓进思卒，弟进忠自称刺史','邓进思是邓进忠的兄长。'),
]:
    B['person_relationships'].append(dict(key=rel,person_a_key=people[a],person_b_key=people[b],
        relation_type=kind,description=desc,status='draft'))
    claim('person_relationship',rel,'description',desc,n,quote,'原文明示亲属及长幼；关系方向为A是B的该关系。')

extra(old_five,'event','event_zztj_263_0902_bian_takes_fuzhou','description',
      '《旧五代史》亦记朱全忠遣孔勍袭鄜州，甲寅鄜州平。',
      '翼日，帝以周彝既離本部，鄜畤必無守備，因命孔勍乘虛襲下之。甲寅，鄜州平。',49,
      'corroborates','旧五以周彝为李茂勋别名；主书的损字“庸阝州”据上下文识别鄜州。')
extra(new_five_xu,'event','event_zztj_263_0902_tian_xu_xu_withdraw_xuanzhou','description',
      '《新五代史》记杨行密召田頵还，田頵收钱并质元瓘而归。',
      '亟召頵還。頵取鏐錢百萬，質鏐子元瓘而歸',54,
      'adds','主书索二十万缗、以传瓘为质；新五写钱百万、元瓘，数额与名异文并列，未强行换算。')
extra(new_tang,'person',people['谭全播'],'description',
      '《新五代史》另记谭全播曾设山谷伏兵败刘巖。',
      '乃選精兵萬人，伏山谷中',58,'adds',
      '该传所记对手为刘巖、地点脉络不同于主书902年刘隐攻韶州；不认作同一战事或据此改主书。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(49,60):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷263天复二年第49—59段连续处理；疑损字、姓名异文及不同史书战事脉络见review.md。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=263,year=902,
    primary_source_key=primary,primary_source_keys=[primary,primary_late],
    paragraphs=[Q[n]['id'] for n in range(49,60)],next_paragraph='zztj-v263-y0903-p001',
    coverage='卷263天复二年共59个非空段落中的第49—59段连续处理；本卷本年段落至此全部覆盖，下一年仍在卷263。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
