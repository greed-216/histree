"""Curate Tongjian 266, year 907, consecutive paragraphs 8–15."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 62))
primary = 'tongjian-266-907-spring-later'
new_liu = 'xinwudaishi-039-liushouguang'
B = {'format_version': 1, 'batch_key': 'zztj-v266-y0907-p008-p015',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P / 'sources/library' / primary, '81ed5300', '司马光等'),
    (new_liu, P / 'sources/library' / new_liu, '81ed5300', '欧阳修等'),
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
primary_texts = {primary: (source_dirs[primary] / 'source.txt').read_text()}
for n in range(8, 16):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/266.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '梁王':'朱温', '王景仁':'王茂章'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/year-0907/content-batch.json').read_text())['events']}
legacy_relations = {row['key']: row for row in json.loads((ROOT / 'content/year-0907/content-batch.json').read_text())['person_relationships']}

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_266_0907_02_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷266·开平元年（907）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical,
                   aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷266开平元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=907, time_quote=None, reuse_key=None):
    assert quote in Q[n]['text'], (n, quote)
    key = reuse_key or ('event_zztj_266_0907_' + code)
    if reuse_key:
        assert not actors, 'Published event edges are preserved by stable key'
        if key not in {row['key'] for row in B['events']}:
            row = dict(legacy_events[reuse_key], status='draft')
            B['events'].append(row)
        reused.add(key)
        desc = legacy_events[reuse_key]['description']
    else:
        desc = title + '。'
        B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                                time_original=when or '907年本段条；确日未载', dynasty='唐', description=desc,
                                phases=[], location_name=place, location_modern_name=None, location_lat=None,
                                location_lng=None, location_precision='unknown',
                                location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '907年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_266_0907_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def relation(key, n, quote, note):
    assert quote in Q[n]['text']
    row = legacy_relations[key]
    if key not in {item['key'] for item in B['person_relationships']}:
        B['person_relationships'].append(dict(row, status='draft'))
        reused.add(key)
    claim('person_relationship',key,'description',row['description'],n,quote,note)

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_266_0907_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 8-9: Expedition and continued abdication negotiations are existing 907 events.
event('li_sian_sent_youzhou','李思安受命攻幽州',8,
      '三月，癸未，王以亳州刺史李思安为北路行军都统，将兵击幽州。',
      when='907年三月癸未',place='幽州',
      note='本段是遣兵日；四月到城及败退在第13段，复用旧907幽州战事事件。',
      reuse_key='event_0907_youzhou_campaign')
event('abdication_envoys_march','唐昭宣帝再遣薛贻矩、苏循往大梁',9,
      '庚寅，唐昭宣帝诏薛贻矩再诣大梁谕禅位之意，又诏礼部尚书苏循赍百官诣大梁。',
      when='907年三月庚寅',place='大梁',
      note='“再诣”显示薛贻矩此前已经出使；此时传达禅位意向，尚未完成禅位。',
      reuse_key='event_0907_abdication_petitions')

# 10: The departure is part of the earlier published Wenzhou campaign.
event('qian_sends_sons_to_wenzhou','钱镠遣两子讨卢佶',10,
      '镇海、镇东节度使吴王钱镠遣其子传镣、传瓘讨卢佶于温州。',
      when='907年三月条；确日未载',place='温州',
      note='只记出兵；温州陷落和卢佶被杀见第15段。',
      reuse_key='event_0907_wenzhou')
for name in ('钱镠','钱传镣','钱传瓘'):
    person(name,10,'钱氏温州出兵记载中的人物','钱镠遣其子传镣、传瓘讨卢佶于温州')
relation('relationship_person_钱镠_person_钱传镣_父亲',10,
         '钱镠遣其子传镣、传瓘讨卢佶于温州','“其子”承钱镠；保留已有父亲关系方向。')
relation('relationship_person_钱镠_person_钱传瓘_父亲',10,
         '钱镠遣其子传镣、传瓘讨卢佶于温州','“其子”承钱镠；保留已有父亲关系方向。')

# 11: Separate the proposed cession from completion of the rite.
event('tang_issues_cession_edict','唐昭宣帝下御札并分派禅位册礼使者',11,
      '甲辰，唐昭宣帝降御札禅位于梁。以摄中书令张文蔚为册礼使，礼部尚书苏循副之；摄侍中杨涉为押传国宝使，翰林学士张策副之；御史大夫薛贻矩为押金宝使，尚书左丞赵光逢副之；帅百官备法驾诣大梁。',
      when='907年三月甲辰',place='大梁',
      note='本段是降御札与分派使者，梁王即位在后续段落；旧907劝进事件复用。',
      reuse_key='event_0907_abdication_petitions')
event('yang_ningshi_urges_father_decline','杨凝式劝父杨涉辞送玺之事',11,
      '杨涉子直史馆凝式言于涉曰：“大人为唐宰相，而国家至此，不可谓之无过。况手持天子玺绶与人，虽保富贵，奈千载何！盍辞之！”涉大骇曰：“汝灭吾族！”',
      [('杨凝式','劝谏父亲者'),('杨涉','受劝而惊惧者')],
      when='907年三月甲辰后；确日未载',
      note='“千载何”是杨凝式的劝辞，杨涉回应为原文记载；不把辞官当成已经执行。')
relation('relationship_person_杨涉_person_杨凝式_父亲',11,
         '杨涉子直史馆凝式言于涉曰','“杨涉子”明示父子；复用原档案关系。')

# 12: Liu Rengong's mountain residence and monetary policy lack a clear start year.
event('liu_rengong_builds_daan_residence','刘仁恭于大安山筑馆并求长生',12,
      '常虑幽州城不固，筑馆于大安山，曰：“此山四面悬绝，可以少制众。”其栋宇壮丽，拟于帝者。选美女实其中。与方士炼丹药，求不死。',
      [('刘仁恭','筑馆与求长生者')],
      when='907年前后；筑馆确年未载',place='大安山',year=None,
      note='“常虑”表持续心态，筑馆没有本年确日；“拟于帝者”为主书评价。')
event('liu_rengong_controls_currency_and_tea','刘仁恭敛钱并限制茶商入境',12,
      '悉敛境内钱，瘗于山颠；令民间用堇泥为钱。又禁江南茶商无得入境，自采山中草木为茶，鬻之。',
      [('刘仁恭','下令控制钱与茶交易者')],
      when='907年前后；施行起讫未载',place='幽州境内',year=None,
      note='保留“堇泥”为底本文字；不推定民间交易规模或市场价格。')

# 13: Private family dispute, the expedition outcome and seizure of power.
event('liu_shouguang_expelled_after_luo_affair','刘仁恭因守光与罗氏私通而杖斥守光',13,
      '仁恭有爱妾罗氏，其子守光通焉。仁恭杖守光而斥之，不以为子数。',
      [('刘仁恭','杖斥守光者'),('刘守光','被杖斥者')],
      when='李思安攻幽州前；确年日未载',year=None,
      note='“罗氏”仅姓氏，不与其他同姓人物合并；此为前情，不定为907年发生。')
relation('relationship_person_刘仁恭_person_刘守光_父亲',13,
         '仁恭有爱妾罗氏，其子守光通焉','“其子守光”明确刘仁恭为父；“不以为子数”不消灭亲属事实。')
event('li_sian_repulsed_at_youzhou','刘守光入幽州抵御李思安并使其退兵',13,
      '夏，四月，己酉，直抵幽州城下。仁恭犹在大安山。城中无备，几至不守。守光自外引兵入，登城拒守；又出兵与思安战，思安败退。',
      when='907年四月己酉至城下；退兵确日未载',place='幽州',
      note='“几至不守”是险情，不写作幽州已陷；与第8段旧幽州战事同一事件。',
      reuse_key='event_0907_youzhou_campaign')
event('liu_shouguang_seizes_father','刘守光遣军攻大安山并囚父刘仁恭',13,
      '守光遂自称节度使，命部将李小喜、元行钦将兵攻大安山。仁恭遣兵拒战，为小喜所败。虏仁恭以归，囚于别室。',
      when='907年四月李思安退后；确日未载',place='大安山、幽州',
      note='李小喜、元行钦均在主书列为攻山部将；此为旧907囚父事件。',
      reuse_key='event_0907_liuren_captured')
event('liu_shouguang_purges_retinue','刘守光杀刘仁恭身边其所恶之人',13,
      '仁恭将佐及左右，凡守光素所恶者皆杀之。',
      [('刘守光','下令杀害者')],
      when='刘仁恭被囚后；确日未载',place='幽州',
      note='本句未给名单和人数，不据此推定全体将佐遇害。')
event('youzhou_exiles','王思同李承约刘守奇离开幽州',13,
      '王思同帅部兵三千，山后八安巡检使李承约帅部兵二千奔河东，守光弟守奇奔契丹，未几，亦奔河东，河东节度使晋王克用以承约为匡霸指挥使，思同为飞腾指挥使。',
      when='刘守光夺权后；确日未载',place='幽州、河东、契丹',
      note='原文“银胡录”属电子底本未识字，摘录从王思同姓名起；不据乱码补写官名。',
      reuse_key='event_0907_youzhou_exiles')
for name in ('刘守光','刘守奇'):
    person(name,13,'幽州夺权及出奔记载中的人物','守光弟守奇奔契丹')
relation('relationship_person_刘守光_person_刘守奇_兄长',13,
         '守光弟守奇奔契丹','“守光弟守奇”明示守光为兄；复用旧关系方向。')

# 14-15: Date-specific steps in the still-unfinished transition and Wenzhou campaign.
event('zhu_removes_tang_era','梁王受百官称臣并令公文去唐年号',14,
      '庚戌，梁王始御金祥殿，受百官称臣，下书称教令，自称曰寡人。辛亥，令诸笺、表、簿、籍皆去唐年号，但称月、日。',
      when='907年四月庚戌、辛亥',place='大梁金祥殿',
      note='两项举措分别有干支日；尚未把此段写成正式即皇帝位。',
      reuse_key='event_0907_remove_tang_era')
event('zhang_wenwei_arrives_daliang','张文蔚等奉禅位册礼到大梁',14,
      '丙辰，张文蔚等至大梁。',
      [('张文蔚','到大梁的册礼使')],when='907年四月丙辰',place='大梁',
      note='“等”不列姓名，不推定所有使者同日到达。')
event('wenzhou_falls_lu_ji_killed','钱传瓘间道袭温州，卢佶被擒杀',15,
      '钱传瓘曰：“佶之精兵尽在于此，不可与战。”乃自安固舍舟，间道袭温州。戊午，温州溃，擒佶斩之。',
      when='907年四月戊午温州溃',place='安固、温州',
      note='钱传瓘关于敌军精兵的判断是其言辞；旧907温州战事复用同一事件。',
      reuse_key='event_0907_wenzhou')
claim('event','event_0907_wenzhou','description',
      '钱镠任吴璋为温州制置使，命钱传瓘等转攻处州。',15,
      '吴王镠以都监使吴璋为温州制置使，命传瓘等移兵讨卢约于处州。',
      '温州治理及转攻处州发生在卢佶被杀后；旧907温州战事的后续步骤。')

extra(new_liu,'event','event_0907_liuren_captured','description',
      '《新五代史》卷三十九同记李思安败退后刘守光自称节度使、攻大安山执父刘仁恭。',
      '梁開平元年，遣李思安攻仁恭，仁恭在大安，守光自外將兵以入，擊走思安，乃自稱盧龍節度使，遣李小喜、元行欽以兵攻大安山，執仁恭而幽之。',
      13,'corroborates','新书另叙兄弟后续争战，非本段即时结果，未倒填。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(8,16):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷266开平元年第8—15段连续处理；旧907事件及明确亲属关系复用，追叙时间与电子疑字单列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=266,year=907,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(8,16)],next_paragraph=Q[16]['id'],
    coverage='卷266开平元年第8—15段连续处理；幽州出兵及刘守光夺权、禅位使者、温州战事。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
