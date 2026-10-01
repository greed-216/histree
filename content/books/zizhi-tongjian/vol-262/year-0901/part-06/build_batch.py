"""Curate Tongjian 262, year 901, consecutive paragraphs 41–48."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 54))
primary_prev = 'tongjian-262-901-nov'
primary = 'tongjian-262-901-yearend'


old_tang_nov = 'jiutangshu-020-901-nov'
old_tang_dec = 'jiutangshu-020-901-dec'


B = {'format_version': 1, 'batch_key': 'zztj-v262-y0901-p041-p048',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_prev, P.parent / 'part-05/sources/library' / primary_prev, '207dc44', '司马光等'),
    (primary, P / 'sources/library' / primary, '67393c4', '司马光等'),
    (old_tang_nov, P.parent / 'part-05/sources/library' / old_tang_nov, '207dc44', '刘昫等'),
    (old_tang_dec, P / 'sources/library' / old_tang_dec, '67393c4', '刘昫等'),
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
for n in range(41, 49):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/262.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅', '李存审': '符存审', '李继昭':'孙德昭', '李继诲':'周承诲', '李彦弼':'董彦弼', '吉谏':'王宗黯', '李继徽':'杨崇本'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_262_0901_06_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷262·天复元年（901）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷262天复元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
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
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_262_0901_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_262_0901_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 41: Han Jian and Huazhou. Skip the damaged words after Zhang Jun's advice.
event('zhu_returns_chishui', '朱全忠闻昭宗西行后回兵赤水',41,
      '硃全忠至零口西，闻车驾西幸，与僚佐议，复引兵还赤水。',
      [('朱温','回兵者')],when='901年十一月昭宗西行后',place='零口、赤水')
event('zhang_jun_advises_against_han', '张浚劝朱全忠先取韩建',41,
      '左仆射至仕张浚说全忠曰：“韩建，茂贞之党，不先取之，必为后患。',
      [('张浚','劝进者'),('朱温','听劝者'),('韩建','被指需先取者')],
      when='901年朱军回赤水后',
      note='“茂贞之党”“必为后患”是张浚判断；紧接有疑损字，不依其构造具体战事。')
event('zhu_executes_li_juchuan', '朱全忠责韩建并以画策为由斩李巨川',41,
      '全忠以巨川常为建画策，斩之军门。',
      [('朱温','下令斩者'),('李巨川','被斩者'),('韩建','被指受其画策者')],
      when='901年十一月丁巳前；确日未载',place='华州军门',
      note='原文韩建自称表章书檄皆李巨川所为，是其答辩；不作无争议的责任认定。')
claim('person',people['李巨川'],'death_year','李巨川于901年被朱全忠斩于军门。',41,
      '全忠以巨川常为建画策，斩之军门。','本年十一月条，确日未单列。')
event('han_jian_zhongwu', '韩建丁巳调任忠武节度使理陈州',41,
      '丁巳，以建为忠武节度使，理陈州，以兵援送之',
      [('韩建','受调任者')],when='901年十一月丁巳',place='陈州',
      note='主书写朝廷任职并送往，不把韩建留守华州。')
event('li_cun_huazhou', '前商州刺史李存权知华州',41,
      '以前商州刺史李存权知华州',
      [('李存','权知华州者')],when='901年十一月丁巳',place='华州',
      note='“李存权知”断为人名李存、职务权知；该名与李存审等不得合并。')
event('zhao_xu_kuangguo', '赵珝改任匡国节度使',41,
      '徙忠武节度使赵珝为匡国节度使。',
      [('赵珝','改任者')],when='901年十一月丁巳',place='匡国军')
event('zhu_takes_huazhou_revenue', '朱全忠取韩建华州所征商税',41,
      '车驾之在华州也，商贾辐凑，韩建重征之，二年，得钱九百万缗。至是，全忠尽取之。',
      [('韩建','此前征税者'),('朱温','取其税钱者')],
      when='901年韩建离华州时；此前征税两年',place='华州',
      note='二年为追述征税时长，不写902年；九百万缗是主书所记两年所得。')

# 42–43: officials urge Zhu to go west, then the emperor reaches Fengxiang.
event('cui_petitions_zhu_west', '崔胤使卢渥等二百余人列状请朱全忠西迎驾',42,
      '崔胤使太子太师卢渥等二百馀人列状请硃全忠西迎车驾',
      [('崔胤','组织列状者'),('卢渥','列状者'),('朱温','受请者')],
      when='901年十一月昭宗西行后',
      note='二百余为列状人员合数；其余未具名不造人物。')
event('wang_pu_meets_zhu_chishui', '崔胤遣王溥至赤水与朱全忠计事',42,
      '又使王溥至赤水见全忠计事。',
      [('崔胤','遣使者'),('王溥','赴赤水者'),('朱温','会见者')],
      when='901年十一月',place='赤水')
event('zhu_leaves_chishui', '朱全忠复书后戊午发赤水',42,
      '全忠复书曰：“进则惧胁君之谤，退则怀负国之惭，然不敢不勉。”戊午，全忠发赤水。',
      [('朱温','复书并出发者')],when='901年十一月戊午',place='赤水',
      note='胁君、负国为朱全忠书中的自陈，不作其动机已获证实。')
event('lu_guangqi_provisional', '卢光启辛酉权句当中书事',43,
      '辛酉，以兵部侍郎卢光启权句当中书事。',
      [('卢光启','暂摄中书事者')],when='901年十一月辛酉',
      note='权句当为暂摄，非正式授同平章事。')
event('emperor_reaches_fengxiang', '昭宗车驾留岐山三日后壬戌至凤翔',43,
      '车驾留岐山三日，壬戌，至凤翔。',
      [('李杰','车驾抵凤翔者')],when='901年十一月壬戌到达；此前留岐山三日',place='岐山、凤翔')

# 44–47: Zhu at Chang'an, competing letters, Wugong battle, Fengxiang standoff.
event('zhu_received_changan', '朱全忠至长安受百官长乐坡迎候',44,
      '硃全忠至长安，宰相帅百官班迎于长乐坡。明日行，复班辞于临皋驿。',
      [('朱温','受迎辞者')],when='901年十一月昭宗至凤翔后',place='长乐坡、临皋驿',
      note='主书未逐名宰相，不把全部百官造人。')
event('zhu_rewards_sun_dezhao', '朱全忠奖孙德昭，孙献兵八千',44,
      '全忠赏李继昭之功，初令权知匡国留后，复留为两街制置使，赐与甚厚，继昭尽献其兵八千人。',
      [('朱温','奖赏者'),('孙德昭','受赏献兵者')],
      when='901年朱全忠至长安后',place='长安',
      note='李继昭=孙德昭；两次任职先后分明，八千人为献兵数，不与第38段六十余守宅兵混同。')
event('zhu_envoys_claim_secret_order', '朱全忠遣李择裴铸入奏自称奉密诏',44,
      '全忠使判官李择、裴铸入奏事，称：“奉密诏及得崔胤书，令臣将兵入朝。”',
      [('朱温','遣使自称奉诏者'),('李择','入奏者'),('裴铸','入奏者'),('崔胤','书信被提及者')],
      when='901年十一月',place='凤翔',
      note='奉密诏是朱方陈述，不能据此独证密诏真伪。')
event('han_replies_with_edict', '韩全诲等以诏答称密诏崔胤伪作',44,
      '韩全诲等矫诏答以：“朕避灾至此，非宦官所劫，密诏皆崔胤诈为之，卿宜敛兵归保土宇。”',
      [('韩全诲','矫诏答者'),('崔胤','被指诈为密诏者'),('朱温','受答者')],
      when='901年朱使入奏后',place='凤翔',
      note='主书称矫诏；非被劫、密诏诈为为该答诏说法，与强迫西行的主书叙述并置。')
event('kang_huaizhen_breaks_fu', '李茂贞遣符道昭屯武功，康怀贞癸亥击破',44,
      '茂贞遣其将符道昭屯武功以拒全忠，癸亥，全忠将康怀贞击破之。',
      [('李茂贞','遣屯者'),('符道昭','屯武功者'),('朱温','遣将者'),('康怀贞','击破者')],
      when='901年十一月癸亥',place='武功')
event('lu_guangqi_joins_state', '卢光启丁卯任右谏议大夫参知机务',45,
      '丁卯，以卢光启为右谏议大夫，参知机务。',
      [('卢光启','受任者')],when='901年十一月丁卯')
event('zhu_camps_fengxiang', '朱全忠戊辰至凤翔城东扎营',46,
      '戊辰，硃全忠至凤翔，军于城东。',
      [('朱温','扎营者')],when='901年十一月戊辰',place='凤翔城东')
event('maozhen_zhu_exchange_accusations', '李茂贞朱全忠隔城争辩昭宗西行责任',46,
      '李茂贞登城谓曰：“天子避灾，非臣下无礼，谗人误公至此。”全忠报曰：“韩全诲劫迁天子，今来问罪，迎扈还宫。岐王苟不预谋，何烦陈谕！”',
      [('李茂贞','登城辩解者'),('朱温','回应者'),('韩全诲','被朱指为劫迁者')],
      when='901年十一月戊辰',place='凤翔城',
      note='双方均为当事人说法；“非臣下无礼”“迎扈还宫”不可直接视为无争议事实。')
event('emperor_orders_zhu_return', '昭宗屡诏朱全忠还镇，朱辞后趋邠州',46,
      '上屡诏全忠还镇，全忠乃拜表奉辞。辛未，移兵北趣邠州。',
      [('李杰','屡诏者'),('朱温','表辞并移兵者')],
      when='901年十一月辛未移兵',place='凤翔至邠州',
      note='诏还镇与实际移兵邠州区分，不写已归汴。')
event('cui_yin_demoted', '崔胤甲戌责授工部尚书',47,
      '甲戌，制：守司空兼门下侍郎、同平章事崔胤责授工部尚书',
      [('崔胤','受责降者')],when='901年十一月甲戌')
event('pei_shu_chancellorship_ended', '裴枢甲戌罢同平章守户部侍郎',47,
      '户部侍郎、同平章事裴枢罢守本官。',
      [('裴枢','罢相守本官者')],when='901年十一月甲戌')

# 48: Binzhou, Jinyang support, and the December fighting at Zhouzhi.
event('zhu_attacks_binzhou', '朱全忠乙亥攻邠州',48,
      '乙亥，硃全忠攻邠州。',
      [('朱温','攻城者')],when='901年十一月乙亥',place='邠州')
event('yang_chongben_surrenders_restores_name', '李继徽丁丑请降并复名杨崇本',48,
      '丁丑，静难节度使李继徽请降，复姓名杨崇本。',
      [('杨崇本','请降复姓名者')],when='901年十一月丁丑',place='邠州',
      note='复用已发布杨崇本，李继徽是旧赐名，不新建人物。')
claim('person',people['杨崇本'],'aliases','杨崇本于901年请降后复姓名，先前名李继徽。',48,
      '李继徽请降，复姓名杨崇本。','两个姓名指同一已发布主体。')
event('zhu_holds_yang_wife', '朱全忠质杨崇本妻于河中并令其仍镇邠州',48,
      '全忠质其妻于河中，令崇本仍镇邠州。',
      [('朱温','质妻并令留镇者'),('杨崇本','妻被质且留镇者')],
      when='901年十一月丁丑降后',place='河中、邠州',
      note='妻未具名，不造具体人名；留镇与人质两项动作分明。')
event('maozhen_asks_keyong_aid', '韩全诲李茂贞诏征河东兵，李茂贞再书求援',48,
      '韩全诲、李茂贞以诏命征兵河东，茂贞仍以书求援于李克用。',
      [('韩全诲','以诏征兵者'),('李茂贞','征兵并致书者'),('李克用','受求援者')],
      when='901年朱全忠西入关时',
      note='征兵诏命与李茂贞书信为求援行动，须与实际出兵分开。')
event('li_sizhao_defeats_bian', '李克用遣李嗣昭五千骑趋晋州，平阳北败汴兵',48,
      '克用遣李嗣昭将五千骑自沁州趣晋州，与汴兵战于平阳北，破之。',
      [('李克用','遣兵者'),('李嗣昭','率军获胜者')],
      when='901年十一月朱西入关后',place='沁州、晋州、平阳北',
      note='五千为李嗣昭所将骑兵，不外推敌我总兵数。')
event('zhu_leaves_bin_reaches_sanyuan', '朱全忠乙亥离邠州、戊寅至三原',48,
      '乙亥，全忠发邠州。戊寅，次三原。',
      [('朱温','移军者')],when='901年十一月乙亥离邠、戊寅至三原',place='邠州、三原',
      note='与本段前一乙亥攻邠州分属不同干支轮次，保留原顺序不强合一日。')
event('cui_reaches_sanyuan_dec', '崔胤十二月癸未至三原促朱全忠迎驾',48,
      '十二月，癸未，崔胤至三原见全忠，趣之迎驾。',
      [('崔胤','促迎驾者'),('朱温','会见者')],when='901年十二月癸未',place='三原',
      note='旧唐书本纪此事作十二月己卯，日期异说并列。')
event('zhu_youning_fails_zhouzhi', '朱全忠遣朱友宁攻盩厔未下',48,
      '乙丑，全忠遣硃友宁攻盩厔，不下。',
      [('朱温','遣兵者'),('朱友宁','进攻未克者')],when='901年十二月乙丑',place='盩厔')
event('zhu_takes_zhouzhi_massacre', '朱全忠戊戌督战，盩厔降后被屠',48,
      '戊戌，全忠自往督战，盩厔降，屠之。',
      [('朱温','督战并屠城一方主帅')],when='901年十二月戊戌',place='盩厔',
      note='主书未具屠杀人数，不造具体伤亡；先降后屠顺序明确。')
event('cui_moves_capital_residents', '朱全忠令崔胤率百官与京城居民迁华州',48,
      '全忠令崔胤帅百官及京城居民悉迁于华州。',
      [('朱温','下令者'),('崔胤','受令率迁者')],
      when='901年十二月盩厔降后',place='京师至华州')
event('pei_zhi_palace_custodian', '朝廷以裴贽充大明宫留守',48,
      '诏以裴贽充大明宫留守。',
      [('裴贽','受任留守者')],when='901年十二月',place='大明宫')

extra(old_tang_nov,'event','event_zztj_262_0901_han_jian_zhongwu','description',
      '《旧唐书》本纪记韩建出降后被署忠武军节度使，以陈州为治。',
      '韓建出降，乃署為忠武軍節度使，以陳州為理所',41,'corroborates',
      '同受职与治所，旧唐叙朱署任，主书作丁巳制授，保留程序差别。')
extra(old_tang_nov,'event','event_zztj_262_0901_zhu_envoys_claim_secret_order','description',
      '《旧唐书》本纪也记朱方称得崔胤书奉密诏迎驾。',
      '得崔胤書，言奉密詔令臣以兵士迎駕',44,'corroborates',
      '印证朱方有此陈述，不据两书确认密诏真实性。')
extra(old_tang_dec,'event','event_zztj_262_0901_cui_reaches_sanyuan_dec','time_original',
      '《旧唐书》作十二月己卯崔胤至三原砦；《通鉴》作癸未。',
      '十二月己卯，崔胤自長安至三原砦',48,'conflicts',
      '保留日期异记，未用历法强行校正。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,49):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='第41—48段连续校核：韩建调任与李巨川被斩、百官请迎驾、昭宗至凤翔、汴岐对峙、邠州与盩厔战事。张浚语后疑损不释；密诏真伪各方说法并列；十二月崔胤至三原旧唐日期异记并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=262,year=901,
    primary_source_key=primary_prev,primary_source_keys=[primary_prev,primary],
    paragraphs=[Q[n]['id'] for n in range(41,49)],next_paragraph=Q[49]['id'],
    coverage='天复元年53段中的第41—48段连续处理；本年尚未完成。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
