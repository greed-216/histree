"""Curate Tongjian 265, year 906, consecutive paragraphs 25–32."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 43))
primary = 'tongjian-265-906-autumn'
old_cangzhou = 'jiuwudaishi-002-cangzhou'
old_li = 'jiuwudaishi-026-li-sizhao'
new_qinpei = 'xinwudaishi-061-qinpei-jiangxi'
new_liu = 'xinwudaishi-039-liurengong'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0906-p025-p032',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P / 'sources/library' / primary, '10d699bc', '司马光等'),
    (old_cangzhou, P / 'sources/library' / old_cangzhou, '10d699bc', '薛居正等'),
    (old_li, P.parent / 'part-02/sources/library' / old_li, '04b02541', '薛居正等'),
    (new_qinpei, P.parent / 'part-03/sources/library' / new_qinpei, 'd7ae356f', '欧阳修等'),
    (new_liu, P / 'sources/library' / new_liu, '10d699bc', '欧阳修等'),
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
for n in range(25, 33):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '裴':'秦裴', '渥':'杨渥', '仁恭':'刘仁恭', '守文':'刘守文', '克用':'李克用', '存勖':'李存勖', '知俊':'刘知俊', '崇本':'杨崇本'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0906_04_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐三年（906）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷265天祐三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=906, time_quote=None):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0906_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '906年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '906年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0906_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0906_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 25–26: Arrival at Cangzhou and the Jiangxi conquest are independent fronts.
event('zhu_crosses_baima_reaches_changlu', '朱全忠辛亥渡白马、丁卯至长芦攻沧州', 25,
      '九月，辛亥朔，硃全忠自白马渡河，丁卯，至沧州，军于长芦，沧人不出。',
      [('朱温','率军渡河并驻长芦者')],
      when='906年九月辛亥朔自白马渡河；丁卯至长芦',place='白马、沧州长芦',
      note='渡河与抵长芦有不同干支；沧人闭城不出，不写成沧州已陷。')
event('luo_supplies_cangzhou_army', '罗绍威为沧州行军持续供应物资', 25,
      '罗绍威馈运，自魏至长芦五百里，不绝于路。又建元帅府舍于魏，所过驿亭供酒馔、幄幕、什器，上下数十万人，无一不备。',
      [('罗绍威','供应军需并建府舍者')],
      when='906年朱全忠驻长芦期间；确日未载',place='魏州至长芦',
      note='五百里与数十万人均为主书概数，不据此推定精确后勤规模。')
event('qin_pei_takes_hongzhou', '秦裴取洪州并俘钟匡时', 26,
      '秦裴拔洪州，虏钟匡时等五千人以归。',
      [('秦裴','攻取洪州者'),('钟匡时','被俘者')],
      when='906年九月条；确日未载',place='洪州',
      note='主书“等五千人”含钟匡时与其他被俘者；《新五代史》另记九月攻克。')
event('yang_wo_assumes_zhennan_appoints_qin', '杨渥兼镇南节度使、任秦裴洪州制置使', 26,
      '杨渥自兼镇南节度使，以裴为洪州制置使。',
      [('杨渥','自兼镇南节度使者'),('秦裴','获洪州制置使者')],
      when='秦裴克洪州后；确日未载',place='洪州',
      note='两项授职在攻克之后；不补写具体诏命或实际就任日期。')

event('yang_chongben_attacks_xiazhou', '杨崇本合诸军攻夏州', 27,
      '静难节度使杨崇本以凤翔、保塞、彰义、保义之兵攻夏州',
      [('杨崇本','领军攻夏州者')],when='906年九月条；确日未载',place='夏州',
      note='这里仅记录进攻，不预断夏州被攻克。')
event('liu_zhijun_hits_fangzhou_force', '刘知俊邀击坊州兵并擒刘彦晖', 27,
      '匡国节度使刘知俊邀击坊州之兵，斩首三千馀级，擒坊州刺史刘彦晖。',
      [('刘知俊','邀击者'),('刘彦晖','被擒的坊州刺史')],
      when='杨崇本攻夏州时；确日未载',place='坊州兵行进途中',
      note='三千余级为主书所记战果，不把刘彦晖被俘记成死亡。')

# 28: Liu Rengong's first coercive order was revised before the mass levy.
event('liu_rengong_first_mass_levy_order', '刘仁恭初令境内成年男子自备粮械赴营', 28,
      '乃下令境内：“男子十五以上，七十以下，悉自备兵粮诣行营，军发之后，有一人在闾里，刑无赦！”',
      [('刘仁恭','下令征发者')],when='906年救沧州屡败后；确日未载',
      note='这是初令及刑罚威胁；后文经人进谏改为能执兵者尽行，不当作原令完全施行。')
event('liu_rengong_revises_levy_tattoos_troops', '刘仁恭改征能执兵者并黥文后军于瓦桥', 28,
      '乃命胜执兵者尽行，文其面曰“定霸都”，士人则文其腕或臂曰“一心事主”，于是境内士民，稚孺之外无不文者。得兵十万，军于瓦桥。',
      [('刘仁恭','改令征兵并驻瓦桥者')],when='906年救沧州期间；确日未载',place='瓦桥',
      note='主书记得兵十万，《新五代史》作二十万人；单位均为人，数字异说保留。')

# 29: Siege hardship, the surrender proposal and Liu Shouwen's answer are separate.
event('bian_army_blockades_cangzhou', '汴军围沧州，城中粮尽', 29,
      '时汴军筑垒围沧州，鸟鼠不能通。仁恭畏其强，不敢战。城中食尽，丸土而食，或互相掠啖。',
      [('刘仁恭','率援军而未与汴军交战者')],
      when='906年九月后；确日未载',place='沧州',
      note='“互相掠啖”为主书记述的围城惨况，无人数；不推断所有城民如此。')
event('zhu_urges_liu_shouwen_surrender', '朱全忠遣人劝刘守文早降', 29,
      '硃全忠使人说刘守文曰：“援兵势不相及，何不早降！”',
      [('朱温','遣使劝降者'),('刘守文','受劝降者')],
      when='沧州受围后；确日未载',place='沧州',
      note='“援兵势不相及”是朱全忠劝降之词，不当成独立核准的战况。')
event('liu_shouwen_refuses_zhu_eases_attack', '刘守文拒降，朱全忠暂缓攻城', 29,
      '守文登城应之曰：“仆于幽州，父子也。梁王方以大义服天下，若子叛父而来，将安用之！”全忠愧其辞直，为之缓攻。',
      [('刘守文','登城答复者'),('朱温','缓攻者')],
      when='朱全忠劝降后；确日未载',place='沧州',
      note='刘守文的话是拒降理由；“缓攻”不等于围城解除。')

event('wang_jian_sets_up_regional_chancellery', '王建丙戌在蜀立行台并称权承制封拜', 30,
      '冬，十月，丙戌，王建始立行台于蜀，建东向舞蹈，号恸，称“自大驾东迁，制命不通，请权立行台，用李晟、郑畋故事，承制封拜。”仍以膀帖告谕所部籓镇州县。',
      [('王建','立行台并宣告承制封拜者')],
      when='906年十月丙戌',place='蜀',
      note='“制命不通”及援引李晟、郑畋为王建公开说法；行台建立和告谕是主书记载的动作。')

# 31: Counsel contains strategic estimates; joint campaign follows the decision.
event('liu_rengong_repeatedly_requests_jin_help', '刘仁恭屡次向河东求救而初未获准', 31,
      '刘仁恭求救于河东，前后百馀辈。李克用恨仁恭返覆，竟未之许',
      [('刘仁恭','多次求援者'),('李克用','起初未许者')],
      when='906年沧州受围期间；确日未载',place='河东',
      note='“百余辈”为使者次数或批次的主书措辞，不推成确切人数。')
event('li_cunxu_advises_jin_liu_alliance', '李存勖劝李克用联合幽沧抗朱全忠', 31,
      '其子存勖谏曰：“今天下之势，归硃温者什七八，虽强大如魏博、镇、定，莫不附之。自河以北，能为温患者独我与幽、沧耳',
      [('李存勖','劝谏者'),('李克用','受谏者'),('朱温','劝谏中所指对手')],
      when='李克用拒绝刘仁恭求援后；确日未载',
      note='什七八等势力估计是李存勖的论证，不作为量化的客观版图。')
event('li_keyong_accepts_liu_alliance', '李克用采纳建议，与刘仁恭和并议攻潞州', 31,
      '克用以为然，与将佐谋召幽州兵与攻潞州，曰：“于彼可以解围，于我可以拓境。”乃许仁恭和，召其兵。',
      [('李克用','采纳并召幽州兵者'),('刘仁恭','获准和好者')],
      when='李存勖进谏后；确日未载',place='河东、幽州',
      note='解围与拓境是李克用表达的预期目标，本段并未记沧州已解围。')
event('li_pu_jin_army_moves_luzhou', '李溥率幽州兵赴晋阳，周德威李嗣昭合兵攻潞州', 31,
      '仁恭遣都指挥使李溥将兵三万诣晋阳，克用遣其将周德威、李嗣昭将兵与之共攻潞州。',
      [('刘仁恭','遣李溥者'),('李溥','率兵赴晋阳者'),('李克用','遣将者'),
       ('周德威','合兵攻潞州者'),('李嗣昭','合兵攻潞州者')],
      when='906年十月后条；确日未载',place='晋阳、潞州',
      note='三万人为主书所载幽州兵数；潞州尚在进攻，降服见后续段落。')

# 32: Xiazhou relief and the Jingnan appointment concern different theatres.
event('zhu_sends_liu_kang_to_xiazhou', '朱全忠戊戌遣刘知俊、康怀英救夏州', 32,
      '夏州告急于硃全忠。戊戌，全忠遣刘知俊及其将康怀英救之。',
      [('朱温','派援者'),('刘知俊','受遣者'),('康怀英','同受遣者')],
      when='906年十月戊戌',place='夏州',
      note='告急与出兵在同句；不推断夏州此时已陷。')
event('liu_zhijun_defeats_yang_chongben', '刘知俊等于美原击败杨崇本', 32,
      '杨崇本将六镇之兵五万，军于美原。知俊等击之，崇本大败，归于邠州。',
      [('杨崇本','驻美原后败退者'),('刘知俊','击败者'),('康怀英','同救夏州者')],
      when='906年十月戊戌后；确日未载',place='美原、邠州',
      note='五万为杨崇本军的主书数字；不据此推定死伤。')
event('gao_jichang_replaces_he_gui_jingnan', '朱全忠以高季昌代贺瑰守荆南', 32,
      '武贞节度使雷彦恭屡寇荆南，留后贺瑰闭城自守。硃全忠以为怯，以颍州防御使高季昌代之',
      [('雷彦恭','多次进攻荆南者'),('贺瑰','守城并被撤换者'),('朱温','作撤换决定者'),('高季昌','获任继代者')],
      when='906年十月后条；确日未载',place='荆南',
      note='“怯”为朱全忠的判断，贺瑰闭城自守是主书记载的行动。')
event('ni_kefu_garrisons_jingnan', '倪可福率兵五千驻防荆南，朗兵引去', 32,
      '又遣驾前指挥使倪可福将兵五千戍荆南以备吴、蜀。朗兵引去。',
      [('朱温','派兵者'),('倪可福','率兵驻防者')],
      when='高季昌代贺瑰后；确日未载',place='荆南',
      note='“朗兵”字样疑与雷彦恭所部有关，按底本原字保留，指代待纸本校核；不写成与吴蜀实际交战。')

extra(old_cangzhou,'event','event_zztj_265_0906_zhu_crosses_baima_reaches_changlu','time_original',
      '《旧五代史》卷二记九月丁卯营于长芦，与主书抵长芦日相合。',
      '九月丁卯，營于長蘆',25,'corroborates',
      '旧书另记八月甲辰复命北征，主书上一批亦记该出兵日。')
extra(new_qinpei,'event','event_zztj_265_0906_qin_pei_takes_hongzhou','description',
      '《新五代史》卷六十一同记九月克洪州、执钟匡时；另记陈象。',
      '九月，克洪州，執匡時及司馬陳象以歸',26,'corroborates',
      '主书称钟匡时等五千人，新书摘录未载五千之数，不作为人数独立证据。')
extra(new_liu,'event','event_zztj_265_0906_liu_rengong_revises_levy_tattoos_troops','description',
      '《新五代史》卷三十九记刘仁恭黥面“定霸都”、兵屯瓦桥，但人数作二十万。',
      '文曰：「定霸都」，得二十萬人，兵糧自具，屯于瓦橋',28,'conflicts',
      '主书作得兵十万；新书作二十万，均保留为书载数字。')
extra(new_liu,'event','event_zztj_265_0906_bian_army_blockades_cangzhou','description',
      '《新五代史》卷三十九亦记沧州受围、城中粮尽。',
      '滄州被圍百餘日，城中食盡',29,'adds',
      '百余日为该书所记时长，主书本段未给围城起讫日，不换算公历。')
extra(old_li,'event','event_zztj_265_0906_li_pu_jin_army_moves_luzhou','description',
      '《旧五代史》李嗣昭传同记幽州刘仁恭求援、三万兵会晋阳、共攻泽潞。',
      '仁恭遣掌書記馬鬱、都指揮使李溥等將兵三萬，會於晉陽',31,'adds',
      '旧书另列马郁，主书只明确李溥率兵；不推定马郁在主书对应句出现。')
extra(old_cangzhou,'event','event_zztj_265_0906_zhu_sends_liu_kang_to_xiazhou','time_original',
      '《旧五代史》卷二记十月辛巳杨崇本来寇及朱全忠命刘知俊、康怀英应敌，主书作戊戌遣援。',
      '十月辛巳，邠州楊崇本以鳳翔、邠、寧、涇、鄜、秦、隴之眾合五六萬來寇',32,'conflicts',
      '两书所记日或对应不同动作；没有证据证明同一遣援日，不强合。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,33):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷265天祐三年第25—32段连续处理；沧州围城、江西归属、征兵异数及并行战场分别记录。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=265,year=906,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph=Q[33]['id'],
    coverage='卷265天祐三年第25—32段连续处理；沧州围城、洪州攻克、夏州战事、刘仁恭征兵、王建行台及河东幽州合兵。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
