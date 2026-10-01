"""Curate Tongjian 265, year 905, consecutive paragraphs 47–52."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 61))
primary_winter = 'tongjian-265-905-winter'
old_november = 'jiutangshu-020-905-november'
new_kong_identity = 'xinwudaishi-043-kongxun-identity'
new_kong_dispute = 'xinwudaishi-043-kongxun-dispute'
new_wang_dispute = 'xinwudaishi-043-wangyin-dispute'
old_campaign = 'jiuwudaishi-002-huainan-campaign'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0905-p047-p052',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_winter, P.parent / 'part-07/sources/library' / primary_winter, '9d94d70f', '司马光等'),
    (old_campaign, P.parent / 'part-07/sources/library' / old_campaign, '9d94d70f', '薛居正等'),
    (old_november, P / 'sources/library' / old_november, '4525bafe', '刘昫等'),
    (new_kong_identity, P / 'sources/library' / new_kong_identity, '4525bafe', '欧阳修等'),
    (new_kong_dispute, P / 'sources/library' / new_kong_dispute, '4525bafe', '欧阳修等'),
    (new_wang_dispute, P / 'sources/library' / new_wang_dispute, '4525bafe', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_winter,)}
for n in range(47, 53):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '殷衡':'孔循', '赵殷衡':'孔循', '卿':'司马卿', '再用':'柴再用', '玄晖':'蒋玄晖', '璨':'柳璨'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0905_08_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐二年（905）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical, aliases=['赵殷衡'] if canonical == '孔循' else [], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷265天祐二年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=905):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0905_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '905年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '905年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0905_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0905_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 47: The attempt at Shouzhou ended in withdrawal, not a siege or capture.
event('zhu_marches_to_shouzhou', '朱全忠戊申由光州趋寿州', 47,
      '戊申，硃全忠发光州，迷失道百馀里，又遇雨，比及寿州',
      [('朱温', '率军由光州赴寿州者')], when='905年十月戊申离光州；抵寿州确日未载', place='光州至寿州',
      note='戊申是离光州日；迷路、遇雨和抵寿州不强行合为同日。')
event('zhu_withdraws_zhengyang', '朱全忠未围寿州而退屯正阳', 47,
      '寿人坚壁清野以待之。全忠欲围之，无林木可为栅，乃退屯正阳。',
      [('朱温', '欲围城而后退兵者')], when='905年十月戊申后；确日未载', place='寿州、正阳',
      note='仅记围城计划及退屯；不得记为已围或已攻克寿州。')

# 48: District renaming is a separate court act.
event('chengde_renamed_wushun', '唐廷改成德军名武顺军', 48,
      '癸丑，更名成德军曰武顺。', when='905年十月癸丑', place='成德军',
      note='只录军额改名，不据此推断辖地变化。')

# 49: Retreat, rear-guard attack, and arrival retain their distinct dates.
event('zhu_crosses_huai_north', '朱全忠丙辰渡淮北还', 49,
      '十一月，丙辰，硃全忠渡淮而北',
      [('朱温', '率军渡淮北还者')], when='905年十一月丙辰', place='淮水、正阳',
      note='《旧唐书》亦记由正阳北渡；不凭本段推断渡口精确坐标。')
event('chai_hits_zhu_rear', '柴再用袭朱全忠后军', 49,
      '柴再用抄其后军，斩首三千级，获辎重万计。',
      [('柴再用', '袭击后军者'), ('朱温', '所部后军遇袭者')],
      when='905年十一月丙辰北渡前后', place='淮水附近',
      note='三千首级与辎重万计为《通鉴》所记数字；旧书本纪未据此独立证实数字。')
event('zhu_returns_daliang_after_huainan', '朱全忠丁卯抵大梁', 49,
      '丁卯，至大梁。', [('朱温', '抵达大梁者')],
      when='905年十一月丁卯', place='大梁',
      note='“全忠悔之，躁忿尤甚”是主书记述，不额外推断心理成因。')

# 50: The paragraph begins with undated retrospective planning. Allegations remain allegations.
event('jiang_liu_plan_nine_bestowals', '蒋玄晖与柳璨拟先封国加九锡再行禅让', 50,
      '玄晖与柳璨等议：以魏、晋以来皆先封大国，加九锡，殊礼，然后受禅，当次第行之。',
      [('蒋玄晖', '参与拟议者'), ('柳璨', '参与拟议者'), ('朱温', '拟受封及禅让者')],
      when='十一月庚午前的追叙；确年日未载', year=None,
      note='“先是”追叙无确年；这是蒋、柳的方案，不记为已获九锡或已受禅。')
event('pei_di_sent_to_zhu', '唐廷遣裴迪为送宫告使', 50,
      '仍以刑部尚书裴迪为送宫告使，全忠大怒。',
      [('裴迪', '受遣为送宫告使者'), ('朱温', '对安排发怒者')],
      when='十一月庚午前；确年日未载', year=None,
      note='裴迪出使和朱全忠的反应来自追叙；不可与庚午改郊礼合为同日。')
event('wang_kong_accuse_jiang_liu', '王殷与赵殷衡向朱全忠指控蒋玄晖、柳璨延唐', 50,
      '宣徽副使王殷、赵殷衡疾玄晖权宠，欲得其处，因谮之于全忠曰：“玄晖、璨等欲延唐祚，故逗遛其事以须变。”',
      [('王殷', '提出指控者'), ('孔循', '以赵殷衡之名提出指控者'),
       ('蒋玄晖', '被指控者'), ('柳璨', '被指控者'), ('朱温', '受言者')],
      when='十一月庚午前；确年日未载', year=None,
      note='延唐及故意拖延是王殷、孔循的指控，不作为蒋柳真实动机。')
event('jiang_explains_at_shouchun', '蒋玄晖赴寿春向朱全忠解释九锡方案', 50,
      '玄晖闻之惧，自至寿春，具言其状。全忠曰：“汝曹巧述闲事以沮我，借使我不受九锡，岂不能作天子邪！”',
      [('蒋玄晖', '赴寿春申辩者'), ('朱温', '驳斥者')],
      when='王殷、赵殷衡指控后；确年日未载', year=None, place='寿春',
      note='记录双方交涉；引语仅作说话者立场，不认定天命、敌情或受禅已发生。')
event('jiang_liu_continue_nine_bestowals', '蒋玄晖与柳璨继续商议九锡', 50,
      '全忠叱之曰：“奴果反矣！”玄晖惶遽辞归，与璨议行九锡。',
      [('蒋玄晖', '辞归后议九锡者'), ('柳璨', '同议九锡者'), ('朱温', '斥责蒋玄晖者')],
      when='寿春交涉后；确年日未载', year=None,
      note='只记再议，不认作九锡已施行；“反”是朱全忠的斥语。')
event('pei_di_reports_zhu_anger_at_rite', '裴迪回报朱全忠反对唐帝郊祀', 50,
      '裴迪自大梁还，言全忠怒曰：“柳璨、蒋玄晖等欲延唐祚，乃郊天也。”',
      [('裴迪', '由大梁返而传达朱全忠之言者'), ('朱温', '郊祀反对意见的说话者'),
       ('柳璨', '被指责者'), ('蒋玄晖', '被指责者')],
      when='905年十一月庚午前；确日未载', place='大梁至唐廷',
      note='“欲延唐祚”仍是朱全忠经裴迪转述的指控，不写作查实事实。')
event('tang_postpones_suburban_rite', '唐廷庚午改郊祀为来年正月上辛', 50,
      '璨等惧，庚午，敕改用来年正月上辛。',
      [('柳璨', '因朱全忠怒而惧者')],
      when='905年十一月庚午下敕；拟于来年正月上辛行礼',
      note='下敕与拟行礼日期分开；此段只证改期，不证来年实际举行。')
event('kong_xun_alias_retrospective', '孔循曾用名赵殷衡', 50,
      '殷衡本姓孔名循，为全忠家乳母养子，故冒姓赵，后渐贵，复其姓名。',
      [('孔循', '曾冒赵姓并用赵殷衡名者')],
      when='本段追叙；改名确年未载', year=None,
      note='孔循与赵殷衡为同一人；本段未给收养和复名的年份，不倒填905年。')

# 51–52: Arrival, envoy response, and departure.
event('zhao_kuangming_arrives_chengdu', '赵匡明壬申抵成都，王建以客礼相待', 51,
      '壬申，赵匡明至成都，王建以客礼遇之。',
      [('赵匡明', '抵达并受客礼者'), ('王建', '以客礼相待者')],
      when='905年十一月壬申', place='成都',
      note='“客礼”照原文保留，不推为正式授职或联盟。')
event('sima_qing_enters_shu', '唐告哀使司马卿进入蜀境', 52,
      '朝廷遣告哀使司马卿宣谕王建，至是始入蜀境。',
      [('司马卿', '宣谕王建的告哀使'), ('王建', '宣谕对象')],
      when='905年十一月壬申后条；确日未载', place='蜀境',
      note='遣使时间与进入蜀境时间不同；仅后一动作属于“至是”。')
event('wang_zongwan_warns_sima_qing', '韦庄为王建谋，王宗绾向司马卿传话', 52,
      '西川掌书记韦庄为建谋，使武定节度使王宗绾谕卿曰：“蜀之将士，世受唐恩，去岁闻乘舆东迁，凡上二十表，皆不报。',
      [('韦庄', '为王建献计者'), ('王建', '受计者'),
       ('王宗绾', '向司马卿传话者'), ('司马卿', '受传话者')],
      when='司马卿入蜀境后；确日未载', place='蜀境',
      note='“二十表皆不报”属于王宗绾传话内容，本段没有独立表文可核，不录为独立事实。')
event('sima_qing_returns', '司马卿听王宗绾传话后折返', 52,
      '舍人宜自图进退。”卿乃还。',
      [('王宗绾', '传达劝退言辞者'), ('司马卿', '折返者')],
      when='王宗绾传话后；确日未载', place='蜀境',
      note='蜀军备战、先帝遇弑及前述奏表均为传话中的说法；折返是主书记载的结果。')

extra(old_campaign, 'event', 'event_zztj_265_0905_zhu_withdraws_zhengyang', 'description',
      '《旧五代史》卷二亦记寿春坚壁清野、朱全忠退屯正阳。',
      '壽春人堅壁清野以待帝。帝乃還，舍于正陽', 47, 'corroborates',
      '旧书与主书均证撤退，均未记攻占寿春。')
extra(old_november, 'event', 'event_zztj_265_0905_zhu_withdraws_zhengyang', 'description',
      '《旧唐书》卷二十下亦记寿州闭壁、朱全忠北还。',
      '壽人閉壁不出，左右言師老不可用', 47, 'corroborates',
      '旧书记“距寿州三十里”，与主书“比及寿州”措辞不同；不推断精确距离。')
extra(old_november, 'event', 'event_zztj_265_0905_zhu_crosses_huai_north', 'time_original',
      '《旧唐书》卷二十下记丙辰自正阳渡淮而北。',
      '是月丙辰，全忠自正陽渡淮而北', 49, 'corroborates',
      '旧书给出正阳但没有柴再用袭击数字。')
extra(old_november, 'event', 'event_zztj_265_0905_zhu_returns_daliang_after_huainan', 'time_original',
      '《旧唐书》卷二十下同记丁卯至大梁。',
      '丁卯，至大樑', 49, 'corroborates',
      '繁体“大樑”保留原字形，主体地名规范为大梁。')
extra(new_kong_identity, 'event', 'event_zztj_265_0905_kong_xun_alias_retrospective', 'description',
      '《新五代史》卷四十三亦称孔循由乳母收养，冒赵姓、名殷衡。',
      '乳母之夫姓趙，循又冒姓為趙氏，名殷衡', 50, 'corroborates',
      '旧书称全忠家乳母，新书称太祖诸儿乳母；原貌并列，复名年份未定。')
extra(new_kong_dispute, 'event', 'event_zztj_265_0905_wang_kong_accuse_jiang_liu', 'description',
      '《新五代史》卷四十三记孔循与王殷向朱全忠指控蒋玄晖等延唐。',
      '循因與王殷讒于太祖曰：「玄暉私侍何太后，與廷範等奉天子郊天，冀延唐祚。」',
      50, 'adds', '该书另有私侍何太后的指控，不作为核实的事实；所指对象与主书措辞不完全相同。')
extra(new_wang_dispute, 'event', 'event_zztj_265_0905_wang_kong_accuse_jiang_liu', 'description',
      '《新五代史》王殷传亦记王殷谮蒋玄晖，内容涉及郊祀。',
      '殷與樞密使蔣玄暉等有隙，因譖之太祖', 50, 'corroborates',
      '同书不同列传不可当作独立来源；指控仍不能写成蒋玄晖的事实行为。')
extra(old_november, 'event', 'event_zztj_265_0905_pei_di_reports_zhu_anger_at_rite', 'description',
      '《旧唐书》卷二十下亦记裴迪自大梁还后传达朱全忠怒意。',
      '裴迪自大樑回，言全忠怒蔣玄暉、張廷范、柳璨等謀延唐祚',
      50, 'corroborates', '旧书列张廷范，主书此处列蒋玄晖、柳璨；保留名单差别。')
extra(old_november, 'event', 'event_zztj_265_0905_tang_postpones_suburban_rite', 'time_original',
      '《旧唐书》卷二十下同记庚午敕改郊礼至来年正月上辛。',
      '庚午，敕曰：「先定此月十九日親禮南郊，雖定吉辰，改卜亦有故事。宜改取來年正月上辛',
      50, 'corroborates', '本句只证明改期；原定十一月十九日见旧书。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(47, 53):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
        review='卷265天祐二年第47—52段连续处理；繁简异体只用于主体匹配，原文不改；追叙与指控均保留属性。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=265, year=905,
    primary_source_key=primary_winter, primary_source_keys=[primary_winter],
    paragraphs=[Q[n]['id'] for n in range(47, 53)], next_paragraph=Q[53]['id'],
    coverage='卷265天祐二年第47—52段连续处理；寿州撤军、柴再用袭后军、九锡与郊礼争议、孔循异名、蜀境告哀使。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
