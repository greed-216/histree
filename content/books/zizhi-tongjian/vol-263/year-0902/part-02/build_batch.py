"""Curate Tongjian 263, year 902, consecutive paragraphs 9–16."""
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
primary = 'tongjian-263-902-opening'
primary_court = 'tongjian-263-902-court'
primary_april = 'tongjian-263-902-april'
old_siege = 'jiuwudaishi-026-902-siege'



old_tang = 'jiutangshu-020-902-opening'
old_five = 'jiuwudaishi-002-902-campaign'


B = {'format_version': 1, 'batch_key': 'zztj-v263-y0902-p009-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-01/sources/library' / primary, '2a58915', '司马光等'),
    (primary_court, P / 'sources/library' / primary_court, '352a55e', '司马光等'),
    (primary_april, P / 'sources/library' / primary_april, '352a55e', '司马光等'),
    (old_tang, P.parent / 'part-01/sources/library' / old_tang, '2a58915', '刘昫等'),
    (old_five, P.parent / 'part-01/sources/library' / old_five, '2a58915', '薛居正等'),
    (old_siege, P / 'sources/library' / old_siege, 'af504b1', '薛居正等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, primary_court, primary_april)}
for n in range(9, 17):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/263.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅', '李存审': '符存审', '李继昭':'符道昭', '刘夫人':'刘夫人（李克用妻）', '曹氏':'曹氏（李存勖母）', '李继诲':'周承诲', '李彦弼':'董彦弼', '吉谏':'王宗黯', '李继徽':'杨崇本'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_263_0902_02_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_263_0902_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 9: defeat and debate over defending Jinyang.
event('li_cunxin_retreats_qingyuan', '李存信赴援至清源遇汴军而退晋阳', 9,
      '李克用闻嗣昭等败，遣李存信以亲兵逆之，至清源，遇汴军，存信走还晋阳。',
      [('李克用','遣援者'),('李存信','退军者')], when='902年三月戊午后',place='清源、晋阳')
event('bian_takes_ci_xi_fen', '汴军再取慈隰汾三州', 9,
      '汴军取慈、隰、汾三州。', when='902年三月辛酉前',place='慈州、隰州、汾州',
      note='第4段曾记慈隰为河东所得；此处是汴军再取，不合并为同一控制变更。')
event('bian_besieges_jinyang', '汴军辛酉围晋阳并攻西门', 9,
      '辛酉，汴军围晋阳，营于晋祠，攻其西门。',
      [('氏叔琮','围城主将')],when='902年三月辛酉',place='晋阳、晋祠',
      note='氏叔琮攻城见本段下句；不把汴军围城直接记为破城。')
event('hedong_returns_jinyang', '周德威李嗣昭收余众依西山返晋阳', 9,
      '周德威、李嗣昭收馀众依西山得还。',
      [('周德威','收军者'),('李嗣昭','收军者')],when='902年三月辛酉后',place='晋阳西山')
event('keyong_debates_yunzhou_retreat', '李克用议走云州，诸将与刘夫人主张守晋阳', 9,
      '召诸将议走保云州，李嗣昭、李嗣源、周德威曰：“儿辈在此，必能固守。王勿为此谋摇人心！”',
      [('李克用','召议者'),('李嗣昭','主张守城者'),('李嗣源','主张守城者'),('周德威','主张守城者')],
      when='902年三月围晋阳期间',place='晋阳',
      note='此事为议论，未实际弃城。李存信异议与刘夫人劝止见同段后文。')
claim('event','event_zztj_263_0902_keyong_debates_yunzhou_retreat','description',
      '李存信劝李克用暂入北虏；李嗣昭力争，刘夫人以王行瑜和达靼旧事劝止，李克用最终留晋阳。',9,
      '刘夫人言于克用曰：“存信，北川牧羊儿耳，安知远虑！',
      '只记主书中各方言论及最后未走的结果，不把主张当作执行。')
event('kening_returns_jinyang', '李克宁闻汴军至，半途返回晋阳',9,
      '克用弟克宁为忻州刺史，闻汴寇至，中涂复还晋阳，曰：“此城吾死所也，去将何之！”众心乃定。',
      [('李克宁','回城者'),('李克用','其兄')],when='902年三月围晋阳期间',place='晋阳',
      note='本句明言克宁为克用弟；回城稳定军心，不据此推定其曾率军参战。')
rel='relationship_person_li_keyong_person_李克宁_兄长'
B['person_relationships'].append(dict(key=rel,person_a_key=people['李克用'],person_b_key=people['李克宁'],
    relation_type='兄长',description='《资治通鉴》天复二年条明言李克宁为李克用之弟。',status='draft'))
claim('person_relationship',rel,'description','李克用是李克宁的兄长。',9,
      '克用弟克宁为忻州刺史','原文明示长幼，关系方向为兄长指向弟弟。')

# 10: counterattacks, epidemic, withdrawal and recapture.
event('zhu_returns_hezhong_and_dispatches', '朱全忠壬戌返河中并遣朱友宁西击李茂贞',10,
      '壬戌，硃全忠还河中，遣硃友宁将兵西击李茂贞，军于兴平、武功之间。',
      [('朱温','遣兵者'),('朱友宁','率兵者'),('李茂贞','进攻对象')],when='902年三月壬戌',place='河中、兴平、武功')
event('night_raids_shu_camp', '李嗣昭李嗣源数次夜袭氏叔琮营',10,
      '李嗣昭、李嗣源数将敢死士夜入氏叔琮营，斩首捕虏，汴军惊扰，备御不暇。',
      [('李嗣昭','夜袭者'),('李嗣源','夜袭者'),('氏叔琮','被袭军主将')],
      when='902年三月围晋阳期间',place='晋阳附近')
event('shu_withdraws_epidemic', '汴军疫起，氏叔琮丁卯撤围',10,
      '会大疫，丁卯，叔琮引兵还。',
      [('氏叔琮','撤军者')],when='902年三月丁卯',place='晋阳',
      note='主书记大疫与撤军相接；旧五代史对该役的月份、撤退过程另有异说。')
event('hedong_reoccupies_three_prefectures', '李嗣昭周德威追汴军后复取慈隰汾',10,
      '嗣昭与周德威将兵追之，及石会关，叔琮留数马及旌旗于高冈之巅。嗣昭等以为有伏兵，乃引去，复取慈、隰、汾三州。',
      [('李嗣昭','追击及复取者'),('周德威','追击及复取者'),('氏叔琮','撤军设疑兵者')],
      when='902年三月丁卯后',place='石会关、慈州、隰州、汾州',
      note='追至石会关后因疑伏而引去，再取三州；旧五代史追击杀戮记载不同。')

# 11: policy discussion and family narrative, retaining reported speech.
event('keyong_seeks_policy', '李克用就粮储兵甲城池向幕府征议',11,
      '克用以使引咨幕府曰：“不贮军食，何以聚众？不置兵甲，何以克敌？不修城池，何以扞御？利害之间，请垂议度。”',
      [('李克用','征议者')],when='902年晋阳围城后；确日未载')
event('li_xiji_advises_keyong', '李袭吉劝李克用崇德爱人、务农训兵',11,
      '掌书记李袭吉献议，略曰：“国富不在仓储，兵强不由众寡，人归有德，神固害盈。',
      [('李袭吉','献议者'),('李克用','受议者')],when='902年晋阳围城后；确日未载',
      note='记录李袭吉的政治建议，不把奏议内容写成已经施行的政策。')
claim('event','event_zztj_263_0902_li_xiji_advises_keyong','description',
      '李袭吉建议崇德爱人、去奢省役、设险固境、训兵务农。',11,
      '伏愿大王崇德爱人，去奢省役，设险固境，训兵务农。',
      '这是建议内容，不作政策落实。')
event('cunxu_criticizes_troops', '李存勖进言李克用亲军侵暴，李克用称待后整治',11,
      '其子存勖以为言，克用曰：“此辈从吾攻战数十年，比者帑藏空虚，诸军卖马以自给。',
      [('李存勖','进言者'),('李克用','答复者')],when='902年本段追叙；确日未载',
      note='承接“亲军皆沙陀杂虏，喜侵暴良民”；李克用答称待稍平再整治，不作实际整治。',year=None)
event('cunxu_consoles_keyong', '李存勖劝李克用待朱全忠势衰',11,
      '存勖进言曰：“物不极则不返，恶不极则不亡。',
      [('李存勖','劝谏者'),('李克用','受劝者')],when='902年本段条；确日未载',
      note='“硃氏”败亡是李存勖当时的判断，不前置为既成事实。')
event('liu_lady_raises_cunxu', '刘夫人厚待曹氏并教养李存勖',11,
      '刘夫人无子，克用宠姬曹氏生存勖，刘夫人待曹氏加厚。克用以是益贤之，诸姬有子，辄命夫人母之。夫人教养，悉如所生。',
      [('刘夫人','教养者'),('曹氏','生母'),('李存勖','受教养者'),('李克用','其父')],
      when='902年条追叙；确年未载',note='为本段家事追叙，不能断定发生于902年。',year=None)

# 12: court titles and corrupt digital text.
event('court_commissions_yang_xingmi', '朝廷命李俨宣谕江淮，授杨行密吴王等职',12,
      '上以左金吾将军李俨为江、淮宣谕使，书御衣赐杨行密，拜行密东面行营都统、中书令、吴王，以讨硃全忠。',
      [('李杰','下诏者'),('李俨','宣谕使'),('杨行密','受任者'),('朱温','讨伐对象')],
      when='902年三月后、四月前；确日未载',place='江淮',
      note='保留此段可读任命；后段乱码不用于推断其他将校。')
event('court_grants_regional_commands', '朝廷授朱瑾冯弘铎朱延寿节镇并加马殷同平章事',12,
      '以硃瑾为平卢节度使，冯弘鐸为武宁节度使，硃延寿为奉国节度使。加武安节度使马殷同平章事。',
      [('朱瑾','受任者'),('冯弘铎','受任者'),('朱延寿','受任者'),('马殷','加官者')],
      when='902年三月后、四月前；确日未载',
      note='只采用乱码前可辨的任命。')
event('li_yan_given_li_surname', '张浚之子李俨获赐李姓',12,
      '俨，张浚之子也，赐姓李。',
      [('李俨','获赐姓者'),('张浚','其父')],when='902年本段条；确日未载',
      note='父子关系本段明言；李俨赐姓前姓名未载，不猜其本名。')
rel='relationship_person_张浚_person_李俨_父亲'
B['person_relationships'].append(dict(key=rel,person_a_key=people['张浚'],person_b_key=people['李俨'],
    relation_type='父亲',description='《资治通鉴》天复二年条明言李俨为张浚之子。',status='draft'))
claim('person_relationship',rel,'description','张浚是李俨的父亲。',12,
      '俨，张浚之子也，赐姓李。','原文明示父子；李俨赐姓前本名未载。')

# 13–16: spring court and regional affairs.
event('cui_yin_urges_zhu', '崔胤四月丁酉至河中催朱全忠迎昭宗',13,
      '夏，四月，丁酉，崔胤自华州诣河中，泣诉于硃全忠，恐李茂贞劫天子幸蜀，宜以时迎奉，势不可缓。',
      [('崔胤','催迎者'),('朱温','被催者'),('李茂贞','崔胤所忧对象')],
      when='902年四月丁酉',place='华州、河中',
      note='劫天子幸蜀是崔胤的担忧，不写为已发生。')
event('huihu_offers_troops', '回鹘遣使请兵赴难，昭宗命韩偓拟书许之',14,
      '辛丑，回鹘遣使入贡，请发兵赴难，上命翰林学士承旨韩偓答书许之。',
      [('李杰','命拟答书者'),('韩偓','拟书者')],when='902年四月辛丑',
      note='“许之”为初拟答书，后续韩偓再谏并改变措辞。')
event('han_wo_advises_against_huihu', '韩偓乙巳谏勿招回鹘兵，昭宗从之',14,
      '乙巳，偓上言：“戎狄兽心，不可倚信。',
      [('韩偓','进谏者'),('李杰','采纳者')],when='902年四月乙巳',
      note='“兽心”等为韩偓当时的判断，不作客观族群事实。')
event('lu_guangqi_removed', '卢光启罢参知机务为太子太保',15,
      '兵部侍郎参知机务卢光启罢为太子太保。',
      [('卢光启','罢任者')],when='902年四月条；确日未载')
event('gu_quanwu_exchange', '杨行密归还顾全武，钱镠遣还秦裴',16,
      '杨行密遣顾全武归杭州以易秦裴，钱镠大喜，遣裴还。',
      [('杨行密','遣归顾全武者'),('顾全武','被遣归者'),('钱镠','遣还秦裴者'),('秦裴','被遣还者')],
      when='902年四月条；确日未载',place='杭州')

# Independent book evidence: retain chronological and naming differences.
extra(old_tang,'event','event_zztj_263_0902_bian_besieges_jinyang','description',
      '《旧唐书》亦记朱友宁乘胜围太原。','進圍太原',9,'corroborates',
      '只印证围城；旧唐与主书的兵力、日期不能直接并同。')
extra(old_siege,'event','event_zztj_263_0902_night_raids_shu_camp','description',
      '《旧五代史》卷二十六天复二年条亦记李嗣昭李嗣源夜袭汴营。',
      '李嗣昭與李嗣源夜入汴軍，斬將搴旗',10,'corroborates',
      '旧五代史明确年为天复二年；仅将夜袭相互印证。')
extra(old_siege,'event','event_zztj_263_0902_hedong_reoccupies_three_prefectures','description',
      '《旧五代史》天复二年条记丁卯朱友宁烧营、周德威追至白壁关并收复三州。',
      '丁卯，朱友寧燒營而遁，周德威追至白壁關，俘斬萬計，因收復慈、隰、汾等三州',10,'conflicts',
      '主书作氏叔琮撤军、石会关疑伏后引去；将领、地点与追击结果并列。')
extra(old_five,'event','event_zztj_263_0902_cui_yin_urges_zhu','description',
      '《旧五代史》同记四月崔胤自华至河中催朱全忠迎驾。',
      '丁酉，唐丞相崔允自華來謁帝，屢述艱運危急，事不可緩',13,'corroborates',
      '旧五作崔允，主书作崔胤；视为同一人的异文，原字保留。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,17):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷263天复二年第9—16段：晋阳围城及进退、石会关异说、李袭吉献议、刘夫人教养追叙、江淮任命与乱码、崔胤催迎、回鹘请兵及韩偓谏、卢光启罢任、顾全武秦裴交换。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=263,year=902,
    primary_source_key=primary,primary_source_keys=[primary,primary_court,primary_april],
    paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],
    coverage='卷263天复二年共59个非空段落中的第9—16段连续处理；本年尚未完成。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
