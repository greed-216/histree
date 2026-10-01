"""Curate Tongjian 262, year 901, consecutive paragraphs 17–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 56))
primary_prev = 'tongjian-262-901-feb-apr'
primary = 'tongjian-262-901-may-june'

old_five = 'jiuwudaishi-002-901-hezhong-taiyuan'
old_five_jin = 'jiuwudaishi-026-901-jin-retreat'
new_five = 'xinwudaishi-004-901-jin'

B = {'format_version': 1, 'batch_key': 'zztj-v262-y0901-p017-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_prev, P.parent / 'part-02/sources/library' / primary_prev, '0e8e093', '司马光等'),
    (primary, P / 'sources/library' / primary, '8f5b1e1', '司马光等'),
    (old_five, P.parent / 'part-02/sources/library' / old_five, '0e8e093', '薛居正等'),
    (old_five_jin, P / 'sources/library' / old_five_jin, '8f5b1e1', '薛居正等'),
    (new_five, P.parent / 'part-02/sources/library' / new_five, '0e8e093', '欧阳修'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_prev, primary)}
for n in range(17, 25):
    assert Q[n]['text'] in ''.join(primary_texts.values()), (n, Q[n]['text'][:30])

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅', '李存审': '符存审'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and Q[n]['text'] in data)

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_262_0901_03_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷262·天复元年（901）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷262天复元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, Q[n]['text'],
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
        pk = person(name, n, role)
        edge = 'participation_zztj_262_0901_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_262_0901_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 17–18: amnesty and the court's brewing monopoly.
event('emperor_visits_temple', '昭宗甲戌谒太庙', 17, '甲戌，上谒太庙。',
      [('李杰','谒庙者')],when='901年四月甲戌',place='太庙')
event('amnesty_era_change', '昭宗丁丑赦天下并改元', 17, '丁丑，赦天下，改元。',
      [('李杰','颁赦并改元者')],when='901年四月丁丑',
      note='原文未在本句列新年号，不据此句推具体称号。')
event('rehabilitates_wang_ya_families', '朝廷为王涯等十七家昭雪',17,
      '雪王涯等十七家。',[('王涯','被昭雪十七家之一')],when='901年四月丁丑赦后',
      note='仅王涯具名；十七为家数，不造另外十六家具体人名。')
event('yang_fugong_withholds_qu_tax', '杨复恭旧借卖曲一年利后未归度支',18,
      '初，杨复恭为中尉，借度支卖曲之利一年以赡两军，自是不肯复归。',
      [('杨复恭','借款并未归还者')],when='初；确年未载',year=None,
      note='“初”追叙，不能强定901年；卖曲之利借一年不等于实际借贷只持续一年。')
event('cui_yin_changes_qu_tax', '崔胤草赦开放自造曲并按月输榷酤钱',18,
      '至是，崔胤草赦，欲抑宦官，听酤者自造曲，但月输榷酤钱。',
      [('崔胤','草赦修改曲税者')],when='901年四月赦令时',
      note='开放造曲而保留按月缴税；“欲抑宦官”是原文对动机的叙述。')
event('army_qu_stock_deadline', '两军旧曲被令降价出售，七月后禁售',18,
      '两军先所造曲，趣令减价卖之，过七月无得复卖。',
      [('崔胤','草赦推动限制者')],when='901年四月赦令；限七月后禁售',
      note='七月为销售截止而非赦令颁日；两军先前库存不限于当月酿造。')

# 19: East Sichuan succession request.
event('wang_zongdi_requests_replacement', '东川王宗涤因病求代',19,
      '东川节度使王宗涤以疾求代', [('王宗涤','因病求代者')],
      when='901年四月后；确日未载',place='东川')
event('wang_jian_nominates_zongyu', '王建表王宗裕为东川留后',19,
      '王建表马步使王宗裕为留后。',
      [('王建','上表者'),('王宗裕','被表留后者')],when='901年王宗涤求代后',place='东川',
      note='王建上表是请求，未据此句写朝廷正式任命。')

# 20: siege of Jinyang, withdrawal, pursuit and Fen/Lu consequences.
event('shu_besieges_jinyang', '氏叔琮军抵晋阳挑战，李克用登城备御',20,
      '氏叔琮等引兵抵晋阳城下，数挑战，城中大恐。李克用登城备御，不遑饮食。',
      [('氏叔琮','率军挑战者'),('李克用','登城备御者')],
      when='901年四月；确日未载',place='晋阳',
      note='数挑战不是已攻陷，李克用仍守城。')
event('jinyang_repairs_rain_damage', '晋阳久雨城坏而随坏随修',20,
      '时大雨积旬，城多颓坏，随加完补。',when='901年四月晋阳受攻时',place='晋阳',
      note='积旬为持续十日量级，不转换成精确起止日。')
event('li_sizhao_siyuan_night_raids', '李嗣昭李嗣源夜出暗门袭汴营',20,
      '河东将李嗣昭、李嗣源凿暗门，夜出攻汴垒，屡有杀获。',
      [('李嗣昭','夜袭者'),('李嗣源','夜袭者')],when='901年四月晋阳受攻时',place='晋阳汴垒',
      note='屡有杀获未具人数，不造伤亡数字。')
event('li_cunjin_wins_dongwo', '李存进于洞涡击败汴军',20,
      '李存进败汴军于洞涡。',[('李存进','击败汴军者')],
      when='901年四月晋阳受攻时',place='洞涡')
event('zhu_orders_withdrawal', '朱全忠因粮草不继久雨疫病召军还',20,
      '时汴军既众，刍粮不给，久雨，士卒疟利，全忠乃召兵还。',
      [('朱温','召军还者')],when='901年四月后；确日未载',
      note='刍粮不足、久雨、疟利均为原文列出的退军背景；不可只归因单项。')
event('liang_armies_retreat_may', '五月氏叔琮自石会关撤军，诸路军退',20,
      '五月，叔琮等自石会关归，诸道军亦退。',
      [('氏叔琮','撤军者')],when='901年五月',place='石会关')
event('zhou_li_pursue_retreat', '周德威李嗣昭率精骑五千追击退军',20,
      '河东将周德威、李嗣昭以精骑五千蹑之，杀获甚众。',
      [('周德威','追击者'),('李嗣昭','追击者')],when='901年五月汴军撤退时',place='石会关后路',
      note='五千为追击骑兵合数；“甚众”未给具体杀获数。')
event('li_tang_turns_to_bian', '汾州刺史李瑭此前据州附汴',20,
      '先是，汾州刺史李瑭举州附于汴军',
      [('李瑭','据汾州附汴者')],when='先是；确年未载',place='汾州',year=None,
      note='“先是”追叙，未给叛附确年；旧五代史作“是岁”，本批保留主书不定年。')
event('li_cunshen_takes_fen_executes_li_tang', '李存审三日拔汾州，执斩李瑭',20,
      '克用遣其将李存审攻之，三日而拔，执瑭，斩之。',
      [('李克用','遣兵者'),('李存审','攻取并执斩者'),('李瑭','被执斩者')],
      when='901年五月条；攻城历三日，确日未载',place='汾州',
      note='旧五代史另列李嗣昭同攻，并记斩于晋阳市；主书仅列李存审，异文并列。')
claim('person',people['李瑭'],'death_year','李瑭于901年被李存审执斩。',20,
      '克用遣其将李存审攻之，三日而拔，执瑭，斩之。',
      '死亡处于本年五月条；旧五代史作斩于晋阳市，地点待核。')
event('meng_qian_moves_south', '孟迁携族随氏叔琮南徙',20,
      '氏叔琮过上党，孟迁挈族随之南徙。',
      [('氏叔琮','南还过上党者'),('孟迁','携族南徙者')],
      when='901年五月撤军途中',place='上党')
event('ding_hui_replaces_meng_lu', '朱全忠遣丁会代守潞州',20,
      '硃全忠遣丁会代守潞州。',
      [('朱温','遣任者'),('丁会','代守潞州者')],when='901年五月孟迁南徙后',place='潞州',
      note='本段遣丁会守潞；后文闰月朝廷任昭义节度另行分录。')
extra(old_five_jin,'event','event_zztj_262_0901_zhou_li_pursue_retreat','description',
      '《旧五代史》卷二十六亦记周德威李嗣昭精骑五千追氏叔琮。',
      '周德威、李嗣昭以精騎五千躡之',20,'corroborates','同追击者及兵数；该书杀戮“万计”与主书“甚众”不换算。')
extra(old_five_jin,'event','event_zztj_262_0901_li_cunshen_takes_fen_executes_li_tang','description',
      '《旧五代史》记李嗣昭、李存审同攻，李瑭斩于晋阳市。',
      '嗣昭悉力攻城，三日而拔，擒李瑭等斬於晉陽市',20,'adds',
      '原段前文明确李嗣昭、李存审将兵讨之；斩刑地点与主书未明地点分别保留。')
extra(new_five,'event','event_zztj_262_0901_zhu_orders_withdrawal','description',
      '《新五代史》亦记霖雨、梁兵多疾而解去。',
      '會天大雨霖，梁兵多疾，皆解去',20,'corroborates','仅印证雨疾退兵；主书另记刍粮不足。')

# 21–24: titles, revenue dispute and June travel.
event('zhu_petitions_hezhong', '朱全忠奏请河中节度并讽吏民拥己',21,
      '硃全忠奏乞除河中节度使，而讽吏民请己为帅。',
      [('朱温','奏请并讽吏民者')],when='901年五月癸卯前',place='河中',
      note='请任与朝廷正式任命区分。')
event('zhu_four_commands', '朱全忠兼宣武宣义天平护国四镇节度',21,
      '癸卯，以全忠为宣武、宣义，天平、护国四镇节度使。',
      [('朱温','受四镇节度者')],when='901年五月癸卯',
      note='四镇名逐字保留，不把兼领误作同时身在四地。')
event('qian_liu_shou_shizhong', '钱镠加守侍中',21,
      '己酉，加镇海、镇东节度使钱镠守侍中。',
      [('钱镠','加守侍中者')],when='901年五月己酉',place='镇海、镇东')
event('cui_extends_qu_ban', '崔胤将两军卖曲禁令扩及近镇',22,
      '崔胤之罢两军卖麹也，并近镇亦禁之。',
      [('崔胤','扩禁者')],when='901年四月赦令后',
      note='连接第18段禁两军卖曲；麹与曲是原文异写，不另立商品。')
event('maozhen_petitions_qu', '李茂贞惜卖曲利，请入朝论奏，韩全诲请允',22,
      '李茂贞惜其利，表乞入朝论奏，韩全诲请许之。',
      [('李茂贞','上表请入朝者'),('韩全诲','请朝廷允之者')],
      when='901年卖曲禁令扩至近镇后',
      note='原文叙李茂贞惜利为动因；不写此时已获恢复卖曲权。')
event('maozhen_eunuch_alliance', '李茂贞至京，与韩全诲深结',22,
      '茂贞至京师，全诲深与相结。',
      [('李茂贞','入京结交者'),('韩全诲','结交者')],
      when='901年请朝获允后',place='京师',
      note='相结为原文明确的政治往来；未注明正式盟约。')
event('cui_deepens_zhu_ties', '崔胤忧惧后暗中加深与朱全忠联系',22,
      '崔胤始惧，阴厚硃全忠益甚，与茂贞为仇敌矣。',
      [('崔胤','转而密厚朱者'),('朱温','受其密厚者'),('李茂贞','与崔为敌者')],
      when='901年李茂贞与韩全诲相结后',
      note='厚、仇敌为主书记述，不额外构造全年永久盟约关系。')
event('zhang_quanyi_zhongshu_ling', '张全义兼中书令',23,
      '以佑国节度使张全义兼中书令。',
      [('张全义','加兼中书令者')],when='901年五月后；确日未载')
event('zhu_goes_hezhong_june', '朱全忠六月癸亥往河中',24,
      '六月，癸亥，硃全忠如河中。',
      [('朱温','赴河中者')],when='901年六月癸亥',place='河中')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17,25):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='第17—24段连续校核：赦令与曲税、东川请代、晋阳围守及撤军、河中四镇任命、京师结交与赴河中。初和先是追叙确年未载；旧五代史补李嗣昭同攻汾州与晋阳斩李瑭。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=262,year=901,
    primary_source_key=primary_prev,primary_source_keys=[primary_prev,primary],
    paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],
    coverage='天复元年55段中的第17—24段连续处理；本年尚未完成。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
