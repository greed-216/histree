"""Curate Tongjian 264, year 903, consecutive paragraphs 25–28."""
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
primary = 'tongjian-264-903-may'
old_five = 'jiuwudaishi-012-zhu-youning'
new_youning = 'xinwudaishi-013-zhu-youning'
new_wang_a = 'xinwudaishi-023-wang-jingren-a'
new_wang_b = 'xinwudaishi-023-wang-jingren-b'

B = {'format_version': 1, 'batch_key': 'zztj-v264-y0903-p025-p028',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-03/sources/library' / primary, '3ae36b2', '司马光等'),
    (old_five, P.parent / 'part-02/sources/library' / old_five, '71feb52', '薛居正等'),
    (new_youning, P / 'sources/library' / new_youning, '56d0c96', '欧阳修等'),
    (new_wang_a, P / 'sources/library' / new_wang_a, '56d0c96', '欧阳修等'),
    (new_wang_b, P / 'sources/library' / new_wang_b, '56d0c96', '欧阳修等'),
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
for n in range(25, 29):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范','李存审':'符存审'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0903_04_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_264_0903_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 25. The protracted siege, coerced construction and sack are distinct phases.
event('bochang_siege','朱友宁围博昌月余未克，朱全忠遣李捍督战',25,
      '硃友宁攻博昌，月馀不拔。硃全忠怒，遣客将李捍往督之。',
      [('朱友宁','攻城者'),('朱温','遣督战者'),('李捍','督战者')],
      when='903年五月至六月间；确日未载',place='博昌',
      note='“月馀”为围城时长，不能据此反推出开战日。')
event('bochang_forced_labor','朱友宁驱民丁及牲畜筑博昌土山',25,
      '捍至，友宁驱民丁十馀万，负木石，牵牛驴，诣城南筑土山，既成，并人畜木石排而筑之，冤号声闻数十里。',
      [('朱友宁','驱民筑山者'),('李捍','到场督战者')],
      when='903年五月至六月间；确日未载',place='博昌城南',
      note='十余万与“冤号声闻数十里”为主书记述，保留记数和叙述范围；不得写作自愿劳役。')
event('bochang_massacre','朱友宁军陷博昌并屠城',25,
      '俄而城陷，尽屠之。',[('朱友宁','围攻主将')],
      when='903年五月至六月间；确日未载',place='博昌',
      note='“之”承博昌城，主书记屠城，不估算死亡人数。')
event('linzi_taken','朱友宁进拔临淄抵青州并遣军攻登莱',25,
      '进拔临淄，抵青州城下，遣别将攻登、莱。',
      [('朱友宁','继续进军与遣军者')],
      when='903年五月至六月间；确日未载',place='临淄、青州、登州、莱州',
      note='临淄记“拔”，登莱只记遣军进攻，不提前写入第27段登州陷落。')

# 26. Mizhou capture and appointments, with an explicit older-brother relation.
event('mizhou_taken','王茂章会王师诲攻取密州并斩刘康乂',26,
      '淮南将王茂章会王师范弟莱州刺史师诲攻密州，拔之，斩其刺史刘康乂',
      [('王茂章','会攻密州者'),('王师诲','会攻密州者'),('刘康乂','被斩密州刺史')],
      when='903年五月至六月间；确日未载',place='密州',
      note='王师范是王师诲之兄，原文未说王师范亲临密州。')
event('zhang_xun_mizhou','张训被置为密州刺史',26,
      '以淮海都游奕使张训为刺史。',[('张训','受任者')],
      when='903年五月至六月间；确日未载',place='密州',
      note='承前密州陷落的刺史任命；未另推断任命文书主体。')
person('王师范',26,'王师诲兄','王师范弟莱州刺史师诲')
rel='relationship_person_王师范_person_王师诲_兄长'
B['person_relationships'].append(dict(key=rel,person_a_key=people['王师范'],
    person_b_key=people['王师诲'],relation_type='兄长',
    description='王师范是王师诲的兄长。',status='draft'))
claim('person_relationship',rel,'description','王师范是王师诲的兄长。',26,
      '王师范弟莱州刺史师诲','“弟师诲”明示长幼；不因此推王师范亲临密州。')

# 27. Dengzhou falls before the Shilou counterattack and Zhu Youning's death.
event('dengzhou_taken','汴军乙亥攻取登州',27,
      '六月，乙亥，汴兵拔登州。',
      when='903年六月乙亥',place='登州',
      note='本句未指具体攻城将领，不补设个人参与。')
event('shilou_two_camps','王师范率登莱兵于石楼设两栅拒朱友宁',27,
      '师范帅登、莱兵拒硃友宁于石楼，为两栅。',
      [('王师范','设栅拒敌者'),('朱友宁','被拒汴军主将')],
      when='903年六月乙亥后；确日未载',place='石楼',
      note='“登、莱兵”是部队来源，登州在本段前句已陷。')
event('shilou_night_assault','朱友宁丙子夜破登州栅，王茂章按兵待机',27,
      '丙子，夜，友宁击登州栅，栅中告急，师范趣茂章出战，茂章案兵不动。友宁破登州栅，进攻莱州栅。',
      [('朱友宁','夜袭者'),('王师范','催援者'),('王茂章','按兵待机者')],
      when='903年六月丙子夜',place='石楼',
      note='“按兵不动”是此夜行为，不误写为全役不战；破栅与次晨反击分录。')
event('shilou_counterattack','王茂章次晨会王师范反击，大败朱友宁军',27,
      '比明，茂章度其兵力已疲，乃与师范合兵出战，大破之。',
      [('王茂章','判断时机并反击者'),('王师范','合兵反击者'),('朱友宁','败军主将')],
      when='903年六月丙子翌晨',place='石楼',
      note='“兵力已疲”为王茂章判断，主书记反击得胜。')
event('zhu_youning_killed','朱友宁马仆，张士枭斩之并传首淮南',27,
      '友宁旁自峻阜驰骑赴敌，马仆，青州将张士枭斩之，传首淮南。',
      [('朱友宁','战死者'),('张士枭','斩杀者')],
      when='903年六月丙子翌晨',place='石楼',
      note='马仆、斩杀与传首据本段；新五代史较简，仅称堕马见杀。')
event('shilou_pursuit','青州与淮南两镇军追汴军至米河',27,
      '两镇兵逐北至米河，俘斩万计，魏博之兵殆尽。',
      [('王师范','青州军主帅'),('王茂章','淮南援军主帅')],
      when='903年六月丙子后；确日未载',place='米河',
      note='“万计”“殆尽”均为主书记数与概述，不独立推精确伤亡。')

# 28. Zhu Quanzhong's July campaign and Wang Maozhang's withdrawal.
event('zhu_marches_qingzhou','朱全忠闻朱友宁死后率军急赴青州',28,
      '全忠闻友宁死，自将兵二十万昼夜兼行赴之。秋，七月，壬子，至临朐，命诸将攻青州。',
      [('朱温','率军并命攻青州者')],
      when='903年六月后；七月壬子至临朐',place='临朐、青州',
      note='二十万为主书记数；友宁已死，不列为本次进军的参与者。')
event('wang_shifan_july_defeat','王师范出战，汴军大破之',28,
      '王师范出战，汴兵大破之。',
      [('王师范','出战败方'),('朱温','汴军主帅')],
      when='903年七月壬子后；确日未载',place='青州',
      note='先记王师范军失利，再记王茂章另一支的反击，避免合并胜负。')
event('wang_maozhang_ambush','王茂章示怯后突击汴军，汴军至晡退',28,
      '王茂章闭垒示怯，伺汴兵稍懈，毁栅而出，驱驰疾战，战酣退坐，召诸将饮酒，已而复战。',
      [('王茂章','佯弱后出战者'),('朱温','对阵汴军主帅')],
      when='903年七月壬子后；确日未载',place='青州',
      note='原文后记“至晡，汴兵乃退”；朱全忠赞王茂章属其当场言论。')
event('wang_maozhang_withdraws','王茂章虑众寡不敌，当夜引军离去',28,
      '茂章度众寡不敌，是夕，引军还。',
      [('王茂章','撤军者')],when='903年七月临朐战后当夜',place='青州附近',
      note='虽局部击退汴军，王茂章仍判断兵力不敌而夜撤。')
event('li_qianyu_rearguard','杨师厚追击王茂章，李虔裕率五百骑殿后被擒杀',28,
      '全忠遣曹州刺史杨师厚追之，及于辅唐。茂章命先锋指挥使李虔裕将五百骑为殿，虔裕殊死战，师厚擒而杀之。',
      [('朱温','遣追兵者'),('杨师厚','追击并擒杀者'),('王茂章','令殿后者'),('李虔裕','殿后战死者')],
      when='903年七月临朐战后；确日未载',place='辅唐',
      note='五百骑为主书记数；《新五代史》记李虔裕战死，但不明说被擒杀，异文并列。')
event('zhang_xun_evacuates_mizhou','张训拒焚掠密州，封府库整军撤离',28,
      '训曰：“不可。”封府库，植旗帜于城上，遣羸弱居前，自以精兵殿其后而去。',
      [('张训','安排撤军者')],when='903年七月王茂章离青州后；确日未载',place='密州',
      note='其将请焚城大掠，张训明确拒绝；不能写成密州被其焚掠。')
event('wang_tan_mizhou','王檀迟疑数日后入密州，朱全忠任其刺史',28,
      '全忠遣左踏白指挥使王檀攻密州，既至，望旗帜，数日乃敢入城。见府库城邑皆完，遂不复追。训全军而还。全忠以檀为密州刺史。',
      [('朱温','遣军并任命者'),('王檀','入城并受任者'),('张训','全军撤还者')],
      when='903年七月王茂章离青州后；确日未载',place='密州',
      note='王檀见旗帜后数日才入城；密州府库城邑完好，张训已撤。')

extra(old_five,'event','event_zztj_264_0903_bochang_forced_labor','description',
      '《旧五代史》卷12亦记朱友宁驱民众筑博昌土山。',
      '友寧乃下俘民眾十餘萬，各領負木石、牽牛驢',25,'corroborates',
      '旧五代史称俘民，通鉴称民丁；身份措辞并列。')
extra(new_youning,'event','event_zztj_264_0903_bochang_massacre','description',
      '《新五代史》卷13亦称朱友宁围博昌并屠之。',
      '圍博昌，屠之',25,'corroborates','新五代史称清河为之不流，为史家叙述，不估算死者。')
extra(old_five,'event','event_zztj_264_0903_zhu_youning_killed','description',
      '《旧五代史》卷12记朱友宁石楼作战马仆而亡。',
      '所乘馬蹶而仆，遂沒於陣',27,'corroborates',
      '旧五代史不指斩者姓名；张士枭见通鉴。')
extra(new_youning,'event','event_zztj_264_0903_zhu_youning_killed','description',
      '《新五代史》卷13记朱友宁石楼兵败、堕马被杀。',
      '戰於石樓，兵敗，友寧墮馬見殺',27,'corroborates',
      '与通鉴大势相合；不把本传数字与通鉴伤亡相加。')
extra(new_wang_a,'event','event_zztj_264_0903_shilou_night_assault','description',
      '《新五代史》卷23中王景仁即王茂章，亦记夜攻一栅时他按兵不动。',
      '柵中告急，趣景仁出戰，景仁按兵不動',27,'corroborates',
      '同段后文以王茂章指称景仁，异名归入已有主体，不新建王景仁。')
extra(new_wang_b,'event','event_zztj_264_0903_wang_maozhang_ambush','description',
      '《新五代史》卷23亦记王茂章在朱全忠军前以战中饮酒示镇定。',
      '召諸將飲酒，已而復戰',28,'corroborates',
      '新五代史同段明言王景仁、王茂章为同一人。')
extra(new_wang_b,'event','event_zztj_264_0903_li_qianyu_rearguard','description',
      '《新五代史》卷23记李虔裕殿后战死、王茂章全军归。',
      '虔裕卒戰死，梁兵以故不能及，而景仁全軍以歸',28,'conflicts',
      '通鉴作杨师厚擒而杀之；旧五代史仅记战死，死法异说并列。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,29):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天复三年第25—28段连续处理；博昌、石楼与临朐战事按月日拆分，王景仁异名及李虔裕死法异说并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=903,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(25,29)],next_paragraph=Q[29]['id'],
    coverage='卷264天复三年共54个非空段落中的第25—28段连续处理；第28段含多轮作战与撤军，按可审粒度分录。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
