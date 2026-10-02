"""Curate Tongjian 266, year 907, consecutive paragraphs 45–61."""
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
primary = 'tongjian-266-907-summer'
yearend = 'tongjian-266-907-yearend'
new_shu = 'xinwudaishi-063-shu-founded'
new_langzhou = 'xinwudaishi-066-langzhou'
B = {'format_version': 1, 'batch_key': 'zztj-v266-y0907-p045-p061',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-05/sources/library' / primary, 'ef31b763', '司马光等'),
    (yearend, P / 'sources/library' / yearend, '3fdb705c', '司马光等'),
    (new_shu, P / 'sources/library' / new_shu, '3fdb705c', '欧阳修等'),
    (new_langzhou, P / 'sources/library' / new_langzhou, '3fdb705c', '欧阳修等'),
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
for n in range(45, 62):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/266.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '梁王':'朱温', '蜀王':'王建', '晋王':'李克用', '吴越王镠':'钱镠', '楚王殷':'马殷', '羅紹威':'罗绍威', '劉守文':'刘守文'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/year-0907/content-batch.json').read_text())['events']}
legacy_relations = {}
for archive in ('content/late-tang-zhu-wen-early/content-batch.json',
                'content/year-0907/content-batch.json'):
    for row in json.loads((ROOT / archive).read_text())['person_relationships']:
        if row['key'] in legacy_relations:
            assert legacy_relations[row['key']] == row
        legacy_relations[row['key']] = row

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_266_0907_06_{len(B["claims"])+1:04d}',
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
        desc = title + '。'
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
    ck = f'claim_zztj_266_0907_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 45-50: July to September local campaigns and Liang commands.
event('lei_yuezhou','雷彦恭攻岳州未克',45,'雷彦恭攻岳州，不克。',
      when='907年七月丙申后、八月前；确日未载',place='岳州',
      note='本段只有攻而未克，不据此推断守将或后续归属。',reuse_key='event_0907_leiyuezhou')
event('zhang_rename','后梁赐张全义名宗奭',46,
      '八月，丙午，赐河南尹张全义名宗奭。',when='907年八月丙午',
      note='张全义与张宗奭为同一人，沿用已发布实体与事件，不新建人物。',reuse_key='event_0907_zhang_rename')
event('qian_ma_commissions','后梁加钱镠、马殷节度使及招讨制置职',47,
      '辛亥，以吴越王镠兼淮南节度使，楚王殷兼武昌节度使，各充本道招讨制置使。',
      when='907年八月辛亥',
      note='名义加官不说明两人已实际控制淮南、武昌。',reuse_key='event_0907_qian_ma_commissions')
event('gaohe_battle','周德威驻高河，康怀贞部秦武出击战败',48,
      '晋周德威壁于高河，康怀贞遣亲骑都头秦武将兵击之，武败。',
      when='907年八月辛亥后；确日未载',place='高河',
      note='秦武部败与潞州后续夹寨攻守相连，仍保留单独战斗事件。',reuse_key='event_0907_gaohe')
event('jiazhai_siege','李思安代康怀贞统兵潞州并筑夹寨',49,
      '丁已，帝以亳州刺史李思安代怀贞为潞州行营都统，黜怀贞为行营都虞候。',
      when='907年八月丁已（原文；干支字形待核）',place='潞州',
      note='底本“丁已”疑应校为“丁巳”，保留原字；与第33、39段潞州围城衔接。',
      reuse_key='event_0907_jiazai')
claim('event','event_0907_jiazai','description','李思安在潞州筑内外夹城，建立运粮甬道；周德威持续袭扰。',49,
      '思安将河北兵西上，至潞州城下，更筑重城，内以防奔突，外以拒援兵，谓之夹寨。调山东民馈军粮，德威日以轻骑抄之，思安乃自东南山口筑甬道，属于夹寨。',
      '营垒与粮道建设为过程；不将一天内的任命日等同全部筑城完成日。')
event('lei_revoked','雷彦恭攻涔阳公安败后，后梁削其官爵',50,
      '九月，雷彦恭攻涔阳、公安，高季昌击败之。',
      when='907年九月；削官在丙申',place='涔阳、公安',
      note='进攻及战败发生于九月，削官在下句丙申；不强合为同一日。',reuse_key='event_0907_lei_revoked')
claim('event','event_0907_lei_revoked','description','后梁命高季昌与马殷讨伐雷彦恭。',50,
      '丙申，诏削彦恭官爵，命季昌与楚王殷讨之。',
      '诏令是朝廷命令，不等于两方后来已经完成讨伐。')

# 51: Debate, accession, personnel, and designated son are distinct facts.
event('shu_foundation','王建即帝位，国号大蜀',51,
      '王用安抚副使、掌书记韦庄之谋，帅吏民哭三日；己亥，即皇帝位，国号大蜀。',
      when='907年九月己亥',place='蜀',
      note='韦庄之谋被采纳；冯涓仅建议称制而王建未采纳，不误写为独立既成政权方案。',reuse_key='event_0907_shu_founded')
claim('event','event_0907_shu_founded','description','冯涓主张先由蜀王称制，王建没有采纳。',51,
      '冯涓独献议，请，以蜀王称制，曰：“朝兴则未爽称臣，贼在则不同为恶。”王不从，涓杜门不出。',
      '史书原文有“请，以”断句疑点，建议本身仍清楚；不改写为冯涓支持立即称帝。')
event('shu_officials','王建称帝后任王宗佶、韦庄、唐道袭等职',51,
      '辛丑，以前东川节度使兼侍中王宗佶为中书令，韦庄为左散骑常侍、判中书门下事，阆州防御使唐道袭为内枢密使。',
      when='907年九月辛丑',place='蜀',
      note='官员任命明确在辛丑，与己亥即位相隔，不合并同日。',reuse_key='event_0907_shu_officials')
claim('event','event_0907_shu_officials','description','王建封次子王宗懿为遂王，长子王宗仁因病被废。',51,
      '蜀主长子校书郎宗仁幼以疾废，立其次子秘书少监宗懿为遂王。',
      '封王的具体日次未载；“幼以疾废”是追叙，不能定为907年新废黜。')
extra(new_shu,'event','event_0907_shu_founded','description',
      '《新五代史》卷六十三也记九月己亥王建即位。',
      '秋九月己亥，建乃即皇帝位。',51,'corroborates',
      '新史前句祥瑞叙述不作为即位的因果事实。')
extra(new_shu,'event','event_0907_shu_officials','description',
      '《新五代史》亦列王宗佶中书令、韦庄判中书门下事和唐袭枢密使。',
      '以王宗佶為中書令，韋莊為左散騎常侍判中書門下之事，唐襲為樞密使',51,'corroborates',
      '“唐襲”与主书“唐道袭”字形/称名差异并列，未仅凭省称创设新主体。')

# 52-55: Langzhou relief, Jin raids, and Liu Shouwen's submission.
event('langzhou_battle','楚军击败淮南救雷彦恭之军，俘泠业李饶',52,
      '冬，十月，高季昌遣其将倪可福会楚将秦彦晖攻朗州，雷彦恭遣使乞降于淮南，且告急。',
      when='907年十月',place='朗州、平江、浏阳',
      note='先记高季昌与楚军攻朗州，再记淮南救援及楚军反击；不把各次战事压成同日。',reuse_key='event_0907_langzhou')
claim('event','event_0907_langzhou','description','许德勋率楚军击败淮南援军，俘泠业、李饶后于长沙处死。',52,
      '又破浏阳寨，擒李饶；掠上高、唐年而归。斩业、饶于长沙市。',
      '泠业被俘见前句“擒业”；本句说明李饶被俘及二人后被斩。')
extra(new_langzhou,'event','event_0907_langzhou','description',
      '《新五代史》卷六十六概述雷彦恭召吴人攻平江而许德勋击败之。',
      '朗州雷彥恭召吳人攻平江，許德勳擊敗之。',52,'adds',
      '新史紧接着叙雷彦恭后来出奔，未据此把后续结果倒填到本段。')
event('jiangzhuling','尹皓攻取晋军江猪岭寨',53,
      '十一月，甲申，夹马指挥使尹皓攻晋江猪岭寨，拔之。',
      when='907年十一月甲申',place='江猪岭寨',
      note='主书未交代此寨后续归属，不作外推。',reuse_key='event_0907_jiangzhuling')
event('liu_brothers','刘守文因刘守光囚父而举兵相攻',54,
      '义昌节度使刘守文闻其弟守光幽其父，集将吏大哭曰：“不意吾家生此枭獍！吾生不如死，誓与诸君讨之！”乃发兵击守光，互有胜负。',
      when='907年十一月条；确日未载',
      note='“闻其弟守光幽其父”为先前事实；本段新事是刘守文起兵，双方互有胜负。',
      reuse_key='event_0907_liu_brothers')
event('liushouwen_submits','罗绍威致书劝降后刘守文请降于梁并送子为质',55,
      '守文亦恐梁乘虚袭其后，戊子，遣使请降，以子延祐为质。',
      when='907年十一月戊子',place='沧州',
      note='请降与送质为主书记载；不将罗绍威的判断写作不战占领沧州。',
      reuse_key='event_0907_liushouwen_surrender')
claim('event','event_0907_liushouwen_surrender','description','后梁加刘守文中书令并予安抚。',55,
      '加守文中书令，抚纳之。','此为请降后的授官，不推定刘守文与刘守光战争当即结束。')

# 56: Retrospective punitive practices are not newly enacted in 907.
event('deserters_amnesty','后梁赦逃亡军士并允许有面纹者还乡',56,
      '壬寅，诏赦其罪，自今虽文面亦听还乡里。盗减什七八。',
      when='907年十一月壬寅',
      note='“盗减什七八”为主书效果概述，非可核现代统计；前述跋队斩和文面之设属追叙。',
      reuse_key='event_0907_deserters_amnesty')
claim('event','event_0907_deserters_amnesty','description','朱温此前使用跋队斩与士兵文面制度，导致逃兵难以归乡。',56,
      '初，帝在籓镇，用法严，将校有战没者，所部兵悉斩之，谓之跋队斩。',
      '“初”明确追叙旧制，起始年未载；本年新措施为赦免。')

# 57-61: Yingzhou, Jinzhou, Mingzhou, and Xinzhou.
event('yingzhou_attack','淮南米志诚攻颍州外郭，张实守子城',57,
      '淮南右都押牙米志诚等将兵渡淮袭颍州，克其外郭。刺史张实据子城拒守。',
      when='907年十一月壬寅后、十二月前；确日未载',place='颍州',
      note='淮南军仅克外郭，刺史继续守子城；援军后续在第59段。',reuse_key='event_0907_yingzhou')
event('jinzhou_attack','李克用命李存璋攻晋州牵制上党梁军',58,
      '晋王命李存璋攻晋州，以分上党兵势。十二月，壬戌，诏河中、陕州发兵救之。',
      when='907年十二月壬戌梁诏救援；晋军攻城日未载',place='晋州',
      note='把晋军攻城与梁廷壬戌救援诏区分；不擅定攻城确日。',reuse_key='event_0907_jinzhou_attack')
event('yingzhou_relief','后梁发兵救颍州，淮南米志诚等撤退',59,
      '甲子，诏发步骑五千救颍州，米志诚等引去。',
      when='907年十二月甲子',place='颍州',
      note='与第57段同一战役复用稳定事件，救援诏令及撤退在此日条。',reuse_key='event_0907_yingzhou')
event('mingzhou_raid','晋军进攻洺州',60,'丁卯，晋兵寇洺州。',
      when='907年十二月丁卯',place='洺州',
      note='主书未指明带兵者及战果，不增加具体将领。',reuse_key='event_0907_mingzhou')
event('xinzhou_attack','淮南兵攻信州，危仔倡求援于吴越',61,
      '淮南兵攻信州，刺史危仔倡求救于吴越。',
      when='907年十二月丁卯后；确日未载',place='信州',
      note='只有攻城与求援，不倒填908年吴越响应。',reuse_key='event_0907_xinzhou')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(45,62):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷266开平元年第45—61段连续处理；前蜀建国与十月至年末诸战事分段，追叙和电子疑字留校。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=266,year=907,
    primary_source_key=primary,primary_source_keys=[primary,yearend],
    paragraphs=[Q[n]['id'] for n in range(45,62)],next_paragraph=None,
    coverage='卷266开平元年第45—61段连续处理；八九月政军事、前蜀建国、朗州攻防及年末各地战事。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
