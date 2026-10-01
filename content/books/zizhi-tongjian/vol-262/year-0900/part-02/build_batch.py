"""Curate Tongjian 262, year 900, consecutive paragraphs 9–16."""
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
primary_summer = 'tongjian-262-900-spring'
primary_autumn = 'tongjian-262-900-autumn'
old_liang = 'jiuwudaishi-002-900-dezhou'
old_ge = 'jiuwudaishi-016-900-ge'
old_tang_june = 'jiutangshu-020-900-wang-tuan'
old_tang_july = 'jiutangshu-020-900-july'
old_tang_september = 'jiutangshu-020-900-xu'
B = {'format_version': 1, 'batch_key': 'zztj-v262-y0900-p009-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_summer, P.parent / 'part-01/sources/library' / primary_summer, 'bb575ad', '司马光等'),
    (old_liang, P.parent / 'part-01/sources/library' / old_liang, 'bb575ad', '薛居正等'),
    (primary_autumn, P / 'sources/library' / primary_autumn, '9c06dec', '司马光等'),
    (old_ge, P / 'sources/library' / old_ge, '9c06dec', '薛居正等'),
    (old_tang_june, P / 'sources/library' / old_tang_june, '9c06dec', '刘昫等'),
    (old_tang_july, P / 'sources/library' / old_tang_july, '9c06dec', '刘昫等'),
    (old_tang_september, P / 'sources/library' / old_tang_september, '9c06dec', '刘昫等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_summer, primary_autumn)}
for n in range(9, 17):
    assert Q[n]['text'] in ''.join(primary_texts.values()), (n, Q[n]['text'][:30])

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '硃道弼': '朱道弼', '硃绍宗': '朱绍宗',
           '薛王知柔': '李知柔', '镕': '王镕', '上': '李杰'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and Q[n]['text'] in data)

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_262_0900_02_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_262_0900_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# The long ninth paragraph is a chronology, not a single purge event.
event('cui_mulls_eunuch_removal', '崔胤与昭宗谋去宦官，南北司相倾', 9,
      '崔胤日与上谋去宦官，宦官知之。由是南、北司益相憎嫉，各结籓镇为援以相倾夺。',
      [('崔胤', '谋去宦官者'), ('李杰', '参与谋议的昭宗')], when='900年王抟罢相前；确日未载',
      note='“上”为昭宗；结藩镇为互相援引的史书概述，不推出各方具体结盟清单。')
event('wang_tuan_advises_emperor', '王抟劝昭宗慎除宦官并勿泄言', 9,
      '抟恐其致乱，从容言于上曰：“人君当务明大体，无所偏私。宦官擅权之弊，谁不知之！顾其势未可猝除，宜俟多难渐平，以道消息。愿陛下言勿轻泄以速奸变。”',
      [('王抟', '进谏者'), ('李杰', '受谏者')], when='900年王抟罢相前；确日未载',
      note='王抟所言为谏议，不等于王已成为宦官外应。')
event('cui_accuses_wang', '崔胤诬王抟为宦官外应', 9,
      '胤闻之，谮抟于上曰：“王抟奸邪，已为道弼辈外应。”上疑之。',
      [('崔胤', '谮奏者'), ('王抟', '被指控者'), ('李杰', '疑忌者')],
      when='900年崔胤出镇前追叙；确日未载', note='主书明确“谮”，指控不当王抟实际与宦官结盟。')
event('cui_requests_zhu_memorial', '崔胤赴广州途中致书朱全忠，请其表论王抟', 9,
      '及出镇广州，遗硃全忠书，具道抟语，令全忠表论之。',
      [('崔胤', '致书请表者'), ('朱温', '受书者'), ('王抟', '被论者')],
      when='900年崔胤出镇广州途中；确日未载', place='赴广州途中',
      note='“出镇广州”是赴任过程，紧接复召；不写已经到达广州。')
event('zhu_memorials_for_cui', '朱全忠接连上表要求崔胤留相并指王抟', 9,
      '全忠上言：“胤不可离辅弼之地，抟与敕使相表里，同危社稷。”表连上不已。',
      [('朱温', '连续上表者'), ('崔胤', '被请求留相者'), ('王抟', '被奏指者')],
      when='900年崔胤出镇途中；确日未载',
      note='抟与敕使相表里是朱奏词，不作为已经核实的人物关系。')
event('emperor_recalls_cui_hunan', '昭宗迫于朱全忠复召崔胤', 9,
      '上虽察其情，迫于全忠，不得已，胤至湖南复召还。',
      [('李杰', '复召者'), ('崔胤', '被复召者'), ('朱温', '施压者')],
      when='900年崔胤行至湖南后；确日未载', place='湖南',
      note='昭宗察情但被迫召还为主书叙述，不写崔到广州后召。')
event('cui_restored_wang_dismissed', '崔胤复任相，王抟罢为工部侍郎', 9,
      '丁卯，以胤为司空、门下侍郎、同平章事，抟罢为工部侍郎。',
      [('崔胤', '复任者'), ('王抟', '罢相者')], when='900年六月丁卯',
      note='丁卯承前段六月；王抟先罢工部侍郎，后续再贬，不合为一步。')
event('eunuchs_sent_monitor', '朱道弼与景务修分赴荆南青州监军', 9,
      '以道弼监荆南军，务修监青州军。',
      [('朱道弼', '赴荆南监军者'), ('景务修', '赴青州监军者')],
      when='900年六月丁卯后；确日未另载', place='荆南、青州',
      note='道弼姓承前“硃道弼”；旧唐本纪作宋道弼，身份待校，不静改主书。')
event('wang_tuan_demoted_twice', '王抟先贬溪州刺史再贬崖州司户', 9,
      '戊辰，贬抟溪州刺史；己巳，又贬崖州司户。',
      [('王抟', '两次被贬者')], when='900年六月戊辰、己巳', place='溪州、崖州',
      note='为连续两日两次贬职，不写王抟曾实际抵任两地。')
event('eunuchs_exiled_order', '朱道弼与景务修分别长流欢州爱州', 9,
      '道弼长流欢州，务修长流爱州。',
      [('朱道弼', '长流欢州者'), ('景务修', '长流爱州者')],
      when='900年六月己巳前后；确日未单列', place='欢州、爱州',
      note='流放命令与随后赐自尽分开；不写两人已到流放地。')
event('wang_eunuchs_executed', '王抟朱道弼景务修同日赐自尽', 9,
      '是日，皆赐自尽。抟死于蓝田驿，道弼、务修死于霸桥驿。',
      [('王抟', '赐自尽于蓝田驿'), ('朱道弼', '赐自尽于霸桥驿'), ('景务修', '赐自尽于霸桥驿')],
      when='900年六月己巳', place='蓝田驿、霸桥驿',
      note='是日承己巳；二驿分人，不误以三人同地死亡。')
for name in ('王抟', '朱道弼', '景务修'):
    claim('person', people[name], 'death_year', f'{name}于900年六月己巳赐自尽。', 9,
          '是日，皆赐自尽。抟死于蓝田驿，道弼、务修死于霸桥驿。',
          '是日承己巳；死亡地点按王抟蓝田驿、道弼务修霸桥驿区分。')
extra(old_tang_june, 'person', people['朱道弼'], 'description',
      '《旧唐书》本纪同案记“宋道弼”，主书作“硃道弼”；姓氏冲突，身份待校。',
      '樞密使宋道弼、景務修並死。', 9, 'conflicts',
      '同景务修及王抟赐死案，但宋/硃姓不同；仅记候选同人异文，不设置宋道弼别名。')
extra(old_tang_june, 'event', 'event_zztj_262_0900_wang_eunuchs_executed', 'description',
      '《旧唐书》记王抟贬崖州司户后寻赐死蓝田驿，与主书死亡地点合。',
      '王摶貶崖州司戶，尋賜死于藍田驛', 9, 'corroborates',
      '旧唐“寻”不支持精确己巳同日，只支持前后次序和蓝田驿地点。')

event('liu_ren_gong_to_cang', '刘仁恭率幽州兵五万救沧营乾宁军', 10,
      '刘仁恭将幽州兵五万救沧州，营于乾宁军。',
      [('刘仁恭', '率兵救沧者')], when='900年六月后、七月前条；确日未载', place='乾宁军',
      note='五万为主书记数；旧五梁纪作六月来援，与主书段内月序并列。')
event('ge_defeats_liu_laoyadi', '葛从周留张存敬氏叔琮守寨并在老鸦堤败刘仁恭', 10,
      '葛从周留张存敬、氏叔琮守沧州寨，自将精兵逆战于老鸦堤，大破仁恭，斩首三万级，仁恭走保瓦桥。',
      [('葛从周', '迎击获胜者'), ('张存敬', '留守沧州寨者'), ('氏叔琮', '留守沧州寨者'), ('刘仁恭', '败走瓦桥者')],
      when='900年刘仁恭救沧后、七月前条；确日未载', place='沧州寨、老鸦堤、瓦桥',
      note='三万为主书记首级数；旧五梁纪万余与葛传三万异记，并列不平均。')
extra(old_liang, 'event', 'event_zztj_262_0900_ge_defeats_liu_laoyadi', 'description',
      '《旧五代史》梁纪称六月老鸦堤大破刘仁恭军，杀万余、俘马慎交等百余。',
      '六月，燕帥劉仁恭大舉來援，從周與諸將逆戰于乾寧軍老鴉堤，大破之，殺萬餘眾，俘其將佐馬慎交已下百餘人。',
      10, 'conflicts', '主书斩首三万与梁纪杀万余统计或叙法不一；不推定二次老鸦堤战。')
extra(old_ge, 'event', 'event_zztj_262_0900_ge_defeats_liu_laoyadi', 'description',
      '《旧五代史》葛从周传记老鸦堤斩首三万、获将佐马慎交以下百余及马三千匹。',
      '從周逆戰於乾寧軍老鴉堤，大破燕軍，斬首三萬，獲將佐馬慎交已下百餘人，奪馬三千匹。',
      10, 'adds', '主书记斩首三万与此传一致；马和俘获为传文补叙，未写为独立第二役。')
event('li_sizhao_july_aid', '李克用再遣李嗣昭五万兵攻邢洺救刘仁恭', 10,
      '秋，七月，李克用复遣都指挥使李嗣昭将兵五万攻邢、洺以救仁恭，',
      [('李克用', '再遣救援者'), ('李嗣昭', '率军攻邢洺者'), ('刘仁恭', '受援方')],
      when='900年秋七月', place='邢州、洺州',
      note='“复遣”与前五月周德威五千骑不同轮；五万为主书记数。')
event('li_sizhao_neiqiu_victory', '李嗣昭于内丘败汴军', 10,
      '败汴军于内丘。', [('李嗣昭', '破汴军者')], when='900年秋七月', place='内丘',
      note='句承李嗣昭率军，不写刘仁恭在内丘亲战。')
event('wang_rong_mediates_ge_recalled', '王镕遣使调解幽汴，久雨后朱全忠召葛从周还', 10,
      '镕遣使和解幽、汴，会久雨，硃全忠召从周还。',
      [('王镕', '遣使调解者'), ('朱温', '召还葛从周者'), ('葛从周', '被召还者')],
      when='900年秋七月李嗣昭内丘胜后；确日未载', place='幽州、汴州之间',
      note='“镕”承王镕；和解为遣使尝试，不写双方已签盟，召还与久雨同条不独断单一原因。')

event('meng_qian_zhaoyi', '孟迁由昭义留后任节度使', 11, Q[11]['text'],
      [('孟迁', '受任节度使者')], when='900年秋七月庚戌', place='昭义军',
      note='主书节度使概称；旧唐有副大使、知节度事等制词官衔细节。')
extra(old_tang_july, 'event', 'event_zztj_262_0900_meng_qian_zhaoyi', 'description',
      '《旧唐书》制词记孟迁为昭义节度副大使、知节度事，并兼潞州大都府长史。',
      '庚戌，制昭義節度留後、光祿大夫、檢校司空、上柱國孟遷為檢校司徒，兼潞州大都府長史，充昭義節度副大使、知節度事、潞磁邢洺等州觀察處置使',
      11, 'adds', '书证官衔细于主书“节度使”，同庚戌，不另造第二次任命。')

event('wang_jian_east_sichuan_command', '王建兼东川信武两道都指挥制置等使', 12, Q[12]['text'],
      [('王建', '受兼东川信武两道职者')], when='900年秋七月甲寅', place='东川、信武军',
      note='只记兼制置职，不由此推两军所有城池已当天受控。')
extra(old_tang_july, 'event', 'event_zztj_262_0900_wang_jian_east_sichuan_command', 'description',
      '《旧唐书》制词记王建兼剑南东川、武信军两道都指挥制置等使，加食邑一千户。',
      '王建可兼劍南東川、武信軍兩道都指揮制置等使，加食邑一千戶，餘如故。',
      12, 'adds', '旧唐作乙卯，主书甲寅，干支日异记并列；职名近同，不静改主书日期。')
extra(old_tang_july, 'event', 'event_zztj_262_0900_wang_jian_east_sichuan_command', 'time_original',
      '《旧唐书》七月乙卯制王建兼东川武信两道职，主书作甲寅。',
      '乙卯，制忠烈衛聖鎮國功臣、劍南西川節度副大使、知節度事、管內營田觀察處置統押近界諸蠻兼西山八國雲南安撫制置等使、開府儀同三司、檢校太尉、中書令、成都尹、上柱國、琅邪郡王、食邑三千戶、實封一百戶王建可兼劍南東川、武信軍兩道都指揮制置等使', 12, 'conflicts',
      '旧唐日期乙卯与主书甲寅相差一天；保两书记载，不以换算推唯一日。')

event('li_sizhao_shamenhe_attack_ming', '李嗣昭八月沙门河再败汴军并攻洺州', 13,
      '八月，李嗣昭又败汴军于沙门河，进攻洺州。',
      [('李嗣昭', '击败汴军及攻洺者')], when='900年八月；确日未载', place='沙门河、洺州')
event('zhu_moves_to_aid_ming', '朱全忠引兵救洺州', 13,
      '乙丑，硃全忠引兵救之，未至，', [('朱温', '引兵救洺者')],
      when='900年八月乙丑', place='洺州方向', note='“未至”为关键限制，不写朱亲率军已抵洺州。')
event('li_sizhao_takes_ming_zhu_shaocaptured', '李嗣昭拔洺州擒朱绍宗', 13,
      '嗣昭拔洺州，擒刺史硃绍宗。', [('李嗣昭', '拔洺及擒刺史者'), ('朱绍宗', '被擒洺州刺史')],
      when='900年八月乙丑朱全忠援军未至时', place='洺州',
      note='主书以李嗣昭为擒者；旧五梁纪称李进通袭陷，身份异说待考，不并为两次陷城。')
event('zhu_orders_ge_against_li', '朱全忠命葛从周击李嗣昭', 13,
      '全忠命葛从周将兵击嗣昭。', [('朱温', '命击者'), ('葛从周', '受命将兵者'), ('李嗣昭', '被击对象')],
      when='900年八月洺州陷后；确日未载', place='洺州方向',
      note='命令与下段九月青山口战果分开，不提前写已击败。')
extra(old_liang, 'event', 'event_zztj_262_0900_li_sizhao_takes_ming_zhu_shaocaptured', 'description',
      '《旧五代史》梁纪记八月河东李进通袭陷洺州、执朱绍宗，主书作李嗣昭拔城。',
      '八月，河東遣李進通襲陷洺州，執刺史朱紹宗。', 13, 'conflicts',
      '同月同城同刺史，但李进通与李嗣昭名称不同；未核身份，不设置两人为别名或造第二次陷城。')

event('kang_ru_retreats_qingxi', '康儒军食尽，自清溪撤归', 14, Q[14]['text'],
      [('康儒', '军食尽撤归者')], when='900年八月条；确日未载', place='清溪',
      note='接年初睦州战线，主书未言钱銶在清溪直接获胜；食尽为撤退缘由。')

event('ge_crosses_zhang_huanglong', '葛从周渡漳水营黄龙镇', 15,
      '九月，葛从周自鄴县渡漳水，营于黄龙镇。', [('葛从周', '率军渡漳营镇者')],
      when='900年九月；确日未载', place='鄴县、漳水、黄龙镇')
event('zhu_crosses_mingwater', '朱全忠率中军三万涉洺水置营', 15,
      '硃全忠自将中军三万涉洺水置营。', [('朱温', '中军统帅')],
      when='900年九月；确日未载', place='洺水', note='三万为主书记数，不当其全部攻洺军。')
event('li_abandons_ming', '李嗣昭弃洺州撤军', 15, '李嗣昭弃城走，',
      [('李嗣昭', '弃洺州撤退者')], when='900年九月朱军涉洺水后；确日未载', place='洺州',
      note='城承上文洺州；不据此写所部已被消灭。')
event('ge_ambush_qingshankou', '葛从周青山口设伏击败李嗣昭', 15,
      '从周设伏于青山口，邀击，大破之。',
      [('葛从周', '设伏邀击者'), ('李嗣昭', '撤军受击者')],
      when='900年九月李嗣昭弃洺后；确日未载', place='青山口',
      note='旧五葛传补斩首五千，不将青山口误作五月老鸦堤之战。')
extra(old_liang, 'event', 'event_zztj_262_0900_ge_crosses_zhang_huanglong', 'description',
      '《旧五代史》梁纪记葛从周自鄴县渡漳水屯黄龙镇。',
      '八月，河東遣李進通襲陷洺州，執刺史朱紹宗。帝遣葛從周自鄴縣渡漳水，屯於黃龍鎮', 15, 'corroborates',
      '梁纪将此置八月条，主书列九月，月序差异保留。')
extra(old_ge, 'event', 'event_zztj_262_0900_ge_ambush_qingshankou', 'description',
      '《旧五代史》葛传记青山口追袭斩首五千、获王郃郎杨师悦等。',
      '從周追襲至青山口，斬首五千級，獲其將王郃郎、楊師悅等', 15, 'adds',
      '葛传未在此句独载九月，主书为九月；王郃郎与899年魏州被擒同名，暂不合并生平。')

event('xu_yanruo_requests_qinghai', '徐彦若求出镇广州代李知柔', 16,
      '惟嗣薛王知柔在广州，乃求代之。',
      [('徐彦若', '求代清海者'), ('李知柔', '被请求替代的嗣薛王')],
      when='900年九月乙巳前；确日未载', place='广州',
      note='徐自求离朝，主书另述崔胤恶其位高；不单定崔必然强制外放。')
event('xu_yanruo_qinghai_appointed', '徐彦若同平章事充清海节度使', 16,
      '乙巳，以彦若同平章事，充清海节度使。',
      [('徐彦若', '受任清海节度使者')], when='900年九月乙巳', place='清海军',
      note='与二月崔胤清海任命先后分期，不写两人同日到广州。')
extra(old_tang_september, 'event', 'event_zztj_262_0900_xu_yanruo_qinghai_appointed', 'description',
      '《旧唐书》制词记徐彦若乙巳任清海军节度、岭南东道观察处置使。',
      '乙巳，制扶危匡國致理功臣、開府儀同三司、守太保、兼門下侍郎、平章事，充太清宮使、修奉太廟使、弘文館大學士、延資庫使、諸道鹽鐵轉運等使、上柱國、齊國公、食邑五千戶、食實封一百戶徐彥若可檢校太尉、同平章事，充清海軍節度、嶺南東道管內觀察處置供軍糧料等使。', 16, 'corroborates',
      '制词同乙巳与清海职衔，未据此推徐彦若已到广州。')
event('cheng_rui_repeated_petition', '成汭屡求澧朗复隶荆南，朝廷不许', 16,
      '初，荆南节度成汭以澧、朗本其巡属，为雷满所据，屡求割隶荆南。朝廷不许，汭颇怨望。',
      [('成汭', '屡次请割者'), ('雷满', '据澧朗者')],
      when='初；确年未定，900年前追叙', place='澧州、朗州、荆南', year=None,
      note='“初”追叙，确年不定；屡求与不许不硬塞900年九月，也不补具体第一次请求日。')
event('cheng_rui_questions_xu', '徐彦若经荆南与成汭议澧朗归属', 16,
      '及彦若过荆南，汭置酒，从容以为言。彦若曰：“令公位尊方面，自比桓、文，雷满小盗不能取，乃怨朝廷乎？”汭甚惭。',
      [('徐彦若', '经荆南回应者'), ('成汭', '设宴重提归属者'), ('雷满', '被徐谈及者')],
      when='900年徐彦若赴清海途中；确日未载', place='荆南',
      note='徐言“雷满小盗”为人物言辞，不当站点客观评价；谈话不代表朝廷已准割地。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9, 17):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='八段连续校核：王抟崔胤与宦官处分、老鸦堤与内丘战、孟迁王建授官、洺州争夺、康儒撤军及徐彦若出镇分录。旧唐宋/硃道弼、王建甲寅/乙卯、旧五李进通/李嗣昭及战果数异说保留；“初”追叙确年不定。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused | {primary_summer, old_liang}), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=262, year=900,
    primary_source_key=primary_summer, primary_source_keys=[primary_summer, primary_autumn],
    paragraphs=[Q[n]['id'] for n in range(9, 17)], next_paragraph=Q[17]['id'],
    coverage='光化三年32段中的第9—16段连续处理；本年累计16/32段，尚未完成。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
