"""Curate Tongjian 263, year 902, consecutive paragraphs 33–40."""
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
primary = 'tongjian-263-902-summer'
primary_late = 'tongjian-263-902-augsep'
old_five = 'jiuwudaishi-002-902-fengxiang'
new_tang = 'xintangshu-063-902-wei'

B = {'format_version': 1, 'batch_key': 'zztj-v263-y0902-p033-p040',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-04/sources/library' / primary, '648c8e6', '司马光等'),
    (primary_late, P / 'sources/library' / primary_late, '4938855', '司马光等'),
    (old_five, P.parent / 'part-04/sources/library' / old_five, '648c8e6', '薛居正等'),
    (new_tang, P / 'sources/library' / new_tang, '4938855', '欧阳修、宋祁等'),
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
for n in range(33, 41):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/263.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅', '李存审': '符存审', '李继昭':'符道昭', '王万弘':'李继密', '王宗播':'许存', '刘夫人':'刘夫人（李克用妻）', '曹氏':'曹氏（李存勖母）', '李继诲':'周承诲', '李彦弼':'董彦弼', '吉谏':'王宗黯', '李继徽':'杨崇本'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_263_0902_05_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_263_0902_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 33–34: Fengxiang raids and the actual restoration of Wei Yifan.
event('maozhen_night_raid_fengtian', '李茂贞庚戌夜袭奉天并俘倪章邵棠',33,
      '庚戌，李茂贞出兵夜袭奉天，虏汴将倪章、邵棠以归。',
      [('李茂贞','夜袭者'),('倪章','被俘者'),('邵棠','被俘者')],
      when='902年八月庚戌',place='奉天',note='被俘不等于遇害。')
event('maozhen_sortie_defeated', '李茂贞乙未出兵战朱全忠而败，汴军追近凤翔西门',33,
      '乙未，茂贞大出兵，与硃全忠战，不胜，暮归，汴兵追之，几入西门。',
      [('李茂贞','出战败退者'),('朱温','交战对方')],when='902年八月乙未',place='凤翔西门',
      note='“几入西门”说明险些入城，不记作攻陷凤翔。')
event('wei_yifan_restored', '韦贻范己亥获起复并于次日视事',34,
      '己亥，再起复前户部侍郎、同平章事韦贻范，使姚洎草制。贻范不让，即表谢，明日，视事。',
      [('韦贻范','实际起复者'),('姚洎','草制者')],when='902年八月己亥起复、次日视事',
      note='第29段前次起复被韩偓阻止；本段为再次命起复，且明确次日视事。')

# 35: the western campaign, surrender and later death.
event('xichuan_passage_refused', '西川请假道兴元，李继密戍三泉拒之',35,
      '西川兵请假道于兴元，山南西道节度使李继密遣兵戍三泉以拒之。',
      [('李继密','设防者')],when='902年八月辛丑前；确日未载',place='兴元、三泉')
event('wang_zongbo_first_assault', '王宗播辛丑攻三泉不克，退守山寨',35,
      '辛丑，西川前锋将王宗播攻之，不克，退保山寨。',
      [('王宗播','初战不克者')],when='902年八月辛丑',place='三泉')
event('wang_zongbo_takes_four_forts', '柳修业劝王宗播决战，西川军破四寨',35,
      '亲吏柳修业谓宗播曰：“公举族归人，不为之死战，何以自保？”宗播令其众曰：“吾与汝曹决战取功名；不尔，死于此！”遂破金牛、黑水、西县、褒城四寨。',
      [('柳修业','劝战者'),('王宗播','率军攻寨者')],
      when='902年八月辛丑后',place='金牛、黑水、西县、褒城',
      note='柳、王的言论按当事人话语存，不转为既成惩罚事实。')
event('qin_chenghou_arrow_wound', '秦承厚攻西县时受贯目箭伤，王建为其处理伤口',35,
      '军校秦承厚攻西县，矢贯左目，达于右目，镞不出。王建自舐其创，脓溃镞出。',
      [('秦承厚','负伤者'),('王建','处理伤口者')],when='902年八月西县战期间',place='西县',
      note='只录史载伤势与处理，未推断医学机制或后遗症。')
event('xichuan_takes_xingyuan', '王宗播破马盘寨，王宗涤先登克兴元，李继密降',35,
      '王宗播攻马盘寨，继密战败，奔还汉中。西川军乘胜至城下，王宗涤帅众先登，遂克之，继密请降，迁于成都。',
      [('王宗播','攻寨者'),('李继密','战败请降者'),('王宗涤','先登取城者')],
      when='902年八月辛丑后',place='马盘寨、汉中、兴元、成都',
      note='先取马盘寨后克兴元，李继密降后迁成都；不把请降当作战死。')
event('li_jimi_restores_wang_name', '李继密降蜀后恢复本名王万弘',35,
      '王建曰：“继密残贼三辅，以其降，不忍杀。”复其姓名曰王万弘，不时召见诸将陵易之。',
      [('王建','复名者'),('王万弘','复本名者')],when='902年降成都后；确日未载',
      note='王万弘与李继密是同一人；沿用既有稳定key，不另建人物。')
event('wang_wanhong_drowns_later', '王万弘在成都纵酒受辱后醉投池水而亡',35,
      '万弘终日纵酒，俳优辈亦加戏诮。万弘不胜忧愤，醉投池水而卒。',
      [('王万弘','去世者')],when='降成都后；确年未载',place='成都',year=None,
      note='本段续叙未给确年，不直接写为902年同月死亡。')

# 36: Wang Zongdi appointed, then killed; earlier Tang Daoxi service is retrospective.
event('wang_zongdi_xingyuan_governor', '王宗涤受任山南西道节度使',36,
      '诏以王宗涤为山南西道节度使。',
      [('王宗涤','受任者')],when='902年兴元克后；确日未载',place='兴元')
event('wang_jian_suspects_zongdi', '王建忌王宗涤得众，王宗佶等构谤',36,
      '宗涤有勇略，得众心，王建忌之。建作府门，绘以硃丹，蜀人谓之“画红楼”，建以宗涤姓名应之，王宗佶等疾其功，复构以飞语。',
      [('王宗涤','受猜忌者'),('王建','猜忌者'),('王宗佶','构谤者')],
      when='902年王宗涤受任后',place='成都',
      note='“画红楼”与姓名相应是史载王建解释，不作可验证的预兆。')
event('wang_zongdi_killed', '王建召王宗涤至成都，唐道袭奉命缢杀之',36,
      '建命亲随马军都指挥使唐道袭夜饮之酒，缢杀之，成都为之罢市，连营涕泣，如丧亲戚。',
      [('王建','下令者'),('唐道袭','执行者'),('王宗涤','被杀者')],
      when='902年王宗涤受任后；确日未载',place='成都',
      note='本段明记王建命唐道袭杀王宗涤；民众反应不量化。')
event('wang_zonghe_acts_xingyuan', '王建以王宗贺权兴元留后',36,
      '建以指挥使王宗贺权兴元留后。',
      [('王建','任命者'),('王宗贺','权知留后者')],when='902年王宗涤被杀后',place='兴元')
event('tang_daoxi_earlier_service', '唐道袭早年以舞童事王建并渐参与谋划',36,
      '道袭，阆州人也，始以舞童事建，后浸预谋画。',
      [('唐道袭','旧属与谋划者'),('王建','受事者')],
      when='始以舞童事王建；确年未载',place='阆州',year=None,
      note='传记式追述，不能定为902年。')

# 37: debate, feigned defection and renewed siege.
event('zhu_debates_withdrawal', '朱全忠九月因久雨士病议撤，季昌知俊劝留',37,
      '九月，乙巳，硃全忠以久雨，士卒病，召诸将议引兵归河中，亲从指挥使高季昌、左开道指挥使刘知俊曰：“天下英雄，窥此举一岁矣。今茂贞已困，奈何舍之去！”',
      [('朱温','议撤者'),('高季昌','劝留者'),('刘知俊','劝留者')],
      when='902年九月乙巳',place='凤翔围城营',
      note='只是议撤，朱全忠此时未撤。')
event('gao_proposes_ruse', '高季昌请设诱敌计，马景愿入凤翔为谍',37,
      '全忠患李茂贞坚壁不出，季昌请以谲计诱致之。募有能入城为谍者，骑士马景请行，曰：“此行必死，愿大王录其妻子。”',
      [('朱温','同意计划者'),('高季昌','献策者'),('马景','自愿执行者')],
      when='902年九月乙巳后',place='凤翔',
      note='马景所说“必死”为其风险判断，不预记其实际死亡。')
event('ma_jing_feigns_desertion', '马景丁未诈逃入凤翔报称汴军将遁',37,
      '丁未旦，偃旗帜潜伏，无得妄出，营中寂如无人。景与众骑皆出，忽跃马西去，诈为逃亡，入城告茂贞曰：“全忠举军遁矣，独留伤病者近万人守营，今夕亦去矣，请速击之！”',
      [('马景','诈降传谍者'),('李茂贞','受骗者'),('朱温','设伏方')],
      when='902年九月丁未',place='凤翔',
      note='汴军已遁及伤病万人都是马景的欺敌话语，不能当作真实撤军或实测人数。')
event('zhu_ambushes_fengxiang_sortie', '李茂贞丁未出城袭汴营，朱全忠伏军反击',37,
      '于是茂贞开门，悉众攻全忠营，全忠鼓于中军，百营俱出，纵兵击之，又遣数百骑据其城门，凤翔军进退失据，自蹈藉，杀伤殆尽。',
      [('李茂贞','出战失利者'),('朱温','伏军反击者')],
      when='902年九月丁未',place='凤翔城外',
      note='“杀伤殆尽”为主书形容，未换成精确伤亡数。')
event('maozhen_seeks_peace', '李茂贞战败后议和并拟奉昭宗回京',37,
      '茂贞自是丧气，始议与全忠连和，奉车驾还京，不复以诏书勒全忠还镇矣。',
      [('李茂贞','议和者'),('朱温','和议对方')],
      when='902年九月丁未战后',place='凤翔',
      note='只记开始议和及拟奉车驾，昭宗实际返京见后年史料。')
event('gao_jichang_songzhou', '朱全忠表高季昌为宋州团练使',37,
      '全忠表季昌为宋州团练使。',
      [('朱温','表荐者'),('高季昌','被表荐者')],when='902年九月丁未战后',place='宋州',
      note='“表”是呈报，不把朝廷正式授任前置。')
event('gao_jichang_past_service', '高季昌旧为朱友恭仆夫',37,
      '季昌，硖石人，本硃友恭之仆夫也。',
      [('高季昌','旧仆夫'),('朱友恭','旧主')],when='本为朱友恭仆夫；确年未载',year=None,
      note='传记追述，确年不明。')

# 38–40: Wuding surrender, siege works and new titles.
event('li_sijing_surrenders_yang_prefecture', '李思敬戊申以洋州归王建',38,
      '戊申，武定节度使李思敬以洋州降王建。',
      [('李思敬','归降者'),('王建','受降者')],when='902年九月戊申',place='洋州')
event('maozhen_forages_neighboring_zhou', '李茂贞辛亥遣骑赴邻州取刍粮',39,
      '辛亥，李茂贞尽出骑兵于邻州就刍粮。',
      [('李茂贞','遣骑者')],when='902年九月辛亥',place='邻州',
      note='“邻州”照底本保留，具体地望未核。')
event('zhu_digs_moat_around_fengxiang', '朱全忠壬子穿蚰蜒壕围凤翔并设铺铃架',39,
      '壬子，硃全忠穿蚰蜒壕围凤翔，设大铺、铃架以绝内外。',
      [('朱温','筑围者')],when='902年九月壬子',place='凤翔')
event('maozhen_four_commands', '朝廷癸亥授李茂贞凤翔等四镇节度使',40,
      '癸亥，以茂贞为凤翔、静难、武定、昭武四镇节度使。',
      [('李茂贞','受任者')],when='902年九月癸亥',place='凤翔、静难、武定、昭武')

extra(new_tang,'event','event_zztj_263_0902_wei_yifan_restored','description',
      '《新唐书》宰相表记八月己亥韦贻范起复并守户部侍郎同平章事。',
      '八月己亥，貽範起復，守戶部侍郎、同中書門下平章事',34,'corroborates',
      '印证前次罢草后此时实际起复；新唐书另列盐铁转运等使职，不覆盖主书。')
extra(old_five,'event','event_zztj_263_0902_ma_jing_feigns_desertion','description',
      '《旧五代史》卷二亦记马景诈逃入岐并诓称汴军将遁。',
      '景因躍馬西走，直叩岐闉，詐以軍怨東遁為告',37,'corroborates',
      '两书皆写诈降传谍；旧五记九月甲戌先登高察岐寨，不据此改主书丁未设伏日期。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(33,41):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷263天复二年第33—40段：奉天夜袭、韦贻范再起复、王宗播克兴元及李继密复名王万弘、王宗涤遇害、马景诈降与凤翔战、洋州归蜀、凤翔围壕及李茂贞四镇任命。追叙确年未定；骗敌言辞与历史事实区分。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=263,year=902,
    primary_source_key=primary,primary_source_keys=[primary,primary_late],
    paragraphs=[Q[n]['id'] for n in range(33,41)],next_paragraph=Q[41]['id'],
    coverage='卷263天复二年共59个非空段落中的第33—40段连续处理；本年尚未完成。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
