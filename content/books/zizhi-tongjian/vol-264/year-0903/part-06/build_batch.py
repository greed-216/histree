"""Curate Tongjian 264, year 903, consecutive paragraphs 33–36."""
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
primary = 'tongjian-264-903-august'
new_background = 'xinwudaishi-061-tian-jun-background'
new_annals = 'xinwudaishi-061-yang-xingmi'
old_du = 'jiuwudaishi-024-du-xunhe'
old_qingzhou = 'jiuwudaishi-002-qingzhou'

B = {'format_version': 1, 'batch_key': 'zztj-v264-y0903-p033-p036',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-05/sources/library' / primary, 'e36b962', '司马光等'),
    (new_background, P / 'sources/library' / new_background, '33d866a', '欧阳修等'),
    (new_annals, P.parent / 'part-02/sources/library' / new_annals, '71feb52', '欧阳修等'),
    (old_du, P / 'sources/library' / old_du, '33d866a', '薛居正等'),
    (old_qingzhou, P / 'sources/library' / old_qingzhou, '33d866a', '薛居正等'),
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
for n in range(33, 37):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范','李存审':'符存审','王宗本':'谢从本'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0903_06_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_264_0903_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 33. The opening “初” retells causes; only the eventual revolt belongs to this year.
event('tian_requests_chi_she','田頵胜冯弘铎后向杨行密请池歙，杨行密拒绝',33,
      '初，宁国节度使田頵破冯弘鐸，诣广陵谢杨行密，因求池、歙为巡属，行密不许。',
      [('田頵','请增巡属者'),('杨行密','拒绝者')],
      when='“初”追叙；葛山胜后，确日未载',year=None,place='广陵',
      note='田頵破冯弘铎已在902年卷263批次录入，不重复建战役；本条仅记战后请地与拒绝，确年不定。')
event('tian_angry_bribes','田頵于广陵被索赂后愤而称不再入城',33,
      '行密左右下及狱吏，皆救赂于頵，頵怒曰：“吏知吾将下狱邪！”及还，指广陵南门曰：“吾不可复入此矣！”',
      [('田頵','被索赂并发言者')],
      when='“初”追叙；确年未载',year=None,place='广陵',
      note='底本作“救赂”，疑为“求赂”讹字，原文照录；两句话都是田頵所说，不把将下狱当事实。')
event('yang_tian_policy_conflict','杨行密抑田頵攻取并与钱镠和解，田頵生怨',33,
      '行密既定淮南，欲保境息民，每抑止之，頵不从。及解释钱镠，頵尤恨之，阴有叛志。',
      [('杨行密','抑扩张并和解者'),('田頵','不从且生怨者'),('钱镠','和解对象')],
      when='叛乱前长期背景；起止年未载',year=None,
      note='“欲保境息民”与“尤恨”属主书叙事归因；不把叛志等同已举兵。')
event('li_shenfu_warns_tian','李神福预警田頵将反，杨行密未先杀之',33,
      '李神福言于行密曰：“頵必反，宜早图之。”行密曰：“頵有大功，反状未露，今杀之，诸将人人自危矣！”',
      [('李神福','预警者'),('杨行密','拒先杀者'),('田頵','预警对象')],
      when='田頵明叛前；确日未载',
      note='“必反”是李神福判断；杨行密明确称反状未露，不能前置为已反。')
event('kang_ru_killed','杨行密擢康儒庐州刺史，田頵疑其贰己而族之',33,
      '頵有良将曰康儒，与頵谋议多不合，行密知之，擢儒为庐州刺史。頵以儒为贰于己，族之。',
      [('杨行密','擢任者'),('康儒','被擢后遭族诛者'),('田頵','族诛者')],
      when='田頵举兵前；确日未载',place='庐州',
      note='“以儒为贰”是田頵怀疑，不等于康儒确曾背叛。')
event('tian_an_rebel','田頵与安仁义同举兵，安仁义焚东塘战舰',33,
      '頵遂与润州团练使安仁义同举兵，仁义悉焚东塘战舰。',
      [('田頵','举兵者'),('安仁义','同举兵并焚舰者')],
      when='903年八月至九月间；确日未载',place='润州、东塘',
      note='本段转入当前编年叙事；先前不满及预警与实际举兵分开。')
event('tian_envoys_zhu_yanshou','田頵遣伪装商人的使者约朱延寿，尚公乃识破获书',33,
      '頵遣二使诈为商人，诣寿州约奉国节度使硃延寿，行密将尚公乃遇之，曰：“非商人也。”杀一人，得其书，以告行密。',
      [('田頵','遣使约盟者'),('朱延寿','被约盟者'),('尚公乃','识破并截获书者'),('杨行密','受报告者')],
      when='903年田頵举兵后；确日未载',place='寿州',
      note='使者一人被杀、书信被获；此句只说约朱延寿，不写成当时约盟已成。')
event('yang_recalls_li_shenfu','杨行密召李神福回师讨田頵，神福佯称攻荆南后东下',33,
      '行密召李神福于鄂州，神福恐杜洪邀之，宣言奉命攻荆南，勒兵具舟楫。及暮，遂沿江东下，始告将士以讨田頵。',
      [('杨行密','召回者'),('李神福','率军东下者'),('杜洪','神福所防截者'),('田頵','讨伐目标')],
      when='903年田頵举兵后；确日未载',place='鄂州、长江',
      note='攻荆南为李神福掩饰行军的宣称，真正目标是田頵；杜洪邀击只是神福担忧。')

# 34. Changzhou raid and Wang Maozhang/Xu Wen's counterattack.
event('an_renyi_changzhou','安仁义己丑袭常州，李遇拒战，安仁义疑伏而退',34,
      '己丑，安仁义袭常州，常州刺史李遇逆战，极口骂仁义，仁义曰：“彼敢辱我，必有备。”乃引去。',
      [('安仁义','袭城后撤者'),('李遇','拒战并激言者')],
      when='903年八月己丑',place='常州',
      note='“必有备”是安仁义的判断；原文没有证实伏兵。')
event('wang_maozhang_xu_wen_runzhou','杨行密任王茂章讨安仁义，徐温伪装援军后击败仁义',34,
      '壬辰，行密以王茂章为润州行营招讨使，击仁义，不克，使徐温将兵会之。温易其衣服旗帜，皆如茂章兵，仁义不知益兵，复出战，温奋击，破之。',
      [('杨行密','任命并遣援者'),('王茂章','招讨使'),('徐温','伪装援军并破敌者'),('安仁义','败方')],
      when='903年八月壬辰及后续；确日未载',place='润州',
      note='王茂章先攻不克，徐温增援后才得胜；不将两战合为一次。')

# 35. Family tie, conspiracy, and contacts with Zhu Quanzhong.
event('zhu_yanshou_plots_tian','朱延寿因怨杨行密而密与田頵通谋',35,
      '行密狎侮延寿，延寿怨怒，阴与田頵通谋。',
      [('杨行密','被怨对象'),('朱延寿','密谋者'),('田頵','共谋者')],
      when='903年八月田頵举兵前后；确日未载',
      note='狎侮为史书归因，密谋是明文事实；与第33段使者尚未谈成时点不可混同。')
event('du_xunhe_missions','田頵遣杜荀鹤访朱延寿结盟，继赴大梁告朱全忠',35,
      '頵遣前进士杜荀鹤至寿州，与延寿相结，又遣至大梁告硃全忠',
      [('田頵','遣使者'),('杜荀鹤','往寿州及大梁者'),('朱延寿','寿州结盟者'),('朱温','大梁受告者')],
      when='903年八月；确日未载',place='寿州、大梁',
      note='杜荀鹤为田頵使者，与此前伪装商人的两名使者分开。')
event('zhu_supports_tian','朱全忠闻杜荀鹤告变后遣兵屯宿州策应',35,
      '全忠大喜，遣兵屯宿州以应之。',
      [('朱温','遣兵策应者')],when='903年八月；确日未载',place='宿州',
      note='“大喜”依史书记当时反应；未据此推断宿州兵实际战果。')

# 36. September Linqu defeat and next-day relief failure.
event('yang_shihou_linqiu_ruse','杨师厚屯临朐声称将去密州，留辎重诱王师范出战',36,
      '杨师厚屯临朐，声言将之密州，留辎重于临朐。',
      [('杨师厚','佯言并留辎重者')],when='903年九月癸卯前；确日未载',place='临朐',
      note='“声言将之密州”是杨师厚对外说法，不写成其已至密州。')
event('linqiu_september_battle','王师范癸卯攻临朐中伏大败，王师克被俘',36,
      '九月，癸卯，王师范出兵攻临朐，师厚伏兵奋击，大破之，杀万馀人，获师范弟师克。',
      [('王师范','出兵败方'),('杨师厚','伏击胜方'),('王师克','被俘者')],
      when='903年九月癸卯',place='临朐',
      note='“万馀人”是主书记数；《旧五代史》亦称俘师克，其他传记有师鲁攻临朐的叙事，不强行合一。')
event('laizhou_relief_defeated','杨师厚次日击溃莱州救青州兵并移寨逼城',36,
      '明日，莱州兵五千救青州。师厚邀击之，杀获殆尽，遂徙寨抵其城下。',
      [('杨师厚','邀击并移寨者')],
      when='903年九月癸卯次日',place='青州附近',
      note='五千及“殆尽”为主书记数与概述；未指名莱州军主将。')

person('朱氏（杨行密夫人）',35,'杨行密夫人、朱延寿之姊','行密夫人，硃延寿之姊也。')
for code,a,b,kind,description,n,quote,note in [
    ('yang_wife',people['朱氏（杨行密夫人）'],people['杨行密'],'妻子','朱氏是杨行密的妻子。',35,'行密夫人，硃延寿之姊也。','“夫人”仅证妻子身份，不补姓名。'),
    ('zhu_sister',people['朱氏（杨行密夫人）'],people['朱延寿'],'姐姐','朱氏是朱延寿的姐姐。',35,'行密夫人，硃延寿之姊也。','原文明示“姊”，方向为朱氏相对朱延寿。'),
]:
    key='relationship_zztj_264_0903_'+code
    B['person_relationships'].append(dict(key=key,person_a_key=a,person_b_key=b,
        relation_type=kind,description=description,status='draft'))
    claim('person_relationship',key,'description',description,n,quote,note)
person('王师范',36,'王师克兄','获师范弟师克')
rel='relationship_person_王师范_person_王师克_兄长'
B['person_relationships'].append(dict(key=rel,person_a_key=people['王师范'],
    person_b_key=people['王师克'],relation_type='兄长',
    description='王师范是王师克的兄长。',status='draft'))
claim('person_relationship',rel,'description','王师范是王师克的兄长。',36,
      '获师范弟师克','“弟师克”明确王师范较长。')

extra(new_background,'event','event_zztj_264_0903_tian_angry_bribes','description',
      '《新五代史》卷61也记田頵在广陵被将吏索赂而愤怒。',
      '頵嘗計事廣陵，行密諸將多就頵求賂，而獄吏亦有所求',33,'corroborates',
      '通鉴底本“救赂”疑讹，新五代史明确作“求賂”；仅校词，不改原文。')
extra(new_annals,'event','event_zztj_264_0903_tian_an_rebel','description',
      '《新五代史》杨行密世家记田頵叛，随后袭升州。',
      '田頵叛，襲昇州',33,'corroborates',
      '只以“田頵叛”印证本段举兵；袭升州留待下一段继续。')
extra(old_du,'event','event_zztj_264_0903_du_xunhe_missions','description',
      '《旧五代史》杜荀鹤传亦记田頵将起兵时遣其通报朱全忠。',
      '頵將起兵，乃陰令以箋問至，太祖遇之頗厚',35,'corroborates',
      '旧五代史作起兵前通报，通鉴此处记举兵叙事后；时点及先后留存差异。')
extra(old_qingzhou,'event','event_zztj_264_0903_linqiu_september_battle','description',
      '《旧五代史》卷2亦记九月癸卯临朐大败王师范、俘师克。',
      '九月癸卯，師厚率大軍與王師範戰於臨朐，青軍大敗，殺萬餘人，並擒師範弟師克',36,'corroborates',
      '旧五代史与通鉴同记师克；本批未据别传的师鲁异说改写主书。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(33,37):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天复三年第33—36段连续处理；初叙背景不强定年，发言与事实分离，田頵举兵及临朐战果按原书顺序。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=903,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(33,37)],next_paragraph=Q[37]['id'],
    coverage='卷264天复三年共54个非空段落中的第33—36段连续处理；第33段长篇背景与叛乱分录。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
