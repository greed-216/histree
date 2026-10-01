"""Curate Tongjian 263, year 902, consecutive paragraphs 41–48."""
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
primary = 'tongjian-263-902-xuwan'
primary_late = 'tongjian-263-902-winter'
old_five = 'jiuwudaishi-002-902-fengxiang'
new_tang = 'xinwudaishi-067-902-xu-wan'

B = {'format_version': 1, 'batch_key': 'zztj-v263-y0902-p041-p048',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P / 'sources/library' / primary, 'd7ab9ff', '司马光等'),
    (primary_late, P / 'sources/library' / primary_late, 'd7ab9ff', '司马光等'),
    (old_five, P.parent / 'part-04/sources/library' / old_five, '648c8e6', '薛居正等'),
    (new_tang, P.parent / 'part-04/sources/library' / new_tang, '648c8e6', '欧阳修等'),
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
for n in range(41, 49):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/263.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅', '李存审': '符存审', '李继昭':'符道昭', '王万弘':'李继密', '王宗播':'许存', '刘夫人':'刘夫人（李克用妻）', '曹氏':'曹氏（李存勖母）', '李继诲':'周承诲', '李彦弼':'董彦弼', '吉谏':'王宗黯', '李继徽':'杨崇本', '杜建微':'杜建徽', '傅璙':'钱传璙', '传璙':'钱传璙', '彦询':'彦询（李茂贞假子）'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_263_0902_06_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_263_0902_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 41–42: the Xu Wan revolt, Yang Xingmi's response, and the marriage alliance.
event('qian_refuses_yuezhou_retreat', '钱镠拒绝东渡越州避徐绾之乱', 41,
      '或劝钱镠渡江东保越州，以避徐、许之难。杜建微按剑叱之曰：“事或不济，同死于此，岂可复东度乎！”',
      [('钱镠','被劝东渡者'),('杜建微','反对东渡者')], place='杭州、越州',
      note='杜建微与本段后称建徽为同一人；保留底本异字，不把劝谏记为实际东渡。')
event('gu_quanwu_advises_guangling', '顾全武建议向杨行密求援', 41,
      '镠命全武告急于杨行密，全武曰：“徒往无益，请得王子为质。”',
      [('钱镠','派遣者'),('顾全武','求援使者'),('杨行密','求援对象')], place='广陵',
      note='顾全武提出以钱镠之子为质；此处尚未记杨行密答允。')
event('qian_chuanliao_goes_guangling', '钱传璙微服随顾全武赴广陵并求婚', 41,
      '镠命其子传璙微服为全武仆，与偕之广陵，且求婚于行密。',
      [('钱镠','派遣其子者'),('传璙','同行为质者'),('顾全武','同行使者'),('杨行密','求婚对象')], place='杭州、广陵',
      note='新五代史此子写作元璙；主书后文写傅璙及残缺私用字，身份依上下文暂并同一人，纸本待核。')
event('an_renyi_attempts_exchange', '安仁义欲以十仆交换钱传璙，顾全武夜逃', 41,
      '过润州，团练使安仁义爱傅璙清丽，将以十仆易之。全武夜半赂阍者逃去。',
      [('安仁义','提出交换者'),('傅璙','被要求交换者'),('顾全武','夜逃者')], place='润州',
      note='“将以”是意图，未证交换发生；傅璙暂依本段传璙并人。')
event('xu_wan_summons_tian_jun', '徐绾等召田頵赴杭州', 42,
      '绾等果召田頵，頵引兵赴之，先遣亲吏何饶谓镠曰',
      [('徐绾','召援者'),('田頵','率兵赴援者'),('何饶','传话者'),('钱镠','受话者')], place='杭州',
      note='引兵赴之确载；何饶要求钱镠迁越州，钱镠回绝。')
event('tian_jun_blocks_hangzhou', '田頵筑垒截断杭州交通', 42,
      '頵筑垒绝往来之道。镠患之，募能夺其地者赏以州。',
      [('田頵','筑垒者'),('钱镠','悬赏者')], place='杭州',
      note='筑垒地点未详，未推定精确坐标。')
event('chen_zhang_breaks_blockade', '陈璋率三百卒破垒并受任衢州刺史', 42,
      '衢州制置使陈璋将卒三百出城奋击，遂夺其地，镠即以为衢州刺史。',
      [('陈璋','率兵破垒及受任者'),('钱镠','任命者')], place='杭州、衢州',
      note='三百为史载出战人数，不转为伤亡人数。')
event('yang_xingmi_marriage_agreement', '杨行密答应顾全武请求并以女嫁钱传璙', 42,
      '行密许之，以女妻傅璙。',
      [('杨行密','许婚者'),('顾全武','请求者'),('傅璙','成婚者')], place='广陵',
      note='底本此处作傅璙；依第41段传璙并人。第42段另一处私用字不据形猜字。')

# 43–45: chancery, Xingzhou, and desertions from Fengxiang.
event('li_yan_reaches_yangzhou', '李俨十月抵杨州', 43, '冬，十月，李俨至杨州',
      [('李俨','抵达者')], when='902年冬十月', place='杨州',
      note='底本作杨州；不擅改扬州。')
event('yang_xingmi_establishes_chancellery', '杨行密建立制敕院并向李俨告知封拜', 43,
      '杨行密始建制敕院，每有封拜，辄以告俨，于紫极宫玄宗像前陈制书，再拜然后下。',
      [('杨行密','建院并行礼者'),('李俨','受告者')], when='902年冬十月', place='杨州紫极宫',
      note='记制敕院程序与史载仪式，不推定李俨实掌所有任命。')
event('wang_jian_takes_xingzhou', '王建攻取兴州并任王宗浩为刺史', 44,
      '王建攻拔兴州，以军使王宗浩为兴州刺史。',
      [('王建','攻取及任命者'),('王宗浩','受任刺史')], place='兴州')
event('yanxun_defects_to_bian', '李茂贞假子彦询率三团步兵投汴军', 45,
      '戊寅夜，李茂贞假子彦询帅三团步兵奔于汴军。',
      [('李茂贞','假父及原属方'),('彦询','率兵投汴者')], when='902年冬十月戊寅夜', place='凤翔',
      note='主书仅称“假子彦询”，未明示姓；不自行补李姓。')
event('li_yantao_defects_to_bian', '李彦韬随后投汴军', 45, '己卯，李彦韬继之。',
      [('李彦韬','继而投汴者')], when='902年冬十月己卯', place='凤翔',
      note='“继之”承上段投汴；不推定所率人数。')

# 46: negotiations, supplies, failed attack, desertion and increased guarding.
event('sima_ye_submits_memorial', '朱全忠遣司马鄴入凤翔奉表', 46,
      '庚辰，硃全忠遣幕僚司马鄴奉表入城。',
      [('朱温','派遣者'),('司马鄴','奉表者')], when='902年冬十月庚辰', place='凤翔')
event('zhu_sends_food_and_cloth', '朱全忠向凤翔献熊白并陆续献食物缯帛', 46,
      '甲申，又遣使献熊白，自是献食物、缯帛相继。',
      [('朱温','献物者')], when='902年冬十月甲申起', place='凤翔',
      note='“熊白”照底本保留，具体物名待核。')
event('zhu_asks_peace_with_maozhen', '朱全忠遣使请与李茂贞连和', 46,
      '丙戌，复遣使请与茂贞议连和，民出城樵采者皆不抄掠。',
      [('朱温','遣使者'),('李茂贞','议和对象')], when='902年冬十月丙戌', place='凤翔',
      note='只记请议和，不当作和约已成。')
event('zhu_requests_palace_repairs', '朱全忠上表请求修宫阙并迎车驾', 46,
      '丁亥，全忠表请修宫阙及迎车驾。',
      [('朱温','上表者')], when='902年冬十月丁亥', place='凤翔',
      note='上表请求未等于迎驾成功。')
event('emperor_sends_edict_to_zhu', '朝廷遣薛昌祚、王延缋赍诏赐朱全忠', 46,
      '己丑，遣国子司业薛昌祚、内使王延缋赍诏赐全忠。',
      [('薛昌祚','赍诏者'),('王延缋','赍诏者'),('朱温','受诏者')], when='902年冬十月己丑', place='凤翔')
event('maozhen_attacks_west_camp', '李茂贞癸巳攻汴军城西寨败还', 46,
      '癸巳，茂贞复出兵击汴军城西寨，败还。',
      [('李茂贞','出击败还者')], when='902年冬十月癸巳', place='凤翔城西寨')
event('fengxiang_desertions_increase', '凤翔军人夜缒及借樵采逃走者增多', 46,
      '凤翔军夜缒去，及因樵采去不返者甚众。',
      [('李茂贞','守城方')], when='902年冬十月癸巳后', place='凤翔',
      note='“甚众”不转成具体人数。')
event('maozhen_reinforces_palace_guard', '李茂贞疑皇帝与朱全忠密约并增御院守卫', 46,
      '茂贞疑上与全忠有密约，壬寅，更于御院北垣外增兵防卫。',
      [('李茂贞','怀疑及增防者')], when='902年冬十月壬寅', place='凤翔御院北垣',
      note='“疑”只是李茂贞的判断，不记皇帝与朱全忠确有密约。')

event('li_maoxun_relieves_fengxiang', '李茂勋十一月率万余人援凤翔', 47,
      '十一月，癸卯朔，保大节度使李茂勋帅其众万馀人救凤翔，屯于城北阪上，与城中举烽相应。',
      [('李茂勋','领军救援者')], when='902年十一月癸卯朔', place='凤翔城北阪',
      note='旧五代史写李周彝，附注说李茂勋即周彝；作为异名记录，不另建人。')
event('emperor_secretly_meets_scholars', '昭宗秘密召见韩偓、姚洎并相泣', 48,
      '甲辰，上使赵国夫人诇学士院二使皆不在，亟召韩偓、姚洎，窃见之于土门外，执手相泣。',
      [('李杰','秘密召见者'),('赵国夫人','探查者'),('韩偓','被召见者'),('姚洎','被召见者')],
      when='902年十一月甲辰', place='土门外',
      note='赵国夫人先侦察两使不在；秘密见面不推成明确政治承诺。')

extra(new_tang, 'event', 'event_zztj_263_0902_qian_chuanliao_goes_guangling', 'description',
      '《新五代史》同记顾全武携钱镠子赴广陵，写作元璙。', '吾嘗欲以元璙婚楊氏', 41,
      'adds', '与主书传璙/傅璙字形不同；仅据相同叙事角色暂并身份，异文待纸本核。')
extra(new_tang, 'event', 'event_zztj_263_0902_yang_xingmi_marriage_agreement', 'description',
      '《新五代史》亦载杨行密以女妻元璙。', '行密以女妻元璙', 42,
      'corroborates', '事件印证，姓名异文保留。')
extra(old_five, 'event', 'event_zztj_263_0902_li_maoxun_relieves_fengxiang', 'description',
      '《旧五代史》记李周彝率万余人屯岐北原，与城中烽火相应。',
      '統兵萬餘人屯於岐之北原，與城中舉烽以相應', 47,
      'adds', '旧五代史正文称李周彝，附注称李茂勋即周彝；保留异名。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,49):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷263天复二年第41—48段连续处理；主书异字与电子私用字在review.md说明，不据不明字推断身份或事实。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=263,year=902,
    primary_source_key=primary,primary_source_keys=[primary,primary_late],
    paragraphs=[Q[n]['id'] for n in range(41,49)],next_paragraph=Q[49]['id'],
    coverage='卷263天复二年共59个非空段落中的第41—48段连续处理；本年尚未完成。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
