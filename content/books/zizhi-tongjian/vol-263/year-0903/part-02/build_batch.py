"""Curate Tongjian 263, year 903, consecutive paragraphs 9–15."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 16))
primary = 'tongjian-263-903-fengxiang'
primary_purge = 'tongjian-263-903-purge'
primary_commentary_a = 'tongjian-263-903-commentary-a'
primary_commentary_b = 'tongjian-263-903-commentary-b'
primary_end = 'tongjian-263-903-end'
old_five = 'jiuwudaishi-002-903-fengxiang'
new_tang = 'xintangshu-208-eunuch-purge'
new_five = 'xinwudaishi-061-shenfu-duhong'

B = {'format_version': 1, 'batch_key': 'zztj-v263-y0903-p009-p015',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-01/sources/library' / primary, 'cb7f7d8', '司马光等'),
    (primary_purge, P / 'sources/library' / primary_purge, 'c528692', '司马光等'),
    (primary_commentary_a, P / 'sources/library' / primary_commentary_a, 'c528692', '司马光等'),
    (primary_commentary_b, P / 'sources/library' / primary_commentary_b, 'c528692', '司马光等'),
    (primary_end, P / 'sources/library' / primary_end, 'c528692', '司马光等'),
    (old_five, P.parent / 'part-01/sources/library' / old_five, 'cb7f7d8', '薛居正等'),
    (new_tang, P / 'sources/library' / new_tang, 'c528692', '欧阳修、宋祁等'),
    (new_five, P / 'sources/library' / new_five, 'c528692', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, primary_purge, primary_commentary_a, primary_commentary_b, primary_end)}
for n in range(9, 16):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/263.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '李继诲':'周承诲', '李彦弼':'董彦弼', '硃友宁':'朱友宁', '侃':'宋侃', '何后':'何氏（唐昭宗皇后）', '景王秘':'李秘', '苏检女':'苏氏（苏检女、景王妃）', '硃友伦':'朱友伦', '硃瑾':'朱瑾', '友伦':'朱友伦', '可范':'第五可范', '神福':'李神福', '克用':'李克用'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_263_0903_02_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷263·天复三年（903）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷263天复三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=903):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_263_0903_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '903年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '903年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_263_0903_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_263_0903_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 9: the emperor leaves Fengxiang and reaches Chang'an.
event('emperor_leaves_fengxiang', '昭宗甲子出凤翔入朱全忠营',9,
      '甲子，车驾出凤翔，幸全忠营，全忠素服待罪。',
      [('李杰','出凤翔者'),('朱温','迎驾并素服待罪者')],
      when='903年正月甲子',place='凤翔、汴营',
      note='出城与第7段开城门不同日；“素服待罪”为朱全忠当时举止。')
event('emperor_pardons_zhu_gives_belt', '昭宗释朱全忠罪并赐玉带',9,
      '命客省使宣旨释罪，去三仗，止报平安，以公服入谢。全忠见上，顿首流涕。上命韩偓扶起之。上亦泣，曰：“宗庙社稷，赖卿再安；朕与宗族，赖卿再生。”亲解玉带以赐之。',
      [('李杰','宣旨及赐带者'),('朱温','受赦受带者'),('韩偓','奉命扶起者')],
      when='903年正月甲子',place='汴营',
      note='皇帝“再安”“再生”为当场言辞，不转为史家对朱全忠功过的结论。')
event('zhu_youlun_escorts_emperor', '朱全忠遣朱友伦扈从昭宗并焚撤凤翔诸寨',9,
      '全忠乃令硃友伦将兵扈从，自留部分后队，焚撤诸寨。友伦，存之子也。',
      [('朱温','遣将及留后队者'),('硃友伦','扈从者')],
      when='903年正月甲子',place='凤翔',
      note='朱友伦从硃友伦规范为朱字；朱存只因明示父子提及，非说其在扈从军中。')
event('emperor_reaches_xingping', '昭宗丁卯至兴平，崔胤迎谒并复相',9,
      '丁卯，至兴平，崔胤始帅百官迎谒，复以胤为司空、门下侍郎、同平章事，领三司如故。',
      [('李杰','抵达及复任者'),('崔胤','迎谒受任者')],
      when='903年正月丁卯',place='兴平',
      note='复任据原文明示，不前移至离凤翔当日。')
event('emperor_enters_changan', '昭宗己巳入长安',9,'己巳，入长安。',
      [('李杰','入京者')],when='903年正月己巳',place='长安')

# 10: Cui Yin's proposal and the massacre of eunuchs.
event('cui_yin_proposes_eunuch_reform', '崔胤奏罢宦官掌兵预政、撤内诸司使与诸道监军，昭宗从之',10,
      '请悉罢内诸司使，其事务尽归之省寺，诸道监军俱召还阙下。”上从之。',
      [('崔胤','进奏者'),('李杰','采纳者')],
      when='903年正月庚午',place='长安',
      note='崔胤奏中关于宦官致乱的长篇归因是其政治主张；只把请罢与皇帝采纳当作当日史事。')
event('zhu_kills_palace_eunuchs', '朱全忠驱第五可范等宦官于内侍省尽杀',10,
      '是日，全忠以兵驱宦官第五可范等数百人于内侍省，尽杀之，冤号之声，彻于内外。',
      [('朱温','遣兵杀戮者'),('第五可范','被杀者')],
      when='903年正月庚午',place='长安内侍省',
      note='主书记数百人，《旧五代史》五百余人，《新唐书》八百余人，分别保留；不当作统一精确数。')
event('court_orders_external_eunuch_purge', '朝廷诏诸地捕杀外出宦官，仅留黄衣幼弱三十人',10,
      '出使外方者，诏所在收捕诛之，止留黄衣幼弱者三十人以备洒扫。',
      [('李杰','下诏者')],when='903年正月庚午后',place='诸道',
      note='诏令范围与各地执行结果分开；“三十人”是保留人数。')
event('wang_rong_selects_messengers', '昭宗诏王镕选五十人充敕使',10,
      '又诏成德节度使王镕选进五十人充敕使，取其土风深厚、人性谨朴也。',
      [('李杰','下诏者'),('王镕','奉诏被令选人者')],place='成德、长安',
      note='“土风深厚、人性谨朴”为主书所记选人理由，不逐人验证。')
event('emperor_mourns_eunuchs', '昭宗为可能无罪的第五可范等作祭文',10,
      '上愍可范等或无罪，为文祭之。',
      [('李杰','作祭文者'),('可范','被悼念者')],place='长安',
      note='“或无罪”为皇帝的疑虑，未裁断所有被杀者个案。')
event('cui_yin_controls_six_armies', '朝廷改由宫人传诏，崔胤兼判六军十二卫',10,
      '自是宣传诏命，皆令宫人出入。其两军内外八镇兵悉属六军，以崔胤兼判六军十二卫事。',
      [('崔胤','兼判六军十二卫者')],place='长安',
      note='制度变动按主书记述，未据此推断所有后续军权安排。')

# 11–14 start with Sima Guang's retrospective argument, not 903 events.
reform_event='event_zztj_263_0903_cui_yin_proposes_eunuch_reform'
for n,quote,summary in [
    (11,'臣光曰：宦官用权，为国家患，其来久矣。',
     '司马光史论认为宦官专权由来已久；这是编者论断。'),
    (12,'汉不握兵，唐握兵故也。',
     '司马光比较汉唐宦官权力，认为掌兵是重要差异；这是后世史论。'),
    (13,'然则宦者之祸，始于明皇，盛于肃、代，成于德宗，极于昭宗。',
     '司马光用唐代诸朝铺陈其宦官之祸论述；并非903年新发生的事件。'),
    (14,'岂可不察臧否，不择是非，欲草薙而禽狝之，能无乱乎！',
     '司马光反对不辨个体而尽诛宦官；这是针对崔胤政策的评价。'),
]:
    used.setdefault(n,[]).append(reform_event)
    claim('event',reform_event,'description',summary,n,quote,
          '“臣光曰”及连续论述属于编纂者史论，挂接第10段改革事件作阅读证据，不录为903年事件。')

# The end of 14 resumes the chronicle after the historiographical passage.
event('wang_shifan_informs_li_keyong', '王师范遣使告李克用举兵，李克用复书褒赞',14,
      '王师范遣使以起兵告李克用，克用贻书褒赞之。',
      [('王师范','遣使告知者'),('李克用','复书者')],
      when='903年正月车驾东归前后；确日未载',
      note='本句在史论后恢复编年叙事；不把司马光史论时代当作事件时间。')
event('li_keyong_attacks_jinzhou_then_ceases', '张承业劝李克用援凤翔，李克用攻晋州后闻车驾东归乃罢',14,
      '河东监军张承业亦劝克用发兵救凤翔，克用攻晋州，闻车驾东归，乃罢。',
      [('张承业','劝兵者'),('李克用','攻晋州后罢兵者')],
      when='903年正月车驾东归前后；确日未载',place='晋州',
      note='攻晋州与闻车驾东归后罢兵有先后；未记攻克晋州。')

# 15: Huainan commands and the move against Du Hong.
event('yang_xingmi_appoints_zhu_jin', '杨行密承制加朱瑾行营副都统同平章事',15,
      '杨行密承制加硃瑾东面诸道行营副都统、同平章事',
      [('杨行密','加官者'),('硃瑾','受任者')],place='淮南',
      note='承制加官照原文，不改写为朝廷亲自任命。')
event('yang_sends_li_shenfu_against_du_hong', '杨行密任李神福行营招讨使、刘有副之，进兵攻杜洪',15,
      '以升州刺史李神福为淮南行军司马、鄂岳行营招讨使，舒州团练使刘有副之，将兵击杜洪。',
      [('杨行密','任命及遣军者'),('李神福','行营招讨使'),('刘有','副将'),('杜洪','被攻者')],
      place='鄂岳',
      note='只记任命及出兵，后续胜负留待连续下文。')
event('luo_yin_abandons_yongxing', '杜洪将骆殷弃永兴，县民方诏据城降李神福',15,
      '洪将骆殷戍永兴，弃城走，县民方诏据城降。',
      [('杜洪','骆殷原主帅'),('骆殷','弃城者'),('方诏','据城归降者'),('李神福','受降方')],
      place='永兴',
      note='方诏据城降的受降方由紧邻上下文李神福军推定，审慎写受降方；永兴县地望未核。')

person('朱存',9,'朱友伦父','友伦，存之子也。')
rel='relationship_person_朱存_person_朱友伦_父亲'
B['person_relationships'].append(dict(key=rel,person_a_key=people['朱存'],person_b_key=people['朱友伦'],
    relation_type='父亲',description='朱存是朱友伦的父亲。',status='draft'))
claim('person_relationship',rel,'description','朱存是朱友伦的父亲。',9,'友伦，存之子也。',
      '原文明示父子；朱存并非扈从队伍成员。')

extra(old_five,'event','event_zztj_263_0903_emperor_leaves_fengxiang','description',
      '《旧五代史》亦记甲子昭宗离凤翔、朱全忠素服见驾。',
      '甲子，昭宗發離鳳翔，幸左劍寨，權駐蹕帝營。帝素服待罪',9,
      'corroborates','旧五记驻左剑寨细节；与主书离凤翔及素服待罪相应。')
extra(old_five,'event','event_zztj_263_0903_zhu_kills_palace_eunuchs','description',
      '《旧五代史》记次日于内侍省杀第五可范等五百余人。',
      '誅宦官第五可范等五百餘人於內侍省',10,
      'adds','主书称数百人，旧五细化五百余；《新唐书》另称八百余，数额差异并列。')
extra(new_tang,'event','event_zztj_263_0903_zhu_kills_palace_eunuchs','description',
      '《新唐书》称崔胤朱全忠议尽诛第五可范等八百余人。',
      '胤、全忠議，盡誅第五可範等八百餘人於內侍省',10,
      'conflicts','与旧五五百余的数字不一，均为电子底本记载，纸本和口径待核。')
extra(new_five,'event','event_zztj_263_0903_yang_sends_li_shenfu_against_du_hong','description',
      '《新五代史》亦记天复三年李神福任鄂岳招讨使攻杜洪。',
      '三年，以李神福為鄂岳招討使以攻杜洪',15,
      'corroborates','以“三年”承天复年号语境；印证任官与出兵，不提前记录君山之战。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,16):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷263天复三年第9—15段连续处理；第11—14段司马光史论作归属明确的出处观点，不伪作903年事件；第14段末恢复编年史事。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=263,year=903,
    primary_source_key=primary,primary_source_keys=[primary,primary_purge,primary_commentary_a,primary_commentary_b,primary_end],
    paragraphs=[Q[n]['id'] for n in range(9,16)],next_paragraph='zztj-v264-y0903-p001',
    coverage='卷263天复三年共15个非空段落中的第9—15段连续处理；903年续于卷264。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
