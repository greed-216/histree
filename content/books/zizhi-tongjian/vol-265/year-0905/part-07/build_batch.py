"""Curate Tongjian 265, year 905, consecutive paragraphs 41–46."""
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
primary_autumn = 'tongjian-265-905-autumn'
primary_winter = 'tongjian-265-905-winter'
old_october = 'jiutangshu-020-905-october'
new_yangwo = 'xinwudaishi-061-yangwo-succession'
old_campaign = 'jiuwudaishi-002-huainan-campaign'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0905-p041-p046',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_autumn, P.parent / 'part-06/sources/library' / primary_autumn, '0ad8e2bd', '司马光等'),
    (primary_winter, P / 'sources/library' / primary_winter, '9d94d70f', '司马光等'),
    (old_october, P / 'sources/library' / old_october, '9d94d70f', '刘昫等'),
    (new_yangwo, P / 'sources/library' / new_yangwo, '9d94d70f', '欧阳修等'),
    (old_campaign, P / 'sources/library' / old_campaign, '9d94d70f', '薛居正等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_autumn, primary_winter)}
for n in range(41, 47):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '渥':'杨渥', '循':'苏循', '楷':'苏楷', '再用':'柴再用'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0905_07_{len(B["claims"])+1:04d}',
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
        row = dict(key='person_' + canonical, name=canonical, aliases=[], era='晚唐', birth_year=None,
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
    ck = f'claim_zztj_265_0905_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 41: Yang Xingmi's illness, disputed succession advice, actual summons and appointment.
event('yang_xingmi_calls_yang_wo', '杨行密病中命周隐召长子杨渥',41,
      '杨行密长子宣州观察使渥，素无令誉，军府轻之。行密寝疾，命节度判官周隐召渥。',
      [('杨行密','患病而命召子者'),('杨渥','被召的长子'),('周隐','受命召杨渥者')],
      when='905年九月后条；确日未载',place='淮南',
      note='“素无令誉，军府轻之”是主书评价与时人态度，不据此写杨渥具体过失；父子关系沿用旧批。')
event('zhou_yin_proposes_liu_wei_regency', '周隐建议刘威暂领军府',41,
      '隐性憃直，对曰：“宣州司徒轻易信谗，喜击球饮酒，非保家之主。馀子皆幼，未能驾驭诸将。庐州刺史刘威，从王起细微，必不负王，不若使之权领军府，俟诸子长以授之。”行密不应。',
      [('周隐','进言刘威权领军府者'),('杨行密','未采纳者'),('刘威','被建议暂掌军府者')],
      when='杨行密命召杨渥时；确日未载',place='淮南',
      note='这是周隐的提议与评价，杨行密未应；刘威没有因此实际接掌军府。')
event('xu_zhang_advise_family_succession', '徐温、张颢劝杨行密由子孙继业',41,
      '左右牙指挥使徐温、张颢言于行密曰：“王平生出万死，冒矢石，为子孙立基业，安可使他人有之！”行密曰：“吾死瞑目矣！”',
      [('徐温','劝进家族继业者'),('张颢','劝进家族继业者'),('杨行密','回应者')],
      when='周隐提出刘威方案后；确日未载',
      note='只记建议与回应，不据此推定张颢后来一定支持杨渥。')
event('yan_xu_dispatch_yang_wo_summons', '严可求与徐温取牒遣使召杨渥',41,
      '可求与徐温诣隐，隐未出见，牒犹在案上，可求即与温取牒，遣使者如宣州召之。',
      [('严可求','取牒遣使者'),('徐温','同取牒遣使者'),('周隐','持牒而未发者'),('杨渥','被遣使召回者')],
      when='杨行密病中；杨渥抵广陵前；确日未载',place='宣州',
      note='召牒被取并遣使的动作与周隐先前建议分开；不把杨渥到达倒填为同日。')
event('yang_xingmi_appoints_wang_maozhang', '杨行密以王茂章为宣州观察使',41,
      '行密以润州团练使王茂章为宣州观察使。',
      [('杨行密','授任者'),('王茂章','由润州调任宣州观察使者')],
      when='杨渥被召后；确日未载',place='宣州')

# 42: Appointment and later reversal in Zhu's military plan.
event('zhu_all_armies_commander', '唐廷十月丙戌以朱全忠为诸道兵马元帅',42,
      '冬，十月，丙戌朔，以硃全忠为诸道兵马元帅，别开幕府。',
      [('朱温','受任诸道兵马元帅者')],when='905年十月丙戌朔',
      note='《旧唐书》同记并另载食邑，不把幕府成立推成特定官员已任职。')
event('zhu_changes_plan_to_attack_huainan', '朱全忠临归大梁改议攻淮南',42,
      '是日，全忠部署将士，将归大梁，忽变计，欲乘胜击淮南。',
      [('朱温','改作进攻淮南决定者')],when='905年十月丙戌朔',
      note='原为归大梁的打算，改变后欲攻淮南；是否成行见后续段落。')
event('jing_xiang_advises_rest', '敬翔劝朱全忠归师息兵而未被采纳',42,
      '敬翔谏曰：“今出师未逾月，平两大镇，辟地数千里，远近闻之，莫不震慑。此威望可惜，不若且归息兵，俟衅而动。”不听。',
      [('敬翔','谏言息兵者'),('朱温','不采纳者')],when='905年十月丙戌后；确日未载',
      note='敬翔的话是进谏，不把其中军事评价和预测当客观战果。')

# 43: Renaming a military district and attaching Junzhou.
event('zhaoxin_renamed_rongzhao', '唐廷改昭信军为戎昭军并割均州隶之',43,
      '改昭信军为戎昭军。仍割均州隶之。',
      when='905年十月本段；确日未载',place='昭信军、均州',
      note='《旧唐书》卷二十下记冯行袭因“昭信”一字犯朱全忠讳而奏改，保留为该书说法；不据此推定区划边界。')

# 44: Route, weather, intimidation and outcome at Guangzhou.
event('zhu_marches_via_zaoyang', '朱全忠辛卯离襄州、壬辰至枣阳遇雨',44,
      '辛卯，硃全忠发襄州。壬辰，至枣阳，遇大雨。',
      [('朱温','率军行进者')],when='905年十月辛卯发襄州、壬辰至枣阳',place='襄州、枣阳',
      note='两日行军按原日序记，不换算公历日。')
event('zhu_army_hard_march', '朱全忠军由申州至光州受雨泥与补给困扰',44,
      '自申州抵光州，道险狭涂潦，人马疲乏，士卒尚未冬服，多逃亡。',
      [('朱温','所部行军者')],when='905年十月枣阳后；确日未载',place='申州至光州',
      note='原文说多逃亡但无人数，不估算损失。')
event('zhu_threatens_chai_at_guangzhou', '朱全忠招降并威胁光州刺史柴再用',44,
      '全忠使人谓光州刺史柴再用曰：“下，我以汝为蔡州刺史；不下，且屠城！”',
      [('朱温','遣使提出条件与威胁者'),('柴再用','受劝降者')],
      when='905年十月朱全忠抵光州后；确日未载',place='光州',
      note='许任蔡州刺史是威胁中的条件，不是实际授官；不把屠城威胁当成发生的屠杀。')
event('chai_holds_guangzhou_zhu_leaves', '柴再用守光州，朱全忠驻城东十日后离去',44,
      '再用严设守备，戎服登城，见全忠，拜伏甚恭，曰：“光州城小兵弱，不足以辱王之威怒。王苟先下寿州，敢不从命。”全忠留其城东旬日而去。',
      [('柴再用','布防并答朱全忠者'),('朱温','驻留后离去者')],
      when='905年十月光州城东旬日；确日未载',place='光州',
      note='柴再用的“苟先下寿州”是条件性言辞，不录为光州已经投降。')

# 45: Retrospective examination, proposal to revise posthumous name, and court adoption.
event('su_kai_exam_dismissal', '苏楷曾中进士后被昭宗覆试黜落',45,
      '乾宁中登进士第，昭宗覆试黜之，仍永不听入科场。',
      [('苏楷','覆试被黜者'),('李杰','下令覆试黜落者')],
      when='唐乾宁年间；确年未载',year=None,
      note='段首追叙，未换算为905年；“素无才行”属主书评价，不作为可验证品性。')
event('su_kai_petitions_posthumous_name', '苏楷甲午请重议昭宗谥号',45,
      '甲午，楷帅同列上言：“谥号美恶，臣子不得而私，先帝谥号多溢美，乞更详议。”事下太常',
      [('苏楷','率同列上言者')],when='905年十月甲午',
      note='“多溢美”是苏楷奏议中的判断，不作为已经核定的史实；《旧唐书》载其长篇奏文。')
event('zhang_tingfan_changes_posthumous_name', '张廷范奏改昭宗谥号和庙号，唐廷从之',45,
      '丁酉，张廷范奏改谥恭灵庄愍孝皇帝，庙号襄宗，诏从之。',
      [('张廷范','奏改者')],when='905年十月丁酉',
      note='此为当时获准的改议，不推断后世庙号未再变化；《旧唐书》“莊閔”与主书“庄愍”保留字形异文。')
su_xun=person('苏循',45,'苏楷父亲','礼部尚书循之子也')
rel='relationship_person_苏循_person_苏楷_父亲'
prior=json.loads((ROOT/'content/year-0907/content-batch.json').read_text())
prior_rel=next(r for r in prior['person_relationships'] if r['key']==rel)
assert prior_rel['person_a_key']==su_xun and prior_rel['person_b_key']==people['苏楷'] and prior_rel['relation_type']=='父亲'
B['person_relationships'].append(dict(prior_rel,status='draft'))
reused.add(rel)
claim('person_relationship',rel,'description','苏循是苏楷的父亲。',45,'苏楷，礼部尚书循之子也',
      '“循之子”承礼部尚书苏循；父亲方向为苏循→苏楷。')

# 46: Arrival is not the same action as the subsequent appointment.
event('yang_wo_arrives_guangling', '杨渥抵达广陵',46,
      '杨渥至广陵。', [('杨渥','到达者')],
      when='905年十月辛丑前；确日未载',place='广陵',
      note='到达日主书未载，不套用下句辛丑。')
event('yang_wo_made_huainan_liuhou', '杨行密辛丑以杨渥为淮南留后',46,
      '辛丑，杨行密承制以渥为淮南留后。',
      [('杨行密','承制授任者'),('杨渥','受任淮南留后者')],
      when='905年十月辛丑',place='淮南',
      note='“承制”保留主书措辞；不与杨渥后来的继位或杨行密去世合为同一日。')

extra(new_yangwo,'event','event_zztj_265_0905_zhou_yin_proposes_liu_wei_regency','description',
      '《新五代史》卷六十一记周隐推荐刘威代掌军政，杨行密未许。',
      '乃薦大將劉威，行密未許',41,'corroborates',
      '该书和主书均是后出叙述，不把周隐的建议当实际继任。')
extra(new_yangwo,'event','event_zztj_265_0905_yan_xu_dispatch_yang_wo_summons','description',
      '《新五代史》卷六十一亦载徐温与严可求取符遣使召杨渥。',
      '溫與嚴可求入問疾',41,'adds',
      '同段后文载温至隐处取召符并遣送；摘录仅证二人同见行密。')
extra(old_october,'event','event_zztj_265_0905_zhu_all_armies_commander','description',
      '《旧唐书》卷二十下同记十月丙戌朱全忠为诸道兵马元帅、别开幕府。',
      '十月丙戌朔，制梁王全忠可充諸道兵馬元帥，別開府幕',42,'corroborates',
      '旧书另记食邑，本批未把具体数额并入主书字段。')
extra(old_campaign,'event','event_zztj_265_0905_jing_xiang_advises_rest','description',
      '《旧五代史》卷二记敬翔切谏班师，朱全忠不听。',
      '敬翔切諫，請班師以全軍勢，帝不聽',42,'corroborates',
      '旧书措辞较短，未给主书所引长篇谏词。')
extra(old_october,'event','event_zztj_265_0905_zhaoxin_renamed_rongzhao','description',
      '《旧唐书》卷二十下称冯行袭以昭信军额犯朱全忠讳为由奏改戎昭军。',
      '金州馮行襲奏當道昭信軍額內一字，與元帥全忠諱字同，乃賜號戎昭軍',43,'adds',
      '只将旧书所载奏改原因并列，不推断谁最初提出均州改隶。')
extra(old_campaign,'event','event_zztj_265_0905_zhu_marches_via_zaoyang','time_original',
      '《旧五代史》卷二亦记辛卯离襄州、壬辰至枣阳遇雨。',
      '辛卯，帝自襄州引軍由光州路趨淮南；將發，敬翔切諫，請班師以全軍勢，帝不聽。壬辰，次於棗陽，遇大雨',44,'corroborates',
      '旧书同列两日行军；仍按原日序，不换算公历。')
extra(old_october,'event','event_zztj_265_0905_su_kai_petitions_posthumous_name','description',
      '《旧唐书》卷二十下保存苏楷甲午驳昭宗谥号奏文。',
      '甲午，起居郎蘇楷駁昭宗諡號',45,'corroborates',
      '奏文中的评价与政治论证仍是苏楷主张，不作为独立事实。')
extra(old_october,'event','event_zztj_265_0905_zhang_tingfan_changes_posthumous_name','description',
      '《旧唐书》卷二十下记改谥恭灵庄閔孝、庙号襄宗。',
      '太常卿張廷範改諡曰恭靈莊閔孝皇帝，廟號曰襄宗',45,'corroborates',
      '“閔”与主书“愍”为异字；旧书本句未给丁酉日。')
extra(new_yangwo,'event','event_zztj_265_0905_yang_wo_arrives_guangling','description',
      '《新五代史》卷六十一载杨渥见徐温所遣使者后启程。',
      '渥見溫使，乃行',46,'adds',
      '新书只证启程条件，不证主书到达广陵的确日。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,47):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷265天祐二年第41—46段连续处理；继任建议与执行分录，追叙科举不倒填，苏楷奏议保留观点属性。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=265,year=905,
    primary_source_key=primary_autumn,primary_source_keys=[primary_autumn,primary_winter],
    paragraphs=[Q[n]['id'] for n in range(41,47)],next_paragraph=Q[47]['id'],
    coverage='卷265天祐二年第41—46段连续处理；杨行密病中召渥、朱全忠淮南行动、军额调整、光州、昭宗谥议与杨渥授任。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
