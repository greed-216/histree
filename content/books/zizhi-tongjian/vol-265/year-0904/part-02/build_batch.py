"""Curate Tongjian 265, year 904, consecutive paragraphs 6–10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 22))
primary_early = 'tongjian-265-904-early'
primary_late = 'tongjian-265-904-late'
old_assassination = 'jiutangshu-020-assassination'
old_succession = 'jiutangshu-020-succession'
new_assassination = 'xinwudaishi-043-assassination'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0904-p006-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_early, P.parent / 'part-01/sources/library' / primary_early, '2377218f', '司马光等'),
    (primary_late, P / 'sources/library' / primary_late, '40fd2522', '司马光等'),
    (old_assassination, P / 'sources/library' / old_assassination, '40fd2522', '刘昫等'),
    (old_succession, P / 'sources/library' / old_succession, '40fd2522', '刘昫等'),
    (new_assassination, P / 'sources/library' / new_assassination, '40fd2522', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_early, primary_late)}
for n in range(6, 11):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '硃友恭':'朱友恭', '李彦威':'朱友恭', '德王裕':'李祐', '裕':'李祐', '辉王祚':'李祚', '祚':'李祚', '柷':'李祚'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0904_02_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐元年（904）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷265天祐元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=904):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0904_' + code
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
        edge = 'participation_zztj_265_0904_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0904_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 6: retrospection after the Fengxiang return, then surveillance at Luoyang.
event('zhu_urges_de_prince_removal','朱全忠于凤翔回銮后疑德王李祐，曾促崔胤劝昭宗除之',6,
      '初，硃全忠自凤翔迎车驾还，见德王裕眉目疏秀，且年齿已壮，恶之，私谓崔胤曰：“德王尝奸帝位，岂可复留！公何不言之！”胤言于帝。',
      [('朱温','私劝崔胤者'),('崔胤','向昭宗转述者'),('李祐','被朱全忠忌惮者'),('李杰','听崔胤转述者')],
      when='凤翔回銮后追叙；确日未载',year=None,
      note='以“初”引往事，不能认作904年七月新发生；德王裕复用原德王李祐主体。')
event('zhu_denies_de_prince_words','昭宗问及德王事，朱全忠否认并指责崔胤',6,
      '帝问全忠，全忠曰：“陛下父子之间，臣安敢窃议，此崔胤卖臣耳。”',
      [('李杰','质问者'),('朱温','否认并指责者'),('崔胤','被指责者')],
      when='凤翔回銮后追叙；确日未载',year=None,
      note='这是朱全忠的辩词；与前句叙述不合，不能只取辩词为事实。')
event('emperor_fears_after_changan','昭宗离长安后忧惧，与皇后饮酒或相对泣',6,
      '帝自离长安，日忧不测，与皇后终日沉饮，或相对涕泣。',
      [('李杰','忧惧者'),('何氏（唐昭宗皇后）','同饮或相泣者')],
      when='离长安后持续状况；904年',place='洛阳',
      note='“终日”为史书概述，不量化为每日确证；迁都后的地点据上下文为洛阳。')
event('jiang_spies_on_emperor','朱全忠使蒋玄晖伺察昭宗动静',6,
      '全忠使枢密使蒋玄晖伺察帝，动静皆知之。',
      [('朱温','命令伺察者'),('蒋玄晖','伺察者'),('李杰','被伺察者')],
      when='昭宗至洛阳后；确日未载',place='洛阳',
      note='伺察属《通鉴》叙述，不据此推定具体侦察制度或密探人数。')
event('emperor_questions_de_prince_threat','昭宗对蒋玄晖问朱全忠为何坚欲杀德王',6,
      '帝从容谓玄晖曰：“德王，朕之爱子，全忠何故坚欲杀之？”因泣下，啮中指血流。玄晖具以语全忠，全忠愈不自安。',
      [('李杰','询问并悲泣者'),('蒋玄晖','听闻并转告者'),('朱温','被问及并获转告者'),('李祐','被昭宗称爱子者')],
      when='昭宗至洛阳后；确日未载',place='洛阳',
      note='“坚欲杀之”为昭宗的疑问，不前置为德王已被杀。')

# 7: proclamations and conspiracy are distinct claims.
event('regional_proclamations_restore_tang','李茂贞等七镇移檄往来，以兴复为辞',7,
      '时李茂贞、杨崇本、李克用、刘仁恭、王建、杨行密、赵匡凝移檄往来，皆以兴复为辞。',
      [('李茂贞','移檄者'),('杨崇本','移檄者'),('李克用','移檄者'),('刘仁恭','移檄者'),
       ('王建','移檄者'),('杨行密','移檄者'),('赵匡凝','移檄者')],
      when='904年昭宗遇害前；确日未载',
      note='名单与动机依主书所记；不推成七镇已组成统一指挥军队。')
event('zhu_plans_child_ruler','朱全忠惧内变，欲立幼君以图禅代',7,
      '全忠方引兵讨，以帝有英气，恐变生于中，欲立幼君，易谋禅代。',
      [('朱温','有立幼君谋划者'),('李杰','被其忌惮者')],
      when='904年昭宗遇害前；确日未载',
      note='“恐变生于中”为朱的顾虑；“欲立幼君”是当时意图，不写成已完成禅代。')
event('li_zhen_plans_luoyang','朱全忠遣李振至洛阳与蒋玄晖、朱友恭、氏叔琮议谋',7,
      '乃遣判官李振至洛阳，与玄晖及左龙武统军硃友恭、右龙武统军氏叔琮等图之。',
      [('朱温','遣李振者'),('李振','赴洛阳议谋者'),('蒋玄晖','参与议谋者'),
       ('朱友恭','参与议谋者'),('氏叔琮','参与议谋者')],
      when='904年八月壬寅前；确日未载',place='洛阳',
      note='“图之”承立幼君、谋禅代及帝位变动，具体分工待下段；不把李振写成持剑行凶者。')

# 8: the palace attack, individual deaths, and the empress's release.
event('jiang_selects_guards','蒋玄晖选史太等龙武牙官夜叩椒殿宫门',8,
      '八月，壬寅，帝在椒殿，玄晖选龙武牙官史太等百人夜叩宫门，言军前有急奏，欲面见帝。',
      [('蒋玄晖','选兵与指挥者'),('史太','所选龙武牙官'),('李杰','被求见者')],
      when='904年八月壬寅夜',place='洛阳椒殿',
      note='“军前有急奏”为叩门说辞；百人为史书约数。')
event('shi_tai_kills_pei','裴贞一开门质疑持兵奏事，史太杀之',8,
      '夫人裴贞一开门见兵，曰：“急奏何以兵为？”史太杀之。',
      [('裴贞一','开门质疑并遇害者'),('史太','杀害者')],
      when='904年八月壬寅夜',place='洛阳椒殿',
      note='《新五代史》作“裴正一”，保留字形异文而不另建人。')
event('shi_tai_kills_zhaozong','史太追及昭宗李杰并弑之',8,
      '帝方醉，遽起，单衣绕柱走，史太追而弑之。',
      [('李杰','遇害者'),('史太','直接行凶者')],
      when='904年八月壬寅夜',place='洛阳椒殿',
      note='《通鉴》《旧唐书》作壬寅夜，《新五代史》这一段作壬辰，日期异说并列。')
event('shi_tai_kills_li_jianrong','昭仪李渐荣护昭宗，亦被史太杀害',8,
      '昭仪李渐荣临轩呼曰：“宁杀我曹，勿伤大家！”帝方醉，遽起，单衣绕柱走，史太追而弑之。渐荣以身蔽帝，太亦杀之。',
      [('李渐荣','护帝并遇害者'),('史太','杀害者')],
      when='904年八月壬寅夜',place='洛阳椒殿',
      note='呼喊和护帝为原文明确动作；不据后续伪诏认定其谋逆。')
event('empress_he_spared','何后求哀于蒋玄晖，暂免当夜被杀',8,
      '又欲杀何后，后求哀于玄晖，乃释之。',
      [('何氏（唐昭宗皇后）','求哀并暂被释放者'),('蒋玄晖','接受求哀者')],
      when='904年八月壬寅夜',place='洛阳椒殿',
      note='“乃释之”仅限当夜，不推为后续始终安全。')

# 9: forged decrees and Li Zuo's accession, without making a second person for Li Zhu.
event('jiang_forges_accusation','蒋玄晖癸卯矫诏诬李渐荣、裴贞一弑逆',9,
      '癸卯，蒋玄晖矫诏称李渐荣、裴贞一弑逆',
      [('蒋玄晖','矫诏并诬告者'),('李渐荣','被诬告者'),('裴贞一','被诬告者')],
      when='904年八月癸卯',
      note='主书标明“矫诏”；弑逆是伪诏指控，与第8段所载受害事实相反。')
event('li_zuo_named_heir','伪诏立辉王李祚为皇太子，更名柷并监军国事',9,
      '宜立辉王祚为皇太子，更名柷，监军国事。',
      [('李祚','被立为皇太子并改名柷者'),('蒋玄晖','伪诏操作者')],
      when='904年八月癸卯',
      note='祚与柷为同一人；复用903年已建李祚主体，不能另建李柷。')
event('jiang_forges_empress_order','蒋玄晖又矫皇后令，令皇太子于柩前即位',9,
      '又矫皇后令，太子于柩前即位。',
      [('蒋玄晖','伪令操作者'),('李祚','被令即位者'),('何氏（唐昭宗皇后）','名义上被冒用者')],
      when='904年八月癸卯',
      note='此令亦为“矫”，不得写成何后真实主动授意。')
event('li_zuo_accession','李祚丙午以昭宣帝身份即位',9,
      '丙午，昭宣帝即位，时年十三。',
      [('李祚','即位者')],when='904年八月丙午',place='洛阳',
      note='昭宣帝即改名柷的辉王祚；本批复用李祚。既有907档案另有“唐昭宣帝”旧主体，后续接续时需专门去重。')

# 10: separate regional appointment.
event('li_keyong_reappoints_zhang_chengye','李克用再次任张承业为监军',10,
      '李克用复以张承业为监军。',
      [('李克用','任命者'),('张承业','受任监军者')],
      when='904年八月后条；确日未载',
      note='“复”明示再次任命；不由此句补出前次离职年月。')

extra(old_assassination,'event','event_zztj_265_0904_shi_tai_kills_zhaozong','description',
      '《旧唐书》卷二十上同记壬寅夜史太追昭宗而弑之。',
      '帝單衣旋柱而走，太追而弑之',8,'corroborates',
      '证实施害者与动作；旧书又记八月壬辰朔，壬寅夜。')
extra(old_assassination,'person',people['裴贞一'],'description',
      '《旧唐书》亦记贞一夫人启关后被史太杀害。',
      '貞一夫人啟關，謂玄暉曰：「急奏不應以卒來。」史太執貞一殺之',8,'corroborates',
      '与主书裴贞一同一人；字形简繁归并，摘录保原字。')
extra(old_succession,'event','event_zztj_265_0904_jiang_forges_accusation','description',
      '《旧唐书》卷二十下录蒋玄晖矫宣遗诏，将罪名归给李渐荣与裴贞一。',
      '蔣玄暉矯宣遺詔',9,'corroborates',
      '旧书引伪诏长文但明确标“矫”；不得把诏内罪名作已证事实。')
extra(old_succession,'event','event_zztj_265_0904_li_zuo_named_heir','description',
      '《旧唐书》伪诏亦称辉王祚改名柷、立为皇太子。',
      '輝王祚幼彰岐嶷，長實端良',9,'corroborates',
      '只以姓名及继位安排作身份对读；赞词属伪诏修辞。')
extra(old_succession,'event','event_zztj_265_0904_li_zuo_accession','time_original',
      '《旧唐书》记丙午皇太子柩前即位。',
      '丙午，大行皇帝大殮，皇太子柩前即皇帝位',9,'corroborates',
      '具体仪节由旧书补充，干支与主书相合。')
extra(new_assassination,'event','event_zztj_265_0904_shi_tai_kills_zhaozong','time_original',
      '《新五代史》卷四十三作八月壬辰，主书及《旧唐书》作壬寅夜。',
      '八月壬辰，彥威、叔琮以龍武兵宿禁中',8,'conflicts',
      '新书原字保留；此段对日期异说暂不取舍，纸本未校。')
extra(new_assassination,'person',people['裴贞一'],'description',
      '《新五代史》作“裴正一”，主书及《旧唐书》作贞一。',
      '夫人裴正一開門問曰',8,'conflicts',
      '同一椒殿开门遇害情节，视为姓名异文，不新建裴正一。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(6,11):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷265天祐元年第6—10段连续处理；“初”段追叙、伪诏指控、史书日期及人名异文分开校核。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=265,year=904,
    primary_source_key=primary_early,primary_source_keys=[primary_early,primary_late],
    paragraphs=[Q[n]['id'] for n in range(6,11)],next_paragraph=Q[11]['id'],
    coverage='卷265天祐元年第6—10段连续处理；昭宗忧惧、朱全忠谋立幼君、椒殿遇害、伪诏继位及张承业任监军。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
