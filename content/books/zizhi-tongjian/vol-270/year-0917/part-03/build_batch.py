"""Curate consecutive Tongjian vol. 270, 917 paragraphs 8–12."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 21))
main = 'tongjian-270-917-autumn'
newgov = 'xinwudaishi-038-zhang-chengye-governance'
newtreasury = 'xinwudaishi-038-zhang-chengye-treasury'
newlady = 'xinwudaishi-014-lady-liu-father'
specs = [
    (main,ROOT / 'content/books/zizhi-tongjian/vol-270/year-0917/part-02/sources/library' / main,'d1b943a5','司马光等'),
    (newgov,P / 'sources/library' / newgov,'6666c0e1','欧阳修'),
    (newtreasury,P / 'sources/library' / newtreasury,'6666c0e1','欧阳修'),
    (newlady,P / 'sources/library' / newlady,'6666c0e1','欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0917-p008-p012',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_dirs = {key: path for key, path, _, _ in specs}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/270.txt').read_text().splitlines()
for n in range(8, 13):
    assert Q[n]['text'] == lines[Q[n]['source_line'] - 1]
registry = {}
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    for row in json.loads(path.read_text())['people']:
        old = registry.get(row['name'])
        if old:
            assert old['key'] == row['key'], (row['name'], path)
        registry[row['name']] = row
people, used, reused, supplements = {}, {}, set(), []

def choose_source(n, quote):
    for key in (main,):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷270·贞明三年（917）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_270_0917_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'晋王':'李存勖','蜀主':'王建','越王岩':'刘岩','吴王':'杨隆演','李绍荣':'元行钦','刘夫人':'刘夫人（李存勖妻）','曹太夫人':'曹太夫人（李存勖母）','韩夫人':'韩夫人（李存勖妻）','伊夫人':'伊夫人（李存勖妻）'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases=[],
                   era='五代十国', birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明三年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '原文称谓与既有姓名合并；原文摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=917):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_270_0917_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '917年本段条；确日未载', dynasty='五代十国',
               description=title + '。', phases=[], location_name=place,
               location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown',
               location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',
               status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote,
          note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', row['time_original'], n, quote,
          '只保留原纪年，不换算公历日；叙述性回顾不推成逐次日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_270_0917_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p008 mixes Jin's return with retrospective accounts of finance and court life.
event('jin_king_returns_jinyang','晋王李存勖返回晋阳',8,
      '晋王还晋阳。',[('晋王','返回晋阳的晋王')],when='917年秋冬间；确日未载',place='晋阳',
      note='只记本段起句，后续长期政务与家事不一律定在返抵当天。')
event('zhang_chengye_jin_governance','张承业长期管理晋军府政事与后勤',8,
      '王连岁出征，凡军府政事一委监军使张承业，承业劝课农桑，畜积金谷，收市兵马，征租行法不宽贵戚，由是军城肃清，馈饷不乏。',
      [('李存勖','长期委军府政事于张承业者'),('张承业','主管军府政务、农桑和军需者')],
      when='晋王连岁出征期间；具体起讫未载',place='晋阳',year=None,
      note='“连岁”是长期概述，不能把各年财政活动全记在917年。')
claim('event','event_zztj_270_0917_zhang_chengye_jin_governance','description',
      '《新五代史》张承业传亦述其管军国事务、积粮购马、劝农桑。',8,
      '軍國之事，皆委承業，承業亦盡心不懈。凡所以畜積金粟，收市兵馬，勸課農桑，而成莊宗之業者，承業之功為多。',
      '传记为后视概述，与《通鉴》叙述可能同源，不作为独立统计。',newgov,'corroborates')
event('zhang_chengye_refuses_treasury_gift','张承业拒用军库钱供李继岌私赐',8,
      '王乃置酒钱库，令其子继岌为承业舞，承业以宝带及币马赠之。王指钱积呼继岌小名谓承业曰：“和哥乏钱，七哥宜以钱一积与之，带马未为厚也。”承业曰：“郎君缠头皆出承业俸禄，此钱，大王所以养战士也，承业不敢以公物为私礼。”',
      [('李存勖','借子起舞请求军库钱者'),('李继岌','为张承业起舞的晋王之子'),('张承业','拒以军库钱私赠者')],
      when='晋王归省期间；具体年月未载',place='晋阳军库',year=None,
      note='“或时”及传记均未给确年；军费与私赐之争不强定917年。')
claim('event','event_zztj_270_0917_zhang_chengye_refuses_treasury_gift','description',
      '《新五代史》亦载李继岌起舞、张承业赠宝带马而拒拨军库钱。',8,
      '莊宗乃置酒庫中，酒酣，使子繼岌為承業起舞，舞罷，承業出寶帶、幣、馬為贈',
      '同一叙事有文字差异，原文分别保留，未定确年。',newtreasury,'corroborates')
event('zhang_chengye_treasury_quarrel_reconciled','晋王与张承业争军库钱，曹太夫人促其和解',8,
      '王怒，顾李绍荣索剑，承业起，挽王衣泣曰：“仆受先王顾托之命，誓为国家诛汴贼，若以惜库物死于王手，仆下见先王无愧矣。今日就王请死！”阎宝从旁解承业手令退，承业奋拳殴宝踣地',
      [('李存勖','因军库钱与张承业激争者'),('张承业','坚持保留军库钱者'),('李绍荣','晋王索剑所呼将领'),('阎宝','从旁调解而遭殴者')],
      when='军库争论期间；具体年月未载',place='晋阳',year=None,
      note='李绍荣复用元行钦，原文只是被索剑，不推断其拔剑行凶。')
claim('event','event_zztj_270_0917_zhang_chengye_treasury_quarrel_reconciled','description',
      '曹太夫人闻讯召晋王，次日与晋王一同到张承业家致歉。',8,
      '曹太夫人闻之，遽令召王，王惶恐叩头，谢承业曰：“吾以酒失忤七哥，必且得罪于太夫人，七哥为吾痛饮以分其过。”王连饮四卮，承业竟不肯饮。王入宫，太夫人使人谢承业曰：“小儿忤特进，适已笞之矣。”明日，太夫人与王俱至承业第谢之。',
      '和解为同一叙事后段；曹太夫人身份以文中“太夫人”与“小儿”暂定，后续可补亲属证。')
claim('event','event_zztj_270_0917_zhang_chengye_treasury_quarrel_reconciled','description',
      '《新五代史》记晋王向张承业致歉，其母次日与晋王登门慰劳。',8,
      '明日，太后與莊宗俱過承業第，慰勞之。',
      '后书使用事后尊号“太后”“庄宗”；对应当时曹太夫人、晋王，不倒填称号。',newtreasury,'corroborates')
event('zhang_chengye_refuses_jin_titles','张承业辞晋王所授开府等官爵',8,
      '未几，承制授承业开府仪同三司、左卫上将军、燕国公。承业固辞不受，但称唐官以至终身。',
      [('李存勖','承制授张承业官爵者'),('张承业','固辞晋授官爵者')],
      when='军库争论后不久；确年未载',place='晋阳',year=None,
      note='“未几”相对军库争论，前事自身未定年；不强系917年。')
event('zhang_chengye_saves_lu_zhi','张承业借试探劝谏使卢质免祸',8,
      '掌书记卢质，嗜酒轻傲，尝呼王诸弟为豚犬，王衔之。承业恐其及祸，乘间言曰：“卢质数无礼，请为大王杀之。”王曰：“吾方招纳贤才以就功业，七哥何言之过也！”承业起立贺曰：“王能如此，何忧不得天下！”质由是获免。',
      [('卢质','失礼而被晋王记恨的掌书记'),('张承业','借进言试探晋王态度者'),('李存勖','表明仍欲招贤免杀卢质者')],
      when='张承业掌晋军政务期间；确年月未载',place='晋阳',year=None,
      note='这段轶事无确年，不写为917年任免或实际处决。')
event('lady_liu_rejects_father','魏国刘夫人拒认来见的刘叟并命笞于宫门',8,
      '父闻其贵，诣魏宫上谒，王召袁建丰示之。建丰曰：“始得夫人时，有黄须丈人护之，此是也。”王以语夫人，夫人方与诸夫人争宠，以门地相高，耻其家寒微，大怒曰：“妾去乡时略可记忆，妾父不幸死乱兵，妾守尸哭之而去，今何物田舍翁敢至此！”命笞刘叟于宫门。',
      [('刘夫人','拒认刘叟并命杖笞者'),('刘叟','来魏宫求见而受笞者'),('袁建丰','指认刘叟为旧日护送者'),('李存勖','召袁建丰辨认者')],
      when='刘夫人得宠后；确年未载',place='魏宫',year=None,
      note='刘叟父亲身份由主书叙述和袁建丰指认，刘夫人否认；两方说法在事件描述中并列。')
claim('event','event_zztj_270_0917_lady_liu_rejects_father','description',
      '《新五代史》亦记刘叟求见、袁建丰辨认及刘氏命笞。',8,
      '其父聞劉氏已貴，詣魏宮上謁。莊宗召袁建豐問之',
      '两书措辞不同，但均呈现刘氏拒认；不把刘氏自述亡父当已证实事实。',newlady,'corroborates')
claim('person',people['刘夫人（李存勖妻）'],'description',
      '《通鉴》列刘夫人为晋王魏国夫人，在韩夫人、伊夫人之后，并称其最得宠。',8,
      '晋王元妃卫国韩夫人，次燕国伊夫人，次魏国刘夫人。刘夫人最有宠',
      '称号是本段叙事时的位序；不据此推断婚期或精确入宫年份。')

# p009–p012: short consecutive diplomatic, appointment, ritual and military-march entries.
event('liu_tang_mission_to_wu','越王刘岩遣刘瑭告吴即位并劝吴王称帝',9,
      '越王岩遣客省使刘瑭使于吴，告即位，且劝吴王称帝。',
      [('越王岩','派使告即位并劝称帝者'),('刘瑭','受命出使吴的客省使'),('吴王','受劝称帝的吴王')],
      when='917年秋冬；确日未载',place='越、吴',
      note='此段只记出使与劝说，不推断吴王当时已经称帝。')
event('yu_ningji_shu_privy_secretary','蜀主任庾凝绩为吏部尚书、内枢密使',10,
      '闰月，戊申，蜀主以判内枢密院庾凝绩为吏部尚书、内枢密使。',
      [('蜀主','任命庾凝绩者'),('庾凝绩','受任吏部尚书、内枢密使者')],
      when='917年闰月戊申；闰月序数未在本句标明',place='蜀',
      note='承接本卷917年纪年；不自行补闰月的公历日期。')
event('shu_wang_jian_round_mound','蜀主十一月丙子朔祀圜丘',11,
      '十一月，丙子朔，日南至，蜀主祀圜丘。',
      [('蜀主','冬至祀圜丘者')],when='917年十一月丙子朔、日南至',place='蜀',
      note='原文日南至按冬至记，不换算现代公历日期。')
event('jin_king_goes_weizhou_frozen_river','晋王见河冰合，赶赴魏州',12,
      '晋王闻河冰合，曰：“用兵数岁，限一水不得渡，今冰自合，天赞我也。”亟如魏州。',
      [('晋王','闻河封冻而赴魏州者')],when='917年十一月后至十二月前；确日未载',place='魏州',
      note='“天赞我也”是晋王当时的判断，不作超自然事实；渡河作战在后续段落。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(8,13):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷270贞明三年第8—12段；张承业、刘夫人不定年追叙与越吴交聘、蜀授官祭祀、晋赴魏州。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=270,year=917,
    primary_source_key=main,primary_source_keys=[main],paragraphs=[Q[n]['id'] for n in range(8,13)],next_paragraph=Q[13]['id'],
    coverage='卷270贞明三年第8—12段；晋军府治理、家室轶事与越吴蜀晋政事。',supplements=supplements,
    reviewed_questions=[
      {'paragraph_id':Q[8]['id'],'note':'张承业治军府、军库争论和刘氏拒父为本段长篇追叙，无确年者事件年null；新五代史称号带有事后追称。'},
      {'paragraph_id':Q[9]['id'],'note':'越国派使劝吴王称帝仅为外交建议，不视作吴王已即位。'},
      {'paragraph_id':Q[10]['id'],'note':'闰月序数与公历日未自行推算。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
