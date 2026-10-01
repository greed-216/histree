"""Curate Tongjian 264, year 903, consecutive paragraphs 50–54."""
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
primary = 'tongjian-264-903-october'
yearend = 'tongjian-264-903-yearend'
old_zhang = 'jiutangshu-179-zhang-jun-death'
old_ge = 'jiutangshu-179-zhang-ge-escape'
new_khitan = 'xinwudaishi-072-khitan'
new_yang = 'xinwudaishi-061-yang-xingmi'
B = {'format_version': 1, 'batch_key': 'zztj-v264-y0903-p050-p054',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-08/sources/library' / primary, 'a3ad61d', '司马光等'),
    (yearend, P / 'sources/library' / yearend, '10d7ddd', '司马光等'),
    (old_zhang, P / 'sources/library' / old_zhang, '10d7ddd', '刘昫等'),
    (old_ge, P / 'sources/library' / old_ge, '10d7ddd', '刘昫等'),
    (new_khitan, P / 'sources/library' / new_khitan, '10d7ddd', '欧阳修等'),
    (new_yang, P.parent / 'part-02/sources/library' / new_yang, '71feb52', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, yearend)}
for n in range(50, 55):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','邪律阿保机':'耶律阿保机','侯矩':'王宗矩','张濬':'张浚','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范','李存审':'符存审','王宗本':'谢从本','硃延寿':'朱延寿','王坛':'王檀','坛':'王檀','硃氏（杨行密夫人）':'朱氏（杨行密夫人）','郭行頵':'郭行悰','侯矩':'王宗矩','硃友伦':'朱友伦','硃全忠':'朱温','邪律阿保机':'耶律阿保机','侯矩':'王宗矩','张濬':'张浚'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0903_09_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_264_0903_09_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 50: Tian Jun's death, Yang Xingmi's response, and appointments after Xuanzhou.
event('tian_last_sortie','田頵十二月乙亥率死士出城，台濛佯退后反击',50,
      '十二月，乙亥，田頵帅死士数百出战，台濛阳退以示弱。頵兵逾濠而斗，濛急击之。',
      [('田頵','率军出战者'),('台濛','佯退反击者')],
      when='903年十二月乙亥',place='宣州',
      note='“阳退”是台濛佯装退却；数百为主书约数。')
event('tian_jun_killed','田頵败退时桥陷坠马被斩，台濛克宣州',50,
      '頵不胜，还走城，桥陷坠马，斩之，其众犹战，以頵首示之，乃溃，濛遂克宣州。',
      [('田頵','坠马被斩者'),('台濛','获胜并克宣州者')],
      when='903年十二月乙亥',place='宣州',
      note='“斩之”未指明行刑者，不写成台濛亲手斩杀。')
event('yang_mourns_tian','杨行密见田頵首哭泣，赦其母殷氏并以子孙礼待之',50,
      '及頵首至广陵，行密视之泣下，赦其母殷氏，行密与诸子皆以子孙礼事之。',
      [('杨行密','哭泣并赦殷氏者'),('田頵','首级送至广陵者'),('殷氏（田頵母）','获赦并受礼遇者')],
      when='903年十二月乙亥后；确日未载',place='广陵',
      note='“其母”承田頵；杨行密与田頵少时约为兄弟为本段追叙，不据此推定血缘。')
event('li_shenfu_declines_ningguo','杨行密授李神福宁国节度使，李以杜洪未平固辞',50,
      '行密以李神福为宁国节度使，神福以杜洪未平，固让不拜。',
      [('杨行密','任命者'),('李神福','固辞者'),('杜洪','尚未平定者')],
      when='903年十二月；确日未载',place='宁国军',
      note='任命与辞让并记，不将节度使视为李神福已实际赴任。')
event('yang_appoints_luo_shen','杨行密任骆知祥与沈文昌于淮南官职',50,
      '行密以知祥为淮南支计官，文昌为节度分推。',
      [('杨行密','任用者'),('骆知祥','淮南支计官'),('沈文昌','节度分推')],
      when='903年十二月；确日未载',place='淮南',
      note='骆知祥善治金谷、沈文昌曾为田頵草檄是本段追叙背景；其任用与此前经历分开。')
event('shen_wenchang_past','沈文昌旧时为田頵草檄骂杨行密',50,
      '观察牙推沈文昌为文精敏，尝为頵草檄骂行密',
      [('沈文昌','旧时草檄者'),('田頵','檄文委托者'),('杨行密','檄文所骂者')],
      when='“尝”追叙；确年未载',year=None,
      note='檄文发生在被任淮南节度分推之前，不能定为田頵死后。')

# 51: hostage protection and Guo Shicong's later appointment.
event('qian_chuanguan_protected','田頵屡欲杀钱传瓘，田母与郭师从常加保护',51,
      '初，頵每战不胜，辄欲杀钱传瓘，其母及宣州都虞候郭师从常保护之。',
      [('田頵','屡生杀意者'),('钱传瓘','受保护者'),('殷氏（田頵母）','保护者'),('郭师从','保护者')],
      when='“初”追叙；田頵多次败战时，确日未载',year=None,place='宣州',
      note='“欲杀”是田頵念头，未实际杀害；“其母”承田頵，按上一段殷氏归并。')
event('qian_chuanguan_returns','田頵败后钱传瓘归杭州，钱镠任郭师从镇东都虞候',51,
      '頵败，传瓘归杭州，钱镠以师从为镇东都虞候。',
      [('钱传瓘','归杭州者'),('钱镠','任命者'),('郭师从','受任者')],
      when='903年十二月田頵败后；确日未载',place='杭州',
      note='郭师从为田頵妻弟由同段明示，任命发生在田頵败后。')

# Explicit relationships; “约为兄弟” is social kinship, not blood kinship.
for code,a,b,kind,description,n,quote,note in [
    ('yin_mother_tian','殷氏（田頵母）','田頵','母亲','殷氏是田頵的母亲。',50,'其母殷氏','“其”承田頵，姓名仅知姓殷。'),
    ('yang_tian_sworn','杨行密','田頵','结义兄弟','杨行密与田頵少时约为兄弟。',50,'少相善，约为兄弟','结义承诺而非血亲；约定长幼未载。'),
    ('guo_wifes_brother','郭师从','田頵','妻弟','郭师从是田頵的妻弟。',51,'頵之妇弟也','原文“妇弟”指田頵妻之弟，未给妻姓名。'),
]:
    pa=person(a,n,kind,quote)
    pb=person(b,n,kind,quote)
    key='relationship_zztj_264_0903_'+code
    B['person_relationships'].append(dict(key=key,person_a_key=pa,person_b_key=pb,
        relation_type=kind,description=description,status='draft'))
    claim('person_relationship',key,'description',description,n,quote,note)

# 52: court appointments and the killing of Zhang Jun.
event('dugu_sun_chancellor','独孤损辛巳任兵部侍郎、同平章事',52,
      '辛巳，以礼部尚书独孤损为兵部侍郎、同平章事。损，及之从曾孙也。',
      [('独孤损','新任宰相')],when='903年十二月辛巳',
      note='与独孤及的“从曾孙”关系依原文保留在说明，不强换现代亲属称谓。')
event('pei_zhi_removed','裴贽罢同平章事改左仆射',52,
      '中书侍郎兼户部尚书、同平章事裴贽罢为左仆射。',
      [('裴贽','罢相改官者')],when='903年十二月辛巳；同段纪事',
      note='原文只标本段月日，具体诏令日未另载。')
event('zhang_jun_in_wang_plan','张浚参与王师范举兵之谋',52,
      '王师范之举兵，浚豫其谋。',
      [('张浚','参与谋划者'),('王师范','举兵者')],
      when='王师范举兵之前后；确日未载',year=None,
      note='这是主书对参与谋划的归结；《旧唐书》作王师范欲取张濬为谋主而事未果，具体参与程度有异。')
event('zhu_moves_against_zhang','朱全忠恐张浚联结藩镇，讽张全义加害',52,
      '硃全忠将谋篡夺，恐浚扇动籓镇，讽张全义使图之。',
      [('朱温','授意者'),('张全义','受示意者'),('张浚','目标')],
      when='903年十二月丙申前；确日未载',
      note='“恐浚扇动籓镇”为史书记朱全忠忧虑，不证明张浚已经发动藩镇。')
event('yang_lin_kills_zhang','杨麟丙申率兵伪装盗贼围杀张浚',52,
      '丙申，全义遣牙将杨麟将兵诈为劫盗，围其墅而杀之。',
      [('张全义','遣兵者'),('杨麟','伪装盗贼围杀者'),('张浚','被杀者')],
      when='903年十二月丙申',place='长水',
      note='地点承上文张浚居长水；《旧唐书》记“十二月晦夜”，日分异说未消解。')
event('ye_warns_zhang_ge','叶彦素预警张格并护送其渡汉入蜀',52,
      '永宁县吏叶彦素为浚所厚，知麟将至，密告浚子格曰：“相公祸不可免，郎君宜自为谋。”谓格曰：“汝留则俱死，去则遗种。”格哭拜而去，叶彦帅义士三十人送之渡汉而还，格遂自荆南入蜀。',
      [('叶彦素','预警并护送者'),('张格','逃往蜀者'),('张浚','被告知祸事者')],
      when='903年十二月丙申前后；确日未载',place='长水、汉水、荆南、蜀',
      note='段内先作“叶彦素”，后简称“叶彦”，《旧唐书》作叶彦；暂同一人。引语第二句在本段承张浚，未误归叶彦素。')

# 53: habitual frontier tactics, raid, capture, and ransom.
event('liu_rengong_autumn_raids','刘仁恭历年秋季越摘星岭攻契丹并焚塞草',53,
      '刘仁恭习知契丹情伪，常选将练兵，乘秋深入，逾摘星岭击之，契丹畏之。每霜降，仁恭辄遣人焚塞下野草，契丹马多饥死，常以良马赂仁恭买牧地。',
      [('刘仁恭','遣兵及焚草者')],
      when='“常”“每霜降”总述；起止年未载',year=None,place='摘星岭、塞下',
      note='这是经年重复的做法，不录为903年十二月单次行动。')
event('abaoji_sends_abo','契丹王邪律阿保机遣述律阿钵万骑犯渝关',53,
      '契丹王邪律阿保机遣其妻兄述律阿钵将万骑寇渝关',
      [('耶律阿保机','遣军者'),('述律阿钵','统兵者')],
      when='903年本段条；确日未载',place='渝关',
      note='“邪律”按通行耶律字形规范化，原文不改；万骑为主书记数。')
event('liu_shouguang_captures_abo','刘守光戍平州，佯和设伏擒述律阿钵',53,
      '仁恭遣其子守光戍平州，守光伪与之和，设幄犒飨于城外，酒酣，伏兵执之以入。',
      [('刘仁恭','遣子戍守者'),('刘守光','佯和设伏者'),('述律阿钵','被擒者')],
      when='903年本段条；确日未载',place='平州城外',
      note='“和”为刘守光诈称；宴席后伏兵擒人。')
event('abo_released_for_ransom','契丹以重赂请还述律阿钵，刘仁恭后释放',53,
      '契丹以重赂请于仁恭，然后归之。',
      [('刘仁恭','受请后释放者'),('述律阿钵','被归还者')],
      when='903年本段条；确日未载',
      note='重赂数额与具体交换条件未载，不扩写。')

# 54: retrospective split between Cui Yin and Zhu Quanzhong, then army recruitment.
event('cui_zhu_split','崔胤借朱全忠灭宦官后，双方渐生猜忌',54,
      '初，崔胤假硃全忠兵力以诛宦官，全忠既破李茂贞，并吞关中，威震天下，遂有篡夺之志。胤惧，与全忠外虽亲厚，私心渐异',
      [('崔胤','惧朱全忠者'),('朱温','生篡夺之志者'),('李茂贞','此前被破者')],
      when='“初”追叙；宦官被诛后，起止日未载',year=None,
      note='此为史书对意图和私心的追叙归因；不将“篡夺”写成已发生。')
event('cui_recruits_guard','崔胤请充实六军十二卫，朱全忠暗遣部众应募窥察',54,
      '六军十二卫，但有空名，请召募以实之，使公无西顾之忧。”全忠知其意，曲从之，阴使麾下壮士应募以察其变。',
      [('崔胤','提出召募者'),('朱温','暗遣部众监视者')],
      when='903年末；确日未载',place='长安',
      note='“使公无西顾之忧”是崔胤向朱全忠所说的理由；朱全忠表面同意且暗中监视。')
event('cui_repairs_weapons','崔胤与郑元规等日夜修治兵仗',54,
      '胤不之知，与郑元规等缮治兵仗，日夜不息。',
      [('崔胤','修治军备者'),('郑元规','参与者')],
      when='903年末；确日未载',place='长安',
      note='“胤不之知”指不知道朱全忠暗遣应募者，不说明郑元规知情。')
event('zhu_suspects_cui_move_luo','朱友伦死后朱全忠益疑崔胤，欲迁帝洛阳并忧崔反对',54,
      '及硃友伦死，全忠益疑胤，且欲迁天子都洛，恐胤立异。',
      [('朱温','猜疑并有迁都意图者'),('崔胤','被怀疑且可能反对者'),('朱友伦','已死的触发人物')],
      when='朱友伦十月辛巳死后；确日未载',
      note='此段仅记迁都意图与担忧；实际迁都留待904年原文处理。')

for code,a,b,kind,description,n,quote,note in [
    ('zhang_ge_son','张格','张浚','儿子','张格是张浚的儿子。',52,'浚子格','原文明示“子”。'),
    ('liu_shouguang_son','刘守光','刘仁恭','儿子','刘守光是刘仁恭的儿子。',53,'其子守光','“其”承刘仁恭。'),
    ('aboji_brother_in_law','述律阿钵','耶律阿保机','妻兄','述律阿钵是耶律阿保机的妻兄。',53,'其妻兄述律阿钵','“其”承邪律阿保机；按本站耶律字形展示。'),
]:
    pa=person(a,n,kind,quote)
    pb=person(b,n,kind,quote)
    key='relationship_zztj_264_0903_'+code
    B['person_relationships'].append(dict(key=key,person_a_key=pa,person_b_key=pb,
        relation_type=kind,description=description,status='draft'))
    claim('person_relationship',key,'description',description,n,quote,note)

aba=next(x for x in B['people'] if x['name']=='耶律阿保机')
aba['aliases']=sorted(set(aba.get('aliases',[])+['邪律阿保机']))
ye=next(x for x in B['people'] if x['name']=='叶彦素')
ye['aliases']=sorted(set(ye.get('aliases',[])+['叶彦']))

extra(new_yang,'event','event_zztj_264_0903_tian_jun_killed','description',
      '《新五代史》杨行密世家亦记台濛击田頵、田頵败死。',
      '行密別遣臺濛擊頵，頵敗死',50,'corroborates',
      '新书简述结果，未记桥陷与确日；与《通鉴》可能同源，不作细节独立确证。')
extra(old_zhang,'event','event_zztj_264_0903_zhang_jun_in_wang_plan','description',
      '《旧唐书》张濬传说王师范欲请张濬为谋主，事未成而迹泄。',
      '王師範青州起兵，欲取濬爲謀主。事雖不果',52,'conflicts',
      '与《通鉴》“浚豫其谋”程度不同；张濬与本站张浚按同人匹配，不能抹平参与程度异说。')
extra(old_zhang,'event','event_zztj_264_0903_yang_lin_kills_zhang','time_original',
      '《旧唐书》张濬传记杨麟杀张浚为天复三年十二月晦夜。',
      '乃令牙將楊麟率健卒五十人，有如劫盜，圍其墅而殺之，天復三年十二月晦夜也',52,'conflicts',
      '《通鉴》书“丙申”；旧书说十二月晦夜，日分未强行换算。')
extra(old_ge,'event','event_zztj_264_0903_ye_warns_zhang_ge','description',
      '《旧唐书》另记叶彦警告张格并率三十人送其渡汉。',
      '葉彥率義士三十人，送渡漢江而旋',52,'corroborates',
      '旧书作叶彦，主书段内有叶彦素与叶彦两写法；因官职和事件对应暂归一，原字照录。')
extra(new_khitan,'event','event_zztj_264_0903_liu_rengong_autumn_raids','description',
      '《新五代史》契丹传也记刘仁恭出兵摘星岭、秋霜焚草，契丹以马求牧地。',
      '每歲秋霜落，則燒其野草，契丹馬多飢死，即以良馬賂仁恭求市牧地',53,'corroborates',
      '旧事为经年做法，不据这条补出精确年份；新书与主书可能共源。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(50,55):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天复三年第50—54段连续处理；十二月战事与年末追叙分列，人物异名及旧唐书异说保留。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=903,
    primary_source_key=primary,primary_source_keys=[primary,yearend],
    paragraphs=[Q[n]['id'] for n in range(50,55)],next_paragraph=None,
    coverage='卷264天复三年共54个非空段落中的第50—54段连续处理；本卷903年段落至此结束，下一条为卷264天祐元年（904）。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
