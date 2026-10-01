"""Curate Tongjian 262, year 901, consecutive paragraphs 49–53."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 54))
primary_prev = 'tongjian-262-901-yearend'



new_tang_annals = 'xintangshu-010-901-yearend'
new_tang_yang = 'xintangshu-188-901-linan'


B = {'format_version': 1, 'batch_key': 'zztj-v262-y0901-p049-p053',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_prev, P.parent / 'part-06/sources/library' / primary_prev, '67393c4', '司马光等'),
    (new_tang_annals, P / 'sources/library' / new_tang_annals, '536cf68', '欧阳修等'),
    (new_tang_yang, P / 'sources/library' / new_tang_yang, '536cf68', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_prev,)}
for n in range(49, 54):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/262.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅', '李存审': '符存审', '李继昭':'孙德昭', '李继诲':'周承诲', '李彦弼':'董彦弼', '吉谏':'王宗黯', '李继徽':'杨崇本'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_262_0901_07_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷262·天复元年（901）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷262天复元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=901):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_262_0901_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '901年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '901年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_262_0901_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_262_0901_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 49: Qinghai succession; preserve the New Tang annals' different emphasis.
event('xu_yanruo_dies', '清海节度使徐彦若卒',49,
      '清海节度使徐彦若薨', [('徐彦若','卒者')],
      when='901年十二月条；确日未载',place='清海军')
claim('person',people['徐彦若'],'death_year','徐彦若于901年卒。',49,
      '清海节度使徐彦若薨','本年十二月条，确日不明。')
event('xu_recommends_liu_yin', '徐彦若遗表荐刘隐权清海留后',49,
      '遗表荐行军司马刘隐权留后。',
      [('徐彦若','遗表荐人者'),('刘隐','被荐权留后者')],
      when='901年徐彦若卒时',place='清海军',
      note='遗表为荐举，不写朝廷已正式任命；新唐书作刘隐自称留后，独立保留。')
extra(new_tang_annals,'event','event_zztj_262_0901_xu_recommends_liu_yin','description',
      '《新唐书》本纪记徐彦若卒后刘隐自称留后；《通鉴》强调徐遗表荐其权留后。',
      '清海軍節度使徐彥若卒，行軍司馬劉隱自稱留後',49,'adds',
      '两书不必互斥：遗表与自称可先后或并存，暂不定朝廷正式批准。')

# 50: Lin'an withdrawal and peace after the earlier capture of Gu Quanwu.
event('li_shenfu_recognizes_qian_alive', '李神福确认钱镠未死且临安难克，谋求退兵',50,
      '李神福知钱镠定不死，而临安城坚，久攻不拔，欲归，恐为镠所邀',
      [('李神福','谋退者'),('钱镠','仍在世且被担心截击者')],
      when='901年十二月条；确日未载',place='临安',
      note='证实先前死讯是误传；久攻不拔不能写为已攻克临安。')
event('li_shenfu_protects_qian_ancestral_tombs', '李神福遣人护钱镠祖考墓并使顾全武通信',50,
      '乃遣人守卫镠祖考丘垄，禁樵采，又使顾全武通家信。',
      [('李神福','遣人护墓并促通信者'),('顾全武','传家信者'),('钱镠','祖考墓获保护者')],
      when='901年李神福谋退时',place='临安附近',
      note='顾全武此前被俘，此处仍可通家信；不写已获释。')
event('qian_liu_thanks_li_shenfu', '钱镠遣使谢李神福护墓',50,
      '镠遣使谢之。',
      [('钱镠','遣谢者'),('李神福','受谢者')],
      when='901年李神福护墓后')
event('li_shenfu_uses_false_camps', '李神福张虚寨诱钱镠以为淮南援军大至',50,
      '神福于要路多张旗帜为虚寨，镠以为淮南兵大至',
      [('李神福','设虚寨者'),('钱镠','误判者')],
      when='901年临安对峙末',place='临安要路',
      note='多张旗帜为虚寨，不能记为援兵确已到达。')
event('qian_li_peace_shenfu_returns', '钱镠请和，李神福受犒退兵',50,
      '遂请和。神福受其犒赂而还。',
      [('钱镠','请和者'),('李神福','受犒退兵者')],
      when='901年临安对峙末',place='临安',
      note='请和与退兵明确；未载具体盟约条款。')
extra(new_tang_yang,'event','event_zztj_262_0901_qian_li_peace_shenfu_returns','description',
      '《新唐书》杨行密传亦记李神福护钱镠先墓、受犒而还。',
      '神福乃令軍中護鏐先墓，禁樵采，鏐遣使者厚謝。神福以鏐不死，臨安未可下，納犒而還',50,'corroborates',
      '印证护墓、钱镠未死、受犒退兵；新唐此段未述虚寨细节。')

# 51: Jinzhou envoys and Wang Jian's two-sided diplomacy.
event('feng_xingxi_sends_lu_to_zhu', '冯行袭遣副使鲁崇矩听朱全忠命',51,
      '硃全忠之入关也，戎昭节度使冯行袭遣副使鲁崇矩听命于全忠。',
      [('冯行袭','遣使者'),('鲁崇矩','奉命者'),('朱温','受听命者')],
      when='朱全忠入关时；确日未载',place='金州、关中',
      note='“之入关也”回叙阶段，不强定为十二月当日。')
event('han_quanhui_sends_eunuchs_jinzhou', '韩全诲遣中使二十余人征江淮兵屯金州',51,
      '韩全诲遣中使二十馀人分道征江、淮兵屯金州，以胁全忠',
      [('韩全诲','遣使征兵者'),('朱温','被施压者')],
      when='901年朱全忠入关期间',place='金州',
      note='二十余为中使人数，不是征集兵数；中使未逐名。')
event('feng_kills_eunuchs_sends_edicts', '冯行袭杀韩全诲中使并以诏敕送朱全忠',51,
      '行袭尽杀中使，收其诏敕送全忠。',
      [('冯行袭','杀使并送诏者'),('朱温','受诏敕者')],
      when='901年中使至金州后',place='金州',
      note='死亡人数承上二十余中使，未据此列出姓名。')
event('han_zhu_seek_wang_jian', '韩全诲与朱全忠分别遣使向王建征请兵',51,
      '又遣中使征兵于王建，硃全忠亦遣使乞师于建。',
      [('韩全诲','遣中使征兵者'),('朱温','遣使乞师者'),('王建','受双方请求者')],
      when='901年金州遣使后',
      note='韩与朱为各自独立请求，不能写为共同向王建求援。')
event('wang_jian_two_sided_policy', '王建外好朱全忠而暗劝李茂贞坚守',51,
      '建外修好于全忠，罪状李茂贞，而阴劝茂贞坚守，许之救援。',
      [('王建','公开修好并暗中许援者'),('朱温','公开修好对象'),('李茂贞','被公开声讨、私下劝援者')],
      when='901年韩朱求兵后',
      note='外好与暗劝并列；许援为承诺，不写王建已实际交付援军。')
event('wang_jian_sends_escort_diversion', '王宗佶王宗涤率五万称迎驾实袭李茂贞山南诸州',51,
      '以武信节度使王宗佶、前东川节度使王宗涤等为扈驾指挥使，将兵五万，声言迎军驾，其实袭茂贞山南诸州。',
      [('王宗佶','领兵者'),('王宗涤','领兵者'),('李茂贞','山南州受攻者')],
      when='901年王建两面应对后',place='山南诸州',
      note='五万为两将等所将合数；“声言迎驾”与主书所述实袭分开。')

# 52–53: Fuzhou settlement, recollection of a tiger hunt, and Wuzhen succession.
event('zhong_chuan_besieges_fu', '钟传围危全讽抚州',52,
      '江西节度使钟传将兵围抚州刺史危全讽',
      [('钟传','围城者'),('危全讽','守抚州者')],
      when='901年年末条；确日未载',place='抚州')
event('zhong_chuan_refuses_fire_assault', '抚州失火，钟传拒乘火进攻并祝勿害民',52,
      '天火烧其城，士民欢惊。诸将请急攻之，传曰：“乘人之危，非仁也。”乃祝曰：“全讽之罪，无为害民。”火寻止。',
      [('钟传','拒急攻并祈祷者'),('危全讽','被围者')],
      when='901年抚州被围时',place='抚州',
      note='“天火”保原称，不推定人为纵火；火止是主书叙述，不据此证明祈祷造成熄火。')
event('wei_quanfeng_submits_marriage', '危全讽谢罪听命并嫁女于钟传子匡时',52,
      '全讽闻之，谢罪听命，以女妻传子匡时。',
      [('危全讽','谢罪并嫁女者'),('钟传','受归附者'),('钟匡时','娶危女者')],
      when='901年抚州火止后',place='抚州',
      note='危氏之女未具名，不造姓名；传子匡时即钟传之子。')
rel='relationship_person_钟传_person_钟匡时_父亲'
B['person_relationships'].append(dict(key=rel,person_a_key=people['钟传'],person_b_key=people['钟匡时'],
    relation_type='父亲',description='《资治通鉴》901年条称匡时为钟传之子。',status='draft'))
claim('person_relationship',rel,'description','钟传是钟匡时的父亲。',52,
      '以女妻传子匡时。','主书明示“传子匡时”，按A是B父亲定向。')
event('zhong_chuan_tiger_anecdote', '钟传早年醉猎与虎搏斗后戒诸子勿恃勇',52,
      '传少时尝猎，醉遇虎，与斗，虎搏其肩，而传亦持虎腰不置。旁人共杀虎，乃得免。既贵，悔之，常戒诸子曰：“士处世贵智谋，勿效吾暴虎也。”',
      [('钟传','早年遇虎并后来戒子者')],
      when='少时遇虎；既贵后戒子，确年均未载',place=None,year=None,
      note='这是同段追叙与后评，不写为901年抚州围城时发生。')
event('lei_man_dies', '武贞节度使雷满卒',53,
      '武贞节度使雷满薨',
      [('雷满','卒者')],when='901年年末条；确日未载',place='武贞军')
claim('person',people['雷满'],'death_year','雷满于901年卒。',53,
      '武贞节度使雷满薨','本年年末条，确日未载。')
event('lei_yanwei_self_appointed', '雷满之子雷彦威自称留后',53,
      '子彦威自称留后。',
      [('雷彦威','自称留后者')],when='901年雷满卒后',place='武贞军',
      note='自称不等于朝廷正式任命。')
rel='relationship_person_雷满_person_雷彦威_父亲'
B['person_relationships'].append(dict(key=rel,person_a_key=people['雷满'],person_b_key=people['雷彦威'],
    relation_type='父亲',description='《资治通鉴》901年条称雷彦威为雷满之子。',status='draft'))
claim('person_relationship',rel,'description','雷满是雷彦威的父亲。',53,
      '武贞节度使雷满薨，子彦威自称留后。','主书明示父子，按A是B父亲定向。')
extra(new_tang_annals,'event','event_zztj_262_0901_lei_yanwei_self_appointed','description',
      '《新唐书》本纪同记雷满卒后其子彦威自称留后。',
      '武貞軍節度使雷滿卒，其子彥威自稱留後',53,'corroborates',
      '印证父子及自称；不视作朝廷授节度。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(49,54):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='第49—53段连续校核：徐彦若卒刘隐留后、临安和退兵、金州征使与王建两面应对、抚州和议及雷彦威自称留后。虎猎为早年追叙，确年未定；新唐书补刘隐自称异叙。原文件93—94为空行，已排除段落计数。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=262,year=901,
    primary_source_key=primary_prev,primary_source_keys=[primary_prev],
    paragraphs=[Q[n]['id'] for n in range(49,54)],next_paragraph='zztj-v263-y0902-p001',
    coverage='天复元年53个非空段落中的第49—53段连续处理；原文件第93—94行为空行，本年正文至第92行。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
