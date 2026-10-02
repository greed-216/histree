"""Curate Tongjian 268, year 913, consecutive paragraphs 1-10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 50))
main1 = 'tongjian-268-912-year-end'
main2 = 'tongjian-268-913-coup'
old_conspiracy = 'jiuwudaishi-008-conspiracy'
old_accession = 'jiuwudaishi-008-accession'
new_yougui = 'xinwudaishi-013-yougui-end'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0913-p001-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, ROOT / 'content/books/zizhi-tongjian/vol-268/year-0912/part-05/sources/library' / main1, 'c07f5489', '司马光等'),
    (main2, P / 'sources/library' / main2, 'be135c91', '司马光等'),
    (old_conspiracy, P / 'sources/library' / old_conspiracy, 'be135c91', '薛居正等'),
    (old_accession, P / 'sources/library' / old_accession, 'be135c91', '薛居正等'),
    (new_yougui, P / 'sources/library' / new_yougui, 'be135c91', '欧阳修'),
]
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
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {key:(source_dirs[key]/'source.txt').read_text() for key in (main1,main2)}
for n in range(1,11):
    row=Q[n]
    assert row['text']==(ROOT/'resources/derived/tongjian/268.txt').read_text().splitlines()[row['source_line']-1]
    assert any(row['text'] in text for text in primary_texts.values()),n

registry = {}
existing_relation_keys = set()
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    archived = json.loads(path.read_text())
    existing_relation_keys.update(row['key'] for row in archived['person_relationships'])
    for row in archived['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (path, row['name'])
        registry[row['name']] = row
aliases = {'吴越王镠':'钱镠','楚王殷':'马殷','蜀主':'王建',
           '王景仁':'王茂章','张宗奭':'张全义','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','元膺':'王宗懿','硃友谦':'朱友谦','王镠':'钱镠','吴越王镠':'钱镠','张宗奭':'张全义','李存审':'符存审','韩珪':'韩勍','丁昭浦':'丁昭溥','徐知浩':'李昪','徐知诰':'李昪','王德明':'张文礼','段凝':'段明远','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1,main2) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1,main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化三年（913）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0913_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1,main2):
        book = json.loads((source_dirs[source] / 'paragraph.json').read_text())['book']
        supplements.append(dict(claim_key=ck, source_book=book, primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=supplement_relation))
    return ck

def person(name, n, role, quote):
    name = aliases.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷268乾化三年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=913):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_268_0913_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '913年本段条；确日未载', dynasty='五代十国',
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
          '段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_268_0913_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key,
                                       role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key

def relation(a, b, kind, n, quote, note):
    ak, bk = people[a], people[b]
    key = f'relationship_{ak}_{bk}_{kind}'
    if key in existing_relation_keys:
        reused.add(key)
    B['person_relationships'].append(dict(key=key, person_a_key=ak, person_b_key=bk,
                                          relation_type=kind, description=f'{a}是{b}的{kind}。', status='draft'))
    claim('person_relationship', key, 'description', f'{a}是{b}的{kind}。', n, quote, note)

event('zhou_dewei_takes_shunzhou', '周德威攻下燕顺州', 1,
      '春，正月，丁巳，晋周德威拔燕顺州。',
      [('周德威','率晋军攻下燕顺州')],
      when='913年正月丁巳',place='顺州',
      note='只确认顺州失于燕、入晋，未记守将姓名。')

event('yougui_fengli_rites', '朱友珪祭太庙、圜丘，大赦并改元凤历', 2,
      '癸亥，郢王友珪朝享太庙；甲子，祀圜丘，大赦，改元凤历。',
      [('朱友珪','主持祭礼并改元凤历的梁帝')],
      when='913年正月癸亥祭太庙、甲子祭圜丘及改元',place='洛阳',
      note='凤历年号只用于朱友珪短暂在位；第9段朱友贞即位后复称乾化三年。')

event('chen_zhang_retreats_jingnan', '陈璋攻荆南未克，以二百舟夜过江口拦截', 3,
      '吴陈璋攻荆南，不克而还，荆南兵与楚兵会于江口以邀之；璋知之，舟二百艘骈为一列，夜过，二镇兵遽出追之，不能及。',
      [('陈璋','攻荆南不克后率吴水军夜过江口脱围')],
      when='913年正月；确日未载',place='荆南、江口',
      note='“二镇兵”是荆南和楚军；原文仅记追而不及，不推水战胜负或伤亡。')

event('zhou_dewei_anyuan_jizhou', '周德威取燕安远军，蓟州将成行言等降晋', 4,
      '晋周德威拔燕安远军，蓟州将成行言等降于晋。',
      [('周德威','率晋军取安远军'),('成行言','与蓟州同僚降晋的燕将')],
      when='913年正月；确日未载',place='安远军、蓟州',
      note='成行言为具名降将，“等”未具名者不另建。')

event('shu_pardon_renwu', '前蜀二月壬午大赦', 5,
      '二月，壬午，蜀大赦。',
      when='913年二月壬午',place='前蜀',
      note='原文未列赦令范围或具名发令者。')

event('youzhen_zhaoyan_conspire', '朱友贞与赵岩在大梁谋诛朱友珪', 6,
      '岩奉使至大梁，均王友贞密与之谋诛友珪，岩曰：“此事成败，在招讨杨令公耳，得其一言谕禁军，吾事立办。”',
      [('赵岩','与朱友贞密谋并主张争取杨师厚的梁驸马'),('朱友贞','在大梁谋诛朱友珪的均王'),('朱友珪','被二人谋求诛除的梁帝'),('杨师厚','赵岩认为需争取的招讨使')],
      when='913年二月庚寅前；确日未载',place='大梁',
      note='这是谋议阶段，未把朱友珪之死或朱友贞即位提前记录。')
claim('event','event_zztj_268_0913_youzhen_zhaoyan_conspire','description',
      '《旧五代史》卷八亦记朱友贞在东京与赵岩议诛朱友珪。',6,
      '會趙岩至東京，從帝私宴，因言及社稷事。帝以誠款謀之，岩曰：「此事易如反掌，成敗在招討楊令公之手，但得一言諭禁軍，其事立辦。」',
      '旧书用即位后的“帝”称朱友贞，本批仍按事发时均王身份展示；东京即大梁。',old_conspiracy,'corroborates')
event('ma_shenjiao_persuades_yang', '朱友贞遣马慎交说杨师厚，允犒军五十万缗', 6,
      '均王乃遣腹心马慎交之魏州说杨师厚曰：“郢王篡弑，人望属在大梁，公若因而成之，此不世之功也。”且许事成之日赐犒军钱五十万缗。',
      [('朱友贞','遣亲信赴魏州并承诺犒军的均王'),('马慎交','赴魏州说服杨师厚的亲信'),('杨师厚','被争取支持政变的魏州将领')],
      when='913年二月庚寅前；确日未载',place='大梁、魏州',
      note='五十万缗为事成之后的许诺，不记作已支付。')
event('yang_shihou_joins_conspiracy', '杨师厚经将佐劝说后响应，遣王舜贤与朱汉宾为内外应', 6,
      '师厚惊曰：“吾几误计。”乃遣其将王舜贤至洛阳，阴与袁象先谋，遣招讨马步都虞候谯人硃汉宾将兵屯滑州为外应。赵岩归洛阳，亦与象先密定计。',
      [('杨师厚','决定响应朱友贞、布置内外联络'),('王舜贤','受遣至洛阳联系袁象先'),('袁象先','在洛阳与杨师厚方及赵岩密议'),('硃汉宾','率兵屯滑州为外应的朱汉宾'),('赵岩','返洛阳与袁象先密定计划')],
      when='913年二月庚寅前；确日未载',place='魏州、洛阳、滑州',
      note='“硃汉宾”为底本字形，站内用朱汉宾；外应驻滑州，不写成已入宫。')

event('yougui_punishes_longxiang', '朱友珪延续追捕龙骧军溃兵并株连', 7,
      '友珪治龙骧军溃乱者，搜捕其党，获者族之，经年不已。',
      [('朱友珪','持续搜捕和株连龙骧军溃兵的梁帝')],
      when='912年八月溃乱后至913年二月；持续发生',place='后梁',
      note='“经年不已”是跨年持续政策，不全归到913年新起事件。')
next(x for x in B['events'] if x['key']=='event_zztj_268_0913_yougui_punishes_longxiang').update(start_year=912,end_year=913)
event('youzhen_rallies_longxiang', '朱友贞借龙骧军恐惧动员其将校赴洛阳', 7,
      '戊子，龙骧将校见均王，泣请可生之路，王曰：“先帝与汝辈三十馀年征战，经营王业。今先帝尚为人所弑，汝辈安所逃死乎！”因出太祖画像示之而泣曰：“汝能自趣洛阳雪仇耻，则转祸为福矣。”众皆踊跃呼万岁，请兵仗，王给之。',
      [('朱友贞','向龙骧将校许以赴洛阳复仇途径并给兵仗的均王')],
      when='913年二月戊子',place='大梁、洛阳',
      note='“天子欲坑汝辈”见前文，是均王使人散布以激兵的言辞，不录为朱友珪真实命令。')

event('yuan_xiangxian_palace_coup', '袁象先率禁兵入宫推翻朱友珪', 8,
      '庚寅旦，袁象先等帅禁兵数千人突入宫中。友珪闻变，与妻张氏及冯廷谔趋北垣楼下，将逾城，自度不免，',
      [('袁象先','率禁兵数千入宫的政变将领'),('朱友珪','闻变欲越城逃走的梁帝'),('张氏（朱友珪妻）','随朱友珪赴北垣的妻子'),('冯廷谔','随朱友珪赴北垣的亲吏')],
      when='913年二月庚寅晨',place='洛阳宫中',
      note='此时为禁兵突入、友珪欲逃，死亡见下一事件。')
event('feng_tinge_kills_yougui_and_self', '冯廷谔依朱友珪令杀张氏、朱友珪，随后自刭', 8,
      '令廷谔先杀妻，次杀己，廷谔亦自刭。',
      [('朱友珪','令冯廷谔杀其妻及自己'),('张氏（朱友珪妻）','被冯廷谔杀害的朱友珪妻'),('冯廷谔','依令杀二人后自刭')],
      when='913年二月庚寅',place='洛阳宫北垣',
      note='主书明确友珪令亲吏先杀妻再杀己，不能写作友珪亲手自刎。')
claim('event','event_zztj_268_0913_feng_tinge_kills_yougui_and_self','description',
      '《新五代史》卷十三也记冯廷谔杀张氏与朱友珪，继而自杀。',8,
      '使馮廷諤進刃其妻及己，廷諤亦自殺。',
      '新史与主书同记执行者及顺序；其“二月”未给确日。',new_yougui,'corroborates')
event('luoyang_sack_after_coup', '政变后洛阳遭大掠，杜晓、李珽被杀，于兢、李振受伤', 8,
      '诸军十馀万大掠都市，百司逃散，中书侍郎、同平章事杜晓、侍讲学士李珽皆为乱兵所杀，门下侍郎、同平章事于兢、宣政使李振被伤。至晡乃定。',
      [('杜晓','洛阳政变后被乱兵杀害的宰相'),('李珽','被乱兵杀害的侍讲学士'),('于兢','在大掠中受伤的宰相'),('李振','在大掠中受伤的宣政使')],
      when='913年二月庚寅晨至晡',place='洛阳',
      note='“十余万”为主书所载诸军规模，不推为实际参与抢掠或死亡人数。')

event('zhu_youzhen_accession_daliang', '朱友贞在大梁即位，复称乾化三年并恢复朱友文官爵', 9,
      '象先、岩赍传国宝诣大梁迎均王，王曰：“大梁国家创业之地，何必洛阳！”乃即帝位于大梁，复称乾化三年，追废友珪为庶人，复博王友文官爵。',
      [('袁象先','携传国宝赴大梁迎均王'),('赵岩','同赴大梁迎均王的驸马'),('朱友贞','在大梁即位并恢复乾化年号的新梁帝'),('朱友珪','死后被追废为庶人'),('朱友文','死后恢复博王官爵')],
      when='913年二月庚寅后；即位确日未载',place='大梁',
      note='主书先述洛阳政变、后记大梁即位，日期未单列；“恢复朱友文官爵”非复活。')
claim('event','event_zztj_268_0913_zhu_youzhen_accession_daliang','description',
      '《旧五代史》卷八记袁象先等携宝迎朱友贞，其决定在东京大梁即位。',9,
      '事定，象先遣趙岩齎傳國寶至東京，請帝即位於洛陽。帝報之曰：「夷門，太祖創業之地',
      '旧书说象先遣赵岩单独齎宝，并先请洛阳即位；主书作象先、岩同往，保留人员与提议差异。',old_accession,'adds')

event('li_cunhui_tanzhou', '李存晖攻燕檀州，陈确以城降晋', 10,
      '丙申，晋李存晖攻燕檀州，刺史陈确以城降。',
      [('李存晖','率晋军攻檀州的将领'),('陈确','以檀州降晋的燕刺史')],
      when='913年二月丙申',place='檀州',
      note='陈确投降且以城归晋，未记围城时长或屠杀。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,11):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷268乾化三年正月至二月第1—10段连续处理；伪说与事实分离，政变、死亡、即位分事件。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=268,year=913,
    primary_source_key=main1,primary_source_keys=[main1,main2],
    paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph='zztj-v268-y0913-p011',
    coverage='卷268乾化三年正月至二月第1—10段，燕晋攻守、梁朱友珪覆亡与朱友贞即位。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[6]['id'],'note':'“天子欲坑龙骧军”是朱友贞使人传播以激兵，不作为朱友珪真实诏令。旧五代史卷8将后续即位称作帝，按当时均王身份展示。'},
      {'paragraph_id':Q[8]['id'],'note':'主书及新五代史均记冯廷谔先杀朱友珪妻张氏、再杀友珪并自杀；乱兵杀杜晓、李珽及伤于兢、李振另列。'},
      {'paragraph_id':Q[9]['id'],'note':'旧五代史作袁象先遣赵岩携宝请洛阳即位，通鉴作象先、岩同赴大梁；过程措辞差异并列，未强并。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
