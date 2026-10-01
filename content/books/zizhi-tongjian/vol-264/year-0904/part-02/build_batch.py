"""Curate Tongjian 264, year 904, consecutive paragraphs 5–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 12))
primary = 'tongjian-264-904-early'
old_feb = 'jiutangshu-020-luoyang-february'
old_kezhen = 'jiutangshu-020-kezhen'
old_gushui = 'jiutangshu-020-gushui'
new_move = 'xinwudaishi-001-relocation'
old_902_a = 'tongjian-263-902-xuwan'
old_902_b = 'tongjian-263-902-winter'
B = {'format_version': 1, 'batch_key': 'zztj-v264-y0904-p005-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-01/sources/library' / primary, 'da18066', '司马光等'),
    (old_feb, P / 'sources/library' / old_feb, '94f48c2c', '刘昫等'),
    (old_kezhen, P / 'sources/library' / old_kezhen, '94f48c2c', '刘昫等'),
    (old_gushui, P / 'sources/library' / old_gushui, '94f48c2c', '刘昫等'),
    (new_move, P / 'sources/library' / new_move, '94f48c2c', '欧阳修等'),
    (old_902_a, ROOT / 'content/books/zizhi-tongjian/vol-263/year-0902/part-06/sources/library' / old_902_a, 'd7ab9ff', '司马光等'),
    (old_902_b, ROOT / 'content/books/zizhi-tongjian/vol-263/year-0902/part-06/sources/library' / old_902_b, 'd7ab9ff', '司马光等'),
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
for n in range(5, 9):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','邪律阿保机':'耶律阿保机','硃友谅':'朱友谅','李继徽':'杨崇本','独孤捐':'独孤损','钱传撩':'钱传璙','侯矩':'王宗矩','张濬':'张浚','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范','李存审':'符存审','王宗本':'谢从本','硃延寿':'朱延寿','王坛':'王檀','坛':'王檀','硃氏（杨行密夫人）':'朱氏（杨行密夫人）','郭行頵':'郭行悰','侯矩':'王宗矩','硃友伦':'朱友伦','硃全忠':'朱温','邪律阿保机':'耶律阿保机','硃友谅':'朱友谅','李继徽':'杨崇本','独孤捐':'独孤损','钱传撩':'钱传璙','侯矩':'王宗矩','张濬':'张浚'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0904_02_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷264·天祐元年（904）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷264天祐元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=904):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_264_0904_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '904年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '904年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_264_0904_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_264_0904_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 5: court offices, the tense banquet, and the emperor's second appeal.
event('zhu_controls_palace_guards','朱全忠三月丁未兼判左右神策及六军诸卫事',5,
      '三月，丁未，以硃全忠兼判左、右神策及六军诸卫事。',
      [('朱温','新兼判者')],when='904年三月丁未',place='陕州行在',
      note='职责按主书原文登记，不推成已直接指挥全部侍卫。')
event('zhu_invites_emperor','朱全忠癸丑设宴邀唐昭宗临幸',5,
      '癸丑，全忠置酒私第，邀上临幸。',
      [('朱温','设宴者'),('李杰','被邀者')],when='904年三月癸丑',place='陕州',
      note='主书仅记设宴与邀请；未扩写该次宴席内容。')
event('zhu_goes_luoyang','朱全忠乙卯先赴洛阳督修宫室',5,
      '乙卯，全忠辞上，先赴洛阳督修宫室。',
      [('朱温','先赴洛阳者'),('李杰','受辞者')],when='904年三月乙卯',place='洛阳',
      note='《旧唐书》昭宗纪将辞赴洛阳记在二月乙亥，月日异说并列。')
event('shan_banquet_suspicion','昭宗宴朱全忠与韩建，可证附耳、韩建蹑足使朱疑而不饮',5,
      '上与之宴群臣，既罢，上独留全忠及忠武节度使韩建饮，皇后出，自捧玉卮以饮全忠，晋国夫人可证附上耳语。建蹑全忠足，全忠以为图己，不饮，阳醉而出。',
      [('李杰','留宴者'),('朱温','猜疑并佯醉者'),('韩建','蹑足者'),('何氏（唐昭宗皇后）','奉酒者'),('可证','附耳语者')],
      when='904年三月乙卯前后；确日未载',place='陕州',
      note='可证为晋国夫人名，《旧唐书》另记其传诏；“图己”只是朱全忠的猜疑，原文未证阴谋。')
event('zhu_reassigns_han_liu','朱全忠奏以长安为佑国军，韩建与刘知俊分任节度使',5,
      '全忠奏以长安为佑国军，以韩建为佑国节度使，以郑州刺史刘知俊为匡国节度使。',
      [('朱温','上奏者'),('韩建','佑国节度使人选'),('刘知俊','匡国节度使人选')],
      when='904年三月乙卯前后；确日未载',place='长安',
      note='原文为朱全忠奏请，不把奏表时点与最终履职时点混为一日。')
event('emperor_silk_appeal','唐昭宗丁巳以绢诏告急王建、杨行密、李克用等',5,
      '丁巳，上复遣间使以绢诏告急于王建、杨行密、李克用等，令纠帅籓镇以图匡复，曰：“朕至洛阳，则为所幽闭，诏敕皆出其手，朕意不复得通矣！”',
      [('李杰','遣使与出诏者'),('王建','受诏对象'),('杨行密','受诏对象'),('李克用','受诏对象')],
      when='904年三月丁巳',
      note='昭宗对将来受幽闭是预期和求援理由，不能前置为已遭幽闭。')

# 6: return of hostages and an unsuccessful peace overture.
event('qian_chuanliao_returns','杨行密遣钱传璙及其妻与顾全武归钱塘',6,
      '杨行密遣钱传撩及其妇并顾全武归钱塘。',
      [('杨行密','遣返者'),('钱传璙','归钱塘者'),('杨氏（钱传璙妻）','随夫归钱塘者'),('顾全武','同归者')],
      when='904年三月；确日未载',place='钱塘',
      note='本地《通鉴》作“钱传撩”，对照卷263天复二年连续叙事之“传璙”“傅璙”和同一求婚关系归并钱传璙；其妇姓名未载。')
event('li_shenfu_renews_e_yue','李神福受任鄂岳招讨使后再攻杜洪',6,
      '以淮南行军司马李神福为鄂岳招讨使，复将兵击杜洪。',
      [('杨行密','任命方'),('李神福','招讨使并率军者'),('杜洪','被攻目标')],
      when='904年三月；确日未载',place='鄂岳',
      note='上年李神福曾固辞宁国节度使；此处另任鄂岳招讨使，不能合并官职。')
event('zhu_yang_e_yue_talks','朱全忠请杨行密舍鄂岳修好，杨要求先迎帝还长安',6,
      '硃全忠遣使诣行密，请舍鄂岳，复修旧好。行密报曰：“俟天子还长安，然后罢兵修好。”',
      [('朱温','遣使求和者'),('杨行密','附条件答复者')],
      when='904年三月；确日未载',
      note='“俟天子还长安”是杨行密设的前提；本段没有达成停战。')

# 7: pressured departure, astrological warning, and executions.
event('zhu_urges_emperor_east','朱全忠四月辛巳称洛阳宫成催行，昭宗请俟十月',7,
      '夏，四月，辛巳，硃全忠奏洛阳宫室已成，请车驾早发，表章相继。上屡遣宫人谕以皇后新产，未任就路，请俟十月东行。',
      [('朱温','上奏催促者'),('李杰','请延行者'),('何氏（唐昭宗皇后）','新产者')],
      when='904年四月辛巳及后续；确日未载',place='陕州、洛阳',
      note='皇后新产为昭宗请求延行的理由；“洛阳宫室已成”是朱全忠奏词，不据此推定工程完全竣工。')
event('zhu_orders_kou_hurry','朱全忠疑昭宗等待变局，令寇彦卿即日促驾',7,
      '全忠疑上徘徊俟变，怒甚，谓牙将寇彦卿曰：“汝速至陕，即日促官家发来。”',
      [('朱温','疑虑并下令者'),('寇彦卿','受命催行者'),('李杰','被催行者')],
      when='904年四月辛巳后；确日未载',place='陕州',
      note='“俟变”仅为朱全忠猜测；不据此认定昭宗已联络反朱行动。')
event('astronomers_warn_east','司天监在陕州奏称秋季星气不利东行，昭宗欲十月入洛',7,
      '上之在陕也，司天监奏：“星气有变，期在今秋，不利东行。”故上欲以十月幸洛。',
      [('李杰','欲推迟东行者')],
      when='在陕时的追叙；904年四月前后',place='陕州',
      note='星气不利是司天监奏言，非天象导致实际灾事的客观结论；奏者个人未载。')
event('emperor_departs_shan','昭宗闰四月丁酉离陕，朱全忠壬寅在新安迎驾',7,
      '闰月，丁酉，车驾发陕。壬寅，全忠逆于新安。',
      [('李杰','离陕者'),('朱温','新安迎驾者')],
      when='904年闰四月丁酉、壬寅',place='陕州、新安',
      note='《旧唐书》书“闰四月乙未朔”，确认闰月为闰四月；两个干支各属不同动作。')
event('zhu_executes_attendants','朱全忠使许昭远告阎祐之、王墀、韦周、可证谋害并杀之',7,
      '至是，全忠令医官许昭远告医官使阎祐之、司天监王墀、内都知韦周、晋国夫人可证等谋害元帅，悉收杀之。',
      [('朱温','命告并收杀者'),('许昭远','告发者'),('阎祐之','被告并被杀者'),('王墀','被告并被杀者'),('韦周','被告并被杀者'),('可证','被告并被杀者')],
      when='904年闰四月壬寅后；确日未载',
      note='“谋害元帅”为朱全忠借许昭远提出的指控，原文未证实；可证与第5段晋国夫人同人。')

# 8: killings at Gushui and accession to the Luoyang palace.
event('gushui_attendants_killed','朱全忠在谷水设食缢杀随驾二百余侍从',8,
      '癸卯，上憩于谷水。自崔胤之死，六军散亡俱尽，所馀击球供奉、内园小儿共二百馀人，从上而东。全忠犹忌之，为设食于幄，尽缢杀之。',
      [('李杰','行至谷水者'),('朱温','设食并杀侍从者')],
      when='904年闰四月癸卯',place='谷水',
      note='二百余人为史书约数；《旧唐书》记“并坑之”，死法异文并列。')
event('gushui_guards_replaced','朱全忠预选相貌相近者替代昭宗原侍卫',8,
      '豫选二百馀人大小相类者，衣其衣服，代之侍卫。上初不觉，累日乃寤。自是上之左右职掌使令皆全忠之人矣。',
      [('朱温','预选并替换侍卫者'),('李杰','数日后察觉者')],
      when='904年闰四月癸卯后；确日未载',place='谷水、洛阳',
      note='替代发生在旧侍从被杀后；“累日”不换算具体天数。')
event('emperor_enters_luoyang','唐昭宗闰四月甲辰入洛阳宫，受朝贺',8,
      '甲辰，车驾发谷水，入宫，御正殿，受朝贺。',
      [('李杰','入宫并受朝贺者')],
      when='904年闰四月甲辰',place='洛阳宫',
      note='先发谷水后入宫，地点顺序按原文。')
event('emperor_amnesty_era','唐昭宗闰四月乙巳光政门赦天下并改元',8,
      '乙巳，御光政门，赦天下，改元。更命陕州曰兴唐府。',
      [('李杰','赦天下并改元者')],
      when='904年闰四月乙巳',place='洛阳光政门',
      note='主书此句未写改元名称，卷年标题作天祐元年；陕州更名兴唐府同日条。')
event('emperor_orders_against_li_yang','唐廷下诏讨李茂贞与杨崇本',8,
      '诏讨李茂贞、杨崇本。',
      [('李杰','下诏名义者'),('李茂贞','被讨对象'),('杨崇本','被讨对象')],
      when='904年闰四月乙巳',
      note='仅为诏讨，不前置为后续实际战役。')

for code,a,b,kind,description,n,quote,note in [
    ('qian_yang_wife','杨氏（钱传璙妻）','钱传璙','妻子','杨氏是钱传璙的妻子。',6,'其妇','本段“其妇”承钱传璙；前卷婚配可核杨行密以女妻之。'),
]:
    pa=person(a,n,kind,quote)
    pb=person(b,n,kind,quote)
    key='relationship_zztj_264_0904_'+code
    B['person_relationships'].append(dict(key=key,person_a_key=pa,person_b_key=pb,
        relation_type=kind,description=description,status='draft'))
    claim('person_relationship',key,'description',description,n,quote,note)

daughter='relationship_zztj_264_0904_yang_daughter'
B['person_relationships'].append(dict(key=daughter,person_a_key=people['杨氏（钱传璙妻）'],
    person_b_key=person('杨行密',6,'钱传璙妻之父','杨行密遣钱传撩及其妇并顾全武归钱塘。'),
    relation_type='女儿',description='杨氏（钱传璙妻）是杨行密的女儿。',status='draft'))

extra(old_902_a,'person',people['钱传璙'],'description',
      '卷263天复二年原文记钱镠之子名传璙，遣与顾全武赴广陵。',
      '镠命其子传璙微服为全武仆，与偕之广陵',6,'adds',
      '据连续叙事与顾全武同行及归钱塘，校读本批底本“传撩”为钱传璙；原字不改。')
extra(old_902_b,'person_relationship',daughter,'description',
      '卷263天复二年记杨行密以女嫁傅璙，确认本批“其妇”的父女身份。',
      '行密许之，以女妻傅璙',6,'adds',
      '该处“傅璙”又为前段钱传璙异写；姓名未载，故以杨氏占位，不外推其他身份。')
extra(old_feb,'event','event_zztj_264_0904_zhu_goes_luoyang','time_original',
      '《旧唐书》昭宗纪作二月乙亥朱全忠辞赴洛阳。',
      '二月丙寅朔。乙亥，全忠辭赴洛陽，親督工作',5,'conflicts',
      '《通鉴》本段置三月乙卯；两书月日不同，不能以一方覆盖另一方。')
extra(old_kezhen,'person',people['可证'],'description',
      '《旧唐书》昭宗纪称晋国夫人可證传诏，印证可证为人物名。',
      '帝遣晉國夫人可證傳詔諭全忠',5,'corroborates',
      '“晋国夫人”为封号，“可证”为人名；旧书作繁体可證。')
extra(old_kezhen,'event','event_zztj_264_0904_zhu_urges_emperor_east','description',
      '《旧唐书》也记朱全忠疑昭宗延行，命寇彦卿催驾。',
      '全忠意上遲留俟變，怒甚，謂牙將寇彥卿曰',7,'corroborates',
      '其传诏日书四月癸巳，主书写四月辛巳起奏请；不强当作同一日。')
extra(old_gushui,'event','event_zztj_264_0904_gushui_attendants_killed','description',
      '《旧唐书》昭宗纪记谷水侍从被“坑”，与《通鉴》“缢杀”死法不同。',
      '至谷水頓，全忠令醫官許昭遠告內園等謀變，因會設幄，酒食次並坑之',8,'conflicts',
      '《通鉴》为设食尽缢杀；旧书坑杀与告发细节并列，不能合成确定死法。')
extra(new_move,'event','event_zztj_264_0904_gushui_guards_replaced','description',
      '《新五代史》梁太祖纪亦记谷水杀随驾人后以梁人替换。',
      '悉殺而代之，然後以聞。由是，天子左右皆梁人矣',8,'corroborates',
      '概述与主书相近，未补出具体替代者姓名。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(5,9):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天祐元年第5—8段连续处理；人名讹字按跨年原文校核，诏令、猜疑与事实分开，谷水死法异说并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=904,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(5,9)],next_paragraph=Q[9]['id'],
    coverage='卷264天祐元年共11个非空段落中的第5—8段连续处理；三月诏令、淮南交涉、闰四月东迁与谷水侍从案。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
