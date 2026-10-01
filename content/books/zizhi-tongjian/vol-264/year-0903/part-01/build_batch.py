"""Curate Tongjian 264, year 903, consecutive paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 55))
primary = 'tongjian-264-903-february'
old_tang = 'jiutangshu-177-cui-yin'
new_tang = 'xintangshu-083-pingyuan'

B = {'format_version': 1, 'batch_key': 'zztj-v264-y0903-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P / 'sources/library' / primary, '149812f', '司马光等'),
    (old_tang, P / 'sources/library' / old_tang, '149812f', '刘昫等'),
    (new_tang, P / 'sources/library' / new_tang, '149812f', '欧阳修、宋祁等'),
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
for n in range(1, 9):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0903_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷264·天复三年（903）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷264天复三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=903):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_264_0903_' + code
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
        edge = 'participation_zztj_264_0903_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_264_0903_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 1. The decree and the survival of some eunuchs are separate actions.
event('cancel_fengxiang_appointments','昭宗下诏停凤翔所除官',1,
      '诏：“比在凤翔府所除官，一切停。”',[('李杰','下诏者')],when='903年二月壬申朔',place='长安')
event('eunuchs_hidden','张承业等宦官被诸镇庇护而免死',1,
      '张承业、幽州监军张居翰、清海监军程匡柔、西川监军鱼全禋及致仕严遵美，为李克用、刘仁恭、杨行密、王建所匿得全，斩他囚以应诏。',
      [('张承业','得全者'),('张居翰','得全者'),('程匡柔','得全者'),('鱼全禋','得全者'),('严遵美','得全者'),('李克用','庇护者之一'),('刘仁恭','庇护者之一'),('杨行密','庇护者之一'),('王建','庇护者之一')],
      when='903年二月壬申朔条；庇护发生确日未载',note='原文分别列出五名得全者、四名庇护者，未逐一配对；另有囚徒被替杀，身份不明。')

# 2. Cui Yin's response to Lu Yi and the separate executions.
event('lu_yi_demoted','崔胤奏贬陆扆为沂王傅分司',2,
      '扆曰：“茂贞罪虽大，然朝廷未与之绝，今独无诏书，示人不广。”崔胤怒，奏贬之。',
      [('陆扆','因进言而被贬者'),('崔胤','奏贬者')],when='903年二月甲戌',place='长安',
      note='陆扆对凤翔未赐诏的评语是其发言；沂王傅分司官名见本段开头。')
event('song_rou_executed','宋柔等宫人及与宦官亲厚者被杖杀',2,
      '宫人宋柔等十一人皆韩全诲所献，及僧、道士与宦官亲厚者二十馀人，并送京兆杖杀。',
      [('宋柔','被杖杀者'),('韩全诲','先前献宫人者')],when='903年二月甲戌条；确日未载',place='京兆',
      note='十一宫人与二十余僧道及亲厚者分组记；韩全诲早先所献是追述，并非本日行动。')

# 3. This is an attributed exchange rather than a proven judgment of Cui Yin.
event('emperor_han_wo_dialogue','昭宗与韩偓议崔胤用机数',3,
      '上谓韩偓曰：“崔胤虽尽忠，然比卿颇用机数。”对曰：“凡为天下者，万国皆属之耳目，安可以机数欺之！莫若推诚直致，虽日计之不足，而岁计之有馀也。”',
      [('李杰','发问并评价者'),('韩偓','答言者'),('崔胤','被议论者')],
      when='903年二月；确日未载',note='“尽忠”“用机数”是昭宗发言，韩偓答语是其政见，不转作客观裁断。')

# 4. Keep distinct dates and distinguish proposals, appointments and failed action.
event('su_lu_forced_suicide','苏检与卢光启被赐自尽',4,
      '丙子，工部侍郎、同平章事苏检，吏部侍郎卢光启，并赐自尽。',
      [('苏检','被赐自尽者'),('卢光启','被赐自尽者')],when='903年二月丙子')
event('wang_pu_demoted','王溥改太子宾客分司',4,
      '丁丑，以中书侍郎、同平章事王溥为太子宾客、分司',
      [('王溥','改授者')],when='903年二月丁丑')
event('reward_reception','昭宗赐朱全忠及僚将迎銮功臣号',4,
      '戊寅，赐硃全忠号回天再造竭忠守正功臣，赐其僚佐敬翔等号迎銮协赞功臣，诸将硃友宁等号迎銮果毅功臣，都头以下号四镇静难功臣。',
      [('朱温','受号者'),('敬翔','受号僚佐之一'),('朱友宁','受号诸将之一')],when='903年二月戊寅',
      note='四类受号群体按原文保留；硃全忠规范为朱温，来源照原字。')
event('li_zuo_marshal','崔胤固请后昭宗任辉王李祚为诸道兵马元帅',4,
      '胤承全忠密旨，利祚冲幼，固请之。己卯，以祚为诸道兵马元帅。',
      [('崔胤','固请者'),('朱温','密旨授意者'),('李祚','受任者'),('李杰','任命者')],
      when='903年二月己卯',note='昭宗原提及年长濮王，但最终任辉王祚；李祚由爵名辉王祚规范，身份待异书校。')
event('zhu_liang_king','朱全忠加太尉副元帅进梁王，崔胤升司徒兼侍中',4,
      '庚辰，加全忠守太尉，充副元帅，进爵梁王。以胤为司徒兼侍中。',
      [('朱温','受封梁王并加官者'),('崔胤','受任司徒兼侍中者')],when='903年二月庚辰')
event('fengxiang_court_exile','从昭宗幸凤翔的朝臣三十余人被贬逐',4,
      '朝臣从上幸凤翔者，凡贬逐三十馀人。',
      [('崔胤','掌握贬逐权势者')],when='903年二月庚辰条；逐人日期未载',
      note='群体人数据本段；“恃势专权”为史书叙述，未据此补造逐人受贬日期。')
event('jing_zhu_appointments','敬翔守太府卿、朱友宁领宁远节度使',4,
      '以敬翔守太府卿，硃友宁领宁远节度使。',
      [('敬翔','受任太府卿者'),('朱友宁','受任宁远节度使者')],when='903年二月庚辰条')
event('fu_daozhao_failed_qinzhou','朱全忠表苻道昭任天雄节度使，护送秦州未达',4,
      '全忠表苻道昭同平章事，充天雄节度使，遣兵援送之秦州，不得至而还。',
      [('朱温','上表及遣兵者'),('苻道昭','被表荐及护送者')],when='903年二月庚辰条；确日未载',place='秦州',
      note='表荐与到任有别；原文明确不得至秦州。')

# 5. The examination appointment is a retrospective with no established year.
event('zhao_chong_examiner','赵崇主持韩偓登第时贡举',5,
      '初，翰林学士承旨韩偓之登进士第也，御史大夫赵崇知贡举。',
      [('韩偓','登第者'),('赵崇','知贡举者')],when='早年追叙；确年未载',year=None,
      note='“初”引出的追叙，不填903年。')
event('han_wo_recommends_successors','昭宗拟以韩偓为相，韩偓荐赵崇王赞自代',5,
      '上返自凤翔，欲用偓为相，偓荐崇及兵部侍郎王赞自代。',
      [('李杰','拟任者'),('韩偓','被拟任并推荐者'),('赵崇','被推荐者'),('王赞','被推荐者')],
      when='903年返自凤翔后；确日未载',note='拟任与推荐均非实际拜相。')
event('han_wo_demoted','朱全忠反对荐相后韩偓贬濮州司马',5,
      '上见全忠怒甚，不得已，癸未，贬偓濮州司马。',
      [('朱温','反对荐相者'),('李杰','贬官者'),('韩偓','被贬者')],when='903年二月癸未',place='濮州',
      note='朱全忠反对赵崇王赞见前文；韩偓称将来篡弑之辱为警告，不记录为当时既成事实。')

# 6-8. The princess is already an entity in volume 263.
event('pingyuan_returned','昭宗令朱全忠致书李茂贞取回平原公主',6,
      '己丑，上令硃全忠与李茂贞书，取平原公主。茂贞不敢违，遽归之。',
      [('李杰','下令者'),('朱温','致书索还者'),('李茂贞','归还者'),('平原公主','被迎回者')],
      when='903年二月己丑',note='平原公主复用卷263已有人物；与此前嫁宋侃的记述衔接。')
event('zhu_youyu_zhenguo','朱友裕任镇国节度使',7,
      '壬辰，以硃友裕为镇国节度使。',[('朱友裕','受任者')],when='903年二月壬辰')
event('zhu_guard_garrison','朱全忠奏留步骑万人驻故两军',8,
      '乙未，全忠奏留步骑万人于故两军',
      [('朱温','奏留军者')],when='903年二月乙未',place='长安',
      note='原文记“奏留”，不把万人驻军进一步写为已完成实数。')
event('zhu_guard_offices','朱友伦张廷范王殷蒋玄晖分任禁卫京辅职',8,
      '以硃友伦为左军宿卫都指挥使，又以汴将张廷范为宫苑使，王殷为皇城使，蒋玄晖充街使。',
      [('朱友伦','左军宿卫都指挥使'),('张廷范','宫苑使'),('王殷','皇城使'),('蒋玄晖','街使')],
      when='903年二月乙未',place='长安')
event('zhu_departs_court','朱全忠戊戌辞归镇，昭宗与百官送别',8,
      '戊戌，全忠辞归镇，留宴寿春殿，又饯之于延喜楼。',
      [('朱温','辞归镇者'),('李杰','设宴送别者')],when='903年二月戊戌',place='寿春殿、延喜楼')
event('cui_farewell','崔胤送朱全忠至霸桥后入宫再对昭宗',8,
      '崔胤独送至霸桥，自置饯席，夜二鼓，胤始还入城。上复召对，问以全忠安否，置酒奏乐，至四鼓乃罢。',
      [('崔胤','送别后入宫者'),('朱温','被送别者'),('李杰','召对者')],
      when='903年二月戊戌夜',place='霸桥、长安')

extra(old_tang,'event','event_zztj_264_0903_fengxiang_court_exile','description',
      '《旧唐书》卷177也记还京后崔胤贬逐从幸群官三十余人。',
      '應從幸群官，貶逐者三十余人',4,'corroborates','旧唐书同段列陆扆、王溥、韩偓等；具体官名有异，不以此覆盖通鉴。')
extra(old_tang,'event','event_zztj_264_0903_han_wo_demoted','description',
      '《旧唐书》卷177记韩偓被贬濮州司户，与通鉴濮州司马官名不同。',
      '韓偓濮州司戶',5,'conflicts','官名异文并列，待核纸本；不修改通鉴所记司马。')
extra(new_tang,'event','event_zztj_264_0903_pingyuan_returned','description',
      '《新唐书》卷83亦记平原公主被朱全忠致书索还；其前夫名作李继偘。',
      '朱全忠移茂貞書，取主還京師',6,'adds','新唐书称李茂贞子李继偘，既有通鉴批次称宋侃；身份异名待校，不因繁简差异合并。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天复三年第1—8段连续处理；繁简字形按既有人物规范匹配，原文照录；追叙、发言和异文未误作903年已证史事。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=903,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],
    coverage='卷264天复三年共54个非空段落中的第1—8段连续处理；同年后续仍待录入。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
